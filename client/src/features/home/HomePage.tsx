import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router";
import { ArrowRight, Brain, Bug, Eye, Flame, Gauge, Microscope, Repeat, ScanSearch, Sparkles, Wand2 } from "lucide-react";
import { patterns, problems } from "@/content";
import { startSession, useStudy } from "@/store/events";
import { dueCards, patternMastery } from "@/store/progress";
import { currentPattern, planSession } from "@/store/session";
import { Button, Panel } from "@/ui/primitives";
import { Heatmap } from "@/ui/Heatmap";
import { PathMap } from "@/features/session/PathMap";
import { TonightPlan } from "@/features/session/TonightPlan";
import { itemHref } from "@/features/session/kinds";
import { HeroDemo } from "./HeroDemo";

const FEATURES = [
  { icon: Eye, tone: "text-accent", title: "Visualize your code", text: "Not just the reference answer: every variable, pointer, comparison and linked-list arrow of the code you wrote, with live values in your editor." },
  { icon: Bug, tone: "text-warn", title: "Where it goes wrong", text: "A fuzzer finds the smallest input you get wrong, then pins the first line where your run leaves the reference's." },
  { icon: Gauge, tone: "text-ref", title: "Complexity, measured", text: "Your growth curve next to brute force and optimal, a heatmap of hot lines, and hidden costs like x in list called out." },
  { icon: Brain, tone: "text-note", title: "Predict mode", text: "Guess every branch before it runs. Active recall inside the visualizer is how tricks stop being tricks." },
  { icon: Microscope, tone: "text-sky", title: "Deterministic judge", text: "Time limits counted in operations, not milliseconds. Same code, same verdict, on any laptop, every time." },
  { icon: Repeat, tone: "text-accent", title: "A plan every night", text: "Recall what's fading, fix what you left broken, learn one new thing, and stretch into the next pattern when you're ready." },
];

export function HomePage() {
  const progress = useStudy((s) => s.progress);
  const session = useStudy((s) => s.session);
  return progress.byProblem.size > 0 || session ? <Tonight /> : <Welcome />;
}

/** Returning users: tonight's plan, your rhythm, and the path. */
function Tonight() {
  const progress = useStudy((s) => s.progress);
  const session = useStudy((s) => s.session);
  const [now] = useState(() => Date.now());
  const tonight = useMemo(() => {
    const items = session ? session.items.filter((it) => it.status !== "done") : planSession(progress, problems, patterns, now);
    return new Set(items.map((it) => it.p));
  }, [session, progress, now]);
  const due = dueCards(progress, now).length;
  const reviews = useStudy((s) => s.events.filter((e) => e.t === "review").length);

  return (
    <div className="mx-auto max-w-6xl space-y-12 px-4 pb-24 pt-8 sm:px-6">
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)]">
        <TonightPlan className="anim-fade-up" />
        <Panel className="flex flex-col p-5">
          <div className="flex items-end justify-between gap-3">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">Your rhythm</div>
              <div className="mt-1 flex items-baseline gap-2">
                <Flame size={22} className={progress.streak ? "self-center fill-accent/30 text-accent" : "self-center text-faint"} />
                <span className="font-display text-4xl font-extrabold">{progress.streak}</span>
                <span className="text-[13px] text-muted">day streak · best {progress.longestStreak}</span>
              </div>
            </div>
            <Link to="/stats" className="text-[12.5px] text-accent hover:underline">Stats →</Link>
          </div>
          <div className="mt-4">
            <Heatmap activity={progress.activity} weeks={17} />
          </div>
          <dl className="mt-4 grid grid-cols-3 gap-2 text-center">
            <Stat label="solved" value={`${progress.solvedCount}/${problems.length}`} />
            <Stat label="due now" value={String(due)} />
            <Stat label="reviews done" value={String(reviews)} />
          </dl>
          <div className="mb-4 mt-5 space-y-2">
            <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-faint">Mastery by pattern</div>
            {patterns.map((p) => {
              const m = patternMastery(progress, problems, p.id);
              return (
                <Link key={p.id} to={`/patterns/${p.id}`} className="group grid grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)_36px] items-center gap-3 text-[12.5px]">
                  <span className="truncate text-muted group-hover:text-accent">{p.name}</span>
                  <span className="h-1.5 overflow-hidden rounded-full bg-elev-2">
                    <span className="block h-full rounded-full bg-ref transition-all" style={{ width: `${m.mastery * 100}%` }} />
                  </span>
                  <span className="text-right font-mono text-[11px] text-faint">{m.solved}/{m.total}</span>
                </Link>
              );
            })}
          </div>
          <div className="mt-auto flex flex-wrap gap-x-4 gap-y-1 border-t border-line pt-3 text-[12.5px]">
            <Link to="/review?mode=patterns" className="text-muted hover:text-accent">Name that pattern →</Link>
            <Link to="/playground" className="text-muted hover:text-accent">Visualize any Python →</Link>
          </div>
        </Panel>
      </div>

      <section>
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="font-display text-2xl font-bold">Your path</h2>
            <p className="text-[13px] text-muted">Every problem is a star: solve it to light it, review it and it burns brighter. Tonight's are pulsing.</p>
          </div>
          <Link to="/patterns" className="text-[13px] text-accent hover:underline">Pattern guides →</Link>
        </div>
        <Panel className="px-4 pb-4 pt-6 sm:px-6">
          <PathMap progress={progress} tonight={tonight} current={currentPattern(progress, problems)} />
        </Panel>
      </section>

      <Footer />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-elev-2/50 px-2 py-2">
      <dd className="font-display text-xl font-bold">{value}</dd>
      <dt className="text-[11px] text-faint">{label}</dt>
    </div>
  );
}

