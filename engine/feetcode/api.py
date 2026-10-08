"""JSON-in, JSON-out entry point for the browser worker.

The worker calls `handle(json_string)` and gets a JSON string back, so the
JS <-> Python boundary carries only plain strings (no proxies to leak).
"""
from __future__ import annotations

import importlib
import json
import traceback

from . import __version__, complexity, diverge, fuzz, judge
from .harness import CompileError
from .tracer import trace_problem, trace_script

_problems: dict = {}


def load_problem(module: str):
    if module not in _problems:
        _problems[module] = importlib.import_module(module).PROBLEM
    return _problems[module]


def reload_problem(module: str):
    _problems.pop(module, None)
    mod = importlib.import_module(module)
    importlib.reload(mod)
    _problems[module] = mod.PROBLEM
    return _problems[module]


def dispatch(req: dict) -> dict:
    op = req.get("op")
    if op == "ping":
        return {"version": __version__}
    if op == "playground":
        return trace_script(req["code"], max_steps=req.get("maxSteps", 1500))
    problem = load_problem(req["module"])
    if op == "run":
        return judge.run(problem, req["code"], req["tests"])
    if op == "submit":
        return judge.submit(problem, req["code"], req["tests"])
    if op == "trace":
        return trace_problem(problem, req["code"], req["args"], max_steps=req.get("maxSteps", 1500))
    if op == "profile":
        return complexity.profile(problem, req["code"], sizes=req.get("sizes"))
    if op == "diagnose":
        return fuzz.diagnose(problem, req["code"], args=req.get("args"))
    if op == "compare":
        trace = trace_problem(problem, req["code"], req["args"], max_steps=req.get("maxSteps", 1500))
        return {"trace": trace, "divergence": diverge.analyze(problem, req["code"], req["args"], trace)}
    raise ValueError(f"unknown op {op!r}")


def handle(payload: str) -> str:
    try:
        req = json.loads(payload)
        res = {"ok": True, "data": dispatch(req)}
    except CompileError as e:
        res = {"ok": True, "data": {"verdict": "compile", "error": e.to_json()}}
    except Exception as e:  # noqa: BLE001 - engine bug: report, don't crash the worker
        res = {"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-2000:]}
    try:
        return json.dumps(res, default=_fallback, allow_nan=False)
    except ValueError:  # inf/nan somewhere in user output: JS JSON.parse can't read them
        return json.dumps(_sanitize(res), default=_fallback, allow_nan=False)


def _sanitize(o):
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return {"f": repr(o)}
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_sanitize(v) for v in o]
    return o


def _fallback(o):
    if isinstance(o, float):
        return repr(o)
    if isinstance(o, (set, frozenset, tuple)):
        return list(o)
    return repr(o)
