import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
import pandas as pd

import api.app as api_app_module
from api.app import create_app


def test_api_health():
    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


class _FakeCrawlManager:
    def __init__(self) -> None:
        self.schedule_enabled = False

    def start(self) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def get_status(self) -> dict:
        return {
            "is_running": False,
            "last_run_source": "manual",
            "last_started_at": None,
            "last_finished_at": "2026-04-11T09:00:00+08:00",
            "last_success_at": "2026-04-11T09:00:00+08:00",
            "last_error": None,
            "current_source_name": None,
            "current_source_index": 0,
            "current_source_progress": 0.0,
            "current_source_detail": None,
            "completed_sources": 3,
            "progress_percent": 100,
            "last_total_sources": 3,
            "last_total_results": 120,
            "last_success_count": 120,
            "last_failed_count": 0,
            "next_run_at": None,
            "schedule_enabled": self.schedule_enabled,
            "schedule_interval_seconds": 86400,
            "schedule_fetch_mode": "requests",
        }

    def trigger_run(self, source: str = "manual") -> tuple[bool, dict]:
        item = self.get_status()
        item["is_running"] = True
        item["last_run_source"] = source
        return True, item

    def update_schedule(self, *, enabled: bool | None = None, interval_seconds: int | None = None, fetch_mode: str | None = None) -> dict:
        self.schedule_enabled = bool(enabled)
        item = self.get_status()
        item["schedule_enabled"] = self.schedule_enabled
        if interval_seconds is not None:
            item["schedule_interval_seconds"] = interval_seconds
        if fetch_mode is not None:
            item["schedule_fetch_mode"] = fetch_mode
        return item


def test_crawl_status_endpoint(monkeypatch):
    monkeypatch.setattr(api_app_module, "get_crawl_manager", lambda: _FakeCrawlManager())
    client = TestClient(create_app())

    response = client.get("/api/crawl/status")

    assert response.status_code == 200
    assert response.json()["item"]["last_total_sources"] == 3
    assert response.json()["item"]["progress_percent"] == 100
    assert "current_source_progress" in response.json()["item"]
    assert "current_source_detail" in response.json()["item"]


def test_crawl_run_endpoint(monkeypatch):
    monkeypatch.setattr(api_app_module, "get_crawl_manager", lambda: _FakeCrawlManager())
    client = TestClient(create_app())

    response = client.post("/api/crawl/run")

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert response.json()["item"]["is_running"] is True
    assert response.json()["item"]["progress_percent"] == 100


def test_crawl_schedule_endpoint(monkeypatch):
    fake_manager = _FakeCrawlManager()
    monkeypatch.setattr(api_app_module, "get_crawl_manager", lambda: fake_manager)
    client = TestClient(create_app())

    response = client.post(
        "/api/crawl/schedule",
        json={"enabled": True, "interval_seconds": 86400, "fetch_mode": "requests"},
    )

    assert response.status_code == 200
    assert response.json()["item"]["schedule_enabled"] is True
    assert response.json()["item"]["schedule_interval_seconds"] == 86400


