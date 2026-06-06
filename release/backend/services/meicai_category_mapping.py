from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.liancai_category_mapping import suggest_liancai_mapping


@dataclass(frozen=True)
class MeicaiInternalCategoryMapping:
    category: str | None
    market_category: str | None
    liancai_top_category: str | None
    liancai_subcategory: str | None
    source: str
    confidence: float


MEICAI_SALE_C1_CATEGORY_MAP: dict[str, tuple[str, str]] = {
    "6202": ("冻品类", "全部"),
    "6203": ("易耗类", "清洁用品"),
    "6204": ("鲜活水产", "鲜冻水产"),
    "6501": ("易耗类", "餐厨用品"),
    "6502": ("禽蛋类", "鲜鸡蛋"),
    "6503": ("冻品类", "调理类"),
    "6504": ("冻品类", "调理类"),
    "6505": ("米面粮油", "全部"),
    "6506": ("蔬菜类", "全部"),
    "6507": ("腌腊类", "其它腌腊制品类"),
    "6508": ("冻品类", "调理类"),
    "6509": ("调味品", "调味料"),
    "6510": ("鲜禽类", "鲜鸡鸭"),
    "6511": ("酒水饮料", "全部"),
    "6512": ("米面粮油", "馒头花卷烧饼"),
    "16676": ("豆制品", "全部"),
    "17104": ("水果类", "全部"),
    "18753": ("干调类", "南北干货"),
    "1": ("蔬菜类", "全部"),
    "302": ("冻品类", "调理类"),
}

MEICAI_SALE_C2_CATEGORY_MAP: dict[str, tuple[str, str]] = {
    "16": ("蔬菜类", "特菜野菜"),
    "6248": ("米面粮油", "食用油"),
    "6249": ("酒水饮料", "果饮/茶饮"),
    "6258": ("酒水饮料", "碳酸饮料"),
    "6261": ("禽蛋类", "鲜鸡蛋"),
    "6262": ("调味品", "罐头/其他"),
    "6265": ("腌腊类", "腌腊肠类"),
    "6266": ("腌腊类", "腌腊肠类"),
    "6269": ("卤味类", "凉菜系列"),
    "6271": ("冻品类", "果蔬类"),
    "6274": ("冻品类", "调理类"),
    "6279": ("冻品类", "调理类"),
    "6284": ("调味品", "调味料"),
    "6285": ("调味品", "调味酱/汁"),
    "6287": ("米面粮油", "馒头花卷烧饼"),
    "6288": ("西餐", "烘焙蛋挞类"),
    "6289": ("西餐", "烘焙蛋挞类"),
    "6292": ("米面粮油", "馒头花卷烧饼"),
    "6293": ("冻品类", "饺子馄饨"),
    "6294": ("冻品类", "肠类制品"),
    "6295": ("冻品类", "调理类"),
    "6296": ("豆制品", "豆干、豆皮、豆泡、腐竹类"),
    "6297": ("米面粮油", "面条"),
    "6299": ("易耗类", "餐厨用品"),
    "6300": ("易耗类", "厨房设备"),
    "6302": ("易耗类", "餐厨用品"),
    "6303": ("易耗类", "打包系列"),
    "6304": ("易耗类", "餐厨用品"),
    "6308": ("易耗类", "清洁用品"),
    "6309": ("易耗类", "清洁用品"),
    "6205": ("蔬菜类", "葱姜蒜"),
    "6209": ("蔬菜类", "椒类"),
    "6210": ("菌菇类", "菌菇类"),
    "6213": ("鲜猪肉", "猪肉类"),
    "6236": ("鲜活水产", "鲜冻水产"),
    "6238": ("鲜活水产", "加工水产"),
    "6515": ("蔬菜类", "叶菜类"),
    "6537": ("鲜活水产", "鲜冻水产"),
    "6553": ("酒水饮料", "饮用水"),
    "6555": ("腌腊类", "腌腊肠类"),
    "6558": ("腌腊类", "腌腊猪肉类"),
    "6559": ("调味品", "罐头/其他"),
    "6560": ("冻品类", "调理类"),
    "6561": ("冻品类", "调理类"),
    "6562": ("鲜活水产", "加工水产"),
    "6563": ("西餐", "其他原料类"),
    "6564": ("西餐", "油炸小吃类"),
    "6569": ("冻品类", "调理类"),
    "6570": ("冻品类", "果蔬类"),
    "6572": ("调味品", "调味料"),
    "6574": ("调味品", "罐头/其他"),
    "6575": ("调味品", "罐头/其他"),
    "6576": ("调味品", "调味酱/汁"),
    "6578": ("调味品", "调味酱/汁"),
    "6581": ("米面粮油", "馒头花卷烧饼"),
    "6582": ("米面粮油", "杂粮"),
    "6583": ("冻品类", "丸子类"),
    "6586": ("易耗类", "餐厨用品"),
    "6588": ("易耗类", "一次性用品"),
    "6590": ("易耗类", "清洁用品"),
    "6592": ("易耗类", "清洁用品"),
    "6593": ("易耗类", "清洁用品"),
    "14958": ("米面粮油", "大米"),
    "15712": ("冻品类", "调理类"),
    "15713": ("冻品类", "调理类"),
    "16288": ("易耗类", "厨房设备"),
    "17105": ("水果类", "瓜果类"),
    "17107": ("水果类", "应季优果"),
    "17199": ("卤味类", "其他卤制品"),
    "17374": ("鲜猪肉", "猪肉类"),
    "18415": ("米面粮油", "面条"),
    "18804": ("干调类", "南北干货"),
    "18805": ("干调类", "南北干货"),
    "19012": ("腌腊类", "腌腊猪肉类"),
    "19108": ("冻品类", "调理类"),
    "20201": ("冻品类", "调理类"),
    "16677": ("豆制品", "豆干、豆皮、豆泡、腐竹类"),
    "16678": ("豆制品", "豆干、豆皮、豆泡、腐竹类"),
    "16933": ("豆制品", "豆腐类"),
    "19835": ("冻品类", "冻鸡鸭"),
}

