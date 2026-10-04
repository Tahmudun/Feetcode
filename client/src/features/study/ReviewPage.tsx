import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import { Brain, CalendarClock, Eye, Radar, Repeat, Shuffle } from "lucide-react";
import { loadProblem, patterns, problemById, problems } from "@/content";
import type { PatternId, ProblemDetail } from "@/content/types";
import { cn, DAY_MS } from "@/lib/utils";
import { logEvent, useStudy } from "@/store/events";
import { dueCards, newCard, schedule, type Grade } from "@/store/progress";
import { Button, DifficultyBadge, Empty, Kbd, Panel, Spinner, Tabs } from "@/ui/primitives";
import { Markdown, renderInline } from "@/ui/Markdown";

export default function ReviewPage() {
  const [mode, setMode] = useState<"recall" | "patterns">("recall");
  return (
    <div className="mx-auto max-w-3xl px-4 pb-24 pt-8 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight">Review</h1>
          <p className="mt-1 text-muted">Ten focused minutes beat an hour of re-solving. Recall first, then check.</p>
        </div>
        <Tabs
          tabs={[
            { id: "recall", label: <><Repeat size={14} /> Recall cards</> },
            { id: "patterns", label: <><Radar size={14} /> Name that pattern</> },
          ]}
          value={mode}
          onChange={setMode}
        />
      </div>
      <div className="mt-6">{mode === "recall" ? <RecallSession /> : <PatternQuiz />}</div>
    </div>
  );
}

const GRADES: { g: Grade; label: string; tone: string }[] = [
  { g: 0, label: "Again", tone: "bg-rose-soft text-rose" },
  { g: 1, label: "Hard", tone: "bg-accent-soft text-accent" },
  { g: 2, label: "Good", tone: "bg-teal-soft text-teal" },
  { g: 3, label: "Easy", tone: "bg-sky-soft text-sky" },
];

function interval(days: number) {
  if (days <= 0) return "10m";
  if (days < 1) return `${Math.round(days * 24)}h`;
  return days < 30 ? `${Math.round(days)}d` : `${Math.round(days / 30)}mo`;
}

