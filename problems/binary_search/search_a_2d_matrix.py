from feetcode.problem import Pitfall, Problem, Solution, sig


def _flat(matrix):
    return [x for row in matrix for x in row]


def generate(rng, n):
    total = max(1, n)
    rows = rng.randint(1, max(1, round(total ** 0.5) + 1))
    cols = max(1, total // rows)
    step = rng.choice((1, 2, 7))
    x, matrix = rng.randint(-30, 30), []
    for _ in range(rows):
        row = []
        for c in range(cols):
            # repeats are allowed inside a row; a new row always starts above the previous row's end
            x += rng.randint(1 if c == 0 and matrix else 0, step)
            row.append(x)
        matrix.append(row)
    flat = _flat(matrix)
    target = rng.choice(flat) if rng.random() < 0.5 else rng.randint(flat[0] - 2, flat[-1] + 2)
    return {"matrix": matrix, "target": target}


def validate(args):
    m = args["matrix"]
    if not m or not m[0] or any(len(row) != len(m[0]) for row in m):
        return False
    if any(a > b for row in m for a, b in zip(row, row[1:])):
        return False
    return all(prev[-1] < row[0] for prev, row in zip(m, m[1:]))


def worst_case(n):
    # rows × cols = n (powers of two split evenly); the target is past the last cell, so the scan reads everything.
    n = max(1, n)
    rows = 1 << (n.bit_length() - 1) // 2
    cols = max(1, n // rows)
    matrix = [[(r * cols + c) * 3 for c in range(cols)] for r in range(rows)]
    return {"matrix": matrix, "target": matrix[-1][-1] + 1}


SCAN = '''class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        for row in matrix:  #> Next row: {row}.
            for value in row:  #~
                if value == target:  #> Found {target}. || {value} isn't {target}. #~
                    return True  #> Found after reading cell by cell: {_return}.
        return False  #> Read every one of the {len(matrix) * len(matrix[0])} cells: {target} isn't there. The ordering was never used.
'''

FLAT = '''class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        rows, cols = len(matrix), len(matrix[0])  #> A {rows} × {cols} matrix. Read row by row, it's one sorted list of {rows * cols} values. #! The two ordering rules (rows sorted, each row starting above the previous row's end) say exactly one thing: the matrix is a sorted list folded into rows. So search it like one.
        lo, hi = 0, rows * cols - 1  #> Search flat positions {lo}..{hi}.
        while lo <= hi:  #> Positions {lo}..{hi} are still possible. || No positions left.
            mid = (lo + hi) // 2  #~
            value = matrix[mid // cols][mid % cols]  #> Flat position {mid} is row {mid // cols}, column {mid % cols}: {value}. #! Unfolding a flat index: divide by the number of columns (not rows) for the row, take the remainder for the column.
            if value == target:  #> That's {target}. ||
                return True  #> Found: {_return}.
            if value < target:  #> {value} < {target}: drop position {mid} and everything before it. || {value} > {target}: drop position {mid} and everything after it.
                lo = mid + 1  #~
            else:
                hi = mid - 1  #~
        return False  #> The range is empty - {target} isn't in the matrix.
'''

TWO_SEARCHES = '''class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        top, bottom = 0, len(matrix) - 1  #> First, find the one row that could hold {target}.
        while top <= bottom:  #~
            r = (top + bottom) // 2  #~
            if target < matrix[r][0]:  #> {target} is below row {r}'s first value {matrix[r][0]}: look higher up. ||
                bottom = r - 1  #~
            elif target > matrix[r][-1]:  #> {target} is above row {r}'s last value {matrix[r][-1]}: look further down. ||
                top = r + 1  #~
            else:
                break  #> Row {r} spans {matrix[r][0]}..{matrix[r][-1]}, so {target} can only be here.
        else:
            return False  #> No row's range contains {target}.
        row = matrix[r]  #~
        lo, hi = 0, len(row) - 1  #> Now an ordinary binary search inside row {r}: {row}.
        while lo <= hi:  #~
            mid = (lo + hi) // 2  #~
            if row[mid] == target:  #> Found {target} at column {mid}. ||
                return True  #> Found: {_return}.
            if row[mid] < target:  #> {row[mid]} < {target}: go right. || {row[mid]} > {target}: go left.
                lo = mid + 1  #~
            else:
                hi = mid - 1  #~
        return False  #> The row could have held {target}, but it doesn't.
'''

PROBLEM = Problem(
    id="search-a-2d-matrix",
    number=74,
    slug="search-a-2d-matrix",
    title="Search a 2D Matrix",
    difficulty="Medium",
    pattern="binary-search",
    order=2,
    signature=sig("searchMatrix", "bool", matrix="List[List[int]]", target="int"),
    statement="""
You're given an `m × n` integer matrix with two ordering rules:

- each row is sorted in non-decreasing order, and
- each row's first value is larger than the previous row's last value.

Return `true` if `target` appears anywhere in the matrix, and `false` otherwise. Aim for **O(log(m · n))** time.
""",
    examples=[
        {"args": {"matrix": [[2, 5, 8], [11, 14, 17], [21, 24, 30]], "target": 14}, "output": True,
         "explain": "14 sits in the middle row."},
        {"args": {"matrix": [[2, 5, 8], [11, 14, 17], [21, 24, 30]], "target": 9}, "output": False,
         "explain": "9 would fall between the first row's 8 and the second row's 11."},
        {"args": {"matrix": [[4]], "target": 4}, "output": True},
    ],
    constraints=["1 ≤ m, n ≤ 100", "−10⁴ ≤ matrix[i][j], target ≤ 10⁴"],
    companies={"Amazon": 4, "Microsoft": 3, "Google": 3, "Meta": 3, "Bloomberg": 3, "Apple": 2, "Adobe": 2},
    topics=["Array", "Binary Search", "Matrix"],
    hints=[
        "Read the matrix left to right, top to bottom. What do the two rules say about that sequence?",
        "It's one sorted list of m · n values folded into rows. You can binary-search positions 0..m·n − 1 directly.",
        "Position k lives at row k // n, column k % n, where n is the number of columns.",
    ],
    insight={
        "pattern": "Binary search on a virtual array",
        "oneLiner": "The matrix is a sorted list folded into rows; binary-search flat positions and unfold each probe with divmod.",
        "mnemonic": "Unfold the page, search the line, fold it back.",
        "why": "Both rules together make the row-major order sorted. Binary search only needs a way to read the k-th "
               "value, and matrix[k // cols][k % cols] gives that in O(1) - no copying needed.",
        "signals": ["sorted rows that continue each other", "a 2-D layout of 1-D sorted data", "O(log(m·n)) required"],
        "recall": [
            {"q": "How do you turn flat index k into a cell?",
             "a": "row = k // cols, col = k % cols - divide by the number of columns."},
            {"q": "What makes the matrix searchable as one array?",
             "a": "Each row is sorted and starts above the previous row's end, so row-major order is sorted."},
        ],
    },
    solutions=[
        Solution("scan", "Scan every cell", "O(m · n)", "O(1)", SCAN,
                 "Read every cell until you find target. Correct, but it ignores both ordering rules."),
        Solution("two-searches", "Find the row, then the column", "O(log m + log n)", "O(1)", TWO_SEARCHES,
                 "Binary-search the rows by their first and last values to find the only row that could hold target, "
                 "then binary-search inside it."),
        Solution("flat", "One binary search over the flattened matrix", "O(log(m · n))", "O(1)", FLAT,
                 "Treat positions 0..m·n − 1 as one sorted array and map each probe back to a cell with divmod. "
                 "One loop, no row-finding phase.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("divided-by-rows", "Unfolded the flat index with the wrong width",
                "Position k is at row k // cols and column k % cols. Dividing by the number of *rows* only works for "
                "square matrices, and an off-by-one hi (m · n instead of m · n − 1) reads past the last cell.",
                error="IndexError: list index"),
        Pitfall("missed-present", "Said false for a value that's in the matrix",
                "The target is there. If you search rows first, make sure you pick the row whose range contains target "
                "(first ≤ target ≤ last), and use an inclusive loop: while lo <= hi.",
                detect=lambda a, e, x: e is True and x is False),
    ],
    edge_cases=[
        {"matrix": [[1]], "target": 1},
        {"matrix": [[1]], "target": 2},
        {"matrix": [[1, 3, 5, 7]], "target": 7},
        {"matrix": [[1], [3], [5]], "target": 3},
        {"matrix": [[1], [3], [5]], "target": 4},
        {"matrix": [[1, 2], [3, 4], [5, 6]], "target": 6},
        {"matrix": [[2, 2, 2], [5, 5, 9]], "target": 9},
    ],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    big=20000,  # the O(n) scan has to run out of operations, as the O(log n) requirement says
    size_of=lambda a: len(a["matrix"]) * len(a["matrix"][0]),
    lesson={"matrix": [[1, 4, 6, 9], [12, 15, 18, 21], [25, 30, 33, 40]], "target": 18},
    lens={"grids": ["matrix"], "arrays": {"row": {"pointers": ["lo", "mid", "hi"], "window": ["lo", "hi"]}}},
    follow_up="If rows didn't continue each other (each row and each column sorted on its own), what would you do instead?",
    related=["binary-search", "search-in-rotated-sorted-array"],
)
