import json

import pytest

from tools.extract_meicai_address_context import (
    extract_latest_change_address_context,
    extract_latest_change_address_body,
    write_address_context_env,
)


def test_extract_latest_change_address_body_writes_env(tmp_path):
    capture_path = tmp_path / "meicai_flows.jsonl"
    output_path = tmp_path / "meicai.env"
    request_body = {
        "locationTo": "encrypted-location",
        "city_id": "17",
        "area_id": "4402",
        "tickets": "ticket-value",
        "time_stamp": 1780109580000,
        "salt_index": 12,
        "mallSaltSign": "mall-sign",
        "salt_sign": "salt-sign",
        "_ENV_": {"location": "encrypted-env-location", "source": "android"},
    }
    flow_record = {
        "path": "/api/auth/changeaddress",
        "request_headers": {
            "device-token": "device-token",
            "passport-token": "passport-token",
            "x-mc-city": "17",
            "x-mc-area": "4402",
        },
        "request_text": json.dumps(request_body, ensure_ascii=False),
    }
    capture_path.write_text(json.dumps(flow_record, ensure_ascii=False) + "\n", encoding="utf-8")

    extracted_body = extract_latest_change_address_body(capture_path)
    write_address_context_env(extracted_body, output_path)
    env_text = output_path.read_text(encoding="utf-8")

    assert extracted_body["locationTo"] == "encrypted-location"
    assert env_text.startswith("MEICAI_REQUEST_HEADERS='")
    assert "MEICAI_REQUEST_HEADERS" in env_text
    assert "MEICAI_COMMON_BODY" in env_text
    assert '"request_body"' in env_text
    assert "encrypted-location" in env_text


def test_extract_latest_change_address_context_prefers_feed_common_body(tmp_path):
    capture_path = tmp_path / "meicai_flows.jsonl"
    change_address_body = {
        "locationTo": "encrypted-location",
        "city_id": "17",
        "area_id": "4402",
        "tickets": "ticket-value",
        "time_stamp": 111,
        "salt_index": 12,
        "mallSaltSign": "change-mall-sign",
        "salt_sign": "change-salt-sign",
    }
    feed_body = {
        "city_id": "17",
        "area_id": "4402",
        "tickets": "ticket-value",
        "time_stamp": 222,
        "salt_index": 13,
        "mallSaltSign": "feed-mall-sign",
        "salt_sign": "feed-salt-sign",
        "_ENV_": {"location": "encrypted-env-location", "source": "android"},
    }
    rows = [
        {
            "path": "/api/auth/changeaddress",
            "request_headers": {"passport-token": "passport-token"},
            "request_text": json.dumps(change_address_body, ensure_ascii=False),
        },
        {
            "path": "/entrance/recommend/xbFeed",
            "request_headers": {"passport-token": "passport-token", "x-mc-city": "17"},
            "request_text": json.dumps(feed_body, ensure_ascii=False),
        },
    ]
    capture_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    context = extract_latest_change_address_context(capture_path)

    assert context["address_context"]["request_body"]["salt_sign"] == "change-salt-sign"
    assert context["common_body"]["salt_sign"] == "feed-salt-sign"
    assert context["request_headers"]["passport-token"] == "passport-token"


def test_extract_latest_change_address_body_rejects_redacted_capture(tmp_path):
    capture_path = tmp_path / "meicai_flows.jsonl"
    request_body = {
        "locationTo": "encrypted-location",
        "city_id": "17",
        "area_id": "4402",
        "tickets": "<redacted>",
        "time_stamp": 1780109580000,
        "salt_index": 12,
        "mallSaltSign": "mall-sign",
        "salt_sign": "salt-sign",
    }
    flow_record = {
        "path": "/api/auth/changeaddress",
        "request_text": json.dumps(request_body, ensure_ascii=False),
    }
    capture_path.write_text(json.dumps(flow_record, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="已脱敏"):
        extract_latest_change_address_body(capture_path)
