from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    return {"n": max(1, min(6, n))}


def validate(args):
    return 1 <= args["n"] <= 8


def shrink(args):
    for k in range(1, args["n"]):
        yield {"n": k}


def _ok(s):
    bal = 0
    for ch in s:
        bal += 1 if ch == "(" else -1
        if bal < 0:
            return False
    return bal == 0


BRUTE = '''class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        res = []
        for bits in product("()", repeat=2 * n):  #~
            s = "".join(bits)  #~
            bal = 0  #~
            for ch in s:  #~
                bal += 1 if ch == "(" else -1  #~
                if bal < 0:  #~
                    break  #~
            if bal == 0:  #~
                res.append(s)  #> {s} is balanced. {len(res)} found so far, out of {4 ** n} strings generated.
        return res  #> Generated all {4 ** n} strings to keep {len(_return)}.
'''

BACKTRACK = '''class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        res = []
        path = []  #> The string under construction, one bracket at a time.

        def backtrack(opened, closed):
            if len(path) == 2 * n:  #> {"".join(path)} is complete - record it. ||
                res.append("".join(path))  #~
                return  #~
            if opened < n:  #> {opened} of {n} openers used - '(' is allowed. || All {n} openers are used.
                path.append("(")  #> Choose '(': {"".join(path)}
                backtrack(opened + 1, closed)  #~
                path.pop()  #> Undo the '(' - back to {"".join(path) or "(empty)"}. #! Backtracking: make a choice, explore everything that follows, then undo it so the next choice starts from the same state.
            if closed < opened:  #> {closed} closers < {opened} openers - a ')' has something to match. || {closed} closers = {opened} openers - a ')' now would be unmatched. #! These two rules are the only constraints: never more than n openers, and never more closers than openers. Every path that obeys them ends in a valid string, so nothing is generated and then thrown away.
                path.append(")")  #> Choose ')': {"".join(path)}
                backtrack(opened, closed + 1)  #~
                path.pop()  #> Undo the ')' - back to {"".join(path) or "(empty)"}.

        backtrack(0, 0)
        return res  #> All {len(_return)} valid strings.
'''

PROBLEM = Problem(
    id="generate-parentheses",
    number=22,
    slug="generate-parentheses",
    title="Generate Parentheses",
    difficulty="Medium",
    pattern="stack",
    order=4,
    signature=sig("generateParenthesis", "List[str]", n="int"),
    statement="""
Given `n`, return **every well-formed string** made of `n` pairs of parentheses. Any order is fine.

A string is well-formed when every `(` is closed by a later `)` and no `)` appears without an open `(` before it.
""",
    examples=[
        {"args": {"n": 2}, "output": ["(())", "()()"]},
        {"args": {"n": 1}, "output": ["()"]},
        {"args": {"n": 3}, "output": ["((()))", "(()())", "(())()", "()(())", "()()()"]},
    ],
    constraints=["1 ≤ n ≤ 8"],
    companies={"Google": 4, "Amazon": 4, "Meta": 3, "Microsoft": 3, "Bloomberg": 3, "Apple": 2, "Uber": 2},
    topics=["String", "Dynamic Programming", "Backtracking"],
    hints=[
        "You could generate all 2²ⁿ strings and filter. Can you avoid ever building an invalid prefix?",
        "At any point, when may you add '('? When may you add ')'?",
        "Add '(' while opened < n; add ')' while closed < opened. Recurse, then undo (backtrack).",
    ],
    insight={
        "pattern": "Backtracking with constraints",
        "oneLiner": "Build left to right: '(' if opened < n, ')' if closed < opened. Every completed path is valid.",
        "mnemonic": "Open while you can, close while it matches.",
        "why": "The two rules exactly characterize valid prefixes, so the search never wanders into dead ends - "
               "the work is proportional to the number of answers (the Catalan numbers).",
        "signals": ["\"all combinations/arrangements\"", "valid strings under a rule", "small n (≤ 8-10)"],
        "recall": [
            {"q": "When can you add ')'?", "a": "Only when closed < opened."},
            {"q": "How many results for n = 3?", "a": "5 (the 3rd Catalan number)."},
        ],
    },
    solutions=[
        Solution("brute", "Generate everything, keep the valid ones", "O(2²ⁿ · n)", "O(n)", BRUTE,
                 "Enumerate all 4ⁿ strings of length 2n and keep the balanced ones."),
        Solution("backtrack", "Backtracking", "O(4ⁿ/√n)", "O(n)", BACKTRACK,
                 "Only ever extend a prefix in a way that can still lead to a valid string.", optimal=True),
    ],
    pitfalls=[
        Pitfall("unbalanced", "Generated invalid strings",
                "Only add ')' when closed < opened - otherwise a prefix like '())' slips in.",
                detect=lambda a, e, x: isinstance(x, list) and any(not _ok(s) for s in x if isinstance(s, str))),
        Pitfall("shared-path", "Results changed after being recorded",
                "Appending the same list object (path) records a reference that keeps changing. Store a copy: ''.join(path).",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e) and len(set(map(str, x))) < len(x)),
    ],
    edge_cases=[{"n": 1}, {"n": 4}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    compare="unordered",
    sizes=[2, 3, 4, 5, 6, 7],
    lesson={"n": 2},
    lens={"stacks": ["path"]},
    related=["valid-parentheses"],
)
