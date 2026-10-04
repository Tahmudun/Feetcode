"""Build stages: one problem module in, JSON artifacts out.

Every stage is a pure function of (problem source, engine source), so builds
are deterministic: the same inputs always produce byte-identical outputs.
That property is what makes the incremental cache and the CI drift check sound.
"""
from __future__ import annotations

import ast
import hashlib
import random

from feetcode import judge
from feetcode.analysis import Program, parse_directives
from feetcode.complexity import profile
from feetcode.harness import compile_user
from feetcode.problem import PATTERNS, Problem, compare
from feetcode.tracer import trace_problem

LARGE_BUDGET = 50_000_000      # references get effectively unlimited operations
BUDGET_FACTOR = 20             # user budget = factor × optimal reference ops ...
BUDGET_FLOOR = 25_000          # ... but never below this (tiny inputs, constant overheads)
SMALL_CASES, MEDIUM_CASES = 30, 10


def seed_for(problem_id: str) -> int:
    return int(hashlib.sha256(problem_id.encode()).hexdigest()[:8], 16)


# --------------------------------------------------------------------------- #
# Starter code
# --------------------------------------------------------------------------- #

LISTNODE_HEADER = """# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
"""

RANDOM_NODE_HEADER = """# Definition for a Node.
# class Node:
#     def __init__(self, x: int, next: 'Node' = None, random: 'Node' = None):
#         self.val = int(x)
#         self.next = next
#         self.random = random
"""


def _def_line(fn: ast.FunctionDef) -> str:
    ret = f" -> {ast.unparse(fn.returns)}" if fn.returns is not None else ""
    return f"def {fn.name}({ast.unparse(fn.args)}){ret}:"


def starter_code(problem: Problem) -> str:
    """LeetCode-style skeleton derived from the optimal solution's class."""
    sg = problem.signature
    tree = ast.parse(parse_directives(problem.optimal.code).code)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == sg.cls)
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
    if sg.kind == "function":
        methods = [m for m in methods if m.name == sg.method]
    else:
        methods = [m for m in methods if not m.name.startswith("_") or m.name == "__init__"]
    lines = [f"class {sg.cls}:"]
    for i, m in enumerate(methods):
        if i:
            lines.append("")
        lines.append(f"    {_def_line(m)}")
        lines.append("        " if sg.kind == "function" else "        pass")
    header = ""
    types = " ".join(p.type for p in sg.params) + " " + sg.returns
    if "ListNode" in types:
        header = LISTNODE_HEADER
    elif "Node" in types:
        header = RANDOM_NODE_HEADER
    return header + "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Problem detail
# --------------------------------------------------------------------------- #

def _example_output(problem: Problem, args: dict):
    from feetcode.fuzz import Runner
    r = Runner(problem, parse_directives(problem.optimal.code).code, budget=LARGE_BUDGET).run(args)
    return r["output"]


def summary(problem: Problem, module: str) -> dict:
    return {
        "id": problem.id,
        "number": problem.number,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "pattern": problem.pattern,
        "order": problem.order,
        "companies": problem.companies,
        "topics": problem.topics,
        "module": module,
        "kind": problem.signature.kind,
        "oneLiner": problem.insight.get("oneLiner", ""),
        "optimal": {"time": problem.optimal.time, "space": problem.optimal.space},
    }


def detail(problem: Problem, module: str) -> dict:
    sg = problem.signature
    examples = []
    for ex in problem.examples:
        out = ex["output"] if "output" in ex else _example_output(problem, ex["args"])
        examples.append({"args": ex["args"], "output": out, "explain": ex.get("explain", "")})
    solutions = []
    for s in problem.solutions:
        d = parse_directives(s.code)
        solutions.append({
            "id": s.id, "name": s.name, "time": s.time, "space": s.space, "idea": s.idea,
            "optimal": s.optimal, "code": d.code,
            "footnotes": [{"line": ln, "text": t} for ln, t in d.footnotes],
        })
    return {
        **summary(problem, module),
        "slug": problem.slug or problem.id,
        "url": f"https://leetcode.com/problems/{problem.slug or problem.id}/",
        "patternName": PATTERNS[problem.pattern],
        "statement": problem.statement.strip(),
        "examples": examples,
        "constraints": problem.constraints,
        "hints": problem.hints,
        "insight": problem.insight,
        "solutions": solutions,
        "pitfalls": [{"id": p.id, "title": p.title, "explain": p.explain} for p in problem.pitfalls],
        "signature": {
            "kind": sg.kind, "method": sg.method, "cls": sg.cls, "returns": sg.returns, "inplace": sg.inplace,
            "params": [{"name": p.name, "type": p.type} for p in sg.params],
            "inputs": list(problem.examples[0]["args"].keys()),
        },
        "starter": starter_code(problem),
        "lens": problem.lens,
        "followUp": problem.follow_up,
        "related": problem.related,
        "sizes": problem.sizes,
        "lessonArgs": problem.lesson or problem.examples[0]["args"],
    }


