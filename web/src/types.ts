export interface MarketSummaryItem {
  product_name: string
  price_identity_key?: string
  group_name?: string | null
  category?: string | null
  spec_text?: string | null
  liancai_top_category?: string | null
  liancai_subcategory?: string | null
  liancai_keyword?: string | null
  liancai_brand_id?: string | null
  liancai_brand_name?: string | null
  site_count?: number | null
  market_count?: number | null
  price_observation_count?: number | null
  price_unit_basis?: string | null
  lowest_price?: number | null
  lowest_price_site?: string | null
  highest_price?: number | null
  highest_price_site?: string | null
  current_lowest_price?: number | null
  current_highest_price?: number | null
  current_lowest_site?: string | null
  current_highest_site?: string | null
  price_span?: number | null
  average_price?: number | null
  region_label?: string | null
  source_names?: string | null
  source_display_names?: string | null
  latest_captured_at?: string | null
  captured_dates?: string | null
  image_url?: string | null
}

export interface SourceCoverageItem {
  source_url: string
  configured_name?: string | null
  source_name?: string | null
  source_tier?: string | null
  strategy?: string | null
  preferred_fetch_mode?: 'requests' | 'playwright' | 'api' | null
  timeout_seconds?: number | null
  retry_count?: number | null
  request_delay_seconds?: number | null
  blocked_status_codes?: number[] | null
  verify_ssl?: boolean | null
  api_strategy?: string | null
  enabled?: boolean | null
  market_scope?: string | null
  market_category?: string | null
  market_subcategory?: string | null
  channel?: string | null
  notes?: string | null
  product_key_count?: number | null
  comparable_item_count?: number | null
  source_item_count?: number | null
  market_count?: number | null
  price_record_count?: number | null
  latest_capture?: string | null
  failed_count?: number | null
  last_failure?: string | null
  status?: string | null
}

export interface SourceConfigUpdatePayload {
  source_url: string
  enabled: boolean
  configured_name?: string
  market_scope?: string
  market_category?: string
  notes?: string
}

export interface SourceStrategyUpdatePayload {
  source_name: string
  preferred_fetch_mode?: 'requests' | 'playwright' | 'api'
  strategy?: string
  timeout_seconds?: number
  retry_count?: number
  request_delay_seconds?: number
  blocked_status_codes?: number[]
  verify_ssl?: boolean
  api_strategy?: string
}

export interface GlobalAlertRuleItem {
  target_name: string
  threshold: number
  note?: string | null
  group_name?: string | null
}

export interface SettingsChangeLogItem {
  id: string
  changed_at: string
  actor_name: string
  action_type: 'schedule' | 'source_config' | 'source_strategy' | 'global_alert'
  target_name: string
  summary: string
}

export interface ProductOptionItem {
  price_identity_key: string
  price_identity_label: string
  site_count: number
  price_observation_count?: number | null
  latest_captured_at?: string | null
  source_name?: string | null
  source_category?: string | null
  liancai_top_category?: string | null
  liancai_subcategory?: string | null
  liancai_keyword?: string | null
  liancai_brand_name?: string | null
  image_url?: string | null
}

export interface ProductTrendRow {
  site_name?: string | null
  source_name?: string | null
  source_tier?: string | null
  liancai_top_category?: string | null
  liancai_subcategory?: string | null
  liancai_keyword?: string | null
  liancai_brand_id?: string | null
  liancai_brand_name?: string | null
  market_name?: string | null
  region_label?: string | null
  province?: string | null
  city?: string | null
  current_price?: number | null
  captured_at?: string | null
  product_name?: string | null
  trend_series_name?: string | null
  trend_series_key?: string | null
  trend_meta_label?: string | null
}

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

export type SupplierRegistrationRequestStatus = 'pending' | 'approved' | 'rejected'

export interface SupplierRegistrationRequestItem {
  id: number
  company_name: string
  contact_name?: string | null
  contact_phone?: string | null
  username: string
  status: SupplierRegistrationRequestStatus
  review_notes?: string | null
  supplier_id?: number | null
  reviewed_by?: string | null
  reviewed_at?: string | null
  created_at?: string | null
  updated_at?: string | null
  supplier_name?: string | null
  market_category?: string | null
  channel?: string | null
  supplier_is_active?: boolean | null
}

export type AuthUserRole = 'admin' | 'supplier'

export interface AuthSupplierProfile {
  supplier_id: number
  supplier_name: string
  market_category?: string | null
  channel?: string | null
  market_scope?: string | null
  is_active?: boolean | null
}

