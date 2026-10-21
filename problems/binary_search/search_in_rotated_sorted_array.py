from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    n = max(1, n)
    gap = rng.choice((1, 3, 1000))
    base = sorted(rng.sample(range(-60, -60 + gap * n + n), n))
    k = rng.choice((0, n - 1, rng.randrange(n))) if n > 1 else 0
    nums = base[k:] + base[:k]
    roll = rng.random()
    if roll < 0.6:
        target = rng.choice(nums)
    elif roll < 0.75:
        target = rng.choice((base[0] - 1, base[-1] + 1))
    else:
        target = rng.randint(base[0] - 2, base[-1] + 2)
    return {"nums": nums, "target": target}


def validate(args):
    nums = args["nums"]
    if not nums or len(set(nums)) != len(nums):
        return False
    drops = sum(1 for a, b in zip(nums, nums[1:]) if a > b)
    return drops == 0 or (drops == 1 and nums[-1] < nums[0])


def worst_case(n):
    # Absent and above everything: the scan reads all n values, the binary searches run their full log n rounds.
    n = max(1, n)
    k = n // 3
    base = list(range(0, 2 * n, 2))
    return {"nums": base[k:] + base[:k], "target": 2 * n + 1}


SCAN = '''class Solution:
    def search(self, nums: List[int], target: int) -> int:
        for i, num in enumerate(nums):  #> nums[{i}] = {num}.
            if num == target:  #> That's {target}. ||
                return i  #> Found at index {_return} by reading everything before it.
        return -1  #> {target} isn't in nums - and we had to read all {len(nums)} values to know.
'''

PIVOT = '''class Solution:
    def search(self, nums: List[int], target: int) -> int:
        lo, hi = 0, len(nums) - 1  #> Phase 1: find where the second sorted run starts.
        while lo < hi:  #~
            mid = (lo + hi) // 2  #~
            if nums[mid] > nums[hi]:  #> nums[{mid}] = {nums[mid]} > nums[{hi}] = {nums[hi]}: the drop is right of {mid}. || nums[{mid}] = {nums[mid]} ≤ nums[{hi}] = {nums[hi]}: the drop is at {mid} or left of it.
                lo = mid + 1  #~
            else:
                hi = mid  #~
        pivot = lo  #> The smallest value, {nums[pivot]}, is at index {pivot}. nums[0..{pivot - 1}] and nums[{pivot}..{len(nums) - 1}] are each sorted.
        if pivot > 0 and nums[0] <= target <= nums[pivot - 1]:  #> {target} fits the first run, {nums[0]}..{nums[pivot - 1]}. || So {target} can only be in the second run.
            lo, hi = 0, pivot - 1  #> Phase 2: an ordinary binary search in nums[{lo}..{hi}].
        else:
            lo, hi = pivot, len(nums) - 1  #> Phase 2: an ordinary binary search in nums[{lo}..{hi}].
        while lo <= hi:  #> Candidates: nums[{lo}..{hi}]. || Nothing left to search.
            mid = (lo + hi) // 2  #~
            if nums[mid] == target:  #> nums[{mid}] is {target}. ||
                return mid  #> Found at index {_return}.
            if nums[mid] < target:  #> {nums[mid]} < {target}: go right. || {nums[mid]} > {target}: go left.
                lo = mid + 1  #~
            else:
                hi = mid - 1  #~
        return -1  #> {target} isn't in nums.
'''

ONE_PASS = '''class Solution:
    def search(self, nums: List[int], target: int) -> int:
        lo, hi = 0, len(nums) - 1  #> If {target} is in nums, it's in nums[{lo}..{hi}].
        while lo <= hi:  #> Candidates: nums[{lo}..{hi}]. || No candidates left.
            mid = (lo + hi) // 2  #> Probe nums[{mid}] = {nums[mid]}.
            if nums[mid] == target:  #> That's {target}. ||
                return mid  #> Found at index {_return}.
            if nums[lo] <= nums[mid]:  #> nums[{lo}..{mid}] runs {nums[lo]}..{nums[mid]} with no drop: the left half is sorted. || nums[{lo}] = {nums[lo]} > nums[{mid}] = {nums[mid]}, so the drop is in the left half - which means the right half, {nums[mid]}..{nums[hi]}, is sorted. #! One half of every split is sorted, because the array has only one drop. Check the sorted half: its ends tell you instantly whether target is inside it. If not, it's in the other half.
                if nums[lo] <= target < nums[mid]:  #> {target} lies inside {nums[lo]}..{nums[mid]}: keep the left half. || {target} isn't inside {nums[lo]}..{nums[mid]}: it can only be in the right half.
                    hi = mid - 1  #~
                else:
                    lo = mid + 1  #~
            else:
                if nums[mid] < target <= nums[hi]:  #> {target} lies inside {nums[mid]}..{nums[hi]}: keep the right half. || {target} isn't inside {nums[mid]}..{nums[hi]}: it can only be in the left half.
                    lo = mid + 1  #~
                else:
                    hi = mid - 1  #~
        return -1  #> The range is empty: {target} isn't in nums.
'''

