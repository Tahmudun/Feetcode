// Regenerate the README screenshots: npm run build && npm run preview & node scripts/readme-shots.mjs
import { chromium } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const out = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../docs/media");
const base = process.env.BASE_URL || "http://localhost:4173";
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
await page.addInitScript(() => localStorage.setItem("fc:theme", "dark"));

async function setCode(code) {
  await page.locator(".cm-content").click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.press("Delete");
  await page.keyboard.insertText(code);
}
const shot = async (name) => {
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${out}/${name}.png` });
  console.log("wrote", name);
};
const ready = () => page.getByText("Python ready").waitFor({ timeout: 90_000 });
// Scroll the player to the top of its scroll container, leaving a little air above it.
const frame = (el) => {
  el.scrollIntoView({ block: "start" });
  let p = el.parentElement;
  while (p && !(p.scrollHeight > p.clientHeight && getComputedStyle(p).overflowY !== "visible")) p = p.parentElement;
  p?.scrollBy(0, -10);
};

// 1. Home
await page.goto(`${base}/`);
await page.waitForTimeout(5200);
await shot("home");

// 2. Lesson: Trapping Rain Water, mid-way, levels visible
await page.goto(`${base}/problems/trapping-rain-water`);
await ready();
await page.getByRole("tab", { name: /Learn/ }).click();
const player = page.locator("section[aria-label^=Execution]");
await player.click();
for (let i = 0; i < 17; i++) await page.keyboard.press("ArrowRight");
await player.evaluate(frame);
await shot("lesson");

// 3. Failure: the fuzzer's minimal input, the pitfall, and the replay
await page.goto(`${base}/problems/two-sum`);
await ready();
await setCode(`class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            seen[n] = i
            if target - n in seen:
                return [seen[target - n], i]
`);
await page.getByRole("button", { name: /^Submit/ }).click();
await page.getByRole("button", { name: /Watch it fail/ }).click();
await page.locator("text=Likely cause").scrollIntoViewIfNeeded();
await shot("failure");

// 4. Complexity: correct but O(n²) - heatmap + growth chart
await setCode(`class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
`);
await page.getByRole("button", { name: /^Submit/ }).click();
// getByText is a case-insensitive substring match by default, and the "judging" placeholder
// says "Profiling how your code grows" - so wait for the verdict itself.
await page.getByText("Time Limit Exceeded", { exact: true }).waitFor({ timeout: 120_000 });
// Give the console room for the chart: drag the editor/console divider up.
const divider = page.locator(".cursor-row-resize").first();
const box = await divider.boundingBox();
if (box) {
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2, 340, { steps: 8 });
  await page.mouse.up();
}
await page.getByRole("tab", { name: /Learn/ }).click();
await page.getByText("Why the optimization matters").scrollIntoViewIfNeeded();
await page.getByRole("button", { name: /Show heatmap in editor/ }).click();
await page.locator("h4", { hasText: "How your code grows" }).scrollIntoViewIfNeeded();
await shot("complexity");

// 5. Linked list: arrows flip, nodes stay
await page.goto(`${base}/problems/reverse-linked-list`);
await ready();
await page.getByRole("tab", { name: /Learn/ }).click();
await player.click();
for (let i = 0; i < 6; i++) await page.keyboard.press("ArrowRight");
await player.evaluate(frame);
await shot("linked-list");

await browser.close();
