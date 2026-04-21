from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from urllib.parse import unquote

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from analysis.metrics import (
    build_cross_market_product_trend,
    build_single_market_product_trend,
    build_single_product_selector_options,
    compute_cross_site_price_summary,
    compute_single_product_summary,
    get_location_options,
)
from api.crawl_manager import CrawlManager
from api.deps import (
    get_db,
    get_history_df,
    get_latest_df,
    get_product_history_identity_df,
    get_runtime_settings,
    get_signal_history_df,
)
from api.schemas import (
    AISearchRequest,
    AISearchResponse,
    CrawlRunResponse,
    CrawlScheduleUpdateRequest,
    MenuPlanRequest,
    MenuPlanResponse,
    PricingPackagesResponse,
    ProcurementRecommendationResponse,
    SalesDemoContentResponse,
    SignalInsightItem,
    SignalOverviewResponse,
)
from services.decision_engine import (
    build_pricing_packages,
    build_procurement_recommendation,
    build_product_signal_detail,
    build_sales_demo_content,
    build_signals_overview,
)
from services.ai_extractor import AIExtractorError, can_use_ai_extraction, run_search_query
from services.menu_planner import build_procurement_plan, enrich_menu_items_with_ai, parse_menu_text
from utils.config_loader import load_json_config
from utils.config_loader import BASE_DIR as CONFIG_BASE_DIR


_CRAWL_MANAGER = CrawlManager()
logger = logging.getLogger(__name__)


def get_crawl_manager() -> CrawlManager:
    return _CRAWL_MANAGER


