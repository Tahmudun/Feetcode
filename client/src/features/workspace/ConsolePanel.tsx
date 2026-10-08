import { useState } from "react";
import { CircleAlert, Eye, Plus, Terminal, X } from "lucide-react";
import type { ProblemDetail } from "@/content/types";
import { lit } from "@/lib/format";
import { cn, compact } from "@/lib/utils";
import { Button, Spinner, Tabs } from "@/ui/primitives";
import { useWorkspace, type ConsoleTab } from "./store";
import { AnalysisView } from "./AnalysisView";
import { VERDICT } from "./verdicts";

export function ConsolePanel({ problem }: { problem: ProblemDetail }) {
  const ws = useWorkspace();
  const v = ws.runResult ? VERDICT[ws.runResult.verdict] : null;
  const sv = ws.submitResult ? VERDICT[ws.submitResult.verdict] : null;
  const tabs: { id: ConsoleTab; label: React.ReactNode }[] = [
    { id: "tests", label: "Testcases" },
    { id: "result", label: <>Result {v && <span className={cn("h-1.5 w-1.5 rounded-full", ws.runResult?.verdict === "accepted" ? "bg-ref" : "bg-warn")} />}</> },
    { id: "analysis", label: <>Submission {sv && <span className={cn("h-1.5 w-1.5 rounded-full", ws.submitResult?.verdict === "accepted" ? "bg-ref" : "bg-warn")} />}</> },
  ];
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-elev">
      <div className="flex shrink-0 items-center gap-2 border-b border-line px-2 py-1.5">
        <Terminal size={14} className="ml-1 text-faint" />
        <Tabs tabs={tabs} value={ws.consoleTab} onChange={ws.setConsoleTab} size="sm" />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {ws.error && (
          <div className="mb-3 flex items-start gap-2 rounded-xl border border-warn/40 bg-warn-soft px-3 py-2 text-[13px] text-warn">
            <CircleAlert size={15} className="mt-0.5 shrink-0" /> {ws.error}
          </div>
        )}
        {ws.consoleTab === "tests" && <TestcasesView problem={problem} />}
        {ws.consoleTab === "result" && <ResultView />}
        {ws.consoleTab === "analysis" && <AnalysisView problem={problem} />}
      </div>
    </div>
  );
}

function CaseChips({ statuses }: { statuses?: (boolean | null)[] }) {
  const { cases, activeCase, setActiveCase, addCase, removeCase } = useWorkspace();
  return (
    <div className="mb-3 flex flex-wrap items-center gap-1.5">
      {cases.map((c, i) => (
        <button
          key={i}
          onClick={() => setActiveCase(i)}
          className={cn(
            "group flex h-7 items-center gap-1.5 rounded-lg px-2.5 text-xs font-medium transition-colors",
            i === activeCase ? "bg-elev-2 text-fg shadow-[inset_0_0_0_1px_var(--border-strong)]" : "text-muted hover:bg-hover",
          )}
        >
          {statuses && statuses[i] !== undefined && statuses[i] !== null && (
            <span className={cn("h-1.5 w-1.5 rounded-full", statuses[i] ? "bg-ref" : "bg-warn")} />
          )}
          Case {i + 1}
          {c.custom && <span className="text-[10px] text-note">custom</span>}
          {c.custom && cases.length > 1 && (
            <X size={11} className="opacity-0 group-hover:opacity-70" onClick={(e) => { e.stopPropagation(); removeCase(i); }} />
          )}
        </button>
      ))}
      {!statuses && cases.length < 8 && (
        <button onClick={addCase} className="flex h-7 w-7 items-center justify-center rounded-lg text-muted hover:bg-hover hover:text-fg" aria-label="Add a custom test case">
          <Plus size={14} />
        </button>
      )}
    </div>
  );
}

function FieldEditor({ name, value, onCommit }: { name: string; value: unknown; onCommit: (v: unknown) => void }) {
  const [text, setText] = useState(() => JSON.stringify(value));
  const [bad, setBad] = useState(false);
  return (
    <label className="block">
      <span className="mb-1 block font-mono text-xs text-muted">{name} =</span>
      <input
        value={text}
        spellCheck={false}
        onChange={(e) => {
          setText(e.target.value);
          try {
            const parsed = JSON.parse(e.target.value);
            setBad(false);
            onCommit(parsed);
          } catch {
            setBad(true);
          }
        }}
        className={cn(
          "h-9 w-full rounded-lg border bg-inset px-3 font-mono text-[13px] text-fg outline-none transition-colors",
          bad ? "border-warn/60" : "border-line focus:border-accent/60",
        )}
      />
      {bad && <span className="mt-0.5 block text-[11px] text-warn">Not valid JSON yet - use double quotes for strings, null for None.</span>}
    </label>
  );
}

