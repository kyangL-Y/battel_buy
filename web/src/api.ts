import axios from 'axios'
import { reactive } from 'vue'
import type {
  AuthLoginPayload,
  AuthLoginResponse,
  AuthMeResponse,
  AuthPasswordResetPayload,
  AuthUserCreatePayload,
  AuthUserDeleteResponse,
  AuthUserItem,
  AuthUserListResponse,
  AuthUserUpdatePayload,
  LiancaiFacetResponse,
  LocationOptionsResponse,
  LiancaiCategorySummaryItem,
  MarketSummaryItem,
  ProductOptionItem,
  ProductTrendRow,
  PricingPackagesResponse,
  ProcurementRecommendationResponse,
  SalesDemoContentResponse,
  SignalInsightItem,
  SignalOverviewResponse,
  SourceCoverageItem,
  SourceConfigUpdatePayload,
  SourceStrategyUpdatePayload,
  GlobalAlertRuleItem,
  SupplierListResponse,
  SupplierItem,
  SupplierQuoteActionCreatePayload,
  SupplierQuoteActionItem,
  SupplierQuoteActionListResponse,
  SupplierQuoteActionQueryOptions,
  SupplierQuoteCompareResponse,
  SupplierQuoteCreatePayload,
  SupplierQuoteCreateResponse,
  SupplierQuoteImportPayload,
  SupplierQuoteImportPreviewPayload,
  SupplierQuoteImportPreviewResponse,
  SupplierQuoteImportResponse,
  SupplierQuoteInvalidatePayload,
  SupplierQuoteInvalidateResponse,
  SupplierQuoteListResponse,
  SupplierSettlementBuildFromQuotesPayload,
  SupplierSettlementBuildFromQuotesResponse,
  SupplierSettlementCancelPayload,
  SupplierSettlementCancelResponse,
  SupplierSettlementCreatePayload,
  SupplierSettlementCreateResponse,
  SupplierSettlementDetailResponse,
  SupplierSettlementListResponse,
  SupplierSettlementQueryOptions,
  SupplierSettlementUpdatePayload,
  SupplierSettlementUpdateResponse,
  SupplierOverviewResponse,
  SupplierUpdatePayload,
} from './types'

const AUTH_STORAGE_KEYS = {
  procurement: 'battel.auth.session.procurement',
  supplier: 'battel.auth.session.supplier',
  admin: 'battel.auth.session.admin',
} as const
const LEGACY_AUTH_STORAGE_KEY = 'battel.auth.session'
const MARKET_SNAPSHOT_URL = (import.meta.env.VITE_MARKET_SNAPSHOT_URL || '/data/market-snapshot.json').trim()
const MARKET_SNAPSHOT_MODE = (import.meta.env.VITE_MARKET_SNAPSHOT_MODE || 'auto').trim().toLowerCase()

function normalizeApiBaseUrl(rawValue?: string) {
  const value = (rawValue || '').trim()
  if (!value && import.meta.env.PROD && typeof window !== 'undefined') {
    const { protocol, hostname, port } = window.location
    if (port && port !== '80' && port !== '443') {
      return `${protocol}//${hostname}/api`
    }
  }
  const normalizedValue = value || '/api'
  if (!normalizedValue) {
    return '/api'
  }
  return normalizedValue.endsWith('/') ? normalizedValue.slice(0, -1) : normalizedValue
}

const apiBaseUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL)
const PRODUCT_TREND_RESPONSE_CACHE_TTL_MS = 15_000
type ProductTrendParams = {
  mode: string
  site_name?: string
  series_key?: string
  province?: string
  city?: string
  source_name?: string
  liancai_top_category?: string
  liancai_subcategory?: string
  liancai_keyword?: string
  liancai_brand?: string
}
const productTrendRequests = new Map<string, Promise<any>>()
const productTrendResponseCache = new Map<string, { expiresAt: number; data: any }>()

export const api = axios.create({
  // Production defaults to the reverse-proxied /api path.
  baseURL: apiBaseUrl,
  timeout: 30000,
})

const publicApi = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
})

const AUTH_REQUEST_TIMEOUT = 60000

