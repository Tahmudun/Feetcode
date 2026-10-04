import { useEffect, useMemo, useState } from "react";
import { loadLessons, loadProblem } from "@/content";
import type { Lessons, ProblemDetail } from "@/content/types";
import { Stage } from "@/viz/Player";
import { buildScene, makeContext } from "@/viz/scene";

/** The real visualizer, autoplaying the Trapping Rain Water lesson on a loop. */
export function HeroDemo() {
  const [data, setData] = useState<{ lessons: Lessons; problem: ProblemDetail } | null>(null);
  const [i, setI] = useState(0);
  const [reduceMotion] = useState(() => typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches);

  useEffect(() => {
    Promise.all([loadLessons("trapping-rain-water"), loadProblem("trapping-rain-water")]).then(([lessons, problem]) =>
      setData({ lessons, problem }),
    );
  }, []);

  const trace = data?.lessons.traces["two-pointers"];
  const ctx = useMemo(() => (trace && data ? makeContext(trace, data.problem.lens, ["height"]) : null), [trace, data]);
  const keySteps = useMemo(() => (trace ? trace.steps.map((s, k) => (s.t && !s.hide ? k : -1)).filter((k) => k >= 0) : []), [trace]);

  useEffect(() => {
    if (!keySteps.length || reduceMotion) return;
    const id = setInterval(() => setI((x) => (x + 1) % (keySteps.length + 4)), 1500);
    return () => clearInterval(id);
  }, [keySteps, reduceMotion]);

  if (!trace || !ctx) return <div className="skeleton h-72 rounded-2xl" />;
  const k = reduceMotion ? keySteps.length - 1 : Math.min(i, keySteps.length - 1);
  const scene = buildScene(trace, keySteps[k], ctx);
  return (
    <div className="relative overflow-hidden rounded-2xl border border-line bg-elev p-4 shadow-panel">
      <div className="mb-3 flex items-center gap-2">
        <span className="flex gap-1">
          <span className="h-2.5 w-2.5 rounded-full bg-rose/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-accent/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-teal/70" />
        </span>
        <span className="font-mono text-[11px] text-faint">trapping-rain-water · two pointers · step {k + 1}/{keySteps.length}</span>
      </div>
      <p className="mb-3 min-h-[44px] text-[13px] leading-snug text-fg/90">{scene.narration}</p>
      <div className="bg-grid -mx-1 rounded-xl p-2">
        <Stage scene={{ ...scene, panels: scene.panels.filter((p) => p.kind === "array") }} />
      </div>
    </div>
  );
}
