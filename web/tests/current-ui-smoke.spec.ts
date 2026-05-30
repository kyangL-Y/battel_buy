import { expect, test } from '@playwright/test'
import type { APIRequestContext, Page } from '@playwright/test'
import { expectNoHorizontalOverflow } from './helpers/layout'

const API_BASE_URL = 'http://127.0.0.1:8000'
const AUTH_STORAGE_KEY = 'battel.auth.session.procurement'

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
    await expect(page.getByRole('heading', { name: /先登录/ })).toBeVisible()
    await expect(page.locator('.platform-choice-login-card')).toContainText('采购账号登录')
    await expect(page.getByTestId('supplier-choice-button')).toBeVisible()

    const loginForm = page.locator('.platform-choice-login-form')
    await loginForm.getByPlaceholder('请输入采购账号').fill('admin')
    await loginForm.getByPlaceholder('请输入密码').fill('admin123')
    await loginForm.getByRole('button', { name: '登录采购端' }).click()

    await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 45_000 })
    await expect(page).toHaveURL(/mode=workspace/)
    await expectNoHorizontalOverflow(page)
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
    await expect(page.getByRole('heading', { name: '真实市场行情监控' })).toBeVisible()

    await page.locator('[data-section-id="quotes"]').click()
    await expect(page.getByRole('heading', { name: '真实报价记录入库台' })).toBeVisible()

    await page.locator('[data-section-id="plan"]').click()
    await expect(page.getByTestId('pcw-menu-workspace')).toBeVisible()

    await page.locator('[data-section-id="settings"]').click()
    await expect(page.getByRole('heading', { name: '真实来源配置与同步状态' })).toBeVisible()
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
    await expect(page.getByText('先登录，再看本团队行情。')).toBeVisible()
    await expect(page.getByText('采购账号登录').first()).toBeVisible()
    await expect(page.getByText('供应商入口').first()).toBeVisible()

    await page.getByRole('button', { name: '登录采购端' }).click()
    await expect(page.getByRole('dialog', { name: '采购端登录' })).toBeVisible()
    await page.getByPlaceholder('采购账号 / 管理员账号').fill('admin')
    await page.getByPlaceholder('请输入密码').fill('admin123')
    await page.getByRole('dialog', { name: '采购端登录' }).getByRole('button', { name: '登录采购端' }).click()

    await expect(page.getByTestId('market-mobile-list')).toBeVisible({ timeout: 45_000 })
    await expect(page).toHaveURL(/mode=workspace/)
    await expectNoHorizontalOverflow(page)
  })

  test('移动工作区行情、预警、采购三主流程可切换', async ({ page, request }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await seedAdminSession(page, request)
    await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })

    await expect(page.getByTestId('market-mobile-list')).toBeVisible({ timeout: 45_000 })
    await page.locator('.market-mobile-bottom-item').filter({ hasText: '预警' }).click()
    await expect(page.getByText('价格预警').first()).toBeVisible()

    await page.locator('.market-mobile-bottom-item').filter({ hasText: '采购' }).click()
    await expect(page.getByRole('heading', { name: '采购表单' })).toBeVisible()
    await expectNoHorizontalOverflow(page)
  })

  test('真实 MySQL 商品接口可返回当前规格商品并打开走势接口', async ({ request }) => {
    const optionsResponse = await request.get(`${API_BASE_URL}/api/product/options`, {
      params: { keyword: '三黄鸡', limit: 20 },
      timeout: 70_000,
    })
    expect(optionsResponse.ok()).toBeTruthy()
    const optionsPayload = await optionsResponse.json()
    const product = (optionsPayload.items ?? []).find((item: { price_identity_key?: string; price_identity_label?: string }) => (
      String(item.price_identity_label || '').includes('三黄鸡')
    ))
    expect(product).toBeTruthy()

    const trendResponse = await request.get(`${API_BASE_URL}/api/product/${encodeURIComponent(product.price_identity_key)}/trend`, {
      params: { mode: 'cross_market' },
      timeout: 70_000,
    })
    expect(trendResponse.ok()).toBeTruthy()
    const trendPayload = await trendResponse.json()
    expect(Array.isArray(trendPayload.items)).toBeTruthy()
  })
})
