from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from utils.config_loader import BASE_DIR, load_json_config
from utils.location_catalog import match_standard_city, match_standard_province


SOURCE_TIER_PRIORITY = {
    "主价格源": 0,
    "官方参考源": 1,
    "第三方参考源": 2,
    "本地市场源": 3,
}


def _collect_source_lookup_keys(values: list[Any]) -> set[str]:
    keys: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        keys.add(text)
        keys.add(text.lower())
        for separator in ("|", "｜"):
            if separator in text:
                prefix = text.split(separator, 1)[0].strip()
                if prefix:
                    keys.add(prefix)
                    keys.add(prefix.lower())
    return keys


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


def _normalize_scope_text(value: Any) -> str:
    return str(value or "").strip()


def _build_compound_scope_text(item: dict[str, Any]) -> str:
    return " ".join(
        text
        for text in [
            _normalize_scope_text(item.get("market_scope")),
            _normalize_scope_text(item.get("market_category")),
            _normalize_scope_text(item.get("source_name")),
            _normalize_scope_text(item.get("site_name")),
            _normalize_scope_text(item.get("product_name")),
            _normalize_scope_text(item.get("notes")),
            _normalize_scope_text(item.get("url")),
            _normalize_scope_text(item.get("source_url")),
        ]
        if text
    )


def _scope_is_nationwide(scope_text: str) -> bool:
    return "全国" in scope_text


def _infer_source_scope(item: dict[str, Any]) -> tuple[str | None, str | None, bool]:
    scope_text = _build_compound_scope_text(item)
    lower_scope = scope_text.lower()
    if _scope_is_nationwide(scope_text):
        return "全国", None, True

    matched_city, matched_city_province = match_standard_city(scope_text)
    matched_province = match_standard_province(scope_text) or matched_city_province

    if "liancaiwang.cn" in lower_scope or "莲菜网" in scope_text:
        return matched_province or "河南省", matched_city or "郑州", False
    if "wbncp.com" in lower_scope or "万邦" in scope_text:
        return matched_province or "河南省", matched_city or "郑州", False
    if "zzny" in lower_scope or "郑州" in scope_text:
        return matched_province or "河南省", matched_city or "郑州", False
    if "hnnhgsc" in lower_scope or "内黄" in scope_text:
        return matched_province or "河南省", matched_city or "安阳", False

    return matched_province, matched_city, False


def filter_sources_by_region(
    items: list[dict[str, Any]] | None,
    *,
    province: str | None = None,
    city: str | None = None,
    target_scope: str | None = None,
) -> list[dict[str, Any]]:
    enabled_items = filter_enabled_sources(items)
    normalized_scope = str(target_scope or "").strip().lower() or "all_saved"
    normalized_city, province_from_city = match_standard_city(city)
    normalized_province = match_standard_province(province) or province_from_city

    if normalized_scope == "all_saved" and not normalized_province and not normalized_city:
        return enabled_items

    filtered: list[dict[str, Any]] = []
    for item in enabled_items:
        source_province, source_city, is_nationwide = _infer_source_scope(item)
        if is_nationwide:
            filtered.append(item)
            continue
        if normalized_city:
            if source_city == normalized_city:
                filtered.append(item)
                continue
            if source_province and source_province == normalized_province and normalized_scope == "province":
                filtered.append(item)
                continue
        elif normalized_province:
            if source_province == normalized_province:
                filtered.append(item)
                continue
        elif normalized_scope == "all_saved":
            filtered.append(item)
    return filtered


def get_source_name(item: dict[str, Any] | None, fallback: str = "") -> str:
    if not isinstance(item, dict):
        return fallback
    for key in ["source_name", "site_name", "product_name", "group_name", "url"]:
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return fallback


def get_source_tier(item: dict[str, Any] | None, fallback: str = "") -> str:
    if not isinstance(item, dict):
        return fallback
    value = str(item.get("source_tier") or "").strip()
    return value or fallback


def normalize_source_tier(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def get_source_tier_rank(source_tier: str | dict[str, Any] | None, fallback: int | None = None) -> int:
    if isinstance(source_tier, dict):
        tier_text = get_source_tier(source_tier)
    else:
        tier_text = normalize_source_tier(source_tier)
    default_rank = len(SOURCE_TIER_PRIORITY) if fallback is None else int(fallback)
    return SOURCE_TIER_PRIORITY.get(tier_text, default_rank)


@lru_cache(maxsize=1)
def _load_source_tier_lookup(config_path: str) -> dict[str, str]:
    items = load_json_config(Path(config_path))
    lookup: dict[str, str] = {}
    if not isinstance(items, list):
        return lookup

    for item in items:
        if not isinstance(item, dict):
            continue
        source_tier = get_source_tier(item)
        if not source_tier:
            continue
        for key in _collect_source_lookup_keys(
            [
                item.get("url"),
                item.get("source_url"),
                item.get("source_name"),
                item.get("site_name"),
                item.get("product_name"),
                item.get("group_name"),
            ]
        ):
            if key:
                lookup.setdefault(key, source_tier)
    return lookup


def get_source_tier_lookup(config_path: Path | None = None) -> dict[str, str]:
    path = config_path or (BASE_DIR / "config" / "products.json")
    return _load_source_tier_lookup(str(path))


def resolve_source_tier(item: dict[str, Any] | None, fallback: str = "") -> str:
    if not isinstance(item, dict):
        return fallback

    source_tier = get_source_tier(item)
    if source_tier:
        return source_tier

    lookup = get_source_tier_lookup()
    for key in _collect_source_lookup_keys(
        [
            item.get("source_url"),
            item.get("url"),
            item.get("source_name"),
            item.get("site_name"),
            item.get("product_name"),
            item.get("group_name"),
            get_source_name(item),
        ]
    ):
        if key and key in lookup:
            return lookup[key]
    return fallback
