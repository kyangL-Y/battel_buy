export interface SupplierItem {
  id: number
  supplier_name: string
  contact_name?: string | null
  contact_phone?: string | null
  market_scope?: string | null
  market_category?: string | null
  channel?: string | null
  notes?: string | null
  is_active?: boolean | null
  created_at?: string | null
  updated_at?: string | null
  quote_count?: number | null
  latest_quoted_at?: string | null
  account_id?: number | null
  account_username?: string | null
  account_display_name?: string | null
  account_is_active?: boolean | null
}

export interface SupplierCategorySummaryItem {
  market_category: string
  supplier_count: number
  active_supplier_count: number
  quote_count: number
  latest_quoted_at?: string | null
}

export interface SupplierOverviewSummary {
  supplier_count: number
  active_supplier_count: number
  inactive_supplier_count: number
  category_count: number
  total_quote_count: number
  latest_quoted_at?: string | null
}

export interface SupplierQuoteItem {
  record_id?: number | null
  supplier_id: number
  supplier_name: string
  contact_name?: string | null
  contact_phone?: string | null
  market_scope?: string | null
  market_category?: string | null
  channel?: string | null
  price_identity_key: string
  price_identity_label?: string | null
  product_name?: string | null
  category?: string | null
  spec_text?: string | null
  quote_price?: number | null
  quote_unit?: string | null
  box_price?: number | null
  tax_price?: number | null
  inventory_status?: string | null
  remarks?: string | null
  quoted_by?: string | null
  status?: string | null
  invalidated_at?: string | null
  invalidated_reason?: string | null
  quoted_at?: string | null
  price_diff_to_market_lowest?: number | null
  price_diff_to_market_average?: number | null
  comparison_label?: string | null
}

export interface SupplierQuoteCompareSummary {
  identity_key: string
  product_name: string
  supplier_count: number
  market_lowest_price?: number | null
  market_lowest_site?: string | null
  market_lowest_source_name?: string | null
  market_lowest_source_tier?: string | null
  market_average_price?: number | null
  lowest_quote?: number | null
  lowest_quote_supplier?: string | null
  latest_quoted_at?: string | null
}

export interface SupplierQuoteCompareResponse {
  summary: SupplierQuoteCompareSummary
  items: SupplierQuoteItem[]
}

export interface SupplierQuoteCreatePayload {
  price_identity_key: string
  source_record_id?: number
  supplier_id?: number
  supplier_name?: string
  contact_name?: string
  contact_phone?: string
  market_scope?: string
  market_category?: string
  channel?: string
  product_name?: string
  price_identity_label?: string
  category?: string
  spec_text?: string
  quote_price: number
  quote_unit?: string
  box_price?: number
  tax_price?: number
  inventory_status?: string
  remarks?: string
  quoted_by?: string
  quoted_at?: string
}

export interface SupplierQuoteCreateResponse {
  item: SupplierQuoteItem
}

export interface SupplierQuoteImportItemPayload {
  row_number?: number
  price_identity_key?: string
  price_identity_label?: string
  product_name?: string
  category?: string
  spec_text?: string
  market_scope?: string
  market_category?: string
  channel?: string
  quote_price?: number
  quote_unit?: string
  box_price?: number
  tax_price?: number
  inventory_status?: string
  remarks?: string
  quoted_at?: string
  quoted_by?: string
}

export type SupplierQuoteImportMode = 'append' | 'skip_duplicate' | 'override_latest'
export type SupplierQuoteDuplicateField =
  | 'quote_price'
  | 'quote_unit'
  | 'box_price'
  | 'tax_price'
  | 'inventory_status'
  | 'remarks'
  | 'channel'
  | 'market_category'
  | 'market_scope'

export interface SupplierQuoteImportPayload {
  supplier_id: number
  operator_name?: string
  file_name?: string
  import_mode?: SupplierQuoteImportMode
  duplicate_match_fields?: SupplierQuoteDuplicateField[]
  abnormal_change_ratio_threshold?: number | null
  items: SupplierQuoteImportItemPayload[]
}

export interface SupplierQuoteImportPreviewPayload {
  supplier_id: number
  import_mode?: SupplierQuoteImportMode
  duplicate_match_fields?: SupplierQuoteDuplicateField[]
  abnormal_change_ratio_threshold?: number | null
  items: SupplierQuoteImportItemPayload[]
}

export interface SupplierQuoteImportResultItem {
  row_number: number
  status: 'success' | 'failed' | 'skipped'
  skipped?: boolean | null
  failure_reason?: string | null
  record_id?: number | null
  price_identity_key?: string | null
  price_identity_label?: string | null
  product_name?: string | null
  duplicate_match_fields?: SupplierQuoteDuplicateField[]
  abnormal_change_ratio?: number | null
  abnormal_change_hint?: string | null
}

export interface SupplierQuoteImportResponse {
  total_count: number
  success_count: number
  failed_count: number
  skipped_count?: number
  items: SupplierQuoteImportResultItem[]
}