export type AuthSessionState = {
  access_token: string
  token_type: 'Bearer'
  expires_in: number
  user: AuthUserItem
}

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

type AuthSessionScope = keyof typeof AUTH_STORAGE_KEYS

function resolveAuthSessionScope(scope?: AuthSessionScope): AuthSessionScope {
  if (scope) return scope
  if (typeof window === 'undefined') return 'procurement'
  const pathname = window.location.pathname
  if (pathname === '/admin') return 'admin'
  if (pathname === '/supplier-portal' || pathname === '/supplier-backend') return 'supplier'
  return 'procurement'
}

function readScopedAuthSession(scope?: AuthSessionScope): AuthSessionState | null {
  if (!canUseStorage()) {
    return null
  }
  try {
    const storageKey = AUTH_STORAGE_KEYS[resolveAuthSessionScope(scope)]
    const rawValue = window.localStorage.getItem(storageKey) || window.localStorage.getItem(LEGACY_AUTH_STORAGE_KEY)
    if (!rawValue) {
      return null
    }
    const parsed = JSON.parse(rawValue) as AuthSessionState
    if (!window.localStorage.getItem(storageKey)) {
      window.localStorage.setItem(storageKey, rawValue)
    }
    return parsed
  } catch {
    return null
  }
}

export function readAuthSession(scope?: AuthSessionScope): AuthSessionState | null {
  return readScopedAuthSession(scope)
}

export function writeAuthSession(session: AuthSessionState, scope?: AuthSessionScope) {
  if (!canUseStorage()) {
    return
  }
  window.localStorage.setItem(AUTH_STORAGE_KEYS[resolveAuthSessionScope(scope)], JSON.stringify(session))
}

export function clearAuthSession(scope?: AuthSessionScope) {
  if (!canUseStorage()) {
    return
  }
  window.localStorage.removeItem(AUTH_STORAGE_KEYS[resolveAuthSessionScope(scope)])
  window.localStorage.removeItem(LEGACY_AUTH_STORAGE_KEY)
}

export function getAccessToken(scope?: AuthSessionScope) {
  return readScopedAuthSession(scope)?.access_token || ''
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const dataSourceState = reactive({
  mode: 'live' as 'live' | 'static' | 'error',
  lastError: '',
})

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

function findSnapshotProductTrend(
  trendMap: StaticMarketSnapshot['product_trends'] | undefined,
  identityKey: string,
) {
  if (!trendMap) return null
  if (trendMap[identityKey]) {
    return trendMap[identityKey]
  }
  const normalizedIdentityKey = normalizeSnapshotIdentity(identityKey)
  const matchedEntry = Object.entries(trendMap).find(([key]) => normalizeSnapshotIdentity(key) === normalizedIdentityKey)
  return matchedEntry?.[1] ?? null
}

function markStaticDataSource() {
  dataSourceState.mode = 'static'
  dataSourceState.lastError = ''
}

async function loadMarketSnapshot() {
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

function paginateItems<T>(items: T[], limit = 0, offset = 0) {
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

function normalizeText(value: unknown) {
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

function filterSnapshotSummaryRows(
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
    if (liancaiKeyword && normalizeText(row.liancai_keyword) !== liancaiKeyword && !normalizeText(row.product_name).includes(liancaiKeyword)) return false
    if (brand && normalizeText(row.liancai_brand_name) !== brand && !normalizeText(row.product_name).includes(brand)) return false
    return true
  })
}

function filterSnapshotProductOptions(
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
    if (liancaiKeyword && normalizeText(item.liancai_keyword) !== liancaiKeyword && !normalizeText(item.price_identity_label).includes(liancaiKeyword)) return false
    if (brand && normalizeText(item.liancai_brand_name) !== brand && !normalizeText(item.price_identity_label).includes(brand)) return false
    return true
  })
}

