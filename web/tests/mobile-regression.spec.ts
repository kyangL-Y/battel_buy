import { expect, test } from '@playwright/test'

import { expectNoHorizontalOverflow } from './helpers/layout'

test.setTimeout(90_000)

async function seedProcurementSession(page: import('@playwright/test').Page) {
  const procurementUser = {
    id: 1,
    username: 'mobile-buyer',
    display_name: '移动采购',
    role: 'procurement',
    supplier_id: null,
    is_active: true,
  }
  const authSession = {
    access_token: 'mobile-procurement-token',
    token_type: 'Bearer',
    expires_in: 3600,
    user: procurementUser,
  }
  await page.addInitScript((session) => {
    window.localStorage.setItem('battel.auth.session.procurement', JSON.stringify(session))
  }, authSession)
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ user: procurementUser }),
    })
  })
}

async function expectUsableMobileLandingLayout(page: import('@playwright/test').Page) {
  const landingGeometry = await page.evaluate(() => {
    const viewportWidth = window.innerWidth
    const readBox = (selector: string) => {
      const element = document.querySelector(selector)
      if (!element) {
        return null
      }
      const box = element.getBoundingClientRect()
      return { top: box.top, bottom: box.bottom, width: box.width, height: box.height }
    }
    const commandButtonHeights = Array.from(document.querySelectorAll('.mobile-redesign-command-grid button'))
      .map((element) => element.getBoundingClientRect().height)
    const touchTargets = Array.from(document.querySelectorAll([
      '.mobile-redesign-login-button',
      '.mobile-redesign-search button',
      '.mobile-redesign-command-grid button',
      '.mobile-redesign-priority-card',
      '.mobile-redesign-nav .market-mobile-bottom-item',
    ].join(','))).map((element) => {
      const box = element.getBoundingClientRect()
      return { width: box.width, height: box.height, label: element.textContent?.trim() || element.getAttribute('aria-label') || '' }
    })
    return {
      viewportWidth,
      heroBox: readBox('.mobile-redesign-hero-card'),
      searchBox: readBox('.mobile-redesign-search'),
      navBox: readBox('.mobile-redesign-nav'),
      firstSectionBox: readBox('.mobile-redesign-main .mobile-redesign-section'),
      priorityCardBox: readBox('.mobile-redesign-priority-card'),
      commandButtonHeights,
      touchTargets,
    }
  })

  expect(landingGeometry.heroBox?.width).toBeGreaterThanOrEqual(landingGeometry.viewportWidth - 32)
  expect(landingGeometry.heroBox?.height).toBeLessThanOrEqual(650)
  expect(landingGeometry.searchBox?.height).toBeGreaterThanOrEqual(60)
  expect(landingGeometry.navBox?.height).toBeGreaterThanOrEqual(66)
  expect(landingGeometry.firstSectionBox?.height).toBeGreaterThanOrEqual(140)
  expect(landingGeometry.firstSectionBox?.top).toBeLessThanOrEqual((landingGeometry.navBox?.top ?? 0) - 71)
  expect(landingGeometry.priorityCardBox?.top).toBeLessThan((landingGeometry.navBox?.top ?? 0) - 44)
  expect(landingGeometry.commandButtonHeights.length).toBe(3)
  for (const commandButtonHeight of landingGeometry.commandButtonHeights) {
    expect(commandButtonHeight).toBeGreaterThanOrEqual(72)
  }
  expect(landingGeometry.touchTargets.length).toBeGreaterThanOrEqual(10)
  for (const touchTarget of landingGeometry.touchTargets) {
    expect.soft(touchTarget.height, `${touchTarget.label} height`).toBeGreaterThanOrEqual(44)
    expect.soft(touchTarget.width, `${touchTarget.label} width`).toBeGreaterThanOrEqual(44)
  }
}

test('移动端未登录时只在用户点定位后切到本地市场', async ({ page }) => {
  let locationSuggestionRequestCount = 0
  await page.route('**/api/location/suggest**', async (route) => {
    locationSuggestionRequestCount += 1
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        matched: true,
        province: '河南省',
        city: '郑州',
        label: '郑州',
        source: 'browser_geolocation',
        source_label: '浏览器定位',
        confidence: 0.86,
        raw_location: '河南省 郑州市',
      }),
    })
  })

  await page.goto('/', { waitUntil: 'domcontentloaded' })

  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await expect(page.locator('.mobile-redesign-location')).toContainText('河南本地市场')
  expect(locationSuggestionRequestCount).toBe(0)

  await page.locator('.mobile-redesign-location').click()
  await expect(page.getByRole('button', { name: '按定位选择' })).toBeVisible()
  await page.getByRole('button', { name: '按定位选择' }).click()

  await expect(page.locator('.mobile-redesign-location')).toContainText('郑州')
  await expect(page.getByText('浏览器定位 · 郑州')).toBeVisible()
  expect(locationSuggestionRequestCount).toBe(1)
  await expectNoHorizontalOverflow(page)
})

