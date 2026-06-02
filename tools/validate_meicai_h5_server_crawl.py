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
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from api.crawl_manager import build_crawler_service
from tools.check_meicai_server_readiness import (
    build_readiness_report,
    find_meicai_product,
    find_meicai_site_rule,
    load_json_file,
)
from utils.config_loader import load_runtime_config


DEFAULT_PRODUCTS_PATH = Path("config/products.json")
DEFAULT_SITES_PATH = Path("config/sites.json")
DEFAULT_RUNTIME_PATH = Path("config/runtime.json")
DEFAULT_PRODUCT_KEY = "meicai-h5-class-products"


def build_meicai_server_crawl_validation_report(
    *,
    products_path: Path,
    sites_path: Path,
    runtime_path: Path,
    secret_env_file: Path | None,
    product_key: str,
) -> dict[str, Any]:
    readiness_report = build_readiness_report(
        products_path=products_path,
        sites_path=sites_path,
        secret_env_file=secret_env_file,
    )
    if not readiness_report.get("ready"):
        return {
            "ready": False,
            "validated": False,
            "crawl_attempted": False,
            "readiness": readiness_report,
        }

    products_payload = load_json_file(products_path)
    site_rules_payload = load_json_file(sites_path)
    if not isinstance(products_payload, list):
        raise RuntimeError(f"{products_path} must contain a JSON array")
    if not isinstance(site_rules_payload, list):
        raise RuntimeError(f"{sites_path} must contain a JSON array")

    meicai_product = _select_meicai_product(products_payload, product_key)
    meicai_site_rule = find_meicai_site_rule(site_rules_payload)
    if not meicai_product:
        raise RuntimeError("missing meicai product config")
    if not meicai_site_rule:
        raise RuntimeError("missing meicai site rule")

    crawl_audit_path = _resolve_optional_path(meicai_site_rule.get("crawl_audit_path"))
    if crawl_audit_path is None:
        raise RuntimeError("meicai_h5_decrypt_batch site rule must set crawl_audit_path for full-crawl validation")

    runtime_settings = load_runtime_config(runtime_path)
    fetch_mode = str(runtime_settings.get("schedule", {}).get("fetch_mode") or "requests")
    crawler_service = build_crawler_service(fetch_mode, runtime_settings, site_rules_path=sites_path)

    database_before_count = crawler_service.database.get_price_record_count()
    crawl_rows = crawler_service.crawl_source(meicai_product)
    database_after_count = crawler_service.database.get_price_record_count()

    success_rows = [row for row in crawl_rows if str(row.get("status") or "") == "success"]
    failed_rows = [row for row in crawl_rows if str(row.get("status") or "") != "success"]
    audit_payload = _load_crawl_audit(crawl_audit_path)
    audit_summary = _summarize_crawl_audit(audit_payload)
    price_record_delta = database_after_count - database_before_count
    expected_category_count = int(readiness_report.get("sale_class_filter_count") or 0)
    validated = (
        bool(success_rows)
        and not failed_rows
        and price_record_delta == len(success_rows)
        and audit_summary["deduplicated_row_count"] == len(success_rows)
        and audit_summary["category_count"] == expected_category_count
        and audit_summary["hit_max_pages_count"] == 0
    )

    return {
        "ready": True,
        "validated": validated,
        "crawl_attempted": True,
        "product_key": meicai_product.get("product_key"),
        "strategy": readiness_report.get("strategy"),
        "database_label": getattr(crawler_service.database, "database_label", ""),
        "price_record_count_before": database_before_count,
        "price_record_count_after": database_after_count,
        "price_record_count_delta": price_record_delta,
        "crawl_result_count": len(crawl_rows),
        "crawl_success_count": len(success_rows),
        "crawl_failure_count": len(failed_rows),
        "crawl_failure_errors": _summarize_failure_errors(failed_rows),
        "expected_category_count": expected_category_count,
        "crawl_audit_path": str(crawl_audit_path),
        "crawl_audit": audit_summary,
        "readiness": readiness_report,
    }


def _select_meicai_product(products: list[dict[str, Any]], product_key: str) -> dict[str, Any] | None:
    normalized_product_key = str(product_key or "").strip()
    if normalized_product_key:
        for product in products:
            if str(product.get("product_key") or "").strip() == normalized_product_key:
                return product
    return find_meicai_product(products)


def _resolve_optional_path(value: Any) -> Path | None:
    path_text = str(value or "").strip()
    if not path_text:
        return None
    return Path(path_text).expanduser()


def _load_crawl_audit(crawl_audit_path: Path) -> dict[str, Any]:
    if not crawl_audit_path.exists():
        return {}
    audit_payload = json.loads(crawl_audit_path.read_text(encoding="utf-8-sig"))
    return audit_payload if isinstance(audit_payload, dict) else {}


def _summarize_crawl_audit(audit_payload: dict[str, Any]) -> dict[str, Any]:
    category_reports = audit_payload.get("category_reports") if isinstance(audit_payload, dict) else None
    category_report_count = len(category_reports) if isinstance(category_reports, list) else 0
    return {
        "present": bool(audit_payload),
        "category_count": int(audit_payload.get("category_count") or category_report_count or 0),
        "request_count": int(audit_payload.get("request_count") or 0),
        "raw_row_count": int(audit_payload.get("raw_row_count") or 0),
        "deduplicated_row_count": int(audit_payload.get("deduplicated_row_count") or 0),
        "hit_max_pages_count": int(audit_payload.get("hit_max_pages_count") or 0),
        "elapsed_seconds": audit_payload.get("elapsed_seconds"),
    }


def _summarize_failure_errors(failed_rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for row in failed_rows[:5]:
        error_text = str(row.get("error") or row.get("suggestion") or "").strip()
        if error_text:
            errors.append(error_text)
    return errors


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Validate Meicai H5 server-side full crawl and database writes without printing secret values."
    )
    argument_parser.add_argument("--products", default=str(DEFAULT_PRODUCTS_PATH))
    argument_parser.add_argument("--sites", default=str(DEFAULT_SITES_PATH))
    argument_parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME_PATH))
    argument_parser.add_argument("--product-key", default=DEFAULT_PRODUCT_KEY)
    argument_parser.add_argument("--secret-env-file", default=os.environ.get("MEICAI_SECRET_ENV_FILE"))
    parsed_args = argument_parser.parse_args()

    try:
        validation_report = build_meicai_server_crawl_validation_report(
            products_path=Path(parsed_args.products),
            sites_path=Path(parsed_args.sites),
            runtime_path=Path(parsed_args.runtime),
            secret_env_file=Path(parsed_args.secret_env_file) if parsed_args.secret_env_file else None,
            product_key=str(parsed_args.product_key or ""),
        )
    except RuntimeError as exc:
        validation_report = {
            "ready": False,
            "validated": False,
            "crawl_attempted": False,
            "error": str(exc),
        }
    print(json.dumps(validation_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
