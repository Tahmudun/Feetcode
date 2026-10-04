# 0007 · Self-hosted Pyodide in a Web Worker with a watchdog

**Status:** accepted

## Context

User code must run in the browser (no execution servers, by design), must never freeze the page, and must be stoppable even when it never yields. Pyodide is about 13 MB and is normally loaded from a public CDN.

## Decision

- **Self-host** Pyodide from the npm package. A small Vite plugin serves `/pyodide/v<version>/*` from `node_modules` in dev and copies it into `dist/` on build. The version in the path makes the assets immutable, so the host caches them forever (`netlify.toml`), and an upgrade changes the URL.
- Run Pyodide and the engine in a **module Web Worker**. The UI talks to it through a typed request/response protocol (`runtime/protocol.ts`).
- `runtime/python.ts` serializes requests and arms a **wall-clock watchdog** per operation, sized to the operation. On timeout it **terminates** the worker, rejects the pending request with a clear message and boots a fresh worker.

## Consequences

- There is no third-party CDN dependency at run time, and the deploy fully describes the code it runs.
- The page stays responsive during heavy runs. A runaway is killed, not waited out.
- **Op budgets (ADR 0001) catch nearly all slow code first.** Even `while True: pass` gets a clean Time Limit Exceeded from the meter (an e2e test checks this). The watchdog is the backstop for what the meter cannot see, such as a huge allocation or a long-running builtin.
- A restart costs one Python boot, a few seconds with a warm cache. The user sees a plain message ("Your code ran for more than 15s and was stopped"), and the runtime indicator shows Python loading again.
