"""Data-quality gate for problem modules.

Every check here exists because content is code: a typo in a reference
solution, a generator that produces invalid inputs, or a pitfall detector that
fires on correct answers would silently teach the wrong thing. The build fails
on any `error`; `warn`s are printed for review.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass

from feetcode.analysis import parse_directives
from feetcode.complexity import RANK, profile
from feetcode.fuzz import Runner
from feetcode.problem import DIFFICULTIES, PATTERNS, Problem, compare
from feetcode.tracer import trace_problem

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
INSIGHT_KEYS = ("pattern", "oneLiner", "mnemonic", "why", "recall")
LENS_KEYS = {"arrays", "maps", "overlay", "stacks", "grids", "hide", "indexes", "nodes"}


@dataclass
class Issue:
    level: str      # error | warn
    problem: str
    check: str
    message: str

    def __str__(self):
        return f"[{self.level}] {self.problem} :: {self.check}: {self.message}"


class Checker:
    def __init__(self, problem: Problem, cases: int = 200, seed: int = 0):
        self.p = problem
        self.cases = cases
        self.seed = seed
        self.issues: list[Issue] = []
        self._runners: dict[str, Runner] = {}

    def err(self, check, msg):
        self.issues.append(Issue("error", self.p.id, check, msg))

    def warn(self, check, msg):
        self.issues.append(Issue("warn", self.p.id, check, msg))

    def runner(self, sol) -> Runner:
        if sol.id not in self._runners:
            self._runners[sol.id] = Runner(self.p, parse_directives(sol.code).code, budget=20_000_000)
        return self._runners[sol.id]

    # ------------------------------------------------------------------ #
    def run(self) -> list[Issue]:
        self.schema()
        if any(i.level == "error" for i in self.issues):
            return self.issues
        self.examples()
        self.agreement()
        self.lessons()
        self.pitfalls()
        return self.issues

    def schema(self):
        p = self.p
        if not SLUG.match(p.id):
            self.err("schema", f"id {p.id!r} is not a slug")
        if p.difficulty not in DIFFICULTIES:
            self.err("schema", f"difficulty {p.difficulty!r}")
        if p.pattern not in PATTERNS:
            self.err("schema", f"pattern {p.pattern!r}")
        if not p.statement.strip():
            self.err("schema", "empty statement")
        if not p.examples:
            self.err("schema", "no examples")
        if len(p.solutions) < 2:
            self.warn("schema", "only one solution - show the brute force too")
        if sum(1 for s in p.solutions if s.optimal) != 1:
            self.err("schema", "exactly one solution must be marked optimal")
        if len({s.id for s in p.solutions}) != len(p.solutions):
            self.err("schema", "duplicate solution ids")
        if len(p.hints) < 2:
            self.warn("schema", "fewer than 2 hints")
        missing = [k for k in INSIGHT_KEYS if not p.insight.get(k)]
        if missing:
            self.err("schema", f"insight missing {missing}")
        if not p.companies:
            self.warn("schema", "no company tags")
        if any(not (1 <= v <= 5) for v in p.companies.values()):
            self.err("schema", "company frequency must be 1..5")
        unknown = set(p.lens) - LENS_KEYS
        if unknown:
            self.err("schema", f"unknown lens keys {sorted(unknown)}")
        for s in p.solutions:
            d = parse_directives(s.code)
            try:
                compile(d.code, s.id, "exec")
            except SyntaxError as e:
                self.err("schema", f"solution {s.id} does not compile: {e}")
            for line, text in d.footnotes:
                if len(text) > 320:
                    self.warn("footnote", f"{s.id} line {line}: footnote is {len(text)} chars")

    def examples(self):
        p = self.p
        for i, ex in enumerate(p.examples):
            args = ex["args"]
            if not p.is_valid(args):
                self.err("examples", f"example {i} violates validate()")
            for s in p.solutions:
                r = self.runner(s).run(args)
                if not r["ok"]:
                    self.err("examples", f"{s.id} fails example {i}: {r.get('error')}")
                elif "output" in ex and not compare(p, args, ex["output"], r["output"]):
                    self.err("examples", f"{s.id} on example {i}: got {r['output']!r}, stated output {ex['output']!r}")
        for i, args in enumerate(p.edge_cases):
            if not p.is_valid(args):
                self.err("edge-cases", f"edge case {i} violates validate(): {args!r}"[:200])

    def agreement(self):
        """All reference solutions must agree with the optimal one on random inputs."""
        p = self.p
        rng = random.Random(self.seed)
        ref = self.runner(p.optimal)
        others = [s for s in p.solutions if not s.optimal]
        valid = 0
        inputs = list(p.edge_cases)
        for k in range(self.cases):
            n = k % 9 if k < self.cases * 0.7 else 5 + k % 30
            args = p.generate(rng, n)
            if p.is_valid(args):
                valid += 1
                inputs.append(args)
        if valid < self.cases * 0.8:
            self.warn("generator", f"only {valid}/{self.cases} generated inputs are valid")
        sizes = set()
        for args in inputs:
            r = ref.run(args)
            if not r["ok"]:
                self.err("agreement", f"optimal fails on {args!r}: {r.get('error')}"[:300])
                return
            sizes.add(p.measure(args))
            for s in others:
                o = self.runner(s).run(args)
                if not o["ok"] or not compare(p, args, r["output"], o["output"]):
                    got = o.get("output") if o["ok"] else o.get("error")
                    self.err("agreement", f"{s.id} disagrees with optimal on {args!r}: {got!r} vs {r['output']!r}"[:400])
                    return
        if len(sizes) < 3:
            self.warn("generator", f"generated inputs only cover sizes {sorted(sizes)}")

    def lessons(self):
        p = self.p
        args = p.lesson or p.examples[0]["args"]
        if not p.is_valid(args):
            self.err("lesson", "lesson input violates validate()")
        expected = self.runner(p.optimal).run(args)
        for s in p.solutions:
            tr = trace_problem(p, s.code, args, strict_narration=False, max_steps=4000)
            if tr.get("narrationErrors"):
                self.err("narration", f"{s.id}: {tr['narrationErrors'][:3]}")
            if tr["error"]:
                self.err("lesson", f"{s.id} errors while tracing: {tr['error']}")
            elif tr["truncated"]:
                self.err("lesson", f"{s.id} lesson trace is truncated - pick a smaller lesson input")
            elif expected["ok"] and not compare(p, args, expected["output"], tr["output"]):
                self.err("lesson", f"{s.id} traced output {tr['output']!r} != {expected['output']!r}")
            shown = [st for st in tr["steps"] if st.get("t") and not st.get("hide")]
            if s.optimal and len(shown) < 4:
                self.warn("lesson", f"{s.id}: only {len(shown)} narrated steps")
            if len(tr["steps"]) > 1500:
                self.warn("lesson", f"{s.id}: {len(tr['steps'])} raw steps (heavy JSON)")

    def pitfalls(self):
        """A pitfall detector must never fire on a correct answer."""
        p = self.p
        rng = random.Random(self.seed + 1)
        ref = self.runner(p.optimal)
        samples = [ex["args"] for ex in p.examples] + [p.generate(rng, n) for n in range(1, 12)]
        for args in samples:
            if not p.is_valid(args):
                continue
            r = ref.run(args)
            if not r["ok"]:
                continue
            for pf in p.pitfalls:
                if pf.detect is None:
                    continue
                try:
                    if pf.detect(args, r["output"], r["output"]):
                        self.err("pitfalls", f"{pf.id} fires on a correct answer for {args!r}"[:300])
                except Exception as e:  # noqa: BLE001
                    self.err("pitfalls", f"{pf.id} crashes: {type(e).__name__}: {e}")

    def complexity(self) -> dict:
        """Fit each solution's growth and compare with its declared complexity."""
        out = {}
        if not self.p.sizes:
            return out
        for s in self.p.solutions:
            pr = profile(self.p, parse_directives(s.code).code)
            out[s.id] = pr
            fitted = (pr.get("time") or {}).get("label")
            declared = _declared_rank(s.time)
            if declared is not None and self.p.signature.kind == "design":
                # declared per operation; the profile runs n operations
                times_n = {"O(1)": "O(n)", "O(log n)": "O(n log n)", "O(n)": "O(n²)", "O(n²)": "O(n³)"}
                label = next(k for k, v in RANK.items() if v == declared)
                declared = RANK.get(times_n.get(label, label))
            if fitted and declared is not None and RANK.get(fitted) is not None:
                if RANK[fitted] > declared:
                    self.warn("complexity", f"{s.id} declared {s.time} but measured {fitted}")
            if pr.get("stopped") and s.optimal:
                self.warn("complexity", f"{s.id} profile stopped early: {pr['stopped']}")
        return out


