from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    n = max(1, n)
    piles = ints(rng, n, 1, rng.choice((3, 12, 60, 1000)))
    roll = rng.random()
    if roll < 0.2:
        h = n                                   # one hour per pile: the answer is the biggest pile
    elif roll < 0.8:
        h = rng.randint(n, max(n, sum(piles)))  # somewhere in between: the interesting range
    else:
        h = sum(piles) + rng.randint(0, 5)      # so much time that speed 1 works
    return {"piles": piles, "h": h}


def validate(args):
    piles, h = args["piles"], args["h"]
    return 1 <= len(piles) <= h and all(isinstance(p, int) and p >= 1 for p in piles)


def worst_case(n):
    # One hour per pile forces the answer up to the biggest pile (n): brute force tries every speed below it.
    n = max(1, n)
    return {"piles": [n - i for i in range(n)], "h": n}


BRUTE = '''class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        k = 1  #> Start at the slowest possible speed: 1 banana per hour.
        while True:
            hours = 0  #~
            for pile in piles:  #~
                hours += (pile + k - 1) // k  #~
            if hours <= h:  #> At speed {k} the piles take {hours} hours - within {h}. || At speed {k} the piles take {hours} hours, more than {h}. Try {k + 1}.
                return k  #> {k} is the first speed that works - found by testing every slower speed first.
            k += 1  #~
'''

BINARY = '''class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        slowest, fastest = 1, max(piles)  #> The answer is a speed in {slowest}..{fastest}. At {fastest}, every pile takes one hour - no faster speed can help. #! The piles aren't sorted, but the answers are: if speed k finishes in time, so does every faster speed. Answers flip from "too slow" to "fast enough" exactly once - that's all binary search needs.
        while slowest < fastest:  #> The answer is somewhere in {slowest}..{fastest}. || Only {slowest} is left.
            k = (slowest + fastest) // 2  #> Test the middle speed, {k}.
            hours = 0  #~
            for pile in piles:  #~
                hours += (pile + k - 1) // k  #~ #! (pile + k - 1) // k is ceil(pile / k) in integer arithmetic: a pile she can't finish still costs a whole hour.
            if hours <= h:  #> Speed {k} needs {hours} hours ≤ {h}: fast enough, so the answer is {k} or slower. || Speed {k} needs {hours} hours > {h}: too slow, so the answer is faster than {k}.
                fastest = k  #> {k} stays a candidate. Search {slowest}..{fastest}. #! fastest = k, not k - 1: k works, so it might be the answer. This "first speed that works" shape never returns from inside the loop - it stops when the range is one speed wide.
            else:
                slowest = k + 1  #> Search {slowest}..{fastest}.
        return slowest  #> The slowest speed that finishes in {h} hours: {_return}.
'''

