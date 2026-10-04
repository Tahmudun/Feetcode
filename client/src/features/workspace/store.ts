import { create } from "zustand";
import { loadSuite } from "@/content";
import type { ProblemDetail } from "@/content/types";
import { draftKey, storage } from "@/lib/storage";
import { engine } from "@/runtime/engine";
import { RuntimeTimeout } from "@/runtime/python";
import type { RunResult, SubmitResult, Trace } from "@/runtime/types";
import { logEvent } from "@/store/events";
import type { EditorMarks } from "@/editor/CodeEditor";

export type LeftTab = "description" | "learn" | "visualize" | "submissions" | "notes";
export type ConsoleTab = "tests" | "result" | "analysis";

export interface TestCase {
  args: Record<string, unknown>;
  expected?: unknown;
  custom?: boolean;
}

export interface Submission {
  ts: number;
  verdict: SubmitResult["verdict"];
  code: string;
  passed?: number;
  total?: number;
  time?: string;
  space?: string;
}

export interface TraceView {
  trace: Trace;
  label: string;
  args: Record<string, unknown>;
  expected?: unknown;
  startAt?: "end" | number;
}

interface WorkspaceState {
  problem: ProblemDetail | null;
  code: string;
  leftTab: LeftTab;
  consoleTab: ConsoleTab;
  cases: TestCase[];
  activeCase: number;
  busy: "run" | "submit" | "trace" | null;
  runResult: RunResult | null;
  submitResult: SubmitResult | null;
  traceView: TraceView | null;
  marks: EditorMarks;
  error: string | null;
  submitStage: string;

  load: (p: ProblemDetail) => void;
  setCode: (code: string) => void;
  resetCode: () => void;
  setLeftTab: (t: LeftTab) => void;
  setConsoleTab: (t: ConsoleTab) => void;
  setActiveCase: (i: number) => void;
  updateCase: (i: number, args: Record<string, unknown>) => void;
  addCase: () => void;
  removeCase: (i: number) => void;
  setMarks: (m: EditorMarks) => void;
  run: () => Promise<void>;
  submit: () => Promise<void>;
  visualize: (caseIndex?: number) => Promise<void>;
  showTrace: (t: TraceView) => void;
}

const subsKey = (id: string) => `fc:subs:${id}`;
export const loadSubmissions = (id: string) => storage.get<Submission[]>(subsKey(id), []);

let saveTimer: ReturnType<typeof setTimeout> | undefined;

function friendly(err: unknown): string {
  if (err instanceof RuntimeTimeout) return err.message;
  const msg = err instanceof Error ? err.message : String(err);
  return msg.startsWith("Engine error") ? `${msg}. This is a Feetcode bug - please report it.` : msg;
}

