import { expect, test } from '@playwright/test'

import { expectNoHorizontalOverflow } from './helpers/layout'

test.setTimeout(90_000)

test('桌面端平台后台独立承载抓取和来源治理', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.goto('/admin', { waitUntil: 'domcontentloaded' })

  await expect(page.getByTestId('platform-admin-screen')).toBeVisible()
  await expect(page.getByRole('heading', { name: '平台后台' })).toBeVisible()
  await expect(page.getByRole('button', { name: '获取最新数据' })).toBeVisible()
  await page.getByRole('button', { name: /来源覆盖 SRC/ }).click()
  await expect(page.getByTestId('platform-source-coverage-list')).toBeVisible()
  await expect(page.getByText('来源覆盖与采集健康')).toBeVisible()
  await expect(page.getByRole('button', { name: '刷新来源覆盖' })).toBeVisible()
  await expect(page.getByRole('button', { name: '切到数据抓取' })).toBeVisible()
})

test('桌面端供应商门户独立承载供应商录价前端', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.goto('/supplier-portal', { waitUntil: 'domcontentloaded' })

  await expect(page.getByTestId('supplier-portal-screen')).toBeVisible()
  await expect(page.getByRole('heading', { name: '供应商报价门户', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '返回采购工作台', exact: true })).toBeVisible()
  await page.getByPlaceholder('账号').fill('admin')
  await page.getByPlaceholder('密码').fill('admin123')
  await page.getByRole('button', { name: '登录门户' }).click()

  await expect(page.getByTestId('auth-session-status')).toContainText('系统管理员')
  await expect(page.getByTestId('supplier-admin-panel')).toBeVisible()
  await expect(page.getByTestId('quote-product-required-alert')).toContainText('请先选择商品')
  await expect(page.getByTestId('quote-import-template')).toBeVisible()
})

test('桌面端无登录态从首页供应商入口进入供应商门户', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.addInitScript(() => {
    window.localStorage.removeItem('battel.auth.session')
  })

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('supplier-choice-button')).toBeVisible()
  await page.getByTestId('supplier-choice-button').click()
  await page.waitForURL(/\/supplier-portal/)

  const currentUrl = new URL(page.url())
  expect(currentUrl.pathname).toBe('/supplier-portal')
  expect(currentUrl.pathname).not.toBe('/supplier-backend')
})

test('桌面端供应商门户注册申请会真实提交并展示异常态', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  const submittedPayloads: unknown[] = []
  await page.route('**/api/supplier-registration-requests', async (route) => {
    submittedPayloads.push(route.request().postDataJSON())
    await route.fulfill({
      status: submittedPayloads.length === 1 ? 409 : 200,
      contentType: 'application/json',
      body: submittedPayloads.length === 1
        ? JSON.stringify({ detail: '该登录账号已存在' })
        : JSON.stringify({ id: 88, status: 'pending', company_name: '自动化测试供应商' }),
    })
  })

  await page.goto('/supplier-portal', { waitUntil: 'domcontentloaded' })
  await page.getByRole('button', { name: '注册' }).click()
  await page.getByPlaceholder('供应商名称').fill('自动化测试供应商')
  await page.getByPlaceholder('联系人').fill('李四')
  await page.getByPlaceholder('手机号').fill('13800000000')
  await page.getByPlaceholder('登录账号').fill('auto-supplier')
  await page.getByTestId('supplier-register-submit').click()

  await expect(page.getByText('该登录账号已存在')).toBeVisible()
  await expectNoHorizontalOverflow(page)

  await page.getByPlaceholder('登录账号').fill('auto-supplier-2')
  await page.getByTestId('supplier-register-submit').click()
  await expect(page.getByTestId('auth-login-button')).toBeVisible()
  expect(submittedPayloads).toEqual([
    {
      company_name: '自动化测试供应商',
      contact_name: '李四',
      contact_phone: '13800000000',
      username: 'auto-supplier',
    },
    {
      company_name: '自动化测试供应商',
      contact_name: '李四',
      contact_phone: '13800000000',
      username: 'auto-supplier-2',
    },
  ])
})