test('移动端选择上海市后汇总行情按上海市场请求', async ({ page }) => {
  await seedProcurementSession(page)
  const summaryRequests: string[] = []
  await page.route('**/api/location/options', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        provinces: ['河南省', '上海市'],
        cities: ['郑州市', '上海市'],
        province_city_map: {
          河南省: ['郑州市'],
          上海市: ['上海市'],
        },
      }),
    })
  })
  await page.route('**/api/market/summary**', async (route) => {
    summaryRequests.push(route.request().url())
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'sh-greens',
            product_name: '上海青 | 公斤',
            lowest_price: 3.8,
            highest_price: 3.8,
            average_price: 3.8,
            market_count: 1,
            site_count: 1,
            lowest_price_site: '上海江桥',
            highest_price_site: '上海江桥',
            region_label: '上海市',
            latest_captured_at: '2026-06-06T08:00:00',
          },
        ],
        total: 1,
        limit: 200,
        offset: 0,
        has_more: false,
      }),
    })
  })

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await page.locator('.mobile-redesign-location').click()
  await page.getByRole('button', { name: '上海市' }).click()
  await expect(page.locator('.mobile-redesign-location')).toContainText('上海市')
  await page.getByTestId('enter-workspace-button').click()

  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  await expect.poll(() => summaryRequests.some((url) => {
    const params = new URL(url).searchParams
    return params.get('province') === '上海市' && params.get('city') === '上海市'
  })).toBe(true)
  await expect(page.getByTestId('market-mobile-list')).toContainText('上海青')
})

test('移动端账号绑定地区时定位和手选都不能覆盖账号市场', async ({ page }) => {
  const lockedUser = {
    id: 31,
    username: 'nanjing-buyer',
    display_name: '南京采购',
    role: 'procurement',
    market_scope: '南京市场',
    default_province: '江苏省',
    default_city: '南京',
    supplier_id: null,
    is_active: true,
    created_at: '2026-05-01T00:00:00',
    updated_at: '2026-05-01T00:00:00',
  }
  let locationSuggestionRequestCount = 0

  await page.addInitScript((authSession) => {
    window.localStorage.setItem('battel.auth.session.procurement', JSON.stringify(authSession))
  }, {
    access_token: 'locked-location-token',
    token_type: 'Bearer',
    expires_in: 3600,
    user: lockedUser,
  })
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ user: lockedUser }),
    })
  })
  await page.route('**/api/location/suggest**', async (route) => {
    locationSuggestionRequestCount += 1
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        matched: true,
        province: '河南省',
        city: '郑州',
        label: '郑州',
        source: 'browser_geolocation',
        source_label: '浏览器定位',
        confidence: 0.86,
        raw_location: '河南省 郑州市',
      }),
    })
  })

  await page.goto('/', { waitUntil: 'domcontentloaded' })

  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await expect(page.locator('.mobile-redesign-location')).toContainText('南京')
  await expect(page.getByText('当前账号已绑定地区')).toBeVisible()
  await page.locator('.mobile-redesign-location').click()
  await expect(page.getByText('账号绑定地区')).toBeVisible()
  await expect(page.getByRole('button', { name: '按定位选择' })).toHaveCount(0)
  await expect(page.locator('.mobile-redesign-location-panel button').first()).toBeDisabled()
  expect(locationSuggestionRequestCount).toBe(0)
  await expectNoHorizontalOverflow(page)
})

test('移动端从提醒直达页可继续切换其他工作区', async ({ page }) => {
  await seedProcurementSession(page)
  await page.goto('/?mode=workspace&tab=alerts', { waitUntil: 'domcontentloaded' })

  await expect(page.getByText('价格提醒').first()).toBeVisible()
  await expect(page).toHaveURL(/tab=alerts/)
  await expectNoHorizontalOverflow(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '菜价' }).click()
  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  await expect(page).toHaveURL(/tab=summary/)
  await expectNoHorizontalOverflow(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '提醒' }).click()
  await expect(page.getByText('价格提醒').first()).toBeVisible()
  await expect(page).toHaveURL(/tab=alerts/)
  await expectNoHorizontalOverflow(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '采购' }).click()
  await expect(page.getByLabel('菜单文本输入')).toBeVisible()
  await expect(page).toHaveURL(/tab=menu/)
  await expectNoHorizontalOverflow(page)
})

