"""Where does your run first disagree with a reference run?  (roadmap: divergence finder + invariant miner)

    shrunk failing input -> trace yours + every reference -> per-variable value histories
        -> the reference you agree with longest is "your approach"
        -> the first value you produce that it never did = the divergence (step, line, variable)
        -> invariants mined from that reference on many inputs -> the first one your run breaks

Why value histories and not step-by-step alignment: two correct programs take different
numbers of steps, assign in different orders and use helper variables the other doesn't
have. What they share is *meaning*: a variable called `l` in a sliding-window solution walks
through the same sequence of values (0, 2, ...) in both. So for every variable name the two
runs share, we compare the sequence of distinct values it takes, in order. The first value
yours takes that the reference's never did is where your code stopped meaning the same thing.

A shared name only counts as the same variable when its first value has the same type in
both runs (`seen = {}` and `seen = set()` are different ideas that happen to share a name).

Invariants are mined from the matched reference on the failing input plus a dozen generated
ones: integer variables that never decrease (or never increase), and `a <= b` for pairs of
variables the reference itself compares in its source. Restricting pairs to comparisons the
reference makes keeps coincidences out ("best <= r" held on these inputs) and keeps the ones
a reader would recognise in ("l <= r").

Everything is a pure function of traces and inputs, deterministic, stdlib only.
"""
from __future__ import annotations

import ast
import random
import sys

from .harness import FILENAME, CompileError, compile_user, fresh_namespace, prepare
from .problem import Problem, compare
from .tracer import trace_problem

MAX_REF_STEPS = 1500
MINING_INPUTS = 12
MINING_EVENTS = 20_000


# --------------------------------------------------------------------------- #
# Canonical values: compare two snapshots by structure, not identity
# --------------------------------------------------------------------------- #

def canon(v, heap: dict, depth: int = 0, path: frozenset = frozenset()):
    """An encoded value (+ its step heap) -> a hashable structure that equal values share."""
    if not isinstance(v, dict):
        return v
    if "r" in v:
        rid = str(v["r"])
        obj = heap.get(rid)
        if obj is None or depth > 60 or rid in path:
            return ("…",)
        path = path | {rid}
        kind = obj[0]
        if kind in ("list", "tuple", "deque"):
            return (kind, tuple(canon(x, heap, depth + 1, path) for x in obj[1]), obj[2] if len(obj) > 2 else None)
        if kind == "set":
            return ("set", tuple(sorted((canon(x, heap, depth + 1, path) for x in obj[1]), key=repr)))
        if kind == "dict":
            pairs = [(canon(k, heap, depth + 1, path), canon(x, heap, depth + 1, path)) for k, x in obj[1]]
            return ("dict", tuple(sorted(pairs, key=repr)))
        if kind == "obj":
            return ("obj", obj[1], tuple((f, canon(x, heap, depth + 1, path)) for f, x in obj[2]))
        return ("?",)
    if "f" in v:
        return ("float", v["f"])
    if "big" in v:
        return int(v["big"])
    if "fn" in v:
        return ("fn",)
    return ("repr", v.get("repr"))


def _kind(c) -> str:
    if isinstance(c, tuple) and c:
        return str(c[0])
    return type(c).__name__


def show(c, limit: int = 60) -> str:
    """Canonical value -> short Python-looking text for the UI."""
    text = _show(c)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _show(c) -> str:
    if not isinstance(c, tuple):
        return repr(c)
    tag = c[0]
    if tag in ("list", "tuple", "deque"):
        inner = ", ".join(_show(x) for x in c[1])
        if c[2]:
            inner += ", …"
        if tag == "list":
            return f"[{inner}]"
        if tag == "tuple":
            return f"({inner}{',' if len(c[1]) == 1 else ''})"
        return f"deque([{inner}])"
    if tag == "set":
        return "{" + ", ".join(_show(x) for x in c[1]) + "}" if c[1] else "set()"
    if tag == "dict":
        return "{" + ", ".join(f"{_show(k)}: {_show(x)}" for k, x in c[1]) + "}"
    if tag == "obj":
        fields = dict(c[2])
        if "val" in fields:
            return f"{c[1]}({_show(fields['val'])})"
        return f"{c[1]}(…)"
    if tag == "float":
        return c[1]
    if tag == "repr":
        return str(c[1])
    return "…"


