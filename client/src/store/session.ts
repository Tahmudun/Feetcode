/**
 * Tonight's session: a short plan for one sitting, built from the event log.
 *
 * `planSession` is a pure function of derived progress. It warms up with recall cards that
 * are about to fade, goes back to the problem you left broken, adds one new problem from the
 * pattern you're in and, once that pattern is mostly solved, one stretch problem from a
 * pattern that builds on it.
 *
 * Starting a session logs the plan as a `session` event. That records a decision ("this is
 * what I'll do tonight"), so it belongs in the log; which items are done is never stored,
 * `sessionState` derives it from the events that come after.
 */
import { prerequisites } from "@/content/roadmap";
import type { Difficulty, PatternId, ProblemSummary } from "@/content/types";
import type { Verdict } from "@/runtime/types";
import { DAY_MS, dayKey, plural } from "@/lib/utils";
import { dueCards, schedule, type ProblemProgress, type Progress, type StudyEvent } from "./progress";

export type SessionKind = "recall" | "fix" | "new" | "stretch";

export interface SessionItem {
  kind: SessionKind;
  /** Problem id. */
  p: string;
  /** Why it is in tonight's plan, in one sentence. */
  reason: string;
  minutes: number;
}

export type ItemStatus = "todo" | "started" | "done";
export type SessionEntry = SessionItem & { status: ItemStatus };

export interface Session {
  /** When the session was started. */
  ts: number;
  items: SessionEntry[];
  done: number;
  /** The first item that isn't done, or null once the session is complete. */
  next: SessionEntry | null;
}

export const MAX_ITEMS = 5;
const MAX_RECALLS = 3;
const RECALL_MINUTES = 2;
const FIX_MINUTES = 10;
const NEW_MINUTES: Record<Difficulty, number> = { Easy: 15, Medium: 25, Hard: 35 };
/** Share of a pattern solved before the planner reaches into the next one. */
export const STRETCH_AT = 0.7;

const FIX_REASON: Record<Exclude<Verdict, "accepted">, string> = {
  wrong: "Your last submit gave a wrong answer. Submit again to see where your run leaves the reference.",
  error: "Your last submit crashed on a hidden test.",
  tle: "Your last submit ran over its op budget: the answer is right, the complexity isn't yet.",
  compile: "Your last submit didn't compile.",
};

type PatternRef = { id: PatternId; name: string };

const days = (n: number) => (n <= 0 ? "today" : n === 1 ? "tomorrow" : `in ${n} days`);

/** Where the card stands, and what recalling it correctly tonight buys you. */
function recallReason(p: ProblemProgress, now: number): string {
  const card = p.card!;
  const gain = `Recall it now and it comes back ${days(Math.round(schedule(card, 2, now).interval))}.`;
  if (card.reps === 0) {
    const ago = Math.max(1, Math.round((now - (p.solvedAt ?? now)) / DAY_MS));
    return `Solved ${plural(ago, "day")} ago, never recalled. ${gain}`;
  }
  return `Recalled ${plural(card.reps, "time")}${card.lapses ? `, slipped ${plural(card.lapses, "time")}` : ""}. ${gain}`;
}

const untouched = (progress: Progress, id: string) => {
  const s = progress.byProblem.get(id)?.status;
  return !s || s === "new";
};

function share(progress: Progress, problems: ProblemSummary[], pattern: PatternId) {
  const list = problems.filter((p) => p.pattern === pattern);
  const solved = list.filter((p) => progress.byProblem.get(p.id)?.status === "solved").length;
  return { solved, total: list.length, ratio: list.length ? solved / list.length : 0 };
}

/** The pattern you're working in: the one you touched last, else the first on the roadmap. */
export function currentPattern(progress: Progress, problems: ProblemSummary[]): PatternId | null {
  let best: ProblemSummary | undefined;
  let at = -1;
  for (const p of problems) {
    const last = progress.byProblem.get(p.id)?.lastAt ?? -1;
    if (last > at) {
      at = last;
      best = p;
    }
  }
  return (best ?? problems[0])?.pattern ?? null;
}

/**
 * Tonight's plan, in the order to do it: recalls (the warm-up), the fix, the new problem,
 * the stretch. At most MAX_ITEMS items; recalls take whatever room the others leave.
 * `problems` must be in roadmap order.
 */
