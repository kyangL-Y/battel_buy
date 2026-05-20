import pandas as pd

import analysis.metrics as metrics_module
from analysis.metrics import (
    append_change_rate,
    apply_ai_structured_enrichment,
    build_ai_enrichment_changes,
    build_compare_selection_label,
    build_cross_market_product_trend,
    build_favorite_compare_selection_labels,
    build_local_compare_result,
    build_lowest_price_summary,
    build_single_market_product_trend,
    build_single_product_selector_options,
    compute_cross_site_price_summary,
    compute_group_metrics,
    compute_single_product_summary,
    compute_unit_metrics,
    current_lowest_price_platform,
    current_lowest_unit_price,
    export_dataframe,
    filter_by_location,
    filter_groups,
    get_location_options,
    prepare_quote_export_dataframe,
    prioritize_favorite_groups,
    search_latest_records,
    sort_search_results,
    standardize_local_compare_file,
    summarize_ai_enrichment,
    summarize_local_compare_result,
)


def test_product_selector_filters_statistical_indicators_from_dish_options():
    df = pd.DataFrame(
        [
            {
                "group_name": "生猪存栏量月度环比变化率",
                "product_name": "生猪存栏量月度环比变化率",
                "product_key": "hog-stock-mom-rate",
                "site_name": "农业指标源",
                "spec_text": "%",
                "current_price": 1.2,
                "captured_at": "2026-04-10T08:00:00",
            },
            {
                "group_name": "猪肉",
                "product_name": "猪肉",
                "product_key": "pork",
                "site_name": "PFSC | 北京新发地",
                "spec_text": "公斤",
                "current_price": 22.5,
                "captured_at": "2026-04-10T08:00:00",
            },
        ]
    )

    selector_df = build_single_product_selector_options(df)

    assert selector_df["price_identity_label"].tolist() == ["猪肉 | 公斤"]


def test_product_selector_keeps_liancai_image_url_from_site_name():
    df = pd.DataFrame(
        [
            {
                "group_name": "白扣",
                "product_name": "白扣",
                "product_key": "liancai-white-cardamom",
                "site_name": "莲菜网App | 干调类",
                "source_url": "https://lcwgetway.liancaiwang.cn/posts/getGoodsDetail",
                "spec_text": "斤",
                "current_price": 35.0,
                "captured_at": "2026-04-10T08:00:00",
                "image_url": "https://cdnlcw.liancaiwang.cn/white-cardamom.jpg",
                "liancai_top_category": "干调类",
                "liancai_subcategory": "南北干货",
            }
        ]
    )

    selector_df = build_single_product_selector_options(df)

    assert selector_df.iloc[0]["source_name"] == "莲菜网"
    assert selector_df.iloc[0]["image_url"] == "https://cdnlcw.liancaiwang.cn/white-cardamom.jpg"


def test_market_summary_filters_statistical_indicators_from_product_rows():
    df = pd.DataFrame(
        [
            {
                "group_name": "生猪存栏量月度环比变化率",
                "product_name": "生猪存栏量月度环比变化率",
                "product_key": "hog-stock-mom-rate",
                "site_name": "农业指标源",
                "spec_text": "%",
                "current_price": 1.2,
                "captured_at": "2026-04-10T08:00:00",
            },
            {
                "group_name": "猪肉",
                "product_name": "猪肉",
                "product_key": "pork",
                "site_name": "PFSC | 北京新发地",
                "spec_text": "公斤",
                "current_price": 22.5,
                "captured_at": "2026-04-10T08:00:00",
            },
        ]
    )

    result = compute_cross_site_price_summary(df)

    assert result["product_name"].tolist() == ["猪肉 | 公斤"]


def build_sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "group_name": "海天味极鲜生抽500ml",
                "compare_key": "酱油|海天|味极鲜生抽|500ml",
                "product_key": "a",
                "site_name": "平台A",
                "category": "酱油",
                "brand": "海天",
                "product_series": "味极鲜生抽",
                "spec_text": "500ml",
                "current_price": 12.0,
                "unit_price": 2.4,
                "captured_at": "2026-03-29T10:00:00",
            },
            {
                "group_name": "海天味极鲜生抽500ml",
                "compare_key": "酱油|海天|味极鲜生抽|500ml",
                "product_key": "a",
                "site_name": "平台A",
                "category": "酱油",
                "brand": "海天",
                "product_series": "味极鲜生抽",
                "spec_text": "500ml",
                "current_price": 11.0,
                "unit_price": 2.2,
                "captured_at": "2026-03-30T10:00:00",
            },
            {
                "group_name": "海天味极鲜生抽500ml",
                "compare_key": "酱油|海天|味极鲜生抽|500ml",
                "product_key": "b",
                "site_name": "平台B",
                "category": "酱油",
                "brand": "海天",
                "product_series": "味极鲜生抽",
                "spec_text": "500ml",
                "current_price": 10.5,
                "unit_price": 2.1,
                "captured_at": "2026-03-30T10:00:00",
            },
            {
                "group_name": "千禾零添加生抽200ml",
                "compare_key": "酱油|千禾|零添加生抽|200ml",
                "product_key": "c",
                "site_name": "平台C",
                "category": "酱油",
                "brand": "千禾",
                "product_series": "零添加生抽",
                "spec_text": "200ml",
                "current_price": 6.0,
                "unit_price": 3.0,
                "captured_at": "2026-03-30T10:00:00",
            },
        ]
    )


def test_standardize_local_compare_file_supports_common_chinese_columns():
    local_df = pd.DataFrame(
        [
            {
                "商品分组": "海天味极鲜生抽500ml",
                "商品名称": "海天味极鲜生抽",
                "品类": "酱油",
                "品牌": "海天",
                "系列": "味极鲜生抽",
                "规格": "500ml",
                "平台": "线下门店",
                "本地价格": "9.80",
            }
        ]
    )

    result = standardize_local_compare_file(local_df)

    assert result.iloc[0]["group_name"] == "海天味极鲜生抽500ml"
    assert result.iloc[0]["brand"] == "海天"
    assert result.iloc[0]["local_price"] == 9.8
    assert result.iloc[0]["local_match_key"] == "海天味极鲜生抽|酱油|海天|味极鲜生抽|500ml"



