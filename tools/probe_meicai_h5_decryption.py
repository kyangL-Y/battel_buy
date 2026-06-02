from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawler.public_source_crawlers import MEICAI_DEFAULT_PAGE_SIZE, MeicaiAppGatewayClient, PublicSourceCrawler
from tools.extract_meicai_category_candidates import load_category_filters_from_sale_class_tree
from tools.probe_meicai_plaintext_endpoints import apply_meicai_address_context, load_secret_env


DEFAULT_SECRET_ENV_FILE = Path(".local-secrets/meicai_address_context.env")
DEFAULT_SALE_CLASS_TREE = Path("tmp/meicai_sale_class_tree.json")
DEFAULT_H5_SALTS_FILE = Path("tmp/meicai_h5_salts.json")
MALL_TYPE3_SECRET_SUFFIX = "MEICAIMALL2026"


def build_h5_decryption_report(
    *,
    secret_env_file: Path,
    sale_class_tree: Path,
    h5_salts_file: Path,
    source_candidates: list[str],
    base_url: str,
    page_size: int,
) -> dict[str, Any]:
    load_secret_env(secret_env_file)
    request_headers = PublicSourceCrawler._load_json_env_object("MEICAI_REQUEST_HEADERS")
    captured_common_body = PublicSourceCrawler._load_json_env_object("MEICAI_COMMON_BODY")
    address_context = PublicSourceCrawler._load_json_env_object("MEICAI_ADDRESS_CONTEXT")
    h5_salts_payload = json.loads(h5_salts_file.read_text(encoding="utf-8-sig"))
    request_source = (
        source_candidates[0]
        if source_candidates
        else extract_source_from_common_body(captured_common_body) or "web"
    )
    common_body = build_h5_common_body(
        captured_common_body=captured_common_body,
        h5_salts_payload=h5_salts_payload,
        request_headers=request_headers,
        request_source=request_source,
    )

    client = MeicaiAppGatewayClient(
        base_url=base_url,
        request_headers={str(header_name): str(header_value) for header_name, header_value in request_headers.items()},
        common_body=common_body,
    )
    city_id, area_id = apply_meicai_address_context(client, address_context)
    category_filter = load_category_filters_from_sale_class_tree(sale_class_tree)[0]
    payload = client.class_products(
        page=1,
        page_size=page_size,
        city_id=city_id,
        area_id=area_id,
        sale_c1_id=str(category_filter.get("sale_c1_id") or category_filter.get("class1_id") or "-1"),
        sale_c2_id=str(category_filter.get("sale_c2_id") or category_filter.get("class2_id") or ""),
    )

    encryption_metadata = payload.get("encryption") if isinstance(payload, dict) else None
    encrypted_data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(encryption_metadata, dict) or not isinstance(encrypted_data, str):
        plaintext_summary = summarize_plaintext_payload(payload)
        return {
            "cipher_response": False,
            "decryption_success": False,
            "reason": "class_products did not return encrypted string data",
            "ret": payload.get("ret") if isinstance(payload, dict) else None,
            "code": payload.get("code") if isinstance(payload, dict) else None,
            "top_level_keys": plaintext_summary["top_level_keys"],
            "data_keys": plaintext_summary["data_keys"],
            "row_count": plaintext_summary["row_count"],
        }

    encryption_type = int(encryption_metadata.get("type") or 0)
    salt_index = int(encryption_metadata.get("salt_index") or 0)
    if encryption_type != 3:
        return {
            "cipher_response": True,
            "encryption_type": encryption_type,
            "decryption_success": False,
            "reason": "only type=3 is implemented by this H5 verification probe",
        }

    h5_salts_payload = json.loads(h5_salts_file.read_text(encoding="utf-8-sig"))
    type3_salts = str(h5_salts_payload["saltsType3"])
    salt_start = (salt_index >> 7) & 127
    salt_end = salt_index & 127
    salt_slice = type3_salts[salt_start:salt_end]

    derived_sources = list(dict.fromkeys([request_source, *source_candidates, extract_source_from_common_body(common_body), "web", "android", "ios"]))
    attempts: list[dict[str, Any]] = []
    for source_name in [candidate for candidate in derived_sources if candidate]:
        plaintext = decrypt_type3_payload(
            encrypted_data=encrypted_data,
            salt_slice=salt_slice,
            source_name=source_name,
        )
        decoded_summary = summarize_plaintext(plaintext)
        attempts.append(
            {
                "source": source_name,
                "json_decoded": decoded_summary["json_decoded"],
                "top_level_keys": decoded_summary["top_level_keys"],
                "row_count": decoded_summary["row_count"],
                "spus_count": decoded_summary["spus_count"],
                "first_spu_keys": decoded_summary["first_spu_keys"],
                "first_sku_keys": decoded_summary["first_sku_keys"],
            }
        )
        if decoded_summary["json_decoded"]:
            return {
                "cipher_response": True,
                "encryption_type": encryption_type,
                "salt_span_length": max(0, salt_end - salt_start),
                "decryption_success": True,
                "working_source": source_name,
                "top_level_keys": decoded_summary["top_level_keys"],
                "row_count": decoded_summary["row_count"],
                "spus_count": decoded_summary["spus_count"],
                "first_spu_keys": decoded_summary["first_spu_keys"],
                "first_sku_keys": decoded_summary["first_sku_keys"],
                "attempts": attempts,
            }

    return {
        "cipher_response": True,
        "encryption_type": encryption_type,
        "salt_span_length": max(0, salt_end - salt_start),
        "decryption_success": False,
        "attempts": attempts,
    }


