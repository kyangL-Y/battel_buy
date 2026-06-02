from __future__ import annotations

from crawler.fetcher import PriceCrawlerService
from crawler.public_source_crawlers import NanjingZhongcaiNoNewArticle
from crawler.requests_fetcher import RequestsFetcher


class DummyDatabase:
    def __init__(self):
        self.failed_records = []
        self.product_records = []
        self.price_records = []

    def upsert_product(self, **kwargs):
        self.product_records.append(kwargs)
        return 1

    def insert_price_record(self, **kwargs):
        self.price_records.append(kwargs)
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


def test_crawl_source_uses_hnnhgsc_batch_strategy(monkeypatch):
    rule = {
        "site_name": "河南内黄果蔬城",
        "domains": ["hnnhgsc.com"],
        "strategy": "hnnhgsc_batch",
        "verify_ssl": False,
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_hnnhgsc",
        lambda product, site_rule=None: [
            {
                "site_name": "河南内黄果蔬城",
                "product_name": "尖椒",
                "current_price": 1.8,
                "original_price": None,
                "promotion_text": "内黄果蔬城页面行情 | 规格字段推断价格",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "果蔬行情",
                    "category": "果蔬行情",
                    "spec_text": "公斤",
                    "compare_key": "尖椒",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://www.hnnhgsc.com/Origin_market.html",
            "product_key": "hnnhgsc-market-price-all",
            "source_type": "batch",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "hnnhgsc_batch"
    assert results[0]["site_name"] == "河南内黄果蔬城"
    assert results[0]["product_name"] == "尖椒"


def test_crawl_source_uses_henan_fgw_price_batch_strategy(monkeypatch):
    rule = {
        "site_name": "河南省发改委价格监测",
        "domains": ["fgw.henan.gov.cn"],
        "strategy": "henan_fgw_price_batch",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_henan_fgw_price",
        lambda product, site_rule=None: [
            {
                "site_name": "河南省发改委价格监测 | 全省均价",
                "product_name": "白菜",
                "current_price": 0.94,
                "original_price": None,
                "promotion_text": "河南发改委全省监测 | 销售价格 | 2026-04-24",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "主要食品",
                    "category": "主要食品",
                    "spec_text": "元/500克",
                    "compare_key": "白菜",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://fgw.henan.gov.cn/bmfw/jgjc/",
            "product_key": "henan-fgw-price-monitor",
            "source_type": "batch",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "henan_fgw_price_batch"
    assert results[0]["site_name"] == "河南省发改委价格监测 | 全省均价"
    assert results[0]["product_name"] == "白菜"


def test_crawl_source_uses_zzny_clz_article_batch_strategy(monkeypatch):
    rule = {
        "site_name": "郑州市农业农村局菜篮子监测",
        "domains": ["zzny.zhengzhou.gov.cn"],
        "strategy": "zzny_clz_article_batch",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_zzny_clz_articles",
        lambda product, site_rule=None: [
            {
                "site_name": "郑州市农业农村局菜篮子监测 | 郑州监测",
                "product_name": "鸡蛋",
                "current_price": 6.26,
                "original_price": None,
                "promotion_text": "郑州菜篮子监测 | 2025年7月份郑州市 生鲜乳、鸡蛋、白羽肉鸡、生猪价格 走势分析 | 第4周 | 2025-08-04 15:31",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "郑州菜篮子监测",
                    "category": "郑州菜篮子监测",
                    "spec_text": "元/公斤",
                    "compare_key": "鸡蛋",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://zzny.zhengzhou.gov.cn/clzxx/index.jhtml",
            "product_key": "zzny-vegetable-basket-monitor",
            "source_type": "batch",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "zzny_clz_article_batch"
    assert results[0]["site_name"] == "郑州市农业农村局菜篮子监测 | 郑州监测"
    assert results[0]["product_name"] == "鸡蛋"


def test_crawl_source_uses_cnhnb_market_batch_strategy(monkeypatch):
    rule = {
        "site_name": "惠农网行情",
        "domains": ["cnhnb.com"],
        "strategy": "cnhnb_market_batch",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_cnhnb_market",
        lambda product, site_rule=None: [
            {
                "site_name": "惠农网行情 | 山里人干货",
                "product_name": "香菇",
                "current_price": 20.0,
                "original_price": 21.0,
                "promotion_text": "惠农网河南参考行情 | 2小时前 | 精品香菇干货",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "惠农网参考行情",
                    "category": "香菇",
                    "spec_text": "斤",
                    "compare_key": "香菇",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://www.cnhnb.com/hangqing/cdlist-0-0-16-0-0-1/",
            "product_key": "cnhnb-henan-market-price",
            "source_type": "batch",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "cnhnb_market_batch"
    assert results[0]["site_name"] == "惠农网行情 | 山里人干货"
    assert results[0]["product_name"] == "香菇"


def test_crawl_source_uses_liancai_h5_batch_strategy(monkeypatch):
    rule = {
        "site_name": "莲菜网H5",
        "domains": ["m.liancaiwang.cn"],
        "strategy": "liancai_h5_batch",
        "base_url": "http://m.liancaiwang.cn",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_liancai_h5",
        lambda product, site_rule=None: [
            {
                "site_name": "莲菜网H5 | 蔬菜类",
                "product_name": "绿包菜 青甘蓝 10斤",
                "current_price": 7.8,
                "original_price": 0,
                "promotion_text": "莲菜网H5 | 分类:蔬菜类 | 页码:1",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "本地市场源",
                    "category": "蔬菜类",
                    "spec_text": "10斤/袋(合每斤0.78元)",
                    "compare_key": "绿包菜 青甘蓝 10斤",
                    "product_series": "102",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "http://m.liancaiwang.cn",
            "product_key": "lencai-miniapp-vegetables",
            "product_name": "莲菜网小程序·蔬菜类",
            "source_type": "batch",
            "category": "蔬菜类",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "liancai_h5_batch"
    assert results[0]["site_name"] == "莲菜网H5 | 蔬菜类"
    assert results[0]["product_name"] == "绿包菜 青甘蓝 10斤"


def test_crawl_source_uses_kuailv_h5_batch_strategy(monkeypatch):
    rule = {
        "site_name": "快驴商城H5",
        "domains": ["klmall.meituan.com"],
        "strategy": "kuailv_h5_batch",
        "gateway_base_url": "https://klmall.meituan.com/wxmall",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_kuailv_h5",
        lambda product, site_rule=None: [
            {
                "site_name": "快驴商城H5 | 蔬菜",
                "product_name": "上海青 500g",
                "current_price": 2.6,
                "original_price": 3.0,
                "promotion_text": "快驴商城H5 | 分类:蔬菜 | 页码:1",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "快驴商城",
                    "category": "叶菜",
                    "spec_text": "500g/份",
                    "compare_key": "上海青 500g",
                    "market_name": "南京快驴商城",
                    "region_label": "南京市",
                    "province": "江苏省",
                    "city": "南京市",
                    "product_series": "g-1",
                    "kuailv_goods_id": "g-1",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://klmall.meituan.com/wxmall",
            "product_key": "kuailv-h5-class-products",
            "product_name": "快驴商城H5·分类商品",
            "source_type": "batch",
            "category": "蔬菜",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "kuailv_h5_batch"
    assert results[0]["site_name"] == "快驴商城H5 | 蔬菜"
    assert results[0]["product_name"] == "上海青 500g"


def test_crawl_source_uses_nanjing_zhongcai_public_batch_strategy(monkeypatch):
    rule = {
        "site_name": "南京众彩",
        "domains": ["www.njnfwl.com"],
        "strategy": "nanjing_zhongcai_public_batch",
        "base_url": "https://www.njnfwl.com",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_nanjing_zhongcai_public",
        lambda product, site_rule=None: [
            {
                "site_name": "南京众彩 | 蔬菜",
                "product_name": "青菜",
                "current_price": 2.8,
                "original_price": 3.2,
                "promotion_text": "2026年5月28日蔬菜价格参考表 | 图片OCR",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "南京众彩",
                    "category": "蔬菜",
                    "spec_text": "价格参考表",
                    "compare_key": "青菜",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://www.njnfwl.com/list-eqpn3l3g/shucaijiage/1/10",
            "product_key": "nanjing-zhongcai-vegetable-price",
            "product_name": "南京众彩·蔬菜价格参考表",
            "source_type": "batch",
            "category": "蔬菜",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "nanjing_zhongcai_public_batch"
    assert results[0]["site_name"] == "南京众彩 | 蔬菜"
    assert results[0]["product_name"] == "青菜"


def test_crawl_source_marks_nanjing_zhongcai_unchanged_incremental_run_as_skipped(monkeypatch):
    rule = {
        "site_name": "南京众彩",
        "domains": ["www.njnfwl.com"],
        "strategy": "nanjing_zhongcai_public_batch",
        "base_url": "https://www.njnfwl.com",
    }
    database = DummyDatabase()
    service = PriceCrawlerService(database, [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    def fake_fetch(product, site_rule=None):
        raise NanjingZhongcaiNoNewArticle("南京众彩没有新价格文章，已跳过 1 篇历史文章")

    monkeypatch.setattr(service.public_source_crawler, "fetch_nanjing_zhongcai_public", fake_fetch)

    results = service.crawl_source(
        {
            "url": "https://www.njnfwl.com/list-eqpn3l3g/shucaijiage/1/10",
            "product_key": "nanjing-zhongcai-vegetable-price",
            "product_name": "南京众彩·蔬菜价格参考表",
            "source_type": "batch",
            "category": "蔬菜",
        }
    )

    assert results[0]["status"] == "success"
    assert results[0]["skipped"] is True
    assert results[0]["status_code"] == 204
    assert database.failed_records == []


def test_crawl_source_uses_liancai_app_gateway_batch_strategy(monkeypatch):
    rule = {
        "site_name": "莲菜网App",
        "domains": ["lcwgetway.liancaiwang.cn"],
        "strategy": "liancai_app_gateway_batch",
        "gateway_base_url": "https://lcwgetway.liancaiwang.cn",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_liancai_app_gateway",
        lambda product, site_rule=None: [
            {
                "site_name": "莲菜网App | 干调类",
                "product_name": "花椒1斤-豫佐味",
                "current_price": 29.9,
                "original_price": 32.5,
                "promotion_text": "莲菜网App | 分类:干调类 | 品类:白扣 | 品牌:小鸽 | 页码:1",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "莲菜网",
                    "category": "干调类",
                    "spec_text": "1斤/袋",
                    "compare_key": "花椒1斤-豫佐味",
                    "product_series": "74",
                    "liancai_keyword": "白扣",
                    "liancai_brand_id": "2887",
                    "liancai_brand_name": "小鸽",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://lcwgetway.liancaiwang.cn",
            "product_key": "lencai-app-seasonings",
            "product_name": "莲菜网App·干调类",
            "source_type": "batch",
            "category": "干调类",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "liancai_app_gateway_batch"
    assert results[0]["site_name"] == "莲菜网App | 干调类"
    assert results[0]["product_name"] == "花椒1斤-豫佐味"


def test_crawl_source_uses_meicai_app_gateway_batch_strategy(monkeypatch):
    rule = {
        "site_name": "美菜网App",
        "domains": ["mall-entrance.yunshanmeicai.com"],
        "strategy": "meicai_app_gateway_batch",
        "gateway_base_url": "https://mall-entrance.yunshanmeicai.com",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_meicai_app_gateway",
        lambda product, site_rule=None: [
            {
                "site_name": "美菜网App | 推荐商品",
                "product_name": "青菜 约500g",
                "current_price": 2.8,
                "original_price": None,
                "promotion_text": "美菜网App | 接口:xb_feed | 页码:1",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "美菜网",
                    "category": "蔬菜",
                    "spec_text": "元/斤",
                    "compare_key": "青菜 约500g",
                    "market_name": "南京美菜网",
                    "region_label": "南京市",
                    "province": "江苏省",
                    "city": "南京市",
                    "product_series": "sku-1",
                    "brand": "本地",
                    "cover": "https://img.example/greens.jpg",
                    "meicai_sku_id": "sku-1",
                    "meicai_spu_id": "spu-1",
                    "liancai_top_category": "蔬菜类",
                    "liancai_subcategory": "叶菜类",
                    "liancai_mapping_source": "meicai_sale_c2_id",
                    "meicai_internal_category": "叶菜类",
                    "meicai_internal_market_category": "蔬菜类",
                    "meicai_internal_mapping_source": "meicai_sale_c2_id",
                    "meicai_internal_mapping_confidence": 0.78,
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://mall-entrance.yunshanmeicai.com",
            "product_key": "meicai-app-feed",
            "product_name": "美菜网App·推荐商品",
            "source_type": "batch",
            "category": "蔬菜",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "meicai_app_gateway_batch"
    assert results[0]["site_name"] == "美菜网App | 推荐商品"
    assert results[0]["product_name"] == "青菜 约500g"
    assert results[0]["image_url"] == "https://img.example/greens.jpg"
    assert service.database.product_records[0]["category"] == "蔬菜"
    assert service.database.product_records[0]["brand"] == "本地"
    assert service.database.product_records[0]["product_series"] == "sku-1"
    assert service.database.product_records[0]["spec_text"] == "元/斤"
    assert service.database.product_records[0]["compare_key"] == "青菜 约500g"
    assert service.database.product_records[0]["market_name"] == "南京美菜网"
    assert service.database.product_records[0]["region_label"] == "南京市"
    assert service.database.product_records[0]["province"] == "江苏省"
    assert service.database.product_records[0]["city"] == "南京市"
    assert service.database.product_records[0]["image_url"] == "https://img.example/greens.jpg"
    assert service.database.product_records[0]["liancai_top_category"] == "蔬菜类"
    assert service.database.product_records[0]["liancai_subcategory"] == "叶菜类"
    assert service.database.product_records[0]["liancai_mapping_source"] == "meicai_sale_c2_id"
    assert service.database.price_records[0]["unit_name"] == "g"
    assert service.database.price_records[0]["unit_value"] == 500.0
    assert service.database.price_records[0]["unit_price"] == 0.56


def test_crawl_source_uses_meicai_h5_decrypt_batch_strategy(monkeypatch):
    rule = {
        "site_name": "美菜网H5",
        "domains": ["mall-entrance.yunshanmeicai.com"],
        "strategy": "meicai_h5_decrypt_batch",
        "gateway_base_url": "https://mall-entrance.yunshanmeicai.com",
    }
    service = PriceCrawlerService(DummyDatabase(), [rule], fetcher=RequestsFetcher(), fallback_to_playwright=True)

    monkeypatch.setattr(
        service.public_source_crawler,
        "fetch_meicai_h5_decrypt",
        lambda product, site_rule=None: [
            {
                "site_name": "美菜网H5 | 推荐商品",
                "product_name": "H5青菜",
                "current_price": 2.8,
                "original_price": None,
                "promotion_text": "美菜网H5 | 接口:h5_class_products | 页码:1",
                "currency": "CNY",
                "extra_fields": {
                    "group_name": "美菜网",
                    "category": "蔬菜",
                    "spec_text": "斤",
                    "compare_key": "H5青菜",
                    "market_name": "南京美菜网",
                    "region_label": "南京市",
                    "province": "江苏省",
                    "city": "南京市",
                    "product_series": "sku-h5",
                    "meicai_sku_id": "sku-h5",
                },
            }
        ],
    )

    results = service.crawl_source(
        {
            "url": "https://mall-entrance.yunshanmeicai.com",
            "product_key": "meicai-h5-feed",
            "product_name": "美菜网H5·分类商品",
            "source_type": "batch",
            "category": "蔬菜",
        }
    )

    assert len(results) == 1
    assert results[0]["source_strategy"] == "meicai_h5_decrypt_batch"
    assert results[0]["site_name"] == "美菜网H5 | 推荐商品"
    assert results[0]["product_name"] == "H5青菜"
