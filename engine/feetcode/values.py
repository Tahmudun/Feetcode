"""Encode live Python values as JSON snapshots that preserve object identity.

Scalars are inlined. Containers and objects live in a per-step `heap` keyed by a
small, stable integer id, and are referenced as {"r": id}. Identity matters:
when `prev` and `curr.next` point at the same node, the visualizer must draw one
node with two arrows into it, not two copies.

Value encoding
    None / bool / int / str      -> as JSON
    int beyond 2**53             -> {"big": "123..."}
    float                        -> {"f": "2.5"}   (repr keeps 1.0 vs 1, inf, nan)
    container / user object      -> {"r": id}
    function / class / module    -> {"fn": "name"}
    anything else                -> {"repr": "..."}

Heap object encoding (compact arrays)
    ["list",  [v...], len?]   len present only when truncated
    ["tuple", [v...], len?]
    ["deque", [v...], len?]
    ["set",   [v...], len?]   sorted for display stability
    ["dict",  [[k, v]...], len?, subtype?]
    ["obj",   "ClassName", [[field, v]...]]
"""
from __future__ import annotations

import collections
import types

MAX_ITEMS = 160          # per container, per snapshot
MAX_OBJECTS = 600        # per snapshot
MAX_STR = 400

USER_MODULES = {"solution", "feetcode.structures", "__main__"}

_DICT_SUBTYPES = {
    collections.defaultdict: "defaultdict",
    collections.Counter: "Counter",
    collections.OrderedDict: "OrderedDict",
}


def _is_user_object(x):
    t = type(x)
    return t.__module__ in USER_MODULES and not isinstance(x, type) and (
        hasattr(t, "__dict__") or hasattr(t, "__slots__")
    )


def object_fields(x):
    """Instance fields without triggering user __getattr__/properties."""
    try:
        d = object.__getattribute__(x, "__dict__")
        return list(d.items())
    except AttributeError:
        out = []
        for name in getattr(type(x), "__slots__", ()):
            try:
                out.append((name, object.__getattribute__(x, name)))
            except AttributeError:
                pass
        return out


def safe_repr(x, limit=80):
    try:
        r = repr(x)
    except Exception:  # noqa: BLE001 - user __repr__ can do anything
        r = f"<{type(x).__name__}>"
    return r if len(r) <= limit else r[: limit - 1] + "…"


def _sort_key(v):
    return (type(v).__name__, v if isinstance(v, (int, float, str)) else repr(v))


class Encoder:
    """Assigns stable small ids to objects for the lifetime of one trace."""

    def __init__(self):
        self._ids: dict[int, int] = {}
        self._keep: list = []  # keep objects alive so id() values are never reused

    def ref(self, obj) -> int:
        key = id(obj)
        rid = self._ids.get(key)
        if rid is None:
            rid = len(self._ids) + 1
            self._ids[key] = rid
            self._keep.append(obj)
        return rid

    def is_ref_type(self, x) -> bool:
        return isinstance(x, (list, tuple, dict, set, frozenset, collections.deque)) or _is_user_object(x)

    def value(self, x, heap, queue):
        if x is None or x is True or x is False:
            return x
        t = type(x)
        if t is int:
            return x if -(2**53) < x < 2**53 else {"big": str(x)}
        if t is float:
            return {"f": repr(x)}
        if t is str:
            return x if len(x) <= MAX_STR else x[:MAX_STR] + "…"
        if isinstance(x, bool):
            return bool(x)
        if isinstance(x, int):  # int subclasses (IntEnum etc.)
            return int(x)
        if self.is_ref_type(x):
            rid = self.ref(x)
            if rid not in heap:
                heap[rid] = None  # reserve; filled when dequeued
                queue.append((rid, x))
            return {"r": rid}
        if isinstance(x, (types.FunctionType, types.BuiltinFunctionType, types.MethodType, type, types.ModuleType)):
            return {"fn": getattr(x, "__name__", "?")}
        return {"repr": safe_repr(x)}

    def _encode_object(self, x, heap, queue):
        def enc(v):
            return self.value(v, heap, queue)

        def seq(items, total):
            body = [enc(v) for v in items[:MAX_ITEMS]]
            return body, (total if total > MAX_ITEMS else None)

        if isinstance(x, list):
            body, trunc = seq(x, len(x))
            return ["list", body] + ([trunc] if trunc else [])
        if isinstance(x, tuple):
            body, trunc = seq(x, len(x))
            return ["tuple", body] + ([trunc] if trunc else [])
        if isinstance(x, collections.deque):
            items = list(x)
            body, trunc = seq(items, len(items))
            return ["deque", body] + ([trunc] if trunc else [])
        if isinstance(x, (set, frozenset)):
            items = list(x)
            try:
                items.sort(key=_sort_key)
            except TypeError:
                items.sort(key=repr)
            body, trunc = seq(items, len(items))
            return ["set", body] + ([trunc] if trunc else [])
        if isinstance(x, dict):
            items = list(dict.items(x))[:MAX_ITEMS]
            body = [[enc(k), enc(v)] for k, v in items]
            sub = next((name for cls, name in _DICT_SUBTYPES.items() if type(x) is cls), None)
            total = len(x)
            out = ["dict", body]
            if total > MAX_ITEMS or sub:
                out.append(total if total > MAX_ITEMS else None)
            if sub:
                out.append(sub)
            return out
        fields = object_fields(x)
        return ["obj", type(x).__name__, [[name, enc(v)] for name, v in fields if not name.startswith("__")]]

    def snapshot(self, named_values):
        """Encode [(name, value)...] -> (encoded pairs, heap) with everything reachable."""
        heap: dict = {}
        queue: collections.deque = collections.deque()
        pairs = [[name, self.value(v, heap, queue)] for name, v in named_values]
        while queue:
            rid, obj = queue.popleft()
            if len(heap) > MAX_OBJECTS:
                heap[rid] = ["obj", "…", []]
                continue
            try:
                heap[rid] = self._encode_object(obj, heap, queue)
            except Exception:  # noqa: BLE001 - never let encoding crash a trace
                heap[rid] = ["obj", type(obj).__name__, []]
        return pairs, {str(k): v for k, v in heap.items()}

    def encode_standalone(self, value):
        """Encode a single value with its own heap (e.g. a return value)."""
        pairs, heap = self.snapshot([("value", value)])
        return {"v": pairs[0][1], "h": heap}
