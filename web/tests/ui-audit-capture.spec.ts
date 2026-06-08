import { expect, test } from '@playwright/test'
import type { APIRequestContext } from '@playwright/test'

import { backendURL } from '../playwright.shared'
import {
  ADMIN_AUTH_STORAGE_KEY,
  LEGACY_AUTH_STORAGE_KEY,
  PROCUREMENT_AUTH_STORAGE_KEY,
  SUPPLIER_AUTH_STORAGE_KEY,
} from './helpers/authSessionStorage'

const loginAccount = process.env.BATTEL_E2E_ACCOUNT || 'admin'
const loginPassword = process.env.BATTEL_E2E_PASSWORD || 'admin123'

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

async function seedAdminSession(page: import('@playwright/test').Page, request: APIRequestContext) {
  const session = await loginAsAdmin(request)
  await page.addInitScript(([storageKey, authSession]) => {
    window.localStorage.setItem(storageKey, JSON.stringify(authSession))
  }, [PROCUREMENT_AUTH_STORAGE_KEY, session] as const)
}

async function clearAuthSessions(page: import('@playwright/test').Page) {
  await page.addInitScript((storageKeys) => {
    storageKeys.forEach((storageKey) => window.localStorage.removeItem(storageKey))
  }, [
    LEGACY_AUTH_STORAGE_KEY,
    PROCUREMENT_AUTH_STORAGE_KEY,
    SUPPLIER_AUTH_STORAGE_KEY,
    ADMIN_AUTH_STORAGE_KEY,
  ] as const)
}

async function seedPlatformAdminSession(page: import('@playwright/test').Page, request: APIRequestContext) {
  const session = await loginAsAdmin(request)
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ user: session.user }),
    })
  })
  await page.addInitScript(([storageKey, authSession]) => {
    window.localStorage.setItem(storageKey, JSON.stringify(authSession))
  }, [ADMIN_AUTH_STORAGE_KEY, session] as const)
}

async function seedSupplierSession(page: import('@playwright/test').Page, request: APIRequestContext) {
  const session = await loginAsAdmin(request)
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ user: session.user }),
    })
  })
  await page.addInitScript(([storageKey, authSession]) => {
    window.localStorage.setItem(storageKey, JSON.stringify(authSession))
  }, [SUPPLIER_AUTH_STORAGE_KEY, session] as const)
}

