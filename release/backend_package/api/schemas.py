from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MarketSummaryResponse(BaseModel):
    items: list[dict]


class TrendOptionsResponse(BaseModel):
    items: list[dict]


class ProductSummaryResponse(BaseModel):
    item: dict


class ProductTrendResponse(BaseModel):
    mode: Literal["cross_market", "single_market"]
    items: list[dict]


class MenuItemInput(BaseModel):
    menu_name: str = Field(..., min_length=1)
    ingredient_name: str | None = None
    remarks: str | None = None


class MenuPlanRequest(BaseModel):
    menu_text: str | None = None
    menu_items: list[MenuItemInput] = Field(default_factory=list)
    diners: int = 0
    tables: int = 0
    preferred_province: str | None = None
    preferred_city: str | None = None
    preferred_location: str | None = None


class MenuPlanResponse(BaseModel):
    ingredient_items: list[dict]
    procurement_plan: list[dict]
    total_cost: float | None = None


class AISearchRequest(BaseModel):
    query: str = Field(..., min_length=1)


class AISearchResponse(BaseModel):
    answer: str


class CrawlRunResponse(BaseModel):
    accepted: bool
    item: dict


class CrawlScheduleUpdateRequest(BaseModel):
    enabled: bool
    interval_seconds: int = Field(default=86400, ge=60)
    fetch_mode: Literal["requests", "playwright"] | None = None


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
