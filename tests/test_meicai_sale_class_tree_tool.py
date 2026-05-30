from __future__ import annotations

import json

import pytest

from tools.extract_meicai_sale_class_tree import (
    ENCRYPTED_CLASS_PRODUCTS_ENDPOINT,
    SALE_CLASS_COVERAGE_SCOPE,
    SALE_CLASS_ENDPOINT,
    fetch_meicai_sale_class_tree,
    extract_sale_class_items,
    flatten_sale_class_tree,
    normalize_sale_class_item,
    write_sale_class_tree,
)


def test_extract_sale_class_items_reads_plain_category_list():
    payload = {
        "ret": 1,
        "data": {
            "list": [
                {"id": "6506", "name": "蔬果豆类", "parent_id": "0"},
                {"id": "6202", "name": "冻肉禽类", "parent_id": "0"},
            ]
        },
        "encryption": {"type": 1},
    }

    items = extract_sale_class_items(payload)

    assert [item["id"] for item in items] == ["6506", "6202"]


def test_extract_sale_class_items_blocks_encrypted_payload():
    with pytest.raises(RuntimeError, match="不转 OCR"):
        extract_sale_class_items({"data": "cipher", "encryption": {"type": 3}})


def test_normalize_sale_class_item_keeps_public_fields_only():
    item = normalize_sale_class_item(
        {
            "ids": 72,
            "id": "6515",
            "name": "叶菜花菜",
            "parent_id": "6506",
            "sortNum": 10,
            "nameImg": "https://img.example/category.png",
        }
    )

    assert item == {
        "id": "6515",
        "name": "叶菜花菜",
        "parent_id": "6506",
        "sortNum": 10,
        "ids": 72,
        "nameImg": "https://img.example/category.png",
    }


def test_flatten_sale_class_tree_adds_internal_category_mapping():
    flat_rows = flatten_sale_class_tree(
        [
            {
                "id": "6506",
                "name": "蔬果豆类",
                "parent_id": "0",
                "children": [
                    {"id": "6515", "name": "叶菜花菜", "parent_id": "6506"},
                    {"id": "6209", "name": "椒类", "parent_id": "6506"},
                ],
            }
        ]
    )

    assert flat_rows[0]["saleC1Id"] == "6506"
    assert flat_rows[0]["saleC2Id"] == "6515"
    assert flat_rows[0]["internalMarketCategory"] == "蔬菜类"
    assert flat_rows[0]["internalCategory"] == "叶菜类"
    assert flat_rows[1]["internalCategory"] == "椒类"


def test_write_sale_class_tree_creates_json(tmp_path):
    output_path = tmp_path / "tree.json"

    write_sale_class_tree({"root_count": 1, "tree": []}, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == {"root_count": 1, "tree": []}


def test_fetch_sale_class_tree_declares_navigation_only_coverage(monkeypatch, tmp_path):
    observed_parent_ids: list[str] = []

    class FakeMeicaiClient:
        def __init__(self, **kwargs):
            pass

        def sale_class(self, **kwargs):
            observed_parent_ids.append(kwargs["parent_id"])
            if kwargs["parent_id"] == "0":
                return {
                    "ret": 1,
                    "data": {"list": [{"id": "6506", "name": "蔬果豆类", "parent_id": "0"}]},
                    "encryption": {"type": 1},
                }
            return {
                "ret": 1,
                "data": {"list": [{"id": "6515", "name": "叶菜花菜", "parent_id": "6506"}]},
                "encryption": {"type": 1},
            }

    monkeypatch.setattr("tools.extract_meicai_sale_class_tree.MeicaiAppGatewayClient", FakeMeicaiClient)
    monkeypatch.setattr(
        "tools.extract_meicai_sale_class_tree.PublicSourceCrawler._load_json_env_object",
        lambda env_name: {},
    )

    tree_payload = fetch_meicai_sale_class_tree(secret_env_file=tmp_path / "missing.env")

    assert observed_parent_ids == ["0", "6506"]
    assert tree_payload["source_endpoint"] == SALE_CLASS_ENDPOINT
    assert tree_payload["coverage"] == SALE_CLASS_COVERAGE_SCOPE
    assert tree_payload["excluded_endpoint"] == ENCRYPTED_CLASS_PRODUCTS_ENDPOINT
    assert "encrypted" in tree_payload["exclusion_reason"]
