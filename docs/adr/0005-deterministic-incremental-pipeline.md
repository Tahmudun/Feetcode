# 0005 · The content build is deterministic, incremental and drift-checked

**Status:** accepted

## Context

The client ships pre-built JSON: problem details, hidden suites with expected outputs and budgets, narrated lesson traces, and baseline growth curves. Building all of it means executing every reference solution many times, which takes minutes. The artifacts are committed, so the site deploys as static files with no build-time Python. That raises two risks: artifacts can go stale against their sources, and rebuilds can churn diffs.

## Decision

- **Deterministic:** every random input comes from an RNG seeded from the problem id. JSON is written canonically (sorted keys, fixed separators). The same inputs produce byte-identical outputs.
- **Incremental:** `manifest.json` records, per problem, a sha256 of the problem module's source, the **engine digest** (a hash over all engine files) and `PIPELINE_VERSION`. A build recomputes only problems whose key changed, and an engine change rebuilds everything.
- **Parallel:** stale problems build in a process pool.
- **Drift-checked:** `build --check` exits non-zero if any artifact would change. CI runs it, so a PR cannot change a problem or the engine without committing the regenerated artifacts.
- **Lineage:** the manifest records which engine and pipeline version produced each artifact.

## Consequences

- A no-op rebuild changes 0 files. Diffs of generated JSON show only real changes, which is reviewable.
- Fixing a narration typo rebuilds one problem in under a second.
- These are the same properties expected of a production data pipeline: idempotence, content-addressed caching, reproducibility, data-quality gates and lineage. Here they are applied to educational content.
- The cost is committed artifacts, about 4 MB of JSON. It buys deploys that need only Node, not Python.
