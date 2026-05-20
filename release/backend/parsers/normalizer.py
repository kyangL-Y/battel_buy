from __future__ import annotations

import re
from typing import Any


SPEC_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>ml|l|g|kg|克|公斤|千克|斤)(?:\s*[*x×]\s*(?P<count>\d+))?", re.IGNORECASE)
UNIT_PRICE_BASE = {"ml": 100.0, "g": 100.0}
UNIT_MULTIPLIER = {
    "ml": ("ml", 1.0),
    "l": ("ml", 1000.0),
    "g": ("g", 1.0),
    "kg": ("g", 1000.0),
    "克": ("g", 1.0),
    "公斤": ("g", 1000.0),
    "千克": ("g", 1000.0),
    "斤": ("g", 500.0),
}
DIRECT_UNIT_MAPPING = {
    "公斤": ("g", 1000.0),
    "千克": ("g", 1000.0),
    "克": ("g", 1.0),
    "斤": ("g", 500.0),
    "kg": ("g", 1000.0),
    "g": ("g", 1.0),
    "ml": ("ml", 1.0),
    "l": ("ml", 1000.0),
}


def clean_price_text(value: str | None) -> str | None:
    if value is None:
        return None

    text = value.strip().replace(",", "")
    text = re.sub(r"[¥￥$€£\s]", "", text)
    if not text:
        return None

    if "-" in text:
        text = text.split("-")[0]

    match = re.search(r"\d+(?:\.\d+)?", text)
    return match.group(0) if match else None


def normalize_price(value: str | int | float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = clean_price_text(value)
    if cleaned is None:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_spec_text(spec_text: str | None) -> str | None:
    text = normalize_text(spec_text)
    if text is None:
        return None
    return text.lower().replace(" ", "")


def parse_spec(spec_text: str | None) -> dict[str, float | str | None]:
    normalized = normalize_spec_text(spec_text)
    if normalized is None:
        return {"unit_name": None, "unit_value": None, "spec_text": None}

    cleaned = normalized
    if cleaned.startswith("元/"):
        cleaned = cleaned[2:]
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]

    direct_unit = DIRECT_UNIT_MAPPING.get(cleaned)
    if direct_unit is not None:
        unit_name, unit_value = direct_unit
        return {"unit_name": unit_name, "unit_value": round(unit_value, 4), "spec_text": normalized}

    match = SPEC_PATTERN.search(cleaned)
    if not match:
        return {"unit_name": None, "unit_value": None, "spec_text": normalized}

    raw_value = float(match.group("value"))
    raw_unit = match.group("unit").lower()
    count = int(match.group("count") or 1)
    unit_name, multiplier = UNIT_MULTIPLIER[raw_unit]
    unit_value = raw_value * multiplier * count
    return {
        "unit_name": unit_name,
        "unit_value": round(unit_value, 4),
        "spec_text": normalized,
    }


def compute_unit_price(current_price: float | None, unit_name: str | None, unit_value: float | None) -> float | None:
    if current_price is None or unit_name is None or unit_value in (None, 0):
        return None
    base_value = UNIT_PRICE_BASE.get(unit_name)
    if base_value is None:
        return None
    return round(float(current_price) / float(unit_value) * base_value, 4)


def compute_jin_price(current_price: float | None, unit_name: str | None, unit_value: float | None) -> float | None:
    if current_price is None or unit_name != "g" or unit_value in (None, 0):
        return None
    return round(float(current_price) / float(unit_value) * 500, 4)


def compute_kg_price(current_price: float | None, unit_name: str | None, unit_value: float | None) -> float | None:
    if current_price is None or unit_name != "g" or unit_value in (None, 0):
        return None
    return round(float(current_price) / float(unit_value) * 1000, 4)


def format_price_unit_basis(spec_text: Any) -> str:
    text = normalize_text(spec_text)
    if text is None:
        return "原始报价"
    return f"元/{text}"


def build_compare_key(
    product_name: str | None,
    category: str | None,
    brand: str | None,
    product_series: str | None,
    spec_text: str | None,
) -> str | None:
    parts = [
        normalize_text(product_name),
        normalize_text(category),
        normalize_text(brand),
        normalize_text(product_series),
    ]
    if not any(parts):
        fallback_spec = normalize_spec_text(spec_text)
        return fallback_spec or None
    return "|".join(part or "未指定" for part in parts)


def normalize_product_metadata(product: dict[str, Any], current_price: float | None = None) -> dict[str, Any]:
    product_name = normalize_text(product.get("product_name"))
    category = normalize_text(product.get("category"))
    brand = normalize_text(product.get("brand"))
    product_series = normalize_text(product.get("product_series"))
    spec_info = parse_spec(product.get("spec_text"))
    compare_key = normalize_text(product.get("compare_key")) or build_compare_key(
        product_name,
        category,
        brand,
        product_series,
        spec_info.get("spec_text"),
    )
    unit_price = compute_unit_price(current_price, spec_info.get("unit_name"), spec_info.get("unit_value"))
    jin_price = compute_jin_price(current_price, spec_info.get("unit_name"), spec_info.get("unit_value"))
    kg_price = compute_kg_price(current_price, spec_info.get("unit_name"), spec_info.get("unit_value"))
    return {
        "category": category,
        "brand": brand,
        "product_series": product_series,
        "spec_text": spec_info.get("spec_text"),
        "compare_key": compare_key,
        "unit_name": spec_info.get("unit_name"),
        "unit_value": spec_info.get("unit_value"),
        "unit_price": unit_price,
        "jin_price": jin_price,
        "kg_price": kg_price,
    }
