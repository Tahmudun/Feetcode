from feetcode.analysis import parse_directives
from feetcode.tracer import trace_problem, trace_script

from helpers import REVERSE, SUM, STACK


def lines(trace, kind=None):
    return [s["l"] for s in trace["steps"] if kind is None or s["k"] == kind]


def local(step, name, frame=-1):
    return dict(step["s"][frame]["v"]).get(name)


def test_one_step_per_statement_and_branches():
    code = """class Solution:
    def total(self, nums):
        t = 0
        for x in nums:
            if x > 0:
                t += x
        return t
"""
    tr = trace_problem(SUM, code, {"nums": [2, -1]})
    assert tr["output"] == 2
    assert tr["error"] is None
    assert lines(tr) == [2, 3, 4, 5, 6, 4, 5, 4, 7]
    ifs = [s for s in tr["steps"] if s["l"] == 5]
    assert [s["b"] for s in ifs] == [1, 0]                 # 2 > 0 entered, -1 > 0 skipped
    fors = [s for s in tr["steps"] if s["l"] == 4]
    assert [s["b"] for s in fors] == [1, 1, 0]             # third visit: loop exhausted
    assert tr["steps"][-1]["k"] == "return" and tr["steps"][-1]["r"] == 2


def test_multiline_statement_is_one_step():
    code = """class Solution:
    def total(self, nums):
        t = max(0,
                sum(nums))
        return t
"""
    tr = trace_problem(SUM, code, {"nums": [1, 2]})
    assert lines(tr) == [2, 3, 5]


def test_comprehension_collapses_but_one_line_loop_iterates():
    code = """class Solution:
    def total(self, nums):
        sq = [x for x in nums if x > 0]
        i = 0
        while i < 3: i += 1
        return sum(sq) + i - 3
"""
    tr = trace_problem(SUM, code, {"nums": [1, 2, 3, 4]})
    assert lines(tr).count(3) == 1
    # CPython 3.12+ duplicates the loop test at the bottom, so a one-line loop reports
    # one event per backward jump: the first test plus one per repeated iteration.
    assert lines(tr).count(5) in (3, 4)
    assert tr["output"] == 10


def test_identity_is_preserved_for_linked_lists():
    tr = trace_problem(REVERSE, REVERSE.optimal.code, {"head": [1, 2, 3]})
    assert tr["output"] == [3, 2, 1]
    # After `prev, curr = curr, nxt` in the first iteration, prev is the old head node.
    step = next(s for s in tr["steps"] if s["l"] == 7)
    prev, head = local(step, "prev"), local(step, "head")
    assert prev == head and "r" in prev                     # same object id, not a copy
    writes = [a for s in tr["steps"] for a in s.get("a", []) if a.get("f") == "next"]
    assert len(writes) == 3 and all(a["m"] == "w" for a in writes)


def test_accesses_compare_and_oob():
    code = """class Solution:
    def total(self, nums):
        i = 0
        if nums[i] < nums[i + 1]:
            return nums[i + 5]
        return 0
"""
    tr = trace_problem(SUM, code, {"nums": [1, 2]})
    cmp_step = next(s for s in tr["steps"] if s["l"] == 4)
    assert [(a["i"], a["m"]) for a in cmp_step["a"]] == [(0, "c"), (1, "c")]
    assert tr["error"]["type"] == "IndexError" and tr["error"]["line"] == 5
    exc = [s for s in tr["steps"] if s["k"] == "exc"]
    assert exc and exc[0]["l"] == 5
    oob = [a for s in tr["steps"] for a in s.get("a", []) if a.get("oob")]
    assert oob and oob[0]["i"] == 5
    assert not any(s["k"] == "return" for s in tr["steps"])  # unwinding isn't a return


def test_recursion_shows_whole_stack():
    code = """class Solution:
    def total(self, nums):
        def go(i):
            if i == len(nums):
                return 0
            return nums[i] + go(i + 1)
        return go(0)
"""
    tr = trace_problem(SUM, code, {"nums": [5, 6]})
    assert tr["output"] == 11
    depths = [len(s["s"]) for s in tr["steps"]]
    assert max(depths) == 4                                 # total + go(0) + go(1) + go(2)
    assert sum(1 for s in tr["steps"] if s["k"] == "call") == 4


def test_infinite_loop_is_stopped_even_if_user_catches_exceptions():
    code = """class Solution:
    def total(self, nums):
        while True:
            try:
                pass
            except Exception:
                pass
"""
    tr = trace_problem(SUM, code, {"nums": [1]}, max_steps=50)
    assert tr["truncated"] is True
    assert len(tr["steps"]) == 50


def test_narration_and_footnotes_from_directives():
    code = """class Solution:
    def total(self, nums):
        t = 0  #> start at {t}
        for x in nums:  #~
            t += x  #> add {x} -> {t} #! accumulate
        return t  #> done: {!str(_return)}
"""
    tr = trace_problem(SUM, code, {"nums": [4, 5]}, strict_narration=True)
    narr = [s.get("t") for s in tr["steps"] if s.get("t")]
    assert narr == ["start at 0", "add 4 -> 4", "add 5 -> 9", "done: 9"]
    assert tr["footnotes"] == [{"line": 5, "text": "accumulate"}]
    assert all(s.get("hide") == 1 for s in tr["steps"] if s["l"] == 4)
    assert "#" not in tr["code"].split("\n")[2]


def test_narration_errors_are_reported():
    d = parse_directives("class Solution:\n    def total(self, nums):\n        return 1  #> {missing}\n")
    tr = trace_problem(SUM, "", {"nums": []}, directives=d)
    assert tr["narrationErrors"]


def test_design_problem_traces_every_method_call():
    tr = trace_problem(STACK, STACK.optimal.code, STACK.examples[0]["args"])
    assert tr["output"] == [None, None, None, 2, None, 1]
    calls = [s["s"][-1]["f"] for s in tr["steps"] if s["k"] == "call"]
    assert calls == ["__init__", "push", "push", "top", "pop", "top"]
    pushes = [a for s in tr["steps"] for a in s.get("a", []) if a["m"] == "push"]
    assert [a["v"] for a in pushes] == ["self.items", "self.items"]


def test_stdout_is_captured_with_positions():
    tr = trace_problem(SUM, "class Solution:\n    def total(self, nums):\n        print('hi')\n        return 0\n",
                       {"nums": []})
    assert tr["stdout"] == "hi\n"
    assert tr["steps"][-1]["o"] == 3


def test_playground_traces_module_level_code():
    tr = trace_script("xs = [3, 1, 2]\nxs.sort()\ntotal = sum(xs)\nprint(total)\n")
    assert tr["error"] is None
    last = tr["steps"][-1]
    names = [n for n, _ in last["s"][0]["v"]]
    assert names == ["xs", "total"]                         # prelude names are hidden
    assert tr["stdout"] == "6\n"
