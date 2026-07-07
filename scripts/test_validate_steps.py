"""Tests for the step-script validator. Run: python3 -m unittest discover scripts"""
import copy
import unittest

from validate_steps import validate


def minimal_script():
    """Smallest script satisfying every invariant in docs/step-script-schema.md."""
    return {
        "schemaVersion": 1,
        "problemId": "test-problem",
        "solutionId": "test-solution",
        "title": "Test",
        "language": "python",
        "complexity": {"time": "O(n)", "space": "O(1)"},
        "code": ["def f(xs):", "    return xs"],
        "steps": [
            {
                "line": 0,
                "phase": "setup",
                "narration": "The plan.",
                "structures": [
                    {"id": "xs", "type": "array", "label": "xs",
                     "cells": [{"v": "1", "state": "idle"}]},
                ],
                "pointers": [],
                "vars": [],
            },
            {
                "line": 1,
                "phase": "resolve",
                "narration": "Return the array.",
                "structures": [
                    {"id": "xs", "type": "array", "label": "xs",
                     "cells": [{"v": "1", "state": "done"}]},
                ],
                "pointers": [],
                "vars": [],
            },
        ],
    }


class ScriptCase(unittest.TestCase):
    def setUp(self):
        self.script = minimal_script()

    def assertHasError(self, substring):
        errors = validate(self.script)
        self.assertTrue(
            any(substring in e for e in errors),
            f"expected an error containing {substring!r}, got {errors!r}",
        )


class TestLineAndPhase(ScriptCase):
    def test_valid_minimal_script_has_no_errors(self):
        self.assertEqual(validate(self.script), [])

    def test_line_past_end_of_code_is_reported(self):
        self.script["steps"][0]["line"] = 2
        self.assertHasError("line")

    def test_line_below_minus_one_is_reported(self):
        self.script["steps"][0]["line"] = -2
        self.assertHasError("line")

    def test_line_minus_one_is_allowed(self):
        self.script["steps"][0]["line"] = -1
        self.assertEqual(validate(self.script), [])

    def test_first_step_must_be_setup(self):
        self.script["steps"][0]["phase"] = "iterate"
        self.assertHasError("setup")

    def test_last_step_must_be_resolve(self):
        self.script["steps"][-1]["phase"] = "iterate"
        self.assertHasError("resolve")

    def test_unknown_phase_is_reported(self):
        self.script["steps"][0]["phase"] = "warmup"
        self.assertHasError("phase")


class TestSnapshotCompleteness(ScriptCase):
    def test_structure_missing_from_a_later_step_is_reported(self):
        self.script["steps"][1]["structures"] = []
        self.assertHasError("snapshot")

    def test_structure_appearing_only_later_is_reported(self):
        extra = {"id": "seen", "type": "map", "label": "seen", "entries": []}
        self.script["steps"][1]["structures"].append(extra)
        self.assertHasError("snapshot")


class TestStates(ScriptCase):
    def test_unknown_cell_state_is_reported(self):
        self.script["steps"][0]["structures"][0]["cells"][0]["state"] = "highlighted"
        self.assertHasError("state")

    def test_unknown_map_entry_state_is_reported(self):
        entries = [{"k": "a", "v": "[x]", "state": "glowing"}]
        for step in self.script["steps"]:
            step["structures"].append(
                {"id": "m", "type": "map", "label": "m", "entries": copy.deepcopy(entries)}
            )
        self.assertHasError("state")

    def test_unknown_var_state_is_reported(self):
        self.script["steps"][0]["vars"] = [{"name": "k", "value": "1", "state": "hot"}]
        self.assertHasError("state")


class TestNarration(ScriptCase):
    def test_narration_over_220_chars_is_reported(self):
        self.script["steps"][0]["narration"] = "x" * 221
        self.assertHasError("narration")

    def test_narration_with_markdown_is_reported(self):
        self.script["steps"][0]["narration"] = "This is **bold** talk."
        self.assertHasError("narration")

    def test_missing_narration_is_reported(self):
        del self.script["steps"][0]["narration"]
        self.assertHasError("narration")


class TestFootnotes(ScriptCase):
    def setUp(self):
        super().setUp()
        self.script["footnotes"] = [
            {"id": 1, "line": 0, "text": "Why line 0 is like that.", "step": 0},
        ]

    def test_valid_footnotes_pass(self):
        self.assertEqual(validate(self.script), [])

    def test_footnote_line_out_of_range_is_reported(self):
        self.script["footnotes"][0]["line"] = 99
        self.assertHasError("footnotes")

    def test_footnote_step_out_of_range_is_reported(self):
        self.script["footnotes"][0]["step"] = 99
        self.assertHasError("footnotes")

    def test_footnote_text_over_280_chars_is_reported(self):
        self.script["footnotes"][0]["text"] = "x" * 281
        self.assertHasError("footnotes")

    def test_footnote_ids_must_be_unique_and_ascending(self):
        self.script["footnotes"].append(
            {"id": 1, "line": 1, "text": "Duplicate id."}
        )
        self.assertHasError("footnotes")


class TestPointers(ScriptCase):
    def test_pointer_to_unknown_structure_is_reported(self):
        self.script["steps"][0]["pointers"] = [
            {"structure": "ghost", "index": 0, "label": "p"}
        ]
        self.assertHasError("pointer")

    def test_pointer_index_past_cells_is_reported(self):
        self.script["steps"][0]["pointers"] = [
            {"structure": "xs", "index": 5, "label": "p"}
        ]
        self.assertHasError("pointer")


class TestTopLevel(ScriptCase):
    def test_missing_required_field_is_reported(self):
        del self.script["problemId"]
        self.assertHasError("problemId")

    def test_wrong_schema_version_is_reported(self):
        self.script["schemaVersion"] = 2
        self.assertHasError("schemaVersion")

    def test_empty_steps_is_reported(self):
        self.script["steps"] = []
        self.assertHasError("steps")


class TestGoldenScript(unittest.TestCase):
    def test_golden_group_anagrams_validates_clean(self):
        import json
        import pathlib

        golden = (
            pathlib.Path(__file__).resolve().parent.parent
            / "client/src/data/steps/group-anagrams.json"
        )
        script = json.loads(golden.read_text())
        self.assertEqual(validate(script), [])


class TestCli(unittest.TestCase):
    def run_cli(self, *args):
        import subprocess
        import sys
        import pathlib

        script = pathlib.Path(__file__).resolve().parent / "validate_steps.py"
        return subprocess.run(
            [sys.executable, str(script), *args], capture_output=True, text=True
        )

    def test_valid_file_exits_zero(self):
        import pathlib

        golden = (
            pathlib.Path(__file__).resolve().parent.parent
            / "client/src/data/steps/group-anagrams.json"
        )
        result = self.run_cli(str(golden))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_file_exits_nonzero_and_prints_errors(self):
        import json
        import tempfile

        bad = minimal_script()
        bad["steps"][0]["phase"] = "iterate"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
        result = self.run_cli(f.name)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("setup", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
