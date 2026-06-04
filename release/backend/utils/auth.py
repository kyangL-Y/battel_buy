from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt


AUTH_ALGORITHM = "HS256"
AUTH_ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("BATTEL_AUTH_ACCESS_TOKEN_EXPIRE_SECONDS", "28800"))
DEFAULT_DEV_AUTH_SECRET = "battel-dev-secret-change-me-please-override-32"
MIN_AUTH_SECRET_LENGTH = 32
PRODUCTION_ENVIRONMENT_NAMES = {"prod", "production", "staging"}
DEFAULT_ADMIN_USERNAME = os.getenv("BATTEL_DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_DEV_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_DISPLAY_NAME = os.getenv("BATTEL_DEFAULT_ADMIN_DISPLAY_NAME", "系统管理员")
PBKDF2_ITERATIONS = int(os.getenv("BATTEL_AUTH_PBKDF2_ITERATIONS", "390000"))
MIN_PASSWORD_LENGTH = 8


def _is_production_environment() -> bool:
    return os.getenv("BATTEL_ENV", "").strip().lower() in PRODUCTION_ENVIRONMENT_NAMES


def _load_auth_secret() -> str:
    auth_secret = os.getenv("BATTEL_AUTH_SECRET", DEFAULT_DEV_AUTH_SECRET)
    if not _is_production_environment():
        return auth_secret
    if auth_secret == DEFAULT_DEV_AUTH_SECRET:
        raise RuntimeError("BATTEL_AUTH_SECRET must be set when BATTEL_ENV is production or staging")
    if len(auth_secret) < MIN_AUTH_SECRET_LENGTH:
        raise RuntimeError(f"BATTEL_AUTH_SECRET must be at least {MIN_AUTH_SECRET_LENGTH} characters")
    return auth_secret


def _load_default_admin_password() -> str:
    default_admin_password = os.getenv("BATTEL_DEFAULT_ADMIN_PASSWORD", DEFAULT_DEV_ADMIN_PASSWORD)
    if _is_production_environment() and default_admin_password == DEFAULT_DEV_ADMIN_PASSWORD:
        raise RuntimeError("BATTEL_DEFAULT_ADMIN_PASSWORD must override the development default in production or staging")
    return default_admin_password


AUTH_SECRET = _load_auth_secret()
DEFAULT_ADMIN_PASSWORD = _load_default_admin_password()


def hash_password(password: str) -> str:
    normalized_password = str(password or "")
    if len(normalized_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized_password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    encoded_digest = base64.b64encode(digest).decode("ascii")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${encoded_digest}"


def verify_password(password: str, encoded_password: str | None) -> bool:
    normalized_encoded = str(encoded_password or "").strip()
    if not normalized_encoded:
        return False

    try:
        algorithm, iterations_text, salt, encoded_digest = normalized_encoded.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_text)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(password or "").encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    computed_digest = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(computed_digest, encoded_digest)


def create_access_token(
    *,
    user_id: int,
    username: str,
    role: str,
    supplier_id: int | None = None,
    display_name: str | None = None,
    expires_seconds: int | None = None,
) -> tuple[str, int]:
    lifetime_seconds = int(expires_seconds or AUTH_ACCESS_TOKEN_EXPIRE_SECONDS)
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=lifetime_seconds)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "supplier_id": supplier_id,
        "display_name": display_name,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, AUTH_SECRET, algorithm=AUTH_ALGORITHM)
    return token, lifetime_seconds


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, AUTH_SECRET, algorithms=[AUTH_ALGORITHM])