test('移动端首页改为卡片流且底部主导航进入采购登录门禁', async ({ page }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' })

  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await expect(page.locator('.market-mobile-summary-table')).toHaveCount(0)
  await expect(page.locator('.market-mobile-pc-table')).toHaveCount(0)
  await expect(page.locator('.market-mobile-pc-filter.main')).toHaveCount(0)
  await expect(page.getByTestId('mobile-spotlight-feed')).toBeVisible()
  await expect(page.getByTestId('mobile-source-groups')).toBeVisible()
  await expectUsableMobileLandingLayout(page)
  await expectNoHorizontalOverflow(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '菜价' }).click()
  await expect(page.getByRole('dialog', { name: '账号登录' })).toBeVisible()
  await expect(page.locator('.market-mobile-tab-strip')).toHaveCount(0)
  await expectNoHorizontalOverflow(page)
})

test('移动端供应商入口只保留账号登录和找回密码', async ({ page }) => {
  const submittedPayloads: unknown[] = []
  await page.route('**/api/supplier-registration-requests', async (route) => {
    submittedPayloads.push(route.request().postDataJSON())
    await route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({ detail: '手机号格式错误' }),
    })
  })

  await page.goto('/supplier-portal', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('supplier-portal-screen')).toBeVisible()
  await expect(page.getByTestId('supplier-login-form')).toBeVisible()
  await expect(page.getByText('账号由采购分配')).toBeVisible()
  await expect(page.getByRole('button', { name: '显示密码' })).toBeVisible()
  await expect(page.getByRole('button', { name: '忘记密码' })).toBeVisible()
  await expect(page.getByRole('button', { name: '注册' })).toHaveCount(0)
  await expectNoHorizontalOverflow(page)
  expect(submittedPayloads).toEqual([])
})

test('移动端汇总行情在重型汇总接口未返回前用商品选项先展示首屏数据', async ({ page }) => {
  await seedProcurementSession(page)
  await page.route('**/api/market/summary**', async () => {
    // 模拟真实问题：汇总接口长时间不返回。
  })
  await page.route('**/api/product/options**', async (route) => {
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
            liancai_subcategory: '其他原料类',
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
  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  await expect(page.getByTestId('market-mobile-card').first()).toBeVisible({ timeout: 10_000 })
  await expect(page.getByTestId('market-mobile-list')).toContainText('伊利淡奶油1L*6盒')
  await expect(page.getByTestId('market-summary-empty-state')).toHaveCount(0)
})

test('移动端未登录直达汇总页会清理过期登录态且不请求行情', async ({ page }) => {
  let currentUserRequestCount = 0
  let summaryRequestCount = 0
  await page.addInitScript(() => {
    const encodeBase64Url = (value: string) => window.btoa(value)
      .replace(/=/g, '')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
    const expiredToken = [
      encodeBase64Url(JSON.stringify({ alg: 'HS256', typ: 'JWT' })),
      encodeBase64Url(JSON.stringify({ sub: '1', role: 'procurement', exp: 1 })),
      'signature',
    ].join('.')
    window.localStorage.setItem('battel.auth.session.procurement', JSON.stringify({
      access_token: expiredToken,
      token_type: 'Bearer',
      expires_in: 3600,
      user: {
        id: 1,
        username: 'expired-buyer',
        display_name: '过期采购',
        role: 'procurement',
        supplier_id: null,
        is_active: true,
      },
    }))
  })
  await page.route('**/api/auth/me', async (route) => {
    currentUserRequestCount += 1
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: '登录状态已失效，请重新登录' }),
    })
  })
  await page.route('**/api/market/summary**', async (route) => {
    summaryRequestCount += 1
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'public-summary|001',
            product_name: '公开行情商品',
            group_name: '公开行情商品',
            category: '测试分类',
            average_price: 8.8,
            lowest_price: 8.2,
            highest_price: 9.1,
            market_count: 2,
            site_count: 2,
          },
        ],
      }),
    })
  })

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })

  await expect(page.getByRole('dialog', { name: '账号登录' })).toBeVisible()
  await expect(page.getByTestId('market-mobile-list')).toHaveCount(0)
  expect(currentUserRequestCount).toBe(0)
  expect(summaryRequestCount).toBe(0)
  const storedSession = await page.evaluate(() => window.localStorage.getItem('battel.auth.session.procurement'))
  expect(storedSession).toBeNull()
})


test('移动端点击商品卡片进入单品趋势后保留可刷新分享的商品深链', async ({ page }) => {
  await seedProcurementSession(page)
  await page.route('**/api/market/summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'liancai-cream|902',
            product_name: '伊利淡奶油1L*6盒 | 伊利 | 902',
            group_name: '伊利淡奶油1L*6盒',
            category: '乳品烘焙',
            average_price: 42,
            lowest_price: 40,
            highest_price: 43,
            market_count: 2,
            site_count: 2,
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'liancai-cream|902',
            price_identity_label: '伊利淡奶油1L*6盒 | 伊利 | 902',
            site_count: 2,
            price_observation_count: 2,
            latest_captured_at: '2026-05-11T15:58:53',
            source_name: '莲菜网',
            source_category: '乳品烘焙',
          },
        ],
      }),
    })
  })

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('market-mobile-card').first()).toBeVisible({ timeout: 10_000 })
  await page.getByTestId('market-mobile-card').first().click()

  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })
  await expect(page).toHaveURL(/tab=trend/)
  await expect(page).toHaveURL(/identity_key=liancai-cream%7C902/)
  await expect(page).toHaveURL(/product_label=/)

  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByText('伊利淡奶油1L*6盒 | 伊利 | 902').first()).toBeVisible()
})

