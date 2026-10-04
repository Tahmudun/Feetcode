import { Link } from "react-router";
import { ArrowRight, Brain, Bug, CalendarDays, Eye, Flame, Gauge, Microscope, Repeat, ScanSearch, Sparkles, Wand2 } from "lucide-react";
import { patterns, problemById, problems } from "@/content";
import { cn } from "@/lib/utils";
import { useStudy } from "@/store/events";
import { nextUp, patternMastery } from "@/store/progress";
import { Button, DifficultyBadge, Panel, ProgressRing } from "@/ui/primitives";
import { Heatmap } from "@/ui/Heatmap";
import { HeroDemo } from "./HeroDemo";

const FEATURES = [
  { icon: Eye, tone: "text-accent", title: "Visualize your code", text: "Not just the reference answer - every variable, pointer, comparison and linked-list arrow of the code you wrote, synced to your editor." },
  { icon: Bug, tone: "text-rose", title: "Failures, explained", text: "A fuzzer hunts for inputs you get wrong and shrinks them to the smallest example - then replays exactly where it breaks." },
  { icon: Gauge, tone: "text-teal", title: "Complexity, measured", text: "Your growth curve next to brute force and optimal, a heatmap of hot lines, and hidden costs like `x in list` called out." },
  { icon: Brain, tone: "text-violet", title: "Predict mode", text: "Guess every branch before it runs. Active recall inside the visualizer is how tricks stop being tricks." },
  { icon: Microscope, tone: "text-sky", title: "Deterministic judge", text: "Time limits counted in operations, not milliseconds. Same code, same verdict - on any laptop, every time." },
  { icon: Repeat, tone: "text-accent", title: "Spaced repetition", text: "Solved problems come back right before you'd forget them, as recall cards: pattern, insight, the one-line trick." },
];

export function HomePage() {
  const progress = useStudy((s) => s.progress);
  const started = progress.byProblem.size > 0;
  const { due, resume, fresh } = nextUp(progress, problems);

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
              shrinks the failure to a two-element example and replays it step by step. When it's slow, it shows you the line that
              grows.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link to={`/problems/${resume?.id ?? fresh?.id ?? "two-sum"}`}>
                <Button variant="primary" size="lg">
                  {started ? "Continue" : "Start with Two Sum"} <ArrowRight size={16} />
                </Button>
              </Link>
              <Link to="/problems/trapping-rain-water">
                <Button size="lg">Watch Trapping Rain Water click</Button>
              </Link>
              <Link to="/playground" className="flex items-center gap-1 text-[13px] text-muted hover:text-accent">
                <Wand2 size={14} /> or visualize any Python
              </Link>
            </div>
            <p className="mt-6 font-mono text-[11px] text-faint">
              <sup className="text-accent">1</sup> yes, the name is a pun. the footnotes are real - every insight is pinned to a line of code.
            </p>
          </div>
          <HeroDemo />
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-14 px-4 pt-12 sm:px-6">
        {started && (
          <section className="grid gap-4 md:grid-cols-[1.2fr_1fr_1fr]">
            <Panel className="p-5">
              <div className="mb-3 flex items-center gap-2 text-[13px] font-semibold"><CalendarDays size={15} className="text-teal" /> Your activity</div>
              <Heatmap activity={progress.activity} weeks={18} />
              <div className="mt-3 flex items-center gap-4 text-xs text-muted">
                <span className="flex items-center gap-1"><Flame size={13} className="text-accent" /> {progress.streak}-day streak</span>
                <span>best {progress.longestStreak}</span>
                <span>{progress.solvedCount} solved</span>
                <Link to="/stats" className="ml-auto text-accent hover:underline">Stats →</Link>
              </div>
            </Panel>
            <Panel className="flex flex-col p-5">
              <div className="mb-2 flex items-center gap-2 text-[13px] font-semibold"><Repeat size={15} className="text-violet" /> Due for review</div>
              <div className="font-display text-4xl font-extrabold">{due.length}</div>
              <p className="mt-1 flex-1 text-xs text-muted">
                {due.length ? `${problemById.get(due[0])?.title} and friends are about to fade.` : "Nothing's fading yet. Solve something to seed your queue."}
              </p>
              <Link to="/review" className="mt-3">
                <Button variant={due.length ? "primary" : "secondary"} size="md" className="w-full">Start review</Button>
              </Link>
            </Panel>
            <Panel className="flex flex-col p-5">
              <div className="mb-2 flex items-center gap-2 text-[13px] font-semibold"><ArrowRight size={15} className="text-accent" /> Up next</div>
              {(resume ?? fresh) && (
                <>
                  <div className="text-[15px] font-semibold">{(resume ?? fresh)!.title}</div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted">
                    <DifficultyBadge value={(resume ?? fresh)!.difficulty} /> {resume ? "in progress" : "next on the roadmap"}
                  </div>
                  <p className="mt-2 flex-1 text-xs text-faint">{(resume ?? fresh)!.oneLiner.slice(0, 110)}…</p>
                  <Link to={`/problems/${(resume ?? fresh)!.id}`} className="mt-3">
                    <Button size="md" className="w-full">Open</Button>
                  </Link>
                </>
              )}
            </Panel>
          </section>
        )}

        <section>
          <div className="mb-5 flex items-end justify-between">
            <div>
              <h2 className="font-display text-2xl font-bold">Five patterns, 38 problems</h2>
              <p className="text-[13px] text-muted">The NeetCode 150 core, in roadmap order. Learn the pattern once, recognize it everywhere.</p>
            </div>
            <Link to="/patterns" className="text-[13px] text-accent hover:underline">Roadmap →</Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {patterns.map((p) => {
              const m = patternMastery(progress, problems, p.id);
              return (
                <Link key={p.id} to={`/patterns/${p.id}`} className="group">
                  <Panel className="h-full p-4 transition-all group-hover:-translate-y-0.5 group-hover:border-line-strong">
                    <div className="flex items-start justify-between">
                      <div className="font-semibold">{p.name}</div>
                      <ProgressRing value={m.mastery} size={34} tone="var(--teal)">
                        <span className="text-[9px] font-bold text-muted">{m.solved}/{m.total}</span>
                      </ProgressRing>
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-muted">{p.tagline}</p>
                  </Panel>
                </Link>
              );
            })}
          </div>
        </section>

        <section>
          <h2 className="mb-5 font-display text-2xl font-bold">More than a judge</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <Panel key={f.title} className="p-5">
                <f.icon size={20} className={f.tone} />
                <div className="mt-3 font-semibold">{f.title}</div>
                <p className="mt-1 text-[13px] leading-relaxed text-muted">{f.text.replace(/`/g, "")}</p>
              </Panel>
            ))}
          </div>
        </section>

        <section className={cn("rounded-2xl border border-line bg-elev p-6 text-[13px] text-muted")}>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
            <span className="flex items-center gap-2"><ScanSearch size={15} className="text-violet" /> No accounts, no servers: your code and progress never leave this browser.</span>
            <span>Python 3.14 via WebAssembly (Pyodide)</span>
            <a className="text-accent hover:underline" href="https://github.com/Tahmudun/Feetcode" target="_blank" rel="noreferrer">How it works →</a>
          </div>
        </section>
      </div>
    </div>
  );
}
