# Feetcode

Free, in-browser DSA platform: a dynamic program analysis lab disguised as a prep site.
Read SCOPE.md before any non-trivial task. Schema contract: docs/step-script-schema.md.

## The Footnote Law
Every explanation the product emits — authored insights, analyzer findings, citations — is a
footnote: `{id, line, text, step?}` anchored to a code line. New analyzers emit footnotes, never
new UI primitives.

## Commands
- Dev server: `cd client && npm run dev`
- Build check (run before claiming a task done): `cd client && npm run build`
- Lint: `cd client && npm run lint`

## Architecture
- `client/src/data/steps/*.json` — step scripts: SNAPSHOT-based (every step carries complete
  state of every structure). The renderer is a pure function of `steps[i]`. Never convert to
  deltas.
- `client/src/data/steps/group-anagrams.json` — the GOLDEN script. Hand-crafted reference for
  what generated scripts must look like. Do not regenerate or "improve" it without being asked.
- `client/src/visualizer/` — StepPlayer (panes + transport + footnote apparatus), Structure
  (pure renderers per structure type), usePlayback (timeline hook).
- `client/src/data/problems.js` — problem catalog; `live: true` requires a script in steps/.
- `client/src/index.css` — ALL colors/fonts live here as tokens (--amber, --teal, --rose,
  --ink...). Never hardcode a color in a component.
- `scripts/` — (P1.5+) Python batch pipeline: Anthropic API → step scripts → validation.

## Hard rules
- Schema changes: additive fields only without a version bump; any change updates
  docs/step-script-schema.md AND the golden script AND the validator together.
- Cell/entry states come only from: idle, active, compare, match, new, done. States carry
  meaning; CSS maps meaning → presentation in exactly one block (the `.st-*` classes).
- Branches: never commit to main. Work on dev or feature/* off dev. Conventional commits
  (feat:, fix:, docs:, refactor:).
- No new runtime dependencies without asking. No servers, ever — in-browser execution is the
  architecture (SCOPE.md §1.3).
- Accessibility floor: keyboard operability, focus-visible, prefers-reduced-motion. Don't
  regress it.

## Owner context
Tah is learning React/full-stack through this project. For visualizer/ and the lens design
(SCOPE.md §4): explain changes and prefer walking through plans before large edits — he must be
able to defend this code in interviews. Boilerplate, pipelines, and config: just do it.
