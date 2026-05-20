from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Callable

from crawler.api_fetcher import ApiFetcher
from crawler.base import BaseFetcher, FetchResult
from crawler.playwright_fetcher import PlaywrightFetcher
from crawler.requests_fetcher import RequestsFetcher
from crawler.public_source_crawlers import PublicSourceCrawler
from crawler.source_strategies import (
    ApiBatchSourceStrategy,
    BrowserAssistedSourceStrategy,
    CnhnbMarketBatchSourceStrategy,
    ChinapriceBatchSourceStrategy,
    HenanFgwPriceBatchSourceStrategy,
    HnnhgscBatchSourceStrategy,
    LiancaiAppGatewayBatchSourceStrategy,
    LiancaiH5BatchSourceStrategy,
    MoaWholesaleBatchSourceStrategy,
    PfscChartBatchSourceStrategy,
    SingleSourceStrategy,
    ZznyClzArticleBatchSourceStrategy,
)
from parsers.api_parser import ApiParser
from parsers.normalizer import normalize_product_metadata
from parsers.site_parser import SiteParser
from storage.database import Database
from utils.logger import setup_logger


def normalize_liancai_image_url(value: str | None) -> str | None:
    url = str(value or "").strip()
    if not url:
        return None
    if re.match(r"^https?://mst\.liancaiwang\.cn/upload/", url, flags=re.IGNORECASE):
        return re.sub(
            r"^https?://mst\.liancaiwang\.cn/upload/",
            "https://cdnlcw.liancaiwang.cn/",
            url,
            flags=re.IGNORECASE,
        )
    return url


def build_success_raw_payload(
    parsed: dict[str, Any],
    metadata: dict[str, Any],
    site_name: str | None = None,
) -> dict[str, Any]:
    return {}


def _compact_key_part(value: Any) -> str:
    return str(value or "").strip().replace(" ", "")


def _join_compact_key(base_key: str, parts: list[Any], fallback: Any) -> str:
    compact_parts = [_compact_key_part(part) for part in parts if _compact_key_part(part)]
    suffix = "-".join(compact_parts) if compact_parts else _compact_key_part(fallback)
    return f"{base_key}::{suffix}" if suffix else str(base_key)