test('移动端单品详情左上返回优先回到来源行情页', async ({ page }) => {
  await seedProcurementSession(page)
  const product = {
    price_identity_key: 'return-flow|001',
    price_identity_label: '返回流转商品 | 001',
    site_count: 2,
    price_observation_count: 2,
    latest_captured_at: '2026-05-17T08:00:00',
    source_name: '莲菜网',
    source_category: '测试分类',
  }

  await page.route('**/api/market/summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: product.price_identity_key,
            product_name: product.price_identity_label,
            group_name: '返回流转商品',
            category: '测试分类',
            average_price: 11.5,
            lowest_price: 10.8,
            highest_price: 12.4,
            market_count: 2,
            site_count: 2,
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [product] }) })
  })
  await page.route('**/api/product/*/summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        item: {
          price_identity_key: product.price_identity_key,
          product_name: product.price_identity_label,
          site_count: 2,
          market_count: 2,
          current_lowest_price: 10.8,
          current_highest_price: 12.4,
          average_price: 11.5,
        },
      }),
    })
  })
  await page.route('**/api/product/*/trend**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        mode: 'cross_market',
        items: [
          {
            price_identity_key: product.price_identity_key,
            product_name: product.price_identity_label,
            trend_series_key: 'market-a',
            trend_series_name: '市场 A',
            market_name: '市场 A',
            current_price: 11.5,
            captured_at: '2026-05-17T08:00:00',
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/*/supplier-quotes**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], summary: null }) })
  })

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('market-mobile-card').first()).toBeVisible({ timeout: 10_000 })
  await page.getByTestId('market-mobile-card').first().click()

  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })
  await expect(page).toHaveURL(/tab=trend/)
  await page.getByRole('button', { name: '返回汇总行情' }).click()

  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  await expect(page).toHaveURL(/tab=summary/)
  await expect(page).not.toHaveURL(/identity_key=/)
})


test('移动端分类来源卡片遇到重复分类名称时不产生 Vue key 冲突', async ({ page }) => {
  const warnings: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'warning') warnings.push(message.text())
  })
  await page.route('**/api/liancai/category-summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            liancai_top_category: '冻品类',
            liancai_subcategory: '面点类',
            product_count: 12,
          },
          {
            liancai_top_category: '冻品类',
            liancai_subcategory: '面点类',
            product_count: 8,
          },
        ],
      }),
    })
  })

  await page.goto('/', { waitUntil: 'networkidle' })
  await expect(page.getByTestId('mobile-source-groups')).toBeVisible()
  expect(warnings.filter((text) => text.includes('Duplicate keys found'))).toEqual([])
})


test('移动端首页分类区不提前拉取行情接口', async ({ page }) => {
  const requestedSummaryUrls: string[] = []
  const requestedCategoryUrls: string[] = []
  await page.route('**/api/liancai/category-summary**', async (route) => {
    requestedCategoryUrls.push(route.request().url())
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          { liancai_top_category: '蔬菜类', liancai_subcategory: '叶菜类', product_count: 2 },
          { liancai_top_category: '水产类', liancai_subcategory: '鲜活水产', product_count: 3 },
        ],
      }),
    })
  })
  await page.route('**/api/market/summary**', async (route) => {
    requestedSummaryUrls.push(route.request().url())
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'veg|001',
            product_name: '上海青 | 公斤',
            group_name: '上海青',
            category: '蔬菜类',
            liancai_top_category: '蔬菜类',
            liancai_subcategory: '叶菜类',
            average_price: 4.2,
            lowest_price: 3.9,
            highest_price: 4.8,
            market_count: 2,
            site_count: 2,
          },
          {
            price_identity_key: 'fish|001',
            product_name: '鲈鱼 | 公斤',
            group_name: '鲈鱼',
            category: '水产类',
            liancai_top_category: '水产类',
            liancai_subcategory: '鲜活水产',
            average_price: 31.5,
            lowest_price: 29,
            highest_price: 34,
            market_count: 3,
            site_count: 3,
          },
        ],
      }),
    })
  })

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('mobile-source-groups')).toBeVisible()
  await expect(page.getByText('暂无商品分类')).toBeVisible()
  await expectNoHorizontalOverflow(page)
  expect(requestedCategoryUrls).toEqual([])
  expect(requestedSummaryUrls).toEqual([])
})


