import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { Building2, ChevronDown, CircleCheck, CircleDashed, Circle, Search, X } from "lucide-react";
import { COMPANY_NAMES, companies, patterns, problems } from "@/content";
import type { Difficulty, PatternId, ProblemSummary } from "@/content/types";
import { cn } from "@/lib/utils";
import { useStudy } from "@/store/events";
import type { Status } from "@/store/progress";
import { Chip, DifficultyBadge, ProgressRing } from "@/ui/primitives";

const DIFFS: Difficulty[] = ["Easy", "Medium", "Hard"];

export function StatusIcon({ status }: { status: Status | undefined }) {
  if (status === "solved") return <CircleCheck size={16} className="text-ref" aria-label="Solved" />;
  if (status === "attempted") return <CircleDashed size={16} className="text-accent" aria-label="Attempted" />;
  return <Circle size={16} className="text-line-strong" aria-label="Not started" />;
}

export function TierBars({ tier, className }: { tier: number; className?: string }) {
  return (
    <span className={cn("inline-flex items-end gap-[2px]", className)} title={`Reported frequency: ${tier}/5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={cn("w-[3px] rounded-sm", i <= tier ? "bg-accent" : "bg-line-strong")} style={{ height: 4 + i * 2 }} />
      ))}
    </span>
  );
}

function CompanyPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const list = COMPANY_NAMES.filter((c) => c.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex h-9 items-center gap-2 rounded-lg border px-3 text-[13px] transition-colors",
          value ? "border-accent/50 bg-accent-soft text-accent" : "border-line bg-elev text-muted hover:text-fg",
        )}
      >
        <Building2 size={14} />
        {value || "Company"}
        {value ? (
          <X size={13} onClick={(e) => { e.stopPropagation(); onChange(""); }} className="opacity-70 hover:opacity-100" />
        ) : (
          <ChevronDown size={13} />
        )}
      </button>
      {open && (
        <div className="anim-fade-up absolute right-0 z-30 mt-1.5 w-64 rounded-xl border border-line-strong bg-elev p-1.5 shadow-panel" onMouseLeave={() => setOpen(false)}>
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Filter companies…"
            className="mb-1 h-8 w-full rounded-md bg-elev-2 px-2.5 text-[13px] text-fg outline-none placeholder:text-faint"
          />
          <ul className="max-h-72 overflow-y-auto">
            {list.map((c) => (
              <li key={c}>
                <button
                  onClick={() => { onChange(c); setOpen(false); }}
                  className="flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-left text-[13px] text-muted hover:bg-hover hover:text-fg"
                >
                  {c}
                  <span className="text-[11px] text-faint">{companies[c].length}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function ProblemsPage() {
  const [params, setParams] = useSearchParams();
  const progress = useStudy((s) => s.progress);
  const [query, setQuery] = useState(params.get("q") ?? "");
  const pattern = (params.get("pattern") ?? "") as PatternId | "";
  const difficulty = (params.get("difficulty") ?? "") as Difficulty | "";
  const company = params.get("company") ?? "";
  const status = (params.get("status") ?? "") as Status | "";

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let list = problems.filter((p) => {
      if (pattern && p.pattern !== pattern) return false;
      if (difficulty && p.difficulty !== difficulty) return false;
      if (company && !p.companies[company]) return false;
      const st = progress.byProblem.get(p.id)?.status ?? "new";
      if (status && st !== status) return false;
      if (q && !`${p.number} ${p.title} ${p.topics.join(" ")}`.toLowerCase().includes(q)) return false;
      return true;
    });
    if (company) list = [...list].sort((a, b) => (b.companies[company] ?? 0) - (a.companies[company] ?? 0));
    return list;
  }, [query, pattern, difficulty, company, status, progress]);

  const solved = problems.filter((p) => progress.byProblem.get(p.id)?.status === "solved");
  const grouped = !company;

  return (
    <div className="mx-auto max-w-6xl px-4 pb-20 pt-8 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-6">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight">Problems</h1>
          <p className="mt-1 text-muted">
            The NeetCode 150 core, pattern by pattern. Every one runs, judges and visualizes in your browser - free.
          </p>
        </div>
        <div className="flex items-center gap-5">
          {DIFFS.map((d) => {
            const all = problems.filter((p) => p.difficulty === d);
            const done = solved.filter((p) => p.difficulty === d).length;
            const tone = d === "Easy" ? "var(--ref)" : d === "Medium" ? "var(--note)" : "var(--warn)";
            return (
              <div key={d} className="flex items-center gap-2.5">
                <ProgressRing value={done / all.length} size={38} tone={tone}>
                  <span className="text-[10px] font-semibold text-muted">{done}</span>
                </ProgressRing>
                <div className="text-xs leading-tight">
                  <div className="font-semibold" style={{ color: tone }}>{d}</div>
                  <div className="text-faint">{done}/{all.length}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="sticky top-[52px] z-20 -mx-2 mb-4 flex flex-wrap items-center gap-2 bg-bg/90 px-2 py-2 backdrop-blur-md">
        <div className="relative min-w-52 flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setParam("q", e.target.value);
            }}
            placeholder="Search by title, number or topic"
            className="h-9 w-full rounded-lg border border-line bg-elev pl-9 pr-3 text-[13px] text-fg outline-none transition-colors placeholder:text-faint focus:border-accent/60"
          />
        </div>
        <div className="flex rounded-lg border border-line bg-elev p-0.5">
          {(["", ...DIFFS] as const).map((d) => (
            <button
              key={d || "all"}
              onClick={() => setParam("difficulty", d)}
              className={cn(
                "h-7 rounded-md px-2.5 text-xs font-medium transition-colors",
                difficulty === d ? "bg-elev-2 text-fg shadow-[inset_0_0_0_1px_var(--border)]" : "text-muted hover:text-fg",
              )}
            >
              {d || "All"}
            </button>
          ))}
        </div>
        <div className="flex rounded-lg border border-line bg-elev p-0.5">
          {([["", "Any"], ["new", "Todo"], ["attempted", "Tried"], ["solved", "Solved"]] as const).map(([v, l]) => (
            <button
              key={l}
              onClick={() => setParam("status", v)}
              className={cn(
                "h-7 rounded-md px-2.5 text-xs font-medium transition-colors",
                status === v ? "bg-elev-2 text-fg shadow-[inset_0_0_0_1px_var(--border)]" : "text-muted hover:text-fg",
              )}
            >
              {l}
            </button>
          ))}
        </div>
        <CompanyPicker value={company} onChange={(v) => setParam("company", v)} />
      </div>

      <div className="mb-5 flex flex-wrap gap-1.5">
        <button
          onClick={() => setParam("pattern", "")}
          className={cn("rounded-full border px-3 py-1 text-xs font-medium transition-colors",
            !pattern ? "border-accent/50 bg-accent-soft text-accent" : "border-line text-muted hover:text-fg")}
        >
          All patterns
        </button>
        {patterns.map((p) => (
          <button
            key={p.id}
            onClick={() => setParam("pattern", pattern === p.id ? "" : p.id)}
            className={cn("rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              pattern === p.id ? "border-accent/50 bg-accent-soft text-accent" : "border-line text-muted hover:text-fg")}
          >
            {p.name}
          </button>
        ))}
      </div>

      {company && (
        <p className="mb-3 text-xs text-faint">
          Ranked by how often {company} reportedly asks each problem. Company tags are compiled from public interview reports - treat them as a signal, not a guarantee.
        </p>
      )}

      {filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line p-12 text-center text-muted">Nothing matches those filters.</div>
      ) : grouped ? (
        patterns
          .filter((p) => filtered.some((x) => x.pattern === p.id))
          .map((p) => {
            const rows = filtered.filter((x) => x.pattern === p.id);
            const all = problems.filter((x) => x.pattern === p.id);
            const done = all.filter((x) => progress.byProblem.get(x.id)?.status === "solved").length;
            return (
              <section key={p.id} className="mb-8">
                <div className="mb-2 flex items-center gap-3">
                  <Link to={`/patterns/${p.id}`} className="font-display text-lg font-bold hover:text-accent">{p.name}</Link>
                  <span className="text-xs text-faint">{p.tagline}</span>
                  <span className="ml-auto text-xs text-muted">{done}/{all.length}</span>
                  <div className="h-1.5 w-24 overflow-hidden rounded-full bg-elev-2">
                    <div className="h-full rounded-full bg-ref transition-all" style={{ width: `${(done / all.length) * 100}%` }} />
                  </div>
                </div>
                <ProblemTable rows={rows} company={company} />
              </section>
            );
          })
      ) : (
        <ProblemTable rows={filtered} company={company} showPattern />
      )}
    </div>
  );
}

function ProblemTable({ rows, company, showPattern = false }: { rows: ProblemSummary[]; company: string; showPattern?: boolean }) {
  const progress = useStudy((s) => s.progress);
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-elev">
      {rows.map((p, i) => {
        const top = Object.entries(p.companies).sort((a, b) => b[1] - a[1]).slice(0, 3);
        return (
          <Link
            key={p.id}
            to={`/problems/${p.id}`}
            className={cn(
              "group grid grid-cols-[24px_1fr_auto] items-center gap-3 px-4 py-3 transition-colors hover:bg-hover sm:grid-cols-[24px_minmax(0,1fr)_90px_minmax(0,220px)_auto]",
              i > 0 && "border-t border-line",
            )}
          >
            <StatusIcon status={progress.byProblem.get(p.id)?.status} />
            <div className="min-w-0">
              <div className="truncate text-[14px] font-medium text-fg group-hover:text-accent">
                <span className="mr-1.5 font-mono text-xs text-faint">{p.number}.</span>
                {p.title}
              </div>
              <div className="truncate text-xs text-faint">
                {showPattern ? patterns.find((x) => x.id === p.pattern)?.name + " · " : ""}
                {p.oneLiner}
              </div>
            </div>
            <DifficultyBadge value={p.difficulty} className="justify-self-start" />
            <div className="hidden items-center gap-1.5 sm:flex">
              {company ? (
                <>
                  <TierBars tier={p.companies[company]} />
                  <span className="text-xs text-muted">{company}</span>
                </>
              ) : (
                <>
                  {top.map(([c]) => (
                    <Chip key={c}>{c}</Chip>
                  ))}
                  {Object.keys(p.companies).length > 3 && <span className="text-[11px] text-faint">+{Object.keys(p.companies).length - 3}</span>}
                </>
              )}
            </div>
            <div className="hidden justify-self-end whitespace-nowrap font-mono text-[11px] text-faint sm:block" title={`Optimal: ${p.optimal.time} time, ${p.optimal.space} space`}>
              {p.optimal.time.replace(/ · /g, "·")}
            </div>
          </Link>
        );
      })}
    </div>
  );
}
