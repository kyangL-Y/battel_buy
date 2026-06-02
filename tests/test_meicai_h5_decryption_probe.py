from __future__ import annotations

import base64
import hashlib
import json

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from tools.probe_meicai_h5_decryption import (
    MALL_TYPE3_SECRET_SUFFIX,
    build_h5_common_body,
    decrypt_type3_payload,
    extract_h5_spu_sku_rows,
    summarize_plaintext,
)


def test_decrypt_type3_payload_decodes_h5_bundle_contract():
    salt_slice = "abc"
    source_name = "android"
    plaintext_payload = json.dumps({"spus": [{"skus": [{"skuBase": {"skuId": "sku-1"}}]}]}, separators=(",", ":"))
    key_text = hashlib.sha256(f"{salt_slice}{source_name}{MALL_TYPE3_SECRET_SUFFIX}".encode()).hexdigest()[:16]
    padded_payload = plaintext_payload.encode()
    padding_size = 16 - len(padded_payload) % 16
    padded_payload += bytes([padding_size]) * padding_size
    encryptor = Cipher(algorithms.AES(key_text.encode()), modes.ECB()).encryptor()
    encrypted_data = base64.b64encode(encryptor.update(padded_payload) + encryptor.finalize()).decode()

    decoded_payload = decrypt_type3_payload(
        encrypted_data=encrypted_data,
        salt_slice=salt_slice,
        source_name=source_name,
    )

    assert json.loads(decoded_payload)["spus"][0]["skus"][0]["skuBase"]["skuId"] == "sku-1"


def test_build_h5_common_body_refreshes_h5_signature_fields():
    h5_salts_payload = {
        "salts": {"online": ["online-salt"]},
        "saltsType3": "abcdefghijklmnopqrstuvwxyz",
    }
    captured_common_body = {
        "tickets": "ticket",
        "_ENV_": {"source": "web"},
        "mallSaltSign": "old-mall-sign",
        "salt_sign": "old-salt-sign",
        "salt_index": 1,
        "time_stamp": 2,
    }

    h5_common_body = build_h5_common_body(
        captured_common_body=captured_common_body,
        h5_salts_payload=h5_salts_payload,
        request_headers={"Device-Token": "device-token"},
        request_source="android",
    )

    assert h5_common_body["_ENV_"]["source"] == "android"
    assert h5_common_body["_ENV_"]["isH5"] == 1
    assert h5_common_body["mallSaltSign"] != "old-mall-sign"
    assert h5_common_body["salt_sign"] != "old-salt-sign"
    assert "salt_index" not in h5_common_body
    assert "time_stamp" not in h5_common_body


def test_summarize_plaintext_counts_h5_spus_skus_without_values():
    plaintext_payload = json.dumps(
        {
            "spus": [
                {"id": "spu-1", "name": "秘密商品", "skus": [{"skuBase": {"skuId": "secret-sku"}}]},
                {"id": "spu-2", "skus": [{"skuBase": {"skuId": "secret-sku-2"}}]},
            ],
            "is_last_page": False,
        },
        ensure_ascii=False,
    )

    summary = summarize_plaintext(plaintext_payload)
    sku_rows = extract_h5_spu_sku_rows(json.loads(plaintext_payload))
    serialized_summary = json.dumps(summary, ensure_ascii=False)

    assert summary["json_decoded"] is True
    assert summary["spus_count"] == 2
    assert summary["row_count"] == 2
    assert len(sku_rows) == 2
    assert "skuBase" in summary["first_sku_keys"]
    assert "秘密商品" not in serialized_summary
    assert "secret-sku" not in serialized_summary
