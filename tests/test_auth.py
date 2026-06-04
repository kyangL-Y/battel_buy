import pytest

import utils.auth as auth


def _set_auth_environment(monkeypatch, *, environment: str | None, auth_secret: str | None, admin_password: str | None) -> None:
    if environment is None:
        monkeypatch.delenv("BATTEL_ENV", raising=False)
    else:
        monkeypatch.setenv("BATTEL_ENV", environment)

    if auth_secret is None:
        monkeypatch.delenv("BATTEL_AUTH_SECRET", raising=False)
    else:
        monkeypatch.setenv("BATTEL_AUTH_SECRET", auth_secret)

    if admin_password is None:
        monkeypatch.delenv("BATTEL_DEFAULT_ADMIN_PASSWORD", raising=False)
    else:
        monkeypatch.setenv("BATTEL_DEFAULT_ADMIN_PASSWORD", admin_password)


def test_auth_allows_development_defaults(monkeypatch):
    _set_auth_environment(
        monkeypatch,
        environment=None,
        auth_secret=None,
        admin_password=None,
    )

    assert auth._load_auth_secret() == auth.DEFAULT_DEV_AUTH_SECRET
    assert auth._load_default_admin_password() == auth.DEFAULT_DEV_ADMIN_PASSWORD


def test_auth_rejects_default_secret_in_production(monkeypatch):
    _set_auth_environment(
        monkeypatch,
        environment="production",
        auth_secret=None,
        admin_password="prod-admin-password",
    )

    with pytest.raises(RuntimeError, match="BATTEL_AUTH_SECRET"):
        auth._load_auth_secret()


def test_auth_rejects_short_secret_in_production(monkeypatch):
    _set_auth_environment(
        monkeypatch,
        environment="production",
        auth_secret="short-secret",
        admin_password="prod-admin-password",
    )

    with pytest.raises(RuntimeError, match="at least 32"):
        auth._load_auth_secret()


def test_auth_rejects_default_admin_password_in_production(monkeypatch):
    _set_auth_environment(
        monkeypatch,
        environment="production",
        auth_secret="x" * 32,
        admin_password=None,
    )

    with pytest.raises(RuntimeError, match="BATTEL_DEFAULT_ADMIN_PASSWORD"):
        auth._load_default_admin_password()


def test_auth_accepts_hardened_production_configuration(monkeypatch):
    _set_auth_environment(
        monkeypatch,
        environment="production",
        auth_secret="x" * 32,
        admin_password="prod-admin-password",
    )

    assert auth._load_auth_secret() == "x" * 32
    assert auth._load_default_admin_password() == "prod-admin-password"
