from feetcode.problem import Pitfall, Problem, Solution, sig

ALPHABET = "ab#;,/: 7\\"


def generate(rng, n):
    strs = []
    for _ in range(n):
        size = rng.choice((0, 1, 2, 3, 10))
        strs.append("".join(rng.choice(ALPHABET) for _ in range(size)))
    return {"strs": strs}


def validate(args):
    return all(isinstance(s, str) and all(32 <= ord(c) < 127 for c in s) for s in args["strs"])


def worst_case(n):
    return {"strs": ["a#b;" * 2 for _ in range(n)]}


ESCAPE = r'''class Solution:
    def encode(self, strs: List[str]) -> str:
        out = []
        for s in strs:  #~
            escaped = s.replace("\\", "\\\\").replace(";", "\\;")  #> Escape backslashes and semicolons in {s}: {escaped}.
            out.append(escaped + ";")  #> Terminate it with an unescaped ';'.
        return "".join(out)  #> Encoded: {_return}.

    def decode(self, s: str) -> List[str]:
        res, cur, i = [], [], 0  #> Read {s} one character at a time.
        while i < len(s):  #~
            if s[i] == "\\":  #> Backslash: the next character is literal. || {s[i]} is not an escape.
                cur.append(s[i + 1])  #~
                i += 2  #~
            elif s[i] == ";":  #> An unescaped ';' ends a string. || {s[i]} is ordinary text.
                res.append("".join(cur))  #> Finished a string: {res[-1]}.
                cur = []  #~
                i += 1  #~
            else:
                cur.append(s[i])  #~
                i += 1  #~
        return res  #> Decoded: {_return}.
'''

LENGTH_PREFIX = '''class Solution:
    def encode(self, strs: List[str]) -> str:
        out = []  #> Each string becomes <length>#<string>.
        for s in strs:  #~
            out.append(str(len(s)) + "#" + s)  #> {s} -> {out[-1]}
        return "".join(out)  #> Encoded: {_return}. #! The length tells the decoder exactly how far to read, so the string may contain '#', digits, anything - nothing is ever ambiguous.

    def decode(self, s: str) -> List[str]:
        res, i = [], 0  #> Decode {s}.
        while i < len(s):  #~
            j = i  #~
            while s[j] != "#":  #~
                j += 1  #~
            length = int(s[i:j])  #> Read the length header {s[i:j]}: the next {length} characters are one string.
            res.append(s[j + 1 : j + 1 + length])  #> Copy {res[-1]} and jump past it - its contents are never scanned for '#'.
            i = j + 1 + length  #~
        return res  #> Decoded: {_return}.
'''

PROBLEM = Problem(
    id="encode-and-decode-strings",
    number=271,
    slug="encode-and-decode-strings",
    title="Encode and Decode Strings",
    difficulty="Medium",
    pattern="arrays-hashing",
    order=6,
    signature=sig("encode", "List[str]", kind="codec", strs="List[str]"),
    statement="""
Design a pair of functions that pack a **list of strings into one string** and unpack it again.

- `encode(strs)` returns a single string.
- `decode(s)` receives that string and must return the original list exactly.

Strings can contain **any** printable character, including whatever separator you'd like to use - and they may be empty. The judge checks `decode(encode(strs)) == strs`.
""",
    examples=[
        {"args": {"strs": ["feet", "code", "rocks"]}, "output": ["feet", "code", "rocks"]},
        {"args": {"strs": ["a#b", "", "#"]}, "output": ["a#b", "", "#"],
         "explain": "Strings may contain '#' and may be empty - the encoding must still be unambiguous."},
        {"args": {"strs": []}, "output": []},
    ],
    constraints=["0 ≤ strs.length ≤ 200", "0 ≤ strs[i].length ≤ 200", "strs[i] contains printable ASCII."],
    companies={"Google": 4, "Meta": 3, "Amazon": 3, "Microsoft": 2, "LinkedIn": 2, "Uber": 2},
    topics=["Array", "String", "Design"],
    hints=[
        "Any single separator can appear *inside* a string. What extra information would make the boundaries unambiguous?",
        "Either escape the separator, or tell the decoder up front how long each string is.",
        "Length prefix: write len(s) + '#' + s. The decoder reads digits up to '#', then copies exactly that many characters.",
    ],
    insight={
        "pattern": "Length-prefixed framing",
        "oneLiner": "Prefix every string with its length and a delimiter; the decoder jumps over the payload instead of scanning it.",
        "mnemonic": "Say how long, then say it.",
        "why": "The delimiter only needs to be unambiguous inside the header, which is digits - the payload is never interpreted.",
        "signals": ["serialize / deserialize", "\"the strings may contain any character\""],
        "recall": [
            {"q": "Why does a plain separator like ',' fail?",
             "a": "A string containing ',' splits into extra pieces when decoding."},
            {"q": "How do network protocols solve the same problem?",
             "a": "Length-prefixed frames (or escaping), exactly as here."},
        ],
    },
    solutions=[
        Solution("escape", "Escape the delimiter", "O(n)", "O(n)", ESCAPE,
                 "Terminate each string with ';' and escape any ';' or backslash inside it, so the decoder can tell them apart."),
        Solution("length-prefix", "Length prefix", "O(n)", "O(n)", LENGTH_PREFIX,
                 "Write each string as <length>#<string>. Decoding reads the length, then slices exactly that many characters.",
                 optimal=True),
    ],
    pitfalls=[
        Pitfall("delimiter-collision", "A string contained your delimiter",
                "Splitting on a separator breaks as soon as a string contains it. Encode lengths, or escape.",
                detect=lambda a, e, x: e != x and any(c in s for s in e for c in "#;,/:\\ 7")),
        Pitfall("empty-cases", "Lost empty strings or the empty list",
                "''.split(',') returns [''], not []. Make sure [] and [''] round-trip differently.",
                detect=lambda a, e, x: e != x and (e == [] or "" in e)),
    ],
    edge_cases=[{"strs": []}, {"strs": [""]}, {"strs": ["", ""]}, {"strs": ["#"]}, {"strs": ["3#abc"]},
                {"strs": ["12", "#3"]}],
    generate=generate,
    validate=validate,
    worst_case=worst_case,
    lesson={"strs": ["fee", "#7", "", "code"]},
    related=["group-anagrams"],
)