test('移动端未登录点击底部明细先进入登录门禁', async ({ page }) => {
  const requestedTrendUrls: string[] = []
  await page.route('**/api/product/*/trend**', async (route) => {
    requestedTrendUrls.push(route.request().url())
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ mode: 'cross_market', items: [] }) })
  })

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await page.locator('.market-mobile-bottom-item').filter({ hasText: '明细' }).click()

  await expect(page.getByRole('dialog', { name: '账号登录' })).toBeVisible()
  await expect(page.getByLabel('趋势模式切换')).toHaveCount(0)
  expect(requestedTrendUrls).toEqual([])
})


test('移动端单品选择框展示当前接口返回商品', async ({ page }) => {
  await seedProcurementSession(page)
  const optionKeywords: string[] = []
  const product = {
    price_identity_key: 'trend-default|001',
    price_identity_label: '默认测试单品 | 001',
    site_count: 2,
    price_observation_count: 2,
    source_name: '莲菜网',
    source_category: '测试分类',
  }

  await page.route('**/api/market/summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ items: [] }),
    })
  })
  await page.route('**/api/product/options**', async (route) => {
    const url = new URL(route.request().url())
    const keyword = url.searchParams.get('keyword') || ''
    optionKeywords.push(keyword)
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: keyword ? [] : [product],
        total: keyword ? 0 : 1,
        limit: 40,
        offset: 0,
        has_more: false,
      }),
    })
  })
  await page.route('**/api/product/*/summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        item: {
          price_identity_key: product.price_identity_key,
          product_name: product.price_identity_label,
          site_count: 2,
          market_count: 2,
        },
      }),
    })
  })
  await page.route('**/api/product/*/trend**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        mode: 'cross_market',
        items: [
          {
            price_identity_key: product.price_identity_key,
            product_name: product.price_identity_label,
            trend_series_key: 'market-a',
            trend_series_name: '市场 A',
            market_name: '市场 A',
            current_price: 12.5,
            captured_at: '2026-05-17T08:00:00',
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/*/supplier-quotes**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], summary: null }) })
  })
  await page.goto('/?mode=workspace&tab=trend', { waitUntil: 'domcontentloaded' })
  await expect.poll(() => optionKeywords.includes('')).toBeTruthy()
  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByText('默认测试单品 | 001').first()).toBeVisible({ timeout: 15_000 })
  const productSelect = page.getByRole('combobox', { name: '选择商品' })
  await expect(productSelect).toContainText('默认测试单品 | 001')
  expect(optionKeywords).toEqual([''])
})


test('移动端切换到新商品趋势时清理旧版 product 深链参数，避免刷新回到旧商品', async ({ page }) => {
  await seedProcurementSession(page)
  await page.route('**/api/market/summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'fresh-product|002',
            product_name: '新商品 | 002',
            group_name: '新商品',
            category: '测试分类',
            average_price: 18,
            lowest_price: 17,
            highest_price: 19,
            market_count: 2,
            site_count: 2,
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'fresh-product|002',
            price_identity_label: '新商品 | 002',
            site_count: 2,
            price_observation_count: 2,
          },
          {
            price_identity_key: 'stale-product|001',
            price_identity_label: '旧商品 | 001',
            site_count: 2,
            price_observation_count: 2,
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/*/summary**', async (route) => {
    const key = decodeURIComponent(route.request().url().split('/api/product/')[1]?.split('/summary')[0] || '')
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        item: {
          price_identity_key: key,
          product_name: key === 'fresh-product|002' ? '新商品 | 002' : '旧商品 | 001',
          site_count: 2,
          market_count: 2,
        },
      }),
    })
  })
  await page.route('**/api/product/*/trend**', async (route) => {
    const key = decodeURIComponent(route.request().url().split('/api/product/')[1]?.split('/trend')[0] || '')
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        mode: 'cross_market',
        items: [
          {
            price_identity_key: key,
            product_name: key === 'fresh-product|002' ? '新商品 | 002' : '旧商品 | 001',
            trend_series_key: 'market-a',
            trend_series_name: '市场 A',
            market_name: '市场 A',
            current_price: 18,
            captured_at: '2026-05-17T08:00:00',
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/*/supplier-quotes**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], summary: null }) })
  })

  await page.goto('/?mode=workspace&tab=summary&product=stale-product%7C001&label=%E6%97%A7%E5%95%86%E5%93%81%20%7C%20001', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('market-mobile-card').first()).toBeVisible({ timeout: 10_000 })
  await page.getByTestId('market-mobile-card').first().click()

  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })
  await expect(page).toHaveURL(/tab=trend/)
  await expect(page).toHaveURL(/identity_key=fresh-product%7C002/)
  await expect(page).not.toHaveURL(/product=stale-product%7C001/)
  await expect(page).not.toHaveURL(/label=%E6%97%A7%E5%95%86%E5%93%81/)

  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByText('新商品 | 002').first()).toBeVisible({ timeout: 15_000 })
})

