from feetcode.problem import Pitfall, Problem, Solution, sig

LIMIT = 2**31


def _eval(tokens, floor=False, swap=False):
    stack = []
    for tok in tokens:
        if tok in ("+", "-", "*", "/"):
            if len(stack) < 2:
                raise ValueError("not enough operands")
            b, a = stack.pop(), stack.pop()
            if swap:
                a, b = b, a
            if tok == "+":
                v = a + b
            elif tok == "-":
                v = a - b
            elif tok == "*":
                v = a * b
            else:
                if b == 0:
                    raise ZeroDivisionError
                v = a // b if floor else int(a / b)
            if not -LIMIT <= v < LIMIT:
                raise OverflowError
            stack.append(v)
        else:
            stack.append(int(tok))
    if len(stack) != 1:
        raise ValueError("leftover operands")
    return stack[0]


def generate(rng, n):
    operands = max(1, n)
    for _ in range(50):
        stack_depth, tokens, placed = 0, [], 0
        while placed < operands or stack_depth > 1:
            if placed < operands and (stack_depth < 2 or rng.random() < 0.55):
                tokens.append(str(rng.randint(-9, 12)))
                placed += 1
                stack_depth += 1
            else:
                tokens.append(rng.choice("+-*/"))
                stack_depth -= 1
        try:
            _eval(tokens)
            return {"tokens": tokens}
        except (ZeroDivisionError, OverflowError, ValueError):
            continue
    return {"tokens": ["1"]}


def validate(args):
    toks = args["tokens"]
    if not toks:
        return False
    try:
        _eval(toks)
        return True
    except (ZeroDivisionError, OverflowError, ValueError):
        return False


