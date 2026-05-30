from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawler.public_source_crawlers import (
    MEICAI_DEFAULT_PAGE_SIZE,
    MeicaiAppGatewayClient,
    PublicSourceCrawler,
)
from services.meicai_category_mapping import suggest_meicai_internal_category


DEFAULT_OUTPUT_PATH = Path("tmp/meicai_category_candidates.json")
DEFAULT_SECRET_ENV_FILE = Path(".local-secrets/meicai_address_context.env")
XB_FEED_ENDPOINT = "/entrance/recommend/xbFeed"
ENCRYPTED_CLASS_PRODUCTS_ENDPOINT = "/entrance/dishes/getSpusByClass"
PLAINTEXT_FEED_COVERAGE_SCOPE = "plaintext_xbfeed_goods_only"
CLASS_PRODUCTS_EXCLUSION_REASON = "getSpusByClass data is encrypted and is not decoded by this plaintext chain"


def collect_meicai_category_candidates(
    payloads: list[dict[str, Any]] | list[tuple[dict[str, Any], str]],
    *,
    source_filter: str = "",
) -> list[dict[str, Any]]:
    grouped_candidates: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for payload_item in payloads:
        if isinstance(payload_item, tuple):
            payload, payload_source_filter = payload_item
        else:
            payload = payload_item
            payload_source_filter = source_filter
        if PublicSourceCrawler._meicai_payload_is_encrypted(payload):
            raise RuntimeError("美菜接口返回加密 data，按约定不转 OCR")
        for goods_row in PublicSourceCrawler.extract_meicai_goods_rows(payload):
            sku_base = goods_row.get("skuBase") if isinstance(goods_row.get("skuBase"), dict) else {}
            sale_c1_id = _clean_text(sku_base.get("saleC1Id") or goods_row.get("saleC1Id"))
            sale_c2_id = _clean_text(sku_base.get("saleC2Id") or goods_row.get("saleC2Id"))
            sale_c1_name = _clean_text(sku_base.get("saleC1Name") or goods_row.get("saleC1Name"))
            sale_c2_name = _clean_text(sku_base.get("saleC2Name") or goods_row.get("saleC2Name"))
            bi_name = _clean_text(sku_base.get("biName") or goods_row.get("biName"))
            bi_alias_name = _clean_text(sku_base.get("biAliasName") or goods_row.get("biAliasName"))
            sku_name = _clean_text(
                sku_base.get("skuName")
                or sku_base.get("spuName")
                or goods_row.get("skuName")
                or goods_row.get("name")
            )
            if not any((sale_c1_id, sale_c2_id, sale_c1_name, sale_c2_name, bi_name, bi_alias_name)):
                continue

            candidate_key = (sale_c1_id, sale_c2_id, sale_c1_name, sale_c2_name, bi_name)
            if candidate_key not in grouped_candidates:
                grouped_candidates[candidate_key] = {
                    "saleC1Id": sale_c1_id or None,
                    "saleC2Id": sale_c2_id or None,
                    "saleC1Name": sale_c1_name or None,
                    "saleC2Name": sale_c2_name or None,
                    "biName": bi_name or None,
                    "biAliasNames": [],
                    "sampleSkuNames": [],
                    "sourceFilters": [],
                    "count": 0,
                    "_alias_counter": Counter(),
                    "_sample_counter": Counter(),
                    "_source_counter": Counter(),
                }
            candidate = grouped_candidates[candidate_key]
            candidate["count"] += 1
            if bi_alias_name:
                candidate["_alias_counter"][bi_alias_name] += 1
            if sku_name:
                candidate["_sample_counter"][sku_name] += 1
            if payload_source_filter:
                candidate["_source_counter"][payload_source_filter] += 1

    ordered_candidates = sorted(
        grouped_candidates.values(),
        key=lambda item: (
            str(item.get("saleC1Id") or ""),
            str(item.get("saleC2Id") or ""),
            str(item.get("saleC1Name") or ""),
            str(item.get("saleC2Name") or ""),
            str(item.get("biName") or ""),
        ),
    )
    for candidate in ordered_candidates:
        candidate["biAliasNames"] = _counter_keys(candidate.pop("_alias_counter"))
        candidate["sampleSkuNames"] = _counter_keys(candidate.pop("_sample_counter"), limit=5)
        candidate["sourceFilters"] = _counter_keys(candidate.pop("_source_counter"))
    return ordered_candidates


