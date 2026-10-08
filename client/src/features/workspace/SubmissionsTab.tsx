import type { ProblemDetail } from "@/content/types";
import { cn, relativeTime } from "@/lib/utils";
import { loadSubmissions, useWorkspace } from "./store";
import { VERDICT } from "./verdicts";

/** Every submission of this problem, newest first, with the code to load back. */
export function SubmissionsList({ problem }: { problem: ProblemDetail }) {
  const subs = loadSubmissions(problem.id);
  const setCode = useWorkspace((s) => s.setCode);
  if (!subs.length) {
    return (
      <p className="text-xs text-faint">
        Nothing yet. Submitting runs the hidden tests, the fuzzer and the complexity profiler; each attempt is kept here, in this browser.
      </p>
    );
  }
  return (
    <div className="divide-y divide-line rounded-xl border border-line">
      {subs.map((s, i) => {
        const v = VERDICT[s.verdict];
        return (
          <div key={i} className="flex items-center gap-3 px-3.5 py-2.5">
            <span className={cn("w-32 text-[13px] font-semibold", v.text)}>{v.label}</span>
            <span className="font-mono text-xs text-muted">{s.passed !== undefined ? `${s.passed}/${s.total}` : ""}</span>
            {s.time && <span className="rounded-md bg-elev-2 px-1.5 py-0.5 font-mono text-[11px] text-muted">{s.time}</span>}
            <span className="ml-auto text-xs text-faint">{relativeTime(s.ts)}</span>
            <button onClick={() => setCode(s.code)} className="rounded-md px-2 py-1 text-xs text-muted hover:bg-hover hover:text-fg">
              Load code
            </button>
          </div>
        );
      })}
    </div>
  );
}
