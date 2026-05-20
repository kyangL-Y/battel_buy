from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterable

import pandas as pd

from analysis.alerts import AlertRule, check_alerts
from analysis.metrics import (
    _build_price_identity_frame,
    build_cross_market_product_trend,
    build_cross_site_identity_frame,
    compute_cross_site_price_summary,
    compute_group_metrics,
    compute_single_product_summary,
    prepare_history,
)


@dataclass
class SignalInsight:
    """Represents a serializable signal record for downstream decisions."""

    signal_key: str
    signal_type: str
    subject_type: str
    subject_id: str
    subject_name: str
    signal_level: str
    timing_score: int
    risk_score: int
    confidence: int
    recommended_action: str
    reason_summary: str
    impact_value: float | None = None
    recommended_market: str | None = None
    source_health: str = "weak"
    current_price: float | None = None
    baseline_price: float | None = None
    price_change_rate: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converts the signal into a JSON-friendly dictionary."""

        payload = asdict(self)
        payload["impact_value"] = _round_optional(payload.get("impact_value"))
        payload["current_price"] = _round_optional(payload.get("current_price"))
        payload["baseline_price"] = _round_optional(payload.get("baseline_price"))
        payload["price_change_rate"] = _round_optional(payload.get("price_change_rate"), digits=4)
        payload["metadata"] = _normalize_value(payload.get("metadata"))
        return _normalize_value(payload)


def build_overview_signals(
    history_df: pd.DataFrame,
    selected_province: str | None = None,
    selected_city: str | None = None,
    alert_rules: list[AlertRule] | None = None,
    top_n: int = 8,
) -> list[SignalInsight]:
    """Builds product-level overview signals from market history."""

    if history_df.empty:
        return []

    summary_df = compute_cross_site_price_summary(
        history_df,
        selected_province=selected_province,
        selected_city=selected_city,
    )
    if summary_df.empty:
        return []

    alert_groups = _build_alert_group_set(history_df, alert_rules)

    ranked = summary_df.copy()
    ranked["spread_rate"] = ranked.apply(
        lambda row: _ratio(
            _safe_float(row.get("highest_price")) - _safe_float(row.get("lowest_price")),
            _safe_float(row.get("average_price")),
        ),
        axis=1,
    )
    ranked = ranked.sort_values(
        ["spread_rate", "site_count", "average_price"],
        ascending=[False, False, True],
        na_position="last",
    )
    top_ranked = ranked.head(max(1, int(top_n))).copy()

    metric_source = history_df
    top_identity_keys = {str(item).strip() for item in top_ranked.get("price_identity_key", pd.Series(dtype=object)).dropna().tolist()}
    if top_identity_keys:
        try:
            cross_history = build_cross_site_identity_frame(_build_price_identity_frame(prepare_history(history_df)))
            if "cross_site_identity_key" in cross_history.columns:
                matched_history = cross_history[
                    cross_history["cross_site_identity_key"].fillna("").astype(str).isin(top_identity_keys)
                ].copy()
                if not matched_history.empty:
                    metric_source = matched_history
        except Exception:
            metric_source = history_df
    metric_df = compute_group_metrics(metric_source)
    metric_index = _build_metric_index(metric_df)

    signals: list[SignalInsight] = []
    for _, row in top_ranked.iterrows():
        identity_key = str(row.get("price_identity_key") or "").strip()
        if not identity_key:
            continue

        # Overview cards must stay fast on remote MySQL. Detailed trend lines are
        # still calculated by the product detail endpoint; the overview uses the
        # already-vectorized group metric trend as a lightweight signal.
        change_rate = 0.0
        trend_name = _normalize_trend_value(metric_index.get(identity_key, {}).get("trend"))
        record_count = int(metric_index.get(identity_key, {}).get("record_count") or 0)
        volatility = _safe_float(metric_index.get(identity_key, {}).get("volatility"))
        site_count = int(row.get("site_count") or 0)
        lowest_price = _safe_float(row.get("lowest_price"))
        average_price = _safe_float(row.get("average_price"))
        highest_price = _safe_float(row.get("highest_price"))
        spread_rate = _ratio(highest_price - lowest_price, average_price)
        discount_rate = _ratio(average_price - lowest_price, average_price)
        alert_hit = str(row.get("group_name") or "").strip() in alert_groups

        timing_score = _clip_score(
            28
            + min(24, abs(change_rate) * 360)
            + min(20, discount_rate * 220)
            + min(16, spread_rate * 120)
            + (14 if alert_hit else 0)
            + (10 if trend_name in {"up", "down"} else 0)
        )
        risk_score = _clip_score(
            16
            + min(28, spread_rate * 140)
            + min(24, volatility * 120)
            + (16 if trend_name == "up" else 0)
            + (8 if site_count <= 1 else 0)
        )
        confidence = _clip_score(
            34
            + min(24, record_count * 2)
            + min(22, site_count * 7)
            + (10 if pd.notna(row.get("lowest_price_site")) else 0)
            + (10 if not pd.isna(change_rate) else 0)
        )
        recommended_action = _choose_market_action(
            confidence=confidence,
            risk_score=risk_score,
            trend_name=trend_name,
            spread_rate=spread_rate,
            change_rate=change_rate,
            alert_hit=alert_hit,
        )
        source_health = _infer_source_health(confidence, site_count=site_count, record_count=record_count)
        impact_value = max(average_price - lowest_price, 0.0) if average_price else None
        reason_summary = _build_overview_reason(
            product_name=str(row.get("product_name") or ""),
            trend_name=trend_name,
            change_rate=change_rate,
            spread_rate=spread_rate,
            discount_rate=discount_rate,
            site_count=site_count,
            alert_hit=alert_hit,
        )

        signals.append(
            SignalInsight(
                signal_key=f"overview:{identity_key}",
                signal_type="overview",
                subject_type="product",
                subject_id=identity_key,
                subject_name=str(row.get("product_name") or row.get("group_name") or identity_key),
                signal_level=_derive_signal_level(timing_score, risk_score, confidence),
                timing_score=timing_score,
                risk_score=risk_score,
                confidence=confidence,
                recommended_action=recommended_action,
                reason_summary=reason_summary,
                impact_value=impact_value,
                recommended_market=_string_or_none(row.get("lowest_price_site")),
                source_health=source_health,
                current_price=lowest_price,
                baseline_price=average_price,
                price_change_rate=change_rate,
                metadata={
                    "group_name": _string_or_none(row.get("group_name")),
                    "highest_price": _round_optional(highest_price),
                    "spread_rate": _round_optional(spread_rate, digits=4),
                    "discount_rate": _round_optional(discount_rate, digits=4),
                    "site_count": site_count,
                    "trend": trend_name,
                    "record_count": record_count,
                    "selected_province": selected_province,
                    "selected_city": selected_city,
                    "alert_hit": alert_hit,
                },
            )
        )

    return signals


def build_single_product_signals(
    history_df: pd.DataFrame,
    identity_key: str,
    selected_province: str | None = None,
    selected_city: str | None = None,
    alert_rules: list[AlertRule] | None = None,
    market_limit: int = 3,
) -> list[SignalInsight]:
    """Builds detailed signals for one cross-market product."""

    normalized_identity = str(identity_key or "").strip()
    if history_df.empty or not normalized_identity:
        return []

    summary = compute_single_product_summary(
        history_df,
        normalized_identity,
        selected_province=selected_province,
        selected_city=selected_city,
    )
    trend_df = build_cross_market_product_trend(
        history_df,
        normalized_identity,
        selected_province=selected_province,
        selected_city=selected_city,
    )
    if not summary or trend_df.empty:
        return []

    latest_by_market = (
        trend_df.sort_values(["trend_series_key", "captured_at"])
        .groupby("trend_series_key", as_index=False, dropna=False)
        .tail(1)
        .sort_values(["current_price", "trend_series_name"], na_position="last")
        .reset_index(drop=True)
    )
    average_price = _safe_float(summary.get("average_price"))
    lowest_price = _safe_float(summary.get("current_lowest_price"))
    highest_price = _safe_float(summary.get("current_highest_price"))
    site_count = int(summary.get("site_count") or 0)
    product_name = str(summary.get("product_name") or normalized_identity)
    alert_groups = _build_alert_group_set(history_df, alert_rules)
    alert_hit = any(str(group_name or "").strip() in alert_groups for group_name in latest_by_market.get("group_name", pd.Series(dtype=object)))
    change_rate = _compute_recent_change_rate(trend_df)
    trend_name = _derive_trend_name(trend_df)
    spread_rate = _ratio(highest_price - lowest_price, average_price)
    discount_rate = _ratio(average_price - lowest_price, average_price)

    overall_timing = _clip_score(
        34
        + min(22, abs(change_rate) * 360)
        + min(22, discount_rate * 220)
        + min(18, spread_rate * 140)
        + (10 if alert_hit else 0)
    )
    overall_risk = _clip_score(
        18
        + min(30, spread_rate * 150)
        + (18 if trend_name == "up" else 0)
        + (10 if site_count <= 1 else 0)
    )
    overall_confidence = _clip_score(
        42
        + min(24, site_count * 9)
        + (10 if len(trend_df.index) >= 3 else 0)
        + (10 if not pd.isna(change_rate) else 0)
    )

    signals = [
        SignalInsight(
            signal_key=f"product:{normalized_identity}:overall",
            signal_type="single_product",
            subject_type="product",
            subject_id=normalized_identity,
            subject_name=product_name,
            signal_level=_derive_signal_level(overall_timing, overall_risk, overall_confidence),
            timing_score=overall_timing,
            risk_score=overall_risk,
            confidence=overall_confidence,
            recommended_action=_choose_market_action(
                confidence=overall_confidence,
                risk_score=overall_risk,
                trend_name=trend_name,
                spread_rate=spread_rate,
                change_rate=change_rate,
                alert_hit=alert_hit,
            ),
            reason_summary=_build_overview_reason(
                product_name=product_name,
                trend_name=trend_name,
                change_rate=change_rate,
                spread_rate=spread_rate,
                discount_rate=discount_rate,
                site_count=site_count,
                alert_hit=alert_hit,
            ),
            impact_value=max(average_price - lowest_price, 0.0) if average_price else None,
            recommended_market=_string_or_none(summary.get("current_lowest_site")),
            source_health=_infer_source_health(overall_confidence, site_count=site_count, record_count=len(trend_df.index)),
            current_price=lowest_price,
            baseline_price=average_price,
            price_change_rate=change_rate,
            metadata={
                "current_highest_price": _round_optional(highest_price),
                "current_highest_site": _string_or_none(summary.get("current_highest_site")),
                "site_count": site_count,
                "latest_captured_at": _string_or_none(summary.get("latest_captured_at")),
                "trend": trend_name,
            },
        )
    ]

    for _, market_row in latest_by_market.head(max(1, int(market_limit))).iterrows():
        market_name = _string_or_none(market_row.get("trend_series_name")) or _string_or_none(market_row.get("site_name"))
        if not market_name:
            continue
        market_price = _safe_float(market_row.get("current_price"))
        market_discount = _ratio(average_price - market_price, average_price)
        market_history = trend_df[trend_df["trend_series_key"] == market_row.get("trend_series_key")].copy()
        market_change = _compute_recent_change_rate(market_history)
        market_trend = _derive_trend_name(market_history, fallback=trend_name)
        sample_count = int(len(market_history.index))
        timing_score = _clip_score(
            38
            + min(25, max(market_discount, 0.0) * 240)
            + min(20, abs(market_change) * 320)
            + (8 if market_trend in {"up", "down"} else 0)
        )
        risk_score = _clip_score(
            20
            + min(26, max(-market_discount, 0.0) * 220)
            + (16 if market_trend == "up" else 0)
            + (10 if sample_count <= 1 else 0)
        )
        confidence = _clip_score(40 + min(28, sample_count * 10) + (10 if site_count >= 2 else 0))

        signals.append(
            SignalInsight(
                signal_key=f"product:{normalized_identity}:{market_row.get('trend_series_key')}",
                signal_type="single_product_market",
                subject_type="market",
                subject_id=str(market_row.get("trend_series_key") or market_name),
                subject_name=market_name,
                signal_level=_derive_signal_level(timing_score, risk_score, confidence),
                timing_score=timing_score,
                risk_score=risk_score,
                confidence=confidence,
                recommended_action=_choose_product_market_action(
                    market_discount=market_discount,
                    market_trend=market_trend,
                    confidence=confidence,
                ),
                reason_summary=_build_market_reason(
                    product_name=product_name,
                    market_name=market_name,
                    market_discount=market_discount,
                    market_change=market_change,
                    market_trend=market_trend,
                ),
                impact_value=average_price - market_price if average_price and market_price else None,
                recommended_market=market_name,
                source_health=_infer_source_health(confidence, site_count=1, record_count=sample_count),
                current_price=market_price,
                baseline_price=average_price,
                price_change_rate=market_change,
                metadata={
                    "site_name": _string_or_none(market_row.get("site_name")),
                    "market_name": _string_or_none(market_row.get("market_name")),
                    "province": _string_or_none(market_row.get("province")),
                    "city": _string_or_none(market_row.get("city")),
                    "sample_count": sample_count,
                    "trend": market_trend,
                },
            )
        )

    return signals


def build_procurement_signals(plan_df: pd.DataFrame) -> list[SignalInsight]:
    """Builds item-level procurement signals from a procurement plan."""

    if plan_df.empty:
        return []

    cost_series = pd.to_numeric(plan_df.get("estimated_cost"), errors="coerce")
    cost_median = _safe_float(cost_series.median()) if cost_series.notna().any() else 0.0

    signals: list[SignalInsight] = []
    for _, row in plan_df.iterrows():
        ingredient_name = str(row.get("ingredient_name") or row.get("menu_name") or "unknown").strip()
        price_status = str(row.get("price_status") or "").strip()
        matched = price_status == "已匹配报价"
        has_backup = bool(_string_or_none(row.get("backup_market")) or _string_or_none(row.get("backup_site")))
        reference_price = _safe_float(row.get("reference_price"))
        estimated_cost = _safe_float(row.get("estimated_cost"))
        source_priority_label = _string_or_none(row.get("source_priority_label"))
        source_tier = _string_or_none(row.get("source_tier"))
        distance_label = _string_or_none(row.get("distance_label"))
        recommended_market = _string_or_none(row.get("recommended_market")) or _string_or_none(row.get("recommended_site"))

        timing_score = _clip_score(
            24
            + (34 if matched else 0)
            + (10 if source_priority_label else 0)
            + (10 if distance_label else 0)
            + (12 if estimated_cost and estimated_cost >= cost_median and cost_median > 0 else 0)
        )
        risk_score = _clip_score(
            16
            + (34 if not matched else 0)
            + (16 if not has_backup else 0)
            + (10 if not recommended_market else 0)
            + (8 if estimated_cost and estimated_cost >= cost_median and cost_median > 0 else 0)
        )
        confidence = _clip_score(
            30
            + (32 if matched else 0)
            + (12 if has_backup else 0)
            + (10 if source_priority_label else 0)
            + (10 if reference_price > 0 else 0)
        )

        signals.append(
            SignalInsight(
                signal_key=f"procurement:{ingredient_name}",
                signal_type="procurement",
                subject_type="ingredient",
                subject_id=ingredient_name,
                subject_name=ingredient_name,
                signal_level=_derive_signal_level(timing_score, risk_score, confidence),
                timing_score=timing_score,
                risk_score=risk_score,
                confidence=confidence,
                recommended_action=_choose_procurement_action(
                    matched=matched,
                    has_backup=has_backup,
                    distance_label=distance_label,
                    confidence=confidence,
                ),
                reason_summary=_build_procurement_reason(
                    ingredient_name=ingredient_name,
                    price_status=price_status,
                    source_priority_label=source_priority_label,
                    source_tier=source_tier,
                    distance_label=distance_label,
                    remarks=_string_or_none(row.get("remarks")),
                ),
                impact_value=estimated_cost if estimated_cost > 0 else reference_price,
                recommended_market=recommended_market,
                source_health=_infer_procurement_source_health(matched=matched, has_backup=has_backup, confidence=confidence),
                current_price=reference_price,
                baseline_price=estimated_cost,
                price_change_rate=None,
                metadata={
                    "menu_name": _string_or_none(row.get("menu_name")),
                    "estimated_quantity": _round_optional(_safe_float(row.get("estimated_quantity"))),
                    "quantity_unit": _string_or_none(row.get("quantity_unit")),
                    "recommended_site": _string_or_none(row.get("recommended_site")),
                    "backup_market": _string_or_none(row.get("backup_market")),
                    "backup_site": _string_or_none(row.get("backup_site")),
                    "price_status": price_status,
                    "source_priority_label": source_priority_label,
                    "source_tier": source_tier,
                    "distance_label": distance_label,
                },
            )
        )

    return signals


def signal_insights_to_dicts(signals: Iterable[SignalInsight]) -> list[dict[str, Any]]:
    """Serializes signal insights into dictionaries."""

    return [signal.to_dict() for signal in signals]


def _build_alert_group_set(history_df: pd.DataFrame, alert_rules: list[AlertRule] | None) -> set[str]:
    if history_df.empty or not alert_rules:
        return set()
    return {
        str(result.group_name or "").strip()
        for result in check_alerts(history_df, alert_rules)
        if str(result.group_name or "").strip()
    }


def _build_metric_index(metric_df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if metric_df.empty:
        return {}

    metric_copy = metric_df.copy()
    metric_copy["trend_rank"] = metric_copy["trend"].map(
        {
            "上涨": 4,
            "波动": 3,
            "下降": 2,
            "平稳": 1,
            "数据不足": 0,
        }
    ).fillna(0)
    metric_copy = metric_copy.sort_values(
        ["price_identity_key", "trend_rank", "record_count", "volatility"],
        ascending=[True, False, False, False],
        na_position="last",
    )

    index: dict[str, dict[str, Any]] = {}
    for product_key, group in metric_copy.groupby("price_identity_key", dropna=False):
        top_row = group.iloc[0]
        index[str(product_key)] = {
            "trend": _normalize_trend_value(top_row.get("trend")),
            "record_count": int(pd.to_numeric(group["record_count"], errors="coerce").fillna(0).sum()),
            "volatility": _safe_float(pd.to_numeric(group["volatility"], errors="coerce").fillna(0).max()),
        }
    return index


def _compute_recent_change_rate(trend_df: pd.DataFrame) -> float:
    if trend_df.empty or "captured_at" not in trend_df.columns or "current_price" not in trend_df.columns:
        return 0.0

    daily_series = (
        trend_df.copy()
        .assign(captured_at=pd.to_datetime(trend_df["captured_at"], errors="coerce"))
        .dropna(subset=["captured_at", "current_price"])
        .groupby("captured_at")["current_price"]
        .mean()
        .sort_index()
    )
    if len(daily_series.index) < 2:
        return 0.0

    previous = _safe_float(daily_series.iloc[-2])
    current = _safe_float(daily_series.iloc[-1])
    if previous <= 0:
        return 0.0
    return (current - previous) / previous


def _derive_trend_name(trend_df: pd.DataFrame, fallback: str | None = None) -> str:
    if trend_df.empty or "captured_at" not in trend_df.columns or "current_price" not in trend_df.columns:
        return _normalize_trend_value(fallback)

    daily_series = (
        trend_df.copy()
        .assign(captured_at=pd.to_datetime(trend_df["captured_at"], errors="coerce"))
        .dropna(subset=["captured_at", "current_price"])
        .groupby("captured_at")["current_price"]
        .mean()
        .sort_index()
        .tail(3)
    )
    if len(daily_series.index) < 2:
        return _normalize_trend_value(fallback)

    values = daily_series.tolist()
    if all(left < right for left, right in zip(values, values[1:])):
        return "up"
    if all(left > right for left, right in zip(values, values[1:])):
        return "down"
    price_range = max(values) - min(values)
    mean_price = sum(values) / len(values)
    if mean_price > 0 and (price_range / mean_price) <= 0.02:
        return "stable"
    return "volatile"


def _normalize_trend_value(value: Any) -> str:
    mapping = {
        "上涨": "up",
        "下降": "down",
        "平稳": "stable",
        "波动": "volatile",
        "数据不足": "insufficient",
        "up": "up",
        "down": "down",
        "stable": "stable",
        "volatile": "volatile",
        "insufficient": "insufficient",
    }
    return mapping.get(str(value or "").strip(), "insufficient")


def _choose_market_action(
    confidence: int,
    risk_score: int,
    trend_name: str,
    spread_rate: float,
    change_rate: float,
    alert_hit: bool,
) -> str:
    if confidence < 45:
        return "manual_check"
    if alert_hit and spread_rate >= 0.08:
        return "lock_price"
    if trend_name == "up" and risk_score >= 65:
        return "restock_early"
    if spread_rate >= 0.12:
        return "switch_market"
    if change_rate <= -0.05:
        return "buy_now"
    return "monitor"


def _choose_product_market_action(market_discount: float, market_trend: str, confidence: int) -> str:
    if confidence < 45:
        return "manual_check"
    if market_discount >= 0.08:
        return "buy_from_market"
    if market_trend == "up":
        return "watch_market"
    return "compare_market"


def _choose_procurement_action(
    matched: bool,
    has_backup: bool,
    distance_label: str | None,
    confidence: int,
) -> str:
    if not matched:
        return "manual_check"
    if confidence < 50:
        return "verify_before_buy"
    if distance_label in {"同城优先", "当前位置附近"}:
        return "purchase_now"
    if has_backup:
        return "compare_backup"
    return "purchase_from_primary"


def _infer_source_health(confidence: int, site_count: int, record_count: int) -> str:
    if confidence >= 75 and site_count >= 2 and record_count >= 3:
        return "healthy"
    if confidence >= 55 and record_count >= 2:
        return "watch"
    return "weak"


def _infer_procurement_source_health(matched: bool, has_backup: bool, confidence: int) -> str:
    if matched and has_backup and confidence >= 70:
        return "healthy"
    if matched and confidence >= 55:
        return "watch"
    return "weak"


def _derive_signal_level(timing_score: int, risk_score: int, confidence: int) -> str:
    severity = (timing_score * 0.55) + (risk_score * 0.45)
    if confidence < 40:
        severity -= 8
    if severity >= 85:
        return "critical"
    if severity >= 68:
        return "high"
    if severity >= 48:
        return "medium"
    return "low"


def _build_overview_reason(
    product_name: str,
    trend_name: str,
    change_rate: float,
    spread_rate: float,
    discount_rate: float,
    site_count: int,
    alert_hit: bool,
) -> str:
    parts = [f"{product_name}"]
    if trend_name == "up":
        parts.append("近几期均价继续上行")
    elif trend_name == "down":
        parts.append("近几期均价回落")
    elif trend_name == "volatile":
        parts.append("近几期价格波动偏大")
    else:
        parts.append("近几期价格相对平稳")

    if abs(change_rate) >= 0.02:
        parts.append(f"最近变动约 {change_rate * 100:+.1f}%")
    if spread_rate >= 0.08:
        parts.append(f"跨市场价差约 {spread_rate * 100:.1f}%")
    if discount_rate >= 0.05:
        parts.append("当前最低报价低于市场均值")
    if site_count <= 1:
        parts.append("可用市场样本偏少")
    if alert_hit:
        parts.append("命中预设提醒阈值")
    return "；".join(parts)


def _build_market_reason(
    product_name: str,
    market_name: str,
    market_discount: float,
    market_change: float,
    market_trend: str,
) -> str:
    parts = [f"{product_name} 在 {market_name}"]
    if market_discount >= 0.05:
        parts.append("当前报价低于该单品跨市场均值")
    elif market_discount <= -0.05:
        parts.append("当前报价高于该单品跨市场均值")
    else:
        parts.append("当前报价接近该单品跨市场均值")

    if abs(market_change) >= 0.02:
        parts.append(f"最近变化约 {market_change * 100:+.1f}%")
    if market_trend == "up":
        parts.append("短期趋势偏强")
    elif market_trend == "down":
        parts.append("短期趋势回落")
    elif market_trend == "volatile":
        parts.append("短期波动明显")
    return "；".join(parts)


def _build_procurement_reason(
    ingredient_name: str,
    price_status: str,
    source_priority_label: str | None,
    source_tier: str | None,
    distance_label: str | None,
    remarks: str | None,
) -> str:
    parts = [f"{ingredient_name} {price_status or '待确认'}"]
    if source_priority_label:
        parts.append(f"来源策略: {source_priority_label}")
    if source_tier:
        parts.append(f"来源层级: {source_tier}")
    if distance_label:
        parts.append(f"位置策略: {distance_label}")
    if remarks:
        parts.append(remarks)
    return "；".join(parts)


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _clip_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _safe_float(value: Any) -> float:
    if value is None or pd.isna(value):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _round_optional(value: Any, digits: int = 2) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def _string_or_none(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_value(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None:
        return None
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (AttributeError, ValueError):
            pass
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return value
