from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    n = max(3, n)
    span = rng.choice((2, 3, 5, 100))
    return {"nums": ints(rng, n, -span, span)}


def validate(args):
    return len(args["nums"]) >= 3


def worst_case(n):
    n = max(3, n)
    return {"nums": [i - n // 2 for i in range(n)]}


def _dups(x):
    keys = [tuple(sorted(t)) for t in x if isinstance(t, list)]
    return len(keys) != len(set(keys))


BRUTE = '''class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        found = set()  #> A set of sorted triples removes duplicates for us.
        n = len(nums)
        for i in range(n):  #~
            for j in range(i + 1, n):  #~
                for k in range(j + 1, n):  #~
                    if nums[i] + nums[j] + nums[k] == 0:  #~
                        found.add(tuple(sorted((nums[i], nums[j], nums[k]))))  #> {nums[i]} + {nums[j]} + {nums[k]} = 0. Triples so far: {sorted(found)}.
        return [list(t) for t in found]  #> Checked all {n * (n - 1) * (n - 2) // 6} triples: {_return}.
'''

SORT_TWO_POINTERS = '''class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        nums.sort()  #> Sort first: {nums}. Duplicates become neighbours, and pairs can be found with two pointers.
        res = []
        for i in range(len(nums) - 2):  #> Anchor nums[{i}] = {nums[i]}. Now find pairs after it that sum to {-nums[i]}.
            if i > 0 and nums[i] == nums[i - 1]:  #> Same anchor value as before - skip it, or we'd repeat triplets. ||
                continue  #~
            if nums[i] > 0:  #> The anchor is positive and so is everything after it - no more triplets can sum to 0. ||
                break  #~
            l, r = i + 1, len(nums) - 1  #> Two pointers over the rest: l = {l}, r = {r}.
            while l < r:  #~
                total = nums[i] + nums[l] + nums[r]  #> {nums[i]} + {nums[l]} + {nums[r]} = {total}.
                if total < 0:  #> Too small: move l right. ||
                    l += 1  #~
                elif total > 0:  #> Too big: move r left. ||
                    r -= 1  #~
                else:
                    res.append([nums[i], nums[l], nums[r]])  #> Zero! Record {res[-1]}.
                    l += 1  #~
                    while l < r and nums[l] == nums[l - 1]:  #> Skip the repeated {nums[l]} so this triplet isn't recorded twice. || #! Duplicates are skipped at both levels: equal anchors in the outer loop, equal left values after a match. Sorting is what makes 'equal' mean 'adjacent'.
                        l += 1  #~
        return res  #> {len(res)} unique triplet(s): {_return}.
'''

PROBLEM = Problem(
    id="3sum",
    number=15,
    slug="3sum",
    title="3Sum",
    difficulty="Medium",
    pattern="two-pointers",
    order=3,
    signature=sig("threeSum", "List[List[int]]", nums="List[int]"),
    statement="""
Given an integer array `nums`, return **every distinct triplet** `[a, b, c]` of values taken from three different positions such that `a + b + c == 0`.

The result must not contain the same triplet twice. Triplets, and the numbers inside them, may be in any order.
""",
    examples=[
        {"args": {"nums": [-2, 0, 1, 1, 2, -1]}, "output": [[-2, 0, 2], [-2, 1, 1], [-1, 0, 1]]},
        {"args": {"nums": [1, 2, -3, 4]}, "output": [[-3, 1, 2]]},
        {"args": {"nums": [0, 0, 0, 0]}, "output": [[0, 0, 0]], "explain": "Many index choices, one distinct triplet."},
    ],
    constraints=["3 ≤ nums.length ≤ 3000", "−10⁵ ≤ nums[i] ≤ 10⁵"],
    companies={"Meta": 5, "Amazon": 5, "Google": 4, "Microsoft": 4, "Apple": 3, "Bloomberg": 3, "Adobe": 3,
               "Uber": 2, "Oracle": 2},
    topics=["Array", "Two Pointers", "Sorting"],
    hints=[
        "Fix one number. What problem is left for the other two?",
        "After sorting, \"find a pair with a given sum\" is Two Sum II - two pointers.",
        "Skip an anchor equal to the previous anchor, and after a match skip equal left values - that's how duplicates are avoided.",
    ],
    insight={
        "pattern": "Sort + anchor + two pointers",
        "oneLiner": "Sort, fix each anchor, and run Two Sum II on the rest; skip equal neighbours to avoid duplicate triplets.",
        "mnemonic": "One fixed, two squeeze.",
        "why": "Sorting costs O(n log n), then each anchor's two-pointer scan is O(n): O(n²) total, down from O(n³).",
        "signals": ["k-sum", "\"unique triplets\"", "sum to zero/target with no duplicate combinations"],
        "recall": [
            {"q": "How are duplicate triplets avoided without a set?",
             "a": "Skip anchors equal to the previous anchor; after a match, advance l past equal values."},
            {"q": "Why can the loop break when nums[i] > 0?", "a": "Everything after it is ≥ nums[i] > 0, so no sum can be 0."},
        ],
    },
    solutions=[
        Solution("brute", "All triples + a set", "O(n³)", "O(n)", BRUTE,
                 "Check every triple and deduplicate by storing sorted tuples in a set."),
        Solution("sort-two-pointers", "Sort + two pointers", "O(n²)", "O(1)", SORT_TWO_POINTERS,
                 "Sort, then for each anchor solve a sorted two-sum on the remainder, skipping duplicates.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("duplicates", "Returned duplicate triplets",
                "Skip anchors equal to the previous one, and after a match move l past repeated values.",
                detect=lambda a, e, x: isinstance(x, list) and _dups(x)),
        Pitfall("missed-after-match", "Stopped after the first match for an anchor",
                "One anchor can be part of several triplets - keep moving the pointers after a match.",
                detect=lambda a, e, x: isinstance(x, list) and not _dups(x) and len(x) < len(e)),
    ],
    edge_cases=[{"nums": [0, 1, 1]}, {"nums": [0, 0, 0]}, {"nums": [-1, 0, 1, 2, -1, -4]}, {"nums": [-2, 0, 0, 2, 2]},
                {"nums": [3, -2, 1, 0]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    compare="unordered_nested",
    big=400,
    sizes=[8, 16, 32, 64, 128, 256],
    lesson={"nums": [-1, 0, 1, 2, -1, -4]},
    lens={"arrays": {"nums": {"pointers": ["i", "l", "r"]}}},
    related=["two-sum-ii-input-array-is-sorted", "two-sum"],
)
