import { compact } from "@/lib/utils";

export interface Series {
  id: string;
  label: string;
  points: { n: number; ops: number | null; capped?: boolean }[];
  color: string;
  dashed?: boolean;
  bold?: boolean;
  fit?: string | null;
}

/**
 * Operations vs input size on log-log axes. On these axes every polynomial is a
 * straight line whose slope is its exponent - O(n) and O(n²) separate at a glance.
 */
export function ComplexityChart({ series, height = 230, cap }: { series: Series[]; height?: number; cap?: number }) {
  const all = series.flatMap((s) => s.points.filter((p) => p.ops !== null && p.ops > 0));
  if (all.length < 2) return <div className="text-[13px] text-faint">Not enough data to chart.</div>;
  const width = 560;
  const pad = { l: 46, r: 16, t: 12, b: 30 };
  const ns = all.map((p) => p.n);
  const ys = all.map((p) => p.ops as number).concat(cap ? [cap] : []);
  const x0 = Math.log2(Math.min(...ns));
  const x1 = Math.log2(Math.max(...ns));
  const y0 = Math.floor(Math.log10(Math.max(1, Math.min(...ys))));
  const y1 = Math.ceil(Math.log10(Math.max(...ys)));
  const X = (n: number) => pad.l + ((Math.log2(n) - x0) / Math.max(1e-9, x1 - x0)) * (width - pad.l - pad.r);
  const Y = (v: number) => pad.t + (1 - (Math.log10(Math.max(1, v)) - y0) / Math.max(1e-9, y1 - y0)) * (height - pad.t - pad.b);
  const xticks = Array.from(new Set(ns)).sort((a, b) => a - b);
  const yticks = Array.from({ length: y1 - y0 + 1 }, (_, i) => 10 ** (y0 + i));

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full max-w-[640px] font-mono" role="img" aria-label="Operations as input grows">
        {yticks.map((t) => (
          <g key={t}>
            <line x1={pad.l} x2={width - pad.r} y1={Y(t)} y2={Y(t)} stroke="var(--border)" strokeDasharray="2 4" />
            <text x={pad.l - 6} y={Y(t) + 3} textAnchor="end" fontSize={9} fill="var(--text-faint)">{compact(t)}</text>
          </g>
        ))}
        {xticks.map((n) => (
          <text key={n} x={X(n)} y={height - pad.b + 14} textAnchor="middle" fontSize={9} fill="var(--text-faint)">{n}</text>
        ))}
        <text x={width - pad.r} y={height - 4} textAnchor="end" fontSize={9} fill="var(--text-faint)">input size n →</text>
        <text x={4} y={pad.t + 2} fontSize={9} fill="var(--text-faint)">ops</text>
        {cap && (
          <g>
            <line x1={pad.l} x2={width - pad.r} y1={Y(cap)} y2={Y(cap)} stroke="var(--warn)" strokeDasharray="6 4" strokeOpacity={0.6} />
            <text x={width - pad.r} y={Y(cap) - 4} textAnchor="end" fontSize={9} fill="var(--warn)">budget</text>
          </g>
        )}
        {series.map((s) => {
          const pts = s.points.filter((p) => p.ops !== null && p.ops > 0);
          if (!pts.length) return null;
          const d = pts.map((p, i) => `${i ? "L" : "M"} ${X(p.n).toFixed(1)} ${Y(p.ops as number).toFixed(1)}`).join(" ");
          const capped = s.points.find((p) => p.capped);
          const last = pts[pts.length - 1];
          return (
            <g key={s.id}>
              <path d={d} fill="none" stroke={s.color} strokeWidth={s.bold ? 2.6 : 1.6} strokeDasharray={s.dashed ? "5 4" : undefined} strokeLinejoin="round" />
              {pts.map((p) => (
                <circle key={p.n} cx={X(p.n)} cy={Y(p.ops as number)} r={s.bold ? 3 : 2.2} fill={s.color}>
                  <title>{`${s.label}: n=${p.n} → ${p.ops?.toLocaleString()} ops`}</title>
                </circle>
              ))}
              {capped && (
                <text x={X(last.n) + 6} y={Y(last.ops as number) - 6} fontSize={11} fill={s.color} fontWeight={700}>↑ over budget</text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1">
        {series.map((s) => (
          <span key={s.id} className="flex items-center gap-1.5 text-[11.5px] text-muted">
            <span className="inline-block h-[3px] w-4 rounded-full" style={{ background: s.color, opacity: s.dashed ? 0.7 : 1 }} />
            {s.label}
            {s.fit && <span className="font-mono text-[11px] font-semibold" style={{ color: s.color }}>{s.fit}</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

export const SERIES_COLORS = ["var(--text-faint)", "var(--note)", "var(--ref)", "var(--sky)"];
