import { chromium } from "file:///D:/Devlopment files/Project files/Frontend code/ssct-Frontend CF/node_modules/playwright-core/index.mjs";
import fs from "node:fs";
fs.mkdirSync("artifacts/admin-redesign", { recursive: true });
const browser = await chromium.launch({ channel: "msedge", headless: true });
const context = await browser.newContext({
  viewport: { width: 1672, height: 1000 },
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto("http://localhost:5174/admin/dashboard");
await page.waitForURL("**/admin/login");
await page.locator("[name=username]").fill("qa-admin");
await page.locator("[name=password]").fill("qa-password-only-123");
await page.getByRole("button", { name: "Sign in securely" }).click();
await page.waitForURL("**/admin/dashboard");
await page.getByText("Active Courses", { exact: true }).waitFor();
await page.waitForTimeout(600);
await page.screenshot({
  path: "artifacts/admin-redesign/dashboard-desktop-test.png",
  fullPage: true,
});
console.log(
  "Dashboard visible; public headers:",
  await page.locator(".header,.announcement,.footer,.chat-widget").count(),
);
await page.getByRole("link", { name: "Courses", exact: true }).click();
await page
  .getByRole("heading", { name: "Courses", exact: true })
  .first()
  .waitFor();
await page.getByRole("button", { name: "Add course", exact: true }).click();
await page
  .getByLabel("Name", { exact: false })
  .first()
  .fill("QA Browser Course");
await page.getByLabel("Stable slug").fill("qa-browser-course-" + Date.now());
await page
  .getByLabel("Short description")
  .fill("Temporary browser test course.");
await page.getByLabel("Category IDs").fill("it");
await page.getByLabel("Category IDs").press("Enter");
await page.getByLabel("Publication status").selectOption("published");
await page.getByRole("button", { name: "Save changes" }).click();
await page.locator("dialog").waitFor({ state: "detached" });
await page
  .getByRole("heading", { name: "Courses", exact: true })
  .first()
  .waitFor();
console.log("Created course through browser.");
await page.getByRole("link", { name: "Public website", exact: true }).click();
await page.waitForURL("http://localhost:5174/");
await page.waitForTimeout(300);
await page.goto("http://localhost:5174/admin/dashboard");
await page.waitForURL("**/admin/login");
console.log("Leaving admin invalidated session and protected reentry.");
await page.locator("[name=username]").fill("qa-admin");
await page.locator("[name=password]").fill("qa-password-only-123");
await page.getByRole("button", { name: "Sign in securely" }).click();
await page.waitForURL("**/admin/dashboard");
await page.setViewportSize({ width: 390, height: 844 });
await page.waitForTimeout(300);
await page.screenshot({
  path: "artifacts/admin-redesign/dashboard-mobile-test.png",
  fullPage: true,
});
await page.getByRole("button", { name: "Toggle navigation" }).click();
await page.getByRole("link", { name: "Registrations", exact: true }).click();
await page
  .getByRole("heading", { name: "Registrations", exact: true })
  .first()
  .waitFor();
console.log("Mobile drawer navigation works.");
await page.goto("http://localhost:5174/batches");
await page.getByRole("heading", { name: "Our Batches", exact: true }).waitFor();
await page.screenshot({
  path: "artifacts/admin-redesign/batches-empty-mobile.png",
  fullPage: true,
});
console.log("Runtime errors:", errors);
if (errors.length) throw new Error(errors.join("\n"));
await browser.close();
