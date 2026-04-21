from __future__ import annotations

from crawler.base import BaseFetcher, FetchResult
from utils.logger import setup_logger

logger = setup_logger()


class PlaywrightFetcher(BaseFetcher):
    """基于 Playwright 的动态页面抓取器，适用于依赖 JavaScript 渲染的页面。

    使用前需安装：
        pip install playwright
        playwright install chromium
    """

    def __init__(
        self,
        timeout_ms: int = 20000,
        headless: bool = True,
        wait_until: str = "networkidle",
        capture_json_responses: bool = True,
        max_captured_responses: int = 8,
        block_resource_types: tuple[str, ...] = ("image", "media", "font"),
    ) -> None:
        self.timeout_ms = timeout_ms
        self.headless = headless
        self.wait_until = wait_until
        self.capture_json_responses = capture_json_responses
        self.max_captured_responses = max_captured_responses
        self.block_resource_types = tuple(block_resource_types)

    def fetch(self, url: str) -> FetchResult:
        try:
            from playwright.sync_api import Error as PlaywrightError, sync_playwright  # 延迟导入，避免未安装时报错
        except ImportError:
            return FetchResult(
                url=url,
                status_code=None,
                html=None,
                error="playwright 未安装，请执行: pip install playwright && playwright install chromium",
                metadata={
                    "suggestion": "请先安装 Playwright Python 包，并执行浏览器安装命令后再重试动态抓取。",
                },
            )

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                )
                if self.block_resource_types:
                    def handle_route(route) -> None:
                        if route.request.resource_type in self.block_resource_types:
                            route.abort("blockedbyclient")
                            return
                        route.continue_()

                    context.route("**/*", handle_route)
                page = context.new_page()
                network_candidates: list[dict] = []

                if self.capture_json_responses:
                    def handle_response(response) -> None:
                        try:
                            request = response.request
                            if request.resource_type not in {"xhr", "fetch"}:
                                return
                            content_type = response.headers.get("content-type", "")
                            if "json" not in content_type.lower():
                                return
                            if len(network_candidates) >= self.max_captured_responses:
                                return
                            json_body = response.json()
                            network_candidates.append(
                                {
                                    "url": response.url,
                                    "method": request.method,
                                    "status": response.status,
                                    "content_type": content_type,
                                    "json_body": json_body,
                                }
                            )
                        except Exception:
                            return

                    page.on("response", handle_response)
                response = page.goto(
                    url,
                    timeout=self.timeout_ms,
                    wait_until=self.wait_until,
                )
                status_code = response.status if response else None
                html = page.content()
                browser.close()

            logger.info("Playwright 抓取成功: %s | status=%s", url, status_code)
            return FetchResult(
                url=url,
                status_code=status_code,
                html=html,
                metadata={
                    "network_candidates": network_candidates,
                    "blocked_resource_types": list(self.block_resource_types),
                },
            )

        except PlaywrightError as exc:
            error_text = str(exc)
            logger.error("Playwright 抓取失败: %s | %s", url, error_text)
            suggestion = "请检查页面是否可访问、是否被站点拦截，或调整等待策略后重试。"
            if "Executable doesn't exist" in error_text or "browserType.launch" in error_text:
                suggestion = "未检测到 Playwright 浏览器，请执行: py -3.8 -m playwright install chromium"
            return FetchResult(
                url=url,
                status_code=None,
                html=None,
                error=error_text,
                metadata={"suggestion": suggestion},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Playwright 抓取失败: %s | %s", url, exc)
            return FetchResult(
                url=url,
                status_code=None,
                html=None,
                error=str(exc),
                metadata={"suggestion": "请检查动态页面依赖、网络状态或 Playwright 安装是否完整。"},
            )
