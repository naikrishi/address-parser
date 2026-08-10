import { expect, test } from "@playwright/test";

const adminUsername = process.env.PLAYWRIGHT_ADMIN_USERNAME || "admin";
const adminPassword = process.env.PLAYWRIGHT_ADMIN_PASSWORD || "admin12345";

async function login(page: import("@playwright/test").Page): Promise<void> {
  await page.goto("/login");

  await page.getByLabel("Username").fill(adminUsername);
  await page.getByLabel("Password").fill(adminPassword);
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.waitForURL("**/");
  await expect(page.getByRole("heading", { name: "Inputs Feed" })).toBeVisible();
}

test("admin can login and run enrichment", async ({ page }) => {
  await login(page);

  await page.getByLabel("Raw address").fill("3400 W Plano Pkwy, Plano, TX 75075, USA");
  await page.getByLabel("Input source").fill("playwright");
  await page.getByLabel("Country hint").fill("US");
  await page.getByRole("button", { name: "Run enrich" }).click();

  await expect(page.getByRole("heading", { name: "Ranked Enrichment Results" })).toBeVisible();
  await expect(page.getByText("Rank #1")).toBeVisible();
  await expect(page.getByRole("link", { name: "Open detail" })).toBeVisible();
});

test("logout returns user to login page", async ({ page }) => {
  await login(page);

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("user can open detail from inputs feed record", async ({ page }) => {
  await login(page);

  await page.getByLabel("Raw address").fill("3400 W Plano Pkwy, Plano, TX 75075, USA");
  await page.getByLabel("Input source").fill("playwright-record-link");
  await page.getByLabel("Country hint").fill("US");
  await page.getByRole("button", { name: "Run enrich" }).click();
  await expect(page.getByRole("heading", { name: "Ranked Enrichment Results" })).toBeVisible();

  const recordDetailLink = page.getByRole("link", { name: "Open latest parse" }).first();
  await expect(recordDetailLink).toBeVisible();
  await recordDetailLink.click();

  await expect(page).toHaveURL(/\/parse\//);
  await expect(page.getByRole("heading", { name: "Detail View" })).toBeVisible();
});