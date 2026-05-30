from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawler.public_source_crawlers import (
    MEICAI_DEFAULT_PAGE_SIZE,
    MeicaiAppGatewayClient,
    PublicSourceCrawler,
)
from tools.extract_meicai_category_candidates import load_category_filters_from_sale_class_tree


DEFAULT_SECRET_ENV_FILE = Path(".local-secrets/meicai_address_context.env")
DEFAULT_SALE_CLASS_TREE = Path("tmp/meicai_sale_class_tree.json")
DEFAULT_ENDPOINTS = ("class_products", "goods_info_location", "smart_list_good_list", "xb_feed")
ENDPOINT_PATHS = {
    "class_products": "/entrance/dishes/getSpusByClass",
    "get_spus_by_class": "/entrance/dishes/getSpusByClass",
    "xb_feed": "/entrance/recommend/xbFeed",
    "goods_info_location": "/entrance/recommend/goodsInfoLocation",
    "smart_list_good_list": "/entrance/smartList/getGoodList",
    "recommend_feed": "/recommend/feed",
    "goods_info_stream": "/entrance/recommend/goodsInfoStream",
    "activity_polymerize_product": "/entrance/activity/polymerizeProduct",
    "commodity_goods_rank": "/entrance/commodity/goodsRank",
    "search_goods_list_by_data_id": "/search/getgoodslistbydataid",
}


def build_probe_report(
    *,
    secret_env_file: Path,
    endpoints: list[str],
    sale_class_tree: Path | None,
    limit_filters: int,
    max_pages: int,
    page_size: int,
    base_url: str,
    sleep_seconds: float = 0.0,
) -> dict[str, Any]:
    original_env = snapshot_meicai_env()
    try:
        load_secret_env(secret_env_file)
        request_headers = PublicSourceCrawler._load_json_env_object("MEICAI_REQUEST_HEADERS")
        common_body = PublicSourceCrawler._load_json_env_object("MEICAI_COMMON_BODY")
        address_context = PublicSourceCrawler._load_json_env_object("MEICAI_ADDRESS_CONTEXT")
        client = MeicaiAppGatewayClient(
            base_url=base_url,
            request_headers={str(key): str(value) for key, value in request_headers.items()},
            common_body=common_body,
        )
        city_id, area_id = apply_meicai_address_context(client, address_context)
        category_filters = load_probe_category_filters(sale_class_tree, limit_filters)

        endpoint_reports = []
        for endpoint_name in endpoints:
            endpoint_reports.append(
                probe_endpoint(
                    client=client,
                    endpoint_name=endpoint_name,
                    category_filters=category_filters,
                    max_pages=max_pages,
                    page_size=page_size,
                    city_id=city_id,
                    area_id=area_id,
                    sleep_seconds=sleep_seconds,
                )
            )

        return {
            "base_url": base_url,
            "city_id": city_id,
            "area_id": area_id,
            "category_filter_count": len(category_filters),
            "page_size": page_size,
            "max_pages": max_pages,
            "endpoints": endpoint_reports,
            "secret_env_file": str(secret_env_file),
        }
    finally:
        restore_meicai_env(original_env)


def snapshot_meicai_env() -> dict[str, str | None]:
    env_names = (
        "MEICAI_SECRET_ENV_FILE",
        "MEICAI_REQUEST_HEADERS",
        "MEICAI_COMMON_BODY",
        "MEICAI_ADDRESS_CONTEXT",
    )
    return {env_name: os.environ.get(env_name) for env_name in env_names}


def restore_meicai_env(original_env: dict[str, str | None]) -> None:
    for env_name, env_value in original_env.items():
        if env_value is None:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = env_value


def load_secret_env(secret_env_file: Path) -> None:
    if secret_env_file.exists():
        os.environ["MEICAI_SECRET_ENV_FILE"] = str(secret_env_file)
    PublicSourceCrawler._load_env_file_if_configured("MEICAI_SECRET_ENV_FILE")


