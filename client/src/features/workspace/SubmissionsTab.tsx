import type { ProblemDetail } from "@/content/types";
import { cn, relativeTime } from "@/lib/utils";
import { Empty } from "@/ui/primitives";
import { History } from "lucide-react";
import { loadSubmissions, useWorkspace } from "./store";
import { VERDICT } from "./verdicts";

export function SubmissionsTab({ problem }: { problem: ProblemDetail }) {
  const subs = loadSubmissions(problem.id);
  const setCode = useWorkspace((s) => s.setCode);
  if (!subs.length) {
    return (
      <Empty icon={<History size={28} />} title="No submissions yet">
        Submit to run the hidden test suite, the fuzzer and the complexity profiler. Your history stays in this browser.
      </Empty>
    );
  }
  return (
    <div className="divide-y divide-line">
      {subs.map((s, i) => {
        const v = VERDICT[s.verdict];
        return (
          <div key={i} className="flex items-center gap-3 px-5 py-3">
            <span className={cn("w-36 text-[13px] font-semibold", v.text)}>{v.label}</span>
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
