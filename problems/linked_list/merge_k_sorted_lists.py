from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    k = rng.randint(0, max(1, min(n, 5)))
    lists = [sorted(rng.randint(-9, 9) for _ in range(rng.randint(0, max(1, n // 2) + 1))) for _ in range(k)]
    return {"lists": lists}


def validate(args):
    return all(lst == sorted(lst) for lst in args["lists"])


def shrink(args):
    lists = args["lists"]
    for i in range(len(lists) - 1, -1, -1):
        yield {"lists": lists[:i] + lists[i + 1:]}
    for i, lst in enumerate(lists):
        for j in range(len(lst) - 1, -1, -1):
            yield {"lists": lists[:i] + [lst[:j] + lst[j + 1:]] + lists[i + 1:]}


def worst_case(n):
    k = max(1, int(n ** 0.5))
    per = max(1, n // k)
    return {"lists": [list(range(i, i + per * k, k)) for i in range(k)]}


COLLECT = '''class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        nodes = []
        for head in lists:  #~
            while head:  #~
                nodes.append(head)  #~
                head = head.next  #~
        nodes.sort(key=lambda node: node.val)  #> Collected {len(nodes)} nodes and sorted them by value - O(N log N), ignoring that every list was already sorted.
        dummy = tail = ListNode()
        for node in nodes:  #~
            tail.next = node  #~
            tail = node  #~
        tail.next = None
        return dummy.next
'''

HEAP = '''class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        heap = []  #> A min-heap holding the current head of every list.
        for i, node in enumerate(lists):  #~
            if node:  #~
                heapq.heappush(heap, (node.val, i, node))  #> Push the head of list {i} ({node.val}). #! The index i breaks ties between equal values. ListNode objects can't be compared with <, so a tie must never fall through to comparing nodes.
        dummy = tail = ListNode()
        while heap:  #~
            val, i, node = heapq.heappop(heap)  #> The smallest head across all lists is {val} (list {i}).
            tail.next = node  #~
            tail = node  #~
            if node.next:  #> List {i} continues with {node.next.val} - push it. || List {i} is used up.
                heapq.heappush(heap, (node.next.val, i, node.next))  #~
        return dummy.next  #> Every node was placed with one O(log k) heap operation: O(N log k).
'''

DIVIDE = '''class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        def merge(a, b):
            dummy = tail = ListNode()
            while a and b:  #~
                if a.val <= b.val:  #~
                    tail.next, a = a, a.next  #~
                else:
                    tail.next, b = b, b.next  #~
                tail = tail.next  #~
            tail.next = a or b  #~
            return dummy.next
        while len(lists) > 1:  #> {len(lists)} lists left - merge them in pairs. #! Pairwise rounds halve the number of lists each time, so each node is merged about log k times: O(N log k), like the heap but with no extra memory.
            lists = [merge(lists[i], lists[i + 1] if i + 1 < len(lists) else None) for i in range(0, len(lists), 2)]  #~
        return lists[0] if lists else None
'''

PROBLEM = Problem(
    id="merge-k-sorted-lists",
    number=23,
    slug="merge-k-sorted-lists",
    title="Merge k Sorted Lists",
    difficulty="Hard",
    pattern="linked-list",
    order=10,
    signature=sig("mergeKLists", "Optional[ListNode]", lists="List[Optional[ListNode]]"),
    statement="""
You're given an array of `k` linked lists, each **sorted ascending**. Merge them all into **one sorted linked list** and return its head.
""",
    examples=[
        {"args": {"lists": [[1, 4, 5], [1, 3, 4], [2, 6]]}, "output": [1, 1, 2, 3, 4, 4, 5, 6]},
        {"args": {"lists": []}, "output": []},
        {"args": {"lists": [[], [0]]}, "output": [0]},
    ],
    constraints=["0 ≤ k ≤ 10⁴", "0 ≤ list length ≤ 500", "−10⁴ ≤ Node.val ≤ 10⁴", "Total nodes ≤ 10⁴"],
    companies={"Amazon": 5, "Meta": 5, "Google": 4, "Microsoft": 4, "Bloomberg": 3, "Uber": 3, "Apple": 3,
               "Airbnb": 2, "Oracle": 2},
    topics=["Linked List", "Divide and Conquer", "Heap", "Merge Sort"],
    hints=[
        "Merging two sorted lists is easy. Merging them one at a time into a growing result is O(N·k). Can you do better?",
        "At each step the next node is the smallest among the k current heads. Which structure gives the minimum quickly?",
        "A min-heap of (value, list index, node): pop the smallest, push its successor. Or merge lists in pairs, like merge sort.",
    ],
    insight={
        "pattern": "K-way merge with a min-heap",
        "oneLiner": "Keep the k current heads in a min-heap; repeatedly pop the smallest and push its successor.",
        "mnemonic": "Only the k fronts can be next.",
        "why": "The heap never holds more than k nodes, so each of the N nodes costs O(log k): O(N log k) overall.",
        "signals": ["merge many sorted sequences", "\"k\" sorted inputs", "streaming minimums"],
        "recall": [
            {"q": "What goes into the heap?", "a": "(value, list index, node) - the index breaks ties so nodes are never compared."},
            {"q": "Alternative with no heap?", "a": "Divide and conquer: merge lists in pairs, halving the count each round."},
        ],
    },
    solutions=[
        Solution("collect", "Collect and sort", "O(N log N)", "O(N)", COLLECT,
                 "Gather every node, sort by value, relink. Ignores that the lists are already sorted."),
        Solution("divide", "Merge in pairs", "O(N log k)", "O(1)", DIVIDE,
                 "Repeatedly merge pairs of lists, halving their number each round."),
        Solution("heap", "Min-heap of heads", "O(N log k)", "O(k)", HEAP,
                 "A min-heap of the k current heads yields the next smallest node in O(log k).", optimal=True),
    ],
    pitfalls=[
        Pitfall("compare-nodes", "Heap compared ListNode objects",
                "On equal values, Python compares the next tuple element. Put a tiebreaker (the list index) before the node.",
                error="TypeError: '<' not supported"),
        Pitfall("empty-lists", "Crashed on empty lists",
                "Some lists can be empty (None) and the array itself can be empty.",
                error="AttributeError: 'NoneType'"),
    ],
    edge_cases=[{"lists": []}, {"lists": [[]]}, {"lists": [[], []]}, {"lists": [[1], [1], [1]]}, {"lists": [[5], [-2, 7], []]}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    worst_case=worst_case,
    size_of=lambda a: sum(len(x) for x in a["lists"]),
    lesson={"lists": [[1, 4, 5], [1, 3, 4], [2, 6]]},
    lens={"stacks": []},
    related=["merge-two-sorted-lists", "top-k-frequent-elements"],
)
