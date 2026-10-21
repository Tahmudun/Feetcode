from feetcode.problem import Pitfall, Problem, Solution, sig


def _rotated(rng, n):
    gap = rng.choice((1, 3, 1000))
    base = sorted(rng.sample(range(-60, -60 + gap * n + n), n))
    k = rng.choice((0, n - 1, rng.randrange(n))) if n > 1 else 0  # unrotated and rotate-by-one are favourite bugs
    return base[k:] + base[:k]


def generate(rng, n):
    return {"nums": _rotated(rng, max(1, n))}


def validate(args):
    nums = args["nums"]
    if not nums or len(set(nums)) != len(nums):
        return False
    drops = sum(1 for a, b in zip(nums, nums[1:]) if a > b)
    return drops == 0 or (drops == 1 and nums[-1] < nums[0])


def worst_case(n):
    n = max(1, n)
    k = n // 3
    base = list(range(n))
    return {"nums": base[k:] + base[:k]}


SCAN = '''class Solution:
    def findMin(self, nums: List[int]) -> int:
        smallest = nums[0]  #> Start with nums[0] = {smallest}.
        for num in nums:  #~
            if num < smallest:  #> {num} is smaller - the new minimum. #~
                smallest = num  #~
        return smallest  #> After reading all {len(nums)} values, the minimum is {_return}.
'''

BINARY = '''class Solution:
    def findMin(self, nums: List[int]) -> int:
        lo, hi = 0, len(nums) - 1  #> The minimum is somewhere in nums[{lo}..{hi}].
        while lo < hi:  #> Candidates: nums[{lo}..{hi}]. || One candidate left.
            mid = (lo + hi) // 2  #> Probe nums[{mid}] = {nums[mid]} and compare it with the right end, nums[{hi}] = {nums[hi]}.
            if nums[mid] > nums[hi]:  #> {nums[mid]} > {nums[hi]}: the values drop somewhere after mid, so the minimum is to the right of {mid}. || {nums[mid]} < {nums[hi]}: mid..hi is sorted, so nothing right of mid beats nums[{mid}]. The minimum is at {mid} or to its left. #! Compare with the right end, not the left. nums[mid] > nums[hi] can only happen if the rotation point lies between them; otherwise mid..hi is one sorted run and nums[mid] is its smallest value.
                lo = mid + 1  #> Search nums[{lo}..{hi}].
            else:
                hi = mid  #> Search nums[{lo}..{hi}]. #! hi = mid, not mid - 1: nums[mid] could be the minimum itself.
        return nums[lo]  #> lo and hi met at the rotation point: the minimum is {_return}.
'''

