import type { MarketSummaryItem, ProductOptionItem, ProductTrendRow } from '../types'

export const ALERT_RULES_STORAGE_KEY = 'battel.alert-rules.v1'

export type ProductAlertRule = {
  identityKey: string
  productLabel: string
  sourceName: string
  sourceLabel: string
  minPrice: number
  maxPrice: number
  enabled: boolean
  createdAt?: string
  updatedAt?: string
}

export type ProductAlertHit = {
  identityKey: string
  productLabel: string
  currentPrice: number
  market: string
  sourceName: string
  triggered: boolean
  tone: 'up' | 'down' | 'warn'
  type: string
  rule: string
}

function normalizeNumber(value: unknown): number {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric < 0) return 0
  return Math.round(numeric * 100) / 100
}

export function normalizeProductAlertRule(value: Partial<ProductAlertRule> | null | undefined): ProductAlertRule {
  const minPrice = normalizeNumber(value?.minPrice)
  const maxPrice = normalizeNumber(value?.maxPrice)
  const normalizedMin = maxPrice > 0 && minPrice > maxPrice ? maxPrice : minPrice
  const normalizedMax = maxPrice > 0 && minPrice > maxPrice ? minPrice : maxPrice
  return {
    identityKey: String(value?.identityKey || '').trim(),
    productLabel: String(value?.productLabel || '').trim(),
    sourceName: String((value as { sourceName?: string }).sourceName || '').trim(),
    sourceLabel: String((value as { sourceLabel?: string }).sourceLabel || '').trim(),
    minPrice: normalizedMin,
    maxPrice: normalizedMax,
    enabled: value?.enabled !== false,
    createdAt: String(value?.createdAt || '').trim() || undefined,
    updatedAt: String(value?.updatedAt || '').trim() || undefined,
  }
}

export function readProductAlertRules(): ProductAlertRule[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(ALERT_RULES_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    if (!Array.isArray(parsed)) return []
    return parsed
      .map((item) => normalizeProductAlertRule(item))
      .filter((item) => item.identityKey && item.productLabel)
  } catch {
    return []
  }
}

export function writeProductAlertRules(rules: ProductAlertRule[]): void {
  if (typeof window === 'undefined') return
  const normalized = rules
    .map((item) => normalizeProductAlertRule(item))
    .filter((item) => item.identityKey && item.productLabel)
  window.localStorage.setItem(ALERT_RULES_STORAGE_KEY, JSON.stringify(normalized))
}

export function upsertProductAlertRule(
  existingRules: ProductAlertRule[],
  nextRule: Partial<ProductAlertRule>,
): ProductAlertRule[] {
  const normalized = normalizeProductAlertRule(nextRule)
  if (!normalized.identityKey || !normalized.productLabel) return existingRules
  const now = new Date().toISOString()
  const previous = existingRules.find((item) => item.identityKey === normalized.identityKey && item.sourceName === normalized.sourceName)
  const merged: ProductAlertRule = {
    ...normalized,
    createdAt: previous?.createdAt || now,
    updatedAt: now,
  }
  return [
    merged,
    ...existingRules.filter((item) => !(item.identityKey === normalized.identityKey && item.sourceName === normalized.sourceName)),
  ]
}

function normalizeSourceValue(value: unknown): string {
  return String(value || '').trim()
}

function rowSourceName(row: ProductTrendRow | MarketSummaryItem | null | undefined): string {
  return normalizeSourceValue((row as { source_name?: string | null; site_name?: string | null })?.source_name)
    || normalizeSourceValue((row as { site_name?: string | null })?.site_name)
}

function sourceMatches(expected: string, row: ProductTrendRow | MarketSummaryItem | null | undefined): boolean {
  const normalizedExpected = normalizeSourceValue(expected)
  if (!normalizedExpected) return true
  const actual = rowSourceName(row)
  return actual === normalizedExpected
}

