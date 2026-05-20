import { expect, test } from '@playwright/test'

test('PC 汇总行情首屏在 market summary 慢时也显示商品选项数据', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  const requests: string[] = []
  await page.route('**/api/market/summary**', async (route) => {
    requests.push(route.request().url())
    // 模拟真实问题：重型汇总接口长时间不返回。
  })
  await page.route('**/api/product/options**', async (route) => {
    requests.push(route.request().url())
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'liancai-cream|902',
            price_identity_label: '伊利淡奶油1L*6盒 | 伊利 | 902',
            site_count: 1,
            price_observation_count: 1,
            latest_captured_at: '2026-05-11T15:58:53',
            source_name: '莲菜网',
            source_category: '乳品烘焙',
            liancai_top_category: '乳品烘焙',
            liancai_subcategory: '其他原料类',
            liancai_keyword: '奶油',
            liancai_brand_name: '伊利',
            image_url: 'https://example.test/cream.jpg',
          },
        ],
        total: null,
        limit: 300,
        offset: 0,
        has_more: true,
      }),
    })
  })

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByText('今日行情列表')).toBeVisible()
  await expect(page.getByTestId('pcw-summary-data-row').first()).toBeVisible({ timeout: 10_000 })
  await expect(page.getByText('伊利淡奶油1L*6盒').first()).toBeVisible()
  await expect(page.getByTestId('pcw-summary-empty-row')).toHaveCount(0)
  expect(requests.some((url) => url.includes('/api/product/options'))).toBeTruthy()
})

test('PC 汇总行情切换莲菜分类时不等待慢 summary，先用商品选项展示', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  const requests: string[] = []

  await page.route('**/api/liancai/category-summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [{ liancai_top_category: '乳品烘焙', liancai_subcategory: '其他原料类', product_count: 1 }],
      }),
    })
  })
  await page.route('**/api/liancai/facets**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ keywords: ['奶油'], brands: ['伊利'] }) })
  })
  await page.route('**/api/market/summary**', async (route) => {
    requests.push(route.request().url())
    const url = new URL(route.request().url())
    if (url.searchParams.get('liancai_top_category') === '乳品烘焙') {
      // 分类切换后的重型汇总接口卡住，页面仍应先显示 product/options 首包。
      return
    }
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, limit: 500, offset: 0, has_more: false }) })
  })
  await page.route('**/api/product/options**', async (route) => {
    requests.push(route.request().url())
    const url = new URL(route.request().url())
    const isFiltered = url.searchParams.get('liancai_top_category') === '乳品烘焙'
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: isFiltered
          ? [{
              price_identity_key: 'liancai-cream|902',
              price_identity_label: '伊利淡奶油1L*6盒 | 伊利 | 902',
              site_count: 1,
              price_observation_count: 1,
              latest_captured_at: '2026-05-11T15:58:53',
              source_name: '莲菜网',
              source_category: '乳品烘焙',
              liancai_top_category: '乳品烘焙',
              liancai_subcategory: '其他原料类',
              liancai_keyword: '奶油',
              liancai_brand_name: '伊利',
            }]
          : [],
        total: null,
        limit: 300,
        offset: 0,
        has_more: false,
      }),
    })
  })

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByText('今日行情列表')).toBeVisible()
  await page.getByRole('button', { name: /全部种类/ }).click()
  await page.getByRole('menuitemradio', { name: /^乳品烘焙$/ }).click()

  await expect(page.getByTestId('pcw-summary-data-row').first()).toBeVisible({ timeout: 10_000 })
  await expect(page.getByText('伊利淡奶油1L*6盒').first()).toBeVisible()
  await expect(page.getByTestId('pcw-summary-empty-row')).toHaveCount(0)
  expect(requests.some((url) => url.includes('/api/product/options') && url.includes('liancai_top_category'))).toBeTruthy()
})


test('PC 汇总行情查看报价会进入对应商品的单品趋势', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  const trendRequests: string[] = []

  await page.route('**/api/market/summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            product_name: '番茄沙司10g*300袋',
            price_identity_key: 'sauce|898',
            average_price: 4.21,
            lowest_price: 0.15,
            highest_price: 12.34,
            market_count: 2,
            site_count: 2,
            latest_captured_at: '2026-05-17T08:00:00',
            source_names: '莲菜网,供应平台',
            liancai_top_category: '西餐',
          },
        ],
        total: 1,
        limit: 500,
        offset: 0,
        has_more: false,
      }),
    })
  })
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'sauce|898',
            price_identity_label: '番茄沙司10g*300袋 | 898',
            site_count: 2,
            price_observation_count: 2,
          },
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
            product_name: '番茄沙司10g*300袋 | 898',
            trend_series_key: 'market-a',
            trend_series_name: '市场 A',
            market_name: '市场 A',
            current_price: 4.21,
            captured_at: '2026-05-17T08:00:00',
          },
        ],
      }),
    })
  })

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByText('今日行情列表')).toBeVisible()
  const summaryRow = page.getByTestId('pcw-summary-data-row').first()
  await expect(summaryRow).toContainText('番茄沙司10g*300袋', { timeout: 10_000 })

  await summaryRow.getByRole('button', { name: '查看报价' }).click()

  await expect(page.locator('[data-section-id="trend"]')).toHaveClass(/active/)
  await expect(page.getByRole('heading', { name: '单品趋势' })).toBeVisible()
  await expect.poll(() => trendRequests).toContain('sauce|898')
  await expect(page.getByTestId('pcw-trend-product-filter')).toContainText('番茄沙司10g*300袋')
  await expect.poll(() => new URL(page.url()).searchParams.get('tab')).toBe('trend')
  await expect.poll(() => new URL(page.url()).searchParams.get('identity_key')).toBe('sauce|898')
})