def build_h5_common_body(
    *,
    captured_common_body: dict[str, Any],
    h5_salts_payload: dict[str, Any],
    request_headers: dict[str, Any],
    request_source: str,
) -> dict[str, Any]:
    h5_common_body = {
        key: value
        for key, value in captured_common_body.items()
        if key not in {"mallSaltSign", "salt_index", "salt_sign", "time_stamp"}
    }
    env_payload = dict(h5_common_body.get("_ENV_") if isinstance(h5_common_body.get("_ENV_"), dict) else {})
    env_payload["source"] = request_source
    env_payload["isH5"] = 1
    env_payload["latestH5"] = 2
    h5_common_body["_ENV_"] = env_payload

    request_millis = int(time.time() * 1000)
    h5_common_body["mallSaltSign"] = calculate_type3_salt_sign(
        h5_salts_payload=h5_salts_payload,
        request_source=request_source,
        request_millis=request_millis,
        device_token=find_header_value(request_headers, "Device-Token"),
    )
    h5_common_body["salt_sign"] = calculate_type1_salt_sign(
        body_payload=h5_common_body,
        h5_salts_payload=h5_salts_payload,
        request_millis=request_millis,
    )
    return h5_common_body


def calculate_type3_salt_sign(
    *,
    h5_salts_payload: dict[str, Any],
    request_source: str,
    request_millis: int,
    device_token: str,
) -> str:
    type3_salts = str(h5_salts_payload["saltsType3"])
    salt_start = 0
    salt_end = 3
    salt_index = (salt_start << 7) | salt_end
    salt_slice = type3_salts[salt_start:salt_end]
    digest_text = hashlib.sha256(
        f"{salt_slice}{request_source}{MALL_TYPE3_SECRET_SUFFIX}{request_millis}{device_token}".encode()
    ).hexdigest()[6:]
    return f"{digest_text},3,{salt_index},{request_millis}"


def calculate_type1_salt_sign(
    *,
    body_payload: dict[str, Any],
    h5_salts_payload: dict[str, Any],
    request_millis: int,
) -> str:
    salt_index = 0
    body_with_timestamp = {**body_payload, "salt_index": salt_index, "time_stamp": request_millis}
    serialized_body = json.dumps(body_with_timestamp, ensure_ascii=False, separators=(",", ":"))
    salt_text = str(h5_salts_payload["salts"]["online"][salt_index])
    digest_text = hashlib.sha256(f"{serialized_body}{salt_text}".encode()).hexdigest().upper()
    return f"{digest_text},{salt_index},{request_millis}"


def find_header_value(request_headers: dict[str, Any], header_name: str) -> str:
    for current_name, header_value in request_headers.items():
        if str(current_name).lower() == header_name.lower():
            return str(header_value)
    return ""


def decrypt_type3_payload(*, encrypted_data: str, salt_slice: str, source_name: str) -> str:
    key_text = hashlib.sha256(f"{salt_slice}{source_name}{MALL_TYPE3_SECRET_SUFFIX}".encode()).hexdigest()[:16]
    decryptor = Cipher(algorithms.AES(key_text.encode()), modes.ECB()).decryptor()
    padded_plaintext = decryptor.update(base64.b64decode(encrypted_data)) + decryptor.finalize()
    padding_size = padded_plaintext[-1]
    if padding_size < 1 or padding_size > 16:
        return padded_plaintext.decode("utf-8", errors="replace")
    return padded_plaintext[:-padding_size].decode("utf-8", errors="replace")


