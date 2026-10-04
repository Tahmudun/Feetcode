import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { ArrowRight, Bug, Flame, Gauge, Microscope, Play, ScanSearch, Shrink, Sparkles } from "lucide-react";
import { loadBaselines, neighbours } from "@/content";
import type { Baselines, ProblemDetail } from "@/content/types";
import { lit } from "@/lib/format";
import { cn, compact } from "@/lib/utils";
import type { Profile, SubmitResult } from "@/runtime/types";
import { ComplexityChart, SERIES_COLORS, type Series } from "@/viz/ComplexityChart";
import { Button, Spinner } from "@/ui/primitives";
import { renderInline } from "@/ui/Markdown";
import { confetti } from "@/ui/confetti";
import { Block } from "./ConsolePanel";
import { useWorkspace } from "./store";
import { VERDICT } from "./verdicts";

const RANK = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(n² log n)", "O(n³)", "O(2ⁿ)"];
const rank = (label?: string | null) => (label ? RANK.indexOf(label) : -1);

export function AnalysisView({ problem }: { problem: ProblemDetail }) {
  const { submitResult: res, busy, submitStage, submit } = useWorkspace();
  const [baselines, setBaselines] = useState<Baselines | null>(null);
  const celebrated = useRef<SubmitResult | null>(null);

  useEffect(() => {
    loadBaselines(problem.id).then(setBaselines).catch(() => setBaselines(null));
  }, [problem.id]);

  useEffect(() => {
    if (res?.verdict === "accepted" && celebrated.current !== res) {
      celebrated.current = res;
      confetti();
    }
  }, [res]);

  if (busy === "submit") {
    return (
      <div className="space-y-4 py-2">
        <div className="flex items-center gap-2 text-[14px] font-semibold"><Spinner className="text-accent" /> {submitStage || "Judging…"}</div>
        <ol className="space-y-2 text-[13px] text-muted">
          <li className="flex items-center gap-2"><Gauge size={14} className="text-accent" /> Hidden tests, with deterministic operation budgets</li>
          <li className="flex items-center gap-2"><ScanSearch size={14} className="text-violet" /> Fuzzing small random inputs against the reference</li>
          <li className="flex items-center gap-2"><Microscope size={14} className="text-teal" /> Profiling how your code grows with n</li>
        </ol>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-elev-2"><div className="skeleton h-full w-full" /></div>
      </div>
    );
  }
  if (!res) {
    return (
      <div className="space-y-3 text-[13px] text-muted">
        <p>Submitting runs more than LeetCode does:</p>
        <ul className="space-y-1.5">
          <li>• <b className="text-fg">Hidden tests</b> with budgets counted in operations - the same code gets the same verdict on any machine.</li>
          <li>• <b className="text-fg">A fuzzer</b> that hunts for inputs your code gets wrong, then shrinks them to the smallest example.</li>
          <li>• <b className="text-fg">A complexity profile</b>: your growth curve next to the brute force and the optimal solution.</li>
        </ul>
        <Button variant="success" onClick={() => void submit()}>Submit</Button>
      </div>
    );
  }
  if (res.verdict === "compile") {
    return (
      <div>
        <div className="mb-2 text-lg font-bold text-rose">Syntax Error</div>
        <pre className="rounded-xl border border-rose/40 bg-rose-soft p-3 font-mono text-[12.5px] text-rose">Line {res.error?.line}: {res.error?.message}</pre>
      </div>
    );
  }
  const v = VERDICT[res.verdict];
  return (
    <div className="anim-fade-up space-y-5">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <span className={cn("font-display text-2xl font-extrabold", v.text)}>{v.label}</span>
        {res.total !== undefined && (
          <span className="text-[13px] text-muted">
            {res.passed}/{res.total} hidden tests passed{res.foundBy === "fuzzer" ? " - but the fuzzer found a bug" : ""}
          </span>
        )}
        {res.ops !== undefined && <span className="font-mono text-[11px] text-faint">{compact(res.ops)} ops total</span>}
      </div>
      {res.verdict === "accepted" && <Accepted problem={problem} res={res} baselines={baselines} />}
      {(res.verdict === "wrong" || res.verdict === "error") && <Failure problem={problem} res={res} />}
      {res.verdict === "tle" && <TooSlow problem={problem} res={res} baselines={baselines} />}
    </div>
  );
}

function growthSeries(problem: ProblemDetail, baselines: Baselines | null, profile?: Profile): Series[] {
  const series: Series[] = [];
  if (baselines) {
    problem.solutions.forEach((s, i) => {
      const b = baselines.solutions[s.id];
      if (!b) return;
      series.push({
        id: s.id, label: s.name, points: b.points, color: s.optimal ? "var(--teal)" : SERIES_COLORS[i % SERIES_COLORS.length],
        dashed: !s.optimal, fit: b.time,
      });
    });
  }
  if (profile) {
    series.push({ id: "you", label: "Your code", points: profile.points.map((p) => ({ n: p.n, ops: p.ops, capped: p.capped })), color: "var(--accent)", bold: true, fit: profile.time?.label });
  }
  return series;
}