test('桌面端采购供应商管理遇到失效登录态时提示重新登录', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.addInitScript(() => {
    window.localStorage.setItem('battel.auth.session', JSON.stringify({
      access_token: 'expired-token',
      token_type: 'Bearer',
      expires_in: 3600,
      user: {
        id: 1,
        username: 'admin',
        display_name: '系统管理员',
        role: 'admin',
        supplier_id: null,
        is_active: true,
        created_at: '2026-05-01T00:00:00',
        updated_at: '2026-05-01T00:00:00',
      },
    }))
  })
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({}) })
  })
  await page.route('**/api/suppliers/overview**', async (route) => {
    await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({}) })
  })
  await page.route('**/api/suppliers?**', async (route) => {
    await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({}) })
  })

  await page.goto('/?mode=workspace&tab=summary&section=suppliers', { waitUntil: 'domcontentloaded' })

  const supplierPanel = page.getByTestId('procurement-supplier-admin-panel')
  await expect(supplierPanel).toBeVisible({ timeout: 15_000 })
  await expect(page.getByTestId('procurement-supplier-login-gate').getByText('登录状态已失效，请重新登录后进入供应商管理')).toBeVisible()
  await expect(supplierPanel.getByText('供应商管理读取失败，请确认采购端登录状态和权限')).toHaveCount(0)
})

test('桌面端 PC 工作台模块切换展示真实数据字段', async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  const summaryWarmup = await request.get('http://127.0.0.1:8000/api/market/summary', { timeout: 70_000 })
  expect(summaryWarmup.ok()).toBeTruthy()
  await page.goto('/', { waitUntil: 'domcontentloaded' })

  await expect(page.getByTestId('enter-workspace-button')).toBeVisible()
  await page.getByTestId('enter-workspace-button').click()
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByRole('heading', { name: '市场价格工作台' })).toBeVisible()

  await page.locator('[data-section-id="trend"]').click()
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible()
  await expect(page.locator('.pcw-trend-page')).toBeVisible()
  await expect(page.locator('.trend-workspace-panel')).toHaveCount(0)

  await expect(page.getByRole('heading', { name: /价格趋势/ }).first()).toBeVisible()
  await expect(page.getByRole('columnheader', { name: '当前报价' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: '来源层级' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: '同步时间' })).toBeVisible()

  await page.locator('[data-section-id="market"]').click()
  await expect(page.getByRole('heading', { name: '真实市场行情监控' })).toBeVisible()
  await expect(page.getByText(/已接入 \d+ 个来源，按真实行情主表监控商品价格。/)).toBeVisible()
  await expect(page.getByRole('columnheader', { name: '报价源' })).toBeVisible()
  await expect(page.locator('.pcw-module-flow p').first()).toBeVisible()

  await page.locator('[data-section-id="quotes"]').click()
  await expect(page.getByRole('heading', { name: '真实报价记录入库台' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: '录入方式' })).toBeVisible()
  await expect(page.locator('.pcw-module-table tbody tr').first()).toBeVisible()

  await page.locator('[data-section-id="plan"]').click()
  await expect(page.getByTestId('pcw-menu-workspace')).toBeVisible()
  await expect(page.getByRole('heading', { name: '菜单采购' }).first()).toBeVisible()
  await expect(page.getByRole('columnheader', { name: '食材 / 菜品' })).toBeVisible()

  await page.locator('[data-section-id="settings"]').click()
  await expect(page.getByRole('heading', { name: '真实来源配置与同步状态' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: '最近同步' })).toBeVisible()
  await expect(page.getByText('真实来源配置与同步状态')).toBeVisible()
  await expectNoHorizontalOverflow(page)
})

