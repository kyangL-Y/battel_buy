from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import ReadTimeout

from crawler.http_utils import without_proxy_env
from parsers.normalizer import normalize_price
from utils.logger import setup_logger


CHINAPRICE_SUMMARY_PAGE_URL = "https://www.chinaprice.cn/viewPage/toSummarySearchMore"
CHINAPRICE_INDEX_PAGE_URL = "https://www.chinaprice.cn/sp/index.jhtml"
CHINAPRICE_COUNT_URL = "https://www.chinaprice.cn/viewPage/summarySearchMore_count"
CHINAPRICE_DETAIL_URL = "https://www.chinaprice.cn/viewPage/summarySearchMore"
CHINAPRICE_PAGE_SIZE = 100
CHINAPRICE_DEFAULT_LANMU = "pl"
CHINAPRICE_PAGE_TIMEOUT = 30
CHINAPRICE_PAGE_RETRIES = 2
CHINAPRICE_DEFAULT_HISTORY_DAYS = 730
CHINAPRICE_CITY_TREE_HISTORY_DAYS = 60
CHINAPRICE_DEFAULT_MENU_CODES = [
    "syyhzjg",
    "twphzjg",
    "rqdhzjg",
    "scphzjg",
    "sclhzjg",
    "sglhzjg",
    "qtsphzjg",
    "pfscsphzjg",
]
CHINAPRICE_MENU_NAME_MAP = {
    "syyhzjg": "食用油汇总价格",
    "twphzjg": "调味品汇总价格",
    "rqdhzjg": "肉禽蛋汇总价格",
    "scphzjg": "水产品汇总价格",
    "sclhzjg": "蔬菜类汇总价格",
    "sglhzjg": "水果类汇总价格",
    "qtsphzjg": "其他食品汇总价格",
    "pfscsphzjg": "批发市场食品汇总价格",
}
PFSC_TABLE_API_URL = "https://pfsc.agri.cn/api/priceQuotationController/pageList"
PFSC_TABLE_PAGE_SIZE = 200
MOA_WHOLESALE_TREE_URL = "https://ncpscxx.moa.gov.cn/product/homeWholesaleProduct/selectTree"
MOA_WHOLESALE_MARKET_URL = "https://ncpscxx.moa.gov.cn/product/homeWholesalePrice/proAndMarket"
MOA_WHOLESALE_CHART_URL = "https://ncpscxx.moa.gov.cn/product/homeWholesalePrice/selectWholesalePriceChart"
MOA_WHOLESALE_AES_KEY = "7s9K$pG2xQ8zR5mB7vA3sD9fH2jW40cV"

PUBLIC_NAME_ALIASES = {
    "大白菜": "白菜",
    "猪肉(白条猪)": "白条猪",
    "花菜(菜花)": "花菜",
    "洋葱(元葱)": "洋葱",
}

PFSC_MARKET_KEYS = [
    "marketName",
    "wholesaleMarketName",
    "market",
    "market_name",
    "marketFullName",
    "regionName",
    "provinceName",
]
PFSC_PRICE_KEYS = ["priceAvg", "avgPrice", "price", "currentPrice"]
PFSC_DATE_KEYS = ["recordDate", "reportDate", "date", "publishDate"]
PFSC_UNIT_KEYS = ["unit", "unitName", "priceUnit"]
MUNICIPALITY_PREFIXES = ("北京", "上海", "天津", "重庆")


