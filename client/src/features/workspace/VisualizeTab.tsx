import { useCallback, useEffect, useMemo, useState } from "react";
import { Code2, Eye, Sparkles } from "lucide-react";
import type { ProblemDetail } from "@/content/types";
import { deepEqual, lit } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Button, Empty, Spinner } from "@/ui/primitives";
import { Player } from "@/viz/Player";
import type { Scene } from "@/viz/scene";
import { useWorkspace } from "./store";

export function VisualizeTab({ problem }: { problem: ProblemDetail }) {
  const { traceView, setMarks, visualize, busy, activeCase } = useWorkspace();
  const params = useMemo(() => problem.signature.params.map((p) => p.name), [problem]);
  const [inlineCode, setInlineCode] = useState(() => typeof window !== "undefined" && window.innerWidth < 1024);

  const onStep = useCallback(
    (scene: Scene) => {
      setMarks({ line: scene.line, next: scene.next, errorLine: traceView?.trace.error?.line ?? undefined });
    },
    [setMarks, traceView],
  );
  useEffect(() => () => setMarks({}), [setMarks]);

  if (!traceView) {
    return (
      <Empty icon={<Eye size={30} />} title="See your code run">
        <p className="mb-4">
          Feetcode traces <b className="text-fg">your</b> code - not just a reference answer. Every variable, pointer, comparison and
          linked-list arrow, one step at a time, synced with the editor.
        </p>
        <Button variant="primary" onClick={() => void visualize(activeCase)} disabled={!!busy}>
          {busy === "trace" ? <Spinner /> : <Eye size={14} />} Visualize Case {activeCase + 1}
        </Button>
      </Empty>
    );
  }

  const { trace, label, args, expected } = traceView;
  const got = trace.output;
  const verdict = trace.error ? "error" : expected === undefined ? null : deepEqual(got, expected) ? "ok" : "wrong";
  return (
    <div className="space-y-3 px-4 py-4">
      <div className="flex flex-wrap items-center gap-2">
        <Sparkles size={15} className="text-accent" />
        <h2 className="text-[14px] font-semibold">{label}</h2>
        <span className="truncate font-mono text-[11.5px] text-faint">
          {Object.entries(args).map(([k, v]) => `${k}=${lit(v, 60)}`).join(", ")}
        </span>
        <button
          onClick={() => setInlineCode((v) => !v)}
          className={cn("ml-auto flex items-center gap-1 rounded-md px-2 py-1 text-[11px]", inlineCode ? "bg-accent-soft text-accent" : "text-muted hover:bg-hover")}
          title="The editor highlights the current line; show code here too"
        >
          <Code2 size={12} /> Code here
        </button>
      </div>
      {(verdict || trace.truncated) && (
        <div className="flex flex-wrap gap-2 text-[12px]">
          {verdict === "ok" && <span className="rounded-md bg-teal-soft px-2 py-0.5 font-semibold text-teal">✓ returns {lit(got, 60)} - correct</span>}
          {verdict === "wrong" && (
            <span className="rounded-md bg-rose-soft px-2 py-0.5 font-semibold text-rose">
              ✗ returns {lit(got, 50)}, expected {lit(expected, 50)}
            </span>
          )}
          {verdict === "error" && trace.error && (
            <span className="rounded-md bg-rose-soft px-2 py-0.5 font-semibold text-rose">
              {trace.error.type}: {trace.error.message}{trace.error.line ? ` (line ${trace.error.line})` : ""}
            </span>
          )}
          {trace.truncated && <span className="rounded-md bg-accent-soft px-2 py-0.5 text-accent">Stopped after {trace.steps.length} steps - try a smaller input.</span>}
        </div>
      )}
      {trace.steps.length > 0 ? (
        <Player
          key={`${label}:${trace.steps.length}:${trace.code.length}`}
          trace={trace}
          lens={problem.lens}
          params={params}
          mode="debug"
          showCode={inlineCode}
          problemId={problem.id}
          initialIndex={traceView.startAt ?? 0}
          onStep={onStep}
        />
      ) : (
        <div className="text-[13px] text-muted">Nothing ran - is the method defined?</div>
      )}
    </div>
  );
}
