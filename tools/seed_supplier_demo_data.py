from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import bindparam, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage.database import DEFAULT_DB_PATH, Database
from utils.auth import hash_password


@dataclass(frozen=True)
class DemoSupplierConfig:
    key: str
    supplier_name: str
    contact_name: str
    contact_phone: str
    market_scope: str
    market_category: str
    channel: str
    notes: str
    username: str
    password: str
    display_name: str
    is_active: bool = True


DEMO_SUPPLIERS = [
    DemoSupplierConfig(
        key="veg",
        supplier_name="鲜蔬直采A",
        contact_name="刘姐",
        contact_phone="13900000011",
        market_scope="杭州主城区",
        market_category="蔬菜类",
        channel="微信小程序",
        notes="适合演示日配蔬菜和快速补货。",
        username="demo-veg-a",
        password="demo123456",
        display_name="鲜蔬直采A",
    ),
    DemoSupplierConfig(
        key="sea",
        supplier_name="海鲜供应站B",
        contact_name="阿海",
        contact_phone="13900000022",
        market_scope="杭州水产档口",
        market_category="水产类",
        channel="Excel",
        notes="适合演示价格波动、部分付款和批量导入。",
        username="demo-sea-b",
        password="demo123456",
        display_name="海鲜供应站B",
    ),
    DemoSupplierConfig(
        key="pantry",
        supplier_name="粮油干调C",
        contact_name="周老板",
        contact_phone="13900000033",
        market_scope="杭州餐饮后厨",
        market_category="粮油米面类",
        channel="门店直报",
        notes="适合演示稳定品类、月结和账号管理。",
        username="demo-pantry-c",
        password="demo123456",
        display_name="粮油干调C",
    ),
    DemoSupplierConfig(
        key="disabled",
        supplier_name="停用演示档口D",
        contact_name="测试员",
        contact_phone="13900000044",
        market_scope="演示停用账号",
        market_category="冻品类",
        channel="电话报价",
        notes="适合演示停用账号无法登录。",
        username="supplier-disabled",
        password="demo123456",
        display_name="停用演示账号",
        is_active=False,
    ),
]

PREFERRED_COMPARE_KEYS = {
    "veg": ["土豆", "大葱", "小白菜", "冬瓜", "圆白菜"],
    "sea": ["基围虾", "大黄花鱼", "扇贝", "三文鱼", "加吉鱼"],
    "pantry": ["蚝油", "大米", "一级豆油", "大豆调和油", "万邦国际行情|干调类|未指定|未指定"],
}


def load_compare_key_catalog(db: Database) -> dict[str, dict[str, str]]:
    rows = db._read_sql(
        """
        SELECT
            compare_key,
            MAX(product_name) AS product_name,
            MAX(category) AS category,
            MAX(spec_text) AS spec_text
        FROM products
        WHERE COALESCE(compare_key, '') <> ''
        GROUP BY compare_key
        """
    )
    catalog: dict[str, dict[str, str]] = {}
    for _, row in rows.iterrows():
        compare_key = str(row.get("compare_key") or "").strip()
        if not compare_key:
            continue
        catalog[compare_key] = {
            "product_name": str(row.get("product_name") or compare_key).strip() or compare_key,
            "category": str(row.get("category") or "").strip(),
            "spec_text": str(row.get("spec_text") or "公斤").strip() or "公斤",
        }
    return catalog


def pick_demo_keys(catalog: dict[str, dict[str, str]], key_group: str, count: int = 3) -> list[str]:
    preferred = PREFERRED_COMPARE_KEYS.get(key_group, [])
    selected = [item for item in preferred if item in catalog]
    if len(selected) >= count:
        return selected[:count]

    for candidate in catalog:
        if candidate not in selected:
            selected.append(candidate)
        if len(selected) >= count:
            break
    if len(selected) < count:
        raise RuntimeError("可用商品对比键不足，无法生成演示报价。")
    return selected[:count]


