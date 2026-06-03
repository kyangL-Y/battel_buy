import {
  buildSnapshotProductSummary,
  clearAuthSession,
  dataSourceState,
  extractApiErrorDetail,
  getAccessToken,
  readAuthSession,
  writeAuthSession,
} from './apiSession'
import type {
  AuthLoginPayload,
  AuthMeResponse,
  AuthPasswordResetPayload,
  AuthUserCreatePayload,
  AuthUserDeleteResponse,
  AuthUserItem,
  AuthUserListResponse,
  AuthUserUpdatePayload,
  LiancaiFacetResponse,
  LiancaiCategorySummaryItem,
  LocationOptionsResponse,
  LocationSuggestionResponse,
  MarketSummaryItem,
  ProductOptionItem,
  ProductTrendRow,
  ProcurementRecommendationResponse,
  SalesDemoContentResponse,
  SignalInsightItem,
  SignalOverviewResponse,
  SourceConfigUpdatePayload,
  SourceStrategyUpdatePayload,
  GlobalAlertRuleItem,
  SupplierOverviewResponse,
  SupplierQuoteCreatePayload,
  SupplierQuoteCreateResponse,
  SupplierQuoteCompareResponse,
  SupplierListResponse,
} from './types'
import type { AuthSessionState } from './apiSession'

type ApiModule = typeof import('./api')

let apiModulePromise: Promise<ApiModule> | null = null

function loadApiModule() {
  if (!apiModulePromise) {
    apiModulePromise = import('./api')
  }
  return apiModulePromise
}

export {
  buildSnapshotProductSummary,
  clearAuthSession,
  dataSourceState,
  extractApiErrorDetail,
  getAccessToken,
  readAuthSession,
  writeAuthSession,
}
export type { AuthSessionState }

export async function login(payload: AuthLoginPayload) {
  return (await loadApiModule()).login(payload)
}

export async function resetAuthPassword(payload: AuthPasswordResetPayload) {
  return (await loadApiModule()).resetAuthPassword(payload)
}

export async function fetchCurrentUser(): Promise<AuthMeResponse> {
  return (await loadApiModule()).fetchCurrentUser()
}

export async function fetchAuthUsers(params: { role?: string; status?: string; keyword?: string } = {}): Promise<AuthUserListResponse> {
  return (await loadApiModule()).fetchAuthUsers(params)
}

export async function createAuthUser(payload: AuthUserCreatePayload): Promise<AuthUserItem> {
  return (await loadApiModule()).createAuthUser(payload)
}

export async function updateAuthUser(userId: number, payload: AuthUserUpdatePayload): Promise<AuthUserItem> {
  return (await loadApiModule()).updateAuthUser(userId, payload)
}

export async function deleteAuthUser(userId: number): Promise<AuthUserDeleteResponse> {
  return (await loadApiModule()).deleteAuthUser(userId)
}

export async function fetchLocationOptions(): Promise<LocationOptionsResponse> {
  return (await loadApiModule()).fetchLocationOptions()
}

export async function fetchLocationSuggestion(latitude?: number, longitude?: number): Promise<LocationSuggestionResponse> {
  return (await loadApiModule()).fetchLocationSuggestion(latitude, longitude)
}

export async function fetchSourceCoverage() {
  return (await loadApiModule()).fetchSourceCoverage()
}

export async function updateSourceCoverage(payload: SourceConfigUpdatePayload) {
  return (await loadApiModule()).updateSourceCoverage(payload)
}

export async function updateSourceStrategy(payload: SourceStrategyUpdatePayload) {
  return (await loadApiModule()).updateSourceStrategy(payload)
}

export async function fetchGlobalAlertRules(): Promise<{ items: GlobalAlertRuleItem[] }> {
  return (await loadApiModule()).fetchGlobalAlertRules()
}

export async function updateGlobalAlertRules(items: GlobalAlertRuleItem[]): Promise<{ items: GlobalAlertRuleItem[] }> {
  return (await loadApiModule()).updateGlobalAlertRules(items)
}

export async function fetchCrawlStatus() {
  return (await loadApiModule()).fetchCrawlStatus()
}

export async function triggerCrawlRun(payload: {
  target_scope?: 'all_saved' | 'province' | 'city'
  target_province?: string
  target_city?: string
  source_url?: string
  source_name?: string
} = {}) {
  return (await loadApiModule()).triggerCrawlRun(payload)
}

export async function updateCrawlSchedule(payload: {
  enabled: boolean
  mode?: 'interval' | 'daily_time'
  daily_run_time?: string | null
  interval_seconds: number
  fetch_mode?: 'requests' | 'playwright'
}) {
  return (await loadApiModule()).updateCrawlSchedule(payload)
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
  return (await loadApiModule()).fetchMarketSummary(params)
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
  return (await loadApiModule()).fetchProductOptions(params)
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
  return (await loadApiModule()).fetchProductSummary(identityKey, params)
}

export async function fetchProductTrend(identityKey: string, params: {
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
}) {
  return (await loadApiModule()).fetchProductTrend(identityKey, params)
}

export async function fetchLiancaiCategorySummary(params?: { source_name?: string }): Promise<{ items: LiancaiCategorySummaryItem[] }> {
  return (await loadApiModule()).fetchLiancaiCategorySummary(params)
}

export async function fetchLiancaiFacets(params: { liancai_top_category?: string; liancai_subcategory?: string }): Promise<LiancaiFacetResponse> {
  return (await loadApiModule()).fetchLiancaiFacets(params)
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
  return (await loadApiModule()).generateMenuPlan(payload)
}

export async function fetchSignalsOverview(params: { province?: string; city?: string; focus?: string }): Promise<SignalOverviewResponse> {
  return (await loadApiModule()).fetchSignalsOverview(params)
}

export async function fetchSignalDetail(identityKey: string, params?: { province?: string; city?: string }): Promise<SignalInsightItem> {
  return (await loadApiModule()).fetchSignalDetail(identityKey, params)
}

export async function fetchProcurementRecommendation(payload: {
  menu_text?: string
  menu_items?: Array<{ menu_name: string; ingredient_name?: string; remarks?: string }>
  diners: number
  tables: number
  preferred_province?: string
  preferred_city?: string
  preferred_location?: string
}): Promise<ProcurementRecommendationResponse> {
  return (await loadApiModule()).fetchProcurementRecommendation(payload)
}

export async function fetchSalesDecisionContent(scene?: string): Promise<SalesDemoContentResponse> {
  return (await loadApiModule()).fetchSalesDecisionContent(scene)
}

export const fetchSalesDemoContent = fetchSalesDecisionContent

export async function fetchSupplierOverview(limit = 12): Promise<SupplierOverviewResponse> {
  return (await loadApiModule()).fetchSupplierOverview(limit)
}

export async function fetchSuppliers(activeOnly = true): Promise<SupplierListResponse> {
  return (await loadApiModule()).fetchSuppliers(activeOnly)
}

export async function fetchProductSupplierQuotes(identityKey: string): Promise<SupplierQuoteCompareResponse> {
  return (await loadApiModule()).fetchProductSupplierQuotes(identityKey)
}

export async function submitSupplierQuote(payload: SupplierQuoteCreatePayload): Promise<SupplierQuoteCreateResponse> {
  return (await loadApiModule()).submitSupplierQuote(payload)
}