def test_source_coverage_endpoint_includes_local_source_metadata(monkeypatch):
    class _FakeDb:
        def get_source_coverage_summary(self):
            return pd.DataFrame(
                [
                    {
                        "source_url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                        "product_key_count": 120,
                        "comparable_item_count": 80,
                        "source_item_count": 80,
                        "market_count": 12,
                        "price_record_count": 500,
                        "latest_capture": "2026-04-18T12:00:00",
                        "failed_count": 0,
                        "last_failure": None,
                    }
                ]
            )

    def fake_load_json_config(path):
        text = str(path)
        if text.endswith("products.json"):
            return [
                {
                    "product_name": "万邦国际行情",
                    "source_name": "万邦国际",
                    "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                    "enabled": True,
                    "market_scope": "全国公开市场",
                    "market_category": "综合行情",
                    "channel": "公开接口",
                    "notes": "已接入",
                },
                {
                    "product_name": "莲菜网小程序·干调类",
                    "source_name": "莲菜网",
                    "url": "https://miniapp-placeholder.local/lencai/dried-goods",
                    "enabled": False,
                    "market_scope": "本地市场",
                    "market_category": "干调类",
                    "channel": "微信小程序",
                    "strategy": "browser_assisted",
                    "notes": "待接入",
                },
            ]
        return []

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    monkeypatch.setattr(api_app_module, "load_json_config", fake_load_json_config)
    client = TestClient(create_app())

    response = client.get("/api/source/coverage")

    assert response.status_code == 200
    rows = response.json()["items"]
    local_row = next(item for item in rows if item["configured_name"] == "莲菜网小程序·干调类")
    assert local_row["status"] == "待接入"
    assert local_row["market_scope"] == "本地市场"
    assert local_row["market_category"] == "干调类"
    assert local_row["channel"] == "微信小程序"


def test_menu_plan_endpoint_accepts_preferred_location(monkeypatch):
    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())
    monkeypatch.setattr(api_app_module, "get_runtime_settings", lambda: {"ai": {"enabled": False}})
    captured_kwargs: dict[str, object] = {}

    def fake_build_procurement_plan(menu_items, latest_df, **kwargs):
        captured_kwargs.update(kwargs)
        return pd.DataFrame(), pd.DataFrame()

    monkeypatch.setattr(api_app_module, "build_procurement_plan", fake_build_procurement_plan)
    client = TestClient(create_app())

    response = client.post(
        "/api/menu/plan",
        json={
            "menu_text": "蒜蓉西兰花",
            "diners": 100,
            "tables": 10,
            "preferred_location": "当前位置",
        },
    )

    assert response.status_code == 200
    assert captured_kwargs["preferred_location"] == "当前位置"


def test_ai_search_endpoint_returns_answer(monkeypatch):
    monkeypatch.setattr(api_app_module, "get_runtime_settings", lambda: {"ai": {"enabled": True}})
    monkeypatch.setattr(api_app_module, "run_search_query", lambda query, runtime_config=None: f"搜索结果: {query}")
    client = TestClient(create_app())

    response = client.post("/api/ai/search", json={"query": "今天的新闻"})

    assert response.status_code == 200
    assert response.json() == {"answer": "搜索结果: 今天的新闻"}


def test_product_endpoints_forward_city_and_province(monkeypatch):
    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())
    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())
    captured: dict[str, dict] = {}

    def fake_selector(df, selected_province=None, selected_city=None):
        captured["selector"] = {"province": selected_province, "city": selected_city}
        return pd.DataFrame()

    def fake_summary(df, identity_key, selected_province=None, selected_city=None):
        captured["summary"] = {"province": selected_province, "city": selected_city, "identity_key": identity_key}
        return {}

    def fake_cross_trend(df, identity_key, selected_province=None, selected_city=None):
        captured["cross_trend"] = {"province": selected_province, "city": selected_city, "identity_key": identity_key}
        return pd.DataFrame()

    monkeypatch.setattr(api_app_module, "build_single_product_selector_options", fake_selector)
    monkeypatch.setattr(api_app_module, "compute_single_product_summary", fake_summary)
    monkeypatch.setattr(api_app_module, "build_cross_market_product_trend", fake_cross_trend)
    client = TestClient(create_app())

    options_response = client.get("/api/product/options?province=北京市&city=北京市")
    summary_response = client.get("/api/product/test-key/summary?province=北京市&city=北京市")
    trend_response = client.get("/api/product/test-key/trend?mode=cross_market&province=北京市&city=北京市")

    assert options_response.status_code == 200
    assert summary_response.status_code == 200
    assert trend_response.status_code == 200
    assert captured["selector"] == {"province": "北京市", "city": "北京市"}
    assert captured["summary"]["province"] == "北京市"
    assert captured["summary"]["city"] == "北京市"
    assert captured["cross_trend"]["province"] == "北京市"
    assert captured["cross_trend"]["city"] == "北京市"


