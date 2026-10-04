import collections
import math
import random

import pytest

from feetcode import complexity, fuzz, judge
from feetcode.analysis import Program, Unsafe, parse_directives, probe_cost, render_template, safe_eval
from feetcode.meter import BudgetExceeded, Meter
from feetcode.harness import compile_user, fresh_namespace, prepare
from feetcode.problem import compare, shrink_args
from feetcode.structures import ListNode, to_cycle_list, from_list, CycleError
from feetcode.values import Encoder

from helpers import CODEC, REVERSE, STACK, SUM

import ast


# --------------------------------------------------------------------------- values
def test_encoder_inlines_scalars_and_references_containers():
    enc = Encoder()
    pairs, heap = enc.snapshot([("a", 1), ("s", "hi"), ("f", 1.0), ("n", None), ("xs", [1, [2]])])
    vals = dict(pairs)
    assert vals["a"] == 1 and vals["s"] == "hi" and vals["f"] == {"f": "1.0"} and vals["n"] is None
    outer = heap[str(vals["xs"]["r"])]
    assert outer[0] == "list" and outer[1][0] == 1 and "r" in outer[1][1]


def test_encoder_preserves_aliasing_and_cycles():
    a = ListNode(1)
    a.next = a
    enc = Encoder()
    pairs, heap = enc.snapshot([("x", a), ("y", a)])
    assert pairs[0][1] == pairs[1][1]
    node = heap[str(pairs[0][1]["r"])]
    assert node[0] == "obj" and node[1] == "ListNode"
    assert dict(node[2])["next"] == pairs[0][1]            # self loop, encoded once


def test_encoder_ids_are_stable_across_snapshots():
    enc = Encoder()
    xs = [1]
    p1, _ = enc.snapshot([("xs", xs)])
    xs.append(2)
    p2, h2 = enc.snapshot([("xs", xs)])
    assert p1[0][1] == p2[0][1] and h2[str(p2[0][1]["r"])][1] == [1, 2]


def test_encoder_truncates_and_tags_dict_subtypes():
    enc = Encoder()
    pairs, heap = enc.snapshot([("big", list(range(1000))), ("c", collections.Counter("aab"))])
    big = heap[str(pairs[0][1]["r"])]
    assert len(big[1]) == 160 and big[2] == 1000
    counter = heap[str(pairs[1][1]["r"])]
    assert counter[0] == "dict" and counter[-1] == "Counter"


# --------------------------------------------------------------------------- analysis
def _expr(src):
    return ast.parse(src, mode="eval").body


def test_safe_eval_allows_pure_expressions():
    scope = {"a": [5, 6, 7], "i": 1, "d": {"k": 3}}
    assert safe_eval(_expr("a[i + 1]"), scope) == 7
    assert safe_eval(_expr("a[-1]"), scope) == 7
    assert safe_eval(_expr("d['k'] * 2"), scope) == 6
    assert safe_eval(_expr("len(a) - 1"), scope) == 2


@pytest.mark.parametrize("src", ["a.append(1)", "f()", "a[i:]", "d['missing']", "undefined", "[x for x in a]"])
def test_safe_eval_refuses_side_effects_and_unknowns(src):
    scope = {"a": [1], "i": 0, "d": {}, "f": lambda: 1}
    with pytest.raises(Unsafe):
        safe_eval(_expr(src), scope)
    assert scope["a"] == [1]


def test_safe_eval_never_triggers_defaultdict_missing():
    d = collections.defaultdict(list)
    with pytest.raises(Unsafe):
        safe_eval(_expr("d['x']"), {"d": d})
    assert "x" not in d


def test_program_maps_continuation_lines_to_their_statement():
    p = Program("x = (1 +\n     2)\nif x:\n    y = 1\n")
    assert p.statement(2) == 1 and p.statement(1) == 1
    assert p.lines[3].body == 4


def test_probe_costs_reflect_runtime_types():
    p = Program("if x in seen:\n    pass\nseen.pop(0)\nys = xs[2:8]\nzs = sorted(xs)\n")
    member = p.lines[1].probes[0]
    assert probe_cost(member, {"x": 1, "seen": [0] * 50}) == 50
    assert probe_cost(member, {"x": 1, "seen": set(range(50))}) == 0   # sets are O(1)
    assert probe_cost(p.lines[3].probes[0], {"seen": [0] * 10}) == 9
    assert probe_cost(p.lines[4].probes[0], {"xs": list(range(20))}) == 6
    assert probe_cost(p.lines[5].probes[0], {"xs": list(range(16))}) == 64


