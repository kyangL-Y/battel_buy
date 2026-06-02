from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from mitmproxy import http


OUTPUT_DIR = Path("E:/battel/tmp/kuailv_capture")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "kuailv_flows.jsonl"
SECRET_OUTPUT_DIR = Path("E:/battel/.local-secrets/kuailv_capture")
SECRET_OUTPUT_FILE = SECRET_OUTPUT_DIR / "kuailv_secret_flows.jsonl"
SECRET_CAPTURE_ENABLED = str(os.environ.get("ALLOW_SECRET_CAPTURE") or "").strip() == "1"

TARGET_HOST_KEYWORDS = (
    "klmall.meituan.com",
)
TARGET_PATH_PREFIXES = (
    "/wxmall/api/goods/",
    "/wxmall/api/register/check/open",
)
SECRET_CAPTURE_PATHS = {
    "/wxmall/api/goods/list",
    "/wxmall/api/goods/category/first/list",
    "/wxmall/api/goods/category/second/list",
    "/wxmall/api/goods/category/filter",
}
SENSITIVE_NAME_PATTERN = re.compile(
    r"token|ticket|cookie|authorization|auth|session|secret|password|phone|mobile|"
    r"contact|receiver|address|poi|grid|lat|lng|device|uuid|oaid|imei|imsi|idfa|idfv|"
    r"sign|signature|x-.*id|user.*id|acct",
    re.IGNORECASE,
)


def request(flow: http.HTTPFlow) -> None:
    if _matches_kuailv_goods_flow(flow):
        _write_flow(flow)


def response(flow: http.HTTPFlow) -> None:
    if _matches_kuailv_goods_flow(flow):
        _write_flow(flow)


def _matches_kuailv_goods_flow(flow: http.HTTPFlow) -> bool:
    request_item = flow.request
    host = (request_item.pretty_host or "").lower()
    path = urlparse(request_item.pretty_url).path
    if not any(host_keyword in host for host_keyword in TARGET_HOST_KEYWORDS):
        return False
    return any(path.startswith(path_prefix) for path_prefix in TARGET_PATH_PREFIXES)


def _write_flow(flow: http.HTTPFlow) -> None:
    request_item = flow.request
    response_item = flow.response
    parsed_url = urlparse(request_item.pretty_url)
    if SECRET_CAPTURE_ENABLED and parsed_url.path in SECRET_CAPTURE_PATHS:
        _write_secret_flow(flow, parsed_url)

    response_payload = _parse_json(response_item.get_text(strict=False)) if response_item else None
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
        "response_summary": _summarize_kuailv_response(response_payload),
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
        "request_text": _raw_text(request_item.get_text(strict=False), limit=20000),
        "status_code": response_item.status_code if response_item else None,
        "response_headers": dict(response_item.headers) if response_item else {},
        "response_text": _raw_text(response_item.get_text(strict=False), limit=80000) if response_item else "",
    }
    with SECRET_OUTPUT_FILE.open("a", encoding="utf-8") as output_file:
        output_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _summarize_kuailv_response(response_payload: object) -> dict[str, object]:
    if not isinstance(response_payload, dict):
        return {"json": False}
    payload_data = response_payload.get("data")
    goods_count = None
    page_keys: list[str] = []
    data_keys: list[str] = []
    if isinstance(payload_data, dict):
        data_keys = sorted(str(key) for key in payload_data.keys())
        goods_list = payload_data.get("goodsList")
        if isinstance(goods_list, list):
            goods_count = len(goods_list)
        page = payload_data.get("page")
        if isinstance(page, dict):
            page_keys = sorted(str(key) for key in page.keys())
    return {
        "json": True,
        "code": response_payload.get("code"),
        "status": response_payload.get("status"),
        "success": response_payload.get("success"),
        "message": response_payload.get("message") or response_payload.get("msg"),
        "data_keys": data_keys,
        "goods_count": goods_count,
        "page_keys": page_keys,
    }


def _redact_mapping(values: dict[str, str]) -> dict[str, str]:
    redacted_values: dict[str, str] = {}
    for key, value in values.items():
        redacted_values[key] = "<redacted>" if SENSITIVE_NAME_PATTERN.search(str(key)) else _safe_text(value)
    return redacted_values


def _redact_url(url: str) -> str:
    parsed_url = urlparse(url)
    if not parsed_url.query:
        return url
    redacted_query = []
    for key, value in parse_qsl(parsed_url.query, keep_blank_values=True):
        query_value = "<redacted>" if SENSITIVE_NAME_PATTERN.search(key) else value
        redacted_query.append(f"{key}={query_value}")
    return parsed_url._replace(query="&".join(redacted_query)).geturl()


def _redact_json_text(value: bytes | str | None, limit: int = 4000) -> str:
    text = _raw_text(value, limit=limit)
    if not text:
        return ""
    parsed_payload = _parse_json(text)
    if parsed_payload is None:
        return _safe_text(text, limit=limit)
    return json.dumps(_redact_json_value(parsed_payload), ensure_ascii=False)[:limit]


def _redact_json_value(value: object) -> object:
    if isinstance(value, dict):
        redacted_value: dict[str, object] = {}
        for key, item in value.items():
            redacted_value[key] = "<redacted>" if SENSITIVE_NAME_PATTERN.search(str(key)) else _redact_json_value(item)
        return redacted_value
    if isinstance(value, list):
        return [_redact_json_value(item) for item in value]
    if isinstance(value, str):
        return value[:1000]
    return value


def _parse_json(value: bytes | str | None) -> object | None:
    text = _raw_text(value, limit=80000)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _safe_text(value: bytes | str | None, limit: int = 4000) -> str:
    text = _raw_text(value, limit=limit)
    return "<redacted-body>" if SENSITIVE_NAME_PATTERN.search(text[:200]) else text


def _raw_text(value: bytes | str | None, limit: int = 4000) -> str:
    if value is None:
        return ""
    text = value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else str(value)
    return text[:limit]
