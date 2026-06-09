import { expect, test } from '@playwright/test'
import type { APIRequestContext, Page } from '@playwright/test'
import { expectNoHorizontalOverflow } from './helpers/layout'
import { backendURL } from '../playwright.shared'
import { PROCUREMENT_AUTH_STORAGE_KEY } from './helpers/authSessionStorage'

const AUTH_STORAGE_KEY = PROCUREMENT_AUTH_STORAGE_KEY

async function loginAsAdmin(request: APIRequestContext) {
  const response = await request.post(`${backendURL}/api/auth/login`, {
    data: {
      username: 'admin',
      password: 'admin123',
    },
  })
  expect(response.ok()).toBeTruthy()
  return await response.json()
}

async function seedAdminSession(page: Page, request: APIRequestContext) {
  const session = await loginAsAdmin(request)
  await page.addInitScript(
    ([storageKey, authSession]) => {
      window.localStorage.setItem(storageKey, JSON.stringify(authSession))
    },
    [AUTH_STORAGE_KEY, session] as const,
  )
}

test.describe('当前采购端全界面冒烟', () => {
  test('桌面首页以采购账号登录为主入口并可进入工作台', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1024 })
    await page.goto('/', { waitUntil: 'domcontentloaded' })

    await expect(page.getByTestId('sales-landing-view')).toBeVisible()
    await expect(page.getByRole('heading', { name: '欢迎登录食采云' })).toBeVisible()
    await expect(page.locator('.platform-choice-login-card')).toContainText('账号登录')
    await expect(page.getByTestId('supplier-choice-button')).toBeVisible()

    const loginForm = page.locator('.platform-choice-login-form')
    await loginForm.getByPlaceholder('采购账号或管理员账号').fill('admin')
    await loginForm.getByPlaceholder('请输入密码').fill('admin123')
    await loginForm.getByRole('button', { name: '登录', exact: true }).click()

    await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 45_000 })
    await expect(page).toHaveURL(/mode=workspace/)
    await expectNoHorizontalOverflow(page)
  })

  test('桌面首页不提前加载工作台页面', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1024 })
    const requestedUrls: string[] = []
    page.on('request', (request) => {
      requestedUrls.push(request.url())
    })

    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('sales-landing-view')).toBeVisible()
    await page.waitForTimeout(800)

    const workspaceChunkPattern = /\/src\/components\/(MarketSummaryPanel|ProductTrendPanel|MenuPlanPanel|PcPriceWorkbench)\.vue|\/assets\/(MarketSummaryPanel|ProductTrendPanel|MenuPlanPanel|PcPriceWorkbench)-/
    expect(requestedUrls.some((requestUrl) => workspaceChunkPattern.test(requestUrl))).toBe(false)
    expect(requestedUrls.some((requestUrl) => requestUrl.includes('/api/'))).toBe(false)
  })

  test('桌面首页有登录态时不提前加载行情数据', async ({ page, request }) => {
    await page.setViewportSize({ width: 1440, height: 1024 })
    await seedAdminSession(page, request)
    const requestedUrls: string[] = []
    page.on('request', (pageRequest) => {
      requestedUrls.push(pageRequest.url())
    })

    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('sales-landing-view')).toBeVisible()
    await page.waitForTimeout(800)

    const workspaceChunkPattern = /\/src\/components\/(MarketSummaryPanel|ProductTrendPanel|MenuPlanPanel|PcPriceWorkbench)\.vue|\/assets\/(MarketSummaryPanel|ProductTrendPanel|MenuPlanPanel|PcPriceWorkbench)-/
    expect(requestedUrls.some((requestUrl) => workspaceChunkPattern.test(requestUrl))).toBe(false)
    expect(requestedUrls.some((requestUrl) => requestUrl.includes('/api/market/summary'))).toBe(false)
    expect(requestedUrls.some((requestUrl) => requestUrl.includes('/api/product/options'))).toBe(false)
  })

  test('桌面工作台核心分区可切换', async ({ page, request }) => {
    await page.setViewportSize({ width: 1440, height: 1024 })
    await seedAdminSession(page, request)
    await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })

    await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 45_000 })
    await expect(page.getByRole('heading', { name: '市场价格工作台' })).toBeVisible()

    await page.locator('[data-section-id="trend"]').click()
    await expect(page.locator('.pcw-trend-page')).toBeVisible({ timeout: 30_000 })

    await page.locator('[data-section-id="market"]').click()
    await expect(page.getByRole('heading', { name: '市场行情' })).toBeVisible()

    await page.locator('[data-section-id="quotes"]').click()
    await expect(page.getByRole('heading', { name: '供应商报价' })).toBeVisible()

    await page.locator('[data-section-id="plan"]').click()
    await expect(page.getByTestId('pcw-menu-workspace')).toBeVisible()

    await page.locator('[data-section-id="settings"]').click()
    await expect(page.getByRole('heading', { name: '同步、来源、策略、提醒统一管理' })).toBeVisible()
    await expectNoHorizontalOverflow(page)
  })

  test('供应商入口不再注册申请，账号登录后进入报价门户', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1024 })
    await page.goto('/supplier-portal', { waitUntil: 'domcontentloaded' })

    await expect(page.getByTestId('supplier-portal-screen')).toBeVisible()
    await expect(page.getByTestId('supplier-login-form')).toBeVisible()
    await expect(page.getByText('账号由采购分配').first()).toBeVisible()
    await expect(page.getByRole('button', { name: '注册' })).toHaveCount(0)

    await page.getByTestId('auth-username-input').fill('admin')
    await page.getByTestId('auth-password-input').fill('admin123')
    await page.getByTestId('auth-login-button').click()

    await expect(page.getByTestId('auth-session-status')).toContainText('系统管理员', { timeout: 45_000 })
    await expect(page.getByTestId('supplier-admin-panel')).toBeVisible()
    await expectNoHorizontalOverflow(page)
  })

  test('移动首页登录卡、供应商入口和采购登录弹窗可用', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/', { waitUntil: 'domcontentloaded' })

    await expect(page.getByTestId('sales-landing-view')).toBeVisible()
    await expect(page.getByRole('heading', { name: '登录后查看菜价' })).toBeVisible()
    await expect(page.getByRole('button', { name: '账号登录' })).toBeVisible()
    await expect(page.getByRole('button', { name: /供应商.*我要报价/ })).toBeVisible()

    await page.getByRole('button', { name: '账号登录' }).click()
    await expect(page.getByRole('dialog', { name: '账号登录' })).toBeVisible()
    await page.getByPlaceholder('采购账号或管理员账号').fill('admin')
    await page.getByPlaceholder('请输入密码').fill('admin123')
    await page.getByRole('dialog', { name: '账号登录' }).getByRole('button', { name: '登录', exact: true }).click()

    await expect(page.getByTestId('market-mobile-list')).toBeVisible({ timeout: 45_000 })
    await expect(page).toHaveURL(/mode=workspace/)
    await expectNoHorizontalOverflow(page)
  })

  test('移动首页不提前加载工作区页面', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    const requestedUrls: string[] = []
    page.on('request', (request) => {
      requestedUrls.push(request.url())
    })

    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('sales-landing-view')).toBeVisible()
    await page.waitForTimeout(800)

    const workspaceChunkPattern = /\/src\/components\/(MarketSummaryPanel|ProductTrendPanel|MenuPlanPanel|PcPriceWorkbench)\.vue|\/assets\/(MarketSummaryPanel|ProductTrendPanel|MenuPlanPanel|PcPriceWorkbench)-/
    expect(requestedUrls.some((requestUrl) => workspaceChunkPattern.test(requestUrl))).toBe(false)
    expect(requestedUrls.some((requestUrl) => requestUrl.includes('/api/'))).toBe(false)

    await page.getByTestId('enter-workspace-button').click()
    await expect(page.getByRole('dialog', { name: '账号登录' })).toBeVisible()
    await expect(page.getByTestId('market-mobile-list')).toHaveCount(0)
    expect(requestedUrls.some((requestUrl) => /\/src\/components\/MarketSummaryPanel\.vue|\/assets\/MarketSummaryPanel-/.test(requestUrl))).toBe(false)
  })

  test('移动菜价页不提前加载明细和采购页面', async ({ page, request }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await seedAdminSession(page, request)
    const requestedUrls: string[] = []
    page.on('request', (pageRequest) => {
      requestedUrls.push(pageRequest.url())
    })
    const trendOrMenuChunkPattern = /\/src\/components\/(ProductTrendPanel|MenuPlanPanel)\.vue|\/assets\/(ProductTrendPanel|MenuPlanPanel)-/

    await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('market-mobile-list')).toBeVisible({ timeout: 45_000 })
    await page.waitForTimeout(800)
    const nextSummaryPagePattern = /\/api\/market\/summary\?.*offset=(?!0(?:&|$))\d+/
    expect(requestedUrls.some((requestUrl) => nextSummaryPagePattern.test(requestUrl))).toBe(false)
    expect(requestedUrls.some((requestUrl) => trendOrMenuChunkPattern.test(requestUrl))).toBe(false)

    await page.locator('.market-mobile-bottom-item').filter({ hasText: '采购' }).click()
    await expect(page.getByRole('heading', { name: '采购计划' }).first()).toBeVisible()
    expect(requestedUrls.some((requestUrl) => /\/src\/components\/MenuPlanPanel\.vue|\/assets\/MenuPlanPanel-/.test(requestUrl))).toBe(true)
  })

  test('移动工作区行情、提醒、采购三主流程可切换', async ({ page, request }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await seedAdminSession(page, request)
    const apiRequests: string[] = []
    page.on('request', (apiRequest) => {
      const requestUrl = apiRequest.url()
      if (requestUrl.includes('/api/')) {
        apiRequests.push(requestUrl)
      }
    })
    await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })

    await expect(page.getByTestId('market-mobile-list')).toBeVisible({ timeout: 45_000 })
    await page.locator('.market-mobile-bottom-item').filter({ hasText: '提醒' }).click()
    await expect(page.getByText('价格提醒').first()).toBeVisible()

    await page.locator('.market-mobile-bottom-item').filter({ hasText: '采购' }).click()
    await expect(page.getByRole('heading', { name: '采购计划' }).first()).toBeVisible()
    await expectNoHorizontalOverflow(page)
    expect(apiRequests.some((requestUrl) => requestUrl.includes('/api/sales/decision-content'))).toBe(false)
  })

  test('真实 MySQL 商品接口可返回当前规格商品并打开走势接口', async ({ request }) => {
    const authSession = await loginAsAdmin(request)
    const headers = { Authorization: `Bearer ${authSession.access_token}` }
    const optionsResponse = await request.get(`${backendURL}/api/product/options`, {
      headers,
      params: { keyword: '三黄鸡', limit: 20 },
      timeout: 70_000,
    })
    expect(optionsResponse.ok()).toBeTruthy()
    const optionsPayload = await optionsResponse.json()
    const product = (optionsPayload.items ?? []).find((item: { price_identity_key?: string; price_identity_label?: string }) => (
      String(item.price_identity_label || '').includes('三黄鸡')
    ))
    expect(product).toBeTruthy()

    const trendResponse = await request.get(`${backendURL}/api/product/${encodeURIComponent(product.price_identity_key)}/trend`, {
      headers,
      params: { mode: 'cross_market' },
      timeout: 70_000,
    })
    expect(trendResponse.ok()).toBeTruthy()
    const trendPayload = await trendResponse.json()
    expect(Array.isArray(trendPayload.items)).toBeTruthy()
  })
})