def test_product_endpoints_use_identity_scoped_history_lookup(monkeypatch):
    captured: dict[str, str] = {}

    def fake_history(identity_key: str) -> pd.DataFrame:
        captured["identity_key"] = identity_key
        return pd.DataFrame()

    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", fake_history)
    monkeypatch.setattr(api_app_module, "compute_single_product_summary", lambda *args, **kwargs: {})
    monkeypatch.setattr(api_app_module, "build_cross_market_product_trend", lambda *args, **kwargs: pd.DataFrame())
    client = TestClient(create_app())

    summary_response = client.get("/api/product/%E5%9C%9F%E8%B1%86%7C%E8%94%AC%E8%8F%9C%E7%B1%BB/summary")
    trend_response = client.get("/api/product/%E5%9C%9F%E8%B1%86%7C%E8%94%AC%E8%8F%9C%E7%B1%BB/trend")

    assert summary_response.status_code == 200
    assert trend_response.status_code == 200
    assert captured["identity_key"] == "土豆|蔬菜类"


def test_location_options_endpoint_returns_province_city_map(monkeypatch):
    latest_df = pd.DataFrame(
        [
            {"product_name": "白菜", "province": "北京市", "city": "北京市"},
            {"product_name": "萝卜", "province": "河南省", "city": "郑州市"},
            {"product_name": "蒜薹", "province": "河南省", "city": "洛阳市"},
        ]
    )
    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: latest_df)
    client = TestClient(create_app())

    response = client.get("/api/location/options")

    assert response.status_code == 200
    assert response.json() == {
        "provinces": ["北京市", "河南省"],
        "cities": ["北京市", "洛阳", "郑州"],
        "province_city_map": {
            "北京市": ["北京市"],
            "河南省": ["洛阳", "郑州"],
        },
    }


def test_signals_overview_endpoint_returns_decision_payload(monkeypatch):
    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())
    monkeypatch.setattr(api_app_module, "get_signal_history_df", lambda: pd.DataFrame())
    monkeypatch.setattr(
        api_app_module,
        "build_signals_overview",
        lambda latest_df, history_df, province=None, city=None, focus=None: {
            "generated_at": "2026-04-18",
            "scope": {"province": province, "city": city, "focus": focus},
            "headline": "北京市 当前适合先讲机会再讲风险",
            "overview_metrics": [{"label": "信号总数", "value": "3", "detail": "mock"}],
            "top_opportunities": [
                {
                    "identity_key": "土豆",
                    "product_name": "土豆",
                    "signal_code": "overview",
                    "signal_level": "high",
                    "timing_score": 81,
                    "risk_score": 38,
                    "confidence": 79,
                    "recommended_action": "立即采购",
                    "reason_summary": "mock opportunity",
                }
            ],
            "top_risks": [],
            "recommended_actions": [{"title": "优先锁定土豆", "description": "mock", "action": "立即采购"}],
            "source_health": {"status": "healthy"},
            "alert_count": 1,
            "alert_items": [],
        },
    )
    client = TestClient(create_app())

    response = client.get("/api/signals/overview?province=北京市&city=北京市&focus=土豆")

    assert response.status_code == 200
    assert response.json()["scope"] == {"province": "北京市", "city": "北京市", "focus": "土豆"}
    assert response.json()["top_opportunities"][0]["identity_key"] == "土豆"


def test_signal_detail_endpoint_returns_404_when_missing(monkeypatch):
    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())
    monkeypatch.setattr(api_app_module, "build_product_signal_detail", lambda *args, **kwargs: {})
    client = TestClient(create_app())

    response = client.get("/api/signals/土豆")

    assert response.status_code == 404


