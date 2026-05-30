from __future__ import annotations

import json

import pytest

from tools.extract_meicai_category_candidates import (
    CLASS_PRODUCTS_EXCLUSION_REASON,
    ENCRYPTED_CLASS_PRODUCTS_ENDPOINT,
    PLAINTEXT_FEED_COVERAGE_SCOPE,
    XB_FEED_ENDPOINT,
    attach_internal_category_mappings,
    build_meicai_category_candidates_output,
    collect_meicai_category_candidates,
    load_meicai_candidate_rows,
    load_category_filters_from_sale_class_tree,
    load_meicai_payloads,
    write_meicai_category_candidates,
)


def test_collect_meicai_category_candidates_groups_sale_and_bi_fields():
    payload = {
        "ret": 1,
        "data": {
            "rows": [
                {
                    "goodsRows": {
                        "skuBase": {
                            "skuName": "红茶 500ml",
                            "saleC1Id": "6511",
                            "saleC2Id": "7101",
                            "saleC1Name": "酒水饮料",
                            "saleC2Name": "茶饮料",
                            "biName": "红茶",
                            "biAliasName": "冰红茶",
                        }
                    }
                },
                {
                    "goodsRows": {
                        "skuBase": {
                            "skuName": "红茶 整箱",
                            "saleC1Id": "6511",
                            "saleC2Id": "7101",
                            "saleC1Name": "酒水饮料",
                            "saleC2Name": "茶饮料",
                            "biName": "红茶",
                            "biAliasName": "红茶饮料",
                        }
                    }
                },
            ]
        },
        "encryption": {"type": 1},
    }

    candidates = collect_meicai_category_candidates([(payload, "酒水饮料")])

    assert candidates == [
        {
            "saleC1Id": "6511",
            "saleC2Id": "7101",
            "saleC1Name": "酒水饮料",
            "saleC2Name": "茶饮料",
            "biName": "红茶",
            "biAliasNames": ["冰红茶", "红茶饮料"],
            "sampleSkuNames": ["红茶 500ml", "红茶 整箱"],
            "sourceFilters": ["酒水饮料"],
            "count": 2,
        }
    ]


def test_collect_meicai_category_candidates_blocks_encrypted_payload():
    with pytest.raises(RuntimeError, match="不转 OCR"):
        collect_meicai_category_candidates([{"data": "cipher", "encryption": {"type": 3}}])


def test_load_meicai_payloads_accepts_secret_capture_jsonl(tmp_path):
    capture_path = tmp_path / "meicai_secret_flows.jsonl"
    capture_path.write_text(
        json.dumps(
            {
                "path": "/entrance/recommend/xbFeed",
                "response_text": json.dumps(
                    {
                        "ret": 1,
                        "data": {
                            "rows": [
                                {
                                    "goodsRows": {
                                        "skuBase": {
                                            "skuName": "小葱",
                                            "saleC1Id": "6506",
                                            "biName": "小葱/香葱",
                                        }
                                    }
                                }
                            ]
                        },
                    },
                    ensure_ascii=False,
                ),
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    payloads = load_meicai_payloads(capture_path)

    assert payloads[0]["data"]["rows"][0]["goodsRows"]["skuBase"]["biName"] == "小葱/香葱"


def test_load_meicai_candidate_rows_accepts_existing_candidate_json(tmp_path):
    candidate_path = tmp_path / "meicai_category_candidates.json"
    candidate_path.write_text(
        json.dumps(
            [
                {
                    "saleC1Id": "6506",
                    "saleC2Id": "6205",
                    "biName": "蒜米",
                    "sampleSkuNames": ["蒜米 普通"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    candidates = load_meicai_candidate_rows(candidate_path)

    assert candidates[0]["biName"] == "蒜米"


def test_load_meicai_candidate_rows_accepts_metadata_wrapped_candidate_json(tmp_path):
    candidate_path = tmp_path / "meicai_category_candidates.json"
    candidate_path.write_text(
        json.dumps(
            {
                "source_endpoint": XB_FEED_ENDPOINT,
                "coverage": PLAINTEXT_FEED_COVERAGE_SCOPE,
                "excluded_endpoint": ENCRYPTED_CLASS_PRODUCTS_ENDPOINT,
                "candidates": [
                    {
                        "saleC1Id": "6506",
                        "saleC2Id": "6205",
                        "biName": "蒜米",
                        "sampleSkuNames": ["蒜米 普通"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    candidates = load_meicai_candidate_rows(candidate_path)

    assert candidates[0]["biName"] == "蒜米"


def test_load_category_filters_from_sale_class_tree_uses_flat_rows(tmp_path):
    tree_path = tmp_path / "tree.json"
    tree_path.write_text(
        json.dumps(
            {
                "flat": [
                    {
                        "saleC1Id": "6506",
                        "saleC1Name": "蔬果豆类",
                        "saleC2Id": "6515",
                        "saleC2Name": "叶菜花菜",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    category_filters = load_category_filters_from_sale_class_tree(tree_path)

    assert category_filters == [
        {
            "category": "蔬果豆类 / 叶菜花菜",
            "class1_id": "6506",
            "class2_id": "6515",
        }
    ]


def test_write_meicai_category_candidates_creates_json(tmp_path):
    output_path = tmp_path / "candidates.json"

    write_meicai_category_candidates([{"biName": "蒜米", "count": 1}], output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == [{"biName": "蒜米", "count": 1}]


def test_build_meicai_category_candidates_output_declares_plaintext_feed_scope():
    candidate_export = build_meicai_category_candidates_output([{"biName": "蒜米", "count": 1}])

    assert candidate_export == {
        "source_endpoint": XB_FEED_ENDPOINT,
        "coverage": PLAINTEXT_FEED_COVERAGE_SCOPE,
        "excluded_endpoint": ENCRYPTED_CLASS_PRODUCTS_ENDPOINT,
        "exclusion_reason": CLASS_PRODUCTS_EXCLUSION_REASON,
        "candidate_count": 1,
        "candidates": [{"biName": "蒜米", "count": 1}],
    }


def test_attach_internal_category_mappings_adds_database_fields():
    mapped_candidates = attach_internal_category_mappings(
        [
            {
                "saleC1Id": "6506",
                "saleC2Id": "6205",
                "biName": "蒜米",
                "sampleSkuNames": ["蒜米 普通"],
            }
        ]
    )

    assert mapped_candidates[0]["internalCategory"] == "葱姜蒜"
    assert mapped_candidates[0]["internalMarketCategory"] == "蔬菜类"
    assert mapped_candidates[0]["liancaiTopCategory"] == "蔬菜类"
    assert mapped_candidates[0]["liancaiSubcategory"] == "葱姜蒜"
    assert mapped_candidates[0]["mappingSource"] == "meicai_bi_exact"
