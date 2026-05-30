from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from crawler.fetcher import PriceCrawlerService


class CrawlSourceStrategy(Protocol):
    name: str

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        ...

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        ...


class ChinapriceBatchSourceStrategy:
    name = "chinaprice_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_chinaprice_batch_source(product, site_rule)


class PfscChartBatchSourceStrategy:
    name = "pfsc_chart_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_pfsc_chart_source(product, site_rule)


class MoaWholesaleBatchSourceStrategy:
    name = "moa_wholesale_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_moa_wholesale_source(product, site_rule)


class HnnhgscBatchSourceStrategy:
    name = "hnnhgsc_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_hnnhgsc_batch_source(product, site_rule)


class HenanFgwPriceBatchSourceStrategy:
    name = "henan_fgw_price_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_henan_fgw_price_source(product, site_rule)


class ZznyClzArticleBatchSourceStrategy:
    name = "zzny_clz_article_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_zzny_clz_article_source(product, site_rule)


class CnhnbMarketBatchSourceStrategy:
    name = "cnhnb_market_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_cnhnb_market_source(product, site_rule)


class NanjingZhongcaiPublicBatchSourceStrategy:
    name = "nanjing_zhongcai_public_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_nanjing_zhongcai_public_source(product, site_rule)


class LiancaiH5BatchSourceStrategy:
    name = "liancai_h5_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_liancai_h5_source(product, site_rule)


class LiancaiAppGatewayBatchSourceStrategy:
    name = "liancai_app_gateway_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_liancai_app_gateway_source(product, site_rule)


class MeicaiAppGatewayBatchSourceStrategy:
    name = "meicai_app_gateway_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        return str((site_rule or {}).get("strategy") or "").strip().lower() == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_meicai_app_gateway_source(product, site_rule)


class ApiBatchSourceStrategy:
    name = "api_batch"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        configured = str((site_rule or {}).get("strategy") or "").strip().lower()
        if configured == self.name:
            return True
        source_type = str(product.get("source_type") or "single").strip().lower()
        return source_type == "batch" and bool(site_rule and site_rule.get("api_url"))

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return service._crawl_batch_api_source(product, site_rule)


class BrowserAssistedSourceStrategy:
    name = "browser_assisted"

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        configured = str((site_rule or {}).get("strategy") or "").strip().lower()
        return configured == self.name

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return [service._build_browser_assisted_result(product, site_rule)]


class SingleSourceStrategy:
    name = "single"
    aliases = {"", "single", "html_single", "html", "generic", "page"}

    def matches(self, product: dict[str, Any], site_rule: dict | None) -> bool:
        configured = str((site_rule or {}).get("strategy") or "").strip().lower()
        if configured in self.aliases:
            return True
        source_type = str(product.get("source_type") or "single").strip().lower()
        return source_type != "batch"

    def crawl(
        self,
        service: "PriceCrawlerService",
        product: dict[str, Any],
        site_rule: dict | None,
    ) -> list[dict[str, Any]]:
        return [service._crawl_single_source(product, site_rule)]
