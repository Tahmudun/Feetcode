# 0001 · Time limits are operation budgets, not wall-clock timeouts

**Status:** accepted

## Context

A judge has to tell an O(n²) solution from an O(n) one. Online judges do this with wall-clock limits on dedicated, uniform hardware. Feetcode runs on the *user's* machine, inside WebAssembly: a 2015 laptop on battery and a new desktop can differ by 10×, and a garbage-collection pause or a busy tab adds noise on top. A wall-clock verdict would be unfair, and it would not be reproducible.

The complexity lab has the same problem. Fitting a growth curve to millisecond timings needs many repetitions and still wobbles, especially at small `n`.

## Decision

Measure **operations**: one per executed line of user code (counted by a `sys.settrace` hook), plus a size-weighted cost for builtins that hide linear work. That covers `x in list`, `list.pop(0)`, slicing, concatenation, `sorted` and walking a linked list (`analysis.probe_cost`).

Each hidden test case gets a budget of `max(25 000, 20 × ops of the optimal reference on that case)`, computed at build time and shipped with the suite. Exceeding it raises `BudgetExceeded`. That class subclasses `BaseException`, so `except Exception:` in user code cannot swallow the stop.

## Consequences

- **Reproducible verdicts.** The same code on the same input costs the same on every machine and every run. This is tested in CPython and Pyodide.
- **Noise-free complexity curves.** Op counts are exact, so model fitting needs one run per size.
- **The 20× factor separates classes, not constants.** A solution with a 3× worse constant still passes. An O(n²) one fails on the large cases. The build logs every reference solution's verdict against the final suite (e.g. `brute=tle two-pointers=accepted`), and a pipeline test asserts this separation for Two Sum.
- **Cost model limits.** A line is not a uniform unit: `x = 1` and `d[k] = sorted(v)` differ. Probes cover the common hidden-linear builtins, and C-level work they don't model still counts as one op. In practice the class boundary is what matters for interview problems, and it is preserved.
- **Tracing overhead.** The hook slows execution several-fold. That's acceptable at interview-problem sizes. A wall-clock watchdog (ADR 0007) still guards against code that never returns to Python.

## Alternatives considered

- **Wall-clock limits, scaled by a calibration benchmark.** Still noisy, still machine-dependent, and gameable by a slow first run.
- **CPython bytecode counting (`f_trace_opcodes`).** Finer-grained but much slower, and per-opcode counts are harder to explain to a learner than "this line ran 524,798 times".