def test_procurement_recommend_and_sales_endpoints(monkeypatch):
    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame())
    monkeypatch.setattr(api_app_module, "get_runtime_settings", lambda: {"ai": {"enabled": False}})
    monkeypatch.setattr(api_app_module, "get_db", lambda: type("FakeDb", (), {"get_price_record_count": lambda self: 42})())
    monkeypatch.setattr(
        api_app_module,
        "build_procurement_recommendation",
        lambda **kwargs: {
            "summary": {"menu_count": 1, "recommendation_count": 1, "matched_count": 1, "pending_count": 0, "total_cost": 88.0},
            "ingredient_items": [{"menu_name": "蒜蓉西兰花", "ingredient_name": "西兰花"}],
            "items": [
                {
                    "menu_name": "蒜蓉西兰花",
                    "ingredient_name": "西兰花",
                    "identity_key": None,
                    "price_status": "已匹配报价",
                    "estimated_cost": 88.0,
                    "reference_price": 8.8,
                    "recommended_market": "北京新发地",
                    "recommended_site": "北京新发地",
                    "backup_market": None,
                    "backup_site": None,
                    "timing_score": 78,
                    "risk_score": 36,
                    "confidence": 82,
                    "signal_level": "high",
                    "recommended_action": "立即锁价",
                    "reason_summary": "mock recommendation",
                }
            ],
        },
    )
    monkeypatch.setattr(
        api_app_module,
        "build_sales_demo_content",
        lambda latest_df, history_df, scene=None, record_count=None: {
            "scene": scene or "default",
            "hero": {"title": "demo"},
            "proof_points": [{"label": "历史记录", "value": str(record_count or 0)}],
            "scenes": [{"title": "老板驾驶舱", "description": "demo", "highlight": "mock"}],
            "storyline": ["a", "b"],
        },
    )
    monkeypatch.setattr(
        api_app_module,
        "build_pricing_packages",
        lambda: {
            "items": [
                {
                    "name": "经营决策版",
                    "price_band": "主推报价",
                    "target": "采购团队",
                    "recommended": True,
                    "features": ["经营信号"],
                    "cta": "立即报价",
                }
            ]
        },
    )
    client = TestClient(create_app())

    recommend_response = client.post("/api/procurement/recommend", json={"menu_text": "蒜蓉西兰花", "diners": 20, "tables": 2})
    demo_response = client.get("/api/sales/demo-content?scene=sales")
    pricing_response = client.get("/api/pricing/packages")

    assert recommend_response.status_code == 200
    assert recommend_response.json()["summary"]["matched_count"] == 1
    assert demo_response.status_code == 200
    assert demo_response.json()["scene"] == "sales"
    assert pricing_response.status_code == 200
    assert pricing_response.json()["items"][0]["recommended"] is True


def test_suppliers_endpoint_returns_supplier_list(monkeypatch):
    class _FakeDb:
        def get_suppliers(self, active_only=True):
            assert active_only is True
            return pd.DataFrame(
                [
                    {
                        "id": 1,
                        "supplier_name": "莲菜档口A",
                        "contact_name": "老王",
                        "contact_phone": "13800000000",
                        "market_scope": "本地市场",
                        "market_category": "干调类",
                        "channel": "微信小程序",
                        "notes": None,
                        "is_active": 1,
                        "created_at": "2026-04-20T09:00:00",
                        "updated_at": "2026-04-20T09:00:00",
                        "quote_count": 3,
                        "latest_quoted_at": "2026-04-20T10:00:00",
                    }
                ]
            )

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    client = TestClient(create_app())

    response = client.get("/api/suppliers")

    assert response.status_code == 200
    assert response.json()["items"][0]["supplier_name"] == "莲菜档口A"
    assert response.json()["items"][0]["quote_count"] == 3


