from __future__ import annotations

import argparse
from pathlib import Path

from analysis.metrics import compute_group_metrics
from crawler.fetcher import PriceCrawlerService
from crawler.playwright_fetcher import PlaywrightFetcher
from crawler.requests_fetcher import RequestsFetcher
from services.site_rule_registry import load_site_rules, upsert_site_rule
from storage.database import Database
from utils.config_loader import load_json_config, load_runtime_config
from utils.scheduler import run_interval
from utils.source_config import filter_enabled_sources


RUNTIME_CONFIG_PATH = "config/runtime.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="商品价格对比分析程序")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init-db", help="初始化数据库")
    init_parser.add_argument("--db", default=None, help="SQLite 文件路径；如未指定则读取运行时数据库配置")

    crawl_parser = subparsers.add_parser("crawl", help="执行一次抓取")
    crawl_parser.add_argument("--config", default="config/products.json", help="商品配置文件路径")
    crawl_parser.add_argument("--sites", default="config/sites.json", help="站点规则文件路径")
    crawl_parser.add_argument("--db", default=None, help="SQLite 文件路径；如未指定则读取运行时数据库配置")
    crawl_parser.add_argument(
        "--fetch-mode",
        default=None,
        choices=["requests", "playwright"],
        help="抓取方式：requests=静态抓取，playwright=动态抓取；留空则使用 runtime.json 默认值",
    )

    export_parser = subparsers.add_parser("export", help="导出统计结果为 CSV")
    export_parser.add_argument("--output", default="exports/price_analysis.csv", help="导出文件路径")
    export_parser.add_argument("--db", default=None, help="SQLite 文件路径；如未指定则读取运行时数据库配置")

    schedule_parser = subparsers.add_parser("schedule", help="按固定间隔执行抓取")
    schedule_parser.add_argument("--seconds", type=int, default=None, help="抓取间隔秒数；留空则使用 runtime.json 默认值")
    schedule_parser.add_argument("--minutes", type=int, default=None, help="抓取间隔分钟数，优先于 --seconds")
    schedule_parser.add_argument("--config", default="config/products.json", help="商品配置文件路径")
    schedule_parser.add_argument("--sites", default="config/sites.json", help="站点规则文件路径")
    schedule_parser.add_argument("--db", default=None, help="SQLite 文件路径；如未指定则读取运行时数据库配置")
    schedule_parser.add_argument(
        "--fetch-mode",
        default=None,
        choices=["requests", "playwright"],
        help="抓取方式：requests=静态抓取，playwright=动态抓取；留空则使用 runtime.json 默认值",
    )
    return parser


def get_db(db_path: str | None) -> Database:
    return Database(db_path) if db_path else Database()


def get_effective_fetch_mode(fetch_mode: str | None, runtime_config: dict) -> str:
    return fetch_mode or runtime_config.get("schedule", {}).get("fetch_mode", "requests")


def get_schedule_interval_seconds(args: argparse.Namespace, runtime_config: dict) -> int:
    if getattr(args, "minutes", None):
        return int(args.minutes) * 60
    if getattr(args, "seconds", None):
        return int(args.seconds)
    return int(runtime_config.get("schedule", {}).get("interval_seconds", 3600))


def build_crawler_service(
    db: Database,
    site_rules: list[dict],
    fetch_mode: str,
    runtime_config: dict,
    sites_path: str,
) -> PriceCrawlerService:
    crawler_config = runtime_config.get("crawler", {})
    fallback_to_playwright = bool(crawler_config.get("fallback_to_playwright", False))
    blocked_status_codes = crawler_config.get("blocked_status_codes", [403, 429])
    timeout = int(crawler_config.get("default_timeout", 15))
    retries = int(crawler_config.get("default_retries", 2))
    delay = float(crawler_config.get("default_delay", 1.0))
    auto_learn_site_rules = bool(crawler_config.get("auto_learn_site_rules", True))
    enable_api_discovery = bool(crawler_config.get("enable_api_discovery", False))
    api_timeout = int(crawler_config.get("api_timeout", timeout))
    api_retries = int(crawler_config.get("api_retries", 1))
    public_source_max_workers = int(crawler_config.get("public_source_max_workers", 1))
    playwright_block_resource_types = tuple(
        crawler_config.get("playwright_block_resource_types", ["image", "media", "font"])
        or ["image", "media", "font"]
    )

    if fetch_mode == "playwright":
        return PriceCrawlerService(
            db,
            site_rules,
            fetcher=PlaywrightFetcher(
                timeout_ms=timeout * 1000,
                block_resource_types=playwright_block_resource_types,
            ),
            fallback_to_playwright=fallback_to_playwright,
            site_rule_store=lambda rule: upsert_site_rule(sites_path, rule),
            auto_learn_site_rules=auto_learn_site_rules,
            enable_api_discovery=enable_api_discovery,
            api_timeout=api_timeout,
            api_retries=api_retries,
            public_source_max_workers=public_source_max_workers,
        )
    return PriceCrawlerService(
        db,
        site_rules,
        fetcher=RequestsFetcher(
            timeout=timeout,
            retries=retries,
            delay=delay,
            blocked_status_codes=blocked_status_codes,
        ),
        fallback_to_playwright=fallback_to_playwright,
        site_rule_store=lambda rule: upsert_site_rule(sites_path, rule),
        auto_learn_site_rules=auto_learn_site_rules,
        enable_api_discovery=enable_api_discovery,
        api_timeout=api_timeout,
        api_retries=api_retries,
        public_source_max_workers=public_source_max_workers,
    )


def run_crawl(
    config_path: str,
    sites_path: str,
    db_path: str | None,
    fetch_mode: str | None = None,
    runtime_config: dict | None = None,
) -> None:
    runtime_config = runtime_config or load_runtime_config(RUNTIME_CONFIG_PATH)
    effective_fetch_mode = get_effective_fetch_mode(fetch_mode, runtime_config)
    db = get_db(db_path)
    db.init_db()
    site_rules = load_site_rules(sites_path)
    products = filter_enabled_sources(load_json_config(config_path))
    service = build_crawler_service(db, site_rules, effective_fetch_mode, runtime_config, sites_path)
    results = service.crawl_many(products)
    for item in results:
        print(item)


def run_export(output_path: str, db_path: str | None) -> None:
    db = get_db(db_path)
    history_df = db.get_price_history()
    metrics_df = compute_group_metrics(history_df)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(target, index=False, encoding="utf-8-sig")
    print(f"已导出: {target}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    runtime_config = load_runtime_config(RUNTIME_CONFIG_PATH)

    if args.command == "init-db":
        db = get_db(args.db)
        db.init_db()
        print(f"数据库已初始化: {db.database_label}")
        return

    if args.command == "crawl":
        run_crawl(args.config, args.sites, args.db, args.fetch_mode, runtime_config)
        return

    if args.command == "export":
        run_export(args.output, args.db)
        return

    if args.command == "schedule":
        interval_seconds = get_schedule_interval_seconds(args, runtime_config)
        effective_fetch_mode = get_effective_fetch_mode(args.fetch_mode, runtime_config)
        print(f"定时抓取已启动：每 {interval_seconds} 秒执行一次，抓取方式={effective_fetch_mode}")
        run_interval(
            lambda: run_crawl(args.config, args.sites, args.db, effective_fetch_mode, runtime_config),
            interval_seconds,
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
