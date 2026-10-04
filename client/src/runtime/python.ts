/**
 * Main-thread handle on the Python worker.
 *
 * Two layers stop runaway code:
 *   1. the engine's deterministic operation budget (raises inside Python), and
 *   2. this watchdog: if a call outlives its wall-clock limit (e.g. user code
 *      swallowed the budget exception in a bare `except:`), the worker is
 *      terminated and a fresh one boots - the page never freezes.
 */
import { create } from "zustand";
import type { RuntimeStatus, WorkerRequest, WorkerResponse } from "./protocol";

interface RuntimeState {
  status: RuntimeStatus;
  detail: string;
  bootMs: number | null;
  restarts: number;
}

export const useRuntime = create<RuntimeState>(() => ({ status: "idle", detail: "", bootMs: null, restarts: 0 }));

export class RuntimeTimeout extends Error {
  constructor(seconds: number) {
    super(`Your code ran for more than ${seconds}s and was stopped. Look for a loop that never ends.`);
    this.name = "RuntimeTimeout";
  }
}

interface Pending {
  resolve: (value: string) => void;
  reject: (err: Error) => void;
  timer?: ReturnType<typeof setTimeout>;
}

class PythonRuntime {
  private worker: Worker | null = null;
  private nextId = 1;
  private pending = new Map<number, Pending>();
  private queue: Promise<unknown> = Promise.resolve();

  start() {
    if (this.worker) return;
    useRuntime.setState({ status: "loading", detail: "Starting Python…" });
    this.worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module", name: "feetcode-python" });
    this.worker.onmessage = (e: MessageEvent<WorkerResponse>) => this.onMessage(e.data);
    this.worker.onerror = (e) => {
      useRuntime.setState({ status: "error", detail: e.message || "The Python worker crashed." });
    };
    this.post({ type: "init", id: this.nextId++ });
  }

  private post(msg: WorkerRequest) {
    this.worker!.postMessage(msg);
  }

  private onMessage(msg: WorkerResponse) {
    if (msg.type === "status") {
      useRuntime.setState({
        status: msg.status,
        detail: msg.detail ?? "",
        ...(msg.ms !== undefined ? { bootMs: msg.ms } : {}),
      });
      return;
    }
    const p = this.pending.get(msg.id);
    if (!p) return;
    this.pending.delete(msg.id);
    if (p.timer) clearTimeout(p.timer);
    if (msg.ok) p.resolve(msg.payload);
    else p.reject(new Error(msg.payload));
  }

  private restart() {
    this.worker?.terminate();
    this.worker = null;
    for (const p of this.pending.values()) {
      if (p.timer) clearTimeout(p.timer);
    }
    this.pending.clear();
    useRuntime.setState((s) => ({ restarts: s.restarts + 1 }));
    this.start();
  }

  /** Send one JSON request; calls are serialized (Python is single-threaded anyway). */
  call<T>(request: Record<string, unknown>, opts: { module?: string; timeoutMs?: number } = {}): Promise<T> {
    const run = () =>
      new Promise<T>((resolve, reject) => {
        this.start();
        const id = this.nextId++;
        const timeoutMs = opts.timeoutMs ?? 20_000;
        const entry: Pending = {
          resolve: (raw) => {
            useRuntime.setState({ status: "ready" });
            const env = JSON.parse(raw) as { ok: boolean; data?: T; error?: string; trace?: string };
            if (env.ok) resolve(env.data as T);
            else reject(new Error(`Engine error: ${env.error}`));
          },
          reject: (err) => {
            useRuntime.setState((s) => ({ status: s.status === "busy" ? "ready" : s.status }));
            reject(err);
          },
        };
        // The watchdog starts once the worker is ready to execute (boot time doesn't count).
        const arm = () => {
          entry.timer = setTimeout(() => {
            this.pending.delete(id);
            reject(new RuntimeTimeout(Math.round(timeoutMs / 1000)));
            this.restart();
          }, timeoutMs);
        };
        this.pending.set(id, entry);
        const status = useRuntime.getState().status;
        if (status === "ready") arm();
        else {
          const unsub = useRuntime.subscribe((s) => {
            if (s.status === "ready" || s.status === "busy") {
              unsub();
              if (this.pending.has(id)) arm();
            }
          });
        }
        useRuntime.setState((s) => ({ status: s.status === "ready" ? "busy" : s.status }));
        this.post({ type: "call", id, payload: JSON.stringify(request), module: opts.module });
      });
    const next = this.queue.then(run, run);
    this.queue = next.catch(() => undefined);
    return next;
  }
}

export const python = new PythonRuntime();

/** Boot Python in the background once the page is idle, so the first Run is instant. */
export function warmUp() {
  const go = () => python.start();
  if ("requestIdleCallback" in window) window.requestIdleCallback(go, { timeout: 2500 });
  else setTimeout(go, 800);
}
