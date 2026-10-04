import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { ArrowRight, BookOpen, Brain, Code2, Dice5, Moon, Repeat, Search, Waypoints } from "lucide-react";
import { patterns, problems } from "@/content";
import { cn } from "@/lib/utils";
import { useSettings } from "@/store/settings";
import { useStudy } from "@/store/events";
import { DifficultyBadge, Kbd } from "@/ui/primitives";

interface Item {
  id: string;
  label: string;
  hint?: string;
  icon: React.ReactNode;
  right?: React.ReactNode;
  haystack: string;
  run: () => void;
}

/** Score a candidate: every query token must appear; prefix and word-start matches rank higher. */
export function score(haystack: string, query: string): number {
  const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!tokens.length) return 1;
  let s = 0;
  for (const t of tokens) {
    const i = haystack.indexOf(t);
    if (i < 0) return 0;
    s += i === 0 ? 6 : /[\s\-#]/.test(haystack[i - 1]) ? 4 : 1;
  }
  return s;
}

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  return open ? <PaletteBody onClose={onClose} /> : null;
}

function PaletteBody({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const toggleTheme = useSettings((s) => s.toggleTheme);
  const progress = useStudy((s) => s.progress);

  const items = useMemo<Item[]>(() => {
    const go = (to: string) => () => navigate(to);
    const unsolved = problems.filter((p) => progress.byProblem.get(p.id)?.status !== "solved");
    const pages: Item[] = [
      { id: "page:problems", label: "All problems", icon: <Code2 size={15} />, haystack: "problems list all", run: go("/problems") },
      { id: "page:patterns", label: "Pattern roadmap", icon: <Waypoints size={15} />, haystack: "patterns roadmap learn", run: go("/patterns") },
      { id: "page:review", label: "Start a review session", icon: <Repeat size={15} />, haystack: "review spaced repetition flashcards recall", run: go("/review") },
      { id: "page:playground", label: "Playground - visualize any Python", icon: <Brain size={15} />, haystack: "playground visualize any code python tutor", run: go("/playground") },
      { id: "action:random", label: "Random unsolved problem", icon: <Dice5 size={15} />, haystack: "random surprise shuffle unsolved",
        run: () => { const p = unsolved[Math.floor(Math.random() * unsolved.length)] ?? problems[0]; navigate(`/problems/${p.id}`); } },
      { id: "action:theme", label: "Toggle light / dark theme", icon: <Moon size={15} />, haystack: "theme dark light mode toggle", run: toggleTheme },
    ];
    const pats: Item[] = patterns.map((p) => ({
      id: `pattern:${p.id}`, label: p.name, hint: "pattern", icon: <BookOpen size={15} />,
      haystack: `${p.name} ${p.id} pattern`.toLowerCase(), run: go(`/patterns/${p.id}`),
    }));
    const probs: Item[] = problems.map((p) => ({
      id: `problem:${p.id}`,
      label: `${p.number}. ${p.title}`,
      hint: patterns.find((x) => x.id === p.pattern)?.name,
      icon: <span className="w-[15px] text-center font-mono text-[10px] text-faint">#</span>,
      right: <DifficultyBadge value={p.difficulty} />,
      haystack: `${p.number} ${p.title} ${p.id} ${p.pattern} ${Object.keys(p.companies).join(" ")} ${p.topics.join(" ")}`.toLowerCase(),
      run: go(`/problems/${p.id}`),
    }));
    return [...probs, ...pats, ...pages];
  }, [navigate, toggleTheme, progress]);

  const results = useMemo(() => {
    if (!query.trim()) return items.filter((i) => !i.id.startsWith("problem:")).concat(items.filter((i) => i.id.startsWith("problem:")).slice(0, 6));
    return items
      .map((i) => ({ i, s: score(i.haystack + " " + i.label.toLowerCase(), query) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s)
      .slice(0, 12)
      .map((x) => x.i);
  }, [items, query]);

  useEffect(() => {
    requestAnimationFrame(() => inputRef.current?.focus());
  }, []);

  const choose = (item?: Item) => {
    if (!item) return;
    onClose();
    item.run();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 px-4 pt-[12vh] backdrop-blur-sm" onMouseDown={onClose}>
      <div
        role="dialog"
        aria-label="Command palette"
        className="anim-fade-up w-full max-w-xl overflow-hidden rounded-2xl border border-line-strong bg-elev shadow-panel"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-line px-4">
          <Search size={16} className="text-faint" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setCursor(0);
            }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setCursor((c) => Math.min(results.length - 1, c + 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setCursor((c) => Math.max(0, c - 1));
              } else if (e.key === "Enter") {
                choose(results[cursor]);
              } else if (e.key === "Escape") {
                onClose();
              }
            }}
            placeholder="Search problems, patterns, companies…"
            className="h-12 flex-1 bg-transparent text-[15px] text-fg outline-none placeholder:text-faint"
          />
          <Kbd>esc</Kbd>
        </div>
        <ul className="max-h-[50vh] overflow-y-auto p-1.5" role="listbox">
          {results.length === 0 && <li className="px-3 py-6 text-center text-sm text-muted">No matches. Try a company name like "google".</li>}
          {results.map((item, i) => (
            <li
              key={item.id}
              role="option"
              aria-selected={i === cursor}
              onMouseEnter={() => setCursor(i)}
              onClick={() => choose(item)}
              className={cn(
                "flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-[13px]",
                i === cursor ? "bg-hover text-fg" : "text-muted",
              )}
            >
              <span className="text-faint">{item.icon}</span>
              <span className="flex-1 truncate">{item.label}</span>
              {item.hint && <span className="text-[11px] text-faint">{item.hint}</span>}
              {item.right}
              {i === cursor && <ArrowRight size={14} className="text-accent" />}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