def summarize_plaintext(plaintext: str) -> dict[str, Any]:
    try:
        decoded_payload = json.loads(plaintext)
    except json.JSONDecodeError:
        return {
            "json_decoded": False,
            "top_level_keys": [],
            "row_count": 0,
            "spus_count": 0,
            "first_spu_keys": [],
            "first_sku_keys": [],
        }
    row_count = 0
    if isinstance(decoded_payload, dict):
        h5_sku_rows = extract_h5_spu_sku_rows(decoded_payload)
        row_count = len(h5_sku_rows) or len(PublicSourceCrawler.extract_meicai_goods_rows({"data": decoded_payload}))
        spus_payload = decoded_payload.get("spus")
        first_spu = spus_payload[0] if isinstance(spus_payload, list) and spus_payload else {}
        first_sku = h5_sku_rows[0] if h5_sku_rows else {}
        return {
            "json_decoded": True,
            "top_level_keys": sorted(str(key) for key in decoded_payload.keys()),
            "row_count": row_count,
            "spus_count": len(spus_payload) if isinstance(spus_payload, list) else 0,
            "first_spu_keys": sorted(str(key) for key in first_spu.keys()) if isinstance(first_spu, dict) else [],
            "first_sku_keys": sorted(str(key) for key in first_sku.keys()) if isinstance(first_sku, dict) else [],
        }
    if isinstance(decoded_payload, list):
        return {
            "json_decoded": True,
            "top_level_keys": [],
            "row_count": len(decoded_payload),
            "spus_count": 0,
            "first_spu_keys": [],
            "first_sku_keys": [],
        }
    return {
        "json_decoded": True,
        "top_level_keys": [],
        "row_count": 0,
        "spus_count": 0,
        "first_spu_keys": [],
        "first_sku_keys": [],
    }


def extract_h5_spu_sku_rows(decoded_payload: dict[str, Any]) -> list[dict[str, Any]]:
    spus_payload = decoded_payload.get("spus")
    if not isinstance(spus_payload, list):
        return []
    sku_rows: list[dict[str, Any]] = []
    for spu_payload in spus_payload:
        if not isinstance(spu_payload, dict):
            continue
        skus_payload = spu_payload.get("skus")
        if isinstance(skus_payload, list):
            sku_rows.extend(sku_payload for sku_payload in skus_payload if isinstance(sku_payload, dict))
    return sku_rows


def summarize_plaintext_payload(payload: dict[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"top_level_keys": [], "data_keys": [], "row_count": 0}
    data_payload = payload.get("data")
    data_keys = sorted(str(key) for key in data_payload.keys()) if isinstance(data_payload, dict) else []
    return {
        "top_level_keys": sorted(str(key) for key in payload.keys()),
        "data_keys": data_keys,
        "row_count": len(PublicSourceCrawler.extract_meicai_goods_rows(payload)),
    }


def extract_source_from_common_body(common_body: dict[str, Any]) -> str:
    env_payload = common_body.get("_ENV_")
    if not isinstance(env_payload, dict):
        return ""
    return str(env_payload.get("source") or "").strip()


def parse_source_candidates(raw_value: str) -> list[str]:
    return [candidate.strip() for candidate in raw_value.split(",") if candidate.strip()]


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Verify whether Meicai H5 type=3 encrypted class_products data can be decoded server-side."
    )
    argument_parser.add_argument("--secret-env-file", default=str(DEFAULT_SECRET_ENV_FILE))
    argument_parser.add_argument("--sale-class-tree", default=str(DEFAULT_SALE_CLASS_TREE))
    argument_parser.add_argument("--h5-salts-file", default=str(DEFAULT_H5_SALTS_FILE))
    argument_parser.add_argument("--source-candidates", default="")
    argument_parser.add_argument("--base-url", default="https://mall-entrance.yunshanmeicai.com")
    argument_parser.add_argument("--page-size", type=int, default=MEICAI_DEFAULT_PAGE_SIZE)
    parsed_args = argument_parser.parse_args()

    report = build_h5_decryption_report(
        secret_env_file=Path(parsed_args.secret_env_file),
        sale_class_tree=Path(parsed_args.sale_class_tree),
        h5_salts_file=Path(parsed_args.h5_salts_file),
        source_candidates=parse_source_candidates(parsed_args.source_candidates),
        base_url=parsed_args.base_url,
        page_size=max(1, parsed_args.page_size),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
