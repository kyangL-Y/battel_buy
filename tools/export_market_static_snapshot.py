from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.app import (  # noqa: E402
    _build_source_coverage_rows,
    _cached_liancai_facets_payload,
    _cached_market_summary_payload,
    _cached_product_summary_payload,
    _cached_product_trend_payload,
    _product_options_page_from_market_summary,
    _product_response_cache_bucket,
    _sanitize_dataframe,
)
from analysis.metrics import (  # noqa: E402
    _build_price_identity_frame,
    _collapse_trend_to_daily_latest,
    _prepare_trend_display_rows,
    apply_location_priority,
    build_cross_site_identity_frame,
    compute_single_product_summary,
    get_location_options,
    prepare_history,
)
from api.deps import get_db, get_latest_df  # noqa: E402


DEFAULT_OUTPUT = ROOT / "web" / "public" / "data" / "market-snapshot.json"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def _facet_key(top_category: str | None, subcategory: str | None) -> str:
    return f"{str(top_category or '').strip()}\u0001{str(subcategory or '').strip()}"


def _build_location_options() -> dict:
    latest_df = get_latest_df()
    provinces, cities, province_city_map = get_location_options(latest_df)
    return {
        "provinces": provinces,
        "cities": cities,
        "province_city_map": province_city_map,
    }


def _build_liancai_category_summary() -> list[dict]:
    try:
        return _sanitize_dataframe(get_db().get_liancai_category_summary())
    except Exception:
        return []


def _iter_trend_product_options(product_options: list[dict], trend_limit: int) -> list[dict]:
    usable_options = [
        item for item in product_options
        if str(item.get("price_identity_key") or "").strip()
    ]
    if trend_limit < 0:
        return usable_options
    return usable_options[:trend_limit]


def _build_history_by_identity() -> dict[str, Any]:
    history_df = get_db().get_trend_history()
    if history_df.empty:
        return {}
    history_df = _build_price_identity_frame(prepare_history(history_df))
    history_df = build_cross_site_identity_frame(history_df)
    if "cross_site_identity_key" not in history_df.columns:
        return {}
    history_df = history_df[history_df["current_price"].notna()].copy()
    if history_df.empty:
        return {}
    return {
        str(identity_key): group.copy()
        for identity_key, group in history_df.groupby("cross_site_identity_key", dropna=False)
        if str(identity_key or "").strip()
    }


def _build_cross_market_trend_items(history_group: Any) -> list[dict]:
    if history_group is None or history_group.empty:
        return []
    base = history_group.copy()
    base["captured_at"] = pd.to_datetime(base["captured_at"], errors="coerce")
    base = _prepare_trend_display_rows(base)
    base = apply_location_priority(base)
    if base.empty:
        return []
    base = base.sort_values(
        ["location_priority", "captured_at", "trend_series_name"],
        ascending=[True, True, True],
        na_position="last",
    )
    return _sanitize_dataframe(_collapse_trend_to_daily_latest(base))


def build_snapshot(trend_limit: int, single_market_series_limit: int, include_facets: bool) -> dict:
    cache_bucket = _product_response_cache_bucket()
    summary_rows = list(_cached_market_summary_payload(cache_bucket, "", "", "", "", "", "", "", ""))
    product_options = list(_product_options_page_from_market_summary(summary_rows, limit=0, offset=0).get("items") or [])
    liancai_category_summary = _build_liancai_category_summary()

    product_summaries: dict[str, Any] = {}
    product_trends: dict[str, Any] = {}
    history_by_identity = _build_history_by_identity() if trend_limit != 0 else {}
    for option in _iter_trend_product_options(product_options, trend_limit):
        identity_key = str(option.get("price_identity_key") or "").strip()
        if not identity_key:
            continue
        history_group = history_by_identity.get(identity_key)
        if history_group is not None and not history_group.empty:
            product_summaries[identity_key] = compute_single_product_summary(history_group, identity_key)
            cross_items = _build_cross_market_trend_items(history_group)
        else:
            product_summaries[identity_key] = _cached_product_summary_payload(
                identity_key,
                cache_bucket,
                "",
                "",
                "",
                "",
                "",
                "",
            )
            _, cross_rows = _cached_product_trend_payload(
                identity_key,
                cache_bucket,
                "cross_market",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            )
            cross_items = list(cross_rows)
        single_market: dict[str, Any] = {}
        series_keys = []
        for row in cross_items:
            series_key = str(row.get("trend_series_key") or row.get("trend_series_name") or row.get("site_name") or "").strip()
            if series_key and series_key not in series_keys:
                series_keys.append(series_key)
        for series_key in series_keys[:single_market_series_limit]:
            single_market[series_key] = {
                "items": [row for row in cross_items if str(row.get("trend_series_key") or "").strip() == series_key],
            }
        product_trends[identity_key] = {
            "cross_market": {"items": cross_items},
            "single_market": single_market,
        }

    facets: dict[str, Any] = {}
    if include_facets:
        for item in liancai_category_summary:
            top_category = str(item.get("liancai_top_category") or "").strip()
            subcategory = str(item.get("liancai_subcategory") or "").strip()
            if top_category and subcategory:
                facets[_facet_key(top_category, subcategory)] = _cached_liancai_facets_payload(top_category, subcategory)

    return _json_safe({
        "schema_version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "location_options": _build_location_options(),
        "source_coverage": {"items": _build_source_coverage_rows()},
        "market_summary": {
            "items": summary_rows,
            "total": len(summary_rows),
        },
        "product_options": {
            "items": product_options,
            "total": len(product_options),
        },
        "product_summaries": product_summaries,
        "product_trends": product_trends,
        "liancai_category_summary": {"items": liancai_category_summary},
        "liancai_facets": facets,
    })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导出行情展示静态快照 JSON。")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出 JSON 文件路径。")
    parser.add_argument("--trend-limit", type=int, default=300, help="导出趋势的商品数量；-1 表示全部，0 表示不导出趋势。")
    parser.add_argument("--single-market-series-limit", type=int, default=12, help="每个商品导出的单市场趋势序列数量。")
    parser.add_argument("--with-facets", action="store_true", help="同时导出莲菜网关键词/品牌筛选面。会访问莲菜网接口，耗时更长。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = build_snapshot(
        trend_limit=args.trend_limit,
        single_market_series_limit=max(0, args.single_market_series_limit),
        include_facets=args.with_facets,
    )
    output_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"exported {output_path}")
    print(f"summary={snapshot['market_summary']['total']} options={snapshot['product_options']['total']} trends={len(snapshot['product_trends'])}")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