def test_suppliers_overview_endpoint_returns_category_and_recent_quotes(monkeypatch):
    class _FakeDb:
        def get_suppliers(self, active_only=False):
            assert active_only is False
            return pd.DataFrame(
                [
                    {
                        "id": 1,
                        "supplier_name": "莲菜档口A",
                        "contact_name": "老王",
                        "contact_phone": "13800000000",
                        "market_scope": "本地市场",
                        "market_category": "干调类",
                        "channel": "微信小程序",
                        "notes": None,
                        "is_active": 1,
                        "created_at": "2026-04-20T09:00:00",
                        "updated_at": "2026-04-20T09:00:00",
                        "quote_count": 3,
                        "latest_quoted_at": "2026-04-20T10:00:00",
                    },
                    {
                        "id": 2,
                        "supplier_name": "蔬菜档口B",
                        "contact_name": "小李",
                        "contact_phone": "13900000000",
                        "market_scope": "本地市场",
                        "market_category": "蔬菜类",
                        "channel": "门店直报",
                        "notes": None,
                        "is_active": 0,
                        "created_at": "2026-04-20T09:10:00",
                        "updated_at": "2026-04-20T09:10:00",
                        "quote_count": 1,
                        "latest_quoted_at": "2026-04-20T09:30:00",
                    },
                ]
            )

        def get_supplier_category_summary(self):
            return pd.DataFrame(
                [
                    {
                        "market_category": "干调类",
                        "supplier_count": 1,
                        "active_supplier_count": 1,
                        "quote_count": 3,
                        "latest_quoted_at": "2026-04-20T10:00:00",
                    },
                    {
                        "market_category": "蔬菜类",
                        "supplier_count": 1,
                        "active_supplier_count": 0,
                        "quote_count": 1,
                        "latest_quoted_at": "2026-04-20T09:30:00",
                    },
                ]
            )

        def get_recent_supplier_quotes(self, limit=12):
            assert limit == 8
            return pd.DataFrame(
                [
                    {
                        "supplier_id": 1,
                        "supplier_name": "莲菜档口A",
                        "contact_name": "老王",
                        "contact_phone": "13800000000",
                        "market_scope": "本地市场",
                        "supplier_market_category": "干调类",
                        "supplier_channel": "微信小程序",
                        "price_identity_key": "香菇|干调类|500g",
                        "price_identity_label": "香菇 | 干调类 | 500g",
                        "product_name": "香菇",
                        "category": "干调类",
                        "spec_text": "500g",
                        "market_category": "干调类",
                        "channel": "微信小程序",
                        "quote_price": 17.9,
                        "quote_unit": "斤",
                        "box_price": 214.8,
                        "tax_price": None,
                        "inventory_status": "现货",
                        "remarks": "上午更新",
                        "quoted_by": "老王",
                        "quoted_at": "2026-04-20T10:00:00",
                    }
                ]
            )

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    client = TestClient(create_app())

    response = client.get("/api/suppliers/overview?limit=8")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["supplier_count"] == 2
    assert payload["summary"]["active_supplier_count"] == 1
    assert payload["summary"]["inactive_supplier_count"] == 1
    assert payload["summary"]["category_count"] == 2
    assert payload["summary"]["total_quote_count"] == 4
    assert payload["category_items"][0]["market_category"] == "干调类"
    assert payload["recent_quotes"][0]["supplier_name"] == "莲菜档口A"