def load_meicai_payloads(input_path: Path) -> list[dict[str, Any]]:
    if not input_path.exists():
        raise RuntimeError(f"输入文件不存在: {input_path}")
    raw_text = input_path.read_text(encoding="utf-8-sig").strip()
    if not raw_text:
        return []
    if input_path.suffix.lower() == ".jsonl":
        payloads: list[dict[str, Any]] = []
        for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            parsed_line = json.loads(line)
            payload = _payload_from_capture_record(parsed_line)
            if isinstance(payload, dict):
                payloads.append(payload)
            else:
                raise RuntimeError(f"输入文件第 {line_number} 行不是美菜响应 JSON object")
        return payloads

    parsed_payload = json.loads(raw_text)
    if isinstance(parsed_payload, dict):
        return [parsed_payload]
    if isinstance(parsed_payload, list):
        return [item for item in parsed_payload if isinstance(item, dict)]
    raise RuntimeError("输入 JSON 必须是 object 或 object array")


def load_meicai_candidate_rows(input_path: Path) -> list[dict[str, Any]]:
    if not input_path.exists() or input_path.suffix.lower() != ".json":
        return []
    raw_text = input_path.read_text(encoding="utf-8-sig").strip()
    if not raw_text:
        return []
    parsed_rows = json.loads(raw_text)
    if isinstance(parsed_rows, dict):
        parsed_rows = parsed_rows.get("candidates")
    if not isinstance(parsed_rows, list):
        return []
    candidate_rows = [item for item in parsed_rows if isinstance(item, dict)]
    if not candidate_rows:
        return []
    if not all(any(key in item for key in ("saleC1Id", "saleC2Id", "biName", "sampleSkuNames")) for item in candidate_rows):
        return []
    return candidate_rows


def fetch_meicai_payloads(
    *,
    secret_env_file: Path,
    category_filters: list[dict[str, str]],
    max_pages: int,
    page_size: int,
    base_url: str,
    sleep_seconds: float = 0.0,
) -> list[tuple[dict[str, Any], str]]:
    PublicSourceCrawler._load_env_file_if_configured("MEICAI_SECRET_ENV_FILE")
    if secret_env_file.exists():
        with _temporary_secret_env(secret_env_file):
            return _fetch_meicai_payloads_with_current_env(
                category_filters=category_filters,
                max_pages=max_pages,
                page_size=page_size,
                base_url=base_url,
                sleep_seconds=sleep_seconds,
            )
    return _fetch_meicai_payloads_with_current_env(
        category_filters=category_filters,
        max_pages=max_pages,
        page_size=page_size,
        base_url=base_url,
        sleep_seconds=sleep_seconds,
    )


