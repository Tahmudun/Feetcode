"""Static facts about user code, evaluated against live frames at runtime.

The tracer knows *what values exist*; this module knows *what each line does*.
Combining the two is what lets Feetcode visualize arbitrary code richly:

* accesses  - `height[l] < height[r]` compares two cells; `seen[n] = i` writes a
              key; `x in window` is a membership probe; `curr.next = prev`
              rewires an edge. The visualizer highlights exactly those things.
* branches  - for if/while/for headers, which line starts the body, so a step
              can say whether the condition was True (and Predict mode can ask).
* probes    - hidden costs. `x in seen` is one line event but scans the whole
              list when `seen` is a list. Probes turn such builtins into
              size-weighted operation counts, so the complexity lab sees O(n^2)
              where a naive line counter sees O(n).

Everything evaluated at runtime goes through `safe_eval`, a tiny interpreter
that refuses anything with side effects (no calls except pure builtins, no
user-defined __getitem__/__getattr__), so analysis can never perturb the
program it is observing.
"""
from __future__ import annotations

import ast
import collections
import io
import math
import re
import tokenize
from dataclasses import dataclass, field

SEQUENCES = (list, tuple, str, collections.deque)
MAPPINGS = (dict,)
SETS = (set, frozenset)


class Unsafe(Exception):
    """Expression cannot be evaluated without risking side effects."""


_SAFE_FUNCS = {"len": len, "abs": abs, "min": min, "max": max, "ord": ord, "chr": chr}
_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}


def _builtin_container(x):
    return type(x) in (list, tuple, str, collections.deque) or isinstance(x, (dict, set, frozenset))


