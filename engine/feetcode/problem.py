"""The problem specification: everything Feetcode knows about one problem.

A problem module (problems/<pattern>/<slug>.py) defines `PROBLEM = Problem(...)`.
It is content *and* code: the statement and teaching material sit next to the
reference solutions, the input generator the fuzzer uses, the validity check
the shrinker respects, and the pitfall detectors that explain failures. The
pipeline turns it into static JSON for the client; the browser imports the
same module inside Pyodide to judge, fuzz and profile.
"""
from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from typing import Any, Callable

PATTERNS = {
    "arrays-hashing": "Arrays & Hashing",
    "two-pointers": "Two Pointers",
    "sliding-window": "Sliding Window",
    "stack": "Stack",
    "linked-list": "Linked List",
}

DIFFICULTIES = ("Easy", "Medium", "Hard")


@dataclass
class Param:
    name: str
    type: str


@dataclass
class Signature:
    method: str
    params: list
    returns: str
    kind: str = "function"      # function | design | codec
    cls: str = "Solution"       # class users define (design problems: e.g. "MinStack")
    inplace: str | None = None  # param whose post-call value is the answer (e.g. reorderList)


def sig(method: str, returns: str, *, kind="function", cls="Solution", inplace=None, **params) -> Signature:
    """sig("trap", "int", height="List[int]") - params keep keyword order."""
    return Signature(method, [Param(k, v) for k, v in params.items()], returns, kind, cls, inplace)


@dataclass
class Solution:
    id: str
    name: str
    time: str
    space: str
    code: str
    idea: str = ""
    optimal: bool = False


@dataclass
class Pitfall:
    """A known mistake, recognised from a failure by any of:
    `detect(args, expected, actual)` on a wrong answer, `error` (an exception type name
    raised by the user's code, optionally "Type: substring"), or `code` (a regex on the source)."""
    id: str
    title: str
    explain: str
    detect: Callable[[dict, Any, Any], bool] | None = None
    code: str | None = None
    error: str | None = None


@dataclass
class Problem:
    id: str
    number: int
    title: str
    difficulty: str
    pattern: str
    order: int
    signature: Signature
    statement: str
    examples: list
    solutions: list
    generate: Callable[[random.Random, int], dict]
    constraints: list = field(default_factory=list)
    companies: dict = field(default_factory=dict)
    topics: list = field(default_factory=list)
    hints: list = field(default_factory=list)
    insight: dict = field(default_factory=dict)
    pitfalls: list = field(default_factory=list)
    edge_cases: list = field(default_factory=list)
    validate: Callable[[dict], bool] | None = None
    compare: Any = "exact"
    lens: dict = field(default_factory=dict)
    lesson: dict | None = None
    sizes: list = field(default_factory=lambda: [16, 32, 64, 128, 256, 512, 1024])
    big: int = 3000
    worst_case: Callable[[int], dict] | None = None
    size_of: Callable[[dict], int] | None = None
    shrink: Callable[[dict], Any] | None = None
    prepare: Callable[[dict], list] | None = None
    extract: Callable[[Any, list, dict], Any] | None = None
    follow_up: str = ""
    related: list = field(default_factory=list)
    slug: str = ""

    @property
    def optimal(self) -> Solution:
        for s in self.solutions:
            if s.optimal:
                return s
        return self.solutions[-1]

    def is_valid(self, args: dict) -> bool:
        if self.validate is None:
            return True
        try:
            return bool(self.validate(args))
        except Exception:  # noqa: BLE001
            return False

    def measure(self, args: dict) -> int:
        if self.size_of is not None:
            return self.size_of(args)
        first = args[self.signature.params[0].name] if self.signature.params else None
        if isinstance(first, (list, str)):
            return len(first)
        if isinstance(first, int):
            return first
        if isinstance(args.get("ops"), list):
            return len(args["ops"])
        return 0


# --------------------------------------------------------------------------- #
# Comparators
# --------------------------------------------------------------------------- #

