"""Deterministic operation counting.

Feetcode's time limits are measured in *operations*, not milliseconds: one
operation per executed line of user code, plus the size-weighted hidden cost of
linear builtins (`x in some_list`, `list.pop(0)`, slicing...). The same code on
the same input always costs the same, on any machine, in any browser - so a
verdict is reproducible and a complexity curve has no noise.
"""
from __future__ import annotations

import sys

from .analysis import Program, Unsafe, probe_cost
from .harness import FILENAME

COMPREHENSION_FRAMES = {"<listcomp>", "<setcomp>", "<dictcomp>", "<genexpr>", "<lambda>"}


class BudgetExceeded(BaseException):
    """Raised inside user code when it runs out of operations.

    A BaseException so that `except Exception:` in user code cannot swallow it.
    """

    def __init__(self, ops, line):
        super().__init__(f"operation budget exceeded at line {line}")
        self.ops, self.line = ops, line


class Meter:
    def __init__(self, program: Program | None = None, budget: int | None = None,
                 line_hits: bool = False, probes: bool = True):
        self.budget = budget
        self.ops = 0
        self.hidden = 0
        self.calls = 0
        self.depth = 0
        self.max_depth = 0
        self.line_hits = line_hits
        self.hits: dict[int, int] = {}
        self.hidden_by_line: dict[int, int] = {}
        self._probes = {}
        if program is not None and probes:
            self._probes = {ln: info.probes for ln, info in program.lines.items() if info.probes}
        self._prev = None

    def __enter__(self):
        self._prev = sys.gettrace()
        sys.settrace(self._global)
        return self

    def __exit__(self, *exc):
        sys.settrace(self._prev)
        return False

    def _global(self, frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None
        if frame.f_code.co_name not in COMPREHENSION_FRAMES:
            self.calls += 1
            self.ops += 1
            self.depth += 1
            if self.depth > self.max_depth:
                self.max_depth = self.depth
        return self._local

    def _local(self, frame, event, arg):
        if event == "line":
            self.ops += 1
            ln = frame.f_lineno
            if self.line_hits:
                self.hits[ln] = self.hits.get(ln, 0) + 1
            probes = self._probes.get(ln)
            if probes:
                scope = frame.f_locals
                for p in probes:
                    try:
                        c = probe_cost(p, scope)
                    except Unsafe:
                        continue
                    if c:
                        self.ops += c
                        self.hidden += c
                        self.hidden_by_line[ln] = self.hidden_by_line.get(ln, 0) + c
            if self.budget is not None and self.ops > self.budget:
                raise BudgetExceeded(self.ops, ln)
        elif event == "return" and frame.f_code.co_name not in COMPREHENSION_FRAMES:
            self.depth -= 1
        return self._local
