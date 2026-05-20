from __future__ import annotations

import asyncio

import pandas as pd
from fastapi.testclient import TestClient

import api.app as api_app_module
from api.app import create_app


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

    client = TestClient(create_app())
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

    client = TestClient(create_app())
    response = client.get("/api/product/options?source_name=%E8%8E%B2%E8%8F%9C%E7%BD%91&limit=2")

    assert response.status_code == 200
    assert captured["source_name"] == "莲菜网"
    assert response.json()["items"][0]["source_name"] == "莲菜网"


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

    client = TestClient(create_app())
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

    client = TestClient(create_app())
    response = client.get("/api/product/options?limit=2&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert payload["limit"] == 2
    assert payload["offset"] == 1
    assert payload["has_more"] is True
    assert [item["price_identity_key"] for item in payload["items"]] == ["item-1", "item-2"]


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

    client = TestClient(create_app())
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
