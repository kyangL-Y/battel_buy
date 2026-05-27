from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from parsers.normalizer import compute_kg_price, parse_spec
from services.ai_extractor import AIExtractorError, call_qwen_chat_completion_text, get_ai_config, get_api_key, is_ai_extraction_enabled
from utils.config_loader import BASE_DIR
from utils.location_catalog import match_standard_city, match_standard_province
from utils.source_config import get_source_tier_rank, resolve_source_tier


MENU_LINE_PATTERN = re.compile(r"^\s*(?:\d+[.、)\-]\s*)?(?P<name>.+?)\s*$")
MENU_STOPWORDS = (
    "清蒸",
    "红烧",
    "蒜蓉",
    "蒜香",
    "香辣",
    "麻辣",
    "干锅",
    "水煮",
    "麻婆",
    "宫保",
    "鱼香",
    "椒盐",
    "爆炒",
    "小炒",
    "酸辣",
    "葱爆",
    "白灼",
    "油焖",
    "炖",
    "煲",
    "焗",
    "烧",
    "煮",
    "炒",
    "煎",
    "炸",
    "焖",
    "炝",
    "溜",
    "烩",
    "拌",
    "卤",
    "酱",
    "汤",
    "羹",
)
MENU_ACTION_WORDS = (
    "炒",
    "炖",
    "烧",
    "煲",
    "焖",
    "蒸",
    "拌",
    "烩",
    "煎",
    "炸",
    "煮",
    "卤",
    "焗",
    "炝",
    "溜",
)
MENU_SYNONYMS = {
    "猪排骨": ["排骨", "猪肋排", "肋排", "猪小排"],
    "牛腩": ["牛杂", "牛肉"],
    "西兰花": ["兰花菜", "绿花菜"],
    "鲈鱼": ["桂花鱼", "清蒸鲈鱼"],
    "土豆": ["马铃薯", "洋芋"],
    "白菜": ["大白菜", "娃娃菜"],
}
MENU_HEURISTIC_RECIPES = {
    "地三鲜": ["土豆", "茄子", "青椒"],
    "佛跳墙": ["鲍鱼", "海参", "花胶", "瑶柱"],
    "宫保鸡丁": ["鸡丁", "花生米", "黄瓜"],
    "番茄炒蛋": ["番茄", "鸡蛋"],
    "西红柿炒鸡蛋": ["番茄", "鸡蛋"],
}
MENU_TOKEN_NORMALIZERS = {
    "蛋": "鸡蛋",
    "鸡蛋": "鸡蛋",
    "西红柿": "番茄",
}
MENU_AI_LOG_PATH = BASE_DIR / "logs" / "menu_ai_history.jsonl"
MENU_LOCATION_ALIASES = {
    "当前位置": "当前位置",
    "附近": "当前位置",
    "本地": "当前位置",
    "就近": "当前位置",
}
INGREDIENT_FAMILY_KEYWORDS = {
    "vegetable": [
        "菜",
        "蔬",
        "菌",
        "豆",
        "瓜",
        "椒",
        "茄",
        "芹",
        "葱",
        "姜",
        "蒜",
        "薯",
        "萝卜",
        "白菜",
        "菠菜",
        "生菜",
        "花菜",
        "西兰花",
        "黄瓜",
        "番茄",
        "西红柿",
        "香菇",
        "金针菇",
        "土豆",
        "莲藕",
        "山药",
    ],
    "aquatic": [
        "鱼",
        "虾",
        "蟹",
        "贝",
        "蛏",
        "蛤",
        "鲍",
        "鳝",
        "鳗",
        "螺",
        "海参",
        "海鲜",
        "水产",
        "海产",
        "小黄鱼",
        "鲈鱼",
        "带鱼",
    ],
    "meat": [
        "肉",
        "猪",
        "牛",
        "羊",
        "鸡",
        "鸭",
        "鹅",
        "排骨",
        "牛腩",
        "牛肉",
        "猪排骨",
        "里脊",
        "五花",
        "腊肉",
        "肘子",
        "禽",
        "蛋",
    ],
}
INGREDIENT_PROCESSING_PROFILES = [
    {
        "keywords": ("牛肉", "牛腩", "牛腱", "牛里脊", "牛排"),
        "edible_yield_ratio": 0.9,
        "cooking_yield_ratio": 0.78,
        "profile_label": "牛肉修切+炖煮损耗",
    },
    {
        "keywords": ("黄瓜", "青瓜"),
        "edible_yield_ratio": 0.86,
        "cooking_yield_ratio": 1.0,
        "profile_label": "黄瓜去皮损耗",
    },
    {
        "keywords": ("土豆", "马铃薯", "洋芋"),
        "edible_yield_ratio": 0.84,
        "cooking_yield_ratio": 1.0,
        "profile_label": "块茎去皮损耗",
    },
]
MENU_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "menu_name": {"type": "string"},
                    "ingredient_name": {"type": ["string", "null"]},
                    "remarks": {"type": ["string", "null"]},
                },
                "required": ["menu_name", "ingredient_name", "remarks"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


def parse_menu_text(menu_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in str(menu_text or "").splitlines():
        match = MENU_LINE_PATTERN.match(raw_line.strip())
        if not match:
            continue
        name = match.group("name").strip()
        if not name:
            continue
        rows.append({"menu_name": name, "remarks": None})
    return rows


def parse_menu_dataframe(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    rows: list[dict[str, Any]] = []
    candidate_columns = [column for column in df.columns if str(column).strip()]
    for _, row in df.iterrows():
        values = [str(row.get(column)).strip() for column in candidate_columns if pd.notna(row.get(column)) and str(row.get(column)).strip()]
        if not values:
            continue
        rows.append({"menu_name": values[0], "remarks": " | ".join(values[1:]) or None})
    return rows


def _normalize_name(text: Any) -> str:
    normalized = str(text or "").strip().lower()
    normalized = re.sub(r"[\s\-_·•|/]+", "", normalized)
    return re.sub(r"[^\u4e00-\u9fa5a-z0-9]+", "", normalized)


def _safe_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _extract_core_keyword(text: Any) -> str:
    normalized = str(text or "").strip()
    if not normalized:
        return ""
    cleaned = normalized
    for stopword in MENU_STOPWORDS:
        cleaned = cleaned.replace(stopword, "")
    cleaned = re.sub(r"[（(].*?[)）]", "", cleaned)
    cleaned = cleaned.strip()
    return cleaned or normalized


def _normalize_menu_ai_ingredient(menu_name: Any, ingredient_name: Any) -> str:
    menu_text = str(menu_name or "").strip()
    ingredient_text = str(ingredient_name or "").strip()
    if not ingredient_text:
        ingredient_text = menu_text
    if not ingredient_text:
        return ""

    normalized_menu = _normalize_name(menu_text)
    normalized_ingredient = _normalize_name(ingredient_text)
    core_menu_text = _extract_core_keyword(menu_text)
    core_ingredient_text = _extract_core_keyword(ingredient_text)

    # If the model echoes the original dish name, fall back to the core ingredient phrase.
    if normalized_menu and normalized_ingredient == normalized_menu and core_menu_text:
        normalized_core_menu = _normalize_name(core_menu_text)
        if normalized_core_menu and normalized_core_menu != normalized_menu:
            return core_menu_text

    # Remove obvious cooking-method wrappers around the returned ingredient text as well.
    if core_ingredient_text:
        normalized_core_ingredient = _normalize_name(core_ingredient_text)
        if normalized_core_ingredient and normalized_core_ingredient != normalized_ingredient:
            return core_ingredient_text

    return ingredient_text


def _extract_json_fragment(content: str) -> str:
    text = str(content or "").strip()
    if not text:
        return ""
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()

    start_positions = [index for index in [text.find("{"), text.find("[")] if index >= 0]
    if not start_positions:
        return text
    start_index = min(start_positions)
    opening = text[start_index]
    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    escape = False
    for index in range(start_index, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1].strip()
    return text


def _parse_menu_ai_payload(content: str) -> Any:
    json_fragment = _extract_json_fragment(content)
    try:
        return json.loads(json_fragment)
    except json.JSONDecodeError as exc:
        raise AIExtractorError(f"菜单 AI 返回 JSON 解析失败：{exc}") from exc


def _normalize_ingredient_token(token: Any) -> str:
    text = str(token or "").strip()
    if not text:
        return ""
    return MENU_TOKEN_NORMALIZERS.get(text, text)


def _join_ingredient_names(items: list[str]) -> str:
    deduped: list[str] = []
    for item in items:
        normalized_item = _normalize_ingredient_token(item)
        if normalized_item and normalized_item not in deduped:
            deduped.append(normalized_item)
    return "、".join(deduped)


def _extract_action_based_ingredients(menu_name: str) -> list[str]:
    text = str(menu_name or "").strip()
    for action_word in MENU_ACTION_WORDS:
        if action_word not in text:
            continue
        left, right = text.split(action_word, 1)
        left = _extract_core_keyword(left)
        right = _extract_core_keyword(right)
        candidates = [item for item in [_normalize_ingredient_token(left), _normalize_ingredient_token(right)] if item]
        if len(candidates) >= 2:
            return candidates
    return []


def _infer_ingredient_name_from_menu(menu_name: Any) -> str:
    menu_text = str(menu_name or "").strip()
    if not menu_text:
        return ""

    exact_match = MENU_HEURISTIC_RECIPES.get(menu_text)
    if exact_match:
        return _join_ingredient_names(exact_match)

    action_based_items = _extract_action_based_ingredients(menu_text)
    if action_based_items:
        return _join_ingredient_names(action_based_items)

    core_keyword = _normalize_ingredient_token(_extract_core_keyword(menu_text))
    return core_keyword or menu_text


def _fallback_enrich_menu_items(menu_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched_rows: list[dict[str, Any]] = []
    for row in menu_items:
        menu_name = str(row.get("menu_name") or "").strip()
        enriched_rows.append(
            {
                **row,
                "ingredient_name": _infer_ingredient_name_from_menu(menu_name),
                "remarks": row.get("remarks") or "AI 失败，已使用本地启发式拆分",
            }
        )
    return enriched_rows


def _build_menu_alias_keys(menu_name: str, ingredient_name: str) -> list[str]:
    candidates: list[str] = []
    for text in [ingredient_name, _extract_core_keyword(ingredient_name), menu_name, _extract_core_keyword(menu_name)]:
        normalized = _normalize_name(text)
        if normalized:
            candidates.append(normalized)
    for canonical_name, aliases in MENU_SYNONYMS.items():
        normalized_canonical = _normalize_name(canonical_name)
        alias_keys = {_normalize_name(alias) for alias in aliases}
        if any(key in alias_keys or key == normalized_canonical for key in candidates):
            candidates.append(normalized_canonical)
            candidates.extend(alias_keys)
    deduped: list[str] = []
    for item in candidates:
        if "冷冻" in item:
            candidates.append(item.replace("冷冻", "冻"))
        if "速冻" in item:
            candidates.append(item.replace("速冻", "冻"))
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def _normalize_recipe_ratios(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid_items = [
        {
            "ingredient_name": str(item.get("ingredient_name") or "").strip(),
            "ratio": float(item.get("ratio") or 0),
        }
        for item in items
        if str(item.get("ingredient_name") or "").strip()
    ]
    total_ratio = sum(max(item["ratio"], 0) for item in valid_items)
    if not valid_items:
        return []
    if total_ratio <= 0:
        equal_ratio = round(1 / len(valid_items), 4)
        return [{"ingredient_name": item["ingredient_name"], "ratio": equal_ratio} for item in valid_items]
    return [
        {
            "ingredient_name": item["ingredient_name"],
            "ratio": round(max(item["ratio"], 0) / total_ratio, 4),
        }
        for item in valid_items
    ]


def _split_ingredient_text(ingredient_name: str) -> list[str]:
    text = str(ingredient_name or "").strip()
    if not text:
        return []
    if not re.search(r"[、,，/＋+]", text):
        return []
    return [segment.strip() for segment in re.split(r"[、,，/＋+]", text) if segment.strip()]


def _resolve_menu_ingredients(menu_name: str, ingredient_name: str) -> list[dict[str, Any]]:
    split_items = _split_ingredient_text(ingredient_name)
    if len(split_items) > 1:
        return _normalize_recipe_ratios(
            [{"ingredient_name": item, "ratio": 1} for item in split_items]
        )

    canonical_name = str(ingredient_name or menu_name).strip()
    if not canonical_name:
        return []
    return [{"ingredient_name": canonical_name, "ratio": 1.0}]


def _expand_menu_items(menu_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded_rows: list[dict[str, Any]] = []
    for row in menu_items:
        menu_name = str(row.get("menu_name") or "").strip()
        ingredient_name = str(row.get("ingredient_name") or menu_name).strip()
        resolved_items = _resolve_menu_ingredients(menu_name, ingredient_name)
        for item in resolved_items:
            expanded_rows.append(
                {
                    **row,
                    "menu_name": menu_name,
                    "ingredient_name": item["ingredient_name"],
                    "ingredient_ratio": item["ratio"],
                }
            )
    return expanded_rows


def _write_menu_ai_log(record: dict[str, Any]) -> None:
    try:
        MENU_AI_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with MENU_AI_LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        return


def _normalize_location_preference(preferred_location: str | None) -> tuple[str | None, str | None]:
    text = str(preferred_location or "").strip()
    if not text:
        return None, None
    alias_text = MENU_LOCATION_ALIASES.get(text, text)
    city_name, province_from_city = match_standard_city(alias_text)
    if city_name:
        return province_from_city, city_name
    province_name = match_standard_province(alias_text)
    return province_name, None


def _build_location_rank(
    row: pd.Series,
    preferred_province: str | None,
    preferred_city: str | None,
    preferred_location: str | None,
) -> tuple[int, int, int]:
    row_city = _safe_text(row.get("city"))
    row_province = _safe_text(row.get("province"))
    preferred_location_province, preferred_location_city = _normalize_location_preference(preferred_location)

    if preferred_city and row_city and row_city == preferred_city:
        return (0, 0, 0)
    if preferred_location_city and row_city and row_city == preferred_location_city:
        return (0, 1, 0)
    if preferred_province and row_province and row_province == preferred_province:
        return (1, 0, 0)
    if preferred_location_province and row_province and row_province == preferred_location_province:
        return (1, 1, 0)
    if row_city or row_province:
        return (2, 0, 0)
    return (3, 0, 0)


def _infer_ingredient_family(ingredient_name: str, category_hint: Any = None) -> str:
    text = " ".join([str(ingredient_name or ""), str(category_hint or "")]).strip()
    for family, keywords in INGREDIENT_FAMILY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return family
    return "generic"


def _infer_source_kind(row: pd.Series) -> str:
    joined_text = " ".join(
        [
            _safe_text(row.get("site_name")),
            _safe_text(row.get("market_name")),
            _safe_text(row.get("category")),
            _safe_text(row.get("group_name")),
        ]
    )
    if "PFSC" in joined_text:
        return "pfsc"
    if "万邦" in joined_text or "wbncp" in joined_text.lower():
        return "wanbang"
    if "Chinaprice" in joined_text or "chinaprice" in joined_text.lower():
        return "chinaprice"
    return "other"


def _build_market_context_text(row: pd.Series) -> str:
    return " ".join(
        [
            _safe_text(row.get("product_name")),
            _safe_text(row.get("group_name")),
            _safe_text(row.get("category")),
            _safe_text(row.get("site_name")),
            _safe_text(row.get("market_name")),
        ]
    )


def _build_ingredient_match_rank(row: pd.Series, normalized_candidates: list[str]) -> int:
    market_key = _normalize_name(_build_market_context_text(row))
    product_key = _normalize_name(_safe_text(row.get("product_name")))
    group_key = _normalize_name(_safe_text(row.get("group_name")))

    if any(candidate and candidate == product_key for candidate in normalized_candidates):
        return 0
    if any(candidate and candidate == group_key for candidate in normalized_candidates):
        return 1
    if any(candidate and candidate in market_key for candidate in normalized_candidates):
        return 2
    return 3


def _has_effective_location(row: pd.Series) -> bool:
    row_city = _safe_text(row.get("city"))
    row_province = _safe_text(row.get("province"))
    return any(value and value != "全国" for value in [row_city, row_province])


def _resolve_source_tier_label(row: pd.Series | None) -> str | None:
    if row is None:
        return None
    source_tier = resolve_source_tier(row.to_dict())
    return source_tier or None


def _build_source_priority(row: pd.Series, ingredient_family: str) -> tuple[int, int, int]:
    source_kind = _infer_source_kind(row)
    market_text = _build_market_context_text(row)
    has_effective_location = _has_effective_location(row)
    source_tier_rank = get_source_tier_rank(_resolve_source_tier_label(row), fallback=99)
    has_vegetable_context = any(keyword in market_text for keyword in ["蔬菜", "果蔬", "菜篮子", "农产品"])
    has_aquatic_context = any(keyword in market_text for keyword in ["水产", "海鲜", "渔", "海产品"])
    has_meat_context = any(keyword in market_text for keyword in ["肉", "禽", "蛋", "畜", "家畜", "牛", "羊", "猪", "排骨", "肋排"])
    is_general_reference = any(keyword in market_text for keyword in ["总平均价", "全国-省", "全国蔬菜平均价", "全国水产平均价"])
    is_market_retail_reference = any(keyword in market_text for keyword in ["集市", "超市"])
    is_produce_focused_market = any(keyword in market_text for keyword in ["蔬菜", "果蔬", "芽、花类", "叶菜类", "根和根茎类", "瓜果类", "食用菌"])

    if ingredient_family == "vegetable":
        if source_kind == "pfsc" and has_vegetable_context:
            return (0, 0, source_tier_rank)
        if source_kind == "wanbang" and has_vegetable_context:
            return (1, 0, source_tier_rank)
        if source_kind == "pfsc":
            return (1, 1, source_tier_rank)
        if source_kind == "wanbang":
            return (2, 0, source_tier_rank)
        if source_kind == "other":
            return (3, 0, source_tier_rank)
        return (5, 0, source_tier_rank)

    if ingredient_family == "aquatic":
        if source_kind == "pfsc" and has_aquatic_context:
            return (0, 0, source_tier_rank)
        if source_kind == "wanbang" and has_aquatic_context:
            return (1, 0, source_tier_rank)
        if source_kind == "pfsc":
            return (1, 1, source_tier_rank)
        if source_kind == "wanbang":
            return (2, 0, source_tier_rank)
        if source_kind == "other":
            return (3, 0, source_tier_rank)
        return (5, 0, source_tier_rank)

    if ingredient_family == "meat":
        if source_kind == "wanbang" and has_meat_context:
            return (0, 0, source_tier_rank)
        if source_kind == "pfsc" and has_meat_context and has_effective_location and not is_produce_focused_market:
            return (1, 0, source_tier_rank)
        if source_kind == "chinaprice" and has_meat_context and has_effective_location and is_market_retail_reference:
            return (2, 0, source_tier_rank)
        if source_kind == "other" and has_meat_context and has_effective_location:
            return (2, 1, source_tier_rank)
        if source_kind == "chinaprice" and has_meat_context and not is_general_reference:
            return (3, 0, source_tier_rank)
        if source_kind == "pfsc" and has_meat_context and not is_produce_focused_market:
            return (3, 1, source_tier_rank)
        if source_kind == "chinaprice" and has_meat_context:
            return (4, 0, source_tier_rank)
        if source_kind == "pfsc" and has_meat_context:
            return (5, 0, source_tier_rank)
        if source_kind == "other":
            return (5, 1, source_tier_rank)
        return (5, 0, source_tier_rank)

    if source_kind == "pfsc":
        return (0, 0, source_tier_rank)
    if source_kind == "wanbang":
        return (1, 0, source_tier_rank)
    if source_kind == "other":
        return (2, 0, source_tier_rank)
    return (4, 0, source_tier_rank)


def _build_source_priority_label(chosen: pd.Series | None, ingredient_family: str) -> str | None:
    if chosen is None:
        return None
    source_kind = _infer_source_kind(chosen)
    has_effective_location = _has_effective_location(chosen)
    market_text = _build_market_context_text(chosen)
    row_city = _safe_text(chosen.get("city"))
    row_province = _safe_text(chosen.get("province"))

    def _reference_region_suffix() -> str:
        if row_city and row_city != "全国":
            return "同城"
        if row_province and row_province != "全国":
            return "同省"
        return "异地"

    if ingredient_family == "vegetable":
        if source_kind == "pfsc":
            return "蔬菜明细市场优先"
        if source_kind == "wanbang":
            return "万邦蔬菜报价优先"
    if ingredient_family == "aquatic":
        if source_kind == "pfsc":
            return "水产明细市场优先"
        if source_kind == "wanbang":
            return "万邦水产报价优先"
    if ingredient_family == "meat":
        if source_kind == "pfsc" and has_effective_location and "蔬菜" not in market_text:
            return "肉类市场报价优先"
        if source_kind == "wanbang":
            return "肉类批发市场优先"
        if source_kind == "chinaprice":
            return f"{_reference_region_suffix()}肉禽蛋参考价优先"
    if source_kind == "chinaprice":
        return "全国综合参考价"
    if source_kind == "pfsc":
        return "市场明细报价优先"
    if source_kind == "wanbang":
        return "批发市场报价优先"
    return "综合报价优先"


def _build_recommendation_reason(
    chosen: pd.Series | None,
    price_status: str,
    ingredient_family: str,
    preferred_province: str | None,
    preferred_city: str | None,
    preferred_location: str | None,
) -> str:
    if price_status != "已匹配报价" or chosen is None:
        return "当前没有命中报价，请人工确认"

    source_priority_label = _build_source_priority_label(chosen, ingredient_family)
    source_tier_label = _resolve_source_tier_label(chosen)
    row_city = _safe_text(chosen.get("city"))
    row_province = _safe_text(chosen.get("province"))
    tier_suffix = f"；来源层级：{source_tier_label}" if source_tier_label else ""
    if preferred_city and row_city == preferred_city:
        return f"已综合位置、来源优先级和价格推荐，当前优先同城市场；来源策略：{source_priority_label}{tier_suffix}"
    preferred_location_province, preferred_location_city = _normalize_location_preference(preferred_location)
    if preferred_location_city and row_city == preferred_location_city:
        return f"已综合位置、来源优先级和价格推荐，当前优先当前位置附近同城市场；来源策略：{source_priority_label}{tier_suffix}"
    if preferred_province and row_province == preferred_province:
        return f"已综合位置、来源优先级和价格推荐，当前优先同省市场；来源策略：{source_priority_label}{tier_suffix}"
    if preferred_location_province and row_province == preferred_location_province:
        return f"已综合位置、来源优先级和价格推荐，当前优先当前位置附近同省市场；来源策略：{source_priority_label}{tier_suffix}"
    return f"已综合位置、来源优先级和价格推荐；来源策略：{source_priority_label}{tier_suffix}"


def _infer_quantity(category: str | None, ingredient_family: str, diners: int, tables: int) -> tuple[float | None, str]:
    effective_tables = max(1, int(tables or 0))
    effective_diners = max(1, int(diners or 0))
    category_text = str(category or "")
    if ingredient_family in {"meat", "aquatic"} or any(keyword in category_text for keyword in ["肉", "禽", "蛋", "海鲜", "水产", "家畜", "畜禽"]):
        return round(effective_tables * 1.2 + effective_diners * 0.05, 2), "公斤"
    if ingredient_family == "vegetable" or any(keyword in category_text for keyword in ["菜", "蔬", "菌", "豆"]):
        return round(effective_tables * 0.8 + effective_diners * 0.03, 2), "公斤"
    return round(effective_tables * 0.6 + effective_diners * 0.02, 2), "公斤"


def _resolve_processing_profile(ingredient_name: str, category: str | None) -> tuple[float, float, str]:
    ingredient_text = str(ingredient_name or "").strip()
    category_text = str(category or "").strip()
    combined_text = f"{ingredient_text} {category_text}"
    for profile in INGREDIENT_PROCESSING_PROFILES:
        keywords = tuple(profile.get("keywords") or ())
        if any(keyword and keyword in combined_text for keyword in keywords):
            edible_yield_ratio = float(profile.get("edible_yield_ratio") or 1.0)
            cooking_yield_ratio = float(profile.get("cooking_yield_ratio") or 1.0)
            profile_label = str(profile.get("profile_label") or "默认净料换算")
            return edible_yield_ratio, cooking_yield_ratio, profile_label
    return 1.0, 1.0, "默认净料换算"


def enrich_menu_items_with_ai(
    menu_items: list[dict[str, Any]],
    runtime_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not menu_items or not is_ai_extraction_enabled(runtime_config):
        return menu_items
    api_key = get_api_key(runtime_config)
    if not api_key:
        return menu_items

    ai_config = get_ai_config(runtime_config)
    provider = str(ai_config.get("provider") or "qwen").strip().lower()
    if provider != "qwen":
        return menu_items

    model = str(ai_config.get("model") or "qwen-plus").strip() or "qwen-plus"
    base_url = str(ai_config.get("base_url") or "https://dashscope.aliyuncs.com/compatible-mode/v1").strip()
    timeout_seconds = int(ai_config.get("timeout_seconds") or 20)
    enable_search = bool(ai_config.get("menu_enable_search", True))
    try:
        content = call_qwen_chat_completion_text(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是餐饮采购助手。请把菜单菜名映射成采购时最核心、最标准的采购食材。"
                        "你可以结合联网搜索判断常见菜的标准主食材组成。"
                        "必须只输出 JSON，不要输出解释。"
                        "优先返回格式："
                        '{"items":[{"menu_name":"菜名","ingredient_name":"食材1、食材2","remarks":"可选备注"}]}'
                        "返回 1 到 4 个主要采购食材，使用中文顿号连接，例如“土豆、茄子、青椒”。"
                        "不要输出盐、油、酱油、醋、料酒、糖、淀粉、葱姜蒜这类基础调料，除非菜名本身核心就是它。"
                        "不要输出做法说明，不要输出菜名本身作为 ingredient_name。"
                        "如果菜名带做法词，例如蒜蓉、红烧、清蒸、宫保、鱼香，只输出核心食材。"
                        "示例：蒜蓉西兰花->西兰花；地三鲜->土豆、茄子、青椒；佛跳墙->鲍鱼、海参、花胶、瑶柱；宫保鸡丁->鸡丁、花生米、黄瓜。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(menu_items, ensure_ascii=False, indent=2),
                },
            ],
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            base_url=base_url,
            temperature=0.1,
            response_format={"type": "json_object"},
            enable_search=enable_search,
        )
        ai_payload = _parse_menu_ai_payload(content)
        _write_menu_ai_log(
            {
                "status": "success",
                "model": model,
                "enable_search": enable_search,
                "request_items": menu_items,
                "raw_content": content,
                "response_payload": ai_payload,
            }
        )
        items = ai_payload.get("items") if isinstance(ai_payload, dict) else None
        enriched_map: dict[str, dict[str, Any]] = {}
        if isinstance(items, list):
            enriched_map = {
                str(item.get("menu_name") or "").strip(): item
                for item in items
                if isinstance(item, dict)
            }
        elif isinstance(ai_payload, list):
            enriched_map = {
                str(item.get("menu_name") or "").strip(): item
                for item in ai_payload
                if isinstance(item, dict) and str(item.get("menu_name") or "").strip()
            }
        elif (
            isinstance(ai_payload, dict)
            and str(ai_payload.get("menu_name") or "").strip()
            and any(ai_payload.get(field) for field in ["ingredient_name", "ingredients"])
        ):
            menu_name = str(ai_payload.get("menu_name") or "").strip()
            enriched_map = {
                menu_name: {
                    "menu_name": menu_name,
                    "ingredient_name": ai_payload.get("ingredient_name") or ai_payload.get("ingredients"),
                    "remarks": ai_payload.get("remarks"),
                }
            }
        elif isinstance(ai_payload, dict):
            enriched_map = {
                str(menu_name).strip(): {
                    "menu_name": str(menu_name).strip(),
                    "ingredient_name": value,
                    "remarks": None,
                }
                for menu_name, value in ai_payload.items()
                if str(menu_name).strip()
            }
        if not enriched_map:
            fallback_rows = _fallback_enrich_menu_items(menu_items)
            _write_menu_ai_log(
                {
                    "status": "fallback",
                    "model": model,
                    "enable_search": enable_search,
                    "request_items": menu_items,
                    "reason": "ai_payload_not_supported",
                    "fallback_items": fallback_rows,
                }
            )
            return fallback_rows
        enriched_rows: list[dict[str, Any]] = []
        for row in menu_items:
            menu_name = str(row.get("menu_name") or "").strip()
            heuristic_ingredient_name = _infer_ingredient_name_from_menu(menu_name)
            ai_row = enriched_map.get(str(row.get("menu_name") or "").strip(), {})
            raw_ai_ingredient_name = ai_row.get("ingredient_name") or ai_row.get("ingredients") or row.get("menu_name")
            normalized_ingredient_name = _normalize_menu_ai_ingredient(
                menu_name,
                raw_ai_ingredient_name,
            )
            if (
                not normalized_ingredient_name
                or _normalize_name(str(raw_ai_ingredient_name or "")) == _normalize_name(menu_name)
            ):
                normalized_ingredient_name = heuristic_ingredient_name
            enriched_rows.append(
                {
                    **row,
                    "ingredient_name": normalized_ingredient_name,
                    "remarks": ai_row.get("remarks") or row.get("remarks"),
                }
            )
        return enriched_rows
    except Exception as exc:  # noqa: BLE001
        fallback_rows = _fallback_enrich_menu_items(menu_items)
        _write_menu_ai_log(
            {
                "status": "error",
                "model": model,
                "enable_search": enable_search,
                "request_items": menu_items,
                "error": str(exc),
                "fallback_items": fallback_rows,
            }
        )
        return fallback_rows


def build_procurement_plan(
    menu_items: list[dict[str, Any]],
    latest_records_df: pd.DataFrame,
    diners: int = 0,
    tables: int = 0,
    preferred_province: str | None = None,
    preferred_city: str | None = None,
    preferred_location: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not menu_items:
        return pd.DataFrame(), pd.DataFrame()

    expanded_menu_items = _expand_menu_items(menu_items)
    if not expanded_menu_items:
        return pd.DataFrame(), pd.DataFrame()

    latest = latest_records_df.copy() if latest_records_df is not None else pd.DataFrame()
    if not latest.empty:
        latest["match_text"] = latest[
            [column for column in ["product_name", "group_name", "category", "brand", "product_series", "market_name", "site_name"] if column in latest.columns]
        ].fillna("").astype(str).agg(" ".join, axis=1)
        latest["match_key"] = latest["match_text"].apply(_normalize_name)
    plan_rows: list[dict[str, Any]] = []
    ingredient_rows: list[dict[str, Any]] = []
    effective_tables = max(1, int(tables or 0))
    effective_diners = max(1, int(diners or 0))

    for row in expanded_menu_items:
        menu_name = str(row.get("menu_name") or "").strip()
        ingredient_name = str(row.get("ingredient_name") or menu_name).strip()
        ingredient_ratio = float(row.get("ingredient_ratio") or 1.0)
        normalized_candidates = _build_menu_alias_keys(menu_name, ingredient_name)
        candidates = latest.copy()
        if not candidates.empty and normalized_candidates:
            match_mask = pd.Series(False, index=candidates.index)
            for candidate in normalized_candidates:
                match_mask = match_mask | candidates["match_key"].str.contains(candidate, regex=False)
            candidates = candidates[match_mask]

        unit_price = None
        price_unit_basis = pd.NA
        chosen = None
        ingredient_family = _infer_ingredient_family(ingredient_name)
        if not candidates.empty and "current_price" in candidates.columns:
            candidates = candidates.dropna(subset=["current_price"]).copy()
            candidates["ingredient_match_rank"] = candidates.apply(
                lambda candidate_row: _build_ingredient_match_rank(candidate_row, normalized_candidates),
                axis=1,
            )
            if "spec_text" in candidates.columns:
                spec_meta = candidates["spec_text"].apply(parse_spec)
                candidates["kg_price"] = [
                    compute_kg_price(price, meta.get("unit_name"), meta.get("unit_value"))
                    for price, meta in zip(candidates["current_price"], spec_meta)
                ]
            else:
                candidates["kg_price"] = pd.NA
            candidates["location_rank"] = candidates.apply(
                lambda candidate_row: _build_location_rank(
                    candidate_row,
                    preferred_province=preferred_province,
                    preferred_city=preferred_city,
                    preferred_location=preferred_location,
                ),
                axis=1,
            )
            candidates["ingredient_family"] = ingredient_family
            candidates["source_priority"] = candidates.apply(
                lambda candidate_row: _build_source_priority(candidate_row, ingredient_family),
                axis=1,
            )
            candidates = candidates.sort_values(
                ["location_rank", "source_priority", "ingredient_match_rank", "kg_price", "current_price", "site_name"],
                ascending=[True, True, True, True, True, True],
                na_position="last",
            )
            if not candidates.empty:
                chosen = candidates.iloc[0]
                kg_price = chosen.get("kg_price")
                if pd.notna(kg_price):
                    unit_price = float(kg_price)
                    price_unit_basis = "元/公斤"
                else:
                    raw_price = chosen.get("current_price")
                    unit_price = float(raw_price) if pd.notna(raw_price) else None
                    price_unit_basis = "原始报价"

        category = chosen.get("category") if chosen is not None else None
        net_quantity, quantity_unit = _infer_quantity(category, ingredient_family=ingredient_family, diners=effective_diners, tables=effective_tables)
        if net_quantity is not None:
            net_quantity = round(float(net_quantity) * ingredient_ratio, 2)
        edible_yield_ratio, cooking_yield_ratio, profile_label = _resolve_processing_profile(ingredient_name, category)
        purchase_yield_ratio = round(max(edible_yield_ratio * cooking_yield_ratio, 0.01), 4)
        estimated_quantity = (
            round(float(net_quantity) / purchase_yield_ratio, 2)
            if net_quantity is not None
            else None
        )
        estimated_cost = round(unit_price * estimated_quantity, 2) if unit_price is not None and estimated_quantity is not None else None
        processing_assumption = (
            f"按{effective_tables}桌共{effective_diners}人测算；净料{net_quantity}公斤，"
            f"套用{profile_label}（可食率{edible_yield_ratio:.0%}×熟制率{cooking_yield_ratio:.0%}），"
            f"折算采购毛料{estimated_quantity}公斤。"
            if estimated_quantity is not None and net_quantity is not None
            else f"按{effective_tables}桌共{effective_diners}人测算；当前缺少可计算的数量或价格。"
        )

        ingredient_rows.append(
            {
                "menu_name": menu_name,
                "ingredient_name": ingredient_name,
                "ingredient_ratio": ingredient_ratio,
                "net_quantity": net_quantity,
                "estimated_quantity": estimated_quantity,
                "quantity_unit": quantity_unit,
                "edible_yield_ratio": edible_yield_ratio,
                "cooking_yield_ratio": cooking_yield_ratio,
                "purchase_yield_ratio": purchase_yield_ratio,
                "processing_profile": profile_label,
                "remarks": row.get("remarks"),
            }
        )
        price_status = "已匹配报价" if chosen is not None else "缺报价/待确认"
        recommendation_reason = _build_recommendation_reason(
            chosen,
            price_status=price_status,
            ingredient_family=ingredient_family,
            preferred_province=preferred_province,
            preferred_city=preferred_city,
            preferred_location=preferred_location,
        )
        plan_rows.append(
            {
                "menu_name": menu_name,
                "ingredient_name": ingredient_name,
                "ingredient_ratio": ingredient_ratio,
                "net_quantity": net_quantity,
                "estimated_quantity": estimated_quantity,
                "quantity_unit": quantity_unit,
                "price_unit_basis": price_unit_basis,
                "reference_price": unit_price,
                "estimated_cost": estimated_cost,
                "edible_yield_ratio": edible_yield_ratio,
                "cooking_yield_ratio": cooking_yield_ratio,
                "purchase_yield_ratio": purchase_yield_ratio,
                "processing_profile": profile_label,
                "guest_context": f"{effective_tables}桌共{effective_diners}人",
                "recommended_market": chosen.get("market_name") if chosen is not None else pd.NA,
                "recommended_site": chosen.get("site_name") if chosen is not None else pd.NA,
                "province": chosen.get("province") if chosen is not None else pd.NA,
                "city": chosen.get("city") if chosen is not None else pd.NA,
                "source_tier": _resolve_source_tier_label(chosen) if chosen is not None else pd.NA,
                "backup_market": candidates.iloc[1]["market_name"] if len(candidates) > 1 and "market_name" in candidates.columns else pd.NA,
                "backup_site": candidates.iloc[1]["site_name"] if len(candidates) > 1 and "site_name" in candidates.columns else pd.NA,
                "backup_source_tier": _resolve_source_tier_label(candidates.iloc[1]) if len(candidates) > 1 else pd.NA,
                "source_priority_label": _build_source_priority_label(chosen, ingredient_family),
                "backup_source_priority_label": (
                    _build_source_priority_label(candidates.iloc[1], ingredient_family) if len(candidates) > 1 else pd.NA
                ),
                "distance_label": (
                    "同城优先"
                    if chosen is not None and preferred_city and _safe_text(chosen.get("city")) == preferred_city
                    else "同省优先"
                    if chosen is not None and preferred_province and _safe_text(chosen.get("province")) == preferred_province
                    else "当前位置附近"
                    if chosen is not None and preferred_location and (
                        _safe_text(chosen.get("city")) == (_normalize_location_preference(preferred_location)[1] or "")
                        or _safe_text(chosen.get("province")) == (_normalize_location_preference(preferred_location)[0] or "")
                    )
                    else pd.NA
                ),
                "price_status": price_status,
                "remarks": row.get("remarks") or f"{processing_assumption} {recommendation_reason}",
            }
        )

    ingredient_df = pd.DataFrame(ingredient_rows)
    plan_df = pd.DataFrame(plan_rows)
    if not plan_df.empty and "estimated_cost" in plan_df.columns:
        total_cost = pd.to_numeric(plan_df["estimated_cost"], errors="coerce").sum(min_count=1)
        plan_df.attrs["total_cost"] = None if pd.isna(total_cost) else round(float(total_cost), 2)
    return ingredient_df, plan_df
