/**
 * Overlays: problem-specific drawings layered on a bars/cells panel - the "aha"
 * pictures. They read only the array itself and variable *values* (matched by
 * common names), so they work on the learner's own code too, not just ours.
 */
import type { Heap, PyVal } from "@/runtime/types";
import type { ArrayPanel } from "./scene";

export interface Level {
  name: string;
  value: number;
  from: number;
  to: number;
  side: "left" | "right";
  bottleneck: boolean;
}

export type Overlay =
  | { kind: "water"; water: number[]; decided: boolean[]; levels: Level[]; total: number; decidedTotal: number }
  | { kind: "container"; l: number; r: number; height: number; area: number }
  | { kind: "rect"; from: number; to: number; height: number; area: number }
  | { kind: "index-graph"; edges: [number, number][]; hot: Record<string, number> };

const pick = (ints: Record<string, number>, names: string[]) => {
  for (const n of names) if (ints[n] !== undefined) return { name: n, value: ints[n] };
  return null;
};

const LEFT = ["l", "left", "lo", "low"];
const RIGHT = ["r", "right", "hi", "high"];
const MAX_L = ["max_l", "maxL", "left_max", "leftMax", "lmax", "l_max", "maxLeft", "max_left", "lm", "leftmax"];
const MAX_R = ["max_r", "maxR", "right_max", "rightMax", "rmax", "r_max", "maxRight", "max_right", "rm", "rightmax"];

/** Water above each column: min(max to the left, max to the right) − height. */
export function trueWater(h: number[]): number[] {
  const n = h.length;
  const left = new Array<number>(n);
  const right = new Array<number>(n);
  for (let i = 0; i < n; i++) left[i] = Math.max(h[i], i ? left[i - 1] : 0);
  for (let i = n - 1; i >= 0; i--) right[i] = Math.max(h[i], i < n - 1 ? right[i + 1] : 0);
  return h.map((x, i) => Math.max(0, Math.min(left[i], right[i]) - x));
}

export function computeOverlay(
  kind: string | undefined,
  panel: ArrayPanel,
  ints: Record<string, number>,
  _roots: [string, PyVal][],
  _heap: Heap,
): Overlay | undefined {
  const values = panel.cells.map((c) => c.value ?? 0);
  const n = values.length;
  if (kind === "water") {
    const water = trueWater(values);
    const L = pick(ints, LEFT);
    const R = pick(ints, RIGHT);
    const I = pick(ints, ["i"]);
    let decided: boolean[];
    if (L && R) decided = values.map((_, i) => i <= L.value || i >= R.value);
    else if (I) decided = values.map((_, i) => i < I.value);
    else decided = values.map(() => false);
    const levels: Level[] = [];
    const ml = pick(ints, MAX_L);
    const mr = pick(ints, MAX_R);
    if (ml && L) levels.push({ name: ml.name, value: ml.value, from: 0, to: L.value, side: "left", bottleneck: false });
    if (mr && R) levels.push({ name: mr.name, value: mr.value, from: R.value, to: n - 1, side: "right", bottleneck: false });
    if (levels.length === 2) {
      const [a, b] = levels;
      if (a.value < b.value) a.bottleneck = true;
      else b.bottleneck = true;
    }
    const total = water.reduce((s, x) => s + x, 0);
    const decidedTotal = water.reduce((s, x, i) => s + (decided[i] ? x : 0), 0);
    return { kind: "water", water, decided, levels, total, decidedTotal };
  }
  if (kind === "container") {
    const L = pick(ints, [...LEFT, "i"]);
    const R = pick(ints, [...RIGHT, "j"]);
    if (!L || !R || L.value >= R.value || R.value >= n) return undefined;
    const height = Math.min(values[L.value], values[R.value]);
    return { kind: "container", l: L.value, r: R.value, height, area: height * (R.value - L.value) };
  }
  if (kind === "histogram") {
    const i = ints.i;
    if (ints.idx !== undefined && ints.height !== undefined && i !== undefined && ints.idx < i) {
      return { kind: "rect", from: ints.idx, to: i - 1, height: ints.height, area: ints.height * (i - ints.idx) };
    }
    if (ints.low !== undefined && i !== undefined && ints.j !== undefined && ints.j >= i) {
      return { kind: "rect", from: i, to: ints.j, height: ints.low, area: ints.low * (ints.j - i + 1) };
    }
    return undefined;
  }
  if (kind === "index-graph") {
    const edges: [number, number][] = values.map((v, i) => [i, v]);
    const hot: Record<string, number> = {};
    for (const name of ["slow", "fast", "slow2"]) if (ints[name] !== undefined) hot[name] = ints[name];
    return { kind: "index-graph", edges: edges.filter(([, t]) => t >= 0 && t < n), hot };
  }
  return undefined;
}
