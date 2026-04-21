from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
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
    get_product_keys_for_identity,
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
    ProductSupplierQuotesResponse,
    ProcurementRecommendationResponse,
    SalesDemoContentResponse,
    SignalInsightItem,
    SignalOverviewResponse,
    SupplierCreateRequest,
    SupplierItem,
    SupplierListResponse,
    SupplierOverviewResponse,
    SupplierQuoteListResponse,
    SupplierQuoteCreateRequest,
    SupplierQuoteCreateResponse,
    SupplierUpdateRequest,
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
from utils.source_config import get_source_name, is_source_enabled


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


def _normalize_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        normalized_value = float(value)
    except (TypeError, ValueError):
        return None
    return round(normalized_value, 2)


def _build_supplier_comparison_label(quote_price: float | None, market_lowest_price: float | None) -> str:
    if quote_price is None or market_lowest_price is None:
        return "待补公开行情"
    diff = round(quote_price - market_lowest_price, 2)
    if abs(diff) < 0.01:
        return "与公开最低价持平"
    if diff < 0:
        return f"低于公开最低价 {abs(diff):.2f}"
    return f"高于公开最低价 {diff:.2f}"


def _build_product_supplier_quotes_response(identity_key: str) -> dict:
    decoded_key = str(identity_key or "").strip()
    history_df = get_product_history_identity_df(decoded_key)
    market_summary = (
        compute_single_product_summary(history_df, decoded_key)
        if history_df is not None and not history_df.empty
        else {}
    )
    quote_rows = _sanitize_dataframe(get_db().get_latest_supplier_quotes(decoded_key))
    market_lowest_price = _normalize_float(market_summary.get("current_lowest_price"))
    market_average_price = _normalize_float(market_summary.get("average_price"))

    items: list[dict] = []
    for row in quote_rows:
        quote_price = _normalize_float(row.get("quote_price"))
        item = {
            "supplier_id": int(row.get("supplier_id") or 0),
            "supplier_name": str(row.get("supplier_name") or "").strip(),
            "contact_name": row.get("contact_name"),
            "contact_phone": row.get("contact_phone"),
            "market_scope": row.get("market_scope"),
            "market_category": row.get("market_category") or row.get("supplier_market_category"),
            "channel": row.get("channel") or row.get("supplier_channel"),
            "price_identity_key": decoded_key,
            "price_identity_label": row.get("price_identity_label"),
            "product_name": row.get("product_name") or market_summary.get("product_name"),
            "category": row.get("category"),
            "spec_text": row.get("spec_text"),
            "quote_price": quote_price,
            "quote_unit": row.get("quote_unit"),
            "box_price": _normalize_float(row.get("box_price")),
            "tax_price": _normalize_float(row.get("tax_price")),
            "inventory_status": row.get("inventory_status"),
            "remarks": row.get("remarks"),
            "quoted_by": row.get("quoted_by"),
            "quoted_at": row.get("quoted_at"),
            "price_diff_to_market_lowest": (
                round(quote_price - market_lowest_price, 2)
                if quote_price is not None and market_lowest_price is not None
                else None
            ),
            "price_diff_to_market_average": (
                round(quote_price - market_average_price, 2)
                if quote_price is not None and market_average_price is not None
                else None
            ),
            "comparison_label": _build_supplier_comparison_label(quote_price, market_lowest_price),
        }
        items.append(item)

    lowest_quote_item = next((item for item in items if item.get("quote_price") is not None), None)
    product_name = (
        str(market_summary.get("product_name") or "").strip()
        or str(lowest_quote_item.get("product_name") or "").strip()
        or decoded_key
    )
    latest_quoted_at = max((str(item.get("quoted_at") or "") for item in items if item.get("quoted_at")), default="") or None
    return {
        "summary": {
            "identity_key": decoded_key,
            "product_name": product_name,
            "supplier_count": len(items),
            "market_lowest_price": market_lowest_price,
            "market_average_price": market_average_price,
            "lowest_quote": lowest_quote_item.get("quote_price") if lowest_quote_item else None,
            "lowest_quote_supplier": lowest_quote_item.get("supplier_name") if lowest_quote_item else None,
            "latest_quoted_at": latest_quoted_at,
        },
        "items": items,
    }


def _build_supplier_quote_item(row: dict) -> dict:
    return {
        "supplier_id": int(row.get("supplier_id") or 0),
        "supplier_name": str(row.get("supplier_name") or "").strip(),
        "contact_name": row.get("contact_name"),
        "contact_phone": row.get("contact_phone"),
        "market_scope": row.get("market_scope"),
        "market_category": row.get("market_category") or row.get("supplier_market_category"),
        "channel": row.get("channel") or row.get("supplier_channel"),
        "price_identity_key": str(row.get("price_identity_key") or "").strip(),
        "price_identity_label": row.get("price_identity_label"),
        "product_name": row.get("product_name"),
        "category": row.get("category"),
        "spec_text": row.get("spec_text"),
        "quote_price": _normalize_float(row.get("quote_price")),
        "quote_unit": row.get("quote_unit"),
        "box_price": _normalize_float(row.get("box_price")),
        "tax_price": _normalize_float(row.get("tax_price")),
        "inventory_status": row.get("inventory_status"),
        "remarks": row.get("remarks"),
        "quoted_by": row.get("quoted_by"),
        "quoted_at": row.get("quoted_at"),
        "price_diff_to_market_lowest": None,
        "price_diff_to_market_average": None,
        "comparison_label": None,
    }