def cleanup_existing_demo_rows(db: Database) -> None:
    supplier_names = [item.supplier_name for item in DEMO_SUPPLIERS]
    usernames = [item.username for item in DEMO_SUPPLIERS]
    rows = db.get_suppliers(active_only=False)
    supplier_ids = [
        int(row["id"])
        for _, row in rows.iterrows()
        if str(row.get("supplier_name") or "").strip() in supplier_names
    ]
    with db.connect() as conn:
        conn.execute(
            text("DELETE FROM auth_users WHERE username IN :usernames").bindparams(bindparam("usernames", expanding=True)),
            {"usernames": usernames},
        )
        if supplier_ids:
            conn.execute(
                text("DELETE FROM supplier_quote_actions WHERE supplier_id IN :supplier_ids").bindparams(bindparam("supplier_ids", expanding=True)),
                {"supplier_ids": supplier_ids},
            )
            conn.execute(
                text("DELETE FROM supplier_settlement_records WHERE supplier_id IN :supplier_ids").bindparams(bindparam("supplier_ids", expanding=True)),
                {"supplier_ids": supplier_ids},
            )
            conn.execute(
                text("DELETE FROM supplier_price_records WHERE supplier_id IN :supplier_ids").bindparams(bindparam("supplier_ids", expanding=True)),
                {"supplier_ids": supplier_ids},
            )
            conn.execute(
                text("DELETE FROM suppliers WHERE id IN :supplier_ids").bindparams(bindparam("supplier_ids", expanding=True)),
                {"supplier_ids": supplier_ids},
            )


def iso_at(days_ago: int, hour: int, minute: int) -> str:
    base = datetime.now().replace(second=0, microsecond=0) - timedelta(days=days_ago)
    return base.replace(hour=hour, minute=minute).isoformat()


