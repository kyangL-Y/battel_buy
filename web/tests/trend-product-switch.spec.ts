import { expect, test } from '@playwright/test'

test('单品趋势切换商品会重新请求走势且过滤非商品选项', async ({ page }) => {
  const trendRequests: string[] = []

  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          { price_identity_key: 'potato|kg', price_identity_label: '土豆 | 公斤', site_count: 2, price_observation_count: 2 },
          { price_identity_key: 'cabbage|kg', price_identity_label: '白菜 | 公斤', site_count: 2, price_observation_count: 2 },
          { price_identity_key: '/copy', price_identity_label: '/copy', site_count: 1, price_observation_count: 1 },
          { price_identity_key: '产区调整影响', price_identity_label: '产区调整影响', site_count: 1, price_observation_count: 1 },
          { price_identity_key: 'empty|kg', price_identity_label: '空来源 | 公斤', site_count: 0, price_observation_count: 5 },
          { price_identity_key: 'no-price|kg', price_identity_label: '无报价 | 公斤', site_count: 1, price_observation_count: 0 },
        ],
      }),
    })
  })
  await page.route('**/api/product/*/summary**', async (route) => {
    const url = new URL(route.request().url())
    const parts = url.pathname.split('/')
    const identityKey = decodeURIComponent(parts[parts.length - 2] || '')
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ item: { price_identity_key: identityKey, product_name: identityKey, site_count: 2 } }),
    })
  })
  await page.route('**/api/product/*/trend**', async (route) => {
    const url = new URL(route.request().url())
    const parts = url.pathname.split('/')
    const identityKey = decodeURIComponent(parts[parts.length - 2] || '')
    trendRequests.push(identityKey)
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        mode: 'cross_market',
        items: [
          {
            price_identity_key: identityKey,
            product_name: identityKey,
            trend_series_key: 'market-a',
            trend_series_name: '市场 A',
            market_name: '市场 A',
            current_price: identityKey === 'cabbage|kg' ? 3.2 : 2.1,
            captured_at: '2026-04-10T10:00:00',
          },
        ],
      }),
    })
  })

  await page.goto('/?mode=workspace&tab=trend', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('[data-section-id="trend"]')).toHaveClass(/active/)
  const productFilter = page.getByTestId('pcw-trend-product-filter')
  await expect(productFilter).toContainText('土豆 | 公斤', { timeout: 30_000 })
  await productFilter.getByRole('button').first().click()
  await expect(page.getByRole('menuitemradio', { name: '/copy' })).toHaveCount(0)
  await expect(page.getByRole('menuitemradio', { name: '产区调整影响' })).toHaveCount(0)
  await expect(page.getByRole('menuitemradio', { name: '空来源 | 公斤' })).toHaveCount(0)
  await expect(page.getByRole('menuitemradio', { name: '无报价 | 公斤' })).toHaveCount(0)
  await page.getByRole('menuitemradio', { name: '白菜 | 公斤' }).click()

  await expect.poll(() => trendRequests).toContain('cabbage|kg')
  await expect(page.locator('.pcw-trend-chart-card')).toContainText('白菜 | 公斤')
})
