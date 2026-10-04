from feetcode.problem import Pitfall, Problem, Solution, sig, word


def generate(rng, n):
    n = max(1, n)
    roots = [word(rng, rng.randint(0, 4), "aebtn") for _ in range(max(1, n // 2))]
    strs = []
    for _ in range(n):
        r = rng.choice(roots)
        strs.append("".join(rng.sample(r, len(r))))
    return {"strs": strs}


def validate(args):
    strs = args["strs"]
    return len(strs) >= 1 and all(s == "" or (s.isalpha() and s.islower()) for s in strs)


def worst_case(n):
    letters = "abcdefghij"
    return {"strs": ["".join(letters[(i * 7 + j) % 10] for j in range(6)) for i in range(n)]}


SORTED_KEY = '''class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        groups = defaultdict(list)  #> Map: canonical key -> words with that key.
        for word in strs:  #> Next word: {word}.
            key = "".join(sorted(word))  #> Sort its letters: key {key}. #! Anagrams sort to the same string - sorting is a canonical form.
            groups[key].append(word)  #> Group {key} is now {groups[key]}.
        return list(groups.values())  #> {len(groups)} group(s).
'''

COUNT_KEY = '''class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        groups = {}  #> Keys will be letter-count signatures; values are the words that share them.
        for word in strs:  #> Next word: {word}.
            count = [0] * 26  #~
            for ch in word:  #~
                count[ord(ch) - ord("a")] += 1  #~
            key = tuple(count)  #> Letter counts of {word}: {"".join(chr(97 + i) + str(c) for i, c in enumerate(count) if c) or "(empty)"}. #! tuple(count), never the list itself - dict keys must be hashable. Counting is O(k) per word, cheaper than sorting's O(k log k).
            if key not in groups:  #> No group has this signature yet - start one. || This signature already has a group.
                groups[key] = []
            groups[key].append(word)  #> That group is now {groups[key]}.
        return list(groups.values())  #> {len(groups)} group(s): anagrams collided on the same key.
'''

PROBLEM = Problem(
    id="group-anagrams",
    number=49,
    slug="group-anagrams",
    title="Group Anagrams",
    difficulty="Medium",
    pattern="arrays-hashing",
    order=4,
    signature=sig("groupAnagrams", "List[List[str]]", strs="List[str]"),
    statement="""
Given a list of strings `strs`, **group the words that are anagrams of each other** (same letters, same counts, any order).

Return the groups in any order; the words inside each group may also be in any order.
""",
    examples=[
        {"args": {"strs": ["stop", "pots", "tea", "spot", "eat", "x"]},
         "output": [["stop", "pots", "spot"], ["tea", "eat"], ["x"]]},
        {"args": {"strs": [""]}, "output": [[""]]},
        {"args": {"strs": ["ab", "ba", "abb"]}, "output": [["ab", "ba"], ["abb"]],
         "explain": "\"abb\" has an extra b, so it is not an anagram of \"ab\"."},
    ],
    constraints=["1 ≤ strs.length ≤ 10⁴", "0 ≤ strs[i].length ≤ 100", "strs[i] contains lowercase English letters."],
    companies={"Amazon": 5, "Meta": 4, "Google": 4, "Microsoft": 4, "Bloomberg": 4, "Uber": 3, "Apple": 3,
               "Goldman Sachs": 2, "Salesforce": 2},
    topics=["Array", "Hash Table", "String", "Sorting"],
    hints=[
        "When are two words in the same group? Find something about a word that every anagram shares.",
        "Sorting a word's letters gives the same string for all its anagrams. Use it as a dictionary key.",
        "Even cheaper: a 26-slot letter count - turned into a tuple so it can be a key.",
    ],
    insight={
        "pattern": "Canonical key",
        "oneLiner": "Map every word to a key that all its anagrams share (sorted letters or letter counts), then bucket by key.",
        "mnemonic": "Same signature, same bucket.",
        "why": "Grouping becomes a single dictionary pass: equal keys collide, and the hash map does the grouping for free.",
        "signals": ["\"group\" / \"bucket\" things that are equivalent", "anagrams", "invariant under reordering"],
        "recall": [
            {"q": "Name two canonical keys for an anagram class and their costs.",
             "a": "Sorted letters, O(k log k); 26-count tuple, O(k)."},
            {"q": "Why tuple(count) and not count?",
             "a": "Lists are mutable and unhashable; dict keys must be hashable."},
        ],
    },
    solutions=[
        Solution("sorted-key", "Key by sorted letters", "O(n · k log k)", "O(n · k)", SORTED_KEY,
                 "Sort each word's letters to get a key shared by all its anagrams."),
        Solution("count-key", "Key by letter counts", "O(n · k)", "O(n · k)", COUNT_KEY,
                 "Count letters into 26 slots; the frozen counts are the key. No sorting needed.", optimal=True),
    ],
    pitfalls=[
        Pitfall("merged-groups", "Merged words that aren't anagrams",
                "Your key collides for words with different letter counts - e.g. a set of letters, or a sum of character codes.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) < len(e)),
        Pitfall("split-groups", "Split anagrams into different groups",
                "Your key isn't canonical: two anagrams produced different keys.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) > len(e)),
    ],
    edge_cases=[{"strs": [""]}, {"strs": ["a"]}, {"strs": ["", ""]}, {"strs": ["ab", "ba", "abc", "cab", "b"]},
                {"strs": ["ac", "bb"]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    compare="unordered_nested",
    lesson={"strs": ["eat", "tea", "tan", "ate", "nat", "bat"]},
    lens={"maps": {"groups": {"key": "letter-counts"}}},
    related=["valid-anagram"],
)
