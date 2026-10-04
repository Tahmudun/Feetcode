"""Record an execution as a list of complete visual snapshots ("steps").

One step = one completed statement. A step carries:

    k   kind: call | line | return | exc
    l   the line that just ran (1-based)
    n   the next line this frame will run, when known
    b   for if/while/for headers: 1 if the body was entered, 0 if not
    a   accesses the line performed (cells compared, keys probed, edges rewired)
    s   the user call stack, outermost first: [{f, id, l, v: [[name, value]...]}]
    h   the heap: every container/object reachable from the stack (values.py)
    r   return value (k=return)       x  exception text (k=exc)
    t   narration (reference solutions only, from `#>` directives)
    o   characters printed to stdout so far
    hide  1 if a `#~` directive hides this step in lesson mode

Steps are snapshots, never deltas: the player renders steps[i] as a pure
function, scrubbing is free, and two traces can be compared step by step.

Line-event normalisation: CPython reports multi-line statements as 3,4,3 and
(3.12+) inlined comprehension iterations as repeated events on one line. Both
collapse into the statement's single step; genuine one-line loops
(`while x: x -= 1`) still produce one step per iteration.
"""
from __future__ import annotations

import collections
import sys

from .analysis import Directives, Program, Unsafe, parse_directives, render_template, safe_eval
from .harness import (FILENAME, BoundedIO, CompileError, EntryError, OutputError, compile_user,
                      describe_error, fresh_namespace, prelude_names, prepare)
from .meter import COMPREHENSION_FRAMES, BudgetExceeded
from .problem import Problem
from .values import Encoder, _sort_key, object_fields

MAX_STEPS = 1500
TRACE_BUDGET = 400_000


class TraceLimit(BaseException):
    """Too many steps; stop the program (BaseException: user code can't catch it)."""


class _FrameState:
    __slots__ = ("fid", "pending", "last_phys", "acc", "unwinding")

    def __init__(self, fid):
        self.fid = fid
        self.pending = None
        self.last_phys = None
        self.acc = None
        self.unwinding = False


