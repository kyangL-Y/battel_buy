import json

from datetime import datetime

from api.crawl_manager import CrawlManager, _next_daily_run_at, build_crawler_service
from utils.source_config import filter_sources_by_region


def test_crawl_manager_progress_callback_updates_status(tmp_path):
    runtime_path = tmp_path / "runtime.json"
    products_path = tmp_path / "products.json"
    runtime_path.write_text(
        json.dumps({"schedule": {"enabled": True, "interval_seconds": 86400, "fetch_mode": "requests"}}),
        encoding="utf-8",
    )
    products_path.write_text("[]", encoding="utf-8")

    manager = CrawlManager(runtime_path=runtime_path, products_path=products_path)
    with manager._lock:
        manager._state["is_running"] = True
        manager._state["current_source_name"] = "万邦国际行情"
        manager._state["current_source_index"] = 2
        manager._state["completed_sources"] = 1
        manager._state["last_total_sources"] = 3

    callback = manager._make_progress_callback(3)
    callback({"progress": 0.5, "detail": "接口分页 12/24"})

    status = manager.get_status()
    assert status["current_source_progress"] == 0.5
    assert status["current_source_detail"] == "接口分页 12/24"
    assert status["progress_percent"] == 50


def test_build_crawler_service_uses_low_load_defaults():
    runtime_settings = {
        "crawler": {
            "default_timeout": 12,
            "default_retries": 1,
            "default_delay": 1.5,
            "fallback_to_playwright": False,
            "enable_api_discovery": False,
            "public_source_max_workers": 1,
            "playwright_block_resource_types": ["image", "media", "font"],
        },
        "schedule": {"fetch_mode": "requests"},
    }

    service = build_crawler_service("requests", runtime_settings)

    assert service.fallback_to_playwright is False
    assert service.enable_api_discovery is False
    assert service.public_source_crawler.default_max_workers == 1


def test_next_daily_run_at_uses_today_or_tomorrow():
    now = datetime.fromisoformat("2026-05-23T02:00:00+08:00")
    next_run = _next_daily_run_at(now, "03:30")
    assert next_run.isoformat() == "2026-05-23T03:30:00+08:00"

    after_run_time = datetime.fromisoformat("2026-05-23T04:00:00+08:00")
    next_day_run = _next_daily_run_at(after_run_time, "03:30")
    assert next_day_run.isoformat() == "2026-05-24T03:30:00+08:00"


def test_crawl_manager_skips_disabled_sources(tmp_path, monkeypatch):
    runtime_path = tmp_path / "runtime.json"
    products_path = tmp_path / "products.json"
    runtime_path.write_text(
        json.dumps({"schedule": {"enabled": False, "interval_seconds": 86400, "fetch_mode": "requests"}}),
        encoding="utf-8",
    )
    products_path.write_text(
        json.dumps(
            [
                {"product_key": "enabled-source", "product_name": "启用来源", "url": "https://example.com/enabled", "enabled": True},
                {"product_key": "disabled-source", "product_name": "停用来源", "url": "https://example.com/disabled", "enabled": False},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    crawled_keys: list[str] = []

    class _FakeService:
        def set_progress_callback(self, callback):
            self.callback = callback

        def crawl_source(self, product):
            crawled_keys.append(product["product_key"])
            return [{"status": "success"}]

    monkeypatch.setattr("api.crawl_manager.build_crawler_service", lambda *args, **kwargs: _FakeService())
    monkeypatch.setattr("api.crawl_manager.clear_dataframe_cache", lambda: None)

    manager = CrawlManager(runtime_path=runtime_path, products_path=products_path)
    manager._run_crawl_job("manual")

    status = manager.get_status()
    assert crawled_keys == ["enabled-source"]
    assert status["last_total_sources"] == 1
    assert status["last_success_count"] == 1


def test_filter_sources_by_region_prefers_matching_city_and_keeps_national_sources():
    items = [
        {"product_key": "nationwide", "product_name": "全国行情", "market_scope": "全国公开市场", "enabled": True},
        {"product_key": "zhengzhou-local", "product_name": "莲菜网", "source_name": "莲菜网", "market_scope": "郑州采购市场", "enabled": True},
        {"product_key": "henan-local", "product_name": "内黄果蔬城", "source_name": "河南内黄果蔬城", "market_scope": "河南公开市场", "enabled": True},
        {"product_key": "beijing-local", "product_name": "北京新发地", "market_scope": "北京公开市场", "enabled": True},
    ]

    filtered = filter_sources_by_region(items, province="河南省", city="郑州", target_scope="city")

    assert [item["product_key"] for item in filtered] == ["nationwide", "zhengzhou-local"]


def test_lian_cai_sources_are_marked_as_zhengzhou_procurement_market():
    from utils.config_loader import load_json_config

    products = load_json_config("config/products.json")
    lian_cai_sources = [
        item for item in products
        if item.get("source_name") == "莲菜网" or "liancaiwang.cn" in str(item.get("url") or "")
    ]

    assert lian_cai_sources
    assert all(item.get("market_scope") == "郑州采购市场" for item in lian_cai_sources)


def test_product_source_config_no_longer_uses_local_market_labels():
    from utils.config_loader import load_json_config

    products = load_json_config("config/products.json")
    source_fields = ("group_name", "source_tier", "market_scope")

    assert all("本地市场" not in str(item.get(field) or "") for item in products for field in source_fields)


def test_region_filter_supports_future_city_procurement_markets():
    items = [
        {"product_key": "nationwide", "product_name": "全国行情", "market_scope": "全国公开市场", "enabled": True},
        {"product_key": "chengdu-procurement", "product_name": "成都采购平台", "market_scope": "成都采购市场", "enabled": True},
        {"product_key": "zhengzhou-procurement", "product_name": "郑州采购平台", "market_scope": "郑州采购市场", "enabled": True},
    ]

    filtered = filter_sources_by_region(items, province="四川省", city="成都", target_scope="city")

    assert [item["product_key"] for item in filtered] == ["nationwide", "chengdu-procurement"]


def test_crawl_manager_filters_products_by_schedule_region(tmp_path, monkeypatch):
    runtime_path = tmp_path / "runtime.json"
    products_path = tmp_path / "products.json"
    runtime_path.write_text(
        json.dumps(
            {
                "schedule": {
                    "enabled": False,
                    "interval_seconds": 86400,
                    "fetch_mode": "requests",
                    "target_scope": "city",
                    "target_province": "河南省",
                    "target_city": "郑州",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    products_path.write_text(
        json.dumps(
            [
                {"product_key": "nationwide", "product_name": "全国行情", "market_scope": "全国公开市场", "enabled": True},
                {"product_key": "zhengzhou-local", "product_name": "莲菜网", "source_name": "莲菜网", "market_scope": "郑州采购市场", "enabled": True},
                {"product_key": "beijing-local", "product_name": "北京新发地", "market_scope": "北京公开市场", "enabled": True},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    crawled_keys: list[str] = []

    class _FakeService:
        def set_progress_callback(self, callback):
            self.callback = callback

        def crawl_source(self, product):
            crawled_keys.append(product["product_key"])
            return [{"status": "success"}]

    monkeypatch.setattr("api.crawl_manager.build_crawler_service", lambda *args, **kwargs: _FakeService())
    monkeypatch.setattr("api.crawl_manager.clear_dataframe_cache", lambda: None)

    manager = CrawlManager(runtime_path=runtime_path, products_path=products_path)
    manager._run_crawl_job("manual", "city", "河南省", "郑州")

    assert crawled_keys == ["nationwide", "zhengzhou-local"]
