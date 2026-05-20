from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


MOBILE_WECHAT_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "MicroMessenger/8.0.47"
)

PAGE_HEADERS = {
    "User-Agent": MOBILE_WECHAT_UA,
}

AJAX_HEADERS = {
    "User-Agent": MOBILE_WECHAT_UA,
    "X-Requested-With": "XMLHttpRequest",
}


@dataclass(frozen=True)
class LiancaiCategory:
    fid: str
    name: str
    page_url: str
    parent_fid: str | None = None
    parent_name: str | None = None


def parse_login_response(payload: str) -> dict[str, Any]:
    return json.loads(payload or "{}")


def parse_h5_categories(html: str, *, base_url: str = "http://m.liancaiwang.cn") -> list[LiancaiCategory]:
    soup = BeautifulSoup(html or "", "html.parser")
    categories: list[LiancaiCategory] = []
    seen: set[tuple[str, str]] = set()
    for selector, fid_attr in (("span.s-category-item", "data-id"), (".type-list li[data-fid][data-url]", "data-fid")):
        for node in soup.select(selector):
            fid = str(node.get(fid_attr) or "").strip()
            page_url = str(node.get("data-url") or "").strip()
            name = node.get_text(" ", strip=True)
            if not fid or not page_url or not name:
                continue
            key = (fid, page_url)
            if key in seen:
                continue
            seen.add(key)
            categories.append(
                LiancaiCategory(
                    fid=fid,
                    name=name,
                    page_url=urljoin(base_url, page_url),
                )
            )
    return categories


def parse_h5_subcategories(
    html: str,
    *,
    parent_fid: str,
    parent_name: str,
    base_url: str = "http://m.liancaiwang.cn",
) -> list[LiancaiCategory]:
    soup = BeautifulSoup(html or "", "html.parser")
    categories: list[LiancaiCategory] = []
    seen: set[tuple[str, str]] = set()
    for node in soup.select("ul.child_terms li[data-id][data-url]"):
        fid = str(node.get("data-id") or "").strip()
        page_url = str(node.get("data-url") or "").strip()
        name = node.get_text(" ", strip=True)
        if not fid or not page_url or not name:
            continue
        key = (fid, page_url)
        if key in seen:
            continue
        seen.add(key)
        categories.append(
            LiancaiCategory(
                fid=fid,
                name=name,
                page_url=urljoin(base_url, page_url),
                parent_fid=parent_fid,
                parent_name=parent_name,
            )
        )
    return categories


def parse_goods_list_payload(payload: dict[str, Any], *, source_name: str = "莲菜网H5") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("value") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "source_name": source_name,
                "product_id": str(item.get("id") or "").strip() or None,
                "termid": str(item.get("termid") or "").strip() or None,
                "title": str(item.get("title") or "").strip(),
                "subtitle": str(item.get("subtitle") or "").strip(),
                "price": item.get("price"),
                "market_price": item.get("marketPrice"),
                "size": str(item.get("size") or "").strip(),
                "unit": str(item.get("unit") or "").strip(),
                "inventory_text": str(item.get("inv") or "").strip(),
                "cover": str(item.get("cover") or "").strip(),
                "raw": item,
            }
        )
    return rows


def parse_goods_list_page(html: str, *, base_url: str = "http://m.liancaiwang.cn") -> list[dict[str, Any]]:
    soup = BeautifulSoup(html or "", "html.parser")
    rows: list[dict[str, Any]] = []
    for node in soup.select("div.goods-item"):
        row = _build_goods_row_from_node(node, base_url=base_url)
        if row:
            rows.append(row)
    return rows


def _build_goods_row_from_node(node: Any, *, base_url: str) -> dict[str, Any] | None:
    goods_id = str(node.get("data-goodsid") or node.get("data-goodsId") or "").strip() or None
    cat_id = str(node.get("data-catid") or node.get("data-catId") or "").strip() or None

    data_payload = _extract_goods_payload(node)
    if data_payload:
        row = {
            "product_id": goods_id or str(data_payload.get("id") or "").strip() or None,
            "category_id": cat_id,
            "termid": str(data_payload.get("termid") or "").strip() or None,
            "title": str(data_payload.get("title") or "").strip(),
            "subtitle": str(data_payload.get("subtitle") or "").strip(),
            "price": data_payload.get("price"),
            "market_price": data_payload.get("marketPrice"),
            "size": str(data_payload.get("size") or "").strip(),
            "unit": str(data_payload.get("unit") or "").strip(),
            "inventory_text": str(data_payload.get("inv") or "").strip(),
            "cover": _absolute_url(base_url, str(data_payload.get("cover") or "").strip()),
            "raw": data_payload,
        }
        if row["title"]:
            return row

    text = node.get_text(" ", strip=True)
    title = _find_first_text(node, [".goods-title", ".title", "h3", "h4", "p"])
    price = _extract_price(text)
    if not title and price is None:
        return None
    return {
        "product_id": goods_id,
        "category_id": cat_id,
        "termid": None,
        "title": title or "",
        "subtitle": "",
        "price": price,
        "market_price": None,
        "size": "",
        "unit": "",
        "inventory_text": "",
        "cover": _extract_cover(node, base_url),
        "raw": {"text": text},
    }


