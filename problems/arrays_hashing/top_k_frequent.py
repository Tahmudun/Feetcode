from collections import Counter

from feetcode.problem import Pitfall, Problem, Solution, sig


def _unique_answer(nums, k):
    freqs = sorted(Counter(nums).values(), reverse=True)
    return 1 <= k <= len(freqs) and (k == len(freqs) or freqs[k - 1] > freqs[k])


def generate(rng, n):
    n = max(1, n)
    for _ in range(100):
        distinct = rng.randint(1, max(1, min(n, 6)))
        values = rng.sample(range(-9, 10), distinct)
        nums = [rng.choice(values) for _ in range(n)]
        k = rng.randint(1, len(set(nums)))
        if _unique_answer(nums, k):
            rng.shuffle(nums)
            return {"nums": nums, "k": k}
    return {"nums": [1] * n, "k": 1}


def validate(args):
    return len(args["nums"]) >= 1 and _unique_answer(args["nums"], args["k"])


def worst_case(n):
    # n distinct values with distinct frequencies is impossible; use ~sqrt(n) values, all frequencies distinct.
    nums, v = [], 0
    while len(nums) < n:
        nums.extend([v] * (v + 1))
        v += 1
    nums = nums[:n]
    k = max(1, len(set(nums)) // 2)
    while not _unique_answer(nums, k) and k > 1:
        k -= 1
    return {"nums": nums, "k": k}


SORTING = '''class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        count = Counter(nums)  #> Frequencies: {dict(count)}.
        ranked = sorted(count, key=count.get, reverse=True)  #> Values ranked by frequency: {ranked}.
        return ranked[:k]  #> Keep the first {k}: {_return}.
'''

HEAP = '''class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        count = Counter(nums)  #> Frequencies: {dict(count)}.
        heap = []  #> A min-heap of (frequency, value) that never holds more than {k} items.
        for num, freq in count.items():  #> Next: {num} with frequency {freq}.
            heapq.heappush(heap, (freq, num))  #> Push it. Heap: {sorted(heap)}.
            if len(heap) > k:  #> Too many - evict the least frequent. || Still at most {k} items.
                heapq.heappop(heap)  #> Evicted. The heap keeps the {k} most frequent seen so far.
        return [num for freq, num in heap]  #> The survivors: {_return}.
'''

BUCKET = '''class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        count = {}  #> First, count how often each value appears.
        for num in nums:  #~
            count[num] = count.get(num, 0) + 1  #> count[{num}] = {count[num]}
        buckets = [[] for _ in range(len(nums) + 1)]  #> Bucket f will hold the values that appear exactly f times. #! A frequency can never exceed len(nums), so there are only n + 1 possible buckets. Indexing by frequency replaces sorting.
        for num, freq in count.items():  #~
            buckets[freq].append(num)  #> {num} appears {freq} time(s), so it goes in bucket {freq}.
        result = []  #> Walk the buckets from the highest frequency down.
        for freq in range(len(buckets) - 1, 0, -1):  #~
            for num in buckets[freq]:  #~
                result.append(num)  #> Take {num} from bucket {freq}. Collected {len(result)} of {k}.
                if len(result) == k:  #~
                    return result  #> The {k} most frequent: {_return}.
        return result
'''

PROBLEM = Problem(
    id="top-k-frequent-elements",
    number=347,
    slug="top-k-frequent-elements",
    title="Top K Frequent Elements",
    difficulty="Medium",
    pattern="arrays-hashing",
    order=5,
    signature=sig("topKFrequent", "List[int]", nums="List[int]", k="int"),
    statement="""
Given an integer array `nums` and an integer `k`, return the `k` values that **appear most often**. The answer may be in any order.

The input guarantees the answer is unique - there is never a tie at the k-th place.
""",
    examples=[
        {"args": {"nums": [4, 4, 4, 2, 2, 9], "k": 2}, "output": [4, 2]},
        {"args": {"nums": [7], "k": 1}, "output": [7]},
        {"args": {"nums": [3, 1, 3, 1, 3, 5, 1, 3], "k": 1}, "output": [3],
         "explain": "3 appears four times, 1 three times, 5 once."},
    ],
    constraints=["1 ≤ nums.length ≤ 10⁵", "1 ≤ k ≤ number of distinct values", "The answer is unique."],
    companies={"Amazon": 5, "Meta": 4, "Google": 3, "Microsoft": 3, "Bloomberg": 3, "Uber": 3, "Oracle": 2,
               "Salesforce": 2, "Yelp": 2},
    topics=["Array", "Hash Table", "Heap", "Bucket Sort", "Counting"],
    hints=[
        "Start by counting. Once you know every value's frequency, the question is just \"which k counts are biggest?\"",
        "Sorting the distinct values by count is O(n log n). A size-k min-heap gets you to O(n log k).",
        "A frequency is an integer between 1 and n. Use it as an index: bucket[f] = values seen f times.",
    ],
    insight={
        "pattern": "Counting + bucket sort",
        "oneLiner": "Count, then index buckets by frequency (frequencies are bounded by n) and read them from the top down.",
        "mnemonic": "When the key is a small integer, index by it instead of sorting by it.",
        "why": "Bucket sort is linear because the 'keys' (frequencies) live in the small range 1..n.",
        "signals": ["\"k most / least frequent\"", "\"top k\"", "frequencies bounded by n"],
        "recall": [
            {"q": "Heap approach: min-heap or max-heap, and why?",
             "a": "Min-heap of size k: the root is the weakest of the current top k, so it's the one to evict."},
            {"q": "Why does bucket sort work here?",
             "a": "Frequencies are integers in [1, n], so n + 1 buckets cover every possibility."},
        ],
    },
    solutions=[
        Solution("sorting", "Count, then sort", "O(n log n)", "O(n)", SORTING,
                 "Count with a hash map, sort the distinct values by count, take k."),
        Solution("heap", "Size-k min-heap", "O(n log k)", "O(n + k)", HEAP,
                 "Keep only the k best candidates in a min-heap; evict the smallest whenever it grows past k."),
        Solution("bucket", "Bucket sort by frequency", "O(n)", "O(n)", BUCKET,
                 "Frequencies are bounded by n, so bucket values by frequency and read buckets from high to low.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("least-frequent", "Returned the least frequent values",
                "Check your sort direction or heap type - a min-heap pops the *smallest* frequency first.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e)
                and sorted(x) == sorted(sorted(Counter(a["nums"]), key=lambda v: Counter(a["nums"])[v])[:len(e)])
                and sorted(x) != sorted(e)),
        Pitfall("values-vs-counts", "Returned frequencies instead of values",
                "The answer is the values themselves, not how often they appear.",
                detect=lambda a, e, x: isinstance(x, list)
                and sorted(x) == sorted(Counter(a["nums"])[v] for v in e) and sorted(x) != sorted(e)),
    ],
    edge_cases=[{"nums": [1], "k": 1}, {"nums": [-1, -1, 2], "k": 1}, {"nums": [5, 6, 7], "k": 3},
                {"nums": [1, 2, 2, 3, 3, 3], "k": 2}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    compare="unordered",
    lesson={"nums": [1, 3, 1, 2, 3, 1, 4], "k": 2},
    related=["group-anagrams"],
)
