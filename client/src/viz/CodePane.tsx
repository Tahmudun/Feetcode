import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { tokenizeLine, TOKEN_CLASS } from "./highlight";

export interface CodePaneProps {
  code: string;
  line?: number;
  next?: number;
  branch?: 0 | 1;
  branchKind?: "if" | "while" | "for" | "other";
  errorLine?: number;
  footnotes?: { line: number; text: string }[];
  hotFootnote?: number | null;
  onFootnoteHover?: (i: number | null) => void;
  heat?: Record<number, number>;
  className?: string;
}

/** Read-only, syntax-highlighted code with the executing line, branch outcome and footnote markers. */
export function CodePane({ code, line, next, branch, branchKind, errorLine, footnotes = [], hotFootnote, onFootnoteHover, heat, className }: CodePaneProps) {
  const ref = useRef<HTMLDivElement>(null);
  const lines = code.replace(/\n$/, "").split("\n");
  useEffect(() => {
    const el = ref.current?.querySelector<HTMLElement>("[data-current='true']");
    el?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [line]);
  const maxHeat = heat ? Math.max(1, ...Object.values(heat)) : 1;
  return (
    <div ref={ref} className={cn("overflow-auto rounded-xl border border-line bg-inset py-2 font-mono text-[12.5px] leading-[1.75]", className)}>
      {lines.map((text, i) => {
        const ln = i + 1;
        const current = ln === line;
        const notes = footnotes.map((f, k) => ({ ...f, k })).filter((f) => f.line === ln);
        const hot = notes.some((n) => n.k === hotFootnote);
        const h = heat?.[ln] ? heat[ln] / maxHeat : 0;
        return (
          <div
            key={i}
            data-current={current}
            className={cn(
              "relative flex min-w-fit pr-4 transition-colors duration-150",
              current && "bg-accent-soft",
              ln === errorLine && "bg-rose-soft",
              hot && !current && "bg-violet-soft",
            )}
            style={h > 0 && !current ? { background: `color-mix(in oklab, var(--rose) ${Math.round(h * 26)}%, transparent)` } : undefined}
          >
            <span className={cn("absolute inset-y-0 left-0 w-[3px]", current ? "bg-accent" : ln === errorLine ? "bg-rose" : "bg-transparent")} />
            <span className={cn("w-10 shrink-0 select-none pr-3 text-right", current ? "text-accent" : "text-faint")}>{ln}</span>
            <span className="whitespace-pre">
              {tokenizeLine(text).map((t, k) => (
                <span key={k} className={TOKEN_CLASS[t.kind]}>
                  {t.text}
                </span>
              ))}
              {text === "" && " "}
              {notes.map((n) => (
                <sup
                  key={n.k}
                  onMouseEnter={() => onFootnoteHover?.(n.k)}
                  onMouseLeave={() => onFootnoteHover?.(null)}
                  className={cn(
                    "ml-1 cursor-help rounded px-1 align-super text-[10px] font-bold",
                    n.k === hotFootnote ? "bg-accent text-accent-ink" : "text-accent",
                  )}
                >
                  {n.k + 1}
                </sup>
              ))}
            </span>
            {current && branch !== undefined && branchKind !== "other" && (
              <span
                className={cn(
                  "anim-pop ml-3 self-center rounded px-1.5 text-[10px] font-bold",
                  branch ? "bg-teal-soft text-teal" : "bg-rose-soft text-rose",
                )}
              >
                {branchKind === "for" ? (branch ? "next item" : "done") : branch ? "True" : "False"}
              </span>
            )}
            {ln === next && !current && <span className="ml-3 self-center text-[10px] text-faint">← next</span>}
          </div>
        );
      })}
    </div>
  );
}