test('桌面端 PC 工作台供应商管理后台入口进入独立后台路径', async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  const summaryWarmup = await request.get('http://127.0.0.1:8000/api/market/summary', { timeout: 70_000 })
  expect(summaryWarmup.ok()).toBeTruthy()

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 15_000 })
  await page.getByRole('button', { name: '进入供应商管理后台' }).click()
  await page.waitForURL(/\/supplier-backend/)

  const currentUrl = new URL(page.url())
  expect(currentUrl.pathname).toBe('/supplier-backend')
  expect(currentUrl.searchParams.get('mode')).toBe('supplier')
  expect(currentUrl.searchParams.get('tab')).toBe('supplier')
})

test('桌面端 PC 工作台侧边栏模块可通过 URL section 刷新恢复', async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  const summaryWarmup = await request.get('http://127.0.0.1:8000/api/market/summary', { timeout: 70_000 })
  expect(summaryWarmup.ok()).toBeTruthy()

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 15_000 })

  await page.locator('[data-section-id="market"]').click()
  await expect(page.getByRole('heading', { name: '真实市场行情监控' })).toBeVisible()
  await expect(page.locator('[data-section-id="market"]')).toHaveClass(/active/)
  expect(new URL(page.url()).searchParams.get('section')).toBe('market')

  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByRole('heading', { name: '真实市场行情监控' })).toBeVisible()
  await expect(page.locator('[data-section-id="market"]')).toHaveClass(/active/)
  expect(new URL(page.url()).searchParams.get('section')).toBe('market')

  await page.locator('[data-section-id="settings"]').click()
  await expect(page.getByRole('heading', { name: '真实来源配置与同步状态' })).toBeVisible()
  expect(new URL(page.url()).searchParams.get('section')).toBe('settings')

  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: '真实来源配置与同步状态' })).toBeVisible()
  await expect(page.locator('[data-section-id="settings"]')).toHaveClass(/active/)
})

test('桌面端汇总行情在重型汇总接口未返回前用商品选项先展示首屏数据', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
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

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await page.getByRole('button', { name: /进入采购平台|我是采购/ }).first().click()
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible()
  await expect(page.getByTestId('pcw-summary-data-row').first()).toBeVisible({ timeout: 10_000 })
  await expect(page.getByRole('button', { name: '伊利淡奶油1L*6盒' })).toBeVisible()
  await expect(page.getByTestId('pcw-summary-empty-row')).toHaveCount(0)
  expect(requests.some((url) => url.includes('/api/product/options'))).toBeTruthy()
})

test('桌面端汇总行情过滤接口和缓存中的非商品统计指标', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
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
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible()
  await expect(page.getByTestId('pc-price-workbench')).toContainText('猪肉 | 公斤')
  await expect(page.getByTestId('pc-price-workbench')).not.toContainText(badProduct)
})

