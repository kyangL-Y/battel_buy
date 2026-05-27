from parsers.normalizer import (
    build_compare_key,
    compute_kg_price,
    clean_price_text,
    compute_jin_price,
    compute_unit_price,
    format_price_unit_basis,
    normalize_price,
    normalize_product_metadata,
    parse_spec,
)


def test_clean_price_text():
    assert clean_price_text("¥ 1,299.00") == "1299.00"
    assert clean_price_text("￥999-1299") == "999"


def test_normalize_price():
    assert normalize_price("$199.50") == 199.5
    assert normalize_price(None) is None
    assert normalize_price("暂无报价") is None


def test_parse_spec():
    assert parse_spec("500ml") == {
        "unit_name": "ml",
        "unit_value": 500.0,
        "spec_text": "500ml",
    }
    assert parse_spec("1L") == {
        "unit_name": "ml",
        "unit_value": 1000.0,
        "spec_text": "1l",
    }
    assert parse_spec("200ml*2") == {
        "unit_name": "ml",
        "unit_value": 400.0,
        "spec_text": "200ml*2",
    }
    assert parse_spec("250g×4") == {
        "unit_name": "g",
        "unit_value": 1000.0,
        "spec_text": "250g×4",
    }
    assert parse_spec("公斤") == {
        "unit_name": "g",
        "unit_value": 1000.0,
        "spec_text": "公斤",
    }
    assert parse_spec("元/500克") == {
        "unit_name": "g",
        "unit_value": 500.0,
        "spec_text": "元/500克",
    }
    assert parse_spec("两斤/袋") == {
        "unit_name": "g",
        "unit_value": 1000.0,
        "spec_text": "两斤/袋",
    }


def test_compute_unit_price():
    assert compute_unit_price(12.0, "ml", 500.0) == 2.4
    assert compute_unit_price(15.0, "g", 1000.0) == 1.5
    assert compute_unit_price(3.2, "g", 500.0) == 0.64
    assert compute_unit_price(None, "ml", 500.0) is None


def test_compute_jin_price():
    assert compute_jin_price(15.0, "g", 1000.0) == 7.5
    assert compute_jin_price(3.2, "g", 500.0) == 3.2
    assert compute_jin_price(12.0, "ml", 500.0) is None


def test_compute_kg_price():
    assert compute_kg_price(15.0, "g", 1000.0) == 15.0
    assert compute_kg_price(3.2, "g", 500.0) == 6.4
    assert compute_kg_price(12.0, "ml", 500.0) is None


def test_format_price_unit_basis():
    assert format_price_unit_basis("500ml") == "元/500ml"
    assert format_price_unit_basis("公斤") == "元/公斤"
    assert format_price_unit_basis(None) == "原始报价"


def test_build_compare_key_prioritizes_product_name():
    assert build_compare_key("白菜", "蔬菜类", None, None, "公斤") == "白菜|蔬菜类|未指定|未指定"


def test_normalize_product_metadata_supports_chinese_units_and_compare_key():
    result = normalize_product_metadata(
        {
            "product_name": "白菜",
            "category": "蔬菜类",
            "spec_text": "元/500克",
        },
        current_price=2.5,
    )

    assert result["compare_key"] == "白菜|蔬菜类|未指定|未指定"
    assert result["unit_name"] == "g"
    assert result["unit_value"] == 500.0
    assert result["unit_price"] == 0.5
    assert result["jin_price"] == 2.5
    assert result["kg_price"] == 5.0


def test_normalize_product_metadata_uses_product_name_spec_when_spec_only_has_unit():
    result = normalize_product_metadata(
        {
            "product_name": "冻虾五斤",
            "category": "水产",
            "spec_text": "斤",
        },
        current_price=138.0,
    )

    assert result["spec_text"] == "5斤"
    assert result["unit_name"] == "g"
    assert result["unit_value"] == 2500.0
    assert result["jin_price"] == 27.6
    assert result["kg_price"] == 55.2


def test_normalize_product_metadata_keeps_liancai_spec_raw_when_only_unit_present():
    result = normalize_product_metadata(
        {
            "product_name": "冻虾五斤",
            "category": "水产",
            "spec_text": "斤",
            "site_name": "莲菜网H5 | 冻品类",
            "source_url": "https://m.liancaiwang.cn/list/index/id/6.html",
        },
        current_price=138.0,
    )

    assert result["spec_text"] == "斤"
    assert result["unit_name"] == "g"
    assert result["unit_value"] == 500.0
    assert result["jin_price"] == 138.0
