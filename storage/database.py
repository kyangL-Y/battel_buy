from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
from sqlalchemy import bindparam, create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine, URL

from utils.config_loader import BASE_DIR, load_database_config


DEFAULT_DB_PATH = BASE_DIR / "data" / "price_tracker.db"
TABLE_ORDER = [
    "products",
    "price_records",
    "failed_crawl_records",
    "local_compare_records",
    "suppliers",
    "supplier_price_records",
]

PRODUCT_COLUMNS = {
    "category": "TEXT",
    "brand": "TEXT",
    "product_series": "TEXT",
    "spec_text": "TEXT",
    "compare_key": "TEXT",
    "province": "TEXT",
    "city": "TEXT",
    "market_name": "TEXT",
    "region_label": "TEXT",
}

PRICE_RECORD_COLUMNS = {
    "unit_name": "TEXT",
    "unit_value": "REAL",
    "unit_price": "REAL",
}

FAILED_CRAWL_COLUMNS = {
    "group_name": "TEXT",
    "product_name": "TEXT",
    "source_url": "TEXT",
    "site_name": "TEXT",
    "fetch_mode": "TEXT",
    "status_code": "INTEGER",
    "error": "TEXT",
    "suggestion": "TEXT",
    "fallback_used": "INTEGER",
    "raw_payload": "TEXT",
}

LOCAL_COMPARE_COLUMNS = {
    "batch_name": "TEXT",
    "match_status": "TEXT",
    "matched_by": "TEXT",
    "price_relation": "TEXT",
    "source_row_no": "TEXT",
    "group_name": "TEXT",
    "product_name": "TEXT",
    "category": "TEXT",
    "brand": "TEXT",
    "product_series": "TEXT",
    "spec_text": "TEXT",
    "site_name": "TEXT",
    "local_price": "REAL",
    "box_price": "REAL",
    "tax_price": "REAL",
    "remarks": "TEXT",
    "market_category": "TEXT",
    "channel": "TEXT",
    "matched_group_name": "TEXT",
    "matched_product_name": "TEXT",
    "matched_site_name": "TEXT",
    "current_price": "REAL",
    "price_diff": "REAL",
    "price_diff_rate": "REAL",
    "promotion_text": "TEXT",
    "raw_payload": "TEXT",
}

SUPPLIER_COLUMNS = {
    "contact_name": "TEXT",
    "contact_phone": "TEXT",
    "market_scope": "TEXT",
    "market_category": "TEXT",
    "channel": "TEXT",
    "notes": "TEXT",
    "is_active": "INTEGER",
    "updated_at": "TEXT",
}

SUPPLIER_PRICE_COLUMNS = {
    "price_identity_label": "TEXT",
    "product_name": "TEXT",
    "category": "TEXT",
    "spec_text": "TEXT",
    "market_category": "TEXT",
    "channel": "TEXT",
    "quote_price": "REAL",
    "quote_unit": "TEXT",
    "box_price": "REAL",
    "tax_price": "REAL",
    "inventory_status": "TEXT",
    "remarks": "TEXT",
    "quoted_by": "TEXT",
    "updated_at": "TEXT",
}

MYSQL_TYPE_MAP = {
    "TEXT": "TEXT",
    "REAL": "DOUBLE",
    "INTEGER": "INT",
}


def _normalize_sqlite_path(path: str | Path) -> Path:
    sqlite_path = Path(path)
    if not sqlite_path.is_absolute():
        sqlite_path = BASE_DIR / sqlite_path
    return sqlite_path.resolve()


