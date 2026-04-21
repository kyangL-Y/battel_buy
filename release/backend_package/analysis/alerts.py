from __future__ import annotations

from dataclasses import dataclass
import json

import pandas as pd

from utils.config_loader import BASE_DIR
from utils.logger import setup_logger

logger = setup_logger()

ALERTS_CONFIG_PATH = BASE_DIR / "config" / "alerts.json"


@dataclass
class AlertRule:
    target_name: str
    threshold: float
    note: str = ""
    alert_type: str = "price"
    group_name: str | None = None
    category: str | None = None

    def __post_init__(self) -> None:
        if self.group_name is None and self.category is None:
            if self.alert_type == "unit_price":
                self.category = self.target_name
            else:
                self.group_name = self.target_name
        if not self.target_name:
            self.target_name = self.category or self.group_name or ""
        if self.alert_type == "unit_price" and self.category is None:
            self.category = self.target_name
        if self.alert_type == "price" and self.group_name is None:
            self.group_name = self.target_name


@dataclass
class AlertResult:
    target_name: str
    site_name: str
    product_name: str
    threshold: float
    note: str = ""
    alert_type: str = "price"
    current_price: float | None = None
    unit_price: float | None = None
    group_name: str | None = None
    category: str | None = None


def load_alert_rules() -> list[AlertRule]:
    if not ALERTS_CONFIG_PATH.exists():
        return []
    try:
        data = json.loads(ALERTS_CONFIG_PATH.read_text(encoding="utf-8"))
        rules: list[AlertRule] = []
        for item in data:
            if "target_name" not in item:
                alert_type = item.get("alert_type", "price")
                item["target_name"] = item.get("category") if alert_type == "unit_price" else item.get("group_name")
            rules.append(AlertRule(**item))
        return rules
    except Exception as exc:  # noqa: BLE001
        logger.error("读取提醒规则失败: %s", exc)
        return []


def save_alert_rules(rules: list[AlertRule]) -> None:
    ALERTS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "target_name": r.target_name,
            "threshold": r.threshold,
            "note": r.note,
            "alert_type": r.alert_type,
            "group_name": r.group_name,
            "category": r.category,
        }
        for r in rules
    ]
    ALERTS_CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check_alerts(history_df: pd.DataFrame, rules: list[AlertRule]) -> list[AlertResult]:
    if history_df.empty or not rules:
        return []

    latest = history_df.sort_values("captured_at").groupby("product_key", as_index=False).tail(1)
    triggered: list[AlertResult] = []

    for rule in rules:
        if rule.alert_type == "unit_price":
            subset = latest.copy()
            if rule.category:
                subset = subset[subset["category"] == rule.category]
            for _, row in subset.iterrows():
                price = row.get("unit_price")
                if price is None or pd.isna(price):
                    continue
                if float(price) <= rule.threshold:
                    triggered.append(
                        AlertResult(
                            target_name=rule.target_name,
                            site_name=str(row.get("site_name", "")),
                            product_name=str(row.get("product_name", "")),
                            threshold=rule.threshold,
                            note=rule.note,
                            alert_type=rule.alert_type,
                            unit_price=float(price),
                            group_name=row.get("group_name"),
                            category=row.get("category"),
                        )
                    )
        else:
            subset = latest[latest["group_name"] == rule.group_name]
            for _, row in subset.iterrows():
                price = row.get("current_price")
                if price is None or pd.isna(price):
                    continue
                if float(price) <= rule.threshold:
                    triggered.append(
                        AlertResult(
                            target_name=rule.target_name,
                            site_name=str(row.get("site_name", "")),
                            product_name=str(row.get("product_name", "")),
                            threshold=rule.threshold,
                            note=rule.note,
                            alert_type=rule.alert_type,
                            current_price=float(price),
                            group_name=row.get("group_name"),
                            category=row.get("category"),
                        )
                    )
    return triggered
