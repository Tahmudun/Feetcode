import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Brain, ChevronFirst, ChevronLast, Footprints, Pause, Play, SkipBack, SkipForward, Sparkles } from "lucide-react";
import type { Lens } from "@/content/types";
import type { Trace } from "@/runtime/types";
import { cn } from "@/lib/utils";
import { logEvent } from "@/store/events";
import { useSettings } from "@/store/settings";
import { Kbd } from "@/ui/primitives";
import { CodePane } from "./CodePane";
import { autoNarrate, describeLine } from "./narrate";
import { buildScene, makeContext, type Panel, type Scene } from "./scene";
import { usePlayback } from "./usePlayback";
import { ArrayView } from "./panels/ArrayView";
import { GraphView } from "./panels/GraphView";
import { GridView, MapView, ObjectView, SetView, StackView } from "./panels/Collections";
import { scalarText } from "./decode";

export interface PlayerProps {
  trace: Trace;
  lens?: Lens;
  params?: string[];
  mode?: "lesson" | "debug";
  showCode?: boolean;
  footnotes?: { line: number; text: string }[];
  problemId?: string;
  initialIndex?: number | "end";
  onStep?: (scene: Scene) => void;
  onFinish?: () => void;
  className?: string;
  heat?: Record<number, number>;
}

function keyStepIndices(trace: Trace): number[] {
  const idx = trace.steps.map((s, i) => (s.t && !s.hide ? i : -1)).filter((i) => i >= 0);
  if (idx.length < 3) return trace.steps.map((_, i) => i);
  if (idx[0] !== 0) idx.unshift(0);
  const last = trace.steps.length - 1;
  if (idx[idx.length - 1] !== last) idx.push(last);
  return idx;
}

export function Stage({ scene, className }: { scene: Scene; className?: string }) {
  return (
    <div className={cn("flex flex-wrap items-start gap-x-8 gap-y-6", className)}>
      {scene.panels.map((p) => (
        <div key={p.key} className={cn("min-w-0 max-w-full", (p.kind === "graph" || (p.kind === "array" && p.view === "bars")) && "basis-full")}>
          <PanelView panel={p} all={scene.panels} />
        </div>
      ))}
      {scene.panels.length === 0 && scene.vars.length === 0 && (
        <div className="text-[13px] text-faint">No data structures in scope yet.</div>
      )}
    </div>
  );
}

function PanelView({ panel, all }: { panel: Panel; all: Panel[] }) {
  switch (panel.kind) {
    case "array":
      return <ArrayView panel={panel} />;
    case "stack":
      return <StackView panel={panel} all={all} />;
    case "map":
      return <MapView panel={panel} />;
    case "set":
      return <SetView panel={panel} />;
    case "grid":
      return <GridView panel={panel} />;
    case "graph":
      return <GraphView panel={panel} />;
    case "object":
      return <ObjectView panel={panel} />;
  }
}

export function VarsBar({ scene }: { scene: Scene }) {
  if (!scene.vars.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {scene.vars.map((v) => (
        <span
          key={v.name}
          className={cn(
            "inline-flex items-center gap-1 rounded-lg border px-2 py-1 font-mono text-[12px] transition-colors",
            v.state === "changed" ? "anim-flash border-accent/60 bg-accent-soft" : v.state === "new" ? "border-note/50 bg-note-soft" : "border-line bg-elev-2",
          )}
        >
          <span className="text-muted">{v.name}</span>
          <span className="text-faint">=</span>
          <span className={cn("font-semibold", v.text === "None" ? "text-faint" : "text-fg")}>{v.text}</span>
        </span>
      ))}
    </div>
  );
}

