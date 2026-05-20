from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from mitmproxy import http


OUTPUT_DIR = Path("E:/battel/tmp/liancai_capture")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "liancai_flows.jsonl"

TARGET_HOST_KEYWORDS = (
    "liancaiwang.cn",
    "shicaiguanjia.com",
    "lcwapp.",
)

TARGET_PATH_KEYWORDS = (
    "/index.php/list/",
    "/list/",
    "/show/",
    "/product",
    "/category",
    "/brand",
    "/search",
)


def _matches(flow: http.HTTPFlow) -> bool:
    request = flow.request
    host = (request.pretty_host or "").lower()
    path = (request.path or "").lower()
    if any(keyword in host for keyword in TARGET_HOST_KEYWORDS):
        return True
    return any(keyword in path for keyword in TARGET_PATH_KEYWORDS)


def _safe_text(value: bytes | str | None, limit: int = 4000) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="ignore")
    else:
        text = str(value)
    return text[:limit]


def response(flow: http.HTTPFlow) -> None:
    if not _matches(flow):
        return

    request = flow.request
    response = flow.response
    parsed = urlparse(request.pretty_url)
    payload = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "method": request.method,
        "url": request.pretty_url,
        "scheme": parsed.scheme,
        "host": request.pretty_host,
        "path": parsed.path,
        "query": dict(parse_qsl(parsed.query, keep_blank_values=True)),
        "request_headers": dict(request.headers),
        "request_text": _safe_text(request.get_text(strict=False)),
        "status_code": response.status_code if response else None,
        "response_headers": dict(response.headers) if response else {},
        "response_text": _safe_text(response.get_text(strict=False) if response else ""),
    }
    with OUTPUT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")
