"""Empirical complexity: run code on growing inputs, count operations, fit a curve.

Because operation counts are deterministic (meter.py), the curves are exact
for the chosen inputs - no warm-up, no timer noise, no machine dependence.
Fitting picks the growth model whose scaled shape best matches the points
(least squares on relative error, intercept allowed for fixed overhead), and
prefers the simpler model when two fit equally well.
"""
from __future__ import annotations

import math
import random
import sys
import time
import tracemalloc

from .analysis import Program
from .harness import BoundedIO, EntryError, OutputError, compile_user, fresh_namespace, prepare
from .meter import BudgetExceeded, Meter
from .problem import Problem

MODELS = [
    ("O(1)", lambda n: 1.0),
    ("O(log n)", lambda n: math.log2(n)),
    ("O(n)", lambda n: float(n)),
    ("O(n log n)", lambda n: n * math.log2(n)),
    ("O(n²)", lambda n: float(n) ** 2),
    ("O(n² log n)", lambda n: float(n) ** 2 * math.log2(n)),
    ("O(n³)", lambda n: float(n) ** 3),
    ("O(2ⁿ)", lambda n: 2.0 ** min(n, 60)),
]
RANK = {name: i for i, (name, _) in enumerate(MODELS)}

PROFILE_CAP = 2_500_000


def _lstsq_rel(xs, ys):
    """Fit y ~ a*x + b minimising relative error; returns (a, b, sse)."""
    w = [1.0 / max(y, 1.0) for y in ys]
    # weighted normal equations for [a, b]
    sxx = sum((wi * x) ** 2 for wi, x in zip(w, xs))
    sx = sum(wi * wi * x for wi, x in zip(w, xs))
    s1 = sum(wi * wi for wi in w)
    sxy = sum(wi * wi * x * y for wi, x, y in zip(w, xs, ys))
    sy = sum(wi * wi * y for wi, y in zip(w, ys))
    det = sxx * s1 - sx * sx
    if abs(det) < 1e-12:
        a, b = (sy / sx if sx else 0.0), 0.0
    else:
        a = (sxy * s1 - sx * sy) / det
        b = (sxx * sy - sx * sxy) / det
    if a < 0:  # decreasing fits are meaningless for cost; force through origin
        a = sxy / sxx if sxx else 0.0
        b = 0.0
    sse = sum((wi * (a * x + b - y)) ** 2 for wi, x, y in zip(w, xs, ys))
    return a, b, sse


SPACE_MODELS = {"O(1)", "O(log n)", "O(n)", "O(n²)"}
MEMORY_FLOOR = 4096  # bytes: below this, tracemalloc sees allocator noise, not growth