PROBLEM = Problem(
    id="koko-eating-bananas",
    number=875,
    slug="koko-eating-bananas",
    title="Koko Eating Bananas",
    difficulty="Medium",
    pattern="binary-search",
    order=3,
    signature=sig("minEatingSpeed", "int", piles="List[int]", h="int"),
    statement="""
Koko has `h` hours to finish several piles of bananas; `piles[i]` is the size of pile `i`. She picks one whole-number speed `k` (bananas per hour) and keeps it. Each hour she eats from a single pile: `k` bananas, or the rest of the pile if fewer than `k` are left - and then she waits out the remainder of that hour.

Return the **smallest** speed `k` that lets her finish every pile within `h` hours. It's guaranteed that `h` is at least the number of piles.
""",
    examples=[
        {"args": {"piles": [4, 9, 2, 13], "h": 7}, "output": 5,
         "explain": "At 5 per hour the piles take 1 + 2 + 1 + 3 = 7 hours. At 4 they take 9."},
        {"args": {"piles": [6, 6, 6], "h": 3}, "output": 6,
         "explain": "One hour per pile, so she must finish a pile per hour."},
        {"args": {"piles": [10, 3], "h": 20}, "output": 1},
    ],
    constraints=["1 ≤ piles.length ≤ 10⁴", "piles.length ≤ h ≤ 10⁹", "1 ≤ piles[i] ≤ 10⁹"],
    companies={"Google": 3, "Amazon": 3, "Meta": 3, "Microsoft": 2, "Bloomberg": 2, "Uber": 2, "Airbnb": 2},
    topics=["Array", "Binary Search"],
    hints=[
        "Given a speed k, can you compute how many hours she needs? Each pile takes ceil(pile / k).",
        "If speed k is fast enough, is k + 1? The answers flip from 'too slow' to 'fast enough' exactly once.",
        "Binary-search the speed between 1 and max(piles). Fast enough → keep it and look slower; too slow → look faster.",
    ],
    insight={
        "pattern": "Binary search on the answer",
        "oneLiner": "The input isn't sorted, but the answers are: binary-search the speed, testing each guess with an O(n) check.",
        "mnemonic": "Don't search the piles - search the speedometer.",
        "why": "Hours needed only go down as k goes up, so 'finishes in time' is false for every speed below the answer "
               "and true from it onward. Binary search finds that flip in log₂(max pile) tests of O(n) each.",
        "signals": ["\"minimum speed / capacity / size such that …\"", "a feasibility check that's monotonic in the answer",
                    "answer range bounded by the input's max or sum"],
        "recall": [
            {"q": "What range do you binary-search, and why those bounds?",
             "a": "Speeds 1..max(piles): 1 is the slowest legal speed, and at max(piles) every pile takes one hour, so nothing faster helps."},
            {"q": "When the middle speed works, why fastest = k and not k - 1?",
             "a": "k itself might be the answer. You're looking for the first speed that works, so you can't discard it."},
            {"q": "How do you compute ceil(pile / k) without floats?",
             "a": "(pile + k - 1) // k."},
        ],
    },
    solutions=[
        Solution("brute", "Try every speed from 1", "O(n · m)", "O(1)", BRUTE,
                 "Test speeds 1, 2, 3, … until one finishes in time. Each test is O(n), and the answer can be as large "
                 "as the biggest pile m, so this is O(n · m)."),
        Solution("binary", "Binary-search the speed", "O(n log m)", "O(1)", BINARY,
                 "Speeds that work form a suffix of 1..max(piles). Binary-search for its first element: about log₂ m "
                 "tests of O(n) each.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("zero-speed", "Tried speed 0",
                "Speed 0 never finishes anything and divides by zero. The answer range starts at 1.",
                error="ZeroDivisionError"),
        Pitfall("too-slow", "Returned a speed that's too slow",
                "At the speed you returned, Koko runs out of time. When the middle speed fails, the answer is strictly "
                "faster: slowest = k + 1. Also make sure each pile costs ceil(pile / k) hours, not pile // k.",
                detect=lambda a, e, x: isinstance(x, int) and x < e),
        Pitfall("not-minimal", "Returned a speed that works but isn't the slowest",
                "Your speed finishes in time, but a slower one does too. When the middle speed works, keep it as a "
                "candidate and keep searching slower: fastest = k.",
                detect=lambda a, e, x: isinstance(x, int) and x > e),
    ],
    edge_cases=[
        {"piles": [1], "h": 1},
        {"piles": [5], "h": 5},
        {"piles": [5], "h": 1},
        {"piles": [30], "h": 4},
        {"piles": [3, 3, 3], "h": 3},
        {"piles": [2, 9, 4], "h": 100},
        {"piles": [7, 1, 7, 1], "h": 5},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"piles": [4, 9, 2, 13], "h": 7},
    lens={"arrays": {"piles": {"view": "bars"}}},
    follow_up="Ship packages within D days (capacity instead of speed) uses the same shape. What are its bounds?",
    related=["binary-search", "find-minimum-in-rotated-sorted-array"],
)
