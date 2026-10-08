import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { BookOpen, ChevronLeft, ChevronRight, Eye, FileText, List, NotebookPen, Play, RotateCcw, Send, Settings2 } from "lucide-react";
import { loadProblem, neighbours, problemById } from "@/content";
import type { ProblemDetail } from "@/content/types";
import { CodeEditor, type CodeEditorHandle } from "@/editor/CodeEditor";
import { cn, modKey } from "@/lib/utils";
import { useDesktop } from "@/lib/useMedia";
import { useSettings } from "@/store/settings";
import { useStudy } from "@/store/events";
import { Button, DifficultyBadge, IconButton, Kbd, Spinner, Tabs } from "@/ui/primitives";
import { SplitPane } from "@/ui/SplitPane";
import { StatusIcon } from "@/features/problems/ProblemsPage";
import { NotFound } from "@/app/NotFound";
import { useWorkspace, type LeftTab } from "./store";
import { DescriptionTab } from "./DescriptionTab";
import { LearnTab } from "./LearnTab";
import { VisualizeTab } from "./VisualizeTab";
import { NotesTab } from "./NotesTab";
import { ConsolePanel } from "./ConsolePanel";
import { Timer } from "./Timer";

export default function WorkspacePage() {
  const { id = "" } = useParams();
  const summary = problemById.get(id);
  const [loaded, setLoaded] = useState<ProblemDetail | null>(null);
  const load = useWorkspace((s) => s.load);
  const problem = loaded?.id === id ? loaded : null; // a stale problem never renders under a new URL

  useEffect(() => {
    let alive = true;
    if (!summary) return;
    loadProblem(id).then((p) => {
      if (!alive) return;
      load(p);
      setLoaded(p);
    });
    return () => {
      alive = false;
    };
  }, [id, summary, load]);

  if (!summary) return <NotFound />;
  if (!problem) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner className="text-accent" />
      </div>
    );
  }
  return <Workspace problem={problem} />;
}

