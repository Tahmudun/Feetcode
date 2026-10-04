from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    return {"head": ints(rng, n, -9, 9)}


def worst_case(n):
    return {"head": list(range(n))}


ITERATIVE = '''class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        prev, curr = None, head  #> prev starts at None (what the new tail will point to); curr starts at the head.
        while curr:  #~
            nxt = curr.next  #> Save curr.next ({nxt.val if nxt else None}) before overwriting it.
            curr.next = prev  #> Flip the arrow: node {curr.val} now points back to {prev.val if prev else None}. #! The order is the whole algorithm: save next, flip the pointer, advance. Flip before saving and the rest of the list is unreachable.
            prev, curr = curr, nxt  #> Advance both: prev = {prev.val}, curr = {curr.val if curr else None}.
        return prev  #> curr ran off the end, so prev is the new head.
'''

RECURSIVE = '''class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if head is None or head.next is None:  #> Base case: an empty or one-node list is already reversed. || First reverse everything after node {head.val}.
            return head  #~
        new_head = self.reverseList(head.next)  #> Everything after {head.val} is reversed, headed by {new_head.val}.
        head.next.next = head  #> The node after {head.val} now points back at it. #! Recursion reverses the tail first; on the way back up, each node hooks itself behind its old successor. Uses O(n) stack space.
        head.next = None  #> Node {head.val} becomes the tail (for now).
        return new_head  #~
'''

PROBLEM = Problem(
    id="reverse-linked-list",
    number=206,
    slug="reverse-linked-list",
    title="Reverse Linked List",
    difficulty="Easy",
    pattern="linked-list",
    order=1,
    signature=sig("reverseList", "Optional[ListNode]", head="Optional[ListNode]"),
    statement="""
Given the `head` of a singly linked list, **reverse the list** and return the new head.
""",
    examples=[
        {"args": {"head": [1, 2, 3, 4]}, "output": [4, 3, 2, 1]},
        {"args": {"head": [7, 9]}, "output": [9, 7]},
        {"args": {"head": []}, "output": []},
    ],
    constraints=["0 ≤ number of nodes ≤ 5000", "−5000 ≤ Node.val ≤ 5000"],
    companies={"Amazon": 5, "Microsoft": 5, "Apple": 4, "Google": 4, "Meta": 4, "Bloomberg": 4, "Adobe": 3,
               "Nvidia": 2, "Yandex": 2},
    topics=["Linked List", "Recursion"],
    hints=[
        "You only need to change where each `next` points. Which node should each one point to?",
        "Walk the list with two pointers: `prev` (already reversed) and `curr` (still to do).",
        "Save curr.next first, then set curr.next = prev, then advance both pointers.",
    ],
    insight={
        "pattern": "Pointer reversal (prev / curr / next)",
        "oneLiner": "Save next, flip curr.next to prev, advance - until curr is None; prev is the new head.",
        "mnemonic": "Save, flip, step.",
        "why": "Each node's pointer is flipped exactly once, in O(1) extra space. Saving next first keeps the unreversed part reachable.",
        "signals": ["reverse a list or part of one", "building block for reorder / k-group / palindrome-list problems"],
        "recall": [
            {"q": "What are prev and curr initialised to?", "a": "prev = None, curr = head."},
            {"q": "What do you return?", "a": "prev - when curr becomes None, prev is the old tail, now the head."},
        ],
    },
    solutions=[
        Solution("recursive", "Recursion", "O(n)", "O(n)", RECURSIVE,
                 "Reverse the rest of the list recursively, then attach the current node at its end."),
        Solution("iterative", "Iterative pointer flipping", "O(n)", "O(1)", ITERATIVE,
                 "Walk once, flipping each next pointer to the previous node.", optimal=True),
    ],
    pitfalls=[
        Pitfall("lost-rest", "Lost the rest of the list",
                "Overwriting curr.next before saving it disconnects everything after curr. Save nxt = curr.next first.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) < len(e)),
        Pitfall("cycle", "Left a cycle behind",
                "The old head must end up pointing to None; otherwise the first two nodes point at each other.",
                error="OutputError: cycle"),
    ],
    edge_cases=[{"head": []}, {"head": [5]}, {"head": [1, 1, 1]}],
    generate=generate,
    worst_case=worst_case,
    lesson={"head": [1, 2, 3, 4]},
    related=["reorder-list", "reverse-nodes-in-k-group", "merge-two-sorted-lists"],
)
