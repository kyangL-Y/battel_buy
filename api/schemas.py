from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AuthUserRole = Literal["admin", "supplier", "procurement"]
SUPPLIER_QUOTE_IMPORT_MAX_ITEMS = 1000


class MarketSummaryResponse(BaseModel):
    items: list[dict]


class TrendOptionsResponse(BaseModel):
    items: list[dict]


class ProductSummaryResponse(BaseModel):
    item: dict


class ProductTrendResponse(BaseModel):
    mode: Literal["cross_market", "single_market"]
    items: list[dict]


class AuthSupplierProfile(BaseModel):
    supplier_id: int
    supplier_name: str
    market_category: str | None = None
    channel: str | None = None
    market_scope: str | None = None
    is_active: bool = True


class AuthUserItem(BaseModel):
    id: int
    username: str
    role: AuthUserRole
    display_name: str | None = None
    market_scope: str | None = None
    default_province: str | None = None
    default_city: str | None = None
    is_active: bool = True
    is_deleted: bool = False
    supplier_id: int | None = None
    supplier_profile: AuthSupplierProfile | None = None
    procurement_supplier_ids: list[int] = Field(default_factory=list)
    last_login_at: str | None = None
    deleted_at: str | None = None
    deleted_by: str | None = None
    deleted_username: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AuthLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)


class AuthPasswordResetRequest(BaseModel):
    username: str = Field(..., min_length=1)
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    user: AuthUserItem


class AuthMeResponse(BaseModel):
    user: AuthUserItem


class AuthUserListResponse(BaseModel):
    items: list[AuthUserItem]


class AuthUserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8)
    role: AuthUserRole
    supplier_id: int | None = Field(default=None, ge=1)
    procurement_supplier_ids: list[int] = Field(default_factory=list)
    display_name: str | None = None
    market_scope: str | None = None
    is_active: bool = True


class AuthUserUpdateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str | None = Field(default=None, min_length=8)
    role: AuthUserRole
    supplier_id: int | None = Field(default=None, ge=1)
    procurement_supplier_ids: list[int] = Field(default_factory=list)
    display_name: str | None = None
    market_scope: str | None = None
    is_active: bool = True


class AuthUserDeleteResponse(BaseModel):
    deleted: bool
    user_id: int


class SupplierItem(BaseModel):
    id: int
    supplier_name: str
    contact_name: str | None = None
    contact_phone: str | None = None
    market_scope: str | None = None
    market_category: str | None = None
    channel: str | None = None
    notes: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None
    quote_count: int | None = None
    latest_quoted_at: str | None = None
    account_id: int | None = None
    account_username: str | None = None
    account_display_name: str | None = None
    account_is_active: bool | None = None


class SupplierListResponse(BaseModel):
    items: list[SupplierItem]


class SupplierCategorySummaryItem(BaseModel):
    market_category: str
    supplier_count: int
    active_supplier_count: int
    quote_count: int
    latest_quoted_at: str | None = None


class SupplierOverviewSummary(BaseModel):
    supplier_count: int
    active_supplier_count: int
    inactive_supplier_count: int
    category_count: int
    total_quote_count: int
    latest_quoted_at: str | None = None


class SupplierCreateRequest(BaseModel):
    supplier_name: str = Field(..., min_length=1)
    contact_name: str | None = None
    contact_phone: str | None = None
    market_scope: str | None = None
    market_category: str | None = None
    channel: str | None = None
    notes: str | None = None
    is_active: bool = True
    account_username: str | None = None
    account_password: str | None = Field(default=None, min_length=8)
    account_display_name: str | None = None
    account_is_active: bool = True


class SupplierUpdateRequest(BaseModel):
    supplier_name: str = Field(..., min_length=1)
    contact_name: str | None = None
    contact_phone: str | None = None
    market_scope: str | None = None
    market_category: str | None = None
    channel: str | None = None
    notes: str | None = None
    is_active: bool = True
    account_username: str | None = None
    account_password: str | None = Field(default=None, min_length=8)
    account_display_name: str | None = None
    account_is_active: bool | None = None


