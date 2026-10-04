// Dev helper: screenshot a route of the preview server after optional actions.
// usage: node scripts/shot.mjs <path> <out.png> [width] [height] [theme]
// ACTIONS='[{"click":"text=Learn"},{"wait":800},{"press":"ArrowRight"},{"waitFor":"css"}]'
import { chromium } from "@playwright/test";
const [path = "/", out = "shot.png", w = "1440", h = "900", theme = "dark"] = process.argv.slice(2);
const actions = JSON.parse(process.env.ACTIONS || "[]");
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || "/opt/pw-browsers/chromium" });
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
page.on("console", (m) => { if (m.type() === "error") console.log("console:", m.text().slice(0, 300)); });
page.on("pageerror", (e) => console.log("pageerror:", e.message));
await page.addInitScript((t) => localStorage.setItem("fc:theme", t), theme);
await page.goto(`http://localhost:4173${path}`, { waitUntil: "networkidle" });
for (const a of actions) {
  if (a.click) await page.click(a.click, { timeout: 30000 });
  if (a.wait) await page.waitForTimeout(a.wait);
  if (a.waitFor) await page.waitForSelector(a.waitFor, { timeout: 90000 });
  if (a.press) await page.keyboard.press(a.press);
  if (a.type) await page.keyboard.type(a.type);
  if (a.type_raw) await page.keyboard.insertText(a.type_raw);
  if (a.eval) console.log("eval:", await page.evaluate(a.eval));
}
await page.waitForTimeout(300);
await page.screenshot({ path: out, fullPage: !!process.env.FULL });
await browser.close();
console.log("saved", out);
