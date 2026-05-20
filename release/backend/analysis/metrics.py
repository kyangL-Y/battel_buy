from __future__ import annotations

import io
import json
import re
from typing import Any, Callable

import pandas as pd

from parsers.normalizer import format_price_unit_basis, parse_spec
from utils.location_catalog import match_standard_city, match_standard_province
from utils.source_config import resolve_source_tier


TREND_STABLE_THRESHOLD = 0.02
NON_PRODUCT_LABEL_PATTERN = re.compile(
    r"影响|调整|建议|采购|预警|趋势|来源动态|老板|驾驶舱|复制|copy"
    r"|环比|同比|变化率|增长率|下降率|增幅|降幅|涨跌幅|增速|指数|指标"
    r"|存栏|出栏|产量|销量|销售量|成交量|进口量|出口量|库存|开工率|利用率"
    r"|均价|平均价|监测情况|价格监测|市场价格|价格表现|市场表现|走势分析"
    r"|基本概况|概况|热点|话题|原因|情况|调查|波动|下降|上涨|持平|回落|反弹|上市量|货量|产区|消费需求|节日|季节",
    re.IGNORECASE,
)
NON_PRODUCT_UNIT_TEXTS = {"%", "％", "百分比", "百分点", "指数", "点", "条", "次"}
NON_FOOD_LABEL_PATTERN = re.compile(
    r"动力煤|煤|线材|螺纹钢|钢材|热轧|中厚板|铜|铝|氧化铝|甲醇|纯碱|烧碱|合成氨"
    r"|水泥|玻璃|原油|石油|汽油|柴油|化工|工业|电解铜|铝锭|豆粕"
    r"|叶面肥|肥料|化肥|复合肥|农药|杀菌剂|杀虫剂|除草剂|助剂|农资"
    r"|垃圾桶|收纳箱|包装|餐具|清洁|用品|耗材|纸巾|抽纸|餐巾纸|手套|托盘|保鲜膜|垃圾袋|易耗"
    r"|固体酒精|火碱|锅|煎锅|不粘锅"
    r"|酒水饮料|饮用水|矿物质水|纯净水|天然水|矿泉水|饮料",
    re.IGNORECASE,
)
NON_FOOD_UNIT_TEXTS = {"美元/桶", "元/吨", "元/平方米", "元/升"}
LOCATION_ENTITY_MARKERS = (
    "农产品",
    "农副产品",
    "蔬菜",
    "果品",
    "果业",
    "水果",
    "粮油",
    "市场",
    "海吉星",
    "物流",
    "交易",
    "批发",
    "国际",
    "九鼎",
    "绿珠",
    "北园春",
    "川北",
    "韩家墅",
    "何庄子",
    "金钟河",
    "红旗",
    "碧城",
    "大沙河",
    "新发地",
    "大洋路",
    "周谷堆",
    "曙光",
    "双福",
    "江桥",
    "石门",
    "美通",
    "哈达",
    "水屯",
)
LOCATION_SPECIAL_CITY_PREFIXES = (
    "乌鲁木齐",
    "呼和浩特",
    "南充",
    "南宁",
    "兰州",
    "吴忠",
    "喀什",
    "义乌",
    "亳州",
    "乐亭",
    "佛山",
    "南京",
    "哈尔滨",
    "嘉善",
    "孝义",
    "宁波",
    "寿光",
    "庆阳",
    "徐州",
    "扶余",
    "昆明",
    "晋城",
    "杭州",
    "海口",
    "洛阳",
    "济南",
    "广州",
    "武汉",
    "潜江",
    "滕州",
    "银川",
    "天长",
    "师宗",
    "平凉",
    "南昌",
)
QUOTE_EXPORT_PRIORITY_COLUMNS = [
    "group_name",
    "site_name",
    "source_url",
    "url",
    "captured_at",
    "product_key",
    "product_name",
    "category",
    "brand",
    "product_series",
    "spec_text",
    "compare_key",
    "province",
    "city",
    "market_name",
    "region_label",
    "current_price",
    "original_price",
    "promotion_text",
    "currency",
    "unit_name",
    "unit_value",
    "unit_price",
    "jin_price",
    "fetch_mode",
    "status_code",
]
QUOTE_EXPORT_DROP_COLUMNS = {
    "诊断类型",
    "诊断结论",
    "处理建议",
    "raw_payload",
    "rn",
    "error",
    "suggestion",
    "fallback_used",
    "timeout",
    "retries",
    "delay",
    "timeout_ms",
    "blocked_status_codes",
}
LOCAL_COMPARE_COLUMN_ALIASES = {
    "group_name": ["group_name", "商品分组", "分组", "商品组", "商品分组名称"],
    "product_name": ["product_name", "商品名称", "名称", "品名", "商品名", "产品", "货品名称"],
    "category": ["category", "商品品类", "品类", "分类"],
    "brand": ["brand", "品牌"],
    "product_series": ["product_series", "系列", "系列/型号", "型号", "商品系列"],
    "spec_text": ["spec_text", "规格", "规格型号", "包装规格", "容量"],
    "site_name": ["site_name", "平台", "网站", "来源平台", "店铺", "站点名称", "供应商", "报价来源"],
    "local_price": ["local_price", "本地价格", "价格", "当前价格", "售价", "采购价", "对比价格", "单价", "报价", "价格（元）"],
    "box_price": ["box_price", "报价（箱）", "箱价", "整箱价", "件价"],
    "tax_price": ["tax_price", "税价", "含税价"],
    "remarks": ["remarks", "备注", "说明"],
    "market_category": ["market_category", "来源分类", "市场分类", "市场品类", "类别"],
    "channel": ["channel", "渠道", "来源渠道"],
    "source_row_no": ["source_row_no", "序号", "编号"],
    "compare_key": ["compare_key", "对比键", "匹配键"],
}


def _normalize_compare_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"[\s\-_·•|/]+", "", text)
    return re.sub(r"[^\u4e00-\u9fa5a-z0-9]+", "", text)


def _normalize_compare_series(series: pd.Series) -> pd.Series:
    normalized = series.fillna("").astype(str).str.strip().str.lower()
    normalized = normalized.str.replace(r"[\s\-_·•|/]+", "", regex=True)
    return normalized.str.replace(r"[^\u4e00-\u9fa5a-z0-9]+", "", regex=True)


def _extract_source_group_name(site_name: Any, source_url: Any = None) -> str:
    source_url_text = ""
    if source_url is not None and not pd.isna(source_url):
        source_url_text = str(source_url).strip().lower()
    if source_url_text.startswith("supplier://"):
        return "供应平台"
    if "liancaiwang.cn" in source_url_text:
        return "莲菜网"
    if "pfsc.agri.cn" in source_url_text:
        return "PFSC"
    if "chinaprice.cn" in source_url_text:
        return "Chinaprice"
    if "wbncp.com" in source_url_text:
        return "万邦国际"

    if site_name is None or pd.isna(site_name):
        return ""
    text = str(site_name).strip()
    if not text:
        return ""
    if text.startswith("莲菜网"):
        return "莲菜网"
    if "|" in text:
        return text.split("|", 1)[0].strip()
    if text.startswith("莲菜网"):
        return "莲菜网"
    return text


def _extract_source_display_name(site_name: Any, group_name: Any = None, source_url: Any = None) -> str:
    platform_name = _extract_source_group_name(site_name, source_url)
    site_text = "" if site_name is None or pd.isna(site_name) else str(site_name).strip()
    group_text = "" if group_name is None or pd.isna(group_name) else str(group_name).strip()

    if platform_name in {"PFSC", "Chinaprice"}:
        parts: list[str] = [platform_name]
        if group_text:
            parts.append(group_text)
        if site_text:
            detail_text = site_text
            prefix = f"{platform_name} |"
            if detail_text.startswith(prefix):
                detail_text = detail_text[len(prefix):].strip()
            if detail_text:
                parts.append(detail_text)
        return " | ".join(dict.fromkeys(part for part in parts if part))

    if site_text:
        return site_text
    return platform_name


def _normalize_location_display_name(value: Any) -> str:
    text = _normalize_location_text(value)
    if not text:
        return ""
    matched_city, _ = match_standard_city(text)
    if matched_city:
        return matched_city
    matched_province = match_standard_province(text)
    if matched_province:
        return matched_province
    return text


def _build_trend_series_name(row: pd.Series) -> str:
    source_name = _extract_source_group_name(row.get("site_name"), row.get("source_url")) or "未知来源"
    market_name = _normalize_location_text(row.get("market_name")) or ""
    region_name = (
        _normalize_location_display_name(row.get("city"))
        or _normalize_location_display_name(row.get("region_label"))
        or _normalize_location_display_name(row.get("province"))
    )

    if source_name == "Chinaprice":
        if region_name and market_name and market_name != "总平均价":
            return f"{source_name} · {region_name} · {market_name}"
        if region_name:
            return f"{source_name} · {region_name}"
        if market_name:
            return f"{source_name} · {market_name}"
        return source_name

    if market_name and region_name and market_name != region_name:
        return f"{source_name} · {market_name}"
    if market_name:
        return f"{source_name} · {market_name}"
    if region_name:
        return f"{source_name} · {region_name}"
    site_text = _normalize_location_text(row.get("site_name")) or ""
    return site_text or source_name


def _build_trend_meta_label(row: pd.Series) -> str:
    source_name = _extract_source_group_name(row.get("site_name"), row.get("source_url")) or "未知来源"
    market_name = _normalize_location_text(row.get("market_name")) or ""
    region_name = (
        _normalize_location_display_name(row.get("city"))
        or _normalize_location_display_name(row.get("region_label"))
        or _normalize_location_display_name(row.get("province"))
    )
    province_name = _normalize_location_display_name(row.get("province"))

    parts: list[str] = []
    if source_name == "Chinaprice" and market_name and market_name != "总平均价":
        parts.append(market_name)
    if region_name:
        parts.append(region_name)
    if province_name and province_name not in parts:
        parts.append(province_name)
    if not parts and market_name:
        parts.append(market_name)
    return " · ".join(parts) if parts else source_name