def _build_supplier_overview_response(recent_limit: int = 12) -> dict:
    supplier_rows = _sanitize_dataframe(get_db().get_suppliers(active_only=False))
    category_rows = _sanitize_dataframe(get_db().get_supplier_category_summary())
    recent_rows = _sanitize_dataframe(get_db().get_recent_supplier_quotes(limit=recent_limit))
    recent_quotes = [_build_supplier_quote_item(row) for row in recent_rows]

    active_supplier_count = sum(1 for item in supplier_rows if bool(item.get("is_active")))
    latest_quoted_at = max((str(item.get("latest_quoted_at") or "") for item in supplier_rows if item.get("latest_quoted_at")), default="") or None

    return {
        "summary": {
            "supplier_count": len(supplier_rows),
            "active_supplier_count": active_supplier_count,
            "inactive_supplier_count": max(len(supplier_rows) - active_supplier_count, 0),
            "category_count": len(category_rows),
            "total_quote_count": sum(int(item.get("quote_count") or 0) for item in supplier_rows),
            "latest_quoted_at": latest_quoted_at,
        },
        "category_items": [
            {
                "market_category": str(item.get("market_category") or "未分类").strip() or "未分类",
                "supplier_count": int(item.get("supplier_count") or 0),
                "active_supplier_count": int(item.get("active_supplier_count") or 0),
                "quote_count": int(item.get("quote_count") or 0),
                "latest_quoted_at": item.get("latest_quoted_at"),
            }
            for item in category_rows
        ],
        "recent_quotes": recent_quotes,
    }