def _declared_rank(text: str):
    """Map a declared bound like 'O(n · k)' to the closest single-variable model rank."""
    t = text.replace(" ", "").replace("·", "").replace("*", "")
    if re.search(r"[a-mo-z]", t.replace("log", "").replace("O(", "")):
        return None  # multi-variable bounds like O(n · k) can't be judged from a 1-D profile
    table = [("O(1)", "O(1)"), ("O(logn)", "O(log n)"), ("O(nlogn)", "O(n log n)"), ("O(n²)", "O(n²)"),
             ("O(n^2)", "O(n²)"), ("O(n³)", "O(n³)"), ("O(2ⁿ)", "O(2ⁿ)")]
    for pat, label in table:
        if t == pat:
            return RANK[label]
    if re.fullmatch(r"O\(n\)", t):
        return RANK["O(n)"]
    if re.fullmatch(r"O\(n[a-z+]*\)", t) or re.fullmatch(r"O\([a-z]\)", t):
        return RANK["O(n)"]       # O(n + k), O(nk) treated as linear in the profiled size
    if "logk" in t or "logn" in t:
        return RANK["O(n log n)"]
    return None


def check(problem: Problem, cases: int = 200, with_complexity: bool = False):
    c = Checker(problem, cases=cases)
    issues = c.run()
    profiles = c.complexity() if with_complexity and not any(i.level == "error" for i in issues) else {}
    return c.issues, profiles
