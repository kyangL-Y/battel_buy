from pathlib import Path

import pytest

from storage.database import Database
from utils.auth import hash_password, verify_password


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


def test_get_latest_records_exposes_only_supported_source_image_url(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()
    liancai_product_id = db.upsert_product(
        product_key="liancai-image-1",
        group_name="白扣",
        product_name="白扣",
        source_url="https://lcwgetway.liancaiwang.cn/app/product",
        site_name="莲菜网App | 干调类",
        category="干调类",
        image_url="https://cdnlcw.liancaiwang.cn/uploads/baiko.jpg",
    )
    meicai_product_id = db.upsert_product(
        product_key="meicai-image-1",
        group_name="美菜网",
        product_name="青菜",
        source_url="https://mall-entrance.yunshanmeicai.com",
        site_name="美菜网App | 推荐商品",
        category="蔬菜类",
        image_url="https://img-oss.yunshanmeicai.com/uploads/greens.jpg",
    )
    other_product_id = db.upsert_product(
        product_key="other-image-1",
        group_name="白菜",
        product_name="白菜",
        source_url="https://www.wbncp.com/product",
        site_name="万邦国际",
        category="蔬菜类",
        image_url="https://example.com/not-liancai.jpg",
    )
    db.insert_price_record(
        product_id=liancai_product_id,
        captured_at="2026-04-15T10:00:00",
        current_price=12.0,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={"source": "liancai"},
    )
    db.insert_price_record(
        product_id=meicai_product_id,
        captured_at="2026-04-15T10:00:00",
        current_price=3.0,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={"source": "meicai"},
    )
    db.insert_price_record(
        product_id=other_product_id,
        captured_at="2026-04-15T10:00:00",
        current_price=2.0,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={"source": "other"},
    )

    latest = db.get_latest_records().set_index("product_key")

    assert latest.loc["liancai-image-1", "image_url"] == "https://cdnlcw.liancaiwang.cn/uploads/baiko.jpg"
    assert latest.loc["meicai-image-1", "image_url"] == "https://img-oss.yunshanmeicai.com/uploads/greens.jpg"
    assert latest.loc["other-image-1", "image_url"] is None


def test_backfill_meicai_product_image_urls_uses_only_meicai_payloads(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()
    meicai_product_id = db.upsert_product(
        product_key="meicai-backfill-1",
        group_name="美菜网",
        product_name="韭菜",
        source_url="https://mall-entrance.yunshanmeicai.com",
        site_name="美菜网App | 推荐商品",
        category="蔬菜类",
    )
    liancai_product_id = db.upsert_product(
        product_key="liancai-backfill-1",
        group_name="莲菜网",
        product_name="韭菜",
        source_url="https://lcwgetway.liancaiwang.cn/app/product",
        site_name="莲菜网App | 蔬菜类",
        category="蔬菜类",
    )
    db.insert_price_record(
        product_id=meicai_product_id,
        captured_at="2026-04-15T10:00:00",
        current_price=3.0,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={
            "site_name": "美菜网App | 推荐商品",
            "parsed": {
                "extra_fields": {
                    "cover": "https://img-oss.yunshanmeicai.com/runtime-chive.jpg",
                },
            },
        },
    )
    db.insert_price_record(
        product_id=meicai_product_id,
        captured_at="2026-04-16T10:00:00",
        current_price=3.1,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={
            "site_name": "美菜网App | 推荐商品",
            "parsed": {"extra_fields": {}},
        },
    )
    db.insert_price_record(
        product_id=liancai_product_id,
        captured_at="2026-04-15T10:00:00",
        current_price=3.2,
        original_price=None,
        promotion_text=None,
        currency="CNY",
        availability=None,
        raw_payload={
            "site_name": "莲菜网App | 蔬菜类",
            "parsed": {
                "extra_fields": {
                    "cover": "https://img-oss.yunshanmeicai.com/should-not-leak.jpg",
                },
            },
        },
    )

    assert db.backfill_meicai_product_image_urls() == 1
    latest = db.get_latest_records().set_index("product_key")

    assert latest.loc["meicai-backfill-1", "image_url"] == "https://img-oss.yunshanmeicai.com/runtime-chive.jpg"
    assert latest.loc["liancai-backfill-1", "image_url"] is None


def test_bulk_upsert_products_and_insert_price_records(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    product_ids = db.bulk_upsert_products(
        [
            {
                "product_key": "bulk-1",
                "group_name": "蔬菜",
                "product_name": "白菜",
                "source_url": "https://example.com/a",
                "site_name": "批量站点",
                "category": "叶菜",
            },
            {
                "product_key": "bulk-2",
                "group_name": "蔬菜",
                "product_name": "菠菜",
                "source_url": "https://example.com/b",
                "site_name": "批量站点",
                "category": "叶菜",
            },
        ],
        batch_size=1,
    )

    assert set(product_ids) == {"bulk-1", "bulk-2"}

    updated_product_ids = db.bulk_upsert_products(
        [
            {
                "product_key": "bulk-1",
                "group_name": "蔬菜",
                "product_name": "大白菜",
                "source_url": "https://example.com/a",
                "site_name": "批量站点",
                "category": "叶菜",
            }
        ]
    )
    assert updated_product_ids["bulk-1"] == product_ids["bulk-1"]

    inserted_count = db.bulk_insert_price_records(
        [
            {
                "product_id": product_ids["bulk-1"],
                "captured_at": "2026-05-14T10:00:00",
                "current_price": 1.2,
                "original_price": None,
                "promotion_text": None,
                "currency": "CNY",
                "availability": None,
                "raw_payload": {"source": "bulk"},
            },
            {
                "product_id": product_ids["bulk-2"],
                "captured_at": "2026-05-14T10:00:00",
                "current_price": 2.3,
                "original_price": None,
                "promotion_text": None,
                "currency": "CNY",
                "availability": None,
                "raw_payload": {"source": "bulk"},
            },
        ],
        batch_size=1,
    )

    assert inserted_count == 2
    result = db.get_price_history()
    assert len(result) == 2
    assert set(result["product_name"].tolist()) == {"大白菜", "菠菜"}


def test_default_admin_account_is_seeded_and_password_is_hashed(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    auth_rows = db.get_auth_user_by_username("admin")

    assert len(auth_rows) == 1
    row = auth_rows.iloc[0]
    assert row["role"] == "admin"
    assert verify_password("admin123", row["password_hash"]) is True


def test_default_admin_account_is_not_reset_on_existing_database(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()
    db.upsert_auth_user(
        username="admin",
        password_hash=hash_password("admin123456"),
        role="admin",
        display_name="旧管理员",
        is_active=False,
    )

    db.init_db()
    auth_rows = db.get_auth_user_by_username("admin")

    assert len(auth_rows) == 1
    row = auth_rows.iloc[0]
    assert row["role"] == "admin"
    assert row["display_name"] == "旧管理员"
    assert bool(row["is_active"]) is False
    assert verify_password("admin123456", row["password_hash"]) is True


def test_supplier_auth_user_can_be_created_and_loaded_by_supplier_id(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
        is_active=True,
    )
    user_id = db.upsert_auth_user(
        username="lencai-a",
        password_hash="pbkdf2_sha256$390000$salt$hash",
        role="supplier",
        supplier_id=supplier_id,
        display_name="莲菜档口A",
        is_active=True,
    )
    supplier_auth_rows = db.get_auth_user_by_supplier_id(supplier_id)

    assert len(supplier_auth_rows) == 1
    assert supplier_auth_rows.iloc[0]["id"] == user_id
    assert supplier_auth_rows.iloc[0]["username"] == "lencai-a"
    assert supplier_auth_rows.iloc[0]["supplier_name"] == "莲菜档口A"


def test_supplier_auth_user_rejects_username_owned_by_another_supplier(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    first_supplier_id = db.upsert_supplier(supplier_name="莲菜档口A")
    second_supplier_id = db.upsert_supplier(supplier_name="莲菜档口B")
    first_user_id = db.upsert_auth_user(
        username="lencai-a",
        password_hash=hash_password("first12345"),
        role="supplier",
        supplier_id=first_supplier_id,
        display_name="莲菜档口A",
        is_active=True,
    )

    with pytest.raises(ValueError, match="username already exists"):
        db.upsert_auth_user(
            username="lencai-a",
            password_hash=hash_password("second12345"),
            role="supplier",
            supplier_id=second_supplier_id,
            display_name="莲菜档口B",
            is_active=True,
        )

    first_auth_rows = db.get_auth_user_by_supplier_id(first_supplier_id)
    second_auth_rows = db.get_auth_user_by_supplier_id(second_supplier_id)

    assert first_auth_rows.iloc[0]["id"] == first_user_id
    assert first_auth_rows.iloc[0]["username"] == "lencai-a"
    assert second_auth_rows.empty


def test_deleted_auth_user_is_archived_and_releases_username_and_supplier_binding(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(supplier_name="莲菜档口A")
    user_id = db.upsert_auth_user(
        username="lencai-a",
        password_hash=hash_password("first12345"),
        role="supplier",
        supplier_id=supplier_id,
        display_name="莲菜档口A",
        is_active=True,
    )

    assert db.delete_auth_user(user_id, deleted_by="tester") is True
    assert db.get_auth_user_by_id(user_id).empty
    assert db.get_auth_user_by_username("lencai-a").empty
    assert db.get_auth_user_by_supplier_id(supplier_id).empty

    archived_rows = db.get_auth_user_by_id(user_id, include_deleted=True)
    assert len(archived_rows) == 1
    archived_row = archived_rows.iloc[0]
    assert bool(archived_row["is_deleted"]) is True
    assert bool(archived_row["is_active"]) is False
    assert archived_row["username"] == f"__deleted_{user_id}"
    assert archived_row["deleted_username"] == "lencai-a"
    assert archived_row["deleted_by"] == "tester"

    recreated_user_id = db.upsert_auth_user(
        username="lencai-a",
        password_hash=hash_password("second12345"),
        role="supplier",
        supplier_id=supplier_id,
        display_name="莲菜档口A-新账号",
        is_active=True,
    )

    recreated_rows = db.get_auth_user_by_supplier_id(supplier_id)
    assert len(recreated_rows) == 1
    assert recreated_rows.iloc[0]["id"] == recreated_user_id
    assert recreated_rows.iloc[0]["username"] == "lencai-a"


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


def test_liancai_category_summary_matches_collapsed_source_name(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    db.upsert_product(
        product_key="lc-app-1",
        group_name="干调类",
        product_name="白扣",
        source_url="https://lcwgetway.liancaiwang.cn",
        site_name="莲菜网App | 干调类",
        category="干调类",
        liancai_top_category="干调类",
        liancai_subcategory="南北干货",
    )
    db.upsert_product(
        product_key="lc-h5-1",
        group_name="干调类",
        product_name="白芝麻",
        source_url="https://lcwgetway.liancaiwang.cn",
        site_name="莲菜网H5 | 干调类",
        category="干调类",
        liancai_top_category="干调类",
        liancai_subcategory="南北干货",
    )
    db.upsert_product(
        product_key="wb-1",
        group_name="白菜",
        product_name="白菜",
        source_url="https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
        site_name="万邦国际",
        category="蔬菜类",
        liancai_top_category="蔬菜类",
        liancai_subcategory="叶菜类",
    )

    result = db.get_liancai_category_summary(source_name="莲菜网")

    assert len(result) == 1
    row = result.iloc[0]
    assert row["liancai_top_category"] == "干调类"
    assert row["liancai_subcategory"] == "南北干货"
    assert row["product_count"] == 2


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


def test_invalidate_supplier_quote_excludes_it_from_active_aggregations(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    first_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
        remarks="早市报价",
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
        quoted_at="2026-04-20T10:00:00",
        remarks="上午更新",
    )

    invalidated_id = db.invalidate_supplier_price_record(first_record_id, reason="录错价格")
    active_quotes = db.get_latest_supplier_quotes("香菇|干调类|500g")
    history_quotes = db.get_supplier_quote_records(supplier_id, limit=10)

    assert invalidated_id == first_record_id
    assert len(active_quotes) == 1
    assert active_quotes.iloc[0]["quote_price"] == 17.9
    invalidated_row = history_quotes.loc[history_quotes["id"] == first_record_id].iloc[0]
    assert invalidated_row["status"] == "invalidated"
    assert invalidated_row["invalidated_reason"] == "录错价格"


def test_invalidate_supplier_quote_can_update_reason_after_already_invalidated(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
        remarks="早市报价",
    )

    db.invalidate_supplier_price_record(record_id, reason="录错价格")
    first_invalidated_record = db.get_supplier_price_record(record_id).iloc[0]
    db.invalidate_supplier_price_record(record_id, reason="规格填错")

    updated_record = db.get_supplier_price_record(record_id).iloc[0]

    assert updated_record["status"] == "invalidated"
    assert updated_record["invalidated_reason"] == "规格填错"
    assert updated_record["invalidated_at"] == first_invalidated_record["invalidated_at"]


def test_invalidate_supplier_quote_keeps_existing_reason_when_no_new_reason_is_provided(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
        remarks="早市报价",
    )

    db.invalidate_supplier_price_record(record_id, reason="录错价格")
    db.invalidate_supplier_price_record(record_id, reason=None)

    updated_record = db.get_supplier_price_record(record_id).iloc[0]

    assert updated_record["status"] == "invalidated"
    assert updated_record["invalidated_reason"] == "录错价格"


def test_get_latest_supplier_quote_for_supplier_returns_latest_active_record(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    first_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
    )
    latest_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
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

    db.invalidate_supplier_price_record(latest_record_id, reason="重复录入")
    latest_quote = db.get_latest_supplier_quote_for_supplier(supplier_id, "香菇|干调类|500g")

    assert len(latest_quote) == 1
    assert latest_quote.iloc[0]["id"] == first_record_id
    assert latest_quote.iloc[0]["quote_price"] == 18.6
    assert latest_quote.iloc[0]["status"] == "active"


def test_get_latest_supplier_quote_for_supplier_supports_identity_aliases(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="粮油档口A",
        contact_name="老周",
        market_scope="本地市场",
        market_category="粮油米面类",
        channel="微信小程序",
    )
    record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="一级豆油",
        price_identity_label="一级豆油",
        product_name="一级豆油",
        category="粮油米面类",
        spec_text="公斤",
        market_category="粮油米面类",
        channel="微信小程序",
        quote_price=11.8,
        quoted_at="2026-04-22T09:10:00",
    )

    latest_quote = db.get_latest_supplier_quote_for_supplier(
        supplier_id,
        price_identity_keys=["一级豆油|公斤", "一级豆油|食用植物油|公斤", "一级豆油"],
    )

    assert len(latest_quote) == 1
    assert latest_quote.iloc[0]["id"] == record_id
    assert latest_quote.iloc[0]["price_identity_key"] == "一级豆油"


def test_invalidate_supplier_quotes_by_identity_marks_all_active_quotes(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    first_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
    )
    second_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
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
    other_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="木耳|干调类|250g",
        price_identity_label="木耳 | 干调类 | 250g",
        product_name="木耳",
        category="干调类",
        spec_text="250g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=22.5,
        quoted_at="2026-04-20T11:00:00",
    )

    invalidated_ids = db.invalidate_supplier_quotes_by_identity(
        supplier_id,
        "香菇|干调类|500g",
        reason="导入覆盖：导入专员",
    )
    history_rows = db.get_supplier_quote_records(supplier_id, limit=10)
    remaining_quote = db.get_latest_supplier_quote_for_supplier(supplier_id, "香菇|干调类|500g")
    other_quote = db.get_latest_supplier_quote_for_supplier(supplier_id, "木耳|干调类|250g")

    assert invalidated_ids == [second_record_id, first_record_id]
    invalidated_rows = history_rows.loc[history_rows["price_identity_key"] == "香菇|干调类|500g"]
    assert set(invalidated_rows["status"].tolist()) == {"invalidated"}
    assert set(invalidated_rows["invalidated_reason"].tolist()) == {"导入覆盖：导入专员"}
    assert remaining_quote.empty
    assert len(other_quote) == 1
    assert other_quote.iloc[0]["id"] == other_record_id
    other_row = history_rows.loc[history_rows["id"] == other_record_id].iloc[0]
    assert other_row["status"] == "active"


def test_invalidate_supplier_quotes_by_identity_supports_identity_aliases(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="粮油档口A",
        contact_name="老周",
        market_scope="本地市场",
        market_category="粮油米面类",
        channel="微信小程序",
    )
    old_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="一级豆油",
        price_identity_label="一级豆油",
        product_name="一级豆油",
        category="粮油米面类",
        spec_text="公斤",
        market_category="粮油米面类",
        channel="微信小程序",
        quote_price=11.8,
        quoted_at="2026-04-22T09:10:00",
    )
    unified_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="一级豆油|公斤",
        price_identity_label="一级豆油 | 公斤",
        product_name="一级豆油",
        category="粮油米面类",
        spec_text="公斤",
        market_category="粮油米面类",
        channel="微信小程序",
        quote_price=11.6,
        quoted_at="2026-04-22T10:10:00",
    )

    invalidated_ids = db.invalidate_supplier_quotes_by_identity(
        supplier_id,
        price_identity_keys=["一级豆油|公斤", "一级豆油|食用植物油|公斤", "一级豆油"],
        reason="统一键覆盖",
    )
    history_rows = db.get_supplier_quote_records(supplier_id, limit=10)

    assert invalidated_ids == [unified_record_id, old_record_id]
    invalidated_rows = history_rows.loc[history_rows["id"].isin([old_record_id, unified_record_id])]
    assert set(invalidated_rows["status"].tolist()) == {"invalidated"}
    assert set(invalidated_rows["invalidated_reason"].tolist()) == {"统一键覆盖"}


def test_supplier_quote_actions_can_be_persisted_and_queried(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
        remarks="早市报价",
    )
    copied_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.8,
        quoted_at="2026-04-21T09:00:00",
        remarks="复制报价",
    )

    action_id = db.insert_supplier_quote_action(
        supplier_id=supplier_id,
        action_type="copy_as_new",
        record_id=record_id,
        target_record_id=copied_record_id,
        action_reason="历史报价复制为新报价",
        operator_name="供应商管理台",
        action_payload={"format": "manual"},
    )

    action_rows = db.get_supplier_quote_actions(supplier_id, limit=10)

    assert len(action_rows) == 1
    assert action_rows.iloc[0]["id"] == action_id
    assert action_rows.iloc[0]["action_type"] == "copy_as_new"
    assert action_rows.iloc[0]["product_name"] == "香菇"
    assert action_rows.iloc[0]["target_product_name"] == "香菇"


def test_supplier_registration_requests_can_be_created_and_reviewed(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    request_id = db.create_supplier_registration_request(
        company_name="新鲜蔬菜供应社",
        contact_name="小张",
        contact_phone="13800138000",
        username="fresh-supplier",
    )

    pending_rows = db.get_supplier_registration_requests(status="pending")

    assert len(pending_rows) == 1
    assert pending_rows.iloc[0]["id"] == request_id
    assert pending_rows.iloc[0]["company_name"] == "新鲜蔬菜供应社"
    assert pending_rows.iloc[0]["status"] == "pending"

    supplier_id = db.upsert_supplier(
        supplier_name="新鲜蔬菜供应社",
        contact_name="小张",
        contact_phone="13800138000",
        market_scope="本地市场",
        market_category="蔬菜类",
        channel="门店直报",
    )
    updated_request_id = db.update_supplier_registration_request(
        request_id,
        status="approved",
        review_notes="资料齐全，允许开通",
        reviewed_by="系统管理员",
        supplier_id=supplier_id,
    )

    approved_rows = db.get_supplier_registration_requests(status="approved", keyword="fresh")

    assert updated_request_id == request_id
    assert len(approved_rows) == 1
    assert approved_rows.iloc[0]["supplier_id"] == supplier_id
    assert approved_rows.iloc[0]["reviewed_by"] == "系统管理员"
    assert approved_rows.iloc[0]["supplier_name"] == "新鲜蔬菜供应社"


def test_supplier_import_quote_action_persists_extended_payload(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
    )

    db.insert_supplier_quote_action(
        supplier_id=supplier_id,
        action_type="import_quotes",
        record_id=record_id,
        action_reason="批量导入报价，成功 1 条，失败 1 条",
        operator_name="导入专员",
        action_payload={
            "file_name": "报价导入.xlsx",
            "success_count": 1,
            "failed_count": 1,
            "failure_examples": [{"row_number": 3, "failure_reason": "缺少 price_identity_key"}],
        },
        created_at="2026-04-21T12:00:00",
    )

    action_rows = db.get_supplier_quote_actions(supplier_id, limit=10, action_type="import_quotes")

    assert len(action_rows) == 1
    assert action_rows.iloc[0]["action_type"] == "import_quotes"
    assert action_rows.iloc[0]["record_id"] == record_id
    assert action_rows.iloc[0]["operator_name"] == "导入专员"
    assert '"file_name": "报价导入.xlsx"' in action_rows.iloc[0]["action_payload"]
    assert '"failed_count": 1' in action_rows.iloc[0]["action_payload"]


def test_supplier_quote_records_support_pagination_and_filters(tmp_path: Path):
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
        quoted_at="2026-04-20T09:00:00",
        remarks="早市报价",
    )
    invalidated_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.8,
        quoted_at="2026-04-21T09:00:00",
        remarks="复制报价",
    )
    db.invalidate_supplier_price_record(invalidated_id, reason="重复录入")

    filtered_total = db.count_supplier_quote_records(
        supplier_id,
        status="invalidated",
        keyword="复制",
        start_quoted_at="2026-04-21",
        end_quoted_at="2026-04-21T23:59:59",
        price_identity_key="香菇|干调类|500g",
    )
    filtered_rows = db.get_supplier_quote_records(
        supplier_id,
        limit=1,
        offset=0,
        status="invalidated",
        keyword="复制",
        start_quoted_at="2026-04-21",
        end_quoted_at="2026-04-21T23:59:59",
        price_identity_key="香菇|干调类|500g",
    )

    assert filtered_total == 1
    assert len(filtered_rows) == 1
    assert filtered_rows.iloc[0]["status"] == "invalidated"
    assert filtered_rows.iloc[0]["remarks"] == "复制报价"


def test_supplier_quote_records_support_identity_alias_filter(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="粮油档口A",
        contact_name="老周",
        market_scope="本地市场",
        market_category="粮油米面类",
        channel="微信小程序",
    )
    matched_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="一级豆油",
        price_identity_label="一级豆油",
        product_name="一级豆油",
        category="粮油米面类",
        spec_text="公斤",
        market_category="粮油米面类",
        channel="微信小程序",
        quote_price=11.8,
        quoted_at="2026-04-22T09:10:00",
        remarks="旧键报价",
    )
    db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="大米",
        price_identity_label="大米",
        product_name="大米",
        category="粮油米面类",
        spec_text="公斤",
        market_category="粮油米面类",
        channel="微信小程序",
        quote_price=5.8,
        quoted_at="2026-04-22T09:20:00",
        remarks="其他商品",
    )

    filtered_total = db.count_supplier_quote_records(
        supplier_id,
        price_identity_keys=["一级豆油|公斤", "一级豆油|食用植物油|公斤", "一级豆油"],
    )
    filtered_rows = db.get_supplier_quote_records(
        supplier_id,
        limit=10,
        price_identity_keys=["一级豆油|公斤", "一级豆油|食用植物油|公斤", "一级豆油"],
    )

    assert filtered_total == 1
    assert len(filtered_rows) == 1
    assert filtered_rows.iloc[0]["id"] == matched_record_id
    assert filtered_rows.iloc[0]["price_identity_key"] == "一级豆油"


