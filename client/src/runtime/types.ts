/**
 * Shapes returned by the Python engine (engine/feetcode). The engine speaks JSON
 * only, so these types are the whole contract between Python and the UI.
 */

/** An encoded Python value (engine/feetcode/values.py). */
export type PyVal =
  | number
  | string
  | boolean
  | null
  | { r: number }
  | { f: string }
  | { big: string }
  | { fn: string }
  | { repr: string };

export type HeapObj =
  | ["list" | "tuple" | "deque" | "set", PyVal[], number?]
  | ["dict", [PyVal, PyVal][], (number | null)?, string?]
  | ["obj", string, [string, PyVal][]];

export type Heap = Record<string, HeapObj>;

export interface Access {
  o?: number; // heap id of the container/object
  v?: string; // variable name (strings, or for display)
  i?: number; // index (sequences)
  ei?: number; // entry index (dict/set, -1 = absent)
  kr?: string; // key repr
  f?: string; // field written (objects)
  m: "r" | "w" | "c" | "del" | "in" | "push" | "pushl" | "pop";
  hit?: number;
  oob?: number;
}

export interface Frame {
  f: string;
  id: number;
  l: number;
  v: [string, PyVal][];
}

export interface Step {
  k: "call" | "line" | "return" | "exc";
  l: number;
  n?: number;
  b?: 0 | 1;
  a?: Access[];
  s: Frame[];
  h: Heap;
  r?: PyVal;
  x?: string;
  t?: string;
  o?: number;
  hide?: 1;
}

export interface EngineError {
  type: string;
  message: string;
  line: number | null;
  col?: number | null;
  trace?: string[];
}

export interface Trace {
  code: string;
  steps: Step[];
  truncated: boolean;
  output?: unknown;
  returned?: { v: PyVal; h: Heap };
  footnotes: { line: number; text: string }[];
  error: EngineError | null;
  stdout?: string;
  ops?: number;
}

export type Verdict = "accepted" | "wrong" | "error" | "tle" | "compile";

export interface CaseResult {
  status: "ok" | "tle" | "error";
  output?: unknown;
  expected?: unknown;
  error?: EngineError;
  pass: boolean;
  ms: number;
  ops: number;
  hidden: number;
  stdout?: string;
  invalid?: boolean;
}

export interface RunResult {
  verdict: Verdict;
  cases: CaseResult[];
  error?: EngineError;
}

export interface Diagnosis {
  found: boolean;
  origin?: "test" | "fuzz";
  args?: Record<string, unknown>;
  expected?: unknown;
  actual?: unknown;
  status?: "wrong" | "error" | "tle";
  error?: EngineError | null;
  originalSize?: number;
  size?: number;
  shrinkSteps?: number;
  pitfalls?: { id: string; title: string; explain: string }[];
  neighbour?: { args: Record<string, unknown>; output: unknown } | null;
}

export interface FitResult {
  label: string;
  slope?: number;
  a?: number;
  b?: number;
  error?: number;
  source?: string;
}

export interface Profile {
  points: { n: number; ops: number | null; hidden?: number; depth?: number; ms?: number; mem?: number; capped?: boolean }[];
  time: FitResult | null;
  space: FitResult | null;
  n: number | null;
  lines: Record<string, number>;
  hidden: { line: number; cost: number; probes: { label: string; hint: string }[] }[];
  stopped: { n: number; reason: string; message?: string } | null;
}

export interface SubmitResult {
  verdict: Verdict;
  passed?: number;
  total?: number;
  ops?: number;
  ms?: number;
  foundBy?: "fuzzer";
  failure?: CaseResult & { index: number; args: Record<string, unknown> | null; argsSummary?: string };
  diagnosis?: Diagnosis;
  trace?: Trace;
  profile?: Profile;
  error?: EngineError;
}
