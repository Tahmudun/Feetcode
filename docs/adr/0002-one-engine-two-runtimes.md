# 0002 · One Python engine, two runtimes

**Status:** accepted

## Context

Several things must agree exactly:

- the build-time answers (expected outputs, op budgets, lesson traces, baseline curves)
- the browser-time judgement of user code

If the browser used a reimplementation, for example a JavaScript tracer or a JS port of the comparators, every difference would become a wrong verdict or a lesson that doesn't match what the user's code does.

## Decision

`engine/feetcode` is a single pure-Python package with **no third-party dependencies**, and it runs in both places:

- the **pipeline** imports it under CPython 3.12+
- the **browser** runs it under Pyodide (CPython 3.14 compiled to WebAssembly)

Vite bundles the engine's `.py` files into the worker as strings (`import.meta.glob(..., { query: "?raw" })`), and the worker writes them into Pyodide's filesystem. Problem modules travel the same way, lazily, one per problem. There is no copy step and no generated mirror, so browser and build always run byte-identical Python.

The engine exposes one entry point, `api.handle(json) -> json`. That keeps the boundary language-neutral and easy to test from both sides.

## Consequences

- **Parity is tested, not assumed.** CI runs the engine's pytest suite on CPython 3.12 and 3.13 and again inside Pyodide under Node (`client/scripts/engine-in-pyodide.mjs`). This caught a real difference: tracemalloc granularity on 32-bit WebAssembly made a hash map look O(n²) in space. That led to the slope-based space classifier.
- **Python ≥ 3.12 is required.** CPython 3.11 emits no line event for `while True: pass`, so an infinite loop could not be metered. 3.12 also inlines comprehensions, which the tracer normalizes.
- **The engine cannot use NumPy or other native packages** without loading them into Pyodide too. Least-squares fitting is a few lines of pure Python.
- **The first visit downloads Python** (about 13 MB, then cached). The UI stays usable while it loads, and lessons are precomputed so they need no Python at all.
