from feetcode.problem import Pitfall, Problem, Solution, sig

PAIRS = {"(": ")", "[": "]", "{": "}"}


def _balanced(rng, pairs):
    if pairs == 0:
        return ""
    inner = rng.randint(0, pairs - 1)
    o = rng.choice("([{")
    return o + _balanced(rng, inner) + PAIRS[o] + _balanced(rng, pairs - 1 - inner)


def generate(rng, n):
    n = max(1, n)
    s = _balanced(rng, max(1, n // 2))
    roll = rng.random()
    if roll < 0.4:
        return {"s": s}
    chars = list(s)
    if roll < 0.7:
        i = rng.randrange(len(chars))
        chars[i] = rng.choice("()[]{}")               # one wrong bracket
    elif roll < 0.85:
        chars.insert(rng.randrange(len(chars) + 1), rng.choice("([{"))  # an unclosed opener
    else:
        rng.shuffle(chars)                             # right counts, wrong order
    return {"s": "".join(chars)}


def validate(args):
    s = args["s"]
    return len(s) >= 1 and all(c in "()[]{}" for c in s)


def worst_case(n):
    k = max(1, n // 2)
    return {"s": "(" * k + ")" * k}


def _counts_balanced(s):
    return all(s.count(o) == s.count(c) for o, c in PAIRS.items())


REPLACE = '''class Solution:
    def isValid(self, s: str) -> bool:
        while "()" in s or "[]" in s or "{}" in s:  #> {s} still has an adjacent matching pair. || No adjacent pairs remain in {s}.
            s = s.replace("()", "").replace("[]", "").replace("{}", "")  #> Delete every adjacent pair: {s}.
        return s == ""  #> {"Everything cancelled out - valid." if _return else "Brackets are left over - invalid."}
'''

STACK = '''class Solution:
    def isValid(self, s: str) -> bool:
        match = {")": "(", "]": "[", "}": "{"}  #> Each closer and the opener it needs.
        stack = []  #> Openers still waiting for their closer. The most recent is on top.
        for ch in s:  #> Read {ch}.
            if ch in match:  #> {ch} is a closer - it must match the most recent unclosed opener. || {ch} is an opener - push it.
                if not stack or stack.pop() != match[ch]:  #> Nothing to match, or the top opener is the wrong kind - invalid. || The top was {match[ch]}: matched and popped. Stack: {stack}. #! Last opened, first closed. Brackets nest, and nesting is exactly what a stack models: the innermost open bracket is always on top.
                    return False  #~
            else:
                stack.append(ch)  #> Stack: {stack}.
        return not stack  #> {"Every opener was closed - valid." if _return else "Unclosed openers remain - invalid."}
'''

PROBLEM = Problem(
    id="valid-parentheses",
    number=20,
    slug="valid-parentheses",
    title="Valid Parentheses",
    difficulty="Easy",
    pattern="stack",
    order=1,
    signature=sig("isValid", "bool", s="str"),
    statement="""
`s` contains only the characters `(`, `)`, `[`, `]`, `{` and `}`. Return `true` if the brackets are **valid**:

1. Every opening bracket is closed by a bracket of the same type.
2. Brackets close in the correct order - the most recently opened one closes first.
3. Every closing bracket has a matching opener before it.
""",
    examples=[
        {"args": {"s": "{[()]}()"}, "output": True},
        {"args": {"s": "([)]"}, "output": False, "explain": "Counts match, but ']' arrives while '(' is still open."},
        {"args": {"s": "(("}, "output": False},
    ],
    constraints=["1 ≤ s.length ≤ 10⁴", "s consists of '()[]{}' only."],
    companies={"Amazon": 5, "Meta": 4, "Google": 4, "Microsoft": 4, "Bloomberg": 4, "LinkedIn": 3, "Apple": 3,
               "Spotify": 2, "Uber": 2},
    topics=["String", "Stack"],
    hints=[
        "Counting each bracket type isn't enough - \"([)]\" has equal counts. What extra information matters?",
        "When you see a closer, which opener must it match?",
        "Push openers on a stack; on a closer, pop and check the type. At the end the stack must be empty.",
    ],
    insight={
        "pattern": "Stack for nesting",
        "oneLiner": "Push openers; every closer must match the top of the stack; valid iff the stack ends empty.",
        "mnemonic": "Last opened, first closed.",
        "why": "Valid bracket strings are nested structures, and the innermost unclosed bracket is exactly the stack's top.",
        "signals": ["matching pairs", "nesting", "\"most recent unmatched\""],
        "recall": [
            {"q": "Two ways a closer can fail?", "a": "The stack is empty, or the top opener is a different type."},
            {"q": "What's the final check?", "a": "The stack must be empty - leftover openers mean invalid."},
        ],
    },
    solutions=[
        Solution("replace", "Delete adjacent pairs", "O(n²)", "O(n)", REPLACE,
                 "Repeatedly remove '()', '[]' and '{}' until nothing changes. Valid strings vanish completely."),
        Solution("stack", "Stack", "O(n)", "O(n)", STACK,
                 "Push openers; a closer must match and pop the top.", optimal=True),
    ],
    pitfalls=[
        Pitfall("leftover", "Forgot unclosed openers",
                "Return `not stack` at the end - '((' never fails a match but is still invalid.",
                detect=lambda a, e, x: e is False and x is True
                and sum(a["s"].count(o) for o in "([{") > sum(a["s"].count(c) for c in ")]}")),
        Pitfall("counting", "Counted instead of matching",
                "Equal counts aren't enough: in '([)]' the brackets close in the wrong order.",
                detect=lambda a, e, x: e is False and x is True and _counts_balanced(a["s"])),
        Pitfall("empty-pop", "Popped an empty stack",
                "A closer can arrive when nothing is open (e.g. ')('). Check the stack before popping.",
                error="IndexError: pop from empty list"),
    ],
    edge_cases=[{"s": "("}, {"s": ")"}, {"s": "()"}, {"s": "]["}, {"s": "(){}}{"}, {"s": "(]"}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"s": "{[()]}("},
    lens={"stacks": ["stack"], "arrays": {"s": {"pointers": []}}},
    related=["generate-parentheses", "min-stack"],
)
