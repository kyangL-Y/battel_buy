from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from mitmproxy import http


OUTPUT_DIR = Path("E:/battel/tmp/meicai_capture")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "meicai_flows.jsonl"
SECRET_OUTPUT_DIR = Path("E:/battel/.local-secrets/meicai_capture")
SECRET_OUTPUT_FILE = SECRET_OUTPUT_DIR / "meicai_secret_flows.jsonl"
SECRET_CAPTURE_ENABLED = str(os.environ.get("ALLOW_SECRET_CAPTURE") or "").strip() == "1"
CHANGE_ADDRESS_PATH = "/api/auth/changeaddress"
SECRET_CAPTURE_PATHS = {
    CHANGE_ADDRESS_PATH,
    "/entrance/dishes/saleClass",
    "/entrance/recommend/xbFeed",
    "/entrance/recommend/goodsInfoLocation",
}

TARGET_HOST_KEYWORDS = (
    "mallapi.yunshanmeicai.com",
    "mall-entrance.yunshanmeicai.com",
    "ampapi.yunshanmeicai.com",
)
IGNORED_HOST_KEYWORDS = (
    "img-oss.",
    "material-page.",
)
TARGET_URL_KEYWORDS = (
    "yunshanmeicai.com",
    "meicai",
)
TARGET_PATH_KEYWORDS = (
    "address",
    "area",
    "goods",
    "sku",
    "ssu",
    "spu",
    "category",
    "city",
    "county",
    "delivery",
    "district",
    "search",
    "feed",
    "geo",
    "location",
    "map",
    "poi",
    "product",
    "cms",
    "region",
)
SENSITIVE_NAME_PATTERN = re.compile(
    r"token|ticket|cookie|authorization|auth|session|secret|password|phone|mobile|"
    r"company.*id|unit.*id|user.*id|receiver|contact|address|lat|lng|device|uuid|oaid|imei|imsi|idfa|idfv|"
    r"sign|signature|x-.*id",
    re.IGNORECASE,
)


def request(flow: http.HTTPFlow) -> None:
    if _matches(flow):
        _write_flow(flow)


def response(flow: http.HTTPFlow) -> None:
    if _matches(flow):
        _write_flow(flow)


def _matches(flow: http.HTTPFlow) -> bool:
    request_item = flow.request
    host = (request_item.pretty_host or "").lower()
    path = (request_item.path or "").lower()
    if any(keyword in host for keyword in IGNORED_HOST_KEYWORDS):
        return False
    if any(keyword in host for keyword in TARGET_HOST_KEYWORDS):
        return True
    if not any(keyword in host for keyword in TARGET_URL_KEYWORDS):
        return False
    return any(keyword in path for keyword in TARGET_PATH_KEYWORDS)


def _write_flow(flow: http.HTTPFlow) -> None:
    request_item = flow.request
    response_item = flow.response
    parsed_url = urlparse(request_item.pretty_url)
    if SECRET_CAPTURE_ENABLED and parsed_url.path in SECRET_CAPTURE_PATHS:
        _write_secret_flow(flow, parsed_url)
    payload = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "event": "response" if response_item else "request",
        "method": request_item.method,
        "url": _redact_url(request_item.pretty_url),
        "scheme": parsed_url.scheme,
        "host": request_item.pretty_host,
        "path": parsed_url.path,
        "query": _redact_mapping(dict(parse_qsl(parsed_url.query, keep_blank_values=True))),
        "request_headers": _redact_mapping(dict(request_item.headers)),
        "request_text": _redact_json_text(request_item.get_text(strict=False)),
        "status_code": response_item.status_code if response_item else None,
        "response_headers": _redact_mapping(dict(response_item.headers)) if response_item else {},
        "response_text": _safe_response_text(response_item),
    }
    with OUTPUT_FILE.open("a", encoding="utf-8") as output_file:
        output_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _write_secret_flow(flow: http.HTTPFlow, parsed_url: object) -> None:
    request_item = flow.request
    response_item = flow.response
    SECRET_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "event": "response" if response_item else "request",
        "method": request_item.method,
        "url": request_item.pretty_url,
        "scheme": parsed_url.scheme,
        "host": request_item.pretty_host,
        "path": parsed_url.path,
        "query": dict(parse_qsl(parsed_url.query, keep_blank_values=True)),
        "request_headers": dict(request_item.headers),
        "request_text": _raw_text(request_item.get_text(strict=False), limit=12000),
        "status_code": response_item.status_code if response_item else None,
        "response_headers": dict(response_item.headers) if response_item else {},
        "response_text": _raw_text(response_item.get_text(strict=False), limit=12000) if response_item else "",
    }
    with SECRET_OUTPUT_FILE.open("a", encoding="utf-8") as output_file:
        output_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _redact_mapping(values: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in values.items():
        redacted[key] = "<redacted>" if SENSITIVE_NAME_PATTERN.search(str(key)) else _safe_text(value, limit=1000)
    return redacted


def _redact_url(url: str) -> str:
    parsed_url = urlparse(url)
    if not parsed_url.query:
        return url
    query_pairs = parse_qsl(parsed_url.query, keep_blank_values=True)
    redacted_query = []
    for key, value in query_pairs:
        redacted_query.append(f"{key}=<redacted>" if SENSITIVE_NAME_PATTERN.search(key) else f"{key}={value}")
    return parsed_url._replace(query="&".join(redacted_query)).geturl()


def _safe_text(value: bytes | str | None, limit: int = 4000) -> str:
    if value is None:
        return ""
    text = value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else str(value)
    if SENSITIVE_NAME_PATTERN.search(text[:200]):
        return "<redacted-body>"
    return text[:limit]


def _raw_text(value: bytes | str | None, limit: int = 4000) -> str:
    if value is None:
        return ""
    text = value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else str(value)
    return text[:limit]


def _safe_response_text(response_item: http.Response | None) -> str:
    if response_item is None:
        return ""
    content_type = str(response_item.headers.get("content-type", "")).lower()
    if "json" not in content_type and "text" not in content_type:
        return f"<{content_type or 'binary'} omitted>"
    response_text = response_item.get_text(strict=False)
    if "json" in content_type:
        return _redact_json_text(response_text, limit=8000)
    return _safe_text(response_text, limit=8000)


def _redact_json_text(value: bytes | str | None, limit: int = 4000) -> str:
    if value is None:
        return ""
    text = value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else str(value)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _safe_text(text, limit=limit)
    return json.dumps(_redact_json_value(payload), ensure_ascii=False)[:limit]


def _redact_json_value(value: object) -> object:
    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        for key, item in value.items():
            redacted[key] = "<redacted>" if SENSITIVE_NAME_PATTERN.search(str(key)) else _redact_json_value(item)
        return redacted
    if isinstance(value, list):
        return [_redact_json_value(item) for item in value]
    if isinstance(value, str):
        return value[:1000]
    return value
