from feetcode.problem import Pitfall, Problem, Solution, sig

DIGITS = "123456789"


def _solved_grid(rng):
    """A random complete Sudoku: a pattern grid shuffled by validity-preserving moves."""
    def pattern(r, c):
        return (3 * (r % 3) + r // 3 + c) % 9

    bands = rng.sample(range(3), 3)
    rows = [b * 3 + r for b in bands for r in rng.sample(range(3), 3)]
    stacks = rng.sample(range(3), 3)
    cols = [s * 3 + c for s in stacks for c in rng.sample(range(3), 3)]
    digits = rng.sample(DIGITS, 9)
    return [[digits[pattern(r, c)] for c in cols] for r in rows]


def _valid(board):
    seen = set()
    for r in range(9):
        for c in range(9):
            d = board[r][c]
            if d == ".":
                continue
            keys = (("r", r, d), ("c", c, d), ("b", r // 3, c // 3, d))
            if any(k in seen for k in keys):
                return False
            seen.update(keys)
    return True


def generate(rng, n):
    grid = _solved_grid(rng)
    filled = min(81, 2 + n * 4 + rng.randint(0, 6))
    keep = set(rng.sample(range(81), filled))
    board = [[grid[r][c] if r * 9 + c in keep else "." for c in range(9)] for r in range(9)]
    if rng.random() < 0.55:
        # Plant one conflict: copy a digit into an empty cell of the same row, column or box.
        filled_cells = [(r, c) for r in range(9) for c in range(9) if board[r][c] != "."]
        if filled_cells:
            r, c = rng.choice(filled_cells)
            kind = rng.choice(("row", "col", "box"))
            if kind == "row":
                cells = [(r, cc) for cc in range(9)]
            elif kind == "col":
                cells = [(rr, c) for rr in range(9)]
            else:
                br, bc = r // 3 * 3, c // 3 * 3
                cells = [(br + i, bc + j) for i in range(3) for j in range(3)]
            empty = [(rr, cc) for rr, cc in cells if board[rr][cc] == "."]
            if empty:
                rr, cc = rng.choice(empty)
                board[rr][cc] = board[r][c]
    return {"board": board}


def validate(args):
    b = args["board"]
    return len(b) == 9 and all(len(row) == 9 and all(ch in DIGITS + "." for ch in row) for row in b)


def shrink(args):
    """Blank out one filled cell at a time - the board stays well-formed."""
    b = args["board"]
    for r in range(9):
        for c in range(9):
            if b[r][c] != ".":
                nb = [row[:] for row in b]
                nb[r][c] = "."
                yield {"board": nb}


THREE_PASSES = '''class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        for r in range(9):  #> Pass 1: check row {r}.
            seen = set()  #~
            for c in range(9):  #~
                d = board[r][c]  #~
                if d != ".":  #~
                    if d in seen:  #> {d} appears twice in row {r}. ||
                        return False  #~
                    seen.add(d)  #~
        for c in range(9):  #> Pass 2: check column {c}.
            seen = set()  #~
            for r in range(9):  #~
                d = board[r][c]  #~
                if d != ".":  #~
                    if d in seen:  #> {d} appears twice in column {c}. ||
                        return False  #~
                    seen.add(d)  #~
        for b in range(9):  #> Pass 3: check box {b}.
            seen = set()  #~
            for k in range(9):  #~
                d = board[b // 3 * 3 + k // 3][b % 3 * 3 + k % 3]  #~
                if d != ".":  #~
                    if d in seen:  #> {d} appears twice in box {b}. ||
                        return False  #~
                    seen.add(d)  #~
        return True  #> All 27 units passed.
'''

ONE_PASS = '''class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        rows = defaultdict(set)
        cols = defaultdict(set)
        boxes = defaultdict(set)  #> One set of seen digits per row, per column and per 3×3 box.
        for r in range(9):  #~
            for c in range(9):  #~
                d = board[r][c]  #~
                if d == ".":  #~
                    continue  #~
                box = (r // 3, c // 3)  #> Digit {d} at row {r}, column {c} belongs to box {box}. #! Integer division maps each cell to its box: rows 0-2 → 0, 3-5 → 1, 6-8 → 2. Using the tuple (r // 3, c // 3) keeps boxes like (0, 1) and (1, 0) apart.
                if d in rows[r] or d in cols[c] or d in boxes[box]:  #> {d} is already in row {r}, column {c} or box {box} - invalid! || {d} is new to its row, column and box.
                    return False  #> One conflict is enough to reject the board.
                rows[r].add(d)  #~
                cols[c].add(d)  #~
                boxes[box].add(d)  #~
        return True  #> Every filled cell was unique in its row, column and box.
'''

LESSON_BOARD = [
    ["5", "3", ".", ".", "7", ".", ".", ".", "."],
    ["6", ".", ".", "1", "9", "5", ".", ".", "."],
    [".", "9", "8", ".", ".", ".", ".", "6", "."],
    ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
    ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
    ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
    [".", "6", ".", ".", ".", ".", "2", "8", "."],
    [".", ".", ".", "4", "1", "9", ".", ".", "5"],
    [".", ".", ".", ".", "8", ".", ".", "7", "9"],
]
LESSON_BOARD[3][1] = "9"  # planted conflict: column 1 already has a 9 in row 2

PROBLEM = Problem(
    id="valid-sudoku",
    number=36,
    slug="valid-sudoku",
    title="Valid Sudoku",
    difficulty="Medium",
    pattern="arrays-hashing",
    order=8,
    signature=sig("isValidSudoku", "bool", board="List[List[str]]"),
    statement="""
You're given a partially filled 9 × 9 Sudoku `board`, where empty cells are `"."`. Decide whether the filled cells are **consistent** with the rules:

1. Each row contains each digit `1`–`9` at most once.
2. Each column contains each digit at most once.
3. Each of the nine 3 × 3 boxes contains each digit at most once.

The board does not need to be solvable - only check the cells that are filled in.
""",
    examples=[
        {"args": {"board": [row[:] for row in LESSON_BOARD]}, "output": False,
         "explain": "Column 1 holds a 9 twice (rows 2 and 3)."},
        {"args": {"board": [["5", "3", ".", ".", "7", ".", ".", ".", "."]] + [["."] * 9 for _ in range(8)]},
         "output": True},
    ],
    constraints=["board is 9 × 9", "board[i][j] is a digit 1-9 or '.'"],
    companies={"Amazon": 4, "Apple": 3, "Uber": 3, "Microsoft": 3, "Google": 2, "Bloomberg": 2, "Snap": 2},
    topics=["Array", "Hash Table", "Matrix"],
    hints=[
        "There are 27 units to check: 9 rows, 9 columns and 9 boxes. A set per unit detects repeats.",
        "Which box is cell (r, c) in? Try integer division by 3.",
        "One pass is enough: keep a set for every row, every column and every box at the same time.",
    ],
    insight={
        "pattern": "Sets keyed by unit",
        "oneLiner": "Give every row, column and box its own seen-set; cell (r, c) belongs to box (r // 3, c // 3).",
        "mnemonic": "Integer-divide to find the box.",
        "why": "Each filled cell is checked against exactly three sets in O(1), so one pass over 81 cells decides it.",
        "signals": ["grid constraints", "\"no repeats in each row/column/region\""],
        "recall": [
            {"q": "Which box does cell (4, 7) belong to?", "a": "(4 // 3, 7 // 3) = (1, 2)."},
            {"q": "Why does r // 3 + c // 3 make a bad box index?",
             "a": "It collides: (0, 1) and (1, 0) both give 1. Use a tuple or r // 3 * 3 + c // 3."},
        ],
    },
    solutions=[
        Solution("three-passes", "Check rows, then columns, then boxes", "O(81)", "O(9)", THREE_PASSES,
                 "Three separate scans, each with a fresh set per unit."),
        Solution("one-pass", "One pass with 27 sets", "O(81)", "O(81)", ONE_PASS,
                 "Check each cell against its row, column and box sets as you go.", optimal=True),
    ],
    pitfalls=[
        Pitfall("box-index", "Box index collides",
                "r // 3 + c // 3 maps different boxes to the same number. Use (r // 3, c // 3) or r // 3 * 3 + c // 3.",
                code=r"r\s*//\s*3\s*\+\s*c\s*//\s*3"),
        Pitfall("false-conflict", "Rejected a consistent board",
                "Common causes: treating '.' as a digit, a box index that merges two boxes, reusing one set "
                "across rows, or checking solvability - only the filled cells matter.",
                detect=lambda a, e, x: e is True and x is False),
    ],
    edge_cases=[{"board": [["."] * 9 for _ in range(9)]}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    sizes=[],
    size_of=lambda a: sum(ch != "." for row in a["board"] for ch in row),
    lesson={"board": [row[:] for row in LESSON_BOARD]},
    lens={"grids": ["board"]},
    related=["contains-duplicate"],
)
