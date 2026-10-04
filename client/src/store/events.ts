import { create } from "zustand";
import { storage } from "@/lib/storage";
import { derive, type Progress, type StudyEvent } from "./progress";

const KEY = "fc:events:v1";
const MAX_EVENTS = 20_000;

interface EventStore {
  events: StudyEvent[];
  progress: Progress;
  log: (e: StudyEvent) => void;
  importEvents: (events: StudyEvent[]) => void;
  reset: () => void;
}

const initial = storage.get<StudyEvent[]>(KEY, []);

export const useStudy = create<EventStore>((set, get) => ({
  events: initial,
  progress: derive(initial),
  log: (e) => {
    const events = [...get().events, e].slice(-MAX_EVENTS);
    storage.set(KEY, events);
    set({ events, progress: derive(events) });
  },
  importEvents: (incoming) => {
    const seen = new Set(get().events.map((e) => `${e.t}:${e.p}:${e.ts}`));
    const merged = [...get().events, ...incoming.filter((e) => !seen.has(`${e.t}:${e.p}:${e.ts}`))].sort((a, b) => a.ts - b.ts);
    storage.set(KEY, merged);
    set({ events: merged, progress: derive(merged) });
  },
  reset: () => {
    storage.remove(KEY);
    set({ events: [], progress: derive([]) });
  },
}));

export const logEvent = (e: StudyEvent) => useStudy.getState().log(e);

/** Export the raw log as newline-delimited JSON - your data, in a format any tool reads. */
export function exportNdjson(): string {
  return useStudy.getState().events.map((e) => JSON.stringify(e)).join("\n") + "\n";
}
