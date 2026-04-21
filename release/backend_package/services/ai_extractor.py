from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

import requests

from utils.config_loader import BASE_DIR


@dataclass
class AIExtractorError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class StructuredProductCandidate:
    row_index: int
    source_text: str
    product_name: str | None = None
    group_name: str | None = None
    category: str | None = None
    brand: str | None = None
    product_series: str | None = None
    spec_text: str | None = None

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "row_index": self.row_index,
            "source_text": self.source_text,
            "product_name": self.product_name,
            "group_name": self.group_name,
            "category": self.category,
            "brand": self.brand,
            "product_series": self.product_series,
            "spec_text": self.spec_text,
        }


DEFAULT_AI_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "row_index": {"type": "integer"},
                    "category": {"type": ["string", "null"]},
                    "brand": {"type": ["string", "null"]},
                    "product_series": {"type": ["string", "null"]},
                    "spec_text": {"type": ["string", "null"]},
                    "remarks": {"type": ["string", "null"]},
                },
                "required": ["row_index", "category", "brand", "product_series", "spec_text", "remarks"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


SYSTEM_PROMPT = """
你是商品报价单结构化助手。
任务：根据输入的中文商品文本，尽量拆分并补全 category、brand、product_series、spec_text、remarks。
要求：
1. 只能根据给定文本谨慎提取，不要臆造不存在的信息。
2. 无法判断时返回 null。
3. spec_text 保留原始规格表达，例如 500ml、900g*10、1L、250g×4。
4. product_series 填写商品系列/型号，不要把品牌重复写进去。
5. 只输出符合 JSON Schema 的结果。
""".strip()


USER_PROMPT_TEMPLATE = """
请处理以下商品行，输出结构化 JSON：
{payload}
""".strip()


DEFAULT_SEARCH_SYSTEM_PROMPT = """
你是联网搜索助手。
请基于联网搜索结果回答用户问题，优先给出简洁、可核对的结论。
如果信息不确定，要明确说明不确定。
""".strip()


DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LOCAL_ENV_PATHS = [BASE_DIR / ".env.local", BASE_DIR / ".env"]
ENV_LINE_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")


def is_ai_extraction_enabled(runtime_config: dict[str, Any] | None) -> bool:
    ai_config = (runtime_config or {}).get("ai", {})
    return bool(ai_config.get("enabled"))


def get_ai_config(runtime_config: dict[str, Any] | None) -> dict[str, Any]:
    return dict((runtime_config or {}).get("ai", {}))


def _strip_env_value(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1].strip()
    return text


def _read_local_env_value(env_name: str) -> str | None:
    for path in LOCAL_ENV_PATHS:
        if not path.exists():
            continue
        try:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                match = ENV_LINE_PATTERN.match(line)
                if not match:
                    continue
                key, value = match.groups()
                if key != env_name:
                    continue
                normalized_value = _strip_env_value(value)
                if normalized_value:
                    return normalized_value
        except OSError:
            continue
    return None


def get_api_key(runtime_config: dict[str, Any] | None) -> str | None:
    ai_config = get_ai_config(runtime_config)
    env_name = str(ai_config.get("api_key_env") or "DASHSCOPE_API_KEY").strip()
    if not env_name:
        env_name = "DASHSCOPE_API_KEY"
    api_key = os.getenv(env_name)
    if isinstance(api_key, str) and api_key.strip():
        return api_key.strip()
    return _read_local_env_value(env_name)


def can_use_ai_extraction(runtime_config: dict[str, Any] | None) -> bool:
    return is_ai_extraction_enabled(runtime_config) and bool(get_api_key(runtime_config))


def normalize_ai_item(item: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {"row_index": item.get("row_index")}
    for field in ["category", "brand", "product_series", "spec_text", "remarks"]:
        value = item.get(field)
        if value is None:
            normalized[field] = None
            continue
        text = str(value).strip()
        normalized[field] = text or None
    return normalized


def parse_ai_response_text(text: str) -> list[dict[str, Any]]:
    if not text.strip():
        raise AIExtractorError("AI 返回内容为空")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIExtractorError(f"AI 返回 JSON 解析失败：{exc}") from exc

    items = payload.get("items")
    if not isinstance(items, list):
        raise AIExtractorError("AI 返回格式无效：缺少 items 列表")
    return [normalize_ai_item(item) for item in items if isinstance(item, dict)]


def build_qwen_chat_payload(rows: list[dict[str, Any]], model: str) -> dict[str, Any]:
    payload = json.dumps(rows, ensure_ascii=False, indent=2)
    return build_qwen_messages_payload(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(payload=payload)},
        ],
        model=model,
        temperature=0.1,
        response_format={"type": "json_object"},
    )