function Findings({ profile }: { profile: Profile }) {
  const setMarks = useWorkspace((s) => s.setMarks);
  if (!profile.hidden.length && !Object.keys(profile.lines).length) return null;
  const hot = Object.entries(profile.lines).sort((a, b) => b[1] - a[1])[0];
  const apply = () =>
    setMarks({
      heat: Object.fromEntries(Object.entries(profile.lines).map(([k, x]) => [Number(k), x])),
      notes: profile.hidden.map((h, i) => ({ line: h.line, n: i + 1 })),
    });
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <h4 className="text-[13px] font-semibold">Where the time goes {profile.n ? <span className="font-normal text-faint">(n = {profile.n})</span> : null}</h4>
        <button onClick={apply} className="ml-auto flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] text-accent hover:bg-accent-soft">
          <Flame size={12} /> Show heatmap in editor
        </button>
      </div>
      {hot && (
        <p className="text-[12.5px] text-muted">
          Hottest line: <span className="font-mono text-fg">line {hot[0]}</span> ran <b className="text-fg">{Number(hot[1]).toLocaleString()}</b> times.
        </p>
      )}
      {profile.hidden.length > 0 && (
        <ol className="space-y-1.5 border-t border-line pt-2">
          {profile.hidden.map((h, i) => (
            <li key={h.line} className="flex gap-2 text-[12.5px] leading-relaxed text-muted">
              <sup className="mt-1.5 font-mono text-[10px] font-bold text-accent">{i + 1}</sup>
              <span>
                <span className="font-mono text-faint">L{h.line} </span>
                <code className="text-fg">{h.probes[0]?.label}</code> costs <b className="text-rose">{h.cost.toLocaleString()}</b> hidden operations: {h.probes[0]?.hint}.
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function Accepted({ problem, res, baselines }: { problem: ProblemDetail; res: SubmitResult; baselines: Baselines | null }) {
  const setLeftTab = useWorkspace((s) => s.setLeftTab);
  const profile = res.profile;
  const optimal = problem.solutions.find((s) => s.optimal)!;
  const optimalFit = baselines?.solutions[optimal.id]?.time ?? optimal.time;
  const yours = profile?.time?.label;
  const slower = yours && rank(yours) > rank(optimalFit);
  const { next } = neighbours(problem.id);
  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Your time" value={yours ?? "-"} tone={slower ? "accent" : "teal"} />
        <Stat label="Your space" value={profile?.space?.label ?? "-"} tone="sky" />
        <Stat label="Optimal" value={`${optimal.time} · ${optimal.space}`} tone="muted" />
      </div>
      {slower ? (
        <div className="rounded-xl border border-accent/40 bg-accent-soft p-3 text-[13px]">
          <b className="text-accent">Correct - and there's a faster idea.</b> Your solution grows like {yours}; the optimal one is {optimalFit}. That gap is invisible on small tests and decisive in interviews.
          <button onClick={() => setLeftTab("learn")} className="mt-2 flex items-center gap-1 font-semibold text-accent hover:underline">
            See why the optimal works <ArrowRight size={13} />
          </button>
        </div>
      ) : (
        <div className="rounded-xl border border-teal/40 bg-teal-soft p-3 text-[13px] text-fg">
          <b className="text-teal">Optimal complexity.</b> {problem.insight.mnemonic} This problem is now in your review queue - you'll see it again in a day to lock it in.
        </div>
      )}
      {profile && (
        <section>
          <h4 className="mb-2 text-[13px] font-semibold">Growth vs. reference solutions</h4>
          <ComplexityChart series={growthSeries(problem, baselines, profile)} />
        </section>
      )}
      {profile && <Findings profile={profile} />}
      {next && (
        <Link to={`/problems/${next.id}`} className="inline-flex items-center gap-2 rounded-xl border border-line px-3 py-2 text-[13px] text-muted hover:border-line-strong hover:text-fg">
          Next: <b className="text-fg">{next.title}</b> <ArrowRight size={14} />
        </Link>
      )}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone: "teal" | "accent" | "sky" | "muted" }) {
  const color = { teal: "text-teal", accent: "text-accent", sky: "text-sky", muted: "text-muted" }[tone];
  return (
    <div className="rounded-xl border border-line bg-elev-2/50 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-faint">{label}</div>
      <div className={cn("font-mono text-[15px] font-bold", color)}>{value}</div>
    </div>
  );
}

function Failure({ problem, res }: { problem: ProblemDetail; res: SubmitResult }) {
  const { showTrace, traceView } = useWorkspace();
  const d = res.diagnosis;
  const f = res.failure;
  return (
    <div className="space-y-4">
      {d?.found ? (
        <>
          <div className="flex flex-wrap items-center gap-2 text-[13px] text-muted">
            <Bug size={15} className="text-rose" />
            {d.origin === "fuzz" ? (
              <span>Your code passed every hidden test, but the <b className="text-fg">fuzzer</b> found an input it gets wrong.</span>
            ) : (
              <span>Failed hidden test #{(f?.index ?? 0) + 1}{f?.argsSummary ? ` (${f.argsSummary})` : ""}.</span>
            )}
            {d.shrinkSteps !== undefined && d.originalSize !== undefined && d.size !== undefined && d.originalSize > d.size && (
              <span className="inline-flex items-center gap-1 rounded-md bg-violet-soft px-1.5 py-0.5 text-[11px] font-semibold text-violet">
                <Shrink size={11} /> shrunk from size {d.originalSize} → {d.size}
              </span>
            )}
          </div>
          <Block label="Smallest failing input">
            {Object.entries(d.args ?? {}).map(([k, val]) => (
              <div key={k}><span className="text-muted">{k} = </span>{lit(val)}</div>
            ))}
          </Block>
          <div className="grid gap-3 sm:grid-cols-2">
            <Block label="Expected" tone="teal">{lit(d.expected)}</Block>
            {d.error ? (
              <Block label={d.error.type} tone="rose">
                {d.error.message}
                {d.error.line ? <div className="mt-1 text-[11px] opacity-80">at line {d.error.line}</div> : null}
              </Block>
            ) : (
              <Block label="Your output" tone="rose">{lit(d.actual)}</Block>
            )}
          </div>
          {d.neighbour && (
            <p className="rounded-xl border border-line bg-elev-2/40 px-3 py-2 text-[12.5px] text-muted">
              <b className="text-fg">Contrast:</b> your code gets{" "}
              <span className="font-mono text-fg">{Object.entries(d.neighbour.args).map(([k, val]) => `${k}=${lit(val, 60)}`).join(", ")}</span>{" "}
              right. What's different about the failing input?
            </p>
          )}
          {d.pitfalls && d.pitfalls.length > 0 && (
            <div className="space-y-2">
              <h4 className="flex items-center gap-1.5 text-[13px] font-semibold"><Sparkles size={14} className="text-accent" /> Likely cause</h4>
              {d.pitfalls.map((p) => (
                <div key={p.id} className="rounded-xl border border-accent/30 bg-accent-soft px-3 py-2 text-[13px]">
                  <div className="font-semibold text-accent">{p.title}</div>
                  <div className="text-fg/85">{renderInline(p.explain)}</div>
                </div>
              ))}
            </div>
          )}
          {res.trace && (
            <Button
              variant="primary"
              onClick={() =>
                showTrace(traceView && traceView.trace === res.trace ? traceView : { trace: res.trace!, label: "Minimal failing input", args: d.args ?? {}, expected: d.expected, startAt: "end" })
              }
            >
              <Play size={14} /> Watch it fail, step by step
            </Button>
          )}
        </>
      ) : f ? (
        <div className="space-y-3">
          {f.args && (
            <Block label="Input">
              {Object.entries(f.args).map(([k, val]) => <div key={k}><span className="text-muted">{k} = </span>{lit(val)}</div>)}
            </Block>
          )}
          {f.error ? <Block label={f.error.type} tone="rose">{f.error.message}</Block> : <Block label="Your output" tone="rose">{lit(f.output)}</Block>}
          <Block label="Expected" tone="teal">{lit(f.expected)}</Block>
        </div>
      ) : null}
      {problem.pitfalls.length > 0 && !d?.pitfalls?.length && (
        <details className="text-[12.5px] text-muted">
          <summary className="cursor-pointer">Common mistakes on this problem</summary>
          <ul className="mt-2 space-y-1.5">
            {problem.pitfalls.map((p) => <li key={p.id}><b className="text-fg">{p.title}:</b> {renderInline(p.explain)}</li>)}
          </ul>
        </details>
      )}
    </div>
  );
}

function TooSlow({ problem, res, baselines }: { problem: ProblemDetail; res: SubmitResult; baselines: Baselines | null }) {
  const f = res.failure;
  const profile = res.profile;
  return (
    <div className="space-y-4">
      <p className="text-[13px] text-muted">
        Your answers were right on {res.passed} test{res.passed === 1 ? "" : "s"}, then test #{(f?.index ?? 0) + 1}
        {f?.argsSummary ? ` (${f.argsSummary})` : ""} ran out of operations
        {f?.error?.line ? <> - it was busy on <b className="text-fg">line {f.error.line}</b></> : null}. The budget is 20× what the optimal solution needs, so this means a slower growth rate, not a slow constant.
      </p>
      {profile && (
        <section>
          <h4 className="mb-2 text-[13px] font-semibold">How your code grows {profile.time && <span className="font-mono text-accent">≈ {profile.time.label}</span>}</h4>
          <ComplexityChart series={growthSeries(problem, baselines, profile)} />
        </section>
      )}
      {profile && <Findings profile={profile} />}
    </div>
  );
}
