from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def _water(h):
    n = len(h)
    if n == 0:
        return 0
    left, right = [0] * n, [0] * n
    left[0], right[-1] = h[0], h[-1]
    for i in range(1, n):
        left[i] = max(left[i - 1], h[i])
    for i in range(n - 2, -1, -1):
        right[i] = max(right[i + 1], h[i])
    return sum(min(left[i], right[i]) - h[i] for i in range(n))


def generate(rng, n):
    n = max(1, n)
    top = rng.choice((3, 5, 9, 100))
    return {"height": ints(rng, n, 0, top)}


def validate(args):
    h = args["height"]
    return 1 <= len(h) and all(0 <= x <= 10**5 for x in h)


def worst_case(n):
    # A valley: tall walls at both ends, every inner column holds water.
    return {"height": [n] + [(i * 7) % 5 for i in range(max(0, n - 2))] + [n]}


BRUTE = '''class Solution:
    def trap(self, height: List[int]) -> int:
        water = 0
        for i in range(len(height)):  #> Column {i} has height {height[i]}.
            left = max(height[: i + 1])  #> Scan left: the tallest wall at or before {i} is {left}.
            right = max(height[i:])  #> Scan right: the tallest wall at or after {i} is {right}.
            water += min(left, right) - height[i]  #> Water here = min({left}, {right}) − {height[i]} = {min(left, right) - height[i]}. Total: {water}. Two full scans for every column is what makes this O(n²). #! The formula is the heart of every solution: water above a column is capped by the SHORTER of the tallest walls on its two sides.
        return water  #> Total water: {_return}.
'''

PREFIX_MAX = '''class Solution:
    def trap(self, height: List[int]) -> int:
        n = len(height)
        left = [0] * n
        right = [0] * n  #> Precompute the tallest wall to the left and to the right of every column, once.
        left[0] = height[0]
        for i in range(1, n):  #~
            left[i] = max(left[i - 1], height[i])  #> left[{i}] = tallest of height[0..{i}] = {left[i]}.
        right[n - 1] = height[n - 1]
        for i in range(n - 2, -1, -1):  #~
            right[i] = max(right[i + 1], height[i])  #> right[{i}] = tallest of height[{i}..end] = {right[i]}.
        water = 0
        for i in range(n):  #~
            water += min(left[i], right[i]) - height[i]  #> Column {i}: min({left[i]}, {right[i]}) − {height[i]} = {min(left[i], right[i]) - height[i]}. Total: {water}.
        return water  #> Total water: {_return}. O(n) time, but two extra arrays.
'''

TWO_POINTERS = '''class Solution:
    def trap(self, height: List[int]) -> int:
        l, r = 0, len(height) - 1  #> Two pointers start at the outer walls: l = {l}, r = {r}.
        max_l, max_r = height[l], height[r]  #> Tallest wall seen from the left: {max_l}. From the right: {max_r}.
        water = 0
        while l < r:  #~
            if max_l < max_r:  #> max_l = {max_l} < max_r = {max_r}, so the LEFT side is the bottleneck. Somewhere on the right there is a wall at least {max_r} tall, so the water just right of l is decided by max_l alone. || max_l = {max_l} ≥ max_r = {max_r}, so the RIGHT side is the bottleneck. There is a wall at least {max_l} tall on the left, so the water just left of r is decided by max_r alone. #! The whole trick. Water at i is min(tallest left, tallest right) − height[i]. We don't know both maxima for every column - but we only need the smaller one, and whichever side has the smaller max is already decided.
                l += 1  #~
                max_l = max(max_l, height[l])  #> Step l to {l} (height {height[l]}). max_l is now {max_l}.
                water += max_l - height[l]  #> Column {l} holds max_l − height[{l}] = {max_l} − {height[l]} = {max_l - height[l]}. Total: {water}.
            else:
                r -= 1  #~
                max_r = max(max_r, height[r])  #> Step r to {r} (height {height[r]}). max_r is now {max_r}.
                water += max_r - height[r]  #> Column {r} holds max_r − height[{r}] = {max_r} − {height[r]} = {max_r - height[r]}. Total: {water}.
        return water  #> The pointers met. Every column was decided exactly once: {_return} units of water, O(1) extra space.
'''

