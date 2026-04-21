from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from analysis.metrics import (
    lowest_price_trend,
    lowest_unit_price_trend,
    prepare_history,
    summarize_latest_prices,
    summarize_latest_unit_prices,
)


EMPTY_FIG = go.Figure()
EMPTY_FIG.update_layout(title="暂无数据")


def build_price_history_chart(df: pd.DataFrame, selected_group: str | None = None) -> go.Figure:
    if df.empty:
        return EMPTY_FIG

    base = prepare_history(df)
    if selected_group:
        base = base[base["group_name"] == selected_group]
    if base.empty:
        return EMPTY_FIG

    return px.line(
        base,
        x="captured_at",
        y="current_price",
        color="site_name",
        line_group="product_key",
        markers=True,
        title="历史价格折线图",
        hover_data=["product_name", "group_name", "spec_text"],
    )


def build_platform_bar_chart(df: pd.DataFrame, selected_group: str | None = None) -> go.Figure:
    latest = summarize_latest_prices(df)
    if latest.empty:
        return EMPTY_FIG
    if selected_group:
        latest = latest[latest["group_name"] == selected_group]
    if latest.empty:
        return EMPTY_FIG

    return px.bar(
        latest,
        x="site_name",
        y="current_price",
        color="site_name",
        text_auto=True,
        title="平台当前价格柱状图",
        hover_data=["product_name", "group_name", "spec_text"],
    )


def build_lowest_price_trend_chart(df: pd.DataFrame, selected_group: str | None = None) -> go.Figure:
    trend = lowest_price_trend(df)
    if trend.empty:
        return EMPTY_FIG
    if selected_group and "price_identity_label" in trend.columns:
        trend = trend[trend["price_identity_label"].astype(str).str.contains(selected_group, regex=False)]
    if trend.empty:
        return EMPTY_FIG

    return px.line(
        trend,
        x="captured_day",
        y="lowest_price",
        color="price_identity_label",
        markers=True,
        title="最低价趋势图",
    )


def build_unit_price_bar_chart(df: pd.DataFrame, selected_category: str | None = None) -> go.Figure:
    latest = summarize_latest_unit_prices(df)
    if latest.empty:
        return EMPTY_FIG
    if selected_category:
        latest = latest[latest["category"] == selected_category]
    if latest.empty:
        return EMPTY_FIG

    latest = latest.copy()
    latest["label"] = latest["brand"].fillna("未指定品牌") + " | " + latest["spec_text"].fillna("未指定规格")
    return px.bar(
        latest,
        x="label",
        y="unit_price",
        color="brand",
        text_auto=True,
        title="单位价对比图",
        hover_data=["category", "product_series", "site_name", "unit_name", "unit_value"],
    )


def build_unit_price_history_chart(df: pd.DataFrame, selected_category: str | None = None) -> go.Figure:
    if df.empty or "unit_price" not in df.columns:
        return EMPTY_FIG

    base = prepare_history(df).dropna(subset=["unit_price"])
    if selected_category:
        base = base[base["category"] == selected_category]
    if base.empty:
        return EMPTY_FIG

    return px.line(
        base,
        x="captured_at",
        y="unit_price",
        color="brand",
        line_group="product_key",
        markers=True,
        title="单位价历史趋势图",
        hover_data=["category", "product_series", "spec_text", "site_name"],
    )


def build_lowest_unit_price_trend_chart(df: pd.DataFrame, selected_category: str | None = None) -> go.Figure:
    trend = lowest_unit_price_trend(df)
    if trend.empty:
        return EMPTY_FIG
    if selected_category:
        trend = trend[trend["category"] == selected_category]
    if trend.empty:
        return EMPTY_FIG

    return px.line(
        trend,
        x="captured_day",
        y="lowest_unit_price",
        color="category",
        markers=True,
        title="最低单位价趋势图",
    )


def build_cross_market_product_trend_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return EMPTY_FIG
    return px.line(
        df,
        x="captured_at",
        y="current_price",
        color="site_name",
        line_group="product_key",
        markers=True,
        title="单品跨市场价格趋势",
        hover_data=["product_name", "market_name", "province", "city", "spec_text"],
    )


def build_single_market_product_trend_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return EMPTY_FIG
    return px.line(
        df,
        x="captured_at",
        y="current_price",
        color="site_name",
        line_group="product_key",
        markers=True,
        title="单市场价格趋势",
        hover_data=["product_name", "market_name", "province", "city", "spec_text"],
    )
