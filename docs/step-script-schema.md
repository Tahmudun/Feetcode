# Step-Script Schema — v1

A step script is a JSON file describing one solution's execution as a sequence of **complete
visual snapshots**. The Step Player renders `steps[i]` as a pure function — no replay, no
accumulated state. This file is the contract between the AI generation pipeline and the renderer.
Breaking changes bump `schemaVersion`.

## Top level

```jsonc
{
  "schemaVersion": 1,
  "problemId": "group-anagrams",      // matches data/problems.js id
  "solutionId": "char-count-key",     // a problem can have many solutions/scripts
  "title": "Hash map keyed by character counts",
  "language": "python",
  "complexity": { "time": "O(n·k)", "space": "O(n·k)" },
  "code": ["def groupAnagrams(strs):", "..."],  // displayed lines, 0-indexed by array position
  "steps": [ /* Step objects, in order */ ]
}
```

## Step object

```jsonc
{
  "line": 2,                 // 0-based index into code[]; the highlighted line. -1 = none
  "phase": "iterate",        // setup | iterate | resolve — drawn as tick groups on the scrubber
  "narration": "Plain-English, one or two sentences, present tense.",
  "structures": [ /* full state of EVERY structure, EVERY step */ ],
  "pointers":   [ { "structure": "strs", "index": 0, "label": "word" } ],
  "vars":       [ { "name": "key", "value": "a1e1t1", "state": "new" } ]
}
```

## Structure types (v1)

**array** — `{ "id", "type": "array", "label", "cells": [ { "v": "eat", "state": "active" } ] }`

**map** — `{ "id", "type": "map", "label", "entries": [ { "k": "a1e1t1", "v": "[eat, tea]", "state": "match" } ] }`

`set`, `stack`, `pointerPair` are reserved for the next scripts; `linkedlist`, `tree`, `heap`,
`grid` are reserved for v2. The renderer must ignore unknown types gracefully (forward compat).

## Cell/entry/var states

| state     | meaning                                | color token |
|-----------|----------------------------------------|-------------|
| `idle`    | present, not in play this step         | --muted     |
| `active`  | the element being processed            | --amber     |
| `compare` | being examined against something       | --rose      |
| `match`   | comparison succeeded / lookup hit      | --teal      |
| `new`     | created this step                      | --amber     |
| `done`    | finalized, will not change again       | --teal-dim  |

The AI writes **meaning**, the renderer maps meaning → presentation. Never put colors, pixels, or
layout in a script.

## Footnotes (added in scope v2.0 — additive, no version bump)

Optional top-level array. Footnotes are the product's single output type for explanations:
authored insights now; analyzer findings (P4+) later use the same shape.

```jsonc
"footnotes": [
  {
    "id": 1,            // display number, unique, ascending
    "line": 6,          // 0-based code line the marker attaches to
    "text": "Why this line is the way it is. ≤ 280 chars, no markdown.",
    "step": 2           // optional: a step index this note deep-links to
  }
]
```

Rendering contract: a superscript marker after the code on `line`; a footnote block below the
player (hairline rule, hanging numbers); hovering either side highlights both; `step` renders a
jump link that seeks the player.

## Invariants (the validator enforces these; the generator must satisfy them)

1. Every `line` ∈ [-1, code.length).
2. Every structure id appears in **every** step (snapshots are complete).
3. States only from the enum above.
4. `steps[0].phase === "setup"`, last step `phase === "resolve"`.
5. The final step's structures must encode the expected output (per-problem check).
6. Narration ≤ 220 chars, no markdown, present tense.

## Authoring guidance (for the generation prompt and for humans)

One step = one *idea*, not one executed instruction. Collapse tight inner loops (e.g. counting
characters) into a single step whose narration summarizes the result. Target 12–25 steps per
script. The first step orients ("here's the plan"); the last step states the takeaway pattern
("anagrams collide on a canonical key").