test('移动端离开单品趋势时清理商品深链参数，避免非单品页分享混入旧商品', async ({ page }) => {
  await seedProcurementSession(page)
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'stale-product|001',
            price_identity_label: '旧商品 | 001',
            site_count: 2,
            price_observation_count: 2,
          },
        ],
      }),
    })
  })
  await page.route('**/api/product/*/summary**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ item: null }) })
  })
  await page.route('**/api/product/*/trend**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [] }) })
  })
  await page.route('**/api/product/*/supplier-quotes**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], summary: null }) })
  })

  await page.goto('/?mode=workspace&tab=trend&identity_key=stale-product%7C001&product_label=%E6%97%A7%E5%95%86%E5%93%81%20%7C%20001', { waitUntil: 'domcontentloaded' })
  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '提醒' }).click()
  await expect(page).toHaveURL(/tab=alerts/)
  await expect(page).not.toHaveURL(/identity_key=/)
  await expect(page).not.toHaveURL(/product_label=/)

  await page.goto('/?mode=workspace&tab=trend&identity_key=stale-product%7C001&product_label=%E6%97%A7%E5%95%86%E5%93%81%20%7C%20001', { waitUntil: 'domcontentloaded' })
  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '采购' }).click()
  await expect(page).toHaveURL(/tab=menu/)
  await expect(page).not.toHaveURL(/identity_key=/)
  await expect(page).not.toHaveURL(/product_label=/)

  await page.goto('/?mode=workspace&tab=trend&identity_key=stale-product%7C001&product_label=%E6%97%A7%E5%95%86%E5%93%81%20%7C%20001', { waitUntil: 'domcontentloaded' })
  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '首页' }).click()
  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await expect(page).not.toHaveURL(/identity_key=/)
  await expect(page).not.toHaveURL(/product_label=/)
})

test('移动端今日菜价列表过滤接口和缓存中的非商品统计指标', async ({ page }) => {
  await seedProcurementSession(page)
  const badProduct = '生猪存栏量月度环比变化率'
  const badRow = {
    price_identity_key: 'hog-stock-mom-rate|%',
    product_name: `${badProduct} | %`,
    group_name: badProduct,
    category: '农业指标',
    spec_text: '%',
    price_unit_basis: '%',
    average_price: 1.2,
    lowest_price: 1.2,
    highest_price: 1.2,
    market_count: 1,
    site_count: 1,
  }
  const goodRow = {
    price_identity_key: 'pork|公斤',
    product_name: '猪肉 | 公斤',
    group_name: '猪肉',
    category: '肉禽',
    spec_text: '公斤',
    price_unit_basis: '元/公斤',
    average_price: 22.5,
    lowest_price: 22,
    highest_price: 23,
    market_count: 2,
    site_count: 2,
    lowest_price_site: '北京新发地',
  }

  await page.route('**/api/market/summary**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [badRow, goodRow] }) })
  })
  await page.addInitScript(([row]) => {
    const contextKey = JSON.stringify({ province: '', city: '' })
    window.localStorage.setItem('battel.market-summary.cache.v3', JSON.stringify({ [contextKey]: [row] }))
  }, [badRow] as const)

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  await expect(page.getByTestId('market-mobile-card').first()).toBeVisible()
  await expect(page.getByTestId('market-mobile-list')).toContainText('猪肉 | 公斤')
  await expect(page.getByTestId('market-mobile-list')).not.toContainText(badProduct)
})