test('桌面端汇总行情选择莲菜网和干调类后请求后端筛选并展示数据', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  const requestedSummaryUrls: string[] = []
  const dryRows = [
    {
      price_identity_key: 'salt|雪天|62',
      product_name: '雪天牌加碘精纯盐400g | 雪天 | 62',
      group_name: '莲菜网',
      liancai_top_category: '调味品',
      liancai_subcategory: '调味料',
      source_names: '莲菜网',
      source_display_names: '莲菜网App | 干调类',
      lowest_price_site: '莲菜网App | 干调类',
      average_price: 2.1,
      lowest_price: 2.1,
      highest_price: 2.1,
      market_count: 1,
      site_count: 1,
    },
  ]
  const vegetableRows = [
    {
      price_identity_key: 'cabbage|other|1',
      product_name: '小白菜 筐装',
      group_name: '莲菜网',
      liancai_top_category: '蔬菜类',
      liancai_subcategory: '叶菜类',
      source_names: '莲菜网',
      average_price: 1.5,
      lowest_price: 1.5,
      highest_price: 1.5,
      market_count: 1,
      site_count: 1,
    },
  ]
  const pfscRows = [
    {
      price_identity_key: 'radish|pfsc|1',
      product_name: '白萝卜 | 公斤',
      group_name: '根茎类',
      category: '根茎类',
      liancai_top_category: '',
      liancai_subcategory: '',
      source_names: 'PFSC',
      source_display_names: 'PFSC | 蔬菜类 | 根茎类',
      lowest_price_site: 'PFSC | 蔬菜类 | 根茎类',
      average_price: 3.6,
      lowest_price: 3.6,
      highest_price: 3.6,
      market_count: 1,
      site_count: 1,
    },
  ]

  await page.route('**/api/market/summary**', async (route) => {
    const url = new URL(route.request().url())
    requestedSummaryUrls.push(`${url.pathname}?${url.searchParams.toString()}`)
    const sourceName = url.searchParams.get('source_name') || ''
    const topCategory = url.searchParams.get('liancai_top_category') || ''
    const items = sourceName === '莲菜网' && topCategory === '干调类'
      ? dryRows
      : [...dryRows, ...vegetableRows, ...pfscRows]
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ items, total: items.length, limit: Number(url.searchParams.get('limit') || 500), offset: 0, has_more: false }),
    })
  })
  await page.route('**/api/liancai/category-summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          { liancai_top_category: '干调类', liancai_subcategory: '调味料', liancai_keyword: '盐', product_count: 1 },
          { liancai_top_category: '蔬菜类', liancai_subcategory: '叶菜类', liancai_keyword: '小白菜', product_count: 1 },
        ],
      }),
    })
  })
  await page.route('**/api/source/coverage', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [{ source_name: '莲菜网', configured_name: '莲菜网', product_key_count: 2 }] }) })
  })
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [] }) })
  })
  await page.route('**/api/location/options', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ provinces: [], cities: [], province_city_map: {} }) })
  })
  await page.route('**/api/signals/overview**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], recommended_actions: [] }) })
  })
  await page.route('**/api/sales/decision-content**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({}) })
  })
  await page.route('**/api/crawl/status', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ item: null }) })
  })

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible()
  await expect(page.getByTestId('pc-price-workbench')).toContainText('小白菜 筐装')

  await page.locator('.pcw-filter-item').nth(0).getByRole('button').click()
  await page.getByRole('menuitemradio', { name: '莲菜网' }).click()
  await page.locator('.pcw-filter-item').nth(1).getByRole('button').click()
  await page.getByRole('menuitemradio', { name: '干调类' }).click()

  await expect(page.getByTestId('pc-price-workbench')).toContainText('雪天牌加碘精纯盐400g')
  await expect(page.getByTestId('pc-price-workbench')).not.toContainText('小白菜 筐装')
  expect(requestedSummaryUrls.some((url) => url.includes('source_name=%E8%8E%B2%E8%8F%9C%E7%BD%91') && url.includes('liancai_top_category=%E5%B9%B2%E8%B0%83%E7%B1%BB'))).toBeTruthy()
})

test('桌面端汇总行情渲染前强制匹配来源和分类', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  const mixedRows = [
    {
      price_identity_key: 'wheat-flour|chinaprice',
      product_name: '特一粉 | 公斤',
      group_name: 'Chinaprice',
      liancai_top_category: '米面粮油',
      liancai_subcategory: '面粉',
      source_names: 'Chinaprice',
      average_price: 175.56,
      lowest_price: 175.56,
      highest_price: 175.56,
      market_count: 1,
      site_count: 1,
    },
    {
      price_identity_key: 'salt|liancai',
      product_name: '雪天牌加碘精纯盐400g*5袋',
      group_name: '莲菜网',
      liancai_top_category: '调味品',
      liancai_subcategory: '调味料',
      source_names: '莲菜网',
      average_price: 2.1,
      lowest_price: 2.1,
      highest_price: 2.1,
      market_count: 1,
      site_count: 1,
    },
  ]
  await page.route('**/api/market/summary**', async (route) => {
    const url = new URL(route.request().url())
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ items: mixedRows, total: mixedRows.length, limit: Number(url.searchParams.get('limit') || 500), offset: 0, has_more: false }),
    })
  })
  await page.route('**/api/liancai/category-summary**', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ items: [{ liancai_top_category: '米面粮油', liancai_subcategory: '面粉', liancai_keyword: '面粉', product_count: 1 }] }),
    })
  })
  await page.route('**/api/source/coverage', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [{ source_name: 'Chinaprice', configured_name: '万邦国际', product_key_count: 1 }, { source_name: '莲菜网', configured_name: '莲菜网', product_key_count: 1 }] }) })
  })
  await page.route('**/api/product/options**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [] }) })
  })
  await page.route('**/api/location/options', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ provinces: [], cities: [], province_city_map: {} }) })
  })
  await page.route('**/api/signals/overview**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], recommended_actions: [] }) })
  })
  await page.route('**/api/sales/decision-content**', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({}) })
  })
  await page.route('**/api/crawl/status', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ item: null }) })
  })

  await page.goto('/?mode=workspace&tab=summary', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible()
  await page.locator('.pcw-filter-item').nth(0).getByRole('button').click()
  await page.getByRole('menuitemradio', { name: 'Chinaprice' }).click()
  await page.locator('.pcw-filter-item').nth(1).getByRole('button').click()
  await page.getByRole('menuitemradio', { name: '米面粮油' }).click()

  await expect(page.getByTestId('pc-price-workbench')).toContainText('特一粉 | 公斤')
  await expect(page.getByTestId('pc-price-workbench')).not.toContainText('雪天牌加碘精纯盐400g*5袋')
})

