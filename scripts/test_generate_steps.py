"""Tests for the generation pipeline. Run: python3 -m unittest discover scripts

The Anthropic call is injected as `complete(prompt) -> str`, so these tests
exercise prompt building, JSON extraction, and the validate-repair loop
without network access or the anthropic package installed.
"""
import json
import unittest

from generate_steps import GenerationError, build_prompt, extract_json, generate_script
from test_validate_steps import minimal_script

PROBLEM = {
    "id": "two-sum",
    "title": "Two Sum",
    "statement": "Given an array of integers and a target, return indices of two numbers adding to target.",
    "approach": "One-pass hash map of value -> index.",
    "trace_input": "nums = [2, 7, 11, 15], target = 9",
}


def valid_response():
    script = minimal_script()
    script["problemId"] = "two-sum"
    return json.dumps(script)


class TestBuildPrompt(unittest.TestCase):
    def test_prompt_contains_problem_schema_and_golden(self):
        prompt = build_prompt(PROBLEM, schema_doc="THE-SCHEMA-DOC", golden="THE-GOLDEN-SCRIPT")
        for expected in (
            PROBLEM["statement"],
            PROBLEM["approach"],
            PROBLEM["trace_input"],
            "THE-SCHEMA-DOC",
            "THE-GOLDEN-SCRIPT",
        ):
            self.assertIn(expected, prompt)


class TestExtractJson(unittest.TestCase):
    def test_bare_json(self):
        self.assertEqual(extract_json('{"a": 1}'), {"a": 1})

    def test_fenced_json(self):
        text = 'Here is the script:\n```json\n{"a": 1}\n```\nDone.'
        self.assertEqual(extract_json(text), {"a": 1})

    def test_unparseable_raises(self):
        with self.assertRaises(GenerationError):
            extract_json("no json here")


class TestGenerateScript(unittest.TestCase):
    def test_valid_first_response_returned(self):
        calls = []

        def complete(prompt):
            calls.append(prompt)
            return valid_response()

        script = generate_script(PROBLEM, complete)
        self.assertEqual(script["problemId"], "two-sum")
        self.assertEqual(len(calls), 1)

    def test_invalid_then_valid_triggers_one_repair_round(self):
        bad = json.loads(valid_response())
        bad["steps"][0]["phase"] = "warmup"
        responses = [json.dumps(bad), valid_response()]
        calls = []

        def complete(prompt):
            calls.append(prompt)
            return responses[len(calls) - 1]

        script = generate_script(PROBLEM, complete)
        self.assertEqual(len(calls), 2)
        self.assertIn("phase", calls[1])  # repair prompt carries validator errors
        self.assertEqual(script["problemId"], "two-sum")

    def test_still_invalid_after_repair_raises_with_errors(self):
        bad = json.loads(valid_response())
        bad["steps"][0]["phase"] = "warmup"

        def complete(prompt):
            return json.dumps(bad)

        with self.assertRaises(GenerationError) as ctx:
            generate_script(PROBLEM, complete)
        self.assertIn("phase", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
