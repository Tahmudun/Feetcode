import type { Verdict } from "@/runtime/types";

export const VERDICT: Record<Verdict, { label: string; text: string; bg: string }> = {
  accepted: { label: "Accepted", text: "text-ref", bg: "bg-ref-soft" },
  wrong: { label: "Wrong Answer", text: "text-warn", bg: "bg-warn-soft" },
  error: { label: "Runtime Error", text: "text-warn", bg: "bg-warn-soft" },
  tle: { label: "Time Limit Exceeded", text: "text-accent", bg: "bg-accent-soft" },
  compile: { label: "Syntax Error", text: "text-warn", bg: "bg-warn-soft" },
};
