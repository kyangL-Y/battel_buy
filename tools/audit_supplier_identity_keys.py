from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from api.deps import get_latest_cross_site_identity_df, get_latest_identity_df
from storage.database import Database


@dataclass
class IdentityAuditRow:
    legacy_key: str
    canonical_key: str | None
    canonical_label: str | None
    status: str
    quote_count: int
    active_quote_count: int
    supplier_count: int
    latest_quoted_at: str | None
    sample_product_name: str | None
    sample_category: str | None
    sample_spec_text: str | None
    collision_supplier_count: int
    collision_record_count: int


def normalize_text(value: object) -> str:
    return str(value or "").strip()


def build_alias_lookup() -> tuple[dict[str, str], dict[str, str]]:
    latest_identity_df = get_latest_identity_df()
    latest_cross_site_identity_df = get_latest_cross_site_identity_df()
    alias_to_canonical: dict[str, str] = {}
    canonical_to_label: dict[str, str] = {}

    if latest_cross_site_identity_df.empty:
        return alias_to_canonical, canonical_to_label

    merged = latest_cross_site_identity_df.copy()
    if not latest_identity_df.empty and "product_key" in latest_identity_df.columns:
        latest_identity_subset = latest_identity_df[
            [column for column in ["product_key", "price_identity_key", "price_identity_label"] if column in latest_identity_df.columns]
        ].drop_duplicates()
        merged = merged.merge(latest_identity_subset, on="product_key", how="left")

    for _, row in merged.iterrows():
        canonical_key = normalize_text(row.get("cross_site_identity_key"))
        canonical_label = normalize_text(row.get("cross_site_identity_label"))
        if not canonical_key:
            continue
        if canonical_label:
            canonical_to_label.setdefault(canonical_key, canonical_label)

        raw_aliases = [
            canonical_key,
            canonical_label,
            row.get("price_identity_key"),
            row.get("price_identity_label"),
            row.get("product_name"),
            row.get("group_name"),
        ]
        for alias in raw_aliases:
            text = normalize_text(alias)
            if not text:
                continue
            alias_to_canonical.setdefault(text, canonical_key)
            if "|" in text:
                prefix = text.split("|", 1)[0].strip()
                if prefix:
                    alias_to_canonical.setdefault(prefix, canonical_key)

    return alias_to_canonical, canonical_to_label


def load_supplier_identity_rows(db: Database) -> pd.DataFrame:
    return db._read_sql(
        """
        SELECT
            r.id,
            r.supplier_id,
            r.price_identity_key,
            r.price_identity_label,
            r.product_name,
            r.category,
            r.spec_text,
            COALESCE(r.status, 'active') AS status,
            r.quoted_at
        FROM supplier_price_records r
        ORDER BY r.quoted_at DESC, r.id DESC
        """
    )


def build_collision_map(rows: pd.DataFrame, alias_to_canonical: dict[str, str]) -> tuple[dict[tuple[int, str], set[str]], Counter[tuple[str, str]]]:
    supplier_canonical_keys: dict[tuple[int, str], set[str]] = defaultdict(set)
    collision_counter: Counter[tuple[str, str]] = Counter()

    for _, row in rows.iterrows():
        supplier_id = int(row.get("supplier_id") or 0)
        legacy_key = normalize_text(row.get("price_identity_key"))
        canonical_key = alias_to_canonical.get(legacy_key, "")
        if supplier_id <= 0 or not legacy_key or not canonical_key:
            continue
        bucket_key = (supplier_id, canonical_key)
        supplier_canonical_keys[bucket_key].add(legacy_key)

    for (supplier_id, canonical_key), legacy_keys in supplier_canonical_keys.items():
        if len(legacy_keys) <= 1:
            continue
        for legacy_key in legacy_keys:
            collision_counter[(legacy_key, canonical_key)] += 1

    return supplier_canonical_keys, collision_counter


