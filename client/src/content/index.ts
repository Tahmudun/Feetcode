/**
 * Typed access to pipeline artifacts. The catalog, patterns and companies are
 * small and bundled eagerly; per-problem detail, hidden suites, lessons and
 * baselines are code-split and fetched only when a problem is opened.
 */
import catalogJson from "./generated/catalog.json";
import patternsJson from "./generated/patterns.json";
import companiesJson from "./generated/companies.json";
import type { Baselines, Catalog, Companies, Lessons, PatternId, PatternInfo, ProblemDetail, ProblemSummary, Suite } from "./types";

export const catalog = catalogJson as unknown as Catalog;
export const patterns = patternsJson as unknown as PatternInfo[];
export const companies = companiesJson as unknown as Companies;

export const problems: ProblemSummary[] = catalog.problems;
export const problemById = new Map(problems.map((p) => [p.id, p]));
export const patternById = new Map(patterns.map((p) => [p.id, p]));

export const PATTERN_ORDER: PatternId[] = patterns.map((p) => p.id);

type Loader<T> = () => Promise<T>;
const glob = {
  problems: import.meta.glob("./generated/problems/*.json", { import: "default" }) as Record<string, Loader<ProblemDetail>>,
  suites: import.meta.glob("./generated/suites/*.json", { import: "default" }) as Record<string, Loader<Suite>>,
  lessons: import.meta.glob("./generated/lessons/*.json", { import: "default" }) as Record<string, Loader<Lessons>>,
  baselines: import.meta.glob("./generated/baselines/*.json", { import: "default" }) as Record<string, Loader<Baselines>>,
};

const cache = new Map<string, Promise<unknown>>();

function load<T>(kind: keyof typeof glob, id: string): Promise<T> {
  const key = `${kind}/${id}`;
  let p = cache.get(key) as Promise<T> | undefined;
  if (!p) {
    const loader = glob[kind][`./generated/${kind}/${id}.json`] as Loader<T> | undefined;
    p = loader ? loader() : Promise.reject(new Error(`No ${kind} artifact for "${id}"`));
    cache.set(key, p);
  }
  return p;
}

export const loadProblem = (id: string) => load<ProblemDetail>("problems", id);
export const loadSuite = (id: string) => load<Suite>("suites", id);
export const loadLessons = (id: string) => load<Lessons>("lessons", id);
export const loadBaselines = (id: string) => load<Baselines>("baselines", id);

/** Neighbours in roadmap order, for "next problem" navigation. */
export function neighbours(id: string): { prev?: ProblemSummary; next?: ProblemSummary } {
  const i = problems.findIndex((p) => p.id === id);
  return { prev: problems[i - 1], next: problems[i + 1] };
}

export const COMPANY_NAMES = Object.keys(companies);
