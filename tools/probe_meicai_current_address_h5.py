from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawler.public_source_crawlers import (  # noqa: E402
    MEICAI_DEFAULT_PAGE_SIZE,
    MeicaiH5DecryptingGatewayClient,
    PublicSourceCrawler,
)
from tools.extract_meicai_current_address import summarize_context  # noqa: E402
from tools.extract_meicai_category_candidates import load_category_filters_from_sale_class_tree  # noqa: E402
from tools.probe_meicai_plaintext_endpoints import load_secret_env  # noqa: E402


DEFAULT_SECRET_ENV_FILE = Path(".local-secrets/meicai_address_context.env")
DEFAULT_CURRENT_ADDRESS_PATH = Path(".local-secrets/meicai_current_address_context.json")
DEFAULT_SALE_CLASS_TREE = Path("tmp/meicai_sale_class_tree.json")
DEFAULT_H5_SALTS_FILE = Path("tmp/meicai_h5_salts.json")
DEFAULT_BASE_URL = "https://mall-entrance.yunshanmeicai.com"


def build_current_address_h5_report(
    *,
    secret_env_file: Path,
    current_address_path: Path,
    sale_class_tree: Path,
    h5_salts_file: Path,
    base_url: str,
    page_size: int,
) -> dict[str, Any]:
    load_secret_env(secret_env_file)
    request_headers = PublicSourceCrawler._load_json_env_object("MEICAI_REQUEST_HEADERS")
    common_body = PublicSourceCrawler._load_json_env_object("MEICAI_COMMON_BODY")
    legacy_address_context = PublicSourceCrawler._load_json_env_object("MEICAI_ADDRESS_CONTEXT")
    current_address_context = load_current_address_context(current_address_path)
    city_id, area_id, city_area_source = resolve_protocol_city_area(
        current_address_context=current_address_context,
        legacy_address_context=legacy_address_context,
    )
    location_text = require_context_text(current_address_context, "locationTo")

    h5_salts_payload = json.loads(h5_salts_file.read_text(encoding="utf-8-sig"))
    category_filter = load_category_filters_from_sale_class_tree(sale_class_tree)[0]
    adjusted_headers = build_current_address_headers(request_headers, city_id=city_id, area_id=area_id)
    adjusted_common_body = build_current_address_common_body(
        common_body,
        city_id=city_id,
        area_id=area_id,
        location_text=location_text,
    )

    client = MeicaiH5DecryptingGatewayClient(
        base_url=base_url,
        request_headers={str(header_name): str(header_value) for header_name, header_value in adjusted_headers.items()},
        common_body=adjusted_common_body,
        h5_salts_payload=h5_salts_payload,
        request_source=str(adjusted_common_body.get("_ENV_", {}).get("source") or "android"),
    )
    payload = client.class_products(
        page=1,
        page_size=page_size,
        city_id=city_id,
        area_id=area_id,
        sale_c1_id=str(category_filter.get("sale_c1_id") or category_filter.get("class1_id") or "-1"),
        sale_c2_id=str(category_filter.get("sale_c2_id") or category_filter.get("class2_id") or ""),
    )
    goods_rows = PublicSourceCrawler.extract_meicai_goods_rows(payload)
    payload_data = payload.get("data") if isinstance(payload, dict) else None
    data_keys = sorted(str(key) for key in payload_data.keys()) if isinstance(payload_data, dict) else []
    first_goods = goods_rows[0] if goods_rows else {}
    sku_base = first_goods.get("skuBase") if isinstance(first_goods.get("skuBase"), dict) else {}
    return {
        "success": bool(goods_rows),
        "city_id": city_id,
        "area_id": area_id,
        "city_area_source": city_area_source,
        "address_summary": summarize_context(current_address_context),
        "ret": payload.get("ret") if isinstance(payload, dict) else None,
        "code": payload.get("code") if isinstance(payload, dict) else None,
        "top_level_keys": sorted(str(key) for key in payload.keys()) if isinstance(payload, dict) else [],
        "data_keys": data_keys,
        "row_count": len(goods_rows),
        "first_goods": {
            "sku_id": str(sku_base.get("skuId") or first_goods.get("skuId") or ""),
            "spu_id": str(sku_base.get("spuId") or first_goods.get("spuId") or ""),
            "name_present": bool(sku_base.get("skuName") or first_goods.get("skuName")),
        },
    }


