import { defineConfig, devices } from '@playwright/test'
import { appWebServers, sharedUse } from './playwright.shared'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  use: sharedUse,
  webServer: appWebServers,
  projects: [
    {
      name: 'desktop-chromium',
      testMatch: /pc-summary-first-paint\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        browserName: 'chromium',
      },
    },
  ],
})
