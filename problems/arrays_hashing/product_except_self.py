from math import prod

from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    n = max(2, n)
    # Mostly ±1 with a few larger values keeps products small, as the original constraints promise.
    nums = [rng.choice((1, -1)) for _ in range(n)]
    for _ in range(min(n, rng.randint(1, 6))):
        nums[rng.randrange(n)] = rng.randint(-5, 5)
    return {"nums": nums}


def validate(args):
    nums = args["nums"]
    return len(nums) >= 2 and all(-30 <= x <= 30 for x in nums)


def worst_case(n):
    return {"nums": [1 if i % 3 else -1 for i in range(max(2, n))]}


BRUTE = '''class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        res = []
        for i in range(len(nums)):  #> Compute the answer for index {i}.
            p = 1  #~
            for j in range(len(nums)):  #~
                if j != i:  #~
                    p *= nums[j]  #~
            res.append(p)  #> Multiplied everything except nums[{i}]: {p}. That inner loop re-multiplies almost the same numbers for every i.
        return res
'''

PREFIX_SUFFIX = '''class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        n = len(nums)
        left = [1] * n  #> left[i] = product of everything before i.
        for i in range(1, n):  #~
            left[i] = left[i - 1] * nums[i - 1]  #> left[{i}] = left[{i - 1}] × nums[{i - 1}] = {left[i]}
        right = [1] * n  #> right[i] = product of everything after i.
        for i in range(n - 2, -1, -1):  #~
            right[i] = right[i + 1] * nums[i + 1]  #> right[{i}] = right[{i + 1}] × nums[{i + 1}] = {right[i]}
        return [left[i] * right[i] for i in range(n)]  #> Combine: answer[i] = left[i] × right[i] = {_return}.
'''

OPTIMAL = '''class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        n = len(nums)
        res = [1] * n  #> res[i] will become (product of everything left of i) × (product of everything right of i).
        prefix = 1  #> Running product of the elements to the left. Nothing yet, so 1.
        for i in range(n):  #~
            res[i] = prefix  #> res[{i}] = product of everything left of {i} = {prefix}.
            prefix *= nums[i]  #> Fold in nums[{i}] = {nums[i]}: prefix is now {prefix}.
        suffix = 1  #> Sweep back from the right with a running product of the elements to the right. #! The output array doubles as the prefix table, so the only extra memory is two integers - O(1) beyond the answer.
        for i in range(n - 1, -1, -1):  #~
            res[i] *= suffix  #> res[{i}] *= product right of {i} ({suffix}) -> {res[i]}.
            suffix *= nums[i]  #> Fold in nums[{i}] = {nums[i]}: suffix is now {suffix}.
        return res  #> Every slot is left-product × right-product: {_return}. No division anywhere, so zeros are no problem.
'''

PROBLEM = Problem(
    id="product-of-array-except-self",
    number=238,
    slug="product-of-array-except-self",
    title="Product of Array Except Self",
    difficulty="Medium",
    pattern="arrays-hashing",
    order=7,
    signature=sig("productExceptSelf", "List[int]", nums="List[int]"),
    statement="""
Given an integer array `nums`, return an array `answer` where `answer[i]` is the **product of every element except `nums[i]`**.

Solve it in O(n) time **without using division**. Every such product fits in a 32-bit integer.
""",
    examples=[
        {"args": {"nums": [2, 3, 4, 5]}, "output": [60, 40, 30, 24],
         "explain": "answer[0] = 3·4·5 = 60, answer[1] = 2·4·5 = 40, and so on."},
        {"args": {"nums": [-1, 2, 0, 3]}, "output": [0, 0, -6, 0],
         "explain": "Only the position holding the 0 gets a non-zero product."},
        {"args": {"nums": [1, 1]}, "output": [1, 1]},
    ],
    constraints=["2 ≤ nums.length ≤ 10⁵", "−30 ≤ nums[i] ≤ 30", "All products fit in a 32-bit integer."],
    companies={"Amazon": 5, "Meta": 5, "Apple": 3, "Microsoft": 3, "Google": 3, "Lyft": 3, "Asana": 2,
               "Bloomberg": 2, "Uber": 2},
    topics=["Array", "Prefix Sum"],
    hints=[
        "answer[i] splits into two independent parts: the product of everything to the left of i, and everything to the right.",
        "Build a prefix-product array and a suffix-product array. Each answer is one multiplication.",
        "Write the prefix products straight into the output, then sweep from the right with a single running suffix.",
    ],
    insight={
        "pattern": "Prefix × suffix",
        "oneLiner": "Everything-except-i = (everything left of i) × (everything right of i). Two sweeps with running products.",
        "mnemonic": "Left pass fills, right pass finishes.",
        "why": "Each running product is reused for the next index instead of being recomputed, so both sweeps are O(n). "
               "No division means zeros can't break it.",
        "signals": ["\"except self\"", "\"without division\"", "answer depends on everything left and right"],
        "recall": [
            {"q": "Why not total product ÷ nums[i]?",
             "a": "It's banned, and it fails on zeros (division by zero, or one zero making every product 0)."},
            {"q": "How does the optimal solution reach O(1) extra space?",
             "a": "The output array stores the prefix products; the suffix is a single running variable."},
        ],
    },
    solutions=[
        Solution("brute", "Multiply everything else", "O(n²)", "O(1)", BRUTE,
                 "For each i, multiply all other elements. Correct, but it redoes nearly the same work n times."),
        Solution("prefix-suffix", "Prefix and suffix arrays", "O(n)", "O(n)", PREFIX_SUFFIX,
                 "Precompute products to the left and right of every index, then multiply pairwise."),
        Solution("two-sweeps", "Two sweeps, O(1) extra", "O(n)", "O(1)", OPTIMAL,
                 "Store left products in the output, then multiply in right products with a running variable.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("division-zero", "Division breaks on zeros",
                "Dividing the total product by nums[i] fails when nums contains a 0 (and it's not allowed here).",
                detect=lambda a, e, x: 0 in a["nums"] and x != e),
        Pitfall("included-self", "Included nums[i] in its own product",
                "Write res[i] = prefix *before* multiplying nums[i] into prefix.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e)
                and all(x[i] == e[i] * a["nums"][i] for i in range(len(e))) and x != e),
    ],
    edge_cases=[{"nums": [0, 0]}, {"nums": [0, 5]}, {"nums": [-1, -1, -1]}, {"nums": [3, 0, 2, 0]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"nums": [2, 3, 4, 5]},
    lens={"arrays": {"nums": {"pointers": ["i"]}, "res": {"pointers": ["i"]}}},
    related=["trapping-rain-water"],
)
