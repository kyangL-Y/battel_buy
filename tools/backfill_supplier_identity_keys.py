from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import bindparam, text

from storage.database import Database
from tools.audit_supplier_identity_keys import build_audit_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 supplier_price_records 中的旧 identity key 回填为统一键")
    parser.add_argument("--apply", action="store_true", help="默认只预览；带上该参数才实际执行更新")
    parser.add_argument("--include-collisions", action="store_true", help="默认跳过同一供应商已同时存在旧键和新键的碰撞项")
    parser.add_argument("--limit", type=int, default=50, help="文本预览时最多展示多少条映射")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果")
    return parser.parse_args()


def build_plan(db: Database, include_collisions: bool = False) -> tuple[list[dict[str, Any]], int]:
    audit_rows = build_audit_rows(db)
    plan: list[dict[str, Any]] = []
    skipped_collision_keys = 0
    for row in audit_rows:
        if row.status != "legacy_alias" or not row.canonical_key:
            continue
        if row.collision_supplier_count > 0 and not include_collisions:
            skipped_collision_keys += 1
            continue
        plan.append(
            {
                "legacy_key": row.legacy_key,
                "canonical_key": row.canonical_key,
                "quote_count": row.quote_count,
                "active_quote_count": row.active_quote_count,
                "supplier_count": row.supplier_count,
                "collision_supplier_count": row.collision_supplier_count,
                "latest_quoted_at": row.latest_quoted_at,
                "sample_product_name": row.sample_product_name,
            }
        )
    return plan, skipped_collision_keys


def apply_plan(db: Database, plan: list[dict[str, Any]]) -> dict[str, Any]:
    if not plan:
        return {"updated_keys": 0, "updated_records": 0}

    updated_keys = 0
    updated_records = 0
    with db.connect() as conn:
        for item in plan:
            result = conn.execute(
                text(
                    """
                    UPDATE supplier_price_records
                    SET price_identity_key = :canonical_key
                    WHERE price_identity_key = :legacy_key
                    """
                ),
                {
                    "legacy_key": item["legacy_key"],
                    "canonical_key": item["canonical_key"],
                },
            )
            affected = int(result.rowcount or 0)
            if affected > 0:
                updated_keys += 1
                updated_records += affected
    return {"updated_keys": updated_keys, "updated_records": updated_records}


def build_payload(
    plan: list[dict[str, Any]],
    skipped_collision_keys: int,
    apply_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = {
        "planned_keys": len(plan),
        "planned_records": sum(int(item["quote_count"]) for item in plan),
        "collision_skipped_keys": skipped_collision_keys,
    }
    payload = {"summary": summary, "plan": plan}
    if apply_result is not None:
        payload["apply_result"] = apply_result
    return payload


def print_text(payload: dict[str, Any], limit: int) -> None:
    print("== Supplier Identity Backfill ==")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print("\n[plan]")
    for item in payload["plan"][:limit]:
        print(json.dumps(item, ensure_ascii=False))
    if "apply_result" in payload:
        print("\n[apply_result]")
        print(json.dumps(payload["apply_result"], ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    db = Database()
    plan, skipped_collision_keys = build_plan(db, include_collisions=args.include_collisions)
    apply_result = apply_plan(db, plan) if args.apply else None
    payload = build_payload(plan, skipped_collision_keys=skipped_collision_keys, apply_result=apply_result)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(payload, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
