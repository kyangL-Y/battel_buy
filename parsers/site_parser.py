from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from parsers.normalizer import normalize_price, normalize_text


class SiteRuleNotFoundError(Exception):
    pass


class SiteParser:
    def __init__(self, site_rules: list[dict]):
        self.site_rules = site_rules

    def find_rule(self, url: str) -> dict | None:
        hostname = urlparse(url).netloc.lower()
        for rule in self.site_rules:
            domains = [domain.lower() for domain in rule.get("domains", [])]
            if any(domain in hostname for domain in domains):
                return rule
        return None

    def match_rule(self, url: str) -> dict:
        rule = self.find_rule(url)
        if rule is not None:
            return rule
        raise SiteRuleNotFoundError(f"未找到匹配的站点规则: {url}")

    def parse(self, url: str, html: str) -> dict:
        rule = self.find_rule(url)
        soup = BeautifulSoup(html, "html.parser")

        name, name_selector = self._select_text(
            soup,
            (rule or {}).get("name_selectors", []),
            self._default_name_selectors(),
        )
        current_price_raw, price_selector = self._select_text(
            soup,
            (rule or {}).get("price_selectors", []),
            self._default_price_selectors(),
        )
        original_price_raw, original_price_selector = self._select_text(
            soup,
            (rule or {}).get("original_price_selectors", []),
            self._default_original_price_selectors(),
        )
        promotion, promotion_selector = self._select_text(
            soup,
            (rule or {}).get("promotion_selectors", []),
            self._default_promotion_selectors(),
        )
        if current_price_raw is None:
            current_price_raw, price_selector = self._extract_price_from_meta(soup)
        if original_price_raw is None:
            original_price_raw = self._extract_original_price_from_text(soup)
        if current_price_raw is None or name is None:
            json_ld_payload = self._extract_product_json_ld(soup)
            if name is None:
                name = json_ld_payload.get("name")
                if name is not None:
                    name_selector = "script[type='application/ld+json']"
            if current_price_raw is None:
                current_price_raw = json_ld_payload.get("price")
                if current_price_raw is not None:
                    price_selector = "script[type='application/ld+json']"
            if original_price_raw is None:
                original_price_raw = json_ld_payload.get("high_price")
                if original_price_raw is not None:
                    original_price_selector = "script[type='application/ld+json']"
        else:
            json_ld_payload = {}

        return {
            "site_name": (rule or {}).get("site_name") or urlparse(url).netloc,
            "product_name": normalize_text(name),
            "current_price": normalize_price(current_price_raw),
            "original_price": normalize_price(original_price_raw),
            "promotion_text": normalize_text(promotion),
            "currency": (rule or {}).get("currency", "CNY"),
            "matched_rule": (rule or {}).get("site_name") or "通用识别",
            "raw_extract": {
                "name": name,
                "current_price": current_price_raw,
                "original_price": original_price_raw,
                "promotion": promotion,
                "json_ld": json_ld_payload or None,
                "matched_selectors": {
                    "name": name_selector,
                    "current_price": price_selector,
                    "original_price": original_price_selector,
                    "promotion": promotion_selector,
                },
            },
        }

    @staticmethod
    def _select_text(
        soup: BeautifulSoup,
        selectors: list[str],
        fallback_selectors: list[str] | None = None,
    ) -> tuple[str | None, str | None]:
        selector_candidates = list(selectors or []) + [item for item in (fallback_selectors or []) if item not in (selectors or [])]
        for selector in selector_candidates:
            node = soup.select_one(selector)
            if node:
                text = node.get("content") if node.has_attr("content") else node.get_text(" ", strip=True)
                if text:
                    return text, selector
        return None, None

    @staticmethod
    def _default_name_selectors() -> list[str]:
        return [
            "meta[property='og:title']",
            "meta[name='og:title']",
            "meta[name='twitter:title']",
            "meta[itemprop='name']",
            "h1",
            "[itemprop='name']",
            ".product-title",
            ".goods-name",
            ".sku-name",
            "title",
        ]

    @staticmethod
    def _default_price_selectors() -> list[str]:
        return [
            "meta[property='product:price:amount']",
            "meta[property='og:price:amount']",
            "meta[itemprop='price']",
            "[itemprop='price']",
            ".price-current",
            ".sale-price",
            ".price",
            ".goods-price",
            ".product-price",
            ".p-price",
            ".price-now",
            "[class*='price']",
            "[data-price]",
        ]

    @staticmethod
    def _default_original_price_selectors() -> list[str]:
        return [
            ".price-original",
            ".market-price",
            ".origin-price",
            ".old-price",
            ".price-old",
            "[class*='original-price']",
        ]

    @staticmethod
    def _default_promotion_selectors() -> list[str]:
        return [
            ".promotion",
            ".promo-text",
            ".tag-promo",
            ".discount-desc",
            ".coupon",
            "[class*='promo']",
        ]

    @staticmethod
    def _extract_price_from_meta(soup: BeautifulSoup) -> tuple[str | None, str | None]:
        for attr_name, attr_value, selector in [
            ("property", "product:price:amount", "meta[property='product:price:amount']"),
            ("property", "og:price:amount", "meta[property='og:price:amount']"),
            ("itemprop", "price", "meta[itemprop='price']"),
            ("name", "price", "meta[name='price']"),
        ]:
            node = soup.find("meta", attrs={attr_name: attr_value})
            if node and node.get("content"):
                return str(node.get("content")), selector
        return None, None

    @staticmethod
    def _extract_original_price_from_text(soup: BeautifulSoup) -> str | None:
        text = soup.get_text(" ", strip=True)
        if not text:
            return None
        match = re.search(r"(原价|划线价|市场价)[^\d]{0,6}(\d+(?:\.\d+)?)", text)
        if match:
            return match.group(2)
        return None

    @classmethod
    def _extract_product_json_ld(cls, soup: BeautifulSoup) -> dict[str, str | None]:
        for script in soup.select("script[type='application/ld+json']"):
            raw_text = script.string or script.get_text(" ", strip=True)
            if not raw_text:
                continue
            try:
                payload = json.loads(raw_text)
            except json.JSONDecodeError:
                continue
            product_payload = cls._find_product_payload(payload)
            if not isinstance(product_payload, dict):
                continue
            offers = product_payload.get("offers") or {}
            if isinstance(offers, list):
                offers = next((item for item in offers if isinstance(item, dict)), {})
            if not isinstance(offers, dict):
                offers = {}
            return {
                "name": normalize_text(product_payload.get("name")),
                "price": normalize_text(offers.get("price") or product_payload.get("price")),
                "high_price": normalize_text(offers.get("highPrice")),
            }
        return {}

    @classmethod
    def _find_product_payload(cls, payload):
        if isinstance(payload, dict):
            payload_type = payload.get("@type")
            if payload_type == "Product" or (isinstance(payload_type, list) and "Product" in payload_type):
                return payload
            for value in payload.values():
                candidate = cls._find_product_payload(value)
                if candidate is not None:
                    return candidate
        elif isinstance(payload, list):
            for item in payload:
                candidate = cls._find_product_payload(item)
                if candidate is not None:
                    return candidate
        return None

    def build_site_rule_from_parse(self, url: str, parsed: dict, fetch_mode: str | None = None) -> dict | None:
        raw_extract = parsed.get("raw_extract") or {}
        matched_selectors = raw_extract.get("matched_selectors") or {}
        price_selector = matched_selectors.get("current_price")
        if not price_selector:
            return None

        hostname = urlparse(url).netloc.lower()
        domains = [hostname]
        if hostname.startswith("www."):
            domains.append(hostname[4:])

        rule = {
            "site_name": parsed.get("site_name") or hostname,
            "domains": domains,
            "currency": parsed.get("currency") or "CNY",
            "name_selectors": self._selector_list(matched_selectors.get("name")),
            "price_selectors": self._selector_list(price_selector),
            "original_price_selectors": self._selector_list(matched_selectors.get("original_price")),
            "promotion_selectors": self._selector_list(matched_selectors.get("promotion")),
            "preferred_fetch_mode": "playwright" if fetch_mode == "playwright" else "requests",
            "notes": "系统根据通用识别结果自动生成。",
        }
        return rule

    @staticmethod
    def _selector_list(selector: str | None) -> list[str]:
        return [selector] if selector else []
