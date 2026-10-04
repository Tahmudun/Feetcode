from feetcode.problem import Pitfall, Problem, Solution, sig, small_alphabet, word


def generate(rng, n):
    return {"s": word(rng, n, small_alphabet(rng, n) + rng.choice(("", " ", "1")))}


def validate(args):
    return all(32 <= ord(c) < 127 for c in args["s"])


def worst_case(n):
    # Every start scans k = 26 characters before a repeat. (A wider alphabet raises k, but moves the bend from
    # n² to n·k into the profiled sizes and blurs every fit; 26 keeps each curve clean.)
    return {"s": "".join("abcdefghijklmnopqrstuvwxyz"[i % 26] for i in range(n))}


BRUTE = '''class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        best = 0
        for i in range(len(s)):  #> Start a substring at {i}.
            seen = set()  #~
            for j in range(i, len(s)):  #~
                if s[j] in seen:  #~
                    break  #~
                seen.add(s[j])  #~
                best = max(best, j - i + 1)  #~
        return best  #> Longest: {_return}. Every start re-scans characters the previous start already saw.
'''

WINDOW_SET = '''class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        window = set()  #> The characters inside the current window s[l..r].
        l = best = 0
        for r in range(len(s)):  #> Grow the window to include s[{r}] = {s[r]}.
            while s[r] in window:  #> {s[r]} is already inside the window - shrink from the left until it isn't. || #! The window only ever moves forward: l and r each advance at most n times, so the nested loop is O(n) in total, not O(n²).
                window.remove(s[l])  #> Remove s[{l}] = {s[l]}.
                l += 1  #~
            window.add(s[r])  #> Window s[{l}..{r}] = {s[l:r + 1]} has no repeats.
            best = max(best, r - l + 1)  #> Its length is {r - l + 1}. Best so far: {best}.
        return best  #> Longest substring without repeats: {_return}.
'''

LAST_SEEN = '''class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        last = {}  #> last[ch] = the most recent index where ch appeared.
        l = best = 0
        for r, ch in enumerate(s):  #> Next character: s[{r}] = {ch}.
            if ch in last and last[ch] >= l:  #> {ch} was last seen at {last[ch]}, inside the window - jump l past it. || {ch} is not inside the current window. #! The last[ch] >= l check matters: an old occurrence before l is already outside the window, and jumping to it would move l backwards.
                l = last[ch] + 1  #> l = {l}.
            last[ch] = r  #~
            best = max(best, r - l + 1)  #> Window s[{l}..{r}] = {s[l:r + 1]}. Best: {best}.
        return best
'''

PROBLEM = Problem(
    id="longest-substring-without-repeating-characters",
    number=3,
    slug="longest-substring-without-repeating-characters",
    title="Longest Substring Without Repeating Characters",
    difficulty="Medium",
    pattern="sliding-window",
    order=2,
    signature=sig("lengthOfLongestSubstring", "int", s="str"),
    statement="""
Given a string `s`, return the length of the **longest substring** (contiguous!) in which no character appears more than once.
""",
    examples=[
        {"args": {"s": "feetcode"}, "output": 5, "explain": "\"etcod\" has five distinct characters."},
        {"args": {"s": "tmmzuxt"}, "output": 5, "explain": "\"mzuxt\". A repeat outside the window doesn't matter."},
        {"args": {"s": "bbbb"}, "output": 1},
        {"args": {"s": ""}, "output": 0},
    ],
    constraints=["0 ≤ s.length ≤ 5 · 10⁴", "s consists of letters, digits, symbols and spaces."],
    companies={"Amazon": 5, "Google": 5, "Meta": 4, "Microsoft": 4, "Bloomberg": 4, "Apple": 3, "Adobe": 3,
               "Uber": 3, "Spotify": 2, "Yahoo": 2},
    topics=["Hash Table", "String", "Sliding Window"],
    hints=[
        "Checking every substring is O(n²) or worse. If s[l..r] has no repeats, what about s[l+1..r]?",
        "Keep a window with no repeats. Extend it on the right; when the new character is a repeat, shrink from the left.",
        "A set holds the window's characters. Or store each character's last index and jump l directly past the repeat.",
    ],
    insight={
        "pattern": "Variable sliding window",
        "oneLiner": "Grow right; while the new character is a duplicate, shrink left. The window is always repeat-free.",
        "mnemonic": "Expand to explore, shrink to repair.",
        "why": "Both pointers only move forward, so each character enters and leaves the window at most once: O(n).",
        "signals": ["longest/shortest contiguous substring or subarray", "a validity condition you can repair by shrinking"],
        "recall": [
            {"q": "Template for a variable sliding window?",
             "a": "for r: add s[r]; while window invalid: remove s[l], l += 1; update answer."},
            {"q": "In the last-index version, why max/guard with last[ch] >= l?",
             "a": "So l never moves backwards when the previous occurrence is already outside the window."},
        ],
    },
    solutions=[
        Solution("brute", "Every start, scan forward", "O(n·k)", "O(k)", BRUTE,
                 "From each start, extend until a repeat appears. A scan can't outlast k, the number of "
                 "distinct characters (at most 95 here), so this is O(n·k): O(n²) while strings are short, "
                 "and a 95× constant once they're long. The window never rescans at all."),
        Solution("window-set", "Sliding window + set", "O(n)", "O(k)", WINDOW_SET,
                 "Keep the window's characters in a set; shrink from the left whenever a repeat enters.",
                 optimal=True),
        Solution("last-seen", "Sliding window + last index", "O(n)", "O(k)", LAST_SEEN,
                 "Jump l past the previous occurrence directly instead of removing characters one by one."),
    ],
    pitfalls=[
        Pitfall("backwards-l", "Moved l backwards",
                "When jumping l to last[ch] + 1, guard with last[ch] >= l (or use max) - an old occurrence is already outside.",
                detect=lambda a, e, x: isinstance(x, int) and x > e),
        Pitfall("subsequence", "Counted distinct characters instead of a substring",
                "The substring must be contiguous - len(set(s)) is not the answer.",
                detect=lambda a, e, x: isinstance(x, int) and x == len(set(a["s"])) and x != e),
    ],
    edge_cases=[{"s": ""}, {"s": " "}, {"s": "au"}, {"s": "abba"}, {"s": "dvdf"}, {"s": "pwwkew"}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"s": "abcabcbb"},
    lens={"arrays": {"s": {"pointers": ["l", "r", "i", "j"], "window": ["l", "r"]}}},
    related=["longest-repeating-character-replacement", "minimum-window-substring"],
)
