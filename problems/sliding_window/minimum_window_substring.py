from collections import Counter

from feetcode.problem import Pitfall, Problem, Solution, sig, word


def _covers(w, t):
    return not (Counter(t) - Counter(w))


def check(args, expected, actual):
    if not isinstance(actual, str):
        return False
    if expected == "":
        return actual == ""
    return len(actual) == len(expected) and actual in args["s"] and _covers(actual, args["t"])


def generate(rng, n):
    alpha = "abc"[: rng.choice((2, 3))] + rng.choice(("", "x", "AB"))
    s = word(rng, max(1, n), alpha)
    t = word(rng, rng.randint(1, 3), alpha)
    return {"s": s, "t": t}


def validate(args):
    s, t = args["s"], args["t"]
    return len(s) >= 1 and len(t) >= 1 and (s + t).isalpha()


def worst_case(n):
    return {"s": "".join("abcdefg"[(i * 3) % 7] for i in range(max(1, n))), "t": "gfa"}


BRUTE = '''class Solution:
    def minWindow(self, s: str, t: str) -> str:
        need = Counter(t)
        best = ""
        for l in range(len(s)):  #> Shortest valid window starting at {l}?
            have = Counter()  #~
            for r in range(l, len(s)):  #~
                have[s[r]] += 1  #~
                if all(have[c] >= need[c] for c in need):  #~
                    if best == "" or r - l + 1 < len(best):  #~
                        best = s[l:r + 1]  #> New best: {best}.
                    break  #~
        return best  #> Shortest window: {_return}.
'''

WINDOW = '''class Solution:
    def minWindow(self, s: str, t: str) -> str:
        need = Counter(t)  #> The window must contain: {dict(need)}.
        window = {}
        have, required = 0, len(need)  #> have counts letters whose requirement is fully met. We need all {required}.
        best_len, best_l = float("inf"), 0
        l = 0
        for r, ch in enumerate(s):  #> Expand: add s[{r}] = {ch}.
            window[ch] = window.get(ch, 0) + 1  #~
            if ch in need and window[ch] == need[ch]:  #> {ch} now meets its requirement of {need[ch]}: have = {have + 1} of {required}. ||
                have += 1  #~
            while have == required:  #> s[{l}..{r}] = {s[l:r + 1]} contains everything. Try shrinking it from the left. || #! Expand until valid, then shrink while still valid. Each index enters the window once (r) and leaves once (l), so this is O(|s| + |t|) despite the nested loop.
                if r - l + 1 < best_len:  #> New shortest window: {s[l:r + 1]} (length {r - l + 1}). ||
                    best_len, best_l = r - l + 1, l  #~
                window[s[l]] -= 1  #> Drop s[{l}] = {s[l]}.
                if s[l] in need and window[s[l]] < need[s[l]]:  #> Without that {s[l]}, the window is missing something - stop shrinking. ||
                    have -= 1  #~
                l += 1  #~
        return s[best_l:best_l + best_len] if best_len != float("inf") else ""  #> Shortest window: {_return}.
'''

PROBLEM = Problem(
    id="minimum-window-substring",
    number=76,
    slug="minimum-window-substring",
    title="Minimum Window Substring",
    difficulty="Hard",
    pattern="sliding-window",
    order=5,
    signature=sig("minWindow", "str", s="str", t="str"),
    statement="""
Given strings `s` and `t`, return the **shortest substring of `s` that contains every character of `t`**, counting duplicates (if `t` has two `a`s, the window needs at least two).

If no such substring exists, return `""`. When several shortest windows exist, any of them is accepted.
""",
    examples=[
        {"args": {"s": "xaybzcax", "t": "abc"}, "output": "bzca"},
        {"args": {"s": "QFEETCODEQ", "t": "CQ"}, "output": "CODEQ"},
        {"args": {"s": "aa", "t": "aaa"}, "output": "", "explain": "s has only two a's."},
    ],
    constraints=["1 ≤ s.length, t.length ≤ 10⁵", "s and t are English letters (case-sensitive)."],
    companies={"Meta": 5, "Amazon": 4, "Google": 4, "LinkedIn": 3, "Microsoft": 3, "Uber": 3, "Airbnb": 3,
               "Snap": 2, "Lyft": 2},
    topics=["Hash Table", "String", "Sliding Window"],
    hints=[
        "Write the check \"does s[l..r] contain t?\" first. Brute force tries every window.",
        "If s[l..r] is valid, so is every window that contains it. So once valid, try to shrink from the left.",
        "Track `have` = how many distinct characters currently meet their required count. Valid iff have == required.",
    ],
    insight={
        "pattern": "Expand until valid, shrink while valid",
        "oneLiner": "Grow r until the window covers t, then advance l as far as it stays valid; record the best each time.",
        "mnemonic": "Stretch to cover, squeeze to minimize.",
        "why": "The have/required counter makes validity an O(1) check, and both pointers move only forward: O(|s| + |t|).",
        "signals": ["\"minimum window\"", "shortest substring containing all of …"],
        "recall": [
            {"q": "What does `have` count?", "a": "Distinct characters of t whose count in the window has reached the required count."},
            {"q": "When does `have` decrease?", "a": "When removing s[l] drops its count below what t requires."},
        ],
    },
    solutions=[
        Solution("brute", "Shortest valid window per start", "O(n²)", "O(k)", BRUTE,
                 "For each start, extend until the window covers t."),
        Solution("window", "Sliding window with have/need", "O(n)", "O(k)", WINDOW,
                 "Expand right until valid, then shrink left while valid, tracking satisfied requirements.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("ignores-multiplicity", "Ignored repeated letters in t",
                "If t = \"aab\", the window needs two a's. Compare counts, not just membership.",
                detect=lambda a, e, x: isinstance(x, str) and x != "" and not _covers(x, a["t"]) and set(a["t"]) <= set(x)),
        Pitfall("not-minimal", "Returned a valid but longer window",
                "Keep shrinking from the left while the window stays valid.",
                detect=lambda a, e, x: isinstance(x, str) and e != "" and len(x) > len(e) and x in a["s"] and _covers(x, a["t"])),
    ],
    edge_cases=[{"s": "a", "t": "a"}, {"s": "a", "t": "aa"}, {"s": "a", "t": "b"}, {"s": "ab", "t": "b"},
                {"s": "bba", "t": "ab"}, {"s": "aAbB", "t": "AB"}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    compare=check,
    lesson={"s": "xaybzcax", "t": "abc"},
    lens={"arrays": {"s": {"pointers": ["l", "r"], "window": ["l", "r"]}}},
    related=["permutation-in-string", "longest-substring-without-repeating-characters"],
)
