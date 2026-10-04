"""CLI: python -m feetcode_pipeline {check,build} [problem ...]"""
from __future__ import annotations

import argparse
import sys
import time

from .discover import discover, load
from .validate import check


def cmd_check(args) -> int:
    sources = discover(args.only)
    errors = 0
    for src in sources:
        t0 = time.perf_counter()
        problem = load(src)
        issues, profiles = check(problem, cases=args.cases, with_complexity=args.complexity)
        took = time.perf_counter() - t0
        status = "FAIL" if any(i.level == "error" for i in issues) else "ok"
        extra = ""
        if profiles:
            extra = "  " + ", ".join(f"{k}={(v.get('time') or {}).get('label')}" for k, v in profiles.items())
        print(f"{status:4} {problem.id:40} {took:5.1f}s{extra}")
        for i in issues:
            print("     ", i)
        errors += sum(1 for i in issues if i.level == "error")
    print(f"\n{len(sources)} problems, {errors} errors")
    return 1 if errors else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="feetcode_pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="validate problem modules")
    c.add_argument("only", nargs="*")
    c.add_argument("--cases", type=int, default=200)
    c.add_argument("--complexity", action="store_true")
    c.set_defaults(fn=cmd_check)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
