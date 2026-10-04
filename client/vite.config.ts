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
function selfHostPyodide(): Plugin {
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
        // Versioned path: the files can be cached forever, and upgrades can't mix versions.
        this.emitFile({ type: "asset", fileName: `pyodide/v${pyodideVersion}/${file}`, source: fs.readFileSync(path.join(pyodideDir, file)) });
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), selfHostPyodide()],
  resolve: { alias: { "@": path.resolve(here, "src") } },
  define: { __PYODIDE_VERSION__: JSON.stringify(pyodideVersion) },
  server: { fs: { allow: [repoRoot] } },
  worker: { format: "es" },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 900,
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
