import type { SessionItem, SessionKind } from "@/store/session";

type Tone = "note" | "warn" | "accent" | "sky";

/** How each kind of session item is named and colored (meaning first: see the palette notes in index.css). */
export const KINDS: Record<SessionKind, { label: string; tone: Tone; verb: string }> = {
  recall: { label: "Recall", tone: "note", verb: "Review" },
  fix: { label: "Fix", tone: "warn", verb: "Fix" },
  new: { label: "New", tone: "accent", verb: "Solve" },
  stretch: { label: "Stretch", tone: "sky", verb: "Try" },
};

/** Where an item is done: recall cards live on the review page, everything else in the workspace. */
export const itemHref = (it: Pick<SessionItem, "kind" | "p">) => (it.kind === "recall" ? "/review" : `/problems/${it.p}`);
