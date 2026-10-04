from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def _pairs(nums, target):
    return [(i, j) for i in range(len(nums)) for j in range(i + 1, len(nums)) if nums[i] + nums[j] == target]


def generate(rng, n):
    n = max(2, n)
    span = rng.choice((5, 20, 1000))
    for _ in range(50):
        nums = ints(rng, n, -span, span)
        i, j = sorted(rng.sample(range(n), 2))
        target = nums[i] + nums[j]
        if len(_pairs(nums, target)) == 1:
            return {"nums": nums, "target": target}
    nums = list(range(n))
    return {"nums": nums, "target": nums[-1] + nums[-2]}


def validate(args):
    nums = args["nums"]
    return 2 <= len(nums) and len(_pairs(nums, args["target"])) == 1


def worst_case(n):
    nums = list(range(n))  # the only pair is the last two: brute force checks ~n²/2 pairs
    return {"nums": nums, "target": nums[-1] + nums[-2]}


BRUTE = '''class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        for i in range(len(nums)):  #> Fix nums[{i}] = {nums[i]} and try every partner after it.
            for j in range(i + 1, len(nums)):  #~
                if nums[i] + nums[j] == target:  #> {nums[i]} + {nums[j]} = {nums[i] + nums[j]}, the target. || {nums[i]} + {nums[j]} = {nums[i] + nums[j]}, not {target}. Keep scanning.
                    return [i, j]  #> Found it after checking pairs one by one: {_return}.
'''

HASHMAP = '''class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}  # value -> index  #> An empty map. It will remember every number we pass and where it was.
        for i, num in enumerate(nums):  #> Look at nums[{i}] = {num}.
            need = target - num  #> To reach {target} with {num}, we need its complement: {need}. #! The whole trick: instead of searching for a pair, ask one O(1) question per element - have I already seen target - num?
            if need in seen:  #> {need} is in the map at index {seen[need]}. || {need} hasn't appeared yet.
                return [seen[need], i]  #> Pair found in a single pass: {_return}.
            seen[num] = i  #> Remember {num} -> {i}, so a later number can find it. #! Store *after* checking. Checking first means nums[i] can never pair with itself - the bug behind [3, 3] style failures.
'''

PROBLEM = Problem(
    id="two-sum",
    number=1,
    slug="two-sum",
    title="Two Sum",
    difficulty="Easy",
    pattern="arrays-hashing",
    order=3,
    signature=sig("twoSum", "List[int]", nums="List[int]", target="int"),
    statement="""
You're given an integer array `nums` and an integer `target`. Find the **two different positions** whose values add up to `target`, and return their indices.

Every input has exactly one valid pair, and a position can't be paired with itself. The two indices may be returned in either order.
""",
    examples=[
        {"args": {"nums": [4, 7, 1, 9], "target": 10}, "output": [2, 3],
         "explain": "nums[2] + nums[3] = 1 + 9 = 10."},
        {"args": {"nums": [5, 5], "target": 10}, "output": [0, 1],
         "explain": "Equal values are fine - they sit at different positions."},
        {"args": {"nums": [-3, 8, 2, 11, 5], "target": 7}, "output": [2, 4]},
    ],
    constraints=["2 ≤ nums.length ≤ 10⁴", "−10⁹ ≤ nums[i], target ≤ 10⁹", "Exactly one valid pair exists."],
    companies={"Amazon": 5, "Google": 5, "Meta": 4, "Apple": 4, "Microsoft": 4, "Bloomberg": 4,
               "Adobe": 3, "Uber": 3, "Oracle": 2, "Yahoo": 2},
    topics=["Array", "Hash Table"],
    hints=[
        "Brute force tries every pair. When nums[i] is fixed, what single value is it actually looking for?",
        "For each x you need exactly target − x. What data structure answers \"have I seen this value?\" in O(1)?",
        "Walk once with a map value → index. Check for the complement *before* storing the current number.",
    ],
    insight={
        "pattern": "Complement lookup",
        "oneLiner": "Don't search for pairs. For each x, ask one O(1) question: have I already seen target − x?",
        "mnemonic": "Remember what you've passed; ask for the missing half.",
        "why": "A pair (i, j) is found the moment you reach j, because nums[i] is already in the map. "
               "So one pass suffices: every pair is discovered at its second element.",
        "signals": ["\"find two elements that sum/combine to …\"", "unsorted input", "return indices"],
        "recall": [
            {"q": "What do you store in the map, and what do you look up?",
             "a": "Store value → index of everything seen so far; look up target − current."},
            {"q": "Why check the map before inserting the current number?",
             "a": "So an element can't pair with itself (e.g. target 6 with a single 3)."},
        ],
    },
    solutions=[
        Solution("brute", "Check every pair", "O(n²)", "O(1)", BRUTE,
                 "Fix each index i and scan every j > i. Correct, but the inner scan repeats work: "
                 "it re-reads the same numbers for every i."),
        Solution("hashmap", "One-pass hash map", "O(n)", "O(n)", HASHMAP,
                 "Trade memory for time. As you walk, store value → index. For each new number, the "
                 "complement target − num is either already stored (pair found) or not yet seen.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("same-element", "Paired an element with itself",
                "You returned the same index twice. Look up the complement *before* inserting the current "
                "number, or make sure the two indices differ.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == 2 and x[0] == x[1]),
        Pitfall("values-not-indices", "Returned values instead of indices",
                "The answer is the two *positions*, not the two numbers.",
                detect=lambda a, e, x: isinstance(x, list) and sorted(x) == sorted(a["nums"][i] for i in e)
                and sorted(x) != sorted(e)),
        Pitfall("sorted-indices", "Sorted the array and lost the original indices",
                "Sorting reorders positions. If you sort, sort (value, index) pairs - or use a hash map.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == 2
                and all(isinstance(k, int) and 0 <= k < len(a["nums"]) for k in x)
                and sorted(a["nums"])[x[0]] + sorted(a["nums"])[x[1]] == a["target"]
                and a["nums"][x[0]] + a["nums"][x[1]] != a["target"]),
    ],
    edge_cases=[
        {"nums": [3, 3], "target": 6},
        {"nums": [0, 4, 3, 0], "target": 0},
        {"nums": [-1, -2, -3, -4, -5], "target": -8},
        {"nums": [1, 5, 9, 2], "target": 11},
        {"nums": [1000000000, -1000000000, 7], "target": 0},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    compare="unordered",
    lesson={"nums": [3, 9, 5, 11, 4], "target": 9},
    lens={"arrays": {"nums": {"pointers": ["i", "j"]}}},
    follow_up="Can you find the pair in less than O(n²) time?",
    related=["two-sum-ii", "3sum"],
)
