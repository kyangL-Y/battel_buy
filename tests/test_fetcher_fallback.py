from __future__ import annotations

import requests

from crawler.base import FetchResult
from crawler.fetcher import PriceCrawlerService
from crawler.playwright_fetcher import PlaywrightFetcher
from crawler.requests_fetcher import RequestsFetcher
from parsers.site_parser import SiteParser


class DummyDatabase:
    def __init__(self):
        self.failed_records = []
        self.price_records = []

    def upsert_product(self, **kwargs):
        return 1

    def insert_price_record(self, **kwargs):
        self.price_records.append(kwargs)
        return 1

    def insert_failed_crawl_record(self, **kwargs):
        self.failed_records.append(kwargs)
        return 1


class FakePlaywrightFetcher(PlaywrightFetcher):
    def __init__(self, result: FetchResult):
        self.result = result

    def fetch(self, url: str) -> FetchResult:
        return self.result


class FakeResponse:
    def __init__(self, status_code: int, text: str = "<html><body>ok</body></html>", headers: dict | None = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {"content-type": "text/html"}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error", response=self)


class ParserStub:
    def __init__(self, site_rule: dict):
        self.site_rule = site_rule

    def find_rule(self, url: str) -> dict:
        return self.site_rule

    def match_rule(self, url: str) -> dict:
        return self.site_rule

    def parse(self, url: str, html: str) -> dict:
        return {
            "site_name": self.site_rule.get("site_name", "测试站点"),
            "product_name": "测试商品",
            "current_price": 9.9,
            "original_price": 12.9,
            "promotion_text": "限时优惠",
            "currency": "CNY",
            "availability": "in_stock",
        }


class ParserStubNoPrice(ParserStub):
    def parse(self, url: str, html: str) -> dict:
        return {
            "site_name": self.site_rule.get("site_name", "测试站点"),
            "product_name": "测试商品",
            "current_price": None,
            "original_price": None,
            "promotion_text": None,
            "currency": "CNY",
            "availability": "in_stock",
            "raw_extract": {},
        }



def build_service(site_rule: dict | None = None, fetcher: RequestsFetcher | None = None) -> PriceCrawlerService:
    rule = site_rule or {"site_name": "测试站点", "domains": ["example.com"]}
    service = PriceCrawlerService(
        DummyDatabase(),
        [rule],
        fetcher=fetcher or RequestsFetcher(),
        fallback_to_playwright=True,
    )
    service.parser = ParserStub(rule)
    return service



def test_fallback_to_playwright_when_requests_blocked(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(status_code=403, text="")

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    playwright_success = FetchResult(
        url="https://example.com/item",
        status_code=200,
        html="<html><body><h1>ok</h1></body></html>",
        metadata={"fetch_mode": "playwright"},
    )
    service = build_service({"site_name": "测试站点", "domains": ["example.com"], "blocked_status_codes": [403, 429]})
    service.playwright_fetcher = FakePlaywrightFetcher(playwright_success)

    result = service.crawl_product({"url": "https://example.com/item", "product_key": "sku-1", "group_name": "测试商品"})

    assert result["status"] == "success"
    assert result["fetch_mode"] == "playwright"
    assert result["fallback_used"] is True



def test_use_playwright_first_when_site_rule_prefers_it(monkeypatch):
    def should_not_call_requests(*args, **kwargs):
        raise AssertionError("设置了 preferred_fetch_mode=playwright 时不应调用 requests")

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", should_not_call_requests)

    playwright_success = FetchResult(
        url="https://example.com/item",
        status_code=200,
        html="<html><body><h1>ok</h1></body></html>",
        metadata={"fetch_mode": "playwright"},
    )
    service = build_service(
        {"site_name": "动态站点", "domains": ["example.com"], "preferred_fetch_mode": "playwright"},
    )
    service.playwright_fetcher = FakePlaywrightFetcher(playwright_success)

    result = service.crawl_product({"url": "https://example.com/item", "product_key": "sku-2", "group_name": "动态商品"})

    assert result["status"] == "success"
    assert result["fetch_mode"] == "playwright"
    assert result["fallback_used"] is False



def test_failed_crawl_is_persisted(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(status_code=429, text="")

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    service = build_service({"site_name": "测试站点", "domains": ["example.com"], "preferred_fetch_mode": "requests_only"})

    result = service.crawl_product({"url": "https://example.com/item", "product_key": "sku-fail", "group_name": "失败商品"})

    assert result["status"] == "failed"
    assert len(service.database.failed_records) == 1
    failed_record = service.database.failed_records[0]
    assert failed_record["product_key"] == "sku-fail"
    assert failed_record["group_name"] == "失败商品"
    assert failed_record["site_name"] == "测试站点"
    assert failed_record["status_code"] == 429



def test_site_rule_overrides_requests_fetcher_settings(monkeypatch):
    captured = {}

    def fake_get(fetcher, url):
        captured["url"] = url
        captured["timeout"] = fetcher.timeout
        captured["headers"] = fetcher.headers
        captured["proxies"] = fetcher._build_proxy_bypass()
        return FakeResponse(status_code=200, text="<html><body><h1>ok</h1></body></html>")

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    service = build_service(
        {
            "site_name": "策略站点",
            "domains": ["example.com"],
            "timeout_seconds": 7,
            "retry_count": 5,
            "request_delay_seconds": 2.5,
            "blocked_status_codes": [418, 429],
            "custom_headers": {"Referer": "https://origin.example.com", "X-Test": "1"},
        },
        fetcher=RequestsFetcher(timeout=15, retries=2, delay=1.0, blocked_status_codes=[403, 429]),
    )

    fetch_result = service._fetch_with_optional_fallback("https://example.com/item", service.parser.match_rule("https://example.com/item"))

    assert captured["url"] == "https://example.com/item"
    assert captured["timeout"] == 7
    assert captured["headers"]["Referer"] == "https://origin.example.com"
    assert captured["headers"]["X-Test"] == "1"
    assert captured["proxies"] == {"http": None, "https": None}
    assert fetch_result.metadata["timeout"] == 7
    assert fetch_result.metadata["retries"] == 5
    assert fetch_result.metadata["delay"] == 2.5
    assert fetch_result.metadata["blocked_status_codes"] == [418, 429]



def test_site_rule_overrides_playwright_timeout(monkeypatch):
    def fake_fetch(self, url: str) -> FetchResult:
        return FetchResult(
            url=url,
            status_code=200,
            html="<html><body><h1>ok</h1></body></html>",
            metadata={"timeout_ms": self.timeout_ms, "wait_until": self.wait_until},
        )

    monkeypatch.setattr(PlaywrightFetcher, "fetch", fake_fetch)

    service = build_service(
        {
            "site_name": "动态站点",
            "domains": ["example.com"],
            "preferred_fetch_mode": "playwright",
            "timeout_seconds": 9,
            "playwright_wait_until": "domcontentloaded",
        }
    )
    service.playwright_fetcher = PlaywrightFetcher(timeout_ms=20000)

    fetch_result = service._fetch_with_optional_fallback("https://example.com/item", service.parser.match_rule("https://example.com/item"))

    assert fetch_result.metadata["fetch_mode"] == "playwright"
    assert fetch_result.metadata["timeout_ms"] == 9000
    assert fetch_result.metadata["wait_until"] == "domcontentloaded"



def test_requests_fetcher_returns_proxy_suggestion(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.exceptions.ProxyError("Unable to connect to proxy")

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    fetcher = RequestsFetcher(timeout=5, retries=0, delay=0)
    result = fetcher.fetch("https://example.com/item")

    assert result.error is not None
    assert result.metadata["suggestion"] == "检测到代理连接异常，请检查系统代理、pip/requests 代理配置，或临时关闭代理后重试。"


def test_requests_fetcher_disables_environment_proxy(monkeypatch):
    captured = {}

    def fake_get(*args, **kwargs):
        fetcher = args[0]
        captured["proxies"] = fetcher._build_proxy_bypass()
        return FakeResponse(status_code=200, text="<html><body>ok</body></html>")

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    fetcher = RequestsFetcher(timeout=5, retries=0, delay=0)
    result = fetcher.fetch("https://example.com/item")

    assert result.status_code == 200
    assert captured["proxies"] == {"http": None, "https": None}


def test_build_batch_product_key_uses_compact_market_identity():
    key = PriceCrawlerService._build_batch_product_key(
        {"product_key": "wbncp-market-all"},
        {
            "product_name": "萝卜",
            "promotion_text": "河南",
            "extra_fields": {
                "category": "蔬菜",
                "spec_text": "公斤",
            },
        },
        1,
    )

    assert key == "wbncp-market-all::蔬菜-萝卜-公斤"



def test_crawl_product_supports_generic_parse_without_site_rule(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(
            status_code=200,
            text="""
            <html>
              <head>
                <meta property="og:title" content="免配置商品" />
                <meta property="product:price:amount" content="19.80" />
              </head>
              <body>
                <div class="promo-text">系统自动识别</div>
              </body>
            </html>
            """,
        )

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    service = PriceCrawlerService(DummyDatabase(), [], fetcher=RequestsFetcher(), fallback_to_playwright=True)
    service.parser = SiteParser([])

    result = service.crawl_product({"url": "https://unknown.example.net/item", "product_key": "sku-404"})

    assert result["status"] == "success"
    assert result["site_name"] == "unknown.example.net"
    assert result["product_name"] == "免配置商品"
    assert result["current_price"] == 19.8


def test_crawl_product_auto_learns_site_rule(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(
            status_code=200,
            text="""
            <html>
              <head>
                <meta property="og:title" content="自动学习商品" />
                <meta property="product:price:amount" content="45.50" />
              </head>
              <body>
                <div class="promo-text">自动规则生成</div>
              </body>
            </html>
            """,
        )

    stored = {}

    def fake_store(rule: dict):
        stored["rule"] = rule
        return rule, True

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    service = PriceCrawlerService(
        DummyDatabase(),
        [],
        fetcher=RequestsFetcher(),
        fallback_to_playwright=True,
        site_rule_store=fake_store,
        auto_learn_site_rules=True,
    )

    result = service.crawl_product({"url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69", "product_key": "sku-auto"})

    assert result["status"] == "success"
    assert "自动识别并保存平台规则" in result["suggestion"]
    assert stored["rule"]["domains"] == ["www.wbncp.com", "wbncp.com"]
    assert stored["rule"]["price_selectors"] == ["meta[property='product:price:amount']"]
    assert stored["rule"]["name_selectors"] == ["meta[property='og:title']"]


def test_api_fetch_is_preferred_when_site_rule_configured(monkeypatch):
    def should_not_call_page(*args, **kwargs):
        raise AssertionError("接口优先成功时不应继续抓页面")

    class FakeApiResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"name": "接口商品", "price": "66.80", "old_price": "88.00"}}

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", lambda *args, **kwargs: FakeApiResponse())
    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", should_not_call_page)

    rule = {
        "site_name": "接口站点",
        "domains": ["example.com"],
        "api_strategy": "prefer",
        "api_url": "https://example.com/api/price",
        "api_method": "GET",
        "api_field_mapping": {
            "product_name": "data.name",
            "current_price": "data.price",
            "original_price": "data.old_price",
        },
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    result = service.crawl_product({"url": "https://example.com/item", "product_key": "sku-api"})

    assert result["status"] == "success"
    assert result["fetch_mode"] == "api"
    assert result["product_name"] == "接口商品"
    assert result["current_price"] == 66.8


def test_api_fetch_supports_product_template_variables(monkeypatch):
    captured = {}

    class FakeApiResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"name": "白菜", "price": "1.55"}}

    def fake_request(fetcher, method, url, headers=None, json=None, timeout=None):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = json
        captured["proxies"] = fetcher._build_proxy_bypass()
        return FakeApiResponse()

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", fake_request)

    rule = {
        "site_name": "万邦国际",
        "domains": ["wbncp.com"],
        "api_strategy": "prefer",
        "api_url": "https://wap.api.banglail.com:62021/api-entrance/productcategory/officialWebsite",
        "api_method": "POST",
        "api_body_template": {
            "page": 1,
            "limit": 5,
            "categoryName": "${category}",
            "productName": "${product_name}",
        },
        "api_field_mapping": {
            "product_name": "data.name",
            "current_price": "data.price",
        },
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    result = service.crawl_product(
        {
            "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
            "product_key": "sku-template",
            "product_name": "白菜",
            "category": "蔬菜类",
        }
    )

    assert result["status"] == "success"
    assert captured["json"]["categoryName"] == "蔬菜类"
    assert captured["json"]["productName"] == "白菜"
    assert captured["proxies"] == {"http": None, "https": None}


def test_api_fetch_disables_environment_proxy(monkeypatch):
    captured = {}

    class FakeApiResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"name": "接口商品", "price": "66.80"}}

    def fake_request(fetcher, method, url, headers=None, json=None, timeout=None):
        captured["proxies"] = fetcher._build_proxy_bypass()
        return FakeApiResponse()

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", fake_request)

    rule = {
        "site_name": "接口站点",
        "domains": ["example.com"],
        "api_strategy": "prefer",
        "api_url": "https://example.com/api/price",
        "api_method": "GET",
        "api_field_mapping": {
            "product_name": "data.name",
            "current_price": "data.price",
        },
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    result = service.crawl_product({"url": "https://example.com/item", "product_key": "sku-api-proxy"})

    assert result["status"] == "success"
    assert captured["proxies"] == {"http": None, "https": None}


def test_success_record_stores_slim_raw_payload(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(status_code=200, text="<html><body>ok</body></html>")

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)
    service = build_service({"site_name": "万邦国际", "domains": ["wbncp.com"]})

    result = service.crawl_product(
        {
            "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
            "product_key": "sku-slim",
            "product_name": "白菜",
        }
    )

    assert result["status"] == "success"
    assert len(service.database.price_records) == 1
    raw_payload = service.database.price_records[0]["raw_payload"]
    assert raw_payload == {}


def test_liancai_success_record_stores_empty_raw_payload(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(status_code=200, text="<html><body>ok</body></html>")

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)
    service = build_service({"site_name": "莲菜网", "domains": ["liancaiwang.cn"]})

    class LiancaiParserStub(ParserStub):
        def parse(self, url: str, html: str) -> dict:
            return {
                "site_name": "莲菜网App | 干调类",
                "product_name": "木耳",
                "current_price": 29.9,
                "original_price": 31.5,
                "promotion_text": "测试",
                "currency": "CNY",
                "availability": "in_stock",
                "raw_extract": {},
                "extra_fields": {
                    "cover": "https://example.com/cover.jpg",
                },
            }

    service.parser = LiancaiParserStub({"site_name": "莲菜网", "domains": ["liancaiwang.cn"]})
    result = service.crawl_product(
        {
            "url": "https://lcwgetway.liancaiwang.cn",
            "product_key": "sku-liancai",
            "product_name": "木耳",
        }
    )

    assert result["status"] == "success"
    raw_payload = service.database.price_records[0]["raw_payload"]
    assert raw_payload == {}


def test_batch_api_source_creates_multiple_records(monkeypatch):
    class FakeApiResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": {
                    "list": [
                        {"categoryName": "蔬菜类", "productName": "白菜", "priceAvg": 1.55, "priceMax": 1.60, "productPlace": "湖北", "unit": "公斤"},
                        {"categoryName": "蔬菜类", "productName": "白豆", "priceAvg": 10.35, "priceMax": 13.00, "productPlace": "云南", "unit": "公斤"},
                    ]
                }
            }

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", lambda *args, **kwargs: FakeApiResponse())

    rule = {
        "site_name": "万邦国际",
        "domains": ["wbncp.com"],
        "api_strategy": "prefer",
        "api_url": "https://wap.api.banglail.com:62021/api-entrance/productcategory/officialWebsite",
        "api_method": "POST",
        "batch_list_path": "data.list",
        "api_field_mapping": {
            "category": "categoryName",
            "product_name": "productName",
            "current_price": "priceAvg",
            "original_price": "priceMax",
            "promotion_text": "productPlace",
            "spec_text": "unit",
            "group_name": "categoryName",
        },
    }

    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)
    results = service.crawl_source(
        {
            "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
            "product_key": "wbncp-list",
            "group_name": "万邦国际",
            "source_type": "batch",
        }
    )

    assert len(results) == 2
    assert results[0]["product_name"] == "白菜"
    assert results[0]["current_price"] == 1.55
    assert results[1]["product_name"] == "白豆"
    assert results[1]["group_name"] == "蔬菜类"
    assert results[0]["product_key"].startswith("wbncp-list::")


