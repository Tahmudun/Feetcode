import { describe, expect, it } from "vitest";
import type { Difficulty, PatternId, ProblemSummary } from "@/content/types";
import { DAY_MS } from "@/lib/utils";
import { derive, type StudyEvent } from "./progress";
import { MAX_ITEMS, currentPattern, planSession, sessionState, totalMinutes } from "./session";

const T0 = new Date("2026-10-01T19:00:00").getTime();
const at = (days: number, minutes = 0) => T0 + days * DAY_MS + minutes * 60_000;

const PATTERNS: { id: PatternId; name: string }[] = [
  { id: "arrays-hashing", name: "Arrays & Hashing" },
  { id: "two-pointers", name: "Two Pointers" },
  { id: "sliding-window", name: "Sliding Window" },
  { id: "stack", name: "Stack" },
  { id: "linked-list", name: "Linked List" },
];
const SHAPE: [PatternId, string[]][] = [
  ["arrays-hashing", ["a1", "a2", "a3"]],
  ["two-pointers", ["t1", "t2", "t3"]],
  ["sliding-window", ["w1", "w2"]],
  ["stack", ["s1", "s2"]],
  ["linked-list", ["l1", "l2"]],
];
const problem = (id: string, pattern: PatternId, order: number, difficulty: Difficulty = "Easy"): ProblemSummary => ({
  id, number: 0, title: id, difficulty, pattern, order, companies: {}, topics: [], module: id, kind: "function",
  oneLiner: "", optimal: { time: "O(n)", space: "O(1)" },
});
const PROBLEMS = SHAPE.flatMap(([pat, ids]) => ids.map((id, i) => problem(id, pat, i + 1, i === 2 ? "Medium" : "Easy")));

const solve = (p: string, ts: number): StudyEvent => ({ t: "submit", p, v: "accepted", ts });
const plan = (events: StudyEvent[], now: number) => planSession(derive(events, now), PROBLEMS, PATTERNS, now);

describe("planSession", () => {
  it("starts a brand-new user on the first problem of the path", () => {
    const items = plan([], T0);
    expect(items).toEqual([{ kind: "new", p: "a1", reason: expect.stringContaining("Where the path starts"), minutes: 15 }]);
  });

  it("warms up with due recalls, then the broken problem, then the next new one", () => {
    const events: StudyEvent[] = [
      solve("a1", at(0)),
      solve("a2", at(0, 30)),
      { t: "submit", p: "a3", v: "tle", ts: at(0, 60) },
    ];
    const items = plan(events, at(2));
    expect(items.map((i) => `${i.kind}:${i.p}`)).toEqual(["recall:a1", "recall:a2", "fix:a3", "new:t1"]);
    expect(items[0].reason).toBe("Solved 2 days ago, never recalled. Recall it now and it comes back tomorrow.");
    expect(items[2].reason).toMatch(/op budget/);
    // a3 is broken, so the pattern has nothing new left: the next new problem comes from the path.
    expect(items[3].reason).toMatch(/Next on the path, in Two Pointers/);
    expect(totalMinutes(items)).toBe(2 + 2 + 10 + 15);
  });

  it("keeps new problems in the pattern you're working in", () => {
    const events: StudyEvent[] = [solve("a1", at(0)), solve("t1", at(0, 10))];
    expect(currentPattern(derive(events), PROBLEMS)).toBe("two-pointers");
    const items = plan(events, at(0, 20));
    expect(items).toEqual([expect.objectContaining({ kind: "new", p: "t2", reason: "Next in Two Pointers, where you've solved 1 of 3." })]);
  });

  it("stretches into a pattern that builds on one you've mostly solved", () => {
    const events: StudyEvent[] = [solve("a1", at(0)), solve("a2", at(0, 1)), solve("a3", at(0, 2)), solve("t1", at(0, 3)), solve("t2", at(0, 4)), solve("t3", at(0, 5))];
    const items = plan(events, at(0, 10));
    // Two Pointers is done, so the next new problem is Sliding Window's; Stack (built on Arrays & Hashing) is the stretch.
    expect(items.map((i) => `${i.kind}:${i.p}`)).toEqual(["new:w1", "stretch:s1"]);
    expect(items[1].reason).toBe("You've solved 3 of 3 in Arrays & Hashing. Stack builds on it.");
  });

  it("never stretches before the current pattern is mostly solved", () => {
    const items = plan([solve("a1", at(0))], at(0, 5));
    expect(items.some((i) => i.kind === "stretch")).toBe(false);
  });

  it(`caps the plan at ${MAX_ITEMS} items and gives recalls only the room left over`, () => {
    const events: StudyEvent[] = [
      ...["a1", "a2", "t1", "t2", "t3"].map((p, i) => solve(p, at(0, i))),
      { t: "run", p: "a3", v: "wrong", ts: at(0, 10) },
    ];
    const items = plan(events, at(3));
    expect(items.length).toBe(MAX_ITEMS);
    expect(items.filter((i) => i.kind === "recall").length).toBe(MAX_ITEMS - items.filter((i) => i.kind !== "recall").length);
    expect(items.find((i) => i.kind === "fix")?.reason).toMatch(/You started this one/);
  });
});

describe("sessionState", () => {
  const items = plan([solve("a1", at(0)), { t: "submit", p: "a2", v: "wrong", ts: at(0, 5) }], at(2));
  const start: StudyEvent = { t: "session", p: "", ts: at(2), items };

  it("is derived from the events after the session started", () => {
    expect(items.map((i) => `${i.kind}:${i.p}`)).toEqual(["recall:a1", "fix:a2", "new:a3"]);
    const events: StudyEvent[] = [
      solve("a1", at(0)),
      { t: "submit", p: "a2", v: "wrong", ts: at(0, 5) },
      start,
      { t: "review", p: "a1", g: 2, ts: at(2, 1) },
      { t: "run", p: "a2", v: "wrong", ts: at(2, 3) },
    ];
    const s = sessionState(events, at(2, 4))!;
    expect(s.items.map((i) => i.status)).toEqual(["done", "started", "todo"]);
    expect(s.done).toBe(1);
    expect(s.next?.p).toBe("a2");

    const finished = sessionState([...events, solve("a2", at(2, 9)), solve("a3", at(2, 30))], at(2, 31))!;
    expect(finished.done).toBe(3);
    expect(finished.next).toBeNull();
  });

  it("ignores events from before the session and expires at midnight", () => {
    const events: StudyEvent[] = [solve("a3", at(2, -1)), start];
    expect(sessionState(events, at(2, 1))!.done).toBe(0);
    expect(sessionState(events, at(3))).toBeNull();
    expect(sessionState([], at(2))).toBeNull();
  });

  it("does not leak into per-problem progress", () => {
    const p = derive([start]);
    expect(p.byProblem.size).toBe(0);
    expect(p.activity.size).toBe(0);
  });
});
