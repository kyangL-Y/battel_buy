import json

from api.crawl_manager import CrawlManager, build_crawler_service


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
