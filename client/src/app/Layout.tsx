import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { Flame, Moon, Search, Sun } from "lucide-react";
import { GithubMark } from "@/ui/icons";
import { cn, modKey } from "@/lib/utils";
import { useSettings } from "@/store/settings";
import { useStudy } from "@/store/events";
import { dueCards } from "@/store/progress";
import { IconButton, Kbd, Wordmark } from "@/ui/primitives";
import { SessionPill } from "@/features/session/SessionPill";
import { CommandPalette } from "./CommandPalette";
import { MobileNav, type NavItem } from "./MobileNav";
import { RuntimePill } from "./RuntimePill";

const NAV: NavItem[] = [
  { to: "/", label: "Tonight", end: true },
  { to: "/problems", label: "Problems" },
  { to: "/review", label: "Review" },
  { to: "/playground", label: "Playground" },
];

export function Layout() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const { theme, toggleTheme } = useSettings();
  const progress = useStudy((s) => s.progress);
  const due = dueCards(progress).length;
  const location = useLocation();
  const inWorkspace = /^\/problems\/[^/]+/.test(location.pathname);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className={cn("flex min-h-full flex-col", inWorkspace && "h-full")}>
      <header className="sticky top-0 z-40 flex h-[52px] shrink-0 items-center gap-4 border-b border-line bg-bg/85 px-3 backdrop-blur-md sm:gap-6 sm:px-4">
        <Link to="/" className="flex items-center" aria-label="Feetcode home">
          <Wordmark />
        </Link>
        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                cn(
                  "relative rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors",
                  isActive ? "text-fg" : "text-muted hover:text-fg",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {n.label}
                  {n.to === "/review" && due > 0 && (
                    <span className="ml-1.5 rounded-full bg-accent px-1.5 text-[10px] font-bold text-accent-ink">{due}</span>
                  )}
                  {isActive && <span className="absolute inset-x-3 -bottom-[11px] h-0.5 rounded-full bg-accent" />}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-1.5">
          <SessionPill collapse className="mr-1.5 hidden md:flex" />
          <button
            onClick={() => setPaletteOpen(true)}
            className="hidden h-8 items-center gap-2 rounded-lg border border-line bg-elev px-2.5 text-[13px] text-faint transition-colors hover:border-line-strong hover:text-muted sm:flex"
          >
            <Search size={14} />
            <span className="w-36 text-left">Jump to a problem…</span>
            <Kbd>{modKey()}</Kbd>
            <Kbd>K</Kbd>
          </button>
          <IconButton label="Search" className="sm:hidden" onClick={() => setPaletteOpen(true)}>
            <Search size={16} />
          </IconButton>
          <RuntimePill />
          <Link
            to="/stats"
            title={`${progress.streak}-day streak`}
            className={cn(
              "flex h-8 items-center gap-1 rounded-lg px-2 text-[13px] font-semibold transition-colors hover:bg-hover",
              progress.streak > 0 ? "text-accent" : "text-faint",
            )}
          >
            <Flame size={15} className={progress.streak > 0 ? "fill-accent/30" : ""} />
            {progress.streak}
          </Link>
          <IconButton label={theme === "dark" ? "Light theme" : "Dark theme"} onClick={toggleTheme}>
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </IconButton>
          <a href="https://github.com/Tahmudun/Feetcode" target="_blank" rel="noreferrer" aria-label="Source on GitHub" className="hidden sm:block">
            <IconButton label="Source on GitHub">
              <GithubMark size={16} />
            </IconButton>
          </a>
          <MobileNav items={NAV} due={due} />
        </div>
      </header>
      <main className={cn("flex-1", inWorkspace && "min-h-0")}>
        <Outlet />
      </main>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
}
