"""Run test cases and produce verdicts.

`run`    - the visible/custom cases, with full per-case detail.
`submit` - the whole hidden suite (stops at the first failure, like LeetCode),
           then goes further than LeetCode does:
             * on Wrong Answer / Runtime Error: shrink the failing case to a
               minimal counterexample, match known pitfalls, trace it, and find
               where it first diverges from the reference (diverge.py);
             * on Time Limit: profile complexity to show *why* it is slow;
             * on all-pass: fuzz small random inputs for bugs the suite missed,
               then profile complexity so "Accepted" comes with a growth curve.
"""
from __future__ import annotations

import sys
import time

from . import complexity, diverge, fuzz
from .analysis import Program
from .harness import (BoundedIO, CompileError, EntryError, OutputError, compile_user, describe_error,
                      fresh_namespace, prepare)
from .meter import BudgetExceeded, Meter
from .problem import Problem, compare
from .tracer import trace_problem

DEFAULT_BUDGET = 1_000_000


def run_case(problem: Problem, code_obj, program: Program, args: dict, budget: int) -> dict:
    out = BoundedIO()
    old = sys.stdout
    meter = Meter(program, budget=budget)
    t0 = time.perf_counter()
    res: dict = {}
    try:
        ns = fresh_namespace(code_obj)
        run, finish = prepare(problem, ns, args)
        sys.stdout = out
        try:
            with meter:
                raw = run()
        finally:
            sys.stdout = old
        res["status"] = "ok"
        res["output"] = finish(raw)
    except BudgetExceeded as e:
        res["status"] = "tle"
        res["error"] = {"type": "TimeLimit", "message": f"exceeded {budget:,} operations", "line": e.line}
    except (EntryError, OutputError) as e:
        res["status"] = "error"
        res["error"] = {"type": type(e).__name__, "message": str(e), "line": None}
    except Exception as e:  # noqa: BLE001
        res["status"] = "error"
        res["error"] = describe_error(e)
    res["ms"] = round((time.perf_counter() - t0) * 1000, 2)
    res["ops"] = meter.ops
    res["hidden"] = meter.hidden
    stdout = out.getvalue()
    if stdout:
        res["stdout"] = stdout + ("\n… (output clipped)" if out.clipped else "")
    return res


def _expected_for(problem: Problem, args: dict, ref_cache: dict):
    """Expected output for a custom case, computed by the optimal reference."""
    key = repr(args)
    if key not in ref_cache:
        ref = fuzz.Runner(problem, problem.optimal.code, budget=5_000_000)
        r = ref.run(args)
        ref_cache[key] = r.get("output") if r["ok"] else None
    return ref_cache[key]


def run(problem: Problem, source: str, tests: list) -> dict:
    """tests: [{"args": {...}, "expected"?: ...}] -> per-case results."""
    try:
        code_obj = compile_user(source)
    except CompileError as e:
        return {"verdict": "compile", "error": e.to_json(), "cases": []}
    program = Program(source)
    cases, ref_cache = [], {}
    for t in tests:
        args = t["args"]
        valid = problem.is_valid(args)
        expected = t["expected"] if "expected" in t else _expected_for(problem, args, ref_cache)
        res = run_case(problem, code_obj, program, args, t.get("budget", DEFAULT_BUDGET))
        res["expected"] = expected
        if not valid:
            res["invalid"] = True
        res["pass"] = res["status"] == "ok" and expected is not None and compare(problem, args, expected, res["output"])
        cases.append(res)
    verdict = "accepted" if cases and all(c["pass"] for c in cases) else _worst(cases)
    return {"verdict": verdict, "cases": cases}


def _worst(cases):
    statuses = {c["status"] for c in cases}
    if "error" in statuses:
        return "error"
    if "tle" in statuses:
        return "tle"
    return "wrong"


def submit(problem: Problem, source: str, tests: list, *, fuzz_cases=150, with_trace=True) -> dict:
    try:
        code_obj = compile_user(source)
    except CompileError as e:
        return {"verdict": "compile", "error": e.to_json()}
    program = Program(source)
    t0 = time.perf_counter()
    total_ops = 0
    passed = 0
    failure = None
    for idx, t in enumerate(tests):
        res = run_case(problem, code_obj, program, t["args"], t.get("budget", DEFAULT_BUDGET))
        total_ops += res["ops"]
        ok = res["status"] == "ok" and compare(problem, t["args"], t["expected"], res["output"])
        if not ok:
            failure = {"index": idx, "args": t["args"], "expected": t["expected"], **res}
            break
        passed += 1
    result: dict = {"passed": passed, "total": len(tests), "ops": total_ops,
                    "ms": round((time.perf_counter() - t0) * 1000, 1)}

    if failure is None:
        # The suite passed - let the fuzzer look for what the suite missed.
        report = fuzz.diagnose(problem, source, n_cases=fuzz_cases, time_limit=4.0)
        if report.get("found"):
            result["verdict"] = "wrong" if report["status"] == "wrong" else report["status"]
            result["foundBy"] = "fuzzer"
            result["diagnosis"] = report
        else:
            result["verdict"] = "accepted"
    elif failure["status"] == "tle":
        result["verdict"] = "tle"
        result["failure"] = _slim(failure, problem)
    else:
        result["verdict"] = "wrong" if failure["status"] == "ok" else "error"
        result["failure"] = _slim(failure, problem)
        result["diagnosis"] = fuzz.diagnose(problem, source, args=failure["args"], time_limit=4.0)

    diag = result.get("diagnosis")
    if with_trace and diag and diag.get("found") and problem.measure(diag["args"]) <= 40:
        try:
            result["trace"] = trace_problem(problem, source, diag["args"], max_steps=800)
        except CompileError:
            pass
        if "trace" in result:
            try:
                diag["divergence"] = diverge.analyze(problem, source, diag["args"], result["trace"])
            except Exception:  # noqa: BLE001 - analysis is a bonus; never fail a verdict over it
                diag["divergence"] = None
    if result["verdict"] in ("accepted", "tle"):
        result["profile"] = complexity.profile(problem, source)
    return result


def _slim(failure, problem):
    """Large failing inputs are summarised; the diagnosis carries the small one."""
    out = dict(failure)
    size = problem.measure(failure["args"])
    if size > 60:
        out["args"] = None
        out["argsSummary"] = f"input of size {size:,}"
        if isinstance(out.get("expected"), list) and len(out["expected"]) > 60:
            out["expected"] = None
        if isinstance(out.get("output"), list) and len(out["output"]) > 60:
            out["output"] = None
    return out