def test_standardize_local_compare_file_supports_simple_quote_sheet_columns():
    local_df = pd.DataFrame(
        [
            {"序号": 1, "产品": "家乐鸡精", "规格": "900g*10", "报价": "187", "备注": ""},
            {"序号": 2, "产品": "百利红腰豆", "规格": "432g*24", "报价": "97", "备注": ""},
            {"序号": None, "产品": None, "规格": None, "报价": None, "备注": None},
        ]
    )

    result = standardize_local_compare_file(local_df)

    assert len(result) == 2
    assert result.iloc[0]["group_name"] == "家乐鸡精"
    assert result.iloc[0]["product_name"] == "家乐鸡精"
    assert result.iloc[0]["source_row_no"] == "1.0"
    assert result.iloc[0]["spec_text"] == "900g*10"
    assert result.iloc[0]["local_price"] == 187.0
    assert result.iloc[1]["product_name"] == "百利红腰豆"


def test_standardize_local_compare_file_keeps_box_price_tax_price_and_market_fields():
    local_df = pd.DataFrame(
        [
            {
                "序号": 1,
                "产品": "900g家乐鸡精 900g*10袋",
                "规格": "900g*10",
                "报价（箱）": "187",
                "税价": "196.35",
                "来源分类": "干调类",
                "渠道": "微信小程序",
                "备注": "莲菜网报价",
            }
        ]
    )

    result = standardize_local_compare_file(local_df)

    assert len(result) == 1
    assert result.iloc[0]["product_name"] == "900g家乐鸡精 900g*10袋"
    assert result.iloc[0]["group_name"] == "900g家乐鸡精 900g*10袋"
    assert result.iloc[0]["box_price"] == 187.0
    assert result.iloc[0]["local_price"] == 187.0
    assert result.iloc[0]["tax_price"] == 196.35
    assert result.iloc[0]["market_category"] == "干调类"
    assert result.iloc[0]["channel"] == "微信小程序"
    assert result.iloc[0]["remarks"] == "莲菜网报价"


def test_apply_ai_structured_enrichment_returns_original_when_ai_disabled():
    df = standardize_local_compare_file(
        pd.DataFrame([{"产品": "海天味极鲜生抽", "规格": None, "报价": "12"}])
    )

    def fake_extractor(rows, runtime_config=None):
        return [
            {
                "row_index": 0,
                "brand": "海天",
                "product_series": "味极鲜生抽",
                "spec_text": "500ml",
                "category": "酱油",
                "remarks": None,
            }
        ]

    result = apply_ai_structured_enrichment(
        df,
        extractor=fake_extractor,
        runtime_config={"ai": {"enabled": False}},
    )

    assert result.equals(df)



def test_apply_ai_structured_enrichment_only_fills_empty_fields():
    df = standardize_local_compare_file(
        pd.DataFrame([{"产品": "海天味极鲜生抽500ml", "品牌": "海天", "报价": "12"}])
    )

    def fake_extractor(rows, runtime_config=None):
        return [
            {
                "row_index": 0,
                "category": "酱油",
                "brand": "其他品牌",
                "product_series": "味极鲜生抽",
                "spec_text": "500ml",
                "remarks": "AI补全",
            }
        ]

    result = apply_ai_structured_enrichment(
        df,
        extractor=fake_extractor,
        runtime_config={"ai": {"enabled": True, "batch_size": 5, "max_rows_per_run": 20}},
    )

    assert result.iloc[0]["brand"] == "海天"
    assert result.iloc[0]["category"] == "酱油"
    assert result.iloc[0]["product_series"] == "味极鲜生抽"
    assert result.iloc[0]["spec_text"] == "500ml"
    assert bool(result.iloc[0]["ai_enriched"]) is True
    assert result.iloc[0]["ai_remarks"] == "AI补全"



def test_apply_ai_structured_enrichment_rebuilds_match_key_after_fill():
    df = standardize_local_compare_file(
        pd.DataFrame([{"产品": "海天味极鲜生抽500ml", "报价": "12"}])
    )

    def fake_extractor(rows, runtime_config=None):
        return [
            {
                "row_index": 0,
                "category": "酱油",
                "brand": "海天",
                "product_series": "味极鲜生抽",
                "spec_text": "500ml",
                "remarks": None,
            }
        ]

    result = apply_ai_structured_enrichment(
        df,
        extractor=fake_extractor,
        runtime_config={"ai": {"enabled": True, "batch_size": 5, "max_rows_per_run": 20}},
    )

    assert result.iloc[0]["local_match_key"] == "海天味极鲜生抽500ml|酱油|海天|味极鲜生抽|500ml"



def test_summarize_ai_enrichment_returns_expected_counts():
    df = pd.DataFrame(
        [
            {"local_row_id": 1, "group_name": "A", "ai_enriched": True, "ai_remarks": "AI补全"},
            {"local_row_id": 2, "group_name": "B", "ai_enriched": False, "ai_remarks": "仅备注"},
            {"local_row_id": 3, "group_name": "C", "ai_enriched": False, "ai_remarks": pd.NA},
        ]
    )

    summary = summarize_ai_enrichment(df)

    assert summary == {
        "total_count": 3,
        "candidate_count": 2,
        "enriched_count": 1,
        "remarks_only_count": 1,
        "untouched_count": 1,
    }



def test_build_ai_enrichment_changes_returns_only_changed_rows():
    before_df = standardize_local_compare_file(
        pd.DataFrame(
            [
                {"产品": "海天味极鲜生抽500ml", "品牌": "海天", "报价": "12"},
                {"产品": "千禾零添加生抽200ml", "品牌": "千禾", "规格": "200ml", "报价": "6"},
            ]
        )
    )
    after_df = before_df.copy()
    after_df.loc[0, "category"] = "酱油"
    after_df.loc[0, "product_series"] = "味极鲜生抽"
    after_df.loc[0, "spec_text"] = "500ml"
    after_df.loc[0, "ai_enriched"] = True
    after_df.loc[0, "ai_remarks"] = "AI补全"
    after_df.loc[1, "ai_enriched"] = False

    result = build_ai_enrichment_changes(before_df, after_df)

    assert len(result) == 1
    assert result.iloc[0]["local_row_id"] == 1
    assert result.iloc[0]["changed_fields"] == "category、product_series、spec_text"
    assert result.iloc[0]["changed_fields_text"] == "品类、系列、规格"
    assert result.iloc[0]["category_before"] is pd.NA or pd.isna(result.iloc[0]["category_before"])
    assert result.iloc[0]["category_after"] == "酱油"
    assert bool(result.iloc[0]["ai_enriched"]) is True
    assert result.iloc[0]["ai_remarks"] == "AI补全"



