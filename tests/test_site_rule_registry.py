from pathlib import Path

from services.site_rule_registry import load_site_rules, upsert_site_rule


def test_upsert_site_rule_creates_new_rule(tmp_path: Path):
    target = tmp_path / "sites.json"

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "示例站点",
            "domains": ["www.example.com", "example.com"],
            "price_selectors": [".price"],
            "name_selectors": ["h1"],
        },
    )

    loaded = load_site_rules(target)

    assert created is True
    assert rule["site_name"] == "示例站点"
    assert len(loaded) == 1
    assert loaded[0]["domains"] == ["www.example.com", "example.com"]


def test_upsert_site_rule_merges_existing_domains(tmp_path: Path):
    target = tmp_path / "sites.json"
    upsert_site_rule(
        target,
        {
            "site_name": "示例站点",
            "domains": ["example.com"],
            "price_selectors": [".price"],
            "name_selectors": ["h1"],
        },
    )

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "示例站点",
            "domains": ["www.example.com"],
            "price_selectors": ["meta[property='product:price:amount']"],
            "name_selectors": ["meta[property='og:title']"],
        },
    )

    loaded = load_site_rules(target)

    assert created is False
    assert sorted(rule["domains"]) == ["example.com", "www.example.com"]
    assert ".price" in rule["price_selectors"]
    assert "meta[property='product:price:amount']" in rule["price_selectors"]
    assert len(loaded) == 1


def test_upsert_site_rule_preserves_api_fields(tmp_path: Path):
    target = tmp_path / "sites.json"

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "接口站点",
            "domains": ["api.example.com"],
            "api_strategy": "prefer",
            "api_url": "https://api.example.com/price",
            "api_method": "POST",
            "api_headers": {"Authorization": "Bearer token"},
            "api_body_template": {"sku": "1"},
            "api_field_mapping": {"current_price": "data.price"},
        },
    )

    assert created is True
    assert rule["api_strategy"] == "prefer"
    assert rule["api_url"] == "https://api.example.com/price"
    assert rule["api_method"] == "POST"
    assert rule["api_headers"] == {"Authorization": "Bearer token"}


def test_upsert_site_rule_preserves_strategy_fields(tmp_path: Path):
    target = tmp_path / "sites.json"

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "策略站点",
            "domains": ["strategy.example.com"],
            "strategy": "api_batch",
            "fallback_strategy": "single",
            "api_url": "https://strategy.example.com/api",
        },
    )

    assert created is True
    assert rule["strategy"] == "api_batch"
    assert rule["fallback_strategy"] == "single"


def test_upsert_site_rule_preserves_verify_ssl_flag(tmp_path: Path):
    target = tmp_path / "sites.json"

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "证书例外站点",
            "domains": ["ssl.example.com"],
            "strategy": "hnnhgsc_batch",
            "verify_ssl": False,
        },
    )

    assert created is True
    assert rule["verify_ssl"] is False


def test_upsert_site_rule_preserves_liancai_h5_fields(tmp_path: Path):
    target = tmp_path / "sites.json"

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "莲菜网H5",
            "domains": ["m.liancaiwang.cn"],
            "strategy": "liancai_h5_batch",
            "base_url": "http://m.liancaiwang.cn",
            "login_phone_env": "LIANCAI_PHONE",
            "login_password_env": "LIANCAI_PASSWORD",
            "max_pages": 20,
        },
    )

    loaded = load_site_rules(target)

    assert created is True
    assert rule["strategy"] == "liancai_h5_batch"
    assert rule["base_url"] == "http://m.liancaiwang.cn"
    assert rule["login_phone_env"] == "LIANCAI_PHONE"
    assert rule["login_password_env"] == "LIANCAI_PASSWORD"
    assert rule["max_pages"] == 20
    assert loaded[0]["base_url"] == "http://m.liancaiwang.cn"


def test_upsert_site_rule_preserves_chinaprice_fast_snapshot_fields(tmp_path: Path):
    target = tmp_path / "sites.json"

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "Chinaprice",
            "domains": ["www.chinaprice.cn"],
            "strategy": "chinaprice_batch",
            "chinaprice_query_mode": "fast_snapshot",
            "chinaprice_menu_codes": ["pfscsphzjg"],
            "chinaprice_history_days": 1,
            "chinaprice_city_tree_history_days": 1,
            "chinaprice_max_queries": 300,
            "chinaprice_max_pages_per_query": 1,
            "chinaprice_max_rows": 5000,
        },
    )

    loaded = load_site_rules(target)

    assert created is True
    assert rule["chinaprice_query_mode"] == "fast_snapshot"
    assert rule["chinaprice_menu_codes"] == ["pfscsphzjg"]
    assert loaded[0]["chinaprice_max_rows"] == 5000
