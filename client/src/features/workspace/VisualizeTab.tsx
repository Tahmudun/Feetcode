import { useCallback, useEffect, useMemo, useState } from "react";
import { Code2, Eye, EyeOff, GitCompareArrows, Sparkles } from "lucide-react";
import type { ProblemDetail } from "@/content/types";
import { deepEqual, lit } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Button, Empty, Spinner, Tabs } from "@/ui/primitives";
import { Player } from "@/viz/Player";
import type { Scene } from "@/viz/scene";
import { inlineValues } from "@/viz/inline";
import { hasPoint } from "./findings";
import { useWorkspace } from "./store";

export function VisualizeTab({ problem }: { problem: ProblemDetail }) {
  const { traceView, traceSide, setTraceSide, setStepMarks, visualize, busy, activeCase } = useWorkspace();
  const params = useMemo(() => problem.signature.params.map((p) => p.name), [problem]);
  const [inlineCode, setInlineCode] = useState(() => typeof window !== "undefined" && window.innerWidth < 1024);
  const [revealRef, setRevealRef] = useState(false);

  const onStep = useCallback(
    (scene: Scene) => {
      if (!traceView) return;
      setStepMarks({
        line: scene.line,
        next: scene.next,
        errorLine: traceView.trace.error?.line ?? undefined,
        values: inlineValues(traceView.trace, scene.index),
      });
    },
    [setStepMarks, traceView],
  );
  useEffect(() => () => setStepMarks({}), [setStepMarks]);

  if (!traceView) {
    return (
      <Empty icon={<Eye size={30} />} title="See your code run">
        <p className="mb-4">
          Feetcode traces <b className="text-fg">your</b> code, not a reference answer: every variable, pointer and comparison, one
          step at a time, with live values in the editor and the reference's run one click away.
        </p>
        <Button variant="primary" onClick={() => void visualize(activeCase)} disabled={!!busy}>
          {busy === "trace" ? <Spinner /> : <Eye size={14} />} Trace Case {activeCase + 1}
        </Button>
      </Empty>
    );
  }

  const { trace, label, args, expected, divergence } = traceView;
  const point = hasPoint(divergence) ? divergence : null;
  const side = point ? traceSide : "yours";
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
          title="The editor follows along with live values; show the code here too"
        >
          <Code2 size={12} /> Code here
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-[12px]">
        {verdict === "ok" && <span className="rounded-md bg-ref-soft px-2 py-0.5 font-semibold text-ref">✓ returns {lit(got, 60)}, correct</span>}
        {verdict === "wrong" && (
          <span className="rounded-md bg-warn-soft px-2 py-0.5 font-semibold text-warn">✗ returns {lit(got, 50)}, expected {lit(expected, 50)}</span>
        )}
        {verdict === "error" && trace.error && (
          <span className="rounded-md bg-warn-soft px-2 py-0.5 font-semibold text-warn">
            {trace.error.type}: {trace.error.message}{trace.error.line ? ` (line ${trace.error.line})` : ""}
          </span>
        )}
        {trace.truncated && <span className="rounded-md bg-accent-soft px-2 py-0.5 text-accent">Stopped after {trace.steps.length} steps - try a smaller input.</span>}
        {divergence?.kind === "agree" && (
          <span className="rounded-md bg-ref-soft px-2 py-0.5 text-ref">Step for step, your run agrees with the reference on {divergence.shared.join(", ")}.</span>
        )}
      </div>

      {point && (
        <div className="flex flex-wrap items-center gap-2">
          <Tabs
            size="sm"
            value={side}
            onChange={(v) => setTraceSide(v as "yours" | "reference")}
            tabs={[
              { id: "yours", label: "Your run" },
              { id: "reference", label: <><GitCompareArrows size={13} /> Reference run</> },
            ]}
          />
          <span className="text-[12px] text-muted">
            First disagreement at step {point.step + 1}, line {point.line}
            {point.var ? <>: your <code className="text-accent">{point.var}</code> = {point.yours}, reference = <span className="text-ref">{point.ref}</span></> : null}
          </span>
        </div>
      )}

      {side === "yours" && trace.steps.length > 0 && (
        <Player
          key={`yours:${label}:${trace.steps.length}:${trace.code.length}:${String(traceView.startAt)}`}
          trace={trace}
          lens={problem.lens}
          params={params}
          mode="debug"
          showCode={inlineCode}
          problemId={problem.id}
          initialIndex={traceView.startAt ?? 0}
          onStep={onStep}
          marker={point ? { step: point.step, label: "diverges", var: point.var, ghost: point.ref, ghostLabel: "reference" } : null}
        />
      )}

      {side === "reference" && point && (
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2 rounded-lg border border-ref/30 bg-ref-soft px-3 py-2 text-[12.5px] text-fg">
            <span>
              The reference solution on the same input, starting where yours diverges.
              {revealRef ? " Its code is shown below." : " Its code stays hidden: compare what it does, not how."}
            </span>
            <button
              onClick={() => setRevealRef((r) => !r)}
              className="ml-auto flex items-center gap-1 rounded-md px-2 py-1 text-[11.5px] font-semibold text-ref hover:bg-hover"
            >
              {revealRef ? <><EyeOff size={12} /> Hide code</> : <><Eye size={12} /> Reveal code (spoiler)</>}
            </button>
          </div>
          <Player
            key={`ref:${point.solution}:${revealRef}`}
            trace={point.trace}
            lens={problem.lens}
            params={params}
            mode="debug"
            showCode={revealRef}
            hideNarration={!revealRef}
            footnotes={revealRef ? undefined : []}
            initialIndex={point.refStep ?? 0}
            marker={point.refStep !== null ? { step: point.refStep, label: "yours diverges", var: point.var, ghost: point.yours, ghostLabel: "yours" } : null}
          />
        </div>
      )}

      {side === "yours" && trace.steps.length === 0 && <div className="text-[13px] text-muted">Nothing ran - is the method defined?</div>}
    </div>
  );
}