test('移动端主流程无横向溢出且关键工作区可用', async ({ page }) => {
  await seedProcurementSession(page)
  await page.goto('/', { waitUntil: 'domcontentloaded' })

  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await expect(page.getByRole('heading', { name: '欢迎，移动采购' })).toBeVisible()
  await expect(page.locator('.mobile-redesign-login-button')).toContainText('移动采购')
  await expect(page.getByText('今天常买的菜')).toBeVisible()
  await expectNoHorizontalOverflow(page)

  await page.getByTestId('enter-workspace-button').click()
  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  const firstMarketCard = page.getByTestId('market-mobile-card').first()
  if (await firstMarketCard.isVisible({ timeout: 15_000 }).catch(() => false)) {
    await firstMarketCard.click()
  } else {
    await page.locator('.market-mobile-bottom-item').filter({ hasText: '明细' }).click()
  }
  await expectNoHorizontalOverflow(page)

  await expect(page.getByLabel('趋势模式切换')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByRole('combobox', { name: '选择商品' })).toBeVisible({ timeout: 15_000 })
  await expect(page.locator('.trend-toolbar, .trend-mobile-mode-switch').first()).toBeVisible()
  await expectNoHorizontalOverflow(page)

  const mobileTrendPager = page.getByTestId('trend-mobile-page-indicator')
  if (await mobileTrendPager.isVisible().catch(() => false)) {
    await expect(mobileTrendPager).toHaveText(/\d+ \/ \d+/)
    await page.getByRole('button', { name: '查看下一组趋势' }).click()
    await expect(mobileTrendPager).toHaveText(/\d+ \/ \d+/)
    await page.getByRole('button', { name: '查看上一组趋势' }).click()
  }

  await page.getByLabel('趋势模式切换').getByRole('button', { name: '单市场' }).click()
  await expect(page.getByRole('combobox', { name: '选择市场' })).toBeVisible()
  await expectNoHorizontalOverflow(page)

  await page.getByLabel('趋势模式切换').getByRole('button', { name: '跨市场' }).click()
  await expect(page.getByLabel('趋势模式切换').getByRole('button', { name: '跨市场' })).toHaveClass(/active/)
  await expectNoHorizontalOverflow(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '提醒' }).click()
  await expect(page.getByText('价格提醒').first()).toBeVisible()
  await expect(page).toHaveURL(/tab=alerts/)
  await expectNoHorizontalOverflow(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '菜价' }).click()
  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  await expect(page).toHaveURL(/tab=summary/)
  await expectNoHorizontalOverflow(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '采购' }).click()
  await expect(page.getByLabel('菜单文本输入')).toBeVisible()
  await expect(page).toHaveURL(/tab=menu/)
  await expectNoHorizontalOverflow(page)

  await page.locator('.market-mobile-bottom-item').filter({ hasText: '首页' }).click()
  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await expectNoHorizontalOverflow(page)

  await page.getByTestId('mobile-supplier-nav-button').click()
  await expect(page).toHaveURL(/\/supplier-portal/)
  await expectNoHorizontalOverflow(page)
})

test('移动端菜单提交会显示食材整理状态并返回采购建议', async ({ page }) => {
  await seedProcurementSession(page)
  await page.route('**/api/menu/plan', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 400))
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        ingredient_items: [
          { menu_name: '蒜蓉西兰花', ingredient_name: '西兰花', estimated_quantity: 2.2, quantity_unit: '公斤' },
          { menu_name: '清蒸鲈鱼', ingredient_name: '鲈鱼', estimated_quantity: 3.4, quantity_unit: '公斤' },
        ],
        procurement_plan: [
          { menu_name: '蒜蓉西兰花', ingredient_name: '西兰花', price_status: '已匹配报价', estimated_cost: 9.24 },
          { menu_name: '清蒸鲈鱼', ingredient_name: '鲈鱼', price_status: '已匹配报价', estimated_cost: 105.4 },
        ],
        total_cost: 114.64,
      }),
    })
  })
  await page.route('**/api/procurement/recommend', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          { menu_name: '蒜蓉西兰花', recommended_market: '北京顺鑫石门国际农产品批发市场集团有限公司' },
          { menu_name: '清蒸鲈鱼', recommended_market: '北京朝阳区大洋路综合市场' },
        ],
      }),
    })
  })

  await page.goto('/?mode=workspace&tab=menu', { waitUntil: 'domcontentloaded' })
  await expect(page.getByLabel('菜单文本输入')).toBeVisible()
  await page.getByLabel('菜单文本输入').fill('蒜蓉西兰花\n清蒸鲈鱼')

  const requestPromise = page.waitForResponse((response) => response.url().includes('/api/menu/plan') && response.request().method() === 'POST')
  await page.getByRole('button', { name: '生成采购方案' }).click()
  await expect(page.getByTestId('menu-ai-status')).toBeVisible()
  await expect(page.getByTestId('menu-ai-status')).toContainText('正在整理食材')
  await requestPromise
  await expect(page.getByTestId('menu-ai-parse-panel')).toContainText('食材拆分结果')
  await expect(page.getByText('AI 解析')).toHaveCount(0)
  await expect(page.getByTestId('menu-ai-parse-panel')).toContainText('西兰花')
  await expect(page.getByTestId('menu-plan-mobile-card').first()).toBeVisible()
  await expect(page.getByTestId('ingredient-mobile-card').first()).toBeVisible()
  await expectNoHorizontalOverflow(page)
})


test('移动端供应商独立入口不会继承旧商品深链参数', async ({ page }) => {
  await page.goto('/?identity_key=stale-product%7C001&product_label=%E6%97%A7%E5%95%86%E5%93%81%20%7C%20001', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('sales-landing-view')).toBeVisible()

  await page.getByTestId('mobile-supplier-nav-button').click()
  await expect(page).toHaveURL(/\/supplier-portal\?/)
  await expect(page).toHaveURL(/mode=supplier-portal/)
  await expect(page).not.toHaveURL(/identity_key=/)
  await expect(page).not.toHaveURL(/product_label=/)
})

