from __future__ import annotations

import json

from tools.probe_meicai_plaintext_endpoints import build_probe_report, parse_endpoints, probe_endpoint


def test_parse_endpoints_uses_default_when_blank():
    assert parse_endpoints(" ") == ["class_products", "goods_info_location", "smart_list_good_list", "xb_feed"]
    assert parse_endpoints("xb_feed,smart_list_good_list") == ["xb_feed", "smart_list_good_list"]


def test_probe_endpoint_summarizes_plaintext_goods_without_values():
    class FakeMeicaiClient:
        def goods_info_location(self, **kwargs):
            return {
                "ret": 1,
                "data": {
                    "rows": [
                        {
                            "goodsRows": {
                                "skuBase": {
                                    "skuName": "青菜",
                                    "skuId": "secret-sku",
                                },
                                "skuPrice": {"minPrice": "2.80", "priceUnit": "斤"},
                            }
                        }
                    ]
                },
                "encryption": {"type": 1},
            }

    report = probe_endpoint(
        client=FakeMeicaiClient(),
        endpoint_name="goods_info_location",
        category_filters=[{"category": "蔬菜", "class1_id": "6506", "class2_id": "6515"}],
        max_pages=1,
        page_size=20,
        city_id="17",
        area_id="4402",
    )
    serialized_report = json.dumps(report, ensure_ascii=False)

    assert report["plaintext"] is True
    assert report["row_count"] == 1
    assert report["unique_goods_count"] == 1
    assert "goodsRows.skuBase" in report["raw_row_keys"]
    assert "skuBase.skuName" in report["goods_field_keys"]
    assert "青菜" not in serialized_report
    assert "secret-sku" not in serialized_report


def test_probe_endpoint_reads_activity_sku_list_without_values():
    class FakeMeicaiClient:
        def activity_polymerize_product(self, **kwargs):
            return {
                "ret": 1,
                "data": {
                    "skuList": [
                        {
                            "skuBase": {
                                "skuName": "活动菜",
                                "skuId": "secret-activity-sku",
                            },
                            "skuPrice": {"minPrice": "3.80", "priceUnit": "斤"},
                        }
                    ],
                    "totalCount": 1,
                },
                "encryption": {"type": 1},
            }

    report = probe_endpoint(
        client=FakeMeicaiClient(),
        endpoint_name="activity_polymerize_product",
        category_filters=[{"category": "活动", "class1_id": "6506", "class2_id": "6515"}],
        max_pages=1,
        page_size=20,
        city_id="17",
        area_id="4402",
    )
    serialized_report = json.dumps(report, ensure_ascii=False)

    assert report["row_count"] == 1
    assert report["unique_goods_count"] == 1
    assert "skuList" in report["data_keys"]
    assert "skuBase.skuName" in report["goods_field_keys"]
    assert "活动菜" not in serialized_report
    assert "secret-activity-sku" not in serialized_report


def test_probe_endpoint_marks_encrypted_payload():
    class FakeMeicaiClient:
        def smart_list_good_list(self, **kwargs):
            return {"ret": 1, "data": "cipher", "encryption": {"type": 3}}

    report = probe_endpoint(
        client=FakeMeicaiClient(),
        endpoint_name="smart_list_good_list",
        category_filters=[{"category": "采购清单", "class1_id": "-1", "class2_id": ""}],
        max_pages=1,
        page_size=20,
        city_id="17",
        area_id="4402",
    )

    assert report["plaintext"] is False
    assert report["encrypted_responses"] == 1
    assert report["row_count"] == 0
    assert report["unique_goods_count"] == 0


def test_probe_endpoint_supports_class_products_with_sale_ids():
    observed_calls: list[dict[str, object]] = []

    class FakeMeicaiClient:
        def class_products(self, **kwargs):
            observed_calls.append(kwargs)
            return {"ret": 1, "data": "cipher", "encryption": {"type": 3}}

    report = probe_endpoint(
        client=FakeMeicaiClient(),
        endpoint_name="class_products",
        category_filters=[
            {
                "category": "叶菜花菜",
                "class1_id": "6506",
                "class2_id": "6515",
                "sale_c1_id": "6202",
                "sale_c2_id": "19835",
            }
        ],
        max_pages=1,
        page_size=10,
        city_id="17",
        area_id="4402",
    )

    assert report["path"] == "/entrance/dishes/getSpusByClass"
    assert report["encrypted_responses"] == 1
    assert observed_calls == [
        {
            "page": 1,
            "page_size": 10,
            "city_id": "17",
            "area_id": "4402",
            "sale_c1_id": "6202",
            "sale_c2_id": "19835",
        }
    ]


