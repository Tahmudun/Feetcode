import { useEffect, useState } from "react";
import type { ProblemDetail } from "@/content/types";
import { storage } from "@/lib/storage";

export function NotesTab({ problem }: { problem: ProblemDetail }) {
  const key = `fc:notes:${problem.id}`;
  const [text, setText] = useState(() => storage.get(key, ""));
  useEffect(() => {
    const t = setTimeout(() => storage.set(key, text), 300);
    return () => clearTimeout(t);
  }, [key, text]);
  return (
    <div className="flex h-full flex-col gap-3 p-5">
      <div>
        <h2 className="text-sm font-semibold">Your notes</h2>
        <p className="text-xs text-faint">
          Write the trick in your own words - explaining it is the fastest way to own it. Saved in this browser.
        </p>
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={`e.g. "${problem.insight.mnemonic}"\n\nWhat tripped me up: …\nThe key invariant: …`}
        className="min-h-64 flex-1 resize-none rounded-xl border border-line bg-inset p-3.5 font-mono text-[13px] leading-relaxed text-fg outline-none placeholder:text-faint focus:border-accent/50"
      />
    </div>
  );
}
