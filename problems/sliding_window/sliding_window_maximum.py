from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    n = max(1, n)
    return {"nums": ints(rng, n, -rng.choice((3, 10, 10**4)), rng.choice((3, 10, 10**4))), "k": rng.randint(1, n)}


def validate(args):
    return 1 <= args["k"] <= len(args["nums"])


def worst_case(n):
    n = max(1, n)
    return {"nums": [(i * 13) % 29 for i in range(n)], "k": max(1, n // 4)}


BRUTE = '''class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        res = []
        for i in range(len(nums) - k + 1):  #~
            res.append(max(nums[i:i + k]))  #> Window {nums[i:i + k]} -> max {res[-1]}. Rescanning k elements for every window.
        return res
'''

HEAP = '''class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        heap, res = [], []  #> Max-heap of (-value, index). Stale entries are removed lazily.
        for r, x in enumerate(nums):  #~
            heapq.heappush(heap, (-x, r))  #> Push {x}.
            if r >= k - 1:  #~
                while heap[0][1] <= r - k:  #> The top (index {heap[0][1]}) has left the window - discard it. ||
                    heapq.heappop(heap)  #~
                res.append(-heap[0][0])  #> Window ending at {r}: max {res[-1]}.
        return res
'''

DEQUE = '''class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        dq = deque()  #> A deque of indices whose values decrease from front to back. Its front is always the window's max.
        res = []
        for r in range(len(nums)):  #> Bring in nums[{r}] = {nums[r]}.
            while dq and nums[dq[-1]] < nums[r]:  #> nums[{dq[-1]}] = {nums[dq[-1]]} is smaller than {nums[r]} and will leave the window first - it can never be a maximum again. Pop it. || #! Anything smaller than a newer element is dominated forever: it leaves sooner and is never larger. Popping it keeps the deque decreasing, and every index is pushed and popped at most once - O(n) total.
                dq.pop()  #~
            dq.append(r)  #> Deque now holds values {[nums[i] for i in dq]}.
            if dq[0] <= r - k:  #> Index {dq[0]} slid out of the window - drop it from the front. ||
                dq.popleft()  #~
            if r >= k - 1:  #> Window [{r - k + 1}, {r}] is complete. Its max sits at the front: {nums[dq[0]]}. ||
                res.append(nums[dq[0]])  #~
        return res  #> Window maxima: {_return}.
'''

PROBLEM = Problem(
    id="sliding-window-maximum",
    number=239,
    slug="sliding-window-maximum",
    title="Sliding Window Maximum",
    difficulty="Hard",
    pattern="sliding-window",
    order=6,
    signature=sig("maxSlidingWindow", "List[int]", nums="List[int]", k="int"),
    statement="""
A window of size `k` slides over `nums` from left to right, one position at a time. Return the **maximum of each window** position, in order.
""",
    examples=[
        {"args": {"nums": [4, 2, 12, 3, 8, 1, 5], "k": 3}, "output": [12, 12, 12, 8, 8]},
        {"args": {"nums": [2, -1, 5, 0, 3, 7, 1], "k": 4}, "output": [5, 5, 7, 7]},
        {"args": {"nums": [9], "k": 1}, "output": [9]},
    ],
    constraints=["1 ≤ nums.length ≤ 10⁵", "−10⁴ ≤ nums[i] ≤ 10⁴", "1 ≤ k ≤ nums.length"],
    companies={"Amazon": 5, "Google": 4, "Meta": 3, "Microsoft": 3, "Citadel": 3, "Uber": 3, "Bloomberg": 2,
               "Salesforce": 2},
    topics=["Array", "Queue", "Sliding Window", "Heap", "Monotonic Queue"],
    hints=[
        "Recomputing max for every window is O(n·k). What information from the previous window is reusable?",
        "If a newer element is larger than an older one, can the older one ever be a window maximum again?",
        "Keep a deque of indices with decreasing values: pop smaller values from the back, expired indices from the front.",
    ],
    insight={
        "pattern": "Monotonic deque",
        "oneLiner": "Keep indices whose values strictly decrease; new elements evict smaller ones from the back, "
                    "expired indices fall off the front, and the front is always the max.",
        "mnemonic": "Newer and bigger evicts older and smaller.",
        "why": "An element smaller than a later element can never be a future maximum, so discarding it loses nothing. "
               "Each index enters and leaves the deque once: O(n).",
        "signals": ["max/min of every window", "\"next greater\" style dominance"],
        "recall": [
            {"q": "Why store indices instead of values?", "a": "To know when the front has slid out of the window."},
            {"q": "What invariant does the deque keep?", "a": "Values decrease from front to back; all indices are inside the window."},
        ],
    },
    solutions=[
        Solution("brute", "Max of every window", "O(n · k)", "O(1)", BRUTE,
                 "Take max() of each window slice."),
        Solution("heap", "Max-heap with lazy deletion", "O(n log n)", "O(n)", HEAP,
                 "Push every element; before reading the top, pop entries that are outside the window."),
        Solution("deque", "Monotonic deque", "O(n)", "O(k)", DEQUE,
                 "Maintain a decreasing deque of indices; its front is the current window maximum.", optimal=True),
    ],
    pitfalls=[
        Pitfall("count", "Wrong number of windows",
                "There are len(nums) − k + 1 windows - start appending once r ≥ k − 1.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) != len(e)),
        Pitfall("stale-max", "Kept a maximum after it left the window",
                "Check the front of the deque (or heap) against the window's left edge before reading it.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e) and any(xi > ei for xi, ei in zip(x, e))),
    ],
    edge_cases=[{"nums": [1], "k": 1}, {"nums": [1, -1], "k": 1}, {"nums": [7, 2, 4], "k": 2},
                {"nums": [1, 3, 1, 2, 0, 5], "k": 3}, {"nums": [5, 4, 3, 2, 1], "k": 5}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"nums": [4, 2, 12, 3, 8, 1, 5], "k": 3},
    lens={"arrays": {"nums": {"pointers": ["r"], "window": ["r - k + 1", "r"]}}, "indexes": {"dq": "nums"}},
    related=["daily-temperatures", "largest-rectangle-in-histogram"],
)
