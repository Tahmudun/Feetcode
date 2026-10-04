from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    head = ints(rng, max(1, n), 0, 9)
    return {"head": head, "k": rng.randint(1, len(head))}


def validate(args):
    return len(args["head"]) >= 1 and 1 <= args["k"] <= len(args["head"])


def shrink(args):
    head, k = args["head"], args["k"]
    for i in range(len(head) - 1, -1, -1):
        rest = head[:i] + head[i + 1:]
        if rest:
            yield {"head": rest, "k": min(k, len(rest))}
    if k > 1:
        yield {"head": head, "k": k - 1}


def worst_case(n):
    return {"head": list(range(max(1, n))), "k": 3}


VALUES = '''class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        vals = []
        node = head
        while node:  #~
            vals.append(node.val)  #~
            node = node.next  #~
        for i in range(0, len(vals) - k + 1, k):  #~
            vals[i:i + k] = vals[i:i + k][::-1]  #> Reverse the chunk at {i}: {vals}.
        node = head
        for v in vals:  #~
            node.val = v  #~
            node = node.next  #~
        return head  #> Rewrote the values. (Interviewers usually forbid this: the nodes themselves must move.)
'''

IN_PLACE = '''class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        dummy = ListNode(0, head)  #> A dummy before the head, so the first group has a predecessor like every other group.
        group_prev = dummy  #~
        while True:  #~
            kth = group_prev  #~
            for _ in range(k):  #~
                kth = kth.next  #~
                if not kth:  #~
                    return dummy.next  #> Fewer than {k} nodes remain - they stay as they are. Done.
            group_next = kth.next  #> The group ends at {kth.val}; the next group starts at {group_next.val if group_next else None}.
            prev, curr = group_next, group_prev.next  #> Reverse the group. prev starts at the NEXT group, so the reversed group's tail is already attached.
            while curr is not group_next:  #~
                nxt = curr.next  #~
                curr.next = prev  #~
                prev, curr = curr, nxt  #~
            first = group_prev.next  #> Reversed: {kth.val} is now the group's first node and {first.val} its last.
            group_prev.next = kth  #> Reconnect: the node before the group now points to {kth.val}.
            group_prev = first  #> {first.val} is the new tail of the group - it becomes group_prev for the next round. #! Reversing a sublist in place needs four handles: the node before the group, the group's first and last nodes, and the node after it. Lose one and the list falls apart.
'''

PROBLEM = Problem(
    id="reverse-nodes-in-k-group",
    number=25,
    slug="reverse-nodes-in-k-group",
    title="Reverse Nodes in k-Group",
    difficulty="Hard",
    pattern="linked-list",
    order=11,
    signature=sig("reverseKGroup", "Optional[ListNode]", head="Optional[ListNode]", k="int"),
    statement="""
Given the `head` of a linked list, reverse the nodes **`k` at a time** and return the modified list. If the number of nodes left at the end is less than `k`, leave them in their original order.

You must rearrange the nodes themselves - don't just rewrite the values.
""",
    examples=[
        {"args": {"head": [1, 2, 3, 4, 5], "k": 2}, "output": [2, 1, 4, 3, 5]},
        {"args": {"head": [1, 2, 3, 4, 5], "k": 3}, "output": [3, 2, 1, 4, 5]},
        {"args": {"head": [7, 8], "k": 1}, "output": [7, 8]},
    ],
    constraints=["1 ≤ k ≤ number of nodes ≤ 5000", "0 ≤ Node.val ≤ 1000"],
    companies={"Amazon": 4, "Microsoft": 4, "Meta": 3, "Google": 3, "Bloomberg": 3, "Apple": 2, "Capital One": 2},
    topics=["Linked List", "Recursion"],
    hints=[
        "Before reversing a group, check that k nodes actually exist.",
        "Reversing one group is ordinary list reversal - but you must reconnect it to what comes before and after.",
        "Track group_prev (node before the group) and group_next (node after). Reverse with prev starting at group_next.",
    ],
    insight={
        "pattern": "Sublist reversal with a dummy and group anchors",
        "oneLiner": "For each full group: find its kth node, reverse it with prev = the node after the group, then hook group_prev to the new first node.",
        "mnemonic": "Count k, flip k, stitch both ends.",
        "why": "Starting the reversal's prev at group_next attaches the reversed group's tail automatically; one more assignment fixes its head.",
        "signals": ["reverse in chunks", "swap nodes in pairs (k = 2)", "in-place list surgery"],
        "recall": [
            {"q": "What does prev start as when reversing a group?", "a": "The node right after the group (group_next)."},
            {"q": "After reversing, what becomes group_prev?", "a": "The group's original first node, now its last."},
        ],
    },
    solutions=[
        Solution("values", "Rewrite the values", "O(n)", "O(n)", VALUES,
                 "Reverse chunks of the value list and write them back. Gets the right output but doesn't move nodes."),
        Solution("in-place", "Reverse each group in place", "O(n)", "O(1)", IN_PLACE,
                 "Find each full group, reverse it, and stitch it between its neighbours.", optimal=True),
    ],
    pitfalls=[
        Pitfall("partial-group", "Reversed the final short group",
                "Leave a final group with fewer than k nodes untouched - check that k nodes exist first.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e) and x != e
                and len(a["head"]) % a["k"] != 0 and x[:len(x) - len(a["head"]) % a["k"]] == e[:len(e) - len(a["head"]) % a["k"]]),
        Pitfall("lost-nodes", "Lost nodes while relinking",
                "Connect group_prev to the new first node and the old first node to group_next.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) < len(e)),
    ],
    edge_cases=[{"head": [1], "k": 1}, {"head": [1, 2], "k": 2}, {"head": [1, 2, 3], "k": 2}, {"head": [1, 2, 3, 4], "k": 4}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    worst_case=worst_case,
    lesson={"head": [1, 2, 3, 4, 5], "k": 2},
    related=["reverse-linked-list", "reorder-list"],
)