def safe_eval(node, scope):
    """Evaluate a small, side-effect-free subset of Python expressions."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in scope:
            return scope[node.id]
        if node.id in ("True", "False", "None"):
            return {"True": True, "False": False, "None": None}[node.id]
        raise Unsafe(node.id)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        a, b = safe_eval(node.left, scope), safe_eval(node.right, scope)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
            try:
                return _BINOPS[type(node.op)](a, b)
            except ZeroDivisionError as e:
                raise Unsafe("div0") from e
        raise Unsafe("binop")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = safe_eval(node.operand, scope)
        if isinstance(v, (int, float)):
            return -v if isinstance(node.op, ast.USub) else v
        raise Unsafe("unary")
    if isinstance(node, ast.Subscript):
        container = safe_eval(node.value, scope)
        if isinstance(node.slice, ast.Slice):
            raise Unsafe("slice")
        key = safe_eval(node.slice, scope)
        if type(container) in (list, tuple, str, collections.deque) and type(key) is int:
            try:
                return container[key]
            except IndexError as e:
                raise Unsafe("index") from e
        if isinstance(container, dict):
            try:
                if dict.__contains__(container, key):
                    return dict.__getitem__(container, key)
            except TypeError as e:
                raise Unsafe("unhashable") from e
            raise Unsafe("missing key")
        raise Unsafe("subscript")
    if isinstance(node, ast.Attribute):
        obj = safe_eval(node.value, scope)
        if _builtin_container(obj) or obj is None or isinstance(obj, (int, float)):
            raise Unsafe("attr on builtin")
        try:
            d = object.__getattribute__(obj, "__dict__")
        except AttributeError as e:
            raise Unsafe("no dict") from e
        if node.attr in d:
            return d[node.attr]
        raise Unsafe("missing attr")
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        fn = _SAFE_FUNCS.get(node.func.id)
        if fn is None or node.func.id in scope:
            raise Unsafe("call")
        args = [safe_eval(a, scope) for a in node.args]
        if node.func.id == "len" and not (len(args) == 1 and _builtin_container(args[0])):
            raise Unsafe("len")
        if node.func.id in ("min", "max") and not all(isinstance(a, (int, float, str)) for a in args):
            raise Unsafe("minmax")
        try:
            return fn(*args)
        except Exception as e:  # noqa: BLE001
            raise Unsafe("call failed") from e
    if isinstance(node, (ast.List, ast.Tuple)):
        vals = [safe_eval(e, scope) for e in node.elts]
        return vals if isinstance(node, ast.List) else tuple(vals)
    raise Unsafe(type(node).__name__)


# --------------------------------------------------------------------------- #
# Per-line facts
# --------------------------------------------------------------------------- #

@dataclass
class Access:
    kind: str           # sub | in | call | heap | attrw
    nodes: tuple        # AST nodes, interpretation depends on kind
    mode: str = "r"     # r | w | c (compare) | del


@dataclass
class Probe:
    kind: str           # member | walk | strlen | pop | sort | slice | concat | heap
    nodes: tuple
    label: str          # source snippet, for the report
    hint: str           # what to do about it


@dataclass
class LineInfo:
    line: int
    stmt: str
    accesses: list = field(default_factory=list)
    probes: list = field(default_factory=list)
    body: int | None = None      # first body line for if/while/for headers
    orelse: int | None = None
    one_line_loop: bool = False  # `while x: x -= 1` - repeated events are iterations


_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.Lambda)
_LINEAR_METHODS = {
    "index": "list.index scans the list",
    "count": "count scans the whole sequence",
    "remove": "remove scans and shifts the list",
    "insert": "insert shifts every later element",
    "copy": "copy duplicates the whole container",
    "reverse": "reverse touches every element",
}
_STR_METHODS = {"split", "replace", "strip", "lower", "upper", "find", "join", "isalnum", "isalpha", "isdigit"}
_LINEAR_BUILTINS = {"list", "set", "tuple", "dict", "sum", "min", "max", "any", "all", "Counter", "str"}


def _header_exprs(stmt):
    """Expressions evaluated *on the header line* of a statement (not nested bodies)."""
    if isinstance(stmt, (ast.If, ast.While)):
        return [stmt.test]
    if isinstance(stmt, (ast.For, ast.AsyncFor)):
        return [stmt.target, stmt.iter]
    if isinstance(stmt, ast.Assign):
        return [*stmt.targets, stmt.value]
    if isinstance(stmt, ast.AugAssign):
        return [stmt.target, stmt.value]
    if isinstance(stmt, ast.AnnAssign):
        return [stmt.target] + ([stmt.value] if stmt.value else [])
    if isinstance(stmt, (ast.Expr, ast.Return)):
        return [stmt.value] if stmt.value is not None else []
    if isinstance(stmt, ast.Delete):
        return list(stmt.targets)
    if isinstance(stmt, ast.Assert):
        return [stmt.test]
    return []


def _walk_no_comprehension(node, parents=()):
    """Yield (node, parents) excluding comprehension/lambda bodies."""
    yield node, parents
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _COMPREHENSIONS):
            continue
        yield from _walk_no_comprehension(child, parents + (node,))


def _walk_all(node):
    yield from ast.walk(node)


def _segment(source, node):
    try:
        seg = ast.get_source_segment(source, node) or ""
    except Exception:  # noqa: BLE001
        seg = ""
    seg = " ".join(seg.split())
    return seg if len(seg) <= 60 else seg[:59] + "…"


def _collect_accesses(stmt, info):
    is_aug = isinstance(stmt, ast.AugAssign)
    for expr in _header_exprs(stmt):
        for node, parents in _walk_no_comprehension(expr):
            if isinstance(node, ast.Subscript) and not isinstance(node.slice, ast.Slice):
                if isinstance(node.ctx, ast.Store) or (is_aug and node is stmt.target):
                    mode = "w"
                elif isinstance(node.ctx, ast.Del):
                    mode = "del"
                elif any(isinstance(p, ast.Compare) for p in parents):
                    mode = "c"
                else:
                    mode = "r"
                info.accesses.append(Access("sub", (node.value, node.slice), mode))
            elif isinstance(node, ast.Compare):
                left = node.left
                for op, right in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.In, ast.NotIn)):
                        info.accesses.append(Access("in", (left, right), "c"))
                    left = right
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                obj, meth = node.func.value, node.func.attr
                if isinstance(obj, ast.Name) and obj.id == "heapq":
                    if node.args:
                        info.accesses.append(Access("heap", (node.args[0], meth), "w"))
                else:
                    info.accesses.append(Access("call", (obj, meth, tuple(node.args)), "w"))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id.startswith("heap"):
                if node.args:
                    info.accesses.append(Access("heap", (node.args[0], node.func.id), "w"))
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
                info.accesses.append(Access("attrw", (node.value, node.attr), "w"))


def _collect_probes(stmt, info, source):
    for expr in _header_exprs(stmt):
        for node in _walk_all(expr):
            if isinstance(node, ast.Compare):
                for op, right in zip(node.ops, node.comparators):
                    if not isinstance(op, (ast.In, ast.NotIn)):
                        continue
                    if (isinstance(right, ast.Call) and isinstance(right.func, ast.Attribute)
                            and right.func.attr == "values" and not right.args):
                        info.probes.append(Probe("walk", (right.func.value,), _segment(source, node),
                                                 "membership in dict.values() is a linear scan - keep a reverse map or a set"))
                    else:
                        info.probes.append(Probe("member", (right,), _segment(source, node),
                                                 "membership on a list/string is a linear scan - use a set or dict for O(1) lookups"))
            elif isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Attribute):
                    meth = fn.attr
                    if meth in _LINEAR_METHODS:
                        info.probes.append(Probe("walk", (fn.value,), _segment(source, node),
                                                 _LINEAR_METHODS[meth]))
                    elif meth == "pop" and node.args:
                        info.probes.append(Probe("pop", (fn.value, node.args[0]), _segment(source, node),
                                                 "pop(i) shifts every later element - use collections.deque.popleft() for the front"))
                    elif meth == "sort":
                        info.probes.append(Probe("sort", (fn.value,), _segment(source, node),
                                                 "sorting costs n log n each time it runs"))
                    elif meth == "join" and node.args:
                        info.probes.append(Probe("walk", (node.args[0],), _segment(source, node),
                                                 "join walks every piece"))
                    elif meth == "extend" and node.args:
                        info.probes.append(Probe("walk", (node.args[0],), _segment(source, node),
                                                 "extend copies every element"))
                    elif meth in _STR_METHODS:
                        info.probes.append(Probe("strlen", (fn.value,), _segment(source, node),
                                                 "string methods walk the whole string"))
                    elif meth in ("heappush", "heappop", "heappushpop", "heapreplace") and node.args:
                        info.probes.append(Probe("heap", (node.args[0],), _segment(source, node),
                                                 "heap operations cost log n"))
                elif isinstance(fn, ast.Name):
                    if fn.id == "sorted" and node.args:
                        info.probes.append(Probe("sort", (node.args[0],), _segment(source, node),
                                                 "sorted() costs n log n each time it runs"))
                    elif fn.id in _LINEAR_BUILTINS and len(node.args) == 1:
                        info.probes.append(Probe("walk", (node.args[0],), _segment(source, node),
                                                 f"{fn.id}() walks every element"))
                    elif fn.id in ("heappush", "heappop", "heappushpop", "heapreplace") and node.args:
                        info.probes.append(Probe("heap", (node.args[0],), _segment(source, node),
                                                 "heap operations cost log n"))
            elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
                sl = node.slice
                info.probes.append(Probe("slice", (node.value, sl.lower, sl.upper, sl.step), _segment(source, node),
                                         "slicing copies the slice - pass indices instead"))
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                info.probes.append(Probe("concat", (node.left, node.right), _segment(source, node),
                                         "list concatenation copies both lists - append in place"))


_SIZE_PRESERVING = {"set", "frozenset", "list", "tuple", "dict", "sorted", "reversed", "enumerate", "iter",
                    "Counter", "deque"}


def _size_of(node, scope) -> int:
    """len() of what `node` evaluates to, seeing through size-preserving wrappers.

    safe_eval refuses calls, so `sorted(set(nums))`, `sorted(count.items())` and `sum(d.values())`
    would otherwise cost nothing - and an O(n log n) solution would be measured as O(n).
    """
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Name) and node.args:
            if fn.id in _SIZE_PRESERVING:
                return _size_of(node.args[0], scope)
            if fn.id == "zip":
                return min(_size_of(a, scope) for a in node.args)
            if fn.id in ("map", "filter") and len(node.args) == 2:
                return _size_of(node.args[1], scope)
            if fn.id == "range" and len(node.args) <= 3:
                bounds = [safe_eval(a, scope) for a in node.args]
                return len(range(*bounds)) if all(type(b) is int for b in bounds) else 0
        if isinstance(fn, ast.Attribute) and fn.attr in ("items", "keys", "values") and not node.args:
            return _size_of(fn.value, scope)
        return 0
    v = safe_eval(node, scope)
    return len(v) if _builtin_container(v) else 0


def probe_cost(probe, scope):
    """Primitive operations hidden inside one execution of the probed builtin."""
    k = probe.kind
    if k == "member":
        v = safe_eval(probe.nodes[0], scope)
        return len(v) if type(v) in (list, tuple, str, collections.deque) else 0
    if k == "walk":
        return _size_of(probe.nodes[0], scope)
    if k == "strlen":
        v = safe_eval(probe.nodes[0], scope)
        return len(v) if type(v) is str and len(v) > 1 else 0
    if k == "pop":
        v = safe_eval(probe.nodes[0], scope)
        if type(v) is list:
            i = safe_eval(probe.nodes[1], scope)
            if type(i) is int:
                i = i + len(v) if i < 0 else i
                return max(0, len(v) - 1 - i)
        return 0
    if k == "sort":
        n = _size_of(probe.nodes[0], scope)
        return int(n * math.log2(n)) if n > 1 else 0
    if k == "heap":
        v = safe_eval(probe.nodes[0], scope)
        if type(v) is list and len(v) > 1:
            return int(math.log2(len(v)))
        return 0
    if k == "slice":
        v = safe_eval(probe.nodes[0], scope)
        if type(v) not in (list, tuple, str):
            return 0
        lo, hi, st = (safe_eval(n, scope) if n is not None else None for n in probe.nodes[1:])
        try:
            return len(range(*slice(lo, hi, st).indices(len(v))))
        except TypeError:
            return 0
    if k == "concat":
        a = safe_eval(probe.nodes[0], scope)
        b = safe_eval(probe.nodes[1], scope)
        if type(a) in (list, tuple) and type(b) is type(a):
            return len(a) + len(b)
        return 0
    return 0


# --------------------------------------------------------------------------- #
# Whole-program analysis
# --------------------------------------------------------------------------- #

class Program:
    """Parsed source + per-line facts, built once per code string."""

    def __init__(self, source: str):
        self.source = source
        self.tree = ast.parse(source)
        self.lines: dict[int, LineInfo] = {}
        self.stmt_of: dict[int, int] = {}       # physical line -> statement start line
        self.comprehension_lines: set[int] = set()
        self.func_lines: dict[str, int] = {}
        self._index()

    def _index(self):
        for node in ast.walk(self.tree):
            if isinstance(node, _COMPREHENSIONS[:-1]):
                self.comprehension_lines.add(node.lineno)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.func_lines[node.name] = node.lineno
            if not isinstance(node, ast.stmt):
                continue
            ln = node.lineno
            info = self.lines.get(ln)
            if info is None:
                info = self.lines[ln] = LineInfo(line=ln, stmt=type(node).__name__)
            else:
                continue  # a one-liner's body shares the header line; header wins
            end = getattr(node, "end_lineno", ln) or ln
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                info.body = node.body[0].lineno if node.body else None
                info.orelse = node.orelse[0].lineno if node.orelse else None
                info.one_line_loop = isinstance(node, (ast.While, ast.For)) and info.body == ln
                header_end = (node.body[0].lineno - 1) if node.body else end
                for phys in range(ln, max(ln, header_end) + 1):
                    self.stmt_of.setdefault(phys, ln)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.With, ast.Try)):
                self.stmt_of.setdefault(ln, ln)
            else:
                for phys in range(ln, end + 1):
                    self.stmt_of.setdefault(phys, ln)
            _collect_accesses(node, info)
            _collect_probes(node, info, self.source)

    def statement(self, line):
        return self.stmt_of.get(line, line)


# --------------------------------------------------------------------------- #
# Authoring directives for reference solutions
# --------------------------------------------------------------------------- #

_DIRECTIVE = re.compile(r"#([>!~])")


@dataclass
class Directives:
    code: str                                           # source with directives stripped
    narration: dict = field(default_factory=dict)       # line -> template
    footnotes: list = field(default_factory=list)       # [(line, text)]
    hidden: set = field(default_factory=set)            # lines skipped in lesson mode


def parse_directives(source: str) -> Directives:
    """Extract `#>` narration, `#!` footnote and `#~` hide directives from comments.

        water += max_l - height[l]  #> Column {l} holds {max_l - height[l]} #! why min()?
    """
    lines = source.split("\n")
    d = Directives(code="")
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError):
        d.code = source
        return d
    for tok in tokens:
        if tok.type != tokenize.COMMENT:
            continue
        text = tok.string
        m = _DIRECTIVE.search(text)
        if m is None:
            continue
        row, col = tok.start
        keep = text[: m.start()].rstrip()          # an ordinary comment before the directive stays
        parts = _DIRECTIVE.split(text[m.start():])
        # parts: ['', kind, body, kind, body, ...]
        for kind, body in zip(parts[1::2], parts[2::2]):
            body = body.strip()
            if kind == ">":
                d.narration[row] = body
            elif kind == "!":
                d.footnotes.append((row, body))
            elif kind == "~":
                d.hidden.add(row)
        code_part = lines[row - 1][:col].rstrip()
        lines[row - 1] = f"{code_part}  {keep}" if keep and keep != "#" and code_part else (keep if not code_part and keep != "#" else code_part)
    d.code = "\n".join(lines)
    return d


def _find_close(s, start):
    depth, i, quote = 0, start, None
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                return i
            depth -= 1
        i += 1
    return -1


def fmt_value(v, raw=False):
    if raw and isinstance(v, str):
        return v
    if isinstance(v, float):
        if v == math.inf:
            return "∞"
        if v == -math.inf:
            return "−∞"
        return f"{v:g}"
    if isinstance(v, bool) or v is None:
        return str(v)
    if isinstance(v, str):
        return repr(v)
    if hasattr(v, "val") and hasattr(v, "next"):
        return f"node({v.val!r})"
    r = repr(v)
    return r if len(r) <= 60 else r[:59] + "…"


class NarrationError(Exception):
    pass


def render_template(template: str, scope: dict, strict=False, errors: list | None = None, where="") -> str:
    """Fill `{expr}` (repr-formatted) and `{!expr}` (raw) holes from a frame's locals."""
    out, i = [], 0
    while i < len(template):
        ch = template[i]
        if ch == "{":
            if template.startswith("{{", i):
                out.append("{")
                i += 2
                continue
            j = _find_close(template, i + 1)
            if j < 0:
                out.append(template[i:])
                break
            expr = template[i + 1: j].strip()
            raw = expr.startswith("!")
            if raw:
                expr = expr[1:].strip()
            try:
                val = eval(expr, {"__builtins__": _NARRATION_BUILTINS}, dict(scope))  # noqa: S307 - trusted authored templates
                out.append(fmt_value(val, raw))
            except Exception as e:  # noqa: BLE001
                problem = f"{where} {{{expr}}}: {type(e).__name__}: {e}".strip()
                if strict:
                    raise NarrationError(problem) from e
                if errors is not None:
                    errors.append(problem)
                out.append("?")
            i = j + 1
        elif ch == "}" and template.startswith("}}", i):
            out.append("}")
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


_NARRATION_BUILTINS = {
    "len": len, "min": min, "max": max, "abs": abs, "sum": sum, "sorted": sorted,
    "list": list, "str": str, "int": int, "ord": ord, "chr": chr, "tuple": tuple,
    "set": set, "dict": dict, "repr": repr, "range": range, "enumerate": enumerate,
    "any": any, "all": all, "zip": zip, "round": round, "float": float,
    "True": True, "False": False, "None": None,
}