test('桌面端 PC 工作台关键按钮打开真实详情面板', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.goto('/', { waitUntil: 'domcontentloaded' })

  await page.getByTestId('enter-workspace-button').click()
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 15_000 })

  await page.locator('[data-section-id="market"]').click()
  await page.getByRole('button', { name: '查看来源' }).first().click()
  await expect(page.getByTestId('pcw-action-panel')).toBeVisible()
  await expect(page.getByTestId('pcw-action-panel')).toContainText('真实数据明细')
  await expect(page.getByRole('button', { name: '导出当前页' })).toBeVisible()
  await page.getByRole('button', { name: '关闭', exact: true }).click()

  await page.locator('[data-section-id="alerts"]').click()
  await page.getByRole('button', { name: '查看明细 ›' }).first().click()
  await expect(page.getByTestId('pcw-action-panel')).toContainText('高优先级预警')
  await page.getByRole('button', { name: '关闭', exact: true }).click()
  await expect(page.locator('[data-section-id="alerts"]')).toHaveClass(/active/)

  await page.locator('[data-section-id="trend"]').click()
  await page.getByRole('button', { name: '30 日' }).click()
  await expect(page.getByText('已切换为近 30 日视图')).toBeVisible()
  await expect(page.getByRole('button', { name: '30 日' })).toHaveClass(/active/)
  await expectNoHorizontalOverflow(page)
})

test('桌面端 PC 工作台下拉菜单、消息和价格预警设置可操作', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.goto('/', { waitUntil: 'domcontentloaded' })

  await page.getByTestId('enter-workspace-button').click()
  await expect(page.getByTestId('pc-price-workbench')).toBeVisible({ timeout: 15_000 })

  await page.locator('[data-section-id="alerts"]').click()
  await expect(page.locator('[data-section-id="alerts"]')).toHaveClass(/active/)

  const alertStatusFilter = page.locator('.pcw-filter-item').nth(3)
  await alertStatusFilter.getByRole('button').click()
  await expect(page.locator('.pcw-filter-menu')).toBeVisible()
  await page.mouse.click(20, 20)
  await expect(page.locator('.pcw-filter-menu')).toHaveCount(0)

  await alertStatusFilter.getByRole('button').click()
  await expect(page.locator('.pcw-filter-menu')).toBeVisible()
  await page.getByRole('menuitemradio', { name: '待处理' }).click()
  await expect(page.locator('.pcw-filter-menu')).toHaveCount(0)
  await expect(alertStatusFilter.getByRole('button')).toContainText('待处理')
  const firstAlertActions = page.locator('.pcw-alert-actions').first()
  await expect(firstAlertActions.getByRole('button', { name: '标记已处理' })).toBeVisible()
  await firstAlertActions.getByRole('button', { name: '标记已处理' }).click()
  await expect(page.getByText(/价格预警已人工处理|已标记.*价格预警处理完成/).first()).toBeVisible()
  await expect(page.locator('.pcw-alert-records')).toContainText('已处理')

  await page.getByRole('button', { name: /^消息/ }).click()
  await expect(page.getByTestId('pcw-message-panel')).toBeVisible()
  await expect(page.getByTestId('pcw-message-panel')).toContainText('真实业务提醒')
  await page.getByTestId('pcw-message-panel').locator('.pcw-message-list button').first().click()
  await expect(page.getByTestId('pcw-message-panel')).toHaveCount(0)

  await page.locator('[data-section-id="trend"]').click()
  await page.getByRole('button', { name: '设置预警 ›' }).click()
  const settingsPanel = page.getByTestId('pcw-alert-settings-panel')
  await expect(settingsPanel).toBeVisible()
  await settingsPanel.getByLabel('最高价提醒').fill('9.99')
  await settingsPanel.getByLabel('最低价提醒').fill('1.23')
  await settingsPanel.getByRole('button', { name: '保存设置' }).click()
  await expect(settingsPanel).toHaveCount(0)
  await expect(page.getByText('价格预警规则已保存')).toBeVisible()

  await page.getByRole('button', { name: /^消息/ }).click()
  await expect(page.getByTestId('pcw-message-panel')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByTestId('pcw-message-panel')).toHaveCount(0)
})