def test_build_ai_enrichment_changes_handles_no_changes():
    before_df = standardize_local_compare_file(pd.DataFrame([{"产品": "海天味极鲜生抽", "报价": "12"}]))
    after_df = before_df.copy()

    result = build_ai_enrichment_changes(before_df, after_df)

    assert result.empty



def test_apply_ai_structured_enrichment_raises_extractor_error():
    df = standardize_local_compare_file(
        pd.DataFrame([{"产品": "海天味极鲜生抽500ml", "报价": "12"}])
    )

    def fake_extractor(rows, runtime_config=None):
        raise RuntimeError("boom")

    try:
        apply_ai_structured_enrichment(
            df,
            extractor=fake_extractor,
            runtime_config={"ai": {"enabled": True, "batch_size": 5, "max_rows_per_run": 20}},
        )
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("预期应抛出提取器异常")



def test_current_lowest_price_platform():
    result = current_lowest_price_platform(build_sample_df())
    haitian = result[result["compare_key"] == "酱油|海天|味极鲜生抽|500ml"].iloc[0]
    assert haitian["site_name"] == "平台B"


def test_compute_cross_site_price_summary_merges_duplicate_products_across_sites():
    result = compute_cross_site_price_summary(build_sample_df())

    haitian = result[result["group_name"] == "海天味极鲜生抽500ml"].iloc[0]
    qianhe = result[result["group_name"] == "千禾零添加生抽200ml"].iloc[0]

    assert len(result) == 2
    assert haitian["lowest_price"] == 21.0
    assert haitian["lowest_price_site"] == "平台B"
    assert haitian["highest_price"] == 22.0
    assert haitian["highest_price_site"] == "平台A"
    assert haitian["average_price"] == 21.5
    assert haitian["site_count"] == 2
    assert qianhe["lowest_price"] == 30.0
    assert qianhe["highest_price"] == 30.0
    assert qianhe["site_count"] == 1


def test_compute_cross_site_price_summary_collapses_liancai_app_and_h5_into_single_source():
    df = pd.DataFrame(
        [
            {
                "group_name": "干调类",
                "product_name": "白扣",
                "product_key": "lc-app",
                "site_name": "莲菜网App | 干调类",
                "source_url": "https://lcwgetway.liancaiwang.cn",
                "current_price": 12.0,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "干调类",
                "product_name": "白扣",
                "product_key": "lc-h5",
                "site_name": "莲菜网H5 | 干调类",
                "source_url": "https://lcwgetway.liancaiwang.cn",
                "current_price": 13.0,
                "captured_at": "2026-04-06T10:00:00",
            },
        ]
    )

    result = compute_cross_site_price_summary(df)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["site_count"] == 1
    assert row["market_count"] == 1
    assert row["price_observation_count"] == 2
    assert row["source_names"] == "莲菜网"
    assert row["lowest_price"] == 12.5
    assert row["highest_price"] == 12.5
    assert row["average_price"] == 12.5


def test_compute_cross_site_price_summary_keeps_single_source_products_and_merges_market_rows():
    df = pd.DataFrame(
        [
            {
                "group_name": "鸡蛋",
                "product_name": "鸡蛋",
                "product_key": "pfsc-a",
                "site_name": "PFSC | 市场A",
                "source_url": "https://pfsc.agri.cn/#/priceMarket",
                "current_price": 8.0,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "鸡蛋",
                "product_name": "鸡蛋",
                "product_key": "pfsc-b",
                "site_name": "市场B",
                "source_url": "https://pfsc.agri.cn/#/priceMarket",
                "current_price": 10.0,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "鸡蛋",
                "product_name": "鸡蛋",
                "product_key": "wb-1",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "current_price": 9.0,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "鲍鱼",
                "product_name": "鲍鱼",
                "product_key": "wb-abalone",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "current_price": 80.0,
                "captured_at": "2026-04-06T10:00:00",
            },
        ]
    )

    result = compute_cross_site_price_summary(df)

    egg_row = result[result["product_name"] == "鸡蛋"].iloc[0]
    abalone_row = result[result["product_name"] == "鲍鱼"].iloc[0]

    assert len(result) == 2
    assert egg_row["lowest_price"] == 9.0
    assert egg_row["lowest_price_site"] == "PFSC | 鸡蛋 | 市场A"
    assert egg_row["highest_price"] == 9.0
    assert egg_row["highest_price_site"] == "PFSC | 鸡蛋 | 市场B"
    assert egg_row["average_price"] == 9.0
    assert egg_row["site_count"] == 2
    assert abalone_row["site_count"] == 1
    assert abalone_row["lowest_price_site"] == "万邦国际"


def test_compute_cross_site_price_summary_normalizes_500g_to_kg_for_cross_source_compare():
    df = pd.DataFrame(
        [
            {
                "group_name": "鸡蛋",
                "product_name": "鸡蛋",
                "product_key": "pfsc-egg",
                "site_name": "PFSC | 市场A",
                "source_url": "https://pfsc.agri.cn/#/priceMarket",
                "spec_text": "公斤",
                "current_price": 8.0,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "鸡蛋",
                "product_name": "鸡蛋",
                "product_key": "wb-egg",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "spec_text": "公斤",
                "current_price": 7.0,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "畜禽蛋品",
                "product_name": "鸡蛋",
                "product_key": "cp-egg",
                "site_name": "Chinaprice | 总平均价",
                "source_url": "https://www.chinaprice.cn",
                "spec_text": "元/500克",
                "current_price": 4.0,
                "captured_at": "2026-04-06T10:00:00",
            },
        ]
    )

    result = compute_cross_site_price_summary(df)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["product_name"] == "鸡蛋 | 公斤"
    assert row["lowest_price"] == 7.0
    assert row["lowest_price_site"] == "万邦国际"
    assert row["highest_price"] == 8.0
    assert row["site_count"] == 3
    assert row["average_price"] == 7.67


def test_compute_cross_site_price_summary_uses_detailed_source_labels_for_pfsc_and_chinaprice():
    df = pd.DataFrame(
        [
            {
                "group_name": "蔬菜类",
                "product_name": "白菜",
                "product_key": "pfsc-cabbage",
                "site_name": "PFSC | 北京新发地",
                "source_url": "https://pfsc.agri.cn/#/priceMarket",
                "spec_text": "公斤",
                "current_price": 2.0,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "蔬菜类",
                "product_name": "白菜",
                "product_key": "cp-cabbage",
                "site_name": "Chinaprice | 总平均价",
                "source_url": "https://www.chinaprice.cn",
                "spec_text": "公斤",
                "current_price": 3.0,
                "captured_at": "2026-04-06T10:00:00",
            },
        ]
    )

    result = compute_cross_site_price_summary(df)

    row = result.iloc[0]
    assert row["lowest_price_site"] == "PFSC | 蔬菜类 | 北京新发地"
    assert row["highest_price_site"] == "Chinaprice | 蔬菜类 | 总平均价"
    assert row["site_count"] == 2


