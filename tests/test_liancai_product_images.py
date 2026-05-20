from __future__ import annotations

import pandas as pd

from analysis.metrics import build_single_product_selector_options, compute_cross_site_price_summary


def test_selector_options_expose_liancai_source_category_and_image_only_for_liancai():
    df = pd.DataFrame(
        [
            {
                "group_name": "莲菜网",
                "product_name": "白扣",
                "product_key": "lc-app",
                "site_name": "莲菜网App | 干调类",
                "source_url": "https://lcwgetway.liancaiwang.cn",
                "category": "干调类",
                "liancai_top_category": "干调类",
                "liancai_subcategory": "香辛料",
                "spec_text": "500g",
                "current_price": 12.0,
                "captured_at": "2026-04-10T08:00:00",
                "image_url": "https://cdnlcw.liancaiwang.cn/uploads/baiko.jpg",
            },
            {
                "group_name": "公开价格源",
                "product_name": "白扣",
                "product_key": "pfsc",
                "site_name": "PFSC | 北京新发地",
                "source_url": "https://pfsc.agri.cn/api/priceQuotationController/pageList",
                "category": "调味品",
                "spec_text": "500g",
                "current_price": 13.0,
                "captured_at": "2026-04-10T08:00:00",
                "image_url": "https://example.com/should-not-leak.jpg",
            },
        ]
    )

    selector_df = build_single_product_selector_options(df)

    assert len(selector_df.index) == 1
    row = selector_df.iloc[0]
    assert row["source_name"] == "莲菜网"
    assert row["source_category"] == "干调类"
    assert row["liancai_subcategory"] == "香辛料"
    assert row["image_url"] == "https://cdnlcw.liancaiwang.cn/uploads/baiko.jpg"


def test_selector_options_do_not_expose_image_for_non_liancai_sources():
    df = pd.DataFrame(
        [
            {
                "group_name": "蔬菜类",
                "product_name": "白菜",
                "product_key": "wbncp",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com",
                "category": "蔬菜类",
                "spec_text": "公斤",
                "current_price": 2.4,
                "captured_at": "2026-04-10T08:00:00",
                "image_url": "https://example.com/not-liancai.jpg",
            }
        ]
    )

    selector_df = build_single_product_selector_options(df)

    assert len(selector_df.index) == 1
    row = selector_df.iloc[0]
    assert row["source_name"] == "万邦国际"
    assert row["source_category"] == "蔬菜类"
    assert row["image_url"] is None


def test_selector_options_recognize_liancai_from_url_even_when_site_name_is_generic():
    df = pd.DataFrame(
        [
            {
                "group_name": "调味品",
                "product_name": "雪天牌加碘精纯盐400g*5袋",
                "product_key": "lc-salt",
                "site_name": "调味料",
                "source_url": "https://lcwgetway.liancaiwang.cn/app/product",
                "category": "调味品",
                "liancai_top_category": "调味品",
                "liancai_subcategory": "调味料",
                "spec_text": "400g*5袋",
                "current_price": 4.2,
                "captured_at": "2026-04-10T08:00:00",
                "image_url": "https://cdnlcw.liancaiwang.cn/uploads/salt.jpg",
            }
        ]
    )

    selector_df = build_single_product_selector_options(df)

    assert len(selector_df.index) == 1
    row = selector_df.iloc[0]
    assert row["source_name"] == "莲菜网"
    assert row["source_category"] == "调味品"
    assert row["liancai_subcategory"] == "调味料"
    assert row["image_url"] == "https://cdnlcw.liancaiwang.cn/uploads/salt.jpg"


def test_cross_site_summary_preserves_liancai_image_when_cheaper_source_is_not_liancai():
    df = pd.DataFrame(
        [
            {
                "group_name": "莲菜网",
                "product_name": "白扣",
                "product_key": "lc-app",
                "site_name": "莲菜网App | 干调类",
                "source_url": "https://lcwgetway.liancaiwang.cn",
                "category": "干调类",
                "liancai_top_category": "干调类",
                "liancai_subcategory": "香辛料",
                "spec_text": "500g",
                "current_price": 15.0,
                "captured_at": "2026-04-10T08:00:00",
                "image_url": "https://cdnlcw.liancaiwang.cn/uploads/baiko.jpg",
            },
            {
                "group_name": "公开价格源",
                "product_name": "白扣",
                "product_key": "pfsc",
                "site_name": "PFSC | 北京新发地",
                "source_url": "https://pfsc.agri.cn/api/priceQuotationController/pageList",
                "category": "调味品",
                "spec_text": "500g",
                "current_price": 13.0,
                "captured_at": "2026-04-10T08:00:00",
                "image_url": "",
            },
        ]
    )

    summary_df = compute_cross_site_price_summary(df)

    assert len(summary_df.index) == 1
    row = summary_df.iloc[0]
    assert row["lowest_price_site"].startswith("PFSC")
    assert row["source_name"] == "莲菜网"
    assert row["liancai_top_category"] == "干调类"
    assert row["liancai_subcategory"] == "香辛料"
    assert row["image_url"] == "https://cdnlcw.liancaiwang.cn/uploads/baiko.jpg"
