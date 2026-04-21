import requests

from services.ai_extractor import (
    AIExtractorError,
    build_qwen_chat_payload,
    call_qwen_chat_completion,
    call_qwen_chat_completion_text,
    extract_qwen_response_text,
    get_api_key,
    parse_ai_response_text,
    run_search_query,
)


def test_get_api_key_reads_dashscope_env(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", " test-key ")

    result = get_api_key({"ai": {"api_key_env": "DASHSCOPE_API_KEY"}})

    assert result == "test-key"


def test_get_api_key_reads_local_env_when_process_env_missing(monkeypatch, tmp_path):
    env_file = tmp_path / ".env.local"
    env_file.write_text("DASHSCOPE_API_KEY=local-test-key\n", encoding="utf-8")
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("services.ai_extractor.LOCAL_ENV_PATHS", [env_file])

    result = get_api_key({"ai": {"api_key_env": "DASHSCOPE_API_KEY"}})

    assert result == "local-test-key"


def test_build_qwen_chat_payload_contains_messages_and_json_mode():
    payload = build_qwen_chat_payload([{"row_index": 1, "source_text": "海天味极鲜500ml"}], model="qwen-plus")

    assert payload["model"] == "qwen-plus"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"


def test_extract_qwen_response_text_supports_string_content():
    payload = {
        "choices": [
            {
                "message": {
                    "content": '{"items": [{"row_index": 1, "category": "酱油", "brand": "海天", "product_series": "味极鲜", "spec_text": "500ml", "remarks": null}]}'
                }
            }
        ]
    }

    result = extract_qwen_response_text(payload)

    assert '"items"' in result


def test_call_qwen_chat_completion_parses_response(monkeypatch):
    class FakeResponse:
        status_code = 200
        text = "ok"

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"items": [{"row_index": 1, "category": "酱油", "brand": "海天", "product_series": "味极鲜", "spec_text": "500ml", "remarks": "AI补全"}]}'
                        }
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        assert url == "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        assert headers["Authorization"] == "Bearer demo-key"
        assert json["model"] == "qwen-plus"
        assert timeout == 20
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    result = call_qwen_chat_completion(
        rows=[{"row_index": 1, "source_text": "海天味极鲜500ml"}],
        api_key="demo-key",
        model="qwen-plus",
        timeout_seconds=20,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    assert result == [
        {
            "row_index": 1,
            "category": "酱油",
            "brand": "海天",
            "product_series": "味极鲜",
            "spec_text": "500ml",
            "remarks": "AI补全",
        }
    ]


def test_call_qwen_chat_completion_raises_readable_error_on_http_failure(monkeypatch):
    class FakeResponse:
        status_code = 401
        text = '{"error":"invalid api key"}'

        def raise_for_status(self):
            raise requests.HTTPError("401 Client Error")

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: FakeResponse())

    try:
        call_qwen_chat_completion(
            rows=[{"row_index": 1, "source_text": "海天味极鲜500ml"}],
            api_key="bad-key",
            model="qwen-plus",
            timeout_seconds=20,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        raise AssertionError("expected AIExtractorError")
    except AIExtractorError as exc:
        assert "HTTP 401" in str(exc)
        assert "invalid api key" in str(exc)


def test_call_qwen_chat_completion_text_passes_enable_search(monkeypatch):
    captured_request: dict[str, object] = {}

    class FakeResponse:
        status_code = 200
        text = "ok"

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "今日要闻：示例搜索结果"
                        }
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        captured_request["url"] = url
        captured_request["headers"] = headers
        captured_request["json"] = json
        captured_request["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    result = call_qwen_chat_completion_text(
        messages=[{"role": "user", "content": "今天的新闻"}],
        api_key="demo-key",
        model="qwen-plus",
        timeout_seconds=20,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        enable_search=True,
    )

    assert result == "今日要闻：示例搜索结果"
    assert captured_request["json"]["enable_search"] is True


def test_run_search_query_requires_non_empty_query():
    try:
        run_search_query("", runtime_config={"ai": {"enabled": True}})
        raise AssertionError("expected AIExtractorError")
    except AIExtractorError as exc:
        assert "搜索内容不能为空" in str(exc)


def test_parse_ai_response_text_rejects_invalid_json():
    try:
        parse_ai_response_text("not-json")
        raise AssertionError("expected AIExtractorError")
    except AIExtractorError as exc:
        assert "JSON 解析失败" in str(exc)
