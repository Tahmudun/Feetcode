"""Compile user code and invoke it the way LeetCode would.

Accepts `class Solution` with the method (LeetCode style), a bare top-level
function with the method's name, design classes (`MinStack`, `LRUCache`) driven
by an operation list, and encode/decode codecs.

Invocation is split into `prepare` (untimed harness work: build ListNodes,
instantiate classes) and the returned zero-arg `run()` (the user's work only),
so meters, tracers and memory probes wrap exactly the code being judged.
"""
from __future__ import annotations

import io
import sys
import traceback

from .problem import Problem
from .structures import convert_in, convert_out, normalize

FILENAME = "<solution>"
MODULE_NAME = "solution"

PRELUDE = """
from typing import *
import collections, heapq, math, itertools, functools, bisect, string, re
from collections import deque, defaultdict, Counter, OrderedDict
from heapq import heappush, heappop, heapify, heappushpop, heapreplace, nlargest, nsmallest
from math import inf, gcd, sqrt, ceil, floor, log2
from functools import lru_cache, cache, reduce
from itertools import accumulate, combinations, permutations, product, zip_longest, chain, groupby
from bisect import bisect_left, bisect_right, insort
from feetcode.structures import ListNode, Node
"""

_BASE: dict | None = None


def base_namespace() -> dict:
    global _BASE
    if _BASE is None:
        _BASE = {"__name__": MODULE_NAME}
        exec(PRELUDE, _BASE)  # noqa: S102 - our own prelude
    ns = dict(_BASE)
    ns["__name__"] = MODULE_NAME
    return ns


def prelude_names() -> set:
    return set(base_namespace())


class CompileError(Exception):
    def __init__(self, msg, line=None, col=None):
        super().__init__(msg)
        self.msg, self.line, self.col = msg, line, col

    def to_json(self):
        return {"type": "SyntaxError", "message": self.msg, "line": self.line, "col": self.col}


class EntryError(Exception):
    """The code doesn't define what the problem needs."""


class OutputError(Exception):
    """User code returned something we cannot interpret (e.g. a cyclic list)."""


def compile_user(source: str):
    try:
        return compile(source, FILENAME, "exec")
    except SyntaxError as e:
        raise CompileError(e.msg, e.lineno, e.offset) from None
    except (ValueError, TypeError) as e:  # null bytes etc.
        raise CompileError(str(e)) from None


def _find_entry(ns: dict, name: str):
    sol = ns.get("Solution")
    if isinstance(sol, type) and hasattr(sol, name):
        return getattr(sol(), name)
    fn = ns.get(name)
    if callable(fn):
        return fn
    raise EntryError(f"Couldn't find `{name}`. Define `class Solution` with a method `{name}` "
                     f"(or a top-level function `{name}`).")


def prepare(problem: Problem, ns: dict, args: dict):
    """Return (run, finish): run() calls user code; finish(raw) converts the answer."""
    sg = problem.signature
    if sg.kind == "design":
        cls = ns.get(sg.cls)
        if not isinstance(cls, type):
            raise EntryError(f"Couldn't find `class {sg.cls}`.")
        ops, argv = args["ops"], args["args"]

        def run_design():
            obj = cls(*argv[0])
            out = [None]
            for op, a in zip(ops[1:], argv[1:]):
                method = getattr(obj, op, None)
                if method is None:
                    raise EntryError(f"`{sg.cls}` has no method `{op}`.")
                out.append(normalize(method(*a)))
            return out

        return run_design, lambda raw: raw

    if sg.kind == "codec":
        sol = ns.get("Solution")
        holder = sol() if isinstance(sol, type) else None
        enc = getattr(holder, "encode", None) if holder else ns.get("encode")
        dec = getattr(holder, "decode", None) if holder else ns.get("decode")
        if not callable(enc) or not callable(dec):
            raise EntryError("Define `encode(strs)` and `decode(s)` (as methods of `class Solution`).")
        strs = list(args[sg.params[0].name])

        def run_codec():
            encoded = enc(list(strs))
            if not isinstance(encoded, str):
                raise OutputError(f"encode() must return a str, got {type(encoded).__name__}")
            return dec(encoded)

        return run_codec, normalize

    fn = _find_entry(ns, sg.method)
    if problem.prepare is not None:
        call_args = problem.prepare(args)
    else:
        call_args = [convert_in(p.type, args[p.name]) for p in sg.params]

    def run_fn():
        return fn(*call_args)

    def finish(raw):
        try:
            if problem.extract is not None:
                return problem.extract(raw, call_args, args)
            if sg.inplace:
                idx = [p.name for p in sg.params].index(sg.inplace)
                return convert_out(sg.params[idx].type, call_args[idx])
            return convert_out(sg.returns, raw)
        except (ValueError, TypeError, AttributeError) as e:
            raise OutputError(str(e)) from e

    return run_fn, finish


class BoundedIO(io.StringIO):
    """stdout capture that stops growing after `limit` characters."""

    def __init__(self, limit=20_000):
        super().__init__()
        self.limit = limit
        self.clipped = False

    def write(self, s):
        room = self.limit - self.tell()
        if room <= 0:
            self.clipped = True
            return len(s)
        if len(s) > room:
            self.clipped = True
            super().write(s[:room])
            return len(s)
        return super().write(s)


def describe_error(exc: BaseException) -> dict:
    """Exception -> {type, message, line, trace} using only user-code frames."""
    tb = exc.__traceback__
    frames = [f for f in traceback.extract_tb(tb) if f.filename == FILENAME]
    line = frames[-1].lineno if frames else None
    trace = [f"line {f.lineno}, in {f.name}" for f in frames][-8:]
    msg = str(exc)
    if isinstance(exc, RecursionError):
        msg = "maximum recursion depth exceeded - is there a missing base case?"
    return {"type": type(exc).__name__, "message": msg[:500], "line": line, "trace": trace}


def fresh_namespace(code_obj) -> dict:
    ns = base_namespace()
    exec(code_obj, ns)  # noqa: S102 - user code; we are the sandbox (Pyodide/WebAssembly)
    return ns


def recursion_guard(limit=2500):
    old = sys.getrecursionlimit()
    if old < limit:
        sys.setrecursionlimit(limit)
