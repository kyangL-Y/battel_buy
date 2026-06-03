from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_PRODUCTS_PATH = Path("config/products.json")
DEFAULT_SITES_PATH = Path("config/sites.json")
MEICAI_SUPPORTED_STRATEGIES = {"meicai_app_gateway_batch", "meicai_h5_decrypt_batch"}


def load_env_file_without_override(path: Path) -> list[str]:
    loaded_names: list[str] = []
    if not path.exists():
        return loaded_names
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        clean_name = name.strip()
        if not clean_name or clean_name in os.environ:
            continue
        os.environ[clean_name] = value.strip().strip("'").strip('"')
        loaded_names.append(clean_name)
    return loaded_names


def load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_meicai_product(products: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next(
        (
            product
            for product in products
            if product.get("strategy") in MEICAI_SUPPORTED_STRATEGIES
            or "yunshanmeicai.com" in str(product.get("url") or "")
        ),
        None,
    )


def find_meicai_site_rule(site_rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next(
        (
            rule
            for rule in site_rules
            if rule.get("strategy") in MEICAI_SUPPORTED_STRATEGIES
            or any("yunshanmeicai.com" in str(domain) for domain in rule.get("domains", []))
        ),
        None,
    )


def parse_json_env(name: str, *, required: bool) -> dict[str, Any]:
    raw_value = os.environ.get(name)
    if not raw_value:
        if required:
            raise RuntimeError(f"missing {name}")
        return {}
    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} is not valid JSON") from exc
    if not isinstance(parsed_value, dict):
        raise RuntimeError(f"{name} must be a JSON object")
    return parsed_value


def summarize_json_object(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "present": bool(value),
        "top_level_keys": sorted(str(key) for key in value.keys()),
    }


def summarize_meicai_current_address(path_text: str) -> dict[str, Any]:
    if not path_text:
        return {"present": False, "path": None}
    current_address_path = Path(path_text)
    if not current_address_path.exists():
        return {"present": False, "path": path_text}
    current_address_payload = load_json_file(current_address_path)
    if not isinstance(current_address_payload, dict):
        raise RuntimeError(f"{path_text} must contain a JSON object")
    address_text = " ".join(
        str(current_address_payload.get(field_name) or "")
        for field_name in ("poi_address", "address_detail", "address")
    )
    inferred_region = "上海市" if "上海" in address_text or "浦东" in address_text else None
    return {
        "present": True,
        "path": path_text,
        "has_location": bool(current_address_payload.get("locationTo") or current_address_payload.get("location_to")),
        "address_id_present": bool(current_address_payload.get("addressId")),
        "city_id_present": bool(str(current_address_payload.get("city_id") or "").strip()),
        "area_id_present": bool(str(current_address_payload.get("area_id") or "").strip()),
        "inferred_region": inferred_region,
    }


def build_readiness_report(
    *,
    products_path: Path,
    sites_path: Path,
    secret_env_file: Path | None,
) -> dict[str, Any]:
    loaded_env_names = load_env_file_without_override(secret_env_file) if secret_env_file else []
    products = load_json_file(products_path)
    site_rules = load_json_file(sites_path)
    if not isinstance(products, list):
        raise RuntimeError(f"{products_path} must contain a JSON array")
    if not isinstance(site_rules, list):
        raise RuntimeError(f"{sites_path} must contain a JSON array")

    meicai_product = find_meicai_product(products)
    meicai_site_rule = find_meicai_site_rule(site_rules)
    if not meicai_product:
        raise RuntimeError("missing meicai product config")
    if not meicai_site_rule:
        raise RuntimeError("missing meicai site rule")

    headers_env_name = str(meicai_site_rule.get("request_headers_env") or "MEICAI_REQUEST_HEADERS")
    common_body_env_name = str(meicai_site_rule.get("common_body_env") or "MEICAI_COMMON_BODY")
    address_context_env_name = str(meicai_site_rule.get("address_context_env") or "MEICAI_ADDRESS_CONTEXT")
    current_address_context_path = str(meicai_site_rule.get("current_address_context_path") or "").strip()
    request_headers = parse_json_env(headers_env_name, required=True)
    common_body = parse_json_env(common_body_env_name, required=True)
    address_context = parse_json_env(address_context_env_name, required=False)
    current_address_summary = summarize_meicai_current_address(current_address_context_path)

    category_filters = [
        {
            "category": str(item.get("category") or ""),
            "class1_id": str(item.get("class1_id") or ""),
            "class2_id": str(item.get("class2_id") or ""),
        }
        for item in meicai_site_rule.get("category_filters", [])
        if isinstance(item, dict)
    ]
    sale_class_tree_path = str(meicai_site_rule.get("sale_class_tree_path") or "").strip()
    h5_salts_path = str(meicai_site_rule.get("h5_salts_path") or "").strip()
    sale_class_filter_count = None
    if sale_class_tree_path:
        tree_payload = load_json_file(Path(sale_class_tree_path))
        flat_rows = tree_payload.get("flat") if isinstance(tree_payload, dict) else None
        if not isinstance(flat_rows, list):
            raise RuntimeError(f"{sale_class_tree_path} missing flat array")
        sale_class_filter_count = sum(
            1
            for item in flat_rows
            if isinstance(item, dict) and str(item.get("saleC1Id") or "").strip()
        )
    if meicai_site_rule.get("strategy") == "meicai_h5_decrypt_batch" and h5_salts_path:
        salts_payload = load_json_file(Path(h5_salts_path))
        if not isinstance(salts_payload, dict) or not salts_payload.get("saltsType3"):
            raise RuntimeError(f"{h5_salts_path} missing saltsType3")
    return {
        "ready": True,
        "product_enabled": bool(meicai_product.get("enabled", False)),
        "product_key": meicai_product.get("product_key"),
        "strategy": meicai_site_rule.get("strategy"),
        "gateway_base_url": meicai_site_rule.get("gateway_base_url"),
        "endpoint": meicai_site_rule.get("endpoint"),
        "city_id": str(meicai_site_rule.get("city_id") or ""),
        "area_id": str(meicai_site_rule.get("area_id") or ""),
        "page_size": meicai_site_rule.get("page_size"),
        "max_pages": meicai_site_rule.get("max_pages"),
        "sale_class_tree_path": sale_class_tree_path or None,
        "h5_salts_path": h5_salts_path or None,
        "current_address_context": current_address_summary,
        "request_source": meicai_site_rule.get("request_source"),
        "sale_class_filter_count": sale_class_filter_count,
        "category_filter_count": len(category_filters),
        "category_filters": category_filters,
        "env": {
            headers_env_name: summarize_json_object(request_headers),
            common_body_env_name: summarize_json_object(common_body),
            address_context_env_name: summarize_json_object(address_context),
        },
        "loaded_env_names": loaded_env_names,
        "secret_env_file": str(secret_env_file) if secret_env_file else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check Meicai server crawl readiness without printing secret values."
    )
    parser.add_argument("--products", default=str(DEFAULT_PRODUCTS_PATH))
    parser.add_argument("--sites", default=str(DEFAULT_SITES_PATH))
    parser.add_argument("--secret-env-file", default=os.environ.get("MEICAI_SECRET_ENV_FILE"))
    parsed_args = parser.parse_args()

    try:
        report = build_readiness_report(
            products_path=Path(parsed_args.products),
            sites_path=Path(parsed_args.sites),
            secret_env_file=Path(parsed_args.secret_env_file) if parsed_args.secret_env_file else None,
        )
    except RuntimeError as exc:
        report = {
            "ready": False,
            "error": str(exc),
            "secret_env_file": str(parsed_args.secret_env_file) if parsed_args.secret_env_file else None,
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
