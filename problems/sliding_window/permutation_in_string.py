from feetcode.problem import Pitfall, Problem, Solution, sig, word


def generate(rng, n):
    alpha = "abc"[: rng.choice((2, 3))] + rng.choice(("", "x"))
    s1 = word(rng, rng.randint(1, 3), alpha)
    s2 = word(rng, max(1, n), alpha)
    if rng.random() < 0.4 and len(s2) >= len(s1):
        i = rng.randint(0, len(s2) - len(s1))
        s2 = s2[:i] + "".join(rng.sample(s1, len(s1))) + s2[i + len(s1):]
    return {"s1": s1, "s2": s2}


def validate(args):
    s1, s2 = args["s1"], args["s2"]
    return len(s1) >= 1 and len(s2) >= 1 and (s1 + s2).isalpha() and (s1 + s2).islower()


def worst_case(n):
    return {"s1": "abcz", "s2": "".join("abcd"[i % 4] for i in range(max(1, n)))}


SORTING = '''class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        k = len(s1)
        target = sorted(s1)  #> The sorted letters every permutation of s1 shares: {"".join(target)}.
        for i in range(len(s2) - k + 1):  #> Window s2[{i}..{i + k - 1}] = {s2[i:i + k]}.
            if sorted(s2[i:i + k]) == target:  #> Sorted, it's {"".join(sorted(s2[i:i + k]))} - a match! || Sorted, it's {"".join(sorted(s2[i:i + k]))} - no match.
                return True  #~
        return False  #> No window matched. Each window was sorted from scratch: O(n · k log k).
'''

FIXED_WINDOW = '''class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        k = len(s1)
        if k > len(s2):
            return False
        need = Counter(s1)  #> Any permutation of s1 has exactly these counts: {dict(need)}.
        window = Counter(s2[:k])  #> The first window, s2[0..{k - 1}] = {s2[:k]}, has counts {dict(window)}.
        if window == need:  #> It already matches. || Not a match yet.
            return True
        for r in range(k, len(s2)):  #> Slide right: add s2[{r}] = {s2[r]}, drop s2[{r - k}] = {s2[r - k]}.
            window[s2[r]] += 1  #~
            window[s2[r - k]] -= 1  #~
            if window[s2[r - k]] == 0:  #~
                del window[s2[r - k]]  #~
            if window == need:  #> Window {s2[r - k + 1:r + 1]} has exactly s1's letters. || Window {s2[r - k + 1:r + 1]} has {dict(window)} - no match. #! A fixed-size window: each slide changes exactly two counts, so updating is O(1) and comparing is O(26). No re-sorting, no re-counting.
                return True  #> Found a permutation of s1 inside s2.
        return False  #> No window matched.
'''

PROBLEM = Problem(
    id="permutation-in-string",
    number=567,
    slug="permutation-in-string",
    title="Permutation in String",
    difficulty="Medium",
    pattern="sliding-window",
    order=4,
    signature=sig("checkInclusion", "bool", s1="str", s2="str"),
    statement="""
Given two strings `s1` and `s2`, return `true` if some **rearrangement of `s1` appears as a contiguous substring of `s2`**, and `false` otherwise.
""",
    examples=[
        {"args": {"s1": "tac", "s2": "xcatz"}, "output": True, "explain": "\"cat\" is a permutation of \"tac\"."},
        {"args": {"s1": "ab", "s2": "eidboaoo"}, "output": False, "explain": "b and a appear, but never next to each other."},
        {"args": {"s1": "aab", "s2": "baa"}, "output": True},
    ],
    constraints=["1 ≤ s1.length, s2.length ≤ 10⁴", "Lowercase English letters only."],
    companies={"Microsoft": 3, "Amazon": 3, "Meta": 3, "Google": 2, "Oracle": 2, "Yandex": 2},
    topics=["Hash Table", "Two Pointers", "String", "Sliding Window"],
    hints=[
        "A permutation of s1 is just a string with the same letter counts. Any matching window has length len(s1).",
        "Slide a window of length len(s1) over s2. Comparing counts from scratch for each window is wasteful.",
        "When the window slides one step, exactly one letter enters and one leaves. Update two counts, then compare.",
    ],
    insight={
        "pattern": "Fixed-size sliding window",
        "oneLiner": "Slide a window of length len(s1) across s2, updating counts in O(1) per step; a match is equal counts.",
        "mnemonic": "Same counts, same size - slide and compare.",
        "why": "Each step adds one letter and removes one, so maintaining the counts is O(1) and the whole scan is O(n).",
        "signals": ["anagram/permutation of a pattern inside a text", "window length is fixed by the pattern"],
        "recall": [
            {"q": "What changes when a fixed window slides by one?", "a": "One character enters on the right, one leaves on the left."},
            {"q": "How to make the comparison O(1) instead of O(26)?",
             "a": "Track how many of the 26 letters currently have matching counts ('matches')."},
        ],
    },
    solutions=[
        Solution("sorting", "Sort every window", "O(n · k log k)", "O(k)", SORTING,
                 "Compare each length-k window's sorted letters with sorted(s1)."),
        Solution("fixed-window", "Fixed window of counts", "O(n)", "O(1)", FIXED_WINDOW,
                 "Maintain the window's letter counts incrementally and compare with s1's counts.", optimal=True),
    ],
    pitfalls=[
        Pitfall("subsequence", "Allowed gaps between letters",
                "The permutation must be contiguous in s2 - check windows of exactly len(s1).",
                detect=lambda a, e, x: e is False and x is True),
        Pitfall("off-by-one", "Missed the last window",
                "With windows of length k, start positions go up to len(s2) − k inclusive.",
                detect=lambda a, e, x: e is True and x is False),
    ],
    edge_cases=[{"s1": "a", "s2": "a"}, {"s1": "ab", "s2": "a"}, {"s1": "abc", "s2": "bbbca"}, {"s1": "adc", "s2": "dcda"}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"s1": "abc", "s2": "eidbcaoo"},
    lens={"arrays": {"s2": {"pointers": ["r", "i"], "window": ["r - k + 1", "r"]}}},
    related=["valid-anagram", "minimum-window-substring"],
)
