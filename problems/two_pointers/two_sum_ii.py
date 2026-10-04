from feetcode.problem import Pitfall, Problem, Solution, sig


def _pairs(nums, target):
    return [(i, j) for i in range(len(nums)) for j in range(i + 1, len(nums)) if nums[i] + nums[j] == target]


def generate(rng, n):
    n = max(2, n)
    span = rng.choice((5, 20, 1000))
    for _ in range(60):
        nums = sorted(rng.randint(-span, span) for _ in range(n))
        i, j = sorted(rng.sample(range(n), 2))
        target = nums[i] + nums[j]
        if len(_pairs(nums, target)) == 1:
            return {"numbers": nums, "target": target}
    nums = list(range(n))
    return {"numbers": nums, "target": nums[-1] + nums[-2]}


def validate(args):
    nums = args["numbers"]
    return len(nums) >= 2 and nums == sorted(nums) and len(_pairs(nums, args["target"])) == 1


def worst_case(n):
    # The only pair is the last two: binary search misses for every i (n log n), two pointers walk l across (n).
    nums = list(range(max(2, n)))
    return {"numbers": nums, "target": nums[-1] + nums[-2]}


BINARY_SEARCH = '''class Solution:
    def twoSum(self, numbers: List[int], target: int) -> List[int]:
        for i in range(len(numbers)):  #> Fix numbers[{i}] = {numbers[i]}; binary-search for {target - numbers[i]} to its right.
            need = target - numbers[i]  #~
            lo, hi = i + 1, len(numbers) - 1  #~
            while lo <= hi:  #~
                mid = (lo + hi) // 2  #~
                if numbers[mid] == need:  #> Found {need} at index {mid}. ||
                    return [i + 1, mid + 1]  #> 1-indexed answer: {_return}.
                if numbers[mid] < need:  #~
                    lo = mid + 1  #~
                else:
                    hi = mid - 1  #~
'''

TWO_POINTERS = '''class Solution:
    def twoSum(self, numbers: List[int], target: int) -> List[int]:
        l, r = 0, len(numbers) - 1  #> l starts at the smallest value, r at the largest.
        while l < r:  #~
            total = numbers[l] + numbers[r]  #> {numbers[l]} + {numbers[r]} = {total}.
            if total == target:  #> That's the target. || Not {target} yet.
                return [l + 1, r + 1]  #> Positions are 1-indexed: {_return}.
            if total < target:  #> {total} < {target}: too small. Moving l right is the only way to increase the sum. || {total} > {target}: too big. Moving r left is the only way to decrease it. #! Because the array is sorted, one comparison rules out a whole set of pairs: if numbers[l] + numbers[r] is too small, numbers[l] is too small with every partner left of r as well.
                l += 1  #~
            else:
                r -= 1  #~
'''

PROBLEM = Problem(
    id="two-sum-ii-input-array-is-sorted",
    number=167,
    slug="two-sum-ii-input-array-is-sorted",
    title="Two Sum II - Input Array Is Sorted",
    difficulty="Medium",
    pattern="two-pointers",
    order=2,
    signature=sig("twoSum", "List[int]", numbers="List[int]", target="int"),
    statement="""
`numbers` is sorted in non-decreasing order. Find the two different positions whose values add up to `target`, and return them as `[index1, index2]` with **1-indexed** positions and `index1 < index2`.

There is exactly one solution. Use only O(1) extra space.
""",
    examples=[
        {"args": {"numbers": [1, 3, 4, 6, 8], "target": 10}, "output": [3, 4],
         "explain": "4 + 6 = 10, at 1-indexed positions 3 and 4."},
        {"args": {"numbers": [-5, -2, 0, 7], "target": -7}, "output": [1, 2]},
        {"args": {"numbers": [2, 2], "target": 4}, "output": [1, 2]},
    ],
    constraints=["2 ≤ numbers.length ≤ 3 · 10⁴", "numbers is sorted in non-decreasing order",
                 "Exactly one solution exists.", "O(1) extra space."],
    companies={"Amazon": 4, "Google": 3, "Meta": 3, "Microsoft": 3, "Apple": 2, "Bloomberg": 2, "Adobe": 2},
    topics=["Array", "Two Pointers", "Binary Search"],
    hints=[
        "The hash-map Two Sum works but uses O(n) space. What does sortedness buy you?",
        "Look at the smallest + largest. If the sum is too big, can the largest value be part of the answer at all?",
        "Pointers at both ends: too small → move l right, too big → move r left.",
    ],
    insight={
        "pattern": "Converging two pointers on sorted input",
        "oneLiner": "Sum too small → move the left pointer up; too big → move the right pointer down. Sortedness makes each move safe.",
        "mnemonic": "Too small, step right; too big, step left.",
        "why": "When numbers[l] + numbers[r] < target, numbers[l] can't pair with anything ≤ numbers[r], so l can be discarded. "
               "Each step discards one index: O(n) total.",
        "signals": ["sorted array", "pair with a given sum/difference", "O(1) space"],
        "recall": [
            {"q": "Why can l be discarded when the sum is too small?",
             "a": "Every other partner for numbers[l] is ≤ numbers[r], so every sum with it is also too small."},
            {"q": "Gotcha in the output format?", "a": "Indices are 1-indexed."},
        ],
    },
    solutions=[
        Solution("binary-search", "Binary search the complement", "O(n log n)", "O(1)", BINARY_SEARCH,
                 "For each element, binary-search for its complement in the sorted suffix."),
        Solution("two-pointers", "Two pointers", "O(n)", "O(1)", TWO_POINTERS,
                 "Start at both ends; move the pointer that brings the sum toward the target.", optimal=True),
    ],
    pitfalls=[
        Pitfall("zero-indexed", "Returned 0-indexed positions",
                "This problem wants 1-indexed positions: add 1 to both.",
                detect=lambda a, e, x: isinstance(x, list) and x == [e[0] - 1, e[1] - 1]),
        Pitfall("same-index", "Used one element twice",
                "Stop when l == r: the two positions must differ.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == 2 and x[0] == x[1]),
    ],
    edge_cases=[{"numbers": [2, 7, 11, 15], "target": 9}, {"numbers": [-1, 0], "target": -1},
                {"numbers": [0, 0, 3, 4], "target": 0}, {"numbers": [1, 2, 3, 4, 4, 9, 56, 90], "target": 8}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"numbers": [1, 2, 4, 6, 8, 11, 15], "target": 14},
    lens={"arrays": {"numbers": {"pointers": ["l", "r", "i", "lo", "hi", "mid"]}}},
    related=["two-sum", "3sum"],
)