function TestcasesView({ problem }: { problem: ProblemDetail }) {
  const { cases, activeCase, updateCase, visualize, busy } = useWorkspace();
  const c = cases[activeCase];
  if (!c) return null;
  return (
    <div>
      <CaseChips />
      <div className="space-y-3" key={activeCase}>
        {problem.signature.inputs.map((name) => (
          <FieldEditor key={name} name={name} value={c.args[name]} onCommit={(v) => updateCase(activeCase, { ...c.args, [name]: v })} />
        ))}
      </div>
      <div className="mt-4 flex items-center gap-2">
        <Button size="sm" onClick={() => void visualize(activeCase)} disabled={!!busy}>
          {busy === "trace" ? <Spinner /> : <Eye size={13} />} Visualize this case
        </Button>
        <span className="text-[11px] text-faint">Custom cases get their expected output from the reference solution.</span>
      </div>
    </div>
  );
}

function ResultView() {
  const { runResult, busy, activeCase, cases, visualize } = useWorkspace();
  if (busy === "run") return <div className="flex items-center gap-2 text-[13px] text-muted"><Spinner className="text-accent" /> Running your code…</div>;
  if (!runResult) return <div className="text-[13px] text-faint">Run your code to see results here.</div>;
  const v = VERDICT[runResult.verdict];
  if (runResult.verdict === "compile") {
    return (
      <div>
        <div className={cn("mb-2 text-lg font-bold", v.text)}>{v.label}</div>
        <pre className="rounded-xl border border-warn/40 bg-warn-soft p-3 font-mono text-[12.5px] text-warn">
          Line {runResult.error?.line}: {runResult.error?.message}
        </pre>
      </div>
    );
  }
  const r = runResult.cases[activeCase] ?? runResult.cases[0];
  const totalOps = runResult.cases.reduce((s, c) => s + c.ops, 0);
  return (
    <div className="anim-fade-up">
      <div className="mb-3 flex flex-wrap items-baseline gap-3">
        <span className={cn("text-lg font-bold", v.text)}>{v.label}</span>
        <span className="text-xs text-faint">
          {runResult.cases.filter((c) => c.pass).length}/{runResult.cases.length} cases · {compact(totalOps)} ops
        </span>
      </div>
      <CaseChips statuses={runResult.cases.map((c) => c.pass)} />
      {r && (
        <div className="space-y-2.5">
          <Block label="Input">
            {Object.entries(cases[activeCase]?.args ?? {}).map(([k, val]) => (
              <div key={k}><span className="text-muted">{k} = </span>{lit(val)}</div>
            ))}
          </Block>
          {r.error ? (
            <Block label={r.error.type} tone="warn">
              {r.error.message}
              {r.error.line && <div className="mt-1 text-[11px] opacity-80">at line {r.error.line}</div>}
            </Block>
          ) : (
            <Block label="Output" tone={r.pass ? "ref" : "warn"}>{lit(r.output)}</Block>
          )}
          <Block label="Expected">{r.expected === null || r.expected === undefined ? <span className="text-faint">(computed by the reference solution)</span> : lit(r.expected)}</Block>
          {r.stdout && <Block label="Stdout"><pre className="whitespace-pre-wrap">{r.stdout}</pre></Block>}
          {r.invalid && <div className="text-[11px] text-accent">This input violates the problem's constraints, so results may be meaningless.</div>}
          <div className="flex items-center gap-3 pt-1">
            <Button size="sm" onClick={() => void visualize(activeCase)}><Eye size={13} /> Visualize this run</Button>
            <span className="font-mono text-[11px] text-faint">{r.ops.toLocaleString()} ops · {r.ms} ms</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function Block({ label, tone, children }: { label: string; tone?: "ref" | "warn"; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-faint">{label}</div>
      <div
        className={cn(
          "overflow-x-auto rounded-lg border px-3 py-2 font-mono text-[12.5px]",
          tone === "ref" ? "border-ref/30 bg-ref-soft text-ref" : tone === "warn" ? "border-warn/30 bg-warn-soft text-warn" : "border-line bg-inset text-fg",
        )}
      >
        {children}
      </div>
    </div>
  );
}
