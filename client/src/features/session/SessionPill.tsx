/**
 * Tonight's session in the header: one dot per item and the way to the next one, so moving
 * between items never needs a trip back home.
 */
import { Link, useLocation } from "react-router";
import { ArrowRight, Check } from "lucide-react";
import { problemById } from "@/content";
import { cn } from "@/lib/utils";
import { useStudy } from "@/store/events";
import type { SessionEntry } from "@/store/session";
import { KINDS, itemHref } from "./kinds";

export function SessionPill({ className }: { className?: string }) {
  const session = useStudy((s) => s.session);
  const { pathname } = useLocation();
  if (!session || !session.items.length) return null;
  const { items, done } = session;
  const base = "flex h-8 items-center gap-2 rounded-full border px-3 text-[12px] transition-colors";

  if (!session.next) {
    return (
      <Link to="/" className={cn(base, "border-ref/40 bg-ref-soft text-ref hover:border-ref", className)} title="Tonight's session is complete">
        <Check size={13} /> Tonight done · {done}/{items.length}
      </Link>
    );
  }

  // On an unfinished item's page (recalls share /review), point past it; anywhere else, at the first unfinished item.
  const here = items.find((it) => it.status !== "done" && itemHref(it) === pathname);
  const target = here ? items.find((it) => it.status !== "done" && itemHref(it) !== pathname) : session.next;
  const dots = <Dots items={items} here={here} />;
  const count = <span className="font-mono text-faint">{done}/{items.length}</span>;

  if (!target) {
    return (
      <div className={cn(base, "border-accent/40 bg-accent-soft text-fg", className)}>
        {dots} {count} <span>Last one: <b className="font-semibold text-accent">{KINDS[here!.kind].label}</b></span>
      </div>
    );
  }
  const title = problemById.get(target.p)?.title ?? target.p;
  return (
    <Link
      to={itemHref(target)}
      className={cn(base, "border-line bg-elev text-muted hover:border-accent/50 hover:text-fg", className)}
      title={`Tonight's session: ${done} of ${items.length} done`}
    >
      {dots} {count}
      <span className="max-w-[220px] truncate">
        {here ? "Then" : "Next"}: <b className="font-semibold text-fg">{KINDS[target.kind].verb} {title}</b>
      </span>
      <ArrowRight size={13} className="shrink-0 text-accent" />
    </Link>
  );
}

function Dots({ items, here }: { items: SessionEntry[]; here?: SessionEntry }) {
  return (
    <span className="flex items-center gap-1" aria-hidden>
      {items.map((it, i) => (
        <span
          key={i}
          className={cn(
            "h-2 w-2 rounded-full",
            it.status === "done" ? "bg-ref" : it.status === "started" ? "border border-accent bg-accent-soft" : "border border-line-strong",
            it === here && "ring-2 ring-accent/60",
          )}
        />
      ))}
    </span>
  );
}