def build_audit_rows(db: Database) -> list[IdentityAuditRow]:
    alias_to_canonical, canonical_to_label = build_alias_lookup()
    rows = load_supplier_identity_rows(db)
    if rows.empty:
        return []

    _, collision_counter = build_collision_map(rows, alias_to_canonical)
    audit_rows: list[IdentityAuditRow] = []

    for legacy_key, group_df in rows.groupby("price_identity_key", dropna=False):
        normalized_key = normalize_text(legacy_key)
        if not normalized_key:
            continue
        canonical_key = alias_to_canonical.get(normalized_key)
        canonical_label = canonical_to_label.get(canonical_key or "")
        active_quote_count = int((group_df["status"] == "active").sum())
        quote_count = int(len(group_df))
        supplier_count = int(group_df["supplier_id"].nunique())
        latest_quoted_at = normalize_text(group_df["quoted_at"].iloc[0]) or None
        sample_row = group_df.iloc[0]
        collision_supplier_count = collision_counter.get((normalized_key, canonical_key or ""), 0)
        collision_record_count = collision_supplier_count * quote_count if collision_supplier_count else 0

        if canonical_key == normalized_key:
            status = "canonical"
        elif canonical_key:
            status = "legacy_alias"
        else:
            status = "unresolved"

        audit_rows.append(
            IdentityAuditRow(
                legacy_key=normalized_key,
                canonical_key=canonical_key,
                canonical_label=canonical_label or None,
                status=status,
                quote_count=quote_count,
                active_quote_count=active_quote_count,
                supplier_count=supplier_count,
                latest_quoted_at=latest_quoted_at,
                sample_product_name=normalize_text(sample_row.get("product_name")) or None,
                sample_category=normalize_text(sample_row.get("category")) or None,
                sample_spec_text=normalize_text(sample_row.get("spec_text")) or None,
                collision_supplier_count=collision_supplier_count,
                collision_record_count=collision_record_count,
            )
        )

    return sorted(
        audit_rows,
        key=lambda item: (
            0 if item.status == "legacy_alias" else 1 if item.status == "unresolved" else 2,
            -item.quote_count,
            item.legacy_key,
        ),
    )


def build_summary(rows: list[IdentityAuditRow]) -> dict[str, Any]:
    summary = {
        "total_keys": len(rows),
        "canonical_keys": 0,
        "legacy_alias_keys": 0,
        "unresolved_keys": 0,
        "total_quotes": 0,
        "legacy_alias_quotes": 0,
        "unresolved_quotes": 0,
        "collision_suppliers": 0,
    }
    for row in rows:
        summary["total_quotes"] += row.quote_count
        if row.status == "canonical":
            summary["canonical_keys"] += 1
        elif row.status == "legacy_alias":
            summary["legacy_alias_keys"] += 1
            summary["legacy_alias_quotes"] += row.quote_count
        else:
            summary["unresolved_keys"] += 1
            summary["unresolved_quotes"] += row.quote_count
        summary["collision_suppliers"] += row.collision_supplier_count
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 supplier_price_records 中的 identity key 是否需要回填")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果")
    parser.add_argument("--limit", type=int, default=30, help="文本输出时每个分组最多展示多少条")
    return parser.parse_args()


def print_text_report(rows: list[IdentityAuditRow], limit: int) -> None:
    summary = build_summary(rows)
    print("== Supplier Identity Audit ==")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    groups = {
        "legacy_alias": [row for row in rows if row.status == "legacy_alias"],
        "unresolved": [row for row in rows if row.status == "unresolved"],
        "canonical": [row for row in rows if row.status == "canonical"],
    }
    for group_name, items in groups.items():
        print(f"\n[{group_name}] count={len(items)}")
        for row in items[:limit]:
            print(
                json.dumps(
                    asdict(row),
                    ensure_ascii=False,
                )
            )


def main() -> int:
    args = parse_args()
    db = Database()
    audit_rows = build_audit_rows(db)
    payload = {
        "summary": build_summary(audit_rows),
        "rows": [asdict(row) for row in audit_rows],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text_report(audit_rows, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
