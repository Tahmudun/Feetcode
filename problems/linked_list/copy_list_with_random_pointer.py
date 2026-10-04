from feetcode.problem import Pitfall, Problem, Solution, sig
from feetcode.structures import CallArgs, from_random_list, list_nodes, to_random_list


def generate(rng, n):
    vals = [rng.randint(-9, 9) for _ in range(n)]
    pairs = [[v, rng.randrange(n) if rng.random() < 0.7 else None] for v in vals]
    return {"head": pairs}


def validate(args):
    pairs = args["head"]
    return all(len(p) == 2 and (p[1] is None or 0 <= p[1] < len(pairs)) for p in pairs)


def shrink(args):
    pairs = args["head"]
    for i in range(len(pairs) - 1, -1, -1):
        rest = []
        for j, (v, r) in enumerate(pairs):
            if j == i:
                continue
            if r is None or r == i:
                rest.append([v, None])
            else:
                rest.append([v, r - 1 if r > i else r])
        yield {"head": rest}
    for i, (v, r) in enumerate(pairs):
        if r is not None:
            yield {"head": pairs[:i] + [[v, None]] + pairs[i + 1:]}


def worst_case(n):
    return {"head": [[i, (i * 7) % n if n else None] for i in range(n)]}


def prepare(args):
    head = to_random_list(args["head"])
    out = CallArgs([head])
    out.keep = list_nodes(head)                  # keep originals alive so ids can't be reused
    out.original = {id(node) for node in out.keep}
    return out


def extract(raw, call_args, args):
    copies = list_nodes(raw)
    if any(id(node) in call_args.original for node in copies):
        raise ValueError("returned the original nodes - every node in the copy must be new")
    for node in copies:
        r = getattr(node, "random", None)
        if r is not None and id(r) in call_args.original:
            raise ValueError("a copied node's random pointer points into the ORIGINAL list")
    return from_random_list(raw)


HASHMAP = '''class Solution:
    def copyRandomList(self, head: Optional[Node]) -> Optional[Node]:
        old_to_new = {None: None}  #> Maps each original node to its copy. None maps to None, so missing links need no special case.
        node = head
        while node:  #~
            old_to_new[node] = Node(node.val)  #> Pass 1: create a copy of node {node.val} (no links yet).
            node = node.next  #~
        node = head
        while node:  #~
            copy = old_to_new[node]  #~
            copy.next = old_to_new[node.next]  #~
            copy.random = old_to_new[node.random]  #> Pass 2: the copy of {node.val} gets next → {copy.next.val if copy.next else None} and random → {copy.random.val if copy.random else None}. #! The map translates every pointer - including random pointers that jump backwards or to nodes not yet visited. That's why all copies are created in a first pass.
            node = node.next  #~
        return old_to_new[head]  #> The copy's head. No node is shared with the original.
'''

INTERLEAVE = '''class Solution:
    def copyRandomList(self, head: Optional[Node]) -> Optional[Node]:
        if not head:
            return None
        node = head
        while node:  #~
            node.next = Node(node.val, node.next)  #> Weave a copy of {node.val} right after it.
            node = node.next.next  #~
        node = head
        while node:  #~
            if node.random:  #~
                node.next.random = node.random.next  #> The copy's random is the node right after the original's random target. #! Interleaving puts every copy at original.next, so "copy of X" is just X.next - the hash map is replaced by the list itself. O(1) extra space.
            node = node.next.next  #~
        node, copy_head = head, head.next
        while node:  #~
            copy = node.next  #~
            node.next = copy.next  #~
            copy.next = copy.next.next if copy.next else None  #> Unweave: restore the original and detach the copy.
            node = node.next  #~
        return copy_head
'''

PROBLEM = Problem(
    id="copy-list-with-random-pointer",
    number=138,
    slug="copy-list-with-random-pointer",
    title="Copy List with Random Pointer",
    difficulty="Medium",
    pattern="linked-list",
    order=6,
    signature=sig("copyRandomList", "Optional[Node]", head="Optional[Node]"),
    statement="""
Each node of a linked list has a `next` pointer and an extra `random` pointer that may point to **any node in the list, or `None`**.

Return a **deep copy**: a brand-new list of new nodes with the same values, where every copied `next` and `random` pointer points to the corresponding *copied* node. No pointer in the copy may point into the original list.

Input format: each node is `[val, random_index]`, where `random_index` is the position the random pointer targets (or `null`).
""",
    examples=[
        {"args": {"head": [[7, None], [13, 0], [11, 4], [10, 2], [1, 0]]},
         "output": [[7, None], [13, 0], [11, 4], [10, 2], [1, 0]]},
        {"args": {"head": [[3, 1], [5, 1]]}, "output": [[3, 1], [5, 1]], "explain": "A random pointer can point to its own node."},
        {"args": {"head": []}, "output": []},
    ],
    constraints=["0 ≤ number of nodes ≤ 1000", "−10⁴ ≤ Node.val ≤ 10⁴", "random is None or points to a node in the list"],
    companies={"Amazon": 5, "Meta": 4, "Microsoft": 4, "Bloomberg": 3, "Google": 2, "Apple": 2, "Oracle": 2},
    topics=["Hash Table", "Linked List"],
    hints=[
        "Copying next pointers is easy. The trouble is random: it may point to a node you haven't copied yet.",
        "First create every copy, then wire the pointers. How do you find the copy of a given original node?",
        "A hash map original → copy translates any pointer. (For O(1) space, weave each copy right after its original.)",
    ],
    insight={
        "pattern": "Old → new node map (two passes)",
        "oneLiner": "Pass 1 creates a copy of every node in a map; pass 2 sets copy.next = map[old.next] and copy.random = map[old.random].",
        "mnemonic": "Clone first, wire second.",
        "why": "Separating creation from wiring means every pointer target already has a copy when you need it.",
        "signals": ["deep copy of a graph-like structure", "pointers that can point anywhere"],
        "recall": [
            {"q": "Why put None in the map?", "a": "map[None] = None lets copy.next/random be set without special cases."},
            {"q": "How does the O(1)-space version find a node's copy?", "a": "It's woven in as original.next."},
        ],
    },
    solutions=[
        Solution("interleave", "Weave copies into the list", "O(n)", "O(1)", INTERLEAVE,
                 "Insert each copy after its original, set randoms via original.random.next, then separate the lists."),
        Solution("hashmap", "Hash map, two passes", "O(n)", "O(n)", HASHMAP,
                 "Map each original node to its copy, then translate every pointer through the map.", optimal=True),
    ],
    pitfalls=[
        Pitfall("shallow", "Returned original nodes",
                "Every node of the result must be newly created - no node may be shared with the input.",
                error="OutputError: original"),
        Pitfall("random-into-original", "Random pointers point into the original list",
                "Set copy.random to the COPY of node.random (map[node.random]), not node.random itself.",
                error="OutputError: ORIGINAL"),
    ],
    edge_cases=[{"head": []}, {"head": [[1, None]]}, {"head": [[1, 0]]}, {"head": [[1, 1], [2, 0]]}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    worst_case=worst_case,
    prepare=prepare,
    extract=extract,
    lesson={"head": [[7, None], [13, 0], [11, 3], [10, 1]]},
    lens={"nodes": {"random": True}},
    related=["lru-cache"],
)
