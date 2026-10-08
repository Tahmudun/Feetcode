import { describe, expect, it } from "vitest";
import { patterns, problems } from "@/content";
import { ROADMAP } from "@/content/roadmap";
import { VIEW, layoutPath } from "./path";

describe("layoutPath", () => {
  const layout = layoutPath(patterns, problems);

  it("places every problem exactly once, inside the view", () => {
    expect(layout.stars.map((s) => s.id).sort()).toEqual(problems.map((p) => p.id).sort());
    for (const s of layout.stars) {
      expect(s.x).toBeGreaterThan(0);
      expect(s.x).toBeLessThan(VIEW.width);
      expect(s.y).toBeGreaterThan(0);
      expect(s.y).toBeLessThan(VIEW.height);
    }
  });

  it("is deterministic: the sky never moves between visits", () => {
    expect(layoutPath(patterns, problems)).toEqual(layout);
  });

  it("reads left to right in roadmap order inside each pattern", () => {
    for (const p of patterns) {
      const xs = layout.stars.filter((s) => s.pattern === p.id).map((s) => s.x);
      expect(xs).toEqual([...xs].sort((a, b) => a - b));
    }
  });

  it("links consecutive problems and bridges every roadmap edge", () => {
    expect(layout.lines.length).toBe(problems.length - patterns.length);
    expect(layout.bridges.map((b) => [b.pattern, b.next])).toEqual(ROADMAP);
    for (const b of layout.bridges) {
      const from = layout.stars.find((s) => s.id === b.from)!;
      const to = layout.stars.find((s) => s.id === b.to)!;
      expect(to.x).toBeGreaterThan(from.x - 1); // later patterns sit further along the path
    }
  });
});
