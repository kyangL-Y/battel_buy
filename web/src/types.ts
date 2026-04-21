export interface MarketSummaryItem {
  product_name: string
  price_identity_key?: string
  site_count?: number | null
  market_count?: number | null
  price_unit_basis?: string | null
  lowest_price?: number | null
  lowest_price_site?: string | null
  highest_price?: number | null
  highest_price_site?: string | null
  average_price?: number | null
  region_label?: string | null
}

export interface SourceCoverageItem {
  source_url: string
  configured_name?: string | null
  source_name?: string | null
  strategy?: string | null
  enabled?: boolean | null
  market_scope?: string | null
  market_category?: string | null
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

export interface ProductOptionItem {
  price_identity_key: string
  price_identity_label: string
  site_count: number
}

export interface ProductTrendRow {
  site_name?: string | null
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
}

export interface MenuPlanRow {
  menu_name: string
  ingredient_name: string
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
  next_run_at?: string | null
  schedule_enabled: boolean
  schedule_interval_seconds: number
  schedule_fetch_mode?: 'requests' | 'playwright' | null
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
