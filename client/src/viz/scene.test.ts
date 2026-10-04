import { describe, expect, it } from "vitest";
import type { Lessons, ProblemDetail } from "@/content/types";
import { buildScene, makeContext, type ArrayPanel, type GraphPanel, type MapPanel, type Scene } from "./scene";
import { autoNarrate } from "./narrate";
import { evalExpr } from "./expr";
import { trueWater } from "./overlays";
import twoSumLessons from "@/content/generated/lessons/two-sum.json";
import twoSum from "@/content/generated/problems/two-sum.json";
import trapLessons from "@/content/generated/lessons/trapping-rain-water.json";
import trap from "@/content/generated/problems/trapping-rain-water.json";
import revLessons from "@/content/generated/lessons/reverse-linked-list.json";
import rev from "@/content/generated/problems/reverse-linked-list.json";
import sudokuLessons from "@/content/generated/lessons/valid-sudoku.json";
import sudoku from "@/content/generated/problems/valid-sudoku.json";
import minStackLessons from "@/content/generated/lessons/min-stack.json";
import minStack from "@/content/generated/problems/min-stack.json";
import swmLessons from "@/content/generated/lessons/sliding-window-maximum.json";
import swm from "@/content/generated/problems/sliding-window-maximum.json";
import lruLessons from "@/content/generated/lessons/lru-cache.json";
import lru from "@/content/generated/problems/lru-cache.json";

function scenes(lessons: unknown, problem: unknown, solution: string): Scene[] {
  const l = lessons as Lessons;
  const p = problem as ProblemDetail;
  const trace = l.traces[solution];
  const ctx = makeContext(trace, p.lens, p.signature.params.map((x) => x.name));
  return trace.steps.map((_, i) => buildScene(trace, i, ctx));
}

describe("scene builder on real traces", () => {
  it("two sum: map probes show hits and misses", () => {
    const all = scenes(twoSumLessons, twoSum, "hashmap");
    const maps = all.map((s) => s.panels.find((p): p is MapPanel => p.kind === "map")).filter(Boolean) as MapPanel[];
    expect(maps.some((m) => m.probe && !m.probe.hit)).toBe(true);
    expect(maps.some((m) => m.probe && m.probe.hit)).toBe(true);
    const last = all[all.length - 1];
    expect(last.ret).toBe("[2, 4]");
    const nums = last.panels.find((p): p is ArrayPanel => p.kind === "array" && p.names.includes("nums"))!;
    expect(nums.pointers.map((p) => p.name)).toContain("i");
  });

  it("trapping rain water: bars with pointers, water overlay and a bottleneck level", () => {
    const all = scenes(trapLessons, trap, "two-pointers");
    const mid = all.find((s) => s.panels.some((p) => p.kind === "array" && p.overlay?.kind === "water" && p.overlay.levels.length === 2))!;
    const bars = mid.panels.find((p): p is ArrayPanel => p.kind === "array")!;
    expect(bars.view).toBe("bars");
    expect(bars.pointers.map((p) => p.name).sort()).toEqual(["l", "r"]);
    const ov = bars.overlay!;
    if (ov.kind !== "water") throw new Error("expected water");
    expect(ov.total).toBe(10);
    expect(ov.levels.filter((l) => l.bottleneck)).toHaveLength(1);
    const end = all[all.length - 1].panels.find((p): p is ArrayPanel => p.kind === "array")!.overlay;
    if (end?.kind !== "water") throw new Error("expected water");
    expect(end.decidedTotal).toBe(10); // every column decided when the pointers meet
  });

  it("reverse linked list: nodes keep their positions while arrows flip", () => {
    const all = scenes(revLessons, rev, "iterative");
    const graphs = all.map((s) => s.panels.find((p): p is GraphPanel => p.kind === "graph")).filter(Boolean) as GraphPanel[];
    const first = graphs[0];
    const last = graphs[graphs.length - 1];
    expect(first.nodes.map((n) => n.label)).toEqual(["1", "2", "3", "4"]);
    const pos = (g: GraphPanel) => Object.fromEntries(g.nodes.map((n) => [n.label, n.col]));
    expect(pos(last)).toEqual(pos(first));
    const colOf = (g: GraphPanel, id: number) => g.nodes.find((n) => n.id === id)!.col;
    // at the start every arrow points right; at the end every arrow points left
    expect(first.edges.every((e) => colOf(first, e.to) > colOf(first, e.from))).toBe(true);
    expect(last.edges.every((e) => colOf(last, e.to) < colOf(last, e.from))).toBe(true);
    expect(graphs.some((g) => g.edges.some((e) => e.state === "new"))).toBe(true);
  });

  it("valid sudoku: a 9x9 grid with 3x3 boxes and highlighted reads", () => {
    const all = scenes(sudokuLessons, sudoku, "one-pass");
    const grid = all[5].panels.find((p) => p.kind === "grid");
    expect(grid && grid.kind === "grid" && grid.rows.length === 9 && grid.box === 3).toBe(true);
    expect(all.some((s) => s.panels.some((p) => p.kind === "grid" && p.rows.flat().some((c) => c.state === "active")))).toBe(true);
  });

  it("min stack: self fields become two stack panels", () => {
    const all = scenes(minStackLessons, minStack, "two-stacks");
    const s = all.find((x) => x.panels.filter((p) => p.kind === "stack").length === 2);
    expect(s?.panels.filter((p) => p.kind === "stack").map((p) => p.names[0]).sort()).toEqual(["self.mins", "self.stack"]);
  });

  it("sliding window maximum: window from a lens expression and deque-marked cells", () => {
    const all = scenes(swmLessons, swm, "deque");
    const s = all.find((x) => x.panels.some((p) => p.kind === "array" && p.window && p.marked?.indices.length))!;
    const nums = s.panels.find((p): p is ArrayPanel => p.kind === "array" && p.names.includes("nums"))!;
    expect(nums.window![1] - nums.window![0]).toBeLessThanOrEqual(2);
    expect(nums.marked!.by).toBe("dq");
  });

  it("lru cache: doubly linked list uses the flow layout and labels sentinels", () => {
    const all = scenes(lruLessons, lru, "dll");
    const g = all.map((s) => s.panels.find((p): p is GraphPanel => p.kind === "graph")).filter(Boolean).pop()!;
    expect(g.edges.some((e) => e.kind === "prev")).toBe(true);
    expect(g.nodes.flatMap((n) => n.vars)).toEqual(expect.arrayContaining(["left", "right"]));
  });

  it("auto narration describes branches and changes", () => {
    const l = twoSumLessons as unknown as Lessons;
    const trace = l.traces.hashmap;
    const lines = trace.code.split("\n");
    const texts = trace.steps.map((_, i) => autoNarrate(trace.steps, i, lines));
    expect(texts[0]).toMatch(/^Call twoSum\(/);
    expect(texts.some((t) => t.includes("condition is False"))).toBe(true);
    expect(texts.some((t) => /in seen\? no/.test(t))).toBe(true);
  });
});

describe("helpers", () => {
  it("evaluates lens window expressions safely", () => {
    expect(evalExpr("r - k + 1", { r: 5, k: 3 })).toBe(3);
    expect(evalExpr("-l", { l: 2 })).toBe(-2);
    expect(evalExpr("r * 2", { r: 1 })).toBeNull();
    expect(evalExpr("alert(1)", {})).toBeNull();
  });
  it("computes trapped water per column", () => {
    expect(trueWater([3, 0, 2, 0, 4])).toEqual([0, 3, 1, 3, 0]);
  });
});
