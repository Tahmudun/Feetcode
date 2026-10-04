from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    n = max(2, n)
    return {"height": ints(rng, n, 0, rng.choice((4, 10, 10**4)))}


def validate(args):
    h = args["height"]
    return len(h) >= 2 and all(0 <= x <= 10**4 for x in h)


def worst_case(n):
    return {"height": [(i * 37) % 101 for i in range(max(2, n))]}


BRUTE = '''class Solution:
    def maxArea(self, height: List[int]) -> int:
        best = 0
        for i in range(len(height)):  #> Left wall at {i} (height {height[i]}): try every right wall.
            for j in range(i + 1, len(height)):  #~
                best = max(best, (j - i) * min(height[i], height[j]))  #~
        return best  #> Best of all {len(height) * (len(height) - 1) // 2} pairs: {_return}.
'''

TWO_POINTERS = '''class Solution:
    def maxArea(self, height: List[int]) -> int:
        l, r = 0, len(height) - 1  #> Start with the widest possible container: walls {l} and {r}.
        best = 0
        while l < r:  #~
            area = (r - l) * min(height[l], height[r])  #> Width {r - l} × height min({height[l]}, {height[r]}) = {area}.
            best = max(best, area)  #> Best so far: {best}.
            if height[l] < height[r]:  #> The left wall ({height[l]}) is the shorter one. Any narrower container that keeps it is still capped at {height[l]} - none can beat {area}. Discard it: move l. || The right wall ({height[r]}) is not taller than the left ({height[l]}). Every narrower container keeping it is capped at {height[r]} - discard it: move r. #! Moving the taller wall can never help: the width shrinks and the height is still capped by the same shorter wall. Moving the shorter wall is the only move that might find a taller partner.
                l += 1  #~
            else:
                r -= 1  #~
        return best  #> The pointers met. Best area: {_return}.
'''

PROBLEM = Problem(
    id="container-with-most-water",
    number=11,
    slug="container-with-most-water",
    title="Container With Most Water",
    difficulty="Medium",
    pattern="two-pointers",
    order=4,
    signature=sig("maxArea", "int", height="List[int]"),
    statement="""
`height[i]` is the height of a vertical line at position `i`. Choose **two lines** that, together with the x-axis, form a container.

Return the **largest amount of water** a container can hold. The water level is limited by the shorter of the two lines, and the container's width is the distance between them. (The container can't be tilted.)
""",
    examples=[
        {"args": {"height": [2, 7, 3, 8, 4, 6, 1]}, "output": 24,
         "explain": "Lines at 1 and 5: width 4 × height min(7, 6) = 24."},
        {"args": {"height": [1, 1]}, "output": 1},
        {"args": {"height": [4, 3, 2, 1, 4]}, "output": 16, "explain": "The two outer lines: width 4 × height 4."},
    ],
    constraints=["2 ≤ height.length ≤ 10⁵", "0 ≤ height[i] ≤ 10⁴"],
    companies={"Amazon": 5, "Google": 4, "Meta": 4, "Microsoft": 4, "Bloomberg": 3, "Apple": 3, "Adobe": 3,
               "Goldman Sachs": 2, "Uber": 2},
    topics=["Array", "Two Pointers", "Greedy"],
    hints=[
        "Area = width × min(left height, right height). Trying all pairs is O(n²).",
        "Start with the widest container. To possibly do better with a narrower one, which wall must change?",
        "Always move the pointer at the shorter line - keeping it can never beat the current area.",
    ],
    insight={
        "pattern": "Two pointers, discard the limiting side",
        "oneLiner": "Start wide; the shorter wall limits every narrower container that keeps it, so move the shorter wall inward.",
        "mnemonic": "The short wall has nothing left to offer - drop it.",
        "why": "Each move eliminates every remaining pair involving the discarded wall, all of which are provably no better. "
               "So n − 1 moves cover all O(n²) pairs.",
        "signals": ["maximize area/score over pairs (i, j)", "value depends on min of the two ends × distance"],
        "recall": [
            {"q": "Which pointer moves, and why?",
             "a": "The shorter one: any narrower container keeping it is capped by it and narrower, so it can't win."},
            {"q": "How is this different from Trapping Rain Water?",
             "a": "Here only the two chosen walls matter (bars in between are ignored); in Trapping Rain Water every bar holds water."},
        ],
    },
    solutions=[
        Solution("brute", "Try every pair", "O(n²)", "O(1)", BRUTE,
                 "Compute the area for all pairs of walls and keep the maximum."),
        Solution("two-pointers", "Two pointers from the outside in", "O(n)", "O(1)", TWO_POINTERS,
                 "Start with the widest container and repeatedly discard the shorter wall.", optimal=True),
    ],
    pitfalls=[
        Pitfall("taller-wall", "Moved the taller wall",
                "Moving the taller wall can only shrink the area. Move the shorter one.",
                detect=lambda a, e, x: isinstance(x, int) and x < e),
        Pitfall("max-height", "Used the taller wall as the water level",
                "Water spills over the shorter line: area = width × min(h[l], h[r]).",
                detect=lambda a, e, x: isinstance(x, int) and x > e),
    ],
    edge_cases=[{"height": [0, 0]}, {"height": [1, 2]}, {"height": [1, 8, 6, 2, 5, 4, 8, 3, 7]}, {"height": [5, 5, 5, 5]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"height": [3, 9, 2, 8, 6, 1]},
    lens={"arrays": {"height": {"view": "bars", "pointers": ["l", "r", "i", "j"]}}, "overlay": "container"},
    related=["trapping-rain-water", "two-sum-ii-input-array-is-sorted"],
)
