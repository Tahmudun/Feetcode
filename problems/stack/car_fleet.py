from feetcode.problem import Pitfall, Problem, Solution, sig


def generate(rng, n):
    n = max(1, n)
    target = rng.randint(n + 1, 3 * n + 12)
    position = rng.sample(range(target), n)
    speed = [rng.randint(1, rng.choice((2, 4, 10))) for _ in range(n)]
    return {"target": target, "position": position, "speed": speed}


def validate(args):
    t, p, s = args["target"], args["position"], args["speed"]
    return (len(p) == len(s) >= 1 and len(set(p)) == len(p) and all(0 <= x < t for x in p)
            and all(v >= 1 for v in s))


def shrink(args):
    p, s = args["position"], args["speed"]
    for i in range(len(p) - 1, -1, -1):
        if len(p) > 1:
            yield {**args, "position": p[:i] + p[i + 1:], "speed": s[:i] + s[i + 1:]}
    for i in range(len(s)):
        if s[i] > 1:
            yield {**args, "speed": s[:i] + [s[i] - 1] + s[i + 1:]}


def worst_case(n):
    n = max(1, n)
    return {"target": 2 * n + 1, "position": list(range(0, 2 * n, 2)), "speed": [1 + (i % 3) for i in range(n)]}


STACK = '''class Solution:
    def carFleet(self, target: int, position: List[int], speed: List[int]) -> int:
        cars = sorted(zip(position, speed), reverse=True)  #> Process cars from closest to the target to farthest: {cars}.
        stack = []  # arrival times of the fleets ahead  #> Arrival times of the fleets formed so far.
        for pos, spd in cars:  #> Car at {pos}, speed {spd}.
            time = (target - pos) / spd  #> Alone, it would reach {target} at time {time}.
            if not stack or time > stack[-1]:  #> It arrives later than the fleet ahead, so it never catches up: a new fleet. || The fleet ahead arrives at {stack[-1]}; this car would arrive by then, so it catches up and joins that fleet. #! A car can never pass the one in front. If it would arrive no later than the fleet ahead, it catches that fleet and is slowed to its speed - so it adds nothing new.
                stack.append(time)  #> Fleet arrival times: {stack}.
        return len(stack)  #> {_return} fleet(s) reach the target.
'''

SLOWEST = '''class Solution:
    def carFleet(self, target: int, position: List[int], speed: List[int]) -> int:
        cars = sorted(zip(position, speed), reverse=True)  #> Closest to the target first: {cars}.
        fleets, slowest = 0, 0.0  #> Only the latest fleet's arrival time matters.
        for pos, spd in cars:  #~
            time = (target - pos) / spd  #> Car at {pos} needs {time}.
            if time > slowest:  #> Slower than every fleet ahead - a new fleet. || It catches the fleet arriving at {slowest}.
                fleets += 1  #~
                slowest = time  #> Fleets: {fleets}.
        return fleets
'''

PROBLEM = Problem(
    id="car-fleet",
    number=853,
    slug="car-fleet",
    title="Car Fleet",
    difficulty="Medium",
    pattern="stack",
    order=6,
    signature=sig("carFleet", "int", target="int", position="List[int]", speed="List[int]"),
    statement="""
`n` cars drive along a one-lane road toward mile `target`. Car `i` starts at `position[i]` (all different) and drives at `speed[i]` miles per hour.

A car can't pass another. When a faster car catches a slower one, it slows down and they continue together as a **fleet** (a single car is also a fleet). A car that catches a fleet exactly at the target still counts as part of it.

Return the number of fleets that arrive at the target.
""",
    examples=[
        {"args": {"target": 10, "position": [6, 2, 0], "speed": [1, 2, 3]}, "output": 1,
         "explain": "Arrival times alone: 4, 4 and 3.33. Nobody can pass the car at 6, so all three arrive together."},
        {"args": {"target": 20, "position": [1, 9, 14], "speed": [3, 1, 2]}, "output": 2},
        {"args": {"target": 5, "position": [3], "speed": [4]}, "output": 1},
    ],
    constraints=["1 ≤ n ≤ 10⁵", "0 ≤ position[i] < target ≤ 10⁶", "positions are distinct", "1 ≤ speed[i] ≤ 10⁶"],
    companies={"Google": 4, "Amazon": 3, "Meta": 2, "Microsoft": 2, "Nvidia": 2, "Uber": 2},
    topics=["Array", "Stack", "Sorting", "Monotonic Stack"],
    hints=[
        "Each car's \"natural\" arrival time is (target − position) / speed. What happens when a car behind has a smaller time?",
        "Process cars from closest to the target to farthest. A car behind either catches the fleet ahead or doesn't.",
        "Sort by position descending. If a car's time ≤ the fleet ahead's time, it merges; otherwise it forms a new fleet.",
    ],
    insight={
        "pattern": "Sort, then stack of arrival times",
        "oneLiner": "Sort by position from the target backwards; a car merges if its time ≤ the fleet ahead's time, else it starts a new fleet.",
        "mnemonic": "Nobody passes - fast cars just join the slowpoke ahead.",
        "why": "Once sorted, only the fleet directly ahead can block a car, so a single comparison with the stack top decides.",
        "signals": ["objects moving in one lane", "merging when one catches another", "\"how many groups arrive\""],
        "recall": [
            {"q": "Why sort by position descending?", "a": "The car closest to the target is never blocked; each car behind can only be blocked by fleets ahead."},
            {"q": "Merge condition?", "a": "time ≤ arrival time of the fleet directly ahead."},
        ],
    },
    solutions=[
        Solution("slowest", "Sort + track the slowest fleet", "O(n log n)", "O(n)", SLOWEST,
                 "Same idea with just the latest fleet's time instead of a stack."),
        Solution("stack", "Sort + stack of fleet times", "O(n log n)", "O(n)", STACK,
                 "Sort cars by position (closest first); push a time only when it forms a new fleet.", optimal=True),
    ],
    pitfalls=[
        Pitfall("unsorted", "Processed cars in input order",
                "Fleets form by position on the road - sort cars by position (closest to the target first).",
                detect=lambda a, e, x: isinstance(x, int) and x != e and a["position"] != sorted(a["position"], reverse=True)),
        Pitfall("strict-merge", "Didn't merge cars that meet exactly at the target",
                "Use time > stack[-1] for a NEW fleet - an equal time means they arrive together.",
                detect=lambda a, e, x: isinstance(x, int) and x > e),
    ],
    edge_cases=[{"target": 10, "position": [3], "speed": [3]}, {"target": 12, "position": [10, 8, 0, 5, 3], "speed": [2, 4, 1, 1, 3]},
                {"target": 10, "position": [0, 4, 2], "speed": [2, 1, 3]}, {"target": 100, "position": [0, 2, 4], "speed": [4, 2, 1]}],
    generate=generate,
    validate=validate,
    shrink=shrink,
    worst_case=worst_case,
    lesson={"target": 12, "position": [10, 8, 0, 5, 3], "speed": [2, 4, 1, 1, 3]},
    lens={"stacks": ["stack"]},
    related=["daily-temperatures"],
)