def test_create_supplier_price_endpoint_accepts_supplier_name(monkeypatch):
    captured: dict[str, object] = {}

    class _FakeDb:
        def upsert_supplier(self, **kwargs):
            captured["supplier"] = kwargs
            return 9

        def insert_supplier_price_record(self, **kwargs):
            captured["quote"] = kwargs
            return 12

        def get_supplier_price_record(self, record_id):
            assert record_id == 12
            return pd.DataFrame(
                [
                    {
                        "supplier_id": 9,
                        "supplier_name": "莲菜档口A",
                        "contact_name": "老王",
                        "contact_phone": None,
                        "market_scope": "本地市场",
                        "supplier_market_category": "干调类",
                        "supplier_channel": "微信小程序",
                        "price_identity_key": "香菇|干调类|500g",
                        "price_identity_label": "香菇 | 干调类 | 500g",
                        "product_name": "香菇",
                        "category": "干调类",
                        "spec_text": "500g",
                        "market_category": "干调类",
                        "channel": "微信小程序",
                        "quote_price": 17.9,
                        "quote_unit": "斤",
                        "box_price": 214.8,
                        "tax_price": None,
                        "inventory_status": "现货",
                        "remarks": "上午更新",
                        "quoted_by": "老王",
                        "quoted_at": "2026-04-20T10:00:00",
                    }
                ]
            )

        def get_latest_supplier_quotes(self, identity_key):
            assert identity_key == "香菇|干调类|500g"
            return pd.DataFrame(
                [
                    {
                        "supplier_id": 9,
                        "supplier_name": "莲菜档口A",
                        "contact_name": "老王",
                        "contact_phone": None,
                        "market_scope": "本地市场",
                        "supplier_market_category": "干调类",
                        "supplier_channel": "微信小程序",
                        "price_identity_label": "香菇 | 干调类 | 500g",
                        "product_name": "香菇",
                        "category": "干调类",
                        "spec_text": "500g",
                        "market_category": "干调类",
                        "channel": "微信小程序",
                        "quote_price": 17.9,
                        "quote_unit": "斤",
                        "box_price": 214.8,
                        "tax_price": None,
                        "inventory_status": "现货",
                        "remarks": "上午更新",
                        "quoted_by": "老王",
                        "quoted_at": "2026-04-20T10:00:00",
                    }
                ]
            )

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    monkeypatch.setattr(api_app_module, "get_product_keys_for_identity", lambda _: ["mock-key"])
    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame())
    client = TestClient(create_app())

    response = client.post(
        "/api/supplier-prices",
        json={
            "price_identity_key": "香菇|干调类|500g",
            "supplier_name": "莲菜档口A",
            "contact_name": "老王",
            "market_scope": "本地市场",
            "market_category": "干调类",
            "channel": "微信小程序",
            "product_name": "香菇",
            "price_identity_label": "香菇 | 干调类 | 500g",
            "quote_price": 17.9,
            "quote_unit": "斤",
            "box_price": 214.8,
            "inventory_status": "现货",
            "remarks": "上午更新",
            "quoted_by": "老王",
            "quoted_at": "2026-04-20T10:00:00",
        },
    )

    assert response.status_code == 200
    assert captured["supplier"]["supplier_name"] == "莲菜档口A"
    assert captured["quote"]["quote_price"] == 17.9
    assert response.json()["item"]["comparison_label"] == "待补公开行情"


def test_product_supplier_quotes_endpoint_returns_comparison_payload(monkeypatch):
    class _FakeDb:
        def get_latest_supplier_quotes(self, identity_key):
            assert identity_key == "香菇|干调类|500g"
            return pd.DataFrame(
                [
                    {
                        "supplier_id": 9,
                        "supplier_name": "莲菜档口A",
                        "contact_name": "老王",
                        "contact_phone": None,
                        "market_scope": "本地市场",
                        "supplier_market_category": "干调类",
                        "supplier_channel": "微信小程序",
                        "price_identity_label": "香菇 | 干调类 | 500g",
                        "product_name": "香菇",
                        "category": "干调类",
                        "spec_text": "500g",
                        "market_category": "干调类",
                        "channel": "微信小程序",
                        "quote_price": 17.9,
                        "quote_unit": "斤",
                        "box_price": 214.8,
                        "tax_price": 18.3,
                        "inventory_status": "现货",
                        "remarks": "上午更新",
                        "quoted_by": "老王",
                        "quoted_at": "2026-04-20T10:00:00",
                    }
                ]
            )

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    monkeypatch.setattr(api_app_module, "get_product_history_identity_df", lambda _: pd.DataFrame([{"demo": True}]))
    monkeypatch.setattr(
        api_app_module,
        "compute_single_product_summary",
        lambda df, identity_key, selected_province=None, selected_city=None: {
            "product_name": "香菇 | 干调类 | 500g",
            "current_lowest_price": 18.5,
            "average_price": 19.2,
        },
    )
    client = TestClient(create_app())

    response = client.get("/api/product/%E9%A6%99%E8%8F%87%7C%E5%B9%B2%E8%B0%83%E7%B1%BB%7C500g/supplier-quotes")

    assert response.status_code == 200
    assert response.json()["summary"]["supplier_count"] == 1
    assert response.json()["summary"]["market_lowest_price"] == 18.5
    assert response.json()["items"][0]["comparison_label"] == "低于公开最低价 0.60"


