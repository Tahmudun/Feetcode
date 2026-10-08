import { Link } from "react-router";
import { patterns, problems } from "@/content";
import { prerequisites } from "@/content/roadmap";
import { useStudy } from "@/store/events";
import { patternMastery } from "@/store/progress";
import { currentPattern } from "@/store/session";
import { PathMap } from "@/features/session/PathMap";
import { Panel } from "@/ui/primitives";

export default function PatternsPage() {
  const progress = useStudy((s) => s.progress);
  return (
    <div className="mx-auto max-w-6xl px-4 pb-24 pt-8 sm:px-6">
      <h1 className="font-display text-3xl font-extrabold tracking-tight">Pattern guides</h1>
      <p className="mt-1 max-w-2xl text-muted">
        Interview problems are variations on a few ideas. Learn each pattern's trick, then recognize it on sight. The dashed links show
        what builds on what.
      </p>

      <Panel className="mt-6 px-4 pb-4 pt-6 sm:px-6">
        <PathMap progress={progress} current={progress.byProblem.size ? currentPattern(progress, problems) : null} />
      </Panel>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {patterns.map((p) => {
          const m = patternMastery(progress, problems, p.id);
          const pre = prerequisites(p.id).map((id) => patterns.find((x) => x.id === id)?.name).filter(Boolean);
          return (
            <Link key={p.id} to={`/patterns/${p.id}`} className="group">
              <Panel className="h-full p-4 transition-all group-hover:-translate-y-0.5 group-hover:border-accent/50 group-hover:shadow-glow">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{p.name}</span>
                  <span className="font-mono text-[11px] text-muted">{m.solved}/{m.total}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-elev-2">
                  <div className="h-full rounded-full bg-ref transition-all" style={{ width: `${m.mastery * 100}%` }} />
                </div>
                <p className="mt-2 text-[12.5px] leading-snug text-muted">{p.tagline}</p>
                {pre.length > 0 && <p className="mt-1.5 text-[11.5px] text-faint">Builds on {pre.join(" and ")}</p>}
              </Panel>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