def test_probe_costs_see_through_size_preserving_wrappers():
    # safe_eval refuses calls; without this an O(n log n) sort of set(nums) would cost nothing
    p = Program("a = sorted(set(xs))\nb = sorted(d.items())\nc = sum(d.values())\ne = sorted(zip(xs, ys))\n")
    scope = {"xs": list(range(16)), "ys": list(range(8)), "d": dict.fromkeys(range(32))}
    sort_of = lambda line: next(q for q in p.lines[line].probes if q.kind == "sort")
    assert probe_cost(sort_of(1), scope) == 64
    assert probe_cost(sort_of(2), scope) == 160
    assert probe_cost(p.lines[3].probes[0], scope) == 32
    assert probe_cost(sort_of(4), scope) == 24


def test_render_template_formats_values():
    assert render_template("{x} and {!s} and {s} {{literal}}", {"x": 3, "s": "ab"}) == "3 and ab and 'ab' {literal}"
    assert render_template("{float('inf')}", {}) == "∞"


def test_directives_keep_ordinary_comments():
    d = parse_directives("x = 1  # keep me  #> narrate\n")
    assert d.code == "x = 1  # keep me\n" and d.narration == {1: "narrate"}


# --------------------------------------------------------------------------- meter
def test_meter_counts_deterministically_and_stops_runaways():
    code = compile_user("def f(n):\n    s = 0\n    for i in range(n):\n        s += i\n    return s\n")
    ns = fresh_namespace(code)
    counts = []
    for _ in range(2):
        with Meter() as m:
            ns["f"](100)
        counts.append(m.ops)
    assert counts[0] == counts[1] == 1 + 1 + 101 + 100 + 1

    code = compile_user("def g():\n    while True:\n        try:\n            pass\n        except Exception:\n            pass\n")
    ns = fresh_namespace(code)
    with pytest.raises(BudgetExceeded):
        with Meter(budget=1000):
            ns["g"]()


def test_meter_charges_hidden_costs():
    src = "def f(xs):\n    seen = []\n    for x in xs:\n        if x not in seen:\n            seen.append(x)\n"
    ns = fresh_namespace(compile_user(src))
    with Meter(Program(src)) as m:
        ns["f"](list(range(100)))
    assert m.hidden == sum(range(100))
    assert m.hidden_by_line == {4: sum(range(100))}


# --------------------------------------------------------------------------- complexity
@pytest.mark.parametrize("label,f", [
    ("O(1)", lambda n: 7),
    ("O(log n)", lambda n: 3 * math.log2(n) + 2),
    ("O(n)", lambda n: 4 * n + 9),
    ("O(n log n)", lambda n: 2 * n * math.log2(n) + n),
    ("O(n²)", lambda n: n * n / 2 + 3 * n),
    ("O(n³)", lambda n: n ** 3 / 6),
])
def test_fit_recognises_growth_models(label, f):
    pts = [{"n": n, "y": f(n)} for n in (16, 32, 64, 128, 256, 512, 1024)]
    assert complexity.fit(pts)["label"] == label


def test_fit_tolerates_input_noise():
    rng = random.Random(3)
    pts = [{"n": n, "y": 5 * n * (1 + rng.uniform(-0.08, 0.08))} for n in (16, 32, 64, 128, 256, 512, 1024)]
    assert complexity.fit(pts)["label"] == "O(n)"


def test_profile_reports_hot_lines():
    src = "class Solution:\n    def total(self, nums):\n        t = 0\n        for a in nums:\n            for b in nums:\n                t += a * b\n        return t\n"
    pr = complexity.profile(SUM, src, sizes=[8, 16, 32, 64])
    assert pr["time"]["label"] == "O(n²)"
    assert pr["lines"]["6"] == 64 * 64


# --------------------------------------------------------------------------- fuzz
def test_fuzz_shrinks_to_a_minimal_counterexample():
    buggy = "class Solution:\n    def total(self, nums):\n        return sum(nums[i] for i in range(len(nums) - 1))\n"
    rep = fuzz.diagnose(SUM, buggy)
    assert rep["found"] and rep["origin"] == "fuzz"
    assert len(rep["args"]["nums"]) == 1 and rep["args"]["nums"][0] != 0
    assert rep["pitfalls"][0]["id"] == "off-by-one"
    assert rep["neighbour"] is not None


def test_fuzz_reports_nothing_for_correct_code():
    ok = "class Solution:\n    def total(self, nums):\n        t = 0\n        for x in nums:\n            t += x\n        return t\n"
    assert fuzz.diagnose(SUM, ok) == {"found": False}


