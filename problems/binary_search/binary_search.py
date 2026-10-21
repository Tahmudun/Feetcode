from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    n = max(1, n)
    gap = rng.choice((1, 2, 5, 1000))
    start = rng.randint(-50, 50)
    nums = sorted(rng.sample(range(start, start + gap * n + n), n))
    roll = rng.random()
    if roll < 0.55:
        target = rng.choice(nums)                       # present: anywhere, ends included
    elif roll < 0.7:
        target = rng.choice((nums[0] - 1, nums[-1] + 1))  # just outside either end
    else:
        target = rng.randint(nums[0] - 2, nums[-1] + 2)  # often falls between two values
    return {"nums": nums, "target": target}


def validate(args):
    nums = args["nums"]
    return 1 <= len(nums) and all(a < b for a, b in zip(nums, nums[1:]))


def worst_case(n):
    # Absent and larger than everything: the scan reads all n values, binary search halves log n times.
    nums = list(range(0, 2 * max(1, n), 2))
    return {"nums": nums, "target": nums[-1] + 1}


SCAN = '''class Solution:
    def search(self, nums: List[int], target: int) -> int:
        for i, num in enumerate(nums):  #> Read nums[{i}] = {num}.
            if num == target:  #> That's {target}. || Not {target}.
                return i  #> Found at index {_return}, after reading every value before it.
        return -1  #> Read all {len(nums)} values; {target} isn't there. The scan never used the fact that nums is sorted.
'''

BINARY = '''class Solution:
    def search(self, nums: List[int], target: int) -> int:
        lo, hi = 0, len(nums) - 1  #> If {target} is anywhere, it's in nums[{lo}..{hi}] - the whole array for now. #! Name the invariant before writing the loop: "if target exists, it is in nums[lo..hi]". Every update below must keep that sentence true.
        while lo <= hi:  #> {hi - lo + 1} candidate(s) left: nums[{lo}..{hi}]. || lo passed hi: no candidates are left.
            mid = (lo + hi) // 2  #> Probe the middle: nums[{mid}] = {nums[mid]}.
            if nums[mid] == target:  #> That's {target}. ||
                return mid  #> Found at index {_return}.
            if nums[mid] < target:  #> {nums[mid]} < {target}, and everything left of mid is even smaller - discard nums[{lo}..{mid}]. || {nums[mid]} > {target}, and everything right of mid is even bigger - discard nums[{mid}..{hi}]. #! One comparison rules out half the range, not just one element. That's the whole algorithm: sortedness turns each probe into a verdict on an entire side.
                lo = mid + 1  #> The search continues in nums[{lo}..{hi}].
            else:
                hi = mid - 1  #> The search continues in nums[{lo}..{hi}]. #! mid - 1, not mid: nums[mid] was already checked. Keeping mid in the range would let lo == hi == mid loop forever.
        return -1  #> The range is empty, so {target} isn't in nums.
'''