PROBLEM = Problem(
    id="search-in-rotated-sorted-array",
    number=33,
    slug="search-in-rotated-sorted-array",
    title="Search in Rotated Sorted Array",
    difficulty="Medium",
    pattern="binary-search",
    order=5,
    signature=sig("search", "int", nums="List[int]", target="int"),
    statement="""
`nums` holds **distinct** integers that were sorted in increasing order and then rotated: a prefix was moved, in order, to the back (possibly an empty prefix). `[1, 3, 5, 7, 9]` rotated by 3 is `[7, 9, 1, 3, 5]`.

Return the index of `target` in `nums`, or `-1` if it isn't there. Your solution must run in **O(log n)** time.
""",
    examples=[
        {"args": {"nums": [7, 9, 1, 3, 5], "target": 3}, "output": 3},
        {"args": {"nums": [7, 9, 1, 3, 5], "target": 8}, "output": -1,
         "explain": "8 would sit between 7 and 9, but it isn't there."},
        {"args": {"nums": [4], "target": 4}, "output": 0},
    ],
    constraints=["1 ≤ nums.length ≤ 5000", "−10⁴ ≤ nums[i], target ≤ 10⁴", "All values are distinct.",
                 "nums is a sorted array rotated between 0 and n − 1 times."],
    companies={"Amazon": 4, "Meta": 4, "Microsoft": 4, "Google": 3, "LinkedIn": 3, "Bloomberg": 3, "Apple": 3,
               "Uber": 2, "Adobe": 2},
    topics=["Array", "Binary Search"],
    hints=[
        "Split the array at mid. With only one drop in the whole array, at least one half has no drop at all.",
        "A sorted half tells you its range from its two ends. Is target inside that range?",
        "If nums[lo] <= nums[mid], the left half is sorted: go left only if nums[lo] <= target < nums[mid]. "
        "Otherwise the right half is sorted: go right only if nums[mid] < target <= nums[hi].",
    ],
    insight={
        "pattern": "Binary search with a sorted half",
        "oneLiner": "At every split one half is sorted; check whether target fits its range, and discard whichever half can't hold it.",
        "mnemonic": "Trust the tidy half.",
        "why": "A rotated sorted array has a single drop, so mid splits it into one sorted half and one that may contain "
               "the drop. A sorted half's ends bound its values, so 'is target in here?' is two comparisons - and "
               "either answer discards half the range.",
        "signals": ["\"rotated sorted array\" with a target", "O(log n) required", "distinct values"],
        "recall": [
            {"q": "How do you know the left half is sorted?",
             "a": "nums[lo] <= nums[mid]. The <= matters when lo == mid (a one-element left half)."},
            {"q": "Once you know which half is sorted, how do you choose a side?",
             "a": "If target is within the sorted half's endpoints, search it; otherwise search the other half."},
            {"q": "What's the two-phase alternative?",
             "a": "First binary-search the rotation point (the minimum), then binary-search the one sorted run that can contain target."},
        ],
    },
    solutions=[
        Solution("scan", "Linear scan", "O(n)", "O(1)", SCAN,
                 "Check each value. Correct, but O(n) - the rotation doesn't matter to it, and neither does the sorting."),
        Solution("pivot", "Find the rotation point, then search one run", "O(log n)", "O(1)", PIVOT,
                 "Binary-search the index of the minimum, which splits nums into two sorted runs. Target's value "
                 "says which run it must be in; binary-search that one."),
        Solution("one-pass", "One binary search, trusting the sorted half", "O(log n)", "O(1)", ONE_PASS,
                 "At each mid, one half is sorted. If target lies within that half's endpoints, search it; "
                 "otherwise search the other half. One loop, one pass.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("strict-sorted-check", "Misjudged a one-element left half",
                "When lo == mid, the left half is just nums[mid], which is trivially sorted - but nums[lo] < nums[mid] "
                "says it isn't. Use nums[lo] <= nums[mid].",
                code=r"nums\[(lo|l|left|low)\]\s*<\s*nums\[(mid|m)\]"),
        Pitfall("missed-present", "Returned -1 for a target that's in the array",
                "The target is there. Check the sorted half's bounds carefully: the left half is nums[lo] <= target < "
                "nums[mid], the right half nums[mid] < target <= nums[hi]. And loop while lo <= hi.",
                detect=lambda a, e, x: x == -1 and e != -1),
        Pitfall("found-a-ghost", "Returned an index for a missing target",
                "Only return mid after checking nums[mid] == target.",
                detect=lambda a, e, x: e == -1 and x != -1),
    ],
    edge_cases=[
        {"nums": [1], "target": 1},
        {"nums": [1], "target": 0},
        {"nums": [3, 1], "target": 1},
        {"nums": [3, 1], "target": 3},
        {"nums": [1, 3], "target": 3},
        {"nums": [5, 1, 3], "target": 5},
        {"nums": [2, 3, 4, 5, 6, 7, 1], "target": 1},
        {"nums": [9, 1, 2, 3, 4, 5, 6], "target": 9},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    big=20000,  # the O(n) scan has to run out of operations, as the O(log n) requirement says
    lesson={"nums": [20, 24, 3, 6, 8, 11, 15, 17], "target": 15},
    lens={"arrays": {"nums": {"pointers": ["lo", "mid", "hi"], "window": ["lo", "hi"]}}},
    follow_up="What breaks if values can repeat? Try [1, 0, 1, 1, 1] with target 0.",
    related=["find-minimum-in-rotated-sorted-array", "binary-search"],
)
