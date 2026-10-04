from feetcode.problem import Problem, Pitfall, Solution, ints, sig
from feetcode.structures import to_cycle_list


def generate(rng, n):
    head = ints(rng, n, -5, 5)
    pos = rng.randint(-1, len(head) - 1) if head and rng.random() < 0.7 else -1
    return {"head": head, "pos": pos}


def validate(args):
    return -1 <= args["pos"] < len(args["head"])


def shrink(args):
    head, pos = args["head"], args["pos"]
    if pos != -1:
        yield {"head": head, "pos": -1}
    for i in range(len(head) - 1, -1, -1):
        rest = head[:i] + head[i + 1:]
        if pos == -1 or not rest:
            new_pos = -1
        elif i < pos:
            new_pos = pos - 1
        else:
            new_pos = min(pos, len(rest) - 1)  # removing the target re-aims the tail at its successor
        yield {"head": rest, "pos": new_pos}


def worst_case(n):
    return {"head": list(range(max(1, n))), "pos": 0}


HASHSET = '''class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        seen = set()  #> Every node object we've visited - by identity, not by value.
        node = head
        while node:  #~
            if node in seen:  #> We've stood on this node ({node.val}) before: the list loops back. || Node {node.val} is new.
                return True  #~
            seen.add(node)  #~
            node = node.next  #~
        return False  #> Reached None - the list ends, so there's no cycle.
'''

FLOYD = '''class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        slow = fast = head  #> Tortoise and hare both start at the head.
        while fast and fast.next:  #~
            slow = slow.next  #~
            fast = fast.next.next  #> slow takes 1 step (to {slow.val}); fast takes 2 (to {fast.val if fast else None}).
            if slow is fast:  #> Same node! fast has lapped slow inside a loop. || Not the same node yet. #! Inside a cycle, fast gains exactly one node on slow per step. The gap shrinks by 1 every step, so they must meet - and it costs O(1) memory.
                return True  #~
        return False  #> fast reached the end of the list: there is no cycle.
'''

PROBLEM = Problem(
    id="linked-list-cycle",
    number=141,
    slug="linked-list-cycle",
    title="Linked List Cycle",
    difficulty="Easy",
    pattern="linked-list",
    order=3,
    signature=sig("hasCycle", "bool", head="Optional[ListNode]"),
    statement="""
Given `head`, return `true` if the linked list contains a **cycle** - some node can be reached again by following `next` pointers - and `false` otherwise.

In the examples, `pos` is the index the tail connects back to (`-1` means no cycle). `pos` is only used to build the input; your function receives just `head`.

Follow-up: can you do it with O(1) memory?
""",
    examples=[
        {"args": {"head": [3, 2, 0, -4], "pos": 1}, "output": True, "explain": "The tail links back to the node at index 1."},
        {"args": {"head": [1, 2], "pos": 0}, "output": True},
        {"args": {"head": [1], "pos": -1}, "output": False},
    ],
    constraints=["0 ≤ number of nodes ≤ 10⁴", "−10⁵ ≤ Node.val ≤ 10⁵", "pos is −1 or a valid index"],
    companies={"Amazon": 4, "Microsoft": 4, "Google": 3, "Meta": 3, "Apple": 3, "Bloomberg": 3, "Goldman Sachs": 2},
    topics=["Hash Table", "Linked List", "Two Pointers"],
    hints=[
        "If there's no cycle, walking the list ends at None. If there is one, you'd walk forever. How can you notice?",
        "Remember the nodes you've visited (the node objects, not values). Seeing one again means a cycle.",
        "For O(1) memory: move one pointer 1 step and another 2 steps. If there's a cycle, they meet.",
    ],
    insight={
        "pattern": "Fast & slow pointers (Floyd)",
        "oneLiner": "slow moves 1, fast moves 2; they meet iff there's a cycle, otherwise fast hits None.",
        "mnemonic": "On a circular track, the faster runner always laps the slower one.",
        "why": "Once both are in the cycle, the distance between them shrinks by exactly 1 per step, so it reaches 0.",
        "signals": ["cycle detection", "\"O(1) extra memory\" on a linked structure", "finding the middle"],
        "recall": [
            {"q": "Why compare nodes with `is`, not values?", "a": "Different nodes can hold equal values; a cycle means the same node object."},
            {"q": "Loop condition for the fast pointer?", "a": "while fast and fast.next - so fast.next.next is always safe."},
        ],
    },
    solutions=[
        Solution("hashset", "Visited set", "O(n)", "O(n)", HASHSET,
                 "Store every node visited; a repeat means a cycle."),
        Solution("floyd", "Fast and slow pointers", "O(n)", "O(1)", FLOYD,
                 "Two pointers at different speeds meet inside any cycle.", optimal=True),
    ],
    pitfalls=[
        Pitfall("values", "Detected repeated values instead of repeated nodes",
                "Two different nodes can store the same value. Track node objects (or use fast/slow pointers).",
                detect=lambda a, e, x: e is False and x is True and len(set(a["head"])) < len(a["head"])),
        Pitfall("fast-null", "fast.next.next crashed",
                "Check both fast and fast.next before jumping two steps.",
                error="AttributeError: 'NoneType'"),
    ],
    edge_cases=[{"head": [], "pos": -1}, {"head": [1], "pos": 0}, {"head": [1, 1, 1], "pos": -1},
                {"head": [1, 2, 3, 4, 5], "pos": 4}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    worst_case=worst_case,
    prepare=lambda a: [to_cycle_list(a["head"], a["pos"])],
    size_of=lambda a: len(a["head"]),
    lesson={"head": [3, 2, 0, -4, 5], "pos": 1},
    related=["find-the-duplicate-number", "reorder-list"],
)