export function buildProductAlertHit(
  rule: ProductAlertRule,
  summaryRows: MarketSummaryItem[],
  trendRows: ProductTrendRow[],
): ProductAlertHit | null {
  if (!rule.enabled || !rule.identityKey) return null
  const summaryRow = summaryRows.find((item) => item.price_identity_key === rule.identityKey)
  const trendCandidates = trendRows.filter((item) => {
    const seriesKey = String(item.trend_series_key || '').trim()
    return (!seriesKey || seriesKey === rule.identityKey) && sourceMatches(rule.sourceName, item)
  })
  const latestTrend = trendCandidates.length ? trendCandidates[trendCandidates.length - 1] : undefined
  let summaryPrice: number | null = null
  if (!rule.sourceName) {
    const value = Number(summaryRow?.average_price ?? summaryRow?.lowest_price ?? 0)
    summaryPrice = Number.isFinite(value) && value > 0 ? value : null
  } else if (summaryRow && normalizeSourceValue(summaryRow.lowest_price_site) === rule.sourceName) {
    const value = Number(summaryRow.lowest_price ?? 0)
    summaryPrice = Number.isFinite(value) && value > 0 ? value : null
  } else if (summaryRow && normalizeSourceValue(summaryRow.highest_price_site) === rule.sourceName) {
    const value = Number(summaryRow.highest_price ?? 0)
    summaryPrice = Number.isFinite(value) && value > 0 ? value : null
  }
  const currentPrice = Number(
    latestTrend?.current_price
    ?? summaryPrice
    ?? 0,
  )
  if (!Number.isFinite(currentPrice) || currentPrice <= 0) return null

  const market = String(
    rule.sourceLabel
    || rule.sourceName
    || latestTrend?.source_name
    || latestTrend?.site_name
    || latestTrend?.region_label
    || summaryRow?.lowest_price_site
    || summaryRow?.region_label
    || '本地市场',
  ).trim()

  if (rule.maxPrice > 0 && currentPrice >= rule.maxPrice) {
    const overflow = currentPrice - rule.maxPrice
    return {
      identityKey: rule.identityKey,
      productLabel: rule.productLabel,
      currentPrice,
      market,
      sourceName: rule.sourceName,
      triggered: true,
      tone: 'up',
      type: '最高价提醒',
      rule: `当前价 ${currentPrice.toFixed(2)}，较上限 ${rule.maxPrice.toFixed(2)} 高 ${overflow.toFixed(2)}`,
    }
  }
  if (rule.minPrice > 0 && currentPrice <= rule.minPrice) {
    const underflow = rule.minPrice - currentPrice
    return {
      identityKey: rule.identityKey,
      productLabel: rule.productLabel,
      currentPrice,
      market,
      sourceName: rule.sourceName,
      triggered: true,
      tone: 'down',
      type: '最低价提醒',
      rule: `当前价 ${currentPrice.toFixed(2)}，较下限 ${rule.minPrice.toFixed(2)} 低 ${underflow.toFixed(2)}`,
    }
  }
  if (rule.maxPrice > 0 || rule.minPrice > 0) {
    const distanceToMin = rule.minPrice > 0 ? currentPrice - rule.minPrice : Number.POSITIVE_INFINITY
    const distanceToMax = rule.maxPrice > 0 ? rule.maxPrice - currentPrice : Number.POSITIVE_INFINITY
    const nearestDistance = Math.min(distanceToMin, distanceToMax)
    const nearestRuleText = distanceToMin <= distanceToMax && rule.minPrice > 0
      ? `距下限 ${rule.minPrice.toFixed(2)} 还差 ${Math.max(distanceToMin, 0).toFixed(2)}`
      : rule.maxPrice > 0
        ? `距上限 ${rule.maxPrice.toFixed(2)} 还差 ${Math.max(distanceToMax, 0).toFixed(2)}`
        : ''
    return {
      identityKey: rule.identityKey,
      productLabel: rule.productLabel,
      currentPrice,
      market,
      sourceName: rule.sourceName,
      triggered: false,
      tone: 'warn',
      type: '价格观察',
      rule: nearestDistance !== Number.POSITIVE_INFINITY ? `当前价 ${currentPrice.toFixed(2)}，${nearestRuleText}` : `当前价 ${currentPrice.toFixed(2)}`,
    }
  }
  return null
}

export function pickAlertRuleProductLabel(
  identityKey: string,
  productOptions: ProductOptionItem[],
  fallbackLabel = '',
): string {
  const matched = productOptions.find((item) => item.price_identity_key === identityKey)
  return String(matched?.price_identity_label || fallbackLabel || '').trim()
}
