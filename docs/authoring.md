# Authoring a problem

A problem is one Python module in `problems/<pattern>/`. Everything the site shows (statement, hidden tests, lessons, growth curves, pitfalls) is computed from it by the pipeline. Nothing is hand-written JSON. The reasons are in [ADR 0004](adr/0004-content-as-code.md).

The fastest way to start is to copy a similar problem. [`problems/arrays_hashing/two_sum.py`](../problems/arrays_hashing/two_sum.py) is a good template for function problems, [`stack/min_stack.py`](../problems/stack/min_stack.py) for design problems and [`linked_list/reorder_list.py`](../problems/linked_list/reorder_list.py) for in-place linked-list problems.

## 1. The module

```python
from feetcode.problem import Pitfall, Problem, Solution, ints, sig

def generate(rng, n):            # random valid input of size ~n (used by the suite, fuzzer, profiler)
    ...
    return {"nums": nums, "target": target}

def validate(args):              # is this a legal input? The shrinker never leaves this set.
    ...

def worst_case(n):               # optional: the input that makes slow solutions slowest
    ...

BRUTE = '''class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        ...
'''

PROBLEM = Problem(
    id="two-sum", number=1, slug="two-sum", title="Two Sum",
    difficulty="Easy", pattern="arrays-hashing", order=3,
    signature=sig("twoSum", "List[int]", nums="List[int]", target="int"),
    statement="""...markdown...""",
    examples=[{"args": {...}, "output": [...], "explain": "..."}],
    solutions=[Solution("brute", "Check every pair", "O(n²)", "O(1)", BRUTE, "idea..."),
               Solution("hashmap", "One-pass hash map", "O(n)", "O(n)", HASHMAP, "idea...", optimal=True)],
    generate=generate, validate=validate, worst_case=worst_case,
    compare="unordered",
    ...
)
```

### Fields

| Field | Notes |
| --- | --- |
| `id`, `slug`, `number`, `title`, `difficulty`, `pattern`, `order` | `pattern` is a pattern id from `problems/_patterns.py`. `order` sets the position within the pattern (roadmap order). |
| `signature` | `sig(method, returns, **params)`. Use `kind="design"` for class-based problems (`cls="MinStack"`), where inputs are `{"ops": [...], "args": [...]}`. Use `kind="codec"` for encode/decode pairs. `inplace="head"` marks a function whose answer is the mutated argument. Types like `ListNode` / `Optional[ListNode]` are converted to and from Python lists automatically. |
| `statement` | Markdown. **Write it yourself.** Don't copy a statement from another site. |
| `examples` | Shown to the user and checked by the gate against every solution. |
| `constraints`, `hints`, `topics`, `follow_up`, `related` | Display only. `related` holds problem ids. |
| `companies` | `{"Amazon": 5, ...}`: a 1–5 frequency estimate. These are curated, so keep them honest. |
| `insight` | `pattern`, `oneLiner`, `mnemonic`, `why`, `signals`, and `recall` (Q/A pairs that become spaced-repetition prompts). |
| `solutions` | Brute force first, optimal last. Exactly one is `optimal=True`. Its outputs are the expected answers, and its op counts set the budgets. |
| `generate(rng, n)` | Must return a **valid** input. Bias it toward bug-finding: duplicates, negatives, small alphabets (`small_alphabet`), all-equal runs. |
| `validate(args)` | Rejects illegal inputs: the gate checks every example and edge case, the fuzzer skips invalid generated inputs, and the shrinker keeps only valid candidates. |
| `worst_case(n)` | Optional. Used by the profiler, so brute force is measured at its worst rather than on lucky random data. |
| `edge_cases` | Inputs always in the hidden suite (empty, single element, all equal, extremes). |
| `compare` | `"exact"`, `"unordered"`, `"unordered_nested"`, `"float"`, or `callable(args, expected, actual) -> bool` when several answers are valid. |
| `pitfalls` | See below. |
| `lens` | See below. |
| `lesson` | The input used for the lessons. Pick one small enough to watch and big enough to show the trick. |
| `sizes`, `big`, `size_of`, `shrink`, `prepare`, `extract` | Advanced: profiler sizes, the "large" suite size, how to measure n, a custom shrinker, and hooks for inputs that need building (a cycle at `pos`) or outputs that need checking (a deep copy that shares no nodes). |

## 2. Narrating a solution

Reference solutions narrate themselves with comment directives. The engine evaluates `{expressions}` in the live frame after the line runs.