def test_supplier_quote_actions_support_pagination_and_filters(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
        remarks="早市报价",
    )
    copied_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.8,
        quoted_at="2026-04-21T09:00:00",
        remarks="复制报价",
    )

    db.insert_supplier_quote_action(
        supplier_id=supplier_id,
        action_type="copy_as_new",
        record_id=record_id,
        target_record_id=copied_record_id,
        action_reason="历史报价复制为新报价",
        operator_name="供应商管理台",
        action_payload={"format": "manual"},
        created_at="2026-04-21T10:00:00",
    )
    db.insert_supplier_quote_action(
        supplier_id=supplier_id,
        action_type="export_quotes",
        record_id=record_id,
        action_reason="导出当前筛选的1条历史报价",
        operator_name="供应商管理台",
        action_payload={"format": "xlsx"},
        created_at="2026-04-21T11:00:00",
    )

    filtered_total = db.count_supplier_quote_actions(supplier_id, action_type="export_quotes")
    filtered_rows = db.get_supplier_quote_actions(supplier_id, limit=1, offset=0, action_type="export_quotes")

    assert filtered_total == 1
    assert len(filtered_rows) == 1
    assert filtered_rows.iloc[0]["action_type"] == "export_quotes"


def test_supplier_settlement_records_can_be_built_from_quotes_and_updated(tmp_path: Path):
    db = Database(tmp_path / "test_price_tracker.db")
    db.init_db()

    supplier_id = db.upsert_supplier(
        supplier_name="莲菜档口A",
        contact_name="老王",
        market_scope="本地市场",
        market_category="干调类",
        channel="微信小程序",
    )
    first_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="香菇|干调类|500g",
        price_identity_label="香菇 | 干调类 | 500g",
        product_name="香菇",
        category="干调类",
        spec_text="500g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=18.6,
        quoted_at="2026-04-20T09:00:00",
    )
    second_record_id = db.insert_supplier_price_record(
        supplier_id=supplier_id,
        price_identity_key="木耳|干调类|250g",
        price_identity_label="木耳 | 干调类 | 250g",
        product_name="木耳",
        category="干调类",
        spec_text="250g",
        market_category="干调类",
        channel="微信小程序",
        quote_price=22.5,
        quoted_at="2026-04-21T11:00:00",
    )

    settlement_id = db.build_supplier_settlement_from_quotes(
        supplier_id=supplier_id,
        settlement_title="4月干调月结单",
        quote_record_ids=[first_record_id, second_record_id],
        payment_due_date="2026-04-30",
        remarks="按已选报价生成",
        created_by="采购部小李",
    )
    settlement_rows = db.get_supplier_settlement_records(
        supplier_id,
        status="pending",
        keyword="月结",
        start_period_start="2026-04-20",
        end_period_end="2026-04-21",
    )

    assert len(settlement_rows) == 1
    assert settlement_rows.iloc[0]["id"] == settlement_id
    assert settlement_rows.iloc[0]["record_count"] == 2
    assert settlement_rows.iloc[0]["total_amount"] == 41.1
    assert settlement_rows.iloc[0]["paid_amount"] == 0
    assert settlement_rows.iloc[0]["pending_amount"] == 41.1
    assert settlement_rows.iloc[0]["period_start"] == "2026-04-20T09:00:00"
    assert settlement_rows.iloc[0]["period_end"] == "2026-04-21T11:00:00"
    assert db.count_supplier_settlement_records(
        supplier_id,
        status="pending",
        keyword="月结",
        start_period_start="2026-04-20",
        end_period_end="2026-04-21",
    ) == 1
    assert db.count_supplier_settlement_records(supplier_id, start_period_start="2026-04-22") == 0

    updated_id = db.update_supplier_settlement_record(
        settlement_id,
        paid_amount=20.0,
        payment_date="2026-04-22",
        remarks="先付一部分",
    )
    updated_rows = db.get_supplier_settlement_record(updated_id or 0)

    assert updated_id == settlement_id
    assert len(updated_rows) == 1
    assert updated_rows.iloc[0]["paid_amount"] == 20.0
    assert updated_rows.iloc[0]["pending_amount"] == 21.1
    assert updated_rows.iloc[0]["status"] == "partial"
    assert updated_rows.iloc[0]["payment_date"] == "2026-04-22"

    cancelled_id = db.update_supplier_settlement_record(settlement_id, status="cancelled")
    cancelled_rows = db.get_supplier_settlement_record(cancelled_id or 0)

    assert cancelled_id == settlement_id
    assert len(cancelled_rows) == 1
    assert cancelled_rows.iloc[0]["status"] == "cancelled"
