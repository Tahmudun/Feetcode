# Feetcode: Project Scope v3

**Interview prep that shows you why your code works, or why it doesn't.** It's free forever, runs entirely in the browser and costs $0/month to operate.

LeetCode tells you *that* you failed. NeetCode shows you someone else's solution. Feetcode points real program-analysis tooling at **the code you wrote**:

- a tracer
- an operation meter
- a fuzzer with a shrinker
- a complexity profiler

It explains what they find in one voice:

> **The Footnote Law: every insight is anchored to a line of code.**

¹ *yes, feet. the footnotes are real.*

v3 replaces v2's plan (an AI-generated step-script pipeline, then a tracer) with what was actually built: one Python engine running at build time and in the browser, and problems as code behind a quality gate. Section 9 records what changed and why.

---

## 1. The demo that gets you hired

*Submit a wrong Two Sum.*

1. The hidden suite fails.
2. The fuzzer shrinks the failure to `nums=[5,5], target=10`.
3. The diagnosis names the mistake ("Paired an element with itself") and shows a passing neighbour input.
4. A footnote pinned under the guilty line says where your run first leaves the reference's: you return `[0, 0]`, the reference returns `[0, 1]`.
5. One click replays your code on that input, step by step, with live values in the editor: the map, the probe and the line that returned `[0, 0]`. Another shows the reference's run from the same point.

*Then submit the brute force.*

1. It's correct but runs out of operations.
2. The profiler fits `O(n²)` and draws it against the optimal `O(n)`.
3. The editor heat-maps line 4, which ran 524,798 times.

All of this runs in the browser with no servers. Each stage is a recognized technique: property-based testing with shrinking (QuickCheck, Hypothesis), dynamic tracing, deterministic cost models and empirical complexity fitting.

Talking points, each a real decision with tradeoffs (see `docs/adr/`):

1. **Deterministic judging.** Budgets in operations, not milliseconds, so verdicts are reproducible on any machine. (ADR 0001)
2. **One engine, two runtimes.** The same Python runs in CPython at build time and in Pyodide in the browser, and is tested in both. (ADR 0002)
3. **Snapshots over deltas.** The renderer is a pure function of one step: free scrubbing, and traces that can be compared step by step. (ADR 0003)
4. **Content as code.** Problems are executable modules behind a quality gate. Content can't silently rot. (ADR 0004)
5. **Data-engineering discipline in the build.** Deterministic, incremental, content-addressed, drift-checked, with lineage. (ADR 0005)
6. **Event-sourced state.** Progress is an immutable log, and everything is derived and queryable. (ADR 0006) Tonight's session is one more event: the plan is logged once, and its progress is derived from what follows.
7. **Comparing runs, not just outputs.** Snapshot traces make it cheap to align your run with a reference's and name the first step where they disagree, plus invariants mined from many reference runs.

## 2. Positioning

For CS students and self-taught developers who can't pay $200 a year, and for anyone who learns better by *seeing* than by memorizing. Pattern-first, roadmap-ordered. Pitch: **"the debugger for learning algorithms."** Irreverent surface, rigorous underneath. It should feel fast, fun and slightly magical to code in.

## 3. Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). In brief:

```
problems/*.py ──► pipeline (gate + deterministic build) ──► static JSON ──┐
engine/feetcode ─┬─► (CPython, build time)                                ▼
                 └─► Pyodide Web Worker (browser) ◄──► React UI (workspace · visualizer · study)
```

**Stack:** React 19 and TypeScript 5.9, Vite, Tailwind v4 with CSS-variable tokens, react-router 7, zustand, CodeMirror 6 and Pyodide. Python 3.12+ for the engine and pipeline. Netlify or any static host.

## 4. The lens (the design problem you own)

The tracer sees raw locals. Something has to know that `l, r` are pointers *into* `height`, that `dq` holds *indices* into `nums`, that `[r - k + 1, r]` is a window, and that Trapping Rain Water deserves water levels while Container With Most Water deserves a rectangle. The answer is a small per-problem **lens**: a declarative map from variable names to views, pointers, windows and overlays, plus heuristics for code with no lens, such as the user's own code and the playground. It lives in `client/src/viz/scene.ts` and `overlays.ts`, and docs/authoring.md §4 lists its keys. Expect interviewers to probe it.

## 5. Status: built (v3)

**Content**
- 38 problems: the NeetCode 150 core for Arrays & Hashing (9), Two Pointers (5), Sliding Window (6), Stack (7) and Linked List (11).
- Each has 2–3 narrated solutions, pitfalls, hints, an insight card, company tags and a hidden suite (46 cases on average).

**Engine**
- Snapshot tracer with an identity-preserving heap and per-line access facts.
- Deterministic op meter with hidden-cost probes.
- Judge, fuzzer, greedy shrinker, pitfall matcher and passing-neighbour search.
- Complexity profiler (time, auxiliary space, recursion depth).
- Divergence finder: compares your trace with the closest reference on the same input and names the first step, line and variable where they disagree.
- Invariant miner: facts that held in every reference run (a pointer that never decreases, `a ≤ b` for compared pairs), reported when your run breaks one.

