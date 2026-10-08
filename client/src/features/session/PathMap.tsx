/**
 * "Your path": the whole roadmap as one sky (layout in path.ts). A problem's star lights up
 * when you solve it and grows as reviews make it stick; a ring means tried but not solved
 * yet; a beacon marks tonight's session. Every star is a link to its problem and every
 * constellation name a link to its pattern guide.
 */
import { Link } from "react-router";
import { patterns, problemById, problems } from "@/content";
import type { PatternId } from "@/content/types";
import { cn } from "@/lib/utils";
import { mastery, patternMastery, type Progress, type Status } from "@/store/progress";
import { STRETCH_AT } from "@/store/session";
import { VIEW, layoutPath, type Star } from "./path";

const LAYOUT = layoutPath(patterns, problems);
const POS = new Map(LAYOUT.stars.map((s) => [s.id, s]));
const left = (x: number) => `${(x / VIEW.width) * 100}%`;
const top = (y: number) => `${(y / VIEW.height) * 100}%`;

const STATUS_TEXT: Record<Status, string> = { solved: "solved", attempted: "tried, not solved yet", new: "not started" };

interface Props {
  progress: Progress;
  /** Problems in tonight's session. */
  tonight?: ReadonlySet<string>;
  /** The pattern you're working in, marked "you are here". */
  current?: PatternId | null;
  className?: string;
}

export function PathMap({ progress, tonight, current, className }: Props) {
  const status = (id: string): Status => progress.byProblem.get(id)?.status ?? "new";
  const ratio = (id: PatternId) => {
    const m = patternMastery(progress, problems, id);
    return m.total ? m.solved / m.total : 0;
  };
  return (
    <div className={className}>
      <div className="-mx-1 overflow-x-auto px-1 pb-1">
        <div className="relative min-w-[720px]" style={{ aspectRatio: `${VIEW.width} / ${VIEW.height}` }}>
          <svg viewBox={`0 0 ${VIEW.width} ${VIEW.height}`} className="absolute inset-0 h-full w-full overflow-visible" aria-hidden>
            {LAYOUT.bridges.map((b) => {
              const a = POS.get(b.from)!;
              const z = POS.get(b.to)!;
              const open = ratio(b.pattern) >= STRETCH_AT;
              const mx = (a.x + z.x) / 2;
              return (
                <path
                  key={`${b.from}-${b.to}`}
                  d={`M ${a.x} ${a.y} C ${mx} ${a.y}, ${mx} ${z.y}, ${z.x} ${z.y}`}
                  fill="none"
                  stroke={open ? "var(--note)" : "var(--border-strong)"}
                  strokeWidth={1.25}
                  strokeDasharray="2 6"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                  opacity={open ? 0.9 : 0.7}
                />
              );
            })}
            {LAYOUT.lines.map(([from, to]) => {
              const a = POS.get(from)!;
              const z = POS.get(to)!;
              const lit = status(from) === "solved" && status(to) === "solved";
              return (
                <line
                  key={`${from}-${to}`}
                  x1={a.x}
                  y1={a.y}
                  x2={z.x}
                  y2={z.y}
                  stroke={lit ? "var(--ref)" : "var(--border-strong)"}
                  strokeWidth={lit ? 1.5 : 1}
                  vectorEffect="non-scaling-stroke"
                  opacity={lit ? 0.75 : 0.6}
                />
              );
            })}
          </svg>

          {LAYOUT.stars.map((s) => (
            <StarLink key={s.id} star={s} status={status(s.id)} glow={mastery(progress.byProblem.get(s.id))} tonight={!!tonight?.has(s.id)} />
          ))}

          {LAYOUT.labels.map((l) => {
            const info = patterns.find((p) => p.id === l.pattern)!;
            const m = patternMastery(progress, problems, l.pattern);
            const here = current === l.pattern;
            return (
              <Link
                key={l.pattern}
                to={`/patterns/${l.pattern}`}
                className="group absolute -translate-x-1/2 whitespace-nowrap rounded-md px-1.5 text-center leading-tight"
                style={{ left: left(l.x), top: top(l.y) }}
                title={`${info.name}: ${info.tagline}`}
              >
                <span className={cn("block font-display text-[13px] font-semibold group-hover:text-accent", m.solved === m.total ? "text-ref" : "text-fg")}>
                  {info.name}
                </span>
                <span className="block font-mono text-[10.5px] text-faint">
                  {m.solved}/{m.total}
                  {here && <span className="text-accent"> · you are here</span>}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-[11.5px] text-muted" aria-hidden>
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-ref shadow-[0_0_8px_var(--ref)]" /> solved (brighter with every review)</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full border-2 border-warn" /> tried, not solved</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full border border-accent bg-accent-soft" /> tonight</span>
        <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-faint" /> not started</span>
      </div>
    </div>
  );
}

function StarLink({ star, status, glow, tonight }: { star: Star; status: Status; glow: number; tonight: boolean }) {
  const p = problemById.get(star.id)!;
  const size = status === "solved" ? 8 + glow * 8 : status === "attempted" ? 10 : 6;
  return (
    <Link
      to={`/problems/${star.id}`}
      aria-label={`${p.title}: ${STATUS_TEXT[status]}${tonight ? ", in tonight's session" : ""}`}
      className="group absolute flex h-6 w-6 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full"
      style={{ left: left(star.x), top: top(star.y) }}
    >
      {tonight && <span className="anim-beacon absolute inset-0.5 rounded-full border border-accent bg-accent-soft" />}
      <span
        className={cn(
          "relative block rounded-full transition-transform duration-150 group-hover:scale-125",
          status === "solved" && "bg-ref",
          status === "attempted" && "border-2 border-warn",
          status === "new" && (tonight ? "bg-accent" : "bg-faint"),
        )}
        style={{
          width: size,
          height: size,
          boxShadow: status === "solved" ? `0 0 ${4 + glow * 10}px var(--ref)` : undefined,
        }}
      />
      <span
        aria-hidden
        className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden -translate-x-1/2 whitespace-nowrap rounded-md border border-line-strong bg-elev px-2 py-1 text-[11.5px] text-fg shadow-panel group-hover:block group-focus-visible:block"
      >
        {p.title} <span className="text-muted">· {p.difficulty} · {STATUS_TEXT[status]}</span>
      </span>
    </Link>
  );
}
