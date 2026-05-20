from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from parsers.normalizer import normalize_price, normalize_text


class ApiParser:
    DEFAULT_NAME_KEYS = [
        "product_name",
        "productName",
        "goodsName",
        "goods_name",
        "name",
        "title",
    ]
    DEFAULT_PRICE_KEYS = [
        "current_price",
        "currentPrice",
        "price",
        "targetPrice",
        "target_price",
        "salePrice",
        "sale_price",
        "value",
    ]
    DEFAULT_ORIGINAL_PRICE_KEYS = [
        "original_price",
        "originalPrice",
        "marketPrice",
        "market_price",
        "oldPrice",
        "old_price",
    ]
    DEFAULT_PROMOTION_KEYS = [
        "promotion",
        "promotion_text",
        "promotionText",
        "promo",
        "message",
    ]
    DEFAULT_CURRENCY_KEYS = ["currency", "currencyCode", "currency_code"]

    def parse_with_rule(self, url: str, payload: Any, site_rule: dict) -> dict | None:
        if site_rule.get("batch_list_path"):
            items = self.parse_list_with_rule(url, payload, site_rule)
            return items[0] if items else None
        mapping = site_rule.get("api_field_mapping") or {}
        current_price = normalize_price(self._extract_value(payload, mapping.get("current_price")))
        if current_price is None:
            return None

        site_name = site_rule.get("site_name") or urlparse(url).netloc
        return {
            "site_name": site_name,
            "product_name": normalize_text(self._extract_value(payload, mapping.get("product_name"))),
            "current_price": current_price,
            "original_price": normalize_price(self._extract_value(payload, mapping.get("original_price"))),
            "promotion_text": normalize_text(self._extract_value(payload, mapping.get("promotion_text"))),
            "currency": normalize_text(self._extract_value(payload, mapping.get("currency"))) or site_rule.get("currency", "CNY"),
            "matched_rule": site_rule.get("site_name") or "接口规则",
            "raw_extract": {},
        }

    def parse_list_with_rule(self, url: str, payload: Any, site_rule: dict) -> list[dict]:
        list_path = site_rule.get("batch_list_path")
        items = self._extract_value(payload, list_path) if list_path else None
        if not isinstance(items, list):
            return []

        mapping = site_rule.get("api_field_mapping") or {}
        site_name = site_rule.get("site_name") or urlparse(url).netloc
        results: list[dict] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            current_price = normalize_price(self._extract_value(item, mapping.get("current_price")))
            if current_price is None:
                continue
            parsed = {
                "site_name": site_name,
                "product_name": normalize_text(self._extract_value(item, mapping.get("product_name"))),
                "current_price": current_price,
                "original_price": normalize_price(self._extract_value(item, mapping.get("original_price"))),
                "promotion_text": normalize_text(self._extract_value(item, mapping.get("promotion_text"))),
                "currency": normalize_text(self._extract_value(item, mapping.get("currency"))) or site_rule.get("currency", "CNY"),
                "matched_rule": site_rule.get("site_name") or "接口规则",
                "raw_extract": {},
                "extra_fields": {},
            }
            for source_key, target_key in {
                "category": "category",
                "brand": "brand",
                "product_series": "product_series",
                "spec_text": "spec_text",
                "group_name": "group_name",
            }.items():
                mapped_path = mapping.get(source_key)
                parsed["extra_fields"][target_key] = normalize_text(self._extract_value(item, mapped_path))
            results.append(parsed)
        return results

    def parse_candidates(self, url: str, candidates: list[dict]) -> tuple[dict | None, dict | None]:
        for candidate in candidates:
            payload = candidate.get("json_body")
            if payload is None:
                continue

            product_name, product_name_path = self._find_first_match(payload, self.DEFAULT_NAME_KEYS)
            current_price_value, current_price_path = self._find_first_match(payload, self.DEFAULT_PRICE_KEYS)
            current_price = normalize_price(current_price_value)
            if current_price is None:
                continue
            original_price_value, original_price_path = self._find_first_match(payload, self.DEFAULT_ORIGINAL_PRICE_KEYS)
            promotion_text, promotion_text_path = self._find_first_match(payload, self.DEFAULT_PROMOTION_KEYS)
            currency_value, currency_path = self._find_first_match(payload, self.DEFAULT_CURRENCY_KEYS)

            parsed = {
                "site_name": urlparse(url).netloc,
                "product_name": normalize_text(product_name),
                "current_price": current_price,
                "original_price": normalize_price(original_price_value),
                "promotion_text": normalize_text(promotion_text),
                "currency": normalize_text(currency_value) or "CNY",
                "matched_rule": "通用接口识别",
                "raw_extract": {},
            }
            inferred_rule = self.build_site_rule_from_candidate(
                url,
                candidate,
                parsed,
                {
                    "product_name": product_name_path,
                    "current_price": current_price_path,
                    "original_price": original_price_path,
                    "promotion_text": promotion_text_path,
                    "currency": currency_path,
                },
            )
            return parsed, inferred_rule
        return None, None

    def build_site_rule_from_candidate(self, url: str, candidate: dict, parsed: dict, mapping: dict[str, str | None]) -> dict:
        hostname = urlparse(url).netloc.lower()
        domains = [hostname]
        if hostname.startswith("www."):
            domains.append(hostname[4:])

        return {
            "site_name": parsed.get("site_name") or hostname,
            "domains": domains,
            "currency": parsed.get("currency") or "CNY",
            "preferred_fetch_mode": "playwright",
            "api_strategy": "prefer",
            "api_url": candidate.get("url"),
            "api_method": candidate.get("method") or "GET",
            "api_headers": {},
            "api_body_template": None,
            "api_field_mapping": {key: value for key, value in mapping.items() if value},
            "api_discovery_enabled": True,
            "notes": "系统根据页面网络响应自动发现接口候选。",
        }

    def _extract_value(self, payload: Any, path: str | None) -> Any:
        if not path:
            return None
        current = payload
        for token in self._parse_path(path):
            if token == "*":
                if isinstance(current, list):
                    current = next((item for item in current if item is not None), None)
                    continue
                return None
            if isinstance(token, int):
                if not isinstance(current, list) or token >= len(current):
                    return None
                current = current[token]
                continue
            if not isinstance(current, dict):
                return None
            current = current.get(token)
            if current is None:
                return None
        return current

    def _parse_path(self, path: str) -> list[str | int]:
        normalized = str(path).replace("[]", "[*]")
        tokens: list[str | int] = []
        for segment in normalized.split("."):
            if not segment:
                continue
            while "[" in segment:
                field, remainder = segment.split("[", 1)
                if field:
                    tokens.append(field)
                index_token, segment = remainder.split("]", 1)
                tokens.append("*" if index_token == "*" else int(index_token))
            if segment:
                tokens.append(segment)
        return tokens

    def _find_first_by_keys(self, payload: Any, keys: list[str]) -> Any:
        value, _ = self._find_first_match(payload, keys)
        return value

    def _find_first_match(
        self,
        payload: Any,
        keys: list[str],
        path: str = "",
    ) -> tuple[Any, str | None]:
        if isinstance(payload, dict):
            for key in keys:
                value = payload.get(key)
                if value not in (None, "", [], {}):
                    current_path = f"{path}.{key}" if path else key
                    return value, current_path
            for key, value in payload.items():
                next_path = f"{path}.{key}" if path else key
                found, found_path = self._find_first_match(value, keys, next_path)
                if found not in (None, "", [], {}):
                    return found, found_path
        elif isinstance(payload, list):
            for index, item in enumerate(payload):
                next_path = f"{path}[{index}]" if path else f"[{index}]"
                found, found_path = self._find_first_match(item, keys, next_path)
                if found not in (None, "", [], {}):
                    return found, found_path
        return None, None

    @staticmethod
    def _preview_payload(payload: Any) -> str:
        try:
            preview = json.dumps(payload, ensure_ascii=False)
        except TypeError:
            preview = str(payload)
        return preview[:1000]
