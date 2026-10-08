import { create } from "zustand";
import { storage } from "@/lib/storage";
import { derive, type Progress, type StudyEvent } from "./progress";
import { sessionState, type Session, type SessionItem } from "./session";

const KEY = "fc:events:v1";
const MAX_EVENTS = 20_000;

interface EventStore {
  events: StudyEvent[];
  progress: Progress;
  /** Today's session, if one was started (derived from the log like everything else). */
  session: Session | null;
  log: (e: StudyEvent) => void;
  importEvents: (events: StudyEvent[]) => void;
  reset: () => void;
}

const initial = storage.get<StudyEvent[]>(KEY, []);

/** Everything the store derives from the log, recomputed whenever the log changes. */
const fold = (events: StudyEvent[]) => ({ events, progress: derive(events), session: sessionState(events) });

export const useStudy = create<EventStore>((set, get) => ({
  ...fold(initial),
  log: (e) => {
    const events = [...get().events, e].slice(-MAX_EVENTS);
    storage.set(KEY, events);
    set(fold(events));
  },
  importEvents: (incoming) => {
    const seen = new Set(get().events.map((e) => `${e.t}:${e.p}:${e.ts}`));
    const merged = [...get().events, ...incoming.filter((e) => !seen.has(`${e.t}:${e.p}:${e.ts}`))].sort((a, b) => a.ts - b.ts);
    storage.set(KEY, merged);
    set(fold(merged));
  },
  reset: () => {
    storage.remove(KEY);
    set(fold([]));
  },
}));

export const logEvent = (e: StudyEvent) => useStudy.getState().log(e);

/** Start tonight's session with this plan. */
export const startSession = (items: SessionItem[]) => logEvent({ t: "session", p: "", ts: Date.now(), items });

/** Export the raw log as newline-delimited JSON - your data, in a format any tool reads. */
export function exportNdjson(): string {
  return useStudy.getState().events.map((e) => JSON.stringify(e)).join("\n") + "\n";
}