def test_batch_api_source_fetches_all_pages(monkeypatch):
    responses = [
        {
            "data": {
                "total": 3,
                "pageNum": 1,
                "pageSize": 2,
                "hasNext": True,
                "list": [
                    {"categoryName": "蔬菜类", "productName": "白菜", "priceAvg": 1.55},
                    {"categoryName": "蔬菜类", "productName": "白豆", "priceAvg": 10.35},
                ],
            }
        },
        {
            "data": {
                "total": 3,
                "pageNum": 2,
                "pageSize": 2,
                "hasNext": False,
                "list": [
                    {"categoryName": "蔬菜类", "productName": "菠菜", "priceAvg": 3.80},
                ],
            }
        },
    ]
    requested_pages = []

    class FakeApiResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_request(_fetcher, method, url, headers=None, json=None, timeout=None):
        requested_pages.append(json.get("page"))
        return FakeApiResponse(responses[len(requested_pages) - 1])

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", fake_request)

    rule = {
        "site_name": "万邦国际",
        "domains": ["wbncp.com"],
        "api_strategy": "prefer",
        "api_url": "https://wap.api.banglail.com:62021/api-entrance/productcategory/officialWebsite",
        "api_method": "POST",
        "api_body_template": {"page": 1, "limit": 2},
        "batch_list_path": "data.list",
        "api_field_mapping": {
            "group_name": "categoryName",
            "product_name": "productName",
            "current_price": "priceAvg",
        },
    }

    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)
    results = service.crawl_source(
        {
            "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
            "product_key": "wbncp-list",
            "group_name": "万邦国际",
            "source_type": "batch",
        }
    )

    assert requested_pages == [1, 2]
    assert len(results) == 3
    assert results[-1]["product_name"] == "菠菜"


