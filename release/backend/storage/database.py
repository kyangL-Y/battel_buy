from __future__ import annotations

import json
import re
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
from sqlalchemy import bindparam, create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine, URL

from utils.auth import DEFAULT_ADMIN_DISPLAY_NAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME, hash_password
from utils.config_loader import BASE_DIR, load_database_config


DEFAULT_DB_PATH = BASE_DIR / "data" / "price_tracker.db"
AUTH_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{2,63}$")
TABLE_ORDER = [
    "products",
    "price_records",
    "failed_crawl_records",
    "local_compare_records",
    "auth_users",
    "suppliers",
    "procurement_user_suppliers",
    "supplier_registration_requests",
    "procurement_registration_requests",
    "supplier_price_records",
    "supplier_settlement_records",
    "supplier_quote_actions",
    "procurement_plan_records",
    "settings_change_records",
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
    "liancai_top_category": "TEXT",
    "liancai_subcategory": "TEXT",
    "liancai_keyword": "TEXT",
    "liancai_brand_id": "TEXT",
    "liancai_brand_name": "TEXT",
    "liancai_mapping_source": "TEXT",
    "liancai_mapped_at": "TEXT",
    "image_url": "TEXT",
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

SUPPLIER_REGISTRATION_REQUEST_COLUMNS = {
    "company_name": "TEXT",
    "contact_name": "TEXT",
    "contact_phone": "TEXT",
    "username": "TEXT",
    "status": "TEXT",
    "review_notes": "TEXT",
    "supplier_id": "INTEGER",
    "reviewed_by": "TEXT",
    "reviewed_at": "TEXT",
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
    "status": "TEXT",
    "invalidated_at": "TEXT",
    "invalidated_reason": "TEXT",
    "updated_at": "TEXT",
}

SUPPLIER_QUOTE_ACTION_COLUMNS = {
    "record_id": "INTEGER",
    "target_record_id": "INTEGER",
    "action_type": "TEXT",
    "action_reason": "TEXT",
    "operator_name": "TEXT",
    "action_payload": "TEXT",
    "created_at": "TEXT",
}

SUPPLIER_SETTLEMENT_COLUMNS = {
    "period_start": "TEXT",
    "period_end": "TEXT",
    "quote_record_ids": "TEXT",
    "record_count": "INTEGER",
    "total_amount": "REAL",
    "paid_amount": "REAL",
    "pending_amount": "REAL",
    "status": "TEXT",
    "payment_due_date": "TEXT",
    "payment_date": "TEXT",
    "remarks": "TEXT",
    "created_by": "TEXT",
    "updated_at": "TEXT",
}

PROCUREMENT_PLAN_COLUMNS = {
    "plan_title": "TEXT",
    "menu_text": "TEXT",
    "diners": "INTEGER",
    "tables": "INTEGER",
    "preferred_province": "TEXT",
    "preferred_city": "TEXT",
    "preferred_location": "TEXT",
    "ingredient_items": "TEXT",
    "procurement_plan": "TEXT",
    "row_count": "INTEGER",
    "matched_count": "INTEGER",
    "pending_count": "INTEGER",
    "total_cost": "REAL",
    "created_by_user_id": "INTEGER",
    "created_by": "TEXT",
    "updated_at": "TEXT",
}

SETTINGS_CHANGE_COLUMNS = {
    "action_type": "TEXT",
    "target_name": "TEXT",
    "summary": "TEXT",
    "actor_user_id": "INTEGER",
    "actor_name": "TEXT",
    "change_payload": "TEXT",
    "created_at": "TEXT",
}

AUTH_USER_COLUMNS = {
    "username": "TEXT",
    "password_hash": "TEXT",
    "role": "TEXT",
    "supplier_id": "INTEGER",
    "display_name": "TEXT",
    "market_scope": "TEXT",
    "is_active": "INTEGER",
    "is_deleted": "INTEGER",
    "last_login_at": "TEXT",
    "deleted_at": "TEXT",
    "deleted_by": "TEXT",
    "deleted_username": "TEXT",
    "updated_at": "TEXT",
}

PROCUREMENT_REGISTRATION_REQUEST_COLUMNS = {
    "company_name": "TEXT",
    "contact_name": "TEXT",
    "contact_phone": "TEXT",
    "username": "TEXT",
    "market_scope": "TEXT",
    "requested_supplier_names": "TEXT",
    "status": "TEXT",
    "review_notes": "TEXT",
    "auth_user_id": "INTEGER",
    "reviewed_by": "TEXT",
    "reviewed_at": "TEXT",
    "created_at": "TEXT",
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
                raise RuntimeError(
                    "Runtime database backend must be mysql. "
                    "SQLite is only allowed when Database(db_path=...) is passed explicitly for tests or migrations."
                )

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
            statement = text(query) if isinstance(query, str) else query
            return pd.read_sql_query(statement, conn, params=params or {})

    def _column_type(self, value: str) -> str:
        if self.backend == "mysql":
            return MYSQL_TYPE_MAP.get(value, value)
        return value

    @staticmethod
    def _is_meicai_image_url(value: Any) -> bool:
        image_url = str(value or "").strip().lower()
        return image_url.startswith(("http://", "https://")) and "yunshanmeicai.com" in image_url

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
                    CREATE TABLE IF NOT EXISTS auth_users (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        username VARCHAR(255) NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        role VARCHAR(32) NOT NULL,
                        created_at VARCHAR(64) NOT NULL
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
                    CREATE TABLE IF NOT EXISTS procurement_user_suppliers (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        user_id BIGINT NOT NULL,
                        supplier_id BIGINT NOT NULL,
                        created_at VARCHAR(64) NOT NULL,
                        CONSTRAINT fk_procurement_user_suppliers_user FOREIGN KEY (user_id) REFERENCES auth_users(id),
                        CONSTRAINT fk_procurement_user_suppliers_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS supplier_registration_requests (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        company_name VARCHAR(255) NOT NULL,
                        created_at VARCHAR(64) NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS procurement_registration_requests (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        company_name VARCHAR(255) NOT NULL,
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
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS supplier_quote_actions (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        supplier_id BIGINT NOT NULL,
                        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS supplier_settlement_records (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        supplier_id BIGINT NOT NULL,
                        settlement_title VARCHAR(255) NOT NULL,
                        created_at VARCHAR(64) NOT NULL,
                        CONSTRAINT fk_supplier_settlement_records_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS procurement_plan_records (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        plan_title VARCHAR(255) NOT NULL,
                        created_at VARCHAR(64) NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS settings_change_records (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        action_type VARCHAR(64) NOT NULL,
                        target_name VARCHAR(255) NOT NULL,
                        created_at VARCHAR(64) NOT NULL
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
                    CREATE TABLE IF NOT EXISTS auth_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL,
                        created_at TEXT NOT NULL
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
                    CREATE TABLE IF NOT EXISTS procurement_user_suppliers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        supplier_id INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES auth_users(id),
                        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS supplier_registration_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS procurement_registration_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT NOT NULL,
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
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS supplier_quote_actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        supplier_id INTEGER NOT NULL,
                        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS supplier_settlement_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        supplier_id INTEGER NOT NULL,
                        settlement_title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS procurement_plan_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_title TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS settings_change_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action_type TEXT NOT NULL,
                        target_name TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )

            self._ensure_columns(conn, "products", PRODUCT_COLUMNS)
            self._ensure_columns(conn, "price_records", PRICE_RECORD_COLUMNS)
            self._ensure_columns(conn, "failed_crawl_records", FAILED_CRAWL_COLUMNS)
            self._ensure_columns(conn, "local_compare_records", LOCAL_COMPARE_COLUMNS)
            self._ensure_columns(conn, "auth_users", AUTH_USER_COLUMNS)
            self._ensure_columns(conn, "suppliers", SUPPLIER_COLUMNS)
            self._ensure_columns(conn, "procurement_user_suppliers", {
                "user_id": "INTEGER",
                "supplier_id": "INTEGER",
                "created_at": "TEXT",
            })
            self._ensure_columns(conn, "supplier_registration_requests", SUPPLIER_REGISTRATION_REQUEST_COLUMNS)
            self._ensure_columns(conn, "procurement_registration_requests", PROCUREMENT_REGISTRATION_REQUEST_COLUMNS)
            self._ensure_columns(conn, "supplier_price_records", SUPPLIER_PRICE_COLUMNS)
            self._ensure_columns(conn, "supplier_quote_actions", SUPPLIER_QUOTE_ACTION_COLUMNS)
            self._ensure_columns(conn, "supplier_settlement_records", SUPPLIER_SETTLEMENT_COLUMNS)
            self._ensure_columns(conn, "procurement_plan_records", PROCUREMENT_PLAN_COLUMNS)
            self._ensure_columns(conn, "settings_change_records", SETTINGS_CHANGE_COLUMNS)
            self._ensure_indexes(conn)
            self._ensure_default_admin(conn)

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
            for table in [
                "price_records",
                "products",
                "auth_users",
                "suppliers",
                "procurement_user_suppliers",
                "supplier_registration_requests",
                "procurement_registration_requests",
                "supplier_price_records",
                "supplier_quote_actions",
                "supplier_settlement_records",
                "procurement_plan_records",
                "settings_change_records",
            ]
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
        if "idx_auth_users_username" not in existing["auth_users"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_auth_users_username
                ON auth_users (username(255))
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_auth_users_username
                ON auth_users (username)
                """
            )
        if "idx_auth_users_role_supplier" not in existing["auth_users"]:
                conn.exec_driver_sql(
                    """
                    CREATE INDEX idx_auth_users_role_supplier
                    ON auth_users (role, supplier_id)
                    """
                )
        if "idx_procurement_user_suppliers_user_supplier" not in existing.get("procurement_user_suppliers", set()):
            if self.engine.dialect.name == "mysql":
                conn.exec_driver_sql(
                    """
                    CREATE UNIQUE INDEX idx_procurement_user_suppliers_user_supplier
                    ON procurement_user_suppliers (user_id, supplier_id)
                    """
                )
                if "idx_procurement_user_suppliers_supplier" not in existing.get("procurement_user_suppliers", set()):
                    conn.exec_driver_sql(
                        """
                        CREATE INDEX idx_procurement_user_suppliers_supplier
                        ON procurement_user_suppliers (supplier_id, user_id)
                        """
                    )
            else:
                conn.exec_driver_sql(
                    """
                    CREATE UNIQUE INDEX idx_procurement_user_suppliers_user_supplier
                    ON procurement_user_suppliers (user_id, supplier_id)
                    """
                )
                if "idx_procurement_user_suppliers_supplier" not in existing.get("procurement_user_suppliers", set()):
                    conn.exec_driver_sql(
                        """
                        CREATE INDEX idx_procurement_user_suppliers_supplier
                        ON procurement_user_suppliers (supplier_id, user_id)
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
        if "idx_supplier_registration_requests_status_created_id" not in existing["supplier_registration_requests"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_supplier_registration_requests_status_created_id
                ON supplier_registration_requests (status(64), created_at, id)
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_supplier_registration_requests_status_created_id
                ON supplier_registration_requests (status, created_at, id)
                """
            )
        if "idx_procurement_registration_requests_status_created_id" not in existing["procurement_registration_requests"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_procurement_registration_requests_status_created_id
                ON procurement_registration_requests (status(64), created_at, id)
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_procurement_registration_requests_status_created_id
                ON procurement_registration_requests (status, created_at, id)
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
        if "idx_supplier_quote_actions_supplier_created_id" not in existing["supplier_quote_actions"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_supplier_quote_actions_supplier_created_id
                ON supplier_quote_actions (supplier_id, created_at(64), id)
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_supplier_quote_actions_supplier_created_id
                ON supplier_quote_actions (supplier_id, created_at, id)
                """
            )
        if "idx_supplier_settlements_supplier_status_created_id" not in existing["supplier_settlement_records"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_supplier_settlements_supplier_status_created_id
                ON supplier_settlement_records (supplier_id, status(64), created_at, id)
                """
                if self.backend == "mysql"
                else """
                CREATE INDEX idx_supplier_settlements_supplier_status_created_id
                ON supplier_settlement_records (supplier_id, status, created_at, id)
                """
            )
        if "idx_procurement_plan_records_user_created_id" not in existing["procurement_plan_records"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_procurement_plan_records_user_created_id
                ON procurement_plan_records (created_by_user_id, created_at, id)
                """
            )
        if "idx_settings_change_records_created_id" not in existing["settings_change_records"]:
            conn.exec_driver_sql(
                """
                CREATE INDEX idx_settings_change_records_created_id
                ON settings_change_records (created_at, id)
                """
            )

    def _ensure_default_admin(self, conn: Connection) -> None:
        now = datetime.utcnow().isoformat()
        existing_row = conn.execute(
            text(
                """
                SELECT id
                FROM auth_users
                WHERE username = :username
                  AND COALESCE(is_deleted, 0) = 0
                LIMIT 1
                """
            ),
            {"username": DEFAULT_ADMIN_USERNAME},
        ).fetchone()
        if existing_row:
            # 只在缺失时种子管理员；已有账号不应在每次启动时被重置密码或重新启用。
            return

        conn.execute(
            text(
                """
                INSERT INTO auth_users (
                    username, password_hash, role, supplier_id,
                    display_name, is_active, last_login_at, created_at, updated_at
                ) VALUES (
                    :username, :password_hash, :role, :supplier_id,
                    :display_name, :is_active, :last_login_at, :created_at, :updated_at
                )
                """
            ),
            {
                "username": DEFAULT_ADMIN_USERNAME,
                "password_hash": hash_password(DEFAULT_ADMIN_PASSWORD),
                "role": "admin",
                "supplier_id": None,
                "display_name": DEFAULT_ADMIN_DISPLAY_NAME,
                "is_active": 1,
                "last_login_at": None,
                "created_at": now,
                "updated_at": now,
            },
        )

    def _normalize_auth_user_role(self, role: str | None) -> str:
        normalized_role = str(role or "").strip().lower()
        if normalized_role not in {"admin", "supplier", "procurement"}:
            raise ValueError("role must be admin, supplier or procurement")
        return normalized_role

    def _normalize_auth_username(self, username: str | None) -> str:
        normalized_username = str(username or "").strip()
        if not normalized_username:
            raise ValueError("username is required")
        if not AUTH_USERNAME_RE.match(normalized_username):
            raise ValueError("username must be 3-64 characters and only contain letters, numbers, underscore, dash, dot or @")
        return normalized_username

    def upsert_auth_user(
        self,
        *,
        username: str,
        role: str,
        password_hash: str | None = None,
        supplier_id: int | None = None,
        display_name: str | None = None,
        market_scope: str | None = None,
        is_active: bool = True,
        user_id: int | None = None,
    ) -> int:
        normalized_username = self._normalize_auth_username(username)

        normalized_role = self._normalize_auth_user_role(role)
        if normalized_role == "supplier" and supplier_id is None:
            raise ValueError("supplier role requires supplier_id")
        if normalized_role in {"admin", "procurement"}:
            supplier_id = None

        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            existing = None
            if user_id is not None:
                existing = conn.execute(
                    text("SELECT * FROM auth_users WHERE id = :user_id AND COALESCE(is_deleted, 0) = 0"),
                    {"user_id": int(user_id)},
                ).mappings().fetchone()
                if existing is None:
                    raise ValueError("auth user not found")
            if existing is None and normalized_role == "supplier" and supplier_id is not None:
                existing = conn.execute(
                    text(
                        """
                        SELECT *
                        FROM auth_users
                        WHERE role = 'supplier'
                          AND supplier_id = :supplier_id
                          AND COALESCE(is_deleted, 0) = 0
                        """
                    ),
                    {"supplier_id": int(supplier_id)},
                ).mappings().fetchone()
            username_owner = conn.execute(
                text("SELECT * FROM auth_users WHERE username = :username AND COALESCE(is_deleted, 0) = 0"),
                {"username": normalized_username},
            ).mappings().fetchone()
            if username_owner is not None:
                username_owner_row = dict(username_owner)
                if existing is None and normalized_role == "admin":
                    existing = username_owner
                elif existing is None or int(username_owner_row.get("id") or 0) != int(dict(existing).get("id") or 0):
                    raise ValueError("username already exists")

            if existing is not None:
                existing_row = dict(existing)
                next_password_hash = password_hash if password_hash is not None else existing_row.get("password_hash")
                if not next_password_hash:
                    raise ValueError("password_hash is required")
                conn.execute(
                    text(
                        """
                        UPDATE auth_users
                        SET username = :username,
                            password_hash = :password_hash,
                            role = :role,
                            supplier_id = :supplier_id,
                            display_name = :display_name,
                            market_scope = :market_scope,
                            is_active = :is_active,
                            is_deleted = 0,
                            deleted_at = NULL,
                            deleted_by = NULL,
                            deleted_username = NULL,
                            updated_at = :updated_at
                        WHERE id = :user_id
                        """
                    ),
                    {
                        "user_id": int(existing_row["id"]),
                        "username": normalized_username,
                        "password_hash": next_password_hash,
                        "role": normalized_role,
                        "supplier_id": int(supplier_id) if supplier_id is not None else None,
                        "display_name": str(display_name or "").strip() or None,
                        "market_scope": str(market_scope or "").strip() or None,
                        "is_active": 1 if is_active else 0,
                        "updated_at": now,
                    },
                )
                return int(existing_row["id"])

            if password_hash is None:
                raise ValueError("password_hash is required")

            result = conn.execute(
                text(
                    """
                    INSERT INTO auth_users (
                        username, password_hash, role, supplier_id,
                        display_name, market_scope, is_active, is_deleted, last_login_at,
                        deleted_at, deleted_by, deleted_username, created_at, updated_at
                    ) VALUES (
                        :username, :password_hash, :role, :supplier_id,
                        :display_name, :market_scope, :is_active, :is_deleted, :last_login_at,
                        :deleted_at, :deleted_by, :deleted_username, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "username": normalized_username,
                    "password_hash": password_hash,
                    "role": normalized_role,
                    "supplier_id": int(supplier_id) if supplier_id is not None else None,
                    "display_name": str(display_name or "").strip() or None,
                    "market_scope": str(market_scope or "").strip() or None,
                    "is_active": 1 if is_active else 0,
                    "is_deleted": 0,
                    "last_login_at": None,
                    "deleted_at": None,
                    "deleted_by": None,
                    "deleted_username": None,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            return int(result.lastrowid)

    def touch_auth_user_login(self, user_id: int, logged_in_at: str | None = None) -> int | None:
        timestamp = str(logged_in_at or datetime.utcnow().isoformat()).strip()
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE auth_users
                    SET last_login_at = :last_login_at,
                        updated_at = :updated_at
                    WHERE id = :user_id
                      AND COALESCE(is_deleted, 0) = 0
                    """
                ),
                {
                    "user_id": int(user_id),
                    "last_login_at": timestamp,
                    "updated_at": timestamp,
                },
            )
        return int(user_id) if int(getattr(result, "rowcount", 0) or 0) > 0 else None

    def _build_auth_user_query(self, where_sql: str, *, include_deleted: bool = False) -> str:
        deleted_filter = "" if include_deleted else " AND COALESCE(u.is_deleted, 0) = 0"
        return f"""
        SELECT
            u.id,
            u.username,
            u.password_hash,
            u.role,
            u.supplier_id,
            u.display_name,
            u.market_scope,
            u.is_active,
            u.is_deleted,
            u.last_login_at,
            u.deleted_at,
            u.deleted_by,
            u.deleted_username,
            u.created_at,
            u.updated_at,
            s.supplier_name,
            s.contact_name AS supplier_contact_name,
            s.contact_phone AS supplier_contact_phone,
            s.market_scope AS supplier_market_scope,
            s.market_category AS supplier_market_category,
            s.channel AS supplier_channel,
            s.notes AS supplier_notes,
            s.is_active AS supplier_is_active
        FROM auth_users u
        LEFT JOIN suppliers s ON s.id = u.supplier_id
        WHERE ({where_sql}){deleted_filter}
        LIMIT 1
        """

    def get_auth_user_by_username(self, username: str, *, include_deleted: bool = False) -> pd.DataFrame:
        normalized_username = str(username or "").strip()
        if not normalized_username:
            return pd.DataFrame()
        return self._read_sql(
            self._build_auth_user_query("u.username = :username", include_deleted=include_deleted),
            {"username": normalized_username},
        )

    def get_auth_user_by_id(self, user_id: int, *, include_deleted: bool = False) -> pd.DataFrame:
        return self._read_sql(
            self._build_auth_user_query("u.id = :user_id", include_deleted=include_deleted),
            {"user_id": int(user_id)},
        )

    def get_auth_user_by_supplier_id(self, supplier_id: int, *, include_deleted: bool = False) -> pd.DataFrame:
        return self._read_sql(
            self._build_auth_user_query(
                "u.role = 'supplier' AND u.supplier_id = :supplier_id",
                include_deleted=include_deleted,
            ),
            {"supplier_id": int(supplier_id)},
        )

    def get_auth_users(
        self,
        role: str | None = None,
        active_status: str | None = None,
        keyword: str | None = None,
        include_deleted: bool = False,
    ) -> pd.DataFrame:
        where_clauses: list[str] = []
        params: dict[str, Any] = {}
        if not include_deleted:
            where_clauses.append("COALESCE(u.is_deleted, 0) = 0")
        normalized_role = str(role or "").strip().lower()
        if normalized_role in {"admin", "supplier", "procurement"}:
            where_clauses.append("u.role = :role")
            params["role"] = normalized_role
        normalized_status = str(active_status or "").strip().lower()
        if normalized_status == "active":
            where_clauses.append("COALESCE(u.is_active, 0) = 1")
        elif normalized_status == "inactive":
            where_clauses.append("COALESCE(u.is_active, 0) = 0")
        normalized_keyword = str(keyword or "").strip().lower()
        if normalized_keyword:
            params["keyword_like"] = f"%{normalized_keyword}%"
            where_clauses.append(
                """
                (
                    LOWER(COALESCE(u.username, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(u.display_name, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(u.market_scope, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(s.supplier_name, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(s.contact_name, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(s.contact_phone, '')) LIKE :keyword_like
                )
                """
            )
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return self._read_sql(
            f"""
            SELECT
                u.id,
                u.username,
                u.password_hash,
                u.role,
                u.supplier_id,
                u.display_name,
                u.market_scope,
                u.is_active,
                u.is_deleted,
                u.last_login_at,
                u.deleted_at,
                u.deleted_by,
                u.deleted_username,
                u.created_at,
                u.updated_at,
                s.supplier_name,
                s.contact_name AS supplier_contact_name,
                s.contact_phone AS supplier_contact_phone,
                s.market_scope AS supplier_market_scope,
                s.market_category AS supplier_market_category,
                s.channel AS supplier_channel,
                s.notes AS supplier_notes,
                s.is_active AS supplier_is_active
            FROM auth_users u
            LEFT JOIN suppliers s ON s.id = u.supplier_id
            {where_sql}
            ORDER BY
                CASE u.role WHEN 'admin' THEN 0 ELSE 1 END,
                COALESCE(u.is_active, 0) DESC,
                u.updated_at DESC,
                u.id DESC
            """,
            params,
        )

    def get_procurement_user_supplier_ids(self, user_id: int) -> list[int]:
        rows = self._read_sql(
            """
            SELECT pus.supplier_id
            FROM procurement_user_suppliers pus
            JOIN suppliers s
              ON s.id = pus.supplier_id
             AND COALESCE(s.is_active, 0) = 1
            JOIN auth_users u
              ON u.id = pus.user_id
             AND u.role = 'procurement'
             AND COALESCE(u.is_active, 0) = 1
             AND COALESCE(u.is_deleted, 0) = 0
            WHERE pus.user_id = :user_id
            ORDER BY pus.supplier_id ASC
            """,
            {"user_id": int(user_id)},
        )
        if rows.empty:
            return []
        return [
            int(value)
            for value in rows["supplier_id"].tolist()
            if value is not None and str(value).strip()
        ]

    def get_supplier_by_name(self, supplier_name: str) -> pd.DataFrame:
        normalized_name = str(supplier_name or "").strip()
        if not normalized_name:
            return pd.DataFrame()
        return self._read_sql(
            """
            SELECT id, supplier_name, contact_name, contact_phone, market_scope, market_category, channel, notes, is_active, created_at, updated_at
            FROM suppliers
            WHERE supplier_name = :supplier_name
            LIMIT 1
            """,
            {"supplier_name": normalized_name},
        )

    def get_procurement_user_supplier_mappings(self, supplier_ids: list[int] | tuple[int, ...]) -> pd.DataFrame:
        normalized_supplier_ids = sorted({
            int(supplier_id)
            for supplier_id in supplier_ids or []
            if supplier_id is not None and int(supplier_id) > 0
        })
        if not normalized_supplier_ids:
            return pd.DataFrame(columns=["user_id", "supplier_id"])
        statement = text(
            """
            SELECT pus.user_id, pus.supplier_id
            FROM procurement_user_suppliers pus
            JOIN auth_users u
              ON u.id = pus.user_id
             AND u.role = 'procurement'
             AND COALESCE(u.is_active, 0) = 1
             AND COALESCE(u.is_deleted, 0) = 0
            WHERE pus.supplier_id IN :supplier_ids
            ORDER BY pus.supplier_id ASC, pus.user_id ASC
            """
        ).bindparams(bindparam("supplier_ids", expanding=True))
        return self._read_sql(statement, {"supplier_ids": normalized_supplier_ids})

    def replace_procurement_user_suppliers(self, user_id: int, supplier_ids: list[int] | tuple[int, ...]) -> None:
        normalized_user_id = int(user_id)
        normalized_supplier_ids = sorted({
            int(supplier_id)
            for supplier_id in (supplier_ids or [])
            if supplier_id is not None and int(supplier_id) > 0
        })
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                text("DELETE FROM procurement_user_suppliers WHERE user_id = :user_id"),
                {"user_id": normalized_user_id},
            )
            for supplier_id in normalized_supplier_ids:
                conn.execute(
                    text(
                        """
                        INSERT INTO procurement_user_suppliers (user_id, supplier_id, created_at)
                        VALUES (:user_id, :supplier_id, :created_at)
                        """
                    ),
                    {
                        "user_id": normalized_user_id,
                        "supplier_id": supplier_id,
                        "created_at": now,
                    },
                )

    def delete_auth_user(self, user_id: int, deleted_by: str | None = None) -> bool:
        now = datetime.utcnow().isoformat()
        normalized_user_id = int(user_id)
        archived_username = f"__deleted_{normalized_user_id}"
        with self.connect() as conn:
            existing = conn.execute(
                text(
                    """
                    SELECT username, role, supplier_id
                    FROM auth_users
                    WHERE id = :user_id
                      AND COALESCE(is_deleted, 0) = 0
                    """
                ),
                {"user_id": normalized_user_id},
            ).mappings().fetchone()
            if existing is None:
                return False
            if str(existing.get("role") or "").strip() == "procurement":
                conn.execute(
                    text("DELETE FROM procurement_user_suppliers WHERE user_id = :user_id"),
                    {"user_id": normalized_user_id},
                )
            if str(existing.get("role") or "").strip() == "supplier" and existing.get("supplier_id") is not None:
                supplier_id = int(existing["supplier_id"])
                conn.execute(
                    text("DELETE FROM procurement_user_suppliers WHERE supplier_id = :supplier_id"),
                    {"supplier_id": supplier_id},
                )
                conn.execute(
                    text(
                        """
                        UPDATE suppliers
                        SET is_active = 0,
                            updated_at = :updated_at
                        WHERE id = :supplier_id
                        """
                    ),
                    {
                        "supplier_id": supplier_id,
                        "updated_at": now,
                    },
                )
            result = conn.execute(
                text(
                    """
                    UPDATE auth_users
                    SET username = :archived_username,
                        is_active = 0,
                        is_deleted = 1,
                        deleted_at = :deleted_at,
                        deleted_by = :deleted_by,
                        deleted_username = :deleted_username,
                        updated_at = :updated_at
                    WHERE id = :user_id
                      AND COALESCE(is_deleted, 0) = 0
                    """
                ),
                {
                    "user_id": normalized_user_id,
                    "archived_username": archived_username,
                    "deleted_at": now,
                    "deleted_by": str(deleted_by or "").strip() or None,
                    "deleted_username": str(existing.get("username") or "").strip() or None,
                    "updated_at": now,
                },
            )
            return int(getattr(result, "rowcount", 0) or 0) > 0

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
        liancai_top_category: str | None = None,
        liancai_subcategory: str | None = None,
        liancai_keyword: str | None = None,
        liancai_brand_id: str | None = None,
        liancai_brand_name: str | None = None,
        liancai_mapping_source: str | None = None,
        image_url: str | None = None,
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
                            region_label = :region_label,
                            liancai_top_category = COALESCE(:liancai_top_category, liancai_top_category),
                            liancai_subcategory = COALESCE(:liancai_subcategory, liancai_subcategory),
                            liancai_keyword = COALESCE(:liancai_keyword, liancai_keyword),
                            liancai_brand_id = COALESCE(:liancai_brand_id, liancai_brand_id),
                            liancai_brand_name = COALESCE(:liancai_brand_name, liancai_brand_name),
                            liancai_mapping_source = COALESCE(:liancai_mapping_source, liancai_mapping_source),
                            liancai_mapped_at = COALESCE(:liancai_mapped_at, liancai_mapped_at),
                            image_url = CASE
                                WHEN :image_url IS NOT NULL AND :image_url != '' THEN :image_url
                                ELSE image_url
                            END
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
                        "liancai_top_category": liancai_top_category,
                        "liancai_subcategory": liancai_subcategory,
                        "liancai_keyword": liancai_keyword,
                        "liancai_brand_id": liancai_brand_id,
                        "liancai_brand_name": liancai_brand_name,
                        "liancai_mapping_source": liancai_mapping_source,
                        "liancai_mapped_at": created_at if liancai_top_category or liancai_subcategory else None,
                        "image_url": image_url,
                    },
                )
                return int(existing["id"])

            result = conn.execute(
                text(
                    """
                    INSERT INTO products (
                        product_key, group_name, product_name, source_url, site_name, created_at,
                        category, brand, product_series, spec_text, compare_key,
                        province, city, market_name, region_label,
                        liancai_top_category, liancai_subcategory, liancai_keyword, liancai_brand_id, liancai_brand_name,
                        liancai_mapping_source, liancai_mapped_at, image_url
                    )
                    VALUES (
                        :product_key, :group_name, :product_name, :source_url, :site_name, :created_at,
                        :category, :brand, :product_series, :spec_text, :compare_key,
                        :province, :city, :market_name, :region_label,
                        :liancai_top_category, :liancai_subcategory, :liancai_keyword, :liancai_brand_id, :liancai_brand_name,
                        :liancai_mapping_source, :liancai_mapped_at, :image_url
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
                    "liancai_top_category": liancai_top_category,
                    "liancai_subcategory": liancai_subcategory,
                    "liancai_keyword": liancai_keyword,
                    "liancai_brand_id": liancai_brand_id,
                    "liancai_brand_name": liancai_brand_name,
                    "liancai_mapping_source": liancai_mapping_source,
                    "liancai_mapped_at": created_at if liancai_top_category or liancai_subcategory else None,
                    "image_url": image_url,
                },
            )
            return int(result.lastrowid)

    def bulk_upsert_products(
        self,
        records: list[dict[str, Any]],
        batch_size: int = 500,
        *,
        update_existing: bool = True,
    ) -> dict[str, int]:
        if not records:
            return {}

        created_at = datetime.utcnow().isoformat()
        product_columns = [
            "product_key",
            "group_name",
            "product_name",
            "source_url",
            "site_name",
            "category",
            "brand",
            "product_series",
            "spec_text",
            "compare_key",
            "province",
            "city",
            "market_name",
            "region_label",
            "liancai_top_category",
            "liancai_subcategory",
            "liancai_keyword",
            "liancai_brand_id",
            "liancai_brand_name",
            "liancai_mapping_source",
            "liancai_mapped_at",
            "image_url",
        ]
        deduped: dict[str, dict[str, Any]] = {}
        for record in records:
            product_key = str(record.get("product_key") or "").strip()
            if not product_key:
                continue
            normalized = {column: record.get(column) for column in product_columns}
            normalized["product_key"] = product_key
            normalized["created_at"] = created_at
            normalized["liancai_mapped_at"] = (
                created_at if normalized.get("liancai_top_category") or normalized.get("liancai_subcategory") else None
            )
            deduped[product_key] = normalized

        if not deduped:
            return {}

        select_stmt = text("SELECT id, product_key FROM products WHERE product_key IN :product_keys").bindparams(
            bindparam("product_keys", expanding=True)
        )
        update_stmt = text(
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
                region_label = :region_label,
                liancai_top_category = COALESCE(:liancai_top_category, liancai_top_category),
                liancai_subcategory = COALESCE(:liancai_subcategory, liancai_subcategory),
                liancai_keyword = COALESCE(:liancai_keyword, liancai_keyword),
                liancai_brand_id = COALESCE(:liancai_brand_id, liancai_brand_id),
                liancai_brand_name = COALESCE(:liancai_brand_name, liancai_brand_name),
                liancai_mapping_source = COALESCE(:liancai_mapping_source, liancai_mapping_source),
                liancai_mapped_at = COALESCE(:liancai_mapped_at, liancai_mapped_at),
                image_url = CASE
                    WHEN :image_url IS NOT NULL AND :image_url != '' THEN :image_url
                    ELSE image_url
                END
            WHERE product_key = :product_key
            """
        )
        insert_stmt = text(
            """
            INSERT INTO products (
                product_key, group_name, product_name, source_url, site_name, created_at,
                category, brand, product_series, spec_text, compare_key,
                province, city, market_name, region_label,
                liancai_top_category, liancai_subcategory, liancai_keyword, liancai_brand_id, liancai_brand_name,
                liancai_mapping_source, liancai_mapped_at, image_url
            )
            VALUES (
                :product_key, :group_name, :product_name, :source_url, :site_name, :created_at,
                :category, :brand, :product_series, :spec_text, :compare_key,
                :province, :city, :market_name, :region_label,
                :liancai_top_category, :liancai_subcategory, :liancai_keyword, :liancai_brand_id, :liancai_brand_name,
                :liancai_mapping_source, :liancai_mapped_at, :image_url
            )
            """
        )

        product_keys = list(deduped)
        existing: dict[str, int] = {}
        for start in range(0, len(product_keys), batch_size):
            chunk = product_keys[start : start + batch_size]
            with self.connect() as conn:
                rows = conn.execute(select_stmt, {"product_keys": chunk}).mappings().all()
                existing.update({str(row["product_key"]): int(row["id"]) for row in rows})

        existing_records = [record for key, record in deduped.items() if key in existing]
        missing_records = [record for key, record in deduped.items() if key not in existing]
        if update_existing:
            for start in range(0, len(existing_records), batch_size):
                with self.connect() as conn:
                    conn.execute(update_stmt, existing_records[start : start + batch_size])
        for start in range(0, len(missing_records), batch_size):
            with self.connect() as conn:
                conn.execute(insert_stmt, missing_records[start : start + batch_size])

        product_id_map: dict[str, int] = {}
        for start in range(0, len(product_keys), batch_size):
            chunk = product_keys[start : start + batch_size]
            with self.connect() as conn:
                rows = conn.execute(select_stmt, {"product_keys": chunk}).mappings().all()
            product_id_map.update({str(row["product_key"]): int(row["id"]) for row in rows})
        return product_id_map

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

    def bulk_insert_price_records(self, records: list[dict[str, Any]], batch_size: int = 500) -> int:
        if not records:
            return 0
        statement = text(
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
        )
        normalized_records = []
        for record in records:
            raw_payload = record.get("raw_payload")
            normalized_records.append(
                {
                    "product_id": record.get("product_id"),
                    "captured_at": record.get("captured_at"),
                    "current_price": record.get("current_price"),
                    "original_price": record.get("original_price"),
                    "promotion_text": record.get("promotion_text"),
                    "currency": record.get("currency") or "CNY",
                    "availability": record.get("availability"),
                    "raw_payload": json.dumps(raw_payload or {}, ensure_ascii=False),
                    "unit_name": record.get("unit_name"),
                    "unit_value": record.get("unit_value"),
                    "unit_price": record.get("unit_price"),
                }
            )
        for start in range(0, len(normalized_records), batch_size):
            with self.connect() as conn:
                conn.execute(statement, normalized_records[start : start + batch_size])
        return len(normalized_records)

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
                p.liancai_top_category,
                p.liancai_subcategory,
                p.liancai_keyword,
                p.liancai_brand_id,
                p.liancai_brand_name,
                p.liancai_mapping_source,
                p.liancai_mapped_at,
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

    def get_crawled_location_records(self) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT DISTINCT
                p.province,
                p.city,
                p.market_name,
                p.region_label,
                p.site_name,
                p.source_url
            FROM products p
            WHERE EXISTS (
                SELECT 1
                FROM price_records r
                WHERE r.product_id = p.id
                LIMIT 1
            )
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
                p.liancai_top_category,
                p.liancai_subcategory,
                p.liancai_keyword,
                p.liancai_brand_id,
                p.liancai_brand_name,
                p.liancai_mapping_source,
                p.liancai_mapped_at,
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
                p.liancai_top_category,
                p.liancai_subcategory,
                p.liancai_keyword,
                p.liancai_brand_id,
                p.liancai_brand_name,
                p.liancai_mapping_source,
                p.liancai_mapped_at,
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

    def get_product_keys_for_identity(self, identity_key: str, limit: int = 200) -> list[str]:
        normalized_identity_key = str(identity_key or "").strip()
        if not normalized_identity_key:
            return []

        def normalize_compare_segment(value: str) -> str:
            normalized_value = value.strip().lower()
            normalized_value = re.sub(r"[\s\-_·•|/]+", "", normalized_value)
            return re.sub(r"[^\u4e00-\u9fa5a-z0-9]+", "", normalized_value)

        identity_parts = [normalize_compare_segment(item) for item in normalized_identity_key.split("|")]
        identity_parts = [item for item in identity_parts if item]
        if not identity_parts:
            return []

        def normalized_column_sql(column_name: str) -> str:
            expression = f"LOWER(COALESCE({column_name}, ''))"
            for token in [" ", "\t", "\r", "\n", "-", "_", "·", "•", "|", "/", "*", ".", "。", ",", "，", "(", ")", "（", "）"]:
                expression = f"REPLACE({expression}, '{token}', '')"
            return expression

        product_name_match = (
            f"({normalized_column_sql('product_name')} = :primary_part "
            f"OR {normalized_column_sql('group_name')} = :primary_part)"
        )
        attribute_columns = ["category", "brand", "product_series", "spec_text"]
        where_clauses = [
            "product_key = :identity_key",
            f"{normalized_column_sql('compare_key')} = :compact_identity_key",
        ]
        params: dict[str, object] = {
            "identity_key": normalized_identity_key,
            "compact_identity_key": normalize_compare_segment(normalized_identity_key),
            "primary_part": identity_parts[0],
            "limit": max(1, min(int(limit or 0), 1000)),
        }

        if len(identity_parts) == 1:
            where_clauses.append(product_name_match)
        else:
            attribute_match_clauses: list[str] = []
            for index, identity_part in enumerate(identity_parts[1:], start=1):
                param_name = f"identity_part_{index}"
                params[param_name] = identity_part
                attribute_match_clauses.append(
                    "("
                    + " OR ".join(f"{normalized_column_sql(column_name)} = :{param_name}" for column_name in attribute_columns)
                    + ")"
                )
            where_clauses.append(f"({product_name_match} AND {' AND '.join(attribute_match_clauses)})")

        statement = text(
            f"""
            SELECT product_key
            FROM products
            WHERE {' OR '.join(where_clauses)}
            ORDER BY id DESC
            LIMIT :limit
            """
        )
        with self.connect() as conn:
            rows = conn.execute(statement, params).mappings().all()
        return [str(row["product_key"]) for row in rows if str(row.get("product_key") or "").strip()]

    def get_latest_records(self) -> pd.DataFrame:
        if self.backend == "mysql":
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
                    p.liancai_top_category,
                    p.liancai_subcategory,
                    p.liancai_keyword,
                    p.liancai_brand_id,
                    p.liancai_brand_name,
                    p.liancai_mapping_source,
                    p.liancai_mapped_at,
                    p.site_name,
                    p.source_url,
                    CASE
                        WHEN (p.site_name LIKE '莲菜网%' OR p.source_url LIKE '%liancaiwang.cn%') THEN p.image_url
                        WHEN (
                            p.site_name LIKE '美菜网%'
                            OR p.source_url LIKE '%yunshanmeicai.com%'
                            OR p.source_url LIKE '%meicai.cn%'
                        ) THEN p.image_url
                        ELSE NULL
                    END AS image_url,
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
                FROM price_records r
                JOIN (
                    SELECT product_id, MAX(id) AS latest_record_id
                    FROM price_records
                    GROUP BY product_id
                ) latest ON latest.latest_record_id = r.id
                JOIN products p ON p.id = r.product_id
                ORDER BY r.captured_at DESC
                """
            )
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
                p.liancai_top_category,
                p.liancai_subcategory,
                p.liancai_keyword,
                p.liancai_brand_id,
                p.liancai_brand_name,
                p.liancai_mapping_source,
                p.liancai_mapped_at,
                p.site_name,
                p.source_url,
                CASE
                    WHEN (p.site_name LIKE '莲菜网%' OR p.source_url LIKE '%liancaiwang.cn%') THEN p.image_url
                    WHEN (
                        p.site_name LIKE '美菜网%'
                        OR p.source_url LIKE '%yunshanmeicai.com%'
                        OR p.source_url LIKE '%meicai.cn%'
                    ) THEN p.image_url
                    ELSE NULL
                END AS image_url,
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

    def backfill_liancai_product_image_urls(self) -> int:
        """Backfill lightweight product image URLs from existing Liancai raw payloads."""
        if self.backend != "mysql":
            return 0
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE products p
                    JOIN (
                        SELECT
                            lp.id AS product_id,
                            COALESCE(
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.parsed.extra_fields.cover')), ''),
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.parsed.extra_fields.image_url')), ''),
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.parsed.image_url')), ''),
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.cover')), ''),
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.image_url')), '')
                            ) AS image_url
                        FROM products lp
                        JOIN price_records r ON r.id = (
                            SELECT pr2.id
                            FROM price_records pr2
                            WHERE pr2.product_id = lp.id
                            ORDER BY pr2.id DESC
                            LIMIT 1
                        )
                        WHERE (lp.site_name LIKE '莲菜网%' OR lp.source_url LIKE '%liancaiwang.cn%')
                            AND r.raw_payload IS NOT NULL
                            AND JSON_VALID(r.raw_payload)
                    ) latest_image ON latest_image.product_id = p.id
                    SET p.image_url = latest_image.image_url
                    WHERE (p.site_name LIKE '莲菜网%' OR p.source_url LIKE '%liancaiwang.cn%')
                        AND (p.image_url IS NULL OR p.image_url = '')
                        AND latest_image.image_url IS NOT NULL
                        AND latest_image.image_url != ''
                    """
                )
            )
            return int(result.rowcount or 0)

    def backfill_meicai_product_image_urls(self) -> int:
        if self.backend == "mysql":
            return self._backfill_meicai_product_image_urls_mysql()
        return self._backfill_meicai_product_image_urls_sqlite()

    def _backfill_meicai_product_image_urls_mysql(self) -> int:
        with self.connect() as conn:
            backfill_result = conn.execute(
                text(
                    """
                    UPDATE products p
                    JOIN (
                        SELECT
                            mp.id AS product_id,
                            COALESCE(
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.parsed.extra_fields.cover')), ''),
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.parsed.extra_fields.image_url')), ''),
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.parsed.image_url')), ''),
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.cover')), ''),
                                NULLIF(JSON_UNQUOTE(JSON_EXTRACT(r.raw_payload, '$.image_url')), '')
                            ) AS image_url
                        FROM products mp
                        JOIN price_records r ON r.id = (
                            SELECT pr2.id
                            FROM price_records pr2
                            WHERE pr2.product_id = mp.id
                                AND pr2.raw_payload IS NOT NULL
                                AND JSON_VALID(pr2.raw_payload)
                                AND COALESCE(
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.parsed.extra_fields.cover')), ''),
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.parsed.extra_fields.image_url')), ''),
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.parsed.image_url')), ''),
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.cover')), ''),
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.image_url')), '')
                                ) LIKE 'http%'
                                AND COALESCE(
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.parsed.extra_fields.cover')), ''),
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.parsed.extra_fields.image_url')), ''),
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.parsed.image_url')), ''),
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.cover')), ''),
                                    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(pr2.raw_payload, '$.image_url')), '')
                                ) LIKE '%yunshanmeicai.com%'
                            ORDER BY pr2.id DESC
                            LIMIT 1
                        )
                        WHERE (
                                mp.site_name LIKE '美菜网%'
                                OR mp.source_url LIKE '%yunshanmeicai.com%'
                                OR mp.source_url LIKE '%meicai.cn%'
                            )
                    ) latest_image ON latest_image.product_id = p.id
                    SET p.image_url = latest_image.image_url
                    WHERE (
                            p.site_name LIKE '美菜网%'
                            OR p.source_url LIKE '%yunshanmeicai.com%'
                            OR p.source_url LIKE '%meicai.cn%'
                        )
                        AND (p.image_url IS NULL OR p.image_url = '')
                        AND latest_image.image_url IS NOT NULL
                        AND latest_image.image_url != ''
                        AND latest_image.image_url LIKE 'http%'
                        AND latest_image.image_url LIKE '%yunshanmeicai.com%'
                    """
                )
            )
            return int(backfill_result.rowcount or 0)

    def _backfill_meicai_product_image_urls_sqlite(self) -> int:
        with self.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        p.id AS product_id,
                        r.raw_payload AS raw_payload
                    FROM products p
                    JOIN price_records r ON r.product_id = p.id
                    WHERE (
                            p.site_name LIKE '美菜网%'
                            OR p.source_url LIKE '%yunshanmeicai.com%'
                            OR p.source_url LIKE '%meicai.cn%'
                        )
                        AND (p.image_url IS NULL OR p.image_url = '')
                        AND r.raw_payload IS NOT NULL
                    ORDER BY p.id ASC, r.id DESC
                    """
                )
            ).mappings().all()
            updated_count = 0
            seen_product_ids: set[int] = set()
            for row in rows:
                product_id = int(row["product_id"])
                if product_id in seen_product_ids:
                    continue
                image_url = self._extract_meicai_image_url_from_raw_payload(row.get("raw_payload"))
                if not image_url:
                    continue
                update_result = conn.execute(
                    text(
                        """
                        UPDATE products
                        SET image_url = :image_url
                        WHERE id = :product_id
                          AND (image_url IS NULL OR image_url = '')
                        """
                    ),
                    {"product_id": product_id, "image_url": image_url},
                )
                updated_count += int(update_result.rowcount or 0)
                seen_product_ids.add(product_id)
            return updated_count

    @classmethod
    def _extract_meicai_image_url_from_raw_payload(cls, raw_payload: Any) -> str | None:
        if isinstance(raw_payload, str):
            try:
                payload = json.loads(raw_payload)
            except json.JSONDecodeError:
                return None
        elif isinstance(raw_payload, dict):
            payload = raw_payload
        else:
            return None

        parsed = payload.get("parsed") if isinstance(payload.get("parsed"), dict) else {}
        extra_fields = parsed.get("extra_fields") if isinstance(parsed.get("extra_fields"), dict) else {}
        candidates = [
            extra_fields.get("cover"),
            extra_fields.get("image_url"),
            parsed.get("image_url"),
            payload.get("cover"),
            payload.get("image_url"),
        ]
        for candidate in candidates:
            image_url = str(candidate or "").strip()
            if cls._is_meicai_image_url(image_url):
                return image_url
        return None

    def get_liancai_category_summary(self, source_name: str | None = None) -> pd.DataFrame:
        where_clauses: list[str] = []
        params: dict[str, Any] = {}
        if source_name:
            normalized_source_name = str(source_name).strip()
            if "莲菜网" in normalized_source_name:
                where_clauses.append("site_name LIKE :source_name_prefix")
                params["source_name_prefix"] = f"{normalized_source_name}%"
            else:
                where_clauses.append("site_name = :source_name")
                params["source_name"] = normalized_source_name
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return self._read_sql(
            f"""
            SELECT
                COALESCE(liancai_top_category, '未映射') AS liancai_top_category,
                COALESCE(liancai_subcategory, '未映射') AS liancai_subcategory,
                COALESCE(liancai_keyword, '未映射') AS liancai_keyword,
                COALESCE(liancai_brand_id, '未映射') AS liancai_brand_id,
                COALESCE(liancai_brand_name, '未映射') AS liancai_brand_name,
                COUNT(*) AS product_count
            FROM products
            {where_sql}
            GROUP BY
                COALESCE(liancai_top_category, '未映射'),
                COALESCE(liancai_subcategory, '未映射'),
                COALESCE(liancai_keyword, '未映射'),
                COALESCE(liancai_brand_id, '未映射'),
                COALESCE(liancai_brand_name, '未映射')
            ORDER BY product_count DESC, liancai_top_category ASC, liancai_subcategory ASC, liancai_keyword ASC, liancai_brand_name ASC
            """,
            params,
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
            a.id AS account_id,
            a.username AS account_username,
            a.display_name AS account_display_name,
            a.is_active AS account_is_active,
            COUNT(r.id) AS quote_count,
            MAX(r.quoted_at) AS latest_quoted_at
        FROM suppliers s
        LEFT JOIN auth_users a
            ON a.supplier_id = s.id
           AND a.role = 'supplier'
        LEFT JOIN supplier_price_records r
            ON r.supplier_id = s.id
           AND COALESCE(r.status, 'active') = 'active'
        """
        params: dict[str, Any] = {}
        if active_only:
            query += " WHERE COALESCE(s.is_active, 0) = 1"
        query += """
        GROUP BY
            s.id, s.supplier_name, s.contact_name, s.contact_phone, s.market_scope,
            s.market_category, s.channel, s.notes, s.is_active, s.created_at, s.updated_at,
            a.id, a.username, a.display_name, a.is_active
        ORDER BY COALESCE(s.is_active, 0) DESC, s.supplier_name ASC
        """
        return self._read_sql(query, params)

    def create_supplier_registration_request(
        self,
        company_name: str,
        contact_name: str | None = None,
        contact_phone: str | None = None,
        username: str | None = None,
    ) -> int:
        normalized_company_name = str(company_name or "").strip()
        normalized_username = self._normalize_auth_username(username)
        if not normalized_company_name:
            raise ValueError("company_name is required")

        existing_auth = self.get_auth_user_by_username(normalized_username)
        if not existing_auth.empty:
            raise ValueError("username already exists")

        pending_request = self._read_sql(
            """
            SELECT id
            FROM supplier_registration_requests
            WHERE username = :username
              AND COALESCE(status, 'pending') = 'pending'
            LIMIT 1
            """,
            {"username": normalized_username},
        )
        if not pending_request.empty:
            raise ValueError("registration request already pending")

        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO supplier_registration_requests (
                        company_name, contact_name, contact_phone, username,
                        status, review_notes, supplier_id, reviewed_by, reviewed_at, created_at, updated_at
                    ) VALUES (
                        :company_name, :contact_name, :contact_phone, :username,
                        :status, :review_notes, :supplier_id, :reviewed_by, :reviewed_at, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "company_name": normalized_company_name,
                    "contact_name": str(contact_name or "").strip() or None,
                    "contact_phone": str(contact_phone or "").strip() or None,
                    "username": normalized_username,
                    "status": "pending",
                    "review_notes": None,
                    "supplier_id": None,
                    "reviewed_by": None,
                    "reviewed_at": None,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            return int(result.lastrowid)

    def create_procurement_registration_request(
        self,
        company_name: str,
        contact_name: str | None = None,
        contact_phone: str | None = None,
        username: str | None = None,
        market_scope: str | None = None,
        requested_supplier_names: str | None = None,
    ) -> int:
        normalized_company_name = str(company_name or "").strip()
        normalized_username = self._normalize_auth_username(username)
        if not normalized_company_name:
            raise ValueError("company_name is required")
        existing_auth = self.get_auth_user_by_username(normalized_username)
        if not existing_auth.empty:
            raise ValueError("username already exists")
        pending_request = self._read_sql(
            """
            SELECT id
            FROM procurement_registration_requests
            WHERE username = :username
              AND COALESCE(status, 'pending') = 'pending'
            LIMIT 1
            """,
            {"username": normalized_username},
        )
        if not pending_request.empty:
            raise ValueError("registration request already pending")
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO procurement_registration_requests (
                        company_name, contact_name, contact_phone, username, market_scope, requested_supplier_names,
                        status, review_notes, auth_user_id, reviewed_by, reviewed_at, created_at, updated_at
                    ) VALUES (
                        :company_name, :contact_name, :contact_phone, :username, :market_scope, :requested_supplier_names,
                        :status, :review_notes, :auth_user_id, :reviewed_by, :reviewed_at, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "company_name": normalized_company_name,
                    "contact_name": str(contact_name or "").strip() or None,
                    "contact_phone": str(contact_phone or "").strip() or None,
                    "username": normalized_username,
                    "market_scope": str(market_scope or "").strip() or None,
                    "requested_supplier_names": str(requested_supplier_names or "").strip() or None,
                    "status": "pending",
                    "review_notes": None,
                    "auth_user_id": None,
                    "reviewed_by": None,
                    "reviewed_at": None,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            return int(result.lastrowid)

    def get_supplier_registration_requests(
        self,
        status: str | None = None,
        keyword: str | None = None,
    ) -> pd.DataFrame:
        where_clauses: list[str] = []
        params: dict[str, Any] = {}
        normalized_status = str(status or "").strip().lower()
        if normalized_status:
            where_clauses.append("LOWER(COALESCE(r.status, 'pending')) = :status")
            params["status"] = normalized_status
        normalized_keyword = str(keyword or "").strip().lower()
        if normalized_keyword:
            params["keyword_like"] = f"%{normalized_keyword}%"
            where_clauses.append(
                """
                (
                    LOWER(COALESCE(r.company_name, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(r.contact_name, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(r.contact_phone, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(r.username, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(s.supplier_name, '')) LIKE :keyword_like
                )
                """
            )
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return self._read_sql(
            f"""
            SELECT
                r.id,
                r.company_name,
                r.contact_name,
                r.contact_phone,
                r.username,
                COALESCE(r.status, 'pending') AS status,
                r.review_notes,
                r.supplier_id,
                r.reviewed_by,
                r.reviewed_at,
                r.created_at,
                r.updated_at,
                s.supplier_name,
                s.market_category,
                s.channel,
                s.is_active AS supplier_is_active
            FROM supplier_registration_requests r
            LEFT JOIN suppliers s ON s.id = r.supplier_id
            {where_sql}
            ORDER BY
                CASE COALESCE(r.status, 'pending')
                    WHEN 'pending' THEN 0
                    WHEN 'approved' THEN 1
                    WHEN 'rejected' THEN 2
                    ELSE 3
                END,
                r.created_at DESC,
                r.id DESC
            """,
            params,
        )

    def get_procurement_registration_requests(
        self,
        status: str | None = None,
        keyword: str | None = None,
    ) -> pd.DataFrame:
        where_clauses: list[str] = []
        params: dict[str, Any] = {}
        normalized_status = str(status or "").strip().lower()
        if normalized_status:
            where_clauses.append("LOWER(COALESCE(r.status, 'pending')) = :status")
            params["status"] = normalized_status
        normalized_keyword = str(keyword or "").strip().lower()
        if normalized_keyword:
            params["keyword_like"] = f"%{normalized_keyword}%"
            where_clauses.append(
                """
                (
                    LOWER(COALESCE(r.company_name, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(r.contact_name, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(r.contact_phone, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(r.username, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(r.market_scope, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(r.requested_supplier_names, '')) LIKE :keyword_like
                    OR LOWER(COALESCE(u.display_name, '')) LIKE :keyword_like
                )
                """
            )
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return self._read_sql(
            f"""
            SELECT
                r.id,
                r.company_name,
                r.contact_name,
                r.contact_phone,
                r.username,
                r.market_scope,
                r.requested_supplier_names,
                COALESCE(r.status, 'pending') AS status,
                r.review_notes,
                r.auth_user_id,
                r.reviewed_by,
                r.reviewed_at,
                r.created_at,
                r.updated_at,
                u.display_name
            FROM procurement_registration_requests r
            LEFT JOIN auth_users u ON u.id = r.auth_user_id
            {where_sql}
            ORDER BY
                CASE COALESCE(r.status, 'pending')
                    WHEN 'pending' THEN 0
                    WHEN 'approved' THEN 1
                    WHEN 'rejected' THEN 2
                    ELSE 3
                END,
                r.created_at DESC,
                r.id DESC
            """,
            params,
        )

    def update_supplier_registration_request(
        self,
        request_id: int,
        *,
        status: str,
        review_notes: str | None = None,
        reviewed_by: str | None = None,
        supplier_id: int | None = None,
    ) -> int | None:
        normalized_status = str(status or "").strip().lower()
        if normalized_status not in {"pending", "approved", "rejected"}:
            raise ValueError("invalid registration status")
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            existing = conn.execute(
                text("SELECT id FROM supplier_registration_requests WHERE id = :request_id"),
                {"request_id": int(request_id)},
            ).mappings().first()
            if existing is None:
                return None
            conn.execute(
                text(
                    """
                    UPDATE supplier_registration_requests
                    SET status = :status,
                        review_notes = :review_notes,
                        supplier_id = :supplier_id,
                        reviewed_by = :reviewed_by,
                        reviewed_at = :reviewed_at,
                        updated_at = :updated_at
                    WHERE id = :request_id
                    """
                ),
                {
                    "request_id": int(request_id),
                    "status": normalized_status,
                    "review_notes": str(review_notes or "").strip() or None,
                    "supplier_id": int(supplier_id) if supplier_id else None,
                    "reviewed_by": str(reviewed_by or "").strip() or None,
                    "reviewed_at": now if normalized_status in {"approved", "rejected"} else None,
                    "updated_at": now,
                },
            )
            return int(request_id)

    def update_procurement_registration_request(
        self,
        request_id: int,
        *,
        status: str,
        review_notes: str | None = None,
        reviewed_by: str | None = None,
        auth_user_id: int | None = None,
    ) -> int | None:
        normalized_status = str(status or "").strip().lower()
        if normalized_status not in {"pending", "approved", "rejected"}:
            raise ValueError("invalid registration status")
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            existing = conn.execute(
                text("SELECT id FROM procurement_registration_requests WHERE id = :request_id"),
                {"request_id": int(request_id)},
            ).mappings().first()
            if existing is None:
                return None
            conn.execute(
                text(
                    """
                    UPDATE procurement_registration_requests
                    SET status = :status,
                        review_notes = :review_notes,
                        auth_user_id = :auth_user_id,
                        reviewed_by = :reviewed_by,
                        reviewed_at = :reviewed_at,
                        updated_at = :updated_at
                    WHERE id = :request_id
                    """
                ),
                {
                    "request_id": int(request_id),
                    "status": normalized_status,
                    "review_notes": str(review_notes or "").strip() or None,
                    "auth_user_id": int(auth_user_id) if auth_user_id else None,
                    "reviewed_by": str(reviewed_by or "").strip() or None,
                    "reviewed_at": now if normalized_status in {"approved", "rejected"} else None,
                    "updated_at": now,
                },
            )
            return int(request_id)

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
            LEFT JOIN supplier_price_records r
                ON r.supplier_id = s.id
               AND COALESCE(r.status, 'active') = 'active'
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
                        remarks, quoted_by, status, updated_at
                    )
                    VALUES (
                        :supplier_id, :price_identity_key, :quoted_at, :price_identity_label,
                        :product_name, :category, :spec_text, :market_category, :channel,
                        :quote_price, :quote_unit, :box_price, :tax_price, :inventory_status,
                        :remarks, :quoted_by, :status, :updated_at
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
                    "status": "active",
                    "updated_at": now,
                },
            )
            return int(result.lastrowid)

    def insert_supplier_quote_action(
        self,
        supplier_id: int,
        action_type: str,
        record_id: int | None = None,
        target_record_id: int | None = None,
        action_reason: str | None = None,
        operator_name: str | None = None,
        action_payload: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> int:
        now = created_at or datetime.utcnow().isoformat()
        payload_text = json.dumps(action_payload, ensure_ascii=False) if action_payload is not None else None
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO supplier_quote_actions (
                        supplier_id, record_id, target_record_id, action_type,
                        action_reason, operator_name, action_payload, created_at
                    )
                    VALUES (
                        :supplier_id, :record_id, :target_record_id, :action_type,
                        :action_reason, :operator_name, :action_payload, :created_at
                    )
                    """
                ),
                {
                    "supplier_id": int(supplier_id),
                    "record_id": int(record_id) if record_id is not None else None,
                    "target_record_id": int(target_record_id) if target_record_id is not None else None,
                    "action_type": str(action_type or "").strip(),
                    "action_reason": action_reason,
                    "operator_name": operator_name,
                    "action_payload": payload_text,
                    "created_at": now,
                },
            )
            return int(result.lastrowid)

    def _normalize_supplier_settlement_record_ids(self, quote_record_ids: list[int] | None) -> list[int]:
        normalized_ids: list[int] = []
        seen: set[int] = set()
        for raw_value in quote_record_ids or []:
            try:
                record_id = int(raw_value)
            except (TypeError, ValueError):
                continue
            if record_id <= 0 or record_id in seen:
                continue
            normalized_ids.append(record_id)
            seen.add(record_id)
        return normalized_ids

    def _parse_supplier_settlement_record_ids(self, raw_value: Any) -> list[int]:
        if isinstance(raw_value, list):
            return self._normalize_supplier_settlement_record_ids(raw_value)
        if raw_value is None:
            return []
        text_value = str(raw_value).strip()
        if not text_value:
            return []
        try:
            parsed = json.loads(text_value)
        except json.JSONDecodeError:
            parsed = [item.strip() for item in text_value.split(",") if item.strip()]
        return self._normalize_supplier_settlement_record_ids(parsed if isinstance(parsed, list) else [])

    def _normalize_supplier_settlement_status(
        self,
        total_amount: float,
        paid_amount: float,
        status: str | None = None,
    ) -> str:
        normalized_status = str(status or "").strip().lower()
        if normalized_status == "cancelled":
            return "cancelled"
        if paid_amount <= 0:
            return "pending"
        if total_amount > 0 and paid_amount >= total_amount:
            return "paid"
        if paid_amount > 0:
            return "partial"
        return normalized_status or "pending"

    def get_supplier_price_records_by_ids(self, supplier_id: int, record_ids: list[int]) -> pd.DataFrame:
        normalized_ids = self._normalize_supplier_settlement_record_ids(record_ids)
        if not normalized_ids:
            return pd.DataFrame()

        statement = text(
            """
            SELECT
                r.id,
                r.supplier_id,
                r.price_identity_key,
                r.price_identity_label,
                r.product_name,
                r.category,
                r.spec_text,
                r.market_category,
                r.channel,
                r.quote_price,
                r.quote_unit,
                r.quoted_at,
                r.remarks,
                COALESCE(r.status, 'active') AS status
            FROM supplier_price_records r
            WHERE r.supplier_id = :supplier_id
              AND r.id IN :record_ids
            ORDER BY r.quoted_at ASC, r.id ASC
            """
        ).bindparams(bindparam("record_ids", expanding=True))
        with self.connect() as conn:
            return pd.read_sql_query(
                statement,
                conn,
                params={"supplier_id": int(supplier_id), "record_ids": normalized_ids},
            )

    def _build_supplier_settlement_filters(
        self,
        supplier_id: int,
        status: str | None = None,
        keyword: str | None = None,
        start_period_start: str | None = None,
        end_period_end: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        where_clauses = ["st.supplier_id = :supplier_id"]
        params: dict[str, Any] = {"supplier_id": int(supplier_id)}

        normalized_status = str(status or "").strip().lower()
        if normalized_status:
            where_clauses.append("LOWER(COALESCE(st.status, 'pending')) = :status")
            params["status"] = normalized_status

        normalized_keyword = str(keyword or "").strip().lower()
        if normalized_keyword:
            where_clauses.append(
                """
                (
                    LOWER(COALESCE(st.settlement_title, '')) LIKE :keyword
                    OR LOWER(COALESCE(st.remarks, '')) LIKE :keyword
                    OR LOWER(COALESCE(st.created_by, '')) LIKE :keyword
                    OR LOWER(COALESCE(s.supplier_name, '')) LIKE :keyword
                )
                """
            )
            params["keyword"] = f"%{normalized_keyword}%"

        normalized_start_period = str(start_period_start or "").strip()
        if normalized_start_period:
            if len(normalized_start_period) == 10:
                normalized_start_period = f"{normalized_start_period}T00:00:00"
            where_clauses.append("COALESCE(st.period_start, st.created_at) >= :start_period_start")
            params["start_period_start"] = normalized_start_period

        normalized_end_period = str(end_period_end or "").strip()
        if normalized_end_period:
            if len(normalized_end_period) == 10:
                normalized_end_period = f"{normalized_end_period}T23:59:59"
            where_clauses.append("COALESCE(st.period_end, st.period_start, st.created_at) <= :end_period_end")
            params["end_period_end"] = normalized_end_period

        return " AND ".join(where_clauses), params

    def count_supplier_settlement_records(
        self,
        supplier_id: int,
        status: str | None = None,
        keyword: str | None = None,
        start_period_start: str | None = None,
        end_period_end: str | None = None,
    ) -> int:
        where_sql, params = self._build_supplier_settlement_filters(
            supplier_id=supplier_id,
            status=status,
            keyword=keyword,
            start_period_start=start_period_start,
            end_period_end=end_period_end,
        )
        with self.connect() as conn:
            result = conn.execute(
                text(
                    f"""
                    SELECT COUNT(*) AS total
                    FROM supplier_settlement_records st
                    JOIN suppliers s ON s.id = st.supplier_id
                    WHERE {where_sql}
                    """
                ),
                params,
            ).mappings().first()
        if not result:
            return 0
        return int(result.get("total") or 0)

    def get_supplier_settlement_record(self, record_id: int) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT
                st.id,
                st.supplier_id,
                s.supplier_name,
                s.contact_name,
                s.contact_phone,
                s.market_scope,
                s.market_category,
                s.channel,
                st.settlement_title,
                st.period_start,
                st.period_end,
                st.quote_record_ids,
                COALESCE(st.record_count, 0) AS record_count,
                COALESCE(st.total_amount, 0) AS total_amount,
                COALESCE(st.paid_amount, 0) AS paid_amount,
                COALESCE(st.pending_amount, 0) AS pending_amount,
                COALESCE(st.status, 'pending') AS status,
                st.payment_due_date,
                st.payment_date,
                st.remarks,
                st.created_by,
                st.created_at,
                st.updated_at
            FROM supplier_settlement_records st
            JOIN suppliers s ON s.id = st.supplier_id
            WHERE st.id = :record_id
            """,
            {"record_id": int(record_id)},
        )

    def get_supplier_settlement_records(
        self,
        supplier_id: int,
        limit: int | None = 20,
        offset: int = 0,
        status: str | None = None,
        keyword: str | None = None,
        start_period_start: str | None = None,
        end_period_end: str | None = None,
    ) -> pd.DataFrame:
        where_sql, params = self._build_supplier_settlement_filters(
            supplier_id=supplier_id,
            status=status,
            keyword=keyword,
            start_period_start=start_period_start,
            end_period_end=end_period_end,
        )
        query = """
        SELECT
            st.id,
            st.supplier_id,
            s.supplier_name,
            s.contact_name,
            s.contact_phone,
            s.market_scope,
            s.market_category,
            s.channel,
            st.settlement_title,
            st.period_start,
            st.period_end,
            st.quote_record_ids,
            COALESCE(st.record_count, 0) AS record_count,
            COALESCE(st.total_amount, 0) AS total_amount,
            COALESCE(st.paid_amount, 0) AS paid_amount,
            COALESCE(st.pending_amount, 0) AS pending_amount,
            COALESCE(st.status, 'pending') AS status,
            st.payment_due_date,
            st.payment_date,
            st.remarks,
            st.created_by,
            st.created_at,
            st.updated_at
        FROM supplier_settlement_records st
        JOIN suppliers s ON s.id = st.supplier_id
        WHERE {where_sql}
        ORDER BY COALESCE(st.period_end, st.created_at) DESC, st.created_at DESC, st.id DESC
        """.format(where_sql=where_sql)
        if limit is not None and limit > 0:
            query += " LIMIT :limit OFFSET :offset"
            params["limit"] = int(limit)
            params["offset"] = max(int(offset), 0)
        return self._read_sql(query, params)

    def insert_supplier_settlement_record(
        self,
        supplier_id: int,
        settlement_title: str,
        period_start: str | None = None,
        period_end: str | None = None,
        quote_record_ids: list[int] | None = None,
        total_amount: float | None = None,
        paid_amount: float | None = None,
        status: str | None = None,
        payment_due_date: str | None = None,
        payment_date: str | None = None,
        remarks: str | None = None,
        created_by: str | None = None,
        created_at: str | None = None,
    ) -> int:
        normalized_title = str(settlement_title or "").strip()
        if not normalized_title:
            raise ValueError("settlement_title is required")

        normalized_record_ids = self._normalize_supplier_settlement_record_ids(quote_record_ids)
        normalized_total_amount = round(max(float(total_amount or 0), 0.0), 2)
        normalized_paid_amount = round(max(float(paid_amount or 0), 0.0), 2)
        normalized_pending_amount = round(max(normalized_total_amount - normalized_paid_amount, 0.0), 2)
        resolved_status = self._normalize_supplier_settlement_status(
            normalized_total_amount,
            normalized_paid_amount,
            status=status,
        )
        now = created_at or datetime.utcnow().isoformat()
        with self.connect() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO supplier_settlement_records (
                        supplier_id, settlement_title, period_start, period_end,
                        quote_record_ids, record_count, total_amount, paid_amount,
                        pending_amount, status, payment_due_date, payment_date,
                        remarks, created_by, created_at, updated_at
                    )
                    VALUES (
                        :supplier_id, :settlement_title, :period_start, :period_end,
                        :quote_record_ids, :record_count, :total_amount, :paid_amount,
                        :pending_amount, :status, :payment_due_date, :payment_date,
                        :remarks, :created_by, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "supplier_id": int(supplier_id),
                    "settlement_title": normalized_title,
                    "period_start": period_start,
                    "period_end": period_end,
                    "quote_record_ids": json.dumps(normalized_record_ids, ensure_ascii=False),
                    "record_count": len(normalized_record_ids),
                    "total_amount": normalized_total_amount,
                    "paid_amount": normalized_paid_amount,
                    "pending_amount": normalized_pending_amount,
                    "status": resolved_status,
                    "payment_due_date": payment_due_date,
                    "payment_date": payment_date,
                    "remarks": remarks,
                    "created_by": str(created_by or "").strip() or None,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            return int(result.lastrowid)

    def update_supplier_settlement_record(
        self,
        record_id: int,
        settlement_title: str | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
        quote_record_ids: list[int] | None = None,
        total_amount: float | None = None,
        paid_amount: float | None = None,
        status: str | None = None,
        payment_due_date: str | None = None,
        payment_date: str | None = None,
        remarks: str | None = None,
    ) -> int | None:
        with self.connect() as conn:
            existing = conn.execute(
                text("SELECT * FROM supplier_settlement_records WHERE id = :record_id"),
                {"record_id": int(record_id)},
            ).mappings().first()
            if not existing:
                return None

            existing_row = dict(existing)
            next_record_ids = (
                self._normalize_supplier_settlement_record_ids(quote_record_ids)
                if quote_record_ids is not None
                else self._parse_supplier_settlement_record_ids(existing_row.get("quote_record_ids"))
            )
            next_title = (
                str(settlement_title).strip()
                if settlement_title is not None
                else str(existing_row.get("settlement_title") or "").strip()
            )
            if not next_title:
                raise ValueError("settlement_title is required")

            next_total_amount = round(
                max(float(existing_row.get("total_amount") if total_amount is None else total_amount or 0), 0.0),
                2,
            )
            next_paid_amount = round(
                max(float(existing_row.get("paid_amount") if paid_amount is None else paid_amount or 0), 0.0),
                2,
            )
            next_pending_amount = round(max(next_total_amount - next_paid_amount, 0.0), 2)
            resolved_status = self._normalize_supplier_settlement_status(
                next_total_amount,
                next_paid_amount,
                status=status if status is not None else str(existing_row.get("status") or "").strip(),
            )
            now = datetime.utcnow().isoformat()
            conn.execute(
                text(
                    """
                    UPDATE supplier_settlement_records
                    SET settlement_title = :settlement_title,
                        period_start = :period_start,
                        period_end = :period_end,
                        quote_record_ids = :quote_record_ids,
                        record_count = :record_count,
                        total_amount = :total_amount,
                        paid_amount = :paid_amount,
                        pending_amount = :pending_amount,
                        status = :status,
                        payment_due_date = :payment_due_date,
                        payment_date = :payment_date,
                        remarks = :remarks,
                        updated_at = :updated_at
                    WHERE id = :record_id
                    """
                ),
                {
                    "record_id": int(record_id),
                    "settlement_title": next_title,
                    "period_start": existing_row.get("period_start") if period_start is None else period_start,
                    "period_end": existing_row.get("period_end") if period_end is None else period_end,
                    "quote_record_ids": json.dumps(next_record_ids, ensure_ascii=False),
                    "record_count": len(next_record_ids),
                    "total_amount": next_total_amount,
                    "paid_amount": next_paid_amount,
                    "pending_amount": next_pending_amount,
                    "status": resolved_status,
                    "payment_due_date": existing_row.get("payment_due_date") if payment_due_date is None else payment_due_date,
                    "payment_date": existing_row.get("payment_date") if payment_date is None else payment_date,
                    "remarks": existing_row.get("remarks") if remarks is None else remarks,
                    "updated_at": now,
                },
            )
            return int(existing_row["id"])

    def build_supplier_settlement_from_quotes(
        self,
        supplier_id: int,
        settlement_title: str,
        quote_record_ids: list[int],
        payment_due_date: str | None = None,
        remarks: str | None = None,
        created_by: str | None = None,
        paid_amount: float | None = None,
    ) -> int:
        normalized_record_ids = self._normalize_supplier_settlement_record_ids(quote_record_ids)
        if not normalized_record_ids:
            raise ValueError("quote_record_ids is required")

        quote_rows = self.get_supplier_price_records_by_ids(supplier_id, normalized_record_ids)
        if quote_rows.empty or len(quote_rows) != len(normalized_record_ids):
            raise ValueError("未找到全部报价记录")

        total_amount = round(
            sum(float(value) for value in quote_rows["quote_price"].tolist() if pd.notna(value)),
            2,
        )
        period_start = str(quote_rows["quoted_at"].iloc[0] or "").strip() or None
        period_end = str(quote_rows["quoted_at"].iloc[-1] or "").strip() or None
        return self.insert_supplier_settlement_record(
            supplier_id=supplier_id,
            settlement_title=settlement_title,
            period_start=period_start,
            period_end=period_end,
            quote_record_ids=normalized_record_ids,
            total_amount=total_amount,
            paid_amount=paid_amount,
            payment_due_date=payment_due_date,
            remarks=remarks,
            created_by=created_by,
        )

    def insert_procurement_plan_record(
        self,
        *,
        plan_title: str,
        menu_text: str | None,
        diners: int,
        tables: int,
        preferred_province: str | None = None,
        preferred_city: str | None = None,
        preferred_location: str | None = None,
        ingredient_items: list[dict[str, Any]] | None = None,
        procurement_plan: list[dict[str, Any]] | None = None,
        total_cost: float | None = None,
        created_by_user_id: int | None = None,
        created_by: str | None = None,
    ) -> int:
        normalized_title = str(plan_title or "").strip()
        if not normalized_title:
            raise ValueError("plan_title is required")
        ingredient_rows = list(ingredient_items or [])
        plan_rows = list(procurement_plan or [])
        matched_count = sum(1 for row in plan_rows if str(row.get("price_status") or "") == "已匹配报价")
        pending_count = sum(1 for row in plan_rows if str(row.get("price_status") or "") != "已匹配报价")
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            record_id = conn.execute(
                text(
                    """
                    INSERT INTO procurement_plan_records (
                        plan_title, menu_text, diners, tables,
                        preferred_province, preferred_city, preferred_location,
                        ingredient_items, procurement_plan,
                        row_count, matched_count, pending_count, total_cost,
                        created_by_user_id, created_by, created_at, updated_at
                    ) VALUES (
                        :plan_title, :menu_text, :diners, :tables,
                        :preferred_province, :preferred_city, :preferred_location,
                        :ingredient_items, :procurement_plan,
                        :row_count, :matched_count, :pending_count, :total_cost,
                        :created_by_user_id, :created_by, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "plan_title": normalized_title,
                    "menu_text": str(menu_text or "").strip(),
                    "diners": int(diners or 0),
                    "tables": int(tables or 0),
                    "preferred_province": preferred_province,
                    "preferred_city": preferred_city,
                    "preferred_location": preferred_location,
                    "ingredient_items": json.dumps(ingredient_rows, ensure_ascii=False, default=str),
                    "procurement_plan": json.dumps(plan_rows, ensure_ascii=False, default=str),
                    "row_count": len(plan_rows),
                    "matched_count": matched_count,
                    "pending_count": pending_count,
                    "total_cost": total_cost,
                    "created_by_user_id": int(created_by_user_id) if created_by_user_id is not None else None,
                    "created_by": created_by,
                    "created_at": now,
                    "updated_at": now,
                },
            ).lastrowid
            return int(record_id)

    def get_procurement_plan_records(
        self,
        *,
        created_by_user_id: int | None = None,
        limit: int = 12,
        offset: int = 0,
    ) -> pd.DataFrame:
        conditions = []
        params: dict[str, Any] = {
            "limit": int(limit),
            "offset": int(offset),
        }
        if created_by_user_id is not None:
            conditions.append("created_by_user_id = :created_by_user_id")
            params["created_by_user_id"] = int(created_by_user_id)
        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return self._read_sql(
            f"""
            SELECT *
            FROM procurement_plan_records
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )

    def get_procurement_plan_record(self, record_id: int) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT *
            FROM procurement_plan_records
            WHERE id = :record_id
            """,
            {"record_id": int(record_id)},
        )

    def insert_settings_change_record(
        self,
        *,
        action_type: str,
        target_name: str,
        summary: str,
        actor_user_id: int | None = None,
        actor_name: str | None = None,
        change_payload: dict[str, Any] | None = None,
    ) -> int:
        normalized_action = str(action_type or "").strip()
        normalized_target = str(target_name or "").strip()
        normalized_summary = str(summary or "").strip()
        if not normalized_action:
            raise ValueError("action_type is required")
        if not normalized_target:
            raise ValueError("target_name is required")
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            record_id = conn.execute(
                text(
                    """
                    INSERT INTO settings_change_records (
                        action_type, target_name, summary,
                        actor_user_id, actor_name, change_payload, created_at
                    ) VALUES (
                        :action_type, :target_name, :summary,
                        :actor_user_id, :actor_name, :change_payload, :created_at
                    )
                    """
                ),
                {
                    "action_type": normalized_action,
                    "target_name": normalized_target,
                    "summary": normalized_summary,
                    "actor_user_id": int(actor_user_id) if actor_user_id is not None else None,
                    "actor_name": actor_name,
                    "change_payload": json.dumps(change_payload or {}, ensure_ascii=False, default=str),
                    "created_at": now,
                },
            ).lastrowid
            return int(record_id)

    def get_settings_change_records(self, limit: int = 12, offset: int = 0) -> pd.DataFrame:
        return self._read_sql(
            """
            SELECT *
            FROM settings_change_records
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """,
            {
                "limit": int(limit),
                "offset": int(offset),
            },
        )

    def invalidate_supplier_price_record(self, record_id: int, reason: str | None = None) -> int | None:
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            existing = conn.execute(
                text(
                    """
                    SELECT id, status, invalidated_at, invalidated_reason
                    FROM supplier_price_records
                    WHERE id = :record_id
                    """
                ),
                {"record_id": int(record_id)},
            ).mappings().first()
            if not existing:
                return None

            current_status = str(existing.get("status") or "active").strip() or "active"
            invalidated_at = existing.get("invalidated_at") or now
            if current_status == "invalidated":
                next_reason = reason if reason is not None else existing.get("invalidated_reason")
                conn.execute(
                    text(
                        """
                        UPDATE supplier_price_records
                        SET invalidated_reason = :invalidated_reason,
                            updated_at = :updated_at
                        WHERE id = :record_id
                        """
                    ),
                    {
                        "record_id": int(record_id),
                        "invalidated_reason": next_reason,
                        "updated_at": now,
                    },
                )
                return int(existing["id"])

            conn.execute(
                text(
                    """
                    UPDATE supplier_price_records
                    SET status = 'invalidated',
                        invalidated_at = :invalidated_at,
                        invalidated_reason = :invalidated_reason,
                        updated_at = :updated_at
                    WHERE id = :record_id
                    """
                ),
                {
                    "record_id": int(record_id),
                    "invalidated_at": invalidated_at,
                    "invalidated_reason": reason,
                    "updated_at": now,
                },
            )
            return int(existing["id"])

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
                COALESCE(r.status, 'active') AS status,
                r.invalidated_at,
                r.invalidated_reason,
                r.quoted_at,
                r.updated_at
            FROM supplier_price_records r
            JOIN suppliers s ON s.id = r.supplier_id
            WHERE r.id = :record_id
            """,
            {"record_id": int(record_id)},
        )

    def get_latest_supplier_quote_for_supplier(
        self,
        supplier_id: int,
        price_identity_key: str | None = None,
        price_identity_keys: list[str] | None = None,
    ) -> pd.DataFrame:
        normalized_keys = [
            str(item or "").strip()
            for item in (price_identity_keys or ([price_identity_key] if price_identity_key is not None else []))
            if str(item or "").strip()
        ]
        if not normalized_keys:
            return pd.DataFrame()

        query = text(
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
                COALESCE(r.status, 'active') AS status,
                r.invalidated_at,
                r.invalidated_reason,
                r.quoted_at,
                r.updated_at
            FROM supplier_price_records r
            JOIN suppliers s ON s.id = r.supplier_id
            WHERE r.supplier_id = :supplier_id
              AND r.price_identity_key IN :price_identity_keys
              AND COALESCE(r.status, 'active') = 'active'
            ORDER BY r.quoted_at DESC, r.id DESC
            LIMIT 1
            """
        ).bindparams(bindparam("price_identity_keys", expanding=True))
        return self._read_sql(
            query,
            {
                "supplier_id": int(supplier_id),
                "price_identity_keys": normalized_keys,
            },
        )

    def invalidate_supplier_quotes_by_identity(
        self,
        supplier_id: int,
        price_identity_key: str | None = None,
        reason: str | None = None,
        price_identity_keys: list[str] | None = None,
    ) -> list[int]:
        normalized_keys = [
            str(item or "").strip()
            for item in (price_identity_keys or ([price_identity_key] if price_identity_key is not None else []))
            if str(item or "").strip()
        ]
        if not normalized_keys:
            return []

        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id
                    FROM supplier_price_records
                    WHERE supplier_id = :supplier_id
                      AND price_identity_key IN :price_identity_keys
                      AND COALESCE(status, 'active') = 'active'
                    ORDER BY quoted_at DESC, id DESC
                    """
                ).bindparams(bindparam("price_identity_keys", expanding=True)),
                {
                    "supplier_id": int(supplier_id),
                    "price_identity_keys": normalized_keys,
                },
            ).mappings().all()
            record_ids = [int(row["id"]) for row in rows]
            if not record_ids:
                return []

            conn.execute(
                text(
                    """
                    UPDATE supplier_price_records
                    SET status = 'invalidated',
                        invalidated_at = :invalidated_at,
                        invalidated_reason = :invalidated_reason,
                        updated_at = :updated_at
                    WHERE supplier_id = :supplier_id
                      AND price_identity_key IN :price_identity_keys
                      AND COALESCE(status, 'active') = 'active'
                    """
                ).bindparams(bindparam("price_identity_keys", expanding=True)),
                {
                    "supplier_id": int(supplier_id),
                    "price_identity_keys": normalized_keys,
                    "invalidated_at": now,
                    "invalidated_reason": reason,
                    "updated_at": now,
                },
            )
            return record_ids

    def get_latest_supplier_quotes(
        self,
        price_identity_key: str | None = None,
        price_identity_keys: list[str] | None = None,
    ) -> pd.DataFrame:
        normalized_keys = [
            str(item or "").strip()
            for item in (price_identity_keys or ([price_identity_key] if price_identity_key is not None else []))
            if str(item or "").strip()
        ]
        if not normalized_keys:
            return pd.DataFrame()

        query = text(
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
                COALESCE(r.status, 'active') AS status,
                r.invalidated_at,
                r.invalidated_reason,
                r.quoted_at,
                r.updated_at
            FROM suppliers s
            JOIN supplier_price_records r
                ON r.id = (
                    SELECT sr2.id
                    FROM supplier_price_records sr2
                    WHERE sr2.supplier_id = s.id
                      AND sr2.price_identity_key IN :price_identity_keys
                      AND COALESCE(sr2.status, 'active') = 'active'
                    ORDER BY sr2.quoted_at DESC, sr2.id DESC
                    LIMIT 1
                )
            WHERE COALESCE(s.is_active, 0) = 1
            ORDER BY
                CASE WHEN r.quote_price IS NULL THEN 1 ELSE 0 END,
                r.quote_price ASC,
                r.quoted_at DESC,
                s.supplier_name ASC
            """
        ).bindparams(bindparam("price_identity_keys", expanding=True))
        return self._read_sql(
            query,
            {"price_identity_keys": normalized_keys},
        )

    def _build_supplier_quote_record_filters(
        self,
        supplier_id: int,
        status: str | None = None,
        keyword: str | None = None,
        start_quoted_at: str | None = None,
        end_quoted_at: str | None = None,
        price_identity_key: str | None = None,
        price_identity_keys: list[str] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        where_clauses = ["r.supplier_id = :supplier_id"]
        params: dict[str, Any] = {"supplier_id": int(supplier_id)}

        normalized_status = str(status or "").strip()
        if normalized_status:
            where_clauses.append("COALESCE(r.status, 'active') = :status")
            params["status"] = normalized_status

        normalized_keyword = str(keyword or "").strip().lower()
        if normalized_keyword:
            where_clauses.append(
                """
                (
                    LOWER(COALESCE(r.product_name, '')) LIKE :keyword
                    OR LOWER(COALESCE(r.price_identity_label, '')) LIKE :keyword
                    OR LOWER(COALESCE(r.price_identity_key, '')) LIKE :keyword
                    OR LOWER(COALESCE(r.spec_text, '')) LIKE :keyword
                    OR LOWER(COALESCE(r.market_category, '')) LIKE :keyword
                    OR LOWER(COALESCE(r.quote_unit, '')) LIKE :keyword
                    OR LOWER(COALESCE(r.remarks, '')) LIKE :keyword
                    OR LOWER(COALESCE(r.invalidated_reason, '')) LIKE :keyword
                    OR LOWER(COALESCE(r.channel, '')) LIKE :keyword
                )
                """
            )
            params["keyword"] = f"%{normalized_keyword}%"

        normalized_start = str(start_quoted_at or "").strip()
        if normalized_start:
            where_clauses.append("r.quoted_at >= :start_quoted_at")
            params["start_quoted_at"] = normalized_start

        normalized_end = str(end_quoted_at or "").strip()
        if normalized_end:
            where_clauses.append("r.quoted_at <= :end_quoted_at")
            params["end_quoted_at"] = normalized_end

        normalized_identity_keys = [
            str(item or "").strip()
            for item in (price_identity_keys or ([price_identity_key] if price_identity_key is not None else []))
            if str(item or "").strip()
        ]
        if normalized_identity_keys:
            where_clauses.append("r.price_identity_key IN :price_identity_keys")
            params["price_identity_keys"] = normalized_identity_keys

        return " AND ".join(where_clauses), params

    def _build_supplier_quote_action_filters(
        self,
        supplier_id: int,
        action_type: str | None = None,
        operator_name: str | None = None,
        keyword: str | None = None,
        start_created_at: str | None = None,
        end_created_at: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        where_clauses = ["a.supplier_id = :supplier_id"]
        params: dict[str, Any] = {"supplier_id": int(supplier_id)}

        normalized_action_type = str(action_type or "").strip()
        if normalized_action_type:
            where_clauses.append("a.action_type = :action_type")
            params["action_type"] = normalized_action_type

        normalized_operator_name = str(operator_name or "").strip().lower()
        if normalized_operator_name:
            where_clauses.append("LOWER(COALESCE(a.operator_name, '')) LIKE :operator_name")
            params["operator_name"] = f"%{normalized_operator_name}%"

        normalized_keyword = str(keyword or "").strip().lower()
        if normalized_keyword:
            where_clauses.append(
                """
                (
                    LOWER(COALESCE(a.action_type, '')) LIKE :keyword
                    OR LOWER(COALESCE(a.action_reason, '')) LIKE :keyword
                    OR LOWER(COALESCE(a.operator_name, '')) LIKE :keyword
                    OR LOWER(COALESCE(a.action_payload, '')) LIKE :keyword
                    OR LOWER(COALESCE(src.price_identity_key, '')) LIKE :keyword
                    OR LOWER(COALESCE(src.price_identity_label, '')) LIKE :keyword
                    OR LOWER(COALESCE(src.product_name, '')) LIKE :keyword
                    OR LOWER(COALESCE(target.price_identity_label, '')) LIKE :keyword
                    OR LOWER(COALESCE(target.product_name, '')) LIKE :keyword
                )
                """
            )
            params["keyword"] = f"%{normalized_keyword}%"

        normalized_start = str(start_created_at or "").strip()
        if normalized_start:
            where_clauses.append("a.created_at >= :start_created_at")
            params["start_created_at"] = normalized_start

        normalized_end = str(end_created_at or "").strip()
        if normalized_end:
            where_clauses.append("a.created_at <= :end_created_at")
            params["end_created_at"] = normalized_end

        return " AND ".join(where_clauses), params

    def count_supplier_quote_records(
        self,
        supplier_id: int,
        status: str | None = None,
        keyword: str | None = None,
        start_quoted_at: str | None = None,
        end_quoted_at: str | None = None,
        price_identity_key: str | None = None,
        price_identity_keys: list[str] | None = None,
    ) -> int:
        where_sql, params = self._build_supplier_quote_record_filters(
            supplier_id=supplier_id,
            status=status,
            keyword=keyword,
            start_quoted_at=start_quoted_at,
            end_quoted_at=end_quoted_at,
            price_identity_key=price_identity_key,
            price_identity_keys=price_identity_keys,
        )
        query = text(
            f"""
            SELECT COUNT(*) AS total
            FROM supplier_price_records r
            WHERE {where_sql}
            """
        )
        if "price_identity_keys" in params:
            query = query.bindparams(bindparam("price_identity_keys", expanding=True))
        with self.connect() as conn:
            result = conn.execute(
                query,
                params,
            ).mappings().first()
        if not result:
            return 0
        return int(result.get("total") or 0)

    def get_supplier_quote_records(
        self,
        supplier_id: int,
        limit: int | None = 20,
        offset: int = 0,
        status: str | None = None,
        keyword: str | None = None,
        start_quoted_at: str | None = None,
        end_quoted_at: str | None = None,
        price_identity_key: str | None = None,
        price_identity_keys: list[str] | None = None,
    ) -> pd.DataFrame:
        where_sql, params = self._build_supplier_quote_record_filters(
            supplier_id=supplier_id,
            status=status,
            keyword=keyword,
            start_quoted_at=start_quoted_at,
            end_quoted_at=end_quoted_at,
            price_identity_key=price_identity_key,
            price_identity_keys=price_identity_keys,
        )
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
            COALESCE(r.status, 'active') AS status,
            r.invalidated_at,
            r.invalidated_reason,
            r.quoted_at,
            r.updated_at
        FROM supplier_price_records r
        JOIN suppliers s ON s.id = r.supplier_id
        WHERE {where_sql}
        ORDER BY r.quoted_at DESC, r.id DESC
        """.format(where_sql=where_sql)
        if limit is not None and limit > 0:
            query += " LIMIT :limit OFFSET :offset"
            params["limit"] = int(limit)
            params["offset"] = max(int(offset), 0)
        if "price_identity_keys" in params:
            return self._read_sql(text(query).bindparams(bindparam("price_identity_keys", expanding=True)), params)
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
            COALESCE(r.status, 'active') AS status,
            r.invalidated_at,
            r.invalidated_reason,
            r.quoted_at,
            r.updated_at
        FROM supplier_price_records r
        JOIN suppliers s ON s.id = r.supplier_id
        WHERE COALESCE(r.status, 'active') = 'active'
        ORDER BY r.quoted_at DESC, r.id DESC
        """
        if limit is not None and limit > 0:
            query += " LIMIT :limit"
            return self._read_sql(query, {"limit": int(limit)})
        return self._read_sql(query)

    def count_supplier_quote_actions(
        self,
        supplier_id: int,
        action_type: str | None = None,
        operator_name: str | None = None,
        keyword: str | None = None,
        start_created_at: str | None = None,
        end_created_at: str | None = None,
    ) -> int:
        where_sql, params = self._build_supplier_quote_action_filters(
            supplier_id=supplier_id,
            action_type=action_type,
            operator_name=operator_name,
            keyword=keyword,
            start_created_at=start_created_at,
            end_created_at=end_created_at,
        )
        with self.connect() as conn:
            result = conn.execute(
                text(
                    f"""
                    SELECT COUNT(*) AS total
                    FROM supplier_quote_actions a
                    LEFT JOIN supplier_price_records src ON src.id = a.record_id
                    LEFT JOIN supplier_price_records target ON target.id = a.target_record_id
                    WHERE {where_sql}
                    """
                ),
                params,
            ).mappings().first()
        if not result:
            return 0
        return int(result.get("total") or 0)

    def get_supplier_quote_actions(
        self,
        supplier_id: int,
        limit: int | None = 20,
        offset: int = 0,
        action_type: str | None = None,
        operator_name: str | None = None,
        keyword: str | None = None,
        start_created_at: str | None = None,
        end_created_at: str | None = None,
    ) -> pd.DataFrame:
        where_sql, params = self._build_supplier_quote_action_filters(
            supplier_id=supplier_id,
            action_type=action_type,
            operator_name=operator_name,
            keyword=keyword,
            start_created_at=start_created_at,
            end_created_at=end_created_at,
        )
        query = """
        SELECT
            a.id,
            a.supplier_id,
            s.supplier_name,
            a.record_id,
            a.target_record_id,
            a.action_type,
            a.action_reason,
            a.operator_name,
            a.action_payload,
            a.created_at,
            src.price_identity_key,
            src.price_identity_label,
            src.product_name,
            src.quote_price,
            src.quote_unit,
            src.quoted_at,
            target.price_identity_label AS target_price_identity_label,
            target.product_name AS target_product_name,
            target.quote_price AS target_quote_price,
            target.quoted_at AS target_quoted_at
        FROM supplier_quote_actions a
        JOIN suppliers s ON s.id = a.supplier_id
        LEFT JOIN supplier_price_records src ON src.id = a.record_id
        LEFT JOIN supplier_price_records target ON target.id = a.target_record_id
        WHERE {where_sql}
        ORDER BY a.created_at DESC, a.id DESC
        """.format(where_sql=where_sql)
        if limit is not None and limit > 0:
            query += " LIMIT :limit OFFSET :offset"
            params["limit"] = int(limit)
            params["offset"] = max(int(offset), 0)
        return self._read_sql(query, params)

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
