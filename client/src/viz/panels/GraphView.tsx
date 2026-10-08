import type { GraphEdgeView, GraphNodeView, GraphPanel } from "../scene";
import { TONE_VARS } from "./ArrayView";

const NW = 50;
const NH = 32;
const DX = 88;
const DY = 104;
const PAD_X = 20;
const PAD_TOP = 56;

const FILL: Record<string, string> = {
  idle: "var(--bg-elev-2)",
  active: "var(--accent-soft)",
  changed: "var(--accent-soft)",
  new: "var(--note-soft)",
  match: "var(--ref-soft)",
  compare: "var(--warn-soft)",
};
const STROKE: Record<string, string> = {
  idle: "var(--border-strong)",
  active: "var(--accent)",
  changed: "var(--accent)",
  new: "var(--note)",
  match: "var(--ref)",
  compare: "var(--warn)",
};

const NAME_TONES: Record<string, number> = { prev: 1, curr: 0, cur: 0, nxt: 2, next: 2, head: 3, dummy: 4, slow: 0, fast: 1, tail: 3 };
function tone(name: string) {
  if (name in NAME_TONES) return NAME_TONES[name];
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return h % TONE_VARS.length;
}

const cx = (n: { col: number }) => PAD_X + n.col * DX + NW / 2;
const cy = (n: { row: number }) => PAD_TOP + n.row * DY + NH / 2;

function edgePath(e: GraphEdgeView, a: GraphNodeView, b: GraphNodeView, doubly: boolean): string {
  const ax = cx(a);
  const ay = cy(a);
  const bx = cx(b);
  const by = cy(b);
  if (e.kind === "random") {
    const depth = 26 + Math.abs(b.col - a.col) * 8 + (a.id === b.id ? 10 : 0);
    if (a.id === b.id) return `M ${ax - 10} ${ay + NH / 2} C ${ax - 30} ${ay + NH / 2 + depth}, ${ax + 30} ${ay + NH / 2 + depth}, ${ax + 10} ${ay + NH / 2}`;
    return `M ${ax} ${ay + NH / 2} Q ${(ax + bx) / 2} ${Math.max(ay, by) + NH / 2 + depth} ${bx} ${by + NH / 2 + 2}`;
  }
  if (a.row === b.row) {
    const off = doubly ? (e.kind === "next" ? -7 : 7) : 0;
    if (b.col === a.col + 1) return `M ${ax + NW / 2} ${ay + off} L ${bx - NW / 2 - 2} ${by + off}`;
    if (b.col === a.col - 1) return `M ${ax - NW / 2} ${ay + off} L ${bx + NW / 2 + 2} ${by + off}`;
    if (a.id === b.id) return `M ${ax + 8} ${ay - NH / 2} C ${ax + 30} ${ay - NH / 2 - 34}, ${ax - 30} ${ay - NH / 2 - 34}, ${ax - 8} ${ay - NH / 2 - 2}`;
    const lift = 22 + Math.abs(b.col - a.col) * 7;
    return `M ${ax} ${ay - NH / 2} Q ${(ax + bx) / 2} ${ay - NH / 2 - lift} ${bx} ${by - NH / 2 - 2}`;
  }
  const down = b.row > a.row;
  const y1 = down ? ay + NH / 2 : ay - NH / 2;
  const y2 = down ? by - NH / 2 - 2 : by + NH / 2 + 2;
  const mid = (y1 + y2) / 2;
  return `M ${ax} ${y1} C ${ax} ${mid}, ${bx} ${mid}, ${bx} ${y2}`;
}

