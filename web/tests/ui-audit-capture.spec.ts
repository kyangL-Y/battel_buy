import { expect, test } from '@playwright/test'
import type { APIRequestContext } from '@playwright/test'

const loginAccount = process.env.BATTEL_E2E_ACCOUNT || 'admin'
const loginPassword = process.env.BATTEL_E2E_PASSWORD || 'admin123'
const API_BASE_URL = process.env.PLAYWRIGHT_BACKEND_URL || 'http://127.0.0.1:8001'

const procurementUser = {
  id: 1,
  username: 'capture-buyer',
  display_name: '截图采购',
  role: 'procurement',
  supplier_id: null,
  is_active: true,
}

async function loginAsAdmin(request: APIRequestContext) {
  const response = await request.post(`${API_BASE_URL}/api/auth/login`, {
    data: {
      username: 'admin',
      password: 'admin123',
    },
  })
  expect(response.ok()).toBeTruthy()
  return await response.json()
}

async function seedAdminSession(page: import('@playwright/test').Page, request: APIRequestContext) {
  const session = await loginAsAdmin(request)
  await page.addInitScript(([storageKey, authSession]) => {
    window.localStorage.setItem(storageKey, JSON.stringify(authSession))
  }, ['battel.auth.session.procurement', session] as const)
}

async function seedProcurementSession(page: import('@playwright/test').Page) {
  await page.addInitScript((user) => {
    window.localStorage.setItem('battel.auth.session.procurement', JSON.stringify({
      access_token: 'capture-procurement-token',
      token_type: 'Bearer',
      expires_in: 3600,
      user,
    }))
  }, procurementUser)
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ user: procurementUser }),
    })
  })
}

test.setTimeout(180_000)

test('capture desktop landing and workbench screens', async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop-landing-home.png', fullPage: true })

  await seedAdminSession(page, request)
  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-summary.png', fullPage: true })

  await page.locator('[data-section-id="trend"]').click()
  await expect(page.locator('.pcw-trend-page')).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-trend.png', fullPage: true })

  await page.locator('[data-section-id="alerts"]').click()
  await expect(page.getByRole('heading', { name: '今日价格提醒' })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-alerts.png', fullPage: true })

  await page.locator('[data-section-id="plan"]').click()
  await expect(page.getByRole('heading', { name: '采购计划' }).first()).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-plan.png', fullPage: true })

  await page.locator('[data-section-id="settings"]').click()
  await expect(page.getByRole('heading', { name: '数据同步设置' })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-settings.png', fullPage: true })
})

test('capture platform admin and supplier backend screens', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })

  await page.goto('/admin', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('platform-admin-screen')).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop-platform-admin-login.png', fullPage: true })

  await page.getByRole('button', { name: /来源覆盖 SRC/ }).click()
  await expect(page.getByTestId('platform-source-coverage-list')).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop-platform-admin-coverage.png', fullPage: true })

  await page.goto('/supplier-backend', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('supplier-login-form')).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop-supplier-backend-login.png', fullPage: true })

  await page.getByPlaceholder('账号').fill(loginAccount)
  await page.getByPlaceholder('密码').fill(loginPassword)
  const loginResponse = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200)
  await page.getByRole('button', { name: '登录' }).click()
  await loginResponse
  await expect(page.getByTestId('supplier-admin-panel')).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-supplier-backend-panel.png', fullPage: true })
})

test('capture mobile landing and workflow screens', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-landing-first-screen.png', fullPage: false })

  await page.getByRole('button', { name: '账号登录' }).click()
  await expect(page.getByRole('dialog', { name: '账号登录' })).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-procurement-login-sheet.png', fullPage: false })

  await page.keyboard.press('Escape')
  await seedProcurementSession(page)
  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-market-summary-workspace.png', fullPage: false })

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '提醒' }).click()
  await expect(page.getByText('价格提醒').first()).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-alerts-workspace.png', fullPage: false })

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '采购' }).click()
  await expect(page.getByLabel('菜单文本输入')).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-menu-workspace.png', fullPage: false })
})

test('capture mobile supplier portal pages', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })

  await page.goto('/supplier-portal?mode=supplier-portal', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('supplier-portal-screen')).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-supplier-portal-login.png', fullPage: false })

  await page.getByPlaceholder('账号').fill(loginAccount)
  await page.getByPlaceholder('密码').fill(loginPassword)
  const loginResponse = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200)
  await page.getByTestId('auth-login-button').click()
  await loginResponse
  await expect(page.getByTestId('auth-session-status')).toContainText('系统管理员', { timeout: 30_000 })
  await page.screenshot({ path: 'test-results/mobile-supplier-portal-panel.png', fullPage: true })
})
