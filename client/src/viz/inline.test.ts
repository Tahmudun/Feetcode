import { describe, expect, it } from "vitest";
import type { Lessons } from "@/content/types";
import { assignedNames, inlineValues } from "./inline";
import { buildTracks, positionOf } from "./tracks";
import twoSumLessons from "@/content/generated/lessons/two-sum.json";
import substringLessons from "@/content/generated/lessons/longest-substring-without-repeating-characters.json";

const trace = (lessons: unknown, id: string) => (lessons as Lessons).traces[id];

describe("assignedNames", () => {
  it.each([
    ["l = best = 0", ["l", "best"]],
    ["for r, c in enumerate(s):", ["r", "c"]],
    ["seen[c] = r", ["seen"]],
    ["water += max_l - height[l]", ["water"]],
    ["max_l, max_r = height[l], height[r]", ["max_l", "max_r"]],
    ["nums[i], nums[j] = nums[j], nums[i]", ["nums"]],
    ["x: int = 5", ["x"]],
    ["x = y == z", ["x"]],
    ["x <<= 2", ["x"]],
    ["s = 'a=b'  # not a=c", ["s"]],
    ["if (n := len(a)) > 3:", ["n"]],
    ["if a == b:", []],
    ["while l <= r:", []],
    ["print(f(x=1))", []],
    ["res.append(x)", []],
    ["self.items = []", []],
    ["return best", []],
  ])("%s", (line, names) => {
    expect(assignedNames(line)).toEqual(names);
  });
});

describe("inlineValues on a real trace", () => {
  const t = trace(twoSumLessons, "hashmap");
  const last = t.steps.length - 1;
  const lineOf = (needle: string) => t.code.split("\n").findIndex((l) => l.includes(needle)) + 1;

  it("shows the current value of what each executed line assigns", () => {
    const v = inlineValues(t, last);
    expect(v[lineOf("seen = {}")]).toMatch(/^seen = \{/);
    expect(v[lineOf("for i, num")]).toMatch(/^i = \d+, num = \d+$/);
  });

  it("shows the return value on the returning line", () => {
    expect(inlineValues(t, last)[t.steps[last].l]).toBe("returns [2, 4]");
  });

  it("shows a branch outcome on the line that just ran", () => {
    const i = t.steps.findIndex((s) => s.b !== undefined && t.code.split("\n")[s.l - 1].trim().startsWith("if"));
    expect(inlineValues(t, i)[t.steps[i].l]).toMatch(/^→ (True|False)$/);
  });

  it("knows nothing about lines that have not run yet", () => {
    expect(inlineValues(t, 1)[lineOf("seen[num] = i")]).toBeUndefined();
  });
});

describe("buildTracks", () => {
  const t = trace(substringLessons, "last-seen");
  const visible = t.steps.map((_, i) => i);
  const tracks = buildTracks(t, visible);

  it("has one row per changing variable, each a run of value segments", () => {
    const names = tracks.map((x) => x.name);
    expect(names).toEqual(expect.arrayContaining(["l", "r", "best"]));
    const best = tracks.find((x) => x.name === "best")!;
    expect(best.segs[best.segs.length - 1].text).toBe("3");
  });

  it("segments tile the steps where the variable exists, in order and without overlap", () => {
    for (const track of tracks) {
      for (let i = 1; i < track.segs.length; i++) expect(track.segs[i].from).toBeGreaterThan(track.segs[i - 1].to);
      for (let i = 1; i < track.segs.length; i++) expect(track.segs[i].text === track.segs[i - 1].text && track.segs[i].from === track.segs[i - 1].to + 1).toBe(false);
    }
  });

  it("in the reference, l only ever moves forward", () => {
    const l = tracks.find((x) => x.name === "l")!;
    const values = l.segs.map((s) => Number(s.text));
    expect(values).toEqual([...values].sort((a, b) => a - b));
  });

  it("maps raw steps to visible positions", () => {
    expect(positionOf([0, 3, 7, 9], 8)).toBe(2);
    expect(positionOf([0, 3, 7, 9], 0)).toBe(0);
  });
});
