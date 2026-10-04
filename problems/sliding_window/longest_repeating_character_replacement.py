from feetcode.problem import Pitfall, Problem, Solution, sig, word


def generate(rng, n):
    n = max(1, n)
    s = word(rng, n, "ABC"[: rng.choice((1, 2, 3))])
    return {"s": s, "k": rng.randint(0, max(0, n // 2))}


def validate(args):
    s, k = args["s"], args["k"]
    return len(s) >= 1 and s.isupper() and s.isalpha() and 0 <= k <= len(s)


def worst_case(n):
    return {"s": "".join("ABCD"[(i * 7) % 4] for i in range(max(1, n))), "k": 2}


BRUTE = '''class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        best = 0
        for l in range(len(s)):  #> Windows starting at {l}.
            count = {}  #~
            maxf = 0  #~
            for r in range(l, len(s)):  #~
                count[s[r]] = count.get(s[r], 0) + 1  #~
                maxf = max(maxf, count[s[r]])  #~
                if (r - l + 1) - maxf <= k:  #~
                    best = max(best, r - l + 1)  #~
        return best  #> Longest valid window: {_return}.
'''

WINDOW = '''class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        count = {}  #> Letter counts inside the window s[l..r].
        l = best = maxf = 0
        for r in range(len(s)):  #> Add s[{r}] = {s[r]}.
            count[s[r]] = count.get(s[r], 0) + 1  #~
            maxf = max(maxf, count[s[r]])  #> Counts {count}; the most common letter appears {maxf} times.
            while (r - l + 1) - maxf > k:  #> Window length {r - l + 1} − {maxf} = {r - l + 1 - maxf} letters would need replacing, more than k = {k}. Shrink. || The window needs {r - l + 1 - maxf} replacement(s), within k = {k}. #! A window is valid when (length − count of its most common letter) ≤ k: keep the majority letter, replace the rest.
                count[s[l]] -= 1  #> Drop s[{l}] = {s[l]}.
                l += 1  #~
            best = max(best, r - l + 1)  #> Valid window s[{l}..{r}] = {s[l:r + 1]}. Best: {best}.
        return best  #> Longest achievable run: {_return}. #! maxf is never decreased when shrinking. That's safe: the answer can only improve when some letter's count beats the old maxf, so a stale maxf never produces a wrong (too large) best.
'''

PROBLEM = Problem(
    id="longest-repeating-character-replacement",
    number=424,
    slug="longest-repeating-character-replacement",
    title="Longest Repeating Character Replacement",
    difficulty="Medium",
    pattern="sliding-window",
    order=3,
    signature=sig("characterReplacement", "int", s="str", k="int"),
    statement="""
You're given an uppercase string `s` and an integer `k`. You may **change at most `k` characters** of `s` into any other uppercase letter.

Return the length of the longest substring that can be made of **one repeated letter**.
""",
    examples=[
        {"args": {"s": "AABABBA", "k": 1}, "output": 4, "explain": "Replace the B at index 2 to get \"AAAA\" at indices 0-3."},
        {"args": {"s": "XYYXXYX", "k": 2}, "output": 5},
        {"args": {"s": "ABCD", "k": 0}, "output": 1},
    ],
    constraints=["1 ≤ s.length ≤ 10⁵", "s is uppercase English letters", "0 ≤ k ≤ s.length"],
    companies={"Google": 4, "Amazon": 3, "Meta": 3, "Microsoft": 2, "Uber": 2, "Bloomberg": 2},
    topics=["Hash Table", "String", "Sliding Window"],
    hints=[
        "For a fixed window, how many changes does it need? Keep the most common letter and replace the rest.",
        "A window is valid when (length − count of its most frequent letter) ≤ k.",
        "Slide: grow r, update counts and the max frequency; shrink l while the window is invalid.",
    ],
    insight={
        "pattern": "Variable window with a validity formula",
        "oneLiner": "Window is valid iff len − maxFreq ≤ k. Grow right, shrink left while invalid.",
        "mnemonic": "Keep the majority, pay for the minority.",
        "why": "Validity is monotone: if a window is valid, every window inside it is too, which is what lets the window slide.",
        "signals": ["\"at most k changes/flips\"", "longest substring with a budget"],
        "recall": [
            {"q": "How many replacements does window s[l..r] need?", "a": "(r − l + 1) − (count of its most common letter)."},
            {"q": "Why is it OK to never decrease maxf?",
             "a": "best only grows when a letter's count beats the old maxf, so a stale maxf can't inflate the answer."},
        ],
    },
    solutions=[
        Solution("brute", "Every window", "O(n²)", "O(1)", BRUTE,
                 "Check every window, tracking counts incrementally per start."),
        Solution("window", "Sliding window", "O(n)", "O(1)", WINDOW,
                 "Grow the window to the right; shrink it from the left while it needs more than k changes.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("count-distinct", "Measured the wrong thing",
                "The cost of a window is len − maxFreq (letters that aren't the majority), not the number of distinct letters.",
                code=r"len\(set\("),
    ],
    edge_cases=[{"s": "A", "k": 0}, {"s": "AB", "k": 2}, {"s": "ABAB", "k": 2}, {"s": "AAAA", "k": 0},
                {"s": "ABBB", "k": 2}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"s": "AABABBA", "k": 1},
    lens={"arrays": {"s": {"pointers": ["l", "r"], "window": ["l", "r"]}}},
    related=["longest-substring-without-repeating-characters"],
)
