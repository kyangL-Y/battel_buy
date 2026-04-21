from __future__ import annotations

import pandas as pd

from api import deps
from analysis.metrics import filter_by_location, get_location_options


class _FakeDb:
    def __init__(self) -> None:
        self.history_calls = 0
        self.latest_calls = 0
        self.trend_history_calls = 0
        self.trend_history_keys_calls = 0
        self.last_product_keys: list[str] = []
        self.price_record_count_calls = 0

    def get_price_history(self) -> pd.DataFrame:
        self.history_calls += 1
        return pd.DataFrame([{"value": 1}])

    def get_trend_history(self) -> pd.DataFrame:
        self.trend_history_calls += 1
        return pd.DataFrame([{"captured_at": "2026-04-11T10:00:00", "current_price": 1.0}])

    def get_trend_history_for_product_keys(self, product_keys: list[str]) -> pd.DataFrame:
        self.trend_history_keys_calls += 1
        self.last_product_keys = list(product_keys)
        return pd.DataFrame(
            [
                {
                    "product_key": product_key,
                    "group_name": "土豆",
                    "product_name": "土豆",
                    "category": "蔬菜类" if product_key == "sku-potato-pfsc" else "",
                    "brand": "",
                    "product_series": "",
                    "spec_text": "公斤",
                    "compare_key": "",
                    "captured_at": "2026-04-11T10:00:00",
                    "current_price": 1.0,
                }
                for product_key in product_keys
            ]
        )

    def get_latest_records(self) -> pd.DataFrame:
        self.latest_calls += 1
        return pd.DataFrame(
            [
                {
                    "product_key": "sku-potato-pfsc",
                    "group_name": "土豆",
                    "product_name": "土豆",
                    "category": "蔬菜类",
                    "brand": "",
                    "product_series": "",
                    "spec_text": "公斤",
                    "compare_key": "",
                    "captured_at": "2026-04-11T11:00:00",
                    "current_price": 2.0,
                },
                {
                    "product_key": "sku-potato-wb",
                    "group_name": "土豆",
                    "product_name": "土豆",
                    "category": "",
                    "brand": "",
                    "product_series": "",
                    "spec_text": "公斤",
                    "compare_key": "",
                    "captured_at": "2026-04-11T11:00:00",
                    "current_price": 2.2,
                }
            ]
        )

    def get_price_record_count(self) -> int:
        self.price_record_count_calls += 1
        return 2


def test_history_df_uses_cache(monkeypatch):
    fake_db = _FakeDb()
    deps.clear_dataframe_cache()
    monkeypatch.setattr(deps, "get_db", lambda: fake_db)

    first = deps.get_history_df()
    second = deps.get_history_df()

    assert fake_db.history_calls == 1
    assert first.equals(second)


def test_history_identity_df_uses_trend_history_cache(monkeypatch):
    fake_db = _FakeDb()
    deps.clear_dataframe_cache()
    monkeypatch.setattr(deps, "get_db", lambda: fake_db)

    first = deps.get_history_identity_df()
    second = deps.get_history_identity_df()

    assert fake_db.trend_history_calls == 1
    assert first.equals(second)


def test_signal_history_df_uses_trend_history_cache(monkeypatch):
    fake_db = _FakeDb()
    deps.clear_dataframe_cache()
    monkeypatch.setattr(deps, "get_db", lambda: fake_db)

    first = deps.get_signal_history_df()
    second = deps.get_signal_history_df()

    assert fake_db.trend_history_calls == 1
    assert first.equals(second)


def test_product_history_identity_df_queries_only_matched_product_keys(monkeypatch):
    fake_db = _FakeDb()
    deps.clear_dataframe_cache()
    monkeypatch.setattr(deps, "get_db", lambda: fake_db)

    first = deps.get_product_history_identity_df("土豆|公斤")
    second = deps.get_product_history_identity_df("土豆|公斤")

    assert fake_db.latest_calls == 1
    assert fake_db.trend_history_keys_calls == 1
    assert set(fake_db.last_product_keys) == {"sku-potato-pfsc", "sku-potato-wb"}
    assert first.equals(second)


