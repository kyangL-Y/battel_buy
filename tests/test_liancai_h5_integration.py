from crawler.liancai_h5 import LiancaiCategory
from crawler.public_source_crawlers import PublicSourceCrawler
from crawler.source_strategies import LiancaiH5BatchSourceStrategy


class _FakeClient:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

    def login(self):
        return {"code": 200, "message": "ok"}

    def fetch_category_tree(self):
        top = [
            LiancaiCategory(fid="6", name="蔬菜类", page_url="http://m.liancaiwang.cn/list/index/id/6.html"),
            LiancaiCategory(fid="774", name="干调类", page_url="http://m.liancaiwang.cn/list/index/id/774.html"),
        ]
        subs = [
            LiancaiCategory(fid="102", name="叶菜类", page_url="http://m.liancaiwang.cn/list/index/id/102.html", parent_fid="6", parent_name="蔬菜类"),
        ]
        return top, subs

    def fetch_category_page(self, fid: str, page: int = 1):
        if page > 1:
            return []
        return [
            {
                "product_id": "91702",
                "category_id": fid,
                "termid": "102",
                "title": "绿包菜 青甘蓝 10斤",
                "subtitle": "叶片浅绿色",
                "price": 7.8,
                "market_price": 0,
                "size": "10斤/袋(合每斤0.78元)",
                "unit": "袋",
                "inventory_text": "剩余库存16件",
                "cover": "http://mst.liancaiwang.cn/upload/uploads/cabbage.jpg",
                "raw": {"brand": {"name": "测试品牌"}},
            }
        ]


def test_liancai_h5_strategy_matches_and_delegates():
    strategy = LiancaiH5BatchSourceStrategy()

    assert strategy.matches({}, {"strategy": "liancai_h5_batch"}) is True
    assert strategy.matches({}, {"strategy": "browser_assisted"}) is False

    class _Service:
        def __init__(self):
            self.called = False

        def _crawl_liancai_h5_source(self, product, site_rule):
            self.called = True
            return [{"status": "success"}]

    service = _Service()
    result = strategy.crawl(service, {"url": "http://m.liancaiwang.cn"}, {"strategy": "liancai_h5_batch"})

    assert service.called is True
    assert result == [{"status": "success"}]


def test_fetch_liancai_h5_uses_login_and_category_mapping(monkeypatch):
    monkeypatch.setattr("crawler.public_source_crawlers.LiancaiH5Client", _FakeClient)
    monkeypatch.setenv("LIANCAI_PHONE", "18639214007")
    monkeypatch.setenv("LIANCAI_PASSWORD", "sm18639214007")

    crawler = PublicSourceCrawler()
    product = {
        "url": "http://m.liancaiwang.cn",
        "group_name": "本地市场源",
        "category": "蔬菜类",
    }
    site_rule = {
        "base_url": "http://m.liancaiwang.cn",
        "login_phone_env": "LIANCAI_PHONE",
        "login_password_env": "LIANCAI_PASSWORD",
        "max_pages": 3,
    }

    result = crawler.fetch_liancai_h5(product, site_rule)

    assert len(result) == 1
    assert result[0]["site_name"] == "莲菜网H5 | 蔬菜类"
    assert result[0]["product_name"] == "绿包菜 青甘蓝 10斤"
    assert result[0]["extra_fields"]["category"] == "叶菜类"
    assert result[0]["extra_fields"]["brand"] == "测试品牌"
