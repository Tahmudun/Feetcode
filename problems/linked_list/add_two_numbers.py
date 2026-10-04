from feetcode.problem import Pitfall, Problem, Solution, sig


def _digits(rng, k):
    if k <= 1:
        return [rng.randint(0, 9)]
    return [rng.randint(0, 9) for _ in range(k - 1)] + [rng.randint(1, 9)]


def generate(rng, n):
    a = _digits(rng, rng.randint(1, max(1, n)))
    b = _digits(rng, rng.randint(1, max(1, n)))
    if rng.random() < 0.3:  # lots of carries
        a = [9] * len(a)
    return {"l1": a, "l2": b}


def validate(args):
    for v in (args["l1"], args["l2"]):
        if not v or any(not 0 <= d <= 9 for d in v) or (len(v) > 1 and v[-1] == 0):
            return False
    return True


def worst_case(n):
    return {"l1": [9] * max(1, n), "l2": [1]}


DIGITS = '''class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode()  #> Digits are stored least-significant first - exactly the order we add them by hand.
        tail = dummy
        carry = 0
        while l1 or l2 or carry:  #~
            a = l1.val if l1 else 0  #~
            b = l2.val if l2 else 0  #~
            carry, digit = divmod(a + b + carry, 10)  #> {a} + {b} + carry → write {digit}, carry {carry}. #! divmod by 10 splits a column sum into the digit to write and the carry - just like column addition on paper.
            tail.next = ListNode(digit)  #~
            tail = tail.next  #~
            l1 = l1.next if l1 else None  #~
            l2 = l2.next if l2 else None  #~
        return dummy.next  #> The loop also ran for a final carry, so nothing is lost.
'''

AS_INTEGERS = '''class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        def to_int(node):
            value, place = 0, 1
            while node:  #~
                value += node.val * place  #~
                place *= 10  #~
                node = node.next  #~
            return value  #> Read the digits back into the number {_return}.
        total = to_int(l1) + to_int(l2)  #> Add them as ordinary integers: {total}. (Works in Python because ints have no size limit - in most languages this overflows.)
        dummy = tail = ListNode()
        for ch in reversed(str(total)):  #~
            tail.next = ListNode(int(ch))  #~
            tail = tail.next  #~
        return dummy.next
'''

PROBLEM = Problem(
    id="add-two-numbers",
    number=2,
    slug="add-two-numbers",
    title="Add Two Numbers",
    difficulty="Medium",
    pattern="linked-list",
    order=7,
    signature=sig("addTwoNumbers", "Optional[ListNode]", l1="Optional[ListNode]", l2="Optional[ListNode]"),
    statement="""
Two non-negative integers are stored as linked lists of digits in **reverse order** (the ones digit first). For example `[3, 4, 2]` represents 243.

Return their **sum** as a linked list in the same reversed format. The numbers have no leading zeros, except the number 0 itself.
""",
    examples=[
        {"args": {"l1": [3, 4, 2], "l2": [4, 6, 5]}, "output": [7, 0, 8], "explain": "243 + 564 = 807."},
        {"args": {"l1": [9, 9], "l2": [1]}, "output": [0, 0, 1], "explain": "99 + 1 = 100: the final carry adds a digit."},
        {"args": {"l1": [0], "l2": [0]}, "output": [0]},
    ],
    constraints=["1 ≤ number of nodes in each list ≤ 100", "0 ≤ Node.val ≤ 9", "No leading zeros (except 0 itself)."],
    companies={"Amazon": 5, "Microsoft": 4, "Bloomberg": 4, "Meta": 3, "Google": 3, "Apple": 3, "Adobe": 2, "Uber": 2},
    topics=["Linked List", "Math", "Recursion"],
    hints=[
        "The lists are already in the order you add digits by hand: ones first.",
        "Walk both lists together, adding digit + digit + carry. What if one list is shorter?",
        "Keep looping while either list has nodes OR there is a carry left over.",
    ],
    insight={
        "pattern": "Column addition with carry",
        "oneLiner": "Add digit by digit with a carry, treating a missing digit as 0, and keep going while a carry remains.",
        "mnemonic": "Add, divmod, carry on.",
        "why": "Reverse order means the lists start at the ones place, so one simultaneous walk mirrors pencil-and-paper addition.",
        "signals": ["numbers stored as digit lists", "big-number arithmetic without converting"],
        "recall": [
            {"q": "Loop condition?", "a": "while l1 or l2 or carry."},
            {"q": "Why not convert to integers?", "a": "In fixed-width languages they overflow; digit-by-digit works for any length."},
        ],
    },
    solutions=[
        Solution("as-integers", "Convert to integers", "O(n)", "O(n)", AS_INTEGERS,
                 "Turn both lists into numbers, add, and convert back. Leans on Python's arbitrary-precision ints."),
        Solution("digits", "Digit-by-digit with carry", "O(n)", "O(1)", DIGITS,
                 "Walk both lists at once, adding digits and a carry, like column addition.", optimal=True),
    ],
    pitfalls=[
        Pitfall("final-carry", "Dropped the final carry",
                "99 + 1 needs a new leading digit: keep looping while carry is non-zero.",
                detect=lambda a, e, x: isinstance(x, list) and x == e[:-1] and e[-1] == 1),
        Pitfall("unequal-lengths", "Stopped when the shorter list ended",
                "Treat a finished list's digit as 0 and continue with the longer one.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) < len(e) - 1),
    ],
    edge_cases=[{"l1": [0], "l2": [0]}, {"l1": [9, 9, 9, 9], "l2": [9, 9]}, {"l1": [5], "l2": [5]}, {"l1": [1, 8], "l2": [0]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    size_of=lambda a: max(len(a["l1"]), len(a["l2"])),
    big=100,
    lesson={"l1": [9, 4, 2], "l2": [4, 6, 9]},
    related=["merge-two-sorted-lists"],
)
