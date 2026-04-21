import axios from 'axios'
import { reactive } from 'vue'
import type {
  LocationOptionsResponse,
  PricingPackagesResponse,
  ProcurementRecommendationResponse,
  SalesDemoContentResponse,
  SignalInsightItem,
  SignalOverviewResponse,
  SupplierListResponse,
  SupplierItem,
  SupplierQuoteCompareResponse,
  SupplierQuoteCreatePayload,
  SupplierQuoteCreateResponse,
  SupplierOverviewResponse,
  SupplierUpdatePayload,
} from './types'

function normalizeApiBaseUrl(rawValue?: string) {
  const value = (rawValue || '/api').trim()
  if (!value) {
    return '/api'
  }
  return value.endsWith('/') ? value.slice(0, -1) : value
}

const apiBaseUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL)

export const api = axios.create({
  // Production defaults to the reverse-proxied /api path.
  baseURL: apiBaseUrl,
  timeout: 15000,
})

export const dataSourceState = reactive({
  mode: 'live' as 'live' | 'error',
  lastError: '',
})

type RequestStateOptions = {
  affectGlobalState?: boolean
}

function isAxiosError(error: unknown) {
  return typeof error === 'object' && error !== null && 'isAxiosError' in error
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
    return '当前请求没有权限，请检查接口认证设置'
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

export async function fetchLocationOptions() {
  return requestWithState(async () => {
    const { data } = await api.get<LocationOptionsResponse>('/location/options')
    return data
  })
}

export async function fetchSourceCoverage() {
  return requestWithState(async () => {
    const { data } = await api.get('/source/coverage')
    return data
  }, { affectGlobalState: false })
}

export async function fetchCrawlStatus() {
  return requestWithState(async () => {
    const { data } = await api.get('/crawl/status')
    return data
  }, { affectGlobalState: false })
}

export async function triggerCrawlRun() {
  return requestWithState(async () => {
    const { data } = await api.post('/crawl/run')
    return data
  }, { affectGlobalState: false })
}

export async function updateCrawlSchedule(payload: {
  enabled: boolean
  interval_seconds: number
  fetch_mode?: 'requests' | 'playwright'
}) {
  return requestWithState(async () => {
    const { data } = await api.post('/crawl/schedule', payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchMarketSummary(params: { province?: string; city?: string; keyword?: string }) {
  return requestWithState(async () => {
    const { data } = await api.get('/market/summary', { params })
    return data
  })
}

export async function fetchProductOptions(params: { province?: string; city?: string }) {
  return requestWithState(async () => {
    const { data } = await api.get('/product/options', { params })
    return data
  }, { affectGlobalState: false })
}

export async function fetchProductSummary(identityKey: string, params?: { province?: string; city?: string }) {
  return requestWithState(async () => {
    const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/summary`, { params })
    return data
  }, { affectGlobalState: false })
}

export async function fetchProductTrend(identityKey: string, params: { mode: string; site_name?: string; series_key?: string; province?: string; city?: string }) {
  return requestWithState(async () => {
    const { data } = await api.get(`/product/${encodeURIComponent(identityKey)}/trend`, {
      params,
      timeout: 45000,
    })
    return data
  }, { affectGlobalState: false })
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
    const { data } = await api.post('/menu/plan', payload)
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
    const { data } = await api.post<ProcurementRecommendationResponse>('/procurement/recommend', payload, { timeout: 30000 })
    return data
  }, { affectGlobalState: false })
}

export async function fetchSalesDemoContent(scene?: string) {
  return requestWithState(async () => {
    const { data } = await api.get<SalesDemoContentResponse>('/sales/demo-content', { params: { scene } })
    return data
  }, { affectGlobalState: false })
}

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

export async function updateSupplier(supplierId: number, payload: SupplierUpdatePayload) {
  return requestWithState(async () => {
    const { data } = await api.put(`/suppliers/${supplierId}`, payload)
    return data
  }, { affectGlobalState: false })
}

export async function fetchSupplierQuotesBySupplier(supplierId: number, limit = 20) {
  return requestWithState(async () => {
    const { data } = await api.get(`/suppliers/${supplierId}/quotes`, { params: { limit } })
    return data
  }, { affectGlobalState: false })
}
