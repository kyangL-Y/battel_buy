import { defineConfig } from '@playwright/test'
import { noTraceUse } from './playwright.shared'

// 外部已经启动好前端和后端时使用；只做页面采集，不接管服务生命周期。
export default defineConfig({
  testDir: './tests',
  testMatch: /ui-audit-capture\.spec\.ts/,
  timeout: 180_000,
  use: noTraceUse,
})
