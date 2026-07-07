# feetcode¹

**A dynamic program analysis lab disguised as a DSA prep site.** Free forever, runs
entirely in the browser, $0/month to operate.

¹ *yes, feet. the footnotes are real.*

<!-- GIF slot: flagship pipeline demo (fuzz → shrink → trace → diverge → footnote).
     Until P4 ships, a Step Player scrub of Group Anagrams goes here. -->

LeetCode tells you *that* you failed. Feetcode shows you **where, why, and how
expensive** — by pointing real program-analysis tooling (a tracer, a fuzzer, a
shrinker, an execution differ) at the code *you* wrote, and explaining everything it
finds in one voice:

> **The Footnote Law: everything Feetcode tells you is a footnote anchored to a line
> of code.**

Insights on reference solutions, narration during playback, the bug the fuzzer found,
the citation to the 1967 paper — all of it renders as numbered footnotes pinned to
exact lines, styled like the apparatus of a real text.

## How it works

```
BUILD TIME (occasionally, offline)
  Anthropic API → reference step-scripts + authored footnotes
  → schema validation → invariant checks → review → committed as static JSON

RUN TIME (React SPA, everything in-browser — no servers, ever)
  the voice      footnotes: insights, findings, citations
  the analyzers  judge → tracer → fuzzer/shrinker → differ   (phased)
  the substrate  step-script schema + Step Player
```

One schema, many producers: the AI pipeline writes scripts for reference solutions;
a `sys.settrace` hook (via Pyodide) will write them for code you typed; the differ
consumes two of them. The player is a pure function of `steps[i]` and doesn't care
where a script came from. Snapshots over deltas buys free scrubbing and trivially
diffable traces — the divergence feature falls out of that decision.

Full design rationale: [SCOPE.md](SCOPE.md). Schema contract:
[docs/step-script-schema.md](docs/step-script-schema.md).

## Status

**P1 — substrate + identity.** Step Player (code / state / narration on one
scrubbable timeline), hand-crafted golden Group Anagrams script, footnote system v1.

Next up: AI reference-content pipeline (P1.5) → in-browser judge (P2) → live tracer
(P3) → the flagship fuzz-shrink-diverge demo (P4).

## Development

```sh
cd client
npm install
npm run dev      # Vite dev server
npm run build    # production build — run before shipping
npm run lint
```

**Stack:** React 19 + Vite, Tailwind + token CSS (all color/type in
`client/src/index.css`), react-router, Netlify. No runtime backend.

## License

[MIT](LICENSE)
