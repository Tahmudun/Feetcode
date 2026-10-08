/**
 * Variable tracks (see tracks.ts): one row per variable, segments for the stretches of
 * steps over which it held one value. Clicking a segment seeks there. An optional
 * marker draws a line across every row (e.g. where your run diverges from the reference)
 * and, on the marked variable's row, a dashed "ghost" lane with the other run's value.
 */
import { Fragment } from "react";
import { cn } from "@/lib/utils";
import type { Track } from "./tracks";

export interface TrackMarker {
  /** Position in the player's visible steps. */
  pos: number;
  label: string;
  var?: string | null;
  /** The other run's value of `var` from the marker on. */
  ghost?: string | null;
  ghostLabel?: string;
}

interface Props {
  tracks: Track[];
  n: number;
  index: number;
  onSeek: (pos: number) => void;
  marker?: TrackMarker | null;
}

const pct = (x: number, n: number) => `${(x / Math.max(1, n)) * 100}%`;

export function Tracks({ tracks, n, index, onSeek, marker }: Props) {
  if (!tracks.length) return null;
  const ghostOf = (name: string) => (marker && marker.var === name && marker.ghost ? marker : null);
  return (
    <div className="rounded-xl border border-line bg-inset/50 px-3 pb-2 pt-2.5">
      <div className="grid grid-cols-[84px_minmax(0,1fr)] gap-x-2" aria-label="Variable tracks: the values each variable took over the run">
        <div className="space-y-1">
          {tracks.map((t) => (
            <Fragment key={t.name}>
              <div className="flex h-6 items-center truncate font-mono text-[11.5px] font-semibold text-muted" title={t.name}>{t.name}</div>
              {ghostOf(t.name) && <div className="flex h-5 items-center truncate font-mono text-[10.5px] text-ref">↳ {marker!.ghostLabel ?? "reference"}</div>}
            </Fragment>
          ))}
        </div>
        <div className="relative space-y-1">
          {tracks.map((t) => {
            const ghost = ghostOf(t.name);
            return (
              <Fragment key={t.name}>
                <div className="relative h-6">
                  {t.segs.map((seg) => {
                    const current = index >= seg.from && index <= seg.to;
                    const diverged = !!marker && marker.var === t.name && seg.from === marker.pos;
                    return (
                      <button
                        key={seg.from}
                        type="button"
                        tabIndex={-1}
                        onClick={() => onSeek(seg.from)}
                        title={`${t.name} = ${seg.text} · step ${seg.from + 1}${seg.to > seg.from ? `-${seg.to + 1}` : ""}`}
                        className={cn(
                          "absolute inset-y-0.5 overflow-hidden whitespace-nowrap rounded-[5px] border px-1.5 text-left font-mono text-[11px] leading-[18px] transition-colors",
                          diverged
                            ? "border-warn bg-warn-soft font-bold text-warn"
                            : current
                              ? "border-accent bg-accent-soft text-fg"
                              : "border-accent/35 bg-accent-soft/40 text-muted hover:border-accent/70 hover:text-fg",
                        )}
                        style={{ left: `calc(${pct(seg.from, n)} + 1px)`, width: `calc(${pct(seg.to - seg.from + 1, n)} - 2px)` }}
                      >
                        {seg.text}
                      </button>
                    );
                  })}
                </div>
                {ghost && (
                  <div className="relative h-5">
                    <span
                      className="absolute inset-y-0.5 overflow-hidden whitespace-nowrap rounded-[5px] border border-dashed border-ref/70 bg-ref-soft px-1.5 font-mono text-[11px] leading-[14px] text-ref"
                      style={{ left: `calc(${pct(ghost.pos, n)} + 1px)`, width: `calc(${pct(n - ghost.pos, n)} - 2px)` }}
                    >
                      {ghost.ghost}
                    </span>
                  </div>
                )}
              </Fragment>
            );
          })}
          {marker && (
            <span aria-hidden className="pointer-events-none absolute -bottom-1 -top-1 border-l border-dashed border-warn/80" style={{ left: pct(marker.pos, n) }} />
          )}
          <span aria-hidden className="pointer-events-none absolute -bottom-1 -top-1 w-px bg-accent shadow-[0_0_6px_var(--accent)]" style={{ left: pct(index + 0.5, n) }} />
        </div>
      </div>
      {marker && (
        <div className="relative ml-[92px] mt-1.5 h-3.5" aria-hidden>
          <span className="absolute -translate-x-1/2 whitespace-nowrap font-mono text-[10px] font-bold text-warn" style={{ left: pct(marker.pos, n) }}>
            ▲ {marker.label}
          </span>
        </div>
      )}
    </div>
  );
}
