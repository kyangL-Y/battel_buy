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
    group_name: str | None = None

    def __post_init__(self) -> None:
        if not self.target_name:
            self.target_name = self.group_name or ""
        if self.group_name is None:
            self.group_name = self.target_name


@dataclass
class AlertResult:
    target_name: str
    site_name: str
    product_name: str
    threshold: float
    note: str = ""
    current_price: float | None = None
    group_name: str | None = None


def load_alert_rules() -> list[AlertRule]:
    if not ALERTS_CONFIG_PATH.exists():
        return []
    try:
        data = json.loads(ALERTS_CONFIG_PATH.read_text(encoding="utf-8"))
        rules: list[AlertRule] = []
        for item in data:
            alert_type = str(item.get("alert_type", "price") or "price").strip()
            if alert_type != "price":
                logger.warning("跳过不再支持的预警规则类型: %s", alert_type)
                continue
            if "target_name" not in item:
                item["target_name"] = item.get("group_name")
            item.pop("alert_type", None)
            item.pop("category", None)
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
            "group_name": r.group_name,
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
                        current_price=float(price),
                        group_name=row.get("group_name"),
                    )
                )
    return triggered
