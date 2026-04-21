from __future__ import annotations

from crawler.fetcher import PriceCrawlerService
from crawler.requests_fetcher import RequestsFetcher


class DummyDatabase:
    def __init__(self):
        self.failed_records = []

    def upsert_product(self, **kwargs):
        return 1

    def insert_price_record(self, **kwargs):
        return 1

    def insert_failed_crawl_record(self, **kwargs):
        self.failed_records.append(kwargs)
        return 1


class FakeApiResponse:
    status_code = 200
    headers = {"content-type": "application/json"}

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeResponse:
    def __init__(self, status_code: int, text: str, headers: dict | None = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {"content-type": "text/html"}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"{self.status_code} error")



def test_crawl_source_uses_api_batch_strategy(monkeypatch):
    responses = [
        {"data": {"total": 2, "pageNum": 1, "pageSize": 100, "hasNext": False, "list": [
            {"categoryName": "蔬菜类", "productName": "白菜", "priceAvg": 1.55},
            {"categoryName": "蔬菜类", "productName": "菠菜", "priceAvg": 3.80},
        ]}}
    ]

    def fake_request(*args, **kwargs):
        return FakeApiResponse(responses[0])

    monkeypatch.setattr("crawler.api_fetcher.ApiFetcher._request_once", fake_request)

    rule = {
        "site_name": "万邦国际",
        "domains": ["wbncp.com"],
        "strategy": "api_batch",
        "api_strategy": "prefer",
        "api_url": "https://example.com/api",
        "api_method": "POST",
        "api_body_template": {"page": 1, "limit": 100},
        "batch_list_path": "data.list",
        "api_field_mapping": {
            "group_name": "categoryName",
            "product_name": "productName",
            "current_price": "priceAvg",
        },
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    results = service.crawl_source({
        "url": "https://www.wbncp.com/?m=home&c=Lists&a=index&tid=69",
        "product_key": "wbncp-list",
        "source_type": "batch",
    })

    assert len(results) == 2
    assert all(item["source_strategy"] == "api_batch" for item in results)
    assert results[0]["product_name"] == "白菜"



def test_crawl_source_uses_single_strategy_for_normal_page(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(
            status_code=200,
            text="<html><head><meta property='og:title' content='普通商品' /><meta property='product:price:amount' content='12.80' /></head><body></body></html>",
        )

    monkeypatch.setattr("crawler.requests_fetcher.RequestsFetcher._request_once", fake_get)

    service = PriceCrawlerService(DummyDatabase(), [], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    results = service.crawl_source({
        "url": "https://example.com/item",
        "product_key": "sku-single",
    })

    assert len(results) == 1
    assert results[0]["status"] == "success"
    assert results[0]["source_strategy"] == "single"
    assert results[0]["product_name"] == "普通商品"



def test_crawl_source_returns_browser_assisted_guidance():
    rule = {
        "site_name": "受保护站点",
        "domains": ["secure.example.com"],
        "strategy": "browser_assisted",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    results = service.crawl_source({
        "url": "https://secure.example.com/list",
        "product_key": "secure-1",
        "product_name": "测试商品",
    })

    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert results[0]["fetch_mode"] == "browser_assisted"
    assert results[0]["source_strategy"] == "browser_assisted"
    assert "浏览器态" in results[0]["suggestion"]


def test_crawl_source_uses_chinaprice_batch_strategy(monkeypatch):
    rule = {
        "site_name": "Chinaprice",
        "domains": ["chinaprice.cn"],
        "strategy": "chinaprice_batch",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_chinaprice",
        lambda product, site_rule=None: [
            {
                "site_name": "Chinaprice",
                "product_name": "白菜",
                "current_price": 1.07,
                "original_price": None,
                "promotion_text": "全国 | 总平均价 | 2025-12-31",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "蔬菜类",
                    "category": "蔬菜类",
                    "spec_text": "元/500克",
                    "compare_key": "白菜",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://www.chinaprice.cn/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg",
            "product_key": "chinaprice-summary-all",
            "source_type": "batch",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "chinaprice_batch"
    assert results[0]["site_name"] == "Chinaprice"
    assert results[0]["unit_name"] == "g"
    assert results[0]["unit_value"] == 500.0


def test_crawl_source_uses_pfsc_chart_batch_strategy(monkeypatch):
    rule = {
        "site_name": "PFSC",
        "domains": ["pfsc.agri.cn"],
        "strategy": "pfsc_chart_batch",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_pfsc",
        lambda product, site_rule=None: [
            {
                "site_name": "北京新发地",
                "product_name": "白菜",
                "current_price": 1.5,
                "original_price": None,
                "promotion_text": "PFSC市场行情 | 2026-04-06",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "蔬菜类",
                    "category": "蔬菜类",
                    "spec_text": "公斤",
                    "compare_key": "白菜",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://pfsc.agri.cn/#/priceMarket",
            "product_key": "pfsc-price-market-all",
            "source_type": "batch",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "pfsc_chart_batch"
    assert results[0]["site_name"] == "北京新发地"
    assert results[0]["spec_text"] == "公斤"


def test_crawl_source_uses_moa_wholesale_batch_strategy(monkeypatch):
    rule = {
        "site_name": "重点农产品市场信息平台",
        "domains": ["ncpscxx.moa.gov.cn"],
        "strategy": "moa_wholesale_batch",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_moa_wholesale",
        lambda product, site_rule=None: [
            {
                "site_name": "重点农产品平台 | 北京新发地",
                "product_name": "白条猪",
                "current_price": 12.5,
                "original_price": None,
                "promotion_text": "重点农产品平台批发价 | 2026-04-11",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "家畜",
                    "category": "家畜",
                    "spec_text": "公斤",
                    "compare_key": "白条猪",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://ncpscxx.moa.gov.cn/",
            "product_key": "moa-wholesale-market-all",
            "source_type": "batch",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "moa_wholesale_batch"
    assert results[0]["site_name"] == "重点农产品平台 | 北京新发地"
    assert results[0]["spec_text"] == "公斤"