test('桌面端菜单提交后在右侧展示AI食材解析结果', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.route('**/api/menu/plan', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 300))
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        ingredient_items: [
          { menu_name: '佛跳墙', ingredient_name: '鲍鱼', estimated_quantity: 0.42, quantity_unit: '公斤', remarks: '传统主料' },
          { menu_name: '佛跳墙', ingredient_name: '海参', estimated_quantity: 0.42, quantity_unit: '公斤', remarks: '传统主料' },
          { menu_name: '惠灵顿牛排', ingredient_name: '牛里脊', estimated_quantity: 0.42, quantity_unit: '公斤', remarks: '核心食材' },
          { menu_name: '惠灵顿牛排', ingredient_name: '蘑菇', estimated_quantity: 0.28, quantity_unit: '公斤', remarks: '核心食材' },
        ],
        procurement_plan: [
          { menu_name: '佛跳墙', ingredient_name: '鲍鱼', price_status: '待确认', estimated_cost: 0 },
          { menu_name: '惠灵顿牛排', ingredient_name: '牛里脊', price_status: '已匹配报价', estimated_cost: 88 },
        ],
        total_cost: 88,
      }),
    })
  })
  await page.route('**/api/procurement/recommend', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [] }) })
  })

  await page.goto('/?mode=workspace&tab=menu', { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: '菜单采购' }).first()).toBeVisible()
  const submitMenuButton = page.locator('.menu-submit-bar').getByRole('button', { name: '生成采购方案' })
  await expect(submitMenuButton).toBeDisabled()
  await expect(page.locator('.menu-input-required')).toContainText('请先输入至少 1 个菜名')
  await page.getByLabel('菜单文本输入').fill('佛跳墙\n惠灵顿牛排')
  await expect(submitMenuButton).toBeEnabled()
  await submitMenuButton.click()
  await expect(page.getByTestId('menu-ai-status')).toBeVisible()
  await expect(page.getByTestId('menu-ai-parse-panel')).toContainText('食材拆分结果')
  await expect(page.getByTestId('menu-ai-parse-panel')).toContainText('鲍鱼')
  await expect(page.getByTestId('menu-ai-parse-panel')).toContainText('牛里脊')
  await expect(page.getByRole('columnheader', { name: '食材 / 菜品' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: '操作' })).toBeVisible()
  await expect(page.getByTestId('menu-plan-row-actions').first()).toContainText('补供应商价')
  await expectNoHorizontalOverflow(page)
})

