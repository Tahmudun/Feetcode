import { expect, test } from "@playwright/test";
import { pythonReady, setCode } from "./helpers";

const BUGGY = `class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            seen[n] = i
            if target - n in seen:
                return [seen[target - n], i]
`;

const OPTIMAL = `class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
`;

const BRUTE = `class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
`;

test.describe("workspace", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/problems/two-sum");
    await pythonReady(page);
  });

  test("run shows per-case results for user code", async ({ page }) => {
    await setCode(page, BUGGY);
    await page.getByRole("button", { name: /^Run/ }).click();
    await expect(page.getByText("Wrong Answer")).toBeVisible();
    await expect(page.getByText(/2\/3 cases/)).toBeVisible();
  });

  test("submit shrinks a failure, names the pitfall, pins it to a line, and replays it", async ({ page }) => {
    await setCode(page, BUGGY);
    await page.getByRole("button", { name: /^Submit/ }).click();
    await expect(page.getByText("Smallest failing input")).toBeVisible();
    await expect(page.getByText("Where it goes wrong · line 7")).toBeVisible();
    // the finding is pinned under the line where the run first disagrees with the reference
    const note = page.locator(".cm-line-footnote");
    await expect(note).toContainText("Paired an element with itself");
    await expect(note).toContainText("The reference returns [0, 1].");
    await page.getByRole("button", { name: /Watch it go wrong/ }).click();
    const player = page.locator("section[aria-label^=Execution]");
    await expect(player.getByText(/returns \[0, 0\]/).first()).toBeVisible();
    // the editor follows the player: one highlighted line, live values at line ends
    await expect(page.locator(".cm-trace-line")).toHaveCount(1);
    await expect(page.locator(".cm-inline-value").first()).toBeVisible();
  });

  test("brute force is correct but exceeds the operation budget", async ({ page }) => {
    await setCode(page, BRUTE);
    await page.getByRole("button", { name: /^Submit/ }).click();
    await expect(page.getByText("Time Limit Exceeded")).toBeVisible();
    await expect(page.getByText(/How your code grows/)).toBeVisible();
    await expect(page.getByText("O(n²)").first()).toBeVisible();
  });

  test("accepted solution gets a complexity report and updates progress", async ({ page }) => {
    await setCode(page, OPTIMAL);
    await page.getByRole("button", { name: /^Submit/ }).click();
    await expect(page.getByText("Accepted", { exact: true })).toBeVisible();
    await expect(page.getByText(/Optimal complexity/)).toBeVisible();
    await page.goto("/problems");
    await expect(page.getByLabel("Solved").first()).toBeVisible();
  });

  test("visualize traces the user's own code", async ({ page }) => {
    await setCode(page, OPTIMAL);
    await page.getByRole("button", { name: "Visualize", exact: true }).click();
    const player = page.locator("section[aria-label^=Execution]");
    await expect(player).toBeVisible();
    await player.click();
    for (let i = 0; i < 6; i++) await page.keyboard.press("ArrowRight");
    await expect(player.getByText("seen", { exact: true }).first()).toBeVisible();
    await expect(player.getByLabel(/Variable tracks/)).toBeVisible();
  });
});

test("the divergence finder shows where a run leaves the reference, and the reference's run", async ({ page }) => {
  await page.goto("/problems/longest-substring-without-repeating-characters");
  await pythonReady(page);
  await setCode(
    page,
    "class Solution:\n    def lengthOfLongestSubstring(self, s):\n        seen = {}\n        l = best = 0\n        for r, c in enumerate(s):\n            if c in seen:\n                l = seen[c] + 1\n            seen[c] = r\n            best = max(best, r - l + 1)\n        return best\n",
  );
  await page.getByRole("button", { name: /^Submit/ }).click();
  await expect(page.locator(".cm-line-footnote")).toContainText("l never decreases");
  await page.getByRole("button", { name: /Show step/ }).click();
  await expect(page.getByLabel(/Variable tracks/)).toBeVisible();
  await expect(page.getByText("First disagreement at step")).toBeVisible();
  await page.getByRole("tab", { name: /Reference run/ }).click();
  await expect(page.getByText(/Its code stays hidden/)).toBeVisible();
});

test("an infinite loop is stopped and the page stays responsive", async ({ page }) => {
  await page.goto("/problems/two-sum");
  await pythonReady(page);
  await setCode(page, "class Solution:\n    def twoSum(self, nums, target):\n        while True:\n            pass\n");
  await page.getByRole("button", { name: /^Run/ }).click();
  await expect(page.getByText("Time Limit Exceeded")).toBeVisible();
});
