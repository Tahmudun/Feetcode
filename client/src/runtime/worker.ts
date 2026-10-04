/// <reference lib="webworker" />
/**
 * The Python worker. Runs Pyodide (CPython compiled to WebAssembly) off the main
 * thread so user code can never freeze the UI, and so a runaway program can be
 * killed by terminating the worker.
 *
 * The engine and problem modules are the same .py files the build pipeline
 * runs - Vite inlines them as strings and we write them into Pyodide's
 * in-memory filesystem, so browser and build always run identical code.
 */
import type { PyodideInterface } from "pyodide";
import type { WorkerRequest, WorkerResponse } from "./protocol";

declare const self: DedicatedWorkerGlobalScope;

const engineFiles = import.meta.glob("../../../engine/feetcode/*.py", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

const packageInits = import.meta.glob("../../../problems/**/__init__.py", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

const problemFiles = import.meta.glob(["../../../problems/*/*.py", "!../../../problems/**/__init__.py"], {
  query: "?raw",
  import: "default",
}) as Record<string, () => Promise<string>>;

const HOME = "/home/pyodide";
let py: PyodideInterface | null = null;
let handle: ((payload: string) => string) | null = null;
let booting: Promise<void> | null = null;
const mounted = new Set<string>();

function post(msg: WorkerResponse) {
  self.postMessage(msg);
}

function writeFile(rel: string, source: string) {
  const path = `${HOME}/${rel}`;
  py!.FS.mkdirTree(path.slice(0, path.lastIndexOf("/")));
  py!.FS.writeFile(path, source);
}

const relFromGlob = (key: string) => key.replace(/^(\.\.\/)+/, "");

async function boot() {
  const t0 = performance.now();
  post({ type: "status", status: "loading", detail: "Downloading Python (WebAssembly)…" });
  const root = new URL(`${import.meta.env.BASE_URL}pyodide/v${__PYODIDE_VERSION__}/`, self.location.origin).href;
  const mod = (await import(/* @vite-ignore */ `${root}pyodide.mjs`)) as typeof import("pyodide");
  py = await mod.loadPyodide({ indexURL: root });
  post({ type: "status", status: "loading", detail: "Mounting the Feetcode engine…" });
  for (const [key, src] of Object.entries(engineFiles)) writeFile(relFromGlob(key).replace(/^engine\//, ""), src);
  for (const [key, src] of Object.entries(packageInits)) writeFile(relFromGlob(key), src);
  py.runPython(`import sys\nif "${HOME}" not in sys.path: sys.path.insert(0, "${HOME}")`);
  const api = py.pyimport("feetcode.api");
  handle = (payload: string) => api.handle(payload) as string;
  const version = JSON.parse(handle(JSON.stringify({ op: "ping" }))).data.version as string;
  post({
    type: "status",
    status: "ready",
    detail: `Python ${py.runPython("import sys; sys.version.split()[0]")} · engine ${version}`,
    ms: Math.round(performance.now() - t0),
  });
}

async function mount(module: string) {
  if (mounted.has(module)) return;
  const rel = module.replace(/\./g, "/") + ".py";
  const loader = problemFiles[`../../../${rel}`];
  if (!loader) throw new Error(`unknown problem module ${module}`);
  writeFile(rel, await loader());
  mounted.add(module);
}

self.onmessage = async (event: MessageEvent<WorkerRequest>) => {
  const req = event.data;
  try {
    booting ??= boot();
    await booting;
    if (req.type === "init") {
      post({ type: "result", id: req.id, ok: true, payload: "" });
      return;
    }
    if (req.module) await mount(req.module);
    const out = handle!(req.payload);
    post({ type: "result", id: req.id, ok: true, payload: out });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (!handle) post({ type: "status", status: "error", detail: message });
    post({ type: "result", id: req.id, ok: false, payload: message });
  }
};
