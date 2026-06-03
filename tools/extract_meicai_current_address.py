from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_MMKV_PATH = Path(".local-secrets/meicai_app_state/mmkv/GlobalAddressSp")
DEFAULT_OUTPUT_PATH = Path(".local-secrets/meicai_current_address_context.json")
CURRENT_ADDRESS_KEY = "currentAddressStr"


def extract_current_address(mmkv_path: Path) -> dict[str, Any]:
    if not mmkv_path.exists():
        raise RuntimeError(f"美菜地址 MMKV 文件不存在: {mmkv_path}")
    mmkv_bytes = mmkv_path.read_bytes()
    decoded_text = mmkv_bytes.decode("utf-8", errors="ignore")
    key_position = decoded_text.find(CURRENT_ADDRESS_KEY)
    if key_position < 0:
        raise RuntimeError(f"未找到 {CURRENT_ADDRESS_KEY}")
    json_start = decoded_text.find("{", key_position)
    if json_start < 0:
        raise RuntimeError(f"{CURRENT_ADDRESS_KEY} 后未找到 JSON object")

    decoder = json.JSONDecoder()
    address_payload, _ = decoder.raw_decode(decoded_text[json_start:])
    if not isinstance(address_payload, dict):
        raise RuntimeError(f"{CURRENT_ADDRESS_KEY} 不是 JSON object")
    return address_payload


def infer_meicai_city_area(address_payload: dict[str, Any]) -> tuple[str, str]:
    address_text = " ".join(
        str(address_payload.get(field_name) or "")
        for field_name in ("poi_address", "address_detail", "address")
    )
    # 已验证当前南京地址为 city_id=17、area_id=4402；更多城市需要由 App 切地址后请求/响应校验沉淀。
    if re.search(r"南京|溧水", address_text):
        return "17", "4402"
    return "", ""


def build_current_address_context(address_payload: dict[str, Any]) -> dict[str, Any]:
    city_id, area_id = infer_meicai_city_area(address_payload)
    location_text = str(address_payload.get("location") or "").strip()
    if not location_text:
        raise RuntimeError("当前地址缺少 location 密文")
    return {
        "locationTo": location_text,
        "location": location_text,
        "city_id": city_id,
        "area_id": area_id,
        "addressId": str(address_payload.get("addressId") or "").strip(),
        "has_location": True,
        "poi_address": str(address_payload.get("poi_address") or "").strip(),
        "address_detail": str(address_payload.get("address_detail") or "").strip(),
    }


def summarize_context(address_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "city_id": address_context.get("city_id") or "",
        "area_id": address_context.get("area_id") or "",
        "addressId": address_context.get("addressId") or "",
        "has_location": bool(address_context.get("locationTo")),
        "poi_address": address_context.get("poi_address") or "",
        "address_detail": address_context.get("address_detail") or "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Meicai current address context from App MMKV state.")
    parser.add_argument("--input", "-i", default=str(DEFAULT_MMKV_PATH))
    parser.add_argument("--output", "-o", default=str(DEFAULT_OUTPUT_PATH))
    parsed_arguments = parser.parse_args()

    address_payload = extract_current_address(Path(parsed_arguments.input))
    address_context = build_current_address_context(address_payload)
    output_path = Path(parsed_arguments.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(address_context, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output_path), **summarize_context(address_context)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
