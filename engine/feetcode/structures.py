"""Data structures that problems hand to user code, plus JSON <-> object converters.

Problem inputs and expected outputs are stored as plain JSON (lists, numbers,
strings). These converters turn them into the node objects user code expects,
and turn whatever the user returns back into comparable JSON.
"""
from __future__ import annotations


class ListNode:
    """Singly linked list node, LeetCode-compatible."""

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __repr__(self):
        return f"ListNode({self.val!r})"


class Node:
    """Linked list node with an extra `random` pointer (Copy List with Random Pointer)."""

    def __init__(self, x=0, next=None, random=None):
        self.val = x
        self.next = next
        self.random = random

    def __repr__(self):
        return f"Node({self.val!r})"


class CycleError(ValueError):
    """Raised when a returned list contains a cycle (or is absurdly long)."""


def to_list(values):
    dummy = ListNode()
    tail = dummy
    for v in values or []:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def from_list(head, limit=200_000):
    out, seen = [], set()
    node = head
    while node is not None:
        if id(node) in seen or len(out) >= limit:
            raise CycleError("returned list contains a cycle")
        if not hasattr(node, "val"):
            raise TypeError(f"expected a ListNode, got {type(node).__name__}")
        seen.add(id(node))
        out.append(node.val)
        node = node.next
    return out


def to_cycle_list(values, pos):
    """Build a list whose tail links back to index `pos` (-1 = no cycle)."""
    nodes = [ListNode(v) for v in values]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if nodes and 0 <= pos < len(nodes):
        nodes[-1].next = nodes[pos]
    return nodes[0] if nodes else None


def to_random_list(pairs):
    """[[val, random_index|None], ...] -> head Node."""
    nodes = [Node(v) for v, _ in pairs]
    for i, (_, r) in enumerate(pairs):
        if i + 1 < len(nodes):
            nodes[i].next = nodes[i + 1]
        nodes[i].random = nodes[r] if r is not None else None
    return nodes[0] if nodes else None


def from_random_list(head, limit=10_000):
    nodes, index = [], {}
    node = head
    while node is not None:
        if id(node) in index or len(nodes) >= limit:
            raise CycleError("returned list contains a cycle")
        index[id(node)] = len(nodes)
        nodes.append(node)
        node = node.next
    out = []
    for n in nodes:
        r = getattr(n, "random", None)
        if r is not None and id(r) not in index:
            raise ValueError("a random pointer points outside the returned list")
        out.append([n.val, index[id(r)] if r is not None else None])
    return out


def list_nodes(head, limit=200_000):
    """All node objects reachable from head via .next (cycle-safe)."""
    out, seen = [], set()
    while head is not None and id(head) not in seen and len(out) < limit:
        seen.add(id(head))
        out.append(head)
        head = head.next
    return out


# Type-string driven conversion. Signature types are written LeetCode-style.
_IN = {
    "ListNode": to_list,
    "Optional[ListNode]": to_list,
    "List[ListNode]": lambda xs: [to_list(x) for x in xs],
    "List[Optional[ListNode]]": lambda xs: [to_list(x) for x in xs],
    "Node": to_random_list,
    "Optional[Node]": to_random_list,
}

_OUT = {
    "ListNode": from_list,
    "Optional[ListNode]": from_list,
    "Node": from_random_list,
    "Optional[Node]": from_random_list,
}


def convert_in(type_name, value):
    fn = _IN.get(type_name)
    if fn is not None:
        return fn(value)
    return _deep_copy_json(value)


def convert_out(type_name, value):
    fn = _OUT.get(type_name)
    if fn is not None:
        return fn(value)
    return normalize(value)


def _deep_copy_json(value):
    if isinstance(value, list):
        return [_deep_copy_json(v) for v in value]
    if isinstance(value, dict):
        return {k: _deep_copy_json(v) for k, v in value.items()}
    return value


def normalize(value):
    """Make a user's return value JSON-comparable (tuples -> lists, sets -> sorted lists)."""
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, (set, frozenset)):
        items = [normalize(v) for v in value]
        try:
            return sorted(items)
        except TypeError:
            return sorted(items, key=repr)
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in value.items()}
    if isinstance(value, ListNode):
        return from_list(value)
    if isinstance(value, float) and value.is_integer() and abs(value) < 2**53:
        return value
    return value


class CallArgs(list):
    """Positional call arguments that can carry notes from prepare() to extract()."""
    original: set = frozenset()
    keep: list = ()
