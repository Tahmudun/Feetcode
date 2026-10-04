import { expect, type Page } from "@playwright/test";

/** Replace the editor's contents (insertText bypasses auto-indent and bracket closing). */
export async function setCode(page: Page, code: string) {
  await page.locator(".cm-content").click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.press("Delete");
  await page.keyboard.insertText(code);
}

export async function pythonReady(page: Page) {
  await expect(page.getByText("Python ready")).toBeVisible({ timeout: 90_000 });
}