function Workspace({ problem }: { problem: ProblemDetail }) {
  const ws = useWorkspace();
  const { fontSize, vim, set: setSettings } = useSettings();
  const status = useStudy((s) => s.progress.byProblem.get(problem.id)?.status);
  const editor = useRef<CodeEditorHandle>(null);
  const navigate = useNavigate();
  const { prev, next } = neighbours(problem.id);
  const [showSettings, setShowSettings] = useState(false);
  const [mobileView, setMobileView] = useState<"problem" | "code">("problem");
  const desktop = useDesktop();
  // The editor shows two layers: where the player is (line, live values) over what analysis found (the
  // pinned finding, heat). An error line from either wins.
  const marks = useMemo(
    () => ({ ...ws.analysisMarks, ...ws.stepMarks, errorLine: ws.stepMarks.errorLine ?? ws.analysisMarks.errorLine }),
    [ws.analysisMarks, ws.stepMarks],
  );

  // Keep the editor in sync when code changes from outside (reset, load a submission).
  useEffect(() => {
    editor.current?.setValue(ws.code);
  }, [ws.code]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey)) return;
      if (e.key === "Enter" && e.shiftKey) {
        e.preventDefault();
        void useWorkspace.getState().submit();
      } else if (e.key === "Enter") {
        e.preventDefault();
        void useWorkspace.getState().run();
      } else if (e.key === ".") {
        e.preventDefault();
        void useWorkspace.getState().visualize();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const tabs: { id: LeftTab; label: React.ReactNode }[] = [
    { id: "description", label: <><FileText size={14} /> Problem</> },
    { id: "learn", label: <><BookOpen size={14} /> Learn</> },
    { id: "visualize", label: <><Eye size={14} /> Visualize{ws.traceView && <span className="h-1.5 w-1.5 rounded-full bg-accent" />}</> },
    { id: "notes", label: <><NotebookPen size={14} /> Notes</> },
  ];

  const left = (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-elev">
      <div className="flex shrink-0 items-center gap-1 overflow-x-auto border-b border-line px-2 py-1.5">
        <Tabs tabs={tabs} value={ws.leftTab} onChange={ws.setLeftTab} size="sm" />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {ws.leftTab === "description" && <DescriptionTab problem={problem} />}
        {ws.leftTab === "learn" && <LearnTab problem={problem} />}
        {ws.leftTab === "visualize" && <VisualizeTab problem={problem} />}
        {ws.leftTab === "notes" && <NotesTab problem={problem} />}
      </div>
    </div>
  );

  const right = (
    <SplitPane
      id="ws-editor-console"
      direction="vertical"
      initial={0.6}
      min={0.25}
      max={0.85}
      first={
        <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-elev">
          <div className="flex shrink-0 items-center gap-2 border-b border-line px-3 py-1.5 text-xs text-muted">
            <span className="font-mono font-semibold text-fg">Python 3</span>
            <span className="text-faint">· runs in your browser</span>
            <div className="ml-auto flex items-center gap-0.5">
              <IconButton label="Reset to starter code" onClick={() => confirm("Reset your code to the starter template?") && ws.resetCode()}>
                <RotateCcw size={14} />
              </IconButton>
              <div className="relative">
                <IconButton label="Editor settings" onClick={() => setShowSettings((s) => !s)}>
                  <Settings2 size={14} />
                </IconButton>
                {showSettings && (
                  <div className="anim-fade-up absolute right-0 z-30 mt-1 w-56 space-y-3 rounded-xl border border-line-strong bg-elev p-3 text-[13px] shadow-panel" onMouseLeave={() => setShowSettings(false)}>
                    <label className="flex items-center justify-between">
                      Font size
                      <select value={fontSize} onChange={(e) => setSettings({ fontSize: Number(e.target.value) })} className="rounded-md border border-line bg-elev-2 px-1.5 py-0.5">
                        {[12, 13, 14, 15, 16, 18].map((s) => <option key={s}>{s}</option>)}
                      </select>
                    </label>
                    <label className="flex items-center justify-between">
                      Vim mode
                      <input type="checkbox" checked={vim} onChange={(e) => setSettings({ vim: e.target.checked })} className="accent-[var(--accent)]" />
                    </label>
                  </div>
                )}
              </div>
            </div>
          </div>
          <CodeEditor
            ref={editor}
            value={ws.code}
            onChange={ws.setCode}
            onRun={() => void ws.run()}
            onSubmit={() => void ws.submit()}
            onVisualize={() => void ws.visualize()}
            onFootnoteAction={ws.footnoteAction}
            marks={marks}
            fontSize={fontSize}
            vimMode={vim}
            className="min-h-0 flex-1 overflow-hidden"
          />
        </div>
      }
      second={<ConsolePanel problem={problem} />}
    />
  );

  return (
    <div className="flex h-[calc(100dvh-52px)] flex-col gap-2 p-2">
      <header className="flex shrink-0 flex-wrap items-center gap-2 px-1">
        <Link to="/problems" className="flex h-8 items-center gap-1 rounded-lg px-2 text-[13px] text-muted hover:bg-hover hover:text-fg">
          <List size={15} /> <span className="hidden sm:inline">Problems</span>
        </Link>
        <div className="flex items-center">
          <IconButton label="Previous problem" disabled={!prev} onClick={() => prev && navigate(`/problems/${prev.id}`)}>
            <ChevronLeft size={16} />
          </IconButton>
          <IconButton label="Next problem" disabled={!next} onClick={() => next && navigate(`/problems/${next.id}`)}>
            <ChevronRight size={16} />
          </IconButton>
        </div>
        <StatusIcon status={status} />
        <h1 className="truncate font-display text-[17px] font-bold">
          <span className="mr-1 font-mono text-sm text-faint">{problem.number}.</span>
          {problem.title}
        </h1>
        <DifficultyBadge value={problem.difficulty} />
        <div className="ml-auto flex items-center gap-1.5">
          <Timer key={problem.id} />
          <Button size="md" variant="secondary" onClick={() => void ws.visualize()} disabled={!!ws.busy} title={`Visualize your code (${modKey()} .)`}>
            {ws.busy === "trace" ? <Spinner /> : <Eye size={15} />} <span className="hidden md:inline">Visualize</span>
          </Button>
          <Button size="md" variant="secondary" onClick={() => void ws.run()} disabled={!!ws.busy} title={`Run examples (${modKey()} Enter)`}>
            {ws.busy === "run" ? <Spinner /> : <Play size={15} />} Run
            <Kbd className="hidden xl:inline-flex">{modKey()}↵</Kbd>
          </Button>
          <Button size="md" variant="primary" onClick={() => void ws.submit()} disabled={!!ws.busy} title={`Submit (${modKey()} Shift Enter)`}>
            {ws.busy === "submit" ? <Spinner /> : <Send size={14} />} Submit
          </Button>
        </div>
      </header>
      {desktop ? (
        <div className="flex min-h-0 flex-1">
          <SplitPane id="ws-main" initial={0.46} min={0.28} max={0.72} first={left} second={right} className="flex-1" />
        </div>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col gap-2">
          <Tabs
            tabs={[{ id: "problem", label: "Problem" }, { id: "code", label: "Code" }]}
            value={mobileView}
            onChange={(v) => setMobileView(v as "problem" | "code")}
            size="sm"
          />
          {/* both stay mounted so the editor keeps its state; only one is shown */}
          <div className={cn("min-h-0 flex-1", mobileView !== "problem" && "hidden")}>{left}</div>
          <div className={cn("min-h-0 flex-1", mobileView !== "code" && "hidden")}>{right}</div>
        </div>
      )}
    </div>
  );
}