def test_batch_api_source_default_page_limit_exceeds_fifty(monkeypatch):
    requested_pages = []

    class FakeApiResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def __init__(self, page: int):
            self.page = page

        def raise_for_status(self):
            return None

        def json(self):
            has_next = self.page < 55
            return {
                "data": {
                    "total": 55,
                    "pageNum": self.page,
                    "pageSize": 1,
                    "hasNext": has_next,
                    "list": [{"categoryName": "蔬菜类", "productName": f"白菜{self.page}", "priceAvg": 1.0 + self.page}],
                }
            }

    def fake_request(_fetcher, method, url, headers=None, json=None, timeout=None):
        page = int(json.get("page"))
        requested_pages.append(page)
        return FakeApiResponse(page)

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", fake_request)

    rule = {
        "site_name": "万邦国际",
        "domains": ["wbncp.com"],
        "api_strategy": "prefer",
        "api_url": "https://wap.api.banglail.com:62021/api-entrance/productcategory/officialWebsite",
        "api_method": "POST",
        "api_body_template": {"page": 1, "limit": 1},
        "batch_list_path": "data.list",
        "api_field_mapping": {
            "group_name": "categoryName",
            "product_name": "productName",
            "current_price": "priceAvg",
        },
    }

    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)
    results = service.crawl_source(
        {
            "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
            "product_key": "wbncp-list",
            "group_name": "万邦国际",
            "source_type": "batch",
        }
    )

    assert requested_pages[0] == 1
    assert requested_pages[-1] == 55
    assert len(results) == 55