def _trend_market_priority(row: pd.Series) -> int:
    source_name = _extract_source_group_name(row.get("site_name"), row.get("source_url"))
    market_name = _normalize_location_text(row.get("market_name")) or ""
    if source_name != "Chinaprice":
        return 0
    if market_name == "总平均价":
        return 0
    if market_name == "集市":
        return 1
    if market_name == "超市":
        return 2
    return 3


def _build_trend_source_name(row: pd.Series) -> str:
    source_name = _extract_source_group_name(row.get("site_name"), row.get("source_url"))
    if source_name:
        return source_name
    site_name = _normalize_location_text(row.get("site_name"))
    return site_name or "未知来源"


def _build_trend_source_tier(row: pd.Series) -> str | None:
    source_tier = resolve_source_tier(
        {
            "source_tier": row.get("source_tier"),
            "source_url": row.get("source_url"),
            "url": row.get("source_url"),
            "site_name": row.get("site_name"),
            "source_name": _build_trend_source_name(row),
        }
    )
    return source_tier or None


def _prepare_trend_display_rows(df: pd.DataFrame, prefer_primary_channel: bool = True) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    trend_df = enrich_location_fields(df.copy())
    trend_df["source_group_name"] = trend_df.apply(
        lambda row: _extract_source_group_name(row.get("site_name"), row.get("source_url")),
        axis=1,
    )
    trend_df["trend_region_label"] = trend_df.apply(
        lambda row: (
            _normalize_location_display_name(row.get("city"))
            or _normalize_location_display_name(row.get("region_label"))
            or _normalize_location_display_name(row.get("province"))
        ),
        axis=1,
    )
    trend_df["source_name"] = trend_df.apply(_build_trend_source_name, axis=1)
    trend_df["source_tier"] = trend_df.apply(_build_trend_source_tier, axis=1)
    trend_df["trend_series_name"] = trend_df.apply(_build_trend_series_name, axis=1)
    trend_df["trend_series_key"] = trend_df["trend_series_name"]
    trend_df["trend_meta_label"] = trend_df.apply(_build_trend_meta_label, axis=1)
    trend_df["trend_market_priority"] = trend_df.apply(_trend_market_priority, axis=1)

    if prefer_primary_channel:
        chinaprice_rows = trend_df["source_group_name"].eq("Chinaprice")
        if chinaprice_rows.any():
            chinaprice_df = trend_df[chinaprice_rows].copy()
            other_df = trend_df[~chinaprice_rows].copy()
            chinaprice_df = chinaprice_df.sort_values(
                ["captured_at", "trend_region_label", "trend_market_priority", "trend_series_name"],
                ascending=[True, True, True, True],
                na_position="last",
            )
            chinaprice_df = chinaprice_df.groupby(
                ["captured_at", "trend_region_label"],
                as_index=False,
                dropna=False,
            ).head(1)
            trend_df = pd.concat([other_df, chinaprice_df], ignore_index=False)

    trend_df = trend_df.sort_values(["captured_at", "trend_series_name"], na_position="last")
    return trend_df.reset_index(drop=True)


