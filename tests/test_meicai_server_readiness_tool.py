import json
import subprocess

from tools.check_meicai_server_readiness import build_readiness_report


def test_build_readiness_report_summarizes_env_without_secret_values(tmp_path, monkeypatch):
    products_path = tmp_path / "products.json"
    sites_path = tmp_path / "sites.json"
    sale_class_tree_path = tmp_path / "meicai_sale_class_tree.json"
    current_address_path = tmp_path / "meicai_current_address_context.json"
    products_path.write_text(
        json.dumps(
            [
                {
                    "product_key": "meicai-app-feed",
                    "url": "https://mall-entrance.yunshanmeicai.com",
                    "strategy": "meicai_app_gateway_batch",
                    "enabled": True,
                }
            ]
        ),
        encoding="utf-8",
    )
    sale_class_tree_path.write_text(
        '{"flat":[{"saleC1Id":"6506","saleC2Id":"6515"},{"saleC1Id":"6506","saleC2Id":"6205"}]}',
        encoding="utf-8",
    )
    current_address_path.write_text(
        json.dumps(
            {
                "addressId": "22117779",
                "locationTo": "secret-current-location",
                "poi_address": "上海市浦东新区羽山路陆家嘴金融贸易区桃林一小区",
                "address_detail": "桃林一小区-27号楼",
            }
        ),
        encoding="utf-8",
    )
    sites_path.write_text(
        json.dumps(
            [
                {
                    "domains": ["mall-entrance.yunshanmeicai.com"],
                    "strategy": "meicai_app_gateway_batch",
                    "gateway_base_url": "https://mall-entrance.yunshanmeicai.com",
                    "endpoint": "xb_feed",
                    "city_id": "17",
                    "area_id": "4402",
                    "page_size": 20,
                    "max_pages": 5,
                    "sale_class_tree_path": str(sale_class_tree_path),
                    "current_address_context_path": str(current_address_path),
                    "category_filters": [
                        {"category": "推荐商品", "class1_id": "-1", "class2_id": ""},
                        {"category": "蔬菜", "class1_id": "6506", "class2_id": ""},
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MEICAI_REQUEST_HEADERS", '{"Device-Token":"secret-token","x-mc-city":"17"}')
    monkeypatch.setenv("MEICAI_COMMON_BODY", '{"tickets":"secret-ticket","city_id":"17"}')
    monkeypatch.setenv("MEICAI_ADDRESS_CONTEXT", '{"request_body":{"locationTo":"secret-location"}}')

    report = build_readiness_report(
        products_path=products_path,
        sites_path=sites_path,
        secret_env_file=None,
    )
    serialized_report = json.dumps(report, ensure_ascii=False)

    assert report["ready"] is True
    assert report["product_enabled"] is True
    assert report["category_filter_count"] == 2
    assert report["sale_class_filter_count"] == 2
    assert report["current_address_context"]["present"] is True
    assert report["current_address_context"]["has_location"] is True
    assert report["current_address_context"]["address_id_present"] is True
    assert report["current_address_context"]["inferred_region"] == "上海市"
    assert report["env"]["MEICAI_REQUEST_HEADERS"]["top_level_keys"] == ["Device-Token", "x-mc-city"]
    assert "secret-token" not in serialized_report
    assert "secret-ticket" not in serialized_report
    assert "secret-location" not in serialized_report
    assert "secret-current-location" not in serialized_report


def test_build_readiness_report_loads_secret_env_file_without_overriding_existing(tmp_path, monkeypatch):
    products_path = tmp_path / "products.json"
    sites_path = tmp_path / "sites.json"
    secret_env_path = tmp_path / "meicai.env"
    products_path.write_text(
        '[{"product_key":"meicai-app-feed","url":"https://mall-entrance.yunshanmeicai.com","strategy":"meicai_app_gateway_batch","enabled":true}]',
        encoding="utf-8",
    )
    sites_path.write_text(
        '[{"domains":["mall-entrance.yunshanmeicai.com"],"strategy":"meicai_app_gateway_batch","category_filters":[]}]',
        encoding="utf-8",
    )
    secret_env_path.write_text(
        'MEICAI_REQUEST_HEADERS={"Device-Token":"from-file"}\n'
        'MEICAI_COMMON_BODY={"tickets":"from-file"}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("MEICAI_REQUEST_HEADERS", '{"Device-Token":"from-env"}')
    monkeypatch.delenv("MEICAI_COMMON_BODY", raising=False)
    monkeypatch.delenv("MEICAI_ADDRESS_CONTEXT", raising=False)

    report = build_readiness_report(
        products_path=products_path,
        sites_path=sites_path,
        secret_env_file=secret_env_path,
    )

    assert report["loaded_env_names"] == ["MEICAI_COMMON_BODY"]
    assert report["env"]["MEICAI_REQUEST_HEADERS"]["top_level_keys"] == ["Device-Token"]
    assert report["env"]["MEICAI_COMMON_BODY"]["top_level_keys"] == ["tickets"]


def test_readiness_cli_reports_missing_env_without_traceback(tmp_path, monkeypatch):
    products_path = tmp_path / "products.json"
    sites_path = tmp_path / "sites.json"
    products_path.write_text(
        '[{"product_key":"meicai-app-feed","url":"https://mall-entrance.yunshanmeicai.com","strategy":"meicai_app_gateway_batch","enabled":true}]',
        encoding="utf-8",
    )
    sites_path.write_text(
        '[{"domains":["mall-entrance.yunshanmeicai.com"],"strategy":"meicai_app_gateway_batch"}]',
        encoding="utf-8",
    )
    monkeypatch.delenv("MEICAI_REQUEST_HEADERS", raising=False)
    monkeypatch.delenv("MEICAI_COMMON_BODY", raising=False)

    completed = subprocess.run(
        [
            "python",
            "tools/check_meicai_server_readiness.py",
            "--products",
            str(products_path),
            "--sites",
            str(sites_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(completed.stdout)
    assert report["ready"] is False
    assert report["error"] == "missing MEICAI_REQUEST_HEADERS"
    assert "Traceback" not in completed.stderr
