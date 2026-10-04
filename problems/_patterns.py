"""Pattern primers: the 'why' behind each family of problems.

Exported by the pipeline to patterns.json and shown on each pattern's page.
"""

PATTERNS = [
    {
        "id": "arrays-hashing",
        "name": "Arrays & Hashing",
        "tagline": "Trade memory for time: remember what you've seen.",
        "summary": "Most brute-force array solutions re-scan data they've already looked at. A hash map or set "
                   "remembers it instead, turning an O(n) search into an O(1) lookup - and an O(n²) algorithm into O(n).",
        "signals": [
            "\"Have I seen this before?\" - duplicates, complements, pairs",
            "Grouping things that are equivalent under some transformation",
            "Counting occurrences or frequencies",
            "An O(n) answer is expected and sorting isn't required",
        ],
        "ideas": [
            {"title": "Seen-set / complement map", "text": "Walk once; before storing x, ask whether its partner is already stored."},
            {"title": "Canonical key", "text": "Map each item to a key shared by everything in its group (sorted letters, counts)."},
            {"title": "Counting", "text": "A dict or a 26-slot array of counts answers 'same letters?' and 'most frequent?'."},
            {"title": "Prefix products/sums", "text": "Precompute running totals so each answer is O(1)."},
        ],
        "template": '''seen = {}                      # value -> index (or count, or group)
for i, x in enumerate(nums):
    if want(x) in seen:        # ask before you store
        return seen[want(x)], i
    seen[x] = i''',
        "complexity": "Usually O(n) time and O(n) extra space - the space is what buys the speed.",
    },
    {
        "id": "two-pointers",
        "name": "Two Pointers",
        "tagline": "Two indices moving with purpose eliminate whole rows of pairs at once.",
        "summary": "Instead of checking every pair (i, j), keep two indices and move one of them based on a comparison. "
                   "Each move rules out every pair involving the discarded position, so n moves cover all n² pairs.",
        "signals": [
            "Sorted input, or input you can sort",
            "Pairs/triplets with a target sum",
            "Palindromes and other mirror checks",
            "Something is bounded by the shorter/smaller of two ends",
        ],
        "ideas": [
            {"title": "Converging pointers", "text": "Start at both ends; the comparison tells you which end can't be part of a better answer."},
            {"title": "Move the bottleneck", "text": "When a value is capped by the smaller of two sides, the smaller side is the one to move."},
            {"title": "Anchor + squeeze", "text": "For k-sum, fix one element and run two pointers on the rest."},
            {"title": "Skip duplicates", "text": "After sorting, equal values are adjacent - skip them to avoid duplicate answers."},
        ],
        "template": '''l, r = 0, len(nums) - 1
while l < r:
    if good(nums[l], nums[r]):
        record(l, r)
    if should_move_left(nums[l], nums[r]):
        l += 1
    else:
        r -= 1''',
        "complexity": "O(n) per scan, O(1) extra space. Add O(n log n) if you sort first.",
    },
    {
        "id": "sliding-window",
        "name": "Sliding Window",
        "tagline": "Grow to explore, shrink to repair - and never move backwards.",
        "summary": "For contiguous subarrays or substrings, keep a window [l, r] with a running summary (a set, counts, a sum). "
                   "Extend r to explore; when the window breaks a rule, advance l until it's valid again. "
                   "Both pointers only move forward, so the 'nested' loop is O(n) in total.",
        "signals": [
            "\"Longest/shortest contiguous substring or subarray such that …\"",
            "A condition you can repair by removing elements from the left",
            "Fixed-size windows: \"every window of length k\"",
            "Counts of characters inside a range",
        ],
        "ideas": [
            {"title": "Variable window", "text": "for r: add s[r]; while invalid: remove s[l], l += 1; update the answer."},
            {"title": "Fixed window", "text": "When the size is fixed, each slide adds one element and removes one: O(1) updates."},
            {"title": "Validity formula", "text": "Find a cheap test for 'window is valid' - e.g. len − maxFreq ≤ k."},
            {"title": "Monotonic deque", "text": "Keep candidates in decreasing order to read the window max in O(1)."},
        ],
        "template": '''window = Counter()
l = best = 0
for r, x in enumerate(s):
    window[x] += 1
    while invalid(window):
        window[s[l]] -= 1
        l += 1
    best = max(best, r - l + 1)''',
        "complexity": "O(n): each element enters and leaves the window once. Space is the window summary.",
    },
    {
        "id": "stack",
        "name": "Stack",
        "tagline": "The most recent unfinished thing is the one that matters next.",
        "summary": "Stacks model nesting and 'most recent unmatched' relationships: brackets, expression evaluation, and the "
                   "monotonic stack, where each element waits until something larger (or smaller) arrives to resolve it.",
        "signals": [
            "Matching pairs and nesting",
            "\"Next greater/smaller element\", spans, waiting times",
            "Evaluating expressions",
            "Undo / backtracking, or a min/max that must survive pops",
        ],
        "ideas": [
            {"title": "Match the top", "text": "A closer must match the most recent unmatched opener - the top of the stack."},
            {"title": "Monotonic stack", "text": "Keep the stack sorted; a new element pops everything it resolves. Each item is pushed and popped once."},
            {"title": "Augmented stack", "text": "Store extra info (like the running minimum) with every element."},
            {"title": "Operand stack", "text": "Numbers wait on the stack; operators consume the top two."},
        ],
        "template": '''stack = []                      # indices still waiting
for i, x in enumerate(nums):
    while stack and nums[stack[-1]] < x:
        j = stack.pop()             # x resolves j
        answer[j] = i - j
    stack.append(i)''',
        "complexity": "Monotonic stacks are O(n) total: every index is pushed once and popped at most once.",
    },
    {
        "id": "linked-list",
        "name": "Linked List",
        "tagline": "It's all pointer surgery - draw the arrows before you move them.",
        "summary": "Linked list problems are about rewiring next pointers without losing anything. A handful of moves cover "
                   "almost everything: a dummy head, save-flip-advance reversal, fast/slow pointers, and merging.",
        "signals": [
            "Reverse, reorder, or remove nodes in place",
            "Cycle detection or finding the middle",
            "Merging sorted lists",
            "O(1) extra space on a sequence",
        ],
        "ideas": [
            {"title": "Dummy node", "text": "A node before the head removes every 'what if it's the first node?' special case."},
            {"title": "Save, flip, step", "text": "nxt = curr.next; curr.next = prev; prev, curr = curr, nxt."},
            {"title": "Fast & slow", "text": "Speeds 1 and 2 find the middle, detect cycles, and locate a cycle's entrance."},
            {"title": "Gap pointers", "text": "Start one pointer n nodes ahead to find the n-th node from the end in one pass."},
        ],
        "template": '''dummy = ListNode(0, head)
prev, curr = None, head
while curr:
    nxt = curr.next         # 1. save
    curr.next = prev        # 2. flip
    prev, curr = curr, nxt  # 3. step
return prev''',
        "complexity": "Typically O(n) time and O(1) extra space - the nodes already exist; you only move arrows.",
    },
]
