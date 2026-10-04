/** LeetCode-style literals for showing inputs and outputs: [1, 2], "abc", true, null. */
export function lit(v: unknown, limit = 400): string {
  const s = render(v);
  return s.length > limit ? `${s.slice(0, limit - 1)}…` : s;
}

function render(v: unknown): string {
  if (v === null || v === undefined) return "null";
  if (typeof v === "string") return JSON.stringify(v);
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (Array.isArray(v)) return `[${v.map(render).join(", ")}]`;
  if (typeof v === "object") {
    const o = v as Record<string, unknown>;
    if ("f" in o && Object.keys(o).length === 1) return String(o.f);
    return `{${Object.entries(o).map(([k, x]) => `${JSON.stringify(k)}: ${render(x)}`).join(", ")}}`;
  }
  return String(v);
}

/** Size of an input for display ("size 3,000"). */
export function sizeOf(v: unknown): number {
  if (Array.isArray(v)) return v.length;
  if (typeof v === "string") return v.length;
  return 0;
}

export function deepEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}
