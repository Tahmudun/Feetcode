# Architecture decision records

Short records of the decisions that shape Feetcode. Each covers what we decided, why, and what it costs. Read them alongside [../ARCHITECTURE.md](../ARCHITECTURE.md).

| # | Decision |
| --- | --- |
| [0001](0001-deterministic-operation-budgets.md) | Time limits are operation budgets, not wall-clock timeouts |
| [0002](0002-one-engine-two-runtimes.md) | One Python engine runs at build time (CPython) and in the browser (Pyodide) |
| [0003](0003-snapshot-traces.md) | Traces are full snapshots with an identity-preserving heap, not deltas |
| [0004](0004-content-as-code.md) | Problems are Python modules behind a quality gate |
| [0005](0005-deterministic-incremental-pipeline.md) | The content build is deterministic, incremental and drift-checked |
| [0006](0006-event-sourced-progress.md) | Study progress is an event log; everything else is derived |
| [0007](0007-self-hosted-pyodide.md) | Pyodide is self-hosted at a versioned path, in a Web Worker with a watchdog |