def test_compute_cross_site_price_summary_merges_same_product_even_when_category_differs():
    df = pd.DataFrame(
        [
            {
                "group_name": "根茎类",
                "category": "根茎类",
                "product_name": "萝卜",
                "product_key": "pfsc-radish",
                "site_name": "PFSC | 市场A",
                "source_url": "https://pfsc.agri.cn/#/priceMarket",
                "spec_text": "公斤",
                "current_price": 2.0,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "蔬菜",
                "category": "蔬菜",
                "product_name": "萝卜",
                "product_key": "wb-radish",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "spec_text": "公斤",
                "current_price": 1.5,
                "captured_at": "2026-04-06T10:00:00",
            },
            {
                "group_name": "蔬菜类",
                "category": "蔬菜类",
                "product_name": "萝卜",
                "product_key": "cp-radish",
                "site_name": "Chinaprice | 总平均价",
                "source_url": "https://www.chinaprice.cn",
                "spec_text": "元/500克",
                "current_price": 0.9,
                "captured_at": "2026-04-06T10:00:00",
            },
        ]
    )

    result = compute_cross_site_price_summary(df)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["product_name"] == "萝卜 | 公斤"
    assert row["lowest_price"] == 1.5
    assert row["lowest_price_site"] == "万邦国际"
    assert row["highest_price"] == 2.0
    assert row["highest_price_site"] == "PFSC | 根茎类 | 市场A"
    assert row["site_count"] == 3


def test_compute_unit_metrics():
    result = compute_unit_metrics(build_sample_df())
    assert not result.empty
    assert "average_unit_price" in result.columns
    assert "historical_min_unit_price" in result.columns


def test_current_lowest_unit_price():
    result = current_lowest_unit_price(build_sample_df())
    assert result.iloc[0]["brand"] == "海天"
    assert result.iloc[0]["unit_price"] == 2.1


def test_build_local_compare_result_matches_latest_crawled_price():
    local_df = pd.DataFrame(
        [
            {
                "商品分组": "海天味极鲜生抽500ml",
                "商品名称": "海天味极鲜生抽",
                "品类": "酱油",
                "品牌": "海天",
                "系列": "味极鲜生抽",
                "规格": "500ml",
                "本地价格": 9.8,
            },
            {
                "商品分组": "不存在商品",
                "商品名称": "未知商品",
                "品类": "零食",
                "品牌": "测试品牌",
                "系列": "测试系列",
                "规格": "100g",
                "本地价格": 5.0,
            },
        ]
    )

    result = build_local_compare_result(local_df, build_sample_df())

    matched_row = result[result["group_name"] == "海天味极鲜生抽500ml"].iloc[0]
    unmatched_row = result[result["group_name"] == "不存在商品"].iloc[0]

    assert matched_row["match_status"] == "已匹配"
    assert matched_row["matched_site_name"] == "平台B"
    assert matched_row["current_price"] == 10.5
    assert round(float(matched_row["price_diff"]), 2) == 0.7
    assert matched_row["price_diff_rate_text"] == "+7.14%"

    assert unmatched_row["match_status"] == "未匹配"
    assert pd.isna(unmatched_row["current_price"])
    assert unmatched_row["matched_by"] == "未命中"



def test_summarize_local_compare_result_returns_expected_counts():
    local_df = pd.DataFrame(
        [
            {
                "商品分组": "海天味极鲜生抽500ml",
                "商品名称": "海天味极鲜生抽",
                "品类": "酱油",
                "品牌": "海天",
                "系列": "味极鲜生抽",
                "规格": "500ml",
                "本地价格": 9.8,
            },
            {
                "商品分组": "千禾零添加生抽200ml",
                "商品名称": "千禾零添加生抽",
                "品类": "酱油",
                "品牌": "千禾",
                "系列": "零添加生抽",
                "规格": "200ml",
                "本地价格": 6.0,
            },
            {
                "商品分组": "不存在商品",
                "商品名称": "未知商品",
                "品类": "零食",
                "品牌": "测试品牌",
                "系列": "测试系列",
                "规格": "100g",
                "本地价格": 5.0,
            },
        ]
    )

    result = build_local_compare_result(local_df, build_sample_df())
    summary = summarize_local_compare_result(result)

    assert summary == {
        "total_count": 3,
        "matched_count": 2,
        "unmatched_count": 1,
        "higher_count": 1,
        "lower_count": 0,
        "same_count": 1,
    }


def test_search_latest_records_returns_latest_unit_price_rows():
    result = search_latest_records(build_sample_df(), keyword="酱油", mode="unit_price")

    assert len(result) == 3
    assert "unit_price" in result.columns
    assert result.iloc[0]["site_name"] == "平台B"


def test_search_latest_records_ignores_blank_keyword():
    result = search_latest_records(build_sample_df(), keyword="   ", mode="price")

    assert len(result) == 3


def test_append_change_rate_returns_formatted_text():
    df = build_sample_df().copy()
    latest = search_latest_records(df, keyword="海天", mode="price")
    result = append_change_rate(latest, history_df=df, mode="price")

    row_a = result[result["product_key"] == "a"].iloc[0]
    row_b = result[result["product_key"] == "b"].iloc[0]

    assert row_a["change_rate_text"] == "-8.33%"
    assert pd.isna(row_b["change_rate"])
    assert row_b["change_rate_text"] == "暂无"


    row = search_latest_records(build_sample_df(), keyword="平台B", mode="price").iloc[0]

    label = build_compare_selection_label(row, mode="price")

    assert "平台B" in label
    assert "海天" in label
    assert "价格:10.50" in label


def test_build_compare_selection_label_uses_unit_price_mode():
    row = search_latest_records(build_sample_df(), keyword="平台B", mode="unit_price").iloc[0]

    label = build_compare_selection_label(row, mode="unit_price")

    assert "平台B" in label
    assert "500ml" in label
    assert "单位价:2.10" in label


def test_sort_search_results_by_lowest_price():
    result = sort_search_results(search_latest_records(build_sample_df(), keyword="酱油", mode="price"), mode="price", sort_by="最低价优先")

    assert result.iloc[0]["site_name"] == "平台C"
    assert result.iloc[0]["current_price"] == 6.0


