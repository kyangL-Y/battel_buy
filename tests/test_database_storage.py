from pathlib import Path

from storage.database import Database


def test_database_connections_enable_wal_and_busy_timeout(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    with db.connect() as conn:
        journal_mode = conn.exec_driver_sql("PRAGMA journal_mode").fetchone()[0]
        busy_timeout = conn.exec_driver_sql("PRAGMA busy_timeout").fetchone()[0]
        foreign_keys = conn.exec_driver_sql("PRAGMA foreign_keys").fetchone()[0]

    assert str(journal_mode).lower() == "wal"
    assert int(busy_timeout) == 30000
    assert int(foreign_keys) == 1


def test_database_nested_connect_reuses_active_transaction(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    with db.connect() as outer_conn:
        with db.connect() as inner_conn:
            assert inner_conn is outer_conn

        product_id = db.upsert_product(
            product_key="nested-1",
            group_name="白菜",
            product_name="白菜",
            source_url="https://example.com/bc",
            site_name="测试站点",
        )
        db.insert_price_record(
            product_id=product_id,
            captured_at="2026-04-15T10:00:00",
            current_price=1.8,
            original_price=None,
            promotion_text=None,
            currency="CNY",
            availability=None,
            raw_payload={"demo": True},
        )

    result = db.get_price_history()
    assert len(result) == 1
    assert result.iloc[0]["product_key"] == "nested-1"


def test_local_compare_records_are_persisted_and_queryable(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    saved_count = db.insert_local_compare_records(
        [
            {
                "match_status": "已匹配",
                "matched_by": "匹配键",
                "price_relation": "抓取价更高",
                "source_row_no": "1",
                "group_name": "海天味极鲜生抽500ml",
                "product_name": "海天味极鲜生抽",
                "category": "酱油",
                "brand": "海天",
                "product_series": "味极鲜生抽",
                "spec_text": "500ml",
                "site_name": "线下门店",
                "local_price": 9.8,
                "box_price": 117.6,
                "tax_price": 10.29,
                "remarks": "本地报价单",
                "market_category": "干调类",
                "channel": "微信小程序",
                "matched_group_name": "海天味极鲜生抽500ml",
                "matched_product_name": "海天味极鲜生抽",
                "matched_site_name": "平台B",
                "current_price": 10.5,
                "price_diff": 0.7,
                "price_diff_rate": 0.0714,
                "promotion_text": "满减",
            },
            {
                "match_status": "未匹配",
                "matched_by": "未命中",
                "price_relation": "暂无",
                "source_row_no": "2",
                "group_name": "未知商品",
                "product_name": "未知商品",
                "category": "零食",
                "brand": "测试品牌",
                "product_series": "测试系列",
                "spec_text": "100g",
                "site_name": "本地表格",
                "local_price": 5.0,
                "box_price": None,
                "tax_price": None,
                "remarks": None,
                "market_category": "干调类",
                "channel": "Excel",
                "matched_group_name": None,
                "matched_product_name": None,
                "matched_site_name": None,
                "current_price": None,
                "price_diff": None,
                "price_diff_rate": None,
                "promotion_text": None,
            },
        ],
        captured_at="2026-04-01T11:00:00",
        batch_name="sample-batch",
    )

    result = db.get_local_compare_records()

    assert saved_count == 2
    assert result.iloc[0]["batch_name"] == "sample-batch"
    assert result.iloc[0]["match_status"] in {"已匹配", "未匹配"}
    assert "market_category" in result.columns
    assert "box_price" in result.columns
    assert len(result) == 2


def test_local_compare_batch_can_be_deleted(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    db.insert_local_compare_records(
        [
            {
                "match_status": "已匹配",
                "matched_by": "匹配键",
                "price_relation": "抓取价更高",
                "group_name": "测试商品A",
                "product_name": "测试商品A",
            },
            {
                "match_status": "未匹配",
                "matched_by": "未命中",
                "price_relation": "暂无",
                "group_name": "测试商品B",
                "product_name": "测试商品B",
            },
        ],
        captured_at="2026-04-01T12:00:00",
        batch_name="batch-delete",
    )

    deleted_count = db.delete_local_compare_batch("batch-delete")
    result = db.get_local_compare_records()

    assert deleted_count == 2
    assert result.empty



def test_failed_crawl_records_are_persisted_and_queryable(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    db.insert_failed_crawl_record(
        product_key="sku-1",
        captured_at="2026-04-01T10:00:00",
        group_name="酱油",
        product_name="海天味极鲜",
        source_url="https://example.com/item/1",
        site_name="平台A",
        fetch_mode="requests",
        status_code=429,
        error="HTTP 429",
        suggestion="降低频率",
        fallback_used=False,
        raw_payload={"demo": True},
    )
    db.insert_failed_crawl_record(
        product_key="sku-2",
        captured_at="2026-04-01T10:05:00",
        group_name="酱油",
        product_name="千禾生抽",
        source_url="https://example.com/item/2",
        site_name="平台B",
        fetch_mode="playwright",
        status_code=None,
        error="empty html after javascript render",
        suggestion="检查动态渲染",
        fallback_used=True,
        raw_payload={"demo": False},
    )

    result = db.get_failed_crawl_records()

    assert result["site_name"].tolist() == ["平台B", "平台A"]
    assert result.iloc[0]["fallback_used"] == 1
    assert result.iloc[1]["status_code"] == 429


def test_product_geo_fields_are_persisted_in_history_and_latest_records(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    product_id = db.upsert_product(
        product_key="geo-1",
        group_name="白菜",
        product_name="白菜",
        source_url="https://example.com/bc",
        site_name="PFSC | 北京新发地",
        category="蔬菜类",
        province="北京市",
        city="北京市",
        market_name="北京新发地",
        region_label="北京市",
    )
    db.insert_price_record(
        product_id=product_id,
        captured_at="2026-04-09T10:00:00",
        current_price=2.5,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={},
    )

    history_df = db.get_price_history()
    latest_df = db.get_latest_records()

    assert history_df.iloc[0]["province"] == "北京市"
    assert history_df.iloc[0]["market_name"] == "北京新发地"
    assert latest_df.iloc[0]["city"] == "北京市"
    assert latest_df.iloc[0]["region_label"] == "北京市"


def test_get_trend_history_for_product_keys_filters_to_target_products(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    keep_id = db.upsert_product(
        product_key="keep-1",
        group_name="土豆",
        product_name="土豆",
        source_url="https://example.com/keep",
        site_name="万邦国际",
        category="蔬菜类",
    )
    drop_id = db.upsert_product(
        product_key="drop-1",
        group_name="白菜",
        product_name="白菜",
        source_url="https://example.com/drop",
        site_name="万邦国际",
        category="蔬菜类",
    )
    db.insert_price_record(
        product_id=keep_id,
        captured_at="2026-04-15T10:00:00",
        current_price=2.6,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={},
    )
    db.insert_price_record(
        product_id=drop_id,
        captured_at="2026-04-15T11:00:00",
        current_price=3.1,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={},
    )

    result = db.get_trend_history_for_product_keys(["keep-1"])

    assert len(result) == 1
    assert result.iloc[0]["product_key"] == "keep-1"


def test_bulk_insert_records_can_restore_table_rows(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()
    db.bulk_insert_records(
        "products",
        [
            {
                "id": 1,
                "product_key": "bulk-1",
                "group_name": "青椒",
                "product_name": "青椒",
                "source_url": "https://example.com/a",
                "site_name": "平台A",
                "created_at": "2026-04-14T10:00:00",
                "category": "蔬菜",
                "brand": None,
                "product_series": None,
                "spec_text": None,
                "compare_key": None,
                "province": None,
                "city": None,
                "market_name": None,
                "region_label": None,
            }
        ],
    )

    result = db.get_all_products()

    assert len(result) == 1
    assert result.iloc[0]["product_key"] == "bulk-1"


def test_supplier_quotes_can_be_upserted_and_compared(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        box_price=223.2,
        quoted_at="2026-04-20T09:00:00",
        remarks="今日现货",
    )
    db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=17.9,
        box_price=214.8,
        quoted_at="2026-04-20T10:00:00",
        remarks="上午更新",
    )

    supplier_rows = db.get_suppliers(active_only=True)
    latest_quotes = db.get_latest_supplier_quotes("香菇|干调类|500g")

    assert len(supplier_rows) == 1
    assert supplier_rows.iloc[0]["quote_count"] == 2
    assert len(latest_quotes) == 1
    assert latest_quotes.iloc[0]["supplier_name"] == "莲菜档口A"
    assert latest_quotes.iloc[0]["quote_price"] == 17.9
    assert latest_quotes.iloc[0]["market_category"] == "干调类"


def test_supplier_overview_queries_return_category_and_recent_rows(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    dried_supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
        is_active=True,
    )
    vegetable_supplier_id = db.upsert_supplier(
        supplier_name="蔬菜档口B",
        contact_name="小李",
        market_scope="本地市场",
        market_category="蔬菜类",
        channel="门店直报",
        is_active=False,
    )
    db.insert_supplier_price_record(
        supplier_id=dried_supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=17.9,
        quoted_at="2026-04-20T10:00:00",
    )
    db.insert_supplier_price_record(
        supplier_id=vegetable_supplier_id,
        price_identity_key="菠菜|蔬菜类|斤",
        price_identity_label="菠菜 | 蔬菜类 | 斤",
        product_name="菠菜",
        category="蔬菜类",
        spec_text="斤",
        market_category="蔬菜类",
        channel="门店直报",
        quote_price=4.8,
        quoted_at="2026-04-20T09:30:00",
    )

    category_rows = db.get_supplier_category_summary()
    recent_rows = db.get_recent_supplier_quotes(limit=2)

    assert len(category_rows) == 2
    assert set(category_rows["market_category"].tolist()) == {"干调类", "蔬菜类"}
    assert category_rows.loc[category_rows["market_category"] == "干调类", "quote_count"].iloc[0] == 1
    assert len(recent_rows) == 2
    assert recent_rows.iloc[0]["supplier_name"] == "莲菜档口A"
    assert recent_rows.iloc[1]["supplier_name"] == "蔬菜档口B"