PROBLEM = Problem(
    id="trapping-rain-water",
    number=42,
    slug="trapping-rain-water",
    title="Trapping Rain Water",
    difficulty="Hard",
    pattern="two-pointers",
    order=5,
    signature=sig("trap", "int", height="List[int]"),
    statement="""
`height[i]` is the height of a bar of width 1 in an elevation map. After it rains, water settles between the bars.

Return the **total units of water** trapped.

A column can only hold water if there is something taller on *both* sides of it - water spills over the lower of the two.
""",
    examples=[
        {"args": {"height": [0, 2, 0, 3, 1, 0, 1, 4, 2, 1, 2, 1]}, "output": 10},
        {"args": {"height": [3, 0, 2, 0, 4]}, "output": 7,
         "explain": "Columns 1-3 sit under a water level of 3 (the shorter outer wall): 3 + 1 + 3 = 7."},
        {"args": {"height": [5, 1, 1, 4]}, "output": 6},
    ],
    constraints=["1 ≤ height.length ≤ 2 · 10⁴", "0 ≤ height[i] ≤ 10⁵"],
    companies={"Amazon": 5, "Google": 5, "Meta": 4, "Goldman Sachs": 4, "Bloomberg": 4, "Microsoft": 4,
               "Apple": 3, "Uber": 3, "Citadel": 3, "Adobe": 2},
    topics=["Array", "Two Pointers", "Dynamic Programming", "Stack", "Monotonic Stack"],
    hints=[
        "Forget the whole map - look at ONE column. How high can water stand above it?",
        "Water at i = min(tallest bar on the left, tallest bar on the right) − height[i]. Can you precompute those maxima?",
        "With pointers at both ends, compare max_l and max_r. The side with the smaller max is already decided - "
        "process that side and move inward.",
    ],
    insight={
        "pattern": "Two pointers, bottleneck side first",
        "oneLiner": "Water at i = min(maxLeft, maxRight) − h[i]. Move the pointer whose max is smaller: "
                    "that side's water level is already decided.",
        "mnemonic": "The shorter wall sets the waterline - so trust it and move it.",
        "why": "If max_l < max_r, the column right of l has max_l as its left max, and its right max is at least "
               "max_r > max_l. So min(...) = max_l, without ever knowing the true right max.",
        "signals": ["\"trapped\" between bars", "answer per index depends on max to the left AND right",
                    "O(1) space follow-up"],
        "recall": [
            {"q": "Write the per-column water formula.", "a": "min(max height left of i, max height right of i) − height[i]."},
            {"q": "Why is it safe to move the pointer with the smaller max?",
             "a": "The other side already has a wall at least as tall, so min() is determined by the smaller max."},
            {"q": "Brute → better → best?", "a": "Rescan per column O(n²) → prefix/suffix max arrays O(n)/O(n) → two pointers O(n)/O(1)."},
        ],
    },
    solutions=[
        Solution("brute", "Scan both sides for every column", "O(n²)", "O(1)", BRUTE,
                 "Apply the water formula directly, finding each column's left and right maximum by scanning."),
        Solution("prefix-max", "Prefix and suffix maxima", "O(n)", "O(n)", PREFIX_MAX,
                 "The scans repeat work. Precompute left[i] and right[i] in two sweeps, then apply the formula."),
        Solution("two-pointers", "Two pointers", "O(n)", "O(1)", TWO_POINTERS,
                 "You only ever need the smaller of the two maxima. Walk inward from both ends, always moving "
                 "the side whose max is smaller - its water is already determined.", optimal=True),
    ],
    pitfalls=[
        Pitfall("one-side", "Used only one side's maximum",
                "Water is capped by BOTH sides: min(max_left, max_right). Using one max overfills columns near the lower wall.",
                detect=lambda a, e, x: isinstance(x, int) and x > e),
        Pitfall("undercount", "Counted too little water",
                "Usual causes: subtracting before updating the running max (a taller bar adds negative water), "
                "moving the pointer with the LARGER max, or stopping one column early.",
                detect=lambda a, e, x: isinstance(x, int) and x < e),
    ],
    edge_cases=[{"height": [0]}, {"height": [5, 0, 5]}, {"height": [1, 2, 3, 4]}, {"height": [4, 3, 2, 1]},
                {"height": [2, 0, 2, 0, 2]}, {"height": [0, 0, 0]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"height": [0, 2, 0, 3, 1, 0, 1, 4, 2, 1, 2, 1]},
    lens={"arrays": {"height": {"view": "bars", "pointers": ["l", "r", "i"]}}, "overlay": "water"},
    related=["container-with-most-water", "product-of-array-except-self", "largest-rectangle-in-histogram"],
)