# --------------------------------------------------------------------------- #
# Hidden test suite
# --------------------------------------------------------------------------- #

def suite(problem: Problem) -> dict:
    """Deterministic test cases with expected outputs and per-case operation budgets."""
    rng = random.Random(seed_for(problem.id))
    candidates: list[tuple[str, dict]] = [("example", ex["args"]) for ex in problem.examples]
    candidates += [("edge", a) for a in problem.edge_cases]
    for k in range(SMALL_CASES):
        candidates.append(("random", problem.generate(rng, k % 11)))
    for k in range(MEDIUM_CASES):
        candidates.append(("random", problem.generate(rng, 12 + k * 6)))
    if problem.sizes:  # fixed-size problems (Sudoku) have no "large"
        candidates.append(("large", problem.generate(rng, problem.big)))
        if problem.worst_case is not None:
            candidates.append(("stress", problem.worst_case(problem.big)))

    optimal = parse_directives(problem.optimal.code).code
    code_obj, program = compile_user(optimal), Program(optimal)
    seen, cases = set(), []
    for kind, args in candidates:
        key = repr(args)
        if key in seen or not problem.is_valid(args):
            continue
        seen.add(key)
        res = judge.run_case(problem, code_obj, program, args, LARGE_BUDGET)
        if res["status"] != "ok":
            raise RuntimeError(f"{problem.id}: optimal solution failed a generated case ({res.get('error')})")
        budget = max(BUDGET_FLOOR, BUDGET_FACTOR * res["ops"])
        cases.append({"kind": kind, "args": args, "expected": res["output"], "budget": budget, "refOps": res["ops"]})
    return {"id": problem.id, "cases": cases}


def reference_verdicts(problem: Problem, cases: list) -> dict:
    """How each reference solution fares on the suite - a sanity check on the budgets."""
    out = {}
    for s in problem.solutions:
        code = parse_directives(s.code).code
        code_obj, program = compile_user(code), Program(code)
        verdict, failed_at = "accepted", None
        for i, c in enumerate(cases):
            res = judge.run_case(problem, code_obj, program, c["args"], c["budget"])
            if res["status"] == "tle":
                verdict, failed_at = "tle", i
                break
            if res["status"] != "ok" or not compare(problem, c["args"], c["expected"], res["output"]):
                verdict, failed_at = "wrong", i
                break
        out[s.id] = {"verdict": verdict, "case": failed_at}
    return out


# --------------------------------------------------------------------------- #
# Lessons and baselines
# --------------------------------------------------------------------------- #

def lessons(problem: Problem) -> dict:
    args = problem.lesson or problem.examples[0]["args"]
    traces = {}
    for s in problem.solutions:
        tr = trace_problem(problem, s.code, args, max_steps=3000, strict_narration=True)
        traces[s.id] = {k: tr[k] for k in ("code", "steps", "truncated", "output", "returned", "footnotes", "error", "stdout")
                        if k in tr}
    return {"id": problem.id, "args": args, "traces": traces}


def baselines(problem: Problem) -> dict:
    """Operation-count growth of every reference solution (deterministic: no timings)."""
    if not problem.sizes:
        return {"id": problem.id, "sizes": [], "solutions": {}}
    out = {}
    for s in problem.solutions:
        pr = profile(problem, parse_directives(s.code).code)
        out[s.id] = {
            "points": [{"n": p["n"], "ops": p.get("ops"), "capped": p.get("capped", False)} for p in pr["points"]],
            "time": (pr.get("time") or {}).get("label"),
            "slope": (pr.get("time") or {}).get("slope"),
            "space": (pr.get("space") or {}).get("label"),
        }
    return {"id": problem.id, "sizes": problem.sizes, "solutions": out}
