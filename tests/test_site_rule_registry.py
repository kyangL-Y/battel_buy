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


def test_upsert_site_rule_preserves_nanjing_zhongcai_fields(tmp_path: Path):
    target = tmp_path / "sites.json"

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "南京众彩",
            "domains": ["www.njnfwl.com"],
            "strategy": "nanjing_zhongcai_public_batch",
            "base_url": "https://www.njnfwl.com",
            "list_url": "https://www.njnfwl.com/list-eqpn3l3g/shucaijiage/1/10",
            "zhongcai_category": "蔬菜",
            "max_pages": 1,
            "max_articles": 1,
            "min_ocr_rows": 20,
            "ocr_cache_path": "tmp/nanjing_zhongcai_ocr_cache.json",
            "processed_article_state_path": "tmp/nanjing_zhongcai_processed_articles.json",
        },
    )

    loaded = load_site_rules(target)

    assert created is True
    assert rule["strategy"] == "nanjing_zhongcai_public_batch"
    assert rule["list_url"] == "https://www.njnfwl.com/list-eqpn3l3g/shucaijiage/1/10"
    assert rule["zhongcai_category"] == "蔬菜"
    assert loaded[0]["max_articles"] == 1
    assert loaded[0]["min_ocr_rows"] == 20
    assert loaded[0]["ocr_cache_path"] == "tmp/nanjing_zhongcai_ocr_cache.json"
    assert loaded[0]["processed_article_state_path"] == "tmp/nanjing_zhongcai_processed_articles.json"


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


def test_upsert_site_rule_preserves_meicai_h5_decrypt_fields(tmp_path: Path):
    target = tmp_path / "sites.json"

    rule, created = upsert_site_rule(
        target,
        {
            "site_name": "美菜网H5",
            "domains": ["mall-entrance.yunshanmeicai.com"],
            "strategy": "meicai_h5_decrypt_batch",
            "gateway_base_url": "https://mall-entrance.yunshanmeicai.com",
            "request_headers_env": "MEICAI_REQUEST_HEADERS",
            "common_body_env": "MEICAI_COMMON_BODY",
            "current_address_context_path": ".local-secrets/meicai_current_address_context.json",
            "secret_env_file_env": "MEICAI_SECRET_ENV_FILE",
            "endpoint": "class_products",
            "city_id": "17",
            "area_id": "4402",
            "category_filters": [{"category": "推荐商品", "class1_id": "-1", "class2_id": ""}],
            "sale_class_tree_path": "tmp/meicai_sale_class_tree.json",
            "h5_salts_path": "tmp/meicai_h5_salts.json",
            "request_source": "android",
            "crawl_audit_path": "tmp/meicai_audit.json",
            "page_size": 200,
            "max_pages": 20,
        },
    )

    loaded = load_site_rules(target)

    assert created is True
    assert rule["strategy"] == "meicai_h5_decrypt_batch"
    assert loaded[0]["gateway_base_url"] == "https://mall-entrance.yunshanmeicai.com"
    assert loaded[0]["current_address_context_path"] == ".local-secrets/meicai_current_address_context.json"
    assert loaded[0]["sale_class_tree_path"] == "tmp/meicai_sale_class_tree.json"
    assert loaded[0]["h5_salts_path"] == "tmp/meicai_h5_salts.json"
    assert loaded[0]["request_source"] == "android"
    assert loaded[0]["crawl_audit_path"] == "tmp/meicai_audit.json"
    assert loaded[0]["category_filters"] == [{"category": "推荐商品", "class1_id": "-1", "class2_id": ""}]
