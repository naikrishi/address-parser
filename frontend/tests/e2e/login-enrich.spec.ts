import { expect, test } from "@playwright/test";

const adminUsername = process.env.PLAYWRIGHT_ADMIN_USERNAME || "admin";
const adminPassword = process.env.PLAYWRIGHT_ADMIN_PASSWORD || "admin12345";

test("admin can login and run enrichment", async ({ page }) => {
  await page.goto("/login");

  await page.getByLabel("Username").fill(adminUsername);
  await page.getByLabel("Password").fill(adminPassword);
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.waitForURL("**/");
  await expect(page.getByRole("heading", { name: "Inputs Feed" })).toBeVisible();

  await page.getByLabel("Raw address").fill("3400 W Plano Pkwy, Plano, TX 75075, USA");
  await page.getByLabel("Input source").fill("playwright");
  await page.getByLabel("Country hint").fill("US");
  await page.getByRole("button", { name: "Run enrich" }).click();

  await expect(page.getByRole("heading", { name: "Ranked Enrichment Results" })).toBeVisible();
  await expect(page.getByText("Rank #1")).toBeVisible();
  await expect(page.getByRole("link", { name: "Open detail" })).toBeVisible();
});