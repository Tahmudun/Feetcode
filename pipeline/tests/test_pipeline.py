import dataclasses
import json

from feetcode.problem import Pitfall
from feetcode_pipeline import stages
from feetcode_pipeline.build import dumps
from feetcode_pipeline.discover import discover, load
from feetcode_pipeline.validate import check


def problem(name):
    return load(next(s for s in discover([name])))


def test_discovers_every_problem():
    ids = {load(s).id for s in discover()}
    assert len(ids) == 38
    assert {"two-sum", "trapping-rain-water", "lru-cache", "min-stack"} <= ids


def test_starter_code_function_design_and_linked_list():
    two = stages.starter_code(problem("two_sum"))
    assert "class Solution:" in two and "def twoSum(self, nums: List[int], target: int) -> List[int]:" in two
    lru = stages.starter_code(problem("lru_cache"))
    assert "class LRUCache:" in lru and "def get(self, key: int) -> int:" in lru and "_remove" not in lru
    rev = stages.starter_code(problem("reverse_linked_list"))
    assert rev.startswith("# Definition for singly-linked list.")
    codec = stages.starter_code(problem("encode_decode"))
    assert "def encode" in codec and "def decode" in codec
    for src in discover():
        code = stages.starter_code(load(src))
        if code.endswith("        \n"):        # function starters end where the cursor goes
            code = code[:-1] + "pass\n"
        compile(code, src.module, "exec")  # every starter is valid Python


def test_suite_is_deterministic_and_budgeted():
    p = problem("trapping_rain_water")
    a, b = stages.suite(p), stages.suite(p)
    assert dumps(a) == dumps(b)
    kinds = {c["kind"] for c in a["cases"]}
    assert {"example", "edge", "random", "large", "stress"} <= kinds
    assert all(c["budget"] >= stages.BUDGET_FLOOR for c in a["cases"])
    assert all(p.is_valid(c["args"]) for c in a["cases"])


def test_budgets_separate_complexity_classes():
    p = problem("two_sum")
    verdicts = stages.reference_verdicts(p, stages.suite(p)["cases"])
    assert verdicts["hashmap"]["verdict"] == "accepted"
    assert verdicts["brute"]["verdict"] == "tle"


def test_detail_exports_examples_with_outputs_and_stripped_code():
    d = stages.detail(problem("trapping_rain_water"), "m")
    assert all("output" in ex for ex in d["examples"])
    opt = next(s for s in d["solutions"] if s["optimal"])
    assert "#>" not in opt["code"] and "#!" not in opt["code"]
    assert opt["footnotes"]
    json.loads(dumps(d))


def test_lessons_trace_every_solution_with_narration():
    les = stages.lessons(problem("valid_parentheses"))
    assert set(les["traces"]) == {"replace", "stack"}
    steps = les["traces"]["stack"]["steps"]
    assert any(s.get("t") for s in steps)


def test_gate_catches_wrong_example_output():
    p = problem("two_sum")
    bad = dataclasses.replace(p, examples=[{**p.examples[0], "output": [0, 1]}] + p.examples[1:])
    issues, _ = check(bad, cases=20)
    assert any(i.check == "examples" and i.level == "error" for i in issues)


def test_gate_catches_trigger_happy_pitfalls():
    p = problem("two_sum")
    noisy = dataclasses.replace(p, pitfalls=[Pitfall("always", "Always", "fires", detect=lambda a, e, x: True)])
    issues, _ = check(noisy, cases=20)
    assert any(i.check == "pitfalls" for i in issues)


def test_gate_catches_disagreeing_solutions():
    p = problem("contains_duplicate")
    wrong = dataclasses.replace(p.solutions[0], code=p.solutions[0].code.replace("i + 1", "i"))
    broken = dataclasses.replace(p, solutions=[wrong] + p.solutions[1:])
    issues, _ = check(broken, cases=40)
    assert any(i.check == "agreement" for i in issues)


def test_canonical_json_is_stable():
    assert dumps({"b": 1, "a": [1, {"d": 2, "c": 3}]}) == '{"a":[1,{"c":3,"d":2}],"b":1}'
