import { Link, useParams } from "react-router";
import { Check, Gauge, Radar } from "lucide-react";
import { patternById, problems } from "@/content";
import type { PatternId } from "@/content/types";
import { useStudy } from "@/store/events";
import { mastery } from "@/store/progress";
import { DifficultyBadge, Panel } from "@/ui/primitives";
import { renderInline } from "@/ui/Markdown";
import { CodePane } from "@/viz/CodePane";
import { StatusIcon } from "@/features/problems/ProblemsPage";
import { NotFound } from "@/app/NotFound";

export default function PatternPage() {
  const { id = "" } = useParams();
  const p = patternById.get(id as PatternId);
  const progress = useStudy((s) => s.progress);
  if (!p) return <NotFound />;
  const list = problems.filter((x) => x.pattern === p.id);
  return (
    <div className="mx-auto max-w-5xl px-4 pb-24 pt-8 sm:px-6">
      <Link to="/patterns" className="text-xs text-muted hover:text-accent">← Roadmap</Link>
      <h1 className="mt-2 font-display text-4xl font-extrabold tracking-tight">{p.name}</h1>
      <p className="mt-2 text-lg text-accent">{p.tagline}</p>
      <p className="mt-4 max-w-3xl text-[15px] leading-relaxed text-fg/85">{renderInline(p.summary)}</p>

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <Panel className="p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold"><Radar size={15} className="text-violet" /> Recognize it when you see…</h2>
          <ul className="space-y-2">
            {p.signals.map((s) => (
              <li key={s} className="flex gap-2 text-[13.5px] text-muted"><Check size={15} className="mt-0.5 shrink-0 text-teal" /> {renderInline(s)}</li>
            ))}
          </ul>
          <p className="mt-4 flex items-start gap-2 border-t border-line pt-3 text-[13px] text-muted">
            <Gauge size={15} className="mt-0.5 shrink-0 text-accent" /> {p.complexity}
          </p>
        </Panel>
        <Panel className="p-5">
          <h2 className="mb-3 text-sm font-semibold">The template</h2>
          <CodePane code={p.template} />
        </Panel>
      </div>

      <h2 className="mb-3 mt-10 text-lg font-bold">Key moves</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {p.ideas.map((idea, i) => (
          <Panel key={idea.title} className="p-4">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent-soft font-mono text-xs font-bold text-accent">{i + 1}</span>
              <span className="font-semibold">{idea.title}</span>
            </div>
            <p className="mt-2 text-[13px] leading-relaxed text-muted">{renderInline(idea.text)}</p>
          </Panel>
        ))}
      </div>

      <h2 className="mb-3 mt-10 text-lg font-bold">Problems, in order</h2>
      <div className="overflow-hidden rounded-2xl border border-line bg-elev">
        {list.map((x, i) => {
          const pr = progress.byProblem.get(x.id);
          return (
            <Link key={x.id} to={`/problems/${x.id}`} className={`group flex items-center gap-3 px-4 py-3 hover:bg-hover ${i ? "border-t border-line" : ""}`}>
              <StatusIcon status={pr?.status} />
              <span className="font-mono text-xs text-faint">{x.number}.</span>
              <span className="flex-1 font-medium group-hover:text-accent">{x.title}</span>
              <span className="hidden max-w-sm truncate text-xs text-faint md:block">{x.oneLiner}</span>
              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-elev-2" title="mastery">
                <div className="h-full bg-teal" style={{ width: `${mastery(pr) * 100}%` }} />
              </div>
              <DifficultyBadge value={x.difficulty} />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
