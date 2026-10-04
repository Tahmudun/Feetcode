/** Messages between the main thread and the Python worker. Payloads are JSON strings. */

export type WorkerRequest =
  | { type: "init"; id: number }
  | { type: "call"; id: number; payload: string; module?: string };

export type RuntimeStatus = "idle" | "loading" | "ready" | "busy" | "error";

export type WorkerResponse =
  | { type: "status"; status: RuntimeStatus; detail?: string; ms?: number }
  | { type: "result"; id: number; ok: boolean; payload: string };