PROBLEM = Problem(
    id="binary-search",
    number=704,
    slug="binary-search",
    title="Binary Search",
    difficulty="Easy",
    pattern="binary-search",
    order=1,
    signature=sig("search", "int", nums="List[int]", target="int"),
    statement="""
You're given an array `nums` of **distinct** integers sorted in increasing order, and an integer `target`. Return the index where `target` appears, or `-1` if it isn't in the array.

Your solution should run in **O(log n)** time - fast enough that it never needs to look at most of the array.
""",
    examples=[
        {"args": {"nums": [-4, 0, 2, 7, 11, 19], "target": 7}, "output": 3,
         "explain": "nums[3] = 7."},
        {"args": {"nums": [-4, 0, 2, 7, 11, 19], "target": 5}, "output": -1,
         "explain": "5 would sit between 2 and 7, but it isn't there."},
        {"args": {"nums": [8], "target": 8}, "output": 0},
    ],
    constraints=["1 ≤ nums.length ≤ 10⁴", "−10⁴ < nums[i], target < 10⁴", "All values in nums are distinct.",
                 "nums is sorted in increasing order."],
    companies={"Amazon": 3, "Microsoft": 3, "Google": 3, "Meta": 2, "Apple": 2, "Adobe": 2, "Bloomberg": 2},
    topics=["Array", "Binary Search"],
    hints=[
        "A scan works but ignores the sorting. If you look at the middle value and it's too small, what do you know about everything to its left?",
        "Keep two indices lo and hi so that the target, if present, is always somewhere in nums[lo..hi].",
        "Probe mid = (lo + hi) // 2. Too small: lo = mid + 1. Too big: hi = mid - 1. Stop when lo > hi.",
    ],
    insight={
        "pattern": "Halve the search range",
        "oneLiner": "Probe the middle; sortedness tells you which half can't contain the target, so throw it away.",
        "mnemonic": "Guess the middle page of the dictionary, then tear the wrong half off.",
        "why": "In a sorted array, nums[mid] < target means every index ≤ mid is also too small. One comparison eliminates "
               "half the candidates, so n candidates run out after about log₂ n probes.",
        "signals": ["sorted input", "\"O(log n)\" in the requirements", "find a value or its position"],
        "recall": [
            {"q": "What is the loop invariant of iterative binary search?",
             "a": "If the target exists, it lies in nums[lo..hi]. The loop runs while that range is non-empty (lo ≤ hi)."},
            {"q": "Why lo = mid + 1 rather than lo = mid?",
             "a": "nums[mid] was already checked. Keeping it can leave lo == hi == mid forever - an infinite loop."},
            {"q": "Why while lo <= hi and not lo < hi?",
             "a": "With an inclusive range, lo == hi is one unchecked candidate. lo < hi would exit without checking it."},
        ],
    },
    solutions=[
        Solution("scan", "Linear scan", "O(n)", "O(1)", SCAN,
                 "Check every value in order. Correct, but it reads up to n values and ignores the one thing the "
                 "problem gives you: the array is sorted."),
        Solution("binary", "Iterative binary search", "O(log n)", "O(1)", BINARY,
                 "Keep the target's possible range as [lo, hi]. Each probe of the middle either finds it or halves the "
                 "range, so about log₂ n probes decide the answer.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("skipped-last-candidate", "Stopped one candidate too early",
                "You returned -1 for a target that is in the array. With an inclusive range, `while lo < hi` exits while "
                "one candidate (lo == hi) is still unchecked - use `while lo <= hi`.",
                detect=lambda a, e, x: x == -1 and e != -1),
        Pitfall("found-a-ghost", "Returned an index for a missing target",
                "The target isn't in the array, but you returned an index. Return -1 when the range runs out, and only "
                "return mid after nums[mid] == target.",
                detect=lambda a, e, x: e == -1 and x != -1),
        Pitfall("mid-not-excluded", "The range stopped shrinking",
                "Setting lo = mid (or hi = mid) keeps an already-checked index in the range. Once lo and hi are adjacent "
                "or equal, mid never changes and the loop never ends. Use mid + 1 and mid - 1.",
                error="TimeLimit: infinite loop"),
    ],
    edge_cases=[
        {"nums": [5], "target": 5},
        {"nums": [5], "target": 4},
        {"nums": [1, 3], "target": 3},
        {"nums": [1, 3], "target": 2},
        {"nums": [-9, -5, 0, 4, 8, 12], "target": -9},
        {"nums": [-9, -5, 0, 4, 8, 12], "target": 12},
        {"nums": [-9, -5, 0, 4, 8, 12], "target": 13},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    big=20000,  # the O(n) scan has to run out of operations, as the O(log n) requirement says
    lesson={"nums": [-3, 1, 4, 6, 9, 12, 15, 20, 27], "target": 12},
    lens={"arrays": {"nums": {"pointers": ["lo", "mid", "hi"], "window": ["lo", "hi"]}}},
    follow_up="If nums could contain duplicates, how would you return the first index of target?",
    related=["search-in-rotated-sorted-array", "search-a-2d-matrix", "two-sum-ii-input-array-is-sorted"],
)
