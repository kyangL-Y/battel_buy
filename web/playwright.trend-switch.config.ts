import { defineConfig, devices } from '@playwright/test'
import { frontendServer, sharedUse } from './playwright.shared'

export default defineConfig({
  testDir: './tests',
  testMatch: /trend-product-switch\.spec\.ts/,
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: {
    timeout: 15_000,
  },
  use: {
    ...sharedUse,
    ...devices['Desktop Chrome'],
    browserName: 'chromium',
  },
  webServer: [frontendServer],
})