# --------------------------------------------------------------------------- #
# Value histories of the entry frame
# --------------------------------------------------------------------------- #

def histories(trace: dict) -> dict:
    """{name: [(step_index, canonical_value), ...]} - one entry per *change*, for the outermost call."""
    hist: dict = {}
    last: dict = {}
    root = None
    for i, st in enumerate(trace.get("steps") or []):
        frames = st.get("s") or []
        if not frames:
            continue
        f0 = frames[0]
        if root is None:
            root = f0["id"]
        if f0["id"] != root:
            break  # a second top-level call (design problems): out of scope
        heap = st.get("h") or {}
        for name, val in f0["v"]:
            if name == "self":
                continue
            c = canon(val, heap)
            if c == ("fn",):
                continue
            if name not in last or last[name] != c:
                hist.setdefault(name, []).append((i, c))
                last[name] = c
    return hist


def _comparable(user_hist: dict, ref_hist: dict) -> list:
    """Shared names whose first values have the same type: the same idea in both runs."""
    out = []
    for name in sorted(set(user_hist) & set(ref_hist)):
        if _kind(user_hist[name][0][1]) == _kind(ref_hist[name][0][1]):
            out.append(name)
    return out


def _walk(user_hist: dict, ref_hist: dict, names: list):
    """Replay your changes in step order against the reference's history of the same variable."""
    events = sorted((i, name, k, c) for name in names for k, (i, c) in enumerate(user_hist[name]))
    matched = []  # (user_step, ref_step)
    for i, name, k, c in events:
        rh = ref_hist[name]
        if k >= len(rh):
            return {"kind": "extra", "step": i, "var": name, "yours": c, "ref": rh[-1][1], "refStep": rh[-1][0]}, matched
        if rh[k][1] != c:
            return {"kind": "value", "step": i, "var": name, "yours": c, "ref": rh[k][1], "refStep": rh[k][0]}, matched
        matched.append((i, rh[k][0]))
    return None, matched


def _missing(user_hist: dict, ref_hist: dict, names: list, matched: list):
    """Every change you made matched - did the reference make one you never did?"""
    best = None
    for name in names:
        uh, rh = user_hist[name], ref_hist[name]
        if len(rh) > len(uh):
            ref_step = rh[len(uh)][0]
            if best is None or ref_step < best["refStep"]:
                user_step = max((u for u, r in matched if r <= ref_step), default=uh[-1][0])
                best = {"kind": "missing", "step": user_step, "var": name, "yours": uh[-1][1],
                        "ref": rh[len(uh)][1], "refStep": ref_step}
    return best


def _params(problem: Problem) -> set:
    return {p.name for p in problem.signature.params}


# --------------------------------------------------------------------------- #
# Invariant mining
# --------------------------------------------------------------------------- #

class _Stop(BaseException):
    pass