def seed_demo_suppliers(db: Database, catalog: dict[str, dict[str, str]]) -> None:
    supplier_ids: dict[str, int] = {}
    for item in DEMO_SUPPLIERS:
        supplier_ids[item.key] = db.upsert_supplier(
            supplier_name=item.supplier_name,
            contact_name=item.contact_name,
            contact_phone=item.contact_phone,
            market_scope=item.market_scope,
            market_category=item.market_category,
            channel=item.channel,
            notes=item.notes,
            is_active=item.is_active,
        )
        db.upsert_auth_user(
            username=item.username,
            password_hash=hash_password(item.password),
            role="supplier",
            supplier_id=supplier_ids[item.key],
            display_name=item.display_name,
            is_active=item.is_active,
        )

    veg_keys = pick_demo_keys(catalog, "veg")
    sea_keys = pick_demo_keys(catalog, "sea")
    pantry_keys = pick_demo_keys(catalog, "pantry")

    created_record_ids: dict[str, list[int]] = {"veg": [], "sea": [], "pantry": []}

    quote_plan = {
        "veg": [
            (veg_keys[0], 2.65, "现货", "今天晨采直送", iso_at(0, 5, 35)),
            (veg_keys[1], 7.20, "现货", "适合做展示商品", iso_at(0, 5, 42)),
            (veg_keys[2], 4.10, "预定", "下午补货一批", iso_at(0, 5, 48)),
            (veg_keys[0], 2.90, "现货", "旧报价，后续作废", iso_at(2, 6, 10)),
        ],
        "sea": [
            (sea_keys[0], 58.00, "现货", "活鲜到港，适合演示高价品", iso_at(0, 4, 55)),
            (sea_keys[1], 36.50, "现货", "早市价，销量稳定", iso_at(0, 5, 5)),
            (sea_keys[2], 24.80, "缺货", "午后到货", iso_at(1, 11, 15)),
            (sea_keys[0], 56.00, "现货", "昨日报价，适合看历史差异", iso_at(3, 6, 25)),
        ],
        "pantry": [
            (pantry_keys[0], 12.60, "现货", "调味品长期供货", iso_at(0, 7, 25)),
            (pantry_keys[1], 5.80, "现货", "可演示稳定价格带", iso_at(1, 8, 0)),
            (pantry_keys[2], 68.00, "现货", "桶装可月结", iso_at(2, 9, 10)),
        ],
    }

    for supplier_key, entries in quote_plan.items():
        supplier_config = next(item for item in DEMO_SUPPLIERS if item.key == supplier_key)
        for index, (compare_key, quote_price, inventory_status, remarks, quoted_at) in enumerate(entries, start=1):
            item = catalog[compare_key]
            record_id = db.insert_supplier_price_record(
                supplier_id=supplier_ids[supplier_key],
                price_identity_key=compare_key,
                price_identity_label=item["product_name"],
                product_name=item["product_name"],
                category=item["category"],
                spec_text=item["spec_text"],
                market_category=supplier_config.market_category,
                channel=supplier_config.channel,
                quote_price=quote_price,
                quote_unit=item["spec_text"] or "公斤",
                box_price=round(quote_price * 8, 2),
                tax_price=round(quote_price * 1.03, 2),
                inventory_status=inventory_status,
                remarks=remarks,
                quoted_by=supplier_config.contact_name,
                quoted_at=quoted_at,
            )
            created_record_ids[supplier_key].append(record_id)
            if index == 1:
                db.insert_supplier_quote_action(
                    supplier_id=supplier_ids[supplier_key],
                    action_type="import_quotes",
                    record_id=record_id,
                    action_reason=f"{supplier_config.display_name} 批量导入报价",
                    operator_name=supplier_config.display_name,
                    action_payload={
                        "file_name": f"{supplier_config.username}-demo-import.xlsx",
                        "import_mode": "append",
                        "total_count": 3,
                        "success_count": 3,
                        "skipped_count": 0,
                        "failed_count": 0,
                    },
                    created_at=quoted_at,
                )

    invalidated_id = created_record_ids["veg"][-1]
    db.invalidate_supplier_price_record(invalidated_id, reason="旧报价已被最新价格覆盖")
    db.insert_supplier_quote_action(
        supplier_id=supplier_ids["veg"],
        action_type="invalidate",
        record_id=invalidated_id,
        action_reason="旧报价已被最新价格覆盖",
        operator_name="系统管理员",
        action_payload={"record_id": invalidated_id},
        created_at=iso_at(1, 10, 20),
    )

    copied_source = created_record_ids["sea"][1]
    copied_target = db.insert_supplier_price_record(
        supplier_id=supplier_ids["sea"],
        price_identity_key=sea_keys[1],
        price_identity_label=catalog[sea_keys[1]]["product_name"],
        product_name=catalog[sea_keys[1]]["product_name"],
        category=catalog[sea_keys[1]]["category"],
        spec_text=catalog[sea_keys[1]]["spec_text"],
        market_category="水产类",
        channel="Excel",
        quote_price=37.20,
        quote_unit=catalog[sea_keys[1]]["spec_text"] or "公斤",
        box_price=round(37.20 * 8, 2),
        tax_price=round(37.20 * 1.03, 2),
        inventory_status="现货",
        remarks="复制历史报价后微调",
        quoted_by="阿海",
        quoted_at=iso_at(0, 9, 18),
    )
    db.insert_supplier_quote_action(
        supplier_id=supplier_ids["sea"],
        action_type="copy_as_new",
        record_id=copied_source,
        target_record_id=copied_target,
        action_reason="复制历史报价为新报价",
        operator_name="阿海",
        action_payload={"source_record_id": copied_source, "target_record_id": copied_target},
        created_at=iso_at(0, 9, 18),
    )

    veg_settlement_id = db.insert_supplier_settlement_record(
        supplier_id=supplier_ids["veg"],
        settlement_title="本周蔬菜日配结算单",
        period_start=iso_at(4, 0, 0),
        period_end=iso_at(0, 23, 59),
        quote_record_ids=created_record_ids["veg"][:3],
        total_amount=round(2.65 + 7.20 + 4.10, 2),
        paid_amount=4.00,
        payment_due_date=iso_at(-2, 17, 0),
        remarks="适合演示部分付款和继续跟进。",
        created_by="系统管理员",
        created_at=iso_at(0, 10, 40),
    )
    sea_settlement_id = db.insert_supplier_settlement_record(
        supplier_id=supplier_ids["sea"],
        settlement_title="海鲜周转账期单",
        period_start=iso_at(5, 0, 0),
        period_end=iso_at(0, 23, 0),
        quote_record_ids=created_record_ids["sea"][:3],
        total_amount=round(58.00 + 36.50 + 24.80, 2),
        paid_amount=0,
        payment_due_date=iso_at(2, 18, 0),
        remarks="适合演示待付款和高金额账单。",
        created_by="系统管理员",
        created_at=iso_at(0, 11, 5),
    )
    pantry_settlement_id = db.insert_supplier_settlement_record(
        supplier_id=supplier_ids["pantry"],
        settlement_title="月结粮油干调单",
        period_start=iso_at(20, 0, 0),
        period_end=iso_at(0, 23, 0),
        quote_record_ids=created_record_ids["pantry"],
        total_amount=round(12.60 + 5.80 + 68.00, 2),
        paid_amount=round(12.60 + 5.80 + 68.00, 2),
        payment_due_date=iso_at(5, 17, 0),
        payment_date=iso_at(1, 16, 20),
        status="paid",
        remarks="适合演示已结清账单。",
        created_by="系统管理员",
        created_at=iso_at(0, 11, 45),
    )

    for supplier_key, settlement_id, action_reason in [
        ("veg", veg_settlement_id, "创建蔬菜结算单"),
        ("sea", sea_settlement_id, "创建海鲜结算单"),
        ("pantry", pantry_settlement_id, "创建粮油干调结算单"),
    ]:
        db.insert_supplier_quote_action(
            supplier_id=supplier_ids[supplier_key],
            action_type="create_settlement",
            record_id=settlement_id,
            action_reason=action_reason,
            operator_name="系统管理员",
            action_payload={"settlement_id": settlement_id},
            created_at=iso_at(0, 11, 50),
        )


