import type { ArrayPanel } from "../scene";
import { PanelLabel, Probe, TONE_VARS } from "./ArrayView";

const FILL: Record<string, string> = {
  idle: "var(--bg-hover)",
  active: "var(--accent)",
  compare: "var(--rose)",
  match: "var(--teal)",
  changed: "var(--accent)",
  new: "var(--violet)",
  miss: "var(--bg-hover)",
  removed: "var(--bg-elev)",
  oob: "var(--rose)",
};

/**
 * Bars for numeric arrays (heights, prices, temperatures) plus overlays:
 * trapped water and the max_l / max_r levels, container rectangles, histogram rectangles.
 */
export function BarsView({ panel }: { panel: ArrayPanel }) {
  const values = panel.cells.map((c) => c.value ?? 0);
  const n = values.length;
  const ov = panel.overlay;
  const levelMax = ov?.kind === "water" ? Math.max(0, ...ov.levels.map((l) => l.value)) : 0;
  const maxV = Math.max(1, ...values, levelMax);
  const minV = Math.min(0, ...values);
  const slot = Math.max(22, Math.min(48, Math.floor(640 / Math.max(1, n))));
  const barW = slot - 6;
  const H = 168;
  const top = 18;
  const bottom = 46;
  const left = 8;
  const width = left * 2 + n * slot + (ov?.kind === "water" ? 110 : 20);
  const height = top + H + bottom;
  const y = (v: number) => top + H - ((v - minV) / (maxV - minV)) * H;
  const x = (i: number) => left + i * slot + 3;
  const base = y(0);
  const marked = new Set(panel.marked?.indices ?? []);
  const byIndex = new Map<number, typeof panel.pointers>();
  for (const p of panel.pointers) byIndex.set(p.index, [...(byIndex.get(p.index) ?? []), p]);

  return (
    <div>
      <PanelLabel names={panel.names}>
        <span className="text-faint">{panel.container} · {n}</span>
        <Probe probe={panel.probe} />
        {ov?.kind === "water" && (
          <span className="rounded-md bg-sky-soft px-1.5 py-0.5 text-[11px] font-semibold text-sky">
            water decided: {ov.decidedTotal}
          </span>
        )}
        {ov?.kind === "container" && (
          <span className="rounded-md bg-accent-soft px-1.5 py-0.5 text-[11px] font-semibold text-accent">
            area = {ov.r - ov.l} × {ov.height} = {ov.area}
          </span>
        )}
        {ov?.kind === "rect" && (
          <span className="rounded-md bg-rose-soft px-1.5 py-0.5 text-[11px] font-semibold text-rose">
            rectangle = {ov.height} × {ov.to - ov.from + 1} = {ov.area}
          </span>
        )}
      </PanelLabel>
      <div className="overflow-x-auto">
        <svg width={width} height={height} className="block font-mono" role="img" aria-label={`${panel.names[0]} as bars`}>
          {panel.window && (
            <rect
              x={x(panel.window[0]) - 3}
              y={top - 6}
              width={(panel.window[1] - panel.window[0] + 1) * slot}
              height={H + 12}
              rx={8}
              fill="var(--sky-soft)"
              stroke="var(--sky)"
              strokeOpacity={0.5}
              style={{ transition: "all .3s" }}
            />
          )}
          {ov?.kind === "container" && (
            <rect
              x={x(ov.l) + barW / 2}
              y={y(ov.height)}
              width={x(ov.r) - x(ov.l)}
              height={base - y(ov.height)}
              fill="var(--sky-soft)"
              stroke="var(--sky)"
              strokeDasharray="4 3"
              style={{ transition: "all .3s" }}
            />
          )}
          {ov?.kind === "rect" && (
            <rect
              x={x(ov.from) - 2}
              y={y(ov.height)}
              width={(ov.to - ov.from + 1) * slot - 2}
              height={base - y(ov.height)}
              fill="var(--rose-soft)"
              stroke="var(--rose)"
              strokeDasharray="4 3"
              style={{ transition: "all .3s" }}
            />
          )}
          <line x1={left} x2={left + n * slot} y1={base} y2={base} stroke="var(--border-strong)" />
          {values.map((v, i) => {
            const cell = panel.cells[i];
            const water = ov?.kind === "water" ? ov.water[i] : 0;
            const decided = ov?.kind === "water" ? ov.decided[i] : false;
            const fill = FILL[cell.state] ?? FILL.idle;
            const ptrs = byIndex.get(i) ?? [];
            return (
              <g key={i}>
                {decided && water > 0 && (
                  <rect x={x(i)} y={y(v + water)} width={barW} height={y(v) - y(v + water)} fill="var(--sky)" opacity={0.55} rx={2} className="anim-pop" style={{ transformOrigin: `${x(i) + barW / 2}px ${y(v)}px` }}>
                    <title>{`${water} unit(s) of water`}</title>
                  </rect>
                )}
                <rect
                  x={x(i)}
                  y={Math.min(y(v), base)}
                  width={barW}
                  height={Math.max(2, Math.abs(base - y(v)))}
                  rx={3}
                  fill={fill}
                  fillOpacity={cell.state === "idle" ? 1 : 0.85}
                  stroke={marked.has(i) ? "var(--violet)" : cell.state === "idle" ? "var(--border-strong)" : fill}
                  strokeWidth={marked.has(i) ? 2 : 1}
                  style={{ transition: "y .25s, height .25s, fill .2s" }}
                />
                <text x={x(i) + barW / 2} y={Math.min(y(v), base) - 4} textAnchor="middle" fontSize={10} fill="var(--text-muted)">
                  {cell.text}
                </text>
                <text x={x(i) + barW / 2} y={base + 13} textAnchor="middle" fontSize={9} fill={marked.has(i) ? "var(--violet)" : "var(--text-faint)"}>
                  {i}
                </text>
                {ptrs.map((p, k) => (
                  <text key={p.name} x={x(i) + barW / 2} y={base + 27 + k * 11} textAnchor="middle" fontSize={10} fontWeight={700} fill={TONE_VARS[p.tone]}>
                    ▲{p.name}
                  </text>
                ))}
              </g>
            );
          })}
          {ov?.kind === "water" &&
            ov.levels.map((l) => {
              const x1 = x(l.from) - 2;
              const x2 = x(l.to) + barW + 2;
              const color = l.side === "left" ? "var(--accent)" : "var(--violet)";
              return (
                <g key={l.name} style={{ transition: "all .3s" }}>
                  <line x1={x1} x2={x2} y1={y(l.value)} y2={y(l.value)} stroke={color} strokeWidth={l.bottleneck ? 2.5 : 1.5} strokeDasharray={l.bottleneck ? undefined : "5 4"} />
                  <text
                    x={l.side === "left" ? x2 + 4 : x1 - 4}
                    y={y(l.value) - 4}
                    textAnchor={l.side === "left" ? "start" : "end"}
                    fontSize={10}
                    fontWeight={700}
                    fill={color}
                  >
                    {l.name}={l.value}
                    {l.bottleneck ? " ← sets the waterline" : ""}
                  </text>
                </g>
              );
            })}
        </svg>
      </div>
    </div>
  );
}
