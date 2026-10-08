/**
 * Navigation below the md breakpoint, where the header has no room for links: a menu button
 * that opens a panel under the header with the same destinations, tonight's session and the
 * secondary pages. It closes on navigation, Escape or a tap outside.
 */
import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation } from "react-router";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStudy } from "@/store/events";
import { SessionPill } from "@/features/session/SessionPill";
import { IconButton } from "@/ui/primitives";

export interface NavItem {
  to: string;
  label: string;
  end?: boolean;
}

export function MobileNav({ items, due }: { items: NavItem[]; due: number }) {
  const { pathname } = useLocation();
  // Open "on" a path: navigating anywhere closes it, with no effect needed to reset it.
  const [openOn, setOpenOn] = useState<string | null>(null);
  const open = openOn === pathname;
  const button = useRef<HTMLButtonElement>(null);
  const sessionLeft = useStudy((s) => !!s.session?.next);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      setOpenOn(null);
      button.current?.focus();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const link = (to: string, label: string, end?: boolean, badge?: number) => (
    <NavLink
      key={to}
      to={to}
      end={end}
      onClick={() => setOpenOn(null)}
      className={({ isActive }) =>
        cn(
          "flex h-11 items-center justify-between rounded-lg px-3 text-[15px] font-medium transition-colors",
          isActive ? "bg-accent-soft text-fg" : "text-muted hover:bg-hover hover:text-fg",
        )
      }
    >
      {({ isActive }) => (
        <>
          <span className="flex items-center gap-2.5">
            <span className={cn("h-4 w-0.5 rounded-full", isActive ? "bg-accent" : "bg-transparent")} aria-hidden />
            {label}
          </span>
          {badge ? <span className="rounded-full bg-accent px-2 text-[11px] font-bold text-accent-ink">{badge}</span> : null}
        </>
      )}
    </NavLink>
  );

  return (
    <div className="md:hidden">
      <IconButton
        ref={button}
        label={open ? "Close menu" : "Menu"}
        aria-expanded={open}
        aria-controls="mobile-nav"
        onClick={() => setOpenOn(open ? null : pathname)}
        className="relative"
      >
        {open ? <X size={18} /> : <Menu size={18} />}
        {!open && (due > 0 || sessionLeft) && <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-accent" aria-hidden />}
      </IconButton>
      {open && (
        <>
          <div className="fixed inset-x-0 bottom-0 top-[52px] z-30 bg-bg/70 backdrop-blur-sm" onClick={() => setOpenOn(null)} aria-hidden />
          <nav
            id="mobile-nav"
            aria-label="Main"
            className="anim-fade-up fixed inset-x-0 top-[52px] z-40 max-h-[calc(100dvh-52px)] overflow-y-auto border-b border-line bg-elev px-3 pb-4 pt-2 shadow-panel"
          >
            {items.map((n) => link(n.to, n.label, n.end, n.to === "/review" ? due : undefined))}
            <SessionPill className="mt-3 w-full justify-start" />
            <div className="mt-3 border-t border-line pt-2">
              {link("/patterns", "Pattern guides")}
              {link("/stats", "Stats")}
              <a
                href="https://github.com/Tahmudun/Feetcode"
                target="_blank"
                rel="noreferrer"
                className="flex h-11 items-center gap-2.5 rounded-lg px-3 text-[15px] font-medium text-muted hover:bg-hover hover:text-fg"
              >
                <span className="h-4 w-0.5" aria-hidden />
                Source on GitHub
              </a>
            </div>
          </nav>
        </>
      )}
    </div>
  );
}