class Tracer:
    def __init__(self, program: Program, directives: Directives | None = None, max_steps=MAX_STEPS,
                 budget=TRACE_BUDGET, stdout: BoundedIO | None = None, strict_narration=False,
                 hide_names: set | None = None, prelude: dict | None = None):
        self.prog = program
        self.dirs = directives
        self.max_steps = max_steps
        self.budget = budget
        self.stdout = stdout
        self.strict = strict_narration
        self.hide_names = hide_names or set()
        self.prelude = prelude or {}
        self.enc = Encoder()
        self.steps: list[dict] = []
        self.frames: dict = {}
        self.next_fid = 1
        self.ops = 0
        self.truncated = False
        self.narration_errors: list[str] = []
        self._busy = False
        self._last_exc = None
        self._prev = None

    # -- installation ------------------------------------------------------ #
    def __enter__(self):
        self._prev = sys.gettrace()
        sys.settrace(self._global)
        return self

    def __exit__(self, *exc):
        sys.settrace(self._prev)
        return False

    def _global(self, frame, event, arg):
        code = frame.f_code
        if code.co_filename != FILENAME or self._busy:
            return None
        if code.co_name in COMPREHENSION_FRAMES:
            return self._count_only
        st = _FrameState(self.next_fid)
        self.next_fid += 1
        self.frames[frame] = st
        self._tick(code.co_firstlineno)
        self._emit({"k": "call", "l": code.co_firstlineno}, frame)
        return self._local

    def _count_only(self, frame, event, arg):
        if event == "line":
            self._tick(frame.f_lineno)
        return self._count_only

    def _tick(self, line):
        self.ops += 1
        if self.ops > self.budget:
            raise BudgetExceeded(self.ops, line)

    def _local(self, frame, event, arg):
        if self._busy:
            return self._local
        st = self.frames.get(frame)
        if st is None:
            return self._local
        if event == "line":
            st.unwinding = False
            ln = frame.f_lineno
            self._tick(ln)
            stmt = self.prog.statement(ln)
            if st.pending is not None and stmt == st.pending and self._continues(st, ln, stmt):
                st.last_phys = ln
                return self._local
            if st.pending is not None:
                self._complete(frame, st, next_line=stmt)
            st.pending, st.last_phys = stmt, ln
            st.acc = self._accesses(stmt, frame)
        elif event == "return":
            if not st.unwinding:  # an exception unwinding the frame also reports 'return'
                self._complete(frame, st, next_line=None, kind="return", ret=arg)
            self.frames.pop(frame, None)
        elif event == "exception":
            exc = arg[1]
            st.unwinding = True
            if exc is not self._last_exc and not isinstance(exc, (BudgetExceeded, TraceLimit)):
                self._last_exc = exc
                line = st.pending or frame.f_lineno
                step = {"k": "exc", "l": line, "x": f"{type(exc).__name__}: {exc}"[:300]}
                if st.acc:
                    step["a"] = st.acc  # e.g. the out-of-range index that caused an IndexError
                self._emit(step, frame)
        return self._local

    def _continues(self, st, ln, stmt):
        """Is this line event part of the statement already pending (not a new execution)?"""
        if ln != stmt:
            return True                                   # continuation line of a multi-line stmt
        prev = st.last_phys
        if prev is not None and prev != stmt and self.prog.statement(prev) == stmt:
            return True                                   # back on the first line after a continuation
        info = self.prog.lines.get(stmt)
        if prev == ln and stmt in self.prog.comprehension_lines and not (info and info.one_line_loop):
            return True                                   # inlined comprehension iteration
        return False

    # -- steps ------------------------------------------------------------- #
    def _complete(self, frame, st, next_line, kind="line", ret=None):
        line = st.pending if st.pending is not None else frame.f_lineno
        step = {"k": kind, "l": line}
        if next_line is not None:
            step["n"] = next_line
        info = self.prog.lines.get(line)
        branch = None
        if kind == "line" and info is not None and info.body is not None and next_line is not None \
                and not info.one_line_loop and info.body != line:
            branch = 1 if next_line == info.body else 0
            step["b"] = branch
        if st.acc:
            step["a"] = st.acc
        if self.dirs is not None:
            if line in self.dirs.hidden:
                step["hide"] = 1
            template = self.dirs.narration.get(line)
            if template:
                self._busy = True
                try:
                    scope = dict(frame.f_locals)
                    scope["_taken"] = bool(branch) if branch is not None else None
                    if kind == "return":
                        scope["_return"] = ret
                    if " || " in template:  # "when the branch is taken || when it is not"
                        yes, _, no = template.partition(" || ")
                        template = yes if branch != 0 else no
                    step["t"] = render_template(template, scope, strict=self.strict,
                                                errors=self.narration_errors, where=f"line {line}")
                except Exception as e:  # noqa: BLE001
                    self.narration_errors.append(f"line {line}: {e}")
                finally:
                    self._busy = False
        if kind == "return":
            step["_ret"] = ret
        st.pending = None
        st.acc = None
        self._emit(step, frame)

    def _emit(self, step, frame):
        if len(self.steps) >= self.max_steps:
            self.truncated = True
            raise TraceLimit()
        self._busy = True
        try:
            chain = []
            f = frame
            while f is not None:
                st = self.frames.get(f)
                if st is not None:
                    chain.append((f, st))
                f = f.f_back
            chain.reverse()
            heap: dict = {}
            queue: collections.deque = collections.deque()
            stack = []
            for f, st in chain:
                pairs = []
                for name, value in self._visible_locals(f):
                    pairs.append([name, self.enc.value(value, heap, queue)])
                stack.append({"f": f.f_code.co_name, "id": st.fid, "l": f.f_lineno, "v": pairs})
            if "_ret" in step:
                step["r"] = self.enc.value(step.pop("_ret"), heap, queue)
            self._drain(heap, queue)
            step["s"] = stack
            step["h"] = {str(k): v for k, v in heap.items()}
            if self.stdout is not None:
                step["o"] = self.stdout.tell()
            self.steps.append(step)
        finally:
            self._busy = False

    def _drain(self, heap, queue):
        from .values import MAX_OBJECTS
        while queue:
            rid, obj = queue.popleft()
            if len(heap) > MAX_OBJECTS:
                heap[rid] = ["obj", "…", []]
                continue
            try:
                heap[rid] = self.enc._encode_object(obj, heap, queue)
            except Exception:  # noqa: BLE001
                heap[rid] = ["obj", type(obj).__name__, []]

    def _visible_locals(self, frame):
        try:
            items = list(frame.f_locals.items())
        except Exception:  # noqa: BLE001
            return []
        module_level = frame.f_code.co_name == "<module>"
        out = []
        for name, value in items:
            if name.startswith("__") or name in self.hide_names:
                continue
            if module_level and name in self.prelude and self.prelude[name] is value:
                continue
            if module_level and (isinstance(value, type) or callable(value)):
                continue
            if name == "self" and type(value).__name__ == "Solution" and not object_fields(value):
                continue
            out.append((name, value))
        return out

    # -- accesses ---------------------------------------------------------- #
    def _accesses(self, line, frame):
        info = self.prog.lines.get(line)
        if info is None or not info.accesses:
            return None
        self._busy = True
        try:
            scope = frame.f_locals
            out = []
            for acc in info.accesses:
                try:
                    rec = self._eval_access(acc, scope)
                except Unsafe:
                    continue
                except Exception:  # noqa: BLE001
                    continue
                if rec:
                    out.append(rec)
            return out or None
        finally:
            self._busy = False

    def _target(self, node, scope):
        """Evaluate a container expression -> (object, var-name-or-None)."""
        import ast
        obj = safe_eval(node, scope)
        name = node.id if isinstance(node, ast.Name) else None
        if name is None and isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            name = f"{node.value.id}.{node.attr}"
        return obj, name

    def _rec(self, obj, name, **kw):
        rec = dict(kw)
        if type(obj) is str:
            if name is None:
                return None
            rec["v"] = name
        else:
            rec["o"] = self.enc.ref(obj)
            if name:
                rec["v"] = name
        return rec

    def _entry_index(self, container, key):
        try:
            if isinstance(container, dict):
                if not dict.__contains__(container, key):
                    return -1
                for i, k in enumerate(dict.keys(container)):
                    if k == key:
                        return i
                return -1
            if isinstance(container, (set, frozenset)):
                if key not in container:
                    return -1
                items = list(container)
                try:
                    items.sort(key=_sort_key)
                except TypeError:
                    items.sort(key=repr)
                return items.index(key)
        except TypeError:
            return -1
        return -1

    def _eval_access(self, acc, scope):
        kind = acc.kind
        if kind == "sub":
            container, name = self._target(acc.nodes[0], scope)
            key = safe_eval(acc.nodes[1], scope)
            if type(container) in (list, tuple, str, collections.deque):
                if type(key) is not int:
                    return None
                n = len(container)
                idx = key + n if key < 0 else key
                rec = self._rec(container, name, i=idx, m=acc.mode)
                if rec is not None and not (0 <= idx < n) and acc.mode != "w":
                    rec["oob"] = 1
                return rec
            if isinstance(container, dict):
                return self._rec(container, name, ei=self._entry_index(container, key), m=acc.mode,
                                 kr=_short(key), hit=int(dict.__contains__(container, key)))
            return None
        if kind == "in":
            key = safe_eval(acc.nodes[0], scope)
            container, name = self._target(acc.nodes[1], scope)
            if type(container) is str:
                if type(key) is not str:
                    return None
                return self._rec(container, name, i=container.find(key), m="in", hit=int(key in container),
                                 kr=_short(key))
            if type(container) in (list, tuple, collections.deque):
                try:
                    i = list(container).index(key)
                except ValueError:
                    i = -1
                return self._rec(container, name, i=i, m="in", hit=int(i >= 0), kr=_short(key))
            if isinstance(container, (dict, set, frozenset)):
                ei = self._entry_index(container, key)
                return self._rec(container, name, ei=ei, m="in", hit=int(ei >= 0), kr=_short(key))
            return None
        if kind == "call":
            obj, name = self._target(acc.nodes[0], scope)
            meth, argn = acc.nodes[1], acc.nodes[2]
            if type(obj) in (list, collections.deque):
                n = len(obj)
                if meth == "append":
                    return self._rec(obj, name, i=n, m="push")
                if meth == "appendleft":
                    return self._rec(obj, name, i=0, m="pushl")
                if meth == "pop":
                    if argn:
                        i = safe_eval(argn[0], scope)
                        if type(i) is not int:
                            return None
                        i = i + n if i < 0 else i
                    else:
                        i = n - 1
                    return self._rec(obj, name, i=i, m="pop") if n else None
                if meth == "popleft":
                    return self._rec(obj, name, i=0, m="pop") if n else None
                if meth == "insert" and argn:
                    i = safe_eval(argn[0], scope)
                    return self._rec(obj, name, i=i, m="push") if type(i) is int else None
                return None
            if isinstance(obj, (set, frozenset)) and argn:
                key = safe_eval(argn[0], scope)
                if meth == "add":
                    return self._rec(obj, name, ei=self._entry_index(obj, key), m="w", kr=_short(key))
                if meth in ("remove", "discard"):
                    return self._rec(obj, name, ei=self._entry_index(obj, key), m="del", kr=_short(key))
                return None
            if isinstance(obj, dict) and argn:
                key = safe_eval(argn[0], scope)
                hit = int(dict.__contains__(obj, key))
                if meth == "get":
                    return self._rec(obj, name, ei=self._entry_index(obj, key), m="r", hit=hit, kr=_short(key))
                if meth == "pop":
                    return self._rec(obj, name, ei=self._entry_index(obj, key), m="del", hit=hit, kr=_short(key))
                if meth == "setdefault":
                    return self._rec(obj, name, ei=self._entry_index(obj, key), m="w", hit=hit, kr=_short(key))
            return None
        if kind == "heap":
            obj, name = self._target(acc.nodes[0], scope)
            fn = acc.nodes[1]
            if type(obj) is not list:
                return None
            if fn in ("heappop", "heapreplace", "heappushpop"):
                return self._rec(obj, name, i=0, m="pop") if obj else None
            if fn == "heappush":
                return self._rec(obj, name, i=len(obj), m="push")
            return None
        if kind == "attrw":
            obj, _ = self._target(acc.nodes[0], scope)
            if obj is None or isinstance(obj, (int, float, str, list, dict, set, tuple)):
                return None
            return {"o": self.enc.ref(obj), "f": acc.nodes[1], "m": "w"}
        return None