export interface AuthUserItem {
  id: number
  username: string
  role: AuthUserRole
  display_name?: string | null
  is_active?: boolean | null
  is_deleted?: boolean | null
  supplier_id?: number | null
  supplier_profile?: AuthSupplierProfile | null
  last_login_at?: string | null
  deleted_at?: string | null
  deleted_by?: string | null
  deleted_username?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface AuthLoginPayload {
  username: string
  password: string
}

export interface AuthLoginResponse {
  access_token: string
  token_type: 'Bearer'
  expires_in: number
  user: AuthUserItem
}

export interface AuthMeResponse {
  user: AuthUserItem
}

export interface AuthUserListResponse {
  items: AuthUserItem[]
}

export interface AuthUserCreatePayload {
  username: string
  password: string
  role: AuthUserRole
  supplier_id?: number | null
  display_name?: string
  is_active: boolean
}

export interface AuthUserUpdatePayload {
  username: string
  password?: string
  role: AuthUserRole
  supplier_id?: number | null
  display_name?: string
  is_active: boolean
}

export interface AuthUserDeleteResponse {
  deleted: boolean
  user_id: number
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

export interface SupplierRegistrationRequestListResponse {
  items: SupplierRegistrationRequestItem[]
}

export interface SupplierRegistrationCreatePayload {
  company_name: string
  contact_name?: string
  contact_phone: string
  username: string
}

export interface SupplierRegistrationReviewPayload {
  supplier_name?: string
  contact_name?: string
  contact_phone?: string
  market_scope?: string
  market_category?: string
  channel?: string
  notes?: string
  account_display_name?: string
  account_password?: string
  account_is_active?: boolean
  supplier_is_active?: boolean
  review_notes?: string
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

export interface MenuPlanRow {
  menu_name: string
  ingredient_name: string
  identity_key?: string | null
  price_identity_key?: string | null
  product_identity_key?: string | null
  product_label?: string | null
  estimated_quantity?: number | null
  quantity_unit?: string | null
  price_unit_basis?: string | null
  reference_price?: number | null
  estimated_cost?: number | null
  recommended_market?: string | null
  recommended_site?: string | null
  province?: string | null
  city?: string | null
  backup_market?: string | null
  backup_site?: string | null
  source_tier?: string | null
  backup_source_tier?: string | null
  source_priority_label?: string | null
  backup_source_priority_label?: string | null
  distance_label?: string | null
  price_status?: string | null
  remarks?: string | null
}

export interface CrawlStatusItem {
  is_running: boolean
  last_run_source?: string | null
  last_started_at?: string | null
  last_finished_at?: string | null
  last_success_at?: string | null
  last_error?: string | null
  current_source_name?: string | null
  current_source_index?: number | null
  current_source_progress?: number | null
  current_source_detail?: string | null
  completed_sources?: number | null
  progress_percent?: number | null
  last_total_sources?: number | null
  last_total_results?: number | null
  last_success_count?: number | null
  last_failed_count?: number | null
  target_source_url?: string | null
  target_source_name?: string | null
  next_run_at?: string | null
  schedule_enabled: boolean
  schedule_mode?: 'interval' | 'daily_time' | null
  schedule_daily_run_time?: string | null
  schedule_interval_seconds: number
  schedule_fetch_mode?: 'requests' | 'playwright' | null
}

export interface LiancaiCategorySummaryItem {
  liancai_top_category: string
  liancai_subcategory: string
  liancai_keyword?: string
  liancai_brand_id?: string
  liancai_brand_name?: string
  product_count: number
}

export interface LiancaiFacetResponse {
  keywords: string[]
  brands: string[]
}

export interface LocationOptionsResponse {
  provinces: string[]
  cities: string[]
  province_city_map: Record<string, string[]>
}

export interface SignalMetricItem {
  label: string
  value: string
  detail?: string | null
}

export interface SignalInsightItem {
  identity_key: string
  product_name: string
  signal_code: string
  signal_level: 'low' | 'medium' | 'high' | 'critical'
  timing_score: number
  risk_score: number
  confidence: number
  recommended_action: string
  reason_summary: string
  impact_value?: number | null
  recommended_market?: string | null
  recommended_site?: string | null
  source_health?: string | null
  trend_label?: string | null
  latest_captured_at?: string | null
  site_count?: number | null
  current_lowest_price?: number | null
  current_highest_price?: number | null
  average_price?: number | null
  current_price?: number | null
  price_span?: number | null
  trend_points?: number | null
  series_preview?: Array<Record<string, unknown>>
}

export interface SignalActionItem {
  title: string
  description: string
  action: string
  confidence?: number | null
  impact_value?: number | null
}

export interface SignalOverviewResponse {
  generated_at?: string | null
  scope: Record<string, string | null | undefined>
  headline: string
  overview_metrics: SignalMetricItem[]
  top_opportunities: SignalInsightItem[]
  top_risks: SignalInsightItem[]
  recommended_actions: SignalActionItem[]
  source_health: Record<string, unknown>
  alert_count: number
  alert_items: Array<Record<string, unknown>>
}

export interface ProcurementRecommendationItem {
  menu_name?: string | null
  ingredient_name?: string | null
  identity_key?: string | null
  price_status?: string | null
  estimated_cost?: number | null
  reference_price?: number | null
  recommended_market?: string | null
  recommended_site?: string | null
  backup_market?: string | null
  backup_site?: string | null
  timing_score: number
  risk_score: number
  confidence: number
  signal_level: 'low' | 'medium' | 'high' | 'critical'
  recommended_action: string
  reason_summary: string
  impact_value?: number | null
  source_priority_label?: string | null
  source_tier?: string | null
  distance_label?: string | null
}

export interface ProcurementRecommendationResponse {
  summary: Record<string, unknown>
  ingredient_items: Array<Record<string, unknown>>
  items: ProcurementRecommendationItem[]
}

export interface SalesDemoSceneItem {
  title: string
  description: string
  highlight: string
}

export interface SalesDemoContentResponse {
  scene: string
  hero: Record<string, string>
  proof_points: Array<Record<string, string>>
  scenes: SalesDemoSceneItem[]
  storyline: string[]
}

export interface PricingPackageItem {
  name: string
  price_band: string
  target: string
  recommended: boolean
  features: string[]
  cta: string
}

export interface PricingPackagesResponse {
  items: PricingPackageItem[]
}
