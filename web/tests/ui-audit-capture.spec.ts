import { expect, test } from '@playwright/test'

const loginAccount = process.env.BATTEL_E2E_ACCOUNT || 'admin'
const loginPassword = process.env.BATTEL_E2E_PASSWORD || 'admin123'

test('capture pc summary real first paint', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  const apiEvents: string[] = []
  page.on('response', (response) => {
    const url = response.url()
    if (url.includes('/api/product/options') || url.includes('/api/market/summary')) {
      apiEvents.push(`${response.status()} ${url}`)
    }
  })
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  const purchaseEntry = page.getByRole('button', { name: /进入采购平台|我是采购/ }).first()
  if (await purchaseEntry.isVisible().catch(() => false)) {
    await purchaseEntry.click()
  }
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByTestId('pcw-summary-data-row').first()).toBeVisible({ timeout: 15_000 })
  const rowCount = await page.getByTestId('pcw-summary-data-row').count()
  const emptyCount = await page.getByTestId('pcw-summary-empty-row').count()
  await page.screenshot({ path: 'test-results/pc-summary-real-first-paint.png', fullPage: true })
  console.log(JSON.stringify({ rowCount, emptyCount, apiEvents }, null, 2))
})

test('capture supplier backend master data after login', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.goto('/supplier-backend?mode=supplier&tab=supplier', { waitUntil: 'domcontentloaded' })
  await page.getByPlaceholder('账号').fill(loginAccount)
  await page.getByPlaceholder('密码').fill(loginPassword)
  const loginResponse = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200)
  await page.getByRole('button', { name: '登录后台' }).click()
  await loginResponse
  await expect(page.getByTestId('supplier-admin-panel')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByRole('textbox', { name: '供应商名称' })).toHaveValue('海鲜供应站B')
  await page.screenshot({ path: 'test-results/supplier-backend-master-data.png', fullPage: true })
})

test('capture mobile supplier portal independent layout', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/supplier-portal?mode=supplier-portal', { waitUntil: 'domcontentloaded' })
  await page.getByPlaceholder('账号').fill(loginAccount)
  await page.getByPlaceholder('密码').fill(loginPassword)
  const loginResponse = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200)
  await page.getByTestId('auth-login-button').click()
  await loginResponse
  await expect(page.getByTestId('auth-session-status')).toContainText('系统管理员', { timeout: 30_000 })
  await expect(page.getByLabel('报价状态队列')).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-supplier-portal-independent.png', fullPage: true })
})