def test_sort_search_results_by_latest_captured_at():
    df = build_sample_df().copy()
    df.loc[df["product_key"] == "c", "captured_at"] = "2026-03-31T10:00:00"
    result = sort_search_results(search_latest_records(df, keyword="酱油", mode="price"), mode="price", sort_by="最新抓取优先")

    assert result.iloc[0]["product_key"] == "c"


def test_sort_search_results_by_change_rate():
    df = build_sample_df().copy()
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [
                    {
                        "group_name": "千禾零添加生抽200ml",
                        "compare_key": "酱油|千禾|零添加生抽|200ml",
                        "product_key": "c",
                        "site_name": "平台C",
                        "category": "酱油",
                        "brand": "千禾",
                        "product_series": "零添加生抽",
                        "spec_text": "200ml",
                        "current_price": 8.0,
                        "unit_price": 4.0,
                        "captured_at": "2026-03-29T09:00:00",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    latest = search_latest_records(df, keyword="酱油", mode="price")
    result = sort_search_results(latest, mode="price", sort_by="涨跌幅优先", history_df=df)

    assert result.iloc[0]["product_key"] == "c"






def test_build_favorite_compare_selection_labels_returns_favorite_labels_only():
    df = search_latest_records(build_sample_df(), keyword="酱油", mode="price")
    labels = build_favorite_compare_selection_labels(df, ["千禾零添加生抽200ml"], mode="price")

    assert len(labels) == 1
    assert "千禾零添加生抽200ml" in labels[0]
    assert "平台C" in labels[0]



def test_filter_groups_returns_only_favorite_groups():
    result = filter_groups(build_sample_df(), ["千禾零添加生抽200ml"])

    assert len(result) == 1
    assert result.iloc[0]["group_name"] == "千禾零添加生抽200ml"



def test_current_lowest_price_platform_supports_filtered_favorite_groups():
    filtered = filter_groups(build_sample_df(), ["千禾零添加生抽200ml"])
    result = current_lowest_price_platform(filtered)

    assert len(result) == 1
    assert result.iloc[0]["group_name"] == "千禾零添加生抽200ml"
    assert result.iloc[0]["site_name"] == "平台C"



def test_build_lowest_price_summary_returns_expected_columns():
    filtered = filter_groups(build_sample_df(), ["千禾零添加生抽200ml"])
    result = build_lowest_price_summary(filtered, mode="price")

    assert list(result.columns) == [
        "group_name",
        "site_name",
        "product_name",
        "brand",
        "spec_text",
        "current_price",
        "captured_at",
    ]
    assert result.iloc[0]["site_name"] == "平台C"
    assert result.iloc[0]["current_price"] == 6.0



def test_prioritize_favorite_groups_puts_favorites_first():
    df = search_latest_records(build_sample_df(), keyword="酱油", mode="price")
    result = prioritize_favorite_groups(df, ["千禾零添加生抽200ml"])

    assert result.iloc[0]["group_name"] == "千禾零添加生抽200ml"
    assert bool(result.iloc[0]["is_favorite_group"]) is True


def test_prepare_quote_export_dataframe_removes_diagnosis_columns_for_quote_data():
    df = pd.DataFrame(
        [
            {
                "group_name": "副食",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "captured_at": "2026-04-02T23:24:34",
                "product_key": "wbncp-market-all::副食-豆芽尖-公斤",
                "product_name": "豆芽尖",
                "category": "副食",
                "spec_text": "公斤",
                "compare_key": "副食|未指定|未指定|公斤",
                "current_price": 3.3,
                "original_price": 3.4,
                "promotion_text": "河南",
                "currency": "CNY",
                "诊断类型": "通用失败",
                "诊断结论": "抓取失败",
                "处理建议": "检查链接",
                "raw_payload": "{}",
                "rn": 1,
            }
        ]
    )

    result = prepare_quote_export_dataframe(df)

    assert "诊断类型" not in result.columns
    assert "诊断结论" not in result.columns
    assert "处理建议" not in result.columns
    assert "raw_payload" not in result.columns
    assert "rn" not in result.columns
    assert result.iloc[0]["current_price"] == 3.3
    assert result.iloc[0]["promotion_text"] == "河南"


def test_export_dataframe_csv_uses_sanitized_quote_columns():
    df = pd.DataFrame(
        [
            {
                "group_name": "副食",
                "site_name": "万邦国际",
                "product_name": "豆芽尖",
                "current_price": 3.3,
                "original_price": 3.4,
                "promotion_text": "河南",
                "诊断类型": "通用失败",
                "处理建议": "检查链接",
            }
        ]
    )

    content = export_dataframe(df, "csv").decode("utf-8-sig")

    assert "诊断类型" not in content
    assert "处理建议" not in content
    assert "current_price" in content
    assert "promotion_text" in content


def test_filter_by_location_supports_province_and_city():
    df = pd.DataFrame(
        [
            {"product_name": "白菜", "province": "北京市", "city": "北京市"},
            {"product_name": "白菜", "province": "河南省", "city": "郑州市"},
        ]
    )
    result = filter_by_location(df, selected_province="北京市", selected_city="北京市")
    assert len(result) == 1
    assert result.iloc[0]["province"] == "北京市"


def test_get_location_options_returns_province_city_map():
    df = pd.DataFrame(
        [
            {"product_name": "白菜", "province": "北京市", "city": "北京市"},
            {"product_name": "萝卜", "province": "河南省", "city": "郑州市"},
            {"product_name": "蒜薹", "province": "河南省", "city": "洛阳市"},
            {"product_name": "土豆", "province": "河南省", "city": "郑州市"},
        ]
    )

    provinces, cities, province_city_map = get_location_options(df)

    assert provinces == ["北京市", "河南省"]
    assert cities == ["北京市", "洛阳", "郑州"]
    assert province_city_map == {
        "北京市": ["北京市"],
        "河南省": ["洛阳", "郑州"],
    }


def test_single_product_trend_helpers_return_summary_and_trend_rows():
    df = pd.DataFrame(
        [
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "a",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "公斤",
                "current_price": 2.4,
                "captured_at": "2026-04-08T10:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "a",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "公斤",
                "current_price": 2.8,
                "captured_at": "2026-04-09T10:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "b",
                "site_name": "PFSC | 河南万邦",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 2.0,
                "captured_at": "2026-04-09T10:00:00",
            },
        ]
    )
    selector_df = build_single_product_selector_options(df)
    identity_key = selector_df.iloc[0]["price_identity_key"]
    summary = compute_single_product_summary(df, identity_key)
    cross_market_df = build_cross_market_product_trend(df, identity_key)
    single_market_df = build_single_market_product_trend(df, identity_key, series_key="PFSC · 北京新发地")

    assert not selector_df.empty
    assert summary["current_lowest_site"] == "PFSC · 河南万邦"
    assert len(cross_market_df) == 3
    assert len(single_market_df) == 2


def test_single_product_trend_helpers_include_source_tier_metadata(monkeypatch):
    def fake_resolve_source_tier(item, fallback=""):
        source_name = str((item or {}).get("source_name") or "").strip()
        if source_name == "PFSC":
            return "主价格源"
        if source_name == "万邦国际":
            return "第三方参考源"
        return fallback

    monkeypatch.setattr(metrics_module, "resolve_source_tier", fake_resolve_source_tier)

    df = pd.DataFrame(
        [
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "pfsc-a",
                "site_name": "PFSC | 北京新发地",
                "source_url": "https://pfsc.agri.cn/#/priceMarket",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "公斤",
                "current_price": 2.6,
                "captured_at": "2026-04-10T08:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "wb-a",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 2.1,
                "captured_at": "2026-04-10T09:00:00",
            },
        ]
    )

    selector_df = build_single_product_selector_options(df)
    identity_key = selector_df.iloc[0]["price_identity_key"]
    summary = compute_single_product_summary(df, identity_key)
    trend_df = build_cross_market_product_trend(df, identity_key)

    assert set(trend_df["source_name"].tolist()) == {"PFSC", "万邦国际"}
    assert set(trend_df["source_tier"].tolist()) == {"主价格源", "第三方参考源"}
    assert summary["current_lowest_source_name"] == "万邦国际"
    assert summary["current_lowest_source_tier"] == "第三方参考源"
    assert summary["current_highest_source_name"] == "PFSC"
    assert summary["current_highest_source_tier"] == "主价格源"


