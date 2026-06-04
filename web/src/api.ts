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
  SalesDemoContentResponse,
  SignalInsightItem,
  SignalOverviewResponse,
  SourceConfigUpdatePayload,
  SourceStrategyUpdatePayload,
  GlobalAlertRuleItem,
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

export async function fetchLocationSuggestion(latitude?: number, longitude?: number) {
  return requestWithState(async () => {
    const { data } = await api.get<LocationSuggestionResponse>('/location/suggest', {
      params: latitude != null && longitude != null ? { latitude, longitude } : undefined,
      timeout: 8000,
    })
    return data
  }, { affectGlobalState: false })
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

export async function fetchProductSummary(identityKey: string, params?: {
  province?: string
  city?: string
  source_name?: string
  liancai_top_category?: string
  liancai_subcategory?: string
  liancai_keyword?: string
  liancai_brand?: string
}) {
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
  return requestWithState(async () => {
    const { data } = await publicApi.post<ProcurementRecommendationResponse>(
      '/procurement/recommend',
      payload,
      { timeout: 30000 },
    )
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
