# Feetcode — Project Scope v2.0

**A dynamic program analysis lab disguised as a DSA prep site.** Free forever, runs entirely in
the browser, $0/month to operate.

LeetCode tells you *that* you failed. Feetcode shows you **where, why, and how expensive** — by
pointing real program-analysis tooling (a tracer, a fuzzer, a shrinker, an execution differ, an
invariant miner) at the code *you* wrote, and explaining everything it finds in one unified
voice:

> **The Footnote Law: everything Feetcode tells you is a footnote anchored to a line of code.**

Insights on reference solutions, narration during playback, the bug the fuzzer found, the
invariant your loop violates, the citation to the 1967 paper — all of it renders as numbered
footnotes pinned to exact lines. The name is a pun¹. The system is the punchline.

¹ *yes, feet. the footnotes are real.*

---

## 1. Why this gets you hired

The interview demo, end to end: *you submit wrong code → Feetcode fuzzes it against the
reference solution → shrinks the failure to a minimal counterexample (often 2 elements) →
traces both programs on that tiny input → finds the first step where their states diverge →
scrubs the visual player to that exact moment → and files the finding as a footnote on the
guilty line.*

Fuzzer → shrinker → tracer → differ → time-travel debugger, fully in-browser, zero servers.
Every stage is a recognized CS technique (property-based testing with shrinking à la
Hypothesis/QuickCheck; dynamic tracing; trace differencing; dynamic invariant detection in the
Daikon lineage). A senior engineer watching this recognizes their own toolbox — that's the
reaction this project is engineered to produce.

The supporting talking points, each a real decision with real tradeoffs:

1. **One schema, many producers.** The step-script format (§4) is the universal intermediate
   representation. The AI batch pipeline produces scripts for reference solutions; the live
   tracer produces them for user code; the differ consumes two of them. The player renders all
   of it without knowing or caring where a script came from.
2. **Snapshots over deltas.** Each step is a complete visual state. Costs file size (trivial,
   gzip), buys free scrubbing, a pure-function renderer, per-step validation, and — critically —
   trivially diffable traces. The divergence feature falls out of this decision.
3. **In-browser execution (Pyodide/WebAssembly).** No judge servers, no sandboxing
   infrastructure, no per-user cost, no abuse surface. The "run my code" feature that costs
   LeetCode a fleet costs Feetcode nothing.
4. **One output type for every analyzer: the footnote.** New analyzers don't invent new UI;
   they emit annotations `{line, text, optional step-jump}`. Uniform voice, uniform rendering,
   uniform architecture.

## 2. Positioning

For CS students and self-taught devs who can't pay $200/year. Pattern-first pedagogy. The
one-sentence pitch: **"the debugger for learning algorithms."** Tagline territory: *the
footnotes your code was missing.* Irreverent surface, rigorous underneath — the name does the
marketing, the footnotes do the teaching.

## 3. Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│ BUILD TIME (your Mac, occasionally)                                 │
│   scripts/generate_steps.py                                         │
│     Anthropic API → reference step-scripts + authored footnotes     │
│     → schema validation → invariant checks → review → git commit    │
└───────────────────────────────┬────────────────────────────────────┘
                                │ static JSON, committed
