import { defineConfig, devices } from "@playwright/test";

const env = (
  globalThis as { process?: { env?: Record<string, string | undefined> } }
).process?.env ?? {};

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!env.CI,
  retries: env.CI ? 2 : 0,
  workers: env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: env.PLAYWRIGHT_TEST_BASE_URL || "http://127.0.0.1:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});