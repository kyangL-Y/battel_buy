from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


def _resolve_base_dir() -> Path:
    override_dir = os.environ.get("BATTEL_APP_BASE_DIR")
    if override_dir:
        return Path(override_dir).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _resolve_base_dir()

DEFAULT_RUNTIME_CONFIG: dict[str, Any] = {
    "database": {
        "backend": "sqlite",
        "sqlite_path": "data/price_tracker.db",
        "mysql": {
            "host": "",
            "port": 3306,
            "user": "",
            "database": "",
            "charset": "utf8mb4",
            "password_env": "BATTEL_DB_PASSWORD",
        },
    },
    "schedule": {
        "enabled": False,
        "interval_seconds": 3600,
        "fetch_mode": "requests",
        "target_scope": "all_saved",
    },
    "crawler": {
        "default_timeout": 15,
        "default_retries": 2,
        "default_delay": 1.0,
        "fallback_to_playwright": False,
        "blocked_status_codes": [403, 429],
        "auto_learn_site_rules": True,
        "enable_api_discovery": False,
        "api_timeout": 15,
        "api_retries": 1,
        "public_source_max_workers": 1,
        "playwright_block_resource_types": ["image", "media", "font"],
    },
    "ai": {
        "enabled": False,
        "provider": "qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "api_key_env": "DASHSCOPE_API_KEY",
        "timeout_seconds": 20,
        "max_rows_per_run": 20,
        "batch_size": 5,
    },
}


def resolve_config_path(path: str | Path) -> Path:
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = BASE_DIR / config_path
    return config_path


def load_json_config(path: str | Path) -> Any:
    config_path = resolve_config_path(path)
    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json_config(path: str | Path, data: Any) -> Path:
    config_path = resolve_config_path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    return config_path


def merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_runtime_config(path: str | Path = "config/runtime.json") -> dict[str, Any]:
    config_path = resolve_config_path(path)
    if not config_path.exists():
        return deepcopy(DEFAULT_RUNTIME_CONFIG)
    loaded = load_json_config(config_path)
    if not isinstance(loaded, dict):
        return deepcopy(DEFAULT_RUNTIME_CONFIG)
    return merge_dict(DEFAULT_RUNTIME_CONFIG, loaded)


def save_runtime_config(data: dict[str, Any], path: str | Path = "config/runtime.json") -> Path:
    normalized = merge_dict(DEFAULT_RUNTIME_CONFIG, data)
    return save_json_config(path, normalized)


def load_database_config(path: str | Path = "config/runtime.json") -> dict[str, Any]:
    runtime_config = load_runtime_config(path)
    database_config = runtime_config.get("database", {})
    if not isinstance(database_config, dict):
        database_config = {}

    merged = merge_dict(DEFAULT_RUNTIME_CONFIG["database"], database_config)
    backend = str(os.environ.get("BATTEL_DB_BACKEND") or merged.get("backend") or "sqlite").strip().lower()
    merged["backend"] = backend

    sqlite_path = os.environ.get("BATTEL_SQLITE_PATH")
    if sqlite_path:
        merged["sqlite_path"] = sqlite_path

    mysql_config = dict(merged.get("mysql", {}))
    mysql_config["host"] = os.environ.get("BATTEL_DB_HOST") or mysql_config.get("host", "")
    mysql_config["port"] = int(os.environ.get("BATTEL_DB_PORT") or mysql_config.get("port") or 3306)
    mysql_config["user"] = os.environ.get("BATTEL_DB_USER") or mysql_config.get("user", "")
    mysql_config["database"] = os.environ.get("BATTEL_DB_NAME") or mysql_config.get("database", "")
    mysql_config["charset"] = os.environ.get("BATTEL_DB_CHARSET") or mysql_config.get("charset", "utf8mb4")
    mysql_config["password_env"] = os.environ.get("BATTEL_DB_PASSWORD_ENV") or mysql_config.get(
        "password_env",
        "BATTEL_DB_PASSWORD",
    )
    password_value = os.environ.get("BATTEL_DB_PASSWORD")
    if password_value is not None:
        mysql_config["password"] = password_value
    else:
        password_env = str(mysql_config.get("password_env") or "BATTEL_DB_PASSWORD")
        mysql_config["password"] = os.environ.get(password_env, "")

    merged["mysql"] = mysql_config
    return merged
