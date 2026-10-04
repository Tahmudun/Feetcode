import { cn } from "@/lib/utils";
import type { ArrayPanel, CellView } from "../scene";
import { BarsView } from "./BarsView";

export const TONE_VARS = ["var(--accent)", "var(--violet)", "var(--sky)", "var(--teal)", "var(--rose)"];

export function Cell({ cell, size = "md", className }: { cell: CellView; size?: "sm" | "md"; className?: string }) {
  return (
    <div
      className={cn(
        `st-${cell.state}`,
        "flex items-center justify-center rounded-lg border font-mono transition-[background,border-color,color,transform] duration-200",
        size === "md" ? "h-10 min-w-10 px-1.5 text-[13px]" : "h-7 min-w-7 px-1 text-[11px]",
        cell.state === "new" && "anim-pop",
        (cell.state === "active" || cell.state === "compare" || cell.state === "match") && "-translate-y-0.5",
        className,
      )}
      style={{ background: "var(--st-bg)", borderColor: "var(--st-border)", color: "var(--st-fg)" }}
    >
      <span className="max-w-28 truncate">{cell.text === "" ? " " : cell.text}</span>
    </div>
  );
}

export function PanelLabel({ names, children }: { names: string[]; children?: React.ReactNode }) {
  return (
    <div className="mb-2 flex items-center gap-2 font-mono text-[12px]">
      <span className="font-semibold text-fg">{names.join(" = ")}</span>
      {children}
    </div>
  );
}

export function Probe({ probe }: { probe?: { text: string; hit: boolean } }) {
  if (!probe) return null;
  return (
    <span
      className={cn(
        "anim-pop inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-mono text-[11px]",
        probe.hit ? "border-teal/50 bg-teal-soft text-teal" : "border-rose/50 bg-rose-soft text-rose",
      )}
    >
      {probe.text} {probe.hit ? "✓ found" : "✗ not found"}
    </span>
  );
}

export function ArrayView({ panel }: { panel: ArrayPanel }) {
  if (panel.view === "bars") return <BarsView panel={panel} />;
  const byIndex = new Map<number, typeof panel.pointers>();
  for (const p of panel.pointers) byIndex.set(p.index, [...(byIndex.get(p.index) ?? []), p]);
  const marked = new Set(panel.marked?.indices ?? []);
  const slots = panel.cells.length + (panel.pointers.some((p) => p.index === panel.cells.length) || panel.oob !== undefined ? 1 : 0);
  const longest = panel.cells.reduce((m, c) => Math.max(m, c.text.length), 1);
  const cw = Math.min(110, Math.max(40, longest * 8 + 16));
  return (
    <div>
      <PanelLabel names={panel.names}>
        <span className="text-faint">{panel.container === "str" ? `str · ${panel.cells.length}` : `${panel.container} · ${panel.truncated ?? panel.cells.length}`}</span>
        <Probe probe={panel.probe} />
        {panel.marked && <span className="text-[11px] text-violet">● in {panel.marked.by}</span>}
      </PanelLabel>
      <div className="overflow-x-auto pb-1">
        <div className="relative inline-flex items-end gap-1.5 pt-7" style={{ ["--cw" as string]: `${cw}px` }}>
          {panel.window && (
            <div
              className="pointer-events-none absolute bottom-[18px] top-6 rounded-xl border border-sky/60 bg-sky-soft transition-all duration-300"
              style={{ left: `calc(${panel.window[0]} * (var(--cw) + 6px) - 4px)`, width: `calc(${panel.window[1] - panel.window[0] + 1} * (var(--cw) + 6px) + 2px)` }}
            />
          )}
          {Array.from({ length: slots }, (_, i) => {
            const cell = panel.cells[i];
            const ptrs = byIndex.get(i) ?? [];
            return (
              <div key={i} className="relative flex flex-col items-center gap-1">
                <div className="absolute -top-7 flex flex-col-reverse items-center">
                  {ptrs.map((p) => (
                    <span key={p.name} className="font-mono text-[10px] font-bold leading-tight transition-all" style={{ color: TONE_VARS[p.tone] }}>
                      {p.name}
                      <span className="block text-center leading-[6px]">▾</span>
                    </span>
                  ))}
                </div>
                {cell ? (
                  <Cell cell={cell} className="w-[var(--cw)]" />
                ) : i === panel.oob ? (
                  <div className="st-oob flex h-10 w-[var(--cw)] items-center justify-center rounded-lg border border-dashed text-[10px] font-bold text-rose" style={{ borderColor: "var(--rose)" }}>
                    OOB
                  </div>
                ) : (
                  <div className="flex h-10 w-[var(--cw)] items-center justify-center rounded-lg border border-dashed border-line text-[10px] text-faint">end</div>
                )}
                <span className={cn("font-mono text-[10px]", marked.has(i) ? "font-bold text-violet" : "text-faint")}>
                  {marked.has(i) ? "●" : ""}
                  {i}
                </span>
              </div>
            );
          })}
          {panel.ghost && (
            <div className="relative flex flex-col items-center gap-1 opacity-60">
              <div className="st-removed flex h-10 min-w-10 items-center justify-center rounded-lg border border-dashed px-1.5 font-mono text-[13px] line-through" style={{ borderColor: "var(--rose)", color: "var(--text-faint)" }}>
                {panel.ghost.text}
              </div>
              <span className="font-mono text-[10px] text-rose">popped</span>
            </div>
          )}
        </div>
      </div>
      {panel.oob !== undefined && (
        <div className="mt-1 text-[11px] text-rose">Index {panel.oob} is outside {panel.names[0]} (valid: 0…{panel.cells.length - 1}).</div>
      )}
    </div>
  );
}