class SupplierQuoteCreateRequest(BaseModel):
    price_identity_key: str = Field(..., min_length=1)
    source_record_id: int | None = Field(default=None, ge=1)
    supplier_id: int | None = Field(default=None, ge=1)
    supplier_name: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    market_scope: str | None = None
    market_category: str | None = None
    channel: str | None = None
    product_name: str | None = None
    price_identity_label: str | None = None
    category: str | None = None
    spec_text: str | None = None
    quote_price: float = Field(..., ge=0)
    quote_unit: str | None = None
    box_price: float | None = Field(default=None, ge=0)
    tax_price: float | None = Field(default=None, ge=0)
    inventory_status: str | None = None
    remarks: str | None = None
    quoted_by: str | None = None
    quoted_at: str | None = None


class SupplierQuoteImportItemRequest(BaseModel):
    row_number: int | None = Field(default=None, ge=1)
    price_identity_key: str | None = None
    price_identity_label: str | None = None
    product_name: str | None = None
    category: str | None = None
    spec_text: str | None = None
    quote_price: float | None = None
    quote_unit: str | None = None
    box_price: float | None = None
    tax_price: float | None = None
    inventory_status: str | None = None
    remarks: str | None = None
    quoted_at: str | None = None
    quoted_by: str | None = None
    channel: str | None = None
    market_category: str | None = None
    market_scope: str | None = None


class SupplierQuoteImportRequest(BaseModel):
    supplier_id: int = Field(..., ge=1)
    operator_name: str | None = None
    file_name: str | None = None
    import_mode: Literal["append", "skip_duplicate", "override_latest"] = "append"
    duplicate_match_fields: list[str] = Field(default_factory=list)
    abnormal_change_ratio_threshold: float | None = Field(default=None, ge=0)
    items: list[SupplierQuoteImportItemRequest] = Field(..., min_length=1, max_length=SUPPLIER_QUOTE_IMPORT_MAX_ITEMS)


class SupplierQuoteImportPreviewRequest(BaseModel):
    supplier_id: int = Field(..., ge=1)
    import_mode: Literal["append", "skip_duplicate", "override_latest"] = "append"
    duplicate_match_fields: list[str] = Field(default_factory=list)
    abnormal_change_ratio_threshold: float | None = Field(default=None, ge=0)
    items: list[SupplierQuoteImportItemRequest] = Field(..., min_length=1, max_length=SUPPLIER_QUOTE_IMPORT_MAX_ITEMS)


class SupplierQuoteItem(BaseModel):
    record_id: int | None = None
    supplier_id: int
    supplier_name: str
    contact_name: str | None = None
    contact_phone: str | None = None
    market_scope: str | None = None
    market_category: str | None = None
    channel: str | None = None
    price_identity_key: str
    price_identity_label: str | None = None
    product_name: str | None = None
    category: str | None = None
    spec_text: str | None = None
    quote_price: float | None = None
    quote_unit: str | None = None
    box_price: float | None = None
    tax_price: float | None = None
    inventory_status: str | None = None
    remarks: str | None = None
    quoted_by: str | None = None
    status: str = "active"
    invalidated_at: str | None = None
    invalidated_reason: str | None = None
    quoted_at: str | None = None
    price_diff_to_market_lowest: float | None = None
    price_diff_to_market_average: float | None = None
    comparison_label: str | None = None


class SupplierQuoteCreateResponse(BaseModel):
    item: SupplierQuoteItem


class SupplierQuoteImportResultItem(BaseModel):
    row_number: int = Field(..., ge=1)
    status: Literal["success", "failed", "skipped"]
    failure_reason: str | None = None
    record_id: int | None = None
    price_identity_key: str | None = None
    price_identity_label: str | None = None
    product_name: str | None = None
    duplicate_match_fields: list[str] = Field(default_factory=list)
    abnormal_change_ratio: float | None = None
    abnormal_change_hint: str | None = None


class SupplierQuoteImportResponse(BaseModel):
    total_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    items: list[SupplierQuoteImportResultItem]


class SupplierQuoteImportPreviewItem(BaseModel):
    row_number: int = Field(..., ge=1)
    price_identity_key: str | None = None
    preview_status: Literal["append", "skip_duplicate", "override_latest", "invalid"]
    preview_reason: str | None = None
    existing_record_id: int | None = None
    existing_quote_price: float | None = None
    existing_quote_unit: str | None = None
    existing_quoted_at: str | None = None
    existing_remarks: str | None = None
    duplicate_match_fields: list[str] = Field(default_factory=list)
    abnormal_change_ratio: float | None = None
    abnormal_change_hint: str | None = None


class SupplierQuoteImportPreviewResponse(BaseModel):
    items: list[SupplierQuoteImportPreviewItem]


class SupplierQuoteInvalidateRequest(BaseModel):
    reason: str | None = None
    operator_name: str | None = None


