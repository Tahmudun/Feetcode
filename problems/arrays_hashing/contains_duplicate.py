from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    n = max(1, n)
    span = rng.choice((n // 2 + 1, n, 4 * n + 5, 10**9))
    nums = ints(rng, n, -span, span)
    if rng.random() < 0.3:
        nums = list(dict.fromkeys(nums))  # sometimes force all-distinct
    return {"nums": nums}


def validate(args):
    return len(args["nums"]) >= 1


def worst_case(n):
    return {"nums": list(range(n))}  # all distinct: every method must look at everything


BRUTE = '''class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        for i in range(len(nums)):  #> Take nums[{i}] = {nums[i]} and compare it with everything after it.
            for j in range(i + 1, len(nums)):  #~
                if nums[i] == nums[j]:  #> nums[{i}] == nums[{j}]: both are {nums[i]}. || nums[{i}] = {nums[i]} vs nums[{j}] = {nums[j]}: different.
                    return True  #> A repeat - stop immediately.
        return False  #> Every pair was different, so there are no duplicates.
'''

SORTING = '''class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        nums = sorted(nums)  #> Sort a copy: {nums}. Equal values are now next to each other.
        for i in range(1, len(nums)):  #~
            if nums[i] == nums[i - 1]:  #> Neighbours nums[{i - 1}] and nums[{i}] are both {nums[i]}. || {nums[i - 1]} and {nums[i]} differ - move on.
                return True  #> Duplicate found.
        return False  #> No equal neighbours anywhere, so all values are distinct.
'''

HASHSET = '''class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        seen = set()  #> A set gives O(1) "have I seen this?" checks.
        for num in nums:  #> Next number: {num}.
            if num in seen:  #> {num} is already in the set - a repeat. || {num} is new.
                return True  #> Duplicate found after one partial pass.
            seen.add(num)  #> Add {num}. Seen so far: {sorted(seen)}.
        return False  #> We got to the end without a repeat.
'''

PROBLEM = Problem(
    id="contains-duplicate",
    number=217,
    slug="contains-duplicate",
    title="Contains Duplicate",
    difficulty="Easy",
    pattern="arrays-hashing",
    order=1,
    signature=sig("containsDuplicate", "bool", nums="List[int]"),
    statement="""
Given an integer array `nums`, return `true` if **some value appears at least twice**, and `false` if every value is unique.
""",
    examples=[
        {"args": {"nums": [7, 2, 9, 2]}, "output": True, "explain": "2 appears at index 1 and index 3."},
        {"args": {"nums": [4, 1, 8, 6]}, "output": False},
        {"args": {"nums": [5, 5, 5, 0, 5]}, "output": True},
    ],
    constraints=["1 ≤ nums.length ≤ 10⁵", "−10⁹ ≤ nums[i] ≤ 10⁹"],
    companies={"Amazon": 4, "Apple": 4, "Google": 3, "Microsoft": 3, "Adobe": 3, "Bloomberg": 2, "Uber": 2, "Yahoo": 2},
    topics=["Array", "Hash Table", "Sorting"],
    hints=[
        "Comparing every pair works, but it's O(n²). What would let you check a value against *everything before it* at once?",
        "Sorting puts equal values side by side - then you only compare neighbours.",
        "A hash set answers \"have I seen this?\" in O(1). One pass is enough.",
    ],
    insight={
        "pattern": "Seen-set",
        "oneLiner": "Remember everything you've passed in a hash set; a duplicate is any value that's already there.",
        "mnemonic": "Set before you forget.",
        "why": "Each membership check is O(1) on average, so the whole scan is O(n) - at the price of O(n) extra memory.",
        "signals": ["\"appears more than once\"", "\"any repeated value\"", "uniqueness checks"],
        "recall": [
            {"q": "What are the three approaches and their costs?",
             "a": "Pairs O(n²)/O(1); sort O(n log n)/O(1)-ish; hash set O(n)/O(n)."},
            {"q": "Why can the hash-set loop return early?",
             "a": "The first repeat proves the answer is true - no need to look further."},
        ],
    },
    solutions=[
        Solution("brute", "Compare every pair", "O(n²)", "O(1)", BRUTE,
                 "For each element, scan everything after it for an equal value."),
        Solution("sorting", "Sort, then compare neighbours", "O(n log n)", "O(n)", SORTING,
                 "After sorting, any duplicates are adjacent, so a single neighbour comparison pass finds them."),
        Solution("hashset", "Hash set", "O(n)", "O(n)", HASHSET,
                 "Walk the array once, keeping a set of values seen so far.", optimal=True),
    ],
    pitfalls=[
        Pitfall("self-compare", "Compared an element with itself",
                "If the inner loop starts at i instead of i + 1, every element 'matches' itself.",
                detect=lambda a, e, x: e is False and x is True),
        Pitfall("early-false", "Returned False before checking everything",
                "A `return False` inside the loop gives up after the first comparison. "
                "You can only conclude 'no duplicates' after the loop finishes.",
                detect=lambda a, e, x: e is True and x is False),
    ],
    edge_cases=[{"nums": [1]}, {"nums": [0, 0]}, {"nums": [-1, 1]}, {"nums": [3, 1, 4, 1, 5, 9, 2, 6]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"nums": [4, 1, 7, 3, 7]},
    lens={"arrays": {"nums": {"pointers": ["i", "j"]}}},
    related=["valid-anagram", "longest-consecutive-sequence"],
)
