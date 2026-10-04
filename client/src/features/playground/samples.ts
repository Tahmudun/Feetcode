export const SAMPLES: { id: string; name: string; code: string }[] = [
  {
    id: "binary-search",
    name: "Binary search",
    code: `nums = [1, 3, 4, 7, 9, 12, 15, 20]
target = 12
lo, hi = 0, len(nums) - 1
found = -1
while lo <= hi:
    mid = (lo + hi) // 2
    if nums[mid] == target:
        found = mid
        break
    elif nums[mid] < target:
        lo = mid + 1
    else:
        hi = mid - 1
print("found at", found)
`,
  },
  {
    id: "bubble-sort",
    name: "Bubble sort",
    code: `a = [5, 1, 4, 2, 8]
n = len(a)
for i in range(n):
    swapped = False
    for j in range(n - 1 - i):
        if a[j] > a[j + 1]:
            a[j], a[j + 1] = a[j + 1], a[j]
            swapped = True
    if not swapped:
        break
print(a)
`,
  },
  {
    id: "reverse-list",
    name: "Reverse a linked list",
    code: `class ListNode:
    def __init__(self, val, next=None):
        self.val = val
        self.next = next

head = ListNode(1, ListNode(2, ListNode(3, ListNode(4))))
prev, curr = None, head
while curr:
    nxt = curr.next
    curr.next = prev
    prev, curr = curr, nxt
head = prev
`,
  },
  {
    id: "fib-memo",
    name: "Recursion + memo",
    code: `memo = {}

def fib(n):
    if n <= 1:
        return n
    if n in memo:
        return memo[n]
    memo[n] = fib(n - 1) + fib(n - 2)
    return memo[n]

print(fib(6))
`,
  },
  {
    id: "monotonic-stack",
    name: "Next greater element",
    code: `nums = [2, 7, 3, 5, 4, 6, 8]
answer = [-1] * len(nums)
stack = []
for i, x in enumerate(nums):
    while stack and nums[stack[-1]] < x:
        answer[stack.pop()] = x
    stack.append(i)
print(answer)
`,
  },
  {
    id: "bfs-grid",
    name: "BFS on a grid",
    code: `from collections import deque
grid = [
    [0, 0, 1, 0],
    [1, 0, 1, 0],
    [0, 0, 0, 0],
]
dist = {(0, 0): 0}
queue = deque([(0, 0)])
while queue:
    r, c = queue.popleft()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 4 and grid[nr][nc] == 0 and (nr, nc) not in dist:
            dist[(nr, nc)] = dist[(r, c)] + 1
            queue.append((nr, nc))
print(dist[(2, 3)])
`,
  },
];