def write_demo_doc(root: Path) -> Path:
    doc_path = root / "docs" / "supplier-backend-demo-accounts.md"
    doc_path.write_text(
        "\n".join(
            [
                "# 供应商管理台演示账号",
                "",
                "## 管理员",
                "- `admin / admin123`",
                "",
                "## 供应商账号",
                "- `demo-veg-a / demo123456`",
                "- `demo-sea-b / demo123456`",
                "- `demo-pantry-c / demo123456`",
                "",
                "## 停用账号",
                "- `supplier-disabled / demo123456`",
                "",
                "## 演示建议",
                "- 管理员先看供应商管理、录价中心、结算台账、操作日志。",
                "- 供应商账号重点演示“我的报价录入”和“批量导入我的报价”。",
                "- 停用账号用于演示登录拦截提示。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return doc_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed supplier backend demo data.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to sqlite database file.")
    args = parser.parse_args()

    db = Database(Path(args.db))
    db.init_db()
    catalog = load_compare_key_catalog(db)
    cleanup_existing_demo_rows(db)
    seed_demo_suppliers(db, catalog)
    doc_path = write_demo_doc(Path(__file__).resolve().parents[1])

    supplier_count = len(db.get_suppliers(active_only=False))
    print(f"已写入供应商演示数据，当前供应商数: {supplier_count}")
    print("管理员账号: admin / admin123")
    print("供应商账号: demo-veg-a / demo123456, demo-sea-b / demo123456, demo-pantry-c / demo123456")
    print("停用账号: supplier-disabled / demo123456")
    print(f"账号说明: {doc_path}")


if __name__ == "__main__":
    main()
