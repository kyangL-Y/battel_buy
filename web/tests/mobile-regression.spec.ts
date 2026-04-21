import type { Page } from '@playwright/test'
import { expect, test } from '@playwright/test'
import {
  crawlStatusResponse,
  crossMarketTrendByKey,
  locationOptionsResponse,
  marketSummaryResponse,
  menuPlanResponse,
  pricingPackagesResponse,
  procurementRecommendResponse,
  productOptionsResponse,
  productSummaryByKey,
  salesDemoContentResponse,
  singleMarketTrendByKey,
  signalsOverviewResponse,
  sourceCoverageResponse,
} from './fixtures/mobileApi'

async function mockApi(page: Page) {
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const requestUrl = new URL(request.url())
    const pathname = requestUrl.pathname
    const method = request.method()

    if (method === 'GET' && pathname.endsWith('/location/options')) {
      await route.fulfill({ json: locationOptionsResponse })
      return
    }
    if (method === 'GET' && pathname.endsWith('/market/summary')) {
      await route.fulfill({ json: marketSummaryResponse })
      return
    }
    if (method === 'GET' && pathname.endsWith('/source/coverage')) {
      await route.fulfill({ json: sourceCoverageResponse })
      return
    }
    if (method === 'GET' && pathname.endsWith('/crawl/status')) {
      await route.fulfill({ json: crawlStatusResponse })
      return
    }
    if (method === 'GET' && pathname.endsWith('/product/options')) {
      await route.fulfill({ json: productOptionsResponse })
      return
    }
    if (method === 'GET' && pathname.includes('/product/') && pathname.endsWith('/summary')) {
      const identityKey = decodeURIComponent(pathname.split('/product/')[1].replace('/summary', ''))
      await route.fulfill({ json: productSummaryByKey[identityKey] ?? { item: null } })
      return
    }
    if (method === 'GET' && pathname.includes('/product/') && pathname.endsWith('/trend')) {
      const identityKey = decodeURIComponent(pathname.split('/product/')[1].replace('/trend', ''))
      const mode = requestUrl.searchParams.get('mode') || 'cross_market'
      const seriesKey = requestUrl.searchParams.get('series_key') || ''
      if (mode === 'single_market') {
        await route.fulfill({
          json: singleMarketTrendByKey[identityKey]?.[seriesKey] ?? { items: [] },
        })
        return
      }
      await route.fulfill({ json: crossMarketTrendByKey[identityKey] ?? { items: [] } })
      return
    }
    if (method === 'POST' && pathname.endsWith('/menu/plan')) {
      await route.fulfill({ json: menuPlanResponse })
      return
    }
    if (method === 'GET' && pathname.endsWith('/signals/overview')) {
      await route.fulfill({ json: signalsOverviewResponse })
      return
    }
    if (method === 'POST' && pathname.endsWith('/procurement/recommend')) {
      await route.fulfill({ json: procurementRecommendResponse })
      return
    }
    if (method === 'GET' && pathname.endsWith('/sales/demo-content')) {
      await route.fulfill({ json: salesDemoContentResponse })
      return
    }
    if (method === 'GET' && pathname.endsWith('/pricing/packages')) {
      await route.fulfill({ json: pricingPackagesResponse })
      return
    }

    await route.fulfill({
      status: 404,
      json: { detail: `Unhandled mocked route: ${method} ${pathname}` },
    })
  })
}

async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }))
  expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.innerWidth + 1)
}

test('移动端主流程无横向溢出且关键工作区可用', async ({ page }) => {
  await mockApi(page)
  await page.goto('/')

  await expect(page.getByTestId('sales-landing-view')).toBeVisible()
  await expect(page.getByRole('heading', { name: '把价格工作台升级成可直接报价的经营决策产品。' })).toBeVisible()
  await expectNoHorizontalOverflow(page)

  await page.getByTestId('enter-workspace-button').click()
  await expect(page.getByTestId('signals-workspace')).toBeVisible()
  await expect(page.getByText('今日经营摘要')).toBeVisible()
  await expect(page.getByText('今日经营概览')).toBeVisible()
  await expectNoHorizontalOverflow(page)

  await page.getByRole('button', { name: '切换到汇总行情' }).click()
  await expect(page.getByTestId('market-mobile-list')).toBeVisible()
  await expect(page.getByTestId('market-mobile-card')).toHaveCount(2)
  await expectNoHorizontalOverflow(page)

  await page.getByTestId('market-mobile-card').first().click()
  await expect(page.getByRole('button', { name: '切换到单品趋势' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByLabel('趋势模式切换')).toBeVisible()
  await expect(page.getByRole('combobox', { name: '选择商品' })).toBeVisible()
  await expect(page.getByText('跨市场会补齐断档；每页只展示一组完全重合的价格线。')).toBeVisible()
  await expect(page.getByTestId('trend-mobile-page-indicator')).toHaveText('1 / 2')
  await expectNoHorizontalOverflow(page)

  await page.getByRole('button', { name: '查看下一组趋势' }).click()
  await expect(page.getByTestId('trend-mobile-page-indicator')).toHaveText('2 / 2')
  await page.getByRole('button', { name: '查看上一组趋势' }).click()
  await expect(page.getByTestId('trend-mobile-page-indicator')).toHaveText('1 / 2')

  await page.locator('.el-radio-button').filter({ hasText: '单市场' }).click()
  await expect(page.getByRole('combobox', { name: '选择市场' })).toBeVisible()
  await expectNoHorizontalOverflow(page)

  await page.locator('.el-radio-button').filter({ hasText: '跨市场' }).click()
  await expect(page.getByText('跨市场会补齐断档；每页只展示一组完全重合的价格线。')).toBeVisible()

  await page.getByRole('button', { name: '切换到菜单采购' }).click()
  await expect(page.getByRole('button', { name: '切换到菜单采购' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByLabel('菜单文本输入')).toBeVisible()
  await expect(page.getByRole('button', { name: '生成采购方案' })).toBeVisible()

  await page.getByLabel('菜单文本输入').fill('蒜蓉西兰花\n清蒸鲈鱼')
  await page.getByRole('button', { name: '生成采购方案' }).click()

  await expect(page.getByTestId('menu-plan-mobile-list')).toBeVisible()
  await expect(page.getByTestId('menu-plan-mobile-card')).toHaveCount(2)
  await expect(page.getByTestId('ingredient-mobile-list')).toBeVisible()
  await expect(page.getByTestId('ingredient-mobile-card')).toHaveCount(2)
  await expectNoHorizontalOverflow(page)
})