class PriceCrawlerService:
    def __init__(
        self,
        database: Database,
        site_rules: list[dict],
        fetcher: BaseFetcher | None = None,
        fallback_to_playwright: bool = True,
        site_rule_store=None,
        auto_learn_site_rules: bool = True,
        enable_api_discovery: bool = True,
        api_timeout: int = 15,
        api_retries: int = 1,
        public_source_max_workers: int = 1,
    ) -> None:
        self.database = database
        self.fetcher = fetcher or RequestsFetcher()
        self.playwright_fetcher = PlaywrightFetcher()
        self.fallback_to_playwright = fallback_to_playwright
        self.parser = SiteParser(site_rules)
        self.api_fetcher = ApiFetcher(timeout=api_timeout, retries=api_retries)
        self.api_parser = ApiParser()
        self.site_rule_store = site_rule_store
        self.auto_learn_site_rules = auto_learn_site_rules
        self.enable_api_discovery = enable_api_discovery
        self.logger = setup_logger()
        self.public_source_crawler = PublicSourceCrawler(
            timeout=api_timeout,
            default_max_workers=public_source_max_workers,
        )
        self.progress_callback: Callable[[dict[str, Any]], None] | None = None
        self.source_strategies = [
            ChinapriceBatchSourceStrategy(),
            PfscChartBatchSourceStrategy(),
            MoaWholesaleBatchSourceStrategy(),
            HnnhgscBatchSourceStrategy(),
            HenanFgwPriceBatchSourceStrategy(),
            ZznyClzArticleBatchSourceStrategy(),
            CnhnbMarketBatchSourceStrategy(),
            LiancaiAppGatewayBatchSourceStrategy(),
            LiancaiH5BatchSourceStrategy(),
            ApiBatchSourceStrategy(),
            BrowserAssistedSourceStrategy(),
            SingleSourceStrategy(),
        ]

    def set_progress_callback(self, callback: Callable[[dict[str, Any]], None] | None) -> None:
        self.progress_callback = callback
        self.api_fetcher.progress_callback = callback
        self.public_source_crawler.progress_callback = callback

    def _report_progress(self, progress: float, detail: str | None = None) -> None:
        if not callable(self.progress_callback):
            return
        self.progress_callback(
            {
                "progress": min(max(progress, 0.0), 1.0),
                "detail": detail,
            }
        )

    @staticmethod
    def _is_probably_js_page(html: str | None) -> bool:
        if not html:
            return True
        text = html.lower()
        markers = [
            "__next",
            'id="app"></div>',
            "id='app'></div>",
            "请开启javascript",
            "enable javascript",
        ]
        return any(marker in text for marker in markers)

    @staticmethod
    def _to_int(value: Any, default: int) -> int:
        try:
            if value is None or value == "":
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_float(value: Any, default: float) -> float:
        try:
            if value is None or value == "":
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _normalize_status_codes(value: Any, default: list[int]) -> list[int]:
        if not value:
            return list(default)
        if isinstance(value, list):
            normalized = []
            for item in value:
                try:
                    normalized.append(int(item))
                except (TypeError, ValueError):
                    continue
            return normalized or list(default)
        return list(default)

    def _build_requests_fetcher(self, site_rule: dict | None) -> RequestsFetcher:
        base_fetcher = self.fetcher if isinstance(self.fetcher, RequestsFetcher) else RequestsFetcher()
        timeout = self._to_int(getattr(base_fetcher, "timeout", 15), 15)
        retries = self._to_int(getattr(base_fetcher, "retries", 2), 2)
        delay = self._to_float(getattr(base_fetcher, "delay", 1.0), 1.0)
        headers = dict(getattr(base_fetcher, "headers", {}) or {})
        blocked_status_codes = self._normalize_status_codes(
            getattr(base_fetcher, "blocked_status_codes", [403, 429]),
            [403, 429],
        )
        verify_ssl = bool(getattr(base_fetcher, "verify_ssl", True))

        if site_rule:
            timeout = self._to_int(site_rule.get("timeout_seconds"), timeout)
            retries = self._to_int(site_rule.get("retry_count"), retries)
            delay = self._to_float(site_rule.get("request_delay_seconds"), delay)
            if "verify_ssl" in site_rule:
                verify_ssl = bool(site_rule.get("verify_ssl"))
            blocked_status_codes = self._normalize_status_codes(
                site_rule.get("blocked_status_codes"),
                blocked_status_codes,
            )
            custom_headers = site_rule.get("custom_headers")
            if isinstance(custom_headers, dict):
                headers.update(
                    {
                        str(key).strip(): str(value).strip()
                        for key, value in custom_headers.items()
                        if str(key).strip() and str(value).strip()
                    }
                )

        return RequestsFetcher(
            timeout=timeout,
            retries=retries,
            delay=delay,
            headers=headers or None,
            blocked_status_codes=blocked_status_codes,
            verify_ssl=verify_ssl,
        )

    def _build_playwright_fetcher(self, site_rule: dict | None) -> PlaywrightFetcher:
        base_fetcher = self.playwright_fetcher
        timeout_ms = self._to_int(getattr(base_fetcher, "timeout_ms", 20000), 20000)
        headless = getattr(base_fetcher, "headless", True)
        wait_until = getattr(base_fetcher, "wait_until", "networkidle")
        capture_json_responses = bool(getattr(base_fetcher, "capture_json_responses", True)) and (
            self.enable_api_discovery and bool((site_rule or {}).get("api_discovery_enabled", True))
        )
        max_captured_responses = self._to_int(getattr(base_fetcher, "max_captured_responses", 8), 8)

        if site_rule and site_rule.get("timeout_seconds") not in (None, ""):
            timeout_ms = self._to_int(site_rule.get("timeout_seconds"), max(timeout_ms // 1000, 1)) * 1000
        if site_rule and site_rule.get("playwright_wait_until"):
            wait_until = str(site_rule.get("playwright_wait_until"))

        if (
            isinstance(base_fetcher, PlaywrightFetcher)
            and base_fetcher.__class__ is PlaywrightFetcher
            and timeout_ms == getattr(base_fetcher, "timeout_ms", 20000)
            and wait_until == getattr(base_fetcher, "wait_until", "networkidle")
            and capture_json_responses == getattr(base_fetcher, "capture_json_responses", True)
        ):
            return base_fetcher

        if isinstance(base_fetcher, PlaywrightFetcher) and base_fetcher.__class__ is PlaywrightFetcher:
            return PlaywrightFetcher(
                timeout_ms=timeout_ms,
                headless=headless,
                wait_until=wait_until,
                capture_json_responses=capture_json_responses,
                max_captured_responses=max_captured_responses,
            )

        return base_fetcher

    def _fetch_by_requests(self, url: str, site_rule: dict | None) -> FetchResult:
        fetcher = self._build_requests_fetcher(site_rule)
        fetch_result = fetcher.fetch(url)
        metadata = dict(fetch_result.metadata or {})
        metadata.update(
            {
                "fetch_mode": "requests",
                "timeout": fetcher.timeout,
                "retries": fetcher.retries,
                "delay": fetcher.delay,
                "blocked_status_codes": list(fetcher.blocked_status_codes),
            }
        )
        fetch_result.metadata = metadata
        return fetch_result

    def _fetch_by_playwright(self, url: str, site_rule: dict | None) -> FetchResult:
        fetcher = self._build_playwright_fetcher(site_rule)
        fetch_result = fetcher.fetch(url)
        metadata = dict(fetch_result.metadata or {})
        metadata.update(
            {
                "fetch_mode": "playwright",
                "timeout_ms": getattr(fetcher, "timeout_ms", None),
            }
        )
        fetch_result.metadata = metadata
        return fetch_result

    def _fetch_by_api(self, url: str, site_rule: dict, product: dict[str, Any] | None = None) -> FetchResult:
        fetch_result = self.api_fetcher.fetch(url, site_rule, context=product or {})
        metadata = dict(fetch_result.metadata or {})
        metadata.update(
            {
                "fetch_mode": "api",
                "api_url": site_rule.get("api_url"),
                "api_method": site_rule.get("api_method") or "GET",
            }
        )
        fetch_result.metadata = metadata
        return fetch_result

    @staticmethod
    def _should_try_api_first(site_rule: dict | None) -> bool:
        if not site_rule or not site_rule.get("api_url"):
            return False
        api_strategy = site_rule.get("api_strategy") or "off"
        preferred_fetch_mode = site_rule.get("preferred_fetch_mode")
        return api_strategy in {"prefer", "only"} or preferred_fetch_mode == "api"

    def _fetch_with_optional_fallback(
        self,
        url: str,
        site_rule: dict | None,
        product: dict[str, Any] | None = None,
    ) -> FetchResult:
        preferred_fetch_mode = (site_rule or {}).get("preferred_fetch_mode")
        api_strategy = (site_rule or {}).get("api_strategy") or "off"

        if self._should_try_api_first(site_rule):
            api_result = self._fetch_by_api(url, site_rule, product)
            if not api_result.error:
                api_metadata = dict(api_result.metadata or {})
                api_metadata.update({"fallback_used": False, "preferred_fetch_mode": preferred_fetch_mode})
                api_result.metadata = api_metadata
                return api_result
            if api_strategy == "only":
                api_metadata = dict(api_result.metadata or {})
                api_metadata.setdefault("suggestion", "接口抓取失败，且当前站点设置为仅接口模式。")
                api_result.metadata = api_metadata
                return api_result

        if isinstance(self.fetcher, RequestsFetcher) and preferred_fetch_mode == "playwright":
            self.logger.info("站点规则要求优先使用 Playwright: %s", url)
            fetch_result = self._fetch_by_playwright(url, site_rule)
            metadata = dict(fetch_result.metadata or {})
            metadata.update(
                {
                    "fetch_mode": "playwright",
                    "fallback_used": False,
                    "preferred_fetch_mode": preferred_fetch_mode,
                }
            )
            fetch_result.metadata = metadata
            return fetch_result

        fetch_result = self._fetch_by_requests(url, site_rule) if isinstance(self.fetcher, RequestsFetcher) else self.fetcher.fetch(url)
        metadata = dict(fetch_result.metadata or {})
        metadata.setdefault("fetch_mode", self.fetcher.__class__.__name__.replace("Fetcher", "").lower())
        fallback_reason = None

        blocked_status_codes = set(site_rule.get("blocked_status_codes", [403, 429])) if site_rule else {403, 429}
        allow_fallback = self.fallback_to_playwright and preferred_fetch_mode != "requests_only"
        initial_mode = metadata.get("fetch_mode")
        blocked_hint = bool(metadata.get("blocked_hint")) or (fetch_result.status_code in blocked_status_codes if fetch_result.status_code is not None else False)
        js_page_hint = self._is_probably_js_page(fetch_result.html)

        if isinstance(self.fetcher, RequestsFetcher) and allow_fallback:
            if blocked_hint:
                fallback_reason = "检测到访问受限状态"
            elif fetch_result.error and (fetch_result.status_code in blocked_status_codes or fetch_result.status_code in {403, 429}):
                fallback_reason = "静态抓取返回限制状态码"
            elif not fetch_result.html:
                fallback_reason = "静态抓取结果为空"
            elif js_page_hint:
                fallback_reason = "页面疑似依赖 JavaScript 渲染"

        if fallback_reason:
            self.logger.warning("静态抓取失败，准备切换 Playwright: %s | 原因=%s", url, fallback_reason)
            fallback_result = self._fetch_by_playwright(url, site_rule)
            fallback_metadata = dict(fallback_result.metadata or {})
            fallback_metadata.update(
                {
                    "fallback_used": True,
                    "fallback_reason": fallback_reason,
                    "previous_fetch_mode": initial_mode,
                    "fetch_mode": "playwright",
                }
            )
            if fallback_result.error:
                fallback_metadata.setdefault(
                    "suggestion",
                    metadata.get("suggestion") or "请降低抓取频率，检查页面是否需要登录，或确认站点规则是否仍然有效。",
                )
            fallback_result.metadata = fallback_metadata
            return fallback_result

        metadata.update(
            {
                "fallback_used": False,
                "fetch_mode": initial_mode,
                "preferred_fetch_mode": preferred_fetch_mode,
            }
        )
        fetch_result.metadata = metadata
        return fetch_result

    def _parse_fetch_result(self, url: str, fetch_result: FetchResult, site_rule: dict | None) -> tuple[dict | None, dict | None]:
        fetch_metadata = dict(fetch_result.metadata or {})
        if fetch_metadata.get("fetch_mode") == "api":
            payload = fetch_metadata.get("json_body")
            if site_rule:
                return self.api_parser.parse_with_rule(url, payload, site_rule), None
            return None, None

        parsed = self.parser.parse(url, fetch_result.html or "")
        inferred_rule = None
        if parsed.get("current_price") is None and self.enable_api_discovery:
            parsed_from_candidates, inferred_rule = self.api_parser.parse_candidates(
                url,
                list(fetch_metadata.get("network_candidates") or []),
            )
            if parsed_from_candidates is not None:
                return parsed_from_candidates, inferred_rule
        return parsed, None

    def _parse_batch_fetch_result(self, url: str, fetch_result: FetchResult, site_rule: dict | None) -> list[dict]:
        fetch_metadata = dict(fetch_result.metadata or {})
        if fetch_metadata.get("fetch_mode") == "api" and site_rule:
            return self.api_parser.parse_list_with_rule(url, fetch_metadata.get("json_body"), site_rule)
        return []

    def _prepare_result_from_parsed(
        self,
        product: dict[str, Any],
        parsed: dict,
        fetch_result: FetchResult,
        fetch_metadata: dict[str, Any],
        group_name_override: str | None = None,
        product_name_override: str | None = None,
        product_key_override: str | None = None,
    ) -> dict[str, Any]:
        url = product["url"]
        group_name = group_name_override or product.get("group_name")
        product_name = product_name_override or product.get("product_name") or parsed.get("product_name")
        site_name = parsed.get("site_name") or product.get("site_name") or "未知站点"
        extra_fields = parsed.get("extra_fields") or {}
        metadata_source = dict(product)
        metadata_source.update({key: value for key, value in extra_fields.items() if value is not None})
        metadata = normalize_product_metadata(metadata_source, parsed.get("current_price"))
        category = extra_fields.get("category") or metadata.get("category")
        brand = extra_fields.get("brand") or metadata.get("brand")
        product_series = extra_fields.get("product_series") or metadata.get("product_series")
        spec_text = extra_fields.get("spec_text") or metadata.get("spec_text")
        compare_key = metadata.get("compare_key")
        province = extra_fields.get("province")
        city = extra_fields.get("city")
        market_name = extra_fields.get("market_name")
        region_label = extra_fields.get("region_label")
        liancai_top_category = extra_fields.get("liancai_top_category")
        liancai_subcategory = extra_fields.get("liancai_subcategory")
        liancai_keyword = extra_fields.get("liancai_keyword")
        liancai_brand_id = extra_fields.get("liancai_brand_id")
        liancai_brand_name = extra_fields.get("liancai_brand_name")
        liancai_mapping_source = extra_fields.get("liancai_mapping_source")
        image_url = normalize_liancai_image_url(extra_fields.get("cover")) if str(site_name or "").startswith("莲菜网") else None
        product_key = product_key_override or product.get("product_key") or url

        captured_at = datetime.now().isoformat(timespec="seconds")
        raw_payload = build_success_raw_payload(parsed, metadata, site_name=site_name)

        result = {
            "url": url,
            "status": "success",
            "captured_at": captured_at,
            "product_key": product_key,
            "group_name": group_name,
            "product_name": product_name,
            "site_name": site_name,
            "current_price": parsed.get("current_price"),
            "original_price": parsed.get("original_price"),
            "promotion_text": parsed.get("promotion_text"),
            "category": category,
            "brand": brand,
            "product_series": product_series,
            "spec_text": spec_text,
            "compare_key": compare_key,
            "province": province,
            "city": city,
            "market_name": market_name,
            "region_label": region_label,
            "liancai_top_category": liancai_top_category,
            "liancai_subcategory": liancai_subcategory,
            "liancai_keyword": liancai_keyword,
            "liancai_brand_id": liancai_brand_id,
            "liancai_brand_name": liancai_brand_name,
            "unit_name": metadata.get("unit_name"),
            "unit_value": metadata.get("unit_value"),
            "unit_price": metadata.get("unit_price"),
            "jin_price": metadata.get("jin_price"),
            "fetch_mode": fetch_metadata.get("fetch_mode"),
            "status_code": fetch_result.status_code,
            "suggestion": fetch_metadata.get("suggestion"),
            "fallback_used": fetch_metadata.get("fallback_used", False),
            "timeout": fetch_metadata.get("timeout"),
            "retries": fetch_metadata.get("retries"),
            "delay": fetch_metadata.get("delay"),
            "timeout_ms": fetch_metadata.get("timeout_ms"),
            "blocked_status_codes": fetch_metadata.get("blocked_status_codes"),
        }
        product_record = {
            "product_key": product_key,
            "group_name": group_name,
            "product_name": product_name,
            "source_url": url,
            "site_name": site_name,
            "category": category,
            "brand": brand,
            "product_series": product_series,
            "spec_text": spec_text,
            "compare_key": compare_key,
            "province": province,
            "city": city,
            "market_name": market_name,
            "region_label": region_label,
            "liancai_top_category": liancai_top_category,
            "liancai_subcategory": liancai_subcategory,
            "liancai_keyword": liancai_keyword,
            "liancai_brand_id": liancai_brand_id,
            "liancai_brand_name": liancai_brand_name,
            "liancai_mapping_source": liancai_mapping_source,
            "image_url": image_url,
        }
        price_record = {
            "product_key": product_key,
            "captured_at": captured_at,
            "current_price": parsed.get("current_price"),
            "original_price": parsed.get("original_price"),
            "promotion_text": parsed.get("promotion_text"),
            "currency": parsed.get("currency") or "CNY",
            "availability": parsed.get("availability"),
            "raw_payload": raw_payload,
            "unit_name": metadata.get("unit_name"),
            "unit_value": metadata.get("unit_value"),
            "unit_price": metadata.get("unit_price"),
        }
        return result, product_record, price_record

    def _persist_prepared_results(
        self,
        product_records: list[dict[str, Any]],
        price_records: list[dict[str, Any]],
    ) -> None:
        if not product_records or not price_records:
            return
        if not callable(getattr(self.database, "bulk_upsert_products", None)) or not callable(
            getattr(self.database, "bulk_insert_price_records", None)
        ):
            for product_record, price_record in zip(product_records, price_records):
                product_id = self.database.upsert_product(**product_record)
                insert_record = dict(price_record)
                insert_record.pop("product_key", None)
                self.database.insert_price_record(product_id=product_id, **insert_record)
            return

        product_id_map = self.database.bulk_upsert_products(product_records, update_existing=False)
        insert_records = []
        for price_record in price_records:
            product_key = str(price_record.get("product_key") or "").strip()
            product_id = product_id_map.get(product_key)
            if not product_id:
                continue
            insert_record = dict(price_record)
            insert_record.pop("product_key", None)
            insert_record["product_id"] = product_id
            insert_records.append(insert_record)
        self.database.bulk_insert_price_records(insert_records)

    def _build_result_from_parsed(
        self,
        product: dict[str, Any],
        parsed: dict,
        fetch_result: FetchResult,
        fetch_metadata: dict[str, Any],
        group_name_override: str | None = None,
        product_name_override: str | None = None,
        product_key_override: str | None = None,
    ) -> dict[str, Any]:
        result, product_record, price_record = self._prepare_result_from_parsed(
            product,
            parsed,
            fetch_result,
            fetch_metadata,
            group_name_override=group_name_override,
            product_name_override=product_name_override,
            product_key_override=product_key_override,
        )
        self._persist_prepared_results([product_record], [price_record])
        return result

    @staticmethod
    def _build_batch_product_key(product: dict[str, Any], parsed: dict, index: int) -> str:
        base_key = product.get("product_key") or product.get("url")
        extra_fields = parsed.get("extra_fields") or {}
        parts = [
            extra_fields.get("group_name") or extra_fields.get("category"),
            extra_fields.get("compare_key") or parsed.get("product_name"),
            extra_fields.get("product_series"),
            extra_fields.get("brand"),
            extra_fields.get("spec_text"),
            extra_fields.get("market_name"),
        ]
        return _join_compact_key(str(base_key), parts, index)

    def _select_source_strategy(self, product: dict[str, Any], site_rule: dict | None):
        for strategy in self.source_strategies:
            if strategy.matches(product, site_rule):
                return strategy
        return SingleSourceStrategy()

    def _build_browser_assisted_result(
        self,
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> dict[str, Any]:
        url = product["url"]
        product_key = product.get("product_key") or url
        group_name = product.get("group_name")
        site_name = (site_rule or {}).get("site_name") or product.get("site_name") or "未知站点"
        captured_at = datetime.now().isoformat(timespec="seconds")
        suggestion = (
            "当前站点需要浏览器态、登录态或验证码辅助流程。系统已预留专用策略入口，"
            "后续可按站点补接自动化步骤。"
        )
        result = {
            "url": url,
            "status": "failed",
            "error": "当前站点需要浏览器辅助策略",
            "site_name": site_name,
            "fetch_mode": "browser_assisted",
            "status_code": None,
            "suggestion": suggestion,
            "fallback_used": False,
            "captured_at": captured_at,
            "product_key": product_key,
            "group_name": group_name,
            "product_name": product.get("product_name"),
            "source_url": url,
        }
        self.database.insert_failed_crawl_record(
            product_key=product_key,
            captured_at=captured_at,
            group_name=group_name,
            product_name=product.get("product_name"),
            source_url=url,
            site_name=site_name,
            fetch_mode="browser_assisted",
            status_code=None,
            error=result["error"],
            suggestion=suggestion,
            fallback_used=False,
            raw_payload={"site_rule": site_rule or {}, "product": product},
        )
        return result

    def _crawl_single_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> dict[str, Any]:
        url = product["url"]
        product_key = product.get("product_key") or url
        group_name = product.get("group_name")
        site_rule = site_rule or self.parser.find_rule(url)
        if site_rule is None:
            self.logger.warning("未命中站点规则，改用通用识别: %s", url)

        fetch_result = self._fetch_with_optional_fallback(url, site_rule, product)
        fetch_metadata = dict(fetch_result.metadata or {})
        captured_at = datetime.now().isoformat(timespec="seconds")
        if fetch_result.error or (
            fetch_metadata.get("fetch_mode") != "api" and not fetch_result.html
        ):
            result = {
                "url": url,
                "status": "failed",
                "error": fetch_result.error or "页面为空",
                "site_name": (site_rule or {}).get("site_name") or "未知站点",
                "fetch_mode": fetch_metadata.get("fetch_mode"),
                "status_code": fetch_result.status_code,
                "suggestion": fetch_metadata.get("suggestion") or "系统已自动尝试通用识别，请稍后重试；如持续失败，再由管理员补充平台适配。",
                "fallback_used": fetch_metadata.get("fallback_used", False),
                "timeout": fetch_metadata.get("timeout"),
                "retries": fetch_metadata.get("retries"),
                "delay": fetch_metadata.get("delay"),
                "timeout_ms": fetch_metadata.get("timeout_ms"),
                "blocked_status_codes": fetch_metadata.get("blocked_status_codes"),
                "captured_at": captured_at,
                "product_key": product_key,
                "group_name": group_name,
                "product_name": product.get("product_name"),
                "source_url": url,
            }
            self.database.insert_failed_crawl_record(
                product_key=product_key,
                captured_at=captured_at,
                group_name=group_name,
                product_name=product.get("product_name"),
                source_url=url,
                site_name=(site_rule or {}).get("site_name") or "未知站点",
                fetch_mode=fetch_metadata.get("fetch_mode"),
                status_code=fetch_result.status_code,
                error=result["error"],
                suggestion=result["suggestion"],
                fallback_used=fetch_metadata.get("fallback_used", False),
                raw_payload={"fetch_metadata": fetch_metadata},
            )
            return result

        try:
            parsed, inferred_api_rule = self._parse_fetch_result(url, fetch_result, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("解析失败: %s", url)
            result = {
                "url": url,
                "status": "failed",
                "error": str(exc),
                "site_name": (site_rule or {}).get("site_name") or "未知站点",
                "fetch_mode": fetch_metadata.get("fetch_mode"),
                "status_code": fetch_result.status_code,
                "suggestion": "系统已自动尝试通用识别，但本次仍未成功；请检查链接是否可直接打开，必要时由管理员补充平台适配。",
                "fallback_used": fetch_metadata.get("fallback_used", False),
                "captured_at": captured_at,
                "product_key": product_key,
                "group_name": group_name,
                "product_name": product.get("product_name"),
                "source_url": url,
            }
            self.database.insert_failed_crawl_record(
                product_key=product_key,
                captured_at=captured_at,
                group_name=group_name,
                product_name=product.get("product_name"),
                source_url=url,
                site_name=(site_rule or {}).get("site_name") or "未知站点",
                fetch_mode=fetch_metadata.get("fetch_mode"),
                status_code=fetch_result.status_code,
                error=str(exc),
                suggestion=result["suggestion"],
                fallback_used=fetch_metadata.get("fallback_used", False),
                raw_payload={"fetch_metadata": fetch_metadata},
            )
            return result

        if parsed is None and fetch_metadata.get("fetch_mode") == "api" and (site_rule or {}).get("api_strategy") != "only":
            self.logger.warning("接口响应未解析出价格，回退页面抓取: %s", url)
            page_rule = {**(site_rule or {}), "api_strategy": "off", "api_url": None}
            fetch_result = self._fetch_with_optional_fallback(url, page_rule, product)
            fetch_metadata = dict(fetch_result.metadata or {})
            try:
                parsed, inferred_api_rule = self._parse_fetch_result(url, fetch_result, site_rule)
            except Exception:  # noqa: BLE001
                self.logger.exception("接口回退页面后解析失败: %s", url)
                parsed = None
                inferred_api_rule = None

        if parsed is None:
            result = {
                "url": url,
                "status": "failed",
                "error": "未识别到可用接口数据",
                "site_name": (site_rule or {}).get("site_name") or "未知站点",
                "fetch_mode": fetch_metadata.get("fetch_mode"),
                "status_code": fetch_result.status_code,
                "suggestion": "接口抓取未能识别到价格字段，已建议回退页面规则或补充接口字段映射。",
                "fallback_used": fetch_metadata.get("fallback_used", False),
                "captured_at": captured_at,
                "product_key": product_key,
                "group_name": group_name,
                "product_name": product.get("product_name"),
                "source_url": url,
            }
            self.database.insert_failed_crawl_record(
                product_key=product_key,
                captured_at=captured_at,
                group_name=group_name,
                product_name=product.get("product_name"),
                source_url=url,
                site_name=result["site_name"],
                fetch_mode=result["fetch_mode"],
                status_code=fetch_result.status_code,
                error=result["error"],
                suggestion=result["suggestion"],
                fallback_used=fetch_metadata.get("fallback_used", False),
                raw_payload={"fetch_metadata": fetch_metadata},
            )
            return result

        if parsed.get("current_price") is None:
            suggestion = "系统已自动尝试通用识别，但这条链接暂时没有识别到价格；可先换一个商品页链接，若持续失败再由管理员补充平台适配。"
            result = {
                "url": url,
                "status": "failed",
                "error": "未识别到价格",
                "site_name": parsed.get("site_name") or (site_rule or {}).get("site_name") or "未知站点",
                "fetch_mode": fetch_metadata.get("fetch_mode"),
                "status_code": fetch_result.status_code,
                "suggestion": suggestion,
                "fallback_used": fetch_metadata.get("fallback_used", False),
                "captured_at": captured_at,
                "product_key": product_key,
                "group_name": group_name,
                "product_name": product.get("product_name") or parsed.get("product_name"),
                "source_url": url,
            }
            self.database.insert_failed_crawl_record(
                product_key=product_key,
                captured_at=captured_at,
                group_name=group_name,
                product_name=result["product_name"],
                source_url=url,
                site_name=result["site_name"],
                fetch_mode=fetch_metadata.get("fetch_mode"),
                status_code=fetch_result.status_code,
                error=result["error"],
                suggestion=suggestion,
                fallback_used=fetch_metadata.get("fallback_used", False),
                raw_payload={"fetch_metadata": fetch_metadata, "parsed": parsed},
            )
            return result

        auto_rule_message = None
        if site_rule is None and self.auto_learn_site_rules:
            auto_rule_message = self._auto_learn_site_rule(
                url,
                parsed,
                fetch_metadata.get("fetch_mode"),
                inferred_rule=inferred_api_rule,
            )
        result = self._build_result_from_parsed(
            product,
            parsed,
            fetch_result,
            fetch_metadata,
            group_name_override=group_name,
            product_name_override=product.get("product_name") or parsed.get("product_name"),
            product_key_override=product_key,
        )
        if auto_rule_message:
            result["suggestion"] = auto_rule_message
        self.logger.info("抓取成功: %s | 当前价格=%s", url, parsed.get("current_price"))
        return result

    def _crawl_batch_api_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        if not site_rule or not self._should_try_api_first(site_rule):
            return [self._crawl_single_source(product, site_rule)]

        self._report_progress(0.02, "准备抓取接口分页")
        fetch_results = self.api_fetcher.fetch_all_pages(product["url"], site_rule, context=product)
        if not fetch_results or fetch_results[0].error:
            if site_rule.get("fallback_strategy") is None:
                return self._build_failed_source_result(
                    product,
                    site_rule,
                    (fetch_results[0].error if fetch_results else "接口未返回结果"),
                    "api",
                    "批量接口暂不可用，且当前来源已关闭页面回退，避免长时间阻塞抓取任务。",
                )
            return [self._crawl_single_source(product, site_rule)]

        for fetch_result in fetch_results:
            fetch_metadata = dict(fetch_result.metadata or {})
            fetch_metadata.update(
                {
                    "fetch_mode": "api",
                    "api_url": site_rule.get("api_url"),
                    "api_method": site_rule.get("api_method") or "GET",
                    "fallback_used": False,
                    "preferred_fetch_mode": site_rule.get("preferred_fetch_mode"),
                }
            )
            fetch_result.metadata = fetch_metadata

        parsed_items: list[dict[str, Any]] = []
        representative_fetch_result = fetch_results[0]
        total_pages = len(fetch_results)
        for page_index, fetch_result in enumerate(fetch_results, start=1):
            page_items = self._parse_batch_fetch_result(product["url"], fetch_result, site_rule)
            if page_items:
                parsed_items.extend(page_items)
            self._report_progress(
                0.15 + 0.25 * (page_index / total_pages),
                f"已解析接口第 {page_index}/{total_pages} 页",
            )

        if not parsed_items:
            return [self._crawl_single_source(product, site_rule)]

        parsed_items = self._compact_batch_items(product, site_rule, parsed_items)

        results: list[dict[str, Any]] = []
        product_records: list[dict[str, Any]] = []
        price_records: list[dict[str, Any]] = []
        report_every = max(1, len(parsed_items) // 50)
        for index, parsed in enumerate(parsed_items, start=1):
            group_name = (
                parsed.get("extra_fields", {}).get("group_name")
                or parsed.get("extra_fields", {}).get("category")
                or product.get("group_name")
                or parsed.get("site_name")
            )
            result, product_record, price_record = self._prepare_result_from_parsed(
                product,
                parsed,
                representative_fetch_result,
                dict(representative_fetch_result.metadata or {}),
                group_name_override=group_name,
                product_name_override=parsed.get("product_name"),
                product_key_override=self._build_batch_product_key(product, parsed, index),
            )
            results.append(result)
            product_records.append(product_record)
            price_records.append(price_record)
            if index == 1 or index == len(parsed_items) or index % report_every == 0:
                self._report_progress(
                    0.45 + 0.53 * (index / len(parsed_items)),
                    f"已入库 {index}/{len(parsed_items)} 条",
                )
        self._persist_prepared_results(product_records, price_records)
        self.logger.info("批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _compact_batch_items(
        self,
        product: dict[str, Any],
        site_rule: dict[str, Any] | None,
        parsed_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        source_name = str((site_rule or {}).get("site_name") or "").strip()
        if source_name != "万邦国际":
            return parsed_items

        grouped: dict[str, dict[str, Any]] = {}
        counts: dict[str, int] = {}
        price_sums: dict[str, float] = {}
        original_max: dict[str, float | None] = {}
        promotion_sets: dict[str, set[str]] = {}

        for index, parsed in enumerate(parsed_items, start=1):
            key = self._build_batch_product_key(product, parsed, index)
            current_price = parsed.get("current_price")
            if current_price is None:
                continue
            price_value = float(current_price)
            existing = grouped.get(key)
            if existing is None:
                grouped[key] = dict(parsed)
                counts[key] = 0
                price_sums[key] = 0.0
                original_max[key] = None
                promotion_sets[key] = set()
            counts[key] += 1
            price_sums[key] += price_value
            original_value = parsed.get("original_price")
            if original_value is not None:
                original_float = float(original_value)
                original_max[key] = (
                    original_float
                    if original_max[key] is None or original_float > float(original_max[key])
                    else original_max[key]
                )
            promotion_text = str(parsed.get("promotion_text") or "").strip()
            if promotion_text:
                promotion_sets[key].add(promotion_text)

        compacted: list[dict[str, Any]] = []
        for key, parsed in grouped.items():
            count = counts.get(key, 0) or 1
            compact = dict(parsed)
            compact["current_price"] = round(price_sums[key] / count, 4)
            compact["original_price"] = original_max.get(key)
            promotions = sorted(promotion_sets.get(key) or set())
            if len(promotions) <= 1:
                compact["promotion_text"] = promotions[0] if promotions else compact.get("promotion_text")
            else:
                compact["promotion_text"] = "多产地报价"
            compacted.append(compact)
        return compacted

    def _build_custom_batch_results(
        self,
        product: dict[str, Any],
        parsed_items: list[dict[str, Any]],
        fetch_metadata: dict[str, Any],
        key_builder,
    ) -> list[dict[str, Any]]:
        representative_fetch_result = FetchResult(
            url=product["url"],
            status_code=200,
            html=None,
            metadata=fetch_metadata,
        )
        results: list[dict[str, Any]] = []
        product_records: list[dict[str, Any]] = []
        price_records: list[dict[str, Any]] = []
        report_every = max(1, len(parsed_items) // 40) if parsed_items else 1
        for index, parsed in enumerate(parsed_items, start=1):
            extra_fields = parsed.get("extra_fields") or {}
            group_name = extra_fields.get("group_name") or extra_fields.get("category") or product.get("group_name")
            result, product_record, price_record = self._prepare_result_from_parsed(
                product,
                parsed,
                representative_fetch_result,
                dict(fetch_metadata),
                group_name_override=group_name,
                product_name_override=parsed.get("product_name"),
                product_key_override=key_builder(product, parsed, index),
            )
            results.append(result)
            product_records.append(product_record)
            price_records.append(price_record)
            if index == 1 or index == len(parsed_items) or index % report_every == 0:
                self._report_progress(
                    0.45 + 0.53 * (index / len(parsed_items)),
                    f"已入库 {index}/{len(parsed_items)} 条",
                )
        self._persist_prepared_results(product_records, price_records)
        return results

    def _build_failed_source_result(
        self,
        product: dict[str, Any],
        site_rule: dict | None,
        error: str,
        fetch_mode: str,
        suggestion: str,
    ) -> list[dict[str, Any]]:
        captured_at = datetime.now().isoformat(timespec="seconds")
        product_key = product.get("product_key") or product["url"]
        site_name = (site_rule or {}).get("site_name") or "未知站点"
        result = {
            "url": product["url"],
            "status": "failed",
            "error": error,
            "site_name": site_name,
            "fetch_mode": fetch_mode,
            "status_code": None,
            "suggestion": suggestion,
            "fallback_used": False,
            "captured_at": captured_at,
            "product_key": product_key,
            "group_name": product.get("group_name"),
            "product_name": product.get("product_name"),
            "source_url": product["url"],
        }
        self.database.insert_failed_crawl_record(
            product_key=product_key,
            captured_at=captured_at,
            group_name=product.get("group_name"),
            product_name=product.get("product_name"),
            source_url=product["url"],
            site_name=site_name,
            fetch_mode=fetch_mode,
            status_code=None,
            error=error,
            suggestion=suggestion,
            fallback_used=False,
            raw_payload={"site_rule": site_rule or {}, "product": product},
        )
        return [result]

    @staticmethod
    def _build_named_batch_key(product: dict[str, Any], parsed: dict, index: int) -> str:
        base_key = product.get("product_key") or product.get("url")
        compare_key = str((parsed.get("extra_fields") or {}).get("compare_key") or parsed.get("product_name") or index).strip()
        return _join_compact_key(str(base_key), [compare_key], index)

    def _crawl_chinaprice_batch_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        try:
            parsed_items = self.public_source_crawler.fetch_chinaprice(product, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Chinaprice 抓取失败: %s", product["url"])
            return self._build_failed_source_result(
                product,
                site_rule,
                str(exc),
                "api",
                "Chinaprice 公开汇总抓取失败，请检查网络或站点参数。",
            )

        if not parsed_items:
            return self._build_failed_source_result(
                product,
                site_rule,
                "Chinaprice 未返回可用报价",
                "api",
                "当前周期未查询到 Chinaprice 公开汇总数据。",
            )

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "api",
                "api_url": (site_rule or {}).get("api_url"),
                "api_method": (site_rule or {}).get("api_method") or "POST",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_named_batch_key,
        )
        self.logger.info("Chinaprice 批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _crawl_pfsc_chart_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        try:
            parsed_items = self.public_source_crawler.fetch_pfsc(product, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("PFSC 抓取失败: %s", product["url"])
            return self._build_failed_source_result(
                product,
                site_rule,
                str(exc),
                "api",
                "PFSC 图表行情抓取失败，请检查网络状态或系统环境。",
            )

        if not parsed_items:
            return self._build_failed_source_result(
                product,
                site_rule,
                "PFSC 未返回可用行情",
                "api",
                "当前未从 PFSC 图表接口获取到可用市场报价。",
            )

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "api",
                "api_url": (site_rule or {}).get("api_url"),
                "api_method": (site_rule or {}).get("api_method") or "POST",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_named_batch_key,
        )
        self.logger.info("PFSC 批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _crawl_moa_wholesale_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        try:
            parsed_items = self.public_source_crawler.fetch_moa_wholesale(product, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("重点农产品市场信息平台抓取失败: %s", product["url"])
            return self._build_failed_source_result(
                product,
                site_rule,
                str(exc),
                "api",
                "重点农产品市场信息平台抓取失败，请检查网络状态或站点接口是否变更。",
            )

        if not parsed_items:
            return self._build_failed_source_result(
                product,
                site_rule,
                "重点农产品市场信息平台未返回可用行情",
                "api",
                "当前未从重点农产品市场信息平台获取到可用市场报价。",
            )

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "api",
                "api_url": (site_rule or {}).get("api_url"),
                "api_method": (site_rule or {}).get("api_method") or "POST",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_named_batch_key,
        )
        self.logger.info("重点农产品市场信息平台批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _crawl_hnnhgsc_batch_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        try:
            parsed_items = self.public_source_crawler.fetch_hnnhgsc(product, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("内黄果蔬城抓取失败: %s", product["url"])
            return self._build_failed_source_result(
                product,
                site_rule,
                str(exc),
                "requests",
                "内黄果蔬城页面解析失败，请检查证书、页面结构或来源规则。",
            )

        if not parsed_items:
            return self._build_failed_source_result(
                product,
                site_rule,
                "内黄果蔬城未返回可用行情",
                "requests",
                "当前未从内黄果蔬城页面解析到可用价格数据。",
            )

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "requests",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_named_batch_key,
        )
        self.logger.info("内黄果蔬城批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _crawl_henan_fgw_price_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        try:
            parsed_items = self.public_source_crawler.fetch_henan_fgw_price(product, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("河南发改委价格监测抓取失败: %s", product["url"])
            return self._build_failed_source_result(
                product,
                site_rule,
                str(exc),
                "api",
                "河南发改委价格监测接口抓取失败，请检查接口或网络状态。",
            )

        if not parsed_items:
            return self._build_failed_source_result(
                product,
                site_rule,
                "河南发改委价格监测未返回可用行情",
                "api",
                "当前未从河南发改委价格监测接口获取到可用价格数据。",
            )

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "api",
                "api_url": (site_rule or {}).get("api_url"),
                "api_method": (site_rule or {}).get("api_method") or "POST",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_named_batch_key,
        )
        self.logger.info("河南发改委价格监测批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _crawl_zzny_clz_article_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        try:
            parsed_items = self.public_source_crawler.fetch_zzny_clz_articles(product, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("郑州菜篮子监测抓取失败: %s", product["url"])
            return self._build_failed_source_result(
                product,
                site_rule,
                str(exc),
                "requests",
                "郑州菜篮子监测文章解析失败，请检查页面结构或网络状态。",
            )

        if not parsed_items:
            return self._build_failed_source_result(
                product,
                site_rule,
                "郑州菜篮子监测未返回可用行情",
                "requests",
                "当前未从郑州菜篮子监测文章中解析到可用价格数据。",
            )

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "requests",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_named_batch_key,
        )
        self.logger.info("郑州菜篮子监测批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _crawl_cnhnb_market_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        try:
            parsed_items = self.public_source_crawler.fetch_cnhnb_market(product, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("惠农网行情抓取失败: %s", product["url"])
            return self._build_failed_source_result(
                product,
                site_rule,
                str(exc),
                "requests",
                "惠农网页面行情解析失败，请检查 SSR 数据结构或本机 Node 环境。",
            )

        if not parsed_items:
            return self._build_failed_source_result(
                product,
                site_rule,
                "惠农网未返回可用行情",
                "requests",
                "当前未从惠农网页面中解析到可用参考价格数据。",
            )

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "requests",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_named_batch_key,
        )
        self.logger.info("惠农网行情批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _crawl_liancai_h5_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        site_rule = site_rule or self.parser.find_rule(product["url"])
        try:
            parsed_items = self.public_source_crawler.fetch_liancai_h5(product, site_rule)
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("莲菜网H5抓取失败: %s", product["url"])
            return self._build_failed_source_result(
                product,
                site_rule,
                str(exc),
                "requests",
                self._build_liancai_h5_failure_suggestion(str(exc)),
            )

        if not parsed_items:
            return self._build_failed_source_result(
                product,
                site_rule,
                "莲菜网H5未返回可用商品",
                "requests",
                "当前未从莲菜网H5获取到可用商品，请检查分类映射、分页或账号状态。",
            )

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "requests",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_named_batch_key,
        )
        self.logger.info("莲菜网H5批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    def _crawl_liancai_app_gateway_source(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        try:
            parsed_items = self.public_source_crawler.fetch_liancai_app_gateway(product, site_rule)
        except Exception as exc:
            self.logger.exception("莲菜网App网关抓取失败: %s", product["url"])
            self._record_failed_crawl(
                product,
                fetch_mode="app_gateway",
                error=str(exc),
                suggestion="请检查 MuMu 登录状态、接口参数或网关是否变更。",
                fallback_used=False,
                raw_payload={},
            )
            return []

        results = self._build_custom_batch_results(
            product,
            parsed_items,
            {
                "fetch_mode": "app_gateway",
                "fallback_used": False,
                "preferred_fetch_mode": (site_rule or {}).get("preferred_fetch_mode"),
            },
            self._build_liancai_app_gateway_batch_key,
        )
        if not results:
            self._record_failed_crawl(
                product,
                fetch_mode="app_gateway",
                error="莲菜网App网关未返回可用商品",
                suggestion="请检查 term_id、brand_id、post_keywords 或分类映射。",
                fallback_used=False,
                raw_payload={"parsed_count": len(parsed_items)},
            )
            return []

        self.logger.info("莲菜网App网关批量抓取成功: %s | 条数=%s", product["url"], len(results))
        return results

    @staticmethod
    def _build_liancai_app_gateway_batch_key(product: dict[str, Any], parsed: dict, index: int) -> str:
        base_key = product.get("product_key") or product.get("url")
        extra_fields = parsed.get("extra_fields") or {}
        parts = [
            extra_fields.get("group_name") or extra_fields.get("category"),
            extra_fields.get("compare_key") or parsed.get("product_name"),
            extra_fields.get("liancai_brand_name") or extra_fields.get("brand"),
            extra_fields.get("product_series"),
            extra_fields.get("spec_text"),
        ]
        return _join_compact_key(str(base_key), parts, index)

    @staticmethod
    def _build_liancai_h5_failure_suggestion(error: str) -> str:
        message = str(error or "")
        if "缺少莲菜网H5登录凭证" in message:
            return "请在线上环境设置 LIANCAI_PHONE / LIANCAI_PASSWORD，并确认进程可读取到这两个环境变量。"
        if "登录失败" in message:
            return "莲菜网H5登录失败，请检查账号密码、账号状态，或确认该账号是否触发了额外校验。"
        if "未找到莲菜网H5分类映射" in message:
            return "请检查 products.json 中的 category 是否能匹配莲菜网H5的顶层分类名称。"
        if "未返回可用商品" in message:
            return "当前分类未返回可用商品，请检查分类 fid、分页范围或账号登录态是否失效。"
        return "莲菜网H5抓取失败，请检查登录账号环境变量、分类配置或页面结构。"

    def crawl_product(self, product: dict[str, Any]) -> dict[str, Any]:
        site_rule = self.parser.find_rule(product["url"])
        return self._crawl_single_source(product, site_rule)

    def crawl_source(self, product: dict[str, Any]) -> list[dict[str, Any]]:
        site_rule = self.parser.find_rule(product["url"])
        strategy = self._select_source_strategy(product, site_rule)
        results = strategy.crawl(self, product, site_rule)
        for result in results:
            result.setdefault("source_strategy", strategy.name)
        return results

    def _auto_learn_site_rule(
        self,
        url: str,
        parsed: dict,
        fetch_mode: str | None,
        inferred_rule: dict | None = None,
    ) -> str | None:
        if inferred_rule is None:
            inferred_rule = self.parser.build_site_rule_from_parse(url, parsed, fetch_mode)
        if inferred_rule is None:
            self.logger.info("通用识别成功，但无法生成稳定站点规则: %s", url)
            return None

        stored_rule = inferred_rule
        created = True
        if not callable(self.site_rule_store):
            self.logger.info("未配置站点规则存储器，跳过自动沉淀: %s", url)
            return "系统已使用通用识别抓取成功，但当前入口未启用规则自动沉淀。"

        stored_rule, created = self.site_rule_store(inferred_rule)
        self.parser.site_rules = [
            rule
            for rule in self.parser.site_rules
            if not set(domain.lower() for domain in rule.get("domains", [])).intersection(
                set(domain.lower() for domain in stored_rule.get("domains", []))
            )
        ]
        self.parser.site_rules.append(stored_rule)
        self.logger.info(
            "通用识别已自动沉淀站点规则: %s | 站点=%s | created=%s",
            url,
            stored_rule.get("site_name"),
            created,
        )
        if created:
            return f"系统已自动识别并保存平台规则：{stored_rule.get('site_name')}。"
        return f"系统已自动补强平台规则：{stored_rule.get('site_name')}。"

    def crawl_many(self, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for product in products:
            results.extend(self.crawl_source(product))
        return results
