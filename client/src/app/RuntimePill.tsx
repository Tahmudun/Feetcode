import { useRuntime } from "@/runtime/python";
import { cn } from "@/lib/utils";
import { Spinner } from "@/ui/primitives";

/** Where Python is at: downloading, ready, running your code, or broken. */
export function RuntimePill() {
  const { status, detail, bootMs } = useRuntime();
  const label = {
    idle: "Python idle",
    loading: "Python loading",
    ready: "Python ready",
    busy: "Running",
    error: "Python failed",
  }[status];
  const title = status === "ready" && bootMs ? `${detail} · booted in ${(bootMs / 1000).toFixed(1)}s` : detail || label;
  return (
    <div
      title={title}
      className={cn(
        "hidden h-8 items-center gap-2 rounded-lg px-2.5 text-xs font-medium lg:flex",
        status === "error" ? "text-rose" : "text-muted",
      )}
    >
      {status === "loading" || status === "busy" ? (
        <Spinner className="text-accent" />
      ) : (
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            status === "ready" ? "bg-teal shadow-[0_0_8px_var(--teal)]" : status === "error" ? "bg-rose" : "bg-faint",
          )}
        />
      )}
      {label}
    </div>
  );
}
