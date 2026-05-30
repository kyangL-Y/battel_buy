import { defineConfig, devices } from '@playwright/test'
import { appWebServers, sharedUse } from './playwright.shared'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 120_000,
  expect: {
    timeout: 15_000,
  },
  use: sharedUse,
  webServer: appWebServers,
  projects: [
    {
      name: 'current-ui-desktop',
      testMatch: /current-ui-smoke\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        browserName: 'chromium',
      },
    },
  ],
})
