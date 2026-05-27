from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import shutil
import json
import logging
from time import monotonic
from urllib.parse import unquote

import pandas as pd
from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from analysis.metrics import (
    build_cross_market_product_trend,
    build_single_market_product_trend,
    build_single_product_selector_options,
    compute_cross_site_price_summary,
    compute_single_product_summary,
    get_location_options,
)
from analysis.alerts import AlertRule, load_alert_rules, save_alert_rules
from api.crawl_manager import CrawlManager
from api.deps import (
    ensure_supplier_access,
    get_actor_display_name,
    get_auth_user_by_username,
    get_identity_aliases,
    get_current_user,
    get_db,
    get_history_df,
    get_auth_user_by_id,
    is_admin_user,
    get_latest_df,
    get_product_keys_for_identity,
    get_product_history_identity_df,
    require_admin_user,
    require_authenticated_user,
    get_runtime_settings,
    get_signal_history_df,
    resolve_settlement_record_access_supplier_id,
    resolve_supplier_record_access_supplier_id,
)
from crawler.public_source_crawlers import LiancaiAppGatewayClient
from api.schemas import (
    AISearchRequest,
    AISearchResponse,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthMeResponse,
    AuthUserCreateRequest,
    AuthUserDeleteResponse,
    AuthUserItem,
    AuthUserListResponse,
    AuthUserUpdateRequest,
    CrawlRunRequest,
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
    SourceConfigUpdateRequest,
    GlobalAlertRulesUpdateRequest,
    SourceStrategyUpdateRequest,
    SupplierCreateRequest,
    SupplierItem,
    SupplierListResponse,
    SupplierRegistrationCreateRequest,
    SupplierRegistrationRequestItem,
    SupplierRegistrationRequestListResponse,
    SupplierRegistrationReviewRequest,
    SupplierOverviewResponse,
    SupplierQuoteActionCreateRequest,
    SupplierQuoteActionItem,
    SupplierQuoteActionListResponse,
    SupplierSettlementBuildFromQuotesRequest,
    SupplierSettlementCancelRequest,
    SupplierSettlementCreateRequest,
    SupplierSettlementDetailResponse,
    SupplierSettlementItem,
    SupplierSettlementListResponse,
    SupplierSettlementUpdateRequest,
    SupplierQuoteListResponse,
    SupplierQuoteItem,
    SupplierQuoteImportItemRequest,
    SupplierQuoteImportPreviewItem,
    SupplierQuoteImportPreviewRequest,
    SupplierQuoteImportPreviewResponse,
    SupplierQuoteImportRequest,
    SupplierQuoteImportResponse,
    SupplierQuoteImportResultItem,
    SupplierQuoteInvalidateRequest,
    SupplierQuoteInvalidateResponse,
    SupplierQuoteCreateRequest,
    SupplierQuoteCreateResponse,
    SupplierUpdateRequest,
)
from utils.auth import create_access_token, hash_password, verify_password
from services.decision_engine import (
    build_pricing_packages,
    build_procurement_recommendation,
    build_product_signal_detail,
    build_sales_demo_content,
    build_signals_overview,
)
from services.ai_extractor import AIExtractorError, can_use_ai_extraction, run_search_query
from services.menu_planner import build_procurement_plan, enrich_menu_items_with_ai, parse_menu_text
from services.site_rule_registry import load_site_rules, save_site_rules
from utils.config_loader import load_json_config
from utils.config_loader import BASE_DIR as CONFIG_BASE_DIR
from utils.config_loader import save_json_config
from utils.source_config import get_source_name, get_source_tier, is_source_enabled


_CRAWL_MANAGER = CrawlManager()
logger = logging.getLogger(__name__)
_PRODUCT_RESPONSE_CACHE_TTL_SECONDS = 300.0
_DEFAULT_MARKET_SUMMARY_LIMIT = 500
_PRODUCT_OPTIONS_FULL_COMPUTE_LIMIT = 1000
_LAST_CACHE_CLEARED_CRAWL_FINISHED_AT: str | None = None
MARKET_SUMMARY_DISK_CACHE_DIR = CONFIG_BASE_DIR / 'data' / 'market_summary_cache'
DEFAULT_SUPPLIER_QUOTE_DUPLICATE_MATCH_FIELDS = (
    "quote_price",
    "quote_unit",
    "box_price",
    "tax_price",
    "inventory_status",
    "remarks",
    "channel",
    "market_category",
    "market_scope",
)
SUPPORTED_SUPPLIER_QUOTE_DUPLICATE_MATCH_FIELDS = frozenset(DEFAULT_SUPPLIER_QUOTE_DUPLICATE_MATCH_FIELDS)
ACCOUNT_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{2,63}$")
MIN_ACCOUNT_PASSWORD_LENGTH = 8


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


@lru_cache(maxsize=64)
def _cached_liancai_facets_payload(liancai_top_category: str, liancai_subcategory: str) -> dict:
    top_name = str(liancai_top_category or "").strip()
    sub_name = str(liancai_subcategory or "").strip()
    if not top_name or not sub_name:
        return {"keywords": [], "brands": []}

    client = LiancaiAppGatewayClient()
    classify_payload = client.classify(pid="0", is_chaid="1")
    class_list = classify_payload.get("data", {}).get("classList") or []
    top_item = next((item for item in class_list if str(item.get("name") or "").strip() == top_name and int(item.get("level") or 0) == 0), None)
    if top_item is None:
        return {"keywords": [], "brands": []}
    sub_item = next(
        (
            item for item in class_list
            if str(item.get("name") or "").strip() == sub_name
            and str(item.get("parent") or "").strip() == str(top_item.get("term_id") or "").strip()
            and int(item.get("level") or 0) == 1
        ),
        None,
    )
    if sub_item is None:
        return {"keywords": [], "brands": []}

    payload = client.posts_keywords(str(sub_item.get("term_id") or ""))
    data = payload.get("data", {}) or {}
    keywords = sorted({str(item).strip() for item in (data.get("keywords_list") or []) if str(item).strip()})
    brands = sorted({str(item.get("brand_name") or "").strip() for item in (data.get("sale_brand_lists") or []) if str(item.get("brand_name") or "").strip()})
    return {"keywords": keywords, "brands": brands}


