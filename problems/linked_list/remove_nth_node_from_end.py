from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    head = ints(rng, max(1, n), 0, 9)
    return {"head": head, "n": rng.randint(1, len(head))}


def validate(args):
    return len(args["head"]) >= 1 and 1 <= args["n"] <= len(args["head"])


def shrink(args):
    head, k = args["head"], args["n"]
    for i in range(len(head) - 1, -1, -1):
        rest = head[:i] + head[i + 1:]
        if rest:
            yield {"head": rest, "n": min(k, len(rest))}
    if k > 1:
        yield {"head": head, "n": k - 1}


def worst_case(n):
    return {"head": list(range(max(1, n))), "n": 1}


TWO_PASS = '''class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        length = 0
        node = head
        while node:  #~
            length += 1  #~
            node = node.next  #~
        if n == length:  #> The list has {length} nodes, so the {n}-th from the end is the head itself. || The list has {length} nodes: remove the one at index {length - n}.
            return head.next  #~
        node = head
        for _ in range(length - n - 1):  #~
            node = node.next  #~
        node.next = node.next.next  #> Node {node.val} now skips over its neighbour.
        return head
'''

ONE_PASS = '''class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        dummy = ListNode(0, head)  #> A dummy node before the head - removing the head itself becomes an ordinary case.
        left, right = dummy, head  #~
        for _ in range(n):  #~
            right = right.next  #> right runs ahead to open a gap of {n} node(s).
        while right:  #~
            left = left.next  #~
            right = right.next  #> Move both together: left at {left.val}, right at {right.val if right else None}. #! The gap between left and right never changes. When right falls off the end, left sits exactly one node before the n-th node from the end.
        left.next = left.next.next  #> Unlink the target: left now skips straight to {left.next.val if left.next else None}.
        return dummy.next  #> Return the (possibly new) head.
'''

PROBLEM = Problem(
    id="remove-nth-node-from-end-of-list",
    number=19,
    slug="remove-nth-node-from-end-of-list",
    title="Remove Nth Node From End of List",
    difficulty="Medium",
    pattern="linked-list",
    order=5,
    signature=sig("removeNthFromEnd", "Optional[ListNode]", head="Optional[ListNode]", n="int"),
    statement="""
Given the `head` of a linked list, remove the **`n`-th node counting from the end** and return the head of the resulting list.

Follow-up: can you do it in one pass?
""",
    examples=[
        {"args": {"head": [10, 20, 30, 40, 50], "n": 2}, "output": [10, 20, 30, 50]},
        {"args": {"head": [4], "n": 1}, "output": []},
        {"args": {"head": [4, 8], "n": 2}, "output": [8], "explain": "Removing the head itself."},
    ],
    constraints=["1 ≤ number of nodes ≤ 30", "1 ≤ n ≤ number of nodes"],
    companies={"Meta": 4, "Amazon": 4, "Google": 3, "Microsoft": 3, "Apple": 2, "Bloomberg": 2, "Adobe": 2},
    topics=["Linked List", "Two Pointers"],
    hints=[
        "Two passes work: count the length, then walk to the node before the target.",
        "For one pass: if one pointer starts n nodes ahead of another, where is the trailing one when the leader reaches the end?",
        "Start both at a dummy node before the head so removing the head needs no special case.",
    ],
    insight={
        "pattern": "Gap of n between two pointers",
        "oneLiner": "Advance `right` n steps, then move both until `right` is None; `left` is just before the target.",
        "mnemonic": "Same speed, fixed gap.",
        "why": "Keeping a constant gap converts 'n-th from the end' into a position you can reach in one pass. "
               "The dummy node gives the head a predecessor.",
        "signals": ["\"from the end\"", "one pass over a singly linked list"],
        "recall": [
            {"q": "Where do left and right start?", "a": "left at a dummy before head, right at head; then right moves n steps."},
            {"q": "Why the dummy node?", "a": "When n equals the length, the head is removed - the dummy is its predecessor."},
        ],
    },
    solutions=[
        Solution("two-pass", "Count, then remove", "O(n)", "O(1)", TWO_PASS,
                 "Find the length first, then walk to the node before the target."),
        Solution("one-pass", "Two pointers with a gap", "O(n)", "O(1)", ONE_PASS,
                 "Keep a gap of n nodes between two pointers so the trailing one stops right before the target.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("remove-head", "Crashed when removing the head",
                "When n equals the list length, the head itself goes. A dummy node before the head handles it.",
                error="AttributeError: 'NoneType'"),
        Pitfall("off-by-one", "Removed the wrong node",
                "Check the gap: after moving right n steps from head (with left at the dummy), left stops just before the target.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e) and x != e),
    ],
    edge_cases=[{"head": [1], "n": 1}, {"head": [1, 2], "n": 1}, {"head": [1, 2], "n": 2}, {"head": [1, 2, 3], "n": 3}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    worst_case=worst_case,
    big=30,
    lesson={"head": [10, 20, 30, 40, 50], "n": 2},
    related=["linked-list-cycle", "reorder-list"],
)
