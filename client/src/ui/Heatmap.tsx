import { DAY_MS, dayKey } from "@/lib/utils";

/** GitHub-style activity calendar: one cell per day, columns are weeks. */
export function Heatmap({ activity, weeks = 20 }: { activity: Map<string, number>; weeks?: number }) {
  const today = new Date();
  today.setHours(12, 0, 0, 0);
  const end = today.getTime();
  const start = end - (weeks * 7 - 1 - (6 - today.getDay())) * DAY_MS;
  const days: { key: string; count: number; ts: number }[] = [];
  for (let t = start; t <= end; t += DAY_MS) days.push({ key: dayKey(t), ts: t, count: activity.get(dayKey(t)) ?? 0 });
  const max = Math.max(1, ...days.map((d) => d.count));
  const columns: (typeof days)[] = [];
  for (let i = 0; i < days.length; i += 7) columns.push(days.slice(i, i + 7));
  const level = (c: number) => (c === 0 ? 0 : Math.ceil((c / max) * 4));
  const colors = ["var(--bg-elev-2)", "color-mix(in oklab, var(--ref) 30%, var(--bg-elev-2))", "color-mix(in oklab, var(--ref) 55%, var(--bg-elev-2))", "color-mix(in oklab, var(--ref) 78%, var(--bg-elev-2))", "var(--ref)"];
  return (
    <div className="flex gap-[3px]" role="img" aria-label="Study activity over the last weeks">
      {columns.map((col, i) => (
        <div key={i} className="flex flex-col gap-[3px]">
          {col.map((d) => (
            <div
              key={d.key}
              title={`${d.key}: ${d.count} event${d.count === 1 ? "" : "s"}`}
              className="h-[11px] w-[11px] rounded-[3px]"
              style={{ background: colors[level(d.count)] }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
