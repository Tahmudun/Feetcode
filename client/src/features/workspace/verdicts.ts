import type { Verdict } from "@/runtime/types";

export const VERDICT: Record<Verdict, { label: string; text: string; bg: string }> = {
  accepted: { label: "Accepted", text: "text-teal", bg: "bg-teal-soft" },
  wrong: { label: "Wrong Answer", text: "text-rose", bg: "bg-rose-soft" },
  error: { label: "Runtime Error", text: "text-rose", bg: "bg-rose-soft" },
  tle: { label: "Time Limit Exceeded", text: "text-accent", bg: "bg-accent-soft" },
  compile: { label: "Syntax Error", text: "text-rose", bg: "bg-rose-soft" },
};