def record_ints(problem: Problem, source: str, args: dict, names: set, max_events: int = MINING_EVENTS) -> list:
    """Integer locals of the entry frame, before every line and at return (a light tracer)."""
    try:
        ns = fresh_namespace(compile_user(source))
        run, _ = prepare(problem, ns, args)
    except Exception:  # noqa: BLE001
        return []
    rows: list = []
    root: list = []

    def local(frame, event, arg):
        if frame is root[0] and event in ("line", "return"):
            loc = frame.f_locals
            rows.append({n: loc[n] for n in names if n in loc and type(loc[n]) is int})
            if len(rows) > max_events:
                raise _Stop()
        return local

    def glob(frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None
        if not root:
            root.append(frame)
            return local
        return None

    prev = sys.gettrace()
    sys.settrace(glob)
    try:
        run()
    except _Stop:
        pass
    except Exception:  # noqa: BLE001 - a reference never fails on valid input; be defensive anyway
        pass
    finally:
        sys.settrace(prev)
    return rows


def compared_pairs(source: str) -> set:
    """(a, b) name pairs the source compares directly: `l < r`, `while i <= j`, ..."""
    pairs = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return pairs
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            for left, op, right in zip(operands, node.ops, operands[1:]):
                if isinstance(left, ast.Name) and isinstance(right, ast.Name) and \
                        isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                    pairs.add(tuple(sorted((left.id, right.id))))
    return pairs


def mine_invariants(problem: Problem, source: str, names: set, failing_args: dict, *, seed: int = 7,
                    n_inputs: int = MINING_INPUTS) -> list:
    """Invariants of `source` over `names`, holding on every mined run."""
    rng = random.Random(seed)
    inputs = [failing_args]
    tries = 0
    while len(inputs) < n_inputs and tries < n_inputs * 4:
        tries += 1
        args = problem.generate(rng, 2 + tries % 9)
        if problem.is_valid(args):
            inputs.append(args)
    runs = [record_ints(problem, source, a, names) for a in inputs]
    runs = [r for r in runs if r]
    if not runs:
        return []

    found = []
    for name in sorted(names):
        up_ok = down_ok = True
        moved = 0
        for rows in runs:
            prev = None
            for row in rows:
                if name not in row:
                    continue
                v = row[name]
                if prev is not None and v != prev:
                    moved += 1
                    up_ok &= v > prev
                    down_ok &= v < prev
                prev = v
        if moved >= 2 and up_ok:
            found.append({"kind": "nondecreasing", "vars": [name], "text": f"{name} never decreases"})
        elif moved >= 2 and down_ok:
            found.append({"kind": "nonincreasing", "vars": [name], "text": f"{name} never increases"})

    for a, b in sorted(compared_pairs(source)):
        if a not in names or b not in names:
            continue
        le = ge = True
        strict_lt = strict_gt = both = False
        for rows in runs:
            for row in rows:
                if a in row and b in row:
                    both = True
                    x, y = row[a], row[b]
                    le &= x <= y
                    ge &= x >= y
                    strict_lt |= x < y
                    strict_gt |= x > y
        if both and le and strict_lt:
            found.append({"kind": "le", "vars": [a, b], "text": f"{a} ≤ {b}"})
        elif both and ge and strict_gt:
            found.append({"kind": "le", "vars": [b, a], "text": f"{b} ≤ {a}"})
    for inv in found:
        inv["runs"] = len(runs)
    return found


def first_violation(trace: dict, invariants: list):
    """The earliest step of `trace` (entry frame) that breaks one of `invariants`."""
    steps = trace.get("steps") or []
    prev: dict = {}
    root = None
    for i, st in enumerate(steps):
        frames = st.get("s") or []
        if not frames:
            continue
        f0 = frames[0]
        if root is None:
            root = f0["id"]
        if f0["id"] != root:
            break
        cur = {n: v for n, v in f0["v"] if type(v) is int}
        for inv in invariants:
            kind, vs = inv["kind"], inv["vars"]
            if kind in ("nondecreasing", "nonincreasing"):
                n = vs[0]
                if n in cur and n in prev and cur[n] != prev[n]:
                    broke = cur[n] < prev[n] if kind == "nondecreasing" else cur[n] > prev[n]
                    if broke:
                        return {**inv, "step": i, "line": st.get("l"), "before": str(prev[n]), "after": str(cur[n])}
            elif kind == "le":
                a, b = vs
                if a in cur and b in cur and cur[a] > cur[b]:
                    return {**inv, "step": i, "line": st.get("l"), "before": f"{a} = {cur[a]}",
                            "after": f"{b} = {cur[b]}"}
        prev.update(cur)
    return None


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def analyze(problem: Problem, source: str, args: dict, user_trace: dict | None = None, *,
            mine: bool = True) -> dict | None:
    """Compare your run on `args` with the reference that agrees with you longest.

    kind: value (you took a value it never did) | extra (you changed a variable it had stopped
    changing) | missing (it changed one you never did) | return (same path, different or early
    answer) | error (your run raised) | agree | unknown (your trace was truncated).
    Returns None when there is nothing meaningful to compare (design/codec problems, no
    shared variables, or your code could not be traced). Steps index into `user_trace`.
    """
    if problem.signature.kind != "function":
        return None
    if user_trace is None:
        try:
            user_trace = trace_problem(problem, source, args, max_steps=MAX_REF_STEPS)
        except CompileError:
            return None
    user_hist = histories(user_trace)
    if not user_hist:
        return None
    params = _params(problem)

    best = None
    for sol in problem.solutions:
        try:
            ref_trace = trace_problem(problem, sol.code, args, max_steps=MAX_REF_STEPS)
        except CompileError:
            continue
        if ref_trace.get("error") or ref_trace.get("truncated"):
            continue
        ref_hist = histories(ref_trace)
        names = _comparable(user_hist, ref_hist)
        own = [n for n in names if n not in params]
        if not own:
            continue
        div, matched = _walk(user_hist, ref_hist, names)
        if div is None:
            div = _missing(user_hist, ref_hist, names, matched)
        score = (len(matched), len(own), sol.optimal)
        if best is None or score > best["score"]:
            best = {"score": score, "sol": sol, "trace": ref_trace, "hist": ref_hist, "names": names,
                    "div": div, "matched": len(matched)}
    if best is None:
        return None

    steps = user_trace.get("steps") or []
    div = best["div"]
    ref_trace = best["trace"]
    user_returned = bool(steps) and steps[-1].get("k") == "return"
    user_failed = user_trace.get("error") is not None
    different = not user_failed and "output" in user_trace and "output" in ref_trace and \
        not compare(problem, args, ref_trace["output"], user_trace["output"])

    out: dict = {"solution": best["sol"].id, "optimal": bool(best["sol"].optimal),
                 "shared": [n for n in best["names"] if n not in params], "matched": best["matched"],
                 "trace": ref_trace}
    if div is not None and div["kind"] == "missing" and (user_returned or user_failed or user_trace.get("truncated")):
        # You agreed on everything you did: you stopped early (judged by the return value below),
        # crashed before getting there (reported as the error), or the trace was cut short,
        # which proves nothing is missing.
        div = None
    if div is not None:
        st = steps[div["step"]] if 0 <= div["step"] < len(steps) else {}
        out.update(kind=div["kind"], step=div["step"], line=st.get("l"), var=div["var"],
                   yours=show(div["yours"]), ref=show(div["ref"]), refStep=div["refStep"],
                   refLine=(ref_trace["steps"][div["refStep"]].get("l") if div.get("refStep") is not None
                            and div["refStep"] < len(ref_trace["steps"]) else None))
    elif user_failed and steps:
        last = len(steps) - 1
        out.update(kind="error", step=last, line=(user_trace["error"] or {}).get("line") or steps[last].get("l"),
                   var=None, yours=f"{user_trace['error'].get('type')}", ref=None, refStep=None, refLine=None)
    elif different and steps:
        last = len(steps) - 1
        out.update(kind="return", step=last, line=steps[last].get("l"), var=None,
                   yours=_short_json(user_trace.get("output")), ref=_short_json(ref_trace.get("output")),
                   refStep=len(ref_trace["steps"]) - 1, refLine=ref_trace["steps"][-1].get("l") if ref_trace["steps"] else None)
    else:
        kind = "unknown" if user_trace.get("truncated") else "agree"
        out.update(kind=kind, step=None, line=None, var=None, yours=None, ref=None, refStep=None, refLine=None)

    out["invariant"] = None
    if mine and out["shared"]:
        try:
            invariants = mine_invariants(problem, best["sol"].code, set(out["shared"]), args)
            out["invariant"] = first_violation(user_trace, invariants)
        except Exception:  # noqa: BLE001 - mining is a bonus; never fail a diagnosis over it
            out["invariant"] = None
    return out


def _short_json(v, limit: int = 60) -> str:
    try:
        text = repr(v)
    except Exception:  # noqa: BLE001
        text = "?"
    return text if len(text) <= limit else text[: limit - 1] + "…"