def _sanitize_dataframe(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    result = df.copy()
    for column in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[column]):
            result[column] = result[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    return result.where(pd.notna(result), None).to_dict(orient="records")


def _build_source_coverage_rows() -> list[dict]:
    db = get_db()
    summary_df = db.get_source_coverage_summary()
    configured_sources = load_json_config(CONFIG_BASE_DIR / "config" / "products.json")
    site_rules = load_json_config(CONFIG_BASE_DIR / "config" / "sites.json")
    product_name_map = {
        str(item.get("url") or "").strip(): str(item.get("product_name") or "").strip()
        for item in configured_sources
        if isinstance(item, dict) and str(item.get("url") or "").strip()
    }
    strategy_map = {
        str(item.get("site_name") or "").strip(): str(item.get("strategy") or "").strip()
        for item in site_rules
        if isinstance(item, dict) and str(item.get("site_name") or "").strip()
    }

    rows = _sanitize_dataframe(summary_df)
    by_url = {str(row.get("source_url") or "").strip(): row for row in rows}
    result_rows: list[dict] = []

    for item in configured_sources:
        if not isinstance(item, dict):
            continue
        source_url = str(item.get("url") or "").strip()
        configured_name = str(item.get("product_name") or "").strip()
        row = dict(by_url.get(source_url) or {})
        source_site_name = _infer_source_site_name(source_url)
        row["source_url"] = source_url
        row["configured_name"] = configured_name or source_site_name
        row["source_name"] = source_site_name
        row["strategy"] = strategy_map.get(source_site_name)
        product_key_count = int(row.get("product_key_count") or 0)
        source_item_count = int(row.get("source_item_count") or 0)
        failed_count = int(row.get("failed_count") or 0)
        if product_key_count <= 0 and failed_count > 0:
            status = "抓取异常"
        elif product_key_count > 0 and source_item_count > 0 and product_key_count > source_item_count * 1.4:
            status = "重复偏多"
        elif product_key_count > 0:
            status = "已入库"
        else:
            status = "未入库"
        row["status"] = status
        result_rows.append(row)

    return result_rows


def _infer_source_site_name(source_url: str) -> str:
    source_url = str(source_url or "")
    if "wbncp.com" in source_url:
        return "万邦国际"
    if "chinaprice.cn" in source_url:
        return "Chinaprice"
    if "pfsc.agri.cn" in source_url:
        return "PFSC"
    if "ncpscxx.moa.gov.cn" in source_url:
        return "重点农产品市场信息平台"
    return source_url


@asynccontextmanager
async def _app_lifespan(_: FastAPI):
    manager = get_crawl_manager()
    manager.start()
    try:
        yield
    finally:
        manager.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="Battel Price Tracker API", version="0.1.0", lifespan=_app_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/crawl/status")
    def crawl_status() -> dict:
        return {"item": get_crawl_manager().get_status()}

    @app.post("/api/crawl/run", response_model=CrawlRunResponse)
    def crawl_run() -> CrawlRunResponse:
        accepted, item = get_crawl_manager().trigger_run("manual")
        return CrawlRunResponse(accepted=accepted, item=item)

    @app.post("/api/crawl/schedule")
    def crawl_schedule(payload: CrawlScheduleUpdateRequest) -> dict:
        item = get_crawl_manager().update_schedule(
            enabled=payload.enabled,
            interval_seconds=payload.interval_seconds,
            fetch_mode=payload.fetch_mode,
        )
        return {"item": item}

    @app.get("/api/location/options")
    def location_options() -> dict:
        latest_df = get_latest_df()
        provinces, cities, province_city_map = get_location_options(latest_df)
        return {"provinces": provinces, "cities": cities, "province_city_map": province_city_map}

    @app.get("/api/source/coverage")
    def source_coverage() -> dict:
        return {"items": _build_source_coverage_rows()}

    @app.get("/api/market/summary")
    def market_summary(
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
    ) -> dict:
        latest_df = get_latest_df()
        if keyword and "product_name" in latest_df.columns:
            search_text = latest_df["product_name"].fillna("").astype(str)
            latest_df = latest_df[search_text.str.contains(keyword, regex=False)]
        summary_df = compute_cross_site_price_summary(
            latest_df,
            selected_province=province,
            selected_city=city,
        )
        return {"items": _sanitize_dataframe(summary_df)}

    @app.get("/api/product/options")
    def product_options(
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
    ) -> dict:
        latest_df = get_latest_df()
        options_df = build_single_product_selector_options(
            latest_df,
            selected_province=province,
            selected_city=city,
        )
        return {"items": _sanitize_dataframe(options_df)}

    @app.get("/api/product/{identity_key}/summary")
    def product_summary(
        identity_key: str,
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
    ) -> dict:
        decoded_key = unquote(identity_key)
        history_df = get_product_history_identity_df(decoded_key)
        return {
            "item": compute_single_product_summary(
                history_df,
                decoded_key,
                selected_province=province,
                selected_city=city,
            )
        }

    @app.get("/api/product/{identity_key}/trend")
    def product_trend(
        identity_key: str,
        mode: str = Query(default="cross_market"),
        site_name: str | None = Query(default=None),
        series_key: str | None = Query(default=None),
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
    ) -> dict:
        decoded_key = unquote(identity_key)
        history_df = get_product_history_identity_df(decoded_key)
        if mode == "single_market":
            trend_df = build_single_market_product_trend(
                history_df,
                decoded_key,
                site_name,
                series_key,
                selected_province=province,
                selected_city=city,
            )
        else:
            trend_df = build_cross_market_product_trend(
                history_df,
                decoded_key,
                selected_province=province,
                selected_city=city,
            )
            mode = "cross_market"
        return {"mode": mode, "items": _sanitize_dataframe(trend_df)}

    @app.post("/api/menu/plan", response_model=MenuPlanResponse)
    def menu_plan(payload: MenuPlanRequest) -> MenuPlanResponse:
        latest_df = get_latest_df()
        runtime_settings = get_runtime_settings()
        menu_items = [item.model_dump() for item in payload.menu_items]
        if payload.menu_text:
            menu_items.extend(parse_menu_text(payload.menu_text))
        if menu_items and runtime_settings.get("ai", {}).get("enabled") and can_use_ai_extraction(runtime_settings):
            try:
                menu_items = enrich_menu_items_with_ai(menu_items, runtime_config=runtime_settings)
            except Exception:
                logger.exception("Menu AI enrichment failed, fallback to original menu items.")
        ingredient_df, plan_df = build_procurement_plan(
            menu_items,
            latest_df,
            diners=payload.diners,
            tables=payload.tables,
            preferred_province=payload.preferred_province,
            preferred_city=payload.preferred_city,
            preferred_location=payload.preferred_location,
        )
        return MenuPlanResponse(
            ingredient_items=_sanitize_dataframe(ingredient_df),
            procurement_plan=_sanitize_dataframe(plan_df),
            total_cost=plan_df.attrs.get("total_cost") if plan_df is not None else None,
        )

    @app.get("/api/signals/overview", response_model=SignalOverviewResponse)
    def signals_overview(
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
        focus: str | None = Query(default=None),
    ) -> SignalOverviewResponse:
        latest_df = get_latest_df()
        history_df = get_signal_history_df()
        return SignalOverviewResponse(
            **build_signals_overview(
                latest_df,
                history_df,
                province=province,
                city=city,
                focus=focus,
            )
        )

    @app.get("/api/signals/{identity_key}", response_model=SignalInsightItem)
    def signal_detail(
        identity_key: str,
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
    ) -> SignalInsightItem:
        decoded_key = unquote(identity_key)
        history_df = get_product_history_identity_df(decoded_key)
        signal = build_product_signal_detail(
            history_df,
            decoded_key,
            province=province,
            city=city,
        )
        if not signal:
            raise HTTPException(status_code=404, detail="未找到对应商品的经营信号")
        return SignalInsightItem(**signal)

    @app.post("/api/procurement/recommend", response_model=ProcurementRecommendationResponse)
    def procurement_recommend(payload: MenuPlanRequest) -> ProcurementRecommendationResponse:
        latest_df = get_latest_df()
        runtime_settings = get_runtime_settings()
        menu_items = [item.model_dump() for item in payload.menu_items]
        if payload.menu_text:
            menu_items.extend(parse_menu_text(payload.menu_text))
        if menu_items and runtime_settings.get("ai", {}).get("enabled") and can_use_ai_extraction(runtime_settings):
            try:
                menu_items = enrich_menu_items_with_ai(menu_items, runtime_config=runtime_settings)
            except Exception:
                logger.exception("Menu AI enrichment failed for procurement recommendation.")
        return ProcurementRecommendationResponse(
            **build_procurement_recommendation(
                menu_items=menu_items,
                latest_df=latest_df,
                diners=payload.diners,
                tables=payload.tables,
                preferred_province=payload.preferred_province,
                preferred_city=payload.preferred_city,
                preferred_location=payload.preferred_location,
            )
        )

    @app.get("/api/sales/demo-content", response_model=SalesDemoContentResponse)
    def sales_demo_content(scene: str | None = Query(default=None)) -> SalesDemoContentResponse:
        latest_df = get_latest_df()
        return SalesDemoContentResponse(
            **build_sales_demo_content(
                latest_df,
                None,
                scene=scene,
                record_count=get_db().get_price_record_count(),
            )
        )

    @app.get("/api/pricing/packages", response_model=PricingPackagesResponse)
    def pricing_packages() -> PricingPackagesResponse:
        return PricingPackagesResponse(**build_pricing_packages())

    @app.post("/api/ai/search", response_model=AISearchResponse)
    def ai_search(payload: AISearchRequest) -> AISearchResponse:
        runtime_settings = get_runtime_settings()
        try:
            answer = run_search_query(payload.query, runtime_config=runtime_settings)
        except AIExtractorError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return AISearchResponse(answer=answer)

    return app


app = create_app()
