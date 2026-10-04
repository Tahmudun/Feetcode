# 0004 · Problems are Python modules behind a quality gate

**Status:** accepted (replaces the v1 plan of LLM-generated step scripts)

## Context

The first version planned to generate visual step scripts with an LLM and validate them against a JSON schema. That hits a ceiling. A generated script describes what a solution *should* do, not what it does. Every script needs human review. Nothing connects the content to the judge, the fuzzer or the user's code.

## Decision

A problem is a **Python module** (`problems/<pattern>/<slug>.py`) that defines `PROBLEM = Problem(...)`:

- statement, examples, constraints, hints, insight, company tags
- **executable** parts: input generators, `validate`, an optional `shrink`, comparators, several reference solutions and pitfall detectors
- **narration** as `#>` / `#!` / `#~` directives in the reference source, evaluated against the real execution

Lessons, expected outputs, budgets and complexity baselines are all **computed** by running this code, never written by hand.

A **quality gate** (`python -m feetcode_pipeline check`) runs on every build and in CI. It rejects a problem when:

- a stated example output is wrong
- the reference solutions disagree with each other on generated inputs
- a narration template fails to render
- a pitfall detector fires on a correct answer
- a measured growth rate contradicts the declared big-O
- the schema is invalid

## Consequences

- **Content can't silently rot.** The gate found real authoring mistakes while the 38 problems were written: an example with two valid answers, pitfall detectors broad enough to blame correct code, and declared space bounds that were wrong.
- **One source of truth.** The same module drives the judge, the fuzzer, the lessons, the profiler and the UI copy.
- **Authoring needs Python.** That is a fair price for content that is tested like code. [../authoring.md](../authoring.md) walks through it.
- **LLMs can still help write content.** The gate decides what ships.
