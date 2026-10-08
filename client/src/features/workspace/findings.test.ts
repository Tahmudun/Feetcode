import { describe, expect, it } from "vitest";
import type { Divergence } from "@/runtime/types";
import { describeDivergence, divergenceFootnote, hasPoint } from "./findings";

// Shapes as the engine returns them for the classic bugs (engine/tests/test_diverge.py).
const base = { solution: "last-seen", optimal: false, matched: 10, trace: { code: "", steps: [], truncated: false, footnotes: [], error: null } };

const backwardsL: Divergence = {
  ...base, kind: "extra", step: 18, line: 7, var: "l", yours: "1", ref: "2", refStep: 13, refLine: 7, shared: ["best", "l", "r"],
  invariant: { kind: "nondecreasing", vars: ["l"], text: "l never decreases", runs: 12, step: 18, line: 7, before: "2", after: "1" },
};

const earlyReturn: Divergence = {
  ...base, solution: "hashmap", kind: "return", step: 5, line: 7, var: null, yours: "[0, 0]", ref: "[0, 1]", refStep: 9, refLine: 7,
  shared: ["i", "seen"], invariant: null,
};

describe("divergence findings", () => {
  it("pins the note to the divergent line and offers to show the step", () => {
    const note = divergenceFootnote(backwardsL, "Moved l backwards")!;
    expect(note.line).toBe(7);
    expect(note.title).toBe("Moved l backwards");
    expect(note.body).toContain("At step 19, your l became 1; the reference's l stays 2.");
    expect(note.body).toContain("In all 12 reference runs we tried, l never decreases; here yours goes 2 → 1.");
    expect(note.actions?.map((a) => a.id)).toEqual(["jump", "compare"]);
  });

  it("names the broken invariant when no pitfall matched", () => {
    expect(describeDivergence(backwardsL)!.title).toBe('Breaks "l never decreases"');
  });

  it("explains an early return with both answers", () => {
    const f = describeDivergence(earlyReturn)!;
    expect(f.title).toBe("Returns [0, 0]; the reference returns [0, 1]");
    expect(f.body).toContain("agrees with the reference on i and seen");
  });

  it("states facts, never the fix", () => {
    const note = divergenceFootnote(backwardsL)!;
    expect(note.body).not.toMatch(/guard|>=|max\(|should/i);
  });

  it("has nothing to pin when the runs agree", () => {
    const agree: Divergence = { ...earlyReturn, kind: "agree", step: null, line: null };
    expect(hasPoint(agree)).toBe(false);
    expect(divergenceFootnote(agree)).toBeUndefined();
  });
});
