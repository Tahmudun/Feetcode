"""Orchestrate the build: discover -> validate -> stages -> artifacts -> manifest.

Artifacts (client/src/content/generated/):
    catalog.json            every problem's summary (the problem list page)
    patterns.json           pattern primers
    companies.json          company -> problem ids, with frequency tiers
    problems/<id>.json      statement, examples, solutions, hints, insight, starter code
    suites/<id>.json        hidden tests: args, expected output, operation budget
    lessons/<id>.json       pre-traced, narrated executions of every reference solution
    baselines/<id>.json     operation-count growth curves of every reference solution
    manifest.json           input digests + artifact digests (lineage, incremental builds, drift check)

Incremental: a problem is rebuilt only when its input digest changes - the hash
of its module source, the engine source and the pipeline version. Problems are
independent, so they build in parallel worker processes.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .discover import ROOT, Source, discover, engine_digest, load
from .validate import check

PIPELINE_VERSION = "2.0.0"
OUT = ROOT / "client" / "src" / "content" / "generated"
KINDS = ("problems", "suites", "lessons", "baselines")


def dumps(obj) -> str:
    """Canonical JSON: stable key order and separators -> byte-identical rebuilds."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def input_digest(src: Source, engine: str) -> str:
    return digest(f"{PIPELINE_VERSION}:{engine}:{src.digest}")


def _build_one(module: str, rel: str, src_digest: str, engine: str, validate: bool) -> dict:
    """Runs in a worker process. Returns artifacts + report for one problem."""
    from . import stages
    src = Source(module, ROOT / rel, src_digest)
    problem = load(src)
    t0 = time.perf_counter()
    issues = []
    if validate:
        issues, _ = check(problem, cases=120)
        errors = [str(i) for i in issues if i.level == "error"]
        if errors:
            return {"id": problem.id, "module": module, "errors": errors}
    suite = stages.suite(problem)
    artifacts = {
        "problems": stages.detail(problem, module),
        "suites": suite,
        "lessons": stages.lessons(problem),
        "baselines": stages.baselines(problem),
    }
    verdicts = stages.reference_verdicts(problem, suite["cases"])
    return {
        "id": problem.id,
        "module": module,
        "summary": stages.summary(problem, module),
        "artifacts": {k: dumps(v) for k, v in artifacts.items()},
        "verdicts": verdicts,
        "warnings": [str(i) for i in issues if i.level == "warn"],
        "seconds": round(time.perf_counter() - t0, 2),
        "cases": len(suite["cases"]),
    }


def _write(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == text:
        return False
    path.write_text(text)
    return True


def _edited_artifacts(entries: dict, skip_modules: set) -> list:
    """Generated files whose bytes no longer match the digest recorded when they were built."""
    edited = []
    for pid, entry in sorted(entries.items()):
        if entry["module"] in skip_modules:
            continue
        for kind, want in entry.get("artifacts", {}).items():
            path = OUT / kind / f"{pid}.json"
            if not path.exists() or digest(path.read_text()) != want:
                edited.append(f"{kind}/{pid}.json")
    return edited


def _load_manifest() -> dict:
    path = OUT / "manifest.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"problems": {}}


def build(only: list | None = None, force: bool = False, validate: bool = True, jobs: int | None = None,
          check_only: bool = False) -> int:
    from problems._patterns import PATTERNS

    engine = engine_digest()
    sources = discover(only)
    manifest = _load_manifest()
    old = manifest.get("problems", {})
    todo = [s for s in sources
            if force or old.get(_id_for(s, old), {}).get("input") != input_digest(s, engine)
            or not all((OUT / k / f"{_id_for(s, old)}.json").exists() for k in KINDS)]

    if check_only:
        stale = [s.module for s in todo]
        edited = _edited_artifacts(old, {s.module for s in todo})
        if stale:
            print(f"DRIFT: {len(stale)} problem(s) are out of date: {', '.join(stale)}")
        if edited:
            print(f"DRIFT: {len(edited)} generated file(s) differ from the manifest: {', '.join(edited)}")
        if stale or edited:
            print("Run `python -m feetcode_pipeline build` and commit the result (never edit generated files).")
            return 1
        print(f"up to date: {len(sources)} problems, engine {engine[:12]}")
        return 0

    print(f"{len(sources)} problems, {len(todo)} to build (engine {engine[:12]})")
    results, failed = [], []
    jobs = jobs or min(len(todo), os.cpu_count() or 2) or 1
    if todo:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            futures = [pool.submit(_build_one, s.module, s.rel, s.digest, engine, validate) for s in todo]
            for src, fut in zip(todo, futures):
                res = fut.result()
                if res.get("errors"):
                    failed.append(res)
                    print(f"FAIL {res['id']}")
                    for e in res["errors"]:
                        print("     ", e)
                    continue
                results.append((src, res))
                v = " ".join(f"{k}={x['verdict']}" for k, x in res["verdicts"].items())
                print(f"ok   {res['id']:48} {res['seconds']:5.1f}s  {res['cases']:3} cases  {v}")
                for w in res["warnings"]:
                    print("     ", w)
    if failed:
        print(f"\n{len(failed)} problem(s) failed validation - nothing written.")
        return 1

    entries = dict(old)
    changed = 0
    for src, res in results:
        pid = res["id"]
        files = {}
        for kind, text in res["artifacts"].items():
            changed += _write(OUT / kind / f"{pid}.json", text)
            files[kind] = digest(text)
        entries[pid] = {"module": src.module, "input": input_digest(src, engine), "artifacts": files,
                        "summary": res["summary"], "verdicts": res["verdicts"], "cases": res["cases"]}
    # drop entries for problems that no longer exist (only on full builds)
    if not only:
        live = {e for e in entries if entries[e]["module"] in {s.module for s in sources}}
        for pid in set(entries) - live:
            for kind in KINDS:
                (OUT / kind / f"{pid}.json").unlink(missing_ok=True)
            del entries[pid]

    summaries = sorted((e["summary"] for e in entries.values()),
                       key=lambda s: (list(_pattern_order(PATTERNS)).index(s["pattern"]), s["order"]))
    catalog = dumps({"version": PIPELINE_VERSION, "problems": summaries})
    changed += _write(OUT / "catalog.json", catalog)
    changed += _write(OUT / "patterns.json", dumps(_patterns_with_counts(PATTERNS, summaries)))
    changed += _write(OUT / "companies.json", dumps(_companies(summaries)))
    manifest = {
        "pipeline": PIPELINE_VERSION,
        "engine": engine[:16],
        "catalog": digest(catalog),
        "problems": dict(sorted(entries.items())),
    }
    _write(OUT / "manifest.json", json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(f"\n{len(results)} built, {changed} file(s) changed -> {OUT.relative_to(ROOT)}")
    return 0


def _id_for(src: Source, old: dict) -> str:
    for pid, e in old.items():
        if e.get("module") == src.module:
            return pid
    return src.path.stem.replace("_", "-")


def _pattern_order(patterns):
    return [p["id"] for p in patterns]


def _patterns_with_counts(patterns, summaries):
    out = []
    for p in patterns:
        ids = [s["id"] for s in summaries if s["pattern"] == p["id"]]
        out.append({**p, "problems": ids})
    return out


def _companies(summaries):
    table: dict = {}
    for s in summaries:
        for company, tier in s["companies"].items():
            table.setdefault(company, []).append({"id": s["id"], "tier": tier})
    return {c: sorted(v, key=lambda x: -x["tier"]) for c, v in sorted(table.items(), key=lambda kv: (-len(kv[1]), kv[0]))}


if __name__ == "__main__":
    sys.exit(build())