def test_cross_site_summary_normalizes_gram_spec_to_kg_basis():
    df = pd.DataFrame(
        [
            {
                "product_key": "a1",
                "group_name": "白菜",
                "product_name": "白菜",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "500g",
                "current_price": 3.0,
                "captured_at": "2026-04-12T08:00:00",
            },
            {
                "product_key": "a2",
                "group_name": "白菜",
                "product_name": "白菜",
                "site_name": "PFSC | 河南万邦",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 5.0,
                "captured_at": "2026-04-12T08:05:00",
            },
        ]
    )

    result = compute_cross_site_price_summary(df)

    assert len(result) == 1
    assert result.iloc[0]["price_unit_basis"] == "元/公斤"
    assert result.iloc[0]["lowest_price"] == 5.5
    assert result.iloc[0]["highest_price"] == 5.5


def test_build_cross_market_product_trend_prefers_primary_chinaprice_channel_and_cleans_labels():
    df = pd.DataFrame(
        [
            {
                "group_name": "其他食品",
                "product_name": "方便面",
                "product_key": "cp-total",
                "site_name": "Chinaprice | 总平均价 | 其他食品汇总价格 | 食品（36大中城市）汇总树",
                "source_url": "https://www.chinaprice.cn/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg",
                "market_name": "总平均价",
                "province": "新疆",
                "city": "乌鲁木齐市",
                "spec_text": "元/袋",
                "current_price": 3.22,
                "captured_at": "2026-04-11T16:20:54",
            },
            {
                "group_name": "其他食品",
                "product_name": "方便面",
                "product_key": "cp-market",
                "site_name": "Chinaprice | 集市 | 其他食品汇总价格 | 食品（36大中城市）汇总树",
                "source_url": "https://www.chinaprice.cn/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg",
                "market_name": "集市",
                "province": "新疆",
                "city": "乌鲁木齐市",
                "spec_text": "元/袋",
                "current_price": 3.03,
                "captured_at": "2026-04-11T16:20:54",
            },
            {
                "group_name": "其他食品",
                "product_name": "方便面",
                "product_key": "cp-supermarket",
                "site_name": "Chinaprice | 超市 | 其他食品汇总价格 | 食品（36大中城市）汇总树",
                "source_url": "https://www.chinaprice.cn/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg",
                "market_name": "超市",
                "province": "新疆",
                "city": "乌鲁木齐市",
                "spec_text": "元/袋",
                "current_price": 3.41,
                "captured_at": "2026-04-11T16:20:54",
            },
        ]
    )

    selector_df = build_single_product_selector_options(df)
    identity_key = selector_df.iloc[0]["price_identity_key"]
    trend_df = build_cross_market_product_trend(df, identity_key)
    summary = compute_single_product_summary(df, identity_key)

    assert len(trend_df) == 1
    assert trend_df.iloc[0]["trend_series_name"] == "Chinaprice · 乌鲁木齐"
    assert trend_df.iloc[0]["trend_meta_label"] == "乌鲁木齐 · 新疆"
    assert summary["current_lowest_site"] == "Chinaprice · 乌鲁木齐"


def test_build_cross_market_product_trend_keeps_only_latest_point_per_day():
    df = pd.DataFrame(
        [
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "wb-cabbage",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 2.0,
                "captured_at": "2026-04-10T08:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "wb-cabbage",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 2.4,
                "captured_at": "2026-04-10T18:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "wb-cabbage",
                "site_name": "万邦国际",
                "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 2.8,
                "captured_at": "2026-04-11T09:00:00",
            },
        ]
    )

    selector_df = build_single_product_selector_options(df)
    identity_key = selector_df.iloc[0]["price_identity_key"]
    trend_df = build_cross_market_product_trend(df, identity_key)

    assert len(trend_df) == 2
    assert trend_df.iloc[0]["captured_at"] == "2026-04-10"
    assert trend_df.iloc[0]["current_price"] == 2.4
    assert trend_df.iloc[1]["captured_at"] == "2026-04-11"


def test_compute_single_product_summary_uses_latest_row_per_market_from_history():
    df = pd.DataFrame(
        [
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "pfsc-a",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "公斤",
                "current_price": 2.2,
                "captured_at": "2026-04-10T08:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "pfsc-a",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "公斤",
                "current_price": 2.6,
                "captured_at": "2026-04-10T18:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "wb-a",
                "site_name": "万邦国际",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 2.0,
                "captured_at": "2026-04-10T09:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "wb-a",
                "site_name": "万邦国际",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 2.1,
                "captured_at": "2026-04-11T09:00:00",
            },
        ]
    )

    selector_df = build_single_product_selector_options(df)
    identity_key = selector_df.iloc[0]["price_identity_key"]
    summary = compute_single_product_summary(df, identity_key)

    assert summary["current_lowest_price"] == 2.1
    assert summary["current_highest_price"] == 2.6
    assert summary["average_price"] == 2.35
    assert summary["site_count"] == 2
    assert summary["latest_captured_at"] == "2026-04-11"


