from feetcode.problem import Pitfall, Problem, Solution, sig

KEYS = ("tea", "mood", "sky")
VALUES = ("red", "blue", "calm", "busy", "a", "b", "c1", "zz")


def generate(rng, n):
    keys = KEYS[: rng.choice((1, 1, 2, 3))]
    ops, args, t = ["TimeMap"], [[]], 0
    for _ in range(max(1, n)):
        if t == 0 or rng.random() < 0.5:
            t += rng.choice((1, 1, 2, 5))
            ops.append("set")
            args.append([rng.choice(keys), rng.choice(VALUES), t])
        else:
            key = rng.choice(keys) if rng.random() < 0.9 else "owl"   # sometimes a key that was never set
            ops.append("get")
            args.append([key, rng.randint(1, t + 3)])
    return {"ops": ops, "args": args}


def validate(args):
    ops, argv = args["ops"], args["args"]
    if not ops or ops[0] != "TimeMap" or len(ops) != len(argv) or argv[0]:
        return False
    last = 0
    for op, a in zip(ops[1:], argv[1:]):
        if op == "set":
            if len(a) != 3 or not (isinstance(a[0], str) and a[0] and isinstance(a[1], str) and a[1]):
                return False
            if not isinstance(a[2], int) or a[2] <= last:   # set timestamps strictly increase
                return False
            last = a[2]
        elif op == "get":
            if len(a) != 2 or not isinstance(a[0], str) or not a[0] or not isinstance(a[1], int) or a[1] < 1:
                return False
        else:
            return False
    return True


