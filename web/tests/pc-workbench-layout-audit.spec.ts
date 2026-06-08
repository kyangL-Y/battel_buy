import { expect, test } from '@playwright/test'

import { PROCUREMENT_AUTH_STORAGE_KEY } from './helpers/authSessionStorage'

test.setTimeout(120_000)

const pcSections = ['summary', 'trend', 'alerts', 'market', 'suppliers', 'purchase', 'quotes', 'plan', 'reports', 'settings'] as const
const pcViewports = [
  { width: 1280, height: 720, label: '1280' },
  { width: 1366, height: 768, label: '1366' },
  { width: 1440, height: 900, label: '1440' },
  { width: 1536, height: 864, label: '1536' },
  { width: 1920, height: 1080, label: '1920' },
] as const

async function enterPcWorkbench(page: import('@playwright/test').Page) {
  const procurementUser = {
    id: 1,
    username: 'admin',
    display_name: '管理员',
    role: 'admin',
    supplier_id: null,
  }
  await page.addInitScript(([storageKey, sessionUser]) => {
    window.localStorage.setItem(storageKey, JSON.stringify({
      access_token: 'layout-audit-token',
      token_type: 'Bearer',
      expires_in: 3600,
      user: sessionUser,
    }))
  }, [PROCUREMENT_AUTH_STORAGE_KEY, procurementUser] as const)
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ user: procurementUser }),
    })
  })
  await page.goto('/?mode=workspace&tab=summary&section=summary', { waitUntil: 'domcontentloaded' })
  await page.getByTestId('pc-price-workbench').waitFor({ state: 'visible', timeout: 30_000 })
  await expect(page.getByTestId('pcw-summary-data-row').first().or(page.getByTestId('pcw-summary-empty-row'))).toBeVisible({ timeout: 60_000 })
}

async function waitForPcSectionReady(page: import('@playwright/test').Page, section: typeof pcSections[number]) {
  if (section === 'summary') {
    await expect(page.getByTestId('pcw-summary-data-row').first().or(page.getByTestId('pcw-summary-empty-row'))).toBeVisible({ timeout: 60_000 })
    return
  }
  if (section === 'suppliers') {
    await page.locator('.pcw-supplier-admin-embedded,[data-testid="procurement-supplier-admin-panel"],[data-testid="procurement-supplier-login-gate"]').first().waitFor({ state: 'visible', timeout: 30_000 })
    return
  }
  if (section === 'plan') {
    await page.getByTestId('pcw-menu-workspace').waitFor({ state: 'visible', timeout: 30_000 })
    return
  }
  await page.locator('.pcw-card').first().waitFor({ state: 'visible', timeout: 30_000 })
}

test('PC 工作台多宽度无页面级横向溢出且核心区可见', async ({ page }) => {
  for (const viewport of pcViewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height })
    await enterPcWorkbench(page)

    for (const section of pcSections) {
      if (section !== 'summary') {
        await page.locator(`[data-section-id="${section}"]`).click()
        await expect(page.locator(`[data-section-id="${section}"]`)).toHaveClass(/active/)
      }
      await waitForPcSectionReady(page, section)
      const audit = await page.evaluate(() => {
        const doc = document.documentElement
        const main = document.querySelector<HTMLElement>('.pcw-main')
        const top = document.querySelector<HTMLElement>('.pcw-top')
        const side = document.querySelector<HTMLElement>('.pcw-side')
        const workbench = document.querySelector<HTMLElement>('[data-testid="pc-price-workbench"]')
        const contentBlocks = Array.from(
          document.querySelectorAll<HTMLElement>(
            '.pcw-card,.pcw-supplier-admin-embedded,[data-testid="pcw-menu-workspace"]',
          ),
        )
        const visibleContentBlocks = contentBlocks.filter((block) => {
          const rect = block.getBoundingClientRect()
          return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0
        })
        const visibleElements = Array.from(document.querySelectorAll<HTMLElement>('body *')).filter((element) => {
          const rect = element.getBoundingClientRect()
          const style = window.getComputedStyle(element)
          return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
        })
        const viewportLeaks = visibleElements.filter((element) => {
          const rect = element.getBoundingClientRect()
          const closestScrollable = element.closest<HTMLElement>(
            '.pcw-main,.pcw-table-card,.pcw-alert-table-card,.pcw-module-table,.pcw-market-compare,.pcw-peer-products',
          )
          return !closestScrollable && (rect.right > window.innerWidth + 2 || rect.left < -2)
        })
        const tableLeaks = Array.from(
          document.querySelectorAll<HTMLElement>(
            '.pcw-alert-table-card,.pcw-market-compare,.pcw-peer-products',
          ),
        )
          .map((element) => ({
            className: element.className,
            overflow: element.scrollWidth - element.clientWidth,
          }))
          .filter((item) => item.overflow > 180 && !String(item.className).includes('pcw-table-card'))
        return {
          pageOverflow: doc.scrollWidth - window.innerWidth,
          workbenchOverflow: workbench ? workbench.scrollWidth - workbench.clientWidth : 0,
          mainWidth: main?.getBoundingClientRect().width || 0,
          topHeight: top?.getBoundingClientRect().height || 0,
          sideWidth: side?.getBoundingClientRect().width || 0,
          visibleCardCount: visibleContentBlocks.length,
          minVisibleCardWidth: Math.min(...visibleContentBlocks.map((block) => block.getBoundingClientRect().width)),
          viewportLeakCount: viewportLeaks.length,
          tableLeakCount: tableLeaks.length,
        }
      })
      expect(audit.pageOverflow, `${viewport.label}/${section} page overflow`).toBeLessThanOrEqual(1)
      expect(audit.workbenchOverflow, `${viewport.label}/${section} workbench overflow`).toBeLessThanOrEqual(1)
      expect(audit.viewportLeakCount, `${viewport.label}/${section} viewport leaks`).toBe(0)
      expect(audit.tableLeakCount, `${viewport.label}/${section} severe table leaks`).toBe(0)
      expect(audit.mainWidth, `${viewport.label}/${section} main width`).toBeGreaterThan(900)
      expect(audit.topHeight, `${viewport.label}/${section} top height`).toBeLessThanOrEqual(70)
      expect(audit.sideWidth, `${viewport.label}/${section} side width`).toBeGreaterThanOrEqual(190)
      expect(audit.visibleCardCount, `${viewport.label}/${section} visible cards`).toBeGreaterThan(0)
      expect(audit.minVisibleCardWidth, `${viewport.label}/${section} min card width`).toBeGreaterThan(260)
    }
  }
})
