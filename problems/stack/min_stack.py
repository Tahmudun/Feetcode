from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    ops, args, size = ["MinStack"], [[]], 0
    for _ in range(max(1, n)):
        choices = ["push"] if size == 0 else ["push", "push", "pop", "top", "getMin", "getMin"]
        op = rng.choice(choices)
        if op == "push":
            ops.append("push")
            args.append([rng.randint(-5, 5) if rng.random() < 0.7 else rng.randint(-2**31, 2**31 - 1)])
            size += 1
        else:
            ops.append(op)
            args.append([])
            size -= op == "pop"
    return {"ops": ops, "args": args}


def validate(args):
    ops, argv = args["ops"], args["args"]
    if not ops or ops[0] != "MinStack" or len(ops) != len(argv):
        return False
    size = 0
    for op, a in zip(ops[1:], argv[1:]):
        if op == "push":
            if len(a) != 1:
                return False
            size += 1
        elif op in ("pop", "top", "getMin"):
            if size == 0 or a:
                return False
            size -= op == "pop"
        else:
            return False
    return True


def worst_case(n):
    half = max(1, n // 2)
    ops = ["MinStack"] + ["push"] * half + ["getMin"] * half
    args = [[]] + [[half - i] for i in range(half)] + [[] for _ in range(half)]
    return {"ops": ops, "args": args}


SCAN = '''class MinStack:
    def __init__(self):
        self.stack = []

    def push(self, val: int) -> None:
        self.stack.append(val)  #> Push {val}. Stack: {self.stack}.

    def pop(self) -> None:
        self.stack.pop()  #> Pop. Stack: {self.stack}.

    def top(self) -> int:
        return self.stack[-1]  #> Top: {_return}.

    def getMin(self) -> int:
        return min(self.stack)  #> Scan all {len(self.stack)} elements for the minimum: {_return}. That's O(n) per call.
'''

TWO_STACKS = '''class MinStack:
    def __init__(self):
        self.stack = []
        self.mins = []  #> mins[i] will hold the minimum of stack[0..i]. The two stacks always have the same height.

    def push(self, val: int) -> None:
        self.stack.append(val)  #> Push {val}.
        self.mins.append(min(val, self.mins[-1]) if self.mins else val)  #> The minimum at this height is {self.mins[-1]}. mins: {self.mins}. #! Store the running minimum next to every element. When an element is popped, the minimum *below* it is already sitting on top of mins - nothing to recompute.

    def pop(self) -> None:
        self.stack.pop()  #~
        self.mins.pop()  #> Pop both stacks together. Stack: {self.stack}, mins: {self.mins}.

    def top(self) -> int:
        return self.stack[-1]  #> Top: {_return}.

    def getMin(self) -> int:
        return self.mins[-1]  #> The minimum is simply mins' top, in O(1): {_return}.
'''

PROBLEM = Problem(
    id="min-stack",
    number=155,
    slug="min-stack",
    title="Min Stack",
    difficulty="Medium",
    pattern="stack",
    order=2,
    signature=sig("", "List", kind="design", cls="MinStack"),
    statement="""
Design a stack that, besides the usual operations, can report its **minimum element in O(1) time**. Implement `MinStack`:

- `MinStack()` creates an empty stack.
- `push(val)` pushes `val`.
- `pop()` removes the top element.
- `top()` returns the top element.
- `getMin()` returns the smallest element currently in the stack.

`pop`, `top` and `getMin` are only called on a non-empty stack. Every operation should run in O(1).

The input is a list of operations and their arguments; the output lists each call's return value (`null` for none).
""",
    examples=[
        {"args": {"ops": ["MinStack", "push", "push", "push", "getMin", "pop", "top", "getMin"],
                  "args": [[], [4], [-1], [6], [], [], [], []]},
         "output": [None, None, None, None, -1, None, -1, -1]},
        {"args": {"ops": ["MinStack", "push", "push", "getMin", "pop", "getMin"], "args": [[], [2], [1], [], [], []]},
         "output": [None, None, None, 1, None, 2],
         "explain": "After popping 1, the minimum must go back to 2."},
    ],
    constraints=["−2³¹ ≤ val ≤ 2³¹ − 1", "pop, top and getMin are called on non-empty stacks only.",
                 "At most 3 · 10⁴ calls."],
    companies={"Amazon": 5, "Bloomberg": 4, "Microsoft": 3, "Google": 3, "Meta": 3, "Apple": 2, "Oracle": 2,
               "Goldman Sachs": 2},
    topics=["Stack", "Design"],
    hints=[
        "A single `min` variable breaks when the minimum is popped - what should the min become then?",
        "The minimum depends only on what's *below* the top. Can you remember the minimum at every height?",
        "Keep a second stack: when pushing val, push min(val, current min). Pop both together.",
    ],
    insight={
        "pattern": "Augmented stack",
        "oneLiner": "Store, alongside each element, the minimum of everything at or below it; getMin is the top of that record.",
        "mnemonic": "Each floor remembers the lowest floor beneath it.",
        "why": "A stack only changes at the top, so the minimum of the remaining elements after a pop was already computed when they were pushed.",
        "signals": ["\"retrieve min/max in O(1)\"", "stack with an extra query"],
        "recall": [
            {"q": "What do you push onto the min stack?", "a": "min(val, current minimum) - so its top is always the stack's minimum."},
            {"q": "Why does a single min variable fail?", "a": "After popping the minimum you'd need the second smallest, which you no longer know."},
        ],
    },
    solutions=[
        Solution("scan", "Scan on getMin", "O(n) getMin", "O(n)", SCAN,
                 "A plain list; getMin scans everything with min()."),
        Solution("two-stacks", "Stack of running minimums", "O(1)", "O(n)", TWO_STACKS,
                 "Keep a parallel stack of minimums so every operation is O(1).", optimal=True),
    ],
    pitfalls=[
        Pitfall("stale-min", "The minimum wasn't restored after a pop",
                "A single min variable can't recover the previous minimum. Remember the minimum at every height.",
                detect=lambda a, e, x: isinstance(x, list) and "pop" in a["ops"] and x != e),
    ],
    edge_cases=[
        {"ops": ["MinStack", "push", "getMin"], "args": [[], [7], []]},
        {"ops": ["MinStack", "push", "push", "push", "getMin", "pop", "getMin"], "args": [[], [0], [1], [0], [], [], []]},
        {"ops": ["MinStack", "push", "push", "pop", "push", "getMin", "top"], "args": [[], [-2], [-3], [], [5], [], []]},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"ops": ["MinStack", "push", "push", "push", "getMin", "pop", "getMin", "top"],
            "args": [[], [5], [2], [8], [], [], [], []]},
    lens={"stacks": ["self.stack", "self.mins"]},
    related=["valid-parentheses", "lru-cache"],
)