test('桌面端菜单采购待确认行可确认并带上下文跳转补价', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.route('**/api/menu/plan', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        ingredient_items: [
          { menu_name: '佛跳墙', ingredient_name: '鲍鱼', estimated_quantity: 0.42, quantity_unit: '公斤', remarks: '传统主料' },
        ],
        procurement_plan: [
          { menu_name: '佛跳墙', ingredient_name: '鲍鱼', price_status: '待确认', estimated_cost: 0, recommended_market: '', reference_price: null, price_identity_key: 'abalone|kg' },
        ],
        total_cost: 0,
      }),
    })
  })
  await page.route('**/api/procurement/recommend', async (route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [] }) })
  })

  await page.goto('/?mode=workspace&tab=menu', { waitUntil: 'domcontentloaded' })
  await page.getByLabel('菜单文本输入').fill('佛跳墙')
  await page.locator('.menu-submit-bar').getByRole('button', { name: '生成采购方案' }).click()
  const actionCell = page.getByTestId('menu-plan-row-actions').first()
  await expect(actionCell).toBeVisible()
  await expect(actionCell.getByRole('button', { name: '看行情' })).toBeVisible()
  await actionCell.getByRole('button', { name: '标记确认' }).click()
  await expect(actionCell.getByRole('button', { name: '已确认' })).toBeDisabled()
  await actionCell.getByRole('button', { name: '补供应商价' }).click()
  await page.waitForURL(/\/supplier-backend/)
  const currentUrl = new URL(page.url())
  expect(currentUrl.searchParams.get('section')).toBe('quote')
  expect(currentUrl.searchParams.get('source')).toBe('menu_plan')
  expect(currentUrl.searchParams.get('product_label')).toBe('鲍鱼')
  expect(currentUrl.searchParams.get('identity_key')).toBe('abalone|kg')
})

test('供应后台未登录时展示采购来源上下文避免迷失', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.goto('/supplier-backend?mode=supplier&tab=supplier&section=quote&source=price_alert&identity_key=chicken%7Ckg&product_label=%E4%B8%89%E9%BB%84%E9%B8%A1&alert_rule=%E9%AB%98%E4%BA%8E10', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('supplier-login-form')).toBeVisible()
  await expect(page.getByTestId('supplier-carry-context').first()).toContainText('从价格预警带入')
  await expect(page.getByTestId('supplier-carry-context').first()).toContainText('三黄鸡')
})

test('桌面端管理员可登录并进入供应商管理台', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.goto('/supplier-backend?mode=supplier&tab=supplier', { waitUntil: 'domcontentloaded' })

  await expect(page.getByPlaceholder('账号')).toBeVisible({ timeout: 15_000 })

  await page.getByPlaceholder('账号').fill('admin')
  await page.getByPlaceholder('密码').fill('admin123')
  const loginResponse = page.waitForResponse((response) => response.url().includes('/api/auth/login') && response.status() === 200)
  await page.getByRole('button', { name: '登录后台' }).click()
  await loginResponse

  await expect(page.getByTestId('auth-session-status')).toContainText('系统管理员')
  await expect(page.getByTestId('auth-session-status')).toContainText('当前范围：全局供应商数据')
  await expect(page.getByTestId('supplier-admin-panel')).toBeVisible()
  await expect(page.getByTestId('supplier-session-banner')).toHaveCount(0)
  await expect(page.getByTestId('supplier-admin-top-metrics')).toHaveCount(0)
  await expect(page.getByText('供应商列表')).toBeVisible()
  await expect(page.getByRole('button', { name: /海鲜供应站B/ })).toBeVisible()
  await expect(page.getByRole('textbox', { name: '供应商名称' })).toHaveValue('海鲜供应站B')
  await expect(page.getByRole('textbox', { name: '联系人', exact: true })).toHaveValue('阿海')
  await expect(page.getByRole('textbox', { name: '联系电话', exact: true })).toHaveValue('13900000022')
  await expect(page.getByText('账号可用').first()).toBeVisible()
  await expect(page.getByRole('button', { name: '保存修改' })).toBeVisible()
  await page.setViewportSize({ width: 1100, height: 900 })
  const supplierListBox = await page.locator('.supplier-list-column').boundingBox()
  const supplierFormBox = await page.locator('.supplier-form-column').boundingBox()
  expect(supplierListBox).not.toBeNull()
  expect(supplierFormBox).not.toBeNull()
  expect(Math.abs((supplierListBox?.y ?? 0) - (supplierFormBox?.y ?? 0))).toBeLessThan(24)
  expect(supplierFormBox?.x ?? 0).toBeGreaterThan(supplierListBox?.x ?? 0)
  await page.getByRole('button', { name: '进入录价区' }).click()
  await expect(page.getByTestId('quote-product-required-alert')).toContainText('请先选择商品')
  const submitQuoteButton = page.getByRole('button', { name: '提交报价' })
  await expect(submitQuoteButton).toBeDisabled()
  await page.getByRole('combobox', { name: /先选择本次报价商品/ }).click({ force: true })
  await page.locator('.el-select-dropdown:visible .el-select-dropdown__item').first().click()
  await expect(page.getByTestId('quote-product-required-alert')).toHaveCount(0)
  await expect(submitQuoteButton).toBeEnabled()
})

