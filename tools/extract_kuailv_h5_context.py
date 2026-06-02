from __future__ import annotations

import argparse
import json
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


KUAILV_GOODS_LIST_PATH = "/wxmall/api/goods/list"
KUAILV_CATEGORY_PATHS = (
    "/wxmall/api/goods/category/first/list",
    "/wxmall/api/goods/category/second/list",
    "/wxmall/api/goods/category/filter",
)
DEFAULT_OUTPUT_PATH = Path(".local-secrets/kuailv.env")
PASS_THROUGH_HEADER_DENYLIST = {
    "cookie",
    "content-length",
    "host",
}
ADDRESS_CONTEXT_KEYS = (
    "selectedPoiAddressId",
    "selectedSalesGridId",
    "gtCityId",
    "uaEnv",
    "loginAcctType",
    "uuid",
)


def extract_latest_kuailv_h5_context(capture_path: Path) -> dict[str, Any]:
    capture_records = _load_capture_records(capture_path)
    selected_record: dict[str, Any] | None = None
    fallback_record: dict[str, Any] | None = None
    for capture_record in capture_records:
        path = _request_path(capture_record)
        if path == KUAILV_GOODS_LIST_PATH:
            selected_record = capture_record
        elif path in KUAILV_CATEGORY_PATHS:
            fallback_record = capture_record
    request_record = selected_record or fallback_record
    if request_record is None:
        raise RuntimeError("未在抓包文件中找到快驴 H5 分类或商品请求")

    request_headers = _extract_request_headers(request_record)
    request_cookies = _extract_request_cookies(request_record, request_headers)
    address_context = _extract_address_context(request_record)
    goods_body = _parse_request_body(request_record)
    if goods_body:
        for source_key, target_key in (("cat1Id", "cat1_id"), ("cat2Id", "cat2_id"), ("pageSize", "page_size")):
            if goods_body.get(source_key) is not None:
                address_context[target_key] = str(goods_body.get(source_key))
    if not request_cookies and "cookie" not in {key.lower() for key in request_headers}:
        raise RuntimeError("抓包中缺少 Cookie，不能生成服务器可用的 KUAILV_COOKIES")
    selected_context = {
        "request_headers": _drop_cookie_header(request_headers),
        "cookies": request_cookies,
        "address_context": address_context,
        "source_path": _request_path(request_record),
        "has_goods_request": _request_path(request_record) == KUAILV_GOODS_LIST_PATH,
    }
    if _contains_redacted_value(selected_context):
        raise RuntimeError("抓包内容已脱敏，不能生成服务器可用的 KUAILV_* env")
    return selected_context


def write_kuailv_env(kuailv_context: dict[str, Any], output_path: Path) -> None:
    address_context = dict(kuailv_context.get("address_context") or {})
    env_payloads: list[tuple[str, Any]] = [
        ("KUAILV_COOKIES", kuailv_context.get("cookies") or {}),
        ("KUAILV_REQUEST_HEADERS", kuailv_context.get("request_headers") or {}),
        ("KUAILV_ADDRESS_CONTEXT", address_context),
    ]
    if address_context.get("gtCityId"):
        env_payloads.append(("KUAILV_CITY_ID", str(address_context["gtCityId"])))
    if address_context.get("cat1_id"):
        env_payloads.append(("KUAILV_CAT1_ID", str(address_context["cat1_id"])))
    if address_context.get("cat2_id"):
        env_payloads.append(("KUAILV_CAT2_ID", str(address_context["cat2_id"])))

    env_lines: list[str] = []
    for env_name, env_payload in env_payloads:
        if isinstance(env_payload, dict):
            env_value = json.dumps(env_payload, ensure_ascii=False, separators=(",", ":"))
            env_lines.append(f"{env_name}='{env_value}'")
        else:
            env_lines.append(f"{env_name}={env_payload}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")


