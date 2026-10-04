# 0003 · Traces are full snapshots, not deltas

**Status:** accepted (carried over from the original v1 step-script design)

## Context

A trace could store the full state at every step (snapshots) or only what changed (deltas). Deltas are smaller. Snapshots are simpler to consume.

## Decision

Every step carries the **complete** user call stack and a **heap** of every container and object reachable from it. Objects get small integer ids that stay stable for the whole trace, and values refer to them as `{"r": id}`. See [../trace-format.md](../trace-format.md).

## Consequences

- **The renderer is a pure function of one step**: `buildScene(trace, i)`. Scrubbing, jumping to the failing step, Predict mode and the hero animation all just pick an index. No replay, and no state that can drift.
- **Identity is visible.** Because the heap preserves identity, `prev` and `curr.next` pointing at the same node draw as one node with two arrows. Aliasing bugs (`[[0] * n] * n`) are visible too.
- **Traces can be compared step by step**, which the planned divergence finder needs.
- **Size.** A snapshot repeats unchanged state. Containers are capped at 160 items and snapshots at 600 objects, traces stop at 1,500 steps, and the JSON compresses well. The largest generated lesson is still small next to the Pyodide download.
- **The tracer pays for encoding every step.** That is fine at visualization sizes. The meter (ADR 0001) is a separate, much lighter hook for judging.
