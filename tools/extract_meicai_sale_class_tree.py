from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawler.public_source_crawlers import MeicaiAppGatewayClient, PublicSourceCrawler
from services.meicai_category_mapping import suggest_meicai_internal_category


DEFAULT_OUTPUT_PATH = Path("tmp/meicai_sale_class_tree.json")
DEFAULT_SECRET_ENV_FILE = Path(".local-secrets/meicai_address_context.env")
SALE_CLASS_ENDPOINT = "/entrance/dishes/saleClass"
ENCRYPTED_CLASS_PRODUCTS_ENDPOINT = "/entrance/dishes/getSpusByClass"
SALE_CLASS_COVERAGE_SCOPE = "navigation_category_tree_only"
SALE_CLASS_EXCLUSION_REASON = "getSpusByClass data is encrypted and is not decoded by this plaintext chain"


def fetch_meicai_sale_class_tree(
    *,
    secret_env_file: Path,
    base_url: str = "https://mall-entrance.yunshanmeicai.com",
    city_id: str = "17",
    area_id: str = "4402",
) -> dict[str, Any]:
    if secret_env_file.exists():
        _load_secret_env_file(secret_env_file)
    request_headers = PublicSourceCrawler._load_json_env_object("MEICAI_REQUEST_HEADERS")
    common_body = PublicSourceCrawler._load_json_env_object("MEICAI_COMMON_BODY")
    address_context = PublicSourceCrawler._load_json_env_object("MEICAI_ADDRESS_CONTEXT")
    configured_address_body = address_context.get("request_body")
    if isinstance(configured_address_body, dict):
        city_id = _clean_text(configured_address_body.get("city_id")) or city_id
        area_id = _clean_text(configured_address_body.get("area_id")) or area_id

    client = MeicaiAppGatewayClient(
        base_url=base_url,
        request_headers={str(key): str(value) for key, value in request_headers.items()},
        common_body=common_body,
    )
    if isinstance(configured_address_body, dict):
        change_address_payload = client.change_address(configured_address_body)
        if int(change_address_payload.get("ret") or change_address_payload.get("code") or 0) != 1:
            raise RuntimeError("美菜地址切换失败，请刷新 MEICAI_ADDRESS_CONTEXT 或登录态")

    root_payload = client.sale_class(parent_id="0", city_id=city_id, area_id=area_id)
    root_items = extract_sale_class_items(root_payload)
    tree_items: list[dict[str, Any]] = []
    for root_item in root_items:
        root_id = _clean_text(root_item.get("id"))
        child_payload = client.sale_class(parent_id=root_id, city_id=city_id, area_id=area_id)
        child_items = extract_sale_class_items(child_payload)
        tree_items.append(
            {
                **normalize_sale_class_item(root_item),
                "children": [normalize_sale_class_item(child_item) for child_item in child_items],
            }
        )
    return {
        "source_endpoint": SALE_CLASS_ENDPOINT,
        "coverage": SALE_CLASS_COVERAGE_SCOPE,
        "excluded_endpoint": ENCRYPTED_CLASS_PRODUCTS_ENDPOINT,
        "exclusion_reason": SALE_CLASS_EXCLUSION_REASON,
        "city_id": city_id,
        "area_id": area_id,
        "root_count": len(tree_items),
        "leaf_count": sum(len(item["children"]) for item in tree_items),
        "tree": tree_items,
        "flat": flatten_sale_class_tree(tree_items),
    }


def extract_sale_class_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if PublicSourceCrawler._meicai_payload_is_encrypted(payload):
        raise RuntimeError("美菜 saleClass 返回加密 data，按约定不转 OCR")
    data = payload.get("data") if isinstance(payload, dict) else None
    rows = data.get("list") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def normalize_sale_class_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _clean_text(item.get("id")),
        "name": _clean_text(item.get("name")),
        "parent_id": _clean_text(item.get("parent_id")),
        "sortNum": item.get("sortNum"),
        "ids": item.get("ids"),
        "nameImg": _clean_text(item.get("nameImg")) or None,
    }


def flatten_sale_class_tree(tree_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat_rows: list[dict[str, Any]] = []
    for root_item in tree_items:
        root_id = _clean_text(root_item.get("id"))
        root_name = _clean_text(root_item.get("name"))
        children = root_item.get("children")
        if not isinstance(children, list) or not children:
            mapping = suggest_meicai_internal_category({"saleC1Id": root_id, "biName": root_name})
            flat_rows.append(_flat_row(root_id, root_name, "", "", mapping))
            continue
        for child_item in children:
            child_id = _clean_text(child_item.get("id"))
            child_name = _clean_text(child_item.get("name"))
            mapping = suggest_meicai_internal_category(
                {
                    "saleC1Id": root_id,
                    "saleC2Id": child_id,
                    "saleC1Name": root_name,
                    "saleC2Name": child_name,
                    "biName": child_name,
                }
            )
            flat_rows.append(_flat_row(root_id, root_name, child_id, child_name, mapping))
    return flat_rows


def write_sale_class_tree(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _flat_row(root_id: str, root_name: str, child_id: str, child_name: str, mapping: Any) -> dict[str, Any]:
    return {
        "saleC1Id": root_id or None,
        "saleC1Name": root_name or None,
        "saleC2Id": child_id or None,
        "saleC2Name": child_name or None,
        "internalCategory": mapping.category,
        "internalMarketCategory": mapping.market_category,
        "liancaiTopCategory": mapping.liancai_top_category,
        "liancaiSubcategory": mapping.liancai_subcategory,
        "mappingSource": mapping.source,
        "mappingConfidence": mapping.confidence,
    }


def _load_secret_env_file(secret_env_file: Path) -> None:
    import os

    previous_value = os.environ.get("MEICAI_SECRET_ENV_FILE")
    os.environ["MEICAI_SECRET_ENV_FILE"] = str(secret_env_file)
    PublicSourceCrawler._load_env_file_if_configured("MEICAI_SECRET_ENV_FILE")
    if previous_value is None:
        os.environ.pop("MEICAI_SECRET_ENV_FILE", None)
    else:
        os.environ["MEICAI_SECRET_ENV_FILE"] = previous_value


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description=(
            "Extract Meicai saleClass navigation category tree only; "
            "does not decode getSpusByClass encrypted product lists."
        )
    )
    argument_parser.add_argument("--output", "-o", default=str(DEFAULT_OUTPUT_PATH))
    argument_parser.add_argument("--secret-env-file", default=str(DEFAULT_SECRET_ENV_FILE))
    argument_parser.add_argument("--base-url", default="https://mall-entrance.yunshanmeicai.com")
    parsed_arguments = argument_parser.parse_args()

    tree_payload = fetch_meicai_sale_class_tree(
        secret_env_file=Path(parsed_arguments.secret_env_file),
        base_url=parsed_arguments.base_url,
    )
    output_path = Path(parsed_arguments.output)
    write_sale_class_tree(tree_payload, output_path)
    print(
        "wrote Meicai saleClass tree to {output} roots={roots} leaves={leaves}".format(
            output=output_path,
            roots=tree_payload["root_count"],
            leaves=tree_payload["leaf_count"],
        )
    )


if __name__ == "__main__":
    main()