def test_latest_df_cache_refreshes_after_manual_clear(monkeypatch):
    fake_db = _FakeDb()
    deps.clear_dataframe_cache()
    monkeypatch.setattr(deps, "get_db", lambda: fake_db)

    deps.get_latest_df()
    deps.clear_dataframe_cache()
    deps.get_latest_df()

    assert fake_db.latest_calls == 2


def test_location_options_infer_pfsc_market_prefixes():
    df = pd.DataFrame(
        [
            {
                "site_name": "PFSC | 南充川北农产品交易有限公司",
                "province": pd.NA,
                "city": pd.NA,
                "market_name": "南充川北农产品交易有限公司",
                "region_label": pd.NA,
            },
            {
                "site_name": "PFSC | 新疆兵团第五师三和农副产品综合批发市场",
                "province": pd.NA,
                "city": pd.NA,
                "market_name": "新疆兵团第五师三和农副产品综合批发市场",
                "region_label": pd.NA,
            },
        ]
    )

    provinces, cities, _ = get_location_options(df)

    assert "新疆" in provinces
    assert "南充" in cities
    assert "新疆" in cities


def test_filter_by_location_matches_inferred_pfsc_city():
    df = pd.DataFrame(
        [
            {
                "site_name": "PFSC | 南充川北农产品交易有限公司",
                "province": pd.NA,
                "city": pd.NA,
                "market_name": "南充川北农产品交易有限公司",
                "region_label": pd.NA,
                "product_name": "青椒",
            },
            {
                "site_name": "PFSC | 天津武清大沙河批发市场",
                "province": "天津市",
                "city": "天津市",
                "market_name": "天津武清大沙河批发市场",
                "region_label": "天津市",
                "product_name": "青椒",
            },
        ]
    )

    filtered = filter_by_location(df, selected_city="南充")

    assert len(filtered) == 1
    assert filtered.iloc[0]["market_name"] == "南充川北农产品交易有限公司"


def test_location_options_promote_city_to_standard_province():
    df = pd.DataFrame(
        [
            {
                "site_name": "PFSC | 乌鲁木齐北园春果业经营管理有限责任公司",
                "province": "乌鲁木齐市",
                "city": "乌鲁木齐市",
                "market_name": "乌鲁木齐北园春果业经营管理有限责任公司",
                "region_label": "乌鲁木齐市",
            }
        ]
    )

    provinces, cities, _ = get_location_options(df)

    assert "新疆" in provinces
    assert "乌鲁木齐" in cities


def test_location_options_extract_standard_city_from_market_name():
    df = pd.DataFrame(
        [
            {
                "site_name": "PFSC | 浙江嘉兴蔬菜批发交易市场",
                "province": pd.NA,
                "city": pd.NA,
                "market_name": "浙江嘉兴蔬菜批发交易市场",
                "region_label": pd.NA,
            },
            {
                "site_name": "PFSC | 运城蔬菜批发市场有限公司",
                "province": pd.NA,
                "city": pd.NA,
                "market_name": "运城蔬菜批发市场有限公司",
                "region_label": pd.NA,
            },
        ]
    )

    provinces, cities, _ = get_location_options(df)

    assert "浙江省" in provinces
    assert "山西省" in provinces
    assert "嘉兴" in cities
    assert "运城" in cities


def test_location_options_do_not_leak_market_entity_name_as_city():
    df = pd.DataFrame(
        [
            {
                "site_name": "PFSC | 北海果业砀山惠丰市场有限公司",
                "province": pd.NA,
                "city": pd.NA,
                "market_name": "北海果业砀山惠丰市场有限公司",
                "region_label": pd.NA,
            }
        ]
    )

    _, cities, _ = get_location_options(df)

    assert "北海果业砀山惠丰" not in cities