/** First visit: what Feetcode is, the first night's plan, and the whole path ahead. */
function Welcome() {
  const progress = useStudy((s) => s.progress);
  const navigate = useNavigate();
  const [now] = useState(() => Date.now());
  const plan = useMemo(() => planSession(progress, problems, patterns, now), [progress, now]);
  const first = plan[0];
  const begin = () => {
    if (!first) return;
    startSession(plan);
    navigate(itemHref(first));
  };

  return (
    <div className="pb-24">
      <section className="relative overflow-hidden border-b border-line">
        <div className="bg-grid absolute inset-0 opacity-60 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[1fr_1.05fr] lg:py-20">
          <div className="anim-fade-up">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-line bg-elev px-3 py-1 text-xs text-muted">
              <Sparkles size={13} className="text-accent" /> Free forever · Python runs in your browser
            </div>
            <h1 className="font-display text-[44px] font-extrabold leading-[1.02] tracking-tight sm:text-[56px]">
              See <em className="not-italic text-accent">why</em> your
              <br />
              code works.
            </h1>
            <p className="mt-5 max-w-lg text-[16px] leading-relaxed text-muted">
              Interview prep that runs, judges and <b className="text-fg">visualizes the code you write</b>. When it fails, Feetcode
              finds the smallest input that breaks it and points at the line where your run leaves the reference's. Every night it
              plans what to practice next.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button variant="primary" size="lg" onClick={begin}>
                Start tonight: {first ? problems.find((p) => p.id === first.p)?.title : "Two Sum"} <ArrowRight size={16} />
              </Button>
              <Button size="lg" onClick={() => navigate("/problems/trapping-rain-water")}>See the rain-water trick</Button>
              <Link to="/playground" className="flex items-center gap-1 text-[13px] text-muted hover:text-accent">
                <Wand2 size={14} /> or visualize any Python
              </Link>
            </div>
            <p className="mt-6 font-mono text-[11px] text-faint">
              <sup className="text-accent">1</sup> yes, the name is a pun. the footnotes are real: every insight is pinned to a line of code.
            </p>
          </div>
          <HeroDemo />
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-14 px-4 pt-12 sm:px-6">
        <section>
          <div className="mb-3">
            <h2 className="font-display text-2xl font-bold">The path: five patterns, {problems.length} problems</h2>
            <p className="text-[13px] text-muted">
              The NeetCode 150 core as one sky. Learn a pattern's trick once, then recognize it everywhere. Your first star is pulsing.
            </p>
          </div>
          <Panel className="px-4 pb-4 pt-6 sm:px-6">
            <PathMap progress={progress} tonight={new Set(first ? [first.p] : [])} />
          </Panel>
        </section>

        <section>
          <h2 className="mb-5 font-display text-2xl font-bold">More than a judge</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <Panel key={f.title} className="p-5">
                <f.icon size={20} className={f.tone} />
                <div className="mt-3 font-semibold">{f.title}</div>
                <p className="mt-1 text-[13px] leading-relaxed text-muted">{f.text}</p>
              </Panel>
            ))}
          </div>
        </section>

        <Footer />
      </div>
    </div>
  );
}

function Footer() {
  return (
    <section className="rounded-2xl border border-line bg-elev p-6 text-[13px] text-muted">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
        <span className="flex items-center gap-2"><ScanSearch size={15} className="text-note" /> No accounts, no servers: your code and progress never leave this browser.</span>
        <span>Python 3.14 via WebAssembly (Pyodide)</span>
        <a className="text-accent hover:underline" href="https://github.com/Tahmudun/Feetcode" target="_blank" rel="noreferrer">How it works →</a>
      </div>
    </section>
  );
}