┌───────────────────────────────▼────────────────────────────────────┐
│ RUN TIME — React SPA on Netlify, everything below runs in-browser   │
│                                                                     │
│  LAYER 3 · the voice      Footnotes (insights, findings, citations) │
│  LAYER 2 · the analyzers  judge → tracer → fuzzer/shrinker →        │
│                           differ → invariant miner (phased)         │
│  LAYER 1 · the substrate  step-script schema + Step Player          │
│                                                                     │
│  Pyodide (Python→WASM) executes user code; sys.settrace captures    │
│  per-line state and emits step-scripts — same format as build time. │
└────────────────────────────────────────────────────────────────────┘
```

**Stack:** React 19 + Vite, Tailwind v3 + token CSS, react-router v7, Netlify. Phase 2 adds
Pyodide + CodeMirror. Supabase (auth, saved personal footnotes, progress) deferred until the
analysis suite exists — accounts are not the product.

## 4. The step-script schema (the substrate)

Spec: `docs/step-script-schema.md`. Snapshot-based (every step carries complete state of every
structure), fixed structure-type vocabulary, semantic cell states (`active/match/compare/new/
done`) mapped to presentation in exactly one CSS block. v2.0 addition: an optional `footnotes`
array — annotations anchored to code lines, optionally deep-linking to a step. Additive fields
don't bump the schema version; the renderer ignores what it doesn't know.

**The lens problem (the design problem you personally own):** the tracer sees raw locals like
`groups = {(1,0,...): ['eat']}`; something must know to render that as a map with compact keys,
and that `l, r` are pointers *into* `s`. Solution: a small per-problem "lens" config mapping
variable names → structure types + display transforms, plus fallback heuristics. Designing the
lens format is the deepest individual contribution in this project — expect interviewers to
probe it, and welcome that.

## 5. Phases — each independently demoable

**P1 · Substrate + identity (current).** Step Player (code/state/narration on one scrubbable
timeline), golden hand-crafted Group Anagrams script, footnote system v1: superscript markers in
the code pane, hover-linked footnote block styled like a real text's apparatus, step-jump links,
scholarly references per problem, brand carrying the superscript (`feetcode¹`). Deployed to
Netlify. *Done when: one URL, no apologies.*

**P1.5 · Reference content pipeline.** `generate_steps.py`: prompt template → step script +
footnotes; JSON schema validation; invariant checks (final state = expected output, line indices
valid, states in enum); review queue. Generate Arrays & Hashing (9 problems). Claude Code
territory — agentic scripting, not your learning surface.

**P2 · The runtime (table stakes, done cheap).** CodeMirror editor + Pyodide + test runner →
accept/fail. Deliberately minimal: the judge is a commodity and gets exactly commodity effort.
Its real purpose is to put *user code execution* in the browser, which everything after depends
on.

**P3 · The tracer.** `sys.settrace` hook captures line + locals each step → lens config maps
raw state → step script → **the player visualizes code the user wrote**. The moment Feetcode
stops being a content site and becomes a tool.

**P4 · The flagship: fuzz → shrink → diverge.** Property-based input generation per problem;
on failure, greedy shrinking (delete elements / simplify values / re-test until minimal); trace
user + reference on the counterexample; first-divergence search across the two timelines; file
the finding as a footnote on the guilty line with a jump-to-step link. This is the demo.

**P5 · The stretch (build one, design-doc the rest).** Invariant mining (infer `left ≤ right`
from reference traces; report the step where user code breaks it); behavioral fingerprinting
(classify the user's *approach* from trace dynamics, not source text); the complexity lab
(empirical big-O: run on growing n, fit the curve, heatmap the line getting hit n² times).

## 6. Design system

Identity: **late-night study session, annotated.** Ink-blue surfaces, paper text, amber phosphor
for the active, teal for matches, rose for comparisons. Display: Bricolage Grotesque; data: IBM
Plex Mono. Superscript numerals are the brand mark. Footnote blocks use the classic apparatus
convention: short hairline rule, hanging numbers, quiet type. Tokens in `index.css`; nothing
hardcodes a color.

## 7. Quality bar

Keyboard-operable player, visible focus, `prefers-reduced-motion`, responsive to 380px,
Lighthouse 90+, conventional commits, README opening with a GIF of the flagship pipeline. Vitest
on the playback hook, the schema validator, and (P4) the shrinker — the shrinker is the most
test-worthy code in the project.

## 8. Out of scope, permanently or for now

Execution servers of any kind (the in-browser constraint is the architecture), payments (free is
the positioning), mobile apps, contests, social feeds. Accounts only after P4.

## 9. Status — June 12, 2026

P1 substrate running locally on Tah's machine (verified). Today: footnote system v1 shipped into
the substrate — schema addition, golden script annotated, player markers + apparatus block,
references, brand update. Next: README + Netlify deploy, then P1.5.
