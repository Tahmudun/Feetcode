# Feetcode

Free, in-browser DSA platform: interview prep that runs, judges and **visualizes the user's own code**,
backed by a dynamic program analysis engine (tracer, op meter, fuzzer + shrinker, complexity profiler).
Read docs/ARCHITECTURE.md before any non-trivial task; SCOPE.md has the product scope and roadmap.

## The Footnote Law
Every explanation the product emits (authored insights, analyzer findings, narration) is anchored to a
code line: footnotes are `{line, text}`, narration rides on a step. New analyzers emit footnotes or
step annotations, never new UI primitives.

## Commands
- Client dev: `cd client && npm run dev`
- Client checks (run before claiming a task done): `cd client && npm run lint && npm run build && npm test`
- Engine tests: `python -m pytest -q engine/tests` (Python ≥ 3.12; also `cd client && npm run test:engine` for Pyodide)
- Content gate: `cd pipeline && python -m feetcode_pipeline check [filter]`
- Content build: `cd pipeline && python -m feetcode_pipeline build` (incremental), `build --check` (drift)
- Pipeline tests: `cd pipeline && python -m pytest -q tests`
- E2E: `cd client && npm run build && npm run e2e` (set `CHROMIUM_PATH` if Playwright's browser is elsewhere)

## Architecture (details: docs/ARCHITECTURE.md)
- `engine/feetcode/`: pure-Python engine, stdlib only. It runs in CPython (pipeline) AND Pyodide (browser,
  inlined via `?raw`). Never add a dependency or anything Pyodide can't run. JSON in/out via `api.handle`.
- `problems/<pattern>/*.py`: problems as code (`PROBLEM = Problem(...)`). Narration lives in reference
  solutions as `#>` / `#!` / `#~` directives. Guide: docs/authoring.md.
- `pipeline/`: quality gate + deterministic incremental build → `client/src/content/generated/`.
  Generated files are committed; never edit them by hand. Change the source and rebuild.
- `client/src/runtime/`: Pyodide Web Worker + watchdog. `client/src/viz/`: `buildScene(trace, i)` is a
  pure function of one snapshot step. Traces are SNAPSHOTS (docs/trace-format.md). Never convert to deltas.
- `client/src/store/`: progress is an append-only event log; all progress state is derived. Never
  store derived state.
- `client/src/styles/index.css`: ALL colors/fonts live here as tokens (light + dark). Never hardcode a
  color in a component.

## Hard rules
- Trace format: additive fields only; any change updates engine, `runtime/types.ts`, the scene builder and
  docs/trace-format.md together, then rebuild content.
- Cell/entry states come only from: idle, active, compare, match, new, done. CSS maps meaning →
  presentation in exactly one block (the `.st-*` classes).
- Judging is deterministic: limits are op budgets, never wall-clock (ADR 0001).
- Problem statements are original prose; never paste statements from other sites.
- Branches: never commit to main. Conventional commits (feat:, fix:, docs:, refactor:, test:).
- No new runtime dependencies without asking. No servers, ever: in-browser execution is the architecture.
- Accessibility floor: keyboard operability, focus-visible, prefers-reduced-motion. Don't regress it.

## Owner context
Tah is learning React/full-stack through this project. For viz/ and the lens design: explain changes
and prefer walking through plans before large edits - he must be able to defend this code in interviews.
Boilerplate, pipelines, and config: just do it.
