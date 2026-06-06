import { reactive } from 'vue'
import type { AuthUserItem, MarketSummaryItem } from './types'

const AUTH_STORAGE_KEYS = {
  procurement: 'battel.auth.session.procurement',
  supplier: 'battel.auth.session.supplier',
  admin: 'battel.auth.session.admin',
} as const
const LEGACY_AUTH_STORAGE_KEY = 'battel.auth.session'
const AUTH_TOKEN_EXPIRY_SKEW_MS = 30_000

export type AuthSessionState = {
  access_token: string
  token_type: 'Bearer'
  expires_in: number
  user: AuthUserItem
}

type AuthSessionScope = keyof typeof AUTH_STORAGE_KEYS

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

function resolveAuthSessionScope(scope?: AuthSessionScope): AuthSessionScope {
  if (scope) return scope
  if (typeof window === 'undefined') return 'procurement'
  const pathname = window.location.pathname
  if (pathname === '/admin') return 'admin'
  if (pathname === '/supplier-portal' || pathname === '/supplier-backend') return 'supplier'
  return 'procurement'
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const [, payload] = String(token || '').split('.')
  if (!payload) return null
  try {
    const normalizedPayload = payload.replace(/-/g, '+').replace(/_/g, '/')
    const paddedPayload = normalizedPayload.padEnd(Math.ceil(normalizedPayload.length / 4) * 4, '=')
    return JSON.parse(window.atob(paddedPayload)) as Record<string, unknown>
  } catch {
    return null
  }
}

function isExpiredJwtSession(session: AuthSessionState) {
  const payload = decodeJwtPayload(session.access_token)
  if (!payload || typeof payload.exp !== 'number') return false
  return payload.exp * 1000 <= Date.now() + AUTH_TOKEN_EXPIRY_SKEW_MS
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
    if (parsed?.access_token && isExpiredJwtSession(parsed)) {
      window.localStorage.removeItem(storageKey)
      window.localStorage.removeItem(LEGACY_AUTH_STORAGE_KEY)
      return null
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

export const dataSourceState = reactive({
  mode: 'live' as 'live' | 'static' | 'error',
  lastError: '',
})

function normalizeSnapshotIdentity(value: unknown) {
  return String(value ?? '').trim().toLowerCase()
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

export function formatApiErrorMessage(error: unknown) {
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
