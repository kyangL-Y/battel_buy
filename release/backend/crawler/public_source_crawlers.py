from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any, Callable
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import ReadTimeout

from crawler.http_utils import without_proxy_env
from crawler.liancai_h5 import LiancaiH5Client
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
HNNHGSC_DEFAULT_UNIT = "公斤"
PUBLIC_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
HENAN_FGW_CATEGORY_URL = "https://page.henan.gov.cn/api/fgw-product-category"
HENAN_FGW_PRICE_URL = "https://page.henan.gov.cn/api/fgw-product-price"
ZZNY_CLZ_DEFAULT_MAX_PAGES = 24
CNNHB_DEFAULT_MAX_PAGES = 500
LIANCAI_DEFAULT_MAX_PAGES = 20


class LiancaiAppGatewayClient:
    def __init__(self, *, base_url: str = "https://lcwgetway.liancaiwang.cn", timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "authorization": "APPCODE 068ff082d41547cc82cc58881e737440",
                "request-from": "Android",
                "versioncode": "2.2.5",
                "app-channel": "huawei",
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "okhttp/4.9.1",
            }
        )

    def classify(self, pid: str = "0", is_chaid: str = "1") -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/classify",
            data={"pid": pid, "is_chaid": is_chaid},
            timeout=self.timeout,
        )
        return response.json()

    def posts_keywords(self, terms_id: str) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/posts_keywords",
            data={"terms_id": terms_id},
            timeout=self.timeout,
        )
        return response.json()

    def goodslist(
        self,
        *,
        term_id: str,
        page: int = 1,
        post_keywords: str = "",
        brand_id: str = "",
        is_act: str = "0",
    ) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/goodslist",
            data={
                "is_act": is_act,
                "post_keywords": post_keywords,
                "term_id": term_id,
                "page": page,
                "brand_id": brand_id,
            },
            timeout=self.timeout,
        )
        return response.json()
