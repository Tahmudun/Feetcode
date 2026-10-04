from collections import Counter

from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    n = max(1, n)
    dup = rng.randint(1, n)
    nums = list(range(1, n + 1)) + [dup]
    for i in range(len(nums)):
        if nums[i] != dup and rng.random() < 0.15:
            nums[i] = dup  # the duplicate may repeat more than twice
    rng.shuffle(nums)
    return {"nums": nums}


def validate(args):
    nums = args["nums"]
    n = len(nums) - 1
    if n < 1 or any(not 1 <= x <= n for x in nums):
        return False
    return sum(1 for c in Counter(nums).values() if c >= 2) == 1


def shrink(args):
    nums = args["nums"]
    dup = next(v for v, c in Counter(nums).items() if c >= 2)
    # Drop the largest value n (if it isn't the duplicate) - the array stays within [1, n-1].
    n = len(nums) - 1
    if n > 1 and dup != n and n in nums:
        i = nums.index(n)
        yield {"nums": nums[:i] + nums[i + 1:]}
    for i, x in enumerate(nums):
        if x == dup and nums.count(dup) > 2:
            yield {"nums": nums[:i] + [v for v in range(1, n + 1) if v not in nums][:1] + nums[i + 1:]}


def worst_case(n):
    import random
    n = max(1, n)
    nums = list(range(1, n + 1)) + [n // 2 + 1]
    random.Random(n).shuffle(nums)
    return {"nums": nums}


SET = '''class Solution:
    def findDuplicate(self, nums: List[int]) -> int:
        seen = set()  #> Remember every value seen so far.
        for x in nums:  #~
            if x in seen:  #> {x} has been seen before - it's the duplicate. || {x} is new.
                return x  #~
            seen.add(x)  #~
'''

FLOYD = '''class Solution:
    def findDuplicate(self, nums: List[int]) -> int:
        slow = fast = 0  #> Read the array as a linked list: index i points to index nums[i]. Values are in 1..n, so nothing points back to 0 - it's a head. A duplicate value means two indices point to the same node: a cycle.
        while True:  #~
            slow = nums[slow]  #~
            fast = nums[nums[fast]]  #> slow → {slow}, fast → {fast}.
            if slow == fast:  #> They meet at {slow}, somewhere inside the cycle. ||
                break  #~
        slow2 = 0  #> Phase 2: a second pointer starts again from index 0. #! Floyd's theorem: the distance from the start to the cycle's entrance equals the distance from the meeting point to the entrance (going around the loop). Stepping both pointers one at a time, they meet exactly at the entrance - which is the duplicated value.
        while slow != slow2:  #~
            slow = nums[slow]  #~
            slow2 = nums[slow2]  #> slow → {slow}, slow2 → {slow2}.
        return slow  #> They meet at the cycle's entrance: {_return} is the duplicate.
'''

PROBLEM = Problem(
    id="find-the-duplicate-number",
    number=287,
    slug="find-the-duplicate-number",
    title="Find the Duplicate Number",
    difficulty="Medium",
    pattern="linked-list",
    order=8,
    signature=sig("findDuplicate", "int", nums="List[int]"),
    statement="""
`nums` has `n + 1` integers, each in the range `[1, n]`. Exactly **one value is repeated** (possibly more than twice). Return that value.

Do it **without modifying `nums`** and using only **O(1) extra space**.
""",
    examples=[
        {"args": {"nums": [1, 3, 4, 2, 2]}, "output": 2},
        {"args": {"nums": [3, 1, 3, 4, 2]}, "output": 3},
        {"args": {"nums": [2, 2, 2, 2]}, "output": 2, "explain": "The duplicate may appear many times."},
    ],
    constraints=["1 ≤ n ≤ 10⁵", "nums.length == n + 1", "1 ≤ nums[i] ≤ n", "Exactly one value repeats.",
                 "Don't modify nums; O(1) extra space."],
    companies={"Amazon": 4, "Microsoft": 3, "Google": 3, "Meta": 3, "Bloomberg": 3, "Apple": 2, "Uber": 2},
    topics=["Array", "Two Pointers", "Binary Search", "Bit Manipulation"],
    hints=[
        "A set or sorting solves it, but both break the rules (extra space, or modifying the array).",
        "Treat each index as a node with an edge i → nums[i]. Why must this graph contain a cycle?",
        "Floyd's algorithm: find a meeting point with slow/fast pointers, then restart one from 0 - they meet at the cycle entrance.",
    ],
    insight={
        "pattern": "Array as a linked list + Floyd's cycle entrance",
        "oneLiner": "Follow i → nums[i] from index 0; the duplicate is the entrance of the cycle, found with Floyd's two phases.",
        "mnemonic": "Two arrows into one node make a loop - find where the loop starts.",
        "why": "n + 1 indices map into n values, so two indices share a target (pigeonhole). That shared target is where the cycle begins.",
        "signals": ["values are valid indices", "O(1) space with no modification", "\"exactly one duplicate\""],
        "recall": [
            {"q": "Phase 1 and phase 2 of Floyd?", "a": "1: slow/fast until they meet. 2: reset one pointer to the start; step both by 1 until they meet - that's the entrance."},
            {"q": "Why start at index 0?", "a": "No value is 0, so nothing points into index 0 - it's outside the cycle, like a list head."},
        ],
    },
    solutions=[
        Solution("set", "Hash set", "O(n)", "O(n)", SET,
                 "Return the first value seen twice. Simple, but uses O(n) memory."),
        Solution("floyd", "Floyd's cycle detection", "O(n)", "O(1)", FLOYD,
                 "Treat the array as a linked list i → nums[i]; the duplicate is where its cycle begins.", optimal=True),
    ],
    pitfalls=[
        Pitfall("modified", "Modified the input",
                "Sorting or marking nums in place is not allowed - the follow-up is about O(1) space without mutation.",
                code=r"nums\.sort\(\)|nums\[[^\]]+\]\s*=\s*-"),
        Pitfall("phase-two", "Returned the meeting point instead of the entrance",
                "Where slow and fast meet is somewhere in the cycle. Restart one pointer from 0 and walk both by one step.",
                detect=lambda a, e, x: isinstance(x, int) and x != e and 1 <= x < len(a["nums"])),
    ],
    edge_cases=[{"nums": [1, 1]}, {"nums": [2, 2, 2]}, {"nums": [1, 1, 2]}, {"nums": [2, 5, 9, 6, 9, 3, 8, 9, 7, 1]}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    worst_case=worst_case,
    lesson={"nums": [3, 1, 3, 4, 2]},
    lens={"arrays": {"nums": {"pointers": ["slow", "fast", "slow2"]}}, "overlay": "index-graph"},
    related=["linked-list-cycle"],
)
