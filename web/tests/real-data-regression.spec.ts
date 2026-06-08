import type { APIRequestContext, Page } from '@playwright/test'
import { expect, test } from '@playwright/test'

import { backendURL } from '../playwright.shared'
import { PROCUREMENT_AUTH_STORAGE_KEY } from './helpers/authSessionStorage'

const API_BASE_URL = backendURL
const AUTH_STORAGE_KEY = PROCUREMENT_AUTH_STORAGE_KEY
const PRODUCT_OPTIONS_STORAGE_KEY = 'battel.product-options.cache.v3'
const PRODUCT_SUMMARY_STORAGE_KEY = 'battel.product-summary.cache.v3'
const PRODUCT_TREND_STORAGE_KEY = 'battel.product-trend.cache.v3'
const DEFAULT_CONTEXT_KEY = JSON.stringify({
  province: '',
  city: '',
  source_name: '',
  liancai_top_category: '',
  liancai_subcategory: '',
  liancai_keyword: '',
  liancai_brand: '',
})

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

function buildTrendRequestKey(identityKey: string) {
  return JSON.stringify({ identityKey, mode: 'cross_market', siteKey: '' })
}

async function openTrendPage(page: Page, request: APIRequestContext, authHeaders: Record<string, string>, productKeyword: string) {
  const productOptions = await request.get(`${API_BASE_URL}/api/product/options`, {
    headers: authHeaders,
    params: { keyword: productKeyword, limit: 20 },
    timeout: 70_000,
  })
  expect(productOptions.ok()).toBeTruthy()
  const productOptionPayload = await productOptions.json()
  const productItems = productOptionPayload.items ?? []
  const targetProduct = productItems.find((item: { price_identity_key?: string; price_identity_label?: string }) => (
    Boolean(item.price_identity_key) && String(item.price_identity_label || '').includes(productKeyword)
  ))
  expect(targetProduct).toBeTruthy()

  const productLabel = targetProduct.price_identity_label as string
  const identityKey = targetProduct.price_identity_key as string
  const [summaryResponse, trendResponse] = await Promise.all([
    request.get(`${API_BASE_URL}/api/product/${encodeURIComponent(identityKey)}/summary`, {
      headers: authHeaders,
      timeout: 70_000,
    }),
    request.get(`${API_BASE_URL}/api/product/${encodeURIComponent(identityKey)}/trend`, {
      headers: authHeaders,
      params: { mode: 'cross_market' },
      timeout: 70_000,
    }),
  ])
  expect(summaryResponse.ok()).toBeTruthy()
  expect(trendResponse.ok()).toBeTruthy()
  const summaryPayload = await summaryResponse.json()
  const trendPayload = await trendResponse.json()
  expect(summaryPayload.item?.product_name || '').toContain(productKeyword)
  expect((trendPayload.items ?? []).length).toBeGreaterThan(0)

  await page.addInitScript(
    ([productOptionsStorageKey, productSummaryStorageKey, productTrendStorageKey, contextKey, label, options, key, trendCacheKey, summary, trendItems]) => {
      const payload: Record<string, Array<{ price_identity_label?: string }>> = {}
      payload[contextKey] = [...options].sort((left, right) => {
        const leftMatched = left.price_identity_label === label ? 0 : 1
        const rightMatched = right.price_identity_label === label ? 0 : 1
        return leftMatched - rightMatched
      })
      window.localStorage.setItem(productOptionsStorageKey, JSON.stringify(payload))
      window.localStorage.setItem(productSummaryStorageKey, JSON.stringify({ [key]: summary }))
      window.localStorage.setItem(productTrendStorageKey, JSON.stringify({ [trendCacheKey]: trendItems }))
    },
    [
      PRODUCT_OPTIONS_STORAGE_KEY,
      PRODUCT_SUMMARY_STORAGE_KEY,
      PRODUCT_TREND_STORAGE_KEY,
      DEFAULT_CONTEXT_KEY,
      productLabel,
      productItems,
      identityKey,
      buildTrendRequestKey(identityKey),
      summaryPayload.item,
      trendPayload.items ?? [],
    ] as const,
  )
  await page.goto(
    `/?mode=workspace&tab=trend&identity_key=${encodeURIComponent(identityKey)}&product_label=${encodeURIComponent(productLabel)}`,
    { waitUntil: 'domcontentloaded' },
  )
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 45_000 })
  await expect(page.locator('[data-section-id="trend"]')).toHaveClass(/active/)
  await expect(page.locator('.pcw-trend-chart-card')).toContainText(productLabel, { timeout: 45_000 })
  return { productLabel }
}

test.describe('真实数据页面回归', () => {
  let authHeaders: Record<string, string>

  test.beforeEach(async ({ page, request }) => {
    const authSession = await loginAsAdmin(request)
    authHeaders = { Authorization: `Bearer ${authSession.access_token}` }
    const productOptions = await request.get(`${API_BASE_URL}/api/product/options`, {
      headers: authHeaders,
      timeout: 70_000,
    })
    expect(productOptions.ok()).toBeTruthy()
    const productOptionPayload = await productOptions.json()
    await page.addInitScript(
      ([authStorageKey, session, productOptionsStorageKey, contextKey, options]) => {
        window.localStorage.setItem(authStorageKey, JSON.stringify(session))
        window.localStorage.setItem(productOptionsStorageKey, JSON.stringify({ [contextKey]: options }))
      },
      [
        AUTH_STORAGE_KEY,
        authSession,
        PRODUCT_OPTIONS_STORAGE_KEY,
        DEFAULT_CONTEXT_KEY,
        productOptionPayload.items ?? [],
      ] as const,
    )
  })

  test('三黄鸡趋势页展示当前 MySQL 真实莲菜网规格走势', async ({ page, request }) => {
    await openTrendPage(page, request, authHeaders, '三黄鸡')

    await expect(page.locator('.pcw-market-compare')).toContainText('莲菜网')
    await expect(page.locator('.pcw-market-compare')).toContainText('本地市场源')
  })

  test('大豆油新版趋势页显示当前 MySQL 真实本地报价与去重后的来源摘要', async ({ page, request }) => {
    await openTrendPage(page, request, authHeaders, '大豆油')

    const marketCompare = page.locator('.pcw-market-compare')
    await expect(marketCompare).toContainText('莲菜网')
    await expect(marketCompare).toContainText('本地市场源')
    await expect(marketCompare).not.toContainText('莲菜网 · 郑州莲菜网 · 莲菜网 · 本地市场源')
  })
})
