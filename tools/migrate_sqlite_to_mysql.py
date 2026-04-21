from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from storage.database import Database, TABLE_ORDER


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="将 SQLite 数据迁移到当前配置的 MySQL 数据库")
    parser.add_argument(
        "--source-sqlite",
        default="data/price_tracker.db",
        help="SQLite 源文件路径，默认读取 data/price_tracker.db",
    )
    parser.add_argument(
        "--keep-target-data",
        action="store_true",
        help="默认会清空目标库对应表；加此参数后保留目标表已有数据并追加导入",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="基于目标表当前最大 id 断点续传，只导入尚未写入目标库的记录",
    )
    parser.add_argument(
        "--drop-raw-payload",
        action="store_true",
        help="迁移时将 raw_payload 置空，减少远程 MySQL 写入体积",
    )
    return parser


def iter_table_records(
    source_db: Database,
    table_name: str,
    chunk_size: int = 5000,
    min_id: int = 0,
    drop_raw_payload: bool = False,
):
    query = text(f"SELECT * FROM {table_name} WHERE id > :min_id ORDER BY id")
    with source_db.connect() as conn:
        for chunk in pd.read_sql_query(query, conn, params={"min_id": int(min_id)}, chunksize=chunk_size):
            if chunk.empty:
                continue
            if drop_raw_payload and "raw_payload" in chunk.columns:
                chunk["raw_payload"] = None
            normalized = chunk.where(pd.notna(chunk), None)
            yield normalized.to_dict(orient="records")


def main() -> None:
    args = build_parser().parse_args()
    source_path = Path(args.source_sqlite)
    source_db = Database(source_path)
    target_db = Database()

    if target_db.backend != "mysql":
        raise SystemExit("当前运行时数据库配置不是 MySQL，请先设置 BATTEL_DB_BACKEND=mysql 等环境变量。")
    if not source_path.exists():
        raise SystemExit(f"未找到 SQLite 源文件: {source_path}")

    print(f"源库: {source_db.database_label}")
    print(f"目标库: {target_db.database_label}")

    source_db.init_db()
    target_db.init_db()

    if not args.keep_target_data and not args.resume:
        print("清空目标库旧数据...")
        target_db.reset_all_data()

    for table_name in TABLE_ORDER:
        source_total = int(source_db._read_sql(f"SELECT COUNT(*) AS c FROM {table_name}").iloc[0]["c"])
        print(f"{table_name}: 源库共 {source_total} 条")
        if source_total <= 0:
            continue

        min_id = 0
        existing_count = 0
        if args.keep_target_data or args.resume:
            target_stats = target_db._read_sql(
                f"SELECT COUNT(*) AS row_count, COALESCE(MAX(id), 0) AS max_id FROM {table_name}"
            ).iloc[0]
            existing_count = int(target_stats["row_count"])
            min_id = int(target_stats["max_id"])
            print(f"{table_name}: 目标库已有 {existing_count} 条，当前最大 id = {min_id}")

        remaining_total = int(
            source_db._read_sql(
                f"SELECT COUNT(*) AS c FROM {table_name} WHERE id > :min_id",
                {"min_id": min_id},
            ).iloc[0]["c"]
        )
        print(f"{table_name}: 待导入 {remaining_total} 条")
        if remaining_total <= 0:
            continue

        inserted_total = 0
        should_drop_raw_payload = args.drop_raw_payload and table_name in {
            "price_records",
            "failed_crawl_records",
            "local_compare_records",
        }
        for batch in iter_table_records(
            source_db,
            table_name,
            min_id=min_id,
            drop_raw_payload=should_drop_raw_payload,
        ):
            inserted_total += target_db.bulk_insert_records(table_name, batch)
            print(f"{table_name}: 已导入 {inserted_total}/{remaining_total} 条")

    print("迁移完成。")


if __name__ == "__main__":
    main()
