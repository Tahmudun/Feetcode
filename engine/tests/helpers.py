"""Tiny inline problems so engine tests don't depend on the content bank."""
from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def gen_nums(rng, n):
    return {"nums": ints(rng, n, -5, 5)}


SUM = Problem(
    id="sum", number=0, title="Sum", difficulty="Easy", pattern="arrays-hashing", order=0,
    signature=sig("total", "int", nums="List[int]"),
    statement="", examples=[{"args": {"nums": [1, 2, 3]}}],
    solutions=[Solution("ref", "ref", "O(n)", "O(1)",
                        "class Solution:\n    def total(self, nums):\n        return sum(nums)\n", optimal=True)],
    generate=gen_nums,
    pitfalls=[Pitfall("off-by-one", "Skipped the last element", "range(len(nums) - 1) misses the end.",
                      detect=lambda a, e, x: a["nums"] and x == e - a["nums"][-1])],
)

REVERSE = Problem(
    id="rev", number=0, title="Reverse", difficulty="Easy", pattern="linked-list", order=0,
    signature=sig("reverseList", "Optional[ListNode]", head="Optional[ListNode]"),
    statement="", examples=[{"args": {"head": [1, 2, 3]}}],
    solutions=[Solution("ref", "ref", "O(n)", "O(1)", """class Solution:
    def reverseList(self, head):
        prev, curr = None, head
        while curr:
            nxt = curr.next
            curr.next = prev
            prev, curr = curr, nxt
        return prev
""", optimal=True)],
    generate=lambda rng, n: {"head": ints(rng, n, 0, 9)},
)

STACK = Problem(
    id="stk", number=0, title="Stack", difficulty="Easy", pattern="stack", order=0,
    signature=sig("", "", kind="design", cls="Stk"),
    statement="", examples=[{"args": {"ops": ["Stk", "push", "push", "top", "pop", "top"],
                                      "args": [[], [1], [2], [], [], []]}}],
    solutions=[Solution("ref", "ref", "O(1)", "O(n)", """class Stk:
    def __init__(self):
        self.items = []
    def push(self, x):
        self.items.append(x)
    def pop(self):
        self.items.pop()
    def top(self):
        return self.items[-1]
""", optimal=True)],
    generate=lambda rng, n: {"ops": ["Stk"] + ["push"] * max(1, n) + ["top"], "args": [[]] + [[i] for i in range(max(1, n))] + [[]]},
)

CODEC = Problem(
    id="codec", number=0, title="Codec", difficulty="Medium", pattern="arrays-hashing", order=0,
    signature=sig("", "List[str]", kind="codec", strs="List[str]"),
    statement="", examples=[{"args": {"strs": ["a", "b"]}}],
    solutions=[Solution("ref", "ref", "O(n)", "O(n)", """class Solution:
    def encode(self, strs):
        return "".join(f"{len(s)}#{s}" for s in strs)
    def decode(self, s):
        out, i = [], 0
        while i < len(s):
            j = s.index("#", i)
            n = int(s[i:j])
            out.append(s[j + 1:j + 1 + n])
            i = j + 1 + n
        return out
""", optimal=True)],
    generate=lambda rng, n: {"strs": ["".join(rng.choice("a#1,") for _ in range(rng.randint(0, 3))) for _ in range(n)]},
)