NON_PRODUCT_PUBLIC_SUBJECT_PATTERN = re.compile(
    r"存栏|出栏|产量|销量|销售量|成交量|进口量|出口量|库存|指数|指标"
    r"|均价|平均价|监测情况|价格监测|市场价格|价格表现|走势分析"
    r"|基本概况|概况|热点|话题|原因|影响|情况|调查|波动|下降|上涨|持平|回落|反弹"
    r"|上市量|货量|产区|包装成本|消费需求|节日|季节"
)
NON_PRODUCT_PUBLIC_TARGET_PATTERN = re.compile(
    r"存栏|出栏|产量|销量|销售量|成交量|进口量|出口量|库存|指数|指标"
    r"|变化率|增长率|下降率|增幅|降幅|涨跌幅|增速|比价"
)
NON_PRODUCT_PUBLIC_UNIT_PATTERN = re.compile(r"%|％|百分比|百分点|指数|点|万头|头")
NON_FOOD_PUBLIC_SUBJECT_PATTERN = re.compile(
    r"动力煤|煤|线材|螺纹钢|钢材|热轧|中厚板|铜|铝|氧化铝|甲醇|纯碱|烧碱|合成氨"
    r"|水泥|玻璃|原油|石油|汽油|柴油|化工|工业|电解铜|铝锭|豆粕"
    r"|农资|农药|肥料|化肥|叶面肥|除草剂|杀菌剂|杀虫剂|助剂|兽药|饲料"
)
NON_FOOD_PUBLIC_UNIT_PATTERN = re.compile(r"美元/桶|元/吨|元/平方米")
NON_PRODUCT_PUBLIC_EXACT_SUBJECTS = {
    "水果",
    "蔬菜",
    "果品",
    "市场价格监测情况",
    "万邦市场价格监测情况",
    "市场基本概况",
    "本月市场热点话题",
    "本周市场热点话题",
    "热点话题",
    "本月热点话题",
    "本周热点话题",
    "部分品种相关情况",
    "部分价格出现波动的原因：",
    "部分价格出现波动的原因",
    "近期整体价格情况",
    "整体价格情况",
}
PUBLIC_PRICE_UNIT_PATTERN = re.compile(
    r"元\s*/|元\s*每|元\s*／|元\s*/\s*(?:500克|斤|公斤|千克|吨|袋|只|枚|个|箱|件|把|束|升|毫升)"
)

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
        self._henan_fgw_category_cache: list[dict[str, Any]] | None = None

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

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        retry_count: int = 1,
        request_delay_seconds: float = 0.0,
        **kwargs,
    ) -> requests.Response:
        last_error: Exception | None = None
        attempts = max(1, int(retry_count) + 1)
        for attempt in range(1, attempts + 1):
            if request_delay_seconds > 0 and attempt > 1:
                time.sleep(request_delay_seconds * attempt)
            try:
                return self._request(method, url, **kwargs)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= attempts:
                    raise
        assert last_error is not None
        raise last_error

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
        max_rows = self._to_positive_int(site_rule.get("chinaprice_max_rows") if isinstance(site_rule, dict) else None, 0)
        max_pages_per_query = self._to_positive_int(
            site_rule.get("chinaprice_max_pages_per_query") if isinstance(site_rule, dict) else None,
            0,
        )
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
            effective_total_pages = min(total_pages, max_pages_per_query) if max_pages_per_query else total_pages
            effective_total_count = min(total_count, effective_total_pages * CHINAPRICE_PAGE_SIZE)
            for start_row in range(0, effective_total_count, CHINAPRICE_PAGE_SIZE):
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
                    progress = ((query_index - 1) + (page_index / effective_total_pages)) / total_queries
                    detail = f"Chinaprice 查询 {query_index}/{total_queries}，第 {page_index}/{effective_total_pages} 页"
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
                    if max_rows and len(results) >= max_rows:
                        self._report_progress(0.45, f"Chinaprice 快抓达到上限，共 {len(results)} 条")
                        return results
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
        query_mode = str(site_rule.get("chinaprice_query_mode") if isinstance(site_rule, dict) else "full").strip().lower()
        current_state_only = query_mode in {"current", "current_state", "current_page", "fast_snapshot"}
        current_menu_only = current_state_only or query_mode in {"current_menu", "menu_snapshot", "bounded_menu"}
        if current_menu_only:
            if initial_menu:
                menu_source = [initial_menu]
            else:
                fallback_menus = [
                    str(menu).strip()
                    for menu in (configured_menus or self.discover_chinaprice_menu_codes())
                    if str(menu).strip()
                ]
                menu_source = fallback_menus[:1]
        else:
            menu_source = configured_menus or self.discover_chinaprice_menu_codes()
        menu_codes = [str(menu).strip() for menu in menu_source if str(menu).strip()]
        if initial_menu and initial_menu not in menu_codes:
            menu_codes.append(initial_menu)
        max_queries = self._to_positive_int(site_rule.get("chinaprice_max_queries") if isinstance(site_rule, dict) else None, 0)

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
            if current_state_only:
                subtask_options = [
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
                if current_state_only:
                    tree_options = [
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
                        if max_queries and len(queries) >= max_queries:
                            self.logger.warning("Chinaprice 查询数量达到上限: %s", max_queries)
                            return queries
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
            if not self._is_public_product_candidate(
                item["canonical_name"],
                unit_text=unit_label,
                category_name=item["category"],
            ):
                continue
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
                    "raw_extract": {},
                    "extra_fields": {
                        "group_name": item["category"],
                        "category": item["category"],
                        "spec_text": unit_label,
                        "compare_key": item["canonical_name"],
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
            if not self._is_public_product_candidate(
                product_name,
                unit_text=spec_text,
                category_name=category,
            ):
                continue
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
                    "raw_extract": {},
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
        if not self._is_public_product_candidate(
            item["canonical_name"],
            unit_text="公斤",
            category_name=item["category"],
        ):
            return rows
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
                    "raw_extract": {},
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

    def fetch_hnnhgsc(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            str(product.get("url") or ""),
            headers=PUBLIC_REQUEST_HEADERS,
            verify=bool((site_rule or {}).get("verify_ssl", False)),
        )
        html = response.text
        self._report_progress(0.2, "内黄果蔬城页面已返回，开始解析列表")
        rows = self.parse_hnnhgsc_rows(html)
        self._report_progress(0.45, f"内黄果蔬城已解析 {len(rows)} 条")
        return rows

    def parse_hnnhgsc_rows(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html or "", "html.parser")
        rows: list[dict[str, Any]] = []
        for item in soup.select("#p_productslist li.tab-body"):
            field_map: dict[str, str] = {}
            for field in item.select("span.atname"):
                label = str(field.get_text(" ", strip=True) or "").strip()
                value_node = field.find_next_sibling("span", class_="atvalue")
                value = str(value_node.get_text(" ", strip=True) or "").strip() if value_node else ""
                if label:
                    field_map[label] = value

            product_name = self.normalize_public_product_name(
                field_map.get("品名")
                or item.select_one("li.name")
                and item.select_one("li.name").get_text(" ", strip=True)
                or ""
            )
            if not product_name:
                continue

            highest = normalize_price(field_map.get("最高价"))
            lowest = normalize_price(field_map.get("最低价"))
            average = normalize_price(field_map.get("均价"))
            spec_value = normalize_price(field_map.get("规格"))
            current_price = average or highest or lowest
            inferred_from_spec = False
            if current_price is None and spec_value is not None:
                current_price = spec_value
                inferred_from_spec = True
            if current_price is None:
                continue

            raw_unit = str(field_map.get("单位") or "").strip()
            unit_text = raw_unit if raw_unit and raw_unit not in {"/", "-", "--"} else HNNHGSC_DEFAULT_UNIT
            promotion_parts = ["内黄果蔬城页面行情"]
            if inferred_from_spec:
                promotion_parts.append("规格字段推断价格")
            origin = str(field_map.get("产地") or "").strip()
            if origin and origin not in {"/", "-", "--"}:
                promotion_parts.append(origin)
            rows.append(
                {
                    "site_name": "河南内黄果蔬城",
                    "product_name": product_name,
                    "current_price": current_price,
                    "original_price": highest if highest and highest != current_price else None,
                    "promotion_text": " | ".join(promotion_parts),
                    "currency": "CNY",
                    "matched_rule": "内黄果蔬城页面列表",
                    "raw_extract": {},
                    "extra_fields": {
                        "group_name": "果蔬行情",
                        "category": "果蔬行情",
                        "spec_text": unit_text,
                        "compare_key": product_name,
                        "province": "河南省",
                        "city": "安阳市",
                        "market_name": "河南内黄果蔬城",
                        "region_label": "河南省",
                    },
                }
            )
        return rows

    def fetch_henan_fgw_price(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        category_items = self.get_henan_fgw_categories()
        response = self._request("POST", HENAN_FGW_PRICE_URL, headers=PUBLIC_REQUEST_HEADERS)
        payload = response.json()
        raw_items = (payload or {}).get("obj") or []
        self._report_progress(0.25, f"河南发改委价格监测已拉取 {len(raw_items)} 组价格序列")
        return self.build_henan_fgw_rows(raw_items, category_items)

    def get_henan_fgw_categories(self) -> list[dict[str, Any]]:
        if self._henan_fgw_category_cache is not None:
            return self._henan_fgw_category_cache
        response = self._request("POST", HENAN_FGW_CATEGORY_URL, headers=PUBLIC_REQUEST_HEADERS)
        payload = response.json()
        items = (payload or {}).get("obj") or []
        self._henan_fgw_category_cache = items if isinstance(items, list) else []
        return self._henan_fgw_category_cache

    def build_henan_fgw_rows(
        self,
        price_items: list[dict[str, Any]],
        category_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        category_map = {
            str(item.get("code") or "").strip(): item
            for item in category_items
            if isinstance(item, dict) and str(item.get("code") or "").strip()
        }
        parent_map = {
            str(item.get("code") or "").strip(): str(item.get("varietyName") or "").strip()
            for item in category_items
            if isinstance(item, dict) and str(item.get("code") or "").strip() and str(item.get("indexPid") or "").strip() == "-1"
        }
        rows: list[dict[str, Any]] = []
        for item in price_items:
            if not isinstance(item, dict):
                continue
            variety_code = str(item.get("varietyCode") or "").strip()
            price_list = item.get("priceList") or []
            if not variety_code or not isinstance(price_list, list) or not price_list:
                continue

            category = category_map.get(variety_code) or {}
            latest_point = next((point for point in price_list if normalize_price(point.get("price")) is not None), None)
            if latest_point is None:
                continue
            current_price = normalize_price(latest_point.get("price"))
            if current_price is None:
                continue

            variety_name = self.normalize_public_product_name(
                str(category.get("varietyName") or item.get("varietyName") or "").strip()
            )
            if not variety_name:
                continue
            unit_text = str(category.get("unitName") or "").strip() or "元/500克"
            target_name = str(category.get("targetName") or "").strip()
            data_sources = str(category.get("dataSources") or "").strip()
            parent_name = parent_map.get(str(category.get("indexPid") or "").strip())
            if not self._is_public_product_candidate(
                variety_name,
                target_name=target_name,
                unit_text=unit_text,
                category_name=parent_name or "",
            ):
                continue
            report_date = str(latest_point.get("priceDate") or "").strip()
            promotion_parts = ["河南发改委全省监测"]
            if target_name:
                promotion_parts.append(target_name)
            if data_sources:
                promotion_parts.append(data_sources)
            rows.append(
                {
                    "site_name": "河南省发改委价格监测 | 全省均价",
                    "product_name": variety_name,
                    "current_price": current_price,
                    "original_price": None,
                    "promotion_text": " | ".join(promotion_parts + ([report_date] if report_date else [])),
                    "currency": "CNY",
                    "matched_rule": "河南发改委价格监测接口",
                    "raw_extract": {},
                    "extra_fields": {
                        "group_name": parent_name or "河南价格监测",
                        "category": parent_name or "河南价格监测",
                        "spec_text": unit_text,
                        "compare_key": variety_name,
                        "province": "河南省",
                        "city": None,
                        "market_name": "全省均价",
                        "region_label": "河南省",
                    },
                }
            )
        return rows

    def fetch_zzny_clz_articles(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        site_rule = site_rule or {}
        base_url = str(product.get("url") or "").strip()
        configured_max_pages = self._to_positive_int(site_rule.get("max_pages"), ZZNY_CLZ_DEFAULT_MAX_PAGES)
        retry_count = self._to_positive_int(site_rule.get("retry_count"), 1)
        request_delay_seconds = float(site_rule.get("request_delay_seconds") or 0)
        first_response = self._request_with_retry(
            "GET",
            base_url,
            headers=PUBLIC_REQUEST_HEADERS,
            retry_count=retry_count,
            request_delay_seconds=request_delay_seconds,
        )
        first_html = first_response.text
        discovered_max_pages = self._discover_zzny_max_pages(first_html, fallback=1)
        max_pages = max(1, min(configured_max_pages, discovered_max_pages))
        max_consecutive_page_errors = self._to_positive_int(site_rule.get("max_consecutive_page_errors"), 3)
        page_urls = [base_url]
        page_urls.extend(urljoin(base_url, f"index_{page_no}.jhtml") for page_no in range(2, max_pages + 1))

        article_urls: list[str] = []
        seen_urls: set[str] = set()
        consecutive_page_errors = 0
        for page_index, page_url in enumerate(page_urls, start=1):
            try:
                if page_index > 1 and request_delay_seconds > 0:
                    time.sleep(request_delay_seconds)
                html = (
                    first_html
                    if page_index == 1
                    else self._request_with_retry(
                        "GET",
                        page_url,
                        headers=PUBLIC_REQUEST_HEADERS,
                        retry_count=retry_count,
                        request_delay_seconds=request_delay_seconds,
                    ).text
                )
            except Exception as exc:  # noqa: BLE001
                consecutive_page_errors += 1
                self.logger.warning(
                    "郑州菜篮子监测分页抓取失败: page=%s/%s url=%s error=%s",
                    page_index,
                    max_pages,
                    page_url,
                    exc,
                )
                if consecutive_page_errors >= max_consecutive_page_errors:
                    break
                continue
            consecutive_page_errors = 0
            soup = BeautifulSoup(html, "html.parser")
            for anchor in soup.select("a[href*='/clzxx/'][href$='.jhtml']"):
                href = str(anchor.get("href") or "").strip()
                if not href or not re.search(r"/clzxx/\d+\.jhtml$", href):
                    continue
                article_url = urljoin(page_url, href)
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)
                article_urls.append(article_url)
            self._report_progress(
                0.08 + 0.12 * (page_index / max_pages),
                f"郑州菜篮子监测已发现 {len(article_urls)} 篇文章",
            )

        rows: list[dict[str, Any]] = []
        total_articles = len(article_urls)
        for article_index, article_url in enumerate(article_urls, start=1):
            try:
                if article_index > 1 and request_delay_seconds > 0:
                    time.sleep(request_delay_seconds)
                response = self._request_with_retry(
                    "GET",
                    article_url,
                    headers=PUBLIC_REQUEST_HEADERS,
                    retry_count=retry_count,
                    request_delay_seconds=request_delay_seconds,
                )
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(
                    "郑州菜篮子监测文章抓取失败: article=%s/%s url=%s error=%s",
                    article_index,
                    total_articles,
                    article_url,
                    exc,
                )
                continue
            rows.extend(self.parse_zzny_clz_article(response.text, article_url))
            if total_articles:
                self._report_progress(
                    0.2 + 0.25 * (article_index / total_articles),
                    f"郑州菜篮子监测文章 {article_index}/{total_articles}",
                )
        return rows

    @staticmethod
    def _discover_zzny_max_pages(html: str, fallback: int = 1) -> int:
        page_numbers = [
            int(match)
            for match in re.findall(r"(?:^|['\"/])index_(\d+)\.jhtml", html or "")
            if str(match).isdigit()
        ]
        return max(page_numbers, default=max(1, int(fallback)))

    def parse_zzny_clz_article(self, html: str, article_url: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html or "", "html.parser")
        title = (
            self._meta_content(soup, "ArticleTitle")
            or self._text_or_none(soup.select_one(".big-title"))
            or ""
        )
        pub_date = self._meta_content(soup, "PubDate") or ""
        source_name = self._meta_content(soup, "ContentSource") or "郑州市农业技术推广中心"
        content = soup.select_one(".news_content_content")
        if content is None:
            return []
        paragraphs = [
            self._collapse_spaces(node.get_text(" ", strip=True))
            for node in content.select("p")
            if self._collapse_spaces(node.get_text(" ", strip=True))
        ]
        if not paragraphs:
            return []

        subjects = self._extract_zzny_subjects_from_title(title)
        if not subjects:
            subjects = self._extract_zzny_subjects_from_headings(paragraphs)
        sections: dict[str, list[str]] = {}
        current_subject: str | None = None
        for paragraph in paragraphs:
            if paragraph.startswith("免责声明"):
                break
            matched_subject = self._match_zzny_subject(paragraph, subjects)
            if matched_subject:
                current_subject = matched_subject
                sections.setdefault(current_subject, [])
                continue
            if current_subject:
                sections.setdefault(current_subject, []).append(paragraph)

        rows: list[dict[str, Any]] = []
        for subject, section_paragraphs in sections.items():
            row = self._build_zzny_article_row(
                product_name=subject,
                section_text=" ".join(section_paragraphs),
                article_title=title,
                pub_date=pub_date,
                source_name=source_name,
                article_url=article_url,
            )
            if row is not None:
                rows.append(row)

        if rows:
            return rows

        return rows

    def _build_zzny_article_row(
        self,
        *,
        product_name: str,
        section_text: str,
        article_title: str,
        pub_date: str,
        source_name: str,
        article_url: str,
    ) -> dict[str, Any] | None:
        weekly_matches = list(
            re.finditer(
                r"第([0-9一二三四五六七八九十]+)周[^。；]*?(?:均价|价格|塘口价格|出场价格|收购价格)[^。；]*?(?:为|约|在|达|降到|上涨到|上升到|仅有)?([0-9]+(?:\.[0-9]+)?)元/([^\s；，。、]+)(?:左右)?",
                section_text,
            )
        )
        latest_price = None
        latest_label = None
        latest_unit = None
        if weekly_matches:
            latest_match = weekly_matches[-1]
            latest_label = f"第{latest_match.group(1)}周"
            latest_price = normalize_price(latest_match.group(2))
            latest_unit = latest_match.group(3)
        else:
            generic_matches = list(
                re.finditer(
                    r"(?:均价|价格|塘口价格|出场价格|收购价格|平均价格)[^。；]*?(?:为|约|在|达|降到|上涨到|上升到|仅有)?([0-9]+(?:\.[0-9]+)?)元/([^\s；，。、]+)(?:左右)?",
                    section_text,
                )
            )
            if generic_matches:
                latest_match = generic_matches[-1]
                latest_label = "文内均价"
                latest_price = normalize_price(latest_match.group(1))
                latest_unit = latest_match.group(2)

        if latest_price is None or not latest_unit:
            return None

        normalized_name = self.normalize_public_product_name(product_name)
        promotion_parts = ["郑州菜篮子监测", article_title]
        if latest_label:
            promotion_parts.append(latest_label)
        if pub_date:
            promotion_parts.append(pub_date)
        if source_name:
            promotion_parts.append(source_name)
        return {
            "site_name": "郑州市农业农村局菜篮子监测 | 郑州监测",
            "product_name": normalized_name,
            "current_price": latest_price,
            "original_price": None,
            "promotion_text": " | ".join(part for part in promotion_parts if part),
            "currency": "CNY",
            "matched_rule": "郑州菜篮子监测文章",
            "raw_extract": {},
            "extra_fields": {
                "group_name": "郑州菜篮子监测",
                "category": "郑州菜篮子监测",
                "spec_text": f"元/{latest_unit}",
                "compare_key": normalized_name,
                "province": "河南省",
                "city": "郑州市",
                "market_name": "郑州监测",
                "region_label": "郑州市",
            },
        }

    @staticmethod
    def _collapse_spaces(text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()

    @staticmethod
    def _text_or_none(node: Any) -> str | None:
        if node is None:
            return None
        text = str(node.get_text(" ", strip=True) or "").strip()
        return text or None

    @staticmethod
    def _meta_content(soup: BeautifulSoup, name: str) -> str | None:
        node = soup.find("meta", attrs={"name": name})
        if node and node.get("content"):
            return str(node.get("content")).strip()
        return None

    def _extract_zzny_subjects_from_title(self, title: str) -> list[str]:
        matched = re.search(r"郑州市\s*([^。]+?)价格\s*走势分析", title)
        if matched:
            parts = [
                self.normalize_public_product_name(part)
                for part in re.split(r"[、，,]", matched.group(1))
                if self.normalize_public_product_name(part)
                and not self._is_non_product_public_subject(self.normalize_public_product_name(part))
            ]
            return parts
        return []

    @staticmethod
    def _normalize_zzny_heading_text(text: str) -> str:
        normalized = str(text or "").strip()
        normalized = re.sub(r"^[一二三四五六七八九十]+[、.．]\s*", "", normalized)
        normalized = re.sub(r"^\d+[、.．]\s*", "", normalized)
        normalized = re.sub(r"[（(].*?[）)]", "", normalized).strip()
        return normalized

    def _extract_zzny_subjects_from_headings(self, paragraphs: list[str]) -> list[str]:
        subjects: list[str] = []
        ignored_headings = {"水果市场价格表现", "郑州市地产水果"}
        for paragraph in paragraphs:
            if not re.match(r"^(?:[一二三四五六七八九十]+[、.．]|\d+[、.．])", paragraph):
                continue
            normalized = self.normalize_public_product_name(self._normalize_zzny_heading_text(paragraph))
            if not normalized or normalized in ignored_headings or self._is_non_product_public_subject(normalized):
                continue
            if normalized and normalized not in subjects:
                subjects.append(normalized)
        return subjects

    def _match_zzny_subject(self, paragraph: str, subjects: list[str]) -> str | None:
        normalized = self.normalize_public_product_name(self._normalize_zzny_heading_text(paragraph))
        for subject in subjects:
            normalized_subject = self.normalize_public_product_name(subject)
            if normalized == normalized_subject:
                return subject
            if normalized and normalized_subject and normalized_subject in normalized and len(normalized) <= 24:
                return subject
        return None

    @staticmethod
    def _is_non_product_public_subject(subject: str) -> bool:
        return not PublicSourceCrawler._is_public_product_candidate(subject)

    @staticmethod
    def _is_public_product_candidate(
        subject: str,
        *,
        target_name: str = "",
        unit_text: str = "",
        category_name: str = "",
    ) -> bool:
        normalized_subject = PublicSourceCrawler.normalize_public_product_name(subject)
        normalized_subject = str(normalized_subject or "").strip().strip("：:")
        if not normalized_subject:
            return False
        if normalized_subject in NON_PRODUCT_PUBLIC_EXACT_SUBJECTS:
            return False
        if NON_PRODUCT_PUBLIC_SUBJECT_PATTERN.search(normalized_subject):
            return False
        if NON_FOOD_PUBLIC_SUBJECT_PATTERN.search(normalized_subject):
            return False

        normalized_category = str(category_name or "").strip()
        if normalized_category and NON_PRODUCT_PUBLIC_TARGET_PATTERN.search(normalized_category):
            return False
        if normalized_category and NON_FOOD_PUBLIC_SUBJECT_PATTERN.search(normalized_category):
            return False

        normalized_target = str(target_name or "").strip()
        if normalized_target and NON_PRODUCT_PUBLIC_TARGET_PATTERN.search(normalized_target):
            return False

        normalized_unit = str(unit_text or "").strip()
        if normalized_unit:
            if NON_PRODUCT_PUBLIC_UNIT_PATTERN.search(normalized_unit):
                return False
            if NON_FOOD_PUBLIC_UNIT_PATTERN.search(normalized_unit):
                return False
        return True

    def fetch_cnhnb_market(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        site_rule = site_rule or {}
        base_url = str(product.get("url") or "").strip()
        configured_max_pages = self._to_positive_int(site_rule.get("max_pages"), CNNHB_DEFAULT_MAX_PAGES)
        retry_count = self._to_positive_int(site_rule.get("retry_count"), 1)
        request_delay_seconds = float(site_rule.get("request_delay_seconds") or 0)
        base_headers = dict(PUBLIC_REQUEST_HEADERS)
        base_headers["Referer"] = "https://www.cnhnb.com/"
        first_response = self._request_with_retry(
            "GET",
            self._build_cnhnb_page_url(base_url, 1),
            headers=base_headers,
            retry_count=retry_count,
            request_delay_seconds=request_delay_seconds,
        )
        first_html = first_response.text
        discovered_max_pages = self._discover_cnhnb_max_pages(first_html, fallback=1)
        max_pages = max(1, min(configured_max_pages, discovered_max_pages))
        max_consecutive_page_errors = self._to_positive_int(site_rule.get("max_consecutive_page_errors"), 5)
        page_urls = [self._build_cnhnb_page_url(base_url, page_no) for page_no in range(1, max_pages + 1)]

        rows: list[dict[str, Any]] = []
        consecutive_page_errors = 0
        for index, page_url in enumerate(page_urls, start=1):
            try:
                if index > 1 and request_delay_seconds > 0:
                    time.sleep(request_delay_seconds)
                page_headers = dict(PUBLIC_REQUEST_HEADERS)
                page_headers["Referer"] = (
                    "https://www.cnhnb.com/"
                    if index <= 1
                    else self._build_cnhnb_page_url(base_url, max(1, index - 1))
                )
                html = (
                    first_html
                    if index == 1
                    else self._request_with_retry(
                        "GET",
                        page_url,
                        headers=page_headers,
                        retry_count=retry_count,
                        request_delay_seconds=request_delay_seconds,
                    ).text
                )
            except Exception as exc:  # noqa: BLE001
                consecutive_page_errors += 1
                self.logger.warning(
                    "惠农网行情分页抓取失败: page=%s/%s url=%s error=%s",
                    index,
                    max_pages,
                    page_url,
                    exc,
                )
                if consecutive_page_errors >= max_consecutive_page_errors:
                    break
                continue
            consecutive_page_errors = 0
            state = self.extract_cnhnb_market_state(html)
            rows.extend(self.build_cnhnb_rows(state))
            self._report_progress(
                0.12 + 0.33 * (index / max_pages),
                f"惠农网行情第 {index}/{max_pages} 页",
            )
        return rows

    @staticmethod
    def _build_cnhnb_page_url(base_url: str, page_no: int) -> str:
        return re.sub(r"-\d+/?$", f"-{page_no}/", base_url)

    @staticmethod
    def _discover_cnhnb_max_pages(html: str, fallback: int = 1) -> int:
        page_numbers = [
            int(match)
            for match in re.findall(r"/hangqing/cdlist-0-0-16-0-0-(\d+)/", html or "")
            if str(match).isdigit()
        ]
        return max(page_numbers, default=max(1, int(fallback)))

    def extract_cnhnb_market_state(self, html: str) -> dict[str, Any]:
        node = shutil.which("node")
        if not node:
            raise RuntimeError("当前环境缺少 node，无法解析惠农网页面内嵌 SSR 数据")

        script = """
const fs = require('fs');
const html = fs.readFileSync(0, 'utf8');
const marker = 'window.__NUXT__=';
const start = html.indexOf(marker);
if (start === -1) {
  throw new Error('未找到 __NUXT__ 数据');
}
const end = html.indexOf('</script>', start);
const expr = html.slice(start + marker.length, end).trim().replace(/;\\s*$/, '');
const data = eval('(' + expr + ')');
const root = (data.data && data.data[0]) || {};
const result = root.result || {};
process.stdout.write(JSON.stringify({
  selected: result.selected || root.selected || {},
  marketRelevantSulllys: result.marketRelevantSulllys || [],
  market: result.market || root.market || {}
}));
"""
        completed = subprocess.run(
            [node, "-e", script],
            input=html,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "惠农网页面数据解析失败")
        return json.loads(completed.stdout or "{}")

    def build_cnhnb_rows(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        selected = state.get("selected") or {}
        province_name = str(((selected.get("area") or {}).get("province") or {}).get("provinceName") or "河南省").strip()
        market_items = state.get("marketRelevantSulllys") or []
        rows: list[dict[str, Any]] = []
        for item in market_items:
            if not isinstance(item, dict):
                continue
            current_price = normalize_price(item.get("price"))
            if current_price is None:
                continue
            product_name = self.normalize_public_product_name(
                str(item.get("customTitle") or item.get("cateName") or item.get("breedName") or "").strip()
            )
            if not product_name:
                continue
            unit_text = str(item.get("unit") or item.get("originUnit") or "").strip() or "斤"
            category = str(item.get("cateName") or "惠农网参考行情").strip() or "惠农网参考行情"
            title_text = str(item.get("title") or "").strip()
            if not self._is_public_product_candidate(
                product_name,
                target_name=title_text,
                unit_text=unit_text,
                category_name=category,
            ):
                continue
            shop_name = str(item.get("shopName") or "").strip()
            address = str(item.get("address") or "").strip()
            rows.append(
                {
                    "site_name": f"惠农网行情 | {shop_name or '河南供应'}",
                    "product_name": product_name,
                    "current_price": current_price,
                    "original_price": normalize_price(item.get("originPrice")),
                    "promotion_text": " | ".join(
                        part
                        for part in [
                            "惠农网河南参考行情",
                            str(item.get("timeStr") or "").strip(),
                            str(item.get("title") or "").strip(),
                        ]
                        if part
                    ),
                    "currency": "CNY",
                    "matched_rule": "惠农网 SSR 供应行情",
                    "raw_extract": {},
                    "extra_fields": {
                        "group_name": "惠农网参考行情",
                        "category": category,
                        "spec_text": unit_text,
                        "compare_key": product_name,
                        "province": province_name,
                        "city": None,
                        "market_name": address or shop_name or "河南供应",
                        "region_label": province_name,
                    },
                }
            )
        if rows:
            return rows

        market_list = ((state.get("market") or {}).get("list")) or []
        for item in market_list:
            if not isinstance(item, dict):
                continue
            current_price = (
                normalize_price(item.get("weighting_avgPrice"))
                or normalize_price(item.get("avgPrice"))
                or normalize_price(item.get("minPrice"))
            )
            if current_price is None:
                continue
            product_name = self.normalize_public_product_name(
                str(item.get("cateName") or item.get("breedName") or "").strip()
            )
            if not product_name:
                continue
            unit_text = str(item.get("unit") or "斤").strip() or "斤"
            category = str(item.get("cateName") or "惠农网参考行情").strip() or "惠农网参考行情"
            address = str(item.get("addressDetail") or "").strip()
            rows.append(
                {
                    "site_name": f"惠农网行情 | {address or '河南市场'}",
                    "product_name": product_name,
                    "current_price": current_price,
                    "original_price": normalize_price(item.get("avgPrice")),
                    "promotion_text": " | ".join(
                        part
                        for part in [
                            "惠农网河南参考行情",
                            self._format_cnhnb_time_text(item.get("collectDate") or item.get("createTime")),
                            product_name,
                        ]
                        if part
                    ),
                    "currency": "CNY",
                    "matched_rule": "惠农网 SSR 市场行情",
                    "raw_extract": {},
                    "extra_fields": {
                        "group_name": "惠农网参考行情",
                        "category": category,
                        "spec_text": unit_text,
                        "compare_key": product_name,
                        "province": province_name,
                        "city": None,
                        "market_name": address or "河南市场",
                        "region_label": province_name,
                    },
                }
            )
        return rows

    @staticmethod
    def _format_cnhnb_time_text(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if text.isdigit():
            number = int(text)
            if number > 10_000_000_000:
                number = number / 1000
            try:
                return datetime.fromtimestamp(number).strftime("%Y-%m-%d %H:%M:%S")
            except (OverflowError, OSError, ValueError):
                return text
        return text

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

    def fetch_liancai_h5(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        site_rule = site_rule or {}
        phone_env = str(site_rule.get("login_phone_env") or "LIANCAI_PHONE").strip() or "LIANCAI_PHONE"
        password_env = str(site_rule.get("login_password_env") or "LIANCAI_PASSWORD").strip() or "LIANCAI_PASSWORD"
        phone = str(os.environ.get(phone_env) or "").strip()
        password = str(os.environ.get(password_env) or "").strip()
        if not phone or not password:
            raise RuntimeError(
                f"缺少莲菜网H5登录凭证，请设置环境变量 {phone_env} / {password_env}"
            )

        base_url = str(site_rule.get("base_url") or product.get("url") or "http://m.liancaiwang.cn").strip()
        client = LiancaiH5Client(
            phone=phone,
            password=password,
            base_url=base_url,
            timeout=self._to_positive_int(site_rule.get("timeout_seconds"), self.timeout),
        )
        login_result = client.login()
        if int(login_result.get("code") or 0) != 200:
            raise RuntimeError(f"莲菜网H5登录失败: {login_result}")

        top_categories, subcategories = client.fetch_category_tree()
        category_name = str(product.get("category") or "").strip()
        selected = self._match_liancai_category(category_name, top_categories)
        if selected is None:
            available = ", ".join(category.name for category in top_categories)
            raise RuntimeError(f"未找到莲菜网H5分类映射: {category_name or '(空)'} | 可选: {available}")

        max_pages = self._to_positive_int(site_rule.get("max_pages"), LIANCAI_DEFAULT_MAX_PAGES)
        rows: list[dict[str, Any]] = []
        last_first_product_id = None
        for page in range(1, max_pages + 1):
            page_rows = client.fetch_category_page(selected.fid, page=page)
            if not page_rows:
                break
            current_first_product_id = page_rows[0].get("product_id")
            if page > 1 and current_first_product_id and current_first_product_id == last_first_product_id:
                break
            last_first_product_id = current_first_product_id
            rows.extend(self.build_liancai_h5_rows(page_rows, selected, product, subcategories, page))
            self._report_progress(
                0.15 + 0.55 * (page / max_pages),
                f"莲菜网H5 {selected.name} 第 {page}/{max_pages} 页",
            )
            if len(page_rows) < 20:
                break
        self._report_progress(0.72, f"莲菜网H5 {selected.name} 共 {len(rows)} 条")
        return rows

    def fetch_liancai_app_gateway(self, product: dict[str, Any], site_rule: dict | None = None) -> list[dict[str, Any]]:
        site_rule = site_rule or {}
        base_url = str(site_rule.get("gateway_base_url") or "https://lcwgetway.liancaiwang.cn").strip()
        timeout = self._to_positive_int(site_rule.get("timeout_seconds"), self.timeout)
        client = LiancaiAppGatewayClient(base_url=base_url, timeout=timeout)

        root_payload = client.classify(pid="0", is_chaid="1")
        class_list = root_payload.get("data", {}).get("classList") or []
        category_name = str(product.get("category") or "").strip()
        selected_category = self._match_liancai_app_category(category_name, class_list)
        if selected_category is None:
            available = ", ".join(str(item.get("name") or "").strip() for item in class_list if str(item.get("name") or "").strip())
            raise RuntimeError(f"未找到莲菜网App分类映射: {category_name or '(空)'} | 可选: {available}")

        max_pages = self._to_positive_int(site_rule.get("max_pages"), LIANCAI_DEFAULT_MAX_PAGES)
        rows: list[dict[str, Any]] = []

        child_categories = [
            item
            for item in class_list
            if str(item.get("parent") or "").strip() == str(selected_category.get("term_id") or "").strip()
            and int(item.get("level") or 0) == 1
            and str(item.get("name") or "").strip()
        ]
        if not child_categories:
            child_categories = [selected_category]

        for child_category in child_categories:
            child_rows = self._collect_liancai_app_goods_rows(
                client,
                root_category=selected_category,
                selected_category=child_category,
                product=product,
                page_limit=max_pages,
            )
            rows.extend(child_rows)

        self._report_progress(0.72, f"莲菜网App {selected_category.get('name') or category_name} 共 {len(rows)} 条")
        return self._deduplicate_liancai_rows(rows)

    @staticmethod
    def _match_liancai_app_category(category_name: str, categories: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not category_name:
            return None
        normalized = category_name.strip().lower()
        for category in categories:
            name = str(category.get("name") or "").strip().lower()
            if name == normalized:
                return category
        return None

    def _collect_liancai_app_goods_rows(
        self,
        client: LiancaiAppGatewayClient,
        root_category: dict[str, Any],
        selected_category: dict[str, Any],
        product: dict[str, Any],
        *,
        page_limit: int,
    ) -> list[dict[str, Any]]:
        term_id = str(selected_category.get("term_id") or "").strip()
        rows: list[dict[str, Any]] = []
        last_first_id = None
        for page in range(1, page_limit + 1):
            payload = client.goodslist(
                term_id=term_id,
                page=page,
            )
            items = payload.get("data", {}).get("list") or []
            if not items:
                break
            first_id = items[0].get("id")
            if page > 1 and first_id and first_id == last_first_id:
                break
            last_first_id = first_id
            rows.extend(
                self._build_liancai_app_rows(
                    items,
                    root_category,
                    selected_category,
                    product,
                    page=page,
                )
            )
            if len(items) < 10:
                break
        return rows

    def _build_liancai_app_rows(
        self,
        items: list[dict[str, Any]],
        root_category: dict[str, Any],
        selected_category: dict[str, Any],
        product: dict[str, Any],
        *,
        page: int,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in items:
            title = str(item.get("post_title") or "").strip()
            product_name = self.normalize_public_product_name(title)
            if not product_name:
                continue
            current_price = normalize_price(item.get("sale_real_price") or item.get("sale_price") or item.get("goods_base_real_price"))
            if current_price is None:
                continue
            sale_brand = str(item.get("sale_brand") or "").strip() or None
            sale_term_id = str(item.get("term_id") or "").strip()
            rows.append(
                {
                    "site_name": f"莲菜网App | {root_category.get('name') or ''}",
                    "product_name": product_name,
                    "current_price": current_price,
                    "original_price": normalize_price(item.get("original_price") or item.get("sale_market_price")),
                    "promotion_text": " | ".join(
                        part
                        for part in [
                            "莲菜网App",
                            f"分类:{root_category.get('name') or ''}",
                            f"子类:{selected_category.get('name') or ''}",
                            f"页码:{page}",
                        ]
                        if part
                    ),
                    "currency": "CNY",
                    "matched_rule": "莲菜网App分类页",
                    "raw_extract": {},
                    "extra_fields": {
                        "group_name": "莲菜网",
                        "category": str(selected_category.get("name") or "").strip() or None,
                        "liancai_top_category": str(root_category.get("name") or "").strip() or None,
                        "liancai_subcategory": str(selected_category.get("name") or "").strip() or None,
                        "liancai_mapping_source": "liancai_app_gateway",
                        "spec_text": str(item.get("sale_guige") or "").strip() or None,
                        "compare_key": product_name,
                        "market_name": "郑州莲菜网",
                        "region_label": "郑州市",
                        "province": "河南省",
                        "city": "郑州市",
                        "product_series": sale_term_id or None,
                        "brand": sale_brand,
                        "liancai_brand_name": sale_brand,
                        "cover": str(item.get("thumb") or item.get("thumb_sm") or "").strip() or None,
                    },
                }
            )
        return rows

    @staticmethod
    def _deduplicate_liancai_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str, str]] = set()
        for row in rows:
            extra = row.get("extra_fields") or {}
            key = (
                str(row.get("site_name") or "").strip(),
                str(row.get("product_name") or "").strip(),
                str(extra.get("liancai_keyword") or "").strip(),
                str(extra.get("liancai_brand_id") or "").strip(),
                str(extra.get("spec_text") or "").strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped

    @staticmethod
    def _match_liancai_category(category_name: str, categories: list[Any]) -> Any | None:
        if not category_name:
            return None
        normalized = category_name.strip().lower()
        for category in categories:
            if str(category.name).strip().lower() == normalized:
                return category
        return None

    def build_liancai_h5_rows(
        self,
        items: list[dict[str, Any]],
        selected_category: Any,
        product: dict[str, Any],
        subcategories: list[Any],
        page: int,
    ) -> list[dict[str, Any]]:
        subcategory_lookup = {str(item.fid): item for item in subcategories if getattr(item, "parent_fid", None) == selected_category.fid}
        rows: list[dict[str, Any]] = []
        for item in items:
            product_name = self.normalize_public_product_name(str(item.get("title") or "").strip())
            if not product_name:
                continue
            current_price = normalize_price(item.get("price"))
            if current_price is None:
                continue
            termid = str(item.get("termid") or "").strip()
            subcategory = subcategory_lookup.get(termid)
            group_name = "莲菜网"
            category = str((subcategory.name if subcategory else selected_category.name) or "").strip() or selected_category.name
            liancai_subcategory = category if category != selected_category.name else "全部"
            subtitle = str(item.get("subtitle") or "").strip()
            size = str(item.get("size") or "").strip()
            unit = str(item.get("unit") or "").strip()
            inventory_text = str(item.get("inventory_text") or "").strip()
            product_id = str(item.get("product_id") or "").strip()
            raw_brand = item.get("raw", {}).get("brand") if isinstance(item.get("raw"), dict) else None
            if isinstance(raw_brand, dict):
                brand_name = str(raw_brand.get("name") or raw_brand.get("brand_name") or "").strip() or None
            else:
                brand_name = str(raw_brand or "").strip() or None
            promotion_parts = [
                "莲菜网H5",
                f"分类:{selected_category.name}",
                f"页码:{page}",
            ]
            if subcategory and subcategory.name != "全部":
                promotion_parts.append(f"细分类:{subcategory.name}")
            if inventory_text:
                promotion_parts.append(inventory_text)
            rows.append(
                {
                    "site_name": f"莲菜网H5 | {selected_category.name}",
                    "product_name": product_name,
                    "current_price": current_price,
                    "original_price": normalize_price(item.get("market_price")),
                    "promotion_text": " | ".join(promotion_parts),
                    "currency": "CNY",
                    "matched_rule": "莲菜网H5分类页",
                    "raw_extract": {},
                    "extra_fields": {
                        "group_name": group_name,
                        "category": category,
                        "liancai_top_category": selected_category.name,
                        "liancai_subcategory": liancai_subcategory,
                        "liancai_mapping_source": "liancai_h5",
                        "spec_text": size or unit,
                        "compare_key": product_name,
                        "market_name": "郑州莲菜网",
                        "region_label": "郑州市",
                        "province": "河南省",
                        "city": "郑州市",
                        "product_series": termid or None,
                        "brand": brand_name,
                        "cover": item.get("cover"),
                    },
                }
            )
        return rows

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
        if not self._is_public_product_candidate(
            item["canonical_name"],
            unit_text="公斤",
            category_name=item["category"],
        ):
            return rows
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
                    "raw_extract": {},
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
