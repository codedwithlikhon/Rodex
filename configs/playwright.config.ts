import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '../tests/automation',
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  reporter: [['list'], ['html', { outputFolder: '../artifacts/playwright-report' }]],
  use: {
    baseURL: process.env.RODEX_AUTOMATION_BASE_URL ?? 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    storageState: process.env.PLAYWRIGHT_STORAGE_STATE ?? undefined,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], headless: process.env.CI ? true : false },
    },
  ],
});