async function seedSupplierBackendFixtureData(page: import('@playwright/test').Page) {
  await page.route('**/api/location/options**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        provinces: ['上海市'],
        cities: ['上海市'],
        province_city_map: { 上海市: ['上海市'] },
      }),
    })
  })
  await page.route('**/api/auth/users**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 1,
            username: 'admin',
            display_name: '系统管理员',
            role: 'admin',
            supplier_id: null,
            is_active: true,
          },
          {
            id: 2,
            username: 'demo-sea-b',
            display_name: '海鲜供应站B',
            role: 'supplier',
            supplier_id: 2,
            supplier_profile: {
              supplier_id: 2,
              supplier_name: '海鲜供应站B',
              market_category: '水产类',
              channel: '微信小程序',
              market_scope: '上海市场',
              is_active: true,
            },
            is_active: true,
          },
          {
            id: 31,
            username: 'nanjing-buyer',
            display_name: '南京采购',
            role: 'procurement',
            supplier_id: null,
            procurement_supplier_ids: [1, 2],
            market_scope: '南京市场',
            is_active: true,
          },
        ],
      }),
    })
  })
  await page.route('**/api/suppliers/overview**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        summary: {
          supplier_count: 2,
          active_supplier_count: 2,
          inactive_supplier_count: 0,
          category_count: 2,
          total_quote_count: 6,
          latest_quoted_at: '2026-06-06T09:00:00',
        },
        category_items: [
          { market_category: '水产类', supplier_count: 1, active_supplier_count: 1, quote_count: 4, latest_quoted_at: '2026-06-06T09:00:00' },
          { market_category: '蔬菜类', supplier_count: 1, active_supplier_count: 1, quote_count: 2, latest_quoted_at: '2026-06-05T11:20:00' },
        ],
        recent_quotes: [
          {
            supplier_id: 2,
            supplier_name: '海鲜供应站B',
            price_identity_key: 'croaker|kg',
            price_identity_label: '大黄花鱼 | 公斤',
            product_name: '大黄花鱼',
            quote_price: 32.8,
            quote_unit: '元/公斤',
            quoted_at: '2026-06-06T09:00:00',
          },
        ],
      }),
    })
  })
  await page.route('**/api/suppliers?**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 2,
            supplier_name: '海鲜供应站B',
            contact_name: '阿海',
            contact_phone: '13900000022',
            market_scope: '上海市场',
            market_category: '水产类',
            channel: '微信小程序',
            notes: '仅供截图链稳定展示',
            is_active: true,
            account_id: 102,
            account_username: 'demo-sea-b',
            account_display_name: '海鲜供应站B',
            account_is_active: true,
            quote_count: 4,
            latest_quoted_at: '2026-06-06T09:00:00',
          },
          {
            id: 1,
            supplier_name: '鲜蔬直采A',
            contact_name: '老王',
            contact_phone: '13800000000',
            market_scope: '上海市场',
            market_category: '蔬菜类',
            channel: '微信小程序',
            notes: '稳定展示用',
            is_active: true,
            account_id: 101,
            account_username: 'demo-veg-a',
            account_display_name: '鲜蔬直采A',
            account_is_active: true,
            quote_count: 2,
            latest_quoted_at: '2026-06-05T16:20:00',
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/*/supplier-quotes**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        summary: {
          identity_key: 'croaker|kg',
          product_name: '大黄花鱼 | 公斤',
          supplier_count: 2,
          market_lowest_price: 31.8,
          market_lowest_site: '上海海鲜市场',
          market_lowest_source_name: '海鲜市场',
          market_lowest_source_tier: '本地市场源',
          market_average_price: 32.4,
          lowest_quote: 32.8,
          lowest_quote_supplier: '海鲜供应站B',
          latest_quoted_at: '2026-06-06T09:00:00',
        },
        items: [
          {
            supplier_id: 2,
            supplier_name: '海鲜供应站B',
            contact_name: '阿海',
            contact_phone: '13900000022',
            market_scope: '上海市场',
            market_category: '水产类',
            channel: '微信小程序',
            price_identity_key: 'croaker|kg',
            price_identity_label: '大黄花鱼 | 公斤',
            product_name: '大黄花鱼',
            category: '水产类',
            spec_text: '公斤',
            quote_price: 32.8,
            quote_unit: '元/公斤',
            inventory_status: '有货',
            remarks: '稳定展示用',
            quoted_by: '阿海',
            status: 'active',
            quoted_at: '2026-06-06T09:00:00',
          },
        ],
      }),
    })
  })
  await page.route('**/api/suppliers/2/quotes**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            record_id: 201,
            supplier_id: 2,
            supplier_name: '海鲜供应站B',
            contact_name: '阿海',
            contact_phone: '13900000022',
            market_scope: '上海市场',
            market_category: '水产类',
            channel: '微信小程序',
            price_identity_key: 'croaker|kg',
            price_identity_label: '大黄花鱼 | 公斤',
            product_name: '大黄花鱼',
            category: '水产类',
            spec_text: '公斤',
            quote_price: 32.8,
            quote_unit: '元/公斤',
            inventory_status: '有货',
            remarks: '稳定展示用',
            quoted_by: '阿海',
            status: 'active',
            quoted_at: '2026-06-06T09:00:00',
          },
        ],
        total: 1,
        limit: 12,
        offset: 0,
        has_more: false,
      }),
    })
  })
  await page.route('**/api/suppliers/2/quote-actions**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 301,
            supplier_id: 2,
            supplier_name: '海鲜供应站B',
            record_id: 201,
            action_type: 'quote_create',
            action_reason: '截图稳定展示',
            operator_name: '系统管理员',
            created_at: '2026-06-06T09:01:00',
            price_identity_key: 'croaker|kg',
            price_identity_label: '大黄花鱼 | 公斤',
            product_name: '大黄花鱼',
            quote_price: 32.8,
            quote_unit: '元/公斤',
            quoted_at: '2026-06-06T09:00:00',
          },
        ],
        total: 1,
        limit: 12,
        offset: 0,
        has_more: false,
      }),
    })
  })
  await page.route('**/api/suppliers/2/settlements**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 401,
            supplier_id: 2,
            supplier_name: '海鲜供应站B',
            settlement_no: 'SET-20260606-001',
            status: 'pending',
            total_amount: 3280,
            paid_amount: 0,
            unpaid_amount: 3280,
            created_at: '2026-06-06T09:05:00',
          },
        ],
        total: 1,
        limit: 12,
        offset: 0,
        has_more: false,
      }),
    })
  })
  await page.route('**/api/supplier-settlements/401**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        item: {
          id: 401,
          supplier_id: 2,
          supplier_name: '海鲜供应站B',
          settlement_no: 'SET-20260606-001',
          status: 'pending',
          total_amount: 3280,
          paid_amount: 0,
          unpaid_amount: 3280,
          created_at: '2026-06-06T09:05:00',
        },
      }),
    })
  })
}

