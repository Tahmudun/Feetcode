import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { Difficulty } from "@/content/types";

type Variant = "primary" | "secondary" | "ghost" | "success" | "danger";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-accent text-accent-ink hover:bg-accent-strong shadow-[0_6px_20px_-8px_var(--accent)] font-semibold",
  secondary: "bg-elev-2 text-fg border border-line hover:border-line-strong hover:bg-hover",
  ghost: "text-muted hover:text-fg hover:bg-hover",
  success: "bg-ref text-ref-ink hover:brightness-110 font-semibold shadow-[0_6px_20px_-8px_var(--ref)]",
  danger: "bg-warn-soft text-warn border border-warn/40 hover:bg-warn/20",
};
const SIZES: Record<Size, string> = {
  sm: "h-7 px-2.5 text-xs gap-1.5 rounded-md",
  md: "h-8 px-3 text-[13px] gap-2 rounded-lg",
  lg: "h-10 px-4 text-sm gap-2 rounded-xl",
};

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }>(
  function Button({ variant = "secondary", size = "md", className, ...props }, ref) {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap transition-all duration-150 select-none",
          "disabled:opacity-45 active:scale-[0.97]",
          VARIANTS[variant],
          SIZES[size],
          className,
        )}
        {...props}
      />
    );
  },
);

export function IconButton({ label, className, children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-hover hover:text-fg disabled:opacity-40",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

const DIFF: Record<Difficulty, string> = {
  Easy: "text-ref bg-ref-soft",
  Medium: "text-note bg-note-soft",
  Hard: "text-warn bg-warn-soft",
};

export function DifficultyBadge({ value, className }: { value: Difficulty; className?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold", DIFF[value], className)}>
      {value}
    </span>
  );
}

export function Chip({ children, className, tone = "neutral" }: { children: ReactNode; className?: string; tone?: "neutral" | "accent" | "ref" | "warn" | "note" | "sky" }) {
  const tones = {
    neutral: "bg-elev-2 text-muted border-line",
    accent: "bg-accent-soft text-accent border-accent/30",
    ref: "bg-ref-soft text-ref border-ref/30",
    warn: "bg-warn-soft text-warn border-warn/30",
    note: "bg-note-soft text-note border-note/30",
    sky: "bg-sky-soft text-sky border-sky/30",
  };
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium", tones[tone], className)}>
      {children}
    </span>
  );
}

export function Kbd({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <kbd
      className={cn(
        "inline-flex h-5 min-w-5 items-center justify-center rounded border border-line border-b-2 bg-elev-2 px-1 font-mono text-[10px] text-muted",
        className,
      )}
    >
      {children}
    </kbd>
  );
}

export function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("rounded-2xl border border-line bg-elev shadow-panel", className)}>{children}</div>;
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cn("inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-r-transparent", className)}
      aria-hidden
    />
  );
}

export function ProgressRing({ value, size = 40, stroke = 4, tone = "var(--accent)", children }: {
  value: number; size?: number; stroke?: number; tone?: string; children?: ReactNode;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={tone}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - Math.max(0, Math.min(1, value)))}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      {children && <div className="absolute inset-0 flex items-center justify-center">{children}</div>}
    </div>
  );
}

export function Tabs<T extends string>({ tabs, value, onChange, className, size = "md" }: {
  tabs: { id: T; label: ReactNode; badge?: ReactNode }[];
  value: T;
  onChange: (id: T) => void;
  className?: string;
  size?: "sm" | "md";
}) {
  return (
    <div role="tablist" className={cn("flex items-center gap-0.5", className)}>
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={value === t.id}
          onClick={() => onChange(t.id)}
          className={cn(
            "relative inline-flex items-center gap-1.5 rounded-lg font-medium transition-colors",
            size === "sm" ? "h-7 px-2.5 text-xs" : "h-8 px-3 text-[13px]",
            value === t.id ? "bg-elev-2 text-fg shadow-[inset_0_0_0_1px_var(--border)]" : "text-muted hover:text-fg hover:bg-hover/60",
          )}
        >
          {t.label}
          {t.badge}
        </button>
      ))}
    </div>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("wordmark text-[17px] text-fg", className)}>
      feetcode<sup>1</sup>
    </span>
  );
}

export function Empty({ icon, title, children }: { icon?: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center">
      {icon && <div className="mb-1 text-faint">{icon}</div>}
      <div className="text-sm font-semibold text-fg">{title}</div>
      {children && <div className="max-w-sm text-[13px] text-muted">{children}</div>}
    </div>
  );
}
