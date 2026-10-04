/** Typed wrappers over the engine's JSON API (engine/feetcode/api.py). */
import type { ProblemSummary } from "@/content/types";
import { python } from "./python";
import type { Diagnosis, Profile, RunResult, SubmitResult, Trace } from "./types";

type Args = Record<string, unknown>;
export interface TestInput {
  args: Args;
  expected?: unknown;
  budget?: number;
}

export const engine = {
  run: (p: ProblemSummary, code: string, tests: TestInput[]) =>
    python.call<RunResult>({ op: "run", module: p.module, code, tests }, { module: p.module, timeoutMs: 15_000 }),

  submit: (p: ProblemSummary, code: string, tests: TestInput[]) =>
    python.call<SubmitResult>({ op: "submit", module: p.module, code, tests }, { module: p.module, timeoutMs: 60_000 }),

  trace: (p: ProblemSummary, code: string, args: Args, maxSteps = 1500) =>
    python.call<Trace>({ op: "trace", module: p.module, code, args, maxSteps }, { module: p.module, timeoutMs: 15_000 }),

  profile: (p: ProblemSummary, code: string) =>
    python.call<Profile>({ op: "profile", module: p.module, code }, { module: p.module, timeoutMs: 30_000 }),

  diagnose: (p: ProblemSummary, code: string, args?: Args) =>
    python.call<Diagnosis>({ op: "diagnose", module: p.module, code, args }, { module: p.module, timeoutMs: 30_000 }),

  playground: (code: string, maxSteps = 1500) =>
    python.call<Trace & { verdict?: string; error: Trace["error"] }>({ op: "playground", code, maxSteps }, { timeoutMs: 15_000 }),
};
