import pandas as pd

from services.decision_engine import build_procurement_recommendation


def test_build_procurement_recommendation_exposes_source_tier_and_priority_label():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "西兰花",
                "group_name": "西兰花",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 4.2,
            }
        ]
    )

    payload = build_procurement_recommendation(
        menu_items=[{"menu_name": "蒜蓉西兰花", "ingredient_name": "西兰花"}],
        latest_df=latest_df,
        diners=20,
        tables=2,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    item = payload["items"][0]
    assert item["recommended_market"] == "北京新发地"
    assert item["source_priority_label"] == "蔬菜明细市场优先"
    assert item["source_tier"] == "主价格源"
    assert "来源层级: 主价格源" in item["reason_summary"]
