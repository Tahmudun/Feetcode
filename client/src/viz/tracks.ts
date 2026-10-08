/**
 * Variable tracks: the whole run at a glance, one row per variable, like tracks in a
 * music editor. A row is a run of segments, each a stretch of steps over which the
 * variable held one value, so "l went 0, 2, 1" reads as a shape instead of a number you
 * have to remember while scrubbing.
 *
 * Built from the outermost call (the method being judged) over the steps the player is
 * currently showing. Pure: (trace, visible steps) -> tracks.
 */
import type { Trace } from "@/runtime/types";
import { isRef, pyRepr } from "./decode";

/** `from`/`to` are positions in the player's `visible` list (inclusive). */
export interface TrackSeg {
  from: number;
  to: number;
  text: string;
}

export interface Track {
  name: string;
  segs: TrackSeg[];
  scalar: boolean;
}

export function buildTracks(trace: Trace, visible: number[], maxTracks = 8): Track[] {
  const first = trace.steps.find((s) => s.s.length);
  if (!first) return [];
  const root = first.s[0].id;
  const rows = new Map<string, Track>();
  visible.forEach((raw, pos) => {
    const st = trace.steps[raw];
    const f0 = st?.s[0];
    if (!f0 || f0.id !== root) return;
    for (const [name, v] of f0.v) {
      if (name === "self" || (typeof v === "object" && v !== null && "fn" in v)) continue;
      const text = pyRepr(v, st.h, 2);
      let row = rows.get(name);
      if (!row) {
        row = { name, segs: [], scalar: !isRef(v) };
        rows.set(name, row);
      }
      const last = row.segs[row.segs.length - 1];
      if (last && last.text === text && last.to === pos - 1) last.to = pos;
      else row.segs.push({ from: pos, to: pos, text });
    }
  });
  // Keep the rows worth reading: variables that change first, scalars before containers,
  // then restore source order so the rows line up with the code.
  return [...rows.values()]
    .map((t, i) => ({ t, i, score: (t.segs.length > 1 ? 2 : 0) + (t.scalar ? 1 : 0) }))
    .sort((a, b) => b.score - a.score || a.i - b.i)
    .slice(0, maxTracks)
    .sort((a, b) => a.i - b.i)
    .map((x) => x.t);
}

/** Position in `visible` of raw step `raw`, or the last visible step before it. */
export function positionOf(visible: number[], raw: number): number {
  let pos = 0;
  for (let i = 0; i < visible.length; i++) {
    if (visible[i] <= raw) pos = i;
    else break;
  }
  return pos;
}
