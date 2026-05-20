from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from analysis.alerts import AlertRule, load_alert_rules
from analysis.metrics import build_cross_market_product_trend, compute_single_product_summary
from analysis.signals import (
    SignalInsight,
    build_overview_signals,
    build_procurement_signals,
    build_single_product_signals,
    signal_insights_to_dicts,
)
from services.menu_planner import build_procurement_plan


@dataclass
class DecisionPayload:
    """Represents a unified decision object for API-facing services."""

    decision_type: str
    generated_at: str
    summary: dict[str, Any]
    signals: list[dict[str, Any]]
    data: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converts the decision payload into a JSON-friendly dictionary."""

        return _normalize_payload(asdict(self))


def build_signals_overview_decision(
    history_df: pd.DataFrame,
    selected_province: str | None = None,
    selected_city: str | None = None,
    alert_rules: list[AlertRule] | None = None,
    top_n: int = 8,
) -> DecisionPayload:
    """Builds the internal decision model for signals overview."""

    resolved_rules = alert_rules if alert_rules is not None else load_alert_rules()
    signals = build_overview_signals(
        history_df,
        selected_province=selected_province,
        selected_city=selected_city,
        alert_rules=resolved_rules,
        top_n=top_n,
    )
    signal_dicts = signal_insights_to_dicts(signals)

    return DecisionPayload(
        decision_type="signals_overview",
        generated_at=_now_iso(),
        summary=_summarize_signals(signals),
        signals=signal_dicts,
        data={
            "top_signal": signal_dicts[0] if signal_dicts else None,
            "signal_count": len(signal_dicts),
        },
        context={
            "selected_province": selected_province,
            "selected_city": selected_city,
            "top_n": top_n,
        },
    )


def build_single_product_signal_decision(
    history_df: pd.DataFrame,
    identity_key: str,
    selected_province: str | None = None,
    selected_city: str | None = None,
    alert_rules: list[AlertRule] | None = None,
    market_limit: int = 3,
) -> DecisionPayload:
    """Builds the internal decision model for single-product signals."""

    resolved_rules = alert_rules if alert_rules is not None else load_alert_rules()
    signals = build_single_product_signals(
        history_df,
        identity_key=identity_key,
        selected_province=selected_province,
        selected_city=selected_city,
        alert_rules=resolved_rules,
        market_limit=market_limit,
    )
    signal_dicts = signal_insights_to_dicts(signals)
    product_summary = compute_single_product_summary(
        history_df,
        identity_key,
        selected_province=selected_province,
        selected_city=selected_city,
    )
    trend_df = build_cross_market_product_trend(
        history_df,
        identity_key,
        selected_province=selected_province,
        selected_city=selected_city,
    )

    return DecisionPayload(
        decision_type="single_product_signals",
        generated_at=_now_iso(),
        summary=_summarize_signals(signals),
        signals=signal_dicts,
        data={
            "product_summary": _records_or_value(product_summary),
            "trend_points": _dataframe_records(trend_df),
            "market_limit": market_limit,
        },
        context={
            "identity_key": identity_key,
            "selected_province": selected_province,
            "selected_city": selected_city,
        },
    )


def build_procurement_recommend_decision(
    menu_items: list[dict[str, Any]],
    latest_records_df: pd.DataFrame,
    diners: int = 0,
    tables: int = 0,
    preferred_province: str | None = None,
    preferred_city: str | None = None,
    preferred_location: str | None = None,
) -> DecisionPayload:
    """Builds the internal decision model for procurement recommendations."""

    ingredient_df, plan_df = build_procurement_plan(
        menu_items=menu_items,
        latest_records_df=latest_records_df,
        diners=diners,
        tables=tables,
        preferred_province=preferred_province,
        preferred_city=preferred_city,
        preferred_location=preferred_location,
    )
    signals = build_procurement_signals(plan_df)
    signal_dicts = signal_insights_to_dicts(signals)
    total_cost = plan_df.attrs.get("total_cost") if hasattr(plan_df, "attrs") else None

    return DecisionPayload(
        decision_type="procurement_recommend",
        generated_at=_now_iso(),
        summary=_summarize_procurement(signals, plan_df, total_cost),
        signals=signal_dicts,
        data={
            "ingredients": _dataframe_records(ingredient_df),
            "procurement_items": _dataframe_records(plan_df),
            "total_cost": total_cost,
        },
        context={
            "diners": diners,
            "tables": tables,
            "preferred_province": preferred_province,
            "preferred_city": preferred_city,
            "preferred_location": preferred_location,
        },
    )


def build_decision_payload(decision_type: str, **kwargs: Any) -> DecisionPayload:
    """Dispatches a decision builder by decision type."""

    normalized = str(decision_type or "").strip().lower()
    if normalized == "signals_overview":
        return build_signals_overview_decision(**kwargs)
    if normalized == "single_product_signals":
        return build_single_product_signal_decision(**kwargs)
    if normalized == "procurement_recommend":
        return build_procurement_recommend_decision(**kwargs)
    raise ValueError(f"Unsupported decision_type: {decision_type}")


def _summarize_signals(signals: list[SignalInsight]) -> dict[str, Any]:
    if not signals:
        return {
            "signal_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "avg_confidence": 0,
            "top_action": None,
            "total_impact_value": None,
        }

    level_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    total_confidence = 0
    impact_values: list[float] = []
    action_counter: dict[str, int] = {}

    for signal in signals:
        level_counts[signal.signal_level] = level_counts.get(signal.signal_level, 0) + 1
        total_confidence += signal.confidence
        if signal.impact_value is not None:
            impact_values.append(float(signal.impact_value))
        action_counter[signal.recommended_action] = action_counter.get(signal.recommended_action, 0) + 1

    top_action = max(action_counter.items(), key=lambda item: item[1])[0] if action_counter else None
    total_impact = round(sum(impact_values), 2) if impact_values else None
    return {
        "signal_count": len(signals),
        "critical_count": level_counts.get("critical", 0),
        "high_count": level_counts.get("high", 0),
        "avg_confidence": round(total_confidence / len(signals), 2),
        "top_action": top_action,
        "total_impact_value": total_impact,
    }


def _summarize_procurement(
    signals: list[SignalInsight],
    plan_df: pd.DataFrame,
    total_cost: float | None,
) -> dict[str, Any]:
    base_summary = _summarize_signals(signals)
    if plan_df.empty:
        base_summary["matched_count"] = 0
        base_summary["missing_quote_count"] = 0
        base_summary["total_cost"] = total_cost
        return base_summary

    price_status = plan_df.get("price_status", pd.Series(dtype=object)).fillna("").astype(str)
    base_summary["matched_count"] = int((price_status == "已匹配报价").sum())
    base_summary["missing_quote_count"] = int((price_status != "已匹配报价").sum())
    base_summary["total_cost"] = total_cost
    return base_summary


def _dataframe_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return _normalize_payload(frame.to_dict(orient="records"))


def _records_or_value(value: Any) -> Any:
    return _normalize_payload(value)


def _normalize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_payload(item) for item in value]
    if isinstance(value, pd.Timestamp):
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


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _map_signal_level(level: Any) -> str:
    value = str(level or "").strip().lower()
    if value == "critical":
        return "high"
    if value in {"high", "medium", "low"}:
        return value
    return "medium"


def _to_api_signal_item(signal: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = signal.get("metadata") or {}
    highest_price = signal.get("current_highest_price") or metadata.get("current_highest_price")
    current_price = signal.get("current_price")
    price_span = None
    if current_price is not None and highest_price is not None:
        try:
            price_span = round(float(highest_price) - float(current_price), 2)
        except (TypeError, ValueError):
            price_span = None

    payload = {
        "identity_key": str(signal.get("subject_id") or ""),
        "product_name": str(signal.get("subject_name") or ""),
        "signal_code": str(signal.get("signal_type") or signal.get("signal_key") or ""),
        "signal_level": _map_signal_level(signal.get("signal_level")),
        "timing_score": float(signal.get("timing_score") or 0),
        "risk_score": float(signal.get("risk_score") or 0),
        "confidence": float(signal.get("confidence") or 0),
        "recommended_action": str(signal.get("recommended_action") or ""),
        "reason_summary": str(signal.get("reason_summary") or ""),
        "impact_value": signal.get("impact_value"),
        "recommended_market": signal.get("recommended_market"),
        "recommended_site": metadata.get("site_name") or signal.get("recommended_market"),
        "source_health": signal.get("source_health"),
        "trend_label": metadata.get("trend"),
        "latest_captured_at": metadata.get("latest_captured_at"),
        "site_count": metadata.get("site_count"),
        "current_lowest_price": current_price,
        "current_highest_price": highest_price,
        "average_price": signal.get("baseline_price"),
        "current_price": current_price,
        "price_span": price_span,
        "trend_points": None,
        "series_preview": [],
    }
    if extra:
        payload.update(extra)
    return payload


def build_signals_overview(
    latest_df: pd.DataFrame,
    history_df: pd.DataFrame,
    *,
    province: str | None = None,
    city: str | None = None,
    focus: str | None = None,
) -> dict[str, Any]:
    history_scope = history_df.copy()
    if focus and not history_scope.empty and "product_name" in history_scope.columns:
        focus_text = str(focus).strip()
        if focus_text:
            names = history_scope["product_name"].fillna("").astype(str)
            history_scope = history_scope[names.str.contains(focus_text, regex=False)].copy()

    decision = build_signals_overview_decision(
        history_scope,
        selected_province=province,
        selected_city=city,
        top_n=8,
    )
    signals = [_to_api_signal_item(item) for item in decision.signals]
    top_opportunities = sorted(signals, key=lambda item: item["timing_score"], reverse=True)[:4]
    top_risks = sorted(signals, key=lambda item: item["risk_score"], reverse=True)[:4]
    summary = decision.summary or {}

    recommended_actions = []
    for item in [top_opportunities[:1], top_risks[:1]]:
        if not item:
            continue
        current = item[0]
        recommended_actions.append(
            {
                "title": current["product_name"] or "重点信号",
                "description": current["reason_summary"],
                "action": current["recommended_action"],
                "confidence": current["confidence"],
                "impact_value": current["impact_value"],
            }
        )

    latest_capture = None
    if history_df is not None and not history_df.empty and "captured_at" in history_df.columns:
        captured = pd.to_datetime(history_df["captured_at"], errors="coerce").dropna()
        if not captured.empty:
            latest_capture = captured.max().strftime("%Y-%m-%d")

    return {
        "generated_at": latest_capture or decision.generated_at,
        "scope": {"province": province, "city": city, "focus": focus},
        "headline": f"{city or province or '全国市场'} 现在最适合先展示机会窗口，再展示风险规避建议。",
        "overview_metrics": [
            {"label": "信号总数", "value": str(summary.get('signal_count', 0)), "detail": "当前筛选范围内可直接展示的经营信号"},
            {"label": "高优先级", "value": str(summary.get('high_count', 0) + summary.get('critical_count', 0)), "detail": "值得先讲给客户听的核心信号"},
            {"label": "平均置信度", "value": str(summary.get('avg_confidence', 0)), "detail": "规则判断的整体可信度"},
            {"label": "预估影响值", "value": str(summary.get('total_impact_value') or 0), "detail": "可用于销售表达的潜在收益/风险值"},
        ],
        "top_opportunities": top_opportunities,
        "top_risks": top_risks,
        "recommended_actions": recommended_actions,
        "source_health": {
            "status": "healthy" if (summary.get("avg_confidence") or 0) >= 70 else "watch",
            "product_count": len(signals),
            "market_count": len({item.get("recommended_market") for item in signals if item.get("recommended_market")}),
            "latest_capture": latest_capture,
            "freshness_days": None,
        },
        "alert_count": int(summary.get("critical_count", 0) + summary.get("high_count", 0)),
        "alert_items": [],
    }


def build_product_signal_detail(
    history_df: pd.DataFrame,
    identity_key: str,
    *,
    province: str | None = None,
    city: str | None = None,
) -> dict[str, Any]:
    decision = build_single_product_signal_decision(
        history_df,
        identity_key,
        selected_province=province,
        selected_city=city,
    )
    if not decision.signals:
        return {}

    primary = _to_api_signal_item(
        decision.signals[0],
        {
            "trend_points": len(decision.data.get("trend_points") or []),
            "series_preview": (decision.data.get("trend_points") or [])[-7:],
        },
    )
    return primary


def build_procurement_recommendation(
    *,
    menu_items: list[dict[str, Any]],
    latest_df: pd.DataFrame,
    diners: int = 0,
    tables: int = 0,
    preferred_province: str | None = None,
    preferred_city: str | None = None,
    preferred_location: str | None = None,
) -> dict[str, Any]:
    decision = build_procurement_recommend_decision(
        menu_items=menu_items,
        latest_records_df=latest_df,
        diners=diners,
        tables=tables,
        preferred_province=preferred_province,
        preferred_city=preferred_city,
        preferred_location=preferred_location,
    )

    items: list[dict[str, Any]] = []
    for signal in decision.signals:
        metadata = signal.get("metadata") or {}
        items.append(
            {
                "menu_name": metadata.get("menu_name"),
                "ingredient_name": signal.get("subject_name"),
                "identity_key": None,
                "price_status": metadata.get("price_status"),
                "estimated_cost": signal.get("baseline_price"),
                "reference_price": signal.get("current_price"),
                "recommended_market": signal.get("recommended_market"),
                "recommended_site": metadata.get("recommended_site"),
                "backup_market": metadata.get("backup_market"),
                "backup_site": metadata.get("backup_site"),
                "timing_score": float(signal.get("timing_score") or 0),
                "risk_score": float(signal.get("risk_score") or 0),
                "confidence": float(signal.get("confidence") or 0),
                "signal_level": _map_signal_level(signal.get("signal_level")),
                "recommended_action": signal.get("recommended_action"),
                "reason_summary": signal.get("reason_summary"),
                "impact_value": signal.get("impact_value"),
                "source_priority_label": metadata.get("source_priority_label"),
                "source_tier": metadata.get("source_tier"),
                "distance_label": metadata.get("distance_label"),
            }
        )

    return {
        "summary": {
            "menu_count": len(decision.data.get("ingredients") or []),
            "recommendation_count": len(items),
            "matched_count": decision.summary.get("matched_count", 0),
            "pending_count": decision.summary.get("missing_quote_count", 0),
            "total_cost": decision.summary.get("total_cost"),
        },
        "ingredient_items": decision.data.get("ingredients") or [],
        "items": items,
    }


def build_sales_demo_content(
    latest_df: pd.DataFrame,
    history_df: pd.DataFrame | None,
    scene: str | None = None,
    record_count: int | None = None,
) -> dict[str, Any]:
    product_count = 0
    market_count = 0
    if latest_df is not None and not latest_df.empty:
        if "product_name" in latest_df.columns:
            product_count = int(latest_df["product_name"].fillna("").astype(str).nunique())
        if "site_name" in latest_df.columns:
            market_count = int(latest_df["site_name"].fillna("").astype(str).nunique())
    if record_count is None:
        if history_df is not None and not history_df.empty:
            record_count = int(len(history_df))
        else:
            record_count = 0

    return {
        "scene": scene or "default",
        "hero": {
            "eyebrow": "REAL MARKET SIGNALS",
            "title": "真实行情经营信号",
            "description": "基于已入库的商品、市场和价格记录，先看风险与机会，再进入采购建议和报价承接。",
            "primary_cta": "进入老板驾驶舱",
            "secondary_cta": "查看真实行情",
        },
        "proof_points": [
            {"label": "可分析商品", "value": str(product_count)},
            {"label": "覆盖市场", "value": str(market_count)},
            {"label": "历史记录", "value": str(record_count)},
        ],
        "scenes": [
            {"title": "老板驾驶舱", "description": "先展示真实信号里今天该关注什么。", "highlight": "按接口数据生成"},
            {"title": "经营信号", "description": "展示为什么现在买、为什么现在不买。", "highlight": "规则优先，可解释"},
            {"title": "菜单采购建议", "description": "从菜单用量进入采购建议。", "highlight": "可接供应商报价"},
        ],
        "storyline": [
            "先讲今天的机会和风险。",
            "再落到单品和菜单，证明建议真实可用。",
            "最后进入供应商报价或菜单采购承接。",
        ],
    }


def build_pricing_packages() -> dict[str, Any]:
    return {
        "items": [
            {
                "name": "试点成交版",
                "price_band": "轻量试点",
                "target": "顾问型销售 / 单城市客户",
                "recommended": False,
                "features": ["老板驾驶舱", "经营信号概览", "菜单采购建议", "标准讲解脚本"],
                "cta": "适合快速试点和验证成交意向",
            },
            {
                "name": "经营决策版",
                "price_band": "主推报价",
                "target": "区域餐饮集团 / 采购团队",
                "recommended": True,
                "features": ["多地区经营信号", "单品建议详情", "采购增强建议", "报价承接页面"],
                "cta": "适合作为正式主包报价",
            },
            {
                "name": "定制交付版",
                "price_band": "高客单升级",
                "target": "品牌连锁 / 平台客户",
                "recommended": False,
                "features": ["品牌包装定制", "规则与提醒定制", "私有部署支持", "培训与验收模板"],
                "cta": "用于抬高客单价和交付价值",
            },
        ]
    }
