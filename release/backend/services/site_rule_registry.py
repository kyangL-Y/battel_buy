from __future__ import annotations

import json
from pathlib import Path

from utils.config_loader import load_json_config, save_json_config


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_site_rule(rule: dict) -> dict:
    blocked_codes = rule.get("blocked_status_codes")
    if isinstance(blocked_codes, str):
        blocked_codes = [int(code.strip()) for code in blocked_codes.split(",") if code.strip().isdigit()]
    elif isinstance(blocked_codes, list):
        blocked_codes = [int(code) for code in blocked_codes if str(code).strip()]
    else:
        blocked_codes = None

    custom_headers = rule.get("custom_headers")
    if isinstance(custom_headers, str):
        try:
            parsed_headers = json.loads(custom_headers)
            custom_headers = parsed_headers if isinstance(parsed_headers, dict) else None
        except json.JSONDecodeError:
            custom_headers = None
    elif isinstance(custom_headers, dict):
        custom_headers = {
            str(key).strip(): str(value).strip()
            for key, value in custom_headers.items()
            if str(key).strip() and str(value).strip()
        }
    else:
        custom_headers = None

    playwright_wait_until = clean_optional_text(rule.get("playwright_wait_until"))
    if playwright_wait_until not in {None, "load", "domcontentloaded", "networkidle", "commit"}:
        playwright_wait_until = None

    normalized = {
        "site_name": clean_optional_text(rule.get("site_name")),
        "domains": [str(domain).strip() for domain in rule.get("domains", []) if str(domain).strip()],
        "currency": clean_optional_text(rule.get("currency")) or "CNY",
        "name_selectors": [str(sel).strip() for sel in rule.get("name_selectors", []) if str(sel).strip()],
        "price_selectors": [str(sel).strip() for sel in rule.get("price_selectors", []) if str(sel).strip()],
        "original_price_selectors": [str(sel).strip() for sel in rule.get("original_price_selectors", []) if str(sel).strip()],
        "promotion_selectors": [str(sel).strip() for sel in rule.get("promotion_selectors", []) if str(sel).strip()],
        "strategy": clean_optional_text(rule.get("strategy")) or "single",
        "fallback_strategy": clean_optional_text(rule.get("fallback_strategy")),
        "preferred_fetch_mode": clean_optional_text(rule.get("preferred_fetch_mode")),
        "api_strategy": clean_optional_text(rule.get("api_strategy")) or "off",
        "api_url": clean_optional_text(rule.get("api_url")),
        "api_method": clean_optional_text(rule.get("api_method")) or "GET",
        "api_headers": normalize_optional_json_object(rule.get("api_headers")),
        "api_body_template": normalize_optional_json_object(rule.get("api_body_template")),
        "api_field_mapping": normalize_optional_json_object(rule.get("api_field_mapping")),
        "batch_list_path": clean_optional_text(rule.get("batch_list_path")),
        "api_discovery_enabled": bool(rule.get("api_discovery_enabled", True)),
        "timeout_seconds": rule.get("timeout_seconds"),
        "retry_count": rule.get("retry_count"),
        "request_delay_seconds": rule.get("request_delay_seconds"),
        "blocked_status_codes": blocked_codes,
        "verify_ssl": bool(rule.get("verify_ssl", True)),
        "playwright_wait_until": playwright_wait_until,
        "custom_headers": custom_headers,
        "notes": clean_optional_text(rule.get("notes")),
    }
    for key in (
        "max_pages",
        "page_size",
        "max_varieties",
        "max_workers",
        "table_api_url",
        "base_url",
        "login_phone_env",
        "login_password_env",
        "chinaprice_query_mode",
        "chinaprice_menu_codes",
        "chinaprice_history_days",
        "chinaprice_city_tree_history_days",
        "chinaprice_max_queries",
        "chinaprice_max_pages_per_query",
        "chinaprice_max_rows",
    ):
        if key in rule and rule.get(key) not in (None, ""):
            normalized[key] = rule.get(key)
    return normalized


def load_site_rules(path: str | Path) -> list[dict]:
    config_path = Path(path)
    if not config_path.exists():
        return []
    rules = load_json_config(config_path)
    if not isinstance(rules, list):
        return []
    return [normalize_site_rule(rule) for rule in rules if isinstance(rule, dict)]


def save_site_rules(path: str | Path, rules: list[dict]) -> Path:
    normalized_rules = [normalize_site_rule(rule) for rule in rules]
    return save_json_config(path, normalized_rules)


def upsert_site_rule(path: str | Path, rule: dict) -> tuple[dict, bool]:
    normalized_rule = normalize_site_rule(rule)
    normalized_domains = {domain.lower() for domain in normalized_rule.get("domains", [])}
    rules = load_site_rules(path)

    for index, existing_rule in enumerate(rules):
        existing_domains = {domain.lower() for domain in existing_rule.get("domains", [])}
        if normalized_domains and _domains_overlap(existing_domains, normalized_domains):
            merged_rule = normalize_site_rule(
                {
                    **existing_rule,
                    **normalized_rule,
                    "domains": sorted(existing_domains.union(normalized_domains)),
                    "name_selectors": _merge_selector_lists(
                        existing_rule.get("name_selectors", []),
                        normalized_rule.get("name_selectors", []),
                    ),
                    "price_selectors": _merge_selector_lists(
                        existing_rule.get("price_selectors", []),
                        normalized_rule.get("price_selectors", []),
                    ),
                    "original_price_selectors": _merge_selector_lists(
                        existing_rule.get("original_price_selectors", []),
                        normalized_rule.get("original_price_selectors", []),
                    ),
                    "promotion_selectors": _merge_selector_lists(
                        existing_rule.get("promotion_selectors", []),
                        normalized_rule.get("promotion_selectors", []),
                    ),
                    "api_headers": normalized_rule.get("api_headers") or existing_rule.get("api_headers"),
                    "api_body_template": normalized_rule.get("api_body_template") or existing_rule.get("api_body_template"),
                    "api_field_mapping": normalized_rule.get("api_field_mapping") or existing_rule.get("api_field_mapping"),
                }
            )
            rules[index] = merged_rule
            save_site_rules(path, rules)
            return merged_rule, False

    rules.append(normalized_rule)
    save_site_rules(path, rules)
    return normalized_rule, True


def _merge_selector_lists(existing: list[str], incoming: list[str]) -> list[str]:
    merged: list[str] = []
    for selector in list(existing or []) + list(incoming or []):
        normalized = str(selector).strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def _domains_overlap(left: set[str], right: set[str]) -> bool:
    for left_domain in left:
        for right_domain in right:
            if (
                left_domain == right_domain
                or left_domain.endswith(f".{right_domain}")
                or right_domain.endswith(f".{left_domain}")
            ):
                return True
    return False


def normalize_optional_json_object(value):
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    if isinstance(value, dict):
        return value
    return None