```python
for i, num in enumerate(nums):  #> Look at nums[{i}] = {num}.
    need = target - num         #> We need its complement: {need}. #! The whole trick: one O(1) question per element.
    if need in seen:            #> {need} is in the map at index {seen[need]}. || {need} hasn't appeared yet.
        return [seen[need], i]  #> Pair found in a single pass: {_return}.
    seen[num] = i               #> Remember {num} -> {i}.
```

| Directive | Effect |
| --- | --- |
| `#> text` | Narration for this line's step. `{expr}` is `repr`-formatted and `{!expr}` is inserted raw. `_return` (on return lines) and `_taken` (on branch lines) are in scope. |
| `#> yes \|\| no` | On `if` / `while` / `for` lines: the first text when the body runs, the second when it doesn't. Either side may be empty. |
| `#! text` | A footnote pinned to this line, shown as a superscript in the code and in the footnote list. Keep these for the *insight*, not the mechanics. |
| `#~` | Hide this step in "key steps" mode (e.g. an inner loop header that would repeat 50 times). |

Directives are stripped from the code shown in the editor. The gate renders every template in strict mode, so a typo in `{expr}` fails the build instead of showing a blank.

Write narration that explains **why**, not what. "max_l = 2 < max_r = 3, so the left side is the bottleneck" teaches. "Compare max_l and max_r" doesn't.

## 3. Pitfalls

A pitfall is a common mistake that the diagnosis can name once the fuzzer has shrunk a failing input.

```python
Pitfall("same-element", "Paired an element with itself",
        "You returned the same index twice. Look up the complement *before* inserting...",
        detect=lambda args, expected, actual: isinstance(actual, list) and len(actual) == 2 and actual[0] == actual[1])
Pitfall("off-by-one", "Read past the end", "...", error="IndexError: list index")    # matches the exception
Pitfall("pop-zero", "Used list.pop(0) as a queue", "...", code=r"\.pop\(0\)")          # matches the source
```

The gate runs every `detect` against **correct** answers and fails the build if one fires. A pitfall that blames correct code is worse than none.

## 4. Lens

The lens tells the visualizer how to draw this problem's variables. Without one you still get a reasonable picture from heuristics. With one you get the picture that makes the trick obvious.

```python
lens={"arrays": {"height": {"view": "bars", "pointers": ["l", "r", "i"]}}, "overlay": "water"}
lens={"arrays": {"nums": {"pointers": ["r"], "window": ["r - k + 1", "r"]}}, "indexes": {"dq": "nums"}}
lens={"maps": {"groups": {"key": "letter-counts"}}}
```

| Key | Effect |
| --- | --- |
| `arrays.<name>.view` | `"bars"` (heights, prices, temperatures) or `"chars"` (strings) |
| `arrays.<name>.pointers` | Integer variables drawn as labeled pointers under this array |
| `arrays.<name>.window` | Two expressions, evaluated per step, that bound a highlighted window |
| `maps.<name>.key` | Compact key rendering, e.g. `letter-counts` for 26-tuples |
| `indexes` | `{container: array}`: the container holds indices into `array` (monotonic deques, index stacks) |
| `stacks`, `grids`, `nodes`, `hide` | Force a stack or grid view, name linked-structure roots, hide helper variables |
| `overlay` | `water`, `container`, `histogram` or `index-graph`: problem-specific geometry drawn over the bars or arrays |

## 5. Build and check

```sh
cd pipeline
python -m feetcode_pipeline check two-sum                # the quality gate for one problem (substring match)
python -m feetcode_pipeline check --complexity two-sum   # ... plus a growth profile of every solution
python -m feetcode_pipeline build                        # regenerates only what changed
```

`--complexity` (which CI always runs) profiles every solution on `worst_case(n)`:

- **Measured growth worse than declared is an error.** Either the solution or its declared bound is wrong.
- **Better than declared is a warning.** It almost always means `worst_case` isn't the worst case: the pair is found on the first try, or the alphabet caps a scan. The growth charts are built from these profiles, so a lucky input would teach the wrong curve.
- Multi-variable bounds (`O(n·k)`) are skipped.

Then run `npm run dev` in `client/`, open the problem, and step through each lesson. Read the narration out loud: if it doesn't explain the trick to someone seeing it for the first time, rewrite it.

Commit the module **and** the regenerated files in `client/src/content/generated/`. CI runs `build --check` and fails if they're out of sync.
