from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    n = max(1, n)
    return {"temperatures": ints(rng, n, 30, rng.choice((33, 40, 100)))}


def validate(args):
    t = args["temperatures"]
    return len(t) >= 1 and all(30 <= x <= 100 for x in t)


def worst_case(n):
    # Strictly decreasing, then one hot day: brute force scans to the end for every day.
    n = max(1, n)
    return {"temperatures": [30 + (n - i) * 69 // n for i in range(n - 1)] + [100]}


BRUTE = '''class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        res = [0] * len(temperatures)
        for i in range(len(temperatures)):  #> Day {i} ({temperatures[i]}°): scan forward for a warmer day.
            for j in range(i + 1, len(temperatures)):  #~
                if temperatures[j] > temperatures[i]:  #~
                    res[i] = j - i  #> Day {j} is warmer: wait {res[i]} day(s).
                    break  #~
        return res
'''

STACK = '''class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        res = [0] * len(temperatures)
        stack = []  # indices of days still waiting for a warmer day  #> Days still waiting for a warmer day. Their temperatures never increase from bottom to top.
        for i, t in enumerate(temperatures):  #> Day {i}: {t}°.
            while stack and temperatures[stack[-1]] < t:  #> Day {stack[-1]} ({temperatures[stack[-1]]}°) was waiting and {t}° is warmer: its answer is {i} − {stack[-1]} = {i - stack[-1]}. || No waiting day is colder than {t}°. #! Every day is pushed once and popped once - exactly when its warmer day arrives - so the nested loop is O(n) in total.
                j = stack.pop()  #~
                res[j] = i - j  #~
            stack.append(i)  #> Day {i} starts waiting. Waiting days: {stack}.
        return res  #> Days still on the stack never warm up and keep 0: {_return}.
'''

PROBLEM = Problem(
    id="daily-temperatures",
    number=739,
    slug="daily-temperatures",
    title="Daily Temperatures",
    difficulty="Medium",
    pattern="stack",
    order=5,
    signature=sig("dailyTemperatures", "List[int]", temperatures="List[int]"),
    statement="""
`temperatures[i]` is the temperature on day `i`. Return an array `answer` where `answer[i]` is the **number of days you'd wait after day `i` for a strictly warmer day**. If no warmer day ever comes, `answer[i]` is `0`.
""",
    examples=[
        {"args": {"temperatures": [70, 72, 71, 69, 74, 73]}, "output": [1, 3, 2, 1, 0, 0]},
        {"args": {"temperatures": [30, 40, 50, 60]}, "output": [1, 1, 1, 0]},
        {"args": {"temperatures": [60, 50, 40]}, "output": [0, 0, 0]},
    ],
    constraints=["1 ≤ temperatures.length ≤ 10⁵", "30 ≤ temperatures[i] ≤ 100"],
    companies={"Amazon": 4, "Meta": 4, "Google": 3, "Microsoft": 3, "Bloomberg": 3, "Uber": 2, "Salesforce": 2},
    topics=["Array", "Stack", "Monotonic Stack"],
    hints=[
        "Brute force scans forward from every day: O(n²). Which days are still \"waiting\" when you reach day i?",
        "If today is warmer than some waiting days, today answers all of them at once.",
        "Keep a stack of waiting days (their temperatures don't increase going up). Pop while today is warmer.",
    ],
    insight={
        "pattern": "Monotonic stack (next greater element)",
        "oneLiner": "Keep unanswered days on a stack; a warmer day pops and answers every colder day on top.",
        "mnemonic": "The hot day settles every colder debt.",
        "why": "Each index is pushed and popped once, so the 'nested' loop totals O(n). The stack stays non-increasing "
               "because anything colder than today gets answered and removed.",
        "signals": ["\"next greater/smaller element\"", "\"how long until …\"", "spans"],
        "recall": [
            {"q": "What does the stack hold, and in what order?", "a": "Indices of days without an answer yet; temperatures are non-increasing from bottom to top."},
            {"q": "When is a day's answer written?", "a": "When it's popped by a strictly warmer day: answer = i − j."},
        ],
    },
    solutions=[
        Solution("brute", "Scan forward from each day", "O(n²)", "O(1)", BRUTE,
                 "For each day, look ahead until a warmer one appears."),
        Solution("stack", "Monotonic stack", "O(n)", "O(n)", STACK,
                 "Days wait on a stack until a warmer day pops them.", optimal=True),
    ],
    pitfalls=[
        Pitfall("not-strict", "Treated an equal temperature as warmer",
                "Only a strictly warmer day counts: pop while temperatures[top] < t, not <=.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e)
                and any(isinstance(xi, int) and xi != 0 and (ei == 0 or xi < ei) for xi, ei in zip(x, e))
                and len(set(a["temperatures"])) < len(a["temperatures"])),
        Pitfall("values-not-distance", "Stored the temperature or index instead of the wait",
                "answer[j] is the number of days waited: i − j.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e)
                and any(xi > len(e) for xi in x if isinstance(xi, int))),
    ],
    edge_cases=[{"temperatures": [50]}, {"temperatures": [50, 50]}, {"temperatures": [30, 60, 90]},
                {"temperatures": [55, 38, 53, 81, 61, 93, 97, 32, 43, 78]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"temperatures": [70, 72, 71, 69, 74, 73]},
    lens={"arrays": {"temperatures": {"view": "bars", "pointers": ["i", "j"]}, "res": {"pointers": []}},
          "indexes": {"stack": "temperatures"}},
    related=["sliding-window-maximum", "largest-rectangle-in-histogram", "car-fleet"],
)
