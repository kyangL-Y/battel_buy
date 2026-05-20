import type { APIRequestContext, Page } from '@playwright/test'
import { expect, test } from '@playwright/test'

const API_BASE_URL = 'http://127.0.0.1:8000'
const AUTH_STORAGE_KEY = 'battel.auth.session'
const PRODUCT_OPTIONS_STORAGE_KEY = 'battel.product-options.cache.v3'
const PRODUCT_SUMMARY_STORAGE_KEY = 'battel.product-summary.cache.v3'
const PRODUCT_TREND_STORAGE_KEY = 'battel.product-trend.cache.v3'
const DEFAULT_CONTEXT_KEY = JSON.stringify({ province: '', city: '' })

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

async function openTrendPage(page: Page, request: APIRequestContext, productLabel: string) {
  const productOptions = await request.get(`${API_BASE_URL}/api/product/options`, { timeout: 70_000 })
  expect(productOptions.ok()).toBeTruthy()
  const productOptionPayload = await productOptions.json()
  const productItems = productOptionPayload.items ?? []
  const targetProduct = productItems.find((item: { price_identity_label?: string }) => item.price_identity_label === productLabel)
  expect(targetProduct).toBeTruthy()

  const identityKey = targetProduct.price_identity_key as string
  const [summaryResponse, trendResponse] = await Promise.all([
    request.get(`${API_BASE_URL}/api/product/${encodeURIComponent(identityKey)}/summary`, { timeout: 70_000 }),
    request.get(`${API_BASE_URL}/api/product/${encodeURIComponent(identityKey)}/trend`, {
      params: { mode: 'cross_market' },
      timeout: 70_000,
    }),
  ])
  expect(summaryResponse.ok()).toBeTruthy()
  expect(trendResponse.ok()).toBeTruthy()
  const summaryPayload = await summaryResponse.json()
  const trendPayload = await trendResponse.json()

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
  await page.goto('/?mode=workspace&tab=trend', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 45_000 })
  await expect(page.locator('[data-section-id="trend"]')).toHaveClass(/active/)
  await expect(page.locator('.pcw-trend-chart-card')).toContainText(productLabel, { timeout: 45_000 })
}

test.describe('真实数据页面回归', () => {
  test.beforeEach(async ({ page, request }) => {
    const productOptions = await request.get(`${API_BASE_URL}/api/product/options`, { timeout: 70_000 })
    expect(productOptions.ok()).toBeTruthy()
    const productOptionPayload = await productOptions.json()
    const authSession = await loginAsAdmin(request)
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

  test('三黄鸡趋势页同时展示官方参考源与主价格源', async ({ page, request }) => {
    await openTrendPage(page, request, '三黄鸡 | 公斤')

    await expect(page.locator('.pcw-market-compare')).toContainText('官方参考源')
    await expect(page.locator('.pcw-market-compare')).toContainText('主价格源')
    await expect(page.locator('.pcw-market-compare')).toContainText('重点农产品平台')
    await expect(page.locator('.pcw-market-compare')).toContainText('PFSC')
  })

  test('一级豆油新版趋势页显示真实本地报价与去重后的公开来源摘要', async ({ page, request }) => {
    await openTrendPage(page, request, '一级豆油 | 公斤')

    const marketCompare = page.locator('.pcw-market-compare')
    await expect(marketCompare).toContainText('PFSC')
    await expect(marketCompare).toContainText('主价格源')
    await expect(marketCompare).not.toContainText('PFSC · 定西 · PFSC · 主价格源')
  })
})