test('桌面端结算和日志分区保留供应商范围并收起中间空列', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1024 })
  await page.goto('/supplier-backend?mode=supplier&tab=supplier', { waitUntil: 'domcontentloaded' })

  await page.getByPlaceholder('账号').fill('admin')
  await page.getByPlaceholder('密码').fill('admin123')
  await page.getByRole('button', { name: '登录后台' }).click()

  await page.getByRole('button', { name: /结算台账 SET/ }).click()
  expect(new URL(page.url()).pathname).toBe('/supplier-backend')
  await expect(page.getByText('供应商结算台账')).toBeVisible()
  await expect(page.getByTestId('settlement-selected-quotes-guide')).toContainText('需先到报价管理/历史报价勾选有效报价，再生成结算单')
  await expect(page.getByRole('button', { name: '用已选报价生成结算单' })).toBeDisabled()
  await expect(page.getByTestId('settlement-go-quote-history')).toBeVisible()
  await expect(page.locator('.supplier-form-column')).toBeHidden()
  await expect(page.locator('.supplier-list-column')).toBeVisible()
  await expect(page.locator('.supplier-quotes-column')).toBeVisible()
  await expect(page.locator('.supplier-list-column')).toContainText('当前选中：海鲜供应站B')
  const settlementListBox = await page.locator('.supplier-list-column').boundingBox()
  const settlementContentBox = await page.locator('.supplier-quotes-column').boundingBox()
  expect(settlementListBox).not.toBeNull()
  expect(settlementContentBox).not.toBeNull()
  expect(settlementContentBox?.x ?? 0).toBeGreaterThan(settlementListBox?.x ?? 0)
  expect(settlementContentBox?.width ?? 0).toBeGreaterThan(settlementListBox?.width ?? 0)

  await page.getByTestId('settlement-go-quote-history').click()
  expect(new URL(page.url()).pathname).toBe('/supplier-backend')
  expect(new URL(page.url()).searchParams.get('section')).toBe('quote')
  await expect(page.getByRole('button', { name: /全部报价/ })).toBeVisible()

  await page.getByRole('button', { name: '操作日志' }).click()
  await expect(page.getByText('最近操作日志')).toBeVisible()
  await expect(page.locator('.supplier-form-column')).toBeHidden()
  await expect(page.locator('.supplier-list-column')).toBeVisible()
  await expect(page.locator('.supplier-quotes-column')).toBeVisible()
  await expect(page.locator('.supplier-list-column')).toContainText('当前选中：海鲜供应站B')
  const logsListBox = await page.locator('.supplier-list-column').boundingBox()
  const logsContentBox = await page.locator('.supplier-quotes-column').boundingBox()
  expect(logsListBox).not.toBeNull()
  expect(logsContentBox).not.toBeNull()
  expect(logsContentBox?.x ?? 0).toBeGreaterThan(logsListBox?.x ?? 0)
  expect(logsContentBox?.width ?? 0).toBeGreaterThan(logsListBox?.width ?? 0)
})
