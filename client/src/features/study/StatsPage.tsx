import { useMemo, useRef } from "react";
import { Database, Download, Upload } from "lucide-react";
import { patterns, problems } from "@/content";
import { useStudy, exportNdjson } from "@/store/events";
import { patternMastery, type StudyEvent } from "@/store/progress";
import { Button, Panel } from "@/ui/primitives";
import { Heatmap } from "@/ui/Heatmap";
import { CodePane } from "@/viz/CodePane";

const SQL = `-- Your study log is plain NDJSON. Load it in DuckDB:
SELECT p AS problem,
       count(*) FILTER (WHERE t = 'submit')                  AS submits,
       count(*) FILTER (WHERE t = 'submit' AND v = 'accepted') AS accepted,
       min(to_timestamp(ts / 1000)) FILTER (WHERE v = 'accepted') AS first_solved
FROM read_json_auto('feetcode-events.ndjson')
GROUP BY p
ORDER BY submits DESC;`;

export default function StatsPage() {
  const { events, progress, importEvents } = useStudy();
  const fileRef = useRef<HTMLInputElement>(null);
  const stats = useMemo(() => {
    const submits = events.filter((e): e is Extract<StudyEvent, { t: "submit" }> => e.t === "submit");
    const verdicts: Record<string, number> = {};
    for (const s of submits) verdicts[s.v] = (verdicts[s.v] ?? 0) + 1;
    const predictions = events.filter((e): e is Extract<StudyEvent, { t: "predict" }> => e.t === "predict");
    return {
      submits: submits.length,
      accepted: verdicts.accepted ?? 0,
      verdicts,
      runs: events.filter((e) => e.t === "run").length,
      lessons: events.filter((e) => e.t === "lesson").length,
      reviews: events.filter((e) => e.t === "review").length,
      predictions: predictions.length,
      predictRight: predictions.filter((p) => p.ok).length,
    };
  }, [events]);

  const download = () => {
    const blob = new Blob([exportNdjson()], { type: "application/x-ndjson" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "feetcode-events.ndjson";
    a.click();
    URL.revokeObjectURL(a.href);
  };
  const upload = async (file: File) => {
    const lines = (await file.text()).split("\n").filter(Boolean);
    const parsed = lines.map((l) => JSON.parse(l) as StudyEvent).filter((e) => e && typeof e.ts === "number" && typeof e.t === "string");
    importEvents(parsed);
  };

  const kpis = [
    { label: "Solved", value: `${progress.solvedCount}/${problems.length}` },
    { label: "Acceptance", value: stats.submits ? `${Math.round((stats.accepted / stats.submits) * 100)}%` : "-" },
    { label: "Streak", value: `${progress.streak}d`, sub: `best ${progress.longestStreak}d` },
    { label: "Lessons", value: String(stats.lessons) },
    { label: "Predictions", value: stats.predictions ? `${Math.round((stats.predictRight / stats.predictions) * 100)}%` : "-", sub: `${stats.predictions} made` },
    { label: "Reviews", value: String(stats.reviews) },
  ];
  const verdictColors: Record<string, string> = { accepted: "var(--ref)", wrong: "var(--warn)", error: "var(--note)", tle: "var(--accent)", compile: "var(--text-faint)" };

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 pb-24 pt-8 sm:px-6">
      <div>
        <h1 className="font-display text-3xl font-extrabold tracking-tight">Your stats</h1>
        <p className="mt-1 text-muted">Everything here is derived from one append-only event log stored in this browser.</p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {kpis.map((k) => (
          <Panel key={k.label} className="p-4">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-faint">{k.label}</div>
            <div className="mt-1 font-display text-2xl font-bold">{k.value}</div>
            {k.sub && <div className="text-[11px] text-faint">{k.sub}</div>}
          </Panel>
        ))}
      </div>
      <Panel className="p-5">
        <h2 className="mb-3 text-sm font-semibold">Activity</h2>
        <div className="overflow-x-auto"><Heatmap activity={progress.activity} weeks={26} /></div>
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel className="p-5">
          <h2 className="mb-3 text-sm font-semibold">Pattern mastery</h2>
          <div className="space-y-3">
            {patterns.map((p) => {
              const m = patternMastery(progress, problems, p.id);
              return (
                <div key={p.id}>
                  <div className="mb-1 flex justify-between text-[13px]"><span>{p.name}</span><span className="font-mono text-xs text-muted">{m.solved}/{m.total} · {Math.round(m.mastery * 100)}%</span></div>
                  <div className="h-2 overflow-hidden rounded-full bg-elev-2"><div className="h-full rounded-full bg-ref transition-all" style={{ width: `${m.mastery * 100}%` }} /></div>
                </div>
              );
            })}
          </div>
        </Panel>
        <Panel className="p-5">
          <h2 className="mb-3 text-sm font-semibold">Submission outcomes</h2>
          {stats.submits === 0 ? (
            <p className="text-[13px] text-faint">No submissions yet.</p>
          ) : (
            <>
              <div className="flex h-3 overflow-hidden rounded-full">
                {Object.entries(stats.verdicts).map(([v, n]) => (
                  <div key={v} style={{ width: `${(n / stats.submits) * 100}%`, background: verdictColors[v] }} title={`${v}: ${n}`} />
                ))}
              </div>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
                {Object.entries(stats.verdicts).map(([v, n]) => (
                  <span key={v} className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full" style={{ background: verdictColors[v] }} /> {v} {n}</span>
                ))}
              </div>
            </>
          )}
          <p className="mt-4 text-xs text-faint">{stats.runs} runs · {events.length} events logged</p>
        </Panel>
      </div>
      <Panel className="p-5">
        <h2 className="mb-1 flex items-center gap-2 text-sm font-semibold"><Database size={15} className="text-sky" /> Your data</h2>
        <p className="mb-4 text-[13px] text-muted">
          Progress is event-sourced: streaks, mastery and the review schedule are all recomputed from this log. Export it, analyse it, or move it to another browser.
        </p>
        <div className="mb-4 flex flex-wrap gap-2">
          <Button onClick={download} disabled={!events.length}><Download size={14} /> Export NDJSON</Button>
          <Button onClick={() => fileRef.current?.click()}><Upload size={14} /> Import</Button>
          <input ref={fileRef} type="file" accept=".ndjson,.jsonl,.json,application/x-ndjson" className="hidden" onChange={(e) => e.target.files?.[0] && void upload(e.target.files[0])} />
        </div>
        <CodePane code={SQL} />
      </Panel>
    </div>
  );
}