def _sort_any(xs):
    try:
        return sorted(xs)
    except TypeError:
        return sorted(xs, key=repr)


def compare(problem: Problem, args: dict, expected, actual) -> bool:
    mode = problem.compare
    if callable(mode):
        return bool(mode(args, expected, actual))
    if mode == "exact":
        return expected == actual
    if mode == "unordered":
        return isinstance(actual, list) and len(actual) == len(expected) and _sort_any(actual) == _sort_any(expected)
    if mode == "unordered_nested":
        if not isinstance(actual, list) or not all(isinstance(g, list) for g in actual):
            return False
        norm = lambda xs: _sort_any([_sort_any(g) for g in xs])  # noqa: E731
        return norm(actual) == norm(expected)
    if mode == "float":
        try:
            return abs(float(actual) - float(expected)) < 1e-5
        except (TypeError, ValueError):
            return False
    raise ValueError(f"unknown compare mode {mode!r}")


# --------------------------------------------------------------------------- #
# Generic shrinking (problems can override with their own `shrink`)
# --------------------------------------------------------------------------- #

def _shrink_int(v):
    seen = set()
    for c in (0, 1, v // 2, abs(v) if v < 0 else None, v - 1 if v > 0 else None, v + 1 if v < 0 else None):
        if c is not None and c != v and c not in seen and abs(c) <= abs(v):
            seen.add(c)
            yield c


def _shrink_list(v, depth=0):
    n = len(v)
    if n == 0:
        return
    yield []
    if n > 1:
        yield v[: n // 2]
        yield v[n // 2:]
    for i in range(n - 1, -1, -1):
        yield v[:i] + v[i + 1:]
    if depth < 2:
        for i in range(n):
            for c in shrink_value(v[i], depth + 1):
                yield v[:i] + [c] + v[i + 1:]


def _shrink_str(v):
    n = len(v)
    if n == 0:
        return
    yield ""
    if n > 1:
        yield v[: n // 2]
        yield v[n // 2:]
    for i in range(n - 1, -1, -1):
        yield v[:i] + v[i + 1:]
    for i in range(n):
        if v[i] != "a":
            yield v[:i] + "a" + v[i + 1:]


def shrink_value(v, depth=0):
    if isinstance(v, bool):
        if v:
            yield False
    elif isinstance(v, int):
        yield from _shrink_int(v)
    elif isinstance(v, str):
        yield from _shrink_str(v)
    elif isinstance(v, list):
        yield from _shrink_list(v, depth)


def shrink_args(problem: Problem, args: dict):
    """Candidate inputs strictly 'smaller' than args, most aggressive first."""
    if problem.shrink is not None:
        yield from problem.shrink(args)
        return
    if problem.signature.kind == "design":
        ops, argv = args["ops"], args["args"]
        for i in range(len(ops) - 1, 0, -1):
            yield {"ops": ops[:i] + ops[i + 1:], "args": argv[:i] + argv[i + 1:]}
        for i in range(1, len(ops)):
            for j, a in enumerate(argv[i]):
                for c in shrink_value(a):
                    new = [list(x) for x in argv]
                    new[i][j] = c
                    yield {"ops": ops, "args": new}
        return
    for p in problem.signature.params:
        for c in shrink_value(args[p.name]):
            yield {**args, p.name: c}


# --------------------------------------------------------------------------- #
# Generator helpers for problem modules
# --------------------------------------------------------------------------- #

def ints(rng: random.Random, n: int, lo: int, hi: int) -> list:
    return [rng.randint(lo, hi) for _ in range(n)]


def word(rng: random.Random, n: int, alphabet: str = string.ascii_lowercase) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


def small_alphabet(rng: random.Random, n: int) -> str:
    """Skewed alphabets find more bugs: repeats and collisions are common."""
    k = rng.choice((2, 3, 4, 26))
    return string.ascii_lowercase[:k]