def test_wbncp_batch_items_are_compacted_by_product_key():
    service = build_service({"site_name": "万邦国际", "domains": ["wbncp.com"]})
    product = {"product_key": "wbncp-market-all", "url": "https://www.wbncp.com/"}
    parsed_items = [
        {
            "site_name": "万邦国际",
            "product_name": "萝卜",
            "current_price": 1.0,
            "original_price": 1.5,
            "promotion_text": "河南",
            "extra_fields": {
                "category": "蔬菜类",
                "group_name": "蔬菜类",
                "spec_text": "公斤",
            },
        },
        {
            "site_name": "万邦国际",
            "product_name": "萝卜",
            "current_price": 2.0,
            "original_price": 2.5,
            "promotion_text": "山东",
            "extra_fields": {
                "category": "蔬菜类",
                "group_name": "蔬菜类",
                "spec_text": "公斤",
            },
        },
    ]

    compacted = service._compact_batch_items(product, {"site_name": "万邦国际"}, parsed_items)

    assert len(compacted) == 1
    assert compacted[0]["current_price"] == 1.5
    assert compacted[0]["original_price"] == 2.5
    assert compacted[0]["promotion_text"] == "多产地报价"


def test_crawl_many_flattens_batch_results(monkeypatch):
    class FakeApiResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"list": [{"categoryName": "蔬菜类", "productName": "白菜", "priceAvg": 1.55}]}}

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", lambda *args, **kwargs: FakeApiResponse())

    def fake_get(*args, **kwargs):
        return FakeResponse(
            status_code=200,
            text="<html><head><meta property='og:title' content='单商品' /><meta property='product:price:amount' content='9.90' /></head><body></body></html>",
        )

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    rule = {
        "site_name": "万邦国际",
        "domains": ["wbncp.com"],
        "api_strategy": "prefer",
        "api_url": "https://wap.api.banglail.com:62021/api-entrance/productcategory/officialWebsite",
        "api_method": "POST",
        "batch_list_path": "data.list",
        "api_field_mapping": {
            "group_name": "categoryName",
            "product_name": "productName",
            "current_price": "priceAvg",
        },
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    results = service.crawl_many(
        [
            {
                "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
                "product_key": "wbncp-list",
                "source_type": "batch",
            },
            {
                "url": "https://example.com/item",
                "product_key": "single-item",
                "group_name": "单商品",
            },
        ]
    )

    assert len(results) == 2
    assert any(item["product_name"] == "白菜" for item in results)
    assert any(item["product_name"] == "单商品" for item in results)


def test_api_fetch_falls_back_to_page_when_api_fails(monkeypatch):
    class FailedApiResponse:
        status_code = 500
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            raise requests.HTTPError("500 Server Error", response=self)

        def json(self):
            return {"error": "fail"}

    def fake_get(*args, **kwargs):
        return FakeResponse(
            status_code=200,
            text="<html><head><meta property='og:title' content='回退商品' /><meta property='product:price:amount' content='23.50' /></head><body></body></html>",
        )

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", lambda *args, **kwargs: FailedApiResponse())
    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    rule = {
        "site_name": "接口站点",
        "domains": ["example.com"],
        "api_strategy": "prefer",
        "api_url": "https://example.com/api/price",
        "api_method": "GET",
        "api_field_mapping": {"current_price": "data.price"},
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    result = service.crawl_product({"url": "https://example.com/item", "product_key": "sku-api-fallback"})

    assert result["status"] == "success"
    assert result["fetch_mode"] in {"requests", "playwright"}
    assert result["current_price"] == 23.5


def test_playwright_network_candidates_are_used_when_html_has_no_price():
    playwright_result = FetchResult(
        url="https://example.com/item",
        status_code=200,
        html="<html><body><h1>无价页面</h1></body></html>",
        metadata={
            "fetch_mode": "playwright",
            "network_candidates": [
                {
                    "url": "https://example.com/api/detail",
                    "method": "GET",
                    "content_type": "application/json",
                    "json_body": {"data": {"name": "网络接口商品", "price": "109.90"}},
                }
            ],
        },
    )
    service = build_service({"site_name": "动态站点", "domains": ["example.com"], "preferred_fetch_mode": "playwright"})
    service.playwright_fetcher = FakePlaywrightFetcher(playwright_result)
    service.parser = ParserStubNoPrice({"site_name": "动态站点", "domains": ["example.com"]})

    result = service.crawl_product({"url": "https://example.com/item", "product_key": "sku-net"})

    assert result["status"] == "success"
    assert result["fetch_mode"] == "playwright"
    assert result["product_name"] == "网络接口商品"
    assert result["current_price"] == 109.9



def test_playwright_fetcher_missing_package_returns_suggestion(monkeypatch):
    original_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "playwright.sync_api":
            raise ImportError("missing playwright")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)

    fetcher = PlaywrightFetcher()
    result = fetcher.fetch("https://example.com/item")

    assert result.error == "playwright 未安装，请执行: pip install playwright && playwright install chromium"
    assert result.metadata["suggestion"] == "请先安装 Playwright Python 包，并执行浏览器安装命令后再重试动态抓取。"