export function planSession(progress: Progress, problems: ProblemSummary[], patterns: PatternRef[], now = Date.now()): SessionItem[] {
  const byId = new Map(problems.map((p) => [p.id, p]));
  const nameOf = (id: PatternId) => patterns.find((p) => p.id === id)?.name ?? id;
  const items: SessionItem[] = [];

  const broken = problems
    .filter((p) => progress.byProblem.get(p.id)?.status === "attempted")
    .sort((a, b) => (progress.byProblem.get(b.id)!.lastAt ?? 0) - (progress.byProblem.get(a.id)!.lastAt ?? 0))[0];
  if (broken) {
    const v = progress.byProblem.get(broken.id)!.lastVerdict;
    const reason = v && v !== "accepted" ? FIX_REASON[v] : "You started this one. Finish it while the idea is fresh.";
    items.push({ kind: "fix", p: broken.id, reason, minutes: FIX_MINUTES });
  }

  const current = currentPattern(progress, problems);
  const fresh = (p: ProblemSummary) => untouched(progress, p.id) && p.id !== broken?.id;
  const inCurrent = problems.find((p) => p.pattern === current && fresh(p));
  const next = inCurrent ?? problems.find(fresh);
  if (next) {
    const s = share(progress, problems, next.pattern);
    const reason = progress.byProblem.size === 0
      ? `Where the path starts: the first ${nameOf(next.pattern)} problem.`
      : inCurrent
        ? `Next in ${nameOf(next.pattern)}, where you've solved ${s.solved} of ${s.total}.`
        : `Next on the path, in ${nameOf(next.pattern)}.`;
    items.push({ kind: "new", p: next.id, reason, minutes: NEW_MINUTES[next.difficulty] });
  }

  // Stretch: once the current pattern is mostly solved, reach into a fresh pattern that builds on one you've (nearly) mastered.
  if (current && share(progress, problems, current).ratio >= STRETCH_AT) {
    for (const pat of patterns) {
      if (pat.id === current || pat.id === next?.pattern) continue;
      const list = problems.filter((p) => p.pattern === pat.id);
      if (!list.every((p) => untouched(progress, p.id))) continue;
      const base = prerequisites(pat.id).find((pre) => share(progress, problems, pre).ratio >= STRETCH_AT);
      if (!base || !list[0]) continue;
      const s = share(progress, problems, base);
      items.push({
        kind: "stretch",
        p: list[0].id,
        reason: `You've solved ${s.solved} of ${s.total} in ${nameOf(base)}. ${pat.name} builds on it.`,
        minutes: NEW_MINUTES[list[0].difficulty],
      });
      break;
    }
  }

  const room = Math.min(MAX_RECALLS, MAX_ITEMS - items.length);
  const recalls: SessionItem[] = dueCards(progress, now)
    .filter((id) => byId.has(id))
    .slice(0, Math.max(0, room))
    .map((id) => ({ kind: "recall", p: id, reason: recallReason(progress.byProblem.get(id)!, now), minutes: RECALL_MINUTES }));
  return [...recalls, ...items];
}

export const totalMinutes = (items: SessionItem[]) => items.reduce((sum, it) => sum + it.minutes, 0);

/** An event finishes an item: a review (or a re-solve) for a recall, an accepted submit for anything else. */
const finishes = (kind: SessionKind, e: StudyEvent) =>
  (e.t === "submit" && e.v === "accepted") || (kind === "recall" && e.t === "review");

/**
 * Today's session, if one was started today: the latest `session` event, with each item's
 * status folded from the events after it.
 */
export function sessionState(events: StudyEvent[], now = Date.now()): Session | null {
  let start = -1;
  for (let i = events.length - 1; i >= 0; i--) {
    if (events[i].t === "session") {
      start = i;
      break;
    }
  }
  if (start < 0) return null;
  const s = events[start] as Extract<StudyEvent, { t: "session" }>;
  if (dayKey(s.ts) !== dayKey(now)) return null;
  const items: SessionEntry[] = s.items.map((it) => ({ ...it, status: "todo" }));
  for (let i = start + 1; i < events.length; i++) {
    const e = events[i];
    for (const it of items) {
      if (it.p !== e.p || it.status === "done") continue;
      it.status = finishes(it.kind, e) ? "done" : "started";
    }
  }
  const done = items.filter((it) => it.status === "done").length;
  return { ts: s.ts, items, done, next: items.find((it) => it.status !== "done") ?? null };
}