class PublicSourceCrawler:
    def __init__(
        self,
        timeout: int = 15,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        default_max_workers: int = 1,
    ) -> None:
        self.timeout = timeout
        self.progress_callback = progress_callback
        self.default_max_workers = max(1, int(default_max_workers))
        self.logger = setup_logger()
        self._session_state = threading.local()
        self._chinaprice_page_cache: dict[tuple[str, str | None, str | None, str], str] = {}
        self._chinaprice_menu_codes_cache: list[str] | None = None
        self._pfsc_variety_cache: dict[str, str] | None = None
        self._pfsc_items_cache: list[dict[str, Any]] | None = None
        self._moa_wholesale_items_cache: list[dict[str, Any]] | None = None
        self._moa_wholesale_market_cache: list[dict[str, Any]] | None = None

    @staticmethod
    def _proxy_bypass() -> dict[str, None]:
        return {"http": None, "https": None}

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=8, pool_maxsize=8, pool_block=False)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_session(self) -> requests.Session:
        session = getattr(self._session_state, "session", None)
        if session is None:
            session = self._build_session()
            self._session_state.session = session
        return session

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("proxies", self._proxy_bypass())
        with without_proxy_env():
            response = self._get_session().request(method, url, **kwargs)
        response.raise_for_status()
        return response

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
    def _to_positive_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def normalize_public_product_name(name: str) -> str:
        cleaned = str(name or "").strip()
        if not cleaned:
            return ""
        if cleaned in PUBLIC_NAME_ALIASES:
            return PUBLIC_NAME_ALIASES[cleaned]
        bracket_trimmed = re.sub(r"[（(].*?[）)]", "", cleaned).strip()
        return PUBLIC_NAME_ALIASES.get(bracket_trimmed, bracket_trimmed or cleaned)

    @staticmethod
    def split_public_product_label(label: str) -> tuple[str, str | None]:
        parts = [part.strip() for part in str(label or "").split("-") if part.strip()]
        if not parts:
            return "", None
        source_name = parts[0]
        spec_text = "-".join(parts[1:]) or None
        return source_name, spec_text

    @staticmethod
    def _clean_geo_text(value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

    @classmethod
    def infer_market_geo(
        cls,
        market_name: Any = None,
        region_name: Any = None,
        province_name: Any = None,
        city_name: Any = None,
    ) -> dict[str, str | None]:
        market_text = cls._clean_geo_text(market_name)
        region_text = cls._clean_geo_text(region_name)
        province_text = cls._clean_geo_text(province_name)
        city_text = cls._clean_geo_text(city_name)

        if not province_text and region_text:
            if region_text.endswith(("省", "市", "自治区", "特别行政区")) or region_text in {"全国"}:
                province_text = region_text
        if not city_text and region_text and region_text != province_text:
            city_text = region_text

        if market_text and not province_text:
            for prefix in MUNICIPALITY_PREFIXES:
                if market_text.startswith(prefix):
                    province_text = f"{prefix}市"
                    city_text = city_text or f"{prefix}市"
                    break
        if market_text and not city_text:
            if province_text and market_text.startswith(province_text.replace("省", "").replace("市", "")):
                city_text = province_text

        region_label = region_text or city_text or province_text
        return {
            "province": province_text,
            "city": city_text,
            "market_name": market_text,
            "region_label": region_label,
        }

    @staticmethod
    def _decode_json_response(response: requests.Response) -> Any:
        content_type = str(response.headers.get("content-type") or "").lower()
        if content_type.startswith("application/json"):
            return response.json()
        return json.loads(response.text)

    def fetch_chinaprice(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        results: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str, str, str]] = set()
        queries = self.get_chinaprice_queries(product, site_rule)
        total_queries = len(queries)
        if total_queries:
            self._report_progress(0.02, f"Chinaprice 准备抓取 {total_queries} 组查询")

        for query_index, query in enumerate(queries, start=1):
            end_date, begin_date = self._resolve_chinaprice_date_range(query, site_rule)
            item_context = {
                **dict(query["item"]),
                "menu_code": query["menu_code"],
                "menu_name": query["menu_name"],
                "subtask_id": query["subtask_id"],
                "subtask_label": query["subtask_label"],
                "tree_id": query["tree_id"],
                "tree_label": query["tree_label"],
            }
            count_payload = {
                "SUBTASK_ID": query["subtask_id"],
                "TREE_ID": query["tree_id"],
                "BEGINDATE": begin_date.isoformat(),
                "ENDDATE": end_date.isoformat(),
                "areaId": query["area_value"],
                "jg": ",".join(query["price_values"]),
                "pz": item_context["item_id"],
            }
            count_response = self._request(
                "POST",
                CHINAPRICE_COUNT_URL,
                headers=headers,
                data=count_payload,
            )
            count_body = self._decode_json_response(count_response)
            if not isinstance(count_body, dict) or int(count_body.get("count") or 0) <= 0 or not count_body.get("maxqh"):
                if total_queries:
                    self._report_progress(
                        0.45 * (query_index / total_queries),
                        f"Chinaprice 查询 {query_index}/{total_queries} 无可用结果",
                    )
                continue

            total_count = int(count_body.get("count") or 0)
            total_pages = max(1, math.ceil(total_count / CHINAPRICE_PAGE_SIZE))
            for start_row in range(0, total_count, CHINAPRICE_PAGE_SIZE):
                page_index = start_row // CHINAPRICE_PAGE_SIZE + 1
                detail_payload = dict(count_payload)
                detail_payload.update(
                    {
                        "startRow": start_row,
                        "pageSize": CHINAPRICE_PAGE_SIZE,
                        "maxqh": count_body["maxqh"],
                    }
                )
                detail_response = self._request(
                    "POST",
                    CHINAPRICE_DETAIL_URL,
                    headers=headers,
                    data=detail_payload,
                )
                detail_body = self._decode_json_response(detail_response)
                parsed_rows = self.extract_chinaprice_rows(detail_body, item_context)
                if total_queries:
                    progress = ((query_index - 1) + (page_index / total_pages)) / total_queries
                    detail = f"Chinaprice 查询 {query_index}/{total_queries}，第 {page_index}/{total_pages} 页"
                    self._report_progress(0.45 * progress, detail)
                if not parsed_rows:
                    break
                for parsed in parsed_rows:
                    identity = (
                        str(parsed.get("product_name") or ""),
                        str(parsed.get("site_name") or ""),
                        str(parsed.get("promotion_text") or ""),
                        str(parsed.get("extra_fields", {}).get("tree_label") or ""),
                    )
                    if identity in seen_keys:
                        continue
                    seen_keys.add(identity)
                    results.append(parsed)
        if total_queries:
            self._report_progress(0.45, f"Chinaprice 抓取完成，共 {len(results)} 条")
        return results

    @staticmethod
    def _resolve_chinaprice_date_range(
        query: dict[str, Any],
        site_rule: dict[str, Any] | None = None,
    ) -> tuple[date, date]:
        end_date = date.today()
        default_days = CHINAPRICE_DEFAULT_HISTORY_DAYS
        city_tree_days = CHINAPRICE_CITY_TREE_HISTORY_DAYS
        if isinstance(site_rule, dict):
            default_days = PublicSourceCrawler._to_positive_int(
                site_rule.get("chinaprice_history_days"),
                CHINAPRICE_DEFAULT_HISTORY_DAYS,
            )
            city_tree_days = PublicSourceCrawler._to_positive_int(
                site_rule.get("chinaprice_city_tree_history_days"),
                CHINAPRICE_CITY_TREE_HISTORY_DAYS,
            )
        tree_label = str(query.get("tree_label") or "").strip()
        history_days = city_tree_days if "36大中城市" in tree_label else default_days
        begin_date = end_date - timedelta(days=history_days)
        return end_date, begin_date

    def get_chinaprice_queries(
        self,
        product: dict[str, Any],
        site_rule: dict | None = None,
    ) -> list[dict[str, Any]]:
        url = str(product.get("url") or "")
        parsed_url = urlparse(url)
        query_args = parse_qs(parsed_url.query)
        lanmu = str(query_args.get("lanmu", [CHINAPRICE_DEFAULT_LANMU])[0] or CHINAPRICE_DEFAULT_LANMU)
        initial_menu = str(query_args.get("MENUNAME", [""])[0] or "").strip()
        configured_menus = site_rule.get("chinaprice_menu_codes") if isinstance(site_rule, dict) else None
        menu_codes = [
            str(menu).strip()
            for menu in (configured_menus or self.discover_chinaprice_menu_codes())
            if str(menu).strip()
        ]
        if initial_menu and initial_menu not in menu_codes:
            menu_codes.append(initial_menu)

        queries: list[dict[str, Any]] = []
        seen_states: set[tuple[str, str, str]] = set()
        for menu_code in menu_codes:
            try:
                base_state = self.get_chinaprice_page_state(menu_code=menu_code, lanmu=lanmu)
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Chinaprice 菜单加载失败: %s | error=%s", menu_code, exc)
                continue
            if not base_state["items"]:
                continue
            subtask_options = base_state["subtask_options"] or [
                {
                    "id": base_state["current_subtask_id"],
                    "label": base_state["current_subtask_label"] or "",
                }
            ]
            for subtask in subtask_options:
                subtask_id = str(subtask.get("id") or "").strip()
                if not subtask_id:
                    continue
                try:
                    state = (
                        base_state
                        if subtask_id == base_state["current_subtask_id"]
                        else self.get_chinaprice_page_state(menu_code=menu_code, lanmu=lanmu, subtask_id=subtask_id)
                    )
                except Exception as exc:  # noqa: BLE001
                    self.logger.warning(
                        "Chinaprice 子任务加载失败: %s | subtask=%s | error=%s",
                        menu_code,
                        subtask_id,
                        exc,
                    )
                    continue
                if not state["items"]:
                    continue
                tree_options = state["tree_options"] or [
                    {
                        "id": state["current_tree_id"],
                        "label": state["current_tree_label"] or "",
                    }
                ]
                for tree in tree_options:
                    tree_id = str(tree.get("id") or "").strip()
                    if not tree_id:
                        continue
                    try:
                        query_state = (
                            state
                            if tree_id == state["current_tree_id"]
                            else self.get_chinaprice_page_state(
                                menu_code=menu_code,
                                lanmu=lanmu,
                                subtask_id=subtask_id,
                                tree_id=tree_id,
                            )
                        )
                    except Exception as exc:  # noqa: BLE001
                        self.logger.warning(
                            "Chinaprice 汇总树加载失败: %s | subtask=%s | tree=%s | error=%s",
                            menu_code,
                            subtask_id,
                            tree_id,
                            exc,
                        )
                        continue
                    if not query_state["items"]:
                        continue
                    state_key = (
                        menu_code,
                        query_state["current_subtask_id"] or subtask_id,
                        query_state["current_tree_id"] or tree_id,
                    )
                    if state_key in seen_states:
                        continue
                    seen_states.add(state_key)

                    for item in query_state["items"]:
                        queries.append(
                            {
                                "menu_code": menu_code,
                                "menu_name": query_state["menu_name"],
                                "subtask_id": query_state["current_subtask_id"] or subtask_id,
                                "subtask_label": query_state["current_subtask_label"] or str(subtask.get("label") or "").strip(),
                                "tree_id": query_state["current_tree_id"] or tree_id,
                                "tree_label": query_state["current_tree_label"] or str(tree.get("label") or "").strip(),
                                "area_id": query_state["area_id"],
                                "area_value": query_state["area_value"],
                                "price_values": query_state["price_values"],
                                "item": item,
                            }
                        )
        return queries

    def discover_chinaprice_menu_codes(self) -> list[str]:
        if self._chinaprice_menu_codes_cache is not None:
            return list(self._chinaprice_menu_codes_cache)

        try:
            html = self._request("GET", CHINAPRICE_INDEX_PAGE_URL, headers={"User-Agent": "Mozilla/5.0"}).text
            menu_codes = self._extract_chinaprice_menu_codes(html)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Chinaprice 菜单发现失败，改用默认菜单列表: error=%s", exc)
            menu_codes = []

        if not menu_codes:
            menu_codes = list(CHINAPRICE_DEFAULT_MENU_CODES)
        self._chinaprice_menu_codes_cache = menu_codes
        return list(menu_codes)

    @staticmethod
    def _format_chinaprice_area_values(area_ids: list[str]) -> str:
        clean_ids = [str(area_id).strip() for area_id in area_ids if str(area_id).strip()]
        if not clean_ids:
            return "3435"
        return ",".join(f"'{area_id}'" for area_id in clean_ids)

    @classmethod
    def _resolve_chinaprice_area_value(cls, state: dict[str, Any]) -> str:
        tree_label = str(state.get("current_tree_label") or "").strip()
        child_ids = [str(item).strip() for item in state.get("area_child_ids") or [] if str(item).strip()]
        root_id = str(state.get("area_id") or "").strip()
        if "36大中城市" in tree_label and child_ids:
            return cls._format_chinaprice_area_values(child_ids)
        return root_id or cls._format_chinaprice_area_values(child_ids)

    def get_chinaprice_page_state(
        self,
        menu_code: str,
        lanmu: str = CHINAPRICE_DEFAULT_LANMU,
        subtask_id: str | None = None,
        tree_id: str | None = None,
    ) -> dict[str, Any]:
        html = self.fetch_chinaprice_page_html(
            menu_code=menu_code,
            lanmu=lanmu,
            subtask_id=subtask_id,
            tree_id=tree_id,
        )
        return self.parse_chinaprice_page_state(html, menu_code=menu_code)

    def fetch_chinaprice_page_html(
        self,
        menu_code: str,
        lanmu: str = CHINAPRICE_DEFAULT_LANMU,
        subtask_id: str | None = None,
        tree_id: str | None = None,
    ) -> str:
        cache_key = (menu_code, subtask_id, tree_id, lanmu)
        if cache_key in self._chinaprice_page_cache:
            return self._chinaprice_page_cache[cache_key]

        headers = {"User-Agent": "Mozilla/5.0"}
        for attempt in range(1, CHINAPRICE_PAGE_RETRIES + 1):
            try:
                if subtask_id or tree_id:
                    payload = {
                        "lanmu": lanmu,
                        "MENUNAME": menu_code,
                    }
                    if subtask_id:
                        payload["subtaskid"] = subtask_id
                    if tree_id:
                        payload["TREE_ID"] = tree_id
                    response = self._request(
                        "POST",
                        CHINAPRICE_SUMMARY_PAGE_URL,
                        headers=headers,
                        data=payload,
                        timeout=max(self.timeout, CHINAPRICE_PAGE_TIMEOUT),
                    )
                else:
                    response = self._request(
                        "GET",
                        f"{CHINAPRICE_SUMMARY_PAGE_URL}?lanmu={lanmu}&MENUNAME={menu_code}",
                        headers=headers,
                        timeout=max(self.timeout, CHINAPRICE_PAGE_TIMEOUT),
                    )
                html = response.text
                self._chinaprice_page_cache[cache_key] = html
                return html
            except ReadTimeout:
                if attempt >= CHINAPRICE_PAGE_RETRIES:
                    raise
                self.logger.warning(
                    "Chinaprice 页面读取超时，准备重试: %s | subtask=%s | tree=%s | attempt=%s",
                    menu_code,
                    subtask_id,
                    tree_id,
                    attempt,
                )
        raise RuntimeError(f"Chinaprice 页面加载失败: {menu_code}")

    def parse_chinaprice_page_state(self, html: str, menu_code: str | None = None) -> dict[str, Any]:
        soup = BeautifulSoup(str(html or ""), "html.parser")
        subtask_options = self._extract_chinaprice_select_options(soup, "subtask")
        tree_options = self._extract_chinaprice_select_options(soup, "tree")
        current_subtask = next((option for option in subtask_options if option.get("selected")), subtask_options[0] if subtask_options else None)
        current_tree = next((option for option in tree_options if option.get("selected")), tree_options[0] if tree_options else None)
        area_options = self._extract_chinaprice_vue_options(str(html or ""), "vm")
        price_values = self._extract_chinaprice_checkbox_values(soup, "jg")
        menu_name = self._extract_chinaprice_menu_name(str(html or "")) or CHINAPRICE_MENU_NAME_MAP.get(str(menu_code or "").strip()) or str(menu_code or "").strip()
        area_id = self._extract_chinaprice_area_id(area_options)
        area_child_ids = self._extract_chinaprice_area_child_ids(area_options)
        return {
            "menu_code": str(menu_code or "").strip(),
            "menu_name": menu_name,
            "subtask_options": subtask_options,
            "tree_options": tree_options,
            "current_subtask_id": current_subtask["id"] if current_subtask else None,
            "current_subtask_label": current_subtask["label"] if current_subtask else None,
            "current_tree_id": current_tree["id"] if current_tree else None,
            "current_tree_label": current_tree["label"] if current_tree else None,
            "area_id": area_id,
            "area_child_ids": area_child_ids,
            "area_value": self._resolve_chinaprice_area_value(
                {
                    "current_tree_label": current_tree["label"] if current_tree else None,
                    "area_id": area_id,
                    "area_child_ids": area_child_ids,
                }
            ),
            "price_values": price_values,
            "items": self.parse_chinaprice_items(html),
        }

    def parse_chinaprice_items(self, html: str) -> list[dict[str, Any]]:
        options = self._extract_chinaprice_vue_options(str(html or ""), "vm1")
        if not options:
            raise RuntimeError("未找到 Chinaprice 商品树定义")
        items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for category in options:
            if not isinstance(category, dict):
                continue
            category_name = str(category.get("label") or "").strip() or "未分类"
            for child in category.get("children") or []:
                if not isinstance(child, dict):
                    continue
                item_id = str(child.get("id") or "").strip()
                label = str(child.get("label") or "").strip()
                if not item_id or not label or item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                source_name, spec_text = self.split_public_product_label(label)
                canonical_name = self.normalize_public_product_name(source_name)
                items.append(
                    {
                        "canonical_name": canonical_name or source_name,
                        "source_name": source_name,
                        "category": category_name,
                        "item_id": item_id,
                        "spec_text": spec_text,
                    }
                )
        items = self._disambiguate_chinaprice_items(items)
        if not items:
            raise RuntimeError("Chinaprice 商品树为空")
        return items

    @staticmethod
    def _extract_chinaprice_variant_name(spec_text: str | None) -> str | None:
        parts = [part.strip() for part in str(spec_text or "").split("-") if part.strip()]
        if not parts:
            return None
        if len(parts) == 1:
            return parts[0] or None
        if parts[-1].startswith("元/"):
            variant = "-".join(parts[:-1]).strip()
            return variant or None
        return "-".join(parts).strip() or None

    @classmethod
    def _disambiguate_chinaprice_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        name_counts = Counter(str(item.get("canonical_name") or "").strip() for item in items if str(item.get("canonical_name") or "").strip())
        normalized_items: list[dict[str, Any]] = []
        for item in items:
            canonical_name = str(item.get("canonical_name") or "").strip()
            if canonical_name and name_counts.get(canonical_name, 0) > 1:
                variant_name = cls._extract_chinaprice_variant_name(item.get("spec_text"))
                if variant_name and variant_name != canonical_name:
                    item = dict(item)
                    item["canonical_name"] = f"{canonical_name}（{variant_name}）"
            normalized_items.append(item)
        return normalized_items

    @staticmethod
    def _extract_chinaprice_select_options(soup: BeautifulSoup, select_id: str) -> list[dict[str, Any]]:
        select = soup.find("select", id=select_id)
        if select is None:
            return []
        options: list[dict[str, Any]] = []
        for option in select.find_all("option"):
            option_id = str(option.get("value") or "").strip()
            label = option.get_text(strip=True)
            if option_id:
                options.append(
                    {
                        "id": option_id,
                        "label": label,
                        "selected": option.has_attr("selected"),
                    }
                )
        return options

    @staticmethod
    def _extract_chinaprice_checkbox_values(soup: BeautifulSoup, name: str) -> list[str]:
        values: list[str] = []
        for checkbox in soup.find_all("input", attrs={"name": name}):
            value = str(checkbox.get("value") or "").strip()
            if value:
                values.append(value)
        return values

    @staticmethod
    def _extract_chinaprice_menu_name(html: str) -> str | None:
        match = re.search(r"var\s+menuname='([^']+)'", html)
        if not match:
            return None
        value = str(match.group(1) or "").strip()
        return value or None

    @staticmethod
    def _extract_chinaprice_menu_codes(html: str) -> list[str]:
        text = str(html or "")
        discovered: list[str] = []
        seen: set[str] = set()
        name_to_code = {value: key for key, value in CHINAPRICE_MENU_NAME_MAP.items()}
        patterns = [
            r"moreFind\('([^']+)'\)",
            r"MENUNAME=([A-Za-z0-9_]+)",
        ]
        for pattern in patterns:
            for raw_code in re.findall(pattern, text):
                code = str(raw_code or "").strip()
                if code in name_to_code:
                    code = name_to_code[code]
                if not code or code in seen:
                    continue
                if not re.fullmatch(r"[A-Za-z0-9_]+", code):
                    continue
                seen.add(code)
                discovered.append(code)
        for default_code in CHINAPRICE_DEFAULT_MENU_CODES:
            if default_code not in seen:
                discovered.append(default_code)
        return discovered

    @staticmethod
    def _extract_chinaprice_area_id(area_options: list[dict[str, Any]]) -> str:
        for option in area_options:
            if str(option.get("label") or "").strip() == "全国":
                area_id = str(option.get("id") or "").strip()
                if area_id:
                    return area_id
        if area_options:
            return str(area_options[0].get("id") or "").strip()
        return "3435"

    @staticmethod
    def _extract_chinaprice_area_child_ids(area_options: list[dict[str, Any]]) -> list[str]:
        for option in area_options:
            label = str(option.get("label") or "").strip()
            if label in {"全国", "36大中城市"}:
                return [
                    str(child.get("id") or "").strip()
                    for child in option.get("children") or []
                    if str(child.get("id") or "").strip()
                ]
        if area_options:
            return [
                str(child.get("id") or "").strip()
                for child in area_options[0].get("children") or []
                if str(child.get("id") or "").strip()
            ]
        return []

    def _extract_chinaprice_vue_options(self, html: str, var_name: str) -> list[dict[str, Any]]:
        options_json = self._extract_chinaprice_options_json(html, var_name)
        return json.loads(options_json) if options_json else []

    @staticmethod
    def _extract_chinaprice_options_json(html: str, var_name: str) -> str | None:
        anchor = html.find(f"var {var_name}")
        if anchor < 0:
            return None
        options_anchor = html.find("options:[", anchor)
        if options_anchor < 0:
            return None
        start = html.find("[", options_anchor)
        if start < 0:
            return None

        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(html)):
            char = html[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return html[start : index + 1]
        return None

    def extract_chinaprice_row(self, payload: dict[str, Any], item: dict[str, Any]) -> dict[str, Any] | None:
        rows = self.extract_chinaprice_rows(payload, item)
        return rows[0] if rows else None

    def extract_chinaprice_rows(self, payload: dict[str, Any], item: dict[str, Any]) -> list[dict[str, Any]]:
        row_html = str((payload or {}).get("fhxx") or "").strip()
        if not row_html:
            return []
        menu_name = str(item.get("menu_name") or "").strip()
        tree_label = str(item.get("tree_label") or "").strip()
        source_tag = " | ".join(part for part in [menu_name, tree_label] if part)
        rows: list[dict[str, Any]] = []
        cell_fragments = re.findall(r"<td\b[^>]*>(.*?)</td>", row_html, flags=re.IGNORECASE | re.DOTALL)
        cells = [BeautifulSoup(fragment, "html.parser").get_text(strip=True) for fragment in cell_fragments]
        for offset in range(0, len(cells), 7):
            chunk = cells[offset : offset + 7]
            if len(chunk) < 7:
                continue
            try:
                current_price = float(chunk[6])
            except (TypeError, ValueError):
                continue

            report_date = chunk[3]
            region = chunk[4]
            quote_site = chunk[5]
            unit_label = chunk[2]
            source_name = chunk[0]
            site_label = quote_site or region or "未命名报价点"
            if source_tag:
                site_label = f"{site_label} | {source_tag}"
            rows.append(
                {
                    "site_name": f"Chinaprice | {site_label}",
                    "product_name": item["canonical_name"],
                    "current_price": current_price,
                    "original_price": None,
                    "promotion_text": " | ".join(
                        part
                        for part in [menu_name, tree_label, region, quote_site, report_date]
                        if str(part or "").strip()
                    ),
                    "currency": "CNY",
                    "matched_rule": "Chinaprice公开汇总",
                    "raw_extract": {
                        "source_name": source_name,
                        "region": region,
                        "quote_site": quote_site,
                        "menu_code": item.get("menu_code"),
                        "menu_name": menu_name,
                        "subtask_id": item.get("subtask_id"),
                        "subtask_label": item.get("subtask_label"),
                        "tree_id": item.get("tree_id"),
                        "tree_label": tree_label,
                        "row_cells": chunk,
                    },
                    "extra_fields": {
                        "group_name": item["category"],
                        "category": item["category"],
                        "spec_text": unit_label,
                        "compare_key": item["canonical_name"],
                        "menu_code": item.get("menu_code"),
                        "menu_name": menu_name,
                        "subtask_id": item.get("subtask_id"),
                        "subtask_label": item.get("subtask_label"),
                        "tree_id": item.get("tree_id"),
                        "tree_label": tree_label,
                        **self.infer_market_geo(
                            market_name=quote_site,
                            region_name=region,
                            city_name=region,
                        ),
                    },
                }
            )
        return rows

    def fetch_pfsc(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        table_rows = self.fetch_pfsc_table(site_rule)
        if table_rows:
            self._report_progress(0.45, f"PFSC 分页接口已返回 {len(table_rows)} 条")
            return table_rows

        items = self.get_pfsc_items()
        max_varieties = self._to_positive_int((site_rule or {}).get("max_varieties"), len(items))
        max_workers = min(
            self._to_positive_int((site_rule or {}).get("max_workers"), self.default_max_workers),
            max(1, min(len(items), max_varieties)),
        )
        selected_items = items[:max_varieties]
        if not selected_items:
            return []
        self._report_progress(0.05, f"PFSC 准备抓取 {len(selected_items)} 个品种")

        if max_workers <= 1:
            results: list[dict[str, Any]] = []
            for index, item in enumerate(selected_items, start=1):
                results.extend(self.fetch_pfsc_chart_item(item))
                self._report_progress(0.05 + 0.4 * (index / len(selected_items)), f"PFSC 品种 {index}/{len(selected_items)}")
            return results

        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(self.fetch_pfsc_chart_item, item): item for item in selected_items}
            completed = 0
            for future in as_completed(future_map):
                item = future_map[future]
                try:
                    results.extend(future.result())
                except Exception as exc:  # noqa: BLE001
                    self.logger.warning("PFSC 品种抓取失败: %s | error=%s", item.get("source_name"), exc)
                completed += 1
                self._report_progress(0.05 + 0.4 * (completed / len(selected_items)), f"PFSC 品种 {completed}/{len(selected_items)}")
        return results

    def fetch_pfsc_table(self, site_rule: dict | None = None) -> list[dict[str, Any]]:
        site_rule = site_rule or {}
        api_url = str(site_rule.get("table_api_url") or PFSC_TABLE_API_URL)
        page_size = self._to_positive_int(site_rule.get("page_size"), PFSC_TABLE_PAGE_SIZE)
        max_pages = self._to_positive_int(site_rule.get("max_pages"), 200)
        results: list[dict[str, Any]] = []
        try:
            for page_num in range(1, max_pages + 1):
                payload = {
                    "pageNum": page_num,
                    "pageSize": page_size,
                    "marketId": "",
                    "provinceCode": "",
                    "pid": "",
                    "varietyId": "",
                }
                response = self._request("POST", api_url, json=payload)
                body = self._decode_json_response(response)
                if not isinstance(body, dict) or body.get("code") not in {0, 200}:
                    break
                content = body.get("content") or body.get("data") or {}
                if not isinstance(content, dict):
                    break
                list_items = content.get("list") or []
                page_rows = self.parse_pfsc_table_rows(list_items)
                if not page_rows:
                    break
                results.extend(page_rows)
                total = self._to_positive_int(content.get("total"), 0)
                total_pages = max(1, math.ceil(total / page_size)) if total else None
                if total_pages:
                    self._report_progress(0.05 + 0.4 * (page_num / total_pages), f"PFSC 分页 {page_num}/{total_pages}")
                else:
                    self._report_progress(0.1, f"PFSC 已抓取第 {page_num} 页")
                if total and page_num * page_size >= total:
                    break
                has_next = content.get("hasNext")
                if has_next is False:
                    break
        except Exception as exc:  # noqa: BLE001
            self.logger.info("PFSC 分页接口不可用，回退图表接口: %s", exc)
            return []
        return results

    def parse_pfsc_table_rows(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            product_name = self.normalize_public_product_name(str(item.get("productName") or item.get("varietyName") or "").strip())
            current_price = None
            for key in PFSC_PRICE_KEYS:
                current_price = normalize_price(item.get(key))
                if current_price is not None:
                    break
            if not product_name or current_price is None:
                continue

            site_label = next((str(item.get(key) or "").strip() for key in PFSC_MARKET_KEYS if item.get(key)), "")
            report_date = next((str(item.get(key) or "").strip() for key in PFSC_DATE_KEYS if item.get(key)), "")
            spec_text = next((str(item.get(key) or "").strip() for key in PFSC_UNIT_KEYS if item.get(key)), "") or "公斤"
            category = str(item.get("categoryName") or item.get("majorCategoryName") or "未分类").strip()
            geo_fields = self.infer_market_geo(
                market_name=site_label,
                region_name=item.get("regionName"),
                province_name=item.get("provinceName"),
                city_name=item.get("cityName"),
            )
            rows.append(
                {
                    "site_name": f"PFSC | {site_label or '市场报价'}",
                    "product_name": product_name,
                    "current_price": current_price,
                    "original_price": None,
                    "promotion_text": f"PFSC市场报价 | {report_date}".strip(),
                    "currency": "CNY",
                    "matched_rule": "PFSC分页接口",
                    "raw_extract": {
                        "item_preview": json.dumps(item, ensure_ascii=False)[:1000],
                    },
                    "extra_fields": {
                        "group_name": category,
                        "category": category,
                        "spec_text": spec_text,
                        "compare_key": product_name,
                        **geo_fields,
                    },
                }
            )
        return rows

    def fetch_pfsc_chart_item(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        response = self._request(
            "POST",
            "https://pfsc.agri.cn/price_portal/index/getMarketReportPriceChart",
            params={"varietyID": item["variety_id"]},
        )
        payload = response.json()
        encrypted = (payload or {}).get("data")
        if not encrypted:
            return []
        chart_data = json.loads(self.decrypt_pfsc_chart_data(encrypted))
        return self.build_pfsc_rows(chart_data, item)

    def get_pfsc_items(self) -> list[dict[str, Any]]:
        if self._pfsc_items_cache is not None:
            return self._pfsc_items_cache
        response = self._request("GET", "https://pfsc.agri.cn/price_portal/sys-user-relation/getVarietiesTree")
        payload = response.json()
        items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        self._collect_pfsc_items(payload, items, seen_ids, [])
        if not items:
            raise RuntimeError("PFSC 品种树为空")
        self._pfsc_items_cache = items
        self._pfsc_variety_cache = {item["source_name"]: item["variety_id"] for item in items}
        return items

    def get_pfsc_variety_map(self) -> dict[str, str]:
        if self._pfsc_variety_cache is not None:
            return self._pfsc_variety_cache
        items = self.get_pfsc_items()
        self._pfsc_variety_cache = {item["source_name"]: item["variety_id"] for item in items}
        return self._pfsc_variety_cache

    def _collect_pfsc_items(
        self,
        payload: Any,
        items: list[dict[str, Any]],
        seen_ids: set[str],
        category_path: list[str],
    ) -> None:
        if isinstance(payload, list):
            for item in payload:
                self._collect_pfsc_items(item, items, seen_ids, category_path)
            return
        if not isinstance(payload, dict):
            return

        label = str(payload.get("varietyName") or payload.get("label") or "").strip()
        child_nodes = []
        for key in ("content", "children", "attributelist"):
            child = payload.get(key)
            if isinstance(child, list) and child:
                child_nodes.extend(child)
            elif isinstance(child, dict):
                child_nodes.append(child)

        next_path = list(category_path)
        if label and child_nodes:
            next_path.append(label)

        if child_nodes:
            for child in child_nodes:
                self._collect_pfsc_items(child, items, seen_ids, next_path)
            return

        variety_id = str(payload.get("id") or "").strip()
        if not variety_id or not label or variety_id in seen_ids:
            return
        seen_ids.add(variety_id)
        category = next((entry for entry in reversed(category_path) if entry), "未分类")
        items.append(
            {
                "variety_id": variety_id,
                "source_name": label,
                "canonical_name": self.normalize_public_product_name(label),
                "category": category,
            }
        )

    @staticmethod
    def resolve_pfsc_variety_id(variety_map: dict[str, str], aliases: list[str]) -> str | None:
        for alias in aliases:
            if alias in variety_map:
                return variety_map[alias]
        return None

    def build_pfsc_rows(self, chart_data: dict[str, Any], item: dict[str, Any]) -> list[dict[str, Any]]:
        report_date = str(chart_data.get("date") or "")
        markets = list(chart_data.get("x") or [])
        prices = list(chart_data.get("y") or [])
        rows: list[dict[str, Any]] = []
        for market_name, price in zip(markets, prices):
            try:
                current_price = float(price)
            except (TypeError, ValueError):
                continue
            geo_fields = self.infer_market_geo(market_name=market_name)
            rows.append(
                {
                    "site_name": f"PFSC | {str(market_name).strip()}",
                    "product_name": item["canonical_name"],
                    "current_price": current_price,
                    "original_price": None,
                    "promotion_text": f"PFSC市场行情 | {report_date}",
                    "currency": "CNY",
                    "matched_rule": "PFSC图表接口",
                    "raw_extract": {
                        "report_date": report_date,
                        "market_name": market_name,
                    },
                    "extra_fields": {
                        "group_name": item["category"],
                        "category": item["category"],
                        "spec_text": "公斤",
                        "compare_key": item["canonical_name"],
                        **geo_fields,
                    },
                }
            )
        return rows

    def fetch_moa_wholesale(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        site_rule = site_rule or {}
        items = self.get_moa_wholesale_items()
        max_varieties = self._to_positive_int(site_rule.get("max_varieties"), len(items))
        max_workers = min(
            self._to_positive_int(site_rule.get("max_workers"), self.default_max_workers),
            max(1, min(len(items), max_varieties)),
        )
        selected_items = items[:max_varieties]
        if not selected_items:
            return []
        self._report_progress(0.05, f"重点农产品平台准备抓取 {len(selected_items)} 个品种")

        if max_workers <= 1:
            results: list[dict[str, Any]] = []
            for index, item in enumerate(selected_items, start=1):
                results.extend(self.fetch_moa_wholesale_item(item))
                self._report_progress(
                    0.05 + 0.4 * (index / len(selected_items)),
                    f"重点农产品平台品种 {index}/{len(selected_items)}",
                )
            return results

        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(self.fetch_moa_wholesale_item, item): item for item in selected_items}
            completed = 0
            for future in as_completed(future_map):
                item = future_map[future]
                try:
                    results.extend(future.result())
                except Exception as exc:  # noqa: BLE001
                    self.logger.warning("重点农产品平台品种抓取失败: %s | error=%s", item.get("source_name"), exc)
                completed += 1
                self._report_progress(
                    0.05 + 0.4 * (completed / len(selected_items)),
                    f"重点农产品平台品种 {completed}/{len(selected_items)}",
                )
        return results

    def fetch_moa_wholesale_item(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        response = self._request(
            "POST",
            MOA_WHOLESALE_CHART_URL,
            params={
                "varietyCode": item["variety_id"],
                "marketNames": "",
                "provinceNames": "",
            },
        )
        payload = response.json()
        encrypted = (payload or {}).get("data")
        if not encrypted:
            return []
        chart_data = json.loads(self.decrypt_aes_chart_data(encrypted, MOA_WHOLESALE_AES_KEY))
        return self.build_moa_wholesale_rows(chart_data, item)

    def get_moa_wholesale_items(self) -> list[dict[str, Any]]:
        if self._moa_wholesale_items_cache is not None:
            return self._moa_wholesale_items_cache
        response = self._request("POST", MOA_WHOLESALE_TREE_URL)
        payload = response.json()
        items: list[dict[str, Any]] = []
        self._collect_moa_wholesale_items((payload or {}).get("data"), items, [])
        if not items:
            raise RuntimeError("重点农产品市场信息平台品种树为空")
        self._moa_wholesale_items_cache = items
        return items

    def get_moa_wholesale_markets(self) -> list[dict[str, Any]]:
        if self._moa_wholesale_market_cache is not None:
            return self._moa_wholesale_market_cache
        response = self._request("POST", MOA_WHOLESALE_MARKET_URL)
        payload = response.json()
        data = (payload or {}).get("data") or []
        self._moa_wholesale_market_cache = data if isinstance(data, list) else []
        return self._moa_wholesale_market_cache

    def close(self) -> None:
        session = getattr(self._session_state, "session", None)
        if session is not None:
            session.close()
            self._session_state.session = None

    def _collect_moa_wholesale_items(
        self,
        payload: Any,
        items: list[dict[str, Any]],
        category_path: list[str],
    ) -> None:
        if isinstance(payload, list):
            for item in payload:
                self._collect_moa_wholesale_items(item, items, category_path)
            return
        if not isinstance(payload, dict):
            return

        label = str(payload.get("label") or "").strip()
        child_nodes = payload.get("children") or []
        next_path = list(category_path)
        if label and child_nodes:
            next_path.append(label)

        if isinstance(child_nodes, list) and child_nodes:
            for child in child_nodes:
                self._collect_moa_wholesale_items(child, items, next_path)
            return

        variety_id = str(payload.get("id") or "").strip()
        if not variety_id or not label:
            return
        category = next((entry for entry in reversed(category_path) if entry), "未分类")
        items.append(
            {
                "variety_id": variety_id,
                "source_name": label,
                "canonical_name": self.normalize_public_product_name(label),
                "category": category,
            }
        )

    def build_moa_wholesale_rows(self, chart_data: dict[str, Any], item: dict[str, Any]) -> list[dict[str, Any]]:
        report_date = str(chart_data.get("date") or "")
        markets = list(chart_data.get("x") or [])
        prices = list(chart_data.get("y") or [])
        rows: list[dict[str, Any]] = []
        for market_name, price in zip(markets, prices):
            try:
                current_price = float(price)
            except (TypeError, ValueError):
                continue
            market_text = str(market_name or "").strip()
            if not market_text:
                continue
            geo_fields = self.infer_market_geo(market_name=market_text)
            rows.append(
                {
                    "site_name": f"重点农产品平台 | {market_text}",
                    "product_name": item["canonical_name"],
                    "current_price": current_price,
                    "original_price": None,
                    "promotion_text": f"重点农产品平台批发价 | {report_date}",
                    "currency": "CNY",
                    "matched_rule": "重点农产品市场信息平台",
                    "raw_extract": {
                        "report_date": report_date,
                        "market_name": market_text,
                        "variety_id": item.get("variety_id"),
                    },
                    "extra_fields": {
                        "group_name": item["category"],
                        "category": item["category"],
                        "spec_text": "公斤",
                        "compare_key": item["canonical_name"],
                        **geo_fields,
                    },
                }
            )
        return rows

    def decrypt_aes_chart_data(self, encrypted_payload: str, key_text: str) -> str:
        openssl = shutil.which("openssl")
        if openssl:
            return self._decrypt_aes_chart_data_with_openssl(openssl, encrypted_payload, key_text)

        shell = shutil.which("powershell") or shutil.which("pwsh")
        if shell:
            return self._decrypt_aes_chart_data_with_powershell(shell, encrypted_payload, key_text)

        raise RuntimeError("当前环境缺少可用的 AES 解密后端（openssl / PowerShell），无法解密图表数据")

    @staticmethod
    def _split_encrypted_payload(encrypted_payload: str) -> tuple[str, str]:
        cipher = str(encrypted_payload or "")
        if len(cipher) <= 16:
            raise RuntimeError("图表数据密文格式无效")
        return cipher[:16], cipher[16:]

    def _decrypt_aes_chart_data_with_openssl(
        self,
        openssl: str,
        encrypted_payload: str,
        key_text: str,
    ) -> str:
        iv_text, cipher_text = self._split_encrypted_payload(encrypted_payload)
        key_bytes = str(key_text).encode("utf-8")
        iv_bytes = iv_text.encode("utf-8")
        algorithm = f"-aes-{len(key_bytes) * 8}-cbc"
        completed = subprocess.run(
            [
                openssl,
                "enc",
                algorithm,
                "-d",
                "-base64",
                "-A",
                "-K",
                key_bytes.hex(),
                "-iv",
                iv_bytes.hex(),
            ],
            input=f"{cipher_text}\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "图表数据解密失败")
        plain_text = completed.stdout.strip()
        if not plain_text:
            raise RuntimeError("图表数据解密结果为空")
        return plain_text

    def _decrypt_aes_chart_data_with_powershell(
        self,
        shell: str,
        encrypted_payload: str,
        key_text: str,
    ) -> str:
        script = f"""
$ErrorActionPreference = 'Stop'
$cipher = $env:PFSC_CIPHER
$keyText = '{key_text}'
$ivText = $cipher.Substring(0,16)
$cipherText = $cipher.Substring(16)
$key = [System.Text.Encoding]::UTF8.GetBytes($keyText)
$iv = [System.Text.Encoding]::UTF8.GetBytes($ivText)
$bytes = [Convert]::FromBase64String($cipherText)
$aes = [System.Security.Cryptography.Aes]::Create()
$aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
$aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
$aes.Key = $key
$aes.IV = $iv
$decryptor = $aes.CreateDecryptor()
$ms = New-Object System.IO.MemoryStream(,$bytes)
$cs = New-Object System.Security.Cryptography.CryptoStream($ms,$decryptor,[System.Security.Cryptography.CryptoStreamMode]::Read)
$sr = New-Object System.IO.StreamReader($cs,[System.Text.Encoding]::UTF8)
$plain = $sr.ReadToEnd()
$sr.Close(); $cs.Close(); $ms.Close(); $aes.Dispose()
Write-Output $plain
"""
        env = dict(os.environ)
        env["PFSC_CIPHER"] = encrypted_payload
        completed = subprocess.run(
            [shell, "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "图表数据解密失败")
        plain_text = completed.stdout.strip()
        if not plain_text:
            raise RuntimeError("图表数据解密结果为空")
        return plain_text

    def decrypt_pfsc_chart_data(self, encrypted_payload: str) -> str:
        return self.decrypt_aes_chart_data(encrypted_payload, MOA_WHOLESALE_AES_KEY)
