"""Validator for step scripts — enforces docs/step-script-schema.md invariants."""
import re

PHASES = ("setup", "iterate", "resolve")
STATES = ("idle", "active", "compare", "match", "new", "done")
MARKDOWN_RE = re.compile(r"\*\*|`|\]\(|^#", re.MULTILINE)


def _check_states(errors, where, items):
    for j, item in enumerate(items):
        state = item.get("state")
        if state not in STATES:
            errors.append(f"{where}[{j}]: state {state!r} not one of {STATES}")


def _check_narration(errors, i, step):
    narration = step.get("narration")
    if not isinstance(narration, str) or not narration.strip():
        errors.append(f"steps[{i}]: narration missing or empty")
        return
    if len(narration) > 220:
        errors.append(f"steps[{i}]: narration is {len(narration)} chars (max 220)")
    if MARKDOWN_RE.search(narration):
        errors.append(f"steps[{i}]: narration contains markdown")


REQUIRED_FIELDS = ("problemId", "solutionId", "title", "language", "complexity", "code", "steps")


def _check_footnotes(errors, script, code, steps):
    last_id = 0
    for j, fn in enumerate(script.get("footnotes", [])):
        where = f"footnotes[{j}]"
        fn_id = fn.get("id")
        if not isinstance(fn_id, int) or fn_id <= last_id:
            errors.append(f"{where}: id {fn_id!r} not unique and ascending")
        else:
            last_id = fn_id
        line = fn.get("line")
        if not isinstance(line, int) or not (0 <= line < len(code)):
            errors.append(f"{where}: line {line!r} outside [0, {len(code)})")
        text = fn.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{where}: text missing or empty")
        elif len(text) > 280:
            errors.append(f"{where}: text is {len(text)} chars (max 280)")
        elif MARKDOWN_RE.search(text):
            errors.append(f"{where}: text contains markdown")
        step = fn.get("step")
        if step is not None and (not isinstance(step, int) or not (0 <= step < len(steps))):
            errors.append(f"{where}: step {step!r} outside [0, {len(steps)})")


def _check_pointers(errors, i, step):
    by_id = {s.get("id"): s for s in step.get("structures", [])}
    for j, p in enumerate(step.get("pointers", [])):
        where = f"steps[{i}].pointers[{j}]"
        target = by_id.get(p.get("structure"))
        if target is None:
            errors.append(f"{where}: pointer targets unknown structure {p.get('structure')!r}")
            continue
        index = p.get("index")
        cells = target.get("cells", [])
        if not isinstance(index, int) or not (0 <= index < len(cells)):
            errors.append(f"{where}: pointer index {index!r} outside [0, {len(cells)})")


def validate(script):
    """Return a list of human-readable error strings; empty list means valid."""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in script:
            errors.append(f"top level: missing required field {field!r}")
    if script.get("schemaVersion") != 1:
        errors.append(f"top level: schemaVersion {script.get('schemaVersion')!r} != 1")

    code = script.get("code", [])
    steps = script.get("steps", [])
    if "steps" in script and not steps:
        errors.append("top level: steps is empty")

    snapshot_ids = None  # structure ids seen in steps[0]; every step must match
    for i, step in enumerate(steps):
        line = step.get("line")
        if not isinstance(line, int) or not (-1 <= line < len(code)):
            errors.append(f"steps[{i}]: line {line!r} outside [-1, {len(code)})")
        phase = step.get("phase")
        if phase not in PHASES:
            errors.append(f"steps[{i}]: phase {phase!r} not one of {PHASES}")
        _check_narration(errors, i, step)

        structures = step.get("structures", [])
        ids = {s.get("id") for s in structures}
        if snapshot_ids is None:
            snapshot_ids = ids
        elif ids != snapshot_ids:
            errors.append(
                f"steps[{i}]: incomplete snapshot — structure ids {sorted(map(str, ids))} "
                f"differ from steps[0] {sorted(map(str, snapshot_ids))}"
            )
        for s in structures:
            where = f"steps[{i}].structures[{s.get('id')}]"
            _check_states(errors, where + ".cells", s.get("cells", []))
            _check_states(errors, where + ".entries", s.get("entries", []))
        _check_states(errors, f"steps[{i}].vars", step.get("vars", []))
        _check_pointers(errors, i, step)

    if steps and steps[0].get("phase") != "setup":
        errors.append('steps[0]: first phase must be "setup"')
    if steps and steps[-1].get("phase") != "resolve":
        errors.append(f'steps[{len(steps) - 1}]: last phase must be "resolve"')

    _check_footnotes(errors, script, code, steps)
    return errors


def main(argv):
    import json
    import pathlib

    if not argv:
        print("usage: validate_steps.py <script.json | directory> ...")
        return 2

    paths = []
    for arg in argv:
        p = pathlib.Path(arg)
        paths.extend(sorted(p.glob("*.json")) if p.is_dir() else [p])

    failed = 0
    for p in paths:
        errors = validate(json.loads(p.read_text()))
        if errors:
            failed += 1
            print(f"FAIL {p}")
            for e in errors:
                print(f"  {e}")
        else:
            print(f"ok   {p}")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
