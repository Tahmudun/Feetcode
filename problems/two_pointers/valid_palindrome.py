from feetcode.problem import Pitfall, Problem, Solution, sig

NOISE = " ,.:!-'"


def generate(rng, n):
    n = max(1, n)
    core = "".join(rng.choice("abAB12") for _ in range(max(1, n // 2)))
    if rng.random() < 0.55:
        mid = rng.choice(("", rng.choice("abc1")))
        core = core + mid + core[::-1]
        core = "".join(ch.swapcase() if rng.random() < 0.3 else ch for ch in core)
    out = []
    for ch in core:
        if rng.random() < 0.3:
            out.append(rng.choice(NOISE))
        out.append(ch)
    s = "".join(out)[: max(1, n)] if rng.random() < 0.3 else "".join(out)
    return {"s": s or "a"}


def validate(args):
    s = args["s"]
    return 1 <= len(s) and all(32 <= ord(c) < 127 for c in s)


def worst_case(n):
    half = "".join("abcdefg"[i % 7] for i in range(n // 2))
    return {"s": half + " " + half[::-1].upper()}


FILTER = '''class Solution:
    def isPalindrome(self, s: str) -> bool:
        cleaned = [ch.lower() for ch in s if ch.isalnum()]  #> Keep only letters and digits, lowercased: {"".join(cleaned)}.
        return cleaned == cleaned[::-1]  #> Compare it with its reverse, {"".join(cleaned[::-1])}: {"same" if _return else "different"}.
'''

TWO_POINTERS = '''class Solution:
    def isPalindrome(self, s: str) -> bool:
        l, r = 0, len(s) - 1  #> One pointer at each end: l = {l}, r = {r}.
        while l < r:  #~
            while l < r and not s[l].isalnum():  #> s[{l}] = {s[l]} isn't a letter or digit - skip it. ||
                l += 1  #~
            while l < r and not s[r].isalnum():  #> s[{r}] = {s[r]} isn't a letter or digit - skip it. ||
                r -= 1  #~
            if s[l].lower() != s[r].lower():  #> {s[l]} vs {s[r]}: they differ, so this is not a palindrome. || {s[l]} vs {s[r]}: they match (ignoring case). #! Compare as you go instead of building a cleaned copy - O(1) extra space.
                return False  #~
            l, r = l + 1, r - 1  #> Both pointers move inward: l = {l}, r = {r}.
        return True  #> The pointers met with no mismatch - it reads the same in both directions.
'''

PROBLEM = Problem(
    id="valid-palindrome",
    number=125,
    slug="valid-palindrome",
    title="Valid Palindrome",
    difficulty="Easy",
    pattern="two-pointers",
    order=1,
    signature=sig("isPalindrome", "bool", s="str"),
    statement="""
A phrase is a **palindrome** if, after lower-casing every letter and dropping everything that isn't a letter or a digit, it reads the same forwards and backwards.

Given a string `s`, return `true` if it is a palindrome under that rule, and `false` otherwise.
""",
    examples=[
        {"args": {"s": "Never odd, or even."}, "output": True, "explain": "Cleaned: \"neveroddoreven\"."},
        {"args": {"s": "feet code"}, "output": False},
        {"args": {"s": " .,"}, "output": True, "explain": "Nothing is left after cleaning - the empty string is a palindrome."},
    ],
    constraints=["1 ≤ s.length ≤ 2 · 10⁵", "s contains printable ASCII characters."],
    companies={"Meta": 5, "Amazon": 3, "Microsoft": 3, "Apple": 3, "Bloomberg": 3, "Google": 2, "Spotify": 2,
               "Wayfair": 2},
    topics=["Two Pointers", "String"],
    hints=[
        "Simplest: build the cleaned string and compare it with its reverse. That costs O(n) extra space.",
        "Compare characters from both ends instead. What should you do when a pointer lands on punctuation?",
        "Skip non-alphanumeric characters with inner while loops; compare lowercased characters; move both pointers inward.",
    ],
    insight={
        "pattern": "Converging two pointers",
        "oneLiner": "Walk inward from both ends, skipping junk, comparing lowercased characters - no cleaned copy needed.",
        "mnemonic": "Squeeze from both ends.",
        "why": "A palindrome is a statement about mirror pairs (i, n − 1 − i); two pointers visit exactly those pairs.",
        "signals": ["symmetry / mirror checks", "\"reads the same backward\"", "O(1) space follow-up"],
        "recall": [
            {"q": "What counts as a character here?", "a": "Letters AND digits (isalnum), compared case-insensitively."},
            {"q": "Why the l < r guard inside the skip loops?", "a": "So a string of only punctuation can't run a pointer off the end."},
        ],
    },
    solutions=[
        Solution("filter-reverse", "Clean, then reverse", "O(n)", "O(n)", FILTER,
                 "Build the cleaned, lowercased list of characters and compare it with its reverse."),
        Solution("two-pointers", "Two pointers", "O(n)", "O(1)", TWO_POINTERS,
                 "Compare mirror characters in place, skipping anything that isn't a letter or digit.", optimal=True),
    ],
    pitfalls=[
        Pitfall("case", "Compared case-sensitively",
                "'A' and 'a' must match - compare ch.lower().",
                detect=lambda a, e, x: e is True and x is False and any(c.isupper() for c in a["s"])),
        Pitfall("digits", "Dropped digits",
                "Digits count as characters: use isalnum(), not isalpha().",
                detect=lambda a, e, x: x != e and any(c.isdigit() for c in a["s"])),
        Pitfall("punctuation", "Didn't skip punctuation and spaces",
                "Only letters and digits take part in the comparison.",
                detect=lambda a, e, x: e is True and x is False and any(not c.isalnum() for c in a["s"])),
    ],
    edge_cases=[{"s": "a"}, {"s": " "}, {"s": "0P"}, {"s": "ab_a"}, {"s": ".,a"}, {"s": "Aa"}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"s": "Taco, cat!"},
    lens={"arrays": {"s": {"pointers": ["l", "r"]}}},
    related=["two-sum-ii-input-array-is-sorted"],
)