def test_location_priority_prefers_selected_city_in_summary_and_trend_helpers():
    df = pd.DataFrame(
        [
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "bj",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "公斤",
                "current_price": 3.2,
                "captured_at": "2026-04-10T10:00:00",
            },
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "zz",
                "site_name": "PFSC | 河南万邦",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "spec_text": "公斤",
                "current_price": 2.1,
                "captured_at": "2026-04-10T10:00:00",
            },
        ]
    )

    summary_df = compute_cross_site_price_summary(df, selected_city="北京市")
    selector_df = build_single_product_selector_options(df, selected_city="北京市")
    identity_key = selector_df.iloc[0]["price_identity_key"]
    summary = compute_single_product_summary(df, identity_key, selected_city="北京市")
    trend_df = build_cross_market_product_trend(df, identity_key, selected_city="北京市")

    assert summary_df.iloc[0]["lowest_price_site"] == "PFSC | 白菜 | 北京新发地"
    assert summary["current_lowest_site"] == "PFSC · 北京新发地"
    assert trend_df.iloc[0]["city"] == "北京市"


def test_cross_site_summary_identity_key_matches_trend_history_from_multiple_sources_with_category_mismatch():
    df = pd.DataFrame(
        [
            {
                "group_name": "土豆",
                "product_name": "土豆",
                "product_key": "pfsc-potato",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "category": "蔬菜类",
                "spec_text": "公斤",
                "current_price": 2.6,
                "captured_at": "2026-04-10T10:00:00",
            },
            {
                "group_name": "土豆",
                "product_name": "土豆",
                "product_key": "wb-potato",
                "site_name": "万邦国际",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "category": "",
                "spec_text": "公斤",
                "current_price": 2.1,
                "captured_at": "2026-04-10T10:00:00",
            },
        ]
    )

    summary_df = compute_cross_site_price_summary(df)
    identity_key = summary_df.iloc[0]["price_identity_key"]
    trend_df = build_cross_market_product_trend(df, identity_key)
    summary = compute_single_product_summary(df, identity_key)

    assert identity_key == "土豆|公斤"
    assert len(trend_df) == 2
    assert set(trend_df["trend_series_name"].tolist()) == {"PFSC · 北京新发地", "万邦国际 · 河南万邦"}
    assert summary["site_count"] == 2


def test_single_product_selector_options_merges_cross_source_rows_with_category_mismatch():
    df = pd.DataFrame(
        [
            {
                "group_name": "土豆",
                "product_name": "土豆",
                "product_key": "pfsc-potato",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "category": "蔬菜类",
                "spec_text": "公斤",
                "current_price": 2.6,
                "captured_at": "2026-04-10T10:00:00",
            },
            {
                "group_name": "土豆",
                "product_name": "土豆",
                "product_key": "wb-potato",
                "site_name": "万邦国际",
                "market_name": "河南万邦",
                "province": "河南省",
                "city": "郑州市",
                "category": "",
                "spec_text": "公斤",
                "current_price": 2.1,
                "captured_at": "2026-04-10T10:00:00",
            },
        ]
    )

    selector_df = build_single_product_selector_options(df)

    assert len(selector_df) == 1
    assert selector_df.iloc[0]["price_identity_key"] == "土豆|公斤"
    assert selector_df.iloc[0]["price_identity_label"] == "土豆 | 公斤"
    assert selector_df.iloc[0]["site_count"] == 2


def test_cross_site_summary_uses_priority_location_fields_for_display():
    df = pd.DataFrame(
        [
            {
                "group_name": "大葱",
                "product_name": "大葱",
                "product_key": "anhui-onion",
                "site_name": "PFSC | 亳州农产品有限责任公司",
                "market_name": "亳州农产品有限责任公司",
                "province": "安徽省",
                "city": "亳州",
                "spec_text": "公斤",
                "current_price": 2.0,
                "captured_at": "2026-04-12T10:00:00",
            },
            {
                "group_name": "大葱",
                "product_name": "大葱",
                "product_key": "henan-onion",
                "site_name": "PFSC | 河南濮阳宏进农副产品批发市场有限公司",
                "market_name": "河南濮阳宏进农副产品批发市场有限公司",
                "province": "河南省",
                "city": "濮阳",
                "spec_text": "公斤",
                "current_price": 2.3,
                "captured_at": "2026-04-12T10:00:00",
            },
        ]
    )

    result = compute_cross_site_price_summary(df, selected_province="安徽省")

    assert len(result) == 1
    row = result.iloc[0]
    assert row["province"] == "安徽省"
    assert row["city"] == "亳州"
    assert row["region_label"] == "亳州"
    assert row["lowest_price_site"] == "PFSC | 大葱 | 亳州农产品有限责任公司"


def test_single_product_selector_options_excludes_non_product_action_labels():
    df = pd.DataFrame(
        [
            {
                "group_name": "土豆",
                "product_name": "土豆",
                "product_key": "potato",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "公斤",
                "current_price": 2.6,
                "captured_at": "2026-04-10T10:00:00",
            },
            {
                "group_name": "/copy",
                "product_name": "/copy",
                "product_key": "copy-action",
                "site_name": "操作项",
                "market_name": "操作项",
                "spec_text": "次",
                "current_price": 1.0,
                "captured_at": "2026-04-10T10:00:00",
            },
            {
                "group_name": "产区调整影响",
                "product_name": "产区调整影响",
                "product_key": "signal-copy",
                "site_name": "经营信号",
                "market_name": "经营信号",
                "spec_text": "条",
                "current_price": 1.0,
                "captured_at": "2026-04-10T10:00:00",
            },
        ]
    )

    selector_df = build_single_product_selector_options(df)

    assert selector_df["price_identity_label"].tolist() == ["土豆 | 公斤"]
    assert selector_df.iloc[0]["price_observation_count"] == 1


