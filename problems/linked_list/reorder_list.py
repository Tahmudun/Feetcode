from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    return {"head": ints(rng, max(1, n), 0, 9)}


def validate(args):
    return len(args["head"]) >= 1


def worst_case(n):
    return {"head": list(range(max(1, n)))}


ARRAY = '''class Solution:
    def reorderList(self, head: Optional[ListNode]) -> None:
        nodes = []
        node = head
        while node:  #~
            nodes.append(node)  #~
            node = node.next  #~
        i, j = 0, len(nodes) - 1  #> Collected {len(nodes)} nodes into an array; now link from both ends.
        while i < j:  #~
            nodes[i].next = nodes[j]  #> {nodes[i].val} → {nodes[j].val}.
            i += 1  #~
            if i == j:  #~
                break  #~
            nodes[j].next = nodes[i]  #> {nodes[j].val} → {nodes[i].val}.
            j -= 1  #~
        nodes[i].next = None  #> Node {nodes[i].val} is the new tail.
'''

IN_PLACE = '''class Solution:
    def reorderList(self, head: Optional[ListNode]) -> None:
        slow, fast = head, head.next  #> Step 1: find the middle. slow moves 1 node per step, fast moves 2.
        while fast and fast.next:  #~
            slow = slow.next  #~
            fast = fast.next.next  #~
        second = slow.next  #> slow stopped at {slow.val}, the end of the first half. The second half starts at {second.val if second else None}.
        slow.next = None  #> Cut the list in two.
        prev = None  #> Step 2: reverse the second half.
        while second:  #~
            nxt = second.next  #~
            second.next = prev  #~
            prev, second = second, nxt  #~
        second = prev  #> The second half is reversed and now starts at {second.val if second else None}. #! Three classic moves in one problem: find the middle (fast/slow), reverse a list (save-flip-step), then merge two lists by alternating.
        first = head  #> Step 3: weave the halves together.
        while second:  #~
            t1, t2 = first.next, second.next  #~
            first.next = second  #> Link {first.val} → {second.val}.
            second.next = t1  #> Link {second.val} → {t1.val if t1 else None}.
            first, second = t1, t2  #~
'''

PROBLEM = Problem(
    id="reorder-list",
    number=143,
    slug="reorder-list",
    title="Reorder List",
    difficulty="Medium",
    pattern="linked-list",
    order=4,
    signature=sig("reorderList", "None", inplace="head", head="Optional[ListNode]"),
    statement="""
A list `L0 → L1 → … → Ln-1 → Ln` must be rearranged **in place** into

`L0 → Ln → L1 → Ln-1 → L2 → Ln-2 → …`

Change the links between nodes, not their values. The function returns nothing; the judge reads the list from `head` afterwards.
""",
    examples=[
        {"args": {"head": [1, 2, 3, 4]}, "output": [1, 4, 2, 3]},
        {"args": {"head": [1, 2, 3, 4, 5]}, "output": [1, 5, 2, 4, 3]},
        {"args": {"head": [8]}, "output": [8]},
    ],
    constraints=["1 ≤ number of nodes ≤ 5 · 10⁴", "1 ≤ Node.val ≤ 1000"],
    companies={"Amazon": 4, "Meta": 4, "Microsoft": 3, "Google": 2, "Bloomberg": 2, "Adobe": 2},
    topics=["Linked List", "Two Pointers", "Stack", "Recursion"],
    hints=[
        "The pattern alternates nodes from the front and from the back. How could you reach the back easily?",
        "Split the list in the middle, reverse the second half, then merge the two halves by alternating.",
        "Use fast/slow pointers for the middle; remember to cut the first half off (slow.next = None).",
    ],
    insight={
        "pattern": "Middle + reverse + merge",
        "oneLiner": "Find the middle with fast/slow, reverse the second half, then interleave the two halves.",
        "mnemonic": "Split, flip, zip.",
        "why": "Reversing the back half turns 'take from the end' into 'take from the front', so a simple two-list merge does the rest in O(1) space.",
        "signals": ["\"in place\" rearrangement of a list", "alternating from both ends"],
        "recall": [
            {"q": "The three steps?", "a": "Find the middle (fast/slow), reverse the second half, merge alternately."},
            {"q": "Why must you cut slow.next = None?", "a": "Otherwise the first half still points into the (reversed) second half and creates a cycle."},
        ],
    },
    solutions=[
        Solution("array", "Array of nodes", "O(n)", "O(n)", ARRAY,
                 "Put the nodes in an array, then relink them from both ends."),
        Solution("in-place", "Middle + reverse + merge", "O(n)", "O(1)", IN_PLACE,
                 "Split at the middle, reverse the back half, and weave the halves together.", optimal=True),
    ],
    pitfalls=[
        Pitfall("no-cut", "Didn't cut the list at the middle",
                "Set slow.next = None before reversing, or the halves stay connected and form a cycle.",
                error="OutputError: cycle"),
        Pitfall("returned-new", "Built a new list instead of relinking",
                "The judge reads the original head after your function returns - modify the links in place.",
                detect=lambda a, e, x: x == a["head"] and x != e),
    ],
    edge_cases=[{"head": [1]}, {"head": [1, 2]}, {"head": [1, 2, 3]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"head": [1, 2, 3, 4, 5]},
    related=["reverse-linked-list", "linked-list-cycle", "merge-two-sorted-lists"],
)