def write_meicai_category_candidates(candidate_export: list[dict[str, Any]] | dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(candidate_export, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def attach_internal_category_mappings(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        mapping = suggest_meicai_internal_category(candidate)
        mapped_candidate = dict(candidate)
        mapped_candidate.update(
            {
                "internalCategory": mapping.category,
                "internalMarketCategory": mapping.market_category,
                "liancaiTopCategory": mapping.liancai_top_category,
                "liancaiSubcategory": mapping.liancai_subcategory,
                "mappingSource": mapping.source,
                "mappingConfidence": mapping.confidence,
            }
        )
        mapped_candidates.append(mapped_candidate)
    return mapped_candidates


def build_meicai_category_candidates_output(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_endpoint": XB_FEED_ENDPOINT,
        "coverage": PLAINTEXT_FEED_COVERAGE_SCOPE,
        "excluded_endpoint": ENCRYPTED_CLASS_PRODUCTS_ENDPOINT,
        "exclusion_reason": CLASS_PRODUCTS_EXCLUSION_REASON,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def _fetch_meicai_payloads_with_current_env(
    *,
    category_filters: list[dict[str, str]],
    max_pages: int,
    page_size: int,
    base_url: str,
    sleep_seconds: float = 0.0,
) -> list[tuple[dict[str, Any], str]]:
    request_headers = PublicSourceCrawler._load_json_env_object("MEICAI_REQUEST_HEADERS")
    common_body = PublicSourceCrawler._load_json_env_object("MEICAI_COMMON_BODY")
    address_context = PublicSourceCrawler._load_json_env_object("MEICAI_ADDRESS_CONTEXT")
    client = MeicaiAppGatewayClient(
        base_url=base_url,
        request_headers={str(key): str(value) for key, value in request_headers.items()},
        common_body=common_body,
    )
    city_id = "17"
    area_id = "4402"
    address_body = address_context.get("request_body")
    if isinstance(address_body, dict):
        city_id = _clean_text(address_body.get("city_id")) or city_id
        area_id = _clean_text(address_body.get("area_id")) or area_id
        response_payload = client.change_address(address_body)
        if int(response_payload.get("ret") or response_payload.get("code") or 0) != 1:
            raise RuntimeError("美菜地址切换失败，请刷新 MEICAI_ADDRESS_CONTEXT 或登录态")

    payloads: list[tuple[dict[str, Any], str]] = []
    for category_filter in category_filters:
        category_name = category_filter.get("category") or category_filter.get("class1_id") or "live"
        class1_id = category_filter.get("class1_id") or "-1"
        class2_id = category_filter.get("class2_id") or ""
        for page in range(1, max_pages + 1):
            payload = client.xb_feed(
                page=page,
                page_size=page_size,
                class1_id=class1_id,
                class2_id=class2_id,
                city_id=city_id,
                area_id=area_id,
            )
            payloads.append((payload, category_name))
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            goods_rows = PublicSourceCrawler.extract_meicai_goods_rows(payload)
            if len(goods_rows) < page_size:
                break
    return payloads


class _temporary_secret_env:
    def __init__(self, secret_env_file: Path) -> None:
        self.secret_env_file = secret_env_file
        self.previous_value: str | None = None

    def __enter__(self) -> None:
        import os

        self.previous_value = os.environ.get("MEICAI_SECRET_ENV_FILE")
        os.environ["MEICAI_SECRET_ENV_FILE"] = str(self.secret_env_file)
        PublicSourceCrawler._load_env_file_if_configured("MEICAI_SECRET_ENV_FILE")

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        import os

        if self.previous_value is None:
            os.environ.pop("MEICAI_SECRET_ENV_FILE", None)
        else:
            os.environ["MEICAI_SECRET_ENV_FILE"] = self.previous_value


def _payload_from_capture_record(parsed_record: Any) -> dict[str, Any] | None:
    if not isinstance(parsed_record, dict):
        return None
    for response_key in ("response_json", "response_body", "response_text", "response"):
        response_value = parsed_record.get(response_key)
        if isinstance(response_value, dict):
            return response_value
        if isinstance(response_value, str) and response_value.strip():
            decoded_response = json.loads(response_value)
            return decoded_response if isinstance(decoded_response, dict) else None
    if "data" in parsed_record or "ret" in parsed_record or "code" in parsed_record:
        return parsed_record
    return None


def _counter_keys(counter: Counter[str], *, limit: int | None = None) -> list[str]:
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    if limit is not None:
        items = items[:limit]
    return [key for key, _ in items]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _parse_category_filters(raw_filters: str) -> list[dict[str, str]]:
    if not raw_filters.strip():
        return [{"category": "推荐商品", "class1_id": "-1", "class2_id": ""}]
    parsed_filters = json.loads(raw_filters)
    if not isinstance(parsed_filters, list):
        raise RuntimeError("--category-filters 必须是 JSON array")
    return [
        {
            "category": _clean_text(item.get("category")),
            "class1_id": _clean_text(item.get("class1_id") or "-1"),
            "class2_id": _clean_text(item.get("class2_id")),
        }
        for item in parsed_filters
        if isinstance(item, dict)
    ]


def load_category_filters_from_sale_class_tree(tree_path: Path) -> list[dict[str, str]]:
    if not tree_path.exists():
        raise RuntimeError(f"美菜 saleClass 树文件不存在: {tree_path}")
    payload = json.loads(tree_path.read_text(encoding="utf-8-sig"))
    flat_rows = payload.get("flat") if isinstance(payload, dict) else None
    if not isinstance(flat_rows, list):
        raise RuntimeError("美菜 saleClass 树文件缺少 flat 数组")
    category_filters: list[dict[str, str]] = []
    for row in flat_rows:
        if not isinstance(row, dict):
            continue
        class1_id = _clean_text(row.get("saleC1Id"))
        class2_id = _clean_text(row.get("saleC2Id"))
        if not class1_id:
            continue
        class1_name = _clean_text(row.get("saleC1Name"))
        class2_name = _clean_text(row.get("saleC2Name"))
        category_filters.append(
            {
                "category": " / ".join(part for part in (class1_name, class2_name) if part) or class1_id,
                "class1_id": class1_id,
                "class2_id": class2_id,
            }
        )
    return category_filters


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description=(
            "Extract category candidates from plaintext Meicai xbFeed payloads only; "
            "does not decode getSpusByClass encrypted product lists."
        )
    )
    argument_parser.add_argument("--input", "-i", help="Offline xbFeed JSON or JSONL capture file.")
    argument_parser.add_argument(
        "--output",
        "-o",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Output JSON path.",
    )
    argument_parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch low-frequency xbFeed pages with current MEICAI_* env.",
    )
    argument_parser.add_argument(
        "--secret-env-file",
        default=str(DEFAULT_SECRET_ENV_FILE),
        help="Private env file containing MEICAI_* values.",
    )
    argument_parser.add_argument("--max-pages", type=int, default=1)
    argument_parser.add_argument("--page-size", type=int, default=MEICAI_DEFAULT_PAGE_SIZE)
    argument_parser.add_argument(
        "--base-url",
        default="https://mall-entrance.yunshanmeicai.com",
    )
    argument_parser.add_argument(
        "--category-filters",
        default='[{"category":"推荐商品","class1_id":"-1","class2_id":""},{"category":"蔬菜","class1_id":"6506","class2_id":""},{"category":"酒水饮料","class1_id":"6511","class2_id":""}]',
        help="JSON array of category/class filters for live mode.",
    )
    argument_parser.add_argument(
        "--sale-class-tree",
        help="Use saleClass flat rows as xbFeed live filters; this does not fetch encrypted class product lists.",
    )
    argument_parser.add_argument(
        "--limit-filters",
        type=int,
        default=0,
        help="Limit live filters for smoke tests. 0 means no limit.",
    )
    argument_parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Sleep between live xbFeed requests.",
    )
    parsed_arguments = argument_parser.parse_args()

    if parsed_arguments.live:
        if parsed_arguments.sale_class_tree:
            category_filters = load_category_filters_from_sale_class_tree(Path(parsed_arguments.sale_class_tree))
        else:
            category_filters = _parse_category_filters(parsed_arguments.category_filters)
        if parsed_arguments.limit_filters > 0:
            category_filters = category_filters[: parsed_arguments.limit_filters]
        payloads = fetch_meicai_payloads(
            secret_env_file=Path(parsed_arguments.secret_env_file),
            category_filters=category_filters,
            max_pages=max(1, parsed_arguments.max_pages),
            page_size=max(1, parsed_arguments.page_size),
            base_url=parsed_arguments.base_url,
            sleep_seconds=max(0.0, parsed_arguments.sleep_seconds),
        )
        candidates = collect_meicai_category_candidates(payloads, source_filter="live")
    elif parsed_arguments.input:
        input_path = Path(parsed_arguments.input)
        candidates = load_meicai_candidate_rows(input_path)
        if not candidates:
            payloads = load_meicai_payloads(input_path)
            candidates = collect_meicai_category_candidates(payloads, source_filter=input_path.name)
    else:
        raise RuntimeError("必须指定 --input 或 --live")

    candidates = attach_internal_category_mappings(candidates)
    output_path = Path(parsed_arguments.output)
    write_meicai_category_candidates(build_meicai_category_candidates_output(candidates), output_path)
    print(f"wrote {len(candidates)} category candidates to {output_path}")


if __name__ == "__main__":
    main()
