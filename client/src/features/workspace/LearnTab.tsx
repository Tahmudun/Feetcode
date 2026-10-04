import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Brain, ClipboardCopy, Gauge, Lightbulb, Quote, TriangleAlert } from "lucide-react";
import { loadBaselines, loadLessons } from "@/content";
import type { Baselines, Lessons, ProblemDetail } from "@/content/types";
import { cn } from "@/lib/utils";
import { logEvent } from "@/store/events";
import { Chip, Spinner } from "@/ui/primitives";
import { renderInline } from "@/ui/Markdown";
import { Player } from "@/viz/Player";
import { ComplexityChart, SERIES_COLORS } from "@/viz/ComplexityChart";
import { useWorkspace } from "./store";

export function LearnTab({ problem }: { problem: ProblemDetail }) {
  const [lessons, setLessons] = useState<Lessons | null>(null);
  const [baselines, setBaselines] = useState<Baselines | null>(null);
  const optimalId = problem.solutions.find((s) => s.optimal)!.id;
  const [selected, setSelected] = useState(optimalId);
  const setCode = useWorkspace((s) => s.setCode);
  const params = useMemo(() => problem.signature.params.map((p) => p.name), [problem]);

  useEffect(() => {
    loadLessons(problem.id).then(setLessons);
    loadBaselines(problem.id).then(setBaselines);
  }, [problem.id]);

  const sol = problem.solutions.find((s) => s.id === selected)!;
  const trace = lessons?.traces[selected];
  const ins = problem.insight;

  return (
    <div className="space-y-6 px-5 py-5">
      {/* the insight, up front */}
      <section className="relative overflow-hidden rounded-2xl border border-accent/30 bg-gradient-to-br from-accent-soft via-transparent to-violet-soft p-4">
        <div className="mb-2 flex items-center gap-2">
          <Lightbulb size={15} className="text-accent" />
          <span className="text-[11px] font-semibold uppercase tracking-wider text-accent">The key insight</span>
          <Chip tone="accent" className="ml-auto">{ins.pattern}</Chip>
        </div>
        <p className="font-display text-[17px] font-semibold leading-snug text-fg">{renderInline(ins.oneLiner)}</p>
        <p className="mt-3 flex gap-2 text-[13px] italic text-muted">
          <Quote size={14} className="mt-0.5 shrink-0 text-accent" /> {ins.mnemonic}
        </p>
        <p className="mt-3 text-[13px] leading-relaxed text-fg/85">{renderInline(ins.why)}</p>
        {ins.signals && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            <span className="text-[11px] text-faint">Recognize it by:</span>
            {ins.signals.map((s) => <Chip key={s}>{s}</Chip>)}
          </div>
        )}
      </section>

      {/* brute -> optimal */}
      <section>
        <h3 className="mb-2 text-sm font-semibold">From brute force to optimal</h3>
        <div className="flex flex-wrap items-center gap-1.5">
          {problem.solutions.map((s, i) => (
            <div key={s.id} className="flex items-center gap-1.5">
              {i > 0 && <ArrowRight size={14} className="text-faint" />}
              <button
                onClick={() => setSelected(s.id)}
                className={cn(
                  "rounded-xl border px-3 py-1.5 text-left transition-colors",
                  selected === s.id ? "border-accent/60 bg-accent-soft" : "border-line hover:border-line-strong",
                )}
              >
                <div className={cn("text-[12.5px] font-semibold", selected === s.id ? "text-fg" : "text-muted")}>
                  {s.name} {s.optimal && <span className="text-accent">★</span>}
                </div>
                <div className="font-mono text-[10.5px] text-faint">{s.time} · {s.space}</div>
              </button>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[13px] leading-relaxed text-muted">{renderInline(sol.idea)}</p>
      </section>

      <section>
        <div className="mb-2 flex items-center gap-2">
          <h3 className="text-sm font-semibold">Watch it run</h3>
          <span className="text-xs text-faint">
            input: {Object.entries(problem.lessonArgs).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(", ").slice(0, 80)}
          </span>
          <button
            onClick={() => confirm("Replace your editor code with this reference solution?") && setCode(sol.code)}
            className="ml-auto flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted hover:bg-hover hover:text-fg"
            title="Load this solution into the editor"
          >
            <ClipboardCopy size={12} /> Load into editor
          </button>
        </div>
        {trace ? (
          <Player
            key={selected}
            trace={trace}
            lens={problem.lens}
            params={params}
            mode="lesson"
            footnotes={sol.footnotes}
            problemId={problem.id}
            onFinish={() => logEvent({ t: "lesson", p: problem.id, s: selected, ts: Date.now() })}
          />
        ) : (
          <div className="flex h-40 items-center justify-center"><Spinner className="text-accent" /></div>
        )}
        <p className="mt-2 flex items-center gap-1.5 text-[11.5px] text-faint">
          <Brain size={12} /> Turn on <b>Predict</b> to guess each decision before it happens - the fastest way to make the trick stick.
        </p>
      </section>

      {baselines && Object.keys(baselines.solutions).length > 1 && (
        <section>
          <h3 className="mb-1 flex items-center gap-2 text-sm font-semibold"><Gauge size={15} className="text-teal" /> Why the optimization matters</h3>
          <p className="mb-3 text-[12.5px] text-muted">
            Operations each solution performs as the input grows (log-log: steeper line = worse complexity). Counted, not timed - so it's exact.
          </p>
          <ComplexityChart
            series={problem.solutions.map((s, i) => ({
              id: s.id,
              label: s.name,
              points: baselines.solutions[s.id]?.points ?? [],
              color: s.optimal ? "var(--teal)" : SERIES_COLORS[(i + 1) % SERIES_COLORS.length],
              dashed: !s.optimal,
              bold: s.optimal,
              fit: baselines.solutions[s.id]?.time,
            }))}
          />
          {lessons && (
            <div className="mt-3 space-y-1.5">
              {problem.solutions.map((s) => {
                const n = lessons.traces[s.id]?.steps.length ?? 0;
                const max = Math.max(...problem.solutions.map((x) => lessons.traces[x.id]?.steps.length ?? 0));
                return (
                  <div key={s.id} className="flex items-center gap-2 text-[12px]">
                    <span className="w-40 truncate text-muted">{s.name}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-elev-2">
                      <div className={cn("h-full rounded-full", s.optimal ? "bg-teal" : "bg-line-strong")} style={{ width: `${(n / max) * 100}%` }} />
                    </div>
                    <span className="w-24 text-right font-mono text-[11px] text-faint">{n} steps</span>
                  </div>
                );
              })}
              <p className="text-[11px] text-faint">Steps to finish the lesson input above.</p>
            </div>
          )}
        </section>
      )}

      {problem.pitfalls.length > 0 && (
        <section>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold"><TriangleAlert size={15} className="text-rose" /> Common mistakes</h3>
          <div className="space-y-2">
            {problem.pitfalls.map((p) => (
              <div key={p.id} className="rounded-xl border border-line bg-elev-2/40 px-3.5 py-2.5 text-[13px]">
                <div className="font-semibold text-fg">{p.title}</div>
                <div className="text-muted">{renderInline(p.explain)}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className="mb-2 text-sm font-semibold">Recall check</h3>
        <div className="grid gap-2 sm:grid-cols-2">
          {ins.recall.map((r) => <RecallCard key={r.q} q={r.q} a={r.a} />)}
        </div>
      </section>
    </div>
  );
}

export function RecallCard({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <button
      onClick={() => setOpen((o) => !o)}
      className={cn(
        "min-h-24 rounded-xl border p-3.5 text-left text-[13px] transition-all",
        open ? "border-teal/40 bg-teal-soft" : "border-line bg-elev-2/40 hover:border-line-strong",
      )}
    >
      <div className="font-medium text-fg">{q}</div>
      <div className={cn("mt-2 text-muted transition-opacity", open ? "opacity-100" : "opacity-0")}>{renderInline(a)}</div>
      {!open && <div className="mt-1 text-[11px] text-faint">Answer in your head, then tap to check</div>}
    </button>
  );
}