def test_product_surfaces_exclude_statistical_and_monitoring_labels():
    df = pd.DataFrame(
        [
            {
                "group_name": "土豆",
                "product_name": "土豆",
                "product_key": "potato",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "公斤",
                "current_price": 2.6,
                "captured_at": "2026-04-10T10:00:00",
            },
            {
                "group_name": "郑州菜篮子监测",
                "product_name": "万邦市场价格监测情况",
                "product_key": "market-monitor",
                "site_name": "郑州市农业农村局菜篮子监测 | 郑州监测",
                "market_name": "郑州监测",
                "category": "郑州菜篮子监测",
                "spec_text": "元/公斤",
                "current_price": 3.2,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "畜牧统计",
                "product_name": "全省猪存栏量",
                "product_key": "pig-stock",
                "site_name": "统计监测",
                "market_name": "统计监测",
                "category": "畜牧统计",
                "spec_text": "万头",
                "current_price": 120.0,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "郑州菜篮子监测",
                "product_name": "11种蔬菜均价",
                "product_key": "vegetable-average",
                "site_name": "郑州市农业农村局菜篮子监测 | 郑州监测",
                "market_name": "郑州监测",
                "category": "郑州菜篮子监测",
                "spec_text": "元/公斤",
                "current_price": 2.34,
                "captured_at": "2026-05-08T11:45:00",
            },
        ]
    )

    summary_df = compute_cross_site_price_summary(df)
    selector_df = build_single_product_selector_options(df)

    assert summary_df["product_name"].tolist() == ["土豆 | 公斤"]
    assert selector_df["price_identity_label"].tolist() == ["土豆 | 公斤"]


def test_product_surfaces_exclude_industrial_and_energy_products():
    df = pd.DataFrame(
        [
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "cabbage",
                "site_name": "河南省发改委价格监测 | 全省均价",
                "market_name": "全省均价",
                "spec_text": "元/500克",
                "current_price": 0.94,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "河南价格监测",
                "product_name": "现货动力煤",
                "product_key": "coal",
                "site_name": "河南省发改委价格监测 | 全省均价",
                "market_name": "全省均价",
                "spec_text": "元/吨",
                "current_price": 600,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "河南价格监测",
                "product_name": "螺纹钢",
                "product_key": "steel",
                "site_name": "河南省发改委价格监测 | 全省均价",
                "market_name": "全省均价",
                "spec_text": "元/吨",
                "current_price": 3300,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "河南价格监测",
                "product_name": "原油",
                "product_key": "oil",
                "site_name": "河南省发改委价格监测 | 全省均价",
                "market_name": "全省均价",
                "spec_text": "美元/桶",
                "current_price": 70,
                "captured_at": "2026-05-08T11:45:00",
            },
        ]
    )

    summary_df = compute_cross_site_price_summary(df)
    selector_df = build_single_product_selector_options(df)

    assert summary_df["product_name"].tolist() == ["白菜 | 公斤"]
    assert selector_df["price_identity_label"].tolist() == ["白菜 | 公斤"]


def test_product_surfaces_exclude_agricultural_inputs_and_consumables():
    df = pd.DataFrame(
        [
            {
                "group_name": "白菜",
                "product_name": "白菜",
                "product_key": "cabbage",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "category": "蔬菜",
                "spec_text": "公斤",
                "current_price": 2.6,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "叶面肥",
                "product_name": "叶面肥",
                "product_key": "fertilizer",
                "site_name": "惠农网行情 | 农资店",
                "market_name": "农资店",
                "category": "农资",
                "spec_text": "袋",
                "current_price": 8.0,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "杀菌剂",
                "product_name": "杀菌剂",
                "product_key": "fungicide",
                "site_name": "惠农网行情 | 农资店",
                "market_name": "农资店",
                "category": "农资",
                "spec_text": "袋",
                "current_price": 12.0,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "本地市场源",
                "product_name": "后厨圆形垃圾桶90L",
                "product_key": "trash-bin",
                "site_name": "莲菜网H5 | 易耗类",
                "market_name": "郑州莲菜网",
                "category": "餐厨用品",
                "liancai_top_category": "易耗类",
                "liancai_subcategory": "餐厨用品",
                "spec_text": "90L/个",
                "current_price": 60.0,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "本地市场源",
                "product_name": "康师傅饮用矿物质水550ml*12瓶",
                "product_key": "water",
                "site_name": "莲菜网H5 | 酒水饮料",
                "market_name": "郑州莲菜网",
                "category": "酒水饮料",
                "liancai_top_category": "酒水饮料",
                "liancai_subcategory": "水饮",
                "spec_text": "550ml*12瓶",
                "current_price": 18.0,
                "captured_at": "2026-05-08T11:45:00",
            },
            {
                "group_name": "水果动态",
                "product_name": "部分果种市场表现",
                "product_key": "fruit-market-story",
                "site_name": "行情资讯",
                "market_name": "行情资讯",
                "category": "行情资讯",
                "spec_text": "元/kg又下降41.48%",
                "current_price": 1.0,
                "captured_at": "2026-05-08T11:45:00",
            },
        ]
    )

    summary_df = compute_cross_site_price_summary(df)
    selector_df = build_single_product_selector_options(df)

    assert summary_df["product_name"].tolist() == ["白菜 | 公斤"]
    assert selector_df["price_identity_label"].tolist() == ["白菜 | 公斤"]


def test_compute_cross_site_price_summary_includes_supplier_quotes_as_source_rows():
    df = pd.DataFrame(
        [
            {
                "group_name": "本地市场源",
                "product_name": "百利番茄沙司10g*300袋",
                "product_key": "ketchup-300",
                "site_name": "莲菜网H5 | 西餐",
                "source_url": "https://lcwgetway.liancaiwang.cn/app/product",
                "market_name": "郑州莲菜网",
                "category": "西餐 / 调味品酱料类",
                "liancai_top_category": "西餐",
                "liancai_subcategory": "调味品酱料类",
                "spec_text": "10g*300袋",
                "current_price": 0.15,
                "captured_at": "2026-05-16T08:00:00",
            },
            {
                "group_name": "供应平台",
                "product_name": "百利番茄沙司10g*300袋",
                "product_key": "ketchup-300",
                "site_name": "鲜蔬直采A",
                "source_url": "supplier://1/price-record/999",
                "market_name": "供应商报价",
                "category": "西餐 / 调味品酱料类",
                "liancai_top_category": "西餐",
                "liancai_subcategory": "调味品酱料类",
                "spec_text": "10g*300袋",
                "current_price": 12.34,
                "captured_at": "2026-05-16T08:30:00",
            },
        ]
    )

    summary_df = compute_cross_site_price_summary(df)

    assert len(summary_df) == 1
    row = summary_df.iloc[0]
    assert row["site_count"] == 2
    assert row["market_count"] == 2
    assert row["source_names"] == "供应平台、莲菜网"