def test_probe_endpoint_supports_h5_candidate_paths():
    observed_calls: list[str] = []

    class FakeMeicaiClient:
        def recommend_feed(self, **kwargs):
            observed_calls.append("recommend_feed")
            return {"ret": 1, "data": {"rows": []}, "encryption": {"type": 1}}

        def goods_info_stream(self, **kwargs):
            observed_calls.append("goods_info_stream")
            return {"ret": 1, "data": {"rows": []}, "encryption": {"type": 1}}

        def activity_polymerize_product(self, **kwargs):
            observed_calls.append("activity_polymerize_product")
            return {"ret": 1, "data": {"rows": []}, "encryption": {"type": 1}}

        def commodity_goods_rank(self, **kwargs):
            observed_calls.append("commodity_goods_rank")
            return {"ret": 1, "data": {"rows": []}, "encryption": {"type": 1}}

        def search_goods_list_by_data_id(self, **kwargs):
            observed_calls.append("search_goods_list_by_data_id")
            return {"ret": 1, "data": {"rows": []}, "encryption": {"type": 1}}

    for endpoint_name in [
        "recommend_feed",
        "goods_info_stream",
        "activity_polymerize_product",
        "commodity_goods_rank",
        "search_goods_list_by_data_id",
    ]:
        report = probe_endpoint(
            client=FakeMeicaiClient(),
            endpoint_name=endpoint_name,
            category_filters=[{"category": "候选", "class1_id": "-1", "class2_id": ""}],
            max_pages=1,
            page_size=20,
            city_id="17",
            area_id="4402",
        )

        assert report["endpoint"] == endpoint_name
        assert report["plaintext"] is True

    assert observed_calls == [
        "recommend_feed",
        "goods_info_stream",
        "activity_polymerize_product",
        "commodity_goods_rank",
        "search_goods_list_by_data_id",
    ]


def test_build_probe_report_loads_env_and_redacts_values(tmp_path, monkeypatch):
    secret_env_path = tmp_path / "meicai.env"
    secret_env_path.write_text(
        'MEICAI_REQUEST_HEADERS={"Device-Token":"secret-token"}\n'
        'MEICAI_COMMON_BODY={"tickets":"secret-ticket"}\n'
        'MEICAI_ADDRESS_CONTEXT={"request_body":{"locationTo":"secret-location","city_id":"17","area_id":"4402"}}\n',
        encoding="utf-8",
    )

    class FakeMeicaiClient:
        def __init__(self, **kwargs):
            pass

        def change_address(self, body_payload):
            return {"ret": 1, "code": 1}

        def xb_feed(self, **kwargs):
            return {"ret": 1, "data": {"rows": []}, "encryption": {"type": 1}}

    monkeypatch.setattr("tools.probe_meicai_plaintext_endpoints.MeicaiAppGatewayClient", FakeMeicaiClient)
    monkeypatch.delenv("MEICAI_REQUEST_HEADERS", raising=False)
    monkeypatch.delenv("MEICAI_COMMON_BODY", raising=False)
    monkeypatch.delenv("MEICAI_ADDRESS_CONTEXT", raising=False)

    report = build_probe_report(
        secret_env_file=secret_env_path,
        endpoints=["xb_feed"],
        sale_class_tree=None,
        limit_filters=1,
        max_pages=1,
        page_size=20,
        base_url="https://mall-entrance.yunshanmeicai.com",
        sleep_seconds=0,
    )
    serialized_report = json.dumps(report, ensure_ascii=False)

    assert report["endpoints"][0]["endpoint"] == "xb_feed"
    assert "secret-token" not in serialized_report
    assert "secret-ticket" not in serialized_report
    assert "secret-location" not in serialized_report
    assert "MEICAI_REQUEST_HEADERS" not in __import__("os").environ
    assert "MEICAI_COMMON_BODY" not in __import__("os").environ
    assert "MEICAI_ADDRESS_CONTEXT" not in __import__("os").environ