def _build_source_coverage_rows() -> list[dict]:
    db = get_db()
    summary_df = db.get_source_coverage_summary()
    configured_sources = load_json_config(CONFIG_BASE_DIR / "config" / "products.json")
    site_rules = load_json_config(CONFIG_BASE_DIR / "config" / "sites.json")
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
        source_site_name = get_source_name(item, fallback=_infer_source_site_name(source_url))
        source_enabled = is_source_enabled(item)
        row["source_url"] = source_url
        row["configured_name"] = configured_name or source_site_name
        row["source_name"] = source_site_name
        row["strategy"] = str(item.get("strategy") or "").strip() or strategy_map.get(source_site_name)
        row["enabled"] = source_enabled
        row["market_scope"] = str(item.get("market_scope") or "").strip() or None
        row["market_category"] = str(item.get("market_category") or "").strip() or None
        row["channel"] = str(item.get("channel") or "").strip() or None
        row["notes"] = str(item.get("notes") or "").strip() or None
        product_key_count = int(row.get("product_key_count") or 0)
        source_item_count = int(row.get("source_item_count") or 0)
        failed_count = int(row.get("failed_count") or 0)
        if not source_enabled:
            status = "待接入"
        elif product_key_count <= 0 and failed_count > 0:
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

    @app.get("/api/product/{identity_key}/supplier-quotes", response_model=ProductSupplierQuotesResponse)
    def product_supplier_quotes(identity_key: str) -> ProductSupplierQuotesResponse:
        decoded_key = unquote(identity_key)
        return ProductSupplierQuotesResponse(**_build_product_supplier_quotes_response(decoded_key))

    @app.get("/api/suppliers", response_model=SupplierListResponse)
    def suppliers(active_only: bool = Query(default=True)) -> SupplierListResponse:
        return SupplierListResponse(items=_sanitize_dataframe(get_db().get_suppliers(active_only=active_only)))

    @app.get("/api/suppliers/overview", response_model=SupplierOverviewResponse)
    def suppliers_overview(limit: int = Query(default=12, ge=1, le=50)) -> SupplierOverviewResponse:
        return SupplierOverviewResponse(**_build_supplier_overview_response(recent_limit=limit))

    @app.post("/api/suppliers", response_model=SupplierItem)
    def create_supplier(payload: SupplierCreateRequest) -> SupplierItem:
        supplier_id = get_db().upsert_supplier(
            supplier_name=payload.supplier_name,
            contact_name=payload.contact_name,
            contact_phone=payload.contact_phone,
            market_scope=payload.market_scope,
            market_category=payload.market_category,
            channel=payload.channel,
            notes=payload.notes,
            is_active=payload.is_active,
        )
        supplier_df = get_db().get_suppliers(active_only=False)
        supplier_rows = _sanitize_dataframe(supplier_df)
        supplier_row = next((item for item in supplier_rows if int(item.get("id") or 0) == supplier_id), None)
        if not supplier_row:
            raise HTTPException(status_code=500, detail="供应商创建成功但返回数据缺失")
        return SupplierItem(**supplier_row)

    @app.put("/api/suppliers/{supplier_id}", response_model=SupplierItem)
    def update_supplier(supplier_id: int, payload: SupplierUpdateRequest) -> SupplierItem:
        updated_supplier_id = get_db().upsert_supplier(
            supplier_name=payload.supplier_name,
            contact_name=payload.contact_name,
            contact_phone=payload.contact_phone,
            market_scope=payload.market_scope,
            market_category=payload.market_category,
            channel=payload.channel,
            notes=payload.notes,
            is_active=payload.is_active,
            supplier_id=supplier_id,
        )
        supplier_df = get_db().get_suppliers(active_only=False)
        supplier_rows = _sanitize_dataframe(supplier_df)
        supplier_row = next((item for item in supplier_rows if int(item.get("id") or 0) == updated_supplier_id), None)
        if not supplier_row:
            raise HTTPException(status_code=404, detail="未找到供应商")
        return SupplierItem(**supplier_row)

    @app.post("/api/supplier-prices", response_model=SupplierQuoteCreateResponse)
    def create_supplier_price(payload: SupplierQuoteCreateRequest) -> SupplierQuoteCreateResponse:
        if payload.supplier_id is None and not str(payload.supplier_name or "").strip():
            raise HTTPException(status_code=400, detail="请至少提供 supplier_id 或 supplier_name")

        decoded_key = str(payload.price_identity_key).strip()
        matched_product_keys = get_product_keys_for_identity(decoded_key)
        supplier_id = (
            int(payload.supplier_id)
            if payload.supplier_id is not None
            else get_db().upsert_supplier(
                supplier_name=str(payload.supplier_name or "").strip(),
                contact_name=payload.contact_name,
                contact_phone=payload.contact_phone,
                market_scope=payload.market_scope,
                market_category=payload.market_category,
                channel=payload.channel,
                is_active=True,
            )
        )
        record_id = get_db().insert_supplier_price_record(
            supplier_id=supplier_id,
            price_identity_key=decoded_key,
            quoted_at=payload.quoted_at or datetime.utcnow().isoformat(),
            price_identity_label=payload.price_identity_label,
            product_name=payload.product_name or (decoded_key if not matched_product_keys else None),
            category=payload.category,
            spec_text=payload.spec_text,
            market_category=payload.market_category,
            channel=payload.channel,
            quote_price=payload.quote_price,
            quote_unit=payload.quote_unit,
            box_price=payload.box_price,
            tax_price=payload.tax_price,
            inventory_status=payload.inventory_status,
            remarks=payload.remarks,
            quoted_by=payload.quoted_by,
        )
        record_rows = _sanitize_dataframe(get_db().get_supplier_price_record(record_id))
        if not record_rows:
            raise HTTPException(status_code=500, detail="报价写入成功但返回数据缺失")

        comparison_response = _build_product_supplier_quotes_response(decoded_key)
        created_item = next(
            (
                item for item in comparison_response["items"]
                if int(item.get("supplier_id") or 0) == supplier_id
            ),
            None,
        )
        if not created_item:
            base_row = record_rows[0]
            created_item = {
                "supplier_id": supplier_id,
                "supplier_name": base_row.get("supplier_name"),
                "contact_name": base_row.get("contact_name"),
                "contact_phone": base_row.get("contact_phone"),
                "market_scope": base_row.get("market_scope"),
                "market_category": base_row.get("market_category") or base_row.get("supplier_market_category"),
                "channel": base_row.get("channel") or base_row.get("supplier_channel"),
                "price_identity_key": decoded_key,
                "price_identity_label": base_row.get("price_identity_label"),
                "product_name": base_row.get("product_name"),
                "category": base_row.get("category"),
                "spec_text": base_row.get("spec_text"),
                "quote_price": _normalize_float(base_row.get("quote_price")),
                "quote_unit": base_row.get("quote_unit"),
                "box_price": _normalize_float(base_row.get("box_price")),
                "tax_price": _normalize_float(base_row.get("tax_price")),
                "inventory_status": base_row.get("inventory_status"),
                "remarks": base_row.get("remarks"),
                "quoted_by": base_row.get("quoted_by"),
                "quoted_at": base_row.get("quoted_at"),
                "price_diff_to_market_lowest": None,
                "price_diff_to_market_average": None,
                "comparison_label": "已录入",
            }
        return SupplierQuoteCreateResponse(item=created_item)

    @app.get("/api/suppliers/{supplier_id}/quotes", response_model=SupplierQuoteListResponse)
    def supplier_quotes(supplier_id: int, limit: int = Query(default=20, ge=1, le=100)) -> SupplierQuoteListResponse:
        rows = _sanitize_dataframe(get_db().get_supplier_quote_records(supplier_id, limit=limit))
        items = [_build_supplier_quote_item(row) for row in rows]
        return SupplierQuoteListResponse(items=items)

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