def test_fuzz_catches_crashes_and_infinite_loops():
    crash = "class Solution:\n    def total(self, nums):\n        return nums[0] + sum(nums[1:])\n"
    rep = fuzz.diagnose(SUM, crash)
    assert rep["status"] == "error" and rep["args"] == {"nums": []}
    hang = "class Solution:\n    def total(self, nums):\n        while len(nums) > 2:\n            pass\n        return sum(nums)\n"
    rep = fuzz.diagnose(SUM, hang)
    assert rep["status"] == "tle" and len(rep["args"]["nums"]) == 3


def test_generic_shrinker_only_proposes_smaller_inputs():
    cands = list(shrink_args(SUM, {"nums": [3, -2]}))
    assert {"nums": []} in cands and {"nums": [3]} in cands and {"nums": [0, -2]} in cands
    assert all(len(c["nums"]) <= 2 for c in cands)


# --------------------------------------------------------------------------- judge
def test_judge_verdicts():
    good = SUM.optimal.code
    wrong = "class Solution:\n    def total(self, nums):\n        return 0\n"
    crash = "class Solution:\n    def total(self, nums):\n        return nums[99]\n"
    hang = "class Solution:\n    def total(self, nums):\n        while True: pass\n"
    tests = [{"args": {"nums": [1, 2]}, "expected": 3}]
    assert judge.run(SUM, good, tests)["verdict"] == "accepted"
    assert judge.run(SUM, wrong, tests)["verdict"] == "wrong"
    r = judge.run(SUM, crash, tests)
    assert r["verdict"] == "error" and r["cases"][0]["error"]["line"] == 3
    assert judge.run(SUM, hang, [{**tests[0], "budget": 5000}])["verdict"] == "tle"
    r = judge.run(SUM, "def total(nums:\n", tests)
    assert r["verdict"] == "compile" and r["error"]["line"] == 1


def test_judge_accepts_plain_functions_and_computes_custom_expectations():
    r = judge.run(SUM, "def total(nums):\n    return sum(nums)\n", [{"args": {"nums": [4, 4]}}])
    assert r["verdict"] == "accepted" and r["cases"][0]["expected"] == 8


def test_judge_reports_missing_entry_point():
    r = judge.run(SUM, "class Solution:\n    pass\n", [{"args": {"nums": []}, "expected": 0}])
    assert r["cases"][0]["error"]["type"] == "EntryError"


def test_judge_design_and_codec_and_linked_list():
    ex = STACK.examples[0]["args"]
    assert judge.run(STACK, STACK.optimal.code, [{"args": ex, "expected": [None, None, None, 2, None, 1]}])["verdict"] == "accepted"
    assert judge.run(CODEC, CODEC.optimal.code, [{"args": {"strs": ["a#", "", "12#3"]}, "expected": ["a#", "", "12#3"]}])["verdict"] == "accepted"
    naive = "class Solution:\n    def encode(self, strs):\n        return ','.join(strs)\n    def decode(self, s):\n        return s.split(',')\n"
    assert fuzz.diagnose(CODEC, naive)["found"]
    assert judge.run(REVERSE, REVERSE.optimal.code, [{"args": {"head": [1, 2, 3]}, "expected": [3, 2, 1]}])["verdict"] == "accepted"
    cyclic = "class Solution:\n    def reverseList(self, head):\n        if head: head.next = head\n        return head\n"
    r = judge.run(REVERSE, cyclic, [{"args": {"head": [1, 2]}, "expected": [2, 1]}])
    assert r["verdict"] == "error" and "cycle" in r["cases"][0]["error"]["message"]


def test_submit_runs_fuzzer_after_suite_passes():
    # Passes the visible suite but breaks on single-element input.
    sneaky = "class Solution:\n    def total(self, nums):\n        return 0 if len(nums) == 1 else sum(nums)\n"
    res = judge.submit(SUM, sneaky, [{"args": {"nums": [1, 2]}, "expected": 3}])
    assert res["verdict"] == "wrong" and res["foundBy"] == "fuzzer"
    assert res["diagnosis"]["args"]["nums"] != [0]
    assert res["trace"]["steps"]


def test_submit_profiles_accepted_code():
    res = judge.submit(SUM, SUM.optimal.code, [{"args": {"nums": [1, 2]}, "expected": 3}])
    assert res["verdict"] == "accepted"
    assert res["profile"]["time"]["label"] in ("O(1)", "O(n)")  # sum() is a builtin: probes charge it O(n)


def test_compare_modes():
    assert compare(SUM, {}, [1, 2], [1, 2])
    p = type("P", (), {"compare": "unordered_nested"})()
    assert compare(p, {}, [["a", "b"], ["c"]], [["c"], ["b", "a"]])


def test_structures_cycle_detection():
    with pytest.raises(CycleError):
        from_list(to_cycle_list([1, 2, 3], 0))
