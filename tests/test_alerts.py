import pandas as pd
import pytest

import analysis.alerts as alerts_module
from analysis.alerts import AlertRule, check_alerts, load_alert_rules


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
        )
    ]
    result = check_alerts(build_alert_df(), rules)
    assert len(result) == 1
    assert result[0].current_price == 11.0
    assert result[0].group_name == "海天味极鲜生抽500ml"


def test_check_alerts_only_matches_exact_product():
    rules = [
        AlertRule(
            target_name="千禾零添加生抽200ml",
            group_name="千禾零添加生抽200ml",
            threshold=6.5,
        )
    ]
    result = check_alerts(build_alert_df(), rules)
    assert len(result) == 1
    assert result[0].product_name == "千禾 零添加生抽 200ml"
    assert result[0].current_price == 6.0


def test_load_alert_rules_skips_legacy_category_rule(tmp_path, monkeypatch, caplog: pytest.LogCaptureFixture):
    config_path = tmp_path / "alerts.json"
    config_path.write_text(
        """
[
  {"target_name": "海天味极鲜生抽500ml", "threshold": 12.0, "group_name": "海天味极鲜生抽500ml"},
  {"target_name": "酱油", "threshold": 2.5, "alert_type": "unit_price", "category": "酱油"}
]
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(alerts_module, "ALERTS_CONFIG_PATH", config_path)

    rules = load_alert_rules()

    assert len(rules) == 1
    assert rules[0].group_name == "海天味极鲜生抽500ml"
    assert "跳过不再支持的预警规则类型" in caplog.text