def test_update_supplier_endpoint_returns_latest_supplier_payload(monkeypatch):
    captured: dict[str, object] = {}

    class _FakeDb:
        def upsert_supplier(self, **kwargs):
            captured["payload"] = kwargs
            return 5

        def get_suppliers(self, active_only=False):
            assert active_only is False
            return pd.DataFrame(
                [
                    {
                        "id": 5,
                        "supplier_name": "莲菜档口B",
                        "contact_name": "小李",
                        "contact_phone": "13900000000",
                        "market_scope": "本地市场",
                        "market_category": "蔬菜类",
                        "channel": "门店直报",
                        "notes": "上午更新",
                        "is_active": 0,
                        "created_at": "2026-04-20T09:00:00",
                        "updated_at": "2026-04-20T10:00:00",
                        "quote_count": 4,
                        "latest_quoted_at": "2026-04-20T10:00:00",
                    }
                ]
            )

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    client = TestClient(create_app())

    response = client.put(
        "/api/suppliers/5",
        json={
            "supplier_name": "莲菜档口B",
            "contact_name": "小李",
            "contact_phone": "13900000000",
            "market_scope": "本地市场",
            "market_category": "蔬菜类",
            "channel": "门店直报",
            "notes": "上午更新",
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert captured["payload"]["supplier_id"] == 5
    assert response.json()["is_active"] is False
    assert response.json()["supplier_name"] == "莲菜档口B"


def test_supplier_quotes_endpoint_returns_supplier_history(monkeypatch):
    class _FakeDb:
        def get_supplier_quote_records(self, supplier_id, limit=20):
            assert supplier_id == 5
            assert limit == 10
            return pd.DataFrame(
                [
                    {
                        "supplier_id": 5,
                        "supplier_name": "莲菜档口B",
                        "contact_name": "小李",
                        "contact_phone": "13900000000",
                        "market_scope": "本地市场",
                        "supplier_market_category": "蔬菜类",
                        "supplier_channel": "门店直报",
                        "price_identity_key": "菠菜|蔬菜类|斤",
                        "price_identity_label": "菠菜 | 蔬菜类 | 斤",
                        "product_name": "菠菜",
                        "category": "蔬菜类",
                        "spec_text": "斤",
                        "market_category": "蔬菜类",
                        "channel": "门店直报",
                        "quote_price": 4.8,
                        "quote_unit": "斤",
                        "box_price": None,
                        "tax_price": None,
                        "inventory_status": "现货",
                        "remarks": "上午更新",
                        "quoted_by": "小李",
                        "quoted_at": "2026-04-20T10:00:00",
                    }
                ]
            )

    monkeypatch.setattr(api_app_module, "get_db", lambda: _FakeDb())
    client = TestClient(create_app())

    response = client.get("/api/suppliers/5/quotes?limit=10")

    assert response.status_code == 200
    assert response.json()["items"][0]["supplier_name"] == "莲菜档口B"
    assert response.json()["items"][0]["price_identity_key"] == "菠菜|蔬菜类|斤"
