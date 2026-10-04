from feetcode.problem import Pitfall, Problem, Solution, ints, sig


def generate(rng, n):
    n = max(1, n)
    return {"prices": ints(rng, n, 0, rng.choice((5, 20, 10**4)))}


def validate(args):
    p = args["prices"]
    return len(p) >= 1 and all(0 <= x <= 10**4 for x in p)


def worst_case(n):
    return {"prices": [(i * 31) % 97 for i in range(max(1, n))]}


BRUTE = '''class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        best = 0
        for buy in range(len(prices)):  #> Buy on day {buy} at {prices[buy]}; try selling on every later day.
            for sell in range(buy + 1, len(prices)):  #~
                best = max(best, prices[sell] - prices[buy])  #~
        return best  #> Best over all pairs of days: {_return}.
'''

WINDOW = '''class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        l, best = 0, 0  #> l is the buy day (the cheapest so far); r will scan forward as the sell day.
        for r in range(1, len(prices)):  #> Consider selling on day {r} at {prices[r]}.
            if prices[r] < prices[l]:  #> {prices[r]} is cheaper than our buy price {prices[l]}. Any future sale does better buying here, so move l to {r}. || Selling now earns {prices[r]} − {prices[l]} = {prices[r] - prices[l]}. #! Moving l to a new low never loses an answer: every later sale is better paired with the lower price. That's why one pass suffices.
                l = r  #~
            else:
                best = max(best, prices[r] - prices[l])  #> Best profit so far: {best}.
        return best  #> Maximum profit: {_return}.
'''

PROBLEM = Problem(
    id="best-time-to-buy-and-sell-stock",
    number=121,
    slug="best-time-to-buy-and-sell-stock",
    title="Best Time to Buy and Sell Stock",
    difficulty="Easy",
    pattern="sliding-window",
    order=1,
    signature=sig("maxProfit", "int", prices="List[int]"),
    statement="""
`prices[i]` is a stock's price on day `i`. You may **buy once** and later **sell once** (selling must happen on a later day than buying).

Return the maximum profit you can make. If no trade makes money, return `0`.
""",
    examples=[
        {"args": {"prices": [8, 3, 6, 1, 7, 5]}, "output": 6, "explain": "Buy at 1 (day 3), sell at 7 (day 4)."},
        {"args": {"prices": [9, 7, 4, 1]}, "output": 0, "explain": "Prices only fall - don't trade."},
        {"args": {"prices": [2, 4, 1]}, "output": 2},
    ],
    constraints=["1 ≤ prices.length ≤ 10⁵", "0 ≤ prices[i] ≤ 10⁴"],
    companies={"Amazon": 5, "Meta": 4, "Google": 4, "Microsoft": 4, "Bloomberg": 4, "Apple": 3, "Goldman Sachs": 3,
               "Uber": 2, "Adobe": 2},
    topics=["Array", "Dynamic Programming", "Sliding Window"],
    hints=[
        "For a fixed sell day, which buy day is best?",
        "The best buy day for selling on day r is the cheapest day before r. Can you track it as you go?",
        "One pass: keep the lowest price so far (l); at each day r, the candidate profit is prices[r] − prices[l].",
    ],
    insight={
        "pattern": "Running minimum (variable window)",
        "oneLiner": "Sweep once, remembering the cheapest buy so far; each day's best sale is price − cheapest-so-far.",
        "mnemonic": "Buy the dip you've already seen.",
        "why": "For any sell day the optimal buy is the minimum before it, so one running minimum covers all O(n²) pairs.",
        "signals": ["best pair (i < j) maximizing a difference", "\"buy before sell\"", "single transaction"],
        "recall": [
            {"q": "When does l move?", "a": "When today's price is below prices[l] - a new cheapest buy day."},
            {"q": "Why return 0 rather than a negative number?", "a": "You can always choose not to trade."},
        ],
    },
    solutions=[
        Solution("brute", "Try every buy/sell pair", "O(n²)", "O(1)", BRUTE,
                 "Check the profit of every (buy, sell) pair with buy < sell."),
        Solution("window", "Track the cheapest day", "O(n)", "O(1)", WINDOW,
                 "Keep l at the cheapest day so far; every new day is a candidate sale.", optimal=True),
    ],
    pitfalls=[
        Pitfall("sell-before-buy", "Sold before buying",
                "max(prices) − min(prices) ignores order - the minimum must come before the maximum.",
                detect=lambda a, e, x: isinstance(x, int) and x == max(a["prices"]) - min(a["prices"]) and x != e),
        Pitfall("negative", "Returned a loss",
                "If prices only fall, the answer is 0 (don't trade).",
                detect=lambda a, e, x: isinstance(x, int) and x < 0),
    ],
    edge_cases=[{"prices": [5]}, {"prices": [1, 2]}, {"prices": [2, 1]}, {"prices": [3, 3, 3]},
                {"prices": [7, 1, 5, 3, 6, 4]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"prices": [8, 3, 6, 1, 7, 5]},
    lens={"arrays": {"prices": {"view": "bars", "pointers": ["l", "r", "buy", "sell"]}}},
    related=["longest-substring-without-repeating-characters"],
)
