import { dataSourceState } from './apiSession'
import type {
  LiancaiCategorySummaryItem,
  LiancaiFacetResponse,
  LocationOptionsResponse,
  MarketSummaryItem,
  ProductOptionItem,
  ProductTrendRow,
  SourceCoverageItem,
} from './types'

const MARKET_SNAPSHOT_URL = (import.meta.env.VITE_MARKET_SNAPSHOT_URL || '/data/market-snapshot.json').trim()
const MARKET_SNAPSHOT_MODE = (import.meta.env.VITE_MARKET_SNAPSHOT_MODE || 'auto').trim().toLowerCase()

type StaticMarketSnapshot = {
  schema_version?: number
  generated_at?: string
  location_options?: LocationOptionsResponse
  source_coverage?: { items?: SourceCoverageItem[] }
  market_summary?: { items?: MarketSummaryItem[] }
  product_options?: { items?: ProductOptionItem[] }
  product_summaries?: Record<string, any>
  product_trends?: Record<string, {
    cross_market?: { items?: ProductTrendRow[] }
    single_market?: Record<string, { items?: ProductTrendRow[] }>
  }>
  liancai_category_summary?: { items?: LiancaiCategorySummaryItem[] }
  liancai_facets?: Record<string, LiancaiFacetResponse>
}

let marketSnapshotPromise: Promise<StaticMarketSnapshot | null> | null = null

function normalizeSnapshotIdentity(value: unknown) {
  return String(value ?? '').trim().toLowerCase()
}

export function findSnapshotProductTrend(
  trendMap: StaticMarketSnapshot['product_trends'] | undefined,
  identityKey: string,
) {
  if (!trendMap) return null
  if (trendMap[identityKey]) {
    return trendMap[identityKey]
  }
  const normalizedIdentityKey = normalizeSnapshotIdentity(identityKey)
  const matchedEntry = Object.entries(trendMap).find(
    ([key]) => normalizeSnapshotIdentity(key) === normalizedIdentityKey,
  )
  return matchedEntry?.[1] ?? null
}

export function markStaticDataSource() {
  dataSourceState.mode = 'static'
  dataSourceState.lastError = ''
}

export async function loadMarketSnapshot() {
  if (!MARKET_SNAPSHOT_URL || MARKET_SNAPSHOT_MODE === 'off') {
    return null
  }
  if (!marketSnapshotPromise) {
    marketSnapshotPromise = fetch(MARKET_SNAPSHOT_URL, { credentials: 'same-origin' })
      .then(async (response) => {
        if (!response.ok) return null
        return (await response.json()) as StaticMarketSnapshot
      })
      .catch(() => null)
  }
  return marketSnapshotPromise
}

export function paginateItems<T>(items: T[], limit = 0, offset = 0) {
  const safeOffset = Math.max(0, Number(offset) || 0)
  const safeLimit = Math.max(0, Number(limit) || 0)
  const total = items.length
  const end = safeLimit === 0 ? total : Math.min(safeOffset + safeLimit, total)
  return {
    items: items.slice(safeOffset, end),
    total,
    limit: safeLimit,
    offset: safeOffset,
    has_more: end < total,
  }
}

export function normalizeText(value: unknown) {
  return String(value ?? '').trim()
}

const LIANCAI_TOP_ALIASES: Record<string, string[]> = {
  干调类: ['干调类', '调味品', '调味料', '调味品酱料类', '干货调料', '干货类', '香辛料'],
  调味品: ['调味品', '干调类', '调味料', '调味品酱料类', '干货调料', '香辛料'],
  米面粮油: ['米面粮油', '粮油米面', '粮油类', '主食类'],
  粮油米面: ['粮油米面', '米面粮油', '粮油类', '主食类'],
  蔬菜类: ['蔬菜类', '蔬菜', '净菜类'],
  肉禽蛋类: ['肉禽蛋类', '鲜猪肉', '鲜禽类', '禽蛋类', '牛羊肉'],
  水产类: ['水产类', '鲜活水产', '水产', '海鲜水产'],
}

function matchesLiancaiTopCategory(actualValue: unknown, expectedValue: unknown) {
  const actual = normalizeText(actualValue)
  const expected = normalizeText(expectedValue)
  if (!expected) return true
  if (actual === expected) return true
  const aliases = LIANCAI_TOP_ALIASES[expected] || []
  return aliases.some((alias) => actual === alias || actual.includes(alias) || alias.includes(actual))
}

