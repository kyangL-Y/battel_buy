import pandas as pd

from analysis.alerts import AlertRule, check_alerts


def build_alert_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "product_key": "a",
                "group_name": "海天味极鲜生抽500ml",
                "category": "酱油",
                "site_name": "平台A",
                "product_name": "海天 味极鲜生抽 500ml",
                "current_price": 11.0,
                "unit_price": 2.2,
                "captured_at": "2026-03-30T10:00:00",
            },
            {
                "product_key": "b",
                "group_name": "千禾零添加生抽200ml",
                "category": "酱油",
                "site_name": "平台B",
                "product_name": "千禾 零添加生抽 200ml",
                "current_price": 6.0,
                "unit_price": 3.0,
                "captured_at": "2026-03-30T10:00:00",
            },
        ]
    )


def test_check_price_alerts():
    rules = [
        AlertRule(
            target_name="海天味极鲜生抽500ml",
            group_name="海天味极鲜生抽500ml",
            threshold=12.0,
            alert_type="price",
        )
    ]
    result = check_alerts(build_alert_df(), rules)
    assert len(result) == 1
    assert result[0].current_price == 11.0
    assert result[0].alert_type == "price"


def test_check_unit_price_alerts():
    rules = [
        AlertRule(
            target_name="酱油",
            category="酱油",
            threshold=2.5,
            alert_type="unit_price",
        )
    ]
    result = check_alerts(build_alert_df(), rules)
    assert len(result) == 1
    assert result[0].unit_price == 2.2
    assert result[0].alert_type == "unit_price"
