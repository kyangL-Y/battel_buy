import { defineConfig } from '@playwright/test'
import { appWebServers, noTraceUse } from './playwright.shared'

// 仅负责截图采集：复用本地后端/前端服务，并关闭 trace 降低噪音。
export default defineConfig({
  testDir: './tests',
  testMatch: /ui-audit-capture\.spec\.ts/,
  timeout: 180_000,
  use: noTraceUse,
  webServer: appWebServers,
})
