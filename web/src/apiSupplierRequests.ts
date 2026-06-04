import { api } from './apiHttpClient'
import { requestWithState } from './apiRequestState'
import type {
  SupplierItem,
  SupplierListResponse,
  SupplierOverviewResponse,
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
  SupplierUpdatePayload,
} from './types'

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
    const { data } = await api.get<SupplierQuoteCompareResponse>(
      `/product/${encodeURIComponent(identityKey)}/supplier-quotes`,
    )
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
    const { data } = await api.put<SupplierItem>(`/suppliers/${supplierId}`, payload)
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
    const { data } = await api.get<SupplierQuoteActionListResponse>(
      `/suppliers/${supplierId}/quote-actions`,
      { params: options },
    )
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
    const { data } = await api.get<SupplierSettlementListResponse>(
      `/suppliers/${supplierId}/settlements`,
      { params: options },
    )
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
    const { data } = await api.post<SupplierSettlementCancelResponse>(
      `/supplier-settlements/${recordId}/cancel`,
      payload,
    )
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