MEICAI_BI_CATEGORY_MAP: dict[str, tuple[str, str]] = {
    "冻鸡琵琶腿": ("冻品类", "冻鸡鸭"),
    "鲜鸡蛋": ("禽蛋类", "鲜鸡蛋"),
    "江苏珍珠米": ("米面粮油", "大米"),
    "转基因大豆油": ("米面粮油", "食用油"),
    "豆皮": ("豆制品", "豆干、豆皮、豆泡、腐竹类"),
    "香干": ("豆制品", "豆干、豆皮、豆泡、腐竹类"),
    "嫩豆腐": ("豆制品", "豆腐类"),
    "小葱/香葱": ("蔬菜类", "葱姜蒜"),
    "红皮洋葱": ("蔬菜类", "葱姜蒜"),
    "蒜米": ("蔬菜类", "葱姜蒜"),
    "青长椒": ("蔬菜类", "椒类"),
    "金针菇": ("菌菇类", "菌菇类"),
    "绿豆芽": ("豆制品", "豆芽类"),
    "胡萝卜": ("蔬菜类", "根茎类"),
    "黄心土豆": ("蔬菜类", "根茎类"),
    "油菜": ("蔬菜类", "叶菜类"),
    "花菜": ("蔬菜类", "叶菜类"),
    "香菜": ("蔬菜类", "叶菜类"),
    "红茶": ("酒水饮料", "果饮/茶饮"),
    "可乐": ("酒水饮料", "碳酸饮料"),
    "柠檬味汽水": ("酒水饮料", "碳酸饮料"),
    "天然水": ("酒水饮料", "饮用水"),
    "纯净水": ("酒水饮料", "饮用水"),
}


def suggest_meicai_internal_category(candidate: dict[str, Any]) -> MeicaiInternalCategoryMapping:
    bi_name = _clean_text(candidate.get("biName"))
    sale_c2_id = _clean_text(candidate.get("saleC2Id"))
    sale_c1_id = _clean_text(candidate.get("saleC1Id"))
    sale_c2_name = _clean_text(candidate.get("saleC2Name"))
    sale_c1_name = _clean_text(candidate.get("saleC1Name"))
    sample_text = " ".join(
        _clean_text(sample_name)
        for sample_name in candidate.get("sampleSkuNames", [])
        if _clean_text(sample_name)
    )

    if bi_name in MEICAI_BI_CATEGORY_MAP:
        top_category, subcategory = MEICAI_BI_CATEGORY_MAP[bi_name]
        return _mapping(top_category, subcategory, source="meicai_bi_exact", confidence=0.95)

    liancai_mapping = suggest_liancai_mapping(
        category=bi_name or sale_c2_name or sale_c1_name,
        product_name=sample_text,
        site_name=None,
    )
    if liancai_mapping.top_category:
        return _mapping(
            liancai_mapping.top_category,
            liancai_mapping.subcategory or "全部",
            source=f"liancai_{liancai_mapping.source}",
            confidence=0.82,
        )

    if sale_c2_id in MEICAI_SALE_C2_CATEGORY_MAP:
        top_category, subcategory = MEICAI_SALE_C2_CATEGORY_MAP[sale_c2_id]
        return _mapping(top_category, subcategory, source="meicai_sale_c2_id", confidence=0.78)

    if sale_c1_id in MEICAI_SALE_C1_CATEGORY_MAP:
        top_category, subcategory = MEICAI_SALE_C1_CATEGORY_MAP[sale_c1_id]
        return _mapping(top_category, subcategory, source="meicai_sale_c1_id", confidence=0.65)

    return MeicaiInternalCategoryMapping(
        category=bi_name or None,
        market_category=None,
        liancai_top_category=None,
        liancai_subcategory=None,
        source="unmapped",
        confidence=0.0,
    )


def _mapping(top_category: str, subcategory: str, *, source: str, confidence: float) -> MeicaiInternalCategoryMapping:
    effective_subcategory = subcategory or "全部"
    return MeicaiInternalCategoryMapping(
        category=effective_subcategory if effective_subcategory != "全部" else top_category,
        market_category=top_category,
        liancai_top_category=top_category,
        liancai_subcategory=effective_subcategory,
        source=source,
        confidence=confidence,
    )


def _clean_text(value: Any) -> str:
    return str(value or "").strip()
