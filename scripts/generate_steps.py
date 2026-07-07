"""P1.5 pipeline: Anthropic API -> step script + footnotes -> validation -> review queue.

Usage:
    python3 scripts/generate_steps.py two-sum [valid-anagram ...]
    python3 scripts/generate_steps.py --all

Requires `pip install anthropic` and credentials (ANTHROPIC_API_KEY or `ant auth login`)
only when actually generating; the pipeline logic itself is testable without either.
Outputs land in scripts/review/ for human review — never directly in client/src/data/steps/.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_DOC = ROOT / "docs/step-script-schema.md"
GOLDEN = ROOT / "client/src/data/steps/group-anagrams.json"
PROBLEMS_MANIFEST = pathlib.Path(__file__).resolve().parent / "problems.json"
REVIEW_DIR = pathlib.Path(__file__).resolve().parent / "review"

MODEL = "claude-opus-4-8"
MAX_TOKENS = 64000

PROMPT_TEMPLATE = """You are writing a step script for Feetcode, a DSA visualization platform.
A step script narrates one solution's execution as complete visual snapshots that a player
renders one step at a time. Your output must be a single JSON object and nothing else.

## The schema contract (follow it exactly)

{schema_doc}

## The golden reference script

This hand-crafted script for Group Anagrams is the quality bar. Match its narration voice
(plain English, present tense, teaches the *idea* behind each step), its step granularity
(one idea per step, tight inner loops collapsed), and its footnote style (why the line is
the way it is, not what it does):

{golden}

## Your problem

Problem id: {id}
Title: {title}
Statement: {statement}
Canonical approach to visualize: {approach}
Trace this exact input (keep the visual state small): {trace_input}

## Requirements

- problemId must be "{id}".
- 12-25 steps. steps[0] is phase "setup" and orients ("here's the plan"); the last step is
  phase "resolve" and states the takeaway pattern.
- Every step carries the complete state of every structure (snapshots, not deltas).
- The final step's structures must encode the correct output for the trace input.
- 2-4 footnotes on the most insight-dense code lines, each ≤ 280 chars, no markdown.
- Narration ≤ 220 chars per step, no markdown.

Output the JSON object only.
"""

REPAIR_TEMPLATE = """Your previous step script failed validation with these errors:

{errors}

Fix every error and output the corrected, complete JSON object only.
"""


class GenerationError(Exception):
    pass


def build_prompt(problem, schema_doc, golden):
    return PROMPT_TEMPLATE.format(
        schema_doc=schema_doc,
        golden=golden,
        id=problem["id"],
        title=problem["title"],
        statement=problem["statement"],
        approach=problem["approach"],
        trace_input=problem["trace_input"],
    )


def extract_json(text):
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text[text.find("{"):text.rfind("}") + 1]
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        raise GenerationError(f"response contained no parseable JSON object:\n{text[:500]}")


def generate_script(problem, complete):
    """Generate and validate a step script. `complete(prompt) -> str` does the model call.

    One repair round: if the first script fails validation, the errors are sent back
    for a fix. Still invalid after that -> GenerationError (human takes over).
    """
    from validate_steps import validate

    prompt = build_prompt(problem, SCHEMA_DOC.read_text(), GOLDEN.read_text())
    script = extract_json(complete(prompt))
    errors = validate(script)
    if not errors:
        return script

    repair = prompt + "\n\n" + REPAIR_TEMPLATE.format(errors="\n".join(errors))
    script = extract_json(complete(repair))
    errors = validate(script)
    if not errors:
        return script
    raise GenerationError(
        f"{problem['id']}: still invalid after repair round:\n" + "\n".join(errors)
    )


def anthropic_complete(prompt):
    import anthropic

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    return next(b.text for b in message.content if b.type == "text")


def main(argv):
    problems = {p["id"]: p for p in json.loads(PROBLEMS_MANIFEST.read_text())}
    ids = list(problems) if argv == ["--all"] else argv
    if not ids:
        print("usage: generate_steps.py <problem-id> ... | --all")
        print("known ids:", ", ".join(problems))
        return 2
    unknown = [i for i in ids if i not in problems]
    if unknown:
        print(f"unknown problem ids: {', '.join(unknown)} (see scripts/problems.json)")
        return 2

    REVIEW_DIR.mkdir(exist_ok=True)
    failed = 0
    for pid in ids:
        print(f"generating {pid} ...")
        try:
            script = generate_script(problems[pid], anthropic_complete)
        except GenerationError as e:
            failed += 1
            print(f"FAIL {pid}: {e}")
            continue
        out = REVIEW_DIR / f"{pid}.json"
        out.write_text(json.dumps(script, indent=2) + "\n")
        print(f"ok   {out} — review, then move to client/src/data/steps/ and set live:true")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
