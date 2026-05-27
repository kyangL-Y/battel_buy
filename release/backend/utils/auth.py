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
AUTH_SECRET = os.getenv(
    "BATTEL_AUTH_SECRET",
    "battel-dev-secret-change-me-please-override-32",
)
DEFAULT_ADMIN_USERNAME = os.getenv("BATTEL_DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("BATTEL_DEFAULT_ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_DISPLAY_NAME = os.getenv("BATTEL_DEFAULT_ADMIN_DISPLAY_NAME", "系统管理员")
PBKDF2_ITERATIONS = int(os.getenv("BATTEL_AUTH_PBKDF2_ITERATIONS", "390000"))
MIN_PASSWORD_LENGTH = 8


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
