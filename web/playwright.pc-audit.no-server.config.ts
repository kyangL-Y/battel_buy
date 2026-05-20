import { defineConfig } from '@playwright/test'
import { noTraceUse } from './playwright.shared'

export default defineConfig({
  testDir: './tests',
  testMatch: /pc-workbench-layout-audit\.spec\.ts/,
  timeout: 120_000,
  expect: {
    timeout: 15_000,
  },
  use: noTraceUse,
  workers: 1,
})
