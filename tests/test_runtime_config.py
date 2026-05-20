from pathlib import Path

from utils.config_loader import load_database_config, load_runtime_config, merge_dict, save_runtime_config


DB_ENV_KEYS = (
    "BATTEL_DB_BACKEND",
    "BATTEL_SQLITE_PATH",
    "BATTEL_DB_HOST",
    "BATTEL_DB_PORT",
    "BATTEL_DB_USER",
    "BATTEL_DB_NAME",
    "BATTEL_DB_CHARSET",
    "BATTEL_DB_PASSWORD_ENV",
    "BATTEL_DB_PASSWORD",
)


def _clear_database_env(monkeypatch):
    for key in DB_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)



def test_load_runtime_config_returns_defaults_for_missing_file(tmp_path: Path):
    config = load_runtime_config(tmp_path / "missing-runtime.json")
    assert config["schedule"]["interval_seconds"] == 3600
    assert config["crawler"]["default_timeout"] == 15
    assert config["crawler"]["blocked_status_codes"] == [403, 429]
    assert config["crawler"]["fallback_to_playwright"] is False
    assert config["crawler"]["auto_learn_site_rules"] is True
    assert config["crawler"]["enable_api_discovery"] is False
    assert config["crawler"]["api_timeout"] == 15
    assert config["crawler"]["api_retries"] == 1
    assert config["crawler"]["public_source_max_workers"] == 1
    assert config["crawler"]["playwright_block_resource_types"] == ["image", "media", "font"]
    assert config["ai"]["enabled"] is False
    assert config["ai"]["provider"] == "qwen"
    assert config["ai"]["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert config["ai"]["model"] == "qwen-plus"
    assert config["ai"]["api_key_env"] == "DASHSCOPE_API_KEY"
    assert config["ai"]["timeout_seconds"] == 20
    assert config["ai"]["max_rows_per_run"] == 20
    assert config["ai"]["batch_size"] == 5



def test_save_runtime_config_merges_defaults(tmp_path: Path):
    target = tmp_path / "runtime.json"
    save_runtime_config({"schedule": {"fetch_mode": "playwright"}, "ai": {"enabled": True, "batch_size": 3}}, target)
    config = load_runtime_config(target)
    assert config["schedule"]["fetch_mode"] == "playwright"
    assert config["schedule"]["interval_seconds"] == 3600
    assert config["crawler"]["fallback_to_playwright"] is False
    assert config["crawler"]["auto_learn_site_rules"] is True
    assert config["crawler"]["enable_api_discovery"] is False
    assert config["crawler"]["public_source_max_workers"] == 1
    assert config["ai"]["enabled"] is True
    assert config["ai"]["batch_size"] == 3
    assert config["ai"]["model"] == "qwen-plus"
    assert config["ai"]["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert config["ai"]["timeout_seconds"] == 20



def test_merge_dict_keeps_nested_defaults():
    result = merge_dict(
        {"schedule": {"enabled": False, "interval_seconds": 3600}},
        {"schedule": {"enabled": True}},
    )
    assert result == {"schedule": {"enabled": True, "interval_seconds": 3600}}


def test_load_database_config_defaults_to_sqlite(monkeypatch, tmp_path: Path):
    _clear_database_env(monkeypatch)

    config = load_database_config(tmp_path / "missing-runtime.json")

    assert config["backend"] == "sqlite"
    assert config["sqlite_path"] == "data/price_tracker.db"
    assert config["mysql"]["port"] == 3306
    assert config["mysql"]["password_env"] == "BATTEL_DB_PASSWORD"


def test_load_database_config_prefers_env(monkeypatch, tmp_path: Path):
    _clear_database_env(monkeypatch)
    target = tmp_path / "runtime.json"
    save_runtime_config(
        {
            "database": {
                "backend": "mysql",
                "mysql": {
                    "host": "runtime-host",
                    "port": 3307,
                    "user": "runtime-user",
                    "database": "runtime-db",
                    "password_env": "CUSTOM_DB_PASSWORD",
                }
            }
        },
        target,
    )
    monkeypatch.setenv("BATTEL_DB_HOST", "env-host")
    monkeypatch.setenv("BATTEL_DB_PORT", "3310")
    monkeypatch.setenv("BATTEL_DB_USER", "env-user")
    monkeypatch.setenv("BATTEL_DB_NAME", "env-db")
    monkeypatch.setenv("CUSTOM_DB_PASSWORD", "secret")

    config = load_database_config(target)

    assert config["backend"] == "mysql"
    assert config["mysql"]["host"] == "env-host"
    assert config["mysql"]["port"] == 3310
    assert config["mysql"]["user"] == "env-user"
    assert config["mysql"]["database"] == "env-db"
    assert config["mysql"]["password"] == "secret"
