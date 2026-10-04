from feetcode.problem import Pitfall, Problem, Solution, sig, small_alphabet, word


def generate(rng, n):
    n = max(1, n)
    s = word(rng, n, small_alphabet(rng, n))
    roll = rng.random()
    if roll < 0.45:
        t = "".join(rng.sample(s, len(s)))                       # an anagram
    elif roll < 0.75:
        chars = list(s)
        chars[rng.randrange(len(chars))] = rng.choice("abcxyz")   # one letter off
        rng.shuffle(chars)
        t = "".join(chars)
    else:
        t = word(rng, max(1, n + rng.choice((-1, 1))), small_alphabet(rng, n))
    return {"s": s, "t": t}


def validate(args):
    s, t = args["s"], args["t"]
    return len(s) >= 1 and len(t) >= 1 and (s + t).isalpha() and (s + t).islower()


def worst_case(n):
    letters = "abcdefghijklmnopqrstuvwxyz"
    s = "".join(letters[i % 26] for i in range(n))
    return {"s": s, "t": s[::-1]}


SORTING = '''class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        return sorted(s) == sorted(t)  #> Sorted, s is {"".join(sorted(s))} and t is {"".join(sorted(t))} - {"equal" if _return else "different"}.
'''

COUNTING = '''class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        if len(s) != len(t):  #> Lengths {len(s)} and {len(t)} differ, so they can't be anagrams. || Both have length {len(s)} - worth counting.
            return False
        count = {}  #> Net count per letter: +1 for every letter in s, −1 for every letter in t.
        for a, b in zip(s, t):  #~
            count[a] = count.get(a, 0) + 1  #> +1 for {a}: {count}
            count[b] = count.get(b, 0) - 1  #> −1 for {b}: {count}
        return all(c == 0 for c in count.values())  #> {"Every letter cancels out to 0 - anagrams." if _return else "Some letter doesn't cancel out - not anagrams."} #! One dict and one pass. If both strings use the same multiset of letters, every +1 meets a matching −1.
'''

PROBLEM = Problem(
    id="valid-anagram",
    number=242,
    slug="valid-anagram",
    title="Valid Anagram",
    difficulty="Easy",
    pattern="arrays-hashing",
    order=2,
    signature=sig("isAnagram", "bool", s="str", t="str"),
    statement="""
Given two strings `s` and `t`, return `true` if `t` is an **anagram** of `s`: the same letters, each used the same number of times, possibly in a different order. Otherwise return `false`.
""",
    examples=[
        {"args": {"s": "listen", "t": "silent"}, "output": True},
        {"args": {"s": "rat", "t": "tar"}, "output": True},
        {"args": {"s": "aab", "t": "abb"}, "output": False,
         "explain": "Same letters, different counts: s has two a's, t has one."},
    ],
    constraints=["1 ≤ s.length, t.length ≤ 5 · 10⁴", "s and t contain lowercase English letters only."],
    companies={"Amazon": 4, "Bloomberg": 4, "Google": 3, "Meta": 3, "Microsoft": 3, "Uber": 2, "Spotify": 2},
    topics=["Hash Table", "String", "Sorting"],
    hints=[
        "Two strings are anagrams exactly when their letters, sorted, are identical. What does sorting cost?",
        "Instead of sorting, count. What should the counts look like for anagrams?",
        "Add 1 for each letter of s and subtract 1 for each letter of t. Anagrams leave every count at 0.",
    ],
    insight={
        "pattern": "Frequency counting",
        "oneLiner": "Anagrams have identical letter counts - count up for s, down for t, and check everything cancels.",
        "mnemonic": "Same bag of letters, different order.",
        "why": "Counting is O(n) with at most 26 keys, beating the O(n log n) sort. The length check up front rejects the easy cases.",
        "signals": ["\"rearrange\"", "\"same characters\"", "permutation / anagram"],
        "recall": [
            {"q": "Why is a set comparison not enough?",
             "a": "A set forgets multiplicity: 'aab' and 'abb' have the same set of letters."},
            {"q": "What's the space cost of the counting solution for lowercase input?",
             "a": "O(1): at most 26 keys."},
        ],
    },
    solutions=[
        Solution("sorting", "Sort both strings", "O(n log n)", "O(n)", SORTING,
                 "Sorting is a canonical form: two anagrams sort to the same string."),
        Solution("counting", "Count letters", "O(n)", "O(1)", COUNTING,
                 "One pass that adds for s and subtracts for t. Every count must return to zero.", optimal=True),
    ],
    pitfalls=[
        Pitfall("set-compare", "Compared sets of letters",
                "set(s) == set(t) ignores how many times each letter appears ('aab' vs 'abb').",
                detect=lambda a, e, x: e is False and x is True and set(a["s"]) == set(a["t"])),
        Pitfall("length", "Skipped the length check",
                "If t is longer than s, checking only s's letters against t can wrongly pass.",
                detect=lambda a, e, x: e is False and x is True and len(a["s"]) != len(a["t"])),
    ],
    edge_cases=[{"s": "a", "t": "a"}, {"s": "a", "t": "b"}, {"s": "ab", "t": "a"}, {"s": "aacc", "t": "ccac"}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"s": "tops", "t": "spot"},
    related=["group-anagrams", "permutation-in-string"],
)
