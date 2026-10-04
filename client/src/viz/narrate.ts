/**
 * Automatic narration for code nobody annotated (yours). Built from the same
 * facts the scene uses: branch outcomes, recorded accesses and the snapshot
 * diff - so it describes what the line actually did, not what it says.
 */
import type { Access, PyVal, Step } from "@/runtime/types";
import { field, isRef, pyRepr, scalarText } from "./decode";

function varMap(step: Step | undefined, frameId: number) {
  const f = step?.s.find((x) => x.id === frameId);
  return new Map<string, PyVal>(f?.v ?? []);
}

/** A readable name for the container an access touched: `grid`, or `grid[2]` for a nested row. */
function nameOf(a: Access, step: Step): string {
  if (a.v) return a.v;
  const top = step.s[step.s.length - 1];
  const direct = top?.v.find(([, v]) => isRef(v) && v.r === a.o);
  if (direct) return direct[0];
  for (const [name, v] of top?.v ?? []) {
    if (!isRef(v)) continue;
    const obj = step.h[String(v.r)];
    if (!obj || obj[0] === "obj" || obj[0] === "dict") continue;
    const i = obj[1].findIndex((x) => isRef(x) && x.r === a.o);
    if (i >= 0) return `${name}[${i}]`;
  }
  return "a container";
}

export function describeLine(code: string): "if" | "while" | "for" | "other" {
  const t = code.trim();
  if (/^(if|elif)\b/.test(t)) return "if";
  if (/^while\b/.test(t)) return "while";
  if (/^for\b/.test(t)) return "for";
  return "other";
}

export function autoNarrate(steps: Step[], index: number, codeLines: string[]): string {
  const step = steps[index];
  const prev = index > 0 ? steps[index - 1] : undefined;
  const top = step.s[step.s.length - 1];
  const heap = step.h;
  if (step.k === "call" && top) {
    const args = top.v.filter(([n]) => n !== "self").map(([n, v]) => `${n}=${pyRepr(v, heap, 1)}`).join(", ");
    return `Call ${top.f}(${args})`;
  }
  if (step.k === "return") return `${top?.f ?? "function"} returns ${pyRepr(step.r, heap, 2)}`;
  if (step.k === "exc") return `💥 ${step.x}`;

  const parts: string[] = [];
  const code = codeLines[step.l - 1] ?? "";
  const kind = describeLine(code);
  if (step.b !== undefined) {
    if (kind === "for") parts.push(step.b ? "next iteration" : "loop finished");
    else if (kind === "while") parts.push(step.b ? "condition holds → loop body" : "condition false → leave loop");
    else parts.push(step.b ? "condition is True → enter branch" : "condition is False → skip");
  }
  for (const a of step.a ?? []) {
    const name = nameOf(a, step);
    if (a.f) {
      const target = top?.v.find(([, v]) => isRef(v) && v.r === a.o);
      const obj = heap[String(a.o)];
      parts.push(`${target?.[0] ?? `node(${scalarText(field(obj, "val"))})`}.${a.f} → ${pyRepr(field(obj, a.f), heap, 1)}`);
    } else if (a.m === "c" && a.i !== undefined) parts.push(`compare ${name}[${a.i}]`);
    else if (a.m === "in") parts.push(`${a.kr} in ${name}? ${a.hit ? "yes" : "no"}`);
    else if (a.m === "push") parts.push(`push onto ${name}`);
    else if (a.m === "pop") parts.push(`pop from ${name}`);
    else if (a.m === "w" && a.kr) parts.push(`${name}[${a.kr}] ${a.ei === -1 ? "added" : "updated"}`);
    else if (a.oob) parts.push(`index ${a.i} is outside ${name} (length ${a.i !== undefined ? "≤ " + a.i : "?"})`);
  }
  if (top) {
    const before = varMap(prev, top.id);
    for (const [n, v] of top.v) {
      if (n === "self" || isRef(v)) continue;
      const old = before.get(n);
      if (!before.has(n)) parts.push(`${n} = ${scalarText(v)}`);
      else if (scalarText(old) !== scalarText(v)) parts.push(`${n}: ${scalarText(old)} → ${scalarText(v)}`);
    }
  }
  const unique = [...new Set(parts)];
  if (!unique.length) return code.trim() ? `ran \`${code.trim().slice(0, 60)}\`` : "";
  return unique.slice(0, 4).join(" · ");
}
