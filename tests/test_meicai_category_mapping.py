from __future__ import annotations

from services.meicai_category_mapping import suggest_meicai_internal_category


def test_suggest_meicai_internal_category_prefers_bi_name_mapping():
    mapping = suggest_meicai_internal_category(
        {
            "saleC1Id": "6506",
            "saleC2Id": "6514",
            "biName": "黄心土豆",
            "sampleSkuNames": ["新黄心土豆 普通 大"],
        }
    )

    assert mapping.category == "根茎类"
    assert mapping.market_category == "蔬菜类"
    assert mapping.liancai_top_category == "蔬菜类"
    assert mapping.liancai_subcategory == "根茎类"
    assert mapping.source == "meicai_bi_exact"
    assert mapping.confidence == 0.95


def test_suggest_meicai_internal_category_uses_sale_c2_when_bi_unknown():
    mapping = suggest_meicai_internal_category(
        {
            "saleC1Id": "6511",
            "saleC2Id": "6553",
            "biName": "未知饮用水",
            "sampleSkuNames": ["饮用水"],
        }
    )

    assert mapping.category == "饮用水"
    assert mapping.market_category == "酒水饮料"
    assert mapping.source == "meicai_sale_c2_id"


def test_suggest_meicai_internal_category_marks_unknown_candidates_unmapped():
    mapping = suggest_meicai_internal_category(
        {
            "saleC1Id": "9999",
            "saleC2Id": "8888",
            "biName": "未知商品",
            "sampleSkuNames": ["未知商品"],
        }
    )

    assert mapping.category == "未知商品"
    assert mapping.market_category is None
    assert mapping.source == "unmapped"
    assert mapping.confidence == 0.0
