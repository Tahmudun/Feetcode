import { expect, test } from "@playwright/test";

test.describe("on a phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("the menu reaches every page, closes on navigation and on Escape", async ({ page }) => {
    await page.goto("/");
    const menu = page.getByRole("button", { name: "Menu" });
    await expect(menu).toHaveAttribute("aria-expanded", "false");

    await menu.click();
    const nav = page.getByRole("navigation", { name: "Main" });
    for (const name of ["Tonight", "Problems", "Review", "Playground", "Pattern guides", "Stats"]) {
      await expect(nav.getByRole("link", { name, exact: true })).toBeVisible();
    }
    await nav.getByRole("link", { name: "Problems", exact: true }).click();
    await expect(page).toHaveURL(/\/problems$/);
    await expect(nav).toBeHidden();

    await page.getByRole("button", { name: "Menu" }).click();
    await page.keyboard.press("Escape");
    await expect(nav).toBeHidden();
    await expect(page.getByRole("button", { name: "Menu" })).toBeFocused();
    // Nothing on the page is wider than the screen.
    expect(await page.evaluate<number>("document.documentElement.scrollWidth")).toBeLessThanOrEqual(390);
  });
});
