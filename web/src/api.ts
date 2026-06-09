import {
  dataSourceState,
  getAccessToken,
  readAuthSession,
  writeAuthSession,
  clearAuthSession,
  extractApiErrorDetail,
  getApiErrorStatus,
  buildSnapshotProductSummary,
} from './apiSession'
import type { AuthSessionState } from './apiSession'
import { api, publicApi } from './apiHttpClient'
import {
  buildSnapshotProductOptions,
  filterSnapshotProductOptions,
  filterSnapshotSummaryRows,
  findSnapshotProductTrend,
  loadMarketSnapshot,
  markStaticDataSource,
  normalizeText,
  paginateItems,
} from './apiMarketSnapshot'
import { requestWithState } from './apiRequestState'
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
  LocationSuggestionResponse,
  LiancaiCategorySummaryItem,
  MarketSummaryItem,
  ProductTrendRow,
  PricingPackagesResponse,
  ProcurementRecommendationResponse,
  ProcurementPlanRecordListResponse,
  ProcurementPlanRecordResponse,
  ProcurementPlanSavePayload,
  SalesDemoContentResponse,
  SignalInsightItem,
  SignalOverviewResponse,
  SettingsSnapshotDocument,
  SettingsSnapshotSourceItem,
  SourceConfigUpdatePayload,
  SourceStrategyUpdatePayload,
  GlobalAlertRuleItem,
  CrawlStatusItem,
  SourceCoverageItem,
} from './types'

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

const AUTH_REQUEST_TIMEOUT = 60000

export {
  api,
  readAuthSession,
  writeAuthSession,
  clearAuthSession,
  getAccessToken,
  dataSourceState,
  extractApiErrorDetail,
  getApiErrorStatus,
  buildSnapshotProductSummary,
}
export type { AuthSessionState }

function normalizeSettingsSnapshotSource(source: SourceCoverageItem): SettingsSnapshotSourceItem {
  return {
    source_url: String(source.source_url || ''),
    source_name: source.source_name || null,
    configured_name: source.configured_name || null,
    enabled: source.enabled,
    market_scope: source.market_scope || null,
    market_category: source.market_category || null,
    notes: source.notes || null,
    preferred_fetch_mode: source.preferred_fetch_mode || null,
    strategy: source.strategy || null,
    timeout_seconds: source.timeout_seconds ?? null,
    retry_count: source.retry_count ?? null,
    request_delay_seconds: source.request_delay_seconds ?? null,
    blocked_status_codes: source.blocked_status_codes || null,
    verify_ssl: source.verify_ssl ?? null,
    api_strategy: source.api_strategy || null,
  }
}

export function buildSettingsSnapshotDocument(input: {
  crawlStatus?: CrawlStatusItem | null
  sourceCoverageRows?: SourceCoverageItem[]
  globalAlertRules?: GlobalAlertRuleItem[]
  selectedSourceUrl?: string | null
}): SettingsSnapshotDocument {
  const sourceCoverageRows = input.sourceCoverageRows || []
  const selectedSourceUrl = String(input.selectedSourceUrl || '').trim()
  const selectedSource = selectedSourceUrl
    ? sourceCoverageRows.find((item) => String(item.source_url || '').trim() === selectedSourceUrl)
    : null
  const normalizedSourceCoverage = sourceCoverageRows.map((item) => normalizeSettingsSnapshotSource(item))
  return {
    schema: 'battel.settings.snapshot',
    version: 1,
    generated_at: new Date().toISOString(),
    summary: {
      source_count: normalizedSourceCoverage.length,
      alert_rule_count: (input.globalAlertRules || []).length,
      selected_source_name: selectedSource?.configured_name || selectedSource?.source_name || null,
    },
    schedule: {
      enabled: Boolean(input.crawlStatus?.schedule_enabled),
      mode: input.crawlStatus?.schedule_mode === 'interval' ? 'interval' : 'daily_time',
      daily_run_time: input.crawlStatus?.schedule_daily_run_time || null,
      interval_seconds: Number(input.crawlStatus?.schedule_interval_seconds || 86400),
      fetch_mode: input.crawlStatus?.schedule_fetch_mode === 'playwright' ? 'playwright' : 'requests',
      target_scope: input.crawlStatus?.target_scope === 'province' || input.crawlStatus?.target_scope === 'city'
        ? input.crawlStatus.target_scope
        : 'all_saved',
      target_province: input.crawlStatus?.target_province || null,
      target_city: input.crawlStatus?.target_city || null,
    },
    source_coverage: normalizedSourceCoverage,
    selected_source_url: selectedSource?.source_url || selectedSourceUrl || null,
    selected_source_name: selectedSource?.source_name || selectedSource?.configured_name || null,
    selected_source_strategy: selectedSource ? normalizeSettingsSnapshotSource(selectedSource) : null,
    alert_rules: (input.globalAlertRules || []).map((item) => ({
      target_name: String(item.target_name || ''),
      threshold: Number(item.threshold || 0),
      note: item.note || null,
      group_name: item.group_name || null,
    })),
  }
}

