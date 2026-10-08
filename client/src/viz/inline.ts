/**
 * Inline values: what the editor prints at the end of each line while you step through
 * a trace, the way a debugger does. A pure function of (trace, step index), like the
 * scene builder: no history is kept, so scrubbing anywhere is free.
 *
 * For every line the current call has run so far, show the current values of the names
 * that line assigns:
 *     l = best = 0                ->  l = 1, best = 2
 *     for r, c in enumerate(s):   ->  r = 3, c = 't'
 *     seen[c] = r                 ->  seen = {'t': 0, 'm': 2}
 * and on the line that just ran, the outcome of a branch (`→ True`) or the value returned.
 */
import type { Trace } from "@/runtime/types";
import { pyRepr } from "./decode";

const IDENT = /^[A-Za-z_][A-Za-z0-9_]*/;
const MAX_VALUE = 34;
const MAX_LINE = 72;

/** Strip a trailing `# comment` (ignoring `#` inside string literals). */
function stripComment(line: string): string {
  let quote: string | null = null;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (quote) {
      if (ch === "\\") i++;
      else if (ch === quote) quote = null;
    } else if (ch === "'" || ch === '"') quote = ch;
    else if (ch === "#") return line.slice(0, i);
  }
  return line;
}

/** The base variable names an assignment target refers to: `seen[c]` -> seen, `(a, *b)` -> a, b. */
function targetNames(target: string): string[] {
  let t = target.trim();
  if ((t.startsWith("(") && t.endsWith(")")) || (t.startsWith("[") && t.endsWith("]"))) t = t.slice(1, -1);
  const names: string[] = [];
  let depth = 0;
  let part = "";
  const flush = () => {
    const m = part.trim().replace(/^[(*\s]+/, "").match(IDENT);
    if (m && m[0] !== "self" && m[0] !== "_") names.push(m[0]);
    part = "";
  };
  for (const ch of t) {
    if ("([{".includes(ch)) depth++;
    else if (")]}".includes(ch)) depth--;
    if (ch === "," && depth === 0) flush();
    else part += ch;
  }
  flush();
  return names;
}

/** Names a line of Python assigns, in source order. Conservative: when unsure, nothing. */
export function assignedNames(source: string): string[] {
  const line = stripComment(source).trim();
  if (!line) return [];
  const loop = line.match(/^(?:async\s+)?for\s+(.+?)\s+in\s/);
  if (loop) return targetNames(loop[1]);
  if (/^(def|class|return|if|elif|else|while|try|except|finally|import|from|raise|assert|pass|break|continue|yield|del|global|nonlocal|lambda)\b/.test(line)) {
    const walrus = [...line.matchAll(/([A-Za-z_]\w*)\s*:=/g)].map((m) => m[1]);
    return walrus;
  }
  const withAs = line.match(/^with\s.+\bas\s+([A-Za-z_]\w*)/);
  if (withAs) return [withAs[1]];

  // Split on top-level `=` (not ==, <=, >=, !=), keeping augmented ops (+=, //=, ...) as assignments.
  const targets: string[] = [];
  let depth = 0;
  let quote: string | null = null;
  let start = 0;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (quote) {
      if (ch === "\\") i++;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === "'" || ch === '"') quote = ch;
    else if ("([{".includes(ch)) depth++;
    else if (")]}".includes(ch)) depth--;
    else if (ch === "=" && depth === 0) {
      const prev = line[i - 1] ?? "";
      const next = line[i + 1] ?? "";
      if (next === "=" || "=!<>".includes(prev) && !/(<<|>>)$/.test(line.slice(i - 2, i))) {
        if (next === "=") i++;
        continue;
      }
      targets.push(line.slice(start, i).replace(/(\*\*|\/\/|>>|<<|[-+*/%&|^@])$/, ""));
      start = i + 1;
    }
  }
  const seen = new Set<string>();
  return targets.flatMap(targetNames).filter((n) => !seen.has(n) && (seen.add(n), true));
}

function short(text: string, limit = MAX_VALUE): string {
  return text.length <= limit ? text : `${text.slice(0, limit - 1)}…`;
}

/** {line: "l = 1, best = 2"} for the editor at step `index` of `trace`. */
export function inlineValues(trace: Trace, index: number): Record<number, string> {
  const step = trace.steps[index];
  if (!step || !step.s.length) return {};
  const frame = step.s[step.s.length - 1];
  const locals = new Map(frame.v);
  const lines = trace.code.split("\n");
  const ran = new Set<number>();
  for (let i = 0; i <= index; i++) {
    const s = trace.steps[i];
    const f = s.s[s.s.length - 1];
    if (f && f.id === frame.id && s.k !== "call") ran.add(s.l);
  }
  const out: Record<number, string> = {};
  for (const ln of ran) {
    const names = assignedNames(lines[ln - 1] ?? "");
    const parts = names.filter((n) => locals.has(n)).map((n) => `${n} = ${short(pyRepr(locals.get(n), step.h, 2))}`);
    if (parts.length) out[ln] = short(parts.join(", "), MAX_LINE);
  }
  if (step.k === "return" && step.r !== undefined) {
    out[step.l] = short(`returns ${pyRepr(step.r, step.h, 2)}`, MAX_LINE);
  } else if (step.b !== undefined) {
    const code = (lines[step.l - 1] ?? "").trim();
    if (/^(if|elif|while)\b/.test(code)) out[step.l] = step.b ? "→ True" : "→ False";
    else if (/^for\b/.test(code) && step.b === 0) out[step.l] = "loop done";
  }
  return out;
}
