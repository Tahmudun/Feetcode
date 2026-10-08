import { useState } from "react";
import { Link } from "react-router";
import { Building2, ExternalLink, Lightbulb, Lock, Sparkles } from "lucide-react";
import { problemById } from "@/content";
import type { ProblemDetail } from "@/content/types";
import { lit } from "@/lib/format";
import { cn } from "@/lib/utils";
import { logEvent, useStudy } from "@/store/events";
import { Chip, DifficultyBadge } from "@/ui/primitives";
import { Markdown, renderInline } from "@/ui/Markdown";
import { TierBars } from "@/features/problems/ProblemsPage";

export function DescriptionTab({ problem }: { problem: ProblemDetail }) {
  const companies = Object.entries(problem.companies).sort((a, b) => b[1] - a[1]);
  const hintsSeen = useStudy((s) => s.progress.byProblem.get(problem.id)?.hints ?? 0);
  const [revealed, setRevealed] = useState(hintsSeen);

  const reveal = (n: number) => {
    setRevealed(n);
    logEvent({ t: "hint", p: problem.id, n, ts: Date.now() });
  };

  return (
    <article className="space-y-6 px-5 py-5">
      <div className="flex flex-wrap items-center gap-2">
        <DifficultyBadge value={problem.difficulty} />
        <Link to={`/patterns/${problem.pattern}`}>
          <Chip tone="accent">{problem.patternName}</Chip>
        </Link>
        {problem.topics.map((t) => (
          <Chip key={t}>{t}</Chip>
        ))}
        <a href={problem.url} target="_blank" rel="noreferrer" className="ml-auto flex items-center gap-1 text-xs text-faint hover:text-accent">
          LeetCode #{problem.number} <ExternalLink size={12} />
        </a>
      </div>

      <Markdown text={problem.statement} className="text-[14px] leading-relaxed text-fg/90" />

      <div className="space-y-3">
        {problem.examples.map((ex, i) => (
          <div key={i} className="rounded-xl border border-line bg-elev-2/50 p-3.5">
            <div className="mb-2 text-xs font-semibold text-muted">Example {i + 1}</div>
            <div className="space-y-1 font-mono text-[12.5px]">
              <div>
                <span className="text-faint">Input: </span>
                {Object.entries(ex.args).map(([k, v], j) => (
                  <span key={k}>
                    {j > 0 && <span className="text-faint">, </span>}
                    <span className="text-muted">{k}</span> = <span className="text-fg">{lit(v)}</span>
                  </span>
                ))}
              </div>
              <div>
                <span className="text-faint">Output: </span>
                <span className="text-ref">{lit(ex.output)}</span>
              </div>
            </div>
            {ex.explain && <p className="mt-2 text-[13px] text-muted">{renderInline(ex.explain)}</p>}
          </div>
        ))}
      </div>

      {problem.constraints.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-semibold">Constraints</h3>
          <ul className="space-y-1">
            {problem.constraints.map((c) => (
              <li key={c} className="flex gap-2 text-[13px] text-muted">
                <span className="text-faint">•</span>
                <code className="font-mono text-[12.5px]">{c}</code>
              </li>
            ))}
          </ul>
        </section>
      )}

      {problem.followUp && (
        <p className="rounded-xl border border-note/30 bg-note-soft px-3.5 py-2.5 text-[13px] text-fg">
          <span className="font-semibold text-note">Follow-up: </span>
          {problem.followUp}
        </p>
      )}

      <section>
        <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold">
          <Lightbulb size={15} className="text-accent" /> Hints
          <span className="text-xs font-normal text-faint">reveal one at a time - try before you peek</span>
        </h3>
        <div className="space-y-2">
          {problem.hints.map((h, i) => {
            const open = i < revealed;
            const next = i === revealed;
            return (
              <button
                key={i}
                disabled={!open && !next}
                onClick={() => next && reveal(i + 1)}
                className={cn(
                  "flex w-full items-start gap-3 rounded-xl border px-3.5 py-2.5 text-left text-[13px] transition-colors",
                  open ? "border-accent/30 bg-accent-soft text-fg" : next ? "border-line bg-elev-2 text-muted hover:border-accent/40 hover:text-fg" : "border-line bg-elev-2/40 text-faint",
                )}
              >
                <span className="mt-0.5 font-mono text-[11px] font-bold text-accent">{i + 1}</span>
                {open ? <span>{renderInline(h)}</span> : <span className="flex items-center gap-1.5">{next ? <Sparkles size={13} /> : <Lock size={13} />} {next ? "Reveal hint" : "Locked"}</span>}
              </button>
            );
          })}
        </div>
      </section>

      <section>
        <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold">
          <Building2 size={15} className="text-muted" /> Asked at
        </h3>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-3">
          {companies.map(([c, tier]) => (
            <Link key={c} to={`/problems?company=${encodeURIComponent(c)}`} className="flex items-center justify-between gap-2 rounded-md px-1 py-0.5 text-[13px] text-muted hover:bg-hover hover:text-fg">
              {c}
              <TierBars tier={tier} />
            </Link>
          ))}
        </div>
        <p className="mt-2 text-[11px] text-faint">Compiled from public interview reports; frequency is relative (1-5).</p>
      </section>

      {problem.related.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-semibold">Related</h3>
          <div className="flex flex-wrap gap-2">
            {problem.related.map((r) => {
              const p = problemById.get(r);
              return p ? (
                <Link key={r} to={`/problems/${r}`} className="flex items-center gap-2 rounded-lg border border-line px-2.5 py-1.5 text-[13px] text-muted hover:border-line-strong hover:text-fg">
                  {p.title} <DifficultyBadge value={p.difficulty} />
                </Link>
              ) : null;
            })}
          </div>
        </section>
      )}
    </article>
  );
}