def _extract_goods_payload(node: Any) -> dict[str, Any] | None:
    candidates = [node]
    candidates.extend(node.select(".counter, [class*='counter']"))
    for candidate in candidates:
        for attr_name, attr_value in candidate.attrs.items():
            if not isinstance(attr_value, str):
                continue
            value = attr_value.strip()
            if not value:
                continue
            parsed = _try_parse_goods_json(value)
            if parsed is not None:
                return parsed
    return None


def _try_parse_goods_json(value: str) -> dict[str, Any] | None:
    normalized = unescape(value)
    if normalized.startswith("{") and normalized.endswith("}"):
        try:
            payload = json.loads(normalized)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return None


def _extract_cover(node: Any, base_url: str) -> str:
    image = node.select_one("img[src]")
    if image and image.get("src"):
        return _absolute_url(base_url, str(image.get("src") or "").strip())
    return ""


def _absolute_url(base_url: str, value: str) -> str:
    if not value:
        return ""
    return urljoin(base_url, value)


def _find_first_text(node: Any, selectors: list[str]) -> str | None:
    for selector in selectors:
        target = node.select_one(selector)
        if target:
            text = target.get_text(" ", strip=True)
            if text:
                return text
    return None


def _extract_price(text: str) -> float | None:
    matched = re.search(r"[¥￥]\s*([0-9]+(?:\.[0-9]+)?)", text or "")
    if not matched:
        return None
    try:
        return float(matched.group(1))
    except ValueError:
        return None


class LiancaiH5Client:
    def __init__(
        self,
        *,
        phone: str,
        password: str,
        base_url: str = "http://m.liancaiwang.cn",
        timeout: int = 20,
    ) -> None:
        self.phone = phone
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(PAGE_HEADERS)
        self.login_entry = (
            f"{self.base_url}/index.php/User/login/index.html?code=testcode&state=123"
        )

    def login(self) -> dict[str, Any]:
        self.session.get(self.login_entry, timeout=self.timeout)
        response = self.session.post(
            f"{self.base_url}/index.php/user/login/dologin.html",
            headers={**AJAX_HEADERS, "Referer": self.login_entry},
            data={
                "phone": self.phone,
                "password": self.password,
                "code": "testcode",
                "openid": "",
                "wxuid": "",
            },
            timeout=self.timeout,
        )
        return parse_login_response(response.text)

    def fetch_categories(self) -> list[LiancaiCategory]:
        response = self.session.get(
            f"{self.base_url}/list/category.html",
            headers={**PAGE_HEADERS, "Referer": self.login_entry},
            timeout=self.timeout,
        )
        categories = parse_h5_categories(response.text, base_url=self.base_url)
        if categories:
            return categories

        fallback_response = self.session.get(
            f"{self.base_url}/list/index/id/6.html",
            headers={**PAGE_HEADERS, "Referer": self.login_entry},
            timeout=self.timeout,
        )
        return parse_h5_categories(fallback_response.text, base_url=self.base_url)

    def fetch_category_tree(self) -> tuple[list[LiancaiCategory], list[LiancaiCategory]]:
        top_categories = self.fetch_categories()
        subcategories: list[LiancaiCategory] = []
        for category in top_categories:
            response = self.session.get(
                category.page_url,
                headers={**PAGE_HEADERS, "Referer": self.login_entry},
                timeout=self.timeout,
            )
            subcategories.extend(
                parse_h5_subcategories(
                    response.text,
                    parent_fid=category.fid,
                    parent_name=category.name,
                    base_url=self.base_url,
                )
            )
        return top_categories, subcategories

    def fetch_category_page(self, fid: str, page: int = 1) -> list[dict[str, Any]]:
        page_path = f"/list/index/id/{fid}.html" if page <= 1 else f"/list/index/id/{fid}/page/{page}.html"
        response = self.session.get(
            f"{self.base_url}{page_path}",
            headers={**PAGE_HEADERS, "Referer": self.login_entry},
            timeout=self.timeout,
        )
        return parse_goods_list_page(response.text, base_url=self.base_url)
