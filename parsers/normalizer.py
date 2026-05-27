from __future__ import annotations

import re
from typing import Any


SPEC_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>ml|l|g|kg|克|公斤|千克|斤)(?:\s*[*x×]\s*(?P<count>\d+))?", re.IGNORECASE)
CHINESE_NUMBER_PATTERN = re.compile(r"(?P<number>[零一二两三四五六七八九十百半]+)(?=(?:ml|l|g|kg|克|公斤|千克|斤))", re.IGNORECASE)
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
CHINESE_DIGIT_MAPPING = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
CHINESE_UNIT_MAPPING = {
    "十": 10,
    "百": 100,
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


def _parse_chinese_number(number_text: str) -> float | None:
    normalized = str(number_text or "").strip().replace("兩", "两")
    if not normalized:
        return None
    if normalized == "半":
        return 0.5
    if re.fullmatch(r"\d+(?:\.\d+)?", normalized):
        try:
            return float(normalized)
        except ValueError:
            return None
    if not all(char in CHINESE_DIGIT_MAPPING or char in CHINESE_UNIT_MAPPING for char in normalized):
        return None

    total = 0
    current_digit = 0
    for char in normalized:
        if char in CHINESE_DIGIT_MAPPING:
            current_digit = CHINESE_DIGIT_MAPPING[char]
            continue
        multiplier = CHINESE_UNIT_MAPPING[char]
        if current_digit == 0:
            current_digit = 1
        total += current_digit * multiplier
        current_digit = 0
    total += current_digit
    return float(total) if total > 0 else None


def _replace_chinese_number_with_arabic(match: re.Match[str]) -> str:
    raw_number = match.group("number")
    converted = _parse_chinese_number(raw_number)
    if converted is None:
        return raw_number
    return f"{converted:g}"


def _normalize_spec_quantity(spec_text: str) -> str:
    return CHINESE_NUMBER_PATTERN.sub(_replace_chinese_number_with_arabic, spec_text)


def _extract_weight_spec_from_product_name(product_name: str | None) -> str | None:
    normalized_name = normalize_spec_text(product_name)
    if normalized_name is None:
        return None
    quantity_normalized_name = _normalize_spec_quantity(normalized_name)
    matched_spec = SPEC_PATTERN.search(quantity_normalized_name)
    return matched_spec.group(0) if matched_spec else None


def parse_spec(spec_text: str | None) -> dict[str, float | str | None]:
    normalized = normalize_spec_text(spec_text)
    if normalized is None:
        return {"unit_name": None, "unit_value": None, "spec_text": None}

    cleaned = normalized
    if cleaned.startswith("元/"):
        cleaned = cleaned[2:]
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]
    cleaned = _normalize_spec_quantity(cleaned)

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


def resolve_effective_spec_text(spec_text: str | None, product_name: str | None) -> str | None:
    normalized_spec_text = normalize_spec_text(spec_text)
    inferred_product_spec = _extract_weight_spec_from_product_name(product_name)
    if normalized_spec_text is None:
        return inferred_product_spec

    parsed_spec = parse_spec(normalized_spec_text)
    if normalized_spec_text in DIRECT_UNIT_MAPPING and inferred_product_spec:
        inferred_spec_info = parse_spec(inferred_product_spec)
        if inferred_spec_info.get("unit_name") is not None and inferred_spec_info.get("unit_value") is not None:
            return inferred_product_spec

    if parsed_spec.get("unit_name") is None and inferred_product_spec:
        return inferred_product_spec
    return normalized_spec_text


def is_liancai_source(product: dict[str, Any]) -> bool:
    source_url = str(product.get("source_url") or product.get("url") or "").strip().lower()
    if "liancaiwang.cn" in source_url:
        return True
    for field_name in ("site_name", "source_name", "group_name"):
        field_value = str(product.get(field_name) or "").strip()
        if field_value.startswith("莲菜网") or field_value == "莲菜网":
            return True
    return False


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
    if is_liancai_source(product):
        effective_spec_text = normalize_spec_text(product.get("spec_text"))
    else:
        effective_spec_text = resolve_effective_spec_text(product.get("spec_text"), product_name)
    spec_info = parse_spec(effective_spec_text)
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
