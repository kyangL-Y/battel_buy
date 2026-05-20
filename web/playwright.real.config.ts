import { defineConfig, devices } from '@playwright/test'
import { appWebServers, sharedUse } from './playwright.shared'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  timeout: 120_000,
  expect: {
    timeout: 15_000,
  },
  use: sharedUse,
  webServer: appWebServers,
  projects: [
    {
      name: 'real-desktop-chromium',
      testMatch: /real-data-regression\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        browserName: 'chromium',
      },
    },
  ],
})
