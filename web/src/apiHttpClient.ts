import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { getAccessToken } from './apiSession'

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

export type LazyHttpClient = {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
  post<T = unknown>(url: string, payload?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
  put<T = unknown>(url: string, payload?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
}

let authenticatedHttpClientPromise: Promise<AxiosInstance> | null = null
let publicHttpClientPromise: Promise<AxiosInstance> | null = null

async function createHttpClient() {
  const axiosModule = await import('axios')
  return axiosModule.default.create({
    // Production defaults to the reverse-proxied /api path.
    baseURL: apiBaseUrl,
    timeout: 30000,
  })
}

async function getAuthenticatedHttpClient() {
  if (!authenticatedHttpClientPromise) {
    authenticatedHttpClientPromise = createHttpClient()
  }
  return authenticatedHttpClientPromise
}

async function getPublicHttpClient() {
  if (!publicHttpClientPromise) {
    publicHttpClientPromise = createHttpClient()
  }
  return publicHttpClientPromise
}

function withAuthHeader(config: AxiosRequestConfig = {}) {
  const token = getAccessToken()
  if (!token) {
    return config
  }
  return {
    ...config,
    headers: {
      ...(config.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  }
}

export const api: LazyHttpClient = {
  async get(url, config) {
    const httpClient = await getAuthenticatedHttpClient()
    return httpClient.get(url, withAuthHeader(config))
  },
  async post(url, payload, config) {
    const httpClient = await getAuthenticatedHttpClient()
    return httpClient.post(url, payload, withAuthHeader(config))
  },
  async put(url, payload, config) {
    const httpClient = await getAuthenticatedHttpClient()
    return httpClient.put(url, payload, withAuthHeader(config))
  },
  async delete(url, config) {
    const httpClient = await getAuthenticatedHttpClient()
    return httpClient.delete(url, withAuthHeader(config))
  },
}

export const publicApi: LazyHttpClient = {
  async get(url, config) {
    const httpClient = await getPublicHttpClient()
    return httpClient.get(url, config)
  },
  async post(url, payload, config) {
    const httpClient = await getPublicHttpClient()
    return httpClient.post(url, payload, config)
  },
  async put(url, payload, config) {
    const httpClient = await getPublicHttpClient()
    return httpClient.put(url, payload, config)
  },
  async delete(url, config) {
    const httpClient = await getPublicHttpClient()
    return httpClient.delete(url, config)
  },
}