export function GraphView({ panel }: { panel: GraphPanel }) {
  const byId = new Map(panel.nodes.map((n) => [n.id, n]));
  const doubly = panel.edges.some((e) => e.kind === "prev");
  const nullCol = panel.cols + 0.3;
  const width = PAD_X * 2 + Math.max(panel.cols, 1) * DX + (panel.nulls.length ? DX : 0);
  const height = PAD_TOP + Math.max(panel.rows, 1) * DY - 20 + (panel.edges.some((e) => e.kind === "random") ? 40 : 0);
  return (
    <div>
      <div className="mb-1 flex items-center gap-3 font-mono text-[12px]">
        <span className="font-semibold text-fg">linked nodes</span>
        <span className="text-faint">{panel.nodes.length} node{panel.nodes.length === 1 ? "" : "s"}</span>
        <span className="flex items-center gap-1 text-[10px] text-faint"><span className="inline-block h-0.5 w-4 bg-muted" /> next</span>
        {doubly && <span className="flex items-center gap-1 text-[10px] text-faint"><span className="inline-block h-0.5 w-4 border-t border-dashed border-faint" /> prev</span>}
        {panel.edges.some((e) => e.kind === "random") && <span className="flex items-center gap-1 text-[10px] text-note"><span className="inline-block h-0.5 w-4 bg-note" /> random</span>}
      </div>
      <div className="overflow-x-auto">
        <svg width={width} height={height} className="block font-mono" role="img" aria-label="linked list">
          <defs>
            {[["next", "var(--text-muted)"], ["new", "var(--accent)"], ["random", "var(--note)"], ["prev", "var(--text-faint)"]].map(([id, color]) => (
              <marker key={id} id={`arrow-${id}`} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill={color} />
              </marker>
            ))}
          </defs>
          {panel.edges.map((e) => {
            const a = byId.get(e.from);
            const b = byId.get(e.to);
            if (!a || !b) return null;
            const color = e.state === "new" ? "var(--accent)" : e.kind === "random" ? "var(--note)" : e.kind === "prev" ? "var(--text-faint)" : "var(--text-muted)";
            const marker = e.state === "new" ? "new" : e.kind;
            return (
              <path
                key={`${e.from}-${e.kind}-${e.to}`}
                d={edgePath(e, a, b, doubly)}
                fill="none"
                stroke={color}
                strokeWidth={e.state === "new" ? 2.4 : e.kind === "next" ? 1.6 : 1.2}
                strokeDasharray={e.kind === "prev" ? "4 3" : undefined}
                markerEnd={`url(#arrow-${marker})`}
                className={e.state === "new" ? "anim-pop" : undefined}
              />
            );
          })}
          {panel.nodes.map((n) => (
            <g key={n.id} style={{ transform: `translate(${cx(n) - NW / 2}px, ${cy(n) - NH / 2}px)`, transition: "transform .35s cubic-bezier(.2,.8,.2,1)" }}>
              <rect width={NW} height={NH} rx={9} fill={FILL[n.state] ?? FILL.idle} stroke={STROKE[n.state] ?? STROKE.idle} strokeWidth={n.state === "idle" ? 1 : 2} />
              <text x={NW / 2} y={NH / 2 + 4} textAnchor="middle" fontSize={n.label.length > 5 ? 10 : 13} fontWeight={600} fill="var(--text)">
                {n.label}
              </text>
              {n.vars.slice(0, 3).map((v, k) => (
                <text key={v} x={NW / 2} y={-8 - k * 13} textAnchor="middle" fontSize={11} fontWeight={700} fill={TONE_VARS[tone(v)]}>
                  {v}
                  {k === 0 ? " ▾" : ""}
                </text>
              ))}
              {n.vars.length > 3 && (
                <text x={NW / 2} y={-8 - 3 * 13} textAnchor="middle" fontSize={10} fill="var(--text-faint)">+{n.vars.length - 3}</text>
              )}
            </g>
          ))}
          {panel.nulls.length > 0 && (
            <g transform={`translate(${PAD_X + nullCol * DX}, ${PAD_TOP})`}>
              <rect width={NW} height={NH} rx={9} fill="none" stroke="var(--border-strong)" strokeDasharray="3 3" />
              <text x={NW / 2} y={NH / 2 + 4} textAnchor="middle" fontSize={11} fill="var(--text-faint)">None</text>
              {panel.nulls.slice(0, 3).map((v, k) => (
                <text key={v} x={NW / 2} y={-8 - k * 13} textAnchor="middle" fontSize={11} fontWeight={700} fill={TONE_VARS[tone(v)]}>
                  {v}
                  {k === 0 ? " ▾" : ""}
                </text>
              ))}
            </g>
          )}
        </svg>
      </div>
    </div>
  );
}
