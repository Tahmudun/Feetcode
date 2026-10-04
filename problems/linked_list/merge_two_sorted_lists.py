from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    a = sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, n)))
    b = sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, n)))
    return {"list1": a, "list2": b}


def validate(args):
    return args["list1"] == sorted(args["list1"]) and args["list2"] == sorted(args["list2"])


def shrink(args):
    for name in ("list1", "list2"):
        v = args[name]
        for i in range(len(v) - 1, -1, -1):
            yield {**args, name: v[:i] + v[i + 1:]}


def worst_case(n):
    return {"list1": list(range(0, 2 * n, 2)), "list2": list(range(1, 2 * n, 2))}


ITERATIVE = '''class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode()  #> A dummy node in front of the result - the first real node needs no special case.
        tail = dummy  #~
        while list1 and list2:  #~
            if list1.val <= list2.val:  #> {list1.val} ≤ {list2.val}: take the node from list1. || {list2.val} < {list1.val}: take the node from list2.
                tail.next = list1  #~
                list1 = list1.next  #~
            else:
                tail.next = list2  #~
                list2 = list2.next  #~
            tail = tail.next  #> Appended {tail.val}.
        tail.next = list1 or list2  #> One list ran out - attach whatever remains of the other in a single step. #! The remainder is already sorted and already linked, so there's nothing to copy: one pointer assignment finishes the merge.
        return dummy.next  #> Skip the dummy and return the merged head.
'''

RECURSIVE = '''class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        if not list1:  #> list1 is empty - the answer is list2. ||
            return list2  #~
        if not list2:  #> list2 is empty - the answer is list1. ||
            return list1  #~
        if list1.val <= list2.val:  #> {list1.val} ≤ {list2.val}: {list1.val} goes first; merge the rest behind it. || {list2.val} < {list1.val}: {list2.val} goes first.
            list1.next = self.mergeTwoLists(list1.next, list2)  #~
            return list1  #~
        list2.next = self.mergeTwoLists(list1, list2.next)  #~
        return list2  #~
'''

PROBLEM = Problem(
    id="merge-two-sorted-lists",
    number=21,
    slug="merge-two-sorted-lists",
    title="Merge Two Sorted Lists",
    difficulty="Easy",
    pattern="linked-list",
    order=2,
    signature=sig("mergeTwoLists", "Optional[ListNode]", list1="Optional[ListNode]", list2="Optional[ListNode]"),
    statement="""
Given the heads of two **sorted** linked lists `list1` and `list2`, merge them into one sorted list by **splicing their nodes together**, and return its head.
""",
    examples=[
        {"args": {"list1": [1, 3, 8], "list2": [2, 3, 4]}, "output": [1, 2, 3, 3, 4, 8]},
        {"args": {"list1": [], "list2": [5]}, "output": [5]},
        {"args": {"list1": [], "list2": []}, "output": []},
    ],
    constraints=["0 ≤ number of nodes in each list ≤ 50", "−100 ≤ Node.val ≤ 100", "Both lists are sorted ascending."],
    companies={"Amazon": 5, "Microsoft": 4, "Google": 4, "Apple": 4, "Meta": 3, "Bloomberg": 3, "Adobe": 3,
               "Oracle": 2, "Uber": 2},
    topics=["Linked List", "Recursion"],
    hints=[
        "The smaller of the two heads must come first. Then what?",
        "Keep a `tail` pointer for the merged list and repeatedly attach the smaller current node.",
        "A dummy node before the result removes the special case for the first node. Attach the leftover list at the end.",
    ],
    insight={
        "pattern": "Dummy node + tail pointer",
        "oneLiner": "Start from a dummy node; repeatedly append the smaller head; finally attach the non-empty remainder.",
        "mnemonic": "Dummy first, compare heads, glue the leftovers.",
        "why": "Each comparison places exactly one node, so it's O(n + m). The dummy makes the empty-result and first-node cases disappear.",
        "signals": ["merging sorted sequences", "building a new list from existing nodes"],
        "recall": [
            {"q": "Why a dummy node?", "a": "So 'append to the result' works the same for the first node; return dummy.next."},
            {"q": "What happens when one list runs out?", "a": "Attach the other's remainder directly - it's already sorted."},
        ],
    },
    solutions=[
        Solution("recursive", "Recursion", "O(n + m)", "O(n + m)", RECURSIVE,
                 "The smaller head comes first; its next is the merge of the rest."),
        Solution("iterative", "Dummy node + tail", "O(n + m)", "O(1)", ITERATIVE,
                 "Append the smaller node to a tail pointer until one list is empty.", optimal=True),
    ],
    pitfalls=[
        Pitfall("dropped-remainder", "Dropped the leftover nodes",
                "When one list runs out, attach the rest of the other: tail.next = list1 or list2.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) < len(e)),
        Pitfall("unstable", "Merged out of order",
                "Compare the current heads each step and take the smaller one.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e) and x != e),
    ],
    edge_cases=[{"list1": [], "list2": []}, {"list1": [1], "list2": []}, {"list1": [2], "list2": [1]},
                {"list1": [1, 1], "list2": [1, 1]}, {"list1": [-3, 10], "list2": [-5, 0, 0, 100]}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    worst_case=worst_case,
    size_of=lambda a: len(a["list1"]) + len(a["list2"]),
    lesson={"list1": [1, 3, 8], "list2": [2, 3, 4]},
    related=["merge-k-sorted-lists", "reverse-linked-list"],
)
