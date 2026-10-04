from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    cap = rng.randint(1, 3)
    ops, args = ["LRUCache"], [[cap]]
    keys = rng.randint(2, 5)
    for _ in range(max(1, n)):
        if rng.random() < 0.55:
            ops.append("put")
            args.append([rng.randint(1, keys), rng.randint(0, 20)])
        else:
            ops.append("get")
            args.append([rng.randint(1, keys)])
    return {"ops": ops, "args": args}


def validate(args):
    ops, argv = args["ops"], args["args"]
    if not ops or ops[0] != "LRUCache" or len(ops) != len(argv) or len(argv[0]) != 1 or argv[0][0] < 1:
        return False
    for op, a in zip(ops[1:], argv[1:]):
        if (op == "get" and len(a) != 1) or (op == "put" and len(a) != 2) or op not in ("get", "put"):
            return False
    return True


def worst_case(n):
    cap = max(1, n // 2)
    ops, args = ["LRUCache"], [[cap]]
    for i in range(n):
        ops.append("put" if i % 2 == 0 else "get")
        args.append([i, i] if i % 2 == 0 else [i // 2])
    return {"ops": ops, "args": args}


LIST_SCAN = '''class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.order = []  # least recently used first
        self.vals = {}

    def get(self, key: int) -> int:
        if key not in self.vals:  #> {key} isn't cached. ||
            return -1  #~
        self.order.remove(key)  #~
        self.order.append(key)  #> Mark {key} most recent: {self.order}. list.remove() scans the whole list - O(n) per call.
        return self.vals[key]  #~

    def put(self, key: int, value: int) -> None:
        if key in self.vals:  #~
            self.order.remove(key)  #~
        elif len(self.vals) == self.cap:  #> Full - evict the least recent key, {self.order[0]}. ||
            del self.vals[self.order.pop(0)]  #~
        self.vals[key] = value  #~
        self.order.append(key)  #> Order (least → most recent): {self.order}.
'''

DLL = '''class DNode:
    def __init__(self, key=0, val=0):
        self.key, self.val = key, val
        self.prev = self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache = {}  # key -> node  #> A hash map for O(1) lookup, plus a doubly linked list for O(1) reordering.
        self.left, self.right = DNode(), DNode()  #> Two sentinels: left.next is the least recently used node, right.prev the most recent.
        self.left.next, self.right.prev = self.right, self.left  #~

    def _remove(self, node):
        node.prev.next, node.next.prev = node.next, node.prev  #> Unlink {node.key} by joining its neighbours. #! With prev AND next pointers, a node can unlink itself in O(1) - no search needed. That's why the list must be doubly linked.

    def _insert(self, node):
        prev, nxt = self.right.prev, self.right  #~
        prev.next = nxt.prev = node  #~
        node.prev, node.next = prev, nxt  #> {node.key} is now the most recently used.

    def get(self, key: int) -> int:
        if key in self.cache:  #> {key} is cached - move it to the most-recent end. || {key} isn't cached.
            node = self.cache[key]  #~
            self._remove(node)  #~
            self._insert(node)  #~
            return node.val  #> get({key}) = {_return}.
        return -1  #~

    def put(self, key: int, value: int) -> None:
        if key in self.cache:  #> {key} exists - remove the old node first. ||
            self._remove(self.cache[key])  #~
        node = DNode(key, value)  #~
        self.cache[key] = node  #~
        self._insert(node)  #> Stored {key} = {value}.
        if len(self.cache) > self.cap:  #> Over capacity ({len(self.cache)} > {self.cap}): evict the least recently used. || Within capacity.
            lru = self.left.next  #~
            self._remove(lru)  #~
            del self.cache[lru.key]  #> Evicted key {lru.key}. #! Store the key inside each node - when evicting from the list you need it to delete the map entry too.
'''

PROBLEM = Problem(
    id="lru-cache",
    number=146,
    slug="lru-cache",
    title="LRU Cache",
    difficulty="Medium",
    pattern="linked-list",
    order=9,
    signature=sig("", "List", kind="design", cls="LRUCache"),
    statement="""
Design a **Least Recently Used (LRU) cache** with a fixed capacity:

- `LRUCache(capacity)` creates an empty cache.
- `get(key)` returns the value for `key`, or `-1` if it isn't cached. A successful get counts as *using* the key.
- `put(key, value)` inserts or updates `key`. If that pushes the cache over capacity, evict the **least recently used** key.

Both operations must run in **O(1)** average time.
""",
    examples=[
        {"args": {"ops": ["LRUCache", "put", "put", "get", "put", "get", "get"],
                  "args": [[2], [1, 10], [2, 20], [1], [3, 30], [2], [3]]},
         "output": [None, None, None, 10, None, -1, 30],
         "explain": "get(1) makes key 1 recent, so put(3, 30) evicts key 2."},
        {"args": {"ops": ["LRUCache", "put", "put", "get"], "args": [[1], [5, 1], [6, 2], [5]]},
         "output": [None, None, None, -1]},
    ],
    constraints=["1 ≤ capacity ≤ 3000", "0 ≤ key ≤ 10⁴", "0 ≤ value ≤ 10⁵", "At most 2 · 10⁵ calls."],
    companies={"Amazon": 5, "Meta": 5, "Microsoft": 5, "Google": 4, "Bloomberg": 4, "Apple": 4, "Oracle": 3,
               "Uber": 3, "Salesforce": 3, "Snap": 2},
    topics=["Hash Table", "Linked List", "Design", "Doubly-Linked List"],
    hints=[
        "A hash map gives O(1) lookup, but how do you know which key is least recently used - in O(1)?",
        "You need an order you can update in O(1): move any element to the 'recent' end, remove from the 'old' end.",
        "Hash map key → node of a doubly linked list. Sentinel nodes at both ends remove every edge case.",
    ],
    insight={
        "pattern": "Hash map + doubly linked list",
        "oneLiner": "The map finds a node in O(1); the doubly linked list reorders it in O(1); the least recent node sits next to the left sentinel.",
        "mnemonic": "Map to find it, list to order it.",
        "why": "Each structure covers the other's weakness: the list can't search, the map can't keep order. Prev pointers let a node unlink itself.",
        "signals": ["\"O(1) get and put\" with eviction", "recency or frequency ordering", "caches"],
        "recall": [
            {"q": "Why doubly linked?", "a": "To remove an arbitrary node in O(1), you need its previous node."},
            {"q": "Why store the key in each node?", "a": "When evicting the LRU node you must also delete its map entry."},
        ],
    },
    solutions=[
        Solution("list-scan", "Map + list of keys", "O(n)", "O(n)", LIST_SCAN,
                 "Track recency in a Python list. Correct, but list.remove and pop(0) are O(n)."),
        Solution("dll", "Hash map + doubly linked list", "O(1)", "O(n)", DLL,
                 "A map from key to list node plus a recency-ordered doubly linked list with sentinels.", optimal=True),
    ],
    pitfalls=[
        Pitfall("get-not-recent", "get() didn't refresh recency",
                "A successful get counts as a use - move the key to the most-recent end.",
                detect=lambda a, e, x: isinstance(x, list) and x != e and "get" in a["ops"]),
        Pitfall("update-dup", "Updating a key created a duplicate entry",
                "When put() updates an existing key, remove its old node before inserting the new one.",
                detect=lambda a, e, x: isinstance(x, list) and x != e
                and len([k for o, (k, *_) in zip(a["ops"][1:], a["args"][1:]) if o == "put"])
                != len({k for o, (k, *_) in zip(a["ops"][1:], a["args"][1:]) if o == "put"})),
    ],
    edge_cases=[
        {"ops": ["LRUCache", "get"], "args": [[1], [1]]},
        {"ops": ["LRUCache", "put", "put", "get"], "args": [[1], [1, 1], [1, 2], [1]]},
        {"ops": ["LRUCache", "put", "put", "put", "get", "get"], "args": [[2], [1, 1], [2, 2], [1, 5], [1], [2]]},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"ops": ["LRUCache", "put", "put", "get", "put", "get"], "args": [[2], [1, 10], [2, 20], [1], [3, 30], [2]]},
    lens={"nodes": {"prev": True}, "hide": ["self.cap"]},
    related=["min-stack", "copy-list-with-random-pointer"],
)