function RecallSession() {
  const progress = useStudy((s) => s.progress);
  const [extra, setExtra] = useState<string[]>([]);
  const queue = useMemo(() => [...dueCards(progress), ...extra.filter((x) => !dueCards(progress).includes(x))], [progress, extra]);
  const [revealed, setRevealed] = useState(false);
  const [detail, setDetail] = useState<{ id: string; p: ProblemDetail } | null>(null);
  const [now] = useState(() => Date.now()); // render must stay pure: one clock reading per session
  const current = queue[0];

  useEffect(() => {
    if (current) loadProblem(current).then((p) => setDetail({ id: current, p }));
  }, [current]);

  const grade = (g: Grade) => {
    if (!current) return;
    logEvent({ t: "review", p: current, g, ts: Date.now() });
    setExtra((xs) => xs.filter((x) => x !== current));
    setRevealed(false);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!current) return;
      if (e.key === " " && !revealed) {
        e.preventDefault();
        setRevealed(true);
      } else if (revealed && ["1", "2", "3", "4"].includes(e.key)) grade((Number(e.key) - 1) as Grade);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (!current) {
    const upcoming = [...progress.byProblem.entries()].filter(([, p]) => p.card).sort((a, b) => a[1].card!.due - b[1].card!.due).slice(0, 5);
    const solved = [...progress.byProblem.entries()].filter(([, p]) => p.status === "solved").map(([id]) => id);
    return (
      <Panel className="p-2">
        <Empty icon={<CalendarClock size={28} />} title="All caught up">
          {upcoming.length ? "Nothing is due right now. Next up:" : "Solve problems to seed your review queue - each accepted problem comes back tomorrow, then at growing intervals."}
        </Empty>
        {upcoming.length > 0 && (
          <ul className="mx-auto mb-6 max-w-sm space-y-1.5">
            {upcoming.map(([id, p]) => (
              <li key={id} className="flex justify-between text-[13px]">
                <span className="text-fg">{problemById.get(id)?.title}</span>
                <span className="text-faint">in {interval((p.card!.due - now) / DAY_MS)}</span>
              </li>
            ))}
          </ul>
        )}
        {solved.length > 0 && (
          <div className="mb-6 flex justify-center">
            <Button onClick={() => setExtra(solved.sort(() => Math.random() - 0.5).slice(0, 5))}><Shuffle size={14} /> Practice 5 anyway</Button>
          </div>
        )}
      </Panel>
    );
  }

  const p = detail?.id === current ? detail.p : null;
  const card = progress.byProblem.get(current)?.card ?? newCard(now);
  const firstPara = p?.statement.split(/\n\s*\n/)[0] ?? "";
  return (
    <div>
      <div className="mb-3 flex items-center gap-2 text-xs text-muted">
        <span className="rounded-full bg-accent-soft px-2 py-0.5 font-semibold text-accent">{queue.length} left</span>
        <span>Space to reveal · 1-4 to grade</span>
      </div>
      {!p ? (
        <div className="flex h-60 items-center justify-center"><Spinner className="text-accent" /></div>
      ) : (
        <Panel className="anim-fade-up overflow-hidden">
          <div className="border-b border-line p-6">
            <div className="flex items-center gap-2">
              <DifficultyBadge value={p.difficulty} />
              <span className="font-mono text-xs text-faint">#{p.number}</span>
            </div>
            <h2 className="mt-2 font-display text-2xl font-bold">{p.title}</h2>
            <Markdown text={firstPara} className="mt-2 text-[14px] text-muted" />
            {!revealed && (
              <div className="mt-5 rounded-xl border border-dashed border-line-strong p-4 text-[13px] text-muted">
                <div className="mb-1 flex items-center gap-2 font-semibold text-fg"><Brain size={15} className="text-violet" /> Before you reveal:</div>
                Which pattern? What's the one-line trick? What's the time and space? Say it out loud.
              </div>
            )}
          </div>
          {revealed ? (
            <div className="space-y-4 p-6">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wider text-accent">{p.insight.pattern} · {p.optimal.time} time · {p.optimal.space} space</div>
                <p className="mt-1 font-display text-[17px] font-semibold leading-snug">{renderInline(p.insight.oneLiner)}</p>
                <p className="mt-2 text-[13px] italic text-muted">"{p.insight.mnemonic}"</p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {p.insight.recall.map((r) => (
                  <div key={r.q} className="rounded-xl border border-line bg-elev-2/40 p-3 text-[13px]">
                    <div className="font-medium">{r.q}</div>
                    <div className="mt-1 text-muted">{renderInline(r.a)}</div>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-2 border-t border-line pt-4">
                <span className="mr-1 text-xs text-muted">How well did you recall it?</span>
                {GRADES.map(({ g, label, tone }) => (
                  <button key={g} onClick={() => grade(g)} className={cn("rounded-lg px-3 py-1.5 text-[13px] font-semibold transition-transform hover:scale-105", tone)}>
                    {label} <span className="ml-1 font-mono text-[10px] opacity-70">{interval(g === 0 ? 0 : schedule(card, g, 0).interval)}</span>
                    <Kbd className="ml-1.5">{g + 1}</Kbd>
                  </button>
                ))}
                <Link to={`/problems/${p.id}`} className="ml-auto text-xs text-accent hover:underline">Open problem →</Link>
              </div>
            </div>
          ) : (
            <div className="flex justify-center p-5">
              <Button variant="primary" onClick={() => setRevealed(true)}><Eye size={15} /> Reveal <Kbd className="ml-1">space</Kbd></Button>
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}

function PatternQuiz() {
  const [round, setRound] = useState(0);
  const [pick, setPick] = useState<PatternId | null>(null);
  const [score, setScore] = useState({ right: 0, total: 0 });
  const [detail, setDetail] = useState<ProblemDetail | null>(null);
  const target = useMemo(() => problems[(round * 7919 + 13) % problems.length], [round]);

  useEffect(() => {
    loadProblem(target.id).then(setDetail);
  }, [target]);

  const choose = (id: PatternId) => {
    if (pick) return;
    setPick(id);
    setScore((s) => ({ right: s.right + (id === target.pattern ? 1 : 0), total: s.total + 1 }));
  };
  const next = () => {
    setPick(null);
    setRound((r) => r + 1 + Math.floor(Math.random() * 5));
  };
  const statement = detail?.id === target.id ? detail.statement : null;
  return (
    <div>
      <div className="mb-3 flex items-center justify-between text-xs text-muted">
        <span>Read the problem, then pick its pattern - the skill interviews actually test.</span>
        <span className="rounded-full bg-violet-soft px-2 py-0.5 font-semibold text-violet">{score.right}/{score.total}</span>
      </div>
      <Panel className="p-6">
        {statement ? <Markdown text={statement} className="text-[14px] leading-relaxed text-fg/90" /> : <div className="skeleton h-24 rounded-lg" />}
        <div className="mt-5 grid gap-2 sm:grid-cols-2">
          {patterns.map((p) => {
            const right = pick && p.id === target.pattern;
            const wrong = pick === p.id && p.id !== target.pattern;
            return (
              <button
                key={p.id}
                onClick={() => choose(p.id)}
                className={cn(
                  "rounded-xl border px-4 py-3 text-left text-[13.5px] font-medium transition-colors",
                  right ? "border-teal bg-teal-soft text-teal" : wrong ? "border-rose bg-rose-soft text-rose" : "border-line hover:border-line-strong hover:bg-hover",
                )}
              >
                {p.name}
              </button>
            );
          })}
        </div>
        {pick && (
          <div className="anim-fade-up mt-5 border-t border-line pt-4 text-[13px]">
            <div className="font-semibold">{target.title}</div>
            <p className="mt-1 text-muted">{renderInline(target.oneLiner)}</p>
            <div className="mt-3 flex gap-2">
              <Button variant="primary" onClick={next}>Next problem</Button>
              <Link to={`/problems/${target.id}`}><Button>Open it</Button></Link>
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}
