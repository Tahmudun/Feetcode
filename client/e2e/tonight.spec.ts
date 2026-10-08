import { expect, test } from "@playwright/test";
import { pythonReady, setCode } from "./helpers";

const CONTAINS_DUPLICATE = `class Solution:
    def containsDuplicate(self, nums):
        seen = set()
        for n in nums:
            if n in seen:
                return True
            seen.add(n)
        return False
`;

test("a first session: start from home, solve the item, and the session completes", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Start tonight: Contains Duplicate/ }).click();
  await expect(page).toHaveURL(/\/problems\/contains-duplicate$/);
  // The header carries the session while you work: a single item, so this is the last one.
  await expect(page.getByText(/Last one:/)).toBeVisible();

  await pythonReady(page);
  await setCode(page, CONTAINS_DUPLICATE);
  await page.getByRole("button", { name: /^Submit/ }).click();
  await expect(page.getByText("That was tonight's last item.", { exact: false })).toBeVisible();
  await expect(page.getByRole("link", { name: /Tonight done · 1\/1/ })).toBeVisible();

  await page.getByRole("link", { name: /Tonight done/ }).click();
  await expect(page.getByRole("heading", { name: "That's tonight done." })).toBeVisible();
  // The solved problem is now a lit star on the path.
  await expect(page.getByRole("link", { name: "Contains Duplicate: solved" })).toBeVisible();
});

test("the plan for a returning user mixes recall, fix and new, and the header walks it", async ({ page }) => {
  const day = 86_400_000;
  const now = Date.now();
  const events = [
    { t: "submit", p: "contains-duplicate", v: "accepted", ts: now - 3 * day },
    { t: "submit", p: "valid-anagram", v: "wrong", ts: now - day },
  ];
  await page.addInitScript((ev) => {
    if (!sessionStorage.getItem("seeded")) {
      localStorage.setItem("fc:events:v1", JSON.stringify(ev));
      sessionStorage.setItem("seeded", "1");
    }
  }, events);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Your plan for tonight" })).toBeVisible();
  const plan = page.getByRole("list").filter({ hasText: "Recall" });
  await expect(plan.getByRole("listitem")).toHaveCount(3);
  await expect(plan.getByRole("listitem").nth(0)).toContainText("Contains Duplicate");
  await expect(plan.getByRole("listitem").nth(1)).toContainText("Valid Anagram");
  await expect(plan.getByRole("listitem").nth(1)).toContainText("wrong answer");
  await expect(plan.getByRole("listitem").nth(2)).toContainText("Two Sum");

  await page.getByRole("button", { name: /Start tonight's session/ }).click();
  await expect(page).toHaveURL(/\/review$/);
  // On the recall item's page the header points past it, to the fix.
  await expect(page.getByRole("link", { name: /Then: Fix Valid Anagram/ })).toBeVisible();
  await page.getByRole("button", { name: /Reveal/ }).click();
  await page.getByRole("button", { name: /Good/ }).click();
  await expect(page.getByRole("link", { name: /1\/3.*Next: Fix Valid Anagram/ })).toBeVisible();
  await page.getByRole("link", { name: /Next: Fix Valid Anagram/ }).click();
  await expect(page).toHaveURL(/\/problems\/valid-anagram$/);
  await expect(page.getByRole("link", { name: /Then: Solve Two Sum/ })).toBeVisible();
});
