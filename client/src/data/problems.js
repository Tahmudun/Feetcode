// Problem catalog. One entry per problem; `live: true` means it has at least one
// step script in data/steps/. Everything else renders as "in the lab" on the home page.

export const PATTERNS = [
  "Arrays & Hashing",
  "Two Pointers",
  "Sliding Window",
  "Stack",
  "Binary Search",
];

export const PROBLEMS = [
  {
    id: "group-anagrams",
    title: "Group Anagrams",
    pattern: "Arrays & Hashing",
    difficulty: "Medium",
    live: true,
    blurb:
      "Given an array of strings, group the anagrams together. The classic 'design a canonical key' problem.",
    statement:
      "Given an array of strings strs, group the anagrams together. You can return the answer in any order. An anagram is a word formed by rearranging the letters of another, using all the original letters exactly once.",
    example: 'Input: ["eat","tea","tan","ate","nat","bat"]\nOutput: [["eat","tea","ate"],["tan","nat"],["bat"]]',
    insight:
      "Anagrams are equal under reordering — so build a key that ignores order. Character counts (or the sorted word) give every anagram family one canonical signature, and a hash map does the grouping for free.",
    references: [
      "Cormen, Leiserson, Rivest, Stein. Introduction to Algorithms (CLRS), §11 — Hash Tables.",
      "Python Language Reference, Data Model — “hashable”: why the key must be a tuple, not a list.",
    ],
  },
  { id: "two-sum", title: "Two Sum", pattern: "Arrays & Hashing", difficulty: "Easy", live: false },
  { id: "contains-duplicate", title: "Contains Duplicate", pattern: "Arrays & Hashing", difficulty: "Easy", live: false },
  { id: "valid-anagram", title: "Valid Anagram", pattern: "Arrays & Hashing", difficulty: "Easy", live: false },
  { id: "top-k-frequent", title: "Top K Frequent Elements", pattern: "Arrays & Hashing", difficulty: "Medium", live: false },
  { id: "product-except-self", title: "Product of Array Except Self", pattern: "Arrays & Hashing", difficulty: "Medium", live: false },
  { id: "valid-sudoku", title: "Valid Sudoku", pattern: "Arrays & Hashing", difficulty: "Medium", live: false },
  { id: "encode-decode-strings", title: "Encode and Decode Strings", pattern: "Arrays & Hashing", difficulty: "Medium", live: false },
  { id: "longest-consecutive", title: "Longest Consecutive Sequence", pattern: "Arrays & Hashing", difficulty: "Medium", live: false },
  { id: "valid-palindrome", title: "Valid Palindrome", pattern: "Two Pointers", difficulty: "Easy", live: false },
  { id: "container-water", title: "Container With Most Water", pattern: "Two Pointers", difficulty: "Medium", live: false },
  { id: "longest-substring", title: "Longest Substring Without Repeating Characters", pattern: "Sliding Window", difficulty: "Medium", live: false },
  { id: "valid-parentheses", title: "Valid Parentheses", pattern: "Stack", difficulty: "Easy", live: false },
  { id: "binary-search", title: "Binary Search", pattern: "Binary Search", difficulty: "Easy", live: false },
];
