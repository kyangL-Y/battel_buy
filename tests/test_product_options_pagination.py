from __future__ import annotations

import asyncio

import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

import api.app as api_app_module
from api.app import create_app


def _create_procurement_client(monkeypatch):
    monkeypatch.setattr(
        api_app_module,
        "require_procurement_or_admin_user",
        lambda: {
            "id": 1,
            "username": "pagination-buyer",
            "role": "procurement",
            "display_name": "分页采购",
            "is_active": True,
            "supplier_id": None,
            "procurement_supplier_ids": [],
            "supplier_profile": None,
        },
    )
    return TestClient(create_app())


def test_product_options_first_page_uses_fast_page_provider_without_market_summary(monkeypatch):
    called: list[str] = []
    rows = tuple(
        {
            "price_identity_key": f"item-{index}",
            "price_identity_label": f"商品{index}",
            "site_count": 1,
            "price_observation_count": 1,
            "latest_captured_at": "2026-04-10T08:00:00",
            "source_name": "莲菜网",
            "source_category": "调味品",
            "liancai_subcategory": "调味料",
            "image_url": f"https://cdnlcw.liancaiwang.cn/uploads/{index}.jpg",
        }
        for index in range(2)
    )

    def fake_fast_page(**kwargs):
        called.append("fast_page")
        return {"items": list(rows), "total": None, "limit": kwargs["limit"], "offset": kwargs["offset"], "has_more": True}

    def fake_market_summary(*args):
        called.append("market_summary")
        raise AssertionError("first page must not wait for full market summary before returning data")

    monkeypatch.setattr(api_app_module, "_build_fast_product_options_page", fake_fast_page)
    monkeypatch.setattr(api_app_module, "_cached_market_summary_payload", fake_market_summary)

    client = _create_procurement_client(monkeypatch)
    response = client.get("/api/product/options?limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert called == ["fast_page"]
    assert payload["total"] is None
    assert payload["has_more"] is True
    assert [item["price_identity_key"] for item in payload["items"]] == ["item-0", "item-1"]


def test_product_options_endpoint_forwards_source_name_to_fast_page(monkeypatch):
    captured: dict[str, object] = {}

    def fake_fast_page(**kwargs):
        captured.update(kwargs)
        return {
            "items": [
                {
                    "price_identity_key": "item-1",
                    "price_identity_label": "商品1",
                    "source_name": kwargs["source_name"],
                }
            ],
            "total": None,
            "limit": kwargs["limit"],
            "offset": kwargs["offset"],
            "has_more": False,
        }

    monkeypatch.setattr(api_app_module, "_build_fast_product_options_page", fake_fast_page)

    client = _create_procurement_client(monkeypatch)
    response = client.get("/api/product/options?source_name=%E8%8E%B2%E8%8F%9C%E7%BD%91&limit=2")

    assert response.status_code == 200
    assert captured["source_name"] == "莲菜网"
    assert response.json()["items"][0]["source_name"] == "莲菜网"


def test_product_options_endpoint_returns_cached_page_when_fast_db_query_is_unavailable(monkeypatch):
    cached_rows = tuple(
        {
            "price_identity_key": f"cached-{index}",
            "product_name": f"缓存商品{index}",
            "site_count": 1,
            "market_count": 1,
            "latest_captured_at": "2026-04-10T08:00:00",
            "source_name": "莲菜网",
            "source_category": "调味品",
            "liancai_subcategory": "调味料",
            "image_url": f"https://cdnlcw.liancaiwang.cn/uploads/cached-{index}.jpg",
        }
        for index in range(3)
    )

    def failing_fast_page(**kwargs):
        raise OperationalError("SELECT products", {}, Exception("database name resolution failed"))

    monkeypatch.setattr(api_app_module, "_build_fast_product_options_page", failing_fast_page)
    monkeypatch.setattr(api_app_module, "_load_market_summary_disk_cache", lambda cache_path: cached_rows)

    client = _create_procurement_client(monkeypatch)
    response = client.get("/api/product/options?limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["limit"] == 2
    assert payload["offset"] == 0
    assert payload["has_more"] is True
    assert [item["price_identity_key"] for item in payload["items"]] == ["cached-0", "cached-1"]


def test_product_options_endpoint_returns_empty_page_when_fast_db_query_and_cache_are_unavailable(monkeypatch):
    def failing_fast_page(**kwargs):
        raise OperationalError("SELECT products", {}, Exception("database name resolution failed"))

    monkeypatch.setattr(api_app_module, "_build_fast_product_options_page", failing_fast_page)
    monkeypatch.setattr(api_app_module, "_load_market_summary_disk_cache", lambda cache_path: None)

    client = _create_procurement_client(monkeypatch)
    response = client.get("/api/product/options?limit=2")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 2,
        "offset": 0,
        "has_more": False,
    }


def test_product_options_endpoint_uses_market_summary_page_without_full_options_cache(monkeypatch):
    called: list[str] = []
    market_rows = tuple(
        {
            "price_identity_key": f"item-{index}",
            "product_name": f"商品{index}",
            "site_count": 1,
            "market_count": 1,
            "latest_captured_at": "2026-04-10T08:00:00",
            "source_name": "莲菜网",
            "source_category": "调味品",
            "liancai_subcategory": "调味料",
            "image_url": f"https://cdnlcw.liancaiwang.cn/uploads/{index}.jpg",
        }
        for index in range(5)
    )

    def fake_market_summary(*args):
        called.append("market_summary")
        return market_rows

    def fake_options(*args):
        called.append("product_options")
        raise AssertionError("endpoint should not build uncapped product options before pagination")

    monkeypatch.setattr(api_app_module, "_cached_market_summary_payload", fake_market_summary)
    monkeypatch.setattr(api_app_module, "_cached_product_options_payload", fake_options)
    monkeypatch.setattr(api_app_module, "_PRODUCT_OPTIONS_FULL_COMPUTE_LIMIT", 1)
    monkeypatch.setattr(api_app_module, "_visible_supplier_ids_for_price_read", lambda current_user: None)

    client = _create_procurement_client(monkeypatch)
    response = client.get("/api/product/options?limit=2&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert called == ["market_summary"]
    assert payload["total"] == 5
    assert payload["limit"] == 2
    assert payload["offset"] == 1
    assert payload["has_more"] is True
    assert [item["price_identity_key"] for item in payload["items"]] == ["item-1", "item-2"]


def test_product_options_endpoint_paginates_and_reports_total(monkeypatch):
    api_app_module._cached_product_options_payload.cache_clear()
    rows = tuple(
        {
            "price_identity_key": f"item-{index}",
            "product_name": f"商品{index}",
            "site_count": 1,
            "market_count": 1,
            "latest_captured_at": "2026-04-10T08:00:00",
            "source_name": "莲菜网",
            "source_category": "调味品",
            "liancai_subcategory": "调味料",
            "image_url": f"https://cdnlcw.liancaiwang.cn/uploads/{index}.jpg",
        }
        for index in range(5)
    )
    monkeypatch.setattr(api_app_module, "_cached_market_summary_payload", lambda *args: rows)
    monkeypatch.setattr(api_app_module, "_PRODUCT_OPTIONS_FULL_COMPUTE_LIMIT", 0)
    monkeypatch.setattr(api_app_module, "_visible_supplier_ids_for_price_read", lambda current_user: None)

    client = _create_procurement_client(monkeypatch)
    response = client.get("/api/product/options?limit=2&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert payload["limit"] == 2
    assert payload["offset"] == 1
    assert payload["has_more"] is True
    assert [item["price_identity_key"] for item in payload["items"]] == ["item-1", "item-2"]


def test_product_options_keyword_search_uses_filtered_latest_rows(monkeypatch):
    captured: dict[str, object] = {}

    def fake_latest_rows(**kwargs):
        captured.update(kwargs)
        return [
            {
                "product_key": f"salt-{index}",
                "group_name": "美菜网",
                "product_name": f"食用盐{index}",
                "category": "调味品",
                "brand": "",
                "product_series": "",
                "spec_text": "袋",
                "province": "河南省",
                "city": "郑州市",
                "market_name": "郑州",
                "region_label": "郑州",
                "site_name": "美菜网H5 | 推荐商品",
                "source_url": "https://mall-entrance.yunshanmeicai.com",
                "current_price": 2 + index,
                "captured_at": "2026-06-01T08:00:00",
                "image_url": "",
            }
            for index in range(12)
        ]

    def forbidden_full_options(*args):
        raise AssertionError("keyword search must not compute full product options before filtering")

    monkeypatch.setattr(api_app_module, "_fetch_latest_product_rows", fake_latest_rows)
    monkeypatch.setattr(api_app_module, "_cached_product_options_payload", forbidden_full_options)

    client = _create_procurement_client(monkeypatch)
    response = client.get("/api/product/options?city=%E9%83%91%E5%B7%9E&keyword=%E7%9B%90&limit=0")

    assert response.status_code == 200
    payload = response.json()
    assert captured["city"] == "郑州市"
    assert captured["keyword"] == "盐"
    assert payload["total"] == 12
    assert payload["limit"] == 0
    assert payload["has_more"] is False
    assert len(payload["items"]) == 12
    assert payload["items"][0]["price_identity_label"].startswith("食用盐")


def test_product_options_endpoint_defaults_to_bounded_payload(monkeypatch):
    api_app_module._cached_product_options_payload.cache_clear()
    rows = tuple(
        {
            "price_identity_key": f"item-{index}",
            "product_name": f"商品{index}",
            "site_count": 1,
            "market_count": 1,
            "latest_captured_at": "2026-04-10T08:00:00",
            "source_name": "莲菜网",
            "source_category": "调味品",
            "liancai_subcategory": "调味料",
            "image_url": None,
        }
        for index in range(520)
    )
    monkeypatch.setattr(api_app_module, "_cached_market_summary_payload", lambda *args: rows)
    monkeypatch.setattr(api_app_module, "_PRODUCT_OPTIONS_FULL_COMPUTE_LIMIT", 0)
    monkeypatch.setattr(api_app_module, "_visible_supplier_ids_for_price_read", lambda current_user: None)

    client = _create_procurement_client(monkeypatch)
    response = client.get("/api/product/options")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 520
    assert payload["limit"] == 300
    assert payload["offset"] == 0
    assert payload["has_more"] is True
    assert len(payload["items"]) == 300


def test_warm_startup_caches_skips_expensive_product_options(monkeypatch):
    called: list[str] = []

    async def fake_to_thread(func, *args, **kwargs):
        if func is api_app_module._cached_product_options_payload:
            called.append("product_options")
        elif func is api_app_module._cached_market_summary_payload:
            called.append("market_summary")
        elif func is api_app_module.get_location_options:
            called.append("location_options")
        return func(*args, **kwargs)

    monkeypatch.setattr(api_app_module.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(api_app_module, "get_latest_df", lambda: pd.DataFrame({"province": [], "city": []}))
    monkeypatch.setattr(api_app_module, "get_location_options", lambda latest_df: ([], [], {}))
    monkeypatch.setattr(api_app_module, "_cached_market_summary_payload", lambda *args: tuple())
    monkeypatch.setattr(api_app_module, "_cached_product_options_payload", lambda *args: tuple())

    asyncio.run(api_app_module._warm_startup_caches())

    assert called == []


def test_startup_meicai_image_backfill_clears_product_caches(monkeypatch):
    called: list[str] = []

    class DatabaseStub:
        def backfill_meicai_product_image_urls(self):
            called.append("backfill_meicai")
            return 2

    monkeypatch.setattr(api_app_module, "get_db", lambda: DatabaseStub())
    monkeypatch.setattr(api_app_module, "clear_dataframe_cache", lambda: called.append("dataframe_cache"))
    monkeypatch.setattr(api_app_module, "_clear_product_response_caches", lambda: called.append("response_cache"))
    monkeypatch.setattr(api_app_module, "_clear_market_summary_disk_cache", lambda: called.append("disk_cache"))

    assert api_app_module._backfill_startup_meicai_product_image_urls() == 2
    assert called == ["backfill_meicai", "dataframe_cache", "response_cache", "disk_cache"]
