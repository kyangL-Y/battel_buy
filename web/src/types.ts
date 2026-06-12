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
  source_tier?: string | null
  source_url?: string | null
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

export interface SettingsSnapshotSourceItem {
  source_url: string
  source_name?: string | null
  configured_name?: string | null
  enabled?: boolean | null
  market_scope?: string | null
  market_category?: string | null
  notes?: string | null
  preferred_fetch_mode?: 'requests' | 'playwright' | 'api' | null
  strategy?: string | null
  timeout_seconds?: number | null
  retry_count?: number | null
  request_delay_seconds?: number | null
  blocked_status_codes?: number[] | null
  verify_ssl?: boolean | null
  api_strategy?: string | null
}

export interface SettingsSnapshotDocument {
  schema: 'battel.settings.snapshot'
  version: 1
  generated_at: string
  summary: {
    source_count: number
    alert_rule_count: number
    selected_source_name?: string | null
  }
  schedule: {
    enabled: boolean
    mode: 'interval' | 'daily_time'
    daily_run_time?: string | null
    interval_seconds: number
    fetch_mode?: 'requests' | 'playwright' | null
    target_scope?: 'all_saved' | 'province' | 'city' | null
    target_province?: string | null
    target_city?: string | null
  }
  source_coverage: SettingsSnapshotSourceItem[]
  selected_source_url?: string | null
  selected_source_name?: string | null
  selected_source_strategy?: SettingsSnapshotSourceItem | null
  alert_rules: GlobalAlertRuleItem[]
}

export interface SettingsChangeLogItem {
  id: string | number
  changed_at: string
  actor_name: string
  actor_user_id?: number | null
  action_type: 'schedule' | 'source_config' | 'source_strategy' | 'global_alert' | 'snapshot'
  target_name: string
  summary: string
  change_payload?: Record<string, unknown>
}

export interface SettingsChangeLogCreatePayload {
  action_type: SettingsChangeLogItem['action_type']
  target_name: string
  summary: string
  change_payload?: Record<string, unknown>
}

export interface SettingsChangeLogResponse {
  item: SettingsChangeLogItem
}

export interface SettingsChangeLogListResponse {
  items: SettingsChangeLogItem[]
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
  source_url?: string | null
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

export type {
  SupplierCategorySummaryItem,
  SupplierItem,
  SupplierListResponse,
  SupplierOverviewResponse,
  SupplierOverviewSummary,
  SupplierQuoteActionCreatePayload,
  SupplierQuoteActionItem,
  SupplierQuoteActionListResponse,
  SupplierQuoteActionQueryOptions,
  SupplierQuoteCompareResponse,
  SupplierQuoteCompareSummary,
  SupplierQuoteCreatePayload,
  SupplierQuoteCreateResponse,
  SupplierQuoteDuplicateField,
  SupplierQuoteImportItemPayload,
  SupplierQuoteImportMode,
  SupplierQuoteImportPayload,
  SupplierQuoteImportPreviewItem,
  SupplierQuoteImportPreviewPayload,
  SupplierQuoteImportPreviewResponse,
  SupplierQuoteImportResponse,
  SupplierQuoteImportResultItem,
  SupplierQuoteInvalidatePayload,
  SupplierQuoteInvalidateResponse,
  SupplierQuoteItem,
  SupplierQuoteListResponse,
  SupplierSettlementBuildFromQuotesPayload,
  SupplierSettlementBuildFromQuotesResponse,
  SupplierSettlementCancelPayload,
  SupplierSettlementCancelResponse,
  SupplierSettlementCreatePayload,
  SupplierSettlementCreateResponse,
  SupplierSettlementDetailResponse,
  SupplierSettlementItem,
  SupplierSettlementListResponse,
  SupplierSettlementQueryOptions,
  SupplierSettlementStatus,
  SupplierSettlementUpdatePayload,
  SupplierSettlementUpdateResponse,
  SupplierUpdatePayload,
} from './supplierTypes'

export type AuthUserRole = 'admin' | 'supplier' | 'procurement'

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
  market_scope?: string | null
  default_province?: string | null
  default_city?: string | null
  is_active?: boolean | null
  is_deleted?: boolean | null
  supplier_id?: number | null
  supplier_profile?: AuthSupplierProfile | null
  procurement_supplier_ids?: number[]
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

export interface AuthPasswordResetPayload {
  username: string
  current_password: string
  new_password: string
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
  procurement_supplier_ids?: number[]
  display_name?: string
  market_scope?: string | null
  is_active: boolean
}

export interface AuthUserUpdatePayload {
  username: string
  password?: string
  role: AuthUserRole
  supplier_id?: number | null
  procurement_supplier_ids?: number[]
  display_name?: string
  market_scope?: string | null
  is_active: boolean
}

export interface AuthUserDeleteResponse {
  deleted: boolean
  user_id: number
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

export interface ProcurementPlanRecordItem {
  id: number
  plan_title: string
  menu_text?: string | null
  diners: number
  tables: number
  preferred_province?: string | null
  preferred_city?: string | null
  preferred_location?: string | null
  ingredient_items: Record<string, any>[]
  procurement_plan: MenuPlanRow[]
  row_count: number
  matched_count: number
  pending_count: number
  total_cost?: number | null
  created_by_user_id?: number | null
  created_by?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface ProcurementPlanSavePayload {
  plan_title: string
  menu_text?: string | null
  diners: number
  tables: number
  preferred_province?: string | null
  preferred_city?: string | null
  preferred_location?: string | null
  ingredient_items: Record<string, any>[]
  procurement_plan: MenuPlanRow[]
  total_cost?: number | null
}

export interface ProcurementPlanRecordResponse {
  item: ProcurementPlanRecordItem
}

export interface ProcurementPlanRecordListResponse {
  items: ProcurementPlanRecordItem[]
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
  target_scope?: 'all_saved' | 'province' | 'city' | null
  target_province?: string | null
  target_city?: string | null
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

export interface LocationSuggestionResponse {
  matched: boolean
  province?: string | null
  city?: string | null
  label?: string | null
  source: 'browser_geolocation' | 'ip_geolocation' | 'none'
  source_label: string
  confidence: number
  raw_location?: string | null
  message?: string | null
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
