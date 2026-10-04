"""Property-based testing against the reference solution, with shrinking.

    generate -> run user + reference -> disagree? -> shrink to a minimal input
             -> find a passing neighbour one edit away -> match known pitfalls

This is the QuickCheck/Hypothesis recipe applied to interview problems. The
shrinker is greedy delta-debugging: try strictly smaller candidates (drop
halves, drop single elements, shrink numbers toward 0), keep any that still
fail *and* still satisfy the problem's constraints, repeat until nothing
smaller fails. Most bugs end up as a 1-3 element counterexample a human can
reason about at a glance.
"""
from __future__ import annotations

import random
import re
import sys
import time

from .harness import (BoundedIO, CompileError, EntryError, OutputError, compile_user, describe_error,
                      fresh_namespace, prepare)
from .meter import BudgetExceeded, Meter
from .problem import Problem, compare, shrink_args, shrink_value

SMALL_BUDGET = 200_000


class Runner:
    """Runs one piece of code on many inputs (fresh namespace each time)."""

    def __init__(self, problem: Problem, source: str, budget: int = SMALL_BUDGET):
        self.problem = problem
        self.code_obj = compile_user(source)
        self.budget = budget

    def run(self, args: dict) -> dict:
        out = BoundedIO(limit=2000)
        old = sys.stdout
        meter = Meter(None, budget=self.budget, probes=False)
        try:
            ns = fresh_namespace(self.code_obj)
            run, finish = prepare(self.problem, ns, args)
            sys.stdout = out
            try:
                with meter:
                    raw = run()
            finally:
                sys.stdout = old
            return {"ok": True, "output": finish(raw), "ops": meter.ops}
        except BudgetExceeded as e:
            return {"ok": False, "status": "tle", "error": {"type": "TimeLimit", "message":
                    f"no answer after {e.ops:,} operations - likely an infinite loop", "line": e.line}}
        except (EntryError, OutputError) as e:
            return {"ok": False, "status": "error", "error": {"type": type(e).__name__, "message": str(e), "line": None}}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "status": "error", "error": describe_error(e)}


def _verdict(problem, args, ref_res, user_res) -> bool:
    """True when the user's run counts as correct."""
    if not ref_res["ok"]:
        return True  # reference failed: input out of scope, don't blame the user
    if not user_res["ok"]:
        return False
    return compare(problem, args, ref_res["output"], user_res["output"])


def _sizes(n_cases):
    # Mostly tiny inputs (where bugs are easy to see), occasionally medium.
    for k in range(n_cases):
        if k < n_cases * 0.6:
            yield k % 7
        elif k < n_cases * 0.9:
            yield 3 + k % 12
        else:
            yield 10 + k % 40


def find_failure(problem: Problem, user: Runner, ref: Runner, n_cases=250, seed=1, deadline=None):
    rng = random.Random(seed)
    for n in _sizes(n_cases):
        if deadline is not None and time.perf_counter() > deadline:
            return None
        args = problem.generate(rng, n)
        if not problem.is_valid(args):
            continue
        r, u = ref.run(args), user.run(args)
        if not _verdict(problem, args, r, u):
            return args
    return None


def _failure_kind(res):
    return "ok" if res["ok"] else res.get("status", "error")


def shrink(problem: Problem, user: Runner, ref: Runner, args: dict, max_tries=600, deadline=None):
    """Greedy shrink: returns (minimal_args, steps_taken)."""
    def fails(a):
        if not problem.is_valid(a):
            return False
        r, u = ref.run(a), user.run(a)
        return not _verdict(problem, a, r, u)

    current, steps, tries = args, 0, 0
    improved = True
    while improved and tries < max_tries:
        improved = False
        for cand in shrink_args(problem, current):
            tries += 1
            if tries >= max_tries or (deadline is not None and time.perf_counter() > deadline):
                break
            if fails(cand):
                current, steps, improved = cand, steps + 1, True
                break
    return current, steps


