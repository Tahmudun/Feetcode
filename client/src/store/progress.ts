/**
 * Event-sourced progress.
 *
 * The only thing persisted is an append-only log of study events. Everything
 * shown in the UI - solved status, streaks, the spaced-repetition schedule,
 * pattern mastery - is a pure fold over that log. That makes the state easy to
 * test, easy to migrate (replay the log with new rules), and exportable as
 * plain data (NDJSON) for anyone who wants to analyse their own studying.
 */
import type { PatternId, ProblemSummary } from "@/content/types";
import type { Verdict } from "@/runtime/types";
import { DAY_MS, dayKey } from "@/lib/utils";

export type Grade = 0 | 1 | 2 | 3; // again | hard | good | easy

export type StudyEvent =
  | { t: "run"; p: string; v: Verdict; ts: number }
  | { t: "submit"; p: string; v: Verdict; ts: number; time?: string; space?: string; ops?: number; code?: string }
  | { t: "lesson"; p: string; s: string; ts: number }
  | { t: "visualize"; p: string; ts: number }
  | { t: "hint"; p: string; n: number; ts: number }
  | { t: "predict"; p: string; ok: boolean; ts: number }
  | { t: "review"; p: string; g: Grade; ts: number };

export interface Card {
  reps: number;
  interval: number; // days
  ease: number;
  due: number; // epoch ms
  lapses: number;
}

export type Status = "new" | "attempted" | "solved";

export interface ProblemProgress {
  status: Status;
  attempts: number;
  submits: number;
  solvedAt: number | null;
  lastAt: number | null;
  bestTime: string | null;
  lessons: Set<string>;
  hints: number;
  predictions: { right: number; total: number };
  card: Card | null;
}

export interface Progress {
  byProblem: Map<string, ProblemProgress>;
  activity: Map<string, number>; // day -> events
  streak: number;
  longestStreak: number;
  solvedCount: number;
}

const ACTIVE = new Set<StudyEvent["t"]>(["run", "submit", "lesson", "review", "predict", "visualize"]);

export function newCard(ts: number): Card {
  return { reps: 0, interval: 1, ease: 2.5, due: ts + DAY_MS, lapses: 0 };
}

/** SM-2 style scheduling, simplified to four buttons. */
export function schedule(card: Card, grade: Grade, ts: number): Card {
  let { reps, interval, ease, lapses } = card;
  if (grade === 0) {
    lapses += 1;
    reps = 0;
    ease = Math.max(1.3, ease - 0.2);
    return { reps, interval: 0, ease, lapses, due: ts + 10 * 60_000 }; // see it again soon
  }
  if (grade === 1) {
    interval = Math.max(1, interval * 1.2);
    ease = Math.max(1.3, ease - 0.15);
  } else if (grade === 2) {
    interval = reps === 0 ? 1 : reps === 1 ? 3 : interval * ease;
  } else {
    interval = reps === 0 ? 3 : interval * ease * 1.3;
    ease += 0.15;
  }
  reps += 1;
  interval = Math.round(interval * 10) / 10;
  return { reps, interval, ease, lapses, due: ts + interval * DAY_MS };
}

function blank(): ProblemProgress {
  return {
    status: "new", attempts: 0, submits: 0, solvedAt: null, lastAt: null, bestTime: null,
    lessons: new Set(), hints: 0, predictions: { right: 0, total: 0 }, card: null,
  };
}

const TIME_RANK = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(n² log n)", "O(n³)", "O(2ⁿ)"];

