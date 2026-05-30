from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CHANGE_ADDRESS_PATH = "/api/auth/changeaddress"
FEED_PATHS = ("/entrance/recommend/xbFeed", "/entrance/recommend/goodsInfoLocation")
DEFAULT_CAPTURE_PATH = Path("tmp/meicai_capture/meicai_flows.jsonl")
DEFAULT_OUTPUT_PATH = Path(".local-secrets/meicai_address_context.env")
HEADER_FIELDS = (
    "device-token",
    "company-token",
    "passport-token",
    "x-mc-city",
    "x-mc-area",
    "mc-gray",
    "user-agent",
)
COMMON_BODY_FIELDS = (
    "tickets",
    "time_stamp",
    "salt_index",
    "mallSaltSign",
    "salt_sign",
    "_ENV_",
)
REQUIRED_CHANGE_ADDRESS_FIELDS = (
    "locationTo",
    "city_id",
    "area_id",
    "tickets",
    "time_stamp",
    "salt_index",
    "mallSaltSign",
    "salt_sign",
)


def extract_latest_change_address_context(capture_path: Path) -> dict[str, Any]:
    selected_address_body: dict[str, Any] | None = None
    selected_feed_body: dict[str, Any] | None = None
    selected_feed_headers: dict[str, Any] = {}
    for flow_record in _iter_flow_records(capture_path):
        path = str(flow_record.get("path") or "")
        if path != CHANGE_ADDRESS_PATH and path not in FEED_PATHS:
            continue
        request_body = _parse_request_body(flow_record)
        request_headers = flow_record.get("request_headers") if isinstance(flow_record.get("request_headers"), dict) else {}
        if path == CHANGE_ADDRESS_PATH and request_body:
            selected_address_body = request_body
        if path in FEED_PATHS and request_body:
            selected_feed_body = request_body
            selected_feed_headers = request_headers
    if selected_address_body is None:
        raise RuntimeError(f"未在抓包文件中找到 {CHANGE_ADDRESS_PATH}")
    source_body = selected_feed_body or selected_address_body
    selected_context = {
        "request_headers": _extract_request_headers(selected_feed_headers),
        "common_body": _extract_common_body(source_body),
        "address_context": {"request_body": selected_address_body},
    }
    _validate_change_address_body(selected_address_body)
    if _contains_redacted_value(selected_context):
        raise RuntimeError("抓包中的 changeaddress 请求已脱敏，不能生成服务器可用的 MEICAI_ADDRESS_CONTEXT")
    return selected_context


def extract_latest_change_address_body(capture_path: Path) -> dict[str, Any]:
    return extract_latest_change_address_context(capture_path)["address_context"]["request_body"]


def write_address_context_env(change_address_context: dict[str, Any], output_path: Path) -> None:
    env_lines = []
    for env_name, env_payload in (
        ("MEICAI_REQUEST_HEADERS", change_address_context.get("request_headers") or {}),
        ("MEICAI_COMMON_BODY", change_address_context.get("common_body") or {}),
        ("MEICAI_ADDRESS_CONTEXT", change_address_context.get("address_context") or {"request_body": change_address_context}),
    ):
        env_value = json.dumps(env_payload, ensure_ascii=False, separators=(",", ":"))
        env_lines.append(f"{env_name}='{env_value}'")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")


def _iter_flow_records(capture_path: Path) -> list[dict[str, Any]]:
    if not capture_path.exists():
        raise RuntimeError(f"抓包文件不存在: {capture_path}")
    flow_records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(capture_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            flow_record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"抓包文件第 {line_number} 行不是合法 JSON") from exc
        if isinstance(flow_record, dict):
            flow_records.append(flow_record)
    return flow_records


def _parse_request_body(flow_record: dict[str, Any]) -> dict[str, Any]:
    request_text = str(flow_record.get("request_text") or "").strip()
    if not request_text:
        return {}
    try:
        request_body = json.loads(request_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{CHANGE_ADDRESS_PATH} 的 request_text 不是合法 JSON") from exc
    if not isinstance(request_body, dict):
        raise RuntimeError(f"{CHANGE_ADDRESS_PATH} 的 request_text 必须是 JSON object")
    return request_body


def _extract_request_headers(request_headers: dict[str, Any]) -> dict[str, str]:
    extracted_headers: dict[str, str] = {}
    lower_headers = {str(key).lower(): str(value) for key, value in request_headers.items()}
    for header_name in HEADER_FIELDS:
        header_value = lower_headers.get(header_name)
        if header_value:
            extracted_headers[header_name] = header_value
    return extracted_headers


def _extract_common_body(change_address_body: dict[str, Any]) -> dict[str, Any]:
    return {
        field_name: change_address_body[field_name]
        for field_name in COMMON_BODY_FIELDS
        if field_name in change_address_body
    }


def _validate_change_address_body(change_address_body: dict[str, Any]) -> None:
    missing_fields = [
        field_name
        for field_name in REQUIRED_CHANGE_ADDRESS_FIELDS
        if str(change_address_body.get(field_name) or "").strip() == ""
    ]
    if missing_fields:
        raise RuntimeError("changeaddress 请求缺少字段: " + ", ".join(missing_fields))


def _contains_redacted_value(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_redacted_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_redacted_value(item) for item in value)
    return str(value).strip() == "<redacted>"


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Extract MEICAI_ADDRESS_CONTEXT from a Meicai changeaddress capture."
    )
    argument_parser.add_argument(
        "--input",
        "-i",
        default=str(DEFAULT_CAPTURE_PATH),
        help="Path to a JSONL capture containing /api/auth/changeaddress.",
    )
    argument_parser.add_argument(
        "--output",
        "-o",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Env file output path. Use a gitignored private path.",
    )
    parsed_arguments = argument_parser.parse_args()

    change_address_context = extract_latest_change_address_context(Path(parsed_arguments.input))
    output_path = Path(parsed_arguments.output)
    write_address_context_env(change_address_context, output_path)
    change_address_body = change_address_context["address_context"]["request_body"]
    print(
        "wrote MEICAI_ADDRESS_CONTEXT to {output} city_id={city_id} area_id={area_id}".format(
            output=output_path,
            city_id=change_address_body.get("city_id"),
            area_id=change_address_body.get("area_id"),
        )
    )


if __name__ == "__main__":
    main()
