from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.liancai_category_mapping import suggest_liancai_mapping


DEFAULT_DB_PATH = Path("data/price_tracker.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按莲菜分类体系回填数据库映射字段")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite 数据库路径")
    parser.add_argument("--dry-run", action="store_true", help="仅统计，不写回数据库")
    parser.add_argument(
        "--overwrite-category",
        action="store_true",
        help="将 products.category 直接覆盖为莲菜细分类（无细分类时回退到顶层分类）",
    )
    return parser.parse_args()


def ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()}
    for name in [
        "liancai_top_category",
        "liancai_subcategory",
        "liancai_mapping_source",
        "liancai_mapped_at",
    ]:
        if name not in existing:
            conn.execute(f"ALTER TABLE products ADD COLUMN {name} TEXT")


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ensure_columns(conn)

    rows = conn.execute(
        """
        SELECT id, product_key, product_name, category, site_name
        FROM products
        ORDER BY id ASC
        """
    ).fetchall()

    mapped_at = datetime.now().isoformat(timespec="seconds")
    summary: dict[str, int] = {}
    changed = 0
    for row in rows:
        mapping = suggest_liancai_mapping(
            category=row["category"],
            product_name=row["product_name"],
            site_name=row["site_name"],
        )
        summary[mapping.source] = summary.get(mapping.source, 0) + 1
        if args.dry_run:
            continue
        conn.execute(
            """
            UPDATE products
            SET liancai_top_category = ?,
                liancai_subcategory = ?,
                liancai_mapping_source = ?,
                liancai_mapped_at = ?,
                category = CASE
                    WHEN ? THEN COALESCE(?, ?, category)
                    ELSE category
                END
            WHERE id = ?
            """,
            (
                mapping.top_category,
                mapping.subcategory,
                mapping.source,
                mapped_at,
                1 if args.overwrite_category else 0,
                mapping.subcategory,
                mapping.top_category,
                row["id"],
            ),
        )
        changed += 1

    if not args.dry_run:
        conn.commit()

    top_rows = conn.execute(
        """
        SELECT
            COALESCE(liancai_top_category, '未映射') AS top_category,
            COALESCE(liancai_subcategory, '未映射') AS subcategory,
            COUNT(*) AS total
        FROM products
        GROUP BY COALESCE(liancai_top_category, '未映射'), COALESCE(liancai_subcategory, '未映射')
        ORDER BY total DESC
        LIMIT 200
        """
    ).fetchall()
    conn.close()

    print(
        json.dumps(
            {
                "db": str(db_path),
                "dry_run": bool(args.dry_run),
                "rows_scanned": len(rows),
                "rows_updated": changed,
                "overwrite_category": bool(args.overwrite_category),
                "mapping_source_summary": summary,
                "top_rows": [dict(row) for row in top_rows],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
