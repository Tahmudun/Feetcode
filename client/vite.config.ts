import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..");
const pyodideDir = path.resolve(here, "node_modules/pyodide");
const PYODIDE_FILES = ["pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"];
const pyodideVersion = JSON.parse(fs.readFileSync(path.join(pyodideDir, "package.json"), "utf8")).version;

/**
 * Self-host Pyodide (Python compiled to WebAssembly) instead of using a CDN:
 * version-pinned, works offline once cached, no third-party runtime dependency.
 * Dev: serve /pyodide/* straight from node_modules. Build: copy into dist/pyodide/.
 */
function selfHostPyodide(artifact: boolean): Plugin {
  return {
    name: "feetcode:self-host-pyodide",
    configureServer(server) {
      server.middlewares.use(`/pyodide/v${pyodideVersion}/`, (req, res, next) => {
        const file = (req.url ?? "").split("?")[0].replace(/^\//, "");
        if (!PYODIDE_FILES.includes(file)) return next();
        const type = file.endsWith(".wasm") ? "application/wasm" : file.endsWith(".mjs") ? "text/javascript"
          : file.endsWith(".json") ? "application/json" : "application/zip";
        res.setHeader("Content-Type", type);
        fs.createReadStream(path.join(pyodideDir, file)).pipe(res);
      });
    },
    generateBundle() {
      for (const file of PYODIDE_FILES) {
        const source = fs.readFileSync(path.join(pyodideDir, file));
        if (artifact && file.endsWith(".zip")) {
          // Artifact hosts don't serve archives, so ship the standard library's bytes as base64 JSON;
          // the worker turns them back into a blob: URL for loadPyodide({ stdLibURL }).
          const fileName = `pyodide/v${pyodideVersion}/${file.replace(/\.zip$/, ".json")}`;
          this.emitFile({ type: "asset", fileName, source: JSON.stringify({ zip: source.toString("base64") }) });
          continue;
        }
        // Versioned path: the files can be cached forever, and upgrades can't mix versions.
        this.emitFile({ type: "asset", fileName: `pyodide/v${pyodideVersion}/${file}`, source });
      }
    },
  };
}

/**
 * `vite build --mode artifact`: a build that works from any URL path (relative asset base + hash routing),
 * with index.html reduced to the fragment a claude.ai Artifact page expects (the host adds the document
 * skeleton, charset and viewport). The regular build is untouched.
 */
function artifactPage(): Plugin {
  return {
    name: "feetcode:artifact-page",
    transformIndexHtml: {
      order: "post",
      handler(html) {
        const head = /<head>([\s\S]*)<\/head>/.exec(html)?.[1] ?? "";
        const body = /<body>([\s\S]*)<\/body>/.exec(html)?.[1] ?? "";
        const kept = head
          .replace(/<meta (charset|name="viewport"|name="theme-color")[^>]*>\s*/g, "")
          .replace(/<link rel="icon"[^>]*>\s*/g, "")
          .replace(/<title>[\s\S]*?<\/title>/, "");
        return `<title>Feetcode</title>\n${kept.trim()}\n${body.trim()}\n`;
      },
    },
  };
}

export default defineConfig(({ mode }) => ({
  base: mode === "artifact" ? "./" : "/",
  plugins: [react(), tailwindcss(), selfHostPyodide(mode === "artifact"), mode === "artifact" && artifactPage()],
  resolve: { alias: { "@": path.resolve(here, "src") } },
  define: { __PYODIDE_VERSION__: JSON.stringify(pyodideVersion) },
  server: { fs: { allow: [repoRoot] } },
  worker: { format: "es" },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 900,
    outDir: mode === "artifact" ? "dist-artifact" : "dist",
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
}));
