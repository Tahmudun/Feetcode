/**
 * Turning analyzer output into footnotes (the Footnote Law: every finding is anchored
 * to a line). Pure functions, no React: what the editor pins under the guilty line and
 * what the analysis panel says must read the same, so both come from here.
 *
 * Footnotes state facts, never fixes: "your l became 1 here; the reference's is 2", and
 * the invariant it broke. The fix stays the user's to find (hints exist for that).
 */
import type { EditorFootnote } from "@/editor/CodeEditor";
import type { Divergence } from "@/runtime/types";

/** Kinds that point at a specific step worth showing. */
export function hasPoint(d: Divergence | null | undefined): d is Divergence & { step: number; line: number } {
  return !!d && d.step !== null && d.line !== null && !["agree", "unknown"].includes(d.kind);
}

export interface Finding {
  title: string;
  body: string;
  invariant?: string;
}

export function describeDivergence(d: Divergence, pitfallTitle?: string): Finding | null {
  if (!hasPoint(d)) return null;
  const at = `At step ${d.step + 1}`;
  const inv = d.invariant && d.invariant.step === d.step ? d.invariant : null;
  const invText = inv
    ? `In all ${inv.runs} reference runs we tried, ${inv.text}; here yours goes ${inv.before} → ${inv.after}.`
    : undefined;
  switch (d.kind) {
    case "value":
      return {
        title: pitfallTitle ?? (inv ? `Breaks "${inv.text}"` : `${d.var} takes a value the reference never does`),
        body: `${at}, your ${d.var} became ${d.yours}; at the same point the reference's ${d.var} is ${d.ref}.`,
        invariant: invText,
      };
    case "extra":
      return {
        title: pitfallTitle ?? (inv ? `Breaks "${inv.text}"` : `${d.var} changes when the reference's doesn't`),
        body: `${at}, your ${d.var} became ${d.yours}; the reference's ${d.var} stays ${d.ref}.`,
        invariant: invText,
      };
    case "missing":
      return {
        title: pitfallTitle ?? `The reference updates ${d.var} here; yours doesn't`,
        body: `Up to step ${d.step + 1} your run matches the reference. Then the reference's ${d.var} becomes ${d.ref}, while yours stays ${d.yours}.`,
      };
    case "return":
      return {
        title: pitfallTitle ?? `Returns ${d.yours}; the reference returns ${d.ref}`,
        body: `Your run agrees with the reference on ${list(d.shared)} all the way here, then returns ${d.yours}. The reference returns ${d.ref}.`,
      };
    case "error":
      return {
        title: `${d.yours} on this line`,
        body: `Your run agrees with the reference on ${list(d.shared)} until this line raises ${d.yours}.`,
      };
    default:
      return null;
  }
}

function list(names: string[]): string {
  if (!names.length) return "every variable";
  if (names.length === 1) return names[0];
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

export const FOOTNOTE_ACTIONS = { jump: "jump", compare: "compare" } as const;

/** The note pinned under the line where your run first disagrees with the reference. */
export function divergenceFootnote(d: Divergence | null | undefined, pitfallTitle?: string): EditorFootnote | undefined {
  if (!hasPoint(d)) return undefined;
  const f = describeDivergence(d, pitfallTitle);
  if (!f) return undefined;
  return {
    line: d.line,
    n: 1,
    title: f.title,
    body: f.invariant ? `${f.body} ${f.invariant}` : f.body,
    actions: [
      { id: FOOTNOTE_ACTIONS.jump, label: `Show step ${d.step + 1}` },
      { id: FOOTNOTE_ACTIONS.compare, label: "Compare with the reference" },
    ],
  };
}
