import { Link } from "react-router";
import { patterns, problems } from "@/content";
import type { PatternId } from "@/content/types";
import { useStudy } from "@/store/events";
import { patternMastery } from "@/store/progress";
import { Panel } from "@/ui/primitives";

/** The roadmap: what each pattern builds on (after NeetCode's ordering). */
const NODES: Record<PatternId, { x: number; y: number }> = {
  "arrays-hashing": { x: 50, y: 10 },
  "two-pointers": { x: 28, y: 46 },
  stack: { x: 74, y: 46 },
  "sliding-window": { x: 14, y: 84 },
  "linked-list": { x: 50, y: 84 },
};
const EDGES: [PatternId, PatternId][] = [
  ["arrays-hashing", "two-pointers"],
  ["arrays-hashing", "stack"],
  ["two-pointers", "sliding-window"],
  ["two-pointers", "linked-list"],
];

export default function PatternsPage() {
  const progress = useStudy((s) => s.progress);
  return (
    <div className="mx-auto max-w-5xl px-4 pb-24 pt-8 sm:px-6">
      <h1 className="font-display text-3xl font-extrabold tracking-tight">Pattern roadmap</h1>
      <p className="mt-1 max-w-2xl text-muted">
        Interview problems are variations on a few ideas. Learn each pattern's trick, then recognize it on sight. Arrows show what builds on what.
      </p>

      <div className="relative mt-8 hidden h-[420px] md:block">
        <svg className="absolute inset-0 h-full w-full" preserveAspectRatio="none" viewBox="0 0 100 100" aria-hidden>
          {EDGES.map(([a, b]) => (
            <path
              key={`${a}-${b}`}
              d={`M ${NODES[a].x} ${NODES[a].y + 7} C ${NODES[a].x} ${(NODES[a].y + NODES[b].y) / 2 + 4}, ${NODES[b].x} ${(NODES[a].y + NODES[b].y) / 2}, ${NODES[b].x} ${NODES[b].y - 7}`}
              fill="none"
              stroke="var(--border-strong)"
              strokeWidth={0.35}
              vectorEffect="non-scaling-stroke"
              style={{ strokeWidth: 2 }}
            />
          ))}
        </svg>
        {patterns.map((p) => {
          const m = patternMastery(progress, problems, p.id);
          const pos = NODES[p.id];
          return (
            <Link
              key={p.id}
              to={`/patterns/${p.id}`}
              className="group absolute w-56 -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
            >
              <Panel className="p-4 transition-all group-hover:-translate-y-0.5 group-hover:border-accent/50 group-hover:shadow-glow">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{p.name}</span>
                  <span className="font-mono text-[11px] text-muted">{m.solved}/{m.total}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-elev-2">
                  <div className="h-full rounded-full bg-ref transition-all" style={{ width: `${m.mastery * 100}%` }} />
                </div>
                <p className="mt-2 line-clamp-2 text-[11.5px] leading-snug text-muted">{p.tagline}</p>
              </Panel>
            </Link>
          );
        })}
      </div>

      <div className="mt-8 grid gap-3 md:hidden">
        {patterns.map((p) => {
          const m = patternMastery(progress, problems, p.id);
          return (
            <Link key={p.id} to={`/patterns/${p.id}`}>
              <Panel className="p-4">
                <div className="flex justify-between font-semibold">{p.name}<span className="font-mono text-xs text-muted">{m.solved}/{m.total}</span></div>
                <p className="mt-1 text-xs text-muted">{p.tagline}</p>
              </Panel>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