export interface SupplierQuoteImportPreviewItem {
  row_number: number
  price_identity_key?: string | null
  preview_status: 'append' | 'skip_duplicate' | 'override_latest' | 'invalid'
  preview_reason?: string | null
  existing_record_id?: number | null
  existing_quote_price?: number | null
  existing_quote_unit?: string | null
  existing_quoted_at?: string | null
  existing_remarks?: string | null
  duplicate_match_fields?: SupplierQuoteDuplicateField[]
  abnormal_change_ratio?: number | null
  abnormal_change_hint?: string | null
}

export interface SupplierQuoteImportPreviewResponse {
  items: SupplierQuoteImportPreviewItem[]
}

export interface SupplierQuoteInvalidatePayload {
  reason?: string
  operator_name?: string
}

export interface SupplierQuoteInvalidateResponse {
  item: SupplierQuoteItem
}

export interface SupplierQuoteActionItem {
  id: number
  supplier_id: number
  supplier_name: string
  record_id?: number | null
  target_record_id?: number | null
  action_type: string
  action_reason?: string | null
  operator_name?: string | null
  action_payload?: Record<string, unknown> | string | null
  created_at?: string | null
  price_identity_key?: string | null
  price_identity_label?: string | null
  product_name?: string | null
  quote_price?: number | null
  quote_unit?: string | null
  quoted_at?: string | null
  target_price_identity_label?: string | null
  target_product_name?: string | null
  target_quote_price?: number | null
  target_quoted_at?: string | null
}

export interface SupplierQuoteActionCreatePayload {
  action_type: string
  record_id?: number
  target_record_id?: number
  action_reason?: string
  operator_name?: string
  action_payload?: Record<string, unknown> | string
}

export interface SupplierQuoteActionListResponse {
  items: SupplierQuoteActionItem[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface SupplierQuoteActionQueryOptions {
  limit?: number
  offset?: number
  action_type?: string
  operator_name?: string
  keyword?: string
  start_created_at?: string
  end_created_at?: string
}

export interface SupplierQuoteListResponse {
  items: SupplierQuoteItem[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export type SupplierSettlementStatus = 'pending' | 'partial' | 'paid' | 'cancelled'

export interface SupplierSettlementItem {
  id: number
  supplier_id: number
  supplier_name: string
  contact_name?: string | null
  contact_phone?: string | null
  market_scope?: string | null
  market_category?: string | null
  channel?: string | null
  settlement_title: string
  period_start?: string | null
  period_end?: string | null
  quote_record_ids: number[]
  record_count: number
  total_amount: number
  paid_amount: number
  pending_amount: number
  status: SupplierSettlementStatus
  payment_due_date?: string | null
  payment_date?: string | null
  remarks?: string | null
  created_by?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface SupplierSettlementQueryOptions {
  limit?: number
  offset?: number
  status?: SupplierSettlementStatus | string
  keyword?: string
  start_period_start?: string
  end_period_end?: string
}

export interface SupplierSettlementListResponse {
  items: SupplierSettlementItem[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface SupplierSettlementDetailResponse {
  item: SupplierSettlementItem
  quote_items: SupplierQuoteItem[]
}

export interface SupplierSettlementCreatePayload {
  settlement_title: string
  period_start?: string
  period_end?: string
  quote_record_ids?: number[]
  total_amount?: number
  paid_amount?: number
  status?: SupplierSettlementStatus
  payment_due_date?: string
  payment_date?: string
  remarks?: string
  created_by?: string
}

export type SupplierSettlementCreateResponse = SupplierSettlementItem

export interface SupplierSettlementUpdatePayload {
  settlement_title?: string
  period_start?: string
  period_end?: string
  quote_record_ids?: number[]
  total_amount?: number
  paid_amount?: number
  status?: SupplierSettlementStatus
  payment_due_date?: string
  payment_date?: string
  remarks?: string
  operator_name?: string
}

export type SupplierSettlementUpdateResponse = SupplierSettlementItem

export interface SupplierSettlementCancelPayload {
  operator_name?: string
  cancel_reason?: string
}

export type SupplierSettlementCancelResponse = SupplierSettlementItem

export interface SupplierSettlementBuildFromQuotesPayload {
  settlement_title: string
  quote_record_ids: number[]
  paid_amount?: number
  payment_due_date?: string
  remarks?: string
  created_by?: string
}

export type SupplierSettlementBuildFromQuotesResponse = SupplierSettlementItem

export interface SupplierListResponse {
  items: SupplierItem[]
}

export interface SupplierOverviewResponse {
  summary: SupplierOverviewSummary
  category_items: SupplierCategorySummaryItem[]
  recent_quotes: SupplierQuoteItem[]
}

export interface SupplierUpdatePayload {
  supplier_name: string
  contact_name?: string
  contact_phone?: string
  market_scope?: string
  market_category?: string
  channel?: string
  notes?: string
  is_active: boolean
  account_username?: string
  account_password?: string
  account_display_name?: string
  account_is_active?: boolean
}