def fit(points: list, allowed: set | None = None) -> dict | None:
    """points: [{"n": int, "y": number}] -> best model + slope diagnostics."""
    pts = [(p["n"], p["y"]) for p in points if p.get("y") is not None and p["n"] > 1]
    if len(pts) < 3:
        return None
    ns = [n for n, _ in pts]
    ys = [max(float(y), 1.0) for _, y in pts]
    results = []
    for name, f in MODELS:
        if allowed is not None and name not in allowed:
            continue
        xs = [f(n) for n in ns]
        if any(math.isinf(x) for x in xs):
            continue
        a, b, sse = _lstsq_rel(xs, ys)
        if a <= 0 and name != "O(1)":
            continue
        # A fixed-cost intercept bigger than the largest observation is a sign the model is wrong.
        if b > ys[-1] * 1.5:
            sse *= 10
        results.append((sse, name, a, b))
    if not results:
        return None
    results.sort()
    best_sse = results[0][0]
    # Prefer the simplest model within tolerance of the best fit.
    tolerance = max(best_sse * 1.25, 1e-4)
    candidates = [r for r in results if r[0] <= tolerance]
    candidates.sort(key=lambda r: RANK[r[1]])
    sse, name, a, b = candidates[0]
    # log-log slope over the upper half: the "empirical exponent"
    k = max(2, len(pts) // 2)
    (n1, y1), (n2, y2) = pts[-k], pts[-1]
    slope = math.log(max(y2, 1) / max(y1, 1)) / math.log(n2 / n1) if n2 > n1 else 0.0
    return {"label": name, "a": a, "b": b, "slope": round(slope, 2), "error": round(math.sqrt(sse / len(pts)), 4)}


def input_for(problem: Problem, n: int, seed: int = 7) -> dict:
    if problem.worst_case is not None:
        return problem.worst_case(n)
    return problem.generate(random.Random(seed * 100_003 + n), n)


def profile(problem: Problem, source: str, sizes: list | None = None, cap: int = PROFILE_CAP,
            seed: int = 7, measure_memory: bool = True) -> dict:
    """Operation counts (and time/memory) of `source` across growing n."""
    code_obj = compile_user(source)
    program = Program(source)
    sizes = sizes or problem.sizes
    points = []
    hits, hidden_lines = {}, {}
    stopped = None
    for n in sizes:
        args = input_for(problem, n, seed)
        meter = Meter(program, budget=cap, line_hits=True)
        out = BoundedIO(limit=1000)
        old = sys.stdout
        try:
            ns = fresh_namespace(code_obj)
            run, finish = prepare(problem, ns, args)
            sys.stdout = out
            try:
                with meter:
                    run()
            finally:
                sys.stdout = old
        except BudgetExceeded:
            stopped = {"n": n, "reason": "budget", "ops": meter.ops}
            points.append({"n": n, "ops": None, "capped": True})
            break
        except (EntryError, OutputError, RecursionError, Exception) as e:  # noqa: BLE001
            stopped = {"n": n, "reason": "error", "message": f"{type(e).__name__}: {e}"[:200]}
            break
        point = {"n": n, "ops": meter.ops, "hidden": meter.hidden, "depth": meter.max_depth}
        points.append(point)
        hits, hidden_lines = meter.hits, meter.hidden_by_line
    if measure_memory:
        for point in points:
            if point.get("ops") is None:
                continue
            args = input_for(problem, point["n"], seed)
            point.update(_time_and_memory(problem, code_obj, args))
    time_fit = fit([{"n": p["n"], "y": p["ops"]} for p in points])
    space_fit = fit_space(points) if measure_memory else None
    probe_labels = {}
    for ln, info in program.lines.items():
        if info.probes and ln in hidden_lines:
            probe_labels[ln] = [{"label": pr.label, "hint": pr.hint} for pr in info.probes]
    largest = max((p["n"] for p in points if p.get("ops") is not None), default=None)
    return {
        "points": points,
        "time": time_fit,
        "space": space_fit,
        "n": largest,
        "lines": {str(k): v for k, v in sorted(hits.items())},
        "hidden": [{"line": ln, "cost": c, "probes": probe_labels.get(ln, [])}
                   for ln, c in sorted(hidden_lines.items(), key=lambda kv: -kv[1])],
        "stopped": stopped,
    }


def fit_space(points: list) -> dict | None:
    """Peak heap growth and recursion depth; whichever grows faster wins."""
    done = [p for p in points if p.get("ops") is not None]
    if len(done) < 3:
        return None
    mem = [{"n": p["n"], "y": p.get("mem", 0)} for p in done]
    depth = [{"n": p["n"], "y": p.get("depth", 1)} for p in done]
    if max(m["y"] for m in mem) < MEMORY_FLOOR:
        mem_fit = {"label": "O(1)", "slope": 0.0}
    else:
        mem_fit = fit([{"n": m["n"], "y": max(m["y"], MEMORY_FLOOR)} for m in mem], SPACE_MODELS)
    best = mem_fit
    if max(d["y"] for d in depth) > 16:
        depth_fit = fit(depth, SPACE_MODELS)
        if depth_fit and (best is None or RANK[depth_fit["label"]] > RANK[best["label"]]):
            best = {**depth_fit, "source": "recursion depth"}
    return best


def _time_and_memory(problem, code_obj, args) -> dict:
    """Untraced run for wall time; tracemalloc run for peak memory (input excluded)."""
    out = BoundedIO(limit=1000)
    old = sys.stdout
    result = {}
    try:
        ns = fresh_namespace(code_obj)
        run, _ = prepare(problem, ns, args)
        sys.stdout = out
        t0 = time.perf_counter()
        run()
        result["ms"] = round((time.perf_counter() - t0) * 1000, 3)
        ns = fresh_namespace(code_obj)
        run, _ = prepare(problem, ns, args)
        tracemalloc.start()
        try:
            run()
            result["mem"] = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
    except Exception:  # noqa: BLE001
        pass
    finally:
        sys.stdout = old
    return result