def apply_meicai_address_context(
    client: MeicaiAppGatewayClient,
    address_context: dict[str, Any],
) -> tuple[str, str]:
    city_id = "17"
    area_id = "4402"
    address_body = address_context.get("request_body")
    if isinstance(address_body, dict):
        city_id = clean_text(address_body.get("city_id")) or city_id
        area_id = clean_text(address_body.get("area_id")) or area_id
        response_payload = client.change_address(address_body)
        if int(response_payload.get("ret") or response_payload.get("code") or 0) != 1:
            raise RuntimeError("美菜地址切换失败，请刷新 MEICAI_ADDRESS_CONTEXT 或登录态")
    return city_id, area_id


def load_probe_category_filters(sale_class_tree: Path | None, limit_filters: int) -> list[dict[str, str]]:
    if sale_class_tree and sale_class_tree.exists():
        category_filters = load_category_filters_from_sale_class_tree(sale_class_tree)
    else:
        category_filters = [{"category": "推荐商品", "class1_id": "-1", "class2_id": ""}]
    if limit_filters > 0:
        return category_filters[:limit_filters]
    return category_filters


def probe_endpoint(
    *,
    client: MeicaiAppGatewayClient,
    endpoint_name: str,
    category_filters: list[dict[str, str]],
    max_pages: int,
    page_size: int,
    city_id: str,
    area_id: str,
    sleep_seconds: float = 0.0,
) -> dict[str, Any]:
    if endpoint_name not in ENDPOINT_PATHS:
        raise RuntimeError(f"unsupported endpoint: {endpoint_name}")

    encrypted_count = 0
    response_count = 0
    row_count = 0
    top_level_keys: set[str] = set()
    payload_data_keys: set[str] = set()
    raw_row_keys: set[str] = set()
    goods_field_keys: set[str] = set()
    unique_goods_ids: set[str] = set()
    errors: list[str] = []

    for category_filter in category_filters:
        for page in range(1, max_pages + 1):
            try:
                payload = call_probe_endpoint(
                    client,
                    endpoint_name=endpoint_name,
                    page=page,
                    page_size=page_size,
                    city_id=city_id,
                    area_id=area_id,
                    class1_id=category_filter.get("class1_id") or "-1",
                    class2_id=category_filter.get("class2_id") or "",
                    sale_c1_id=category_filter.get("sale_c1_id") or category_filter.get("class1_id") or "-1",
                    sale_c2_id=category_filter.get("sale_c2_id") or category_filter.get("class2_id") or "",
                )
            except Exception as exc:  # noqa: BLE001 - probe keeps endpoint failures in the report.
                errors.append(f"{category_filter.get('category') or 'filter'} page={page}: {type(exc).__name__}")
                break
            response_count += 1
            if isinstance(payload, dict):
                top_level_keys.update(str(key) for key in payload.keys())
                payload_data = payload.get("data")
                if isinstance(payload_data, dict):
                    payload_data_keys.update(str(key) for key in payload_data.keys())
                    raw_rows = payload_data.get("rows")
                    if isinstance(raw_rows, list):
                        for raw_row in raw_rows[:3]:
                            if isinstance(raw_row, dict):
                                raw_row_keys.update(flatten_field_keys(raw_row, depth=2))
            if PublicSourceCrawler._meicai_payload_is_encrypted(payload):
                encrypted_count += 1
                break
            goods_rows = PublicSourceCrawler.extract_meicai_goods_rows(payload)
            row_count += len(goods_rows)
            for goods_row in goods_rows[:3]:
                goods_field_keys.update(flatten_field_keys(goods_row, depth=2))
            for goods_row in goods_rows:
                goods_identity = extract_goods_identity(goods_row)
                if goods_identity:
                    unique_goods_ids.add(goods_identity)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            if len(goods_rows) < page_size:
                break

    return {
        "endpoint": endpoint_name,
        "path": ENDPOINT_PATHS[endpoint_name],
        "responses": response_count,
        "encrypted_responses": encrypted_count,
        "plaintext": response_count > 0 and encrypted_count == 0,
        "row_count": row_count,
        "unique_goods_count": len(unique_goods_ids),
        "top_level_keys": sorted(top_level_keys),
        "data_keys": sorted(payload_data_keys),
        "raw_row_keys": sorted(raw_row_keys),
        "goods_field_keys": sorted(goods_field_keys),
        "errors": errors,
    }