export function parseSettingsSnapshotDocument(text: string) {
  const parsed = JSON.parse(text)
  if (!parsed || typeof parsed !== 'object') throw new Error('快照文件格式无效')
  if ((parsed as Record<string, unknown>).schema !== 'battel.settings.snapshot') throw new Error('快照文件标识不匹配')
  if ((parsed as Record<string, unknown>).version !== 1) throw new Error('快照版本不受支持')
  const snapshot = parsed as SettingsSnapshotDocument
  if (!Array.isArray(snapshot.source_coverage) || !Array.isArray(snapshot.alert_rules)) {
    throw new Error('快照内容不完整')
  }
  return snapshot
}

export function serializeSettingsSnapshotDocument(document: SettingsSnapshotDocument) {
  return JSON.stringify(document, null, 2)
}

function shouldUseStaticSnapshot(error: unknown) {
  const status = getApiErrorStatus(error)
  return status !== 401 && status !== 403
}

export function clearProcurementApiResponseCache() {
  productTrendRequests.clear()
  productTrendResponseCache.clear()
}

function assertProcurementApiAccess() {
  const sessions = [readAuthSession(), readAuthSession('procurement'), readAuthSession('admin')]
  const canUseProcurementApi = sessions.some((session) => {
    const role = session?.user?.role
    return Boolean(session?.access_token && (role === 'admin' || role === 'procurement'))
  })
  if (!canUseProcurementApi) {
    throw new Error('请先登录采购端账号')
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
    const { data } = await api.post<AuthLoginResponse>(
      '/auth/password/reset',
      payload,
      { timeout: AUTH_REQUEST_TIMEOUT },
    )
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
    const { data } = await api.delete<AuthUserDeleteResponse>(
      `/auth/users/${userId}`,
      { timeout: AUTH_REQUEST_TIMEOUT },
    )
    return data
  }, { affectGlobalState: false })
}

export async function fetchLocationOptions() {
  try {
    return await requestWithState(async () => {
      const { data } = await publicApi.get<LocationOptionsResponse>('/location/options')
      return data
    })
  } catch (error) {
    if (!shouldUseStaticSnapshot(error)) throw error
    const snapshot = await loadMarketSnapshot()
    if (snapshot?.location_options) {
      markStaticDataSource()
      return snapshot.location_options
    }
    throw error
  }
}