def load_current_address_context(current_address_path: Path) -> dict[str, Any]:
    if not current_address_path.exists():
        raise RuntimeError(f"当前地址上下文不存在: {current_address_path}")
    parsed_payload = json.loads(current_address_path.read_text(encoding="utf-8-sig"))
    if not isinstance(parsed_payload, dict):
        raise RuntimeError("当前地址上下文必须是 JSON object")
    return parsed_payload


def require_context_text(current_address_context: dict[str, Any], field_name: str) -> str:
    field_value = str(current_address_context.get(field_name) or "").strip()
    if not field_value:
        raise RuntimeError(f"当前地址上下文缺少 {field_name}")
    return field_value


def resolve_protocol_city_area(
    *,
    current_address_context: dict[str, Any],
    legacy_address_context: dict[str, Any],
) -> tuple[str, str, str]:
    current_city_id = str(current_address_context.get("city_id") or "").strip()
    current_area_id = str(current_address_context.get("area_id") or "").strip()
    if current_city_id and current_area_id:
        return current_city_id, current_area_id, "current_address"

    legacy_request_body = legacy_address_context.get("request_body")
    if isinstance(legacy_request_body, dict):
        legacy_city_id = str(legacy_request_body.get("city_id") or "").strip()
        legacy_area_id = str(legacy_request_body.get("area_id") or "").strip()
        if legacy_city_id and legacy_area_id:
            return legacy_city_id, legacy_area_id, "legacy_address_context"

    # 已验证 H5 商品流主要由 _ENV_.location 驱动；city/area 在这里作为接口协议占位。
    return "17", "4402", "site_default"


def build_current_address_headers(request_headers: dict[str, Any], *, city_id: str, area_id: str) -> dict[str, Any]:
    adjusted_headers = dict(request_headers)
    adjusted_headers["x-mc-city"] = city_id
    adjusted_headers["x-mc-area"] = area_id
    mc_gray = str(adjusted_headers.get("mc-gray") or "")
    if "cityId=" in mc_gray:
        mc_gray = replace_mc_gray_value(mc_gray, "cityId", city_id)
    if "saleArea=" in mc_gray:
        mc_gray = replace_mc_gray_value(mc_gray, "saleArea", area_id)
    if mc_gray:
        adjusted_headers["mc-gray"] = mc_gray
    return adjusted_headers


def replace_mc_gray_value(mc_gray: str, key_name: str, value_text: str) -> str:
    parts = []
    for part in mc_gray.split("_"):
        if part.startswith(f"{key_name}="):
            parts.append(f"{key_name}={value_text}")
        else:
            parts.append(part)
    return "_".join(parts)


def build_current_address_common_body(
    common_body: dict[str, Any],
    *,
    city_id: str,
    area_id: str,
    location_text: str,
) -> dict[str, Any]:
    adjusted_common_body = dict(common_body)
    env_payload = dict(adjusted_common_body.get("_ENV_") if isinstance(adjusted_common_body.get("_ENV_"), dict) else {})
    env_payload["city_id"] = city_id
    env_payload["area_id"] = area_id
    env_payload["location"] = location_text
    adjusted_common_body["_ENV_"] = env_payload
    return adjusted_common_body


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe Meicai H5 class products using current App address state without changeaddress."
    )
    parser.add_argument("--secret-env-file", default=os.environ.get("MEICAI_SECRET_ENV_FILE") or str(DEFAULT_SECRET_ENV_FILE))
    parser.add_argument("--current-address", default=str(DEFAULT_CURRENT_ADDRESS_PATH))
    parser.add_argument("--sale-class-tree", default=str(DEFAULT_SALE_CLASS_TREE))
    parser.add_argument("--h5-salts", default=str(DEFAULT_H5_SALTS_FILE))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--page-size", type=int, default=MEICAI_DEFAULT_PAGE_SIZE)
    parsed_arguments = parser.parse_args()

    try:
        probe_report = build_current_address_h5_report(
            secret_env_file=Path(parsed_arguments.secret_env_file),
            current_address_path=Path(parsed_arguments.current_address),
            sale_class_tree=Path(parsed_arguments.sale_class_tree),
            h5_salts_file=Path(parsed_arguments.h5_salts),
            base_url=str(parsed_arguments.base_url),
            page_size=max(1, parsed_arguments.page_size),
        )
    except RuntimeError as exc:
        probe_report = {"success": False, "error": str(exc)}
    print(json.dumps(probe_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
