from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def _merged(a):
    return sorted(a["nums1"] + a["nums2"])


def generate(rng, n):
    total = max(1, n)
    split = rng.choice((0, total, rng.randint(0, total), rng.randint(0, total)))
    span = rng.choice((3, 20, 1000))
    nums1 = sorted(ints(rng, split, -span, span))
    nums2 = sorted(ints(rng, total - split, -span, span))
    return {"nums1": nums1, "nums2": nums2}


def validate(args):
    a, b = args["nums1"], args["nums2"]
    return len(a) + len(b) >= 1 and a == sorted(a) and b == sorted(b)


def worst_case(n):
    # Equal halves with all of nums1 above all of nums2: the merge walks to the middle, and the partition
    # search has to drive i all the way down to 0 (interleaved halves would hit the right split on probe one).
    n = max(2, n)
    return {"nums1": list(range(n // 2, n)), "nums2": list(range(n // 2))}


def _lower_middle_only(a, e, x):
    m = _merged(a)
    k = len(m) // 2
    return len(m) % 2 == 0 and m[k - 1] != m[k] and isinstance(x, (int, float)) and x in (m[k - 1], m[k])


MERGE = '''class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        total = len(nums1) + len(nums2)  #> {total} values in all. Merge just far enough to reach the middle.
        i = j = 0  #~
        prev = curr = 0  #~
        for _ in range(total // 2 + 1):  #~
            prev = curr  #~
            if j == len(nums2) or (i < len(nums1) and nums1[i] <= nums2[j]):  #> The next smallest value is nums1[{i}] = {nums1[i]}. || The next smallest value is nums2[{j}] = {nums2[j]}.
                curr = nums1[i]  #~
                i += 1  #~
            else:
                curr = nums2[j]  #~
                j += 1  #~
        if total % 2:  #> An odd count: the median is the middle value, {curr}. || An even count: the median averages the two middle values, {prev} and {curr}.
            return float(curr)  #> Median: {_return}.
        return (prev + curr) / 2  #> Median: {_return}. Correct - but we walked through half of both arrays to get here.
'''

PARTITION = '''class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        if len(nums1) > len(nums2):  #> nums1 is the longer one - swap, so the search runs over the shorter array. ||
            return self.findMedianSortedArrays(nums2, nums1)  #~
        m, n = len(nums1), len(nums2)  #~
        half = (m + n + 1) // 2  #> The left half of the merged order holds {half} of the {m + n} values. #! Don't merge - choose. The left half takes some count i from nums1 and the rest, j = half - i, from nums2. Only i is free, and it ranges over 0..m, so binary-search it.
        lo, hi = 0, m  #> nums1 contributes somewhere between {lo} and {hi} values.
        while lo <= hi:  #~
            i = (lo + hi) // 2  #> Try {i} from nums1...
            j = half - i  #> ...and {j} from nums2.
            left1 = nums1[i - 1] if i > 0 else float("-inf")  #~ #! Missing neighbours become -inf and +inf, so taking none (or all) of an array needs no special case: an empty side can't break the ordering check.
            right1 = nums1[i] if i < m else float("inf")  #~
            left2 = nums2[j - 1] if j > 0 else float("-inf")  #~
            right2 = nums2[j] if j < n else float("inf")  #~
            if left1 <= right2 and left2 <= right1:  #> {left1} ≤ {right2} and {left2} ≤ {right1}: everything on the left is ≤ everything on the right. This is the median split. || #! Each array is sorted on its own, so only the two cross pairs need checking: nums1's last-left against nums2's first-right, and vice versa.
                if (m + n) % 2:  #> {m + n} values, an odd count: the median is the largest value on the left. || {m + n} values, an even count: the median averages the two values beside the split.
                    return float(max(left1, left2))  #> Median: {_return}.
                return (max(left1, left2) + min(right1, right2)) / 2  #> ({max(left1, left2)} + {min(right1, right2)}) / 2 = {_return}.
            if left1 > right2:  #> nums1's left side ends at {left1}, above {right2} on nums2's right: too many from nums1. || nums2's left side ends at {left2}, above {right1} on nums1's right: too few from nums1.
                hi = i - 1  #~
            else:
                lo = i + 1  #~
'''

PROBLEM = Problem(
    id="median-of-two-sorted-arrays",
    number=4,
    slug="median-of-two-sorted-arrays",
    title="Median of Two Sorted Arrays",
    difficulty="Hard",
    pattern="binary-search",
    order=7,
    signature=sig("findMedianSortedArrays", "float", nums1="List[int]", nums2="List[int]"),
    statement="""
You're given two arrays `nums1` and `nums2`, each sorted in non-decreasing order (either may be empty, but not both). Return the **median** of all their values combined: the middle value of the merged order, or the average of the two middle values when the total count is even.

Aim for **O(log(m + n))** time, where `m` and `n` are the two lengths - without merging the arrays.
""",
    examples=[
        {"args": {"nums1": [1, 4, 9], "nums2": [2, 3, 7, 11, 12]}, "output": 5.5,
         "explain": "Merged: [1, 2, 3, 4, 7, 9, 11, 12]. The middle two are 4 and 7."},
        {"args": {"nums1": [2, 6], "nums2": [5]}, "output": 5.0,
         "explain": "Merged: [2, 5, 6]."},
        {"args": {"nums1": [], "nums2": [3, 8]}, "output": 5.5},
    ],
    constraints=["0 ≤ m, n ≤ 1000", "1 ≤ m + n ≤ 2000", "−10⁶ ≤ nums1[i], nums2[i] ≤ 10⁶"],
    companies={"Google": 5, "Amazon": 4, "Microsoft": 4, "Apple": 4, "Meta": 3, "Adobe": 3, "Bloomberg": 3,
               "Goldman Sachs": 3, "Uber": 2},
    topics=["Array", "Binary Search", "Divide and Conquer"],
    hints=[
        "Merging works in O(m + n). To beat it, describe the median without building the merged array.",
        "The median splits all values into a left half and a right half. If i values of the left half come from nums1, how many come from nums2?",
        "Binary-search i over the shorter array. The split is right when nums1[i−1] ≤ nums2[j] and nums2[j−1] ≤ nums1[i].",
    ],
    insight={
        "pattern": "Binary search on a partition",
        "oneLiner": "Don't merge - choose how many of the left half come from the shorter array, and binary-search that count.",
        "mnemonic": "Cut both decks so every card on the left is ≤ every card on the right.",
        "why": "A left half of fixed size half = (m + n + 1) / 2 is fully described by i, the number taken from nums1. "
               "If nums1's last-left is too big, i is too large; if nums2's last-left is too big, i is too small. "
               "That's a sorted yes/no question over 0..m, so it takes O(log m) probes.",
        "signals": ["two sorted arrays, a k-th element or median", "O(log) required on more than one array",
                    "\"without merging\""],
        "recall": [
            {"q": "Why binary-search the shorter array?",
             "a": "j = half − i must stay within 0..n for every i in 0..m. That holds when m ≤ n, and it makes the search O(log(min(m, n)))."},
            {"q": "What two comparisons decide whether a split is correct?",
             "a": "nums1[i−1] ≤ nums2[j] and nums2[j−1] ≤ nums1[i] - the within-array pairs are sorted already."},
            {"q": "How do you handle i = 0 or i = m?",
             "a": "Treat the missing neighbours as −∞ (left) and +∞ (right), so the comparisons still work."},
        ],
    },
    solutions=[
        Solution("merge", "Merge to the middle", "O(m + n)", "O(1)", MERGE,
                 "Walk both arrays like the merge step of merge sort, stopping at the middle and keeping the last two "
                 "values. Simple and correct, but linear."),
        Solution("partition", "Binary-search the partition", "O(log(min(m, n)))", "O(1)", PARTITION,
                 "Pick i values from the shorter array and half − i from the other. Compare the values beside the cut: "
                 "the comparison says whether i is too big or too small, so binary search finds the median split.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("integer-division", "Used integer division for the even case",
                "With an even count the median is the average of two values, which can end in .5. Use / 2, not // 2.",
                detect=lambda a, e, x: isinstance(x, (int, float)) and abs(x - e) == 0.5 and float(x).is_integer()),
        Pitfall("one-middle-only", "Returned one middle value instead of their average",
                "When the total count is even there are two middle values. The median is their average.",
                detect=_lower_middle_only),
        Pitfall("no-sentinels", "Read past the end of an array",
                "When i is 0 or m (or j is 0 or n), one neighbour of the cut doesn't exist. Use −∞ and +∞ for the missing "
                "values instead of indexing.",
                error="IndexError: list index"),
    ],
    edge_cases=[
        {"nums1": [], "nums2": [4]},
        {"nums1": [4], "nums2": []},
        {"nums1": [1], "nums2": [2]},
        {"nums1": [1, 2], "nums2": [3, 4]},
        {"nums1": [3, 4], "nums2": [1, 2]},
        {"nums1": [5, 5, 5], "nums2": [5, 5]},
        {"nums1": [-1000000], "nums2": [1000000]},
        {"nums1": [1, 2, 3, 4, 5, 6], "nums2": [7]},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    big=20000,  # the O(n) scan has to run out of operations, as the O(log n) requirement says
    compare="float",
    size_of=lambda a: len(a["nums1"]) + len(a["nums2"]),
    lesson={"nums1": [10, 12, 14, 16], "nums2": [1, 2, 3, 4, 5, 20]},
    lens={"arrays": {"nums1": {"pointers": ["i"], "window": ["0", "i - 1"]},
                     "nums2": {"pointers": ["j"], "window": ["0", "j - 1"]}}},
    follow_up="The same partition idea finds the k-th smallest value of two sorted arrays. What changes?",
    related=["binary-search", "merge-two-sorted-lists"],
)