PROBLEM = Problem(
    id="find-minimum-in-rotated-sorted-array",
    number=153,
    slug="find-minimum-in-rotated-sorted-array",
    title="Find Minimum in Rotated Sorted Array",
    difficulty="Medium",
    pattern="binary-search",
    order=4,
    signature=sig("findMin", "int", nums="List[int]"),
    statement="""
An array of **distinct** integers was sorted in increasing order and then rotated: some number of elements (possibly none) were moved from the front to the back, keeping their order. For example `[2, 4, 6, 8, 9]` rotated by 2 is `[6, 8, 9, 2, 4]`.

Given the rotated array `nums`, return its smallest value in **O(log n)** time.
""",
    examples=[
        {"args": {"nums": [6, 8, 9, 2, 4]}, "output": 2,
         "explain": "The original array started at 2."},
        {"args": {"nums": [13, 1, 5, 7, 10]}, "output": 1},
        {"args": {"nums": [3, 5, 7, 11]}, "output": 3,
         "explain": "Rotated by zero: still fully sorted, so the minimum is first."},
    ],
    constraints=["1 ≤ nums.length ≤ 5000", "−5000 ≤ nums[i] ≤ 5000", "All values are distinct.",
                 "nums is a sorted array rotated between 0 and n − 1 times."],
    companies={"Amazon": 4, "Meta": 3, "Microsoft": 3, "Google": 3, "Bloomberg": 3, "Apple": 2, "Goldman Sachs": 2},
    topics=["Array", "Binary Search"],
    hints=[
        "A rotated sorted array is two sorted runs. The minimum is where the second run starts.",
        "Look at nums[mid] and nums[hi]. If nums[mid] > nums[hi], where must the drop be?",
        "If nums[mid] > nums[hi], search right of mid. Otherwise the minimum is at mid or left of it: hi = mid.",
    ],
    insight={
        "pattern": "Binary search for the rotation point",
        "oneLiner": "Compare the middle with the right end: if it's bigger, the drop (and the minimum) is to the right.",
        "mnemonic": "Mid bigger than the right end? The cliff is ahead of you.",
        "why": "Every value before the rotation point is larger than every value after it. So nums[mid] > nums[hi] means "
               "mid is still in the first run and the minimum lies right of mid; otherwise mid..hi is sorted and mid "
               "is as small as anything to its right.",
        "signals": ["\"rotated sorted array\"", "O(log n) required", "find a pivot, break point or minimum"],
        "recall": [
            {"q": "Why compare nums[mid] with nums[hi] rather than nums[lo]?",
             "a": "nums[hi] tells you whether mid..hi is sorted, even when the array isn't rotated at all. "
                  "nums[mid] > nums[lo] is also true for an unrotated array, where the minimum is on the left."},
            {"q": "Why hi = mid but lo = mid + 1?",
             "a": "If nums[mid] > nums[hi], mid can't be the minimum. Otherwise it might be, so it stays in the range."},
        ],
    },
    solutions=[
        Solution("scan", "Linear scan", "O(n)", "O(1)", SCAN,
                 "Track the smallest value seen. Correct, but reads every element."),
        Solution("binary", "Binary search against the right end", "O(log n)", "O(1)", BINARY,
                 "Shrink [lo, hi] toward the rotation point: if nums[mid] > nums[hi] the drop is right of mid, "
                 "otherwise the minimum is at mid or to its left.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("compared-left", "Assumed the array was rotated",
                "Your answer is wrong on an array that wasn't rotated (or was rotated all the way around). Comparing "
                "nums[mid] with nums[lo] can't tell 'sorted' from 'rotated'. Compare with nums[hi] instead.",
                detect=lambda a, e, x: a["nums"] == sorted(a["nums"]) and x != e),
        Pitfall("returned-index", "Returned the minimum's index",
                "The answer is the smallest *value*, nums[lo], not its position lo.",
                detect=lambda a, e, x: isinstance(x, int) and x != e and 0 <= x < len(a["nums"])
                and a["nums"][x] == e),
        Pitfall("dropped-mid", "Skipped over the minimum",
                "When nums[mid] ≤ nums[hi], mid itself might be the minimum. Use hi = mid, not hi = mid - 1.",
                detect=lambda a, e, x: isinstance(x, int) and x != e and x in a["nums"]),
    ],
    edge_cases=[
        {"nums": [1]},
        {"nums": [2, 1]},
        {"nums": [1, 2]},
        {"nums": [1, 2, 3, 4, 5]},
        {"nums": [5, 1, 2, 3, 4]},
        {"nums": [2, 3, 4, 5, 1]},
        {"nums": [-5000, 5000]},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    big=20000,  # the O(n) scan has to run out of operations, as the O(log n) requirement says
    lesson={"nums": [15, 18, 22, 25, 3, 6, 9, 12]},
    lens={"arrays": {"nums": {"pointers": ["lo", "mid", "hi"], "window": ["lo", "hi"]}}},
    follow_up="What if values could repeat? When nums[mid] == nums[hi] you can no longer tell which side the drop is on.",
    related=["search-in-rotated-sorted-array", "binary-search"],
)
