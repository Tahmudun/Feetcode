from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    span = rng.choice((max(1, n // 2), n + 2, 3 * n + 5))
    nums = ints(rng, n, -span, span)
    if n and rng.random() < 0.3:
        start = rng.randint(-span, span)
        run = list(range(start, start + rng.randint(1, n)))
        nums = (nums + run)[: n]
        rng.shuffle(nums)
    return {"nums": nums}


def worst_case(n):
    # One long run, shuffled deterministically: naive "extend from every number" is O(n²) here.
    nums = list(range(n))
    nums = nums[::2] + nums[1::2]
    return {"nums": nums}


SORTING = '''class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        if not nums:
            return 0
        nums = sorted(set(nums))  #> Deduplicate and sort: {nums}.
        best = cur = 1  #~
        for i in range(1, len(nums)):  #~
            if nums[i] == nums[i - 1] + 1:  #> {nums[i]} follows {nums[i - 1]}: the run grows. || {nums[i]} doesn't follow {nums[i - 1]}: a new run starts.
                cur += 1  #~
            else:
                cur = 1  #~
            best = max(best, cur)  #> Current run {cur}, best {best}.
        return best
'''

HASHSET = '''class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        num_set = set(nums)  #> Put every number in a set for O(1) lookups: {sorted(num_set)}.
        best = 0
        for num in num_set:  #> Consider {num}.
            if num - 1 not in num_set:  #> {num - 1} is missing, so {num} starts a run. || {num - 1} is present, so {num} is inside a run - skip it. #! Only extending from run starts is the whole trick: every number is walked over at most once across all runs, so the total work is O(n).
                length = 1  #~
                while num + length in num_set:  #> {num + length} is in the set - the run keeps going. || {num + length} is missing - the run ends.
                    length += 1  #~
                best = max(best, length)  #> The run from {num} has length {length}. Best so far: {best}.
        return best  #> The longest run has length {_return}.
'''

PROBLEM = Problem(
    id="longest-consecutive-sequence",
    number=128,
    slug="longest-consecutive-sequence",
    title="Longest Consecutive Sequence",
    difficulty="Medium",
    pattern="arrays-hashing",
    order=9,
    signature=sig("longestConsecutive", "int", nums="List[int]"),
    statement="""
Given an unsorted integer array `nums`, return the length of the **longest run of consecutive integers** (like `4, 5, 6, 7`) whose values all appear in `nums`. The values can be anywhere in the array.

Aim for O(n) time.
""",
    examples=[
        {"args": {"nums": [10, 4, 20, 1, 3, 2]}, "output": 4, "explain": "1, 2, 3, 4 are all present."},
        {"args": {"nums": [0, -1, 5, 1, 1, 7, 6]}, "output": 3,
         "explain": "Both -1, 0, 1 and 5, 6, 7 have length 3. The duplicate 1 doesn't extend anything."},
        {"args": {"nums": []}, "output": 0},
    ],
    constraints=["0 ≤ nums.length ≤ 10⁵", "−10⁹ ≤ nums[i] ≤ 10⁹"],
    companies={"Google": 5, "Amazon": 4, "Meta": 4, "Microsoft": 3, "Bloomberg": 3, "Uber": 2, "Spotify": 2},
    topics=["Array", "Hash Table", "Union Find"],
    hints=[
        "Sorting makes it easy but costs O(n log n). What does sorting really help you check?",
        "With a set you can ask \"is x + 1 present?\" in O(1). From which numbers should you start counting?",
        "Only start a count at x when x − 1 is NOT in the set. Then each number is visited a constant number of times.",
    ],
    insight={
        "pattern": "Count only from sequence starts",
        "oneLiner": "Put everything in a set; a number starts a run iff num − 1 is missing - only walk forward from those.",
        "mnemonic": "Start where nothing comes before.",
        "why": "Without the start check, a run of length L is re-walked from each of its L numbers - O(n²) on a long run. "
               "With it, each number is stepped over at most once in total.",
        "signals": ["\"consecutive\" values in an unsorted array", "O(n) required where sorting is the obvious approach"],
        "recall": [
            {"q": "What single check keeps the set solution O(n)?", "a": "Skip num unless num − 1 is absent."},
            {"q": "How should duplicates be handled when sorting?", "a": "Deduplicate (or skip equal neighbours) - they neither extend nor break a run."},
        ],
    },
    solutions=[
        Solution("sorting", "Sort and scan", "O(n log n)", "O(n)", SORTING,
                 "After deduplicating and sorting, consecutive runs are contiguous - count them in one scan."),
        Solution("hashset", "Hash set from run starts", "O(n)", "O(n)", HASHSET,
                 "Only start counting from numbers with no predecessor; walk forward with O(1) lookups.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("duplicates-break", "Duplicates broke a run",
                "When sorted, equal neighbours should be skipped - resetting the run on them undercounts.",
                detect=lambda a, e, x: len(set(a["nums"])) < len(a["nums"]) and isinstance(x, int) and x < e),
        Pitfall("duplicates-count", "Counted duplicates as part of a run",
                "1, 1, 2 is a run of length 2, not 3.",
                detect=lambda a, e, x: len(set(a["nums"])) < len(a["nums"]) and isinstance(x, int) and x > e),
        Pitfall("empty", "Mishandled the empty array",
                "An empty array has longest run 0.",
                detect=lambda a, e, x: a["nums"] == [] and x != 0),
    ],
    edge_cases=[{"nums": []}, {"nums": [7]}, {"nums": [1, 1, 1]}, {"nums": [-2, -3, -1]}, {"nums": [9, 1, 4, 7, 3, -1, 0, 5, 8, -1, 6]}],
    generate=generate,
    worst_case=worst_case,
    lesson={"nums": [100, 4, 200, 1, 3, 2]},
    related=["contains-duplicate"],
)
