/**
 * Layout for "Your path": every problem is a star, every pattern a constellation, and the
 * roadmap links one constellation to the next.
 *
 * Pure and deterministic: columns come from roadmap depth, rows from the order of patterns
 * at that depth, and each constellation's shape from a PRNG seeded with its pattern id, so
 * the sky looks hand-drawn but never moves between visits. Coordinates are in a fixed
 * viewBox; the component scales them.
 */
import { ROADMAP, depth } from "@/content/roadmap";
import type { PatternId, ProblemSummary } from "@/content/types";
import { hash } from "@/lib/utils";

export const VIEW = { width: 1000, height: 310 };
const COLUMN_X = [140, 480, 830];
const ROWS = { top: 0, bottom: 290 }; // band the constellations' rows share
const SPREAD_X = 250; // width a constellation spans
const SPREAD_Y = 80; // how far stars wander above and below their row

export interface Star {
  id: string;
  pattern: PatternId;
  x: number;
  y: number;
}

export interface PathLayout {
  stars: Star[];
  /** Consecutive problems inside a pattern. */
  lines: [from: string, to: string][];
  /** Roadmap links: the last star of one pattern to the first star of the next. */
  bridges: { from: string; to: string; pattern: PatternId; next: PatternId }[];
  labels: { pattern: PatternId; x: number; y: number }[];
}

/** mulberry32: a tiny seeded PRNG, so a pattern's shape is a function of its id. */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const round = (x: number) => Math.round(x * 10) / 10;

export function layoutPath(patterns: { id: PatternId }[], problems: ProblemSummary[]): PathLayout {
  const columns = new Map<number, PatternId[]>();
  for (const p of patterns) {
    const d = Math.min(depth(p.id), COLUMN_X.length - 1);
    columns.set(d, [...(columns.get(d) ?? []), p.id]);
  }

  const stars: Star[] = [];
  const lines: PathLayout["lines"] = [];
  const labels: PathLayout["labels"] = [];
  const first = new Map<PatternId, string>();
  const last = new Map<PatternId, string>();

  for (const [d, ids] of columns) {
    ids.forEach((pattern, row) => {
      const cx = COLUMN_X[d];
      const cy = ROWS.top + (ROWS.bottom - ROWS.top) * ((row + 0.5) / ids.length);
      const list = problems.filter((p) => p.pattern === pattern).sort((a, b) => a.order - b.order);
      const rand = rng(parseInt(hash(pattern), 36));
      const phase = rand() * Math.PI * 2;
      list.forEach((p, i) => {
        const t = list.length > 1 ? i / (list.length - 1) : 0.5;
        // A gentle wave plus jitter: reads as a constellation, still left-to-right in roadmap order.
        const wave = Math.sin(phase + t * Math.PI * 1.6) * 0.55 + (rand() - 0.5) * 0.9;
        stars.push({
          id: p.id,
          pattern,
          x: round(cx - SPREAD_X / 2 + t * SPREAD_X + (rand() - 0.5) * 10),
          y: round(cy + wave * (SPREAD_Y / 2)),
        });
        if (i > 0) lines.push([list[i - 1].id, p.id]);
      });
      if (list.length) {
        first.set(pattern, list[0].id);
        last.set(pattern, list[list.length - 1].id);
      }
      labels.push({ pattern, x: cx, y: round(cy + SPREAD_Y / 2 + 22) });
    });
  }

  const bridges = ROADMAP.filter(([a, b]) => last.has(a) && first.has(b)).map(([a, b]) => ({
    from: last.get(a)!,
    to: first.get(b)!,
    pattern: a,
    next: b,
  }));
  return { stars, lines, bridges, labels };
}