export const useWorkspace = create<WorkspaceState>((set, get) => ({
  problem: null,
  code: "",
  leftTab: "description",
  consoleTab: "tests",
  cases: [],
  activeCase: 0,
  busy: null,
  runResult: null,
  submitResult: null,
  traceView: null,
  marks: {},
  error: null,
  submitStage: "",

  load: (p) =>
    set({
      problem: p,
      code: storage.get<string | null>(draftKey(p.id), null) ?? p.starter,
      leftTab: "description",
      consoleTab: "tests",
      cases: p.examples.map((e) => ({ args: structuredClone(e.args), expected: e.output })),
      activeCase: 0,
      busy: null,
      runResult: null,
      submitResult: null,
      traceView: null,
      marks: {},
      error: null,
    }),

  setCode: (code) => {
    set({ code });
    const id = get().problem?.id;
    if (!id) return;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => storage.set(draftKey(id), code), 400);
  },
  resetCode: () => {
    const p = get().problem;
    if (!p) return;
    storage.remove(draftKey(p.id));
    set({ code: p.starter, marks: {} });
  },
  setLeftTab: (leftTab) => set({ leftTab }),
  setConsoleTab: (consoleTab) => set({ consoleTab }),
  setActiveCase: (activeCase) => set({ activeCase }),
  updateCase: (i, args) =>
    set((s) => ({ cases: s.cases.map((c, k) => (k === i ? { args, custom: true } : c)) })),
  addCase: () =>
    set((s) => {
      const base = s.cases[s.activeCase] ?? s.cases[0];
      return { cases: [...s.cases, { args: structuredClone(base.args), custom: true }], activeCase: s.cases.length };
    }),
  removeCase: (i) =>
    set((s) => {
      const cases = s.cases.filter((_, k) => k !== i);
      return { cases, activeCase: Math.max(0, Math.min(s.activeCase, cases.length - 1)) };
    }),
  setMarks: (marks) => set({ marks }),

  run: async () => {
    const { problem, code, cases, busy } = get();
    if (!problem || busy) return;
    set({ busy: "run", consoleTab: "result", error: null, marks: {} });
    try {
      const res = await engine.run(problem, code, cases.map((c) => ({ args: c.args, ...(c.custom ? {} : { expected: c.expected }) })));
      const firstError = res.cases.find((c) => c.error?.line)?.error?.line ?? res.error?.line ?? undefined;
      set({ runResult: res, marks: firstError ? { errorLine: firstError } : {} });
      logEvent({ t: "run", p: problem.id, v: res.verdict, ts: Date.now() });
    } catch (err) {
      set({ error: friendly(err) });
    } finally {
      set({ busy: null });
    }
  },

  submit: async () => {
    const { problem, code, busy } = get();
    if (!problem || busy) return;
    set({ busy: "submit", consoleTab: "analysis", error: null, submitResult: null, submitStage: "Loading hidden tests…", marks: {} });
    try {
      const suite = await loadSuite(problem.id);
      set({ submitStage: `Judging ${suite.cases.length} hidden tests, then fuzzing and profiling…` });
      const res = await engine.submit(
        problem,
        code,
        suite.cases.map((c) => ({ args: c.args, expected: c.expected, budget: c.budget })),
      );
      set({ submitResult: res });
      const time = res.profile?.time?.label;
      const space = res.profile?.space?.label;
      logEvent({ t: "submit", p: problem.id, v: res.verdict, ts: Date.now(), time, space, ops: res.ops });
      const sub: Submission = { ts: Date.now(), verdict: res.verdict, code, passed: res.passed, total: res.total, time, space };
      storage.set(subsKey(problem.id), [sub, ...loadSubmissions(problem.id)].slice(0, 30));
      const errLine = res.failure?.error?.line ?? res.diagnosis?.error?.line ?? res.error?.line ?? undefined;
      if (res.verdict === "compile") set({ marks: { errorLine: res.error?.line ?? undefined } });
      else if (res.trace && res.diagnosis?.args) {
        set({
          traceView: { trace: res.trace, label: "Minimal failing input", args: res.diagnosis.args, expected: res.diagnosis.expected, startAt: "end" },
          marks: errLine ? { errorLine: errLine } : {},
        });
      } else if (res.profile) {
        const notes = res.profile.hidden.map((h, i) => ({ line: h.line, n: i + 1 }));
        set({ marks: { heat: Object.fromEntries(Object.entries(res.profile.lines).map(([k, v]) => [Number(k), v])), notes } });
      }
    } catch (err) {
      set({ error: friendly(err) });
    } finally {
      set({ busy: null, submitStage: "" });
    }
  },

  visualize: async (caseIndex) => {
    const { problem, code, cases, activeCase, busy } = get();
    if (!problem || busy) return;
    const i = caseIndex ?? activeCase;
    const c = cases[i];
    if (!c) return;
    set({ busy: "trace", error: null });
    try {
      const trace = await engine.trace(problem, code, c.args);
      if ((trace as unknown as { verdict?: string }).verdict === "compile") {
        const e = (trace as unknown as RunResult).error;
        set({ error: `SyntaxError on line ${e?.line}: ${e?.message}`, marks: { errorLine: e?.line ?? undefined } });
        return;
      }
      set({ traceView: { trace, label: `Your code · Case ${i + 1}`, args: c.args, expected: c.custom ? undefined : c.expected }, leftTab: "visualize" });
      logEvent({ t: "visualize", p: problem.id, ts: Date.now() });
    } catch (err) {
      set({ error: friendly(err) });
    } finally {
      set({ busy: null });
    }
  },

  showTrace: (traceView) => set({ traceView, leftTab: "visualize" }),
}));