export async function fetchLocationSuggestion(latitude?: number, longitude?: number) {
  return requestWithState(async () => {
    const { data } = await publicApi.get<LocationSuggestionResponse>('/location/suggest', {
      params: latitude != null && longitude != null ? { latitude, longitude } : undefined,
      timeout: 8000,
    })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSourceCoverage() {
  assertProcurementApiAccess()
  try {
    return await requestWithState(async () => {
      const { data } = await api.get('/source/coverage', { timeout: 45000 })
      return data
    }, { affectGlobalState: false })
  } catch (error) {
    if (!shouldUseStaticSnapshot(error)) throw error
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
  assertProcurementApiAccess()
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
  assertProcurementApiAccess()
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
  target_scope?: 'all_saved' | 'province' | 'city'
  target_province?: string
  target_city?: string
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
  assertProcurementApiAccess()
  try {
    return await requestWithState(async () => {
      const { data } = await api.get('/market/summary', { params, timeout: 60000 })
      return data
    })
  } catch (error) {
    if (!shouldUseStaticSnapshot(error)) throw error
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

export async function fetchProductOptions(params: {
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
  assertProcurementApiAccess()
  try {
    return await requestWithState(async () => {
      const { data } = await api.get('/product/options', { params, timeout: 45000 })
      return data
    }, { affectGlobalState: false })
  } catch (error) {
    if (!shouldUseStaticSnapshot(error)) throw error
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

export async function fetchProductSummary(identityKey: string, params?: {
  province?: string
  city?: string
  source_name?: string
  liancai_top_category?: string
  liancai_subcategory?: string
  liancai_keyword?: string
  liancai_brand?: string
}) {
  assertProcurementApiAccess()
  const decodedIdentityKey = decodeURIComponent(identityKey)
  return requestWithState(async () => {
    const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/summary`, { params })
    return data
  }, { affectGlobalState: false })
}

export async function fetchProductTrend(identityKey: string, params: ProductTrendParams) {
  assertProcurementApiAccess()
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
    if (!shouldUseStaticSnapshot(error)) throw error
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
  assertProcurementApiAccess()
  try {
    return await requestWithState(async () => {
      const { data } = await api.get<{ items: LiancaiCategorySummaryItem[] }>('/liancai/category-summary', { params })
      return data
    }, { affectGlobalState: false })
  } catch (error) {
    if (!shouldUseStaticSnapshot(error)) throw error
    const snapshot = await loadMarketSnapshot()
    if (snapshot?.liancai_category_summary) {
      markStaticDataSource()
      return { items: snapshot.liancai_category_summary.items ?? [] }
    }
    throw error
  }
}

export async function fetchLiancaiFacets(params: { liancai_top_category?: string; liancai_subcategory?: string }) {
  assertProcurementApiAccess()
  const facetKey = `${normalizeText(params.liancai_top_category)}\u0001${normalizeText(params.liancai_subcategory)}`
  try {
    return await requestWithState(async () => {
      const { data } = await api.get<LiancaiFacetResponse>('/liancai/facets', { params, timeout: 45000 })
      return data
    }, { affectGlobalState: false })
  } catch (error) {
    if (!shouldUseStaticSnapshot(error)) throw error
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
  assertProcurementApiAccess()
  return requestWithState(async () => {
    const { data } = await api.post('/menu/plan', payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchSignalsOverview(params: { province?: string; city?: string; focus?: string }) {
  assertProcurementApiAccess()
  return requestWithState(async () => {
    const { data } = await api.get<SignalOverviewResponse>('/signals/overview', { params, timeout: 30000 })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSignalDetail(identityKey: string, params?: { province?: string; city?: string }) {
  assertProcurementApiAccess()
  return requestWithState(async () => {
    const { data } = await api.get<SignalInsightItem>(
      `/signals/${encodeURIComponent(identityKey)}`,
      { params, timeout: 30000 },
    )
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
  assertProcurementApiAccess()
  return requestWithState(async () => {
    const { data } = await api.post<ProcurementRecommendationResponse>(
      '/procurement/recommend',
      payload,
      { timeout: 30000 },
    )
    return data
  }, { affectGlobalState: false })
}

export async function saveProcurementPlanRecord(payload: ProcurementPlanSavePayload) {
  assertProcurementApiAccess()
  return requestWithState(async () => {
    const { data } = await api.post<ProcurementPlanRecordResponse>('/procurement/plans', payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchProcurementPlanRecords(params: { limit?: number; offset?: number } = {}) {
  assertProcurementApiAccess()
  return requestWithState(async () => {
    const { data } = await api.get<ProcurementPlanRecordListResponse>('/procurement/plans', { params, timeout: 30000 })
    return data
  }, { affectGlobalState: false })
}

export async function fetchProcurementPlanRecord(recordId: number) {
  assertProcurementApiAccess()
  return requestWithState(async () => {
    const { data } = await api.get<ProcurementPlanRecordResponse>(`/procurement/plans/${recordId}`, { timeout: 30000 })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSalesDecisionContent(scene?: string) {
  return requestWithState(async () => {
    const { data } = await publicApi.get<SalesDemoContentResponse>('/sales/decision-content', { params: { scene } })
    return data
  }, { affectGlobalState: false })
}

export const fetchSalesDemoContent = fetchSalesDecisionContent

export async function fetchPricingPackages() {
  return requestWithState(async () => {
    const { data } = await publicApi.get<PricingPackagesResponse>('/pricing/packages')
    return data
  }, { affectGlobalState: false })
}

export {
  buildSupplierSettlementsFromQuotes,
  cancelSupplierSettlement,
  createSupplier,
  createSupplierQuoteAction,
  createSupplierSettlement,
  fetchProductSupplierQuotes,
  fetchSupplierOverview,
  fetchSupplierQuoteActions,
  fetchSupplierQuotesBySupplier,
  fetchSupplierSettlementDetail,
  fetchSupplierSettlementsBySupplier,
  fetchSuppliers,
  importSupplierQuotes,
  invalidateSupplierQuote,
  previewImportSupplierQuotes,
  submitSupplierQuote,
  updateSupplier,
  updateSupplierSettlement,
} from './apiSupplierRequests'