test('供应商账号从注册审核深链进入时会落到报价工作台且不请求管理员审核接口', async ({ page }) => {
  let registrationAdminRequestCount = 0
  const supplierUser = {
    id: 2,
    username: 'demo-veg-a',
    role: 'supplier',
    display_name: '鲜蔬直采A',
    is_active: true,
    supplier_id: 1,
    supplier_profile: {
      supplier_id: 1,
      supplier_name: '鲜蔬直采A',
      market_category: '蔬菜类',
      channel: '微信小程序',
      market_scope: '杭州主城区',
      is_active: true,
    },
  }

  await page.route('**/api/auth/login', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'supplier-token',
        token_type: 'Bearer',
        expires_in: 3600,
        user: supplierUser,
      }),
    })
  })
  await page.route('**/api/location/options', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ provinces: ['浙江'], cities: ['杭州'] }) })
  })
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            price_identity_key: 'supplier-product|001',
            price_identity_label: '供应商报价商品 | 001',
            site_count: 1,
            price_observation_count: 1,
          },
        ],
      }),
    })
  })
  await page.route('**/api/supplier-registration-requests**', async (route) => {
    registrationAdminRequestCount += 1
    await route.fulfill({ status: 403, contentType: 'application/json', body: JSON.stringify({ detail: '当前账号没有管理员权限' }) })
  })
  await page.route('**/api/product/**/supplier-quotes**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [] }) })
  })
  await page.route('**/api/suppliers/1/quotes**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], total: 0 }) })
  })
  await page.route('**/api/suppliers**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 1,
            supplier_name: '鲜蔬直采A',
            contact_name: '张三',
            contact_phone: '13800000000',
            market_scope: '杭州主城区',
            market_category: '蔬菜类',
            channel: '微信小程序',
            is_active: true,
            account_username: 'demo-veg-a',
            account_display_name: '鲜蔬直采A',
            account_is_active: true,
          },
        ],
      }),
    })
  })
  await page.route('**/api/suppliers/1/settlements**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], total: 0 }) })
  })

  await page.goto('/supplier?mode=supplier&section=applications', { waitUntil: 'domcontentloaded' })
  await page.getByPlaceholder('账号').fill('demo-veg-a')
  await page.getByPlaceholder('密码').fill('demo123456')
  await page.getByTestId('auth-login-button').click()

  await expect(page.getByTestId('auth-login-button')).not.toBeVisible({ timeout: 30_000 })
  await expect(page.getByTestId('auth-session-status')).toContainText('鲜蔬直采A', { timeout: 30_000 })
  await expect(page.getByText('我的报价工作台')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText('注册审核').first()).not.toBeVisible()
  await expect(page).toHaveURL(/section=quote/)
  expect(registrationAdminRequestCount).toBe(0)
})

test('移动端可登录并进入供应商报价门户', async ({ page }) => {
  await page.goto('/supplier-portal?mode=supplier-portal', { waitUntil: 'domcontentloaded' })
  await expect(page.getByPlaceholder('账号')).toBeVisible({ timeout: 15_000 })

  await page.getByPlaceholder('账号').fill('admin')
  await page.getByPlaceholder('密码').fill('admin123')
  const loginResponse = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200)
  await page.getByTestId('auth-login-button').click()
  await loginResponse

  await expect(page.getByTestId('auth-login-button')).not.toBeVisible({ timeout: 30_000 })
  await expect(page.getByTestId('auth-session-status')).toContainText('系统管理员', { timeout: 30_000 })
  await expect(page.getByTestId('auth-session-status')).toContainText('管理员账号')
  await expect(page.getByLabel('供应商范围')).toContainText('当前账号')
  await expect(page.getByLabel('供应商范围')).toContainText('管理员账号')
  await expect(page.getByLabel('供应商范围')).toContainText('全局可见')
  await expect(page.getByLabel('报价状态队列')).toContainText('待处理')
  await expect(page.getByLabel('报价状态队列')).toContainText('草稿')
  await expect(page.getByLabel('报价状态队列')).toContainText('已提交')
  await page.getByLabel('报价状态队列').getByRole('button', { name: '已提交' }).click()
  await expect(page.getByText('最近报价记录')).toBeVisible()
  await expect(page.getByLabel('供应商快捷操作栏')).toContainText('返回录价')
  await expect(page.getByLabel('供应商快捷操作栏')).toContainText('去管理页')
  await page.getByLabel('供应商快捷操作栏').getByRole('button', { name: '返回录价' }).click()
  await expect(page.getByText('给当前商品录价')).toBeVisible()
  await expect(page.getByTestId('supplier-admin-panel')).toBeVisible()
  await expectNoHorizontalOverflow(page)
})