def worst_case(n):
    # One long history, then lookups older than all but the first entry: the scan walks back through everything.
    half = max(1, n // 2)
    ops = ["TimeMap"] + ["set"] * half + ["get"] * half
    args = [[]] + [["k", f"v{t}", t] for t in range(1, half + 1)] + [["k", 1] for _ in range(half)]
    return {"ops": ops, "args": args}


SCAN = '''class TimeMap:
    def __init__(self):
        self.store = {}  # key -> [(timestamp, value), ...], oldest first

    def set(self, key: str, value: str, timestamp: int) -> None:
        self.store.setdefault(key, []).append((timestamp, value))  #> Append ({timestamp}, {value}) to {!key}'s history.

    def get(self, key: str, timestamp: int) -> str:
        pairs = self.store.get(key, [])  #> Look up {key} as of time {timestamp}. Its history: {pairs}.
        for i in range(len(pairs) - 1, -1, -1):  #~
            if pairs[i][0] <= timestamp:  #> Set at {pairs[i][0]} ≤ {timestamp}: this is the latest version. || Set at {pairs[i][0]}, after {timestamp}. Step back.
                return pairs[i][1]  #> {_return}, found by walking back one entry at a time.
        return ""  #> Nothing was set for {!key} at or before {timestamp}, so the answer is "".
'''

BINARY = '''class TimeMap:
    def __init__(self):
        self.store = {}  # key -> [(timestamp, value), ...], oldest first

    def set(self, key: str, value: str, timestamp: int) -> None:
        self.store.setdefault(key, []).append((timestamp, value))  #> Append ({timestamp}, {value}) to {!key}'s history. #! Timestamps only ever increase, so appending keeps every history sorted by time - for free. That's what makes binary search possible in get.

    def get(self, key: str, timestamp: int) -> str:
        pairs = self.store.get(key, [])  #> Look up {key} as of time {timestamp}. Its history holds {len(pairs)} version(s).
        answer = ""  #> The best version so far: none.
        lo, hi = 0, len(pairs) - 1  #~
        while lo <= hi:  #> Versions {lo}..{hi} are still undecided. || Every version is decided.
            mid = (lo + hi) // 2  #~
            if pairs[mid][0] <= timestamp:  #> Version {mid} was set at {pairs[mid][0]} ≤ {timestamp}: it's valid. A later valid one might exist, so look right. || Version {mid} was set at {pairs[mid][0]}, after {timestamp}: it and everything after it are too new. Look left. #! This is "last element ≤ timestamp". A version that fits isn't returned immediately - it's remembered, and the search keeps looking for a newer one that also fits.
                answer = pairs[mid][1]  #> Remember {answer}.
                lo = mid + 1  #~
            else:
                hi = mid - 1  #~
        return answer  #> The newest version at or before {timestamp}: {_return}.
'''

PROBLEM = Problem(
    id="time-based-key-value-store",
    number=981,
    slug="time-based-key-value-store",
    title="Time Based Key-Value Store",
    difficulty="Medium",
    pattern="binary-search",
    order=6,
    signature=sig("", "List", kind="design", cls="TimeMap"),
    statement="""
Build a key-value store that remembers **every version** of each key. Implement `TimeMap`:

- `TimeMap()` creates an empty store.
- `set(key, value, timestamp)` records that `key` had `value` at time `timestamp`.
- `get(key, timestamp)` returns the value `key` had at time `timestamp`: the value from the `set` with the **largest timestamp ≤ `timestamp`**. If `key` was never set at or before that time, return `""`.

Across all `set` calls, timestamps are strictly increasing.

The input is a list of operations and their arguments; the output lists each call's return value (`null` for none).
""",
    examples=[
        {"args": {"ops": ["TimeMap", "set", "set", "get", "get", "get"],
                  "args": [[], ["mood", "calm", 3], ["mood", "busy", 8], ["mood", 5], ["mood", 8], ["mood", 2]]},
         "output": [None, None, None, "calm", "busy", ""],
         "explain": "At time 5 the latest version is from time 3. At time 2 nothing had been set yet."},
        {"args": {"ops": ["TimeMap", "set", "get", "get"], "args": [[], ["x", "a", 10], ["y", 10], ["x", 99]]},
         "output": [None, None, "", "a"],
         "explain": "y was never set."},
    ],
    constraints=["1 ≤ key.length, value.length ≤ 100", "1 ≤ timestamp ≤ 10⁷",
                 "Timestamps of set calls are strictly increasing.", "At most 2 · 10⁵ calls."],
    companies={"Google": 3, "Amazon": 3, "Netflix": 3, "Uber": 3, "Lyft": 3, "Meta": 2, "Microsoft": 2,
               "Databricks": 2},
    topics=["Hash Table", "String", "Binary Search", "Design"],
    hints=[
        "Store each key's versions in a list of (timestamp, value). In what order do they arrive?",
        "Since set timestamps only increase, every key's list is already sorted by time.",
        "get is 'the last entry with timestamp ≤ t': binary-search, remembering the best fit as you go right.",
    ],
    insight={
        "pattern": "Binary search for the last fit",
        "oneLiner": "Appends arrive in time order, so each key's history is sorted; get binary-searches for the last timestamp ≤ t.",
        "mnemonic": "Keep the latest version that isn't from the future.",
        "why": "The 'set timestamps increase' rule means append keeps every history sorted with no extra work. Then "
               "'which versions are at or before t' is a prefix of the list, and binary search finds where it ends.",
        "signals": ["versioned or time-stamped lookups", "\"largest x ≤ query\"", "data that only arrives in sorted order"],
        "recall": [
            {"q": "Why doesn't set need to sort anything?",
             "a": "Timestamps strictly increase, so appending keeps each key's list sorted by time."},
            {"q": "In get, what do you do when pairs[mid].timestamp ≤ t?",
             "a": "Record pairs[mid] as the answer so far and search to the right for a newer one that still fits."},
            {"q": "What does get return for a key that was never set?",
             "a": "An empty string - handle the missing key instead of raising KeyError."},
        ],
    },
    solutions=[
        Solution("scan", "Walk back through the history", "O(n)", "O(n)", SCAN,
                 "Append on set; on get, walk each key's history from newest to oldest until a timestamp fits. "
                 "Fast for recent lookups, O(n) for old ones."),
        Solution("binary", "Binary-search the history", "O(log n)", "O(n)", BINARY,
                 "Append on set (it stays sorted by time). On get, binary-search for the last entry with "
                 "timestamp ≤ t, remembering the best fit so far.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("missing-key", "Crashed on a key that was never set",
                "get on an unknown key should return \"\", not raise. Use self.store.get(key, []).",
                error="KeyError"),
        Pitfall("exact-only", "Returned \"\" when an older version existed",
                "get(key, t) wants the newest version at or before t - not only one set exactly at t. When "
                "pairs[mid].timestamp ≤ t, remember it and keep searching right.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e)
                and any(ev not in ("", None) and xv == "" for ev, xv in zip(e, x))),
        Pitfall("wrong-version", "Returned the wrong version",
                "You returned a value, but not the newest one at or before the timestamp. Too new means you took a "
                "version from the future; too old means the search stopped before the last fit.",
                detect=lambda a, e, x: isinstance(x, list) and len(x) == len(e)
                and any(ev != xv and isinstance(xv, str) and xv != "" for ev, xv in zip(e, x))),
    ],
    edge_cases=[
        {"ops": ["TimeMap", "get"], "args": [[], ["tea", 1]]},
        {"ops": ["TimeMap", "set", "get"], "args": [[], ["tea", "red", 5], ["tea", 4]]},
        {"ops": ["TimeMap", "set", "get"], "args": [[], ["tea", "red", 5], ["tea", 5]]},
        {"ops": ["TimeMap", "set", "set", "get", "get"],
         "args": [[], ["tea", "red", 1], ["sky", "blue", 2], ["tea", 2], ["sky", 1]]},
        {"ops": ["TimeMap", "set", "set", "set", "get"],
         "args": [[], ["tea", "a", 1], ["tea", "b", 2], ["tea", "c1", 3], ["tea", 10000000]]},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"ops": ["TimeMap", "set", "set", "set", "set", "get", "get", "get"],
            "args": [[], ["tea", "green", 2], ["tea", "oolong", 4], ["tea", "matcha", 7], ["tea", "chai", 9],
                     ["tea", 8], ["tea", 1], ["cocoa", 5]]},
    lens={"arrays": {"pairs": {"pointers": ["lo", "mid", "hi", "i"], "window": ["lo", "hi"]}}},
    follow_up="If set timestamps could arrive out of order, what would set cost - and is there a structure that keeps both operations O(log n)?",
    related=["binary-search", "lru-cache"],
)