async function seedProcurementSession(
  page: import('@playwright/test').Page,
  request: APIRequestContext,
  locationOverrides?: { province?: string; city?: string; scope?: string },
) {
  const session = await loginAsAdmin(request)
  const sessionWithLocation = {
    ...session,
    user: {
      ...session.user,
      default_province: locationOverrides?.province ?? session.user.default_province ?? null,
      default_city: locationOverrides?.city ?? session.user.default_city ?? null,
      market_scope: locationOverrides?.scope ?? session.user.market_scope ?? null,
    },
  }
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ user: sessionWithLocation.user }),
    })
  })
  await page.addInitScript(([storageKey, authSession]) => {
    window.localStorage.setItem(storageKey, JSON.stringify(authSession))
  }, [PROCUREMENT_AUTH_STORAGE_KEY, sessionWithLocation] as const)
}

async function waitForMobileRouteReady(page: import('@playwright/test').Page) {
  await expect(page.locator('.market-mobile-route-progress')).toHaveCount(0, { timeout: 10_000 })
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
  await expect(page.getByText('正在加载价格走势')).toHaveCount(0, { timeout: 60_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-trend.png', fullPage: true })

  await page.locator('[data-section-id="alerts"]').click()
  await expect(page.getByRole('heading', { name: '今日价格提醒' })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-alerts.png', fullPage: true })

  await page.locator('[data-section-id="market"]').click()
  await expect(page.getByRole('heading', { name: '市场行情' })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-market.png', fullPage: true })

  await page.locator('[data-section-id="quotes"]').click()
  await expect(page.getByRole('heading', { name: '供应商报价' })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-quotes.png', fullPage: true })

  await page.locator('[data-section-id="plan"]').click()
  await expect(page.getByTestId('pcw-menu-workspace')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByLabel('菜单文本输入')).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-plan.png', fullPage: true })

  await page.locator('[data-section-id="settings"]').click()
  await expect(page.getByRole('heading', { name: '数据同步设置' })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-workbench-settings.png', fullPage: true })
})

test('capture platform admin and supplier backend screens', async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })

  await clearAuthSessions(page)
  await page.goto('/admin', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('platform-admin-screen')).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop-platform-admin-login.png', fullPage: true })

  await seedPlatformAdminSession(page, request)
  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('button', { name: '退出登录' })).toBeVisible({ timeout: 30_000 })

  await page.getByRole('button', { name: /来源覆盖 SRC/ }).click()
  await expect(page.getByTestId('platform-source-coverage-list')).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop-platform-admin-coverage.png', fullPage: true })

  await page.goto('/supplier-backend', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('supplier-login-form')).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop-supplier-backend-login.png', fullPage: true })

  await seedSupplierBackendFixtureData(page)
  await seedSupplierSession(page, request)
  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('supplier-admin-panel')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByRole('button', { name: /海鲜供应站B/ })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-supplier-backend-suppliers.png', fullPage: true })

  await page.getByRole('button', { name: /账号管理 ACC/ }).click()
  await expect(page.getByTestId('account-admin-panel')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByTestId('account-admin-panel').getByText('demo-sea-b')).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-supplier-backend-accounts.png', fullPage: true })

  await page.getByRole('button', { name: /报价管理 QTE/ }).click()
  await expect(page.getByTestId('supplier-admin-panel')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText('报价工作台').first()).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText('海鲜供应站B').first()).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-supplier-backend-quote.png', fullPage: true })

  await page.getByRole('button', { name: /结算台账 SET/ }).click()
  await expect(page.getByText('供应商结算台账')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByTestId('settlement-selected-quotes-guide')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText('海鲜供应站B').first()).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-supplier-backend-settlement.png', fullPage: true })

  await page.getByRole('button', { name: /操作日志 LOG|操作日志/ }).click()
  await expect(page.getByText('最近操作日志')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText('海鲜供应站B').first()).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-supplier-backend-logs.png', fullPage: true })
})

