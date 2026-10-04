# Trace format

A **trace** is what the engine returns for `{"op": "trace"}` (your code), `{"op": "playground"}` (any script), and what the pipeline stores per solution in `lessons/<id>.json`. The visualizer's input is exactly this format, so the renderer is a pure function of `steps[i]` ([ADR 0003](adr/0003-snapshot-traces.md)).

Sources of truth:
- `engine/feetcode/tracer.py`, `engine/feetcode/values.py`: what the engine produces
- `client/src/runtime/types.ts`: the TypeScript types the client consumes

The two must change together. Fields are only ever **added**. Consumers ignore fields they don't know, so an addition needs no version bump. Renaming or removing a field, or changing a field's meaning, requires changing the engine, the client types, the scene builder and this document in the same commit, then rebuilding the content (an engine change invalidates every artifact anyway; see [ADR 0005](adr/0005-deterministic-incremental-pipeline.md)).

## Trace

```jsonc
{
  "code": "class Solution: ...",          // the exact source that ran
  "steps": [ /* Step, in execution order */ ],
  "truncated": false,                     // true if MAX_STEPS (1500) was hit
  "footnotes": [{ "line": 5, "text": "…" }],  // from #! directives (reference solutions)
  "output": [0, 1],                       // the converted return value (JSON), when the call finished
  "returned": { "v": {"r": 3}, "h": { … } },  // the raw encoded return value + its heap
  "error": null,                          // or { type, message, line, col?, trace? }
  "stdout": "",
  "ops": 42                               // operations used (see ADR 0001)
}
```

## Step

One step is one **completed statement** in user code.

| Key | Type | Meaning |
| --- | --- | --- |
| `k` | `"call" \| "line" \| "return" \| "exc"` | Step kind |
| `l` | int | The line that just ran (1-based) |
| `n` | int? | The next line this frame will run, when known (drawn as "← next") |
| `b` | `0 \| 1`? | On `if`/`elif`/`while`/`for` headers: 1 if the body was entered, 0 if skipped or the loop ended |
| `a` | Access[]? | What the line touched (below) |
| `s` | Frame[] | The user call stack, outermost first |
| `h` | Heap | Every container or object reachable from `s` |
| `r` | Value? | Return value (`k: "return"`) |
| `x` | string? | Exception text (`k: "exc"`) |
| `t` | string? | Narration, rendered from a `#>` directive (reference solutions only) |
| `o` | int? | Characters printed to stdout so far |
| `hide` | `1`? | A `#~` directive hides this step in lesson "key steps" mode |

**Frame:** `{ "f": "twoSum", "id": 1, "l": 5, "v": [["nums", {"r": 1}], ["i", 0]] }`. `id` is stable for the life of the call, so recursive frames are distinguishable. `v` holds locals in definition order.

**Normalization.** CPython reports a multi-line statement as `3, 4, 3`, and since 3.12 it reports an inlined comprehension as one line event per iteration. Both collapse into one step. Genuine one-line loops (`while x: x -= 1`) still produce one step per iteration.

## Values

| Python | Encoded |
| --- | --- |
| `None`, `bool`, `int`, `str` | as JSON |
| `int` beyond ±2⁵³ | `{"big": "123…"}` |
| `float` | `{"f": "2.5"}`, so `repr` keeps `1.0` vs `1`, `inf` and `nan` |
| container or user object | `{"r": id}`, a reference into the step's heap |
| function, class, module | `{"fn": "name"}` |
| anything else | `{"repr": "…"}` |

## Heap

`h` maps a stable id (as a string) to a compact array:

```jsonc
["list",  [v, …], len?]              // len only when truncated (MAX_ITEMS = 160)
["tuple", [v, …], len?]
["deque", [v, …], len?]
["set",   [v, …], len?]              // sorted for display stability
["dict",  [[k, v], …], len?, subtype?]   // subtype: "defaultdict" | "Counter" | "OrderedDict"
["obj",   "ListNode", [["val", 1], ["next", {"r": 7}]]]
```

Ids are **identity**. The same Python object has the same id in every step, and two references to one object share an id. That is why `prev` and `curr.next` draw as one node with two arrows, and why `[[0] * 3] * 3` visibly shares one row. A snapshot holds at most 600 objects.

## Access

Accesses come from evaluating each line's AST facts after the line ran (see [ARCHITECTURE.md §1.1](ARCHITECTURE.md#11-line-facts-what-each-line-can-do)).

| Key | Meaning |
| --- | --- |
| `m` | `r` read · `w` write (incl. `set.add`) · `c` read inside a comparison · `del` (incl. `set.remove`) · `in` membership · `push` (`append`, `insert`) · `pushl` (`appendleft`) · `pop` (`pop`, `popleft`) |
| `o` | Heap id of the container or object |
| `v` | Variable name, when the target is a plain name |
| `i` | Index (sequences) |
| `ei` | Entry index in a dict or set (−1 = absent) |
| `kr` | Key, as `repr` |
| `f` | Field written (`curr.next = …` → `"next"`) |
| `hit` | For `in` and dict reads: 1 if present |
| `oob` | 1 if a read was out of bounds (typically the step that raised `IndexError`) |

## Example

Your Two Sum on `nums=[3, 5], target=8`. This is step 3, the `if target - n in seen:` line on the first iteration:

```json
{
  "k": "line", "l": 5, "n": 7, "b": 0,
  "a": [{ "m": "in", "o": 2, "v": "seen", "kr": "5", "ei": -1, "hit": 0 }],
  "s": [{ "f": "twoSum", "id": 1, "l": 7,
          "v": [["nums", {"r": 1}], ["target", 8], ["seen", {"r": 2}], ["i", 0], ["n", 3]] }],
  "h": { "1": ["list", [3, 5]], "2": ["dict", []] },
  "o": 0
}
```

The visualizer draws `nums` with pointer `i` at index 0 and `seen` as an empty map. It marks the probe for key `5` as a miss, labels the branch as skipped, and auto-narrates "condition is False → skip · 5 in seen? no".
