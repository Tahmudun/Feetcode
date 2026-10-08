/**
 * Run the engine's pytest suite inside Pyodide (CPython compiled to WebAssembly)
 * under Node - the same runtime the browser uses. Proves the engine behaves
 * identically in CPython (pytest) and in WebAssembly.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadPyodide } from "pyodide";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const py = await loadPyodide();

function mount(src, dst) {
  py.FS.mkdirTree(dst);
  for (const name of fs.readdirSync(src)) {
    const full = path.join(src, name);
    if (fs.statSync(full).isDirectory()) {
      if (name !== "__pycache__") mount(full, `${dst}/${name}`);
    } else if (name.endsWith(".py")) {
      py.FS.writeFile(`${dst}/${name}`, fs.readFileSync(full, "utf8"));
    }
  }
}
mount(path.join(root, "engine/feetcode"), "/home/pyodide/feetcode");
mount(path.join(root, "problems"), "/home/pyodide/problems");
mount(path.join(root, "engine/tests"), "/home/pyodide/tests");

// A minimal stand-in for the two pytest features the suite uses.
py.FS.writeFile("/home/pyodide/tests/pytest.py", `
import contextlib
class _Mark:
    def __init__(self, name, args): self.name, self.args = name, args
class mark:
    @staticmethod
    def parametrize(names, values):
        def deco(fn):
            fn.pytestmark = getattr(fn, "pytestmark", []) + [_Mark("parametrize", (names, values))]
            return fn
        return deco
@contextlib.contextmanager
def raises(exc):
    try:
        yield
    except exc:
        return
    raise AssertionError(f"did not raise {exc}")
`);

const started = Date.now();
const report = JSON.parse(py.runPython(`
import importlib, json, os, sys
sys.path.insert(0, "/home/pyodide/tests")
results = []
# Every test module, so a new one can never be silently skipped in WebAssembly.
modules = sorted(f[:-3] for f in os.listdir("/home/pyodide/tests") if f.startswith("test_") and f.endswith(".py"))
for modname in modules:
    mod = importlib.import_module(modname)
    for name in sorted(dir(mod)):
        fn = getattr(mod, name)
        if not name.startswith("test_") or not callable(fn):
            continue
        params = next((m.args[1] for m in getattr(fn, "pytestmark", []) if m.name == "parametrize"), None)
        cases = params if params is not None else [None]
        for case in cases:
            label = name if case is None else f"{name}[{case[0] if isinstance(case, tuple) else case}]"
            try:
                if case is None:
                    fn()
                elif isinstance(case, tuple):
                    fn(*case)
                else:
                    fn(case)
                results.append([label, None])
            except Exception as e:
                results.append([label, f"{type(e).__name__}: {e}"[:300]])
json.dumps({"python": sys.version.split()[0], "results": results})
`));

const failed = report.results.filter(([, err]) => err);
for (const [name, err] of failed) console.log(`FAIL ${name}\n     ${err}`);
console.log(`${report.results.length - failed.length}/${report.results.length} engine tests passed in Pyodide (Python ${report.python}) in ${Date.now() - started}ms`);
process.exit(failed.length ? 1 : 0);