def call_probe_endpoint(
    client: MeicaiAppGatewayClient,
    *,
    endpoint_name: str,
    page: int,
    page_size: int,
    city_id: str,
    area_id: str,
    class1_id: str,
    class2_id: str,
    sale_c1_id: str,
    sale_c2_id: str,
) -> dict[str, Any]:
    common_arguments = {
        "page": page,
        "page_size": page_size,
        "city_id": city_id,
        "area_id": area_id,
        "class1_id": class1_id,
        "class2_id": class2_id,
    }
    if endpoint_name in {"class_products", "get_spus_by_class"}:
        return client.class_products(
            page=page,
            page_size=page_size,
            city_id=city_id,
            area_id=area_id,
            sale_c1_id=sale_c1_id,
            sale_c2_id=sale_c2_id,
        )
    if endpoint_name == "xb_feed":
        return client.xb_feed(**common_arguments)
    if endpoint_name == "goods_info_location":
        return client.goods_info_location(**common_arguments)
    if endpoint_name == "smart_list_good_list":
        return client.smart_list_good_list(**common_arguments)
    if endpoint_name == "recommend_feed":
        return client.recommend_feed(**common_arguments)
    if endpoint_name == "goods_info_stream":
        return client.goods_info_stream(**common_arguments)
    if endpoint_name == "activity_polymerize_product":
        return client.activity_polymerize_product(**common_arguments)
    if endpoint_name == "commodity_goods_rank":
        return client.commodity_goods_rank(**common_arguments)
    if endpoint_name == "search_goods_list_by_data_id":
        return client.search_goods_list_by_data_id(**common_arguments)
    raise RuntimeError(f"unsupported endpoint: {endpoint_name}")


def flatten_field_keys(row: dict[str, Any], *, depth: int) -> set[str]:
    field_keys: set[str] = set()
    for key, value in row.items():
        clean_key = str(key)
        field_keys.add(clean_key)
        if depth > 1 and isinstance(value, dict):
            field_keys.update(f"{clean_key}.{nested_key}" for nested_key in flatten_field_keys(value, depth=depth - 1))
    return field_keys


def extract_goods_identity(goods_row: dict[str, Any]) -> str:
    sku_base = goods_row.get("skuBase") if isinstance(goods_row.get("skuBase"), dict) else {}
    return clean_text(
        sku_base.get("skuId")
        or sku_base.get("spuId")
        or goods_row.get("skuId")
        or goods_row.get("spuId")
    )


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def parse_endpoints(raw_value: str) -> list[str]:
    endpoint_names = [item.strip() for item in raw_value.split(",") if item.strip()]
    return endpoint_names or list(DEFAULT_ENDPOINTS)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe Meicai plaintext candidate endpoints and print redacted structure only."
    )
    parser.add_argument("--secret-env-file", default=str(DEFAULT_SECRET_ENV_FILE))
    parser.add_argument("--sale-class-tree", default=str(DEFAULT_SALE_CLASS_TREE))
    parser.add_argument("--endpoints", default=",".join(DEFAULT_ENDPOINTS))
    parser.add_argument("--limit-filters", type=int, default=3)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=MEICAI_DEFAULT_PAGE_SIZE)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--base-url", default="https://mall-entrance.yunshanmeicai.com")
    parsed_args = parser.parse_args()

    try:
        report = build_probe_report(
            secret_env_file=Path(parsed_args.secret_env_file),
            endpoints=parse_endpoints(parsed_args.endpoints),
            sale_class_tree=Path(parsed_args.sale_class_tree) if parsed_args.sale_class_tree else None,
            limit_filters=max(0, parsed_args.limit_filters),
            max_pages=max(1, parsed_args.max_pages),
            page_size=max(1, parsed_args.page_size),
            base_url=parsed_args.base_url,
            sleep_seconds=max(0.0, parsed_args.sleep_seconds),
        )
    except RuntimeError as exc:
        report = {"ready": False, "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