function CallStack({ scene }: { scene: Scene }) {
  if (scene.frames.length < 2) return null;
  return (
    <div className="rounded-xl border border-line bg-elev-2/50 p-2">
      <div className="mb-1 px-1 text-[10px] font-semibold uppercase tracking-wider text-faint">Call stack · {scene.frames.length} frames</div>
      <div className="flex flex-col-reverse gap-0.5">
        {scene.frames.map((f, i) => (
          <div
            key={f.id}
            className={cn("truncate rounded-md px-2 py-0.5 font-mono text-[11px]", i === scene.frames.length - 1 ? "bg-accent-soft text-accent" : "text-muted")}
            style={{ paddingLeft: 8 + i * 6 }}
          >
            {f.fn}({f.args}) <span className="text-faint">· line {f.line}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface Question {
  target: number;
  raw: number;
  line: number;
  code: string;
  values: string;
  kind: "if" | "while";
}

export function Player({
  trace, lens = {}, params = [], mode = "lesson", showCode = true, footnotes, problemId, initialIndex = 0, onStep, onFinish, className, heat,
}: PlayerProps) {
  const ctx = useMemo(() => makeContext(trace, lens, params), [trace, lens, params]);
  const [keySteps, setKeySteps] = useState(mode === "lesson");
  const visible = useMemo(() => (keySteps ? keyStepIndices(trace) : trace.steps.map((_, i) => i)), [keySteps, trace]);
  const speed = useSettings((s) => s.speed);
  const setSettings = useSettings((s) => s.set);
  const startAt = initialIndex === "end" ? visible.length - 1 : initialIndex;
  const pb = usePlayback(visible.length, speed, startAt);
  const raw = visible[Math.min(pb.index, visible.length - 1)] ?? 0;
  const scene = useMemo(() => buildScene(trace, raw, ctx), [trace, raw, ctx]);
  const narration = scene.authored ? scene.narration : autoNarrate(trace.steps, raw, ctx.codeLines);
  const [hotNote, setHotNote] = useState<number | null>(null);
  const notes = footnotes ?? trace.footnotes ?? [];
  const finished = useRef(false);

  useEffect(() => {
    onStep?.(scene);
    if (raw === trace.steps.length - 1 && !finished.current) {
      finished.current = true;
      onFinish?.();
    }
  }, [scene, onStep, onFinish, raw, trace.steps.length]);

  // ---- Predict mode -------------------------------------------------------
  const [predict, setPredict] = useState(false);
  const [question, setQuestion] = useState<Question | null>(null);
  const [revealState, setReveal] = useState<{ raw: number; correct: boolean; truth: boolean } | null>(null);
  const reveal = revealState?.raw === raw ? revealState : null;
  const [score, setScore] = useState({ right: 0, total: 0 });
  const answered = useRef(new Set<number>());

  const gate = useCallback(
    (target: number) => {
      const r = visible[target];
      const st = trace.steps[r];
      if (st.b === undefined || answered.current.has(r)) return true;
      const code = ctx.codeLines[st.l - 1] ?? "";
      const kind = describeLine(code);
      if (kind !== "if" && kind !== "while") return true;
      // Show the values the condition reads, as they were just before it ran.
      const before = trace.steps[Math.max(0, r - 1)];
      const frame = before.s[before.s.length - 1];
      const names = new Set(code.match(/[A-Za-z_][A-Za-z0-9_]*/g) ?? []);
      const values = (frame?.v ?? [])
        .filter(([n, v]) => names.has(n) && (typeof v !== "object" || v === null))
        .map(([n, v]) => `${n} = ${scalarText(v)}`)
        .join(",  ");
      setQuestion({ target, raw: r, line: st.l, code: code.trim(), values, kind });
      return false;
    },
    [visible, trace, ctx],
  );
  useEffect(() => {
    pb.setGate(predict ? gate : null);
  }, [predict, gate, pb]);

  const answer = (yes: boolean) => {
    if (!question) return;
    const truth = trace.steps[question.raw].b === 1;
    const correct = yes === truth;
    answered.current.add(question.raw);
    setScore((s) => ({ right: s.right + (correct ? 1 : 0), total: s.total + 1 }));
    if (problemId) logEvent({ t: "predict", p: problemId, ok: correct, ts: Date.now() });
    setReveal({ raw: question.raw, correct, truth });
    pb.seek(question.target);
    setQuestion(null);
  };

  const onKeyDown = (e: KeyboardEvent) => {
    if (question) {
      if (e.key.toLowerCase() === "y" || e.key.toLowerCase() === "t") answer(true);
      if (e.key.toLowerCase() === "n" || e.key.toLowerCase() === "f") answer(false);
      return;
    }
    if (e.key === "ArrowRight") { e.preventDefault(); pb.next(); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); pb.prev(); }
    else if (e.key === " ") { e.preventDefault(); pb.toggle(); }
    else if (e.key === "Home") { e.preventDefault(); pb.seek(0); }
    else if (e.key === "End") { e.preventDefault(); pb.seek(visible.length - 1); }
  };

  const errorLine = trace.error?.line ?? undefined;
  const branchKind = describeLine(ctx.codeLines[scene.line - 1] ?? "");

  return (
    <section
      tabIndex={0}
      onKeyDown={onKeyDown}
      aria-label="Execution player. Left and right arrows step; space plays."
      className={cn("@container flex min-h-0 flex-col gap-3 outline-none", className)}
    >
      {/* narration */}
      <div className="flex items-start gap-3 rounded-xl border border-line bg-elev-2/60 px-3.5 py-2.5">
        <span className="mt-0.5 shrink-0 rounded-md bg-accent px-1.5 font-mono text-[11px] font-bold text-accent-ink">
          {pb.index + 1}
        </span>
        <div className="min-w-0 flex-1">
          {question ? (
            <div className="anim-fade-up">
              <div className="flex items-center gap-2 text-[13px] font-semibold text-note">
                <Brain size={14} /> Predict: will this {question.kind === "while" ? "loop keep going" : "branch run"}?
              </div>
              <code className="mt-1 block truncate text-[12.5px] text-fg">line {question.line}: {question.code}</code>
              {question.values && <div className="mt-0.5 font-mono text-[11.5px] text-muted">{question.values}</div>}
              <div className="mt-2 flex gap-2">
                <button onClick={() => answer(true)} className="rounded-lg bg-ref-soft px-3 py-1 text-xs font-semibold text-ref hover:brightness-125">
                  True <Kbd className="ml-1">T</Kbd>
                </button>
                <button onClick={() => answer(false)} className="rounded-lg bg-warn-soft px-3 py-1 text-xs font-semibold text-warn hover:brightness-125">
                  False <Kbd className="ml-1">F</Kbd>
                </button>
              </div>
            </div>
          ) : (
            <>
              {reveal && (
                <div className={cn("anim-pop mb-1 text-[12px] font-bold", reveal.correct ? "text-ref" : "text-warn")}>
                  {reveal.correct ? "✓ Correct" : "✗ Not quite"} - it was {reveal.truth ? "True" : "False"}.
                </div>
              )}
              <p className={cn("text-[13.5px] leading-relaxed", scene.authored ? "text-fg" : "font-mono text-[12.5px] text-muted")} aria-live="polite">
                {narration || "…"}
              </p>
            </>
          )}
        </div>
        {predict && score.total > 0 && (
          <span className="shrink-0 rounded-md bg-note-soft px-2 py-0.5 font-mono text-[11px] font-bold text-note">
            {score.right}/{score.total}
          </span>
        )}
      </div>

      <div className={cn("grid min-h-0 flex-1 gap-3", showCode ? "@4xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.3fr)]" : "")}>
        {showCode && (
          <CodePane
            code={trace.code}
            line={scene.line}
            next={scene.next}
            branch={scene.branch}
            branchKind={branchKind}
            errorLine={errorLine}
            footnotes={notes}
            hotFootnote={hotNote}
            onFootnoteHover={setHotNote}
            heat={heat}
            className="max-h-[360px] @4xl:max-h-[460px]"
          />
        )}
        <div className="min-h-0 min-w-0 space-y-4 overflow-auto rounded-xl border border-line bg-bg/40 p-4 bg-grid">
          <Stage scene={scene} />
          <VarsBar scene={scene} />
          <CallStack scene={scene} />
          {scene.ret !== undefined && (
            <div className="anim-pop inline-flex items-center gap-2 rounded-lg border border-ref/40 bg-ref-soft px-2.5 py-1 font-mono text-[12px] text-ref">
              <Sparkles size={13} /> returns {scene.ret}
            </div>
          )}
          {scene.exc && (
            <div className="anim-pop rounded-lg border border-warn/40 bg-warn-soft px-2.5 py-1.5 font-mono text-[12px] text-warn">💥 {scene.exc}</div>
          )}
          {scene.stdout && (
            <pre className="max-h-24 overflow-auto rounded-lg border border-line bg-inset px-2.5 py-1.5 text-[11.5px] text-muted">{scene.stdout}</pre>
          )}
        </div>
      </div>

      {/* transport */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-0.5">
          <TBtn label="First step (Home)" onClick={() => pb.seek(0)}><ChevronFirst size={16} /></TBtn>
          <TBtn label="Previous (←)" onClick={pb.prev}><SkipBack size={15} /></TBtn>
          <button
            onClick={pb.toggle}
            aria-label={pb.playing ? "Pause (space)" : "Play (space)"}
            className="mx-1 flex h-9 w-9 items-center justify-center rounded-full bg-accent text-accent-ink shadow-[0_4px_16px_-4px_var(--accent)] transition-transform hover:scale-105 active:scale-95"
          >
            {pb.playing ? <Pause size={16} /> : <Play size={16} className="translate-x-px" />}
          </button>
          <TBtn label="Next (→)" onClick={pb.next}><SkipForward size={15} /></TBtn>
          <TBtn label="Last step (End)" onClick={() => pb.seek(visible.length - 1)}><ChevronLast size={16} /></TBtn>
        </div>
        <Scrubber trace={trace} visible={visible} index={pb.index} onSeek={pb.seek} />
        <span className="w-20 text-right font-mono text-[11px] text-faint">
          {pb.index + 1} / {visible.length}
        </span>
        <select
          value={speed}
          onChange={(e) => setSettings({ speed: Number(e.target.value) })}
          className="h-7 rounded-md border border-line bg-elev-2 px-1.5 text-[11px] text-muted"
          aria-label="Playback speed"
        >
          {[0.5, 1, 2, 4, 8].map((s) => (
            <option key={s} value={s}>{s}×</option>
          ))}
        </select>
        <button
          onClick={() => {
            const r = raw;
            setKeySteps((k) => !k);
            requestAnimationFrame(() => {
              const list = !keySteps ? keyStepIndices(trace) : trace.steps.map((_, i) => i);
              let best = 0;
              list.forEach((x, i) => { if (x <= r) best = i; });
              pb.seek(best);
            });
          }}
          className={cn("flex h-7 items-center gap-1 rounded-md px-2 text-[11px] font-medium", keySteps ? "bg-accent-soft text-accent" : "text-muted hover:bg-hover")}
          title="Key steps show only narrated moments; every line shows the full execution"
        >
          <Footprints size={13} /> {keySteps ? "Key steps" : "Every line"}
        </button>
        <button
          onClick={() => { setPredict((p) => !p); setQuestion(null); }}
          className={cn("flex h-7 items-center gap-1 rounded-md px-2 text-[11px] font-medium", predict ? "bg-note-soft text-note" : "text-muted hover:bg-hover")}
          title="Pause at every decision and guess the outcome before seeing it"
        >
          <Brain size={13} /> Predict
        </button>
      </div>

      {notes.length > 0 && (
        <footer className="border-t border-line pt-3">
          <div className="mb-2 h-px w-12 bg-line-strong" />
          <ol className="space-y-1.5">
            {notes.map((n, i) => (
              <li
                key={i}
                onMouseEnter={() => setHotNote(i)}
                onMouseLeave={() => setHotNote(null)}
                className={cn("flex gap-2 rounded-md px-1.5 py-0.5 text-[12.5px] leading-relaxed transition-colors", hotNote === i ? "bg-accent-soft text-fg" : "text-muted")}
              >
                <sup className="mt-1.5 font-mono text-[10px] font-bold text-accent">{i + 1}</sup>
                <span>
                  <span className="mr-1 font-mono text-[10px] text-faint">L{n.line}</span>
                  {n.text}
                </span>
              </li>
            ))}
          </ol>
        </footer>
      )}
    </section>
  );
}

function TBtn({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} aria-label={label} title={label} className="flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-hover hover:text-fg">
      {children}
    </button>
  );
}

function Scrubber({ trace, visible, index, onSeek }: { trace: Trace; visible: number[]; index: number; onSeek: (i: number) => void }) {
  const n = visible.length;
  return (
    <div className="relative mx-1 h-8 min-w-40 flex-1">
      <div className="absolute inset-x-0 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-elev-2" />
      <div className="absolute left-0 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-accent/70" style={{ width: `${n > 1 ? (index / (n - 1)) * 100 : 100}%` }} />
      {n <= 400 &&
        visible.map((r, i) => {
          const st = trace.steps[r];
          const mark = st.k === "exc" ? "bg-warn" : st.k === "call" ? "bg-note" : st.k === "return" ? "bg-ref" : null;
          if (!mark) return null;
          return <span key={i} className={cn("absolute top-1/2 h-2.5 w-[3px] -translate-y-1/2 rounded-full", mark)} style={{ left: `${n > 1 ? (i / (n - 1)) * 100 : 0}%` }} />;
        })}
      <input
        type="range"
        min={0}
        max={Math.max(0, n - 1)}
        value={index}
        onChange={(e) => onSeek(Number(e.target.value))}
        aria-label="Timeline"
        className="absolute inset-0 w-full cursor-pointer opacity-0"
      />
      <span
        className="pointer-events-none absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-accent bg-bg shadow"
        style={{ left: `${n > 1 ? (index / (n - 1)) * 100 : 0}%` }}
      />
    </div>
  );
}
