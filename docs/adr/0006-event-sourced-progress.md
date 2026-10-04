# 0006 · Study progress is an event log; everything else is derived

**Status:** accepted

## Context

Feetcode tracks more than "solved / not solved": attempts, best complexity reached, lessons watched, spaced-repetition reviews, streaks and per-pattern mastery. Storing each of these as mutable fields invites inconsistency: a streak that disagrees with the history, or a review card that outlives its problem. Every new metric would also need a migration. There is no backend, so the data lives in `localStorage` and must survive app updates.

## Decision

Persist only an **append-only log of immutable events** (`fc:events:v1`). Each event looks like `{ t: "submit", p: "two-sum", v: "accepted", time: "O(n)", ts }`. All views are **derived** by a pure fold, `derive(events, now)`:

- per-problem status, attempts and best complexity
- SM-2-lite review cards: due date, interval, ease, lapses
- streaks (today counts until the day ends) and an activity heat map
- mastery, which rewards solving, reviewing and watching lessons

## Consequences

- **Nothing to migrate.** A new metric is a new fold over old events, and it applies to past history immediately.
- **Testable:** `derive` is a pure function, so tests use plain event arrays and fixed clocks.
- **Portable:** the log exports and imports as NDJSON. The stats page shows a DuckDB query over the export. The log is also the natural format for a future multi-device sync: merge two logs and fold.
- **Cost:** derivation re-folds the whole log each time it changes. That takes milliseconds for thousands of events.
