from __future__ import annotations

import json

from tools.collect_meicai_runtime_class_products import build_runtime_price_rows, summarize_runtime_payloads


def test_summarize_runtime_payloads_counts_decoded_goods(tmp_path):
    payload_path = tmp_path / "runtime.jsonl"
    payload_path.write_text(
        "\n".join(
            [
                json.dumps({"event": "trigger", "class1_id": "6506", "class2_id": "6515"}),
                json.dumps({"event": "decoded", "class1_id": "6506", "class2_id": "6515", "row_count": 1}),
                json.dumps(
                    {
                        "event": "decoded_payload",
                        "class1_id": "6506",
                        "class2_id": "6515",
                        "json": {
                            "list": [
                                {
                                    "skuBase": {"skuId": "sku-1", "skuName": "青菜"},
                                    "skuPrice": {"minPrice": "2.8"},
                                }
                            ]
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    summary = summarize_runtime_payloads(payload_path)

    assert summary["trigger_count"] == 1
    assert summary["trigger_dispatched_count"] == 0
    assert summary["trigger_errors"] == []
    assert summary["decoded_pages"] == 1
    assert summary["decoded_category_count"] == 1
    assert summary["row_count"] == 1
    assert summary["unique_goods_count"] == 1


def test_build_runtime_price_rows_uses_existing_meicai_mapping(tmp_path):
    payload_path = tmp_path / "runtime.jsonl"
    payload_path.write_text(
        json.dumps(
            {
                "event": "decoded_payload",
                "class1_id": "6506",
                "class2_id": "19058",
                "json": {
                    "data": {
                        "refeactorSkus": [
                            {
                                "skuBase": {
                                    "skuId": "sku-runtime",
                                    "skuName": "韭菜 去根",
                                    "saleC1Id": "6506",
                                    "saleC2Id": "19058",
                                    "saleC1Name": "蔬果豆类",
                                    "saleC2Name": "粗加工蔬菜",
                                },
                                "selectedSsu": {
                                    "ssuFormat": "2斤",
                                    "ssuPrice": {"unitPrice": "3.20"},
                                },
                            }
                        ]
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    rows = build_runtime_price_rows(payload_path)

    assert len(rows) == 1
    assert rows[0]["product_name"] == "韭菜 去根"
    assert rows[0]["current_price"] == 3.2
    assert rows[0]["extra_fields"]["category"] == "粗加工蔬菜"
    assert rows[0]["extra_fields"]["meicai_mapping_source"] == "meicai_app_gateway_class_products_runtime"
