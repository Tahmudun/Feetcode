from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    n = max(1, n)
    return {"heights": ints(rng, n, 0, rng.choice((3, 6, 10**4)))}


def validate(args):
    h = args["heights"]
    return len(h) >= 1 and all(0 <= x <= 10**4 for x in h)


def worst_case(n):
    return {"heights": [i + 1 for i in range(max(1, n))]}  # increasing: brute force's inner loop never stops early


BRUTE = '''class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        best = 0
        for i in range(len(heights)):  #> Rectangles whose left edge is bar {i}.
            low = heights[i]  #~
            for j in range(i, len(heights)):  #~
                low = min(low, heights[j])  #~
                best = max(best, low * (j - i + 1))  #~
        return best  #> Best over all {len(heights) * (len(heights) + 1) // 2} ranges: {_return}.
'''

STACK = '''class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        stack = []  # (start index, height), heights increasing upward  #> (start, height) pairs for bars whose rectangles can still extend right. Heights increase from bottom to top.
        best = 0
        for i, h in enumerate(heights):  #> Bar {i}, height {h}.
            start = i  #~
            while stack and stack[-1][1] > h:  #> The height-{stack[-1][1]} rectangle starting at {stack[-1][0]} can't extend past bar {i} (only {h} tall). It ends here: {stack[-1][1]} × ({i} − {stack[-1][0]}) = {stack[-1][1] * (i - stack[-1][0])}. || Nothing on the stack is taller than {h}. #! Popping a taller bar finalizes its rectangle (its right edge is i). The new, shorter bar inherits the popped start: its own rectangle can extend left over everything that was taller.
                idx, height = stack.pop()  #~
                best = max(best, height * (i - idx))  #> Best so far: {best}.
                start = idx  #> Bar {i} can reach back to index {start}.
            stack.append((start, h))  #> Stack: {stack}.
        for idx, height in stack:  #> End of input: the height-{height} rectangle from {idx} reaches the right edge: {height} × {len(heights) - idx} = {height * (len(heights) - idx)}.
            best = max(best, height * (len(heights) - idx))  #~
        return best  #> Largest rectangle: {_return}.
'''

PROBLEM = Problem(
    id="largest-rectangle-in-histogram",
    number=84,
    slug="largest-rectangle-in-histogram",
    title="Largest Rectangle in Histogram",
    difficulty="Hard",
    pattern="stack",
    order=7,
    signature=sig("largestRectangleArea", "int", heights="List[int]"),
    statement="""
`heights[i]` is the height of bar `i` in a histogram; every bar has width 1. Return the **area of the largest rectangle** that fits entirely inside the histogram.

A rectangle spanning bars `l..r` can be at most as tall as the shortest bar in that range.
""",
    examples=[
        {"args": {"heights": [2, 4, 3, 5, 1, 2]}, "output": 9, "explain": "Bars 1-3 (heights 4, 3, 5) at height 3: 3 × 3 = 9."},
        {"args": {"heights": [4, 4]}, "output": 8},
        {"args": {"heights": [6, 2, 5, 4, 5, 1, 6]}, "output": 12, "explain": "Bars 2-4 at height 4."},
    ],
    constraints=["1 ≤ heights.length ≤ 10⁵", "0 ≤ heights[i] ≤ 10⁴"],
    companies={"Amazon": 4, "Google": 4, "Meta": 3, "Microsoft": 3, "Bloomberg": 3, "Uber": 2, "Adobe": 2, "Citadel": 2},
    topics=["Array", "Stack", "Monotonic Stack"],
    hints=[
        "For a rectangle whose height is exactly heights[i], how far can it stretch left and right?",
        "It stretches until the first shorter bar on each side. Finding those for every i is a 'next smaller element' problem.",
        "Keep a stack of increasing heights. When a shorter bar arrives, pop taller bars - each popped bar's rectangle ends here.",
    ],
    insight={
        "pattern": "Monotonic stack (next smaller on both sides)",
        "oneLiner": "Every bar's best rectangle spans until the next shorter bar on each side; an increasing stack finds both edges as bars are popped.",
        "mnemonic": "A shorter bar closes every taller rectangle still open.",
        "why": "When bar i pops a taller bar, i is that bar's first shorter neighbour on the right, and its stored start is its left edge. "
               "Each bar is pushed and popped once: O(n).",
        "signals": ["max area under bars", "\"how far can each element extend\"", "maximal rectangle in a matrix (row by row)"],
        "recall": [
            {"q": "What does a pop compute?", "a": "The rectangle of the popped bar's height from its start up to (not including) i."},
            {"q": "Why does the new bar inherit the popped start?", "a": "Everything popped was taller, so the new bar's rectangle can extend left over them."},
        ],
    },
    solutions=[
        Solution("brute", "Every range, tracking its minimum", "O(n²)", "O(1)", BRUTE,
                 "For each left edge, extend right while maintaining the minimum height."),
        Solution("stack", "Monotonic stack", "O(n)", "O(n)", STACK,
                 "Keep bars in increasing height; popping a bar finalizes the widest rectangle of its height.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("leftover", "Forgot the bars left on the stack",
                "Bars still on the stack at the end extend all the way to the right edge - compute their rectangles too.",
                detect=lambda a, e, x: isinstance(x, int) and x < e),
        Pitfall("start", "Didn't extend the new bar's start",
                "After popping taller bars, the new bar's rectangle starts at the last popped start, not at i."),
    ],
    edge_cases=[{"heights": [0]}, {"heights": [5]}, {"heights": [2, 1, 2]}, {"heights": [1, 2, 3, 4, 5]},
                {"heights": [5, 4, 3, 2, 1]}, {"heights": [0, 9]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"heights": [2, 4, 3, 5, 1, 2]},
    lens={"arrays": {"heights": {"view": "bars", "pointers": ["i", "j"]}}, "overlay": "histogram"},
    related=["daily-temperatures", "trapping-rain-water"],
)
