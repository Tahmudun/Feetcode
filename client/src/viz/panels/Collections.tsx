import { cn } from "@/lib/utils";
import type { GridPanel, MapPanel, ObjectPanel, Panel, SetPanel, StackPanel } from "../scene";
import { Cell, PanelLabel, Probe } from "./ArrayView";

export function StackView({ panel, all }: { panel: StackPanel; all: Panel[] }) {
  const target = panel.indexInto ? all.find((p) => p.kind === "array" && p.names.includes(panel.indexInto!)) : undefined;
  const valueAt = (text: string) => {
    if (!target || target.kind !== "array") return null;
    const i = Number(text.replace(/^\(/, "").split(",")[0]);
    return Number.isInteger(i) ? target.cells[i]?.text : null;
  };
  return (
    <div>
      <PanelLabel names={panel.names}>
        <span className="text-faint">{panel.container === "deque" ? "deque" : "stack"} · {panel.items.length}</span>
        <Probe probe={panel.probe} />
      </PanelLabel>
      <div className="flex flex-col-reverse items-start gap-1">
        {panel.items.length === 0 && !panel.ghost && <div className="rounded-lg border border-dashed border-line px-3 py-2 font-mono text-[11px] text-faint">empty</div>}
        {panel.items.map((c, i) => (
          <div key={i} className="flex items-center gap-2">
            <Cell cell={c} className="min-w-16" />
            {valueAt(c.text) !== null && <span className="font-mono text-[11px] text-faint">→ {panel.indexInto}[{c.text.replace(/^\(/, "").split(",")[0]}] = {valueAt(c.text)}</span>}
            {i === panel.items.length - 1 && <span className="font-mono text-[10px] font-semibold text-accent">← top</span>}
          </div>
        ))}
        {panel.ghost && (
          <div className="flex items-center gap-2 opacity-60">
            <div className="flex h-10 min-w-16 items-center justify-center rounded-lg border border-dashed border-warn px-2 font-mono text-[13px] text-faint line-through">
              {panel.ghost.text}
            </div>
            <span className="font-mono text-[10px] text-warn">popped</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function MapView({ panel }: { panel: MapPanel }) {
  return (
    <div>
      <PanelLabel names={panel.names}>
        <span className="text-faint">{panel.subtype ?? "dict"} · {panel.truncated ?? panel.entries.length}</span>
        <Probe probe={panel.probe} />
      </PanelLabel>
      {panel.entries.length === 0 && !panel.ghost ? (
        <div className="inline-block rounded-lg border border-dashed border-line px-3 py-2 font-mono text-[11px] text-faint">{"{ }"} empty</div>
      ) : (
        <div className="inline-flex flex-col gap-1 font-mono text-[12px]">
          {panel.entries.map((e) => (
            <div
              key={e.key}
              className={cn(`st-${e.state}`, "flex items-stretch overflow-hidden rounded-lg border transition-colors", e.state === "new" && "anim-pop")}
              style={{ borderColor: "var(--st-border)", background: "var(--st-bg)" }}
            >
              <span className="px-2.5 py-1 font-semibold" style={{ color: "var(--st-fg)" }}>{e.key}</span>
              <span className="flex items-center border-l px-1.5 text-faint" style={{ borderColor: "var(--st-border)" }}>→</span>
              <span className="max-w-72 truncate px-2.5 py-1 text-muted">{e.value}</span>
            </div>
          ))}
          {panel.ghost && <div className="px-2.5 py-1 text-faint line-through decoration-warn">{panel.ghost.key} (deleted)</div>}
        </div>
      )}
    </div>
  );
}

export function SetView({ panel }: { panel: SetPanel }) {
  return (
    <div>
      <PanelLabel names={panel.names}>
        <span className="text-faint">set · {panel.items.length}</span>
        <Probe probe={panel.probe} />
      </PanelLabel>
      <div className="flex flex-wrap gap-1.5">
        {panel.items.length === 0 && <span className="font-mono text-[11px] text-faint">set() empty</span>}
        {panel.items.map((c) => (
          <Cell key={c.text} cell={c} size="sm" className="rounded-full px-2" />
        ))}
      </div>
    </div>
  );
}

export function GridView({ panel }: { panel: GridPanel }) {
  const cols = panel.rows[0]?.length ?? 0;
  return (
    <div>
      <PanelLabel names={panel.names}>
        <span className="text-faint">{panel.rows.length} × {cols}</span>
      </PanelLabel>
      <div className="inline-grid gap-0 rounded-lg border-2 border-line-strong" style={{ gridTemplateColumns: `repeat(${cols}, 26px)` }}>
        {panel.rows.flatMap((row, r) =>
          row.map((c, ci) => (
            <div
              key={`${r}:${ci}`}
              className={cn(
                `st-${c.state}`,
                "flex h-[26px] items-center justify-center border-line font-mono text-[12px] transition-colors",
                panel.box && ci % panel.box === panel.box - 1 && ci !== cols - 1 ? "border-r-2 border-r-line-strong" : "border-r",
                panel.box && r % panel.box === panel.box - 1 && r !== panel.rows.length - 1 ? "border-b-2 border-b-line-strong" : "border-b",
              )}
              style={{ background: c.state === "idle" ? "transparent" : "var(--st-bg)", color: c.text === "." ? "var(--text-faint)" : "var(--st-fg)" }}
            >
              {c.text === "." ? "·" : c.text}
            </div>
          )),
        )}
      </div>
    </div>
  );
}

export function ObjectView({ panel }: { panel: ObjectPanel }) {
  return (
    <div>
      <PanelLabel names={panel.names}>
        <span className="text-faint">{panel.cls}</span>
      </PanelLabel>
      <div className="inline-grid grid-cols-[auto_auto] gap-x-3 gap-y-0.5 rounded-xl border border-line px-3 py-2 font-mono text-[12px]">
        {panel.fields.map((f) => (
          <div key={f.name} className="contents">
            <span className="text-muted">{f.name}</span>
            <span className="text-fg">{f.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
