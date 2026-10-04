import { useCallback, useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { storage } from "@/lib/storage";

/** Two panes with a draggable divider; the split ratio is remembered per id. */
export function SplitPane({
  id, direction = "horizontal", initial = 0.5, min = 0.2, max = 0.8, first, second, className,
}: {
  id: string;
  direction?: "horizontal" | "vertical";
  initial?: number;
  min?: number;
  max?: number;
  first: ReactNode;
  second: ReactNode;
  className?: string;
}) {
  const [ratio, setRatio] = useState(() => storage.get(`fc:split:${id}`, initial));
  const [dragging, setDragging] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const horizontal = direction === "horizontal";

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      setDragging(true);
      const rect = box.current!.getBoundingClientRect();
      let latest = ratio;
      const move = (ev: PointerEvent) => {
        const r = horizontal ? (ev.clientX - rect.left) / rect.width : (ev.clientY - rect.top) / rect.height;
        latest = Math.max(min, Math.min(max, r));
        setRatio(latest);
      };
      const up = () => {
        setDragging(false);
        storage.set(`fc:split:${id}`, latest);
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerup", up);
      };
      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up);
    },
    [horizontal, id, max, min, ratio],
  );

  return (
    <div ref={box} className={cn("flex h-full min-h-0 min-w-0", horizontal ? "flex-row" : "flex-col", dragging && "select-none", className)}>
      <div className="min-h-0 min-w-0 overflow-hidden" style={{ flexBasis: `${ratio * 100}%`, flexShrink: 0, flexGrow: 0 }}>
        {first}
      </div>
      <div
        role="separator"
        aria-orientation={horizontal ? "vertical" : "horizontal"}
        tabIndex={0}
        onPointerDown={onPointerDown}
        onKeyDown={(e) => {
          const step = e.key === "ArrowLeft" || e.key === "ArrowUp" ? -0.03 : e.key === "ArrowRight" || e.key === "ArrowDown" ? 0.03 : 0;
          if (step) {
            const r = Math.max(min, Math.min(max, ratio + step));
            setRatio(r);
            storage.set(`fc:split:${id}`, r);
          }
        }}
        className={cn(
          "group relative z-10 flex shrink-0 items-center justify-center",
          horizontal ? "w-2 cursor-col-resize" : "h-2 cursor-row-resize",
        )}
      >
        <div
          className={cn(
            "rounded-full bg-line transition-colors group-hover:bg-accent group-focus-visible:bg-accent",
            horizontal ? "h-10 w-[3px]" : "h-[3px] w-10",
            dragging && "bg-accent",
          )}
        />
      </div>
      <div className="min-h-0 min-w-0 flex-1 overflow-hidden">{second}</div>
    </div>
  );
}
