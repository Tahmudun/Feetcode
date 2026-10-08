"""Divergence finder + invariant miner, on real problems from the content bank."""
import importlib

from feetcode import diverge, judge
from feetcode.tracer import trace_problem

from helpers import STACK


def load(module):
    return importlib.import_module(module).PROBLEM


LONGEST = load("problems.sliding_window.longest_substring_without_repeating")
TWO_SUM = load("problems.arrays_hashing.two_sum")
RAIN = load("problems.two_pointers.trapping_rain_water")

# The classic bug: jump l to the last occurrence without checking it is inside the window.
BACKWARDS_L = """class Solution:
    def lengthOfLongestSubstring(self, s):
        seen = {}
        l = best = 0
        for r, c in enumerate(s):
            if c in seen:
                l = seen[c] + 1
            seen[c] = r
            best = max(best, r - l + 1)
        return best
"""

INSERT_BEFORE_CHECK = """class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            seen[n] = i
            if target - n in seen:
                return [seen[target - n], i]
"""

SUBTRACT_BEFORE_MAX = """class Solution:
    def trap(self, height):
        l, r = 0, len(height) - 1
        max_l, max_r = height[l], height[r]
        water = 0
        while l < r:
            if max_l < max_r:
                l += 1
                water += max_l - height[l]
                max_l = max(max_l, height[l])
            else:
                r -= 1
                water += max_r - height[r]
                max_r = max(max_r, height[r])
        return water
"""


def test_finds_the_step_where_l_moves_backwards():
    d = diverge.analyze(LONGEST, BACKWARDS_L, {"s": "tmmt"})
    assert d["solution"] == "last-seen"          # the reference that agrees longest: same approach
    assert d["var"] == "l" and d["line"] == 7
    assert (d["yours"], d["ref"]) == ("1", "2")
    assert {"l", "best", "r"} <= set(d["shared"])
    inv = d["invariant"]
    assert inv["kind"] == "nondecreasing" and inv["vars"] == ["l"]
    assert inv["step"] == d["step"] and (inv["before"], inv["after"]) == ("2", "1")


def test_reports_an_early_return_with_both_answers():
    d = diverge.analyze(TWO_SUM, INSERT_BEFORE_CHECK, {"nums": [5, 5], "target": 10})
    assert d["kind"] == "return" and d["line"] == 7
    assert (d["yours"], d["ref"]) == ("[0, 0]", "[0, 1]")


def test_a_value_the_reference_never_takes_and_the_invariant_it_breaks():
    d = diverge.analyze(RAIN, SUBTRACT_BEFORE_MAX, {"height": [1, 0]})
    assert d["var"] == "water" and d["yours"] == "-1" and d["line"] == 13
    assert d["invariant"]["text"] == "water never decreases"


def test_correct_code_agrees_with_its_reference():
    for sol in LONGEST.solutions:
        d = diverge.analyze(LONGEST, sol.code, {"s": "abcabcbb"})
        assert d["kind"] == "agree" and d["invariant"] is None


def test_nothing_to_compare_without_shared_variables():
    renamed = """class Solution:
    def lengthOfLongestSubstring(self, s):
        window_start = longest = 0
        for idx in range(len(s)):
            pass
        return longest
"""
    assert diverge.analyze(LONGEST, renamed, {"s": "abc"}) is None


def test_design_problems_are_out_of_scope():
    assert diverge.analyze(STACK, STACK.solutions[0].code, STACK.examples[0]["args"]) is None


def test_a_crash_is_reported_where_it_happens():
    crashes = BACKWARDS_L.replace("l = seen[c] + 1", "l = seen[c] + 1 // 0")
    d = diverge.analyze(LONGEST, crashes, {"s": "tmmt"})
    assert d["kind"] == "error" and d["yours"] == "ZeroDivisionError" and d["line"] == 7


def test_canonical_values_ignore_identity_and_dict_order():
    a = trace_problem(TWO_SUM, "class Solution:\n    def twoSum(self, nums, target):\n        x = {1: 2, 3: 4}\n        return [0, 1]\n",
                      {"nums": [1, 2], "target": 3})
    b = trace_problem(TWO_SUM, "class Solution:\n    def twoSum(self, nums, target):\n        x = {3: 4, 1: 2}\n        return [0, 1]\n",
                      {"nums": [1, 2], "target": 3})
    ha, hb = diverge.histories(a), diverge.histories(b)
    assert ha["x"][0][1] == hb["x"][0][1]
    assert diverge.show(ha["x"][0][1]) == "{1: 2, 3: 4}"


def test_only_pairs_the_reference_compares_become_order_invariants():
    assert diverge.compared_pairs("while l < r:\n    if a >= b and x == y: pass\n") == {("l", "r"), ("a", "b")}


def test_submit_attaches_the_divergence_to_the_diagnosis():
    suite = [{"args": {"s": "abc"}, "expected": 3}, {"args": {"s": "tmmzuxt"}, "expected": 5}]
    res = judge.submit(LONGEST, BACKWARDS_L, suite)
    div = res["diagnosis"]["divergence"]
    assert res["verdict"] == "wrong" and div["var"] == "l"
    assert res["trace"]["steps"][div["step"]]["l"] == div["line"]
    assert div["trace"]["steps"], "the reference trace ships with it, for side-by-side tracks"