def _load_capture_records(capture_path: Path) -> list[dict[str, Any]]:
    if not capture_path.exists():
        raise RuntimeError(f"抓包文件不存在: {capture_path}")
    raw_text = capture_path.read_text(encoding="utf-8-sig")
    stripped_text = raw_text.strip()
    if not stripped_text:
        raise RuntimeError(f"抓包文件为空: {capture_path}")
    try:
        payload = json.loads(stripped_text)
    except json.JSONDecodeError:
        return _load_jsonl_capture_records(raw_text)
    if isinstance(payload, dict) and isinstance(payload.get("log"), dict):
        entries = payload["log"].get("entries") or []
        return [_normalize_har_entry(entry) for entry in entries if isinstance(entry, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    raise RuntimeError("抓包文件必须是 HAR、JSON object、JSON array 或 JSONL")


def _load_jsonl_capture_records(raw_text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"抓包文件第 {line_number} 行不是合法 JSON") from exc
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _normalize_har_entry(entry: dict[str, Any]) -> dict[str, Any]:
    request = entry.get("request") if isinstance(entry.get("request"), dict) else {}
    headers = {
        str(item.get("name")): str(item.get("value"))
        for item in request.get("headers", [])
        if isinstance(item, dict) and item.get("name") is not None
    }
    cookies = {
        str(item.get("name")): str(item.get("value"))
        for item in request.get("cookies", [])
        if isinstance(item, dict) and item.get("name") is not None
    }
    post_data = request.get("postData") if isinstance(request.get("postData"), dict) else {}
    return {
        "url": request.get("url"),
        "method": request.get("method"),
        "request_headers": headers,
        "request_cookies": cookies,
        "request_text": post_data.get("text") or "",
    }


def _request_path(capture_record: dict[str, Any]) -> str:
    explicit_path = str(capture_record.get("path") or "").strip()
    if explicit_path:
        return explicit_path
    url = str(capture_record.get("url") or "").strip()
    if not url and isinstance(capture_record.get("request"), dict):
        url = str(capture_record["request"].get("url") or "").strip()
    return urlparse(url).path if url else ""


def _request_url(capture_record: dict[str, Any]) -> str:
    url = str(capture_record.get("url") or "").strip()
    if not url and isinstance(capture_record.get("request"), dict):
        url = str(capture_record["request"].get("url") or "").strip()
    return url


def _extract_request_headers(capture_record: dict[str, Any]) -> dict[str, str]:
    request_headers = capture_record.get("request_headers")
    if not isinstance(request_headers, dict) and isinstance(capture_record.get("headers"), dict):
        request_headers = capture_record.get("headers")
    if not isinstance(request_headers, dict):
        request_headers = {}
    extracted_headers: dict[str, str] = {}
    for header_name, header_value in request_headers.items():
        normalized_name = str(header_name).strip()
        if not normalized_name:
            continue
        if normalized_name.lower() in PASS_THROUGH_HEADER_DENYLIST:
            continue
        extracted_headers[normalized_name] = str(header_value)
    return extracted_headers


def _extract_request_cookies(capture_record: dict[str, Any], request_headers: dict[str, str]) -> dict[str, str]:
    request_cookies = capture_record.get("request_cookies")
    cookies: dict[str, str] = {}
    if isinstance(request_cookies, dict):
        cookies.update({str(name): str(value) for name, value in request_cookies.items() if str(name).strip()})
    cookie_header = next(
        (str(value) for name, value in request_headers.items() if str(name).lower() == "cookie"),
        "",
    )
    if not cookie_header and isinstance(capture_record.get("request_headers"), dict):
        cookie_header = next(
            (
                str(value)
                for name, value in capture_record["request_headers"].items()
                if str(name).lower() == "cookie"
            ),
            "",
        )
    if cookie_header:
        parsed_cookie = SimpleCookie()
        parsed_cookie.load(cookie_header)
        for name, morsel in parsed_cookie.items():
            cookies[name] = morsel.value
    return cookies


def _extract_address_context(capture_record: dict[str, Any]) -> dict[str, str]:
    query_params = _request_query(capture_record)
    address_context: dict[str, str] = {}
    for key in ADDRESS_CONTEXT_KEYS:
        value = query_params.get(key)
        if value:
            address_context[key] = value
    return address_context


def _request_query(capture_record: dict[str, Any]) -> dict[str, str]:
    query_pairs: dict[str, str] = {}
    url = _request_url(capture_record)
    if url:
        for name, values in parse_qs(urlparse(url).query, keep_blank_values=True).items():
            if values:
                query_pairs[name] = values[-1]
    params = capture_record.get("params")
    if isinstance(params, dict):
        query_pairs.update({str(name): str(value) for name, value in params.items()})
    return query_pairs


def _parse_request_body(capture_record: dict[str, Any]) -> dict[str, Any]:
    request_text = str(capture_record.get("request_text") or "").strip()
    if not request_text:
        return {}
    try:
        request_body = json.loads(request_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("快驴 request_text 不是合法 JSON") from exc
    if not isinstance(request_body, dict):
        raise RuntimeError("快驴 request_text 必须是 JSON object")
    return request_body


def _drop_cookie_header(request_headers: dict[str, str]) -> dict[str, str]:
    return {
        header_name: header_value
        for header_name, header_value in request_headers.items()
        if header_name.lower() != "cookie"
    }


def _contains_redacted_value(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_redacted_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_redacted_value(item) for item in value)
    return str(value).strip() == "<redacted>"


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Extract KUAILV_* env from a private Kuailv H5 HAR/JSONL capture."
    )
    argument_parser.add_argument("--input", "-i", required=True, help="Path to a private HAR/JSONL capture.")
    argument_parser.add_argument(
        "--output",
        "-o",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Env file output path. Use a gitignored private path.",
    )
    parsed_arguments = argument_parser.parse_args()

    kuailv_context = extract_latest_kuailv_h5_context(Path(parsed_arguments.input))
    output_path = Path(parsed_arguments.output)
    write_kuailv_env(kuailv_context, output_path)
    address_context = kuailv_context.get("address_context") or {}
    print(
        "wrote KUAILV env to {output} source_path={source_path} has_goods_request={has_goods_request} context_keys={context_keys}".format(
            output=output_path,
            source_path=kuailv_context.get("source_path"),
            has_goods_request=kuailv_context.get("has_goods_request"),
            context_keys=",".join(sorted(address_context.keys())),
        )
    )


if __name__ == "__main__":
    main()
