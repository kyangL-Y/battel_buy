import json
import subprocess

import pytest

from tools.extract_kuailv_h5_context import extract_latest_kuailv_h5_context, write_kuailv_env


def test_extract_kuailv_context_from_jsonl_goods_request(tmp_path):
    capture_path = tmp_path / "kuailv_flows.jsonl"
    output_path = tmp_path / "kuailv.env"
    flow_record = {
        "url": (
            "https://klmall.meituan.com/wxmall/api/goods/list"
            "?gtCityId=320100&selectedPoiAddressId=poi-secret&selectedSalesGridId=grid-secret"
            "&uaEnv=other&loginAcctType=99&uuid=uuid-secret"
        ),
        "request_headers": {
            "User-Agent": "ua-secret",
            "Cookie": "token=secret-cookie; acct=secret-account",
            "Content-Length": "123",
        },
        "request_text": json.dumps({"cat1Id": "9", "cat2Id": "91", "pageSize": 20}, ensure_ascii=False),
    }
    capture_path.write_text(json.dumps(flow_record, ensure_ascii=False) + "\n", encoding="utf-8")

    context = extract_latest_kuailv_h5_context(capture_path)
    write_kuailv_env(context, output_path)
    env_text = output_path.read_text(encoding="utf-8")

    assert context["source_path"] == "/wxmall/api/goods/list"
    assert context["has_goods_request"] is True
    assert context["cookies"] == {"token": "secret-cookie", "acct": "secret-account"}
    assert context["request_headers"] == {"User-Agent": "ua-secret"}
    assert context["address_context"]["selectedPoiAddressId"] == "poi-secret"
    assert context["address_context"]["selectedSalesGridId"] == "grid-secret"
    assert context["address_context"]["cat1_id"] == "9"
    assert context["address_context"]["cat2_id"] == "91"
    assert "KUAILV_COOKIES=" in env_text
    assert "KUAILV_REQUEST_HEADERS=" in env_text
    assert "KUAILV_ADDRESS_CONTEXT=" in env_text
    assert "KUAILV_CITY_ID=320100" in env_text
    assert "KUAILV_CAT1_ID=9" in env_text
    assert "KUAILV_CAT2_ID=91" in env_text


def test_extract_kuailv_context_from_har_category_request(tmp_path):
    capture_path = tmp_path / "kuailv.har"
    har_payload = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": (
                            "https://klmall.meituan.com/wxmall/api/goods/category/first/list"
                            "?gtCityId=320100&selectedPoiAddressId=poi-secret&uaEnv=other&loginAcctType=99"
                        ),
                        "headers": [{"name": "User-Agent", "value": "ua-secret"}],
                        "cookies": [{"name": "token", "value": "secret-cookie"}],
                    }
                }
            ]
        }
    }
    capture_path.write_text(json.dumps(har_payload, ensure_ascii=False), encoding="utf-8")

    context = extract_latest_kuailv_h5_context(capture_path)

    assert context["source_path"] == "/wxmall/api/goods/category/first/list"
    assert context["has_goods_request"] is False
    assert context["cookies"]["token"] == "secret-cookie"
    assert context["address_context"]["selectedPoiAddressId"] == "poi-secret"


def test_extract_kuailv_context_rejects_redacted_capture(tmp_path):
    capture_path = tmp_path / "kuailv_flows.jsonl"
    flow_record = {
        "url": "https://klmall.meituan.com/wxmall/api/goods/category/first/list?gtCityId=320100",
        "request_headers": {"Cookie": "token=<redacted>"},
    }
    capture_path.write_text(json.dumps(flow_record, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="已脱敏"):
        extract_latest_kuailv_h5_context(capture_path)


def test_extract_kuailv_context_cli_does_not_print_secret_values(tmp_path):
    capture_path = tmp_path / "kuailv_flows.jsonl"
    output_path = tmp_path / "kuailv.env"
    flow_record = {
        "url": "https://klmall.meituan.com/wxmall/api/goods/category/first/list?gtCityId=320100&selectedPoiAddressId=poi-secret",
        "request_headers": {"Cookie": "token=secret-cookie", "User-Agent": "ua-secret"},
    }
    capture_path.write_text(json.dumps(flow_record, ensure_ascii=False) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [
            "python",
            "tools/extract_kuailv_h5_context.py",
            "--input",
            str(capture_path),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_path.exists()
    assert "secret-cookie" not in completed.stdout
    assert "ua-secret" not in completed.stdout
    assert "poi-secret" not in completed.stdout
    assert "context_keys=gtCityId,selectedPoiAddressId" in completed.stdout