def _neighbours(problem: Problem, args: dict):
    """Inputs one small edit away from args (bigger or sideways, not just smaller)."""
    if problem.signature.kind == "design":
        return
    for p in problem.signature.params:
        v = args[p.name]
        if isinstance(v, list) and v and all(isinstance(x, int) and not isinstance(x, bool) for x in v):
            for i in range(len(v)):
                for d in (1, -1, 2):
                    yield {**args, p.name: v[:i] + [v[i] + d] + v[i + 1:]}
            if len(v) > 1:
                for i in range(len(v) - 1):
                    yield {**args, p.name: v[:i] + [v[i + 1], v[i]] + v[i + 2:]}
        elif isinstance(v, str) and v:
            for i in range(len(v)):
                for ch in "abz ":
                    if ch != v[i]:
                        yield {**args, p.name: v[:i] + ch + v[i + 1:]}
        elif isinstance(v, int) and not isinstance(v, bool):
            yield {**args, p.name: v + 1}
            yield {**args, p.name: v - 1}
        for c in shrink_value(v):
            yield {**args, p.name: c}


def passing_neighbour(problem: Problem, user: Runner, ref: Runner, args: dict, limit=80):
    for k, cand in enumerate(_neighbours(problem, args)):
        if k >= limit:
            break
        if not problem.is_valid(cand):
            continue
        r, u = ref.run(cand), user.run(cand)
        if r["ok"] and u["ok"] and compare(problem, cand, r["output"], u["output"]):
            return {"args": cand, "output": u["output"]}
    return None


def _error_matches(spec: str, error: dict | None) -> bool:
    if not error:
        return False
    kind, _, needle = spec.partition(":")
    return error.get("type") == kind.strip() and needle.strip().lower() in (error.get("message") or "").lower()


def match_pitfalls(problem: Problem, source: str, args, expected, actual, error: dict | None = None) -> list:
    found = []
    for p in problem.pitfalls:
        hit = bool(p.error) and _error_matches(p.error, error)
        if not hit and p.detect is not None and actual is not None:
            try:
                hit = bool(p.detect(args, expected, actual))
            except Exception:  # noqa: BLE001
                hit = False
        if not hit and p.code and re.search(p.code, source, re.MULTILINE):
            hit = True
        if hit:
            found.append({"id": p.id, "title": p.title, "explain": p.explain})
    return found


def diagnose(problem: Problem, source: str, args: dict | None = None, *, seed=1, time_limit=6.0,
             n_cases=250) -> dict:
    """Find (or start from) a failing input, shrink it, and explain it."""
    deadline = time.perf_counter() + time_limit
    try:
        user = Runner(problem, source)
    except CompileError as e:
        return {"found": False, "compileError": e.to_json()}
    ref = Runner(problem, problem.optimal.code, budget=2_000_000)
    origin = "test"
    if args is None:
        origin = "fuzz"
        args = find_failure(problem, user, ref, n_cases=n_cases, seed=seed, deadline=deadline)
        if args is None:
            return {"found": False}
    original_size = problem.measure(args)
    minimal, steps = shrink(problem, user, ref, args, deadline=deadline + 2.0)
    r, u = ref.run(minimal), user.run(minimal)
    expected = r.get("output")
    actual = u.get("output") if u["ok"] else None
    report = {
        "found": True,
        "origin": origin,
        "args": minimal,
        "expected": expected,
        "actual": actual,
        "status": _failure_kind(u) if not u["ok"] else "wrong",
        "error": u.get("error"),
        "originalSize": original_size,
        "size": problem.measure(minimal),
        "shrinkSteps": steps,
        "pitfalls": match_pitfalls(problem, source, minimal, expected, actual, u.get("error")),
    }
    if time.perf_counter() < deadline + 3.0:
        report["neighbour"] = passing_neighbour(problem, user, ref, minimal)
    return report