function matchesSourceText(text: string, sourceName: string) {
  if (!sourceName) return true
  return text.includes(sourceName) || (sourceName.includes('莲菜网') && text.includes('莲菜网'))
}

export function filterSnapshotSummaryRows(
  rows: MarketSummaryItem[],
  params: {
    province?: string
    city?: string
    keyword?: string
    source_name?: string
    liancai_top_category?: string
    liancai_subcategory?: string
    liancai_keyword?: string
    liancai_brand?: string
  },
) {
  const province = normalizeText(params.province)
  const city = normalizeText(params.city)
  const keyword = normalizeText(params.keyword)
  const sourceName = normalizeText(params.source_name)
  const subcategory = normalizeText(params.liancai_subcategory)
  const liancaiKeyword = normalizeText(params.liancai_keyword)
  const brand = normalizeText(params.liancai_brand)
  return rows.filter((row) => {
    if (province && !normalizeText(row.region_label).includes(province)) return false
    if (city && !normalizeText(row.region_label).includes(city)) return false
    if (keyword && !normalizeText(row.product_name).includes(keyword)) return false
    if (sourceName) {
      const sourceText = [
        row.source_names,
        row.source_display_names,
        row.lowest_price_site,
        row.highest_price_site,
      ].map(normalizeText).filter(Boolean).join(' ')
      if (!matchesSourceText(sourceText, sourceName)) return false
    }
    if (!matchesLiancaiTopCategory(row.liancai_top_category, params.liancai_top_category)) return false
    if (subcategory && normalizeText(row.liancai_subcategory) !== subcategory) return false
    if (
      liancaiKeyword
      && normalizeText(row.liancai_keyword) !== liancaiKeyword
      && !normalizeText(row.product_name).includes(liancaiKeyword)
    ) return false
    if (
      brand
      && normalizeText(row.liancai_brand_name) !== brand
      && !normalizeText(row.product_name).includes(brand)
    ) return false
    return true
  })
}

export function filterSnapshotProductOptions(
  options: ProductOptionItem[],
  params: {
    keyword?: string
    source_name?: string
    liancai_top_category?: string
    liancai_subcategory?: string
    liancai_keyword?: string
    liancai_brand?: string
  },
) {
  const keyword = normalizeText(params.keyword).toLowerCase()
  const sourceName = normalizeText(params.source_name)
  const subcategory = normalizeText(params.liancai_subcategory)
  const liancaiKeyword = normalizeText(params.liancai_keyword)
  const brand = normalizeText(params.liancai_brand)
  return options.filter((item) => {
    if (keyword) {
      const haystack = [
        item.price_identity_label,
        item.price_identity_key,
        item.source_name,
        item.source_category,
        item.liancai_top_category,
        item.liancai_subcategory,
        item.liancai_keyword,
        item.liancai_brand_name,
      ].map((value) => normalizeText(value).toLowerCase()).join(' ')
      if (!haystack.includes(keyword)) return false
    }
    if (sourceName && !matchesSourceText(normalizeText(item.source_name), sourceName)) return false
    if (!matchesLiancaiTopCategory(item.liancai_top_category, params.liancai_top_category)) return false
    if (subcategory && normalizeText(item.liancai_subcategory) !== subcategory) return false
    if (
      liancaiKeyword
      && normalizeText(item.liancai_keyword) !== liancaiKeyword
      && !normalizeText(item.price_identity_label).includes(liancaiKeyword)
    ) return false
    if (
      brand
      && normalizeText(item.liancai_brand_name) !== brand
      && !normalizeText(item.price_identity_label).includes(brand)
    ) return false
    return true
  })
}

export function buildSnapshotProductOptions(rows: MarketSummaryItem[]): ProductOptionItem[] {
  return rows
    .filter((row) => normalizeText(row.price_identity_key) && normalizeText(row.product_name))
    .map((row) => ({
      price_identity_key: normalizeText(row.price_identity_key),
      price_identity_label: normalizeText(row.product_name),
      site_count: Number(row.site_count || row.market_count || 0),
      price_observation_count: Number(row.price_observation_count || row.market_count || row.site_count || 0),
      latest_captured_at: row.latest_captured_at || null,
      source_name: row.source_names || row.source_display_names || null,
      source_category: row.category || null,
      liancai_top_category: row.liancai_top_category || null,
      liancai_subcategory: row.liancai_subcategory || null,
      liancai_keyword: row.liancai_keyword || null,
      liancai_brand_name: row.liancai_brand_name || null,
      image_url: row.image_url || null,
    }))
}