def build_qwen_messages_payload(
    messages: list[dict[str, Any]],
    model: str,
    *,
    temperature: float = 0.1,
    response_format: dict[str, Any] | None = None,
    enable_search: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format is not None:
        payload["response_format"] = response_format
    if enable_search:
        payload["enable_search"] = True
    return payload


def extract_qwen_response_text(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIExtractorError("AI 返回格式无效：缺少 choices")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise AIExtractorError("AI 返回格式无效：缺少 message")

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts).strip()

    raise AIExtractorError("AI 返回格式无效：缺少文本内容")


def call_qwen_chat_completion(
    rows: list[dict[str, Any]],
    api_key: str,
    model: str,
    timeout_seconds: int,
    base_url: str,
) -> list[dict[str, Any]]:
    response_text = call_qwen_chat_completion_text(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(payload=json.dumps(rows, ensure_ascii=False, indent=2))},
        ],
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
        base_url=base_url,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return parse_ai_response_text(response_text)


def call_qwen_chat_completion_text(
    messages: list[dict[str, Any]],
    api_key: str,
    model: str,
    timeout_seconds: int,
    base_url: str,
    *,
    temperature: float = 0.1,
    response_format: dict[str, Any] | None = None,
    enable_search: bool = False,
) -> str:
    target_url = f"{base_url.rstrip('/')}/chat/completions"
    response = requests.post(
        target_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=build_qwen_messages_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format=response_format,
            enable_search=enable_search,
        ),
        timeout=timeout_seconds,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text.strip()
        if detail:
            raise AIExtractorError(f"AI 请求失败：HTTP {response.status_code} | {detail}") from exc
        raise AIExtractorError(f"AI 请求失败：HTTP {response.status_code}") from exc

    try:
        response_payload = response.json()
    except ValueError as exc:
        raise AIExtractorError("AI 返回不是合法 JSON") from exc

    return extract_qwen_response_text(response_payload)


def run_search_query(query: str, runtime_config: dict[str, Any] | None = None) -> str:
    search_query = str(query or "").strip()
    if not search_query:
        raise AIExtractorError("搜索内容不能为空")
    if not is_ai_extraction_enabled(runtime_config):
        raise AIExtractorError("AI 功能未启用")

    api_key = get_api_key(runtime_config)
    if not api_key:
        raise AIExtractorError("未配置 AI API Key")

    ai_config = get_ai_config(runtime_config)
    provider = str(ai_config.get("provider") or "qwen").strip().lower() or "qwen"
    if provider != "qwen":
        raise AIExtractorError(f"当前暂不支持 provider={provider} 的联网搜索")

    model = str(ai_config.get("model") or "qwen-plus").strip() or "qwen-plus"
    base_url = str(ai_config.get("base_url") or DEFAULT_QWEN_BASE_URL).strip() or DEFAULT_QWEN_BASE_URL
    timeout_seconds = int(ai_config.get("timeout_seconds") or 20)

    return call_qwen_chat_completion_text(
        messages=[
            {"role": "system", "content": DEFAULT_SEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": search_query},
        ],
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
        base_url=base_url,
        temperature=0.2,
        enable_search=True,
    )


def extract_product_fields(
    rows: list[dict[str, Any]],
    runtime_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    if not is_ai_extraction_enabled(runtime_config):
        raise AIExtractorError("AI 辅助拆分未启用")

    api_key = get_api_key(runtime_config)
    if not api_key:
        raise AIExtractorError("未配置 AI API Key")

    ai_config = get_ai_config(runtime_config)
    provider = str(ai_config.get("provider") or "qwen").strip().lower() or "qwen"
    model = str(ai_config.get("model") or "qwen-plus").strip() or "qwen-plus"
    timeout_seconds = int(ai_config.get("timeout_seconds") or 20)

    if provider == "qwen":
        base_url = str(ai_config.get("base_url") or DEFAULT_QWEN_BASE_URL).strip() or DEFAULT_QWEN_BASE_URL
        return call_qwen_chat_completion(
            rows=rows,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            base_url=base_url,
        )

    if provider == "anthropic":
        try:
            import anthropic
        except ImportError as exc:
            raise AIExtractorError("未安装 anthropic 依赖，请执行 py -3.8 -m pip install anthropic") from exc

        payload = json.dumps(rows, ensure_ascii=False, indent=2)
        client = anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds)
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(payload=payload),
                }
            ],
            output_config={"format": {"type": "json_schema", "schema": DEFAULT_AI_SCHEMA}},
        )
        response_text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        return parse_ai_response_text(response_text)

    raise AIExtractorError(f"当前 AI 提供商暂未接入：{provider}")
