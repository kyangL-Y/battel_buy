from __future__ import annotations

import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter

from crawler.base import BaseFetcher, FetchResult
from crawler.http_utils import without_proxy_env
from utils.logger import setup_logger


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class RequestsFetcher(BaseFetcher):
    def __init__(
        self,
        timeout: int = 15,
        retries: int = 2,
        delay: float = 1.0,
        headers: dict[str, str] | None = None,
        blocked_status_codes: list[int] | None = None,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.headers = headers or DEFAULT_HEADERS
        self.blocked_status_codes = blocked_status_codes or [403, 429]
        self.logger = setup_logger()
        self.session = self._build_session()

    @staticmethod
    def _build_proxy_bypass() -> dict[str, None]:
        return {"http": None, "https": None}

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=8, pool_maxsize=8, pool_block=False)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _request_once(self, url: str) -> requests.Response:
        with without_proxy_env():
            return self.session.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                proxies=self._build_proxy_bypass(),
            )

    def fetch(self, url: str) -> FetchResult:
        last_error = None
        last_status_code = None
        last_metadata: dict[str, Any] = {
            "fetch_mode": "requests",
            "timeout": self.timeout,
            "retries": self.retries,
            "delay": self.delay,
            "blocked_status_codes": self.blocked_status_codes,
        }
        for attempt in range(1, self.retries + 2):
            try:
                response = self._request_once(url)
                last_status_code = response.status_code
                blocked_hint = response.status_code in set(self.blocked_status_codes)
                suggestion = None
                if blocked_hint:
                    suggestion = "目标站点可能有限频或反爬限制，建议降低抓取频率、拉长请求间隔，或切换 Playwright 动态抓取。"
                    self.logger.warning("访问可能受限: %s | 状态码=%s", url, response.status_code)
                response.raise_for_status()
                return FetchResult(
                    url=url,
                    status_code=response.status_code,
                    html=response.text,
                    metadata={
                        **last_metadata,
                        "headers": dict(response.headers),
                        "attempt": attempt,
                        "blocked_hint": blocked_hint,
                        "suggestion": suggestion,
                    },
                )
            except requests.RequestException as exc:
                response = getattr(exc, "response", None)
                if response is not None:
                    last_status_code = response.status_code
                last_error = str(exc)
                blocked_hint = last_status_code in set(self.blocked_status_codes)
                error_text = last_error.lower()
                if "proxyerror" in error_text or "proxy" in error_text:
                    suggestion = "检测到代理连接异常，请检查系统代理、pip/requests 代理配置，或临时关闭代理后重试。"
                else:
                    suggestion = (
                        "目标站点可能有限频或反爬限制，建议降低抓取频率、拉长请求间隔，或切换 Playwright 动态抓取。"
                        if blocked_hint
                        else "请检查网络连通性、页面结构、站点规则或适当延长超时。"
                    )
                last_metadata = {
                    **last_metadata,
                    "attempt": attempt,
                    "blocked_hint": blocked_hint,
                    "suggestion": suggestion,
                }
                self.logger.error(
                    "抓取失败: %s | 第 %s 次尝试 | 状态码=%s | 错误=%s",
                    url,
                    attempt,
                    last_status_code,
                    last_error,
                )
                if attempt <= self.retries:
                    time.sleep(self.delay)

        return FetchResult(
            url=url,
            status_code=last_status_code,
            html=None,
            error=last_error,
            metadata=last_metadata,
        )

    def close(self) -> None:
        self.session.close()
