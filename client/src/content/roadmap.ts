/**
 * The pattern roadmap: which pattern builds on which (after NeetCode's ordering).
 * Used by the session planner to decide what to stretch into, and by the path view to
 * draw the links between patterns.
 */
import type { PatternId } from "./types";

export const ROADMAP: [from: PatternId, to: PatternId][] = [
  ["arrays-hashing", "two-pointers"],
  ["arrays-hashing", "stack"],
  ["two-pointers", "sliding-window"],
  ["two-pointers", "linked-list"],
];

/** Patterns that `id` builds on. */
export const prerequisites = (id: PatternId): PatternId[] => ROADMAP.filter(([, b]) => b === id).map(([a]) => a);

/** How many roadmap steps from the start a pattern sits (0 for patterns with no prerequisites). */
export function depth(id: PatternId): number {
  const pre = prerequisites(id);
  return pre.length ? 1 + Math.max(...pre.map(depth)) : 0;
}
