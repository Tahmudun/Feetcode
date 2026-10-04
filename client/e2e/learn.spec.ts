import { expect, test } from "@playwright/test";

test("lesson player narrates, steps, and quizzes in predict mode", async ({ page }) => {
  await page.goto("/problems/trapping-rain-water");
  await page.getByRole("tab", { name: /Learn/ }).click();
  await expect(page.getByText("The key insight")).toBeVisible();
  const player = page.locator("section[aria-label^=Execution]");
  await expect(player.getByText(/water decided/)).toBeVisible();
  await player.getByRole("button", { name: /Predict/ }).click();
  await player.click();
  for (let i = 0; i < 6; i++) await page.keyboard.press("ArrowRight");
  await expect(player.getByText(/Predict: will this/)).toBeVisible();
  await player.getByRole("button", { name: /^True/ }).click();
  await expect(player.getByText(/Correct|Not quite/)).toBeVisible();
});

test("problem list filters by company and the palette navigates", async ({ page }) => {
  await page.goto("/problems?company=Google");
  await expect(page.getByText(/Ranked by how often Google/)).toBeVisible();
  await page.keyboard.press("ControlOrMeta+k");
  await page.keyboard.type("lru");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/problems\/lru-cache/);
  await expect(page.getByRole("heading", { name: /LRU Cache/ })).toBeVisible();
});

test("playground visualizes arbitrary code", async ({ page }) => {
  await page.goto("/playground");
  await page.getByRole("button", { name: "Reverse a linked list" }).click();
  await expect(page.getByText("Python ready")).toBeVisible({ timeout: 90_000 });
  await page.getByRole("button", { name: /Visualize/ }).click();
  const player = page.locator("section[aria-label^=Execution]");
  await expect(player.getByText("The program starts")).toBeVisible();
  await player.click();
  await page.keyboard.press("End");
  await expect(player.getByText("linked nodes")).toBeVisible();
  await expect(player.getByText(/1 → 2 → 3 → 4|4 nodes/)).toBeVisible();
});