def worst_case(n):
    toks = ["1"]
    for i in range(max(0, n // 2)):
        toks += [str(i % 5 + 1), "+-"[i % 2]]
    return {"tokens": toks}


STACK = '''class Solution:
    def evalRPN(self, tokens: List[str]) -> int:
        stack = []  #> Operands waiting for an operator.
        for tok in tokens:  #> Token {tok}.
            if tok in ("+", "-", "*", "/"):  #> {tok} is an operator: it applies to the two most recent operands. || {tok} is a number.
                b = stack.pop()  #~
                a = stack.pop()  #> Pop the right operand {b}, then the left operand {a}. #! Order matters: the top of the stack is the RIGHT operand. "a b -" means a − b.
                if tok == "+":  #~
                    stack.append(a + b)  #> {a} + {b} = {stack[-1]}.
                elif tok == "-":  #~
                    stack.append(a - b)  #> {a} − {b} = {stack[-1]}.
                elif tok == "*":  #~
                    stack.append(a * b)  #> {a} × {b} = {stack[-1]}.
                else:
                    stack.append(int(a / b))  #> {a} ÷ {b}, truncated toward zero = {stack[-1]}. #! int(a / b) truncates toward zero, which the problem requires. a // b floors instead: -7 // 2 is -4, but the answer here is -3.
            else:
                stack.append(int(tok))  #> Push it. Stack: {stack}.
        return stack[0]  #> One value remains - the result: {_return}.
'''

RECURSIVE = '''class Solution:
    def evalRPN(self, tokens: List[str]) -> int:
        def solve():
            tok = tokens.pop()  #> Read {tok} from the end.
            if tok not in ("+", "-", "*", "/"):  #> {tok} is a number - it is its own value. || {tok} is an operator - evaluate its right operand, then its left.
                return int(tok)  #~
            b = solve()  #~
            a = solve()  #~
            if tok == "+":
                return a + b  #> {a} + {b} = {_return}.
            if tok == "-":
                return a - b  #> {a} − {b} = {_return}.
            if tok == "*":
                return a * b  #> {a} × {b} = {_return}.
            return int(a / b)  #> {a} ÷ {b} → {_return}.
        return solve()
'''

PROBLEM = Problem(
    id="evaluate-reverse-polish-notation",
    number=150,
    slug="evaluate-reverse-polish-notation",
    title="Evaluate Reverse Polish Notation",
    difficulty="Medium",
    pattern="stack",
    order=3,
    signature=sig("evalRPN", "int", tokens="List[str]"),
    statement="""
`tokens` is an arithmetic expression in **Reverse Polish Notation** (postfix): each operator comes *after* its two operands. For example `["2", "3", "+"]` means `2 + 3`.

Evaluate it and return the integer result. The operators are `+`, `-`, `*` and `/`; **division truncates toward zero**. The expression is always valid, never divides by zero, and every intermediate value fits in 32 bits.
""",
    examples=[
        {"args": {"tokens": ["3", "4", "+", "2", "*"]}, "output": 14, "explain": "(3 + 4) × 2."},
        {"args": {"tokens": ["5", "1", "2", "+", "4", "*", "+", "3", "-"]}, "output": 14,
         "explain": "5 + (1 + 2) × 4 − 3."},
        {"args": {"tokens": ["7", "-2", "/"]}, "output": -3, "explain": "−3.5 truncates toward zero: −3."},
    ],
    constraints=["1 ≤ tokens.length ≤ 10⁴", "tokens[i] is an operator or an integer in [−200, 200]"],
    companies={"Amazon": 4, "LinkedIn": 4, "Google": 3, "Meta": 3, "Microsoft": 2, "Yandex": 2},
    topics=["Array", "Math", "Stack"],
    hints=[
        "When you read an operator, which values does it apply to?",
        "Keep the numbers you've read on a stack. An operator pops two, combines them, and pushes the result.",
        "Careful with '-' and '/': the first value popped is the RIGHT operand. And truncate toward zero: int(a / b).",
    ],
    insight={
        "pattern": "Operand stack",
        "oneLiner": "Push numbers; each operator pops right then left, applies, and pushes the result.",
        "mnemonic": "Numbers wait on the stack; operators eat two and leave one.",
        "why": "Postfix notation encodes the evaluation order directly - the most recent results are always the next operands.",
        "signals": ["postfix/prefix expressions", "evaluating nested operations"],
        "recall": [
            {"q": "Which popped value is the left operand?", "a": "The second one popped."},
            {"q": "How do you divide with truncation toward zero in Python?", "a": "int(a / b) - not a // b, which floors."},
        ],
    },
    solutions=[
        Solution("recursive", "Recursive evaluation from the end", "O(n)", "O(n)", RECURSIVE,
                 "The last token is the root operator; evaluate its right subtree, then its left, recursively."),
        Solution("stack", "Operand stack", "O(n)", "O(n)", STACK,
                 "Scan left to right, pushing numbers and reducing on operators.", optimal=True),
    ],
    pitfalls=[
        Pitfall("floor-division", "Floored instead of truncating",
                "Python's // floors toward −∞. The problem truncates toward zero: use int(a / b).",
                detect=lambda a, e, x: x != e and x == _floor_eval(a["tokens"])),
        Pitfall("operand-order", "Swapped the operands",
                "The first pop is the RIGHT operand: b = pop(); a = pop(); compute a op b.",
                detect=lambda a, e, x: x != e and x == _swapped_eval(a["tokens"])),
    ],
    edge_cases=[{"tokens": ["42"]}, {"tokens": ["-7", "2", "/"]}, {"tokens": ["4", "13", "5", "/", "+"]},
                {"tokens": ["0", "3", "/"]}, {"tokens": ["2", "1", "-"]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"tokens": ["5", "1", "2", "+", "4", "*", "+", "3", "-"]},
    lens={"stacks": ["stack"], "arrays": {"tokens": {"pointers": []}}},
    related=["valid-parentheses"],
)


def _floor_eval(tokens):
    try:
        return _eval(tokens, floor=True)
    except Exception:  # noqa: BLE001
        return None


def _swapped_eval(tokens):
    try:
        return _eval(tokens, swap=True)
    except Exception:  # noqa: BLE001
        return None
