from __future__ import annotations

import json
from pathlib import Path

from tools.validate_meicai_h5_server_crawl import build_meicai_server_crawl_validation_report


def test_validation_report_confirms_full_crawl_and_database_delta(tmp_path: Path, monkeypatch):
    products_path = tmp_path / "products.json"
    sites_path = tmp_path / "sites.json"
    runtime_path = tmp_path / "runtime.json"
    crawl_audit_path = tmp_path / "meicai_crawl_audit.json"
    products_path.write_text(
        json.dumps(
            [
                {
                    "product_key": "meicai-h5-class-products",
                    "url": "https://mall-entrance.yunshanmeicai.com",
                    "strategy": "meicai_h5_decrypt_batch",
                    "enabled": True,
                }
            ]
        ),
        encoding="utf-8",
    )
    sites_path.write_text(
        json.dumps(
            [
                {
                    "domains": ["mall-entrance.yunshanmeicai.com"],
                    "strategy": "meicai_h5_decrypt_batch",
                    "crawl_audit_path": str(crawl_audit_path),
                }
            ]
        ),
        encoding="utf-8",
    )
    runtime_path.write_text('{"schedule":{"fetch_mode":"requests"}}', encoding="utf-8")

    class FakeDatabase:
        database_label = "sqlite://validation"

        def __init__(self) -> None:
            self.price_record_count = 10

        def get_price_record_count(self) -> int:
            return self.price_record_count

    class FakeCrawlerService:
        def __init__(self) -> None:
            self.database = FakeDatabase()

        def crawl_source(self, product):
            self.database.price_record_count += 2
            crawl_audit_path.write_text(
                json.dumps(
                    {
                        "category_count": 2,
                        "request_count": 2,
                        "raw_row_count": 2,
                        "deduplicated_row_count": 2,
                        "hit_max_pages_count": 0,
                        "category_reports": [
                            {"category": "叶菜", "stop_reason": "last_page_marker"},
                            {"category": "根茎", "stop_reason": "empty_page"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            return [{"status": "success"}, {"status": "success"}]

    monkeypatch.setattr(
        "tools.validate_meicai_h5_server_crawl.build_readiness_report",
        lambda **kwargs: {
            "ready": True,
            "strategy": "meicai_h5_decrypt_batch",
            "sale_class_filter_count": 2,
        },
    )
    monkeypatch.setattr(
        "tools.validate_meicai_h5_server_crawl.build_crawler_service",
        lambda *args, **kwargs: FakeCrawlerService(),
    )

    report = build_meicai_server_crawl_validation_report(
        products_path=products_path,
        sites_path=sites_path,
        runtime_path=runtime_path,
        secret_env_file=None,
        product_key="meicai-h5-class-products",
    )

    assert report["validated"] is True
    assert report["price_record_count_delta"] == 2
    assert report["crawl_success_count"] == 2
    assert report["crawl_audit"]["category_count"] == 2
    assert report["crawl_audit"]["hit_max_pages_count"] == 0


def test_validation_report_rejects_truncated_audit(tmp_path: Path, monkeypatch):
    products_path = tmp_path / "products.json"
    sites_path = tmp_path / "sites.json"
    runtime_path = tmp_path / "runtime.json"
    crawl_audit_path = tmp_path / "meicai_crawl_audit.json"
    products_path.write_text(
        '[{"product_key":"meicai-h5-class-products","url":"https://mall-entrance.yunshanmeicai.com","strategy":"meicai_h5_decrypt_batch"}]',
        encoding="utf-8",
    )
    sites_path.write_text(
        json.dumps(
            [
                {
                    "domains": ["mall-entrance.yunshanmeicai.com"],
                    "strategy": "meicai_h5_decrypt_batch",
                    "crawl_audit_path": str(crawl_audit_path),
                }
            ]
        ),
        encoding="utf-8",
    )
    runtime_path.write_text('{"schedule":{"fetch_mode":"requests"}}', encoding="utf-8")

    class FakeDatabase:
        def __init__(self) -> None:
            self.price_record_count = 20

        def get_price_record_count(self) -> int:
            return self.price_record_count

    class FakeCrawlerService:
        def __init__(self) -> None:
            self.database = FakeDatabase()

        def crawl_source(self, product):
            self.database.price_record_count += 1
            crawl_audit_path.write_text(
                json.dumps(
                    {
                        "category_count": 2,
                        "request_count": 40,
                        "raw_row_count": 1,
                        "deduplicated_row_count": 1,
                        "hit_max_pages_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            return [{"status": "success"}]

    monkeypatch.setattr(
        "tools.validate_meicai_h5_server_crawl.build_readiness_report",
        lambda **kwargs: {
            "ready": True,
            "strategy": "meicai_h5_decrypt_batch",
            "sale_class_filter_count": 2,
        },
    )
    monkeypatch.setattr(
        "tools.validate_meicai_h5_server_crawl.build_crawler_service",
        lambda *args, **kwargs: FakeCrawlerService(),
    )

    report = build_meicai_server_crawl_validation_report(
        products_path=products_path,
        sites_path=sites_path,
        runtime_path=runtime_path,
        secret_env_file=None,
        product_key="meicai-h5-class-products",
    )

    assert report["validated"] is False
    assert report["crawl_audit"]["hit_max_pages_count"] == 1
