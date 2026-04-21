from __future__ import annotations

from typing import Any


def is_source_enabled(item: dict[str, Any] | None) -> bool:
    if not isinstance(item, dict):
        return False
    value = item.get("enabled")
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "off", "no", ""}


def filter_enabled_sources(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and is_source_enabled(item)]


def get_source_name(item: dict[str, Any] | None, fallback: str = "") -> str:
    if not isinstance(item, dict):
        return fallback
    for key in ["source_name", "site_name", "product_name", "group_name", "url"]:
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return fallback