**Pipeline**
- Quality gate: schema, examples, cross-checked references, strict narration, pitfall false positives, measured vs declared complexity.
- Deterministic, incremental, parallel build with a sha256 manifest and `--check` drift detection.

**Client**
- Workspace: editor (Vim optional), run, submit, diagnosis, heat map, growth charts, notes, timer, submissions.
- Where it goes wrong: the divergence is a footnote under the guilty line, with *Watch it go wrong* (jumps the player there) and *Compare with the reference* (the reference's run on the same input, code hidden unless you ask).
- Live values at the end of each line as you step, and variable tracks: one row per variable across the whole run, with the divergence marked.
- Visualizer: arrays, bars, chars, grids, maps, sets, stacks and deques, linked lists with stable layout, random-pointer graphs.
- Lens overlays: water, container, histogram, index graph.
- Narrated lessons, auto-narration and Predict mode.
- Tonight: a nightly session planned from the event log (recall what's fading, fix what's broken, one new problem, a stretch into the next pattern), walked from a header pill.
- Your path: every problem as a star on one map of the roadmap, lit as you solve and brighter as you review.
- Pattern primers, spaced-repetition review, stats with streaks, a heat map and mastery, NDJSON export, and a playground with share links.
- The problem list hides each problem's trick and optimal complexity until you've solved it.
- Command palette, light and dark themes.

**Quality**
- Engine tests in CPython 3.12 and 3.13 and in Pyodide; pipeline tests; Vitest; Playwright end-to-end on real Pyodide.
- CI runs all of them plus the content gate and the drift check.

## 6. Roadmap

**Next: the analyzers that make it a lab**
1. **Richer invariants.** The miner knows monotonic integers and compared pairs. Next: structural facts like "the window has no duplicates" and "the stack is monotonic", and invariants over inner frames.
2. **Divergence for renamed code.** Today the finder needs at least one variable name in common with a reference. Matching variables by the shape of their histories would cover code that names everything differently.
3. **Approach fingerprinting.** Classify *how* the user solved it (two pointers vs hash map vs sort) from trace dynamics, and suggest the matching lesson.

**Content**
4. The rest of the NeetCode 150: binary search, trees, tries, heap / priority queue, backtracking, graphs, 1-D and 2-D DP, greedy, intervals, math and bits. Trees and graphs need a tree layout in `viz/graph.ts`, and the engine already preserves identity.

**Product**
5. A mock-interview mode: timer, hidden hints, a scored debrief built from the event log.
6. Optional device sync of the event log (merge logs, re-fold). Still no execution servers.
7. More languages are out of scope until the analyzers above exist. Python first, done well.

## 7. Design system

Identity: **a late-night study session, annotated.**

- **Surfaces:** a night sky (deep indigo with a faint starfield) in dark; "daybreak" lavender-white in light.
- **Text:** paper.
- **Color (Nocturne):** one rule, so color always carries meaning. Magenta (`accent`) is you: your code, your run, your next action. Cyan (`ref`) is the reference: what's correct and what matches it. Yellow (`warn`) is where the two disagree. Violet (`note`) is annotations. Sky marks water and windows.
- **Type:** Bricolage Grotesque for display, Geist for UI and JetBrains Mono for code and data.
- **Brand mark:** superscript numerals (`feetcode¹`).

All tokens live in `client/src/styles/index.css` with light and dark themes. Components never hardcode colors. Cell states (`idle / active / compare / match / new / done`) carry meaning and map to presentation in exactly one place.

## 8. Quality bar

- Keyboard-operable everything: transport, split panes, palette.
- Visible focus and `prefers-reduced-motion`. Layouts respond via container queries.
- Every claim the UI makes is computed, not asserted: complexity labels are measured, and examples are checked.
- Conventional commits, with CI green before merge.

## 9. What changed from v2

| v2 plan | v3 reality | Why |
| --- | --- | --- |
| LLM-generated step scripts and a JSON schema | Problems as code; lessons are *real traces* of reference solutions with `#>` narration | A generated script describes what code should do. A trace shows what it does, and the same tracer then works on user code. |
| Golden hand-crafted script | Quality gate over executable content | Tests scale; hand review doesn't. |
| Judge as a "commodity" afterthought | Deterministic op-budget judge | In-browser wall clocks are unfair and noisy, and op counts also power the complexity lab. |
| JavaScript renderer per structure type | Lens + heuristics over a generic heap | Needed to visualize *arbitrary* user code. |
| Phased P1 → P5 | Engine, pipeline and client built together; differ and miner next | The engine is the product. Everything else is a view of it. |

## 10. Out of scope

Execution servers of any kind, payments, contests, social feeds and native mobile apps. Accounts only if device sync ships, and even then the event log stays the source of truth.