function buildSnapshotProductOptions(rows: MarketSummaryItem[]): ProductOptionItem[] {
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

export function buildSnapshotProductSummary(identityKey: string, rows: MarketSummaryItem[]) {
  const normalizedIdentityKey = normalizeSnapshotIdentity(identityKey)
  const row = (rows || []).find((item) => normalizeSnapshotIdentity(item.price_identity_key) === normalizedIdentityKey)
  if (!row) return null
  const normalizedLowestPrice = row.current_lowest_price ?? row.lowest_price ?? null
  const normalizedHighestPrice = row.current_highest_price ?? row.highest_price ?? null
  const normalizedLowestSite = row.current_lowest_site ?? row.lowest_price_site ?? row.region_label ?? null
  const normalizedHighestSite = row.current_highest_site ?? row.highest_price_site ?? row.region_label ?? null
  return {
    ...row,
    price_identity_key: identityKey,
    product_name: row.product_name,
    average_price: row.average_price,
    lowest_price: row.lowest_price,
    highest_price: row.highest_price,
    current_lowest_price: normalizedLowestPrice,
    current_highest_price: normalizedHighestPrice,
    current_lowest_site: normalizedLowestSite,
    current_highest_site: normalizedHighestSite,
    site_count: row.site_count || row.market_count || null,
    price_span:
      normalizedLowestPrice != null && normalizedHighestPrice != null
        ? Number(normalizedHighestPrice) - Number(normalizedLowestPrice)
        : row.price_span ?? null,
    latest_captured_at: row.latest_captured_at || null,
  }
}

type RequestStateOptions = {
  affectGlobalState?: boolean
}

function isAxiosError(error: unknown) {
  return typeof error === 'object' && error !== null && 'isAxiosError' in error
}

export function extractApiErrorDetail(error: unknown) {
  if (!isAxiosError(error)) {
    return ''
  }

  const axiosError = error as {
    response?: {
      data?: {
        detail?: unknown
      }
    }
  }

  const detail = axiosError.response?.data?.detail
  if (typeof detail === 'string') {
    return detail.trim()
  }
  return ''
}

export function getApiErrorStatus(error: unknown) {
  if (!isAxiosError(error)) {
    return 0
  }

  const axiosError = error as {
    response?: {
      status?: number
    }
  }
  return Number(axiosError.response?.status || 0)
}

function formatApiErrorMessage(error: unknown) {
  if (!isAxiosError(error)) {
    return '接口请求失败，请稍后重试'
  }

  const axiosError = error as {
    code?: string
    message?: string
    response?: {
      status?: number
    }
  }

  const status = Number(axiosError.response?.status || 0)
  if (status >= 500) {
    return '服务暂时不可用，请稍后刷新或检查后端服务'
  }
  if (status === 404) {
    return '接口地址不可用，请检查服务配置'
  }
  if (status === 401 || status === 403) {
    return status === 401 ? '登录状态已失效，请重新登录' : '当前账号没有权限执行这个操作'
  }
  if (axiosError.code === 'ECONNABORTED') {
    return '接口响应超时，请稍后重试'
  }
  if (axiosError.code === 'ERR_NETWORK' || /ECONNREFUSED|Network Error/i.test(String(axiosError.message || ''))) {
    return '无法连接后端服务，请先启动 API 再刷新页面'
  }
  return '接口请求失败，请稍后重试'
}

async function requestWithState<T>(request: () => Promise<T>, options: RequestStateOptions = {}) {
  const { affectGlobalState = true } = options
  try {
    const result = await request()
    if (affectGlobalState) {
      dataSourceState.mode = 'live'
      dataSourceState.lastError = ''
    }
    return result
  } catch (error) {
    if (affectGlobalState && isAxiosError(error)) {
      dataSourceState.mode = 'error'
      dataSourceState.lastError = formatApiErrorMessage(error)
    }
    throw error
  }
}

export async function login(payload: AuthLoginPayload) {
  return requestWithState(async () => {
    const { data } = await api.post<AuthLoginResponse>('/auth/login', payload, { timeout: AUTH_REQUEST_TIMEOUT })
    return data
  }, { affectGlobalState: false })
}

export async function resetAuthPassword(payload: AuthPasswordResetPayload) {
  return requestWithState(async () => {
    const { data } = await api.post<AuthLoginResponse>('/auth/password/reset', payload, { timeout: AUTH_REQUEST_TIMEOUT })
    return data
  }, { affectGlobalState: false })
}

export async function fetchCurrentUser() {
  return requestWithState(async () => {
    const { data } = await api.get<AuthMeResponse>('/auth/me', { timeout: AUTH_REQUEST_TIMEOUT })
    return data
  }, { affectGlobalState: false })
}

export async function fetchAuthUsers(params: { role?: string; status?: string; keyword?: string } = {}) {
  return requestWithState(async () => {
    const { data } = await api.get<AuthUserListResponse>('/auth/users', { params, timeout: AUTH_REQUEST_TIMEOUT })
    return data
  }, { affectGlobalState: false })
}

export async function createAuthUser(payload: AuthUserCreatePayload) {
  return requestWithState(async () => {
    const { data } = await api.post<AuthUserItem>('/auth/users', payload, { timeout: AUTH_REQUEST_TIMEOUT })
    return data
  }, { affectGlobalState: false })
}

export async function updateAuthUser(userId: number, payload: AuthUserUpdatePayload) {
  return requestWithState(async () => {
    const { data } = await api.put<AuthUserItem>(`/auth/users/${userId}`, payload, { timeout: AUTH_REQUEST_TIMEOUT })
    return data
  }, { affectGlobalState: false })
}

export async function deleteAuthUser(userId: number) {
  return requestWithState(async () => {
    const { data } = await api.delete<AuthUserDeleteResponse>(`/auth/users/${userId}`, { timeout: AUTH_REQUEST_TIMEOUT })
    return data
  }, { affectGlobalState: false })
}

export async function fetchLocationOptions() {
  try {
    return await requestWithState(async () => {
      const { data } = await api.get<LocationOptionsResponse>('/location/options')
      return data
    })
  } catch (error) {
    const snapshot = await loadMarketSnapshot()
    if (snapshot?.location_options) {
      markStaticDataSource()
      return snapshot.location_options
    }
    throw error
  }
}

export async function fetchSourceCoverage() {
  try {
    return await requestWithState(async () => {
      const { data } = await api.get('/source/coverage', { timeout: 45000 })
      return data
    }, { affectGlobalState: false })
  } catch (error) {
    const snapshot = await loadMarketSnapshot()
    if (snapshot?.source_coverage) {
      markStaticDataSource()
      return { items: snapshot.source_coverage.items ?? [] }
    }
    throw error
  }
}

export async function updateSourceCoverage(payload: SourceConfigUpdatePayload) {
  return requestWithState(async () => {
    const { data } = await api.put('/source/coverage', payload)
    return data
  }, { affectGlobalState: false })
}

export async function updateSourceStrategy(payload: SourceStrategyUpdatePayload) {
  return requestWithState(async () => {
    const { data } = await api.put('/source/strategy', payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchGlobalAlertRules() {
  return requestWithState(async () => {
    const { data } = await api.get<{ items: GlobalAlertRuleItem[] }>('/settings/alerts')
    return data
  }, { affectGlobalState: false })
}

export async function updateGlobalAlertRules(items: GlobalAlertRuleItem[]) {
  return requestWithState(async () => {
    const { data } = await api.put<{ items: GlobalAlertRuleItem[] }>('/settings/alerts', { items })
    return data
  }, { affectGlobalState: false })
}

export async function fetchCrawlStatus() {
  return requestWithState(async () => {
    const { data } = await api.get('/crawl/status')
    return data
  }, { affectGlobalState: false })
}

export async function triggerCrawlRun(payload: {
  target_scope?: 'all_saved' | 'province' | 'city'
  target_province?: string
  target_city?: string
  source_url?: string
  source_name?: string
} = {}) {
  return requestWithState(async () => {
    const { data } = await api.post('/crawl/run', payload)
    return data
  }, { affectGlobalState: false })
}

export async function updateCrawlSchedule(payload: {
  enabled: boolean
  mode?: 'interval' | 'daily_time'
  daily_run_time?: string | null
  interval_seconds: number
  fetch_mode?: 'requests' | 'playwright'
}) {
  return requestWithState(async () => {
    const { data } = await api.post('/crawl/schedule', payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchMarketSummary(params: {
  province?: string
  city?: string
  keyword?: string
  source_name?: string
  liancai_top_category?: string
  liancai_subcategory?: string
  liancai_keyword?: string
  liancai_brand?: string
  limit?: number
  offset?: number
}) {
  try {
    return await requestWithState(async () => {
      const { data } = await api.get('/market/summary', { params, timeout: 60000 })
      return data
    })
  } catch (error) {
    const snapshot = await loadMarketSnapshot()
    const snapshotRows = snapshot?.market_summary?.items
    const snapshotHasAnyImage = Array.isArray(snapshotRows)
      && snapshotRows.some((row) => String(row?.image_url || '').trim())
    if (snapshotRows && snapshotHasAnyImage) {
      markStaticDataSource()
      return paginateItems(
        filterSnapshotSummaryRows(snapshotRows, params),
        params.limit,
        params.offset,
      )
    }
    throw error
  }
}

export async function fetchProductOptions(params: { province?: string; city?: string; keyword?: string; source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string; limit?: number; offset?: number }) {
  try {
    return await requestWithState(async () => {
      const { data } = await api.get('/product/options', { params, timeout: 45000 })
      return data
    }, { affectGlobalState: false })
  } catch (error) {
    const snapshot = await loadMarketSnapshot()
    if (snapshot?.product_options?.items || snapshot?.market_summary?.items) {
      markStaticDataSource()
      const sourceOptions = snapshot.product_options?.items?.length
        ? snapshot.product_options.items
        : buildSnapshotProductOptions(filterSnapshotSummaryRows(snapshot.market_summary?.items ?? [], params))
      return paginateItems(
        filterSnapshotProductOptions(sourceOptions, params),
        params.limit,
        params.offset,
      )
    }
    throw error
  }
}

export async function fetchProductSummary(identityKey: string, params?: { province?: string; city?: string; source_name?: string; liancai_top_category?: string; liancai_subcategory?: string; liancai_keyword?: string; liancai_brand?: string }) {
  const decodedIdentityKey = decodeURIComponent(identityKey)
  return requestWithState(async () => {
    const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/summary`, { params })
    return data
  }, { affectGlobalState: false })
}

export async function fetchProductTrend(identityKey: string, params: ProductTrendParams) {
  const requestKey = JSON.stringify({
    identityKey,
    mode: params.mode || '',
    site_name: params.site_name || '',
    series_key: params.series_key || '',
    province: params.province || '',
    city: params.city || '',
    source_name: params.source_name || '',
    liancai_top_category: params.liancai_top_category || '',
    liancai_subcategory: params.liancai_subcategory || '',
    liancai_keyword: params.liancai_keyword || '',
    liancai_brand: params.liancai_brand || '',
  })
  const cachedResponse = productTrendResponseCache.get(requestKey)
  if (cachedResponse && cachedResponse.expiresAt > Date.now()) {
    return cachedResponse.data
  }
  const existingRequest = productTrendRequests.get(requestKey)
  if (existingRequest) {
    return existingRequest
  }
  const requestPromise = requestWithState(async () => {
    const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/trend`, {
      params,
      timeout: 45000,
    })
    productTrendResponseCache.set(requestKey, {
      expiresAt: Date.now() + PRODUCT_TREND_RESPONSE_CACHE_TTL_MS,
      data,
    })
    return data
  }, { affectGlobalState: false }).catch(async (error) => {
    const snapshot = await loadMarketSnapshot()
    const snapshotTrendEntry = findSnapshotProductTrend(snapshot?.product_trends, decodeURIComponent(identityKey))
    if (!snapshotTrendEntry) throw error
    const requestedMode = params.mode === 'single_market' ? 'single_market' : 'cross_market'
    let snapshotItems: ProductTrendRow[] = []
    if (requestedMode === 'single_market') {
      const siteKey = normalizeText(params.series_key || params.site_name)
      const singleMarketMap = snapshotTrendEntry.single_market || {}
      if (siteKey && singleMarketMap[siteKey]?.items?.length) {
        snapshotItems = singleMarketMap[siteKey]?.items ?? []
      } else if (siteKey) {
        const matchedEntry = Object.entries(singleMarketMap).find(([key]) => normalizeText(key) === siteKey)
        snapshotItems = matchedEntry?.[1]?.items ?? []
      } else {
        snapshotItems = Object.values(singleMarketMap)[0]?.items ?? []
      }
    } else {
      snapshotItems = snapshotTrendEntry.cross_market?.items ?? []
    }
    markStaticDataSource()
    const data = {
      mode: requestedMode,
      items: snapshotItems,
    }
    productTrendResponseCache.set(requestKey, {
      expiresAt: Date.now() + PRODUCT_TREND_RESPONSE_CACHE_TTL_MS,
      data,
    })
    return data
  })
  productTrendRequests.set(requestKey, requestPromise)
  requestPromise.finally(() => {
    productTrendRequests.delete(requestKey)
  })
  return requestPromise
}

export async function fetchLiancaiCategorySummary(params?: { source_name?: string }) {
  try {
    return await requestWithState(async () => {
      const { data } = await api.get<{ items: LiancaiCategorySummaryItem[] }>('/liancai/category-summary', { params })
      return data
    }, { affectGlobalState: false })
  } catch (error) {
    const snapshot = await loadMarketSnapshot()
    if (snapshot?.liancai_category_summary) {
      markStaticDataSource()
      return { items: snapshot.liancai_category_summary.items ?? [] }
    }
    throw error
  }
}

export async function fetchLiancaiFacets(params: { liancai_top_category?: string; liancai_subcategory?: string }) {
  const facetKey = `${normalizeText(params.liancai_top_category)}\u0001${normalizeText(params.liancai_subcategory)}`
  try {
    return await requestWithState(async () => {
      const { data } = await api.get<LiancaiFacetResponse>('/liancai/facets', { params, timeout: 45000 })
      return data
    }, { affectGlobalState: false })
  } catch (error) {
    const snapshot = await loadMarketSnapshot()
    if (snapshot?.liancai_facets) {
      markStaticDataSource()
      return snapshot.liancai_facets[facetKey] ?? { keywords: [], brands: [] }
    }
    throw error
  }
}

export async function generateMenuPlan(payload: {
  menu_text?: string
  menu_items?: Array<{ menu_name: string; ingredient_name?: string; remarks?: string }>
  diners: number
  tables: number
  preferred_province?: string
  preferred_city?: string
  preferred_location?: string
}) {
  return requestWithState(async () => {
    const { data } = await publicApi.post('/menu/plan', payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchSignalsOverview(params: { province?: string; city?: string; focus?: string }) {
  return requestWithState(async () => {
    const { data } = await api.get<SignalOverviewResponse>('/signals/overview', { params, timeout: 30000 })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSignalDetail(identityKey: string, params?: { province?: string; city?: string }) {
  return requestWithState(async () => {
    const { data } = await api.get<SignalInsightItem>(`/signals/${encodeURIComponent(identityKey)}`, { params, timeout: 30000 })
    return data
  }, { affectGlobalState: false })
}

export async function fetchProcurementRecommendation(payload: {
  menu_text?: string
  menu_items?: Array<{ menu_name: string; ingredient_name?: string; remarks?: string }>
  diners: number
  tables: number
  preferred_province?: string
  preferred_city?: string
  preferred_location?: string
}) {
  return requestWithState(async () => {
    const { data } = await publicApi.post<ProcurementRecommendationResponse>('/procurement/recommend', payload, { timeout: 30000 })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSalesDecisionContent(scene?: string) {
  return requestWithState(async () => {
    const { data } = await api.get<SalesDemoContentResponse>('/sales/decision-content', { params: { scene } })
    return data
  }, { affectGlobalState: false })
}

export const fetchSalesDemoContent = fetchSalesDecisionContent

export async function fetchPricingPackages() {
  return requestWithState(async () => {
    const { data } = await api.get<PricingPackagesResponse>('/pricing/packages')
    return data
  }, { affectGlobalState: false })
}

export async function fetchSuppliers(activeOnly = true) {
  return requestWithState(async () => {
    const { data } = await api.get<SupplierListResponse>('/suppliers', { params: { active_only: activeOnly } })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSupplierOverview(limit = 12) {
  return requestWithState(async () => {
    const { data } = await api.get<SupplierOverviewResponse>('/suppliers/overview', { params: { limit } })
    return data
  }, { affectGlobalState: false })
}

export async function createSupplier(payload: SupplierUpdatePayload) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierItem>('/suppliers', payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchProductSupplierQuotes(identityKey: string) {
  return requestWithState(async () => {
    const { data } = await api.get<SupplierQuoteCompareResponse>(`/product/${encodeURIComponent(identityKey)}/supplier-quotes`)
    return data
  }, { affectGlobalState: false })
}

export async function submitSupplierQuote(payload: SupplierQuoteCreatePayload) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierQuoteCreateResponse>('/supplier-prices', payload)
    return data
  }, { affectGlobalState: false })
}

export async function importSupplierQuotes(payload: SupplierQuoteImportPayload) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierQuoteImportResponse>('/supplier-prices/import', payload)
    return data
  }, { affectGlobalState: false })
}

export async function previewImportSupplierQuotes(payload: SupplierQuoteImportPreviewPayload) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierQuoteImportPreviewResponse>('/supplier-prices/import-preview', payload)
    return data
  }, { affectGlobalState: false })
}

export async function invalidateSupplierQuote(recordId: number, payload: SupplierQuoteInvalidatePayload = {}) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierQuoteInvalidateResponse>(`/supplier-prices/${recordId}/invalidate`, payload)
    return data
  }, { affectGlobalState: false })
}

export async function updateSupplier(supplierId: number, payload: SupplierUpdatePayload) {
  return requestWithState(async () => {
    const { data } = await api.put(`/suppliers/${supplierId}`, payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchSupplierQuotesBySupplier(
  supplierId: number,
  options: {
    limit?: number
    offset?: number
    status?: string
    keyword?: string
    start_quoted_at?: string
    end_quoted_at?: string
    price_identity_key?: string
  } = {},
) {
  return requestWithState(async () => {
    const { data } = await api.get<SupplierQuoteListResponse>(`/suppliers/${supplierId}/quotes`, { params: options })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSupplierQuoteActions(
  supplierId: number,
  options: SupplierQuoteActionQueryOptions = {},
) {
  return requestWithState(async () => {
    const { data } = await api.get<SupplierQuoteActionListResponse>(`/suppliers/${supplierId}/quote-actions`, { params: options })
    return data
  }, { affectGlobalState: false })
}

export async function createSupplierQuoteAction(supplierId: number, payload: SupplierQuoteActionCreatePayload) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierQuoteActionItem>(`/suppliers/${supplierId}/quote-actions`, payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchSupplierSettlementsBySupplier(
  supplierId: number,
  options: SupplierSettlementQueryOptions = {},
) {
  return requestWithState(async () => {
    const { data } = await api.get<SupplierSettlementListResponse>(`/suppliers/${supplierId}/settlements`, { params: options })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSupplierSettlementDetail(recordId: number) {
  return requestWithState(async () => {
    const { data } = await api.get<SupplierSettlementDetailResponse>(`/supplier-settlements/${recordId}`)
    return data
  }, { affectGlobalState: false })
}

export async function createSupplierSettlement(supplierId: number, payload: SupplierSettlementCreatePayload) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierSettlementCreateResponse>(`/suppliers/${supplierId}/settlements`, payload)
    return data
  }, { affectGlobalState: false })
}

export async function updateSupplierSettlement(recordId: number, payload: SupplierSettlementUpdatePayload) {
  return requestWithState(async () => {
    const { data } = await api.put<SupplierSettlementUpdateResponse>(`/supplier-settlements/${recordId}`, payload)
    return data
  }, { affectGlobalState: false })
}

export async function cancelSupplierSettlement(recordId: number, payload: SupplierSettlementCancelPayload = {}) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierSettlementCancelResponse>(`/supplier-settlements/${recordId}/cancel`, payload)
    return data
  }, { affectGlobalState: false })
}

export async function buildSupplierSettlementsFromQuotes(
  supplierId: number,
  payload: SupplierSettlementBuildFromQuotesPayload,
) {
  return requestWithState(async () => {
    const { data } = await api.post<SupplierSettlementBuildFromQuotesResponse>(
      `/suppliers/${supplierId}/settlements/build-from-quotes`,
      payload,
    )
    return data
  }, { affectGlobalState: false })
}