def _short(v):
    try:
        r = repr(v)
    except Exception:  # noqa: BLE001
        r = "?"
    return r if len(r) <= 40 else r[:39] + "…"


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #

def trace_problem(problem: Problem, source: str, args: dict, *, max_steps=MAX_STEPS,
                  directives: Directives | None = None, strict_narration=False, budget=TRACE_BUDGET) -> dict:
    """Trace user (or reference) code solving `problem` on `args`."""
    if directives is None:
        directives = parse_directives(source)
    code = directives.code
    program = Program(code)
    code_obj = compile_user(code)
    out = BoundedIO()
    result: dict = {"code": code, "steps": [], "truncated": False, "stdout": "", "error": None,
                    "footnotes": [{"line": ln, "text": t} for ln, t in directives.footnotes]}
    tracer = Tracer(program, directives, max_steps=max_steps, budget=budget, stdout=out,
                    strict_narration=strict_narration)
    old_stdout = sys.stdout
    try:
        ns = fresh_namespace(code_obj)  # class/def statements: not traced
        run, finish = prepare(problem, ns, args)
        sys.stdout = out
        try:
            with tracer:
                raw = run()
        finally:
            sys.stdout = old_stdout
        result["output"] = finish(raw)
        result["returned"] = tracer.enc.encode_standalone(raw)
    except TraceLimit:
        result["truncated"] = True
    except BudgetExceeded as e:
        result["truncated"] = True
        result["error"] = {"type": "TimeLimit", "message": f"stopped after {e.ops:,} operations", "line": e.line}
    except (EntryError, OutputError) as e:
        result["error"] = {"type": type(e).__name__, "message": str(e), "line": None}
    except CompileError:
        raise
    except Exception as e:  # noqa: BLE001 - user code failed: that's a finding, not a crash
        result["error"] = describe_error(e)
    result["steps"] = tracer.steps
    result["stdout"] = out.getvalue()
    result["ops"] = tracer.ops
    if tracer.narration_errors:
        result["narrationErrors"] = tracer.narration_errors
    return result


def trace_script(source: str, *, max_steps=MAX_STEPS, budget=TRACE_BUDGET) -> dict:
    """Trace a free-form script (the Playground): module-level code included."""
    program = Program(source)
    code_obj = compile_user(source)
    from .harness import base_namespace
    ns = base_namespace()
    out = BoundedIO()
    tracer = Tracer(program, None, max_steps=max_steps, budget=budget, stdout=out, prelude=dict(ns))
    result: dict = {"code": source, "steps": [], "truncated": False, "error": None, "footnotes": []}
    old_stdout = sys.stdout
    sys.stdout = out
    try:
        with tracer:
            exec(code_obj, ns)  # noqa: S102
    except TraceLimit:
        result["truncated"] = True
    except BudgetExceeded as e:
        result["truncated"] = True
        result["error"] = {"type": "TimeLimit", "message": f"stopped after {e.ops:,} operations", "line": e.line}
    except Exception as e:  # noqa: BLE001
        result["error"] = describe_error(e)
    finally:
        sys.stdout = old_stdout
    result["steps"] = tracer.steps
    result["stdout"] = out.getvalue()
    result["ops"] = tracer.ops
    return result


__all__ = ["Tracer", "trace_problem", "trace_script", "TraceLimit", "prelude_names"]
