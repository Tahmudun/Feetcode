/** Reading engine snapshots: encoded values + heap -> display strings and structure. */
import type { Heap, HeapObj, PyVal } from "@/runtime/types";

export const isRef = (v: PyVal | undefined): v is { r: number } => typeof v === "object" && v !== null && "r" in v;

export function deref(heap: Heap, v: PyVal | undefined): HeapObj | undefined {
  return isRef(v) ? heap[String(v.r)] : undefined;
}

export function isScalar(v: PyVal | undefined): boolean {
  return !isRef(v);
}

export function isNumber(v: PyVal | undefined): v is number {
  return typeof v === "number";
}

/** Numeric value of a scalar, if it has one (ints, floats, bools). */
export function num(v: PyVal | undefined): number | null {
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  if (v && typeof v === "object" && "f" in v) {
    const f = v.f;
    if (f === "inf") return Infinity;
    if (f === "-inf") return -Infinity;
    const x = Number(f);
    return Number.isNaN(x) ? null : x;
  }
  return null;
}

export function scalarText(v: PyVal | undefined, quoteStrings = true): string {
  if (v === undefined) return "";
  if (v === null) return "None";
  if (v === true) return "True";
  if (v === false) return "False";
  if (typeof v === "number") return String(v);
  if (typeof v === "string") return quoteStrings ? `'${v}'` : v;
  if ("f" in v) return v.f === "inf" ? "∞" : v.f === "-inf" ? "-∞" : v.f;
  if ("big" in v) return v.big.length > 14 ? `${v.big.slice(0, 6)}…${v.big.slice(-4)}` : v.big;
  if ("fn" in v) return `ƒ ${v.fn}`;
  if ("repr" in v) return v.repr;
  return "?";
}

export function isNodeObj(obj: HeapObj | undefined): boolean {
  return !!obj && obj[0] === "obj" && obj[2].some(([k]) => k === "next" || k === "prev");
}

export function field(obj: HeapObj | undefined, name: string): PyVal | undefined {
  if (!obj || obj[0] !== "obj") return undefined;
  return obj[2].find(([k]) => k === name)?.[1];
}

/** Python-like repr with depth and length limits (cycles are impossible to blow up: depth-bounded). */
export function pyRepr(v: PyVal | undefined, heap: Heap, depth = 3, quote = true): string {
  if (!isRef(v)) return scalarText(v, quote);
  const obj = heap[String(v.r)];
  if (!obj) return "…";
  if (depth <= 0) return obj[0] === "obj" ? `${obj[1]}(…)` : "[…]";
  const kind = obj[0];
  if (kind === "obj") {
    if (isNodeObj(obj)) {
      const val = field(obj, "val") ?? field(obj, "key");
      return `node(${scalarText(val)})`;
    }
    const fields = obj[2].slice(0, 4).map(([k, x]) => `${k}=${pyRepr(x, heap, depth - 1)}`);
    return `${obj[1]}(${fields.join(", ")}${obj[2].length > 4 ? ", …" : ""})`;
  }
  if (kind === "dict") {
    const body = obj[1].slice(0, 8).map(([k, x]) => `${pyRepr(k, heap, depth - 1)}: ${pyRepr(x, heap, depth - 1)}`);
    const more = obj[1].length > 8 || (obj[2] ?? 0) > obj[1].length ? ", …" : "";
    return `{${body.join(", ")}${more}}`;
  }
  const items = obj[1];
  const shown = items.slice(0, 12).map((x) => pyRepr(x, heap, depth - 1));
  const more = items.length > 12 || (obj[2] ?? 0) > items.length ? ", …" : "";
  if (kind === "tuple") return `(${shown.join(", ")}${items.length === 1 ? "," : ""}${more})`;
  if (kind === "set") return items.length ? `{${shown.join(", ")}${more}}` : "set()";
  if (kind === "deque") return `deque([${shown.join(", ")}${more}])`;
  return `[${shown.join(", ")}${more}]`;
}

/** Compact signature for a 26-slot letter-count tuple: (1,0,0,…,1) -> "a1e1t1". */
export function letterCounts(v: PyVal | undefined, heap: Heap): string | null {
  const obj = deref(heap, v);
  if (!obj || obj[0] !== "tuple" || obj[1].length !== 26) return null;
  const parts: string[] = [];
  obj[1].forEach((c, i) => {
    if (typeof c === "number" && c > 0) parts.push(`${String.fromCharCode(97 + i)}${c}`);
  });
  return parts.join("") || "∅";
}

export function length(obj: HeapObj): number {
  if (obj[0] === "obj") return obj[2].length;
  return (obj[0] === "dict" ? obj[2] : obj[2]) ?? obj[1].length;
}