class SupplierQuoteInvalidateResponse(BaseModel):
    item: SupplierQuoteItem


class SupplierQuoteActionItem(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    record_id: int | None = None
    target_record_id: int | None = None
    action_type: str
    action_reason: str | None = None
    operator_name: str | None = None
    action_payload: str | None = None
    created_at: str | None = None
    price_identity_key: str | None = None
    price_identity_label: str | None = None
    product_name: str | None = None
    quote_price: float | None = None
    quote_unit: str | None = None
    quoted_at: str | None = None
    target_price_identity_label: str | None = None
    target_product_name: str | None = None
    target_quote_price: float | None = None
    target_quoted_at: str | None = None


class SupplierQuoteActionCreateRequest(BaseModel):
    action_type: str = Field(..., min_length=1)
    record_id: int | None = Field(default=None, ge=1)
    target_record_id: int | None = Field(default=None, ge=1)
    action_reason: str | None = None
    operator_name: str | None = None
    action_payload: dict | None = None


class SupplierQuoteActionListResponse(BaseModel):
    items: list[SupplierQuoteActionItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class SupplierSettlementItem(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    contact_name: str | None = None
    contact_phone: str | None = None
    market_scope: str | None = None
    market_category: str | None = None
    channel: str | None = None
    settlement_title: str
    period_start: str | None = None
    period_end: str | None = None
    quote_record_ids: list[int] = Field(default_factory=list)
    record_count: int = 0
    total_amount: float = 0
    paid_amount: float = 0
    pending_amount: float = 0
    status: Literal["pending", "partial", "paid", "cancelled"] = "pending"
    payment_due_date: str | None = None
    payment_date: str | None = None
    remarks: str | None = None
    created_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SupplierSettlementCreateRequest(BaseModel):
    settlement_title: str = Field(..., min_length=1)
    period_start: str | None = None
    period_end: str | None = None
    quote_record_ids: list[int] = Field(default_factory=list)
    total_amount: float = Field(default=0, ge=0)
    paid_amount: float = Field(default=0, ge=0)
    status: Literal["pending", "partial", "paid", "cancelled"] | None = None
    payment_due_date: str | None = None
    payment_date: str | None = None
    remarks: str | None = None
    created_by: str | None = None


class SupplierSettlementUpdateRequest(BaseModel):
    settlement_title: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    quote_record_ids: list[int] | None = None
    total_amount: float | None = Field(default=None, ge=0)
    paid_amount: float | None = Field(default=None, ge=0)
    status: Literal["pending", "partial", "paid", "cancelled"] | None = None
    payment_due_date: str | None = None
    payment_date: str | None = None
    remarks: str | None = None
    operator_name: str | None = None


class SupplierSettlementCancelRequest(BaseModel):
    operator_name: str | None = None
    cancel_reason: str | None = None


class SupplierSettlementBuildFromQuotesRequest(BaseModel):
    settlement_title: str = Field(..., min_length=1)
    quote_record_ids: list[int] = Field(..., min_length=1)
    paid_amount: float | None = Field(default=None, ge=0)
    payment_due_date: str | None = None
    remarks: str | None = None
    created_by: str | None = None


class SupplierSettlementListResponse(BaseModel):
    items: list[SupplierSettlementItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class SupplierSettlementDetailResponse(BaseModel):
    item: SupplierSettlementItem
    quote_items: list[SupplierQuoteItem] = Field(default_factory=list)


class SupplierQuoteCompareSummary(BaseModel):
    identity_key: str
    product_name: str
    supplier_count: int
    market_lowest_price: float | None = None
    market_lowest_site: str | None = None
    market_lowest_source_name: str | None = None
    market_lowest_source_tier: str | None = None
    market_average_price: float | None = None
    lowest_quote: float | None = None
    lowest_quote_supplier: str | None = None
    latest_quoted_at: str | None = None


class ProductSupplierQuotesResponse(BaseModel):
    summary: SupplierQuoteCompareSummary
    items: list[SupplierQuoteItem]


class SupplierQuoteListResponse(BaseModel):
    items: list[SupplierQuoteItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class SupplierOverviewResponse(BaseModel):
    summary: SupplierOverviewSummary
    category_items: list[SupplierCategorySummaryItem]
    recent_quotes: list[SupplierQuoteItem]


class MenuItemInput(BaseModel):
    menu_name: str = Field(..., min_length=1)
    ingredient_name: str | None = None
    remarks: str | None = None


class MenuPlanRequest(BaseModel):
    menu_text: str | None = None
    menu_items: list[MenuItemInput] = Field(default_factory=list)
    diners: int = Field(0, ge=0, description="总人数（全部桌合计）")
    tables: int = Field(0, ge=0, description="总桌数")
    preferred_province: str | None = None
    preferred_city: str | None = None
    preferred_location: str | None = None


class MenuPlanResponse(BaseModel):
    ingredient_items: list[dict]
    procurement_plan: list[dict]
    total_cost: float | None = None


class ProcurementPlanSaveRequest(BaseModel):
    plan_title: str = Field(..., min_length=1)
    menu_text: str | None = None
    diners: int = Field(0, ge=0)
    tables: int = Field(0, ge=0)
    preferred_province: str | None = None
    preferred_city: str | None = None
    preferred_location: str | None = None
    ingredient_items: list[dict] = Field(default_factory=list)
    procurement_plan: list[dict] = Field(default_factory=list)
    total_cost: float | None = None


class ProcurementPlanRecordItem(BaseModel):
    id: int
    plan_title: str
    menu_text: str | None = None
    diners: int = 0
    tables: int = 0
    preferred_province: str | None = None
    preferred_city: str | None = None
    preferred_location: str | None = None
    ingredient_items: list[dict] = Field(default_factory=list)
    procurement_plan: list[dict] = Field(default_factory=list)
    row_count: int = 0
    matched_count: int = 0
    pending_count: int = 0
    total_cost: float | None = None
    created_by_user_id: int | None = None
    created_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProcurementPlanRecordResponse(BaseModel):
    item: ProcurementPlanRecordItem


class ProcurementPlanRecordListResponse(BaseModel):
    items: list[ProcurementPlanRecordItem]


class AISearchRequest(BaseModel):
    query: str = Field(..., min_length=1)


class AISearchResponse(BaseModel):
    answer: str


class CrawlRunResponse(BaseModel):
    accepted: bool
    item: dict


class CrawlRunRequest(BaseModel):
    target_scope: Literal["all_saved", "province", "city"] = "all_saved"
    target_province: str | None = None
    target_city: str | None = None
    source_url: str | None = None
    source_name: str | None = None


class CrawlScheduleUpdateRequest(BaseModel):
    enabled: bool
    mode: Literal["interval", "daily_time"] = "interval"
    daily_run_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    interval_seconds: int = Field(default=86400, ge=60)
    fetch_mode: Literal["requests", "playwright"] | None = None
    target_scope: Literal["all_saved", "province", "city"] = "all_saved"
    target_province: str | None = None
    target_city: str | None = None


class SourceConfigUpdateRequest(BaseModel):
    source_url: str = Field(..., min_length=1)
    enabled: bool
    configured_name: str | None = None
    market_scope: str | None = None
    market_category: str | None = None
    notes: str | None = None


class SourceStrategyUpdateRequest(BaseModel):
    source_name: str = Field(..., min_length=1)
    preferred_fetch_mode: Literal["requests", "playwright", "api"] | None = None
    strategy: str | None = None
    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    retry_count: int | None = Field(default=None, ge=0, le=20)
    request_delay_seconds: float | None = Field(default=None, ge=0, le=60)
    blocked_status_codes: list[int] | None = None
    verify_ssl: bool | None = None
    api_strategy: str | None = None


class GlobalAlertRuleItem(BaseModel):
    target_name: str | None = Field(default=None)
    threshold: float = Field(..., ge=0)
    note: str | None = None
    group_name: str | None = None


class GlobalAlertRulesUpdateRequest(BaseModel):
    items: list[GlobalAlertRuleItem] = Field(default_factory=list)


class SettingsSnapshotItem(BaseModel):
    key: str
    label: str
    value: str | None = None
    changed_at: str | None = None


class SettingsSnapshotSummary(BaseModel):
    source_count: int = 0
    strategy_count: int = 0
    alert_rule_count: int = 0


class SettingsSnapshotSchedule(BaseModel):
    enabled: bool = False
    mode: str | None = "interval"
    daily_run_time: str | None = None
    interval_seconds: int = 86400
    fetch_mode: str | None = None
    target_scope: str | None = None
    target_province: str | None = None
    target_city: str | None = None


class SettingsSnapshotSourceCoverageItem(BaseModel):
    source_url: str | None = None
    source_name: str | None = None
    configured_name: str | None = None
    enabled: bool = True
    market_scope: str | None = None
    market_category: str | None = None
    market_subcategory: str | None = None
    channel: str | None = None
    notes: str | None = None


class SettingsSnapshotSourceStrategyItem(BaseModel):
    source_name: str | None = None
    preferred_fetch_mode: str | None = None
    strategy: str | None = None
    timeout_seconds: int | None = None
    retry_count: int | None = None
    request_delay_seconds: float | None = None
    blocked_status_codes: list[int] = Field(default_factory=list)
    verify_ssl: bool | None = None
    api_strategy: str | None = None


class SettingsSnapshotResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    snapshot_schema: Literal["battel.settings.snapshot"] = Field(default="battel.settings.snapshot", alias="schema")
    version: Literal[1] = 1
    generated_at: str
    summary: SettingsSnapshotSummary = Field(default_factory=SettingsSnapshotSummary)
    schedule: SettingsSnapshotSchedule = Field(default_factory=SettingsSnapshotSchedule)
    source_coverage: list[SettingsSnapshotSourceCoverageItem] = Field(default_factory=list)
    source_strategies: list[SettingsSnapshotSourceStrategyItem] = Field(default_factory=list)
    selected_source_url: str | None = None
    selected_source_name: str | None = None
    selected_source_strategy: SettingsSnapshotSourceStrategyItem | None = None
    alert_rules: list[GlobalAlertRuleItem] = Field(default_factory=list)


class SettingsSnapshotPreviewRequest(SettingsSnapshotResponse):
    pass


class SettingsSnapshotPreviewResponse(SettingsSnapshotResponse):
    warnings: list[str] = Field(default_factory=list)


class SettingsSnapshotApplyRequest(SettingsSnapshotResponse):
    pass


class SignalMetric(BaseModel):
    label: str
    value: str
    detail: str | None = None


class SignalActionItem(BaseModel):
    title: str
    description: str
    action: str
    confidence: float | None = None
    impact_value: float | None = None


class SignalInsightItem(BaseModel):
    identity_key: str
    product_name: str
    signal_code: str
    signal_level: Literal["low", "medium", "high"]
    timing_score: float
    risk_score: float
    confidence: float
    recommended_action: str
    reason_summary: str
    impact_value: float | None = None
    recommended_market: str | None = None
    recommended_site: str | None = None
    source_health: str | None = None
    trend_label: str | None = None
    latest_captured_at: str | None = None
    site_count: int | None = None
    current_lowest_price: float | None = None
    current_highest_price: float | None = None
    average_price: float | None = None
    current_price: float | None = None
    price_span: float | None = None
    trend_points: int | None = None
    series_preview: list[dict] = Field(default_factory=list)


class SignalOverviewResponse(BaseModel):
    generated_at: str | None = None
    scope: dict
    headline: str
    overview_metrics: list[SignalMetric]
    top_opportunities: list[SignalInsightItem]
    top_risks: list[SignalInsightItem]
    recommended_actions: list[SignalActionItem]
    source_health: dict
    alert_count: int
    alert_items: list[dict] = Field(default_factory=list)


class ProcurementRecommendationItem(BaseModel):
    menu_name: str | None = None
    ingredient_name: str | None = None
    identity_key: str | None = None
    price_status: str | None = None
    estimated_cost: float | None = None
    reference_price: float | None = None
    recommended_market: str | None = None
    recommended_site: str | None = None
    backup_market: str | None = None
    backup_site: str | None = None
    timing_score: float
    risk_score: float
    confidence: float
    signal_level: Literal["low", "medium", "high"]
    recommended_action: str
    reason_summary: str
    impact_value: float | None = None
    source_priority_label: str | None = None
    source_tier: str | None = None
    distance_label: str | None = None


class ProcurementRecommendationResponse(BaseModel):
    summary: dict
    ingredient_items: list[dict]
    items: list[ProcurementRecommendationItem]


class DemoSceneItem(BaseModel):
    title: str
    description: str
    highlight: str


class SalesDemoContentResponse(BaseModel):
    scene: str
    hero: dict
    proof_points: list[dict]
    scenes: list[DemoSceneItem]
    storyline: list[str]


class PricingPackageItem(BaseModel):
    name: str
    price_band: str
    target: str
    recommended: bool = False
    features: list[str] = Field(default_factory=list)
    cta: str


class PricingPackagesResponse(BaseModel):
    items: list[PricingPackageItem]