export function derive(events: StudyEvent[], now = Date.now()): Progress {
  const byProblem = new Map<string, ProblemProgress>();
  const activity = new Map<string, number>();
  const get = (id: string) => {
    let p = byProblem.get(id);
    if (!p) byProblem.set(id, (p = blank()));
    return p;
  };
  for (const e of events) {
    const p = get(e.p);
    p.lastAt = Math.max(p.lastAt ?? 0, e.ts);
    if (ACTIVE.has(e.t)) activity.set(dayKey(e.ts), (activity.get(dayKey(e.ts)) ?? 0) + 1);
    switch (e.t) {
      case "run":
        p.attempts += 1;
        if (p.status === "new") p.status = "attempted";
        break;
      case "submit":
        p.attempts += 1;
        p.submits += 1;
        if (e.v === "accepted") {
          if (p.status !== "solved") {
            p.status = "solved";
            p.solvedAt = e.ts;
            p.card = newCard(e.ts);
          } else if (p.card && e.ts >= p.card.due) {
            p.card = schedule(p.card, 2, e.ts); // re-solving a due problem counts as a good review
          }
          if (e.time && (!p.bestTime || TIME_RANK.indexOf(e.time) < TIME_RANK.indexOf(p.bestTime))) p.bestTime = e.time;
        } else if (p.status === "new") p.status = "attempted";
        break;
      case "lesson":
        p.lessons.add(e.s);
        break;
      case "hint":
        p.hints = Math.max(p.hints, e.n);
        break;
      case "predict":
        p.predictions.total += 1;
        if (e.ok) p.predictions.right += 1;
        break;
      case "review":
        p.card = schedule(p.card ?? newCard(e.ts), e.g, e.ts);
        break;
      case "visualize":
        break;
    }
  }
  const { streak, longest } = streaks(activity, now);
  let solvedCount = 0;
  for (const p of byProblem.values()) if (p.status === "solved") solvedCount++;
  return { byProblem, activity, streak, longestStreak: longest, solvedCount };
}

export function streaks(activity: Map<string, number>, now = Date.now()) {
  const days = [...activity.keys()].sort();
  let longest = 0;
  let run = 0;
  let prev: number | null = null;
  for (const d of days) {
    const t = new Date(`${d}T12:00:00`).getTime();
    run = prev !== null && Math.round((t - prev) / DAY_MS) === 1 ? run + 1 : 1;
    longest = Math.max(longest, run);
    prev = t;
  }
  // Current streak: counts back from today (or yesterday, so it survives until you study today).
  let streak = 0;
  let cursor = now;
  if (!activity.has(dayKey(cursor))) cursor -= DAY_MS;
  while (activity.has(dayKey(cursor))) {
    streak++;
    cursor -= DAY_MS;
  }
  return { streak, longest };
}

/** 0..1 - solved, reviewed, and understood (lessons, predictions) all count. */
export function mastery(p: ProblemProgress | undefined): number {
  if (!p) return 0;
  let m = 0;
  if (p.status === "solved") m += 0.45;
  else if (p.status === "attempted") m += 0.1;
  if (p.lessons.size) m += 0.1;
  if (p.card) m += Math.min(0.35, p.card.reps * 0.12);
  if (p.predictions.total >= 3) m += 0.1 * (p.predictions.right / p.predictions.total);
  return Math.min(1, m);
}

export function patternMastery(progress: Progress, problems: ProblemSummary[], pattern: PatternId) {
  const list = problems.filter((p) => p.pattern === pattern);
  if (!list.length) return { mastery: 0, solved: 0, total: 0 };
  const solved = list.filter((p) => progress.byProblem.get(p.id)?.status === "solved").length;
  const m = list.reduce((sum, p) => sum + mastery(progress.byProblem.get(p.id)), 0) / list.length;
  return { mastery: m, solved, total: list.length };
}

export function dueCards(progress: Progress, now = Date.now()): string[] {
  return [...progress.byProblem.entries()]
    .filter(([, p]) => p.card && p.card.due <= now)
    .sort((a, b) => a[1].card!.due - b[1].card!.due)
    .map(([id]) => id);
}

/** What to do next: due reviews first, then the first unsolved problem on the roadmap. */
export function nextUp(progress: Progress, problems: ProblemSummary[], now = Date.now()) {
  const due = dueCards(progress, now);
  const attempted = problems.find((p) => progress.byProblem.get(p.id)?.status === "attempted");
  const fresh = problems.find((p) => !progress.byProblem.get(p.id) || progress.byProblem.get(p.id)!.status === "new");
  return { due, resume: attempted, fresh };
}
