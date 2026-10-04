import { describe, expect, it } from "vitest";
import { DAY_MS } from "@/lib/utils";
import { derive, dueCards, mastery, newCard, schedule, streaks, type StudyEvent } from "./progress";

const T0 = new Date("2026-10-01T12:00:00").getTime();
const at = (days: number) => T0 + days * DAY_MS;

describe("derive (event-sourced progress)", () => {
  it("tracks status transitions and creates a review card on first accept", () => {
    const events: StudyEvent[] = [
      { t: "run", p: "two-sum", v: "wrong", ts: at(0) },
      { t: "submit", p: "two-sum", v: "wrong", ts: at(0) + 1000 },
      { t: "submit", p: "two-sum", v: "accepted", ts: at(0) + 2000, time: "O(n²)" },
      { t: "submit", p: "two-sum", v: "accepted", ts: at(0) + 3000, time: "O(n)" },
    ];
    const p = derive(events, at(0)).byProblem.get("two-sum")!;
    expect(p.status).toBe("solved");
    expect(p.attempts).toBe(4);
    expect(p.bestTime).toBe("O(n)");
    expect(p.card?.due).toBe(at(0) + 2000 + DAY_MS);
  });

  it("is order-independent of unrelated problems and replayable", () => {
    const a: StudyEvent[] = [
      { t: "run", p: "x", v: "accepted", ts: at(0) },
      { t: "lesson", p: "y", s: "opt", ts: at(1) },
    ];
    expect(derive(a).byProblem.get("y")!.lessons.has("opt")).toBe(true);
    expect(derive(a).byProblem.get("x")!.status).toBe("attempted");
  });

  it("schedules reviews with growing intervals and resets on lapse", () => {
    let card = newCard(at(0));
    card = schedule(card, 2, at(1));
    expect(card.interval).toBe(1);
    card = schedule(card, 2, at(2));
    expect(card.interval).toBe(3);
    card = schedule(card, 2, at(5));
    expect(card.interval).toBeCloseTo(7.5, 1);
    const lapsed = schedule(card, 0, at(13));
    expect(lapsed.reps).toBe(0);
    expect(lapsed.lapses).toBe(1);
    expect(lapsed.due - at(13)).toBe(10 * 60_000);
    expect(schedule(newCard(0), 3, 0).interval).toBeGreaterThan(schedule(newCard(0), 2, 0).interval);
  });

  it("lists due cards oldest first", () => {
    const events: StudyEvent[] = [
      { t: "submit", p: "a", v: "accepted", ts: at(0) },
      { t: "submit", p: "b", v: "accepted", ts: at(-1) },
    ];
    expect(dueCards(derive(events), at(1) + 1)).toEqual(["b", "a"]);
    expect(dueCards(derive(events), at(0))).toEqual(["b"]);
  });

  it("counts streaks back from today, surviving until the day ends", () => {
    const activity = new Map([["2026-09-28", 1], ["2026-09-29", 2], ["2026-09-30", 1], ["2026-09-25", 1]]);
    expect(streaks(activity, new Date("2026-09-30T20:00:00").getTime())).toEqual({ streak: 3, longest: 3 });
    expect(streaks(activity, new Date("2026-10-01T09:00:00").getTime()).streak).toBe(3); // yesterday still counts
    expect(streaks(activity, new Date("2026-10-02T09:00:00").getTime()).streak).toBe(0);
  });

  it("mastery rewards solving, reviewing and understanding", () => {
    const solvedOnly = derive([{ t: "submit", p: "a", v: "accepted", ts: at(0) }]).byProblem.get("a");
    const reviewed = derive([
      { t: "submit", p: "a", v: "accepted", ts: at(0) },
      { t: "lesson", p: "a", s: "opt", ts: at(0) },
      { t: "review", p: "a", g: 2, ts: at(1) },
      { t: "review", p: "a", g: 2, ts: at(2) },
    ]).byProblem.get("a");
    expect(mastery(undefined)).toBe(0);
    expect(mastery(reviewed)).toBeGreaterThan(mastery(solvedOnly));
    expect(mastery(reviewed)).toBeLessThanOrEqual(1);
  });
});
