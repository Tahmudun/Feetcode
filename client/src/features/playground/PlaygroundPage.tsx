import { useEffect, useRef, useState } from "react";
import { Check, Eye, Link2, Wand2 } from "lucide-react";
import { CodeEditor, type CodeEditorHandle, type EditorMarks } from "@/editor/CodeEditor";
import { engine } from "@/runtime/engine";
import { RuntimeTimeout } from "@/runtime/python";
import type { Trace } from "@/runtime/types";
import { modKey } from "@/lib/utils";
import { storage } from "@/lib/storage";
import { useSettings } from "@/store/settings";
import { useDesktop } from "@/lib/useMedia";
import { Button, Empty, Kbd, Spinner } from "@/ui/primitives";
import { SplitPane } from "@/ui/SplitPane";
import { Player } from "@/viz/Player";
import { SAMPLES } from "./samples";

// Share links carry the code in the URL hash, which the artifact build's host page owns.
const SHAREABLE = import.meta.env.MODE !== "artifact";

async function compress(text: string): Promise<string> {
  const stream = new Blob([text]).stream().pipeThrough(new CompressionStream("deflate-raw"));
  const bytes = new Uint8Array(await new Response(stream).arrayBuffer());
  let bin = "";
  bytes.forEach((b) => (bin += String.fromCharCode(b)));
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function decompress(token: string): Promise<string> {
  const bin = atob(token.replace(/-/g, "+").replace(/_/g, "/"));
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
  return new Response(stream).text();
}

export default function PlaygroundPage() {
  const [code, setCode] = useState(() => storage.get("fc:playground", SAMPLES[0].code));
  const [trace, setTrace] = useState<Trace | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [marks, setMarks] = useState<EditorMarks>({});
  const [copied, setCopied] = useState(false);
  const editor = useRef<CodeEditorHandle>(null);
  const { fontSize, vim } = useSettings();
  const desktop = useDesktop();

  useEffect(() => {
    const token = location.hash.match(/#code=([\w-]+)/)?.[1];
    if (token) decompress(token).then((c) => { setCode(c); editor.current?.setValue(c); }).catch(() => undefined);
  }, []);

  useEffect(() => {
    const t = setTimeout(() => storage.set("fc:playground", code), 400);
    return () => clearTimeout(t);
  }, [code]);

  const run = async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const res = await engine.playground(code, 2000);
      if ((res as unknown as { verdict?: string }).verdict === "compile") {
        setError(`SyntaxError on line ${res.error?.line}: ${res.error?.message}`);
        setMarks({ errorLine: res.error?.line ?? undefined });
        setTrace(null);
      } else setTrace(res);
    } catch (err) {
      setError(err instanceof RuntimeTimeout ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const share = async () => {
    const token = await compress(code);
    const url = `${location.origin}/playground#code=${token}`;
    history.replaceState(null, "", `#code=${token}`);
    await navigator.clipboard?.writeText(url).catch(() => undefined);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const left = (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-line bg-elev">
      <div className="flex shrink-0 flex-wrap items-center gap-1 border-b border-line px-2 py-1.5">
        {SAMPLES.map((s) => (
          <button
            key={s.id}
            onClick={() => { setCode(s.code); editor.current?.setValue(s.code); setTrace(null); setMarks({}); }}
            className="rounded-md px-2 py-1 text-[11.5px] text-muted hover:bg-hover hover:text-fg"
          >
            {s.name}
          </button>
        ))}
      </div>
      <CodeEditor ref={editor} value={code} onChange={setCode} onRun={() => void run()} onVisualize={() => void run()} marks={marks} fontSize={fontSize} vimMode={vim} className="min-h-0 flex-1 overflow-hidden" />
    </div>
  );

  const right = (
    <div className="h-full overflow-y-auto rounded-2xl border border-line bg-elev p-4">
      {error && <div className="mb-3 rounded-xl border border-warn/40 bg-warn-soft px-3 py-2 text-[13px] text-warn">{error}</div>}
      {trace ? (
        <>
          {trace.error && (
            <div className="mb-3 rounded-xl border border-warn/40 bg-warn-soft px-3 py-2 font-mono text-[12.5px] text-warn">
              {trace.error.type}: {trace.error.message}{trace.error.line ? ` (line ${trace.error.line})` : ""}
            </div>
          )}
          <Player key={trace.steps.length + trace.code} trace={trace} mode="debug" showCode={false} onStep={(s) => setMarks({ line: s.line, next: s.next, errorLine: trace.error?.line ?? undefined })} />
        </>
      ) : (
        <Empty icon={<Wand2 size={30} />} title="Visualize any Python">
          Write or pick a program, then press Visualize. Lists, dicts, sets, linked nodes, recursion - all drawn step by step, with
          plain-English narration of what each line did.
        </Empty>
      )}
    </div>
  );

  return (
    <div className="flex h-[calc(100dvh-52px)] flex-col gap-2 p-2">
      <header className="flex shrink-0 flex-wrap items-center gap-2 px-1">
        <Wand2 size={16} className="text-accent" />
        <h1 className="font-display text-[17px] font-bold">Playground</h1>
        <span className="hidden text-xs text-faint sm:inline">Python Tutor-style visualization for any code - runs locally in WebAssembly</span>
        <div className="ml-auto flex items-center gap-1.5">
          {SHAREABLE && (
            <Button onClick={() => void share()}>{copied ? <Check size={14} /> : <Link2 size={14} />} {copied ? "Link copied" : "Share"}</Button>
          )}
          <Button variant="primary" onClick={() => void run()} disabled={busy}>
            {busy ? <Spinner /> : <Eye size={15} />} Visualize <Kbd className="ml-1 border-accent-ink/20 bg-transparent text-accent-ink/70">{modKey()}↵</Kbd>
          </Button>
        </div>
      </header>
      {desktop ? (
        <div className="flex min-h-0 flex-1">
          <SplitPane id="playground" initial={0.42} first={left} second={right} className="flex-1" />
        </div>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col gap-2">
          <div className="h-[45%]">{left}</div>
          <div className="min-h-0 flex-1">{right}</div>
        </div>
      )}
    </div>
  );
}
