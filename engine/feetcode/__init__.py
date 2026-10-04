"""Feetcode engine: judge, tracer, fuzzer and complexity lab for Python solutions.

Runs unchanged in CPython (the build pipeline, tests) and in Pyodide (the
browser, inside a Web Worker).
"""
import sys

if sys.version_info < (3, 12):  # pragma: no cover - guards the build machine, not the browser
    raise ImportError(
        "feetcode needs Python 3.12+: older versions emit no line event for `while True: pass`, "
        "so a runaway loop could not be metered and would hang instead of failing its budget."
    )

__version__ = "2.0.0"
