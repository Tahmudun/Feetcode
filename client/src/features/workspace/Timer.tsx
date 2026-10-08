import { useEffect, useState } from "react";
import { Pause, Timer as TimerIcon, X } from "lucide-react";
import { cn } from "@/lib/utils";

/** Interview mode: a visible clock. Click to start; turns accent at 20 min and warn at 35. */
export function Timer() {
  const [start, setStart] = useState<number | null>(null);
  const [paused, setPaused] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (start === null || paused !== null) return;
    const id = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(id);
  }, [start, paused]);

  if (start === null) {
    return (
      <button
        onClick={() => { setStart(Date.now()); setNow(Date.now()); }}
        title="Start an interview timer"
        className="flex h-8 items-center gap-1.5 rounded-lg px-2 text-xs text-muted hover:bg-hover hover:text-fg"
      >
        <TimerIcon size={15} />
      </button>
    );
  }
  const elapsed = (paused ?? now) - start;
  const m = Math.floor(elapsed / 60000);
  const s = Math.floor((elapsed % 60000) / 1000);
  return (
    <div className={cn("flex h-8 items-center gap-1 rounded-lg border px-2 font-mono text-xs", m >= 35 ? "border-warn/50 text-warn" : m >= 20 ? "border-accent/50 text-accent" : "border-line text-fg")}>
      {String(m).padStart(2, "0")}:{String(s).padStart(2, "0")}
      <button
        aria-label={paused ? "Resume timer" : "Pause timer"}
        onClick={() => {
          if (paused !== null) {
            setStart((st) => (st ?? 0) + (Date.now() - paused));
            setPaused(null);
          } else setPaused(Date.now());
        }}
        className="ml-1 text-muted hover:text-fg"
      >
        {paused ? <TimerIcon size={12} /> : <Pause size={12} />}
      </button>
      <button aria-label="Stop timer" onClick={() => setStart(null)} className="text-muted hover:text-fg">
        <X size={12} />
      </button>
    </div>
  );
}
