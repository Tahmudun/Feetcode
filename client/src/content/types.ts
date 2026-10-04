/** Contracts for the artifacts produced by `python -m feetcode_pipeline build`. */

import type { Trace } from "@/runtime/types";

export type Difficulty = "Easy" | "Medium" | "Hard";
export type PatternId = "arrays-hashing" | "two-pointers" | "sliding-window" | "stack" | "linked-list";

export interface ProblemSummary {
  id: string;
  number: number;
  title: string;
  difficulty: Difficulty;
  pattern: PatternId;
  order: number;
  companies: Record<string, number>;
  topics: string[];
  module: string;
  kind: "function" | "design" | "codec";
  oneLiner: string;
  optimal: { time: string; space: string };
}

export interface Catalog {
  version: string;
  problems: ProblemSummary[];
}

export interface Footnote {
  line: number;
  text: string;
  step?: number;
}

export interface SolutionInfo {
  id: string;
  name: string;
  time: string;
  space: string;
  idea: string;
  optimal: boolean;
  code: string;
  footnotes: Footnote[];
}

export interface Insight {
  pattern: string;
  oneLiner: string;
  mnemonic: string;
  why: string;
  signals?: string[];
  recall: { q: string; a: string }[];
}

export interface ArrayLens {
  view?: "cells" | "bars" | "chars";
  pointers?: string[];
  window?: [string, string];
}

export interface Lens {
  arrays?: Record<string, ArrayLens>;
  maps?: Record<string, { key?: "letter-counts" }>;
  overlay?: "water" | "container" | "histogram" | "index-graph";
  stacks?: string[];
  grids?: string[];
  hide?: string[];
  indexes?: Record<string, string>;
  nodes?: { random?: boolean; prev?: boolean };
}

export interface Signature {
  kind: "function" | "design" | "codec";
  method: string;
  cls: string;
  returns: string;
  inplace: string | null;
  params: { name: string; type: string }[];
  inputs: string[];
}

export interface Example {
  args: Record<string, unknown>;
  output: unknown;
  explain: string;
}

export interface ProblemDetail extends ProblemSummary {
  slug: string;
  url: string;
  patternName: string;
  statement: string;
  examples: Example[];
  constraints: string[];
  hints: string[];
  insight: Insight;
  solutions: SolutionInfo[];
  pitfalls: { id: string; title: string; explain: string }[];
  signature: Signature;
  starter: string;
  lens: Lens;
  followUp: string;
  related: string[];
  sizes: number[];
  lessonArgs: Record<string, unknown>;
}

export interface SuiteCase {
  kind: "example" | "edge" | "random" | "large" | "stress";
  args: Record<string, unknown>;
  expected: unknown;
  budget: number;
  refOps: number;
}

export interface Suite {
  id: string;
  cases: SuiteCase[];
}

export interface Lessons {
  id: string;
  args: Record<string, unknown>;
  traces: Record<string, Trace>;
}

export interface BaselineSeries {
  points: { n: number; ops: number | null; capped: boolean }[];
  time: string | null;
  slope: number | null;
  space: string | null;
}

export interface Baselines {
  id: string;
  sizes: number[];
  solutions: Record<string, BaselineSeries>;
}

export interface PatternInfo {
  id: PatternId;
  name: string;
  tagline: string;
  summary: string;
  signals: string[];
  ideas: { title: string; text: string }[];
  template: string;
  complexity: string;
  problems: string[];
}

export type Companies = Record<string, { id: string; tier: number }[]>;