def _product_response_cache_bucket() -> int:
    return int(monotonic() // _PRODUCT_RESPONSE_CACHE_TTL_SECONDS)


def _clear_product_response_caches() -> None:
    _cached_product_history_payload.cache_clear()
    _cached_product_summary_payload.cache_clear()
    _cached_product_trend_payload.cache_clear()
    _cached_product_options_payload.cache_clear()
    _cached_market_summary_payload.cache_clear()


def _sync_product_response_cache_with_crawl_status(item: dict) -> dict:
    global _LAST_CACHE_CLEARED_CRAWL_FINISHED_AT
    finished_at = str(item.get("last_finished_at") or "").strip()
    if not item.get("is_running") and finished_at and finished_at != _LAST_CACHE_CLEARED_CRAWL_FINISHED_AT:
        _clear_product_response_caches()
        _LAST_CACHE_CLEARED_CRAWL_FINISHED_AT = finished_at
    return item




def _market_summary_cache_path(
    province: str,
    city: str,
    keyword: str,
    source_name: str,
    liancai_top_category: str,
    liancai_subcategory: str,
    liancai_keyword: str,
    liancai_brand: str,
) -> Path:
    payload = json.dumps(
        {
            "province": province,
            "city": city,
            "keyword": keyword,
            "source_name": source_name,
            "liancai_top_category": liancai_top_category,
            "liancai_subcategory": liancai_subcategory,
            "liancai_keyword": liancai_keyword,
            "liancai_brand": liancai_brand,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    return MARKET_SUMMARY_DISK_CACHE_DIR / f"{digest}.json"


def _load_market_summary_disk_cache(cache_path: Path) -> tuple[dict, ...] | None:
    try:
        if not cache_path.exists():
            return None
        with cache_path.open("r", encoding="utf-8") as handle:
            rows = json.load(handle)
        if not isinstance(rows, list):
            return None
        return tuple(item for item in rows if isinstance(item, dict))
    except Exception:
        return None


def _save_market_summary_disk_cache(cache_path: Path, rows: tuple[dict, ...]) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = cache_path.with_suffix(".json.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(list(rows), handle, ensure_ascii=False)
        temp_path.replace(cache_path)
    except Exception:
        return None


def _clear_market_summary_disk_cache() -> None:
    try:
        shutil.rmtree(MARKET_SUMMARY_DISK_CACHE_DIR, ignore_errors=True)
    except Exception:
        return None

async def _warm_startup_caches() -> None:
    return None


@lru_cache(maxsize=64)
def _cached_product_history_payload(identity_key: str, cache_bucket: int) -> tuple[dict, ...]:
    history_df = get_product_history_identity_df(identity_key)
    supplier_history_df = _build_supplier_quotes_market_frame(get_identity_aliases(identity_key))
    if history_df is None or history_df.empty:
        history_df = supplier_history_df
    elif not supplier_history_df.empty:
        history_df = pd.concat([history_df, supplier_history_df], ignore_index=True, sort=False)
    return tuple(_sanitize_dataframe(history_df))


def _cached_product_history_df(identity_key: str, cache_bucket: int) -> pd.DataFrame:
    rows = _cached_product_history_payload(str(identity_key or ""), cache_bucket)
    return pd.DataFrame(list(rows))


@lru_cache(maxsize=128)
def _cached_product_summary_payload(
    identity_key: str,
    cache_bucket: int,
    province: str,
    city: str,
    source_name: str,
    liancai_top_category: str,
    liancai_subcategory: str,
    liancai_keyword: str,
    liancai_brand: str,
) -> dict:
    history_df = _cached_product_history_df(identity_key, cache_bucket)
    history_df = _filter_by_source_name(history_df, source_name or None)
    history_df = _filter_by_liancai_category(
        history_df,
        liancai_top_category=liancai_top_category or None,
        liancai_subcategory=liancai_subcategory or None,
        liancai_keyword=liancai_keyword or None,
        liancai_brand=liancai_brand or None,
    )
    return compute_single_product_summary(
        history_df,
        identity_key,
        selected_province=province or None,
        selected_city=city or None,
    )


@lru_cache(maxsize=128)
def _cached_product_trend_payload(
    identity_key: str,
    cache_bucket: int,
    mode: str,
    site_name: str,
    series_key: str,
    province: str,
    city: str,
    source_name: str,
    liancai_top_category: str,
    liancai_subcategory: str,
    liancai_keyword: str,
    liancai_brand: str,
) -> tuple[str, tuple[dict, ...]]:
    history_df = _cached_product_history_df(identity_key, cache_bucket)
    history_df = _filter_by_source_name(history_df, source_name or None)
    history_df = _filter_by_liancai_category(
        history_df,
        liancai_top_category=liancai_top_category or None,
        liancai_subcategory=liancai_subcategory or None,
        liancai_keyword=liancai_keyword or None,
        liancai_brand=liancai_brand or None,
    )
    if mode == "single_market":
        trend_df = build_single_market_product_trend(
            history_df,
            identity_key,
            site_name or None,
            series_key or None,
            selected_province=province or None,
            selected_city=city or None,
        )
        resolved_mode = "single_market"
    else:
        trend_df = build_cross_market_product_trend(
            history_df,
            identity_key,
            selected_province=province or None,
            selected_city=city or None,
        )
        resolved_mode = "cross_market"
    return resolved_mode, tuple(_sanitize_dataframe(trend_df))


def _product_options_page_from_market_summary(
    summary_rows: tuple[dict, ...] | list[dict],
    *,
    limit: int,
    offset: int,
) -> dict:
    total = len(summary_rows)
    start = min(offset, total)
    end = total if limit == 0 else min(start + limit, total)
    page_rows = list(summary_rows[start:end])
    items: list[dict] = []
    for row in page_rows:
        item = dict(row)
        if "price_identity_label" not in item:
            item["price_identity_label"] = item.get("product_name")
        if "price_observation_count" not in item:
            item["price_observation_count"] = item.get("market_count", item.get("site_count"))
        if "site_count" not in item:
            item["site_count"] = item.get("market_count")
        for column in [
            "price_identity_key",
            "price_identity_label",
            "site_count",
            "price_observation_count",
            "latest_captured_at",
            "source_name",
            "source_category",
            "liancai_top_category",
            "liancai_subcategory",
            "liancai_keyword",
            "liancai_brand_name",
            "image_url",
        ]:
            item.setdefault(column, None)
        items.append(
            {
                "price_identity_key": item.get("price_identity_key"),
                "price_identity_label": item.get("price_identity_label"),
                "site_count": item.get("site_count"),
                "price_observation_count": item.get("price_observation_count"),
                "latest_captured_at": item.get("latest_captured_at"),
                "source_name": item.get("source_name"),
                "source_category": item.get("source_category"),
                "liancai_top_category": item.get("liancai_top_category"),
                "liancai_subcategory": item.get("liancai_subcategory"),
                "liancai_keyword": item.get("liancai_keyword"),
                "liancai_brand_name": item.get("liancai_brand_name"),
                "image_url": item.get("image_url"),
            }
        )
    return {
        "items": _sanitize_dataframe(pd.DataFrame(items)) if items else [],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": end < total,
    }


def _filter_product_option_items(items: tuple[dict, ...] | list[dict], keyword: str | None) -> tuple[dict, ...]:
    normalized_keyword = str(keyword or "").strip().casefold()
    if not normalized_keyword:
        return tuple(items)

    def matches(item: dict) -> bool:
        haystack = " ".join(
            str(item.get(column) or "").strip()
            for column in [
                "price_identity_label",
                "price_identity_key",
                "source_name",
                "source_category",
                "liancai_top_category",
                "liancai_subcategory",
                "liancai_keyword",
                "liancai_brand_name",
            ]
        ).casefold()
        return normalized_keyword in haystack

    return tuple(item for item in items if matches(item))


def _fetch_latest_product_rows(
    *,
    province: str | None = None,
    city: str | None = None,
    keyword: str | None = None,
    source_name: str | None = None,
    liancai_top_category: str | None = None,
    liancai_subcategory: str | None = None,
    liancai_keyword: str | None = None,
    liancai_brand: str | None = None,
    limit: int,
    offset: int = 0,
) -> list[dict]:
    capped_limit = min(max(int(limit or 0), 0), 1000)
    normalized_offset = max(int(offset or 0), 0)
    if capped_limit == 0:
        return []
    fetch_limit = capped_limit + 1
    where_clauses: list[str] = []
    params: dict[str, object] = {"limit": fetch_limit, "offset": normalized_offset}

    def add_product_filter(clause: str) -> None:
        where_clauses.append(clause.format(alias="p"))

    if province:
        add_product_filter("{alias}.province = :province")
        params["province"] = province
    if city:
        add_product_filter("{alias}.city = :city")
        params["city"] = city
    normalized_keyword = str(keyword or "").strip()
    if normalized_keyword:
        params["keyword_like"] = f"%{normalized_keyword}%"
        add_product_filter(
            """
            (
                {alias}.group_name LIKE :keyword_like
                OR {alias}.product_name LIKE :keyword_like
                OR {alias}.category LIKE :keyword_like
                OR {alias}.brand LIKE :keyword_like
                OR {alias}.product_series LIKE :keyword_like
                OR {alias}.spec_text LIKE :keyword_like
            )
            """
        )
    normalized_source_name = str(source_name or "").strip()
    if normalized_source_name:
        params["source_name"] = normalized_source_name
        params["source_name_like"] = f"{normalized_source_name}%"
        source_clauses = ["{alias}.site_name = :source_name", "{alias}.site_name LIKE :source_name_like"]
        if normalized_source_name == "莲菜网":
            params["source_url_like"] = "%liancaiwang.cn%"
            source_clauses.append("{alias}.source_url LIKE :source_url_like")
        elif normalized_source_name == "PFSC":
            params["source_url_like"] = "%pfsc.agri.cn%"
            source_clauses.append("{alias}.source_url LIKE :source_url_like")
        elif normalized_source_name == "Chinaprice":
            params["source_url_like"] = "%chinaprice.cn%"
            source_clauses.append("{alias}.source_url LIKE :source_url_like")
        elif normalized_source_name == "万邦国际":
            params["source_url_like"] = "%wbncp.com%"
            source_clauses.append("{alias}.source_url LIKE :source_url_like")
        add_product_filter(f"({' OR '.join(source_clauses)})")
    if liancai_top_category:
        add_product_filter("{alias}.liancai_top_category = :liancai_top_category")
        params["liancai_top_category"] = liancai_top_category
    if liancai_subcategory:
        add_product_filter("{alias}.liancai_subcategory = :liancai_subcategory")
        params["liancai_subcategory"] = liancai_subcategory
    if liancai_keyword:
        add_product_filter("{alias}.liancai_keyword = :liancai_keyword")
        params["liancai_keyword"] = liancai_keyword
    if liancai_brand:
        add_product_filter("({alias}.liancai_brand_id = :liancai_brand OR {alias}.liancai_brand_name = :liancai_brand)")
        params["liancai_brand"] = liancai_brand
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    select_sql = """
        SELECT
            p.group_name,
            p.product_key,
            p.product_name,
            p.category,
            p.brand,
            p.product_series,
            p.spec_text,
            p.compare_key,
            p.province,
            p.city,
            p.market_name,
            p.region_label,
            p.liancai_top_category,
            p.liancai_subcategory,
            p.liancai_keyword,
            p.liancai_brand_id,
            p.liancai_brand_name,
            p.liancai_mapping_source,
            p.liancai_mapped_at,
            p.site_name,
            p.source_url,
            r.current_price,
            r.original_price,
            r.promotion_text,
            r.currency,
            r.unit_name,
            r.unit_value,
            r.unit_price,
            NULL AS raw_payload,
            CASE
                WHEN (p.site_name LIKE '莲菜网%' OR p.source_url LIKE '%liancaiwang.cn%') THEN p.image_url
                ELSE NULL
            END AS image_url,
            CASE
                WHEN r.unit_name = 'g' AND r.unit_value IS NOT NULL AND r.unit_value > 0 AND r.current_price IS NOT NULL
                THEN ROUND(r.current_price / r.unit_value * 500, 4)
                ELSE NULL
            END AS jin_price,
            r.captured_at
    """
    if where_clauses:
        sql = f"""
            {select_sql}
            FROM products p
            JOIN price_records r ON r.id = (
                SELECT r2.id
                FROM price_records r2
                WHERE r2.product_id = p.id
                ORDER BY r2.captured_at DESC, r2.id DESC
                LIMIT 1
            )
            {where_sql}
            ORDER BY r.captured_at DESC
            LIMIT :limit OFFSET :offset
        """
    else:
        sql = f"""
            {select_sql}
            FROM price_records r
            JOIN (
                SELECT product_id, MAX(id) AS latest_record_id
                FROM price_records
                GROUP BY product_id
            ) latest ON latest.latest_record_id = r.id
            JOIN products p ON p.id = r.product_id
            ORDER BY r.captured_at DESC
            LIMIT :limit OFFSET :offset
        """
    with get_db().connect() as conn:
        return [dict(row) for row in conn.execute(text(sql), params).mappings().all()]


def _build_fast_market_summary_page(
    *,
    province: str | None,
    city: str | None,
    keyword: str | None,
    source_name: str | None,
    liancai_top_category: str | None,
    liancai_subcategory: str | None,
    liancai_keyword: str | None,
    liancai_brand: str | None,
    limit: int,
    offset: int,
) -> dict:
    capped_limit = min(max(int(limit or 0), 0), 1000)
    normalized_offset = max(int(offset or 0), 0)
    if capped_limit == 0:
        return {"items": [], "total": None, "limit": capped_limit, "offset": normalized_offset, "has_more": True}
    raw_fetch_limit = min(max(capped_limit * 3, capped_limit + 1), 1000)
    probe_fetch_limit = min(raw_fetch_limit + 1, 1001)
    rows = _fetch_latest_product_rows(
        province=province,
        city=city,
        keyword=keyword,
        source_name=source_name,
        liancai_top_category=liancai_top_category,
        liancai_subcategory=liancai_subcategory,
        liancai_keyword=liancai_keyword,
        liancai_brand=liancai_brand,
        limit=probe_fetch_limit,
        offset=normalized_offset,
    )
    has_more = len(rows) > raw_fetch_limit
    latest_df = pd.DataFrame(rows[:raw_fetch_limit])
    summary_df = compute_cross_site_price_summary(
        latest_df,
        selected_province=province or None,
        selected_city=city or None,
    )
    if len(summary_df) > capped_limit:
        summary_df = summary_df.head(capped_limit).copy()
    return {
        "items": _sanitize_dataframe(summary_df),
        "total": None,
        "limit": capped_limit,
        "offset": normalized_offset,
        "next_offset": normalized_offset + raw_fetch_limit if has_more else normalized_offset + len(rows),
        "has_more": has_more,
    }


def _build_fast_product_options_page(
    *,
    province: str | None,
    city: str | None,
    source_name: str | None,
    liancai_top_category: str | None,
    liancai_subcategory: str | None,
    limit: int,
    offset: int,
) -> dict:
    capped_limit = min(max(int(limit or 0), 0), 1000)
    normalized_offset = max(int(offset or 0), 0)
    if capped_limit == 0:
        return {"items": [], "total": None, "limit": capped_limit, "offset": normalized_offset, "has_more": True}
    probe_fetch_limit = min(capped_limit + 1, 1001)
    rows = _fetch_latest_product_rows(
        province=province,
        city=city,
        source_name=source_name,
        liancai_top_category=liancai_top_category,
        liancai_subcategory=liancai_subcategory,
        limit=probe_fetch_limit,
        offset=normalized_offset,
    )
    has_more = len(rows) > capped_limit
    page_rows = rows[:capped_limit]
    latest_df = pd.DataFrame(page_rows)
    latest_df = _filter_by_liancai_category(
        latest_df,
        liancai_top_category=liancai_top_category or None,
        liancai_subcategory=liancai_subcategory or None,
    )
    summary_df = compute_cross_site_price_summary(
        latest_df,
        selected_province=province or None,
        selected_city=city or None,
    )
    rows_payload = tuple(_sanitize_dataframe(summary_df))
    page = _product_options_page_from_market_summary(rows_payload, limit=capped_limit, offset=0)
    page["total"] = None
    page["offset"] = normalized_offset
    page["has_more"] = bool(has_more or page.get("has_more"))
    return page


@lru_cache(maxsize=32)
def _cached_product_options_payload(
    cache_bucket: int,
    province: str,
    city: str,
    source_name: str,
    liancai_top_category: str,
    liancai_subcategory: str,
    liancai_keyword: str,
    liancai_brand: str,
) -> tuple[dict, ...]:
    summary_rows = _cached_market_summary_payload(
        cache_bucket,
        province,
        city,
        "",
        source_name,
        liancai_top_category,
        liancai_subcategory,
        liancai_keyword,
        liancai_brand,
    )
    options_df = pd.DataFrame(list(summary_rows))
    if not options_df.empty:
        options_df = options_df.rename(columns={"product_name": "price_identity_label"}).copy()
        if "price_observation_count" not in options_df.columns:
            options_df["price_observation_count"] = pd.to_numeric(
                options_df.get("market_count", options_df.get("site_count")),
                errors="coerce",
            )
        if "site_count" not in options_df.columns:
            options_df["site_count"] = pd.to_numeric(options_df.get("market_count"), errors="coerce")
        if "latest_captured_at" not in options_df.columns:
            options_df["latest_captured_at"] = pd.NA
        for column in [
            "price_identity_key",
            "price_identity_label",
            "site_count",
            "price_observation_count",
            "latest_captured_at",
            "location_priority",
            "source_name",
            "source_category",
            "liancai_top_category",
            "liancai_subcategory",
            "liancai_keyword",
            "liancai_brand_name",
            "image_url",
        ]:
            if column not in options_df.columns:
                options_df[column] = None
        options_df = options_df[
            [
                "price_identity_key",
                "price_identity_label",
                "site_count",
                "price_observation_count",
                "latest_captured_at",
                "location_priority",
                "source_name",
                "source_category",
                "liancai_top_category",
                "liancai_subcategory",
                "liancai_keyword",
                "liancai_brand_name",
                "image_url",
            ]
        ].copy()
        options_df = options_df[
            options_df["price_identity_key"].fillna("").astype(str).str.strip().ne("")
            & options_df["price_identity_label"].fillna("").astype(str).str.strip().ne("")
        ].copy()
        options_df["latest_captured_at"] = pd.to_datetime(options_df["latest_captured_at"], errors="coerce")
        options_df = options_df.sort_values(
            ["location_priority", "latest_captured_at", "price_identity_label"],
            ascending=[True, False, True],
            na_position="last",
        ).drop(columns=["location_priority"])
    if options_df.empty:
        latest_df = get_latest_df()
        latest_df = _filter_by_source_name(latest_df, source_name or None)
        latest_df = _filter_by_liancai_category(
            latest_df,
            liancai_top_category=liancai_top_category or None,
            liancai_subcategory=liancai_subcategory or None,
            liancai_keyword=liancai_keyword or None,
            liancai_brand=liancai_brand or None,
        )
        options_df = build_single_product_selector_options(
            latest_df,
            selected_province=province or None,
            selected_city=city or None,
        )
    return tuple(_sanitize_dataframe(options_df))


@lru_cache(maxsize=64)
def _cached_market_summary_payload(
    cache_bucket: int,
    province: str,
    city: str,
    keyword: str,
    source_name: str,
    liancai_top_category: str,
    liancai_subcategory: str,
    liancai_keyword: str,
    liancai_brand: str,
) -> tuple[dict, ...]:
    cache_path = _market_summary_cache_path(
        province,
        city,
        keyword,
        source_name,
        liancai_top_category,
        liancai_subcategory,
        liancai_keyword,
        liancai_brand,
    )
    cached_rows = _load_market_summary_disk_cache(cache_path)
    if cached_rows is not None:
        has_quote_count = all("price_observation_count" in row for row in cached_rows)
        has_image_contract = all("image_url" in row for row in cached_rows)
        has_any_image = any(str(row.get("image_url") or "").strip() for row in cached_rows)
        explicit_non_liancai_source = bool(source_name and "莲菜网" not in source_name)
        if has_quote_count and has_image_contract and (has_any_image or explicit_non_liancai_source or not cached_rows):
            return cached_rows
    # 旧磁盘缓存可能缺少真实报价记录数，或者是在 get_latest_records 未透传
    # image_url 时生成的全空图片缓存；这里主动重算，避免前端商品图/报价数继续丢失。
    latest_df = get_latest_df()
    supplier_df = _build_supplier_quotes_market_frame()
    if not supplier_df.empty:
        latest_df = pd.concat([latest_df, supplier_df], ignore_index=True, sort=False)
    latest_df = _filter_by_source_name(latest_df, source_name or None)
    latest_df = _filter_by_liancai_category(
        latest_df,
        liancai_top_category=liancai_top_category or None,
        liancai_subcategory=liancai_subcategory or None,
        liancai_keyword=liancai_keyword or None,
        liancai_brand=liancai_brand or None,
    )
    if keyword and "product_name" in latest_df.columns:
        search_text = latest_df["product_name"].fillna("").astype(str)
        latest_df = latest_df[search_text.str.contains(keyword, regex=False)]
    summary_df = compute_cross_site_price_summary(
        latest_df,
        selected_province=province or None,
        selected_city=city or None,
    )
    summary_rows = tuple(_sanitize_dataframe(summary_df))
    _save_market_summary_disk_cache(cache_path, summary_rows)
    return summary_rows


def _normalize_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        normalized_value = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(normalized_value):
        return None
    return round(normalized_value, 2)


def _normalize_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        normalized_value = int(value)
    except (TypeError, ValueError):
        return None
    return normalized_value or None


def _normalize_date_bound(value: str | None, boundary: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if boundary == "end" and len(text) == 10:
        return f"{text}T23:59:59"
    return text


def _build_supplier_quotes_market_frame(
    price_identity_keys: list[str] | None = None,
) -> pd.DataFrame:
    try:
        quote_df = get_db().get_latest_supplier_quotes(price_identity_keys=price_identity_keys)
    except TypeError:
        if not price_identity_keys:
            return pd.DataFrame()
        quote_df = get_db().get_latest_supplier_quotes(price_identity_keys[0])
    if quote_df is None or quote_df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for row in _sanitize_dataframe(quote_df):
        price_identity_key = str(row.get("price_identity_key") or "").strip()
        if not price_identity_key:
            continue
        price_identity_label = str(row.get("price_identity_label") or row.get("product_name") or price_identity_key).strip()
        supplier_name = str(row.get("supplier_name") or "").strip() or "供应平台"
        market_category = str(row.get("market_category") or row.get("supplier_market_category") or row.get("category") or "").strip()
        rows.append(
            {
                "group_name": "供应平台",
                "product_name": row.get("product_name") or price_identity_label,
                "product_key": price_identity_key,
                "site_name": supplier_name,
                "source_url": f"supplier://{row.get('supplier_id') or 0}/price-record/{row.get('record_id') or 0}",
                "market_name": "供应商报价",
                "category": market_category,
                "liancai_top_category": row.get("market_category") or row.get("supplier_market_category"),
                "liancai_subcategory": market_category,
                "spec_text": row.get("spec_text") or row.get("quote_unit"),
                "current_price": row.get("quote_price"),
                "captured_at": row.get("quoted_at") or row.get("updated_at"),
                "price_identity_key": price_identity_key,
                "price_identity_label": price_identity_label,
                "channel": row.get("channel") or row.get("supplier_channel"),
                "market_scope": row.get("market_scope"),
                "source_tier": "供应商报价",
            }
        )
    return pd.DataFrame(rows)


_LIANCAI_TOP_CATEGORY_ALIASES = {
    "干调类": {"干调类", "调味品", "调味料", "调味品酱料类", "干货调料", "干货类", "香辛料"},
    "调味品": {"调味品", "干调类", "调味料", "调味品酱料类", "干货调料", "香辛料"},
    "米面粮油": {"米面粮油", "粮油米面", "粮油类", "主食类"},
    "粮油米面": {"粮油米面", "米面粮油", "粮油类", "主食类"},
    "蔬菜类": {"蔬菜类", "蔬菜", "净菜类"},
    "肉禽蛋类": {"肉禽蛋类", "鲜猪肉", "鲜禽类", "禽蛋类", "牛羊肉"},
    "水产类": {"水产类", "鲜活水产", "水产", "海鲜水产"},
}


def _build_liancai_top_category_mask(series: pd.Series, expected: str) -> pd.Series:
    aliases = _LIANCAI_TOP_CATEGORY_ALIASES.get(expected, {expected})
    mask = series == expected
    for alias in aliases:
        if not alias:
            continue
        mask = mask | (series == alias) | series.str.contains(alias, regex=False, na=False)
    return mask


def _filter_by_source_name(df: pd.DataFrame, source_name: str | None = None) -> pd.DataFrame:
    normalized_source = str(source_name or "").strip()
    if not normalized_source or df.empty:
        return df

    source_aliases = {normalized_source}
    if "莲菜网" in normalized_source:
        source_aliases.update({"莲菜网", "莲菜网App", "莲菜商城"})

    text_columns = [
        column
        for column in ["source_name", "site_name", "source_url", "group_name", "lowest_price_site", "highest_price_site"]
        if column in df.columns
    ]
    if not text_columns:
        return df

    mask = pd.Series(False, index=df.index)
    for column in text_columns:
        text_series = df[column].fillna("").astype(str)
        for alias in source_aliases:
            mask = mask | text_series.str.contains(alias, regex=False, na=False)
    return df[mask]


def _filter_by_liancai_category(
    df: pd.DataFrame,
    *,
    liancai_top_category: str | None = None,
    liancai_subcategory: str | None = None,
    liancai_keyword: str | None = None,
    liancai_brand: str | None = None,
) -> pd.DataFrame:
    result = df
    normalized_top = str(liancai_top_category or "").strip()
    if normalized_top and "liancai_top_category" in result.columns:
        top_series = result["liancai_top_category"].fillna("").astype(str).str.strip()
        if normalized_top in {"未映射", "未归类"}:
            result = result[top_series == ""]
        else:
            result = result[_build_liancai_top_category_mask(top_series, normalized_top)]
    normalized_sub = str(liancai_subcategory or "").strip()
    if normalized_sub and "liancai_subcategory" in result.columns:
        sub_series = result["liancai_subcategory"].fillna("").astype(str).str.strip()
        if normalized_sub in {"未映射", "未归类"}:
            result = result[sub_series == ""]
        else:
            result = result[sub_series == normalized_sub]
    normalized_keyword = str(liancai_keyword or "").strip()
    if normalized_keyword:
        if "liancai_keyword" in result.columns:
            keyword_series = result["liancai_keyword"].fillna("").astype(str).str.strip()
            if normalized_keyword in {"未映射", "未归类"}:
                result = result[keyword_series == ""]
            else:
                matched = result[keyword_series == normalized_keyword]
                if matched.empty and "product_name" in result.columns:
                    fallback_mask = result["product_name"].fillna("").astype(str).str.contains(normalized_keyword, regex=False)
                    if "group_name" in result.columns:
                        fallback_mask |= result["group_name"].fillna("").astype(str).str.contains(normalized_keyword, regex=False)
                    if "category" in result.columns:
                        fallback_mask |= result["category"].fillna("").astype(str).str.contains(normalized_keyword, regex=False)
                    matched = result[fallback_mask]
                result = matched
    normalized_brand = str(liancai_brand or "").strip()
    if normalized_brand and "liancai_brand_name" in result.columns:
        brand_series = result["liancai_brand_name"].fillna("").astype(str).str.strip()
        if normalized_brand in {"未映射", "未归类"}:
            result = result[brand_series == ""]
        else:
            result = result[brand_series == normalized_brand]
    return result


def _build_supplier_comparison_label(quote_price: float | None, market_lowest_price: float | None) -> str:
    if quote_price is None or market_lowest_price is None:
        return "待补公开行情"
    diff = round(quote_price - market_lowest_price, 2)
    if abs(diff) < 0.01:
        return "与公开最低价持平"
    if diff < 0:
        return f"低于公开最低价 {abs(diff):.2f}"
    return f"高于公开最低价 {diff:.2f}"


def _build_auth_user_item(user: dict) -> AuthUserItem:
    supplier_profile = user.get("supplier_profile") or None
    supplier_id = int(user.get("supplier_id")) if user.get("supplier_id") is not None else None
    if supplier_profile is None and supplier_id is not None and user.get("supplier_name"):
        supplier_profile = {
            "supplier_id": supplier_id,
            "supplier_name": str(user.get("supplier_name") or "").strip(),
            "market_category": user.get("supplier_market_category"),
            "channel": user.get("supplier_channel"),
            "market_scope": user.get("supplier_market_scope"),
            "is_active": bool(user.get("supplier_is_active")) if user.get("supplier_is_active") is not None else True,
        }
    return AuthUserItem(
        id=int(user.get("id") or 0),
        username=str(user.get("username") or "").strip(),
        role=str(user.get("role") or "supplier"),
        display_name=user.get("display_name"),
        is_active=bool(user.get("is_active")) if user.get("is_active") is not None else True,
        is_deleted=bool(user.get("is_deleted")) if user.get("is_deleted") is not None else False,
        supplier_id=supplier_id,
        supplier_profile=supplier_profile,
        last_login_at=user.get("last_login_at"),
        deleted_at=user.get("deleted_at"),
        deleted_by=user.get("deleted_by"),
        deleted_username=user.get("deleted_username"),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at"),
    )


def _normalize_account_username(value: str | None) -> str | None:
    username = str(value or "").strip()
    if not username:
        return None
    if not ACCOUNT_USERNAME_RE.match(username):
        raise HTTPException(status_code=400, detail="登录账号需为 3-64 位，只能包含字母、数字、下划线、中划线、点或 @")
    return username


def _hash_required_account_password(value: str | None, detail: str) -> str:
    password = str(value or "").strip()
    if not password:
        raise HTTPException(status_code=400, detail=detail)
    if len(password) < MIN_ACCOUNT_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"账号密码至少 {MIN_ACCOUNT_PASSWORD_LENGTH} 位")
    try:
        return hash_password(password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _ensure_account_username_available(username: str, existing_user_id: int | None = None) -> None:
    existing_user = get_auth_user_by_username(username)
    if not existing_user:
        return
    if existing_user_id is not None and int(existing_user.get("id") or 0) == int(existing_user_id):
        return
    raise HTTPException(status_code=400, detail="登录账号已被其他供应商使用")


def _ensure_supplier_account_available(supplier_id: int | None, existing_user_id: int | None = None) -> None:
    if supplier_id is None:
        return
    existing_rows = get_db().get_auth_user_by_supplier_id(int(supplier_id))
    if existing_rows.empty:
        return
    existing_row = existing_rows.iloc[0].to_dict()
    if existing_user_id is not None and int(existing_row.get("id") or 0) == int(existing_user_id):
        return
    raise HTTPException(status_code=400, detail="该供应商已绑定其他登录账号")


def _ensure_auth_user_can_be_removed(user_id: int, existing_user: dict, current_user: dict) -> None:
    if int(current_user.get("id") or 0) == int(user_id):
        raise HTTPException(status_code=400, detail="不能删除或停用当前登录账号")
    if str(existing_user.get("role") or "") != "admin":
        return
    active_admin_rows = _sanitize_dataframe(get_db().get_auth_users(role="admin", active_status="active"))
    active_admin_ids = {int(item.get("id") or 0) for item in active_admin_rows}
    if int(user_id) in active_admin_ids and len(active_admin_ids) <= 1:
        raise HTTPException(status_code=400, detail="至少保留一个启用的管理员账号")


def _build_product_supplier_quotes_response(identity_key: str, supplier_id: int | None = None) -> dict:
    decoded_key = str(identity_key or "").strip()
    history_df = get_product_history_identity_df(decoded_key)
    supplier_history_df = _build_supplier_quotes_market_frame(get_identity_aliases(decoded_key))
    if history_df is None or history_df.empty:
        history_df = supplier_history_df
    elif not supplier_history_df.empty:
        history_df = pd.concat([history_df, supplier_history_df], ignore_index=True, sort=False)
    market_summary = (
        compute_single_product_summary(history_df, decoded_key)
        if history_df is not None and not history_df.empty
        else {}
    )
    identity_aliases = get_identity_aliases(decoded_key)
    try:
        quote_rows = _sanitize_dataframe(get_db().get_latest_supplier_quotes(price_identity_keys=identity_aliases))
    except TypeError:
        quote_rows = _sanitize_dataframe(get_db().get_latest_supplier_quotes(decoded_key))
    if supplier_id is not None:
        quote_rows = [row for row in quote_rows if int(row.get("supplier_id") or 0) == int(supplier_id)]
    market_lowest_price = _normalize_float(market_summary.get("current_lowest_price"))
    market_average_price = _normalize_float(market_summary.get("average_price"))

    items: list[dict] = []
    for row in quote_rows:
        quote_price = _normalize_float(row.get("quote_price"))
        item = {
            "record_id": int(row.get("record_id") or row.get("id") or 0) or None,
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
            "status": str(row.get("status") or "active").strip() or "active",
            "invalidated_at": row.get("invalidated_at"),
            "invalidated_reason": row.get("invalidated_reason"),
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
        or str((lowest_quote_item or {}).get("product_name") or "").strip()
        or decoded_key
    )
    latest_quoted_at = max((str(item.get("quoted_at") or "") for item in items if item.get("quoted_at")), default="") or None
    return {
        "summary": {
            "identity_key": decoded_key,
            "product_name": product_name,
            "supplier_count": len(items),
            "market_lowest_price": market_lowest_price,
            "market_lowest_site": market_summary.get("current_lowest_site"),
            "market_lowest_source_name": market_summary.get("current_lowest_source_name"),
            "market_lowest_source_tier": market_summary.get("current_lowest_source_tier"),
            "market_average_price": market_average_price,
            "lowest_quote": lowest_quote_item.get("quote_price") if lowest_quote_item else None,
            "lowest_quote_supplier": lowest_quote_item.get("supplier_name") if lowest_quote_item else None,
            "latest_quoted_at": latest_quoted_at,
        },
        "items": items,
    }


def _build_supplier_quote_item(row: dict) -> dict:
    return {
        "record_id": int(row.get("record_id") or row.get("id") or 0) or None,
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
        "status": str(row.get("status") or "active").strip() or "active",
        "invalidated_at": row.get("invalidated_at"),
        "invalidated_reason": row.get("invalidated_reason"),
        "quoted_at": row.get("quoted_at"),
        "price_diff_to_market_lowest": None,
        "price_diff_to_market_average": None,
        "comparison_label": None,
    }


def _build_supplier_quote_action_item(row: dict) -> dict:
    return {
        "id": _normalize_int(row.get("id")) or 0,
        "supplier_id": _normalize_int(row.get("supplier_id")) or 0,
        "supplier_name": str(row.get("supplier_name") or "").strip(),
        "record_id": _normalize_int(row.get("record_id")),
        "target_record_id": _normalize_int(row.get("target_record_id")),
        "action_type": str(row.get("action_type") or "").strip(),
        "action_reason": row.get("action_reason"),
        "operator_name": row.get("operator_name"),
        "action_payload": row.get("action_payload"),
        "created_at": row.get("created_at"),
        "price_identity_key": row.get("price_identity_key"),
        "price_identity_label": row.get("price_identity_label"),
        "product_name": row.get("product_name"),
        "quote_price": _normalize_float(row.get("quote_price")),
        "quote_unit": row.get("quote_unit"),
        "quoted_at": row.get("quoted_at"),
        "target_price_identity_label": row.get("target_price_identity_label"),
        "target_product_name": row.get("target_product_name"),
        "target_quote_price": _normalize_float(row.get("target_quote_price")),
        "target_quoted_at": row.get("target_quoted_at"),
    }


def _parse_supplier_settlement_record_ids(value: object) -> list[int]:
    if isinstance(value, list):
        raw_items = value
    else:
        text = str(value or "").strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = [item.strip() for item in text.split(",") if item.strip()]
        raw_items = parsed if isinstance(parsed, list) else []

    normalized_ids: list[int] = []
    seen: set[int] = set()
    for raw_item in raw_items:
        try:
            record_id = int(raw_item)
        except (TypeError, ValueError):
            continue
        if record_id <= 0 or record_id in seen:
            continue
        normalized_ids.append(record_id)
        seen.add(record_id)
    return normalized_ids


def _normalize_supplier_settlement_status(value: object) -> str:
    status = str(value or "pending").strip().lower()
    if status in {"pending", "partial", "paid", "cancelled"}:
        return status
    return "pending"


def _build_supplier_settlement_item(row: dict) -> dict:
    return {
        "id": int(row.get("id") or 0),
        "supplier_id": int(row.get("supplier_id") or 0),
        "supplier_name": str(row.get("supplier_name") or "").strip(),
        "contact_name": row.get("contact_name"),
        "contact_phone": row.get("contact_phone"),
        "market_scope": row.get("market_scope"),
        "market_category": row.get("market_category"),
        "channel": row.get("channel"),
        "settlement_title": str(row.get("settlement_title") or "").strip(),
        "period_start": row.get("period_start"),
        "period_end": row.get("period_end"),
        "quote_record_ids": _parse_supplier_settlement_record_ids(row.get("quote_record_ids")),
        "record_count": int(row.get("record_count") or 0),
        "total_amount": _normalize_float(row.get("total_amount")) or 0,
        "paid_amount": _normalize_float(row.get("paid_amount")) or 0,
        "pending_amount": _normalize_float(row.get("pending_amount")) or 0,
        "status": _normalize_supplier_settlement_status(row.get("status")),
        "payment_due_date": row.get("payment_due_date"),
        "payment_date": row.get("payment_date"),
        "remarks": row.get("remarks"),
        "created_by": row.get("created_by"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _extract_failure_reason(error: Exception) -> str:
    if isinstance(error, HTTPException):
        return str(error.detail)
    return str(error) or error.__class__.__name__


def _validate_supplier_quote_import_item(item: SupplierQuoteImportItemRequest) -> str | None:
    if not str(item.price_identity_key or "").strip():
        return "缺少 price_identity_key"
    if item.quote_price is None:
        return "缺少 quote_price"
    if item.quote_price < 0:
        return "quote_price 不能小于 0"
    if item.box_price is not None and item.box_price < 0:
        return "box_price 不能小于 0"
    if item.tax_price is not None and item.tax_price < 0:
        return "tax_price 不能小于 0"
    return None


def _get_latest_supplier_quote_row(db, supplier_id: int, price_identity_key: str) -> dict | None:
    """Return the latest active supplier quote for the given identity key."""
    identity_aliases = get_identity_aliases(price_identity_key)
    try:
        rows = _sanitize_dataframe(
            db.get_latest_supplier_quote_for_supplier(
                supplier_id,
                price_identity_keys=identity_aliases,
            )
        )
    except TypeError:
        rows = _sanitize_dataframe(db.get_latest_supplier_quote_for_supplier(supplier_id, price_identity_key))
    if not rows:
        return None
    return rows[0]


def _normalize_supplier_quote_text(value: object) -> str:
    return str(value or "").strip()


def _normalize_supplier_quote_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _is_same_supplier_quote_value(current: object, incoming: object) -> bool:
    current_number = _normalize_supplier_quote_number(current)
    incoming_number = _normalize_supplier_quote_number(incoming)
    if current_number is not None or incoming_number is not None:
        return current_number == incoming_number
    return _normalize_supplier_quote_text(current) == _normalize_supplier_quote_text(incoming)


def _resolve_supplier_quote_duplicate_match_fields(fields: list[str] | None) -> tuple[str, ...]:
    normalized_fields: list[str] = []
    for field_name in fields or []:
        normalized_name = str(field_name or "").strip()
        if not normalized_name or normalized_name not in SUPPORTED_SUPPLIER_QUOTE_DUPLICATE_MATCH_FIELDS:
            continue
        if normalized_name not in normalized_fields:
            normalized_fields.append(normalized_name)
    if normalized_fields:
        return tuple(normalized_fields)
    return DEFAULT_SUPPLIER_QUOTE_DUPLICATE_MATCH_FIELDS


def _is_duplicate_supplier_quote(
    latest_quote_row: dict | None,
    item: SupplierQuoteImportItemRequest,
    duplicate_match_fields: tuple[str, ...],
) -> bool:
    if latest_quote_row is None:
        return False
    incoming_values = {
        "quote_price": item.quote_price,
        "quote_unit": item.quote_unit,
        "box_price": item.box_price,
        "tax_price": item.tax_price,
        "inventory_status": item.inventory_status,
        "remarks": item.remarks,
        "channel": item.channel,
        "market_category": item.market_category,
        "market_scope": item.market_scope,
    }
    return all(
        _is_same_supplier_quote_value(latest_quote_row.get(field_name), incoming_values.get(field_name))
        for field_name in duplicate_match_fields
    )


def _build_supplier_quote_abnormal_change(
    latest_quote_row: dict | None,
    item: SupplierQuoteImportItemRequest,
    abnormal_change_ratio_threshold: float | None,
) -> tuple[float | None, str | None]:
    if abnormal_change_ratio_threshold is None:
        return None, None

    latest_quote_price = _normalize_supplier_quote_number((latest_quote_row or {}).get("quote_price"))
    incoming_quote_price = _normalize_supplier_quote_number(item.quote_price)
    if latest_quote_price in {None, 0} or incoming_quote_price is None:
        return None, None

    change_ratio = abs(incoming_quote_price - latest_quote_price) / abs(latest_quote_price)
    if change_ratio < float(abnormal_change_ratio_threshold):
        return None, None

    rounded_ratio = round(change_ratio, 4)
    return (
        rounded_ratio,
        f"较当前最新有效报价波动 {rounded_ratio:.2%}，超过阈值 {float(abnormal_change_ratio_threshold):.2%}",
    )


def _diagnose_supplier_quote_import_item(
    *,
    item: SupplierQuoteImportItemRequest,
    import_mode: str,
    latest_quote_row: dict | None,
    duplicate_match_fields: tuple[str, ...],
    abnormal_change_ratio_threshold: float | None,
) -> dict:
    failure_reason = _validate_supplier_quote_import_item(item)
    existing_record_id = int(latest_quote_row.get("record_id") or latest_quote_row.get("id") or 0) or None if latest_quote_row else None
    existing_quote_price = _normalize_float(latest_quote_row.get("quote_price")) if latest_quote_row else None
    existing_quote_unit = latest_quote_row.get("quote_unit") if latest_quote_row else None
    existing_quoted_at = latest_quote_row.get("quoted_at") if latest_quote_row else None
    existing_remarks = latest_quote_row.get("remarks") if latest_quote_row else None
    abnormal_change_ratio, abnormal_change_hint = _build_supplier_quote_abnormal_change(
        latest_quote_row,
        item,
        abnormal_change_ratio_threshold,
    )

    diagnosis = {
        "failure_reason": failure_reason,
        "preview_status": "append",
        "preview_reason": "将新增为一条报价记录",
        "existing_record_id": existing_record_id,
        "existing_quote_price": existing_quote_price,
        "existing_quote_unit": existing_quote_unit,
        "existing_quoted_at": existing_quoted_at,
        "existing_remarks": existing_remarks,
        "duplicate_match_fields": list(duplicate_match_fields),
        "abnormal_change_ratio": abnormal_change_ratio,
        "abnormal_change_hint": abnormal_change_hint,
        "is_duplicate": False,
    }
    if failure_reason:
        diagnosis["preview_status"] = "invalid"
        diagnosis["preview_reason"] = failure_reason
        return diagnosis

    is_duplicate = _is_duplicate_supplier_quote(latest_quote_row, item, duplicate_match_fields)
    diagnosis["is_duplicate"] = is_duplicate
    if import_mode == "skip_duplicate" and is_duplicate:
        diagnosis["preview_status"] = "skip_duplicate"
        diagnosis["preview_reason"] = "与当前最新有效报价重复，导入时将跳过"
        return diagnosis

    if import_mode == "override_latest" and latest_quote_row is not None:
        diagnosis["preview_status"] = "override_latest"
        diagnosis["preview_reason"] = "将作废当前有效报价，并录入这条新报价"
        return diagnosis

    return diagnosis


def _build_supplier_quote_import_preview_item(
    *,
    row_number: int,
    item: SupplierQuoteImportItemRequest,
    import_mode: str,
    latest_quote_row: dict | None,
    duplicate_match_fields: tuple[str, ...],
    abnormal_change_ratio_threshold: float | None,
) -> SupplierQuoteImportPreviewItem:
    diagnosis = _diagnose_supplier_quote_import_item(
        item=item,
        import_mode=import_mode,
        latest_quote_row=latest_quote_row,
        duplicate_match_fields=duplicate_match_fields,
        abnormal_change_ratio_threshold=abnormal_change_ratio_threshold,
    )
    return SupplierQuoteImportPreviewItem(
        row_number=row_number,
        price_identity_key=item.price_identity_key,
        preview_status=str(diagnosis["preview_status"]),
        preview_reason=diagnosis["preview_reason"],
        existing_record_id=diagnosis["existing_record_id"],
        existing_quote_price=diagnosis["existing_quote_price"],
        existing_quote_unit=diagnosis["existing_quote_unit"],
        existing_quoted_at=diagnosis["existing_quoted_at"],
        existing_remarks=diagnosis["existing_remarks"],
        duplicate_match_fields=diagnosis["duplicate_match_fields"],
        abnormal_change_ratio=diagnosis["abnormal_change_ratio"],
        abnormal_change_hint=diagnosis["abnormal_change_hint"],
    )


def _build_supplier_quote_import_log_payload(
    *,
    payload: SupplierQuoteImportRequest,
    results: list[SupplierQuoteImportResultItem],
    success_record_ids: list[int],
    skipped_examples: list[dict],
    override_examples: list[dict],
    overridden_record_ids: list[int],
) -> dict:
    """Build a compact audit payload for supplier quote imports."""
    failure_examples = [
        {
            "row_number": item.row_number,
            "failure_reason": item.failure_reason,
            "price_identity_key": item.price_identity_key,
        }
        for item in results
        if item.status == "failed"
    ][:5]
    skipped_count = sum(1 for item in results if item.status == "skipped")
    log_payload = {
        "file_name": payload.file_name,
        "import_mode": payload.import_mode,
        "duplicate_match_fields": list(_resolve_supplier_quote_duplicate_match_fields(payload.duplicate_match_fields)),
        "abnormal_change_ratio_threshold": payload.abnormal_change_ratio_threshold,
        "total_count": len(results),
        "success_count": sum(1 for item in results if item.status == "success"),
        "failed_count": sum(1 for item in results if item.status == "failed"),
        "skipped_count": skipped_count,
        "failure_examples": failure_examples,
        "success_record_ids": success_record_ids[:20],
    }
    if skipped_examples:
        log_payload["skipped_examples"] = skipped_examples[:5]
    if overridden_record_ids:
        log_payload["override_count"] = len(overridden_record_ids)
        log_payload["override_record_ids"] = overridden_record_ids[:20]
        log_payload["override_examples"] = override_examples[:5]
    return log_payload


def _create_supplier_quote_record(
    *,
    supplier_id: int | None,
    supplier_name: str | None,
    contact_name: str | None,
    contact_phone: str | None,
    market_scope: str | None,
    market_category: str | None,
    channel: str | None,
    price_identity_key: str,
    price_identity_label: str | None,
    product_name: str | None,
    category: str | None,
    spec_text: str | None,
    quote_price: float,
    quote_unit: str | None,
    box_price: float | None,
    tax_price: float | None,
    inventory_status: str | None,
    remarks: str | None,
    quoted_by: str | None,
    quoted_at: str | None,
    source_record_id: int | None = None,
    db=None,
) -> tuple[int, int, str, dict]:
    if supplier_id is None and not str(supplier_name or "").strip():
        raise HTTPException(status_code=400, detail="请至少提供 supplier_id 或 supplier_name")

    db = db or get_db()
    decoded_key = str(price_identity_key or "").strip()
    if not decoded_key:
        raise HTTPException(status_code=400, detail="price_identity_key 不能为空")

    matched_product_keys = get_product_keys_for_identity(decoded_key)
    resolved_supplier_id = (
        int(supplier_id)
        if supplier_id is not None
        else db.upsert_supplier(
            supplier_name=str(supplier_name or "").strip(),
            contact_name=contact_name,
            contact_phone=contact_phone,
            market_scope=market_scope,
            market_category=market_category,
            channel=channel,
            is_active=True,
        )
    )
    record_id = db.insert_supplier_price_record(
        supplier_id=resolved_supplier_id,
        price_identity_key=decoded_key,
        quoted_at=quoted_at or datetime.utcnow().isoformat(),
        price_identity_label=price_identity_label,
        product_name=product_name or (decoded_key if not matched_product_keys else None),
        category=category,
        spec_text=spec_text,
        market_category=market_category,
        channel=channel,
        quote_price=quote_price,
        quote_unit=quote_unit,
        box_price=box_price,
        tax_price=tax_price,
        inventory_status=inventory_status,
        remarks=remarks,
        quoted_by=quoted_by,
    )
    if source_record_id is not None:
        operator_name = str(quoted_by or contact_name or "").strip() or "供应商管理台"
        db.insert_supplier_quote_action(
            supplier_id=resolved_supplier_id,
            action_type="copy_as_new",
            record_id=source_record_id,
            target_record_id=record_id,
            action_reason="历史报价复制为新报价",
            operator_name=operator_name,
            action_payload={"price_identity_key": decoded_key},
        )

    record_rows = _sanitize_dataframe(db.get_supplier_price_record(record_id))
    if not record_rows:
        raise HTTPException(status_code=500, detail="报价写入成功但返回数据缺失")
    return resolved_supplier_id, record_id, decoded_key, _build_supplier_quote_item(record_rows[0])


def _build_supplier_overview_response(recent_limit: int = 12, supplier_id: int | None = None) -> dict:
    supplier_rows = _sanitize_dataframe(get_db().get_suppliers(active_only=False))
    if supplier_id is not None:
        supplier_rows = [item for item in supplier_rows if int(item.get("id") or 0) == int(supplier_id)]

    if supplier_id is None:
        category_rows = _sanitize_dataframe(get_db().get_supplier_category_summary())
        recent_rows = _sanitize_dataframe(get_db().get_recent_supplier_quotes(limit=recent_limit))
    else:
        current_supplier = supplier_rows[0] if supplier_rows else {}
        category_rows = [
            {
                "market_category": current_supplier.get("market_category") or "未分类",
                "supplier_count": 1 if current_supplier else 0,
                "active_supplier_count": 1 if current_supplier and bool(current_supplier.get("is_active")) else 0,
                "quote_count": int(current_supplier.get("quote_count") or 0),
                "latest_quoted_at": current_supplier.get("latest_quoted_at"),
            }
        ] if current_supplier else []
        recent_rows = _sanitize_dataframe(
            get_db().get_supplier_quote_records(int(supplier_id), limit=recent_limit, offset=0)
        )
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


def _build_supplier_registration_request_item(row: dict) -> dict:
    return {
        "id": int(row.get("id") or 0),
        "company_name": str(row.get("company_name") or "").strip(),
        "contact_name": str(row.get("contact_name") or "").strip() or None,
        "contact_phone": str(row.get("contact_phone") or "").strip() or None,
        "username": str(row.get("username") or "").strip(),
        "status": str(row.get("status") or "pending").strip().lower() or "pending",
        "review_notes": str(row.get("review_notes") or "").strip() or None,
        "supplier_id": _normalize_int(row.get("supplier_id")),
        "reviewed_by": str(row.get("reviewed_by") or "").strip() or None,
        "reviewed_at": str(row.get("reviewed_at") or "").strip() or None,
        "created_at": str(row.get("created_at") or "").strip() or None,
        "updated_at": str(row.get("updated_at") or "").strip() or None,
        "supplier_name": str(row.get("supplier_name") or "").strip() or None,
        "market_category": str(row.get("market_category") or "").strip() or None,
        "channel": str(row.get("channel") or "").strip() or None,
        "supplier_is_active": None if row.get("supplier_is_active") is None else bool(row.get("supplier_is_active")),
    }


def _build_source_coverage_rows() -> list[dict]:
    db = get_db()
    summary_df = db.get_source_coverage_summary()
    configured_sources = load_json_config(CONFIG_BASE_DIR / "config" / "products.json")
    site_rules = load_json_config(CONFIG_BASE_DIR / "config" / "sites.json")
    site_rule_map = {
        str(item.get("site_name") or "").strip(): dict(item)
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
        site_rule = site_rule_map.get(source_site_name, {})
        row["source_url"] = source_url
        row["configured_name"] = configured_name or source_site_name
        row["source_name"] = source_site_name
        row["source_tier"] = get_source_tier(item)
        row["strategy"] = str(item.get("strategy") or "").strip() or str(site_rule.get("strategy") or "").strip() or None
        row["preferred_fetch_mode"] = str(site_rule.get("preferred_fetch_mode") or "").strip() or None
        row["timeout_seconds"] = int(site_rule.get("timeout_seconds") or 0) or None
        row["retry_count"] = int(site_rule.get("retry_count") or 0) if site_rule.get("retry_count") is not None else None
        row["request_delay_seconds"] = float(site_rule.get("request_delay_seconds") or 0) or None
        row["verify_ssl"] = None if site_rule.get("verify_ssl") is None else bool(site_rule.get("verify_ssl"))
        row["api_strategy"] = str(site_rule.get("api_strategy") or "").strip() or None
        blocked_codes = site_rule.get("blocked_status_codes")
        row["blocked_status_codes"] = blocked_codes if isinstance(blocked_codes, list) else None
        row["enabled"] = source_enabled
        row["market_scope"] = str(item.get("market_scope") or "").strip() or None
        row["market_category"] = str(item.get("market_category") or "").strip() or None
        row["market_subcategory"] = str(item.get("category") or "").strip() or None
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


def _update_source_config_item(payload: SourceConfigUpdateRequest) -> dict:
    config_path = CONFIG_BASE_DIR / "config" / "products.json"
    configured_sources = load_json_config(config_path)
    if not isinstance(configured_sources, list):
        raise HTTPException(status_code=500, detail="来源配置文件格式错误")

    target_url = str(payload.source_url or "").strip()
    if not target_url:
        raise HTTPException(status_code=400, detail="缺少来源地址")

    updated = False
    for item in configured_sources:
        if not isinstance(item, dict):
            continue
        if str(item.get("url") or "").strip() != target_url:
            continue
        item["enabled"] = bool(payload.enabled)
        if payload.configured_name is not None:
            item["product_name"] = str(payload.configured_name).strip()
        if payload.market_scope is not None:
            item["market_scope"] = str(payload.market_scope).strip()
        if payload.market_category is not None:
            item["market_category"] = str(payload.market_category).strip()
        if payload.notes is not None:
            item["notes"] = str(payload.notes).strip()
        updated = True
        break

    if not updated:
        raise HTTPException(status_code=404, detail="未找到对应来源配置")

    save_json_config(config_path, configured_sources)

    rows = _build_source_coverage_rows()
    matched = next((row for row in rows if str(row.get("source_url") or "").strip() == target_url), None)
    if matched is None:
        raise HTTPException(status_code=500, detail="来源配置保存后读取失败")
    return matched


def _update_source_strategy_item(payload: SourceStrategyUpdateRequest) -> dict:
    config_path = CONFIG_BASE_DIR / "config" / "sites.json"
    site_rules = load_site_rules(config_path)
    target_name = str(payload.source_name or "").strip()
    if not target_name:
        raise HTTPException(status_code=400, detail="缺少来源名称")

    updated_rule: dict | None = None
    for item in site_rules:
        if not isinstance(item, dict):
            continue
        if str(item.get("site_name") or "").strip() != target_name:
            continue
        if payload.preferred_fetch_mode is not None:
            item["preferred_fetch_mode"] = payload.preferred_fetch_mode
        if payload.strategy is not None:
            item["strategy"] = str(payload.strategy).strip()
        if payload.timeout_seconds is not None:
            item["timeout_seconds"] = int(payload.timeout_seconds)
        if payload.retry_count is not None:
            item["retry_count"] = int(payload.retry_count)
        if payload.request_delay_seconds is not None:
            item["request_delay_seconds"] = float(payload.request_delay_seconds)
        if payload.blocked_status_codes is not None:
            item["blocked_status_codes"] = [int(code) for code in payload.blocked_status_codes]
        if payload.verify_ssl is not None:
            item["verify_ssl"] = bool(payload.verify_ssl)
        if payload.api_strategy is not None:
            item["api_strategy"] = str(payload.api_strategy).strip()
        updated_rule = dict(item)
        break

    if updated_rule is None:
        raise HTTPException(status_code=404, detail="未找到对应抓取策略")

    save_site_rules(config_path, site_rules)
    return updated_rule


def _serialize_global_alert_rules() -> list[dict]:
    return [
        {
            "target_name": item.target_name,
            "threshold": item.threshold,
            "note": item.note,
            "group_name": item.group_name,
        }
        for item in load_alert_rules()
    ]


def _save_global_alert_rules(payload: GlobalAlertRulesUpdateRequest) -> list[dict]:
    rules = [
        AlertRule(
            target_name=str(item.target_name).strip(),
            threshold=float(item.threshold),
            note=str(item.note or "").strip(),
            group_name=str(item.group_name or "").strip() or None,
        )
        for item in payload.items
        if str(item.target_name).strip()
    ]
    save_alert_rules(rules)
    return _serialize_global_alert_rules()


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
        await _warm_startup_caches()
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
        return {"item": _sync_product_response_cache_with_crawl_status(get_crawl_manager().get_status())}

    @app.post("/api/crawl/run", response_model=CrawlRunResponse)
    def crawl_run(payload: CrawlRunRequest = Body(default_factory=CrawlRunRequest)) -> CrawlRunResponse:
        accepted, item = get_crawl_manager().trigger_run(
            "manual",
            target_scope=payload.target_scope,
            target_province=payload.target_province,
            target_city=payload.target_city,
            source_url=payload.source_url,
            source_name=payload.source_name,
        )
        return CrawlRunResponse(accepted=accepted, item=_sync_product_response_cache_with_crawl_status(item))

    @app.post("/api/crawl/schedule")
    def crawl_schedule(payload: CrawlScheduleUpdateRequest) -> dict:
        item = get_crawl_manager().update_schedule(
            enabled=payload.enabled,
            mode=payload.mode,
            daily_run_time=payload.daily_run_time,
            interval_seconds=payload.interval_seconds,
            fetch_mode=payload.fetch_mode,
            target_scope=payload.target_scope,
            target_province=payload.target_province,
            target_city=payload.target_city,
        )
        return {"item": item}

    @app.get("/api/location/options")
    def location_options() -> dict:
        try:
            rows = _fetch_latest_product_rows(limit=1000, offset=0)
            latest_df = pd.DataFrame(rows[:1000])
        except Exception:
            latest_df = get_latest_df()
        provinces, cities, province_city_map = get_location_options(latest_df)
        return {"provinces": provinces, "cities": cities, "province_city_map": province_city_map}

    @app.get("/api/source/coverage")
    def source_coverage() -> dict:
        return {"items": _build_source_coverage_rows()}

    @app.put("/api/source/coverage")
    def update_source_coverage(payload: SourceConfigUpdateRequest) -> dict:
        return {"item": _update_source_config_item(payload)}

    @app.put("/api/source/strategy")
    def update_source_strategy(payload: SourceStrategyUpdateRequest) -> dict:
        return {"item": _update_source_strategy_item(payload)}

    @app.get("/api/settings/alerts")
    def get_global_alert_rules() -> dict:
        return {"items": _serialize_global_alert_rules()}

    @app.put("/api/settings/alerts")
    def update_global_alert_rules(payload: GlobalAlertRulesUpdateRequest) -> dict:
        return {"items": _save_global_alert_rules(payload)}

    @app.get("/api/market/summary")
    def market_summary(
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        source_name: str | None = Query(default=None),
        liancai_top_category: str | None = Query(default=None),
        liancai_subcategory: str | None = Query(default=None),
        liancai_keyword: str | None = Query(default=None),
        liancai_brand: str | None = Query(default=None),
        limit: int = Query(default=_DEFAULT_MARKET_SUMMARY_LIMIT, ge=0),
        offset: int = Query(default=0, ge=0),
    ) -> dict:


        items = _cached_market_summary_payload(
            _product_response_cache_bucket(),
            str(province or ""),
            str(city or ""),
            str(keyword or "").strip(),
            str(source_name or "").strip(),
            str(liancai_top_category or ""),
            str(liancai_subcategory or ""),
            str(liancai_keyword or ""),
            str(liancai_brand or ""),
        )
        total = len(items)
        start = min(offset, total)
        end = total if limit == 0 else min(start + limit, total)
        limited_items = list(items[start:end])
        return {
            "items": limited_items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": end < total,
        }

    @app.get("/api/product/options")
    def product_options(
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        source_name: str | None = Query(default=None),
        liancai_top_category: str | None = Query(default=None),
        liancai_subcategory: str | None = Query(default=None),
        liancai_keyword: str | None = Query(default=None),
        liancai_brand: str | None = Query(default=None),
        limit: int = Query(default=300, ge=0, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        cache_bucket = _product_response_cache_bucket()
        should_compute_full_options = bool(
            province
            or city
            or keyword
            or liancai_keyword
            or liancai_brand
            or limit == 0
        )
        if should_compute_full_options:
            items = _filter_product_option_items(_cached_product_options_payload(
                cache_bucket,
                str(province or ""),
                str(city or ""),
                str(source_name or ""),
                str(liancai_top_category or ""),
                str(liancai_subcategory or ""),
                str(liancai_keyword or ""),
                str(liancai_brand or ""),
            ), keyword)
            total = len(items)
            start = min(offset, total)
            end = total if limit == 0 else min(start + limit, total)
            return {
                "items": list(items[start:end]),
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": end < total,
            }
        should_use_fast_page = bool(
            not province
            and not city
            and not liancai_keyword
            and not liancai_brand
            and limit > 0
            and offset + limit <= _PRODUCT_OPTIONS_FULL_COMPUTE_LIMIT
        )
        if should_use_fast_page:
            fast_page = _build_fast_product_options_page(
                province=province,
                city=city,
                source_name=source_name,
                liancai_top_category=liancai_top_category,
                liancai_subcategory=liancai_subcategory,
                limit=limit,
                offset=offset,
            )
            if fast_page.get("items") or fast_page.get("has_more"):
                return fast_page
            items = _cached_product_options_payload.__wrapped__(
                cache_bucket,
                str(province or ""),
                str(city or ""),
                str(source_name or ""),
                str(liancai_top_category or ""),
                str(liancai_subcategory or ""),
                str(liancai_keyword or ""),
                str(liancai_brand or ""),
            )
            items = _filter_product_option_items(items, keyword)
            total = len(items)
            start = min(offset, total)
            end = total if limit == 0 else min(start + limit, total)
            return {
                "items": list(items[start:end]),
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": end < total,
            }
        summary_rows = _cached_market_summary_payload(
            cache_bucket,
            str(province or ""),
            str(city or ""),
            "",
            "",
            str(liancai_top_category or ""),
            str(liancai_subcategory or ""),
            str(liancai_keyword or ""),
            str(liancai_brand or ""),
        )
        return _product_options_page_from_market_summary(summary_rows, limit=limit, offset=offset)

    @app.get("/api/product/{identity_key}/summary")
    def product_summary(
        identity_key: str,
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
        source_name: str | None = Query(default=None),
        liancai_top_category: str | None = Query(default=None),
        liancai_subcategory: str | None = Query(default=None),
        liancai_keyword: str | None = Query(default=None),
        liancai_brand: str | None = Query(default=None),
    ) -> dict:
        decoded_key = unquote(identity_key)
        item = _cached_product_summary_payload(
            decoded_key,
            _product_response_cache_bucket(),
            str(province or ""),
            str(city or ""),
            str(source_name or "").strip(),
            str(liancai_top_category or ""),
            str(liancai_subcategory or ""),
            str(liancai_keyword or ""),
            str(liancai_brand or ""),
        )
        return {"item": item}

    @app.get("/api/product/{identity_key}/trend")
    def product_trend(
        identity_key: str,
        mode: str = Query(default="cross_market"),
        site_name: str | None = Query(default=None),
        series_key: str | None = Query(default=None),
        province: str | None = Query(default=None),
        city: str | None = Query(default=None),
        source_name: str | None = Query(default=None),
        liancai_top_category: str | None = Query(default=None),
        liancai_subcategory: str | None = Query(default=None),
        liancai_keyword: str | None = Query(default=None),
        liancai_brand: str | None = Query(default=None),
    ) -> dict:
        decoded_key = unquote(identity_key)
        resolved_mode, items = _cached_product_trend_payload(
            decoded_key,
            _product_response_cache_bucket(),
            mode,
            str(site_name or ""),
            str(series_key or ""),
            str(province or ""),
            str(city or ""),
            str(source_name or "").strip(),
            str(liancai_top_category or ""),
            str(liancai_subcategory or ""),
            str(liancai_keyword or ""),
            str(liancai_brand or ""),
        )
        return {"mode": resolved_mode, "items": list(items)}

    @app.get("/api/liancai/category-summary")
    def liancai_category_summary(source_name: str | None = None) -> dict:
        source_filter = source_name.strip() if source_name else None
        if source_filter:
            summary_df = get_db().get_liancai_category_summary(source_name=source_filter)
        else:
            summary_df = get_db().get_liancai_category_summary()
        return {"items": _sanitize_dataframe(summary_df)}

    @app.get("/api/liancai/facets")
    def liancai_facets(
        liancai_top_category: str | None = Query(default=None),
        liancai_subcategory: str | None = Query(default=None),
    ) -> dict:
        return _cached_liancai_facets_payload(
            str(liancai_top_category or ""),
            str(liancai_subcategory or ""),
        )

    @app.post("/api/auth/login", response_model=AuthLoginResponse)
    def auth_login(payload: AuthLoginRequest) -> AuthLoginResponse:
        user = get_auth_user_by_username(payload.username)
        if not user or not verify_password(payload.password, user.get("password_hash")):
            raise HTTPException(status_code=401, detail="账号或密码错误")
        if not user.get("is_active"):
            raise HTTPException(status_code=403, detail="当前账号已停用")
        token, expires_in = create_access_token(
            user_id=int(user["id"]),
            username=str(user["username"]),
            role=str(user["role"]),
            supplier_id=int(user["supplier_id"]) if user.get("supplier_id") is not None else None,
            display_name=user.get("display_name"),
        )
        get_db().touch_auth_user_login(int(user["id"]))
        latest_user = get_auth_user_by_id(int(user["id"])) or user
        return AuthLoginResponse(access_token=token, expires_in=expires_in, user=_build_auth_user_item(latest_user))

    @app.get("/api/auth/me", response_model=AuthMeResponse)
    def auth_me(current_user: dict = Depends(require_authenticated_user)) -> AuthMeResponse:
        return AuthMeResponse(user=_build_auth_user_item(current_user))

    @app.get("/api/auth/users", response_model=AuthUserListResponse)
    def auth_users(
        role: str | None = Query(default=None),
        status: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        current_user: dict = Depends(require_admin_user),
    ) -> AuthUserListResponse:
        rows = _sanitize_dataframe(
            get_db().get_auth_users(role=role, active_status=status, keyword=keyword)
        )
        return AuthUserListResponse(items=[_build_auth_user_item(row) for row in rows])

    @app.post("/api/auth/users", response_model=AuthUserItem)
    def create_auth_user(
        payload: AuthUserCreateRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> AuthUserItem:
        username = _normalize_account_username(payload.username)
        if not username:
            raise HTTPException(status_code=400, detail="登录账号不能为空")
        supplier_id = payload.supplier_id if payload.role == "supplier" else None
        if payload.role == "supplier" and supplier_id is None:
            raise HTTPException(status_code=400, detail="供应商账号必须绑定供应商")
        _ensure_account_username_available(username)
        _ensure_supplier_account_available(supplier_id)
        password_hash = _hash_required_account_password(payload.password, "创建账号时必须填写初始密码")
        try:
            user_id = get_db().upsert_auth_user(
                username=username,
                password_hash=password_hash,
                role=payload.role,
                supplier_id=supplier_id,
                display_name=payload.display_name,
                is_active=payload.is_active,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        created_user = get_auth_user_by_id(user_id)
        if not created_user:
            raise HTTPException(status_code=500, detail="账号创建成功但返回数据缺失")
        return _build_auth_user_item(created_user)

    @app.put("/api/auth/users/{user_id}", response_model=AuthUserItem)
    def update_auth_user(
        user_id: int,
        payload: AuthUserUpdateRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> AuthUserItem:
        existing_user = get_auth_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="账号不存在")
        if int(current_user.get("id") or 0) == int(user_id):
            if payload.role != "admin":
                raise HTTPException(status_code=400, detail="不能把当前登录管理员降级为供应商")
            if not payload.is_active:
                raise HTTPException(status_code=400, detail="不能删除或停用当前登录账号")
        if str(existing_user.get("role") or "") == "admin" and (payload.role != "admin" or not payload.is_active):
            active_admin_rows = _sanitize_dataframe(get_db().get_auth_users(role="admin", active_status="active"))
            active_admin_ids = {int(item.get("id") or 0) for item in active_admin_rows}
            if int(user_id) in active_admin_ids and len(active_admin_ids) <= 1:
                raise HTTPException(status_code=400, detail="至少保留一个启用的管理员账号")

        username = _normalize_account_username(payload.username)
        if not username:
            raise HTTPException(status_code=400, detail="登录账号不能为空")
        supplier_id = payload.supplier_id if payload.role == "supplier" else None
        if payload.role == "supplier" and supplier_id is None:
            raise HTTPException(status_code=400, detail="供应商账号必须绑定供应商")
        _ensure_account_username_available(username, existing_user_id=user_id)
        _ensure_supplier_account_available(supplier_id, existing_user_id=user_id)
        password_hash = _hash_required_account_password(payload.password, "账号密码不能为空") if payload.password else None
        try:
            updated_user_id = get_db().upsert_auth_user(
                user_id=user_id,
                username=username,
                password_hash=password_hash,
                role=payload.role,
                supplier_id=supplier_id,
                display_name=payload.display_name,
                is_active=payload.is_active,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        updated_user = get_auth_user_by_id(updated_user_id)
        if not updated_user:
            raise HTTPException(status_code=500, detail="账号更新成功但返回数据缺失")
        return _build_auth_user_item(updated_user)

    @app.delete("/api/auth/users/{user_id}", response_model=AuthUserDeleteResponse)
    def delete_auth_user(
        user_id: int,
        current_user: dict = Depends(require_admin_user),
    ) -> AuthUserDeleteResponse:
        existing_user = get_auth_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="账号不存在")
        _ensure_auth_user_can_be_removed(user_id, existing_user, current_user)
        if not get_db().delete_auth_user(user_id, deleted_by=get_actor_display_name(current_user)):
            raise HTTPException(status_code=404, detail="账号不存在")
        return AuthUserDeleteResponse(deleted=True, user_id=int(user_id))

    @app.get("/api/product/{identity_key}/supplier-quotes", response_model=ProductSupplierQuotesResponse)
    def product_supplier_quotes(
        identity_key: str,
        current_user: dict = Depends(require_authenticated_user),
    ) -> ProductSupplierQuotesResponse:
        decoded_key = unquote(identity_key)
        supplier_scope = None
        if not is_admin_user(current_user):
            supplier_scope = ensure_supplier_access(current_user, int(current_user.get("supplier_id") or 0))
        return ProductSupplierQuotesResponse(**_build_product_supplier_quotes_response(decoded_key, supplier_scope))

    @app.post("/api/supplier-registration-requests", response_model=SupplierRegistrationRequestItem)
    def create_supplier_registration_request(
        payload: SupplierRegistrationCreateRequest,
    ) -> SupplierRegistrationRequestItem:
        try:
            request_id = get_db().create_supplier_registration_request(
                company_name=payload.company_name,
                contact_name=payload.contact_name,
                contact_phone=payload.contact_phone,
                username=payload.username,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        rows = _sanitize_dataframe(get_db().get_supplier_registration_requests())
        request_row = next((item for item in rows if int(item.get("id") or 0) == request_id), None)
        if not request_row:
            raise HTTPException(status_code=500, detail="注册申请创建成功但返回数据缺失")
        return SupplierRegistrationRequestItem(**_build_supplier_registration_request_item(request_row))

    @app.get("/api/supplier-registration-requests", response_model=SupplierRegistrationRequestListResponse)
    def supplier_registration_requests(
        status: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierRegistrationRequestListResponse:
        rows = _sanitize_dataframe(
            get_db().get_supplier_registration_requests(status=status, keyword=keyword)
        )
        return SupplierRegistrationRequestListResponse(
            items=[SupplierRegistrationRequestItem(**_build_supplier_registration_request_item(row)) for row in rows]
        )

    @app.post("/api/supplier-registration-requests/{request_id}/approve", response_model=SupplierRegistrationRequestItem)
    def approve_supplier_registration_request(
        request_id: int,
        payload: SupplierRegistrationReviewRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierRegistrationRequestItem:
        request_rows = _sanitize_dataframe(get_db().get_supplier_registration_requests())
        request_row = next((item for item in request_rows if int(item.get("id") or 0) == int(request_id)), None)
        if not request_row:
            raise HTTPException(status_code=404, detail="未找到注册申请")
        if str(request_row.get("status") or "pending").strip().lower() != "pending":
            raise HTTPException(status_code=400, detail="该注册申请已处理")

        supplier_name = payload.supplier_name or str(request_row.get("company_name") or "").strip()
        contact_name = payload.contact_name if payload.contact_name is not None else request_row.get("contact_name")
        contact_phone = payload.contact_phone if payload.contact_phone is not None else request_row.get("contact_phone")
        account_username = _normalize_account_username(str(request_row.get("username") or ""))
        if not account_username:
            raise HTTPException(status_code=400, detail="注册申请缺少登录账号")
        _ensure_account_username_available(account_username)
        password_hash = _hash_required_account_password(payload.account_password, "通过注册申请时必须填写初始密码")
        try:
            supplier_id = get_db().upsert_supplier(
                supplier_name=supplier_name,
                contact_name=contact_name,
                contact_phone=contact_phone,
                market_scope=payload.market_scope,
                market_category=payload.market_category,
                channel=payload.channel,
                notes=payload.notes,
                is_active=payload.supplier_is_active,
            )
            get_db().upsert_auth_user(
                username=account_username,
                password_hash=password_hash,
                role="supplier",
                supplier_id=supplier_id,
                display_name=payload.account_display_name or contact_name or supplier_name,
                is_active=payload.account_is_active,
            )
            updated_request_id = get_db().update_supplier_registration_request(
                request_id,
                status="approved",
                review_notes=payload.review_notes,
                reviewed_by=get_actor_display_name(current_user),
                supplier_id=supplier_id,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if updated_request_id is None:
            raise HTTPException(status_code=404, detail="未找到注册申请")
        rows = _sanitize_dataframe(get_db().get_supplier_registration_requests())
        updated_row = next((item for item in rows if int(item.get("id") or 0) == int(updated_request_id)), None)
        if not updated_row:
            raise HTTPException(status_code=500, detail="注册申请审核成功但返回数据缺失")
        return SupplierRegistrationRequestItem(**_build_supplier_registration_request_item(updated_row))

    @app.post("/api/supplier-registration-requests/{request_id}/reject", response_model=SupplierRegistrationRequestItem)
    def reject_supplier_registration_request(
        request_id: int,
        payload: SupplierRegistrationReviewRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierRegistrationRequestItem:
        request_rows = _sanitize_dataframe(get_db().get_supplier_registration_requests())
        request_row = next((item for item in request_rows if int(item.get("id") or 0) == int(request_id)), None)
        if not request_row:
            raise HTTPException(status_code=404, detail="未找到注册申请")
        if str(request_row.get("status") or "pending").strip().lower() != "pending":
            raise HTTPException(status_code=400, detail="该注册申请已处理")
        updated_request_id = get_db().update_supplier_registration_request(
            request_id,
            status="rejected",
            review_notes=payload.review_notes,
            reviewed_by=get_actor_display_name(current_user),
        )
        if updated_request_id is None:
            raise HTTPException(status_code=404, detail="未找到注册申请")
        rows = _sanitize_dataframe(get_db().get_supplier_registration_requests())
        updated_row = next((item for item in rows if int(item.get("id") or 0) == int(updated_request_id)), None)
        if not updated_row:
            raise HTTPException(status_code=500, detail="注册申请驳回成功但返回数据缺失")
        return SupplierRegistrationRequestItem(**_build_supplier_registration_request_item(updated_row))

    @app.get("/api/suppliers", response_model=SupplierListResponse)
    def suppliers(
        active_only: bool = Query(default=True),
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierListResponse:
        items = _sanitize_dataframe(get_db().get_suppliers(active_only=active_only))
        if not is_admin_user(current_user):
            supplier_scope = ensure_supplier_access(current_user, int(current_user.get("supplier_id") or 0))
            items = [item for item in items if int(item.get("id") or 0) == supplier_scope]
        return SupplierListResponse(items=items)

    @app.get("/api/suppliers/overview", response_model=SupplierOverviewResponse)
    def suppliers_overview(
        limit: int = Query(default=12, ge=1, le=50),
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierOverviewResponse:
        supplier_scope = None
        if not is_admin_user(current_user):
            supplier_scope = ensure_supplier_access(current_user, int(current_user.get("supplier_id") or 0))
        return SupplierOverviewResponse(**_build_supplier_overview_response(recent_limit=limit, supplier_id=supplier_scope))

    @app.post("/api/suppliers", response_model=SupplierItem)
    def create_supplier(
        payload: SupplierCreateRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierItem:
        account_username = _normalize_account_username(payload.account_username)
        account_password_hash = None
        if account_username:
            _ensure_account_username_available(account_username)
            account_password_hash = _hash_required_account_password(payload.account_password, "创建供应商账号时必须填写初始密码")
        try:
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
            if account_username:
                get_db().upsert_auth_user(
                    username=account_username,
                    password_hash=account_password_hash,
                    role="supplier",
                    supplier_id=supplier_id,
                    display_name=payload.account_display_name or payload.contact_name or payload.supplier_name,
                    is_active=payload.account_is_active,
                )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        supplier_df = get_db().get_suppliers(active_only=False)
        supplier_rows = _sanitize_dataframe(supplier_df)
        supplier_row = next((item for item in supplier_rows if int(item.get("id") or 0) == supplier_id), None)
        if not supplier_row:
            raise HTTPException(status_code=500, detail="供应商创建成功但返回数据缺失")
        return SupplierItem(**supplier_row)

    @app.put("/api/suppliers/{supplier_id}", response_model=SupplierItem)
    def update_supplier(
        supplier_id: int,
        payload: SupplierUpdateRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierItem:
        existing_auth_rows = get_db().get_auth_user_by_supplier_id(supplier_id)
        existing_auth_user = existing_auth_rows.iloc[0].to_dict() if not existing_auth_rows.empty else None
        account_username = _normalize_account_username(payload.account_username)
        if account_username:
            _ensure_account_username_available(
                account_username,
                int(existing_auth_user.get("id") or 0) if existing_auth_user else None,
            )
        if account_username and existing_auth_user is None and not payload.account_password:
            raise HTTPException(status_code=400, detail="创建供应商账号时必须填写初始密码")
        try:
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
            if account_username or existing_auth_user is not None:
                next_password_hash = existing_auth_user.get("password_hash") if existing_auth_user else None
                if payload.account_password:
                    next_password_hash = _hash_required_account_password(payload.account_password, "账号密码不能为空")
                if not (account_username or existing_auth_user):
                    raise HTTPException(status_code=400, detail="供应商账号缺少 username")
                get_db().upsert_auth_user(
                    user_id=int(existing_auth_user.get("id") or 0) if existing_auth_user else None,
                    username=account_username or str(existing_auth_user.get("username") or ""),
                    password_hash=next_password_hash,
                    role="supplier",
                    supplier_id=updated_supplier_id,
                    display_name=payload.account_display_name or payload.contact_name or payload.supplier_name,
                    is_active=payload.account_is_active if payload.account_is_active is not None else bool(existing_auth_user.get("is_active")) if existing_auth_user else True,
                )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        supplier_df = get_db().get_suppliers(active_only=False)
        supplier_rows = _sanitize_dataframe(supplier_df)
        supplier_row = next((item for item in supplier_rows if int(item.get("id") or 0) == updated_supplier_id), None)
        if not supplier_row:
            raise HTTPException(status_code=404, detail="未找到供应商")
        return SupplierItem(**supplier_row)

    @app.post("/api/supplier-prices", response_model=SupplierQuoteCreateResponse)
    def create_supplier_price(
        payload: SupplierQuoteCreateRequest,
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierQuoteCreateResponse:
        if is_admin_user(current_user):
            resolved_supplier_id = payload.supplier_id
            resolved_supplier_name = payload.supplier_name
        else:
            resolved_supplier_id = ensure_supplier_access(current_user, int(current_user.get("supplier_id") or 0))
            resolved_supplier_name = None
        supplier_id, record_id, decoded_key, fallback_item = _create_supplier_quote_record(
            supplier_id=resolved_supplier_id,
            supplier_name=resolved_supplier_name,
            contact_name=payload.contact_name,
            contact_phone=payload.contact_phone,
            market_scope=payload.market_scope,
            market_category=payload.market_category,
            channel=payload.channel,
            price_identity_key=payload.price_identity_key,
            price_identity_label=payload.price_identity_label,
            product_name=payload.product_name,
            category=payload.category,
            spec_text=payload.spec_text,
            quote_price=payload.quote_price,
            quote_unit=payload.quote_unit,
            box_price=payload.box_price,
            tax_price=payload.tax_price,
            inventory_status=payload.inventory_status,
            remarks=payload.remarks,
            quoted_by=get_actor_display_name(current_user),
            quoted_at=payload.quoted_at,
            source_record_id=payload.source_record_id,
        )
        comparison_response = _build_product_supplier_quotes_response(
            decoded_key,
            None if is_admin_user(current_user) else int(current_user.get("supplier_id") or 0),
        )
        created_item = next(
            (
                item for item in comparison_response["items"]
                if int(item.get("record_id") or 0) == record_id or int(item.get("supplier_id") or 0) == supplier_id
            ),
            None,
        )
        if not created_item:
            created_item = dict(fallback_item)
            created_item["comparison_label"] = "已录入"
        return SupplierQuoteCreateResponse(item=created_item)

    @app.post("/api/supplier-prices/import", response_model=SupplierQuoteImportResponse)
    def import_supplier_prices(
        payload: SupplierQuoteImportRequest,
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierQuoteImportResponse:
        supplier_id = ensure_supplier_access(
            current_user,
            payload.supplier_id if is_admin_user(current_user) else int(current_user.get("supplier_id") or 0),
        )
        operator_name = get_actor_display_name(current_user)
        db = get_db()
        duplicate_match_fields = _resolve_supplier_quote_duplicate_match_fields(payload.duplicate_match_fields)
        abnormal_change_ratio_threshold = payload.abnormal_change_ratio_threshold
        results: list[SupplierQuoteImportResultItem] = []
        success_record_ids: list[int] = []
        skipped_examples: list[dict] = []
        override_examples: list[dict] = []
        overridden_record_ids: list[int] = []

        for index, item in enumerate(payload.items, start=1):
            row_number = item.row_number or index
            normalized_key = str(item.price_identity_key or "").strip()
            latest_quote_row = None
            if normalized_key and (
                payload.import_mode in {"skip_duplicate", "override_latest"} or abnormal_change_ratio_threshold is not None
            ):
                latest_quote_row = _get_latest_supplier_quote_row(db, supplier_id, normalized_key)
            if latest_quote_row is not None and int(latest_quote_row.get("supplier_id") or supplier_id) != supplier_id:
                latest_quote_row = None

            diagnosis = _diagnose_supplier_quote_import_item(
                item=item,
                import_mode=payload.import_mode,
                latest_quote_row=latest_quote_row,
                duplicate_match_fields=duplicate_match_fields,
                abnormal_change_ratio_threshold=abnormal_change_ratio_threshold,
            )
            if diagnosis["failure_reason"]:
                results.append(
                    SupplierQuoteImportResultItem(
                        row_number=row_number,
                        status="failed",
                        failure_reason=str(diagnosis["failure_reason"]),
                        price_identity_key=item.price_identity_key,
                        price_identity_label=item.price_identity_label,
                        product_name=item.product_name,
                        duplicate_match_fields=diagnosis["duplicate_match_fields"],
                    )
                )
                continue

            if payload.import_mode == "skip_duplicate" and diagnosis["is_duplicate"]:
                existing_record_id = diagnosis["existing_record_id"]
                results.append(
                    SupplierQuoteImportResultItem(
                        row_number=row_number,
                        status="skipped",
                        failure_reason="检测到重复报价，已按 skip_duplicate 跳过",
                        record_id=existing_record_id,
                        price_identity_key=latest_quote_row.get("price_identity_key") or normalized_key,
                        price_identity_label=latest_quote_row.get("price_identity_label") or item.price_identity_label,
                        product_name=latest_quote_row.get("product_name") or item.product_name,
                        duplicate_match_fields=diagnosis["duplicate_match_fields"],
                        abnormal_change_ratio=diagnosis["abnormal_change_ratio"],
                        abnormal_change_hint=diagnosis["abnormal_change_hint"],
                    )
                )
                skipped_examples.append(
                    {
                        "row_number": row_number,
                        "price_identity_key": normalized_key,
                        "existing_record_id": existing_record_id,
                    }
                )
                continue

            if payload.import_mode == "override_latest" and latest_quote_row is not None:
                try:
                    invalidated_record_ids = db.invalidate_supplier_quotes_by_identity(
                        supplier_id,
                        reason=f"导入覆盖：{operator_name}",
                        price_identity_keys=get_identity_aliases(normalized_key),
                    )
                except TypeError:
                    invalidated_record_ids = db.invalidate_supplier_quotes_by_identity(
                        supplier_id,
                        normalized_key,
                        reason=f"导入覆盖：{operator_name}",
                    )
                if invalidated_record_ids:
                    overridden_record_ids.extend(invalidated_record_ids)
                    override_examples.append(
                        {
                            "row_number": row_number,
                            "price_identity_key": normalized_key,
                            "invalidated_record_ids": invalidated_record_ids[:10],
                        }
                    )

            try:
                _, record_id, _, created_item = _create_supplier_quote_record(
                    supplier_id=supplier_id,
                    supplier_name=None,
                    contact_name=None,
                    contact_phone=None,
                    market_scope=item.market_scope,
                    market_category=item.market_category,
                    channel=item.channel,
                    price_identity_key=normalized_key,
                    price_identity_label=item.price_identity_label,
                    product_name=item.product_name,
                    category=item.category,
                    spec_text=item.spec_text,
                    quote_price=float(item.quote_price),
                    quote_unit=item.quote_unit,
                    box_price=item.box_price,
                    tax_price=item.tax_price,
                    inventory_status=item.inventory_status,
                    remarks=item.remarks,
                    quoted_by=operator_name,
                    quoted_at=item.quoted_at,
                    db=db,
                )
            except Exception as error:
                results.append(
                    SupplierQuoteImportResultItem(
                        row_number=row_number,
                        status="failed",
                        failure_reason=_extract_failure_reason(error),
                        price_identity_key=item.price_identity_key,
                        price_identity_label=item.price_identity_label,
                        product_name=item.product_name,
                        duplicate_match_fields=diagnosis["duplicate_match_fields"],
                        abnormal_change_ratio=diagnosis["abnormal_change_ratio"],
                        abnormal_change_hint=diagnosis["abnormal_change_hint"],
                    )
                )
                continue

            success_record_ids.append(record_id)
            results.append(
                SupplierQuoteImportResultItem(
                    row_number=row_number,
                    status="success",
                    record_id=record_id,
                    price_identity_key=created_item.get("price_identity_key"),
                    price_identity_label=created_item.get("price_identity_label"),
                    product_name=created_item.get("product_name"),
                    duplicate_match_fields=diagnosis["duplicate_match_fields"],
                    abnormal_change_ratio=diagnosis["abnormal_change_ratio"],
                    abnormal_change_hint=diagnosis["abnormal_change_hint"],
                )
            )

        success_count = sum(1 for item in results if item.status == "success")
        skipped_count = sum(1 for item in results if item.status == "skipped")
        failed_count = sum(1 for item in results if item.status == "failed")
        if success_count > 0 or skipped_count > 0 or overridden_record_ids:
            db.insert_supplier_quote_action(
                supplier_id=supplier_id,
                action_type="import_quotes",
                record_id=success_record_ids[0] if success_record_ids else None,
                action_reason=f"批量导入报价，成功 {success_count} 条，跳过 {skipped_count} 条，失败 {failed_count} 条",
                operator_name=operator_name,
                action_payload=_build_supplier_quote_import_log_payload(
                    payload=payload,
                    results=results,
                    success_record_ids=success_record_ids,
                    skipped_examples=skipped_examples,
                    override_examples=override_examples,
                    overridden_record_ids=overridden_record_ids,
                ),
            )

        return SupplierQuoteImportResponse(
            total_count=len(results),
            success_count=success_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            items=results,
        )

    @app.post("/api/supplier-prices/import-preview", response_model=SupplierQuoteImportPreviewResponse)
    def preview_import_supplier_prices(
        payload: SupplierQuoteImportPreviewRequest,
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierQuoteImportPreviewResponse:
        db = get_db()
        supplier_id = ensure_supplier_access(
            current_user,
            payload.supplier_id if is_admin_user(current_user) else int(current_user.get("supplier_id") or 0),
        )
        duplicate_match_fields = _resolve_supplier_quote_duplicate_match_fields(payload.duplicate_match_fields)
        preview_items: list[SupplierQuoteImportPreviewItem] = []
        for index, item in enumerate(payload.items, start=1):
            row_number = item.row_number or index
            normalized_key = _normalize_supplier_quote_text(item.price_identity_key)
            latest_quote_row = _get_latest_supplier_quote_row(db, supplier_id, normalized_key) if normalized_key else None
            preview_items.append(
                _build_supplier_quote_import_preview_item(
                    row_number=row_number,
                    item=item,
                    import_mode=payload.import_mode,
                    latest_quote_row=latest_quote_row,
                    duplicate_match_fields=duplicate_match_fields,
                    abnormal_change_ratio_threshold=payload.abnormal_change_ratio_threshold,
                )
            )
        return SupplierQuoteImportPreviewResponse(items=preview_items)

    @app.post("/api/supplier-prices/{record_id}/invalidate", response_model=SupplierQuoteInvalidateResponse)
    def invalidate_supplier_price(
        record_id: int,
        payload: SupplierQuoteInvalidateRequest,
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierQuoteInvalidateResponse:
        resolve_supplier_record_access_supplier_id(current_user, record_id)
        original_rows = _sanitize_dataframe(get_db().get_supplier_price_record(record_id))
        if not original_rows:
            raise HTTPException(status_code=404, detail="未找到对应报价记录")
        original_row = original_rows[0]
        original_status = str(original_row.get("status") or "active").strip() or "active"
        operator_name = get_actor_display_name(current_user)
        invalidated_record_id = get_db().invalidate_supplier_price_record(record_id, reason=payload.reason)
        if invalidated_record_id is None:
            raise HTTPException(status_code=404, detail="未找到对应报价记录")

        record_rows = _sanitize_dataframe(get_db().get_supplier_price_record(invalidated_record_id))
        if not record_rows:
            raise HTTPException(status_code=500, detail="报价作废成功但返回数据缺失")
        get_db().insert_supplier_quote_action(
            supplier_id=int(original_row.get("supplier_id") or 0),
            action_type="update_invalidation_reason" if original_status == "invalidated" else "invalidate",
            record_id=invalidated_record_id,
            action_reason=payload.reason,
            operator_name=operator_name,
            action_payload={
                "price_identity_key": original_row.get("price_identity_key"),
                "price_identity_label": original_row.get("price_identity_label"),
                "product_name": original_row.get("product_name"),
                "quote_price": _normalize_float(original_row.get("quote_price")),
                "quote_unit": original_row.get("quote_unit"),
                "quoted_at": original_row.get("quoted_at"),
                "previous_status": original_status,
                "previous_invalidated_reason": original_row.get("invalidated_reason"),
                "next_invalidated_reason": payload.reason,
            },
        )
        return SupplierQuoteInvalidateResponse(item=SupplierQuoteItem(**_build_supplier_quote_item(record_rows[0])))

    @app.get("/api/suppliers/{supplier_id}/quotes", response_model=SupplierQuoteListResponse)
    def supplier_quotes(
        supplier_id: int,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        status: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        start_quoted_at: str | None = Query(default=None),
        end_quoted_at: str | None = Query(default=None),
        price_identity_key: str | None = Query(default=None),
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierQuoteListResponse:
        supplier_id = ensure_supplier_access(current_user, supplier_id)
        normalized_end = _normalize_date_bound(end_quoted_at, "end")
        identity_aliases = get_identity_aliases(price_identity_key or "") if price_identity_key else []
        rows = _sanitize_dataframe(
            get_db().get_supplier_quote_records(
                supplier_id,
                limit=limit,
                offset=offset,
                status=status,
                keyword=keyword,
                start_quoted_at=start_quoted_at,
                end_quoted_at=normalized_end,
                price_identity_keys=identity_aliases,
            )
        )
        total = get_db().count_supplier_quote_records(
            supplier_id,
            status=status,
            keyword=keyword,
            start_quoted_at=start_quoted_at,
            end_quoted_at=normalized_end,
            price_identity_keys=identity_aliases,
        )
        items = [_build_supplier_quote_item(row) for row in rows]
        return SupplierQuoteListResponse(items=items, total=total, limit=limit, offset=offset, has_more=offset + len(items) < total)

    @app.get("/api/suppliers/{supplier_id}/quote-actions", response_model=SupplierQuoteActionListResponse)
    def supplier_quote_actions(
        supplier_id: int,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        action_type: str | None = Query(default=None),
        operator_name: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        start_created_at: str | None = Query(default=None),
        end_created_at: str | None = Query(default=None),
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierQuoteActionListResponse:
        supplier_id = ensure_supplier_access(current_user, supplier_id)
        normalized_end = _normalize_date_bound(end_created_at, "end")
        rows = _sanitize_dataframe(
            get_db().get_supplier_quote_actions(
                supplier_id,
                limit=limit,
                offset=offset,
                action_type=action_type,
                operator_name=operator_name,
                keyword=keyword,
                start_created_at=start_created_at,
                end_created_at=normalized_end,
            )
        )
        total = get_db().count_supplier_quote_actions(
            supplier_id,
            action_type=action_type,
            operator_name=operator_name,
            keyword=keyword,
            start_created_at=start_created_at,
            end_created_at=normalized_end,
        )
        items = [SupplierQuoteActionItem(**_build_supplier_quote_action_item(row)) for row in rows]
        return SupplierQuoteActionListResponse(items=items, total=total, limit=limit, offset=offset, has_more=offset + len(items) < total)

    @app.post("/api/suppliers/{supplier_id}/quote-actions", response_model=SupplierQuoteActionItem)
    def create_supplier_quote_action(
        supplier_id: int,
        payload: SupplierQuoteActionCreateRequest,
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierQuoteActionItem:
        supplier_id = ensure_supplier_access(current_user, supplier_id)
        action_id = get_db().insert_supplier_quote_action(
            supplier_id=supplier_id,
            action_type=payload.action_type,
            record_id=payload.record_id,
            target_record_id=payload.target_record_id,
            action_reason=payload.action_reason,
            operator_name=get_actor_display_name(current_user),
            action_payload=payload.action_payload,
        )
        rows = _sanitize_dataframe(get_db().get_supplier_quote_actions(supplier_id, limit=100))
        action_row = next((row for row in rows if int(row.get("id") or 0) == action_id), None)
        if not action_row:
            raise HTTPException(status_code=500, detail="操作日志写入成功但返回数据缺失")
        return SupplierQuoteActionItem(**_build_supplier_quote_action_item(action_row))

    @app.get("/api/suppliers/{supplier_id}/settlements", response_model=SupplierSettlementListResponse)
    def supplier_settlements(
        supplier_id: int,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        status: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        start_period_start: str | None = Query(default=None),
        end_period_end: str | None = Query(default=None),
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierSettlementListResponse:
        supplier_id = ensure_supplier_access(current_user, supplier_id)
        rows = _sanitize_dataframe(
            get_db().get_supplier_settlement_records(
                supplier_id,
                limit=limit,
                offset=offset,
                status=status,
                keyword=keyword,
                start_period_start=start_period_start,
                end_period_end=end_period_end,
            )
        )
        total = get_db().count_supplier_settlement_records(
            supplier_id,
            status=status,
            keyword=keyword,
            start_period_start=start_period_start,
            end_period_end=end_period_end,
        )
        items = [SupplierSettlementItem(**_build_supplier_settlement_item(row)) for row in rows]
        return SupplierSettlementListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(items) < total,
        )

    @app.get("/api/supplier-settlements/{record_id}", response_model=SupplierSettlementDetailResponse)
    def supplier_settlement_detail(
        record_id: int,
        current_user: dict = Depends(require_authenticated_user),
    ) -> SupplierSettlementDetailResponse:
        resolve_settlement_record_access_supplier_id(current_user, record_id)
        rows = _sanitize_dataframe(get_db().get_supplier_settlement_record(record_id))
        if not rows:
            raise HTTPException(status_code=404, detail="未找到对应结算台账")

        item = SupplierSettlementItem(**_build_supplier_settlement_item(rows[0]))
        quote_rows = _sanitize_dataframe(
            get_db().get_supplier_price_records_by_ids(
                item.supplier_id,
                item.quote_record_ids,
            )
        )
        quote_items = [SupplierQuoteItem(**_build_supplier_quote_item(row)) for row in quote_rows]
        return SupplierSettlementDetailResponse(item=item, quote_items=quote_items)

    @app.post("/api/suppliers/{supplier_id}/settlements", response_model=SupplierSettlementItem)
    def create_supplier_settlement(
        supplier_id: int,
        payload: SupplierSettlementCreateRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierSettlementItem:
        supplier_id = ensure_supplier_access(current_user, supplier_id)
        try:
            settlement_id = get_db().insert_supplier_settlement_record(
                supplier_id=supplier_id,
                settlement_title=payload.settlement_title,
                period_start=payload.period_start,
                period_end=payload.period_end,
                quote_record_ids=payload.quote_record_ids,
                total_amount=payload.total_amount,
                paid_amount=payload.paid_amount,
                status=payload.status,
                payment_due_date=payload.payment_due_date,
                payment_date=payload.payment_date,
                remarks=payload.remarks,
                created_by=get_actor_display_name(current_user),
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        rows = _sanitize_dataframe(get_db().get_supplier_settlement_record(settlement_id))
        if not rows:
            raise HTTPException(status_code=500, detail="结算台账创建成功但返回数据缺失")
        created_item = SupplierSettlementItem(**_build_supplier_settlement_item(rows[0]))
        get_db().insert_supplier_quote_action(
            supplier_id=supplier_id,
            action_type="create_settlement",
            action_reason=f"创建结算单：{created_item.settlement_title}",
            operator_name=get_actor_display_name(current_user),
            action_payload={
                "settlement_id": created_item.id,
                "settlement_title": created_item.settlement_title,
                "record_count": created_item.record_count,
                "total_amount": created_item.total_amount,
                "paid_amount": created_item.paid_amount,
                "status": created_item.status,
            },
        )
        return created_item

    @app.put("/api/supplier-settlements/{record_id}", response_model=SupplierSettlementItem)
    def update_supplier_settlement(
        record_id: int,
        payload: SupplierSettlementUpdateRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierSettlementItem:
        resolve_settlement_record_access_supplier_id(current_user, record_id)
        before_rows = _sanitize_dataframe(get_db().get_supplier_settlement_record(record_id))
        if not before_rows:
            raise HTTPException(status_code=404, detail="未找到对应结算台账")
        before_item = _build_supplier_settlement_item(before_rows[0])
        try:
            updated_record_id = get_db().update_supplier_settlement_record(
                record_id,
                settlement_title=payload.settlement_title,
                period_start=payload.period_start,
                period_end=payload.period_end,
                quote_record_ids=payload.quote_record_ids,
                total_amount=payload.total_amount,
                paid_amount=payload.paid_amount,
                status=payload.status,
                payment_due_date=payload.payment_due_date,
                payment_date=payload.payment_date,
                remarks=payload.remarks,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if updated_record_id is None:
            raise HTTPException(status_code=404, detail="未找到对应结算台账")

        rows = _sanitize_dataframe(get_db().get_supplier_settlement_record(updated_record_id))
        if not rows:
            raise HTTPException(status_code=500, detail="结算台账更新成功但返回数据缺失")
        updated_item = SupplierSettlementItem(**_build_supplier_settlement_item(rows[0]))
        get_db().insert_supplier_quote_action(
            supplier_id=updated_item.supplier_id,
            action_type="update_settlement",
            action_reason=f"更新结算单：{updated_item.settlement_title}",
            operator_name=get_actor_display_name(current_user),
            action_payload={
                "settlement_id": updated_item.id,
                "settlement_title": updated_item.settlement_title,
                "previous_paid_amount": before_item["paid_amount"],
                "next_paid_amount": updated_item.paid_amount,
                "previous_status": before_item["status"],
                "next_status": updated_item.status,
                "payment_due_date": updated_item.payment_due_date,
                "payment_date": updated_item.payment_date,
            },
        )
        return updated_item

    @app.post("/api/supplier-settlements/{record_id}/cancel", response_model=SupplierSettlementItem)
    def cancel_supplier_settlement(
        record_id: int,
        payload: SupplierSettlementCancelRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierSettlementItem:
        resolve_settlement_record_access_supplier_id(current_user, record_id)
        before_rows = _sanitize_dataframe(get_db().get_supplier_settlement_record(record_id))
        if not before_rows:
            raise HTTPException(status_code=404, detail="未找到对应结算台账")
        before_item = _build_supplier_settlement_item(before_rows[0])
        if before_item["status"] == "paid":
            raise HTTPException(status_code=400, detail="已结清结算单不可作废")
        if before_item["status"] == "cancelled":
            raise HTTPException(status_code=400, detail="结算单已作废")

        updated_record_id = get_db().update_supplier_settlement_record(record_id, status="cancelled")
        if updated_record_id is None:
            raise HTTPException(status_code=404, detail="未找到对应结算台账")

        rows = _sanitize_dataframe(get_db().get_supplier_settlement_record(updated_record_id))
        if not rows:
            raise HTTPException(status_code=500, detail="结算台账作废成功但返回数据缺失")
        cancelled_item = SupplierSettlementItem(**_build_supplier_settlement_item(rows[0]))
        cancel_reason = str(payload.cancel_reason or "").strip() or None
        get_db().insert_supplier_quote_action(
            supplier_id=cancelled_item.supplier_id,
            action_type="cancel_settlement",
            action_reason=f"作废结算单：{cancelled_item.settlement_title}",
            operator_name=get_actor_display_name(current_user),
            action_payload={
                "settlement_id": cancelled_item.id,
                "settlement_title": cancelled_item.settlement_title,
                "record_count": cancelled_item.record_count,
                "total_amount": cancelled_item.total_amount,
                "previous_status": before_item["status"],
                "next_status": cancelled_item.status,
                "cancel_reason": cancel_reason,
            },
        )
        return cancelled_item

    @app.post("/api/suppliers/{supplier_id}/settlements/build-from-quotes", response_model=SupplierSettlementItem)
    def build_supplier_settlement_from_quotes(
        supplier_id: int,
        payload: SupplierSettlementBuildFromQuotesRequest,
        current_user: dict = Depends(require_admin_user),
    ) -> SupplierSettlementItem:
        supplier_id = ensure_supplier_access(current_user, supplier_id)
        try:
            settlement_id = get_db().build_supplier_settlement_from_quotes(
                supplier_id=supplier_id,
                settlement_title=payload.settlement_title,
                quote_record_ids=payload.quote_record_ids,
                payment_due_date=payload.payment_due_date,
                remarks=payload.remarks,
                created_by=get_actor_display_name(current_user),
                paid_amount=payload.paid_amount,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        rows = _sanitize_dataframe(get_db().get_supplier_settlement_record(settlement_id))
        if not rows:
            raise HTTPException(status_code=500, detail="结算台账生成成功但返回数据缺失")
        created_item = SupplierSettlementItem(**_build_supplier_settlement_item(rows[0]))
        get_db().insert_supplier_quote_action(
            supplier_id=supplier_id,
            action_type="build_settlement_from_quotes",
            action_reason=f"从已选报价生成结算单：{created_item.settlement_title}",
            operator_name=get_actor_display_name(current_user),
            action_payload={
                "settlement_id": created_item.id,
                "settlement_title": created_item.settlement_title,
                "quote_record_ids": created_item.quote_record_ids,
                "record_count": created_item.record_count,
                "total_amount": created_item.total_amount,
                "status": created_item.status,
            },
        )
        return created_item

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
        return SignalOverviewResponse(
            **build_signals_overview(
                latest_df,
                latest_df,
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

    def build_sales_content_response(scene: str | None = None) -> SalesDemoContentResponse:
        latest_df = get_latest_df()
        return SalesDemoContentResponse(
            **build_sales_demo_content(
                latest_df,
                None,
                scene=scene,
                record_count=get_db().get_price_record_count(),
            )
        )

    @app.get("/api/sales/decision-content", response_model=SalesDemoContentResponse)
    def sales_decision_content(scene: str | None = Query(default=None)) -> SalesDemoContentResponse:
        return build_sales_content_response(scene)

    @app.get("/api/sales/demo-content", response_model=SalesDemoContentResponse)
    def sales_demo_content(scene: str | None = Query(default=None)) -> SalesDemoContentResponse:
        return build_sales_content_response(scene)

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
