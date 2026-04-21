from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator


PROXY_ENV_KEYS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
]


@contextmanager
def without_proxy_env() -> Iterator[None]:
    """Temporarily clear proxy-related environment variables for direct requests."""
    previous = {key: os.environ.get(key) for key in PROXY_ENV_KEYS if key in os.environ}
    try:
        for key in PROXY_ENV_KEYS:
            os.environ.pop(key, None)
        yield
    finally:
        for key, value in previous.items():
            os.environ[key] = value