class Database:
    def __init__(
        self,
        db_path: str | Path | None = None,
        timeout_seconds: float = 30.0,
        busy_timeout_ms: int = 30000,
        database_config: dict[str, Any] | None = None,
    ) -> None:
        self.timeout_seconds = float(timeout_seconds)
        self.busy_timeout_ms = int(busy_timeout_ms)
        self.database_config = database_config or load_database_config()
        self.backend = "sqlite"
        self.db_path: Path | None = None
        self.mysql_config: dict[str, Any] = {}
        self._connection_state = threading.local()

        if db_path is not None:
            self.db_path = _normalize_sqlite_path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.backend = str(self.database_config.get("backend") or "sqlite").strip().lower()
            if self.backend == "mysql":
                self.mysql_config = dict(self.database_config.get("mysql", {}))
            else:
                sqlite_path = self.database_config.get("sqlite_path") or DEFAULT_DB_PATH
                self.db_path = _normalize_sqlite_path(sqlite_path)
                self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = self._build_engine()

    @property
    def database_label(self) -> str:
        if self.backend == "mysql":
            host = self.mysql_config.get("host") or "localhost"
            port = self.mysql_config.get("port") or 3306
            database = self.mysql_config.get("database") or ""
            return f"mysql://{host}:{port}/{database}"
        return str(self.db_path or DEFAULT_DB_PATH)

    def _build_engine(self) -> Engine:
        if self.backend == "mysql":
            return create_engine(
                URL.create(
                    "mysql+pymysql",
                    username=str(self.mysql_config.get("user") or ""),
                    password=str(self.mysql_config.get("password") or ""),
                    host=str(self.mysql_config.get("host") or ""),
                    port=int(self.mysql_config.get("port") or 3306),
                    database=str(self.mysql_config.get("database") or ""),
                    query={"charset": str(self.mysql_config.get("charset") or "utf8mb4")},
                ),
                pool_pre_ping=True,
                pool_recycle=3600,
                future=True,
            )
        return create_engine(
            f"sqlite:///{(self.db_path or DEFAULT_DB_PATH).as_posix()}",
            connect_args={"timeout": self.timeout_seconds, "check_same_thread": False},
            future=True,
        )

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        active_conn = getattr(self._connection_state, "active_conn", None)
        if active_conn is not None:
            yield active_conn
            return

        with self.engine.begin() as conn:
            if self.backend == "sqlite":
                conn.exec_driver_sql("PRAGMA journal_mode=WAL")
                conn.exec_driver_sql(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
                conn.exec_driver_sql("PRAGMA synchronous=NORMAL")
                conn.exec_driver_sql("PRAGMA foreign_keys=ON")
            else:
                conn.exec_driver_sql(
                    "SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'"
                )
            self._connection_state.active_conn = conn
            try:
                yield conn
            finally:
                self._connection_state.active_conn = None

    def _read_sql(self, query: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
        with self.connect() as conn:
            return pd.read_sql_query(text(query), conn, params=params or {})

    def _column_type(self, value: str) -> str:
        if self.backend == "mysql":
            return MYSQL_TYPE_MAP.get(value, value)
        return value

    def init_db(self) -> None:
        with self.connect() as conn:
            if self.backend == "mysql":
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS products (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        product_key VARCHAR(255) NOT NULL UNIQUE,
                        group_name TEXT,
                        product_name TEXT,
                        source_url TEXT NOT NULL,
                        site_name TEXT NOT NULL,
                        created_at VARCHAR(64) NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS price_records (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        product_id BIGINT NOT NULL,
                        captured_at VARCHAR(64) NOT NULL,
                        current_price DOUBLE NULL,
                        original_price DOUBLE NULL,
                        promotion_text TEXT,
                        currency VARCHAR(16) DEFAULT 'CNY',
                        availability TEXT,
                        raw_payload LONGTEXT,
                        CONSTRAINT fk_price_records_product FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS failed_crawl_records (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        product_key VARCHAR(255),
                        captured_at VARCHAR(64) NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS local_compare_records (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        captured_at VARCHAR(64) NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS suppliers (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        supplier_name VARCHAR(255) NOT NULL UNIQUE,
                        created_at VARCHAR(64) NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS supplier_price_records (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        supplier_id BIGINT NOT NULL,
                        price_identity_key VARCHAR(255) NOT NULL,
                        quoted_at VARCHAR(64) NOT NULL,
                        CONSTRAINT fk_supplier_price_records_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )
            else:
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_key TEXT UNIQUE NOT NULL,
                        group_name TEXT,
                        product_name TEXT,
                        source_url TEXT NOT NULL,
                        site_name TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS price_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        captured_at TEXT NOT NULL,
                        current_price REAL,
                        original_price REAL,
                        promotion_text TEXT,
                        currency TEXT DEFAULT 'CNY',
                        availability TEXT,
                        raw_payload TEXT,
                        FOREIGN KEY(product_id) REFERENCES products(id)
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS failed_crawl_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_key TEXT,
                        captured_at TEXT NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS local_compare_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        captured_at TEXT NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS suppliers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        supplier_name TEXT NOT NULL UNIQUE,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS supplier_price_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        supplier_id INTEGER NOT NULL,
                        price_identity_key TEXT NOT NULL,
                        quoted_at TEXT NOT NULL,
                        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )

            self._ensure_columns(conn, "products", PRODUCT_COLUMNS)
            self._ensure_columns(conn, "price_records", PRICE_RECORD_COLUMNS)
            self._ensure_columns(conn, "failed_crawl_records", FAILED_CRAWL_COLUMNS)
            self._ensure_columns(conn, "local_compare_records", LOCAL_COMPARE_COLUMNS)
            self._ensure_columns(conn, "suppliers", SUPPLIER_COLUMNS)
            self._ensure_columns(conn, "supplier_price_records", SUPPLIER_PRICE_COLUMNS)
            self._ensure_indexes(conn)

    def _ensure_columns(self, conn: Connection, table_name: str, columns: dict[str, str]) -> None:
        existing_columns = {column["name"] for column in inspect(conn).get_columns(table_name)}
        for column_name, column_type in columns.items():
            if column_name not in existing_columns:
                conn.exec_driver_sql(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {self._column_type(column_type)}"
                )

    def _ensure_indexes(self, conn: Connection) -> None:
        inspector = inspect(conn)
        existing = {
            table: {item["name"] for item in inspector.get_indexes(table)}
            for table in ["price_records", "products", "suppliers", "supplier_price_records"]
        }
        if "idx_price_records_product_captured_id" not in existing["price_records"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_price_records_product_captured_id
                ON price_records (product_id, captured_at DESC, id DESC)
                """
            )
        if "idx_price_records_captured_at" not in existing["price_records"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_price_records_captured_at
                ON price_records (captured_at DESC)
                """
            )
        if "idx_products_site_group" not in existing["products"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_products_site_group
                ON products (site_name(255), group_name(255))
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_products_site_group
                ON products (site_name, group_name)
                """
            )
        if "idx_suppliers_name" not in existing["suppliers"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_suppliers_name
                ON suppliers (supplier_name(255))
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_suppliers_name
                ON suppliers (supplier_name)
                """
            )
        if "idx_supplier_price_records_identity_quoted_id" not in existing["supplier_price_records"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_supplier_price_records_identity_quoted_id
                ON supplier_price_records (price_identity_key(255), quoted_at, id)
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_supplier_price_records_identity_quoted_id
                ON supplier_price_records (price_identity_key, quoted_at, id)
                """
            )
        if "idx_supplier_price_records_supplier_identity" not in existing["supplier_price_records"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_supplier_price_records_supplier_identity
                ON supplier_price_records (supplier_id, price_identity_key(255))
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_supplier_price_records_supplier_identity
                ON supplier_price_records (supplier_id, price_identity_key)
                """
            )

    def reset_all_data(self) -> None:
        with self.connect() as conn:
            if self.backend == "mysql":
                conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS=0")
                for table_name in reversed(TABLE_ORDER):
                    conn.exec_driver_sql(f"TRUNCATE TABLE {table_name}")
                conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS=1")
            else:
                for table_name in reversed(TABLE_ORDER):
                    conn.exec_driver_sql(f"DELETE FROM {table_name}")
                conn.exec_driver_sql("DELETE FROM sqlite_sequence")

    def get_table_records(self, table_name: str) -> list[dict[str, Any]]:
        dataframe = self._read_sql(f"SELECT * FROM {table_name}")
        if dataframe.empty:
            return []
        normalized = dataframe.where(pd.notna(dataframe), None)
        return normalized.to_dict(orient="records")

    def bulk_insert_records(self, table_name: str, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        columns = list(records[0].keys())
        column_sql = ", ".join(columns)
        value_sql = ", ".join(f":{column}" for column in columns)
        statement = text(f"INSERT INTO {table_name} ({column_sql}) VALUES ({value_sql})")
        normalized_records = [
            {
                column: (None if pd.isna(value) else value)
                for column, value in record.items()
            }
            for record in records
        ]
        with self.connect() as conn:
            batch_size = 1000
            for start in range(0, len(normalized_records), batch_size):
                conn.execute(statement, normalized_records[start : start + batch_size])
        return len(normalized_records)

    def upsert_product(
        self,
        product_key: str,
        group_name: str | None,
        product_name: str | None,
        source_url: str,
        site_name: str,
        category: str | None = None,
        brand: str | None = None,
        product_series: str | None = None,
        spec_text: str | None = None,
        compare_key: str | None = None,
        province: str | None = None,
        city: str | None = None,
        market_name: str | None = None,
        region_label: str | None = None,
    ) -> int:
        created_at = datetime.utcnow().isoformat()
        with self.connect() as conn:
            existing = conn.execute(
                text("SELECT id FROM products WHERE product_key = :product_key"),
                {"product_key": product_key},
            ).mappings().first()
            if existing:
                conn.execute(
                    text(
                        """
                        UPDATE products
                        SET group_name = :group_name,
                            product_name = :product_name,
                            source_url = :source_url,
                            site_name = :site_name,
                            category = :category,
                            brand = :brand,
                            product_series = :product_series,
                            spec_text = :spec_text,
                            compare_key = :compare_key,
                            province = :province,
                            city = :city,
                            market_name = :market_name,
                            region_label = :region_label
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": int(existing["id"]),
                        "group_name": group_name,
                        "product_name": product_name,
                        "source_url": source_url,
                        "site_name": site_name,
                        "category": category,
                        "brand": brand,
                        "product_series": product_series,
                        "spec_text": spec_text,
                        "compare_key": compare_key,
                        "province": province,
                        "city": city,
                        "market_name": market_name,
                        "region_label": region_label,
                    },
                )
                return int(existing["id"])

            result = conn.execute(
                text(
                    """
                    INSERT INTO products (
                        product_key, group_name, product_name, source_url, site_name, created_at,
                        category, brand, product_series, spec_text, compare_key,
                        province, city, market_name, region_label
                    )
                    VALUES (
                        :product_key, :group_name, :product_name, :source_url, :site_name, :created_at,
                        :category, :brand, :product_series, :spec_text, :compare_key,
                        :province, :city, :market_name, :region_label
                    )
                    """
                ),
                {
                    "product_key": product_key,
                    "group_name": group_name,
                    "product_name": product_name,
                    "source_url": source_url,
                    "site_name": site_name,
                    "created_at": created_at,
                    "category": category,
                    "brand": brand,
                    "product_series": product_series,
                    "spec_text": spec_text,
                    "compare_key": compare_key,
                    "province": province,
                    "city": city,
                    "market_name": market_name,
                    "region_label": region_label,
                },
            )
            return int(result.lastrowid)

    def insert_price_record(
        self,
        product_id: int,
        captured_at: str,
        current_price: float | None,
        original_price: float | None,
        promotion_text: str | None,
        currency: str,
        availability: str | None,
        raw_payload: dict,
        unit_name: str | None = None,
        unit_value: float | None = None,
        unit_price: float | None = None,
    ) -> int:
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO price_records (
                        product_id, captured_at, current_price, original_price,
                        promotion_text, currency, availability, raw_payload,
                        unit_name, unit_value, unit_price
                    )
                    VALUES (
                        :product_id, :captured_at, :current_price, :original_price,
                        :promotion_text, :currency, :availability, :raw_payload,
                        :unit_name, :unit_value, :unit_price
                    )
                    """
                ),
                {
                    "product_id": product_id,
                    "captured_at": captured_at,
                    "current_price": current_price,
                    "original_price": original_price,
                    "promotion_text": promotion_text,
                    "currency": currency,
                    "availability": availability,
                    "raw_payload": json.dumps(raw_payload, ensure_ascii=False),
                    "unit_name": unit_name,
                    "unit_value": unit_value,
                    "unit_price": unit_price,
                },
            )
            return int(result.lastrowid)

    def insert_failed_crawl_record(
        self,
        product_key: str | None,
        captured_at: str,
        group_name: str | None,
        product_name: str | None,
        source_url: str,
        site_name: str | None,
        fetch_mode: str | None,
        status_code: int | None,
        error: str | None,
        suggestion: str | None,
        fallback_used: bool,
        raw_payload: dict,
    ) -> int:
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO failed_crawl_records (
                        product_key, captured_at, group_name, product_name, source_url,
                        site_name, fetch_mode, status_code, error, suggestion,
                        fallback_used, raw_payload
                    )
                    VALUES (
                        :product_key, :captured_at, :group_name, :product_name, :source_url,
                        :site_name, :fetch_mode, :status_code, :error, :suggestion,
                        :fallback_used, :raw_payload
                    )
                    """
                ),
                {
                    "product_key": product_key,
                    "captured_at": captured_at,
                    "group_name": group_name,
                    "product_name": product_name,
                    "source_url": source_url,
                    "site_name": site_name,
                    "fetch_mode": fetch_mode,
                    "status_code": status_code,
                    "error": error,
                    "suggestion": suggestion,
                    "fallback_used": 1 if fallback_used else 0,
                    "raw_payload": json.dumps(raw_payload, ensure_ascii=False),
                },
            )
            return int(result.lastrowid)

    def get_all_products(self) -> pd.DataFrame:
        return self._read_sql("SELECT * FROM products ORDER BY group_name, brand, site_name")

    def delete_product(self, product_id: int) -> None:
        with self.connect() as conn:
            conn.execute(text("DELETE FROM price_records WHERE product_id = :product_id"), {"product_id": product_id})
            conn.execute(text("DELETE FROM products WHERE id = :product_id"), {"product_id": product_id})

    def get_price_history(self) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT
                p.id AS product_id,
                p.product_key,
                p.group_name,
                p.product_name,
                p.category,
                p.brand,
                p.product_series,
                p.spec_text,
                p.compare_key,
                p.province,
                p.city,
                p.market_name,
                p.region_label,
                p.source_url,
                p.site_name,
                r.id AS record_id,
                r.captured_at,
                r.current_price,
                r.original_price,
                r.promotion_text,
                r.currency,
                r.unit_name,
                r.unit_value,
                r.unit_price,
                CASE
                    WHEN r.unit_name = 'g' AND r.unit_value IS NOT NULL AND r.unit_value > 0 AND r.current_price IS NOT NULL
                    THEN ROUND(r.current_price / r.unit_value * 500, 4)
                    ELSE NULL
                END AS jin_price
            FROM price_records r
            JOIN products p ON p.id = r.product_id
            ORDER BY r.captured_at ASC
            """
        )

    def get_trend_history(self) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT
                p.id AS product_id,
                p.product_key,
                p.group_name,
                p.product_name,
                p.category,
                p.brand,
                p.product_series,
                p.spec_text,
                p.compare_key,
                p.province,
                p.city,
                p.market_name,
                p.region_label,
                p.source_url,
                p.site_name,
                r.captured_at,
                r.current_price
            FROM price_records r
            JOIN products p ON p.id = r.product_id
            """
        )

    def get_trend_history_for_product_keys(self, product_keys: list[str]) -> pd.DataFrame:
        normalized_keys = [str(item).strip() for item in product_keys if str(item).strip()]
        if not normalized_keys:
            return pd.DataFrame()

        statement = text(
            """
            SELECT
                p.id AS product_id,
                p.product_key,
                p.group_name,
                p.product_name,
                p.category,
                p.brand,
                p.product_series,
                p.spec_text,
                p.compare_key,
                p.province,
                p.city,
                p.market_name,
                p.region_label,
                p.source_url,
                p.site_name,
                r.captured_at,
                r.current_price
            FROM price_records r
            JOIN products p ON p.id = r.product_id
            WHERE p.product_key IN :product_keys
            ORDER BY r.captured_at ASC
            """
        ).bindparams(bindparam("product_keys", expanding=True))
        with self.connect() as conn:
            return pd.read_sql_query(statement, conn, params={"product_keys": normalized_keys})

    def get_latest_records(self) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT
                p.group_name,
                p.product_key,
                p.product_name,
                p.category,
                p.brand,
                p.product_series,
                p.spec_text,
                p.compare_key,
                p.province,
                p.city,
                p.market_name,
                p.region_label,
                p.site_name,
                p.source_url,
                r.current_price,
                r.original_price,
                r.promotion_text,
                r.currency,
                r.unit_name,
                r.unit_value,
                r.unit_price,
                CASE
                    WHEN r.unit_name = 'g' AND r.unit_value IS NOT NULL AND r.unit_value > 0 AND r.current_price IS NOT NULL
                    THEN ROUND(r.current_price / r.unit_value * 500, 4)
                    ELSE NULL
                END AS jin_price,
                r.captured_at
            FROM products p
            JOIN price_records r
                ON r.id = (
                    SELECT pr2.id
                    FROM price_records pr2
                    WHERE pr2.product_id = p.id
                    ORDER BY pr2.captured_at DESC, pr2.id DESC
                    LIMIT 1
                )
            ORDER BY r.captured_at DESC
            """
        )

    def insert_local_compare_records(
        self,
        rows: list[dict],
        captured_at: str,
        batch_name: str | None = None,
    ) -> int:
        if not rows:
            return 0

        payloads = [
            {
                "captured_at": captured_at,
                "batch_name": batch_name,
                "match_status": row.get("match_status"),
                "matched_by": row.get("matched_by"),
                "price_relation": row.get("price_relation"),
                "source_row_no": row.get("source_row_no"),
                "group_name": row.get("group_name"),
                "product_name": row.get("product_name"),
                "category": row.get("category"),
                "brand": row.get("brand"),
                "product_series": row.get("product_series"),
                "spec_text": row.get("spec_text"),
                "site_name": row.get("site_name"),
                "local_price": row.get("local_price"),
                "box_price": row.get("box_price"),
                "tax_price": row.get("tax_price"),
                "remarks": row.get("remarks"),
                "market_category": row.get("market_category"),
                "channel": row.get("channel"),
                "matched_group_name": row.get("matched_group_name"),
                "matched_product_name": row.get("matched_product_name"),
                "matched_site_name": row.get("matched_site_name"),
                "current_price": row.get("current_price"),
                "price_diff": row.get("price_diff"),
                "price_diff_rate": row.get("price_diff_rate"),
                "promotion_text": row.get("promotion_text"),
                "raw_payload": json.dumps(row, ensure_ascii=False),
            }
            for row in rows
        ]

        with self.connect() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO local_compare_records (
                        captured_at, batch_name, match_status, matched_by, price_relation,
                        source_row_no, group_name, product_name, category, brand, product_series,
                        spec_text, site_name, local_price, box_price, tax_price, remarks, market_category, channel, matched_group_name,
                        matched_product_name, matched_site_name, current_price,
                        price_diff, price_diff_rate, promotion_text, raw_payload
                    )
                    VALUES (
                        :captured_at, :batch_name, :match_status, :matched_by, :price_relation,
                        :source_row_no, :group_name, :product_name, :category, :brand, :product_series,
                        :spec_text, :site_name, :local_price, :box_price, :tax_price, :remarks, :market_category, :channel, :matched_group_name,
                        :matched_product_name, :matched_site_name, :current_price,
                        :price_diff, :price_diff_rate, :promotion_text, :raw_payload
                    )
                    """
                ),
                payloads,
            )
        return len(payloads)

    def get_local_compare_records(self, limit: int | None = 200) -> pd.DataFrame:
        query = """
        SELECT
            batch_name,
            match_status,
            matched_by,
            price_relation,
            source_row_no,
            group_name,
            product_name,
            category,
            brand,
            product_series,
            spec_text,
            site_name,
            local_price,
            box_price,
            tax_price,
            remarks,
            market_category,
            channel,
            matched_group_name,
            matched_product_name,
            matched_site_name,
            current_price,
            price_diff,
            price_diff_rate,
            promotion_text,
            raw_payload,
            captured_at
        FROM local_compare_records
        ORDER BY captured_at DESC, id DESC
        """
        if limit is not None and limit > 0:
            query += " LIMIT :limit"
            return self._read_sql(query, {"limit": int(limit)})
        return self._read_sql(query)

    def delete_local_compare_batch(self, batch_name: str) -> int:
        with self.connect() as conn:
            result = conn.execute(
                text("DELETE FROM local_compare_records WHERE batch_name = :batch_name"),
                {"batch_name": batch_name},
            )
            return int(result.rowcount or 0)

    def upsert_supplier(
        self,
        supplier_name: str,
        contact_name: str | None = None,
        contact_phone: str | None = None,
        market_scope: str | None = None,
        market_category: str | None = None,
        channel: str | None = None,
        notes: str | None = None,
        is_active: bool = True,
        supplier_id: int | None = None,
    ) -> int:
        normalized_name = str(supplier_name or "").strip()
        if not normalized_name:
            raise ValueError("supplier_name is required")

        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            existing = None
            if supplier_id is not None:
                existing = conn.execute(
                    text("SELECT * FROM suppliers WHERE id = :supplier_id"),
                    {"supplier_id": int(supplier_id)},
                ).mappings().first()
            if existing is None:
                existing = conn.execute(
                    text("SELECT * FROM suppliers WHERE supplier_name = :supplier_name"),
                    {"supplier_name": normalized_name},
                ).mappings().first()

            if existing:
                supplier_row = dict(existing)
                conn.execute(
                    text(
                        """
                        UPDATE suppliers
                        SET supplier_name = :supplier_name,
                            contact_name = :contact_name,
                            contact_phone = :contact_phone,
                            market_scope = :market_scope,
                            market_category = :market_category,
                            channel = :channel,
                            notes = :notes,
                            is_active = :is_active,
                            updated_at = :updated_at
                        WHERE id = :supplier_id
                        """
                    ),
                    {
                        "supplier_id": int(supplier_row["id"]),
                        "supplier_name": normalized_name,
                        "contact_name": contact_name if contact_name is not None else supplier_row.get("contact_name"),
                        "contact_phone": contact_phone if contact_phone is not None else supplier_row.get("contact_phone"),
                        "market_scope": market_scope if market_scope is not None else supplier_row.get("market_scope"),
                        "market_category": market_category if market_category is not None else supplier_row.get("market_category"),
                        "channel": channel if channel is not None else supplier_row.get("channel"),
                        "notes": notes if notes is not None else supplier_row.get("notes"),
                        "is_active": 1 if is_active else 0,
                        "updated_at": now,
                    },
                )
                return int(supplier_row["id"])

            result = conn.execute(
                text(
                    """
                    INSERT INTO suppliers (
                        supplier_name, contact_name, contact_phone, market_scope,
                        market_category, channel, notes, is_active, created_at, updated_at
                    )
                    VALUES (
                        :supplier_name, :contact_name, :contact_phone, :market_scope,
                        :market_category, :channel, :notes, :is_active, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "supplier_name": normalized_name,
                    "contact_name": contact_name,
                    "contact_phone": contact_phone,
                    "market_scope": market_scope,
                    "market_category": market_category,
                    "channel": channel,
                    "notes": notes,
                    "is_active": 1 if is_active else 0,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            return int(result.lastrowid)

    def get_suppliers(self, active_only: bool = False) -> pd.DataFrame:
        query = """
        SELECT
            s.id,
            s.supplier_name,
            s.contact_name,
            s.contact_phone,
            s.market_scope,
            s.market_category,
            s.channel,
            s.notes,
            s.is_active,
            s.created_at,
            s.updated_at,
            COUNT(r.id) AS quote_count,
            MAX(r.quoted_at) AS latest_quoted_at
        FROM suppliers s
        LEFT JOIN supplier_price_records r ON r.supplier_id = s.id
        """
        params: dict[str, Any] = {}
        if active_only:
            query += " WHERE COALESCE(s.is_active, 0) = 1"
        query += """
        GROUP BY
            s.id, s.supplier_name, s.contact_name, s.contact_phone, s.market_scope,
            s.market_category, s.channel, s.notes, s.is_active, s.created_at, s.updated_at
        ORDER BY COALESCE(s.is_active, 0) DESC, s.supplier_name ASC
        """
        return self._read_sql(query, params)

    def get_supplier_category_summary(self) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT
                COALESCE(NULLIF(TRIM(s.market_category), ''), '未分类') AS market_category,
                COUNT(*) AS supplier_count,
                SUM(CASE WHEN COALESCE(s.is_active, 0) = 1 THEN 1 ELSE 0 END) AS active_supplier_count,
                COUNT(r.id) AS quote_count,
                MAX(r.quoted_at) AS latest_quoted_at
            FROM suppliers s
            LEFT JOIN supplier_price_records r ON r.supplier_id = s.id
            GROUP BY COALESCE(NULLIF(TRIM(s.market_category), ''), '未分类')
            ORDER BY active_supplier_count DESC, quote_count DESC, market_category ASC
            """
        )

    def insert_supplier_price_record(
        self,
        supplier_id: int,
        price_identity_key: str,
        quoted_at: str,
        price_identity_label: str | None = None,
        product_name: str | None = None,
        category: str | None = None,
        spec_text: str | None = None,
        market_category: str | None = None,
        channel: str | None = None,
        quote_price: float | None = None,
        quote_unit: str | None = None,
        box_price: float | None = None,
        tax_price: float | None = None,
        inventory_status: str | None = None,
        remarks: str | None = None,
        quoted_by: str | None = None,
    ) -> int:
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO supplier_price_records (
                        supplier_id, price_identity_key, quoted_at, price_identity_label,
                        product_name, category, spec_text, market_category, channel,
                        quote_price, quote_unit, box_price, tax_price, inventory_status,
                        remarks, quoted_by, updated_at
                    )
                    VALUES (
                        :supplier_id, :price_identity_key, :quoted_at, :price_identity_label,
                        :product_name, :category, :spec_text, :market_category, :channel,
                        :quote_price, :quote_unit, :box_price, :tax_price, :inventory_status,
                        :remarks, :quoted_by, :updated_at
                    )
                    """
                ),
                {
                    "supplier_id": int(supplier_id),
                    "price_identity_key": str(price_identity_key or "").strip(),
                    "quoted_at": quoted_at,
                    "price_identity_label": price_identity_label,
                    "product_name": product_name,
                    "category": category,
                    "spec_text": spec_text,
                    "market_category": market_category,
                    "channel": channel,
                    "quote_price": quote_price,
                    "quote_unit": quote_unit,
                    "box_price": box_price,
                    "tax_price": tax_price,
                    "inventory_status": inventory_status,
                    "remarks": remarks,
                    "quoted_by": quoted_by,
                    "updated_at": now,
                },
            )
            return int(result.lastrowid)

    def get_supplier_price_record(self, record_id: int) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT
                r.id,
                r.supplier_id,
                s.supplier_name,
                s.contact_name,
                s.contact_phone,
                s.market_scope,
                s.market_category AS supplier_market_category,
                s.channel AS supplier_channel,
                s.notes AS supplier_notes,
                s.is_active,
                r.price_identity_key,
                r.price_identity_label,
                r.product_name,
                r.category,
                r.spec_text,
                r.market_category,
                r.channel,
                r.quote_price,
                r.quote_unit,
                r.box_price,
                r.tax_price,
                r.inventory_status,
                r.remarks,
                r.quoted_by,
                r.quoted_at,
                r.updated_at
            FROM supplier_price_records r
            JOIN suppliers s ON s.id = r.supplier_id
            WHERE r.id = :record_id
            """,
            {"record_id": int(record_id)},
        )

    def get_latest_supplier_quotes(self, price_identity_key: str) -> pd.DataFrame:
        normalized_key = str(price_identity_key or "").strip()
        if not normalized_key:
            return pd.DataFrame()

        return self._read_sql(
            """
            SELECT
                s.id AS supplier_id,
                s.supplier_name,
                s.contact_name,
                s.contact_phone,
                s.market_scope,
                s.market_category AS supplier_market_category,
                s.channel AS supplier_channel,
                s.notes AS supplier_notes,
                s.is_active,
                r.id AS record_id,
                r.price_identity_key,
                r.price_identity_label,
                r.product_name,
                r.category,
                r.spec_text,
                r.market_category,
                r.channel,
                r.quote_price,
                r.quote_unit,
                r.box_price,
                r.tax_price,
                r.inventory_status,
                r.remarks,
                r.quoted_by,
                r.quoted_at,
                r.updated_at
            FROM suppliers s
            JOIN supplier_price_records r
                ON r.id = (
                    SELECT sr2.id
                    FROM supplier_price_records sr2
                    WHERE sr2.supplier_id = s.id
                      AND sr2.price_identity_key = :price_identity_key
                    ORDER BY sr2.quoted_at DESC, sr2.id DESC
                    LIMIT 1
                )
            WHERE COALESCE(s.is_active, 0) = 1
            ORDER BY
                CASE WHEN r.quote_price IS NULL THEN 1 ELSE 0 END,
                r.quote_price ASC,
                r.quoted_at DESC,
                s.supplier_name ASC
            """,
            {"price_identity_key": normalized_key},
        )

    def get_supplier_quote_records(self, supplier_id: int, limit: int | None = 20) -> pd.DataFrame:
        query = """
        SELECT
            r.id,
            r.supplier_id,
            s.supplier_name,
            s.contact_name,
            s.contact_phone,
            s.market_scope,
            s.market_category AS supplier_market_category,
            s.channel AS supplier_channel,
            r.price_identity_key,
            r.price_identity_label,
            r.product_name,
            r.category,
            r.spec_text,
            r.market_category,
            r.channel,
            r.quote_price,
            r.quote_unit,
            r.box_price,
            r.tax_price,
            r.inventory_status,
            r.remarks,
            r.quoted_by,
            r.quoted_at,
            r.updated_at
        FROM supplier_price_records r
        JOIN suppliers s ON s.id = r.supplier_id
        WHERE r.supplier_id = :supplier_id
        ORDER BY r.quoted_at DESC, r.id DESC
        """
        params: dict[str, Any] = {"supplier_id": int(supplier_id)}
        if limit is not None and limit > 0:
            query += " LIMIT :limit"
            params["limit"] = int(limit)
        return self._read_sql(query, params)

    def get_recent_supplier_quotes(self, limit: int | None = 20) -> pd.DataFrame:
        query = """
        SELECT
            r.id,
            r.supplier_id,
            s.supplier_name,
            s.contact_name,
            s.contact_phone,
            s.market_scope,
            s.market_category AS supplier_market_category,
            s.channel AS supplier_channel,
            r.price_identity_key,
            r.price_identity_label,
            r.product_name,
            r.category,
            r.spec_text,
            r.market_category,
            r.channel,
            r.quote_price,
            r.quote_unit,
            r.box_price,
            r.tax_price,
            r.inventory_status,
            r.remarks,
            r.quoted_by,
            r.quoted_at,
            r.updated_at
        FROM supplier_price_records r
        JOIN suppliers s ON s.id = r.supplier_id
        ORDER BY r.quoted_at DESC, r.id DESC
        """
        if limit is not None and limit > 0:
            query += " LIMIT :limit"
            return self._read_sql(query, {"limit": int(limit)})
        return self._read_sql(query)

    def get_failed_crawl_records(self, limit: int | None = None) -> pd.DataFrame:
        query = """
        SELECT
            product_key,
            group_name,
            product_name,
            source_url,
            site_name,
            fetch_mode,
            status_code,
            error,
            suggestion,
            fallback_used,
            raw_payload,
            captured_at
        FROM failed_crawl_records
        ORDER BY captured_at DESC
        """
        if limit is not None and limit > 0:
            query += " LIMIT :limit"
            return self._read_sql(query, {"limit": int(limit)})
        return self._read_sql(query)

    def get_price_record_count(self) -> int:
        with self.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) AS total FROM price_records")).mappings().first()
            if not result:
                return 0
            return int(result.get("total") or 0)

    def get_source_coverage_summary(self) -> pd.DataFrame:
        item_key_expr = (
            "CONCAT_WS('|', COALESCE(group_name, ''), COALESCE(product_name, ''), COALESCE(spec_text, ''))"
            if self.backend == "mysql"
            else "COALESCE(group_name, '') || '|' || COALESCE(product_name, '') || '|' || COALESCE(spec_text, '')"
        )
        source_item_expr = (
            "CONCAT_WS('|', COALESCE(site_name, ''), COALESCE(group_name, ''), COALESCE(product_name, ''), COALESCE(spec_text, ''))"
            if self.backend == "mysql"
            else "COALESCE(site_name, '') || '|' || COALESCE(group_name, '') || '|' || COALESCE(product_name, '') || '|' || COALESCE(spec_text, '')"
        )
        query = f"""
        SELECT
            src.source_url,
            COALESCE(sp.product_key_count, 0) AS product_key_count,
            COALESCE(sp.comparable_item_count, 0) AS comparable_item_count,
            COALESCE(sp.source_item_count, 0) AS source_item_count,
            COALESCE(sp.market_count, 0) AS market_count,
            COALESCE(sr.price_record_count, 0) AS price_record_count,
            sr.latest_capture,
            COALESCE(sf.failed_count, 0) AS failed_count,
            sf.last_failure
        FROM (
            SELECT source_url FROM products
            UNION
            SELECT source_url FROM failed_crawl_records
        ) src
        LEFT JOIN (
            SELECT
                source_url,
                COUNT(DISTINCT product_key) AS product_key_count,
                COUNT(DISTINCT {item_key_expr}) AS comparable_item_count,
                COUNT(DISTINCT {source_item_expr}) AS source_item_count,
                COUNT(DISTINCT site_name) AS market_count
            FROM products
            GROUP BY source_url
        ) sp ON sp.source_url = src.source_url
        LEFT JOIN (
            SELECT
                p.source_url,
                COUNT(*) AS price_record_count,
                MAX(r.captured_at) AS latest_capture
            FROM products p
            JOIN price_records r ON r.product_id = p.id
            GROUP BY p.source_url
        ) sr ON sr.source_url = src.source_url
        LEFT JOIN (
            SELECT
                source_url,
                COUNT(*) AS failed_count,
                MAX(captured_at) AS last_failure
            FROM failed_crawl_records
            GROUP BY source_url
        ) sf ON sf.source_url = src.source_url
        ORDER BY comparable_item_count DESC, product_key_count DESC
        """
        return self._read_sql(query)

    def deduplicate_source_products(self, source_url: str, base_product_key: str | None = None) -> dict[str, int]:
        with self.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id, product_key, group_name, product_name, spec_text, site_name, market_name
                    FROM products
                    WHERE source_url = :source_url
                    ORDER BY id ASC
                    """
                ),
                {"source_url": source_url},
            ).mappings().all()

            groups: dict[str, list[dict[str, Any]]] = {}
            for row in rows:
                normalized_key = self._build_dedup_product_key(
                    base_product_key or source_url,
                    row.get("group_name"),
                    row.get("product_name"),
                    row.get("spec_text"),
                    row.get("site_name"),
                    row.get("market_name"),
                )
                groups.setdefault(normalized_key, []).append(dict(row))

            merged_products = 0
            moved_records = 0
            touched_groups = 0

            for normalized_key, group_rows in groups.items():
                survivor = group_rows[0]
                duplicate_rows = group_rows[1:]

                conn.execute(
                    text("UPDATE products SET product_key = :product_key WHERE id = :id"),
                    {"product_key": normalized_key, "id": survivor["id"]},
                )

                if not duplicate_rows:
                    continue

                touched_groups += 1
                duplicate_ids = [int(row["id"]) for row in duplicate_rows]
                duplicate_params = {f"id{index}": value for index, value in enumerate(duplicate_ids)}
                duplicate_clause = ", ".join(f":id{index}" for index in range(len(duplicate_ids)))

                move_result = conn.execute(
                    text(
                        f"UPDATE price_records SET product_id = :survivor_id WHERE product_id IN ({duplicate_clause})"
                    ),
                    {"survivor_id": survivor["id"], **duplicate_params},
                )
                conn.execute(
                    text(f"DELETE FROM products WHERE id IN ({duplicate_clause})"),
                    duplicate_params,
                )

                moved_records += int(move_result.rowcount or 0)
                merged_products += len(duplicate_ids)

            return {
                "source_groups": len(groups),
                "merged_products": merged_products,
                "moved_records": moved_records,
                "touched_groups": touched_groups,
            }

    @staticmethod
    def _build_dedup_product_key(
        base_product_key: str,
        group_name: str | None,
        product_name: str | None,
        spec_text: str | None,
        site_name: str | None,
        market_name: str | None,
    ) -> str:
        parts = [
            group_name,
            product_name,
            spec_text,
            market_name,
            site_name,
        ]
        suffix = "-".join(str(part).strip().replace(" ", "") for part in parts if str(part or "").strip())
        return f"{base_product_key}::{suffix}" if suffix else str(base_product_key)
