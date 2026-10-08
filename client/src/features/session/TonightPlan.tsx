/**
 * Tonight's plan: before you start, the session the planner proposes; once started, the
 * same items with their progress folded from the log. Any item starts the session.
 */
import { useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { ArrowRight, Check, Moon, RotateCcw } from "lucide-react";
import { patterns, problemById, problems } from "@/content";
import { DAY_MS, cn, plural } from "@/lib/utils";
import { startSession, useStudy } from "@/store/events";
import { dueCards } from "@/store/progress";
import { planSession, totalMinutes, type ItemStatus, type SessionItem, type SessionKind } from "@/store/session";
import { Button, Chip, DifficultyBadge, Panel } from "@/ui/primitives";
import { KINDS, itemHref } from "./kinds";

type Row = SessionItem & { status?: ItemStatus };

function summary(items: SessionItem[]) {
  const counts = new Map<SessionKind, number>();
  for (const it of items) counts.set(it.kind, (counts.get(it.kind) ?? 0) + 1);
  const parts = (["recall", "fix", "new", "stretch"] as const)
    .filter((k) => counts.get(k))
    .map((k) => (k === "recall" ? plural(counts.get(k)!, "recall") : `${counts.get(k)} ${k}`));
  return `About ${totalMinutes(items)} minutes: ${parts.join(", ")}.`;
}

export function TonightPlan({ className }: { className?: string }) {
  const progress = useStudy((s) => s.progress);
  const session = useStudy((s) => s.session);
  const navigate = useNavigate();
  const [now] = useState(() => Date.now()); // render stays pure: one clock reading per visit
  const proposal = useMemo(() => planSession(progress, problems, patterns, now), [progress, now]);

  const rows: Row[] = session ? session.items : proposal;
  const next = session?.next ?? null;
  const complete = !!session && !next;
  const left = session ? session.items.filter((it) => it.status !== "done") : proposal;

  const open = (it: SessionItem) => {
    if (!session) startSession(proposal);
    navigate(itemHref(it));
  };
  const again = () => {
    startSession(proposal);
    if (proposal[0]) navigate(itemHref(proposal[0]));
  };
  const dueTomorrow = dueCards(progress, now + DAY_MS).length;

  return (
    <Panel className={cn("relative overflow-hidden p-5 sm:p-6", className)}>
      <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-accent-soft blur-3xl" aria-hidden />
      <div className="relative">
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-accent">
          <Moon size={13} /> Tonight · {new Date(now).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" })}
        </div>
        <h1 className="mt-2 font-display text-[30px] font-extrabold leading-tight tracking-tight">
          {complete ? "That's tonight done." : session ? `${session.done} of ${session.items.length} done` : rows.length ? "Your plan for tonight" : "Nothing to plan tonight"}
        </h1>
        <p className="mt-1 text-[13.5px] text-muted">
          {complete
            ? `The path is a little brighter. ${dueTomorrow ? `${plural(dueTomorrow, "card")} will be due tomorrow.` : "Nothing is due tomorrow."}`
            : rows.length
              ? summary(left)
              : "Everything is solved and nothing is fading. Practice recall cards anyway, or explore the playground."}
        </p>

        {rows.length > 0 && (
          <ol className="mt-5 space-y-2">
            {rows.map((it, i) => {
              const p = problemById.get(it.p);
              if (!p) return null;
              const k = KINDS[it.kind];
              const isNext = next ? it === next : !session && i === 0;
              const done = it.status === "done";
              return (
                <li key={`${it.kind}:${it.p}`}>
                  <button
                    onClick={() => open(it)}
                    className={cn(
                      "group grid w-full grid-cols-[26px_minmax(0,1fr)_auto] items-start gap-3 rounded-xl border px-3 py-2.5 text-left transition-colors",
                      isNext ? "border-accent/50 bg-accent-soft/60 shadow-glow" : "border-line bg-elev-2/40 hover:border-line-strong hover:bg-hover",
                      done && "opacity-70",
                    )}
                  >
                    <span
                      className={cn(
                        "mt-0.5 flex h-[22px] w-[22px] items-center justify-center rounded-full border font-mono text-[11px] font-bold",
                        done ? "border-ref bg-ref text-ref-ink" : it.status === "started" ? "border-accent text-accent" : "border-line-strong text-faint",
                      )}
                      aria-hidden
                    >
                      {done ? <Check size={12} strokeWidth={3} /> : i + 1}
                    </span>
                    <span className="min-w-0">
                      <span className="sr-only">{done ? "Done. " : it.status === "started" ? "Started. " : `Step ${i + 1}. `}</span>
                      <span className="flex flex-wrap items-center gap-2">
                        <Chip tone={k.tone} className="font-semibold">{k.label}</Chip>
                        <span className={cn("truncate text-[14px] font-semibold", done ? "text-muted line-through decoration-faint" : "text-fg group-hover:text-accent")}>
                          {p.title}
                        </span>
                        <DifficultyBadge value={p.difficulty} />
                      </span>
                      <span className="mt-0.5 block text-[12.5px] leading-snug text-muted">{it.reason}</span>
                    </span>
                    <span className="mt-0.5 whitespace-nowrap font-mono text-[11px] text-faint">{it.minutes}m</span>
                  </button>
                </li>
              );
            })}
          </ol>
        )}

        <div className="mt-5 flex flex-wrap items-center gap-3">
          {!session && proposal.length > 0 && (
            <Button variant="primary" size="lg" onClick={() => open(proposal[0])}>
              Start tonight's session <ArrowRight size={16} />
            </Button>
          )}
          {next && (
            <Button variant="primary" size="lg" onClick={() => open(next)}>
              Continue: {KINDS[next.kind].verb} {problemById.get(next.p)?.title} <ArrowRight size={16} />
            </Button>
          )}
          {complete && proposal.length > 0 && (
            <Button size="lg" onClick={again}>
              <RotateCcw size={15} /> Plan another round
            </Button>
          )}
          {!session && (
            <span className="text-[12px] text-faint">Recall first, then the hard part. Each item is one click away, here or in the header while you work.</span>
          )}
        </div>
      </div>
    </Panel>
  );
}