def _collapse_trend_to_daily_latest(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    trend_df = df.copy()
    trend_df["captured_at"] = pd.to_datetime(trend_df["captured_at"], errors="coerce")
    trend_df = trend_df.dropna(subset=["captured_at"]).copy()
    if trend_df.empty:
        return trend_df

    trend_df["captured_day"] = trend_df["captured_at"].dt.strftime("%Y-%m-%d")
    trend_df = trend_df.sort_values(
        ["trend_series_key", "captured_day", "captured_at"],
        ascending=[True, True, True],
        na_position="last",
    )
    trend_df = (
        trend_df.groupby(["trend_series_key", "captured_day"], as_index=False, dropna=False)
        .tail(1)
        .copy()
    )
    trend_df["captured_at_raw"] = trend_df["captured_at"]
    trend_df["captured_at"] = trend_df["captured_day"]
    chinaprice_rows = trend_df["source_group_name"].eq("Chinaprice") if "source_group_name" in trend_df.columns else pd.Series(False, index=trend_df.index)
    if chinaprice_rows.any():
        chinaprice_df = trend_df[chinaprice_rows].copy()
        other_df = trend_df[~chinaprice_rows].copy()
        chinaprice_df = chinaprice_df.sort_values(
            ["captured_day", "trend_region_label", "trend_market_priority", "captured_at_raw"],
            ascending=[True, True, True, False],
            na_position="last",
        )
        chinaprice_df = (
            chinaprice_df.groupby(["captured_day", "trend_region_label"], as_index=False, dropna=False)
            .head(1)
            .sort_values(["captured_day", "trend_series_name"], na_position="last")
        )
        trend_df = pd.concat([other_df, chinaprice_df], ignore_index=False)
    return trend_df.sort_values(["captured_day", "trend_series_name"], na_position="last").reset_index(drop=True)


def _normalize_cross_site_price(current_price: Any, spec_text: Any) -> tuple[float | None, str]:
    try:
        price = float(current_price)
    except (TypeError, ValueError):
        return None, str(spec_text).strip() if spec_text is not None and not pd.isna(spec_text) else ""

    spec_info = parse_spec(str(spec_text) if spec_text is not None and not pd.isna(spec_text) else None)
    unit_name = spec_info.get("unit_name")
    unit_value = spec_info.get("unit_value")
    normalized_spec_text = str(spec_text).strip() if spec_text is not None and not pd.isna(spec_text) else ""

    if unit_name == "g" and unit_value not in (None, 0):
        return round(price / float(unit_value) * 1000, 6), "公斤"
    if unit_name == "ml" and unit_value not in (None, 0):
        return round(price / float(unit_value) * 1000, 6), "升"
    return price, normalized_spec_text


def _normalize_cross_site_spec_text(spec_text: Any) -> str:
    _, normalized_spec_text = _normalize_cross_site_price(1.0, spec_text)
    return normalized_spec_text


def build_cross_site_identity_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    result = df.copy()
    for column in ["group_name", "product_name", "brand", "product_series", "spec_text"]:
        if column not in result.columns:
            result[column] = ""
        result[column] = result[column].fillna("").astype(str).str.strip()

    primary_name_series = result["product_name"].where(result["product_name"].ne(""), result["group_name"]).fillna("")
    fallback_label_series = primary_name_series.where(primary_name_series.ne(""), "未命名商品")
    result["normalized_spec_text"] = result["spec_text"].apply(_normalize_cross_site_spec_text)

    normalized_parts = pd.DataFrame(
        {
            "primary_name": _normalize_compare_series(primary_name_series),
            "brand": _normalize_compare_series(result["brand"]),
            "product_series": _normalize_compare_series(result["product_series"]),
            "spec_text": _normalize_compare_series(result["normalized_spec_text"]),
        },
        index=result.index,
    ).replace("", pd.NA)
    result["cross_site_identity_key"] = _join_non_empty_series_columns(
        normalized_parts,
        ["primary_name", "brand", "product_series", "spec_text"],
        "|",
    )

    label_extras = _join_non_empty_series_columns(
        pd.DataFrame(
            {
                "brand": result["brand"],
                "product_series": result["product_series"],
                "spec_text": result["normalized_spec_text"],
            },
            index=result.index,
        ),
        ["brand", "product_series", "spec_text"],
        " | ",
    )
    result["cross_site_identity_label"] = fallback_label_series.copy()
    extras_mask = label_extras.str.strip().ne("")
    result.loc[extras_mask, "cross_site_identity_label"] = (
        result.loc[extras_mask, "cross_site_identity_label"] + " | " + label_extras.loc[extras_mask].astype(str)
    )

    if "price_identity_key" in result.columns:
        explicit_identity_key = result["price_identity_key"].fillna("").astype(str).str.strip()
        result.loc[explicit_identity_key.ne(""), "cross_site_identity_key"] = explicit_identity_key.loc[explicit_identity_key.ne("")]
    if "price_identity_label" in result.columns:
        explicit_identity_label = result["price_identity_label"].fillna("").astype(str).str.strip()
        result.loc[explicit_identity_label.ne(""), "cross_site_identity_label"] = explicit_identity_label.loc[explicit_identity_label.ne("")]
    return result


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def _normalize_optional_text(value: Any) -> Any:
    if value is None or pd.isna(value):
        return pd.NA
    text = str(value).strip()
    return text or pd.NA


def _normalize_location_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _normalize_explicit_province(value: Any) -> str | None:
    text = _normalize_location_text(value)
    if not text:
        return None
    matched_province = match_standard_province(text)
    if matched_province:
        return matched_province
    _, matched_city_province = match_standard_city(text)
    return matched_city_province


def _normalize_explicit_city(value: Any) -> str | None:
    text = _normalize_location_text(value)
    if not text:
        return None
    matched_city, _ = match_standard_city(text)
    if matched_city:
        return matched_city
    matched_province = match_standard_province(text)
    if matched_province == "全国":
        return "全国"
    if re.search(r"(市场|批发|物流|交易|农产品|农副产品|海吉星|国际|有限公司)", text):
        return None
    return None


def _is_valid_city_candidate(candidate: str | None) -> bool:
    text = _normalize_location_text(candidate)
    if not text:
        return False
    if any(marker in text for marker in LOCATION_ENTITY_MARKERS):
        return False
    if match_standard_province(text) and text not in {"北京市", "上海市", "天津市", "重庆市", "全国"}:
        return False
    return 2 <= len(text) <= 6


def _extract_location_tokens(*values: Any) -> tuple[str | None, str | None]:
    province_text: str | None = None
    city_text: str | None = None

    for raw_value in values:
        text = _normalize_location_text(raw_value)
        if not text:
            continue
        if "|" in text:
            text = text.split("|")[-1].strip()
        if not text:
            continue

        if province_text is None:
            province_text = match_standard_province(text)

        if city_text is None:
            matched_city, matched_city_province = match_standard_city(text)
            if matched_city:
                city_text = matched_city
                if province_text is None and matched_city_province:
                    province_text = matched_city_province

        if city_text is None:
            if province_text in {"北京市", "上海市", "天津市", "重庆市"}:
                city_text = province_text
            else:
                city_match = re.search(r"^([\u4e00-\u9fa5]{2,12}?)(?:市(?!场)|州(?!场)|盟|地区|县|区|旗)", text)
                if city_match:
                    candidate = str(city_match.group(1) or "").strip()
                    matched_candidate_city, matched_candidate_province = match_standard_city(candidate)
                    if matched_candidate_city:
                        city_text = matched_candidate_city
                        if province_text is None and matched_candidate_province:
                            province_text = matched_candidate_province
                    elif _is_valid_city_candidate(candidate):
                        city_text = candidate
                else:
                    for prefix in LOCATION_SPECIAL_CITY_PREFIXES:
                        if text.startswith(prefix):
                            city_text = prefix
                            if province_text is None:
                                _, matched_prefix_province = match_standard_city(prefix)
                                if matched_prefix_province:
                                    province_text = matched_prefix_province
                            break

        if province_text and city_text:
            break

    return province_text, city_text


def enrich_location_fields(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    enriched = df.copy()
    for column in ["province", "city", "market_name", "region_label", "site_name"]:
        if column not in enriched.columns:
            enriched[column] = pd.NA

    inferred = enriched.apply(
        lambda row: _extract_location_tokens(
            row.get("province"),
            row.get("city"),
            row.get("region_label"),
            row.get("market_name"),
            row.get("site_name"),
        ),
        axis=1,
    )
    inferred_df = pd.DataFrame(inferred.tolist(), columns=["_derived_province", "_derived_city"], index=enriched.index)

    explicit_province = enriched["province"].apply(_normalize_explicit_province)
    explicit_city = enriched["city"].apply(_normalize_explicit_city)
    explicit_region = enriched["region_label"].apply(_normalize_location_text)
    explicit_market = enriched["market_name"].apply(_normalize_location_text)

    enriched["province"] = explicit_province.combine_first(inferred_df["_derived_province"])
    enriched["city"] = explicit_city.combine_first(inferred_df["_derived_city"])
    enriched["region_label"] = explicit_region.combine_first(enriched["city"]).combine_first(enriched["province"]).combine_first(explicit_market)
    return enriched


def standardize_local_compare_file(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=list(LOCAL_COMPARE_COLUMN_ALIASES))

    result = df.copy()
    result.columns = [str(column).strip() for column in result.columns]

    rename_map: dict[str, str] = {}
    for target, aliases in LOCAL_COMPARE_COLUMN_ALIASES.items():
        source = _first_existing_column(result, aliases)
        if source:
            rename_map[source] = target
    result = result.rename(columns=rename_map)

    for column in LOCAL_COMPARE_COLUMN_ALIASES:
        if column not in result.columns:
            result[column] = pd.NA

    text_columns = [
        "group_name",
        "product_name",
        "category",
        "brand",
        "product_series",
        "spec_text",
        "site_name",
        "compare_key",
        "remarks",
        "market_category",
        "channel",
    ]
    for column in text_columns:
        result[column] = result[column].where(result[column].notna(), pd.NA)
        result[column] = result[column].apply(lambda value: str(value).strip() if pd.notna(value) else pd.NA)
        result[column] = result[column].replace({"": pd.NA})

    if result["group_name"].isna().all() and result["product_name"].notna().any():
        result["group_name"] = result["product_name"]
    if result["product_name"].isna().all() and result["group_name"].notna().any():
        result["product_name"] = result["group_name"]

    result["source_row_no"] = result["source_row_no"].apply(_normalize_optional_text)
    result["local_price"] = pd.to_numeric(result["local_price"], errors="coerce")
    result["box_price"] = pd.to_numeric(result["box_price"], errors="coerce")
    result["tax_price"] = pd.to_numeric(result["tax_price"], errors="coerce")
    if result["local_price"].isna().all() and result["box_price"].notna().any():
        result["local_price"] = result["box_price"]
    else:
        result["local_price"] = result["local_price"].fillna(result["box_price"])
    result = result.dropna(how="all", subset=["group_name", "product_name", "spec_text", "local_price"]).copy()
    result["local_row_id"] = range(1, len(result) + 1)
    result["local_match_key"] = result.apply(build_product_match_key, axis=1)
    result["local_match_text"] = result.apply(build_match_text, axis=1)
    return result.reset_index(drop=True)


def build_product_match_key(row: pd.Series) -> str:
    primary_name = row.get("product_name") or row.get("group_name")
    fields = [primary_name, row.get("category"), row.get("brand"), row.get("product_series"), row.get("spec_text")]
    key = "|".join(filter(None, (_normalize_compare_text(value) for value in fields)))
    if key:
        return key

    explicit_key = _normalize_compare_text(row.get("compare_key"))
    if explicit_key:
        return explicit_key

    fallback_fields = [row.get("group_name"), row.get("product_name"), row.get("spec_text")]
    return "|".join(filter(None, (_normalize_compare_text(value) for value in fallback_fields)))


def build_match_text(row: pd.Series) -> str:
    fields = [
        row.get("group_name"),
        row.get("product_name"),
        row.get("category"),
        row.get("brand"),
        row.get("product_series"),
        row.get("spec_text"),
        row.get("site_name"),
    ]
    return " ".join(filter(None, (_normalize_compare_text(value) for value in fields)))


def apply_ai_structured_enrichment(
    df: pd.DataFrame,
    extractor: Callable[[list[dict[str, Any]], dict[str, Any] | None], list[dict[str, Any]]] | None = None,
    runtime_config: dict[str, Any] | None = None,
) -> pd.DataFrame:
    if df.empty or extractor is None:
        return df.copy()

    ai_config = dict((runtime_config or {}).get("ai", {}))
    if not ai_config.get("enabled"):
        return df.copy()

    result = df.copy()
    if "ai_enriched" not in result.columns:
        result["ai_enriched"] = False
    if "ai_remarks" not in result.columns:
        result["ai_remarks"] = pd.NA

    candidate_mask = result.apply(
        lambda row: bool(pd.notna(row.get("product_name")) or pd.notna(row.get("group_name")))
        and (
            pd.isna(row.get("category"))
            or pd.isna(row.get("brand"))
            or pd.isna(row.get("product_series"))
            or pd.isna(row.get("spec_text"))
        ),
        axis=1,
    )
    candidates = result[candidate_mask].copy()
    if candidates.empty:
        return result

    max_rows_per_run = int(ai_config.get("max_rows_per_run") or len(candidates))
    batch_size = max(1, int(ai_config.get("batch_size") or 5))
    candidates = candidates.head(max_rows_per_run).copy()

    candidate_rows: list[dict[str, Any]] = []
    for row_index, row in candidates.iterrows():
        source_text_parts = [
            row.get("group_name"),
            row.get("product_name"),
            row.get("category"),
            row.get("brand"),
            row.get("product_series"),
            row.get("spec_text"),
        ]
        source_text = " | ".join(
            str(part).strip() for part in source_text_parts if pd.notna(part) and str(part).strip()
        )
        if not source_text:
            continue
        candidate_rows.append(
            {
                "row_index": int(row_index),
                "source_text": source_text,
                "group_name": row.get("group_name") if pd.notna(row.get("group_name")) else None,
                "product_name": row.get("product_name") if pd.notna(row.get("product_name")) else None,
                "category": row.get("category") if pd.notna(row.get("category")) else None,
                "brand": row.get("brand") if pd.notna(row.get("brand")) else None,
                "product_series": row.get("product_series") if pd.notna(row.get("product_series")) else None,
                "spec_text": row.get("spec_text") if pd.notna(row.get("spec_text")) else None,
            }
        )

    if not candidate_rows:
        return result

    ai_items: list[dict[str, Any]] = []
    for offset in range(0, len(candidate_rows), batch_size):
        batch = candidate_rows[offset : offset + batch_size]
        extracted_items = extractor(batch, runtime_config)
        if extracted_items:
            ai_items.extend(extracted_items)

    if not ai_items:
        result["local_match_key"] = result.apply(build_product_match_key, axis=1)
        result["local_match_text"] = result.apply(build_match_text, axis=1)
        return result.reset_index(drop=True)

    updates_by_index = {
        item.get("row_index"): item
        for item in ai_items
        if isinstance(item, dict) and item.get("row_index") in result.index
    }

    for row_index, item in updates_by_index.items():
        updated = False
        for field in ["category", "brand", "product_series", "spec_text"]:
            current_value = result.at[row_index, field] if field in result.columns else pd.NA
            if pd.notna(current_value):
                continue
            new_value = _normalize_optional_text(item.get(field))
            if pd.notna(new_value):
                result.at[row_index, field] = new_value
                updated = True

        remarks = _normalize_optional_text(item.get("remarks"))
        if pd.notna(remarks):
            result.at[row_index, "ai_remarks"] = remarks

        if updated:
            result.at[row_index, "ai_enriched"] = True

    result["local_match_key"] = result.apply(build_product_match_key, axis=1)
    result["local_match_text"] = result.apply(build_match_text, axis=1)
    return result.reset_index(drop=True)


def summarize_ai_enrichment(df: pd.DataFrame) -> dict[str, int]:
    if df.empty:
        return {
            "total_count": 0,
            "candidate_count": 0,
            "enriched_count": 0,
            "remarks_only_count": 0,
            "untouched_count": 0,
        }

    ai_enriched_series = df.get("ai_enriched", pd.Series(False, index=df.index)).fillna(False).astype(bool)
    ai_remarks_series = df.get("ai_remarks", pd.Series(pd.NA, index=df.index))
    remarks_mask = ai_remarks_series.notna()
    remarks_only_mask = (~ai_enriched_series) & remarks_mask
    candidate_mask = ai_enriched_series | remarks_mask

    return {
        "total_count": int(len(df)),
        "candidate_count": int(candidate_mask.sum()),
        "enriched_count": int(ai_enriched_series.sum()),
        "remarks_only_count": int(remarks_only_mask.sum()),
        "untouched_count": int((~candidate_mask).sum()),
    }


def build_ai_enrichment_changes(before_df: pd.DataFrame, after_df: pd.DataFrame) -> pd.DataFrame:
    if before_df.empty or after_df.empty:
        return pd.DataFrame()

    before = before_df.copy()
    after = after_df.copy()
    compare_columns = ["category", "brand", "product_series", "spec_text"]
    key_columns = ["local_row_id", "group_name", "product_name", "ai_enriched", "ai_remarks"]

    for column in key_columns + compare_columns:
        if column not in before.columns:
            before[column] = pd.NA
        if column not in after.columns:
            after[column] = pd.NA

    merged = before[key_columns + compare_columns].merge(
        after[key_columns + compare_columns],
        on="local_row_id",
        how="inner",
        suffixes=("_before", "_after"),
    )
    if merged.empty:
        return pd.DataFrame()

    def _display_value(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    change_rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        changed_fields: list[str] = []
        changed_field_labels: list[str] = []
        change_row = {
            "local_row_id": row.get("local_row_id"),
            "group_name": row.get("group_name_after") if pd.notna(row.get("group_name_after")) else row.get("group_name_before"),
            "product_name": row.get("product_name_after") if pd.notna(row.get("product_name_after")) else row.get("product_name_before"),
            "ai_enriched": bool(row.get("ai_enriched_after")) if pd.notna(row.get("ai_enriched_after")) else False,
            "ai_remarks": row.get("ai_remarks_after"),
        }
        for field in compare_columns:
            before_value = _display_value(row.get(f"{field}_before"))
            after_value = _display_value(row.get(f"{field}_after"))
            change_row[f"{field}_before"] = before_value or pd.NA
            change_row[f"{field}_after"] = after_value or pd.NA
            if before_value != after_value:
                changed_fields.append(field)
                changed_field_labels.append(
                    {
                        "category": "品类",
                        "brand": "品牌",
                        "product_series": "系列",
                        "spec_text": "规格",
                    }[field]
                )

        if not changed_fields:
            continue

        change_row["changed_fields"] = "、".join(changed_fields)
        change_row["changed_fields_text"] = "、".join(changed_field_labels)
        change_rows.append(change_row)

    if not change_rows:
        return pd.DataFrame()

    return pd.DataFrame(change_rows).reset_index(drop=True)


def build_local_compare_result(local_df: pd.DataFrame, crawled_df: pd.DataFrame) -> pd.DataFrame:
    standardized_local = standardize_local_compare_file(local_df)
    latest_crawled = summarize_latest_prices(crawled_df)
    if standardized_local.empty:
        return pd.DataFrame()

    if latest_crawled.empty:
        result = standardized_local.copy()
        result["match_status"] = "未匹配"
        result["matched_by"] = "无抓取数据"
        result["current_price"] = pd.NA
        result["price_diff"] = pd.NA
        result["price_diff_rate"] = pd.NA
        result["price_diff_rate_text"] = "暂无"
        return result

    latest_crawled = latest_crawled.copy()
    latest_crawled["crawl_match_key"] = latest_crawled.apply(build_product_match_key, axis=1)
    latest_crawled["crawl_match_text"] = latest_crawled.apply(build_match_text, axis=1)

    key_match_candidates = latest_crawled[latest_crawled["crawl_match_key"].astype(str).str.len() > 0].copy()
    key_match_candidates = key_match_candidates.sort_values("captured_at", ascending=False)
    key_match_candidates = key_match_candidates.drop_duplicates(subset=["crawl_match_key"], keep="first")
    key_match_map = key_match_candidates.set_index("crawl_match_key").to_dict("index")

    compare_rows: list[dict[str, Any]] = []
    for _, row in standardized_local.iterrows():
        local_match_key = row.get("local_match_key") or ""
        matched_record = key_match_map.get(local_match_key)
        matched_by = "匹配键"

        if matched_record is None:
            local_tokens = [token for token in str(row.get("local_match_text") or "").split() if token]
            if local_tokens:
                for _, candidate in latest_crawled.sort_values("captured_at", ascending=False).iterrows():
                    candidate_text = str(candidate.get("crawl_match_text") or "")
                    if all(token in candidate_text for token in local_tokens):
                        matched_record = candidate.to_dict()
                        matched_by = "关键词"
                        break

        compare_row = row.to_dict()
        if matched_record is None:
            compare_row.update(
                {
                    "match_status": "未匹配",
                    "matched_by": "未命中",
                    "product_key": pd.NA,
                    "matched_group_name": pd.NA,
                    "matched_product_name": pd.NA,
                    "matched_site_name": pd.NA,
                    "current_price": pd.NA,
                    "promotion_text": pd.NA,
                    "captured_at": pd.NA,
                    "price_diff": pd.NA,
                    "price_diff_rate": pd.NA,
                    "price_diff_rate_text": "暂无",
                }
            )
            compare_rows.append(compare_row)
            continue

        crawled_price = pd.to_numeric(matched_record.get("current_price"), errors="coerce")
        local_price = pd.to_numeric(row.get("local_price"), errors="coerce")
        price_diff = pd.NA
        price_diff_rate = pd.NA
        price_diff_rate_text = "暂无"
        if pd.notna(local_price) and pd.notna(crawled_price):
            price_diff = float(crawled_price) - float(local_price)
            if float(local_price) != 0:
                price_diff_rate = price_diff / float(local_price)
                price_diff_rate_text = f"{price_diff_rate * 100:+.2f}%"

        compare_row.update(
            {
                "match_status": "已匹配",
                "matched_by": matched_by,
                "product_key": matched_record.get("product_key"),
                "matched_group_name": matched_record.get("group_name"),
                "matched_product_name": matched_record.get("product_name"),
                "matched_site_name": matched_record.get("site_name"),
                "current_price": crawled_price,
                "promotion_text": matched_record.get("promotion_text"),
                "captured_at": matched_record.get("captured_at"),
                "price_diff": price_diff,
                "price_diff_rate": price_diff_rate,
                "price_diff_rate_text": price_diff_rate_text,
            }
        )
        compare_rows.append(compare_row)

    result = pd.DataFrame(compare_rows)
    if result.empty:
        return result

    result["price_relation"] = result["price_diff"].apply(
        lambda value: "暂无"
        if pd.isna(value)
        else ("抓取价更高" if value > 0 else ("抓取价更低" if value < 0 else "价格一致"))
    )
    return result.reset_index(drop=True)


def summarize_local_compare_result(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "total_count": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "higher_count": 0,
            "lower_count": 0,
            "same_count": 0,
        }

    matched_mask = df["match_status"].eq("已匹配") if "match_status" in df.columns else pd.Series(False, index=df.index)
    relation_series = df.get("price_relation", pd.Series(index=df.index, dtype=object)).fillna("暂无")
    return {
        "total_count": int(len(df)),
        "matched_count": int(matched_mask.sum()),
        "unmatched_count": int((~matched_mask).sum()),
        "higher_count": int((relation_series == "抓取价更高").sum()),
        "lower_count": int((relation_series == "抓取价更低").sum()),
        "same_count": int((relation_series == "价格一致").sum()),
    }


def prepare_history(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()
    result["captured_at"] = pd.to_datetime(result["captured_at"])
    return result.sort_values("captured_at")


def _first_non_empty_text(row: pd.Series, columns: list[str], default: str = "未命名商品") -> str:
    for column in columns:
        value = row.get(column)
        if pd.notna(value):
            text = str(value).strip()
            if text:
                return text
    return default


def _join_non_empty_series_columns(frame: pd.DataFrame, columns: list[str], separator: str) -> pd.Series:
    if frame.empty or not columns:
        return pd.Series("", index=frame.index, dtype="object")

    joined = pd.Series("", index=frame.index, dtype="object")
    has_value = pd.Series(False, index=frame.index)
    for column in columns:
        values = frame[column].fillna("").astype(str).str.strip()
        mask = values.ne("")
        prefix = joined.where(~has_value, joined + separator)
        joined = joined.where(~mask, prefix + values)
        has_value = has_value | mask
    return joined


def _build_price_identity_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    result = df.copy()
    text_columns = ["compare_key", "group_name", "product_name", "brand", "product_series", "spec_text"]
    for column in text_columns:
        if column in result.columns:
            result[column] = result[column].fillna("").astype(str).str.strip()
        else:
            result[column] = ""

    category_series = result["category"].fillna("").astype(str).str.strip() if "category" in result.columns else pd.Series("", index=result.index)
    primary_name_series = result["product_name"].where(result["product_name"].ne(""), result["group_name"]).fillna("")
    fallback_label_series = primary_name_series.where(primary_name_series.ne(""), "未命名商品")

    normalized_parts = pd.DataFrame(
        {
            "primary_name": _normalize_compare_series(primary_name_series),
            "category": _normalize_compare_series(category_series),
            "brand": _normalize_compare_series(result["brand"]),
            "product_series": _normalize_compare_series(result["product_series"]),
            "spec_text": _normalize_compare_series(result["spec_text"]),
        },
        index=result.index,
    ).replace("", pd.NA)

    key_series = _join_non_empty_series_columns(
        normalized_parts,
        ["primary_name", "category", "brand", "product_series", "spec_text"],
        "|",
    )
    compare_key_series = _normalize_compare_series(result["compare_key"])
    fallback_key_series = _join_non_empty_series_columns(
        pd.DataFrame(
            {
                "group_name": result["group_name"],
                "product_name": result["product_name"],
                "brand": result["brand"],
                "product_series": result["product_series"],
                "spec_text": result["spec_text"],
            },
            index=result.index,
        ),
        ["group_name", "product_name", "brand", "product_series", "spec_text"],
        " | ",
    )

    label_extras = _join_non_empty_series_columns(
        pd.DataFrame(
            {
                "brand": result["brand"],
                "product_series": result["product_series"],
                "spec_text": result["spec_text"],
            },
            index=result.index,
        ),
        ["brand", "product_series", "spec_text"],
        " | ",
    )
    label_series = fallback_label_series.copy()
    extras_mask = label_extras.str.strip().ne("")
    label_series.loc[extras_mask] = label_series.loc[extras_mask] + " | " + label_extras.loc[extras_mask].astype(str)

    result["price_identity_key"] = key_series.where(key_series.ne(""), compare_key_series)
    result["price_identity_key"] = result["price_identity_key"].where(result["price_identity_key"].ne(""), fallback_key_series)
    result["price_identity_label"] = label_series
    return result

def _filter_non_product_identity_rows(
    df: pd.DataFrame,
    *,
    text_columns: list[str],
    unit_columns: list[str] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    result = df.copy()
    available_text_columns = [column for column in text_columns if column in result.columns]
    if available_text_columns:
        row_text = result[available_text_columns].fillna("").astype(str).agg(" ".join, axis=1)
        result = result[
            ~row_text.str.startswith("/")
            & ~row_text.str.contains(NON_PRODUCT_LABEL_PATTERN, na=False)
            & ~row_text.str.contains(NON_FOOD_LABEL_PATTERN, na=False)
        ].copy()

    available_unit_columns = [column for column in (unit_columns or []) if column in result.columns]
    if available_unit_columns:
        unit_text = result[available_unit_columns].fillna("").astype(str).agg(" ".join, axis=1)
        normalized_unit_text = unit_text.str.strip()
        result = result[
            ~normalized_unit_text.isin(NON_PRODUCT_UNIT_TEXTS)
            & ~normalized_unit_text.isin(NON_FOOD_UNIT_TEXTS)
        ].copy()

    return result



def summarize_latest_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    latest = df.sort_values("captured_at").groupby("product_key", as_index=False).tail(1)
    latest = latest.sort_values(["group_name", "current_price"], na_position="last")
    return latest.reset_index(drop=True)


def summarize_latest_unit_prices(df: pd.DataFrame) -> pd.DataFrame:
    latest = summarize_latest_prices(df)
    if latest.empty or "unit_price" not in latest.columns:
        return pd.DataFrame()
    latest = latest.dropna(subset=["unit_price"])
    return latest.sort_values(["category", "unit_price"], na_position="last").reset_index(drop=True)


def search_latest_records(df: pd.DataFrame, keyword: str | None = None, mode: str = "price") -> pd.DataFrame:
    latest = summarize_latest_unit_prices(df) if mode == "unit_price" else summarize_latest_prices(df)
    if latest.empty:
        return latest

    normalized_keyword = (keyword or "").strip().lower()
    if not normalized_keyword:
        return latest.reset_index(drop=True)

    search_columns = [
        column
        for column in ["group_name", "product_name", "category", "brand", "product_series", "spec_text", "site_name"]
        if column in latest.columns
    ]
    if not search_columns:
        return latest.reset_index(drop=True)

    keywords = [item for item in normalized_keyword.split() if item]
    if not keywords:
        return latest.reset_index(drop=True)

    search_text = latest[search_columns].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    mask = pd.Series(True, index=latest.index)
    for item in keywords:
        mask &= search_text.str.contains(item, regex=False)
    return latest[mask].reset_index(drop=True)


def append_change_rate(df: pd.DataFrame, history_df: pd.DataFrame | None = None, mode: str = "price") -> pd.DataFrame:
    if df.empty or "product_key" not in df.columns:
        return df.copy()

    result = df.copy()
    price_col = "unit_price" if mode == "unit_price" and "unit_price" in result.columns else "current_price"
    history = (history_df if history_df is not None else df).copy()
    if "captured_at" not in history.columns or price_col not in history.columns:
        result["change_rate"] = pd.NA
        return result

    history["captured_at"] = pd.to_datetime(history["captured_at"])
    history = history.sort_values(["product_key", "captured_at"])
    change_rows = []
    for product_key, group in history.groupby("product_key", dropna=False):
        values = group[price_col].dropna().tolist()
        if len(values) >= 2 and values[-2] not in (None, 0):
            change_rate = (values[-1] - values[-2]) / values[-2]
        else:
            change_rate = pd.NA
        change_rows.append({"product_key": product_key, "change_rate": change_rate})

    change_df = pd.DataFrame(change_rows)
    result = result.merge(change_df, on="product_key", how="left")
    result["change_rate_text"] = result["change_rate"].apply(
        lambda value: "暂无"
        if pd.isna(value)
        else f"{value * 100:+.2f}%"
    )
    return result


def build_compare_selection_label(row: pd.Series, mode: str = "price") -> str:
    price_col = "unit_price" if mode == "unit_price" and "unit_price" in row.index else "current_price"
    price_label = "单位价" if price_col == "unit_price" else "价格"
    price_value = row.get(price_col)
    price_text = "暂无" if pd.isna(price_value) else f"{float(price_value):.2f}"
    captured_at = row.get("captured_at")
    captured_text = "未知时间" if pd.isna(captured_at) else str(captured_at)

    return " | ".join(
        [
            str(row.get("group_name") or row.get("product_name") or "未命名商品"),
            str(row.get("site_name") or "未知平台"),
            str(row.get("brand") or "未指定品牌"),
            str(row.get("spec_text") or "未指定规格"),
            f"{price_label}:{price_text}",
            captured_text,
        ]
    )


def build_favorite_compare_selection_labels(
    df: pd.DataFrame,
    favorite_groups: list[str] | None = None,
    mode: str = "price",
) -> list[str]:
    if df.empty or not favorite_groups or "group_name" not in df.columns:
        return []

    labels = []
    favorite_set = set(favorite_groups)
    for _, row in df.iterrows():
        if row.get("group_name") in favorite_set and pd.notna(row.get("product_key")):
            labels.append(build_compare_selection_label(row, mode=mode))
    return labels


def sort_search_results(
    df: pd.DataFrame,
    mode: str = "price",
    sort_by: str = "默认排序",
    history_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.copy()
    price_col = "unit_price" if mode == "unit_price" and "unit_price" in result.columns else "current_price"

    if sort_by == "最低价优先" and price_col in result.columns:
        return result.sort_values(price_col, ascending=True, na_position="last").reset_index(drop=True)

    if sort_by == "最高价优先" and price_col in result.columns:
        return result.sort_values(price_col, ascending=False, na_position="last").reset_index(drop=True)

    if sort_by == "最新抓取优先" and "captured_at" in result.columns:
        result["captured_at"] = pd.to_datetime(result["captured_at"])
        return result.sort_values("captured_at", ascending=False, na_position="last").reset_index(drop=True)

    if sort_by == "涨跌幅优先" and price_col in result.columns and "product_key" in result.columns:
        history = (history_df if history_df is not None else df).copy()
        result = append_change_rate(result, history_df=history, mode=mode)
        result["change_rate_abs"] = result["change_rate"].abs()
        return result.sort_values(["change_rate_abs", price_col], ascending=[False, True], na_position="last").reset_index(drop=True)

    return result.reset_index(drop=True)


def prioritize_favorite_groups(df: pd.DataFrame, favorite_groups: list[str] | None = None) -> pd.DataFrame:
    if df.empty or not favorite_groups or "group_name" not in df.columns:
        return df.copy()

    result = df.copy()
    result["is_favorite_group"] = result["group_name"].isin(favorite_groups)
    order_columns = ["is_favorite_group"]
    ascending = [False]

    if "captured_at" in result.columns:
        result["captured_at"] = pd.to_datetime(result["captured_at"])
        order_columns.append("captured_at")
        ascending.append(False)
    elif "current_price" in result.columns:
        order_columns.append("current_price")
        ascending.append(True)
    elif "average_price" in result.columns:
        order_columns.append("average_price")
        ascending.append(True)
    elif "average_unit_price" in result.columns:
        order_columns.append("average_unit_price")
        ascending.append(True)

    return result.sort_values(order_columns, ascending=ascending, na_position="last").reset_index(drop=True)


def compute_group_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = _build_price_identity_frame(prepare_history(df))
    group_columns = [
        "price_identity_key",
        "price_identity_label",
        "group_name",
        "brand",
        "product_series",
        "spec_text",
        "site_name",
    ]
    grouped = base.groupby(group_columns, dropna=False)
    metrics = grouped["current_price"].agg(["min", "max", "mean", "count"]).reset_index()
    metrics["volatility"] = ((metrics["max"] - metrics["min"]) / metrics["mean"]).round(4)

    trend_rows = []
    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        subset = group[["captured_at", "current_price"]].dropna().tail(3)
        trend_rows.append((*group_key, _trend_from_subset(subset, "current_price")))
    trend_df = pd.DataFrame(trend_rows, columns=[*group_columns, "trend"])
    metrics = metrics.merge(trend_df, on=group_columns, how="left")

    return metrics.rename(
        columns={
            "price_identity_label": "product_name",
            "min": "historical_min_price",
            "max": "historical_max_price",
            "mean": "average_price",
            "count": "record_count",
        }
    )


def compute_cross_site_price_summary(
    df: pd.DataFrame,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    latest_source_df = df.copy()
    latest_source_df["_cross_site_source_key"] = latest_source_df.apply(
        lambda row: "|".join(
            str(row.get(column) or "").strip()
            for column in ["product_key", "source_url", "site_name", "market_name"]
        ),
        axis=1,
    )
    latest_source_df = (
        latest_source_df.sort_values("captured_at")
        .groupby("_cross_site_source_key", as_index=False, dropna=False)
        .tail(1)
        .drop(columns=["_cross_site_source_key"], errors="ignore")
    )
    latest = _build_price_identity_frame(latest_source_df).dropna(subset=["current_price"])
    latest = _filter_non_product_identity_rows(
        latest,
        text_columns=[
            "price_identity_key",
            "price_identity_label",
            "group_name",
            "product_name",
            "category",
            "liancai_top_category",
            "liancai_subcategory",
        ],
        unit_columns=["spec_text"],
    )
    if latest.empty:
        return pd.DataFrame()

    latest = apply_location_priority(
        latest.copy(),
        selected_province=selected_province,
        selected_city=selected_city,
    )
    latest["source_name"] = latest.apply(
        lambda row: _extract_source_group_name(row.get("site_name"), row.get("source_url")),
        axis=1,
    )
    if "image_url" not in latest.columns:
        latest["image_url"] = ""
    latest["image_url"] = latest["image_url"].fillna("").astype(str).str.strip()
    latest["source_display_name"] = latest.apply(
        lambda row: _extract_source_display_name(
            row.get("site_name"),
            row.get("group_name"),
            row.get("source_url"),
        ),
        axis=1,
    )
    normalized_price_meta = latest.apply(
        lambda row: _normalize_cross_site_price(row.get("current_price"), row.get("spec_text")),
        axis=1,
    )
    latest["comparable_price"] = normalized_price_meta.apply(lambda item: item[0])
    latest["normalized_spec_text"] = normalized_price_meta.apply(lambda item: item[1])
    latest["price_unit_basis"] = latest["normalized_spec_text"].apply(format_price_unit_basis)
    latest = latest.dropna(subset=["comparable_price"]).copy()
    if latest.empty:
        return pd.DataFrame()

    # Cross-source comparison must group by normalized sellable identity, not the
    # earlier local price identity that may still include raw unit/category text.
    latest = latest.drop(columns=["price_identity_key", "price_identity_label"], errors="ignore")
    latest = build_cross_site_identity_frame(latest)
    selector_image_lookup = _build_selector_image_lookup(latest)

    identity_group_columns = [
        "cross_site_identity_key",
        "cross_site_identity_label",
        "brand",
        "product_series",
        "normalized_spec_text",
    ]
    source_level = (
        latest.groupby(identity_group_columns + ["source_name"], dropna=False)
        .agg(
            group_name=("group_name", "first"),
            comparable_price=("comparable_price", "mean"),
            source_sample_count=("site_name", "nunique"),
            # Keep the raw latest quote count separate from source coverage; the
            # product selector displays this as the number of quotation records.
            price_observation_count=("comparable_price", "count"),
            latest_captured_at=("captured_at", "max"),
        )
        .reset_index()
    )
    if source_level.empty:
        return pd.DataFrame()

    summary = (
        source_level.groupby(identity_group_columns, dropna=False)
        .agg(
            group_name=("group_name", "first"),
            lowest_price=("comparable_price", "min"),
            highest_price=("comparable_price", "max"),
            average_price=("comparable_price", "mean"),
            site_count=("source_name", "nunique"),
            price_observation_count=("price_observation_count", "sum"),
            source_names=("source_name", lambda values: "、".join(sorted({
                str(value).strip() for value in values if pd.notna(value) and str(value).strip()
            }))),
            latest_captured_at=("latest_captured_at", "max"),
        )
        .reset_index()
    )

    source_display_summary = (
        latest.groupby("cross_site_identity_key", dropna=False)
        .agg(
            source_display_names=("source_display_name", lambda values: "、".join(sorted({
                str(value).strip() for value in values if pd.notna(value) and str(value).strip()
            }))),
            captured_dates=("captured_at", lambda values: "、".join(sorted({
                str(value).strip()[:10] for value in values if pd.notna(value) and str(value).strip()
            }, reverse=True))),
        )
        .reset_index()
    )
    summary = summary.merge(source_display_summary, on="cross_site_identity_key", how="left")

    liancai_columns = [column for column in ["source_name", "liancai_top_category", "liancai_subcategory", "image_url"] if column in latest.columns]
    if liancai_columns:
        liancai_meta_rows = []
        representative_rows = (
            latest.sort_values(
                ["cross_site_identity_key", "location_priority", "comparable_price", "source_display_name"],
                ascending=[True, True, True, True],
                na_position="last",
            )
            .groupby("cross_site_identity_key", as_index=False, dropna=False)
            .head(1)
            .set_index("cross_site_identity_key", drop=False)
        )
        for identity_key, group in latest.groupby("cross_site_identity_key", dropna=False):
            source_names = [str(value).strip() for value in group.get("source_name", pd.Series(dtype="object")).dropna() if str(value).strip()]
            liancai_group = group[group.get("source_name", pd.Series("", index=group.index)).fillna("").astype(str).eq("莲菜网")]
            metadata_group = liancai_group if not liancai_group.empty else group
            representative = representative_rows.loc[identity_key] if identity_key in representative_rows.index else metadata_group.iloc[0]
            liancai_meta_rows.append(
                {
                    "cross_site_identity_key": identity_key,
                    "source_name": "莲菜网" if "莲菜网" in source_names else representative.get("source_name"),
                    "liancai_top_category": _first_non_empty(metadata_group, "liancai_top_category"),
                    "liancai_subcategory": _first_non_empty(metadata_group, "liancai_subcategory"),
                    "image_url": _build_selector_image_url(group, selector_image_lookup),
                }
            )
        liancai_summary = pd.DataFrame(liancai_meta_rows)[["cross_site_identity_key", *liancai_columns]]
        summary = summary.merge(liancai_summary, on="cross_site_identity_key", how="left")

    lowest_site = (
        latest.sort_values(["cross_site_identity_key", "location_priority", "comparable_price", "source_display_name"], ascending=[True, True, True, True])
        .groupby("cross_site_identity_key", as_index=False)
        .head(1)[["cross_site_identity_key", "source_display_name"]]
        .rename(columns={"source_display_name": "lowest_price_site"})
    )
    highest_site = (
        latest.sort_values(["cross_site_identity_key", "comparable_price", "source_display_name"], ascending=[True, False, True])
        .groupby("cross_site_identity_key", as_index=False)
        .head(1)[["cross_site_identity_key", "source_display_name"]]
        .rename(columns={"source_display_name": "highest_price_site"})
    )

    summary = summary.merge(lowest_site, on="cross_site_identity_key", how="left").merge(highest_site, on="cross_site_identity_key", how="left")
    region_columns = [column for column in ["province", "city", "market_name", "region_label"] if column in latest.columns]
    if region_columns:
        region_summary = (
            latest.sort_values(
                ["cross_site_identity_key", "location_priority", "comparable_price", "source_display_name"],
                ascending=[True, True, True, True],
                na_position="last",
            )
            .groupby("cross_site_identity_key", as_index=False, dropna=False)
            .head(1)[["cross_site_identity_key", *region_columns]]
        )
        summary = summary.merge(region_summary, on="cross_site_identity_key", how="left")
    location_priority_summary = latest.groupby("cross_site_identity_key", dropna=False)["location_priority"].min().reset_index()
    summary = summary.merge(location_priority_summary, on="cross_site_identity_key", how="left")
    summary = summary.rename(
        columns={
            "cross_site_identity_key": "price_identity_key",
            "cross_site_identity_label": "product_name",
            "normalized_spec_text": "spec_text",
        }
    )
    summary["market_count"] = summary["site_count"]
    summary["price_unit_basis"] = summary["spec_text"].apply(format_price_unit_basis)
    summary["average_price"] = summary["average_price"].round(2)
    return summary.sort_values(["location_priority", "lowest_price", "average_price", "product_name"], na_position="last").reset_index(drop=True)


def compute_unit_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "unit_price" not in df.columns:
        return pd.DataFrame()

    base = prepare_history(df).dropna(subset=["unit_price"])
    if base.empty:
        return pd.DataFrame()

    group_cols = ["category", "brand", "product_series", "spec_text"]
    metrics = (
        base.groupby(group_cols, dropna=False)["unit_price"]
        .agg(["min", "max", "mean", "count"])
        .reset_index()
    )
    metrics["volatility"] = ((metrics["max"] - metrics["min"]) / metrics["mean"]).round(4)
    metrics["trend"] = metrics.apply(
        lambda row: detect_unit_trend(base, row["category"], row["brand"], row["product_series"], row["spec_text"]),
        axis=1,
    )
    return metrics.rename(
        columns={
            "min": "historical_min_unit_price",
            "max": "historical_max_unit_price",
            "mean": "average_unit_price",
            "count": "record_count",
        }
    )


def detect_trend(
    df: pd.DataFrame,
    group_name: str,
    site_name: str,
    group_col: str = "group_name",
    value_col: str = "current_price",
) -> str:
    subset = (
        prepare_history(df)
        .loc[
            lambda item: (item[group_col] == group_name) & (item["site_name"] == site_name),
            ["captured_at", value_col],
        ]
        .dropna()
        .tail(3)
    )
    return _trend_from_subset(subset, value_col)


def detect_unit_trend(
    df: pd.DataFrame,
    category: str | None,
    brand: str | None,
    product_series: str | None,
    spec_text: str | None,
) -> str:
    subset = (
        prepare_history(df)
        .loc[
            lambda item: (item["category"] == category)
            & (item["brand"] == brand)
            & (item["product_series"] == product_series)
            & (item["spec_text"] == spec_text),
            ["captured_at", "unit_price"],
        ]
        .dropna()
        .tail(3)
    )
    return _trend_from_subset(subset, "unit_price")


def _trend_from_subset(subset: pd.DataFrame, value_col: str) -> str:
    if len(subset) < 2:
        return "数据不足"

    values = subset[value_col].tolist()
    if all(a < b for a, b in zip(values, values[1:])):
        return "上涨"
    if all(a > b for a, b in zip(values, values[1:])):
        return "下降"

    mean_price = subset[value_col].mean()
    if mean_price and (subset[value_col].max() - subset[value_col].min()) / mean_price <= TREND_STABLE_THRESHOLD:
        return "平稳"
    return "波动"


def filter_groups(df: pd.DataFrame, group_names: list[str] | None = None) -> pd.DataFrame:
    if df.empty or not group_names or "group_name" not in df.columns:
        return df.copy()
    return df[df["group_name"].isin(group_names)].copy()


def filter_by_location(
    df: pd.DataFrame,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    filtered = enrich_location_fields(df)
    if selected_province and "province" in filtered.columns:
        filtered = filtered[filtered["province"] == selected_province]
    if selected_city and "city" in filtered.columns:
        filtered = filtered[filtered["city"] == selected_city]
    return filtered


def build_location_priority(
    row: pd.Series,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> tuple[int, int]:
    province = _normalize_location_display_name(row.get("province"))
    city = _normalize_location_display_name(row.get("city"))
    if selected_city and city == selected_city:
        return (0, 0)
    if selected_province and province == selected_province:
        return (1, 0)
    if city or province:
        return (2, 0)
    return (3, 0)


def apply_location_priority(
    df: pd.DataFrame,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    prioritized = enrich_location_fields(df.copy())
    prioritized["location_priority"] = prioritized.apply(
        lambda row: build_location_priority(
            row,
            selected_province=selected_province,
            selected_city=selected_city,
        ),
        axis=1,
    )
    return prioritized


def get_location_options(df: pd.DataFrame) -> tuple[list[str], list[str], dict[str, list[str]]]:
    if df.empty:
        return [], [], {}
    enriched = enrich_location_fields(df)
    provinces = sorted(enriched.get("province", pd.Series(dtype=object)).dropna().astype(str).unique().tolist())
    cities = sorted(enriched.get("city", pd.Series(dtype=object)).dropna().astype(str).unique().tolist())
    province_city_map: dict[str, list[str]] = {}
    if "province" in enriched.columns and "city" in enriched.columns:
        valid_rows = enriched.dropna(subset=["province", "city"]).copy()
        for province, group_df in valid_rows.groupby("province", dropna=True):
            province_city_map[str(province)] = sorted(group_df["city"].dropna().astype(str).unique().tolist())
    return provinces, cities, province_city_map


def _first_non_empty(group: pd.DataFrame, column: str) -> str:
    if column not in group.columns:
        return ""
    values = group[column].dropna().astype(str).str.strip()
    values = values[values.ne("")]
    return values.iloc[0] if not values.empty else ""


def _build_selector_source_category(group: pd.DataFrame) -> str:
    for column in ("liancai_top_category", "category"):
        if column not in group.columns:
            continue
        values = group[column].dropna().astype(str).str.strip()
        values = values[values.ne("")]
        if not values.empty:
            return values.iloc[0]
    return ""


def _build_selector_liancai_subcategory(group: pd.DataFrame) -> str:
    if "liancai_subcategory" not in group.columns:
        return ""
    values = group["liancai_subcategory"].dropna().astype(str).str.strip()
    values = values[values.ne("")]
    return values.iloc[0] if not values.empty else ""


def _simplify_selector_image_label(value: Any) -> str:
    text = "" if value is None or pd.isna(value) else str(value)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[|｜].*$", "", text)
    text = re.sub(r"净菜\d+斤", "", text)
    text = re.sub(r"\d+斤", "", text)
    text = re.sub(r"原包|整包|毛菜|本地|精品|普通|一级|二级|三级|红皮|黄皮|黄心|黑皮|吊瓜|地瓜|圆片|片|条|丝|丁|段", "", text)
    return text.strip().lower()


def _build_selector_image_lookup(df: pd.DataFrame) -> dict[str, str]:
    if df.empty or "image_url" not in df.columns:
        return {}
    source_series = df.get("source_name", pd.Series("", index=df.index)).fillna("").astype(str)
    liancai_rows = df[source_series.eq("莲菜网")].copy()
    if liancai_rows.empty:
        return {}
    liancai_rows["image_url"] = liancai_rows["image_url"].fillna("").astype(str).str.strip()
    liancai_rows = liancai_rows[liancai_rows["image_url"].ne("")]
    if liancai_rows.empty:
        return {}
    lookup: dict[str, str] = {}
    label_columns = [
        "cross_site_identity_label",
        "price_identity_label",
        "product_name",
    ]
    for _, row in liancai_rows.iterrows():
        image_url = str(row.get("image_url") or "").strip()
        if not image_url:
            continue
        for column in label_columns:
            key = _simplify_selector_image_label(row.get(column))
            if key and key not in lookup:
                lookup[key] = image_url
    return lookup


def _build_selector_image_url(group: pd.DataFrame, image_lookup: dict[str, str] | None = None) -> str | None:
    liancai_mask = group.get("source_name", pd.Series("", index=group.index)).fillna("").astype(str).eq("莲菜网")
    if not liancai_mask.any():
        if image_lookup:
            labels = [
                _simplify_selector_image_label(group.get("cross_site_identity_label", pd.Series(dtype="object")).iloc[0])
                if "cross_site_identity_label" in group.columns and not group.empty else "",
                _simplify_selector_image_label(group.get("price_identity_label", pd.Series(dtype="object")).iloc[0])
                if "price_identity_label" in group.columns and not group.empty else "",
                _simplify_selector_image_label(group.get("product_name", pd.Series(dtype="object")).iloc[0])
                if "product_name" in group.columns and not group.empty else "",
            ]
            for label in labels:
                if not label:
                    continue
                if label in image_lookup:
                    return image_lookup[label]
                for candidate, image_url in image_lookup.items():
                    if candidate and (candidate in label or label in candidate):
                        return image_url
        return None
    if "image_url" in group.columns:
        values = group.loc[liancai_mask, "image_url"].dropna().astype(str).str.strip()
        values = values[values.ne("")]
        if not values.empty:
            return values.iloc[0]
    return None


def build_single_product_selector_options(
    df: pd.DataFrame,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> pd.DataFrame:
    latest = summarize_latest_prices(df)
    if latest.empty:
        return pd.DataFrame()
    latest = build_cross_site_identity_frame(latest)
    latest = _filter_non_product_identity_rows(
        latest,
        text_columns=[
            "cross_site_identity_key",
            "cross_site_identity_label",
            "group_name",
            "product_name",
            "category",
            "liancai_top_category",
            "liancai_subcategory",
        ],
        unit_columns=["spec_text", "normalized_spec_text"],
    )
    if latest.empty:
        return pd.DataFrame()
    latest = _prepare_trend_display_rows(latest)
    latest = apply_location_priority(
        latest,
        selected_province=selected_province,
        selected_city=selected_city,
    )
    selector_df = (
        latest.groupby(["cross_site_identity_key", "cross_site_identity_label"], dropna=False)
        .agg(
            latest_captured_at=("captured_at", "max"),
            site_count=("trend_series_key", "nunique"),
            price_observation_count=("current_price", "count"),
            best_location_priority=("location_priority", "min"),
        )
        .reset_index()
        .rename(
            columns={
                "cross_site_identity_key": "price_identity_key",
                "cross_site_identity_label": "price_identity_label",
            }
        )
    )
    selector_meta = []
    for (identity_key, _identity_label), group in latest.groupby(
        ["cross_site_identity_key", "cross_site_identity_label"],
        dropna=False,
    ):
        source_names = [str(value).strip() for value in group.get("source_name", pd.Series(dtype="object")).dropna() if str(value).strip()]
        selector_meta.append(
            {
                "price_identity_key": identity_key,
                "source_name": "莲菜网" if "莲菜网" in source_names else (source_names[0] if source_names else ""),
                "source_category": _build_selector_source_category(group),
                "liancai_subcategory": _build_selector_liancai_subcategory(group),
                "image_url": _build_selector_image_url(group),
            }
        )
    if selector_meta:
        selector_df = selector_df.merge(pd.DataFrame(selector_meta), on="price_identity_key", how="left")
    selector_df["latest_captured_at"] = pd.to_datetime(selector_df["latest_captured_at"], errors="coerce")
    selector_df = selector_df[
        (selector_df["price_observation_count"] > 0)
        & selector_df["price_identity_key"].fillna("").astype(str).str.strip().ne("")
        & selector_df["price_identity_label"].fillna("").astype(str).str.strip().ne("")
        & selector_df["site_count"].fillna(0).astype(float).gt(0)
    ].copy()
    option_text = (
        selector_df["price_identity_key"].fillna("").astype(str)
        + " "
        + selector_df["price_identity_label"].fillna("").astype(str)
    )
    selector_df = selector_df[
        ~option_text.str.startswith("/")
        & ~option_text.str.contains(r"影响|调整|建议|采购|预警|趋势|来源动态|老板|驾驶舱|复制|copy", case=False, regex=True)
    ].copy()
    selector_df = (
        selector_df.sort_values(["best_location_priority", "latest_captured_at", "price_identity_label"], ascending=[True, False, True])
        .reset_index(drop=True)
    )
    return selector_df[[
        "price_identity_key",
        "price_identity_label",
        "site_count",
        "price_observation_count",
        "latest_captured_at",
        "source_name",
        "source_category",
        "liancai_subcategory",
        "image_url",
    ]]


def _filter_single_product_history(df: pd.DataFrame, identity_key: str) -> pd.DataFrame:
    if df.empty or not identity_key:
        return pd.DataFrame()

    base = prepare_history(df)
    if "price_identity_key" not in base.columns or "price_identity_label" not in base.columns:
        base = _build_price_identity_frame(base)

    cross_site_base = build_cross_site_identity_frame(base)
    alias_candidates = {str(identity_key).strip()}
    if "|" in str(identity_key):
        alias_candidates.add(str(identity_key).split("|", 1)[0].strip())
    compact_aliases = {
        re.sub(r"[\s*·•/]+", "", alias).strip()
        for alias in alias_candidates
        if str(alias).strip()
    }
    cross_identity_series = cross_site_base["cross_site_identity_key"].fillna("").astype(str).str.strip()
    compact_cross_identity_series = cross_identity_series.str.replace(r"[\s*·•/]+", "", regex=True).str.strip()
    price_identity_series = cross_site_base["price_identity_key"].fillna("").astype(str).str.strip()
    compact_price_identity_series = price_identity_series.str.replace(r"[\s*·•/]+", "", regex=True).str.strip()
    cross_site_matches = cross_site_base[
        (
            cross_identity_series.isin(alias_candidates)
            | compact_cross_identity_series.isin(compact_aliases)
            | price_identity_series.isin(alias_candidates)
            | compact_price_identity_series.isin(compact_aliases)
        )
        & cross_site_base["current_price"].notna()
    ].copy()
    if not cross_site_matches.empty:
        label_series = cross_site_matches.get("price_identity_label", pd.Series(dtype="object")).fillna("").astype(str).str.strip()
        label_candidates = {value for value in label_series.tolist() if value}
        compact_label_candidates = {
            re.sub(r"[\s*·•/]+", "", value).strip()
            for value in label_candidates
            if value
        }
        if label_candidates:
            base_label_series = cross_site_base.get("price_identity_label", pd.Series(index=cross_site_base.index, dtype="object")).fillna("").astype(str).str.strip()
            compact_base_label_series = base_label_series.str.replace(r"[\s*·•/]+", "", regex=True).str.strip()
            label_matches = cross_site_base[
                (base_label_series.isin(label_candidates) | compact_base_label_series.isin(compact_label_candidates))
                & cross_site_base["current_price"].notna()
            ].copy()
            cross_site_matches = pd.concat([cross_site_matches, label_matches], ignore_index=True, sort=False).drop_duplicates()
        return cross_site_matches

    base_price_identity_series = base["price_identity_key"].fillna("").astype(str).str.strip()
    compact_base_price_identity_series = base_price_identity_series.str.replace(r"[\s*·•/]+", "", regex=True).str.strip()
    return base[
        (base_price_identity_series.isin(alias_candidates) | compact_base_price_identity_series.isin(compact_aliases))
        & base["current_price"].notna()
    ].copy()


def _build_single_product_latest_snapshot(
    df: pd.DataFrame,
    identity_key: str,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> pd.DataFrame:
    base = _filter_single_product_history(df, identity_key)
    if base.empty:
        return pd.DataFrame()

    base["captured_at"] = pd.to_datetime(base["captured_at"], errors="coerce")
    base = base.dropna(subset=["captured_at"])
    if base.empty:
        return pd.DataFrame()

    base = _prepare_trend_display_rows(base)
    if base.empty:
        return pd.DataFrame()
    base = apply_location_priority(
        base,
        selected_province=selected_province,
        selected_city=selected_city,
    )

    base = base.sort_values(
        ["location_priority", "trend_series_key", "captured_at"],
        ascending=[True, True, True],
        na_position="last",
    )
    return (
        base.groupby("trend_series_key", as_index=False, dropna=False)
        .tail(1)
        .reset_index(drop=True)
    )


def compute_single_product_summary(
    df: pd.DataFrame,
    identity_key: str,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> dict[str, Any]:
    latest = _build_single_product_latest_snapshot(
        df,
        identity_key,
        selected_province=selected_province,
        selected_city=selected_city,
    )
    if latest.empty:
        return {}
    source_priority = {
        "主价格源": 0,
        "官方参考源": 1,
        "本地市场源": 2,
        "第三方参考源": 3,
    }
    latest = latest.copy()
    latest["summary_source_rank"] = latest.get("source_tier", pd.Series(index=latest.index, dtype="object")).map(source_priority).fillna(9)
    lowest_row = latest.sort_values(
        ["location_priority", "current_price", "summary_source_rank", "trend_series_name"],
        ascending=[True, True, True, True],
    ).iloc[0]
    highest_row = latest.sort_values(
        ["location_priority", "current_price", "summary_source_rank", "trend_series_name"],
        ascending=[True, False, True, True],
    ).iloc[0]
    latest_time = pd.to_datetime(latest["captured_at"], errors="coerce").max()
    return {
        "price_identity_key": identity_key,
        "product_name": lowest_row.get("price_identity_label"),
        "current_lowest_price": round(float(lowest_row["current_price"]), 2),
        "current_lowest_site": lowest_row.get("trend_series_name") or lowest_row.get("site_name"),
        "current_lowest_source_name": lowest_row.get("source_name"),
        "current_lowest_source_tier": lowest_row.get("source_tier"),
        "current_highest_price": round(float(highest_row["current_price"]), 2),
        "current_highest_site": highest_row.get("trend_series_name") or highest_row.get("site_name"),
        "current_highest_source_name": highest_row.get("source_name"),
        "current_highest_source_tier": highest_row.get("source_tier"),
        "average_price": round(float(latest["current_price"].mean()), 2),
        "latest_captured_at": latest_time.strftime("%Y-%m-%d") if pd.notna(latest_time) else "暂无",
        "site_count": int(latest["trend_series_key"].dropna().nunique()),
    }


def build_cross_market_product_trend(
    df: pd.DataFrame,
    identity_key: str,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> pd.DataFrame:
    base = _filter_single_product_history(df, identity_key)
    if base.empty:
        return pd.DataFrame()
    base["captured_at"] = pd.to_datetime(base["captured_at"], errors="coerce")
    base = _prepare_trend_display_rows(base)
    base = apply_location_priority(
        base,
        selected_province=selected_province,
        selected_city=selected_city,
    )
    base = base.sort_values(["location_priority", "captured_at", "trend_series_name"], ascending=[True, True, True], na_position="last")
    return _collapse_trend_to_daily_latest(base)


def build_single_market_product_trend(
    df: pd.DataFrame,
    identity_key: str,
    site_name: str | None = None,
    series_key: str | None = None,
    selected_province: str | None = None,
    selected_city: str | None = None,
) -> pd.DataFrame:
    trend_df = build_cross_market_product_trend(
        df,
        identity_key,
        selected_province=selected_province,
        selected_city=selected_city,
    )
    if trend_df.empty:
        return trend_df
    selected_key = _normalize_location_text(series_key)
    if selected_key and "trend_series_key" in trend_df.columns:
        trend_df = trend_df[trend_df["trend_series_key"] == selected_key].copy()
    elif site_name:
        trend_df = trend_df[trend_df["site_name"] == site_name].copy()
    return trend_df.reset_index(drop=True)



def build_lowest_price_summary(df: pd.DataFrame, mode: str = "price") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    if mode == "unit_price":
        lowest_df = current_lowest_unit_price(df)
        if lowest_df.empty:
            return lowest_df
        summary_columns = [
            column
            for column in [
                "category",
                "brand",
                "product_series",
                "spec_text",
                "site_name",
                "unit_price",
                "captured_at",
            ]
            if column in lowest_df.columns
        ]
        return lowest_df[summary_columns].reset_index(drop=True)

    lowest_df = current_lowest_price_platform(df)
    if lowest_df.empty:
        return lowest_df
    summary_columns = [
        column
        for column in [
            "group_name",
            "site_name",
            "product_name",
            "brand",
            "spec_text",
            "current_price",
            "promotion_text",
            "captured_at",
        ]
        if column in lowest_df.columns
    ]
    return lowest_df[summary_columns].reset_index(drop=True)



def current_lowest_price_platform(df: pd.DataFrame) -> pd.DataFrame:
    latest = _build_price_identity_frame(summarize_latest_prices(df))
    if latest.empty:
        return latest

    return (
        latest.sort_values(["price_identity_key", "current_price"], na_position="last")
        .groupby("price_identity_key", as_index=False)
        .head(1)
        .reset_index(drop=True)
    )


def current_lowest_unit_price(df: pd.DataFrame) -> pd.DataFrame:
    latest = summarize_latest_unit_prices(df)
    if latest.empty:
        return latest

    return (
        latest.sort_values(["category", "unit_price"], na_position="last")
        .groupby("category", as_index=False)
        .head(1)
        .reset_index(drop=True)
    )


def lowest_price_trend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = _build_price_identity_frame(prepare_history(df))
    base["captured_day"] = base["captured_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    trend = (
        base.groupby(["price_identity_label", "captured_day"], dropna=False)["current_price"]
        .min()
        .reset_index(name="lowest_price")
    )
    return trend


def lowest_unit_price_trend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "unit_price" not in df.columns:
        return pd.DataFrame()

    base = prepare_history(df).dropna(subset=["unit_price"])
    if base.empty:
        return pd.DataFrame()
    base["captured_day"] = base["captured_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return (
        base.groupby(["category", "captured_day"], dropna=False)["unit_price"]
        .min()
        .reset_index(name="lowest_unit_price")
    )


def prepare_quote_export_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    has_quote_columns = any(column in df.columns for column in ["current_price", "original_price", "promotion_text"])
    if not has_quote_columns:
        return df.copy()

    sanitized = df.drop(columns=[column for column in QUOTE_EXPORT_DROP_COLUMNS if column in df.columns], errors="ignore")
    ordered_columns = [column for column in QUOTE_EXPORT_PRIORITY_COLUMNS if column in sanitized.columns]
    remaining_columns = [column for column in sanitized.columns if column not in ordered_columns]
    return sanitized[ordered_columns + remaining_columns].copy()


def export_dataframe(df: pd.DataFrame, fmt: str = "csv") -> bytes:
    export_df = prepare_quote_export_dataframe(df)
    if fmt == "csv":
        return export_df.to_csv(index=False).encode("utf-8-sig")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="price_analysis")
    output.seek(0)
    return output.read()
