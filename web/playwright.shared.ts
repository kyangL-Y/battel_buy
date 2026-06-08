import type { PlaywrightTestConfig } from '@playwright/test'
import os from 'node:os'

function normalizeUrl(value: string | undefined, fallback: string) {
  const normalized = (value || '').trim()
  return (normalized || fallback).replace(/\/$/, '')
}

export const baseURL = normalizeUrl(process.env.PLAYWRIGHT_BASE_URL, 'http://127.0.0.1:4273')
export const backendURL = normalizeUrl(process.env.PLAYWRIGHT_BACKEND_URL, 'http://127.0.0.1:8001')
const frontendPort = Number(new URL(baseURL).port || (baseURL.startsWith('https:') ? 443 : 80))
const backendPort = Number(new URL(backendURL).port || (backendURL.startsWith('https:') ? 443 : 80))

export const sharedUse = {
  baseURL,
  trace: 'on-first-retry' as const,
} satisfies PlaywrightTestConfig['use']

export const noTraceUse = {
  baseURL,
  trace: 'off' as const,
} satisfies PlaywrightTestConfig['use']

// 这两个 server 只是给本地 Playwright 场景复用：一个启动后端，一个启动 Vite 前端。
// capture no-server 配置会刻意跳过它们，避免在只做截图/列表时强依赖本机服务状态。
export const backendServer = {
  command: os.platform() === 'win32' ? 'python -X utf8 backend_launcher.py' : './start_backend.sh',
  cwd: '..',
  env: {
    BATTEL_HOST: new URL(backendURL).hostname,
    BATTEL_PORT: String(backendPort),
  },
  port: backendPort,
  reuseExistingServer: true,
  timeout: 120_000,
} satisfies NonNullable<PlaywrightTestConfig['webServer']>[number]

export const frontendServer = {
  command: `npm run dev -- --host ${new URL(baseURL).hostname} --port ${frontendPort}`,
  env: {
    VITE_DEV_API_TARGET: backendURL,
  },
  port: frontendPort,
  reuseExistingServer: true,
  timeout: 120_000,
} satisfies NonNullable<PlaywrightTestConfig['webServer']>[number]

export const appWebServers = [backendServer, frontendServer] satisfies PlaywrightTestConfig['webServer']