test('capture desktop supplier portal pages', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await clearAuthSessions(page)

  await page.goto('/supplier-portal', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('supplier-portal-screen')).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop-supplier-portal-login.png', fullPage: true })

  await page.getByPlaceholder('账号').fill(loginAccount)
  await page.getByPlaceholder('密码').fill(loginPassword)
  const loginResponse = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200)
  await page.getByTestId('auth-login-button').click()
  await loginResponse
  await expect(page.getByTestId('auth-session-status')).toContainText('系统管理员', { timeout: 30_000 })
  await page.screenshot({ path: 'test-results/desktop-supplier-portal-panel.png', fullPage: true })
})

test('capture mobile landing and workflow screens', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })

  const shanghaiProductKey = 'meicai-h5-class-products::美菜网-香菜普通-3177-斤-上海美菜网'
  const shanghaiProductLabel = '香菜 普通 | 3177 | 斤'
  const shanghaiMarketSummaryItem = {
    price_identity_key: shanghaiProductKey,
    product_name: shanghaiProductLabel,
    group_name: '美菜网',
    category: '蔬菜类',
    liancai_top_category: '蔬菜类',
    liancai_subcategory: '叶菜类',
    average_price: 5.41,
    lowest_price: 5.27,
    highest_price: 5.58,
    lowest_price_site: '上海美菜网',
    highest_price_site: '上海美菜网',
    market_count: 1,
    site_count: 1,
    price_observation_count: 3,
    latest_captured_at: '2026-06-06T08:00:00',
    price_unit_basis: '元/公斤',
    region_label: '上海市',
    source_names: '美菜网',
    source_display_names: '美菜网',
    image_url: 'https://example.test/shanghai-coriander.jpg',
  }
  const shanghaiProductOption = {
    price_identity_key: shanghaiProductKey,
    price_identity_label: shanghaiProductLabel,
    site_count: 1,
    price_observation_count: 3,
    latest_captured_at: '2026-06-06T08:00:00',
    source_name: '美菜网',
    source_category: '蔬菜类',
    liancai_top_category: '蔬菜类',
    liancai_subcategory: '叶菜类',
    image_url: 'https://example.test/shanghai-coriander.jpg',
  }
  const shanghaiTrendRows = [
    {
      site_name: '上海美菜网',
      source_name: '美菜网',
      source_tier: '主价格源',
      source_url: 'https://example.test/meicai/shanghai/coriander',
      liancai_top_category: '蔬菜类',
      liancai_subcategory: '叶菜类',
      market_name: '上海美菜网',
      region_label: '上海市',
      province: '上海市',
      city: '上海市',
      current_price: 5.27,
      captured_at: '2026-06-04T08:00:00',
      product_name: shanghaiProductLabel,
      trend_series_name: '上海美菜网',
      trend_series_key: '上海美菜网',
      trend_meta_label: '上海美菜网 5.27',
    },
    {
      site_name: '上海美菜网',
      source_name: '美菜网',
      source_tier: '主价格源',
      source_url: 'https://example.test/meicai/shanghai/coriander',
      liancai_top_category: '蔬菜类',
      liancai_subcategory: '叶菜类',
      market_name: '上海美菜网',
      region_label: '上海市',
      province: '上海市',
      city: '上海市',
      current_price: 5.41,
      captured_at: '2026-06-05T08:00:00',
      product_name: shanghaiProductLabel,
      trend_series_name: '上海美菜网',
      trend_series_key: '上海美菜网',
      trend_meta_label: '上海美菜网 5.41',
    },
    {
      site_name: '上海美菜网',
      source_name: '美菜网',
      source_tier: '主价格源',
      source_url: 'https://example.test/meicai/shanghai/coriander',
      liancai_top_category: '蔬菜类',
      liancai_subcategory: '叶菜类',
      market_name: '上海美菜网',
      region_label: '上海市',
      province: '上海市',
      city: '上海市',
      current_price: 5.58,
      captured_at: '2026-06-06T08:00:00',
      product_name: shanghaiProductLabel,
      trend_series_name: '上海美菜网',
      trend_series_key: '上海美菜网',
      trend_meta_label: '上海美菜网 5.58',
    },
  ]

  await page.route('**/api/market/summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [shanghaiMarketSummaryItem],
        total: 1,
        limit: 200,
        offset: 0,
        has_more: false,
      }),
    })
  })
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [shanghaiProductOption],
        total: 1,
        limit: 40,
        offset: 0,
        has_more: false,
      }),
    })
  })
  await page.route(`**/api/product/${encodeURIComponent(shanghaiProductKey)}/summary**`, async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        item: {
          price_identity_key: shanghaiProductKey,
          price_identity_label: shanghaiProductLabel,
          product_name: shanghaiProductLabel,
          current_lowest_price: 5.27,
          current_highest_price: 5.58,
          average_price: 5.42,
          current_lowest_site: '上海美菜网',
          current_highest_site: '上海美菜网',
          site_count: 1,
          market_count: 1,
          price_observation_count: 3,
          latest_captured_at: '2026-06-06T08:00:00',
          region_label: '上海市',
          source_names: '美菜网',
          source_display_names: '美菜网',
          price_span: 0.31,
          price_unit_basis: '元/公斤',
        },
      }),
    })
  })
  await page.route(`**/api/product/${encodeURIComponent(shanghaiProductKey)}/trend**`, async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        mode: 'cross_market',
        items: shanghaiTrendRows,
      }),
    })
  })

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-landing-first-screen.png', fullPage: false })

  await page.getByRole('button', { name: '账号登录' }).click()
  await expect(page.getByRole('dialog', { name: '账号登录' })).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-procurement-login-sheet.png', fullPage: false })

  await page.keyboard.press('Escape')
  await seedProcurementSession(page, request, { province: '上海市', city: '上海市', scope: '上海市场' })
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-landing-authenticated.png', fullPage: false })

  await page.getByTestId('enter-workspace-button').click()
  await expect(page.getByTestId('market-mobile-card').first()).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/mobile-market-summary-workspace.png', fullPage: false })

  await page.getByTestId('market-mobile-card').first().click()
  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 30_000 })
  await waitForMobileRouteReady(page)
  await expect(page.locator('.trend-content-shell')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('.trend-mobile-detail-hero')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('.trend-mobile-chart-title')).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: 'test-results/mobile-trend-workspace.png', fullPage: false })

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '菜价' }).click()
  await expect(page.getByTestId('market-mobile-list')).toBeVisible({ timeout: 30_000 })
  await waitForMobileRouteReady(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '提醒' }).click()
  await expect(page.getByText('价格提醒').first()).toBeVisible()
  await waitForMobileRouteReady(page)
  await page.screenshot({ path: 'test-results/mobile-alerts-workspace.png', fullPage: false })

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '采购' }).click()
  await expect(page.getByLabel('菜单文本输入')).toBeVisible()
  await waitForMobileRouteReady(page)
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
