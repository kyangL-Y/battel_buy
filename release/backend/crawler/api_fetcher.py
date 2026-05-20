from __future__ import annotations

import math
import time
from datetime import datetime
from typing import Any, Callable

import requests
from requests.adapters import HTTPAdapter

from crawler.base import FetchResult
from crawler.http_utils import without_proxy_env
from utils.logger import setup_logger


class ApiFetcher:
    def __init__(
        self,
        timeout: int = 15,
        retries: int = 1,
        delay: float = 0.5,
        headers: dict[str, str] | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.headers = headers or {}
        self.progress_callback = progress_callback
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

    def _request_once(
        self,
        method: str,
        api_url: str,
        headers: dict[str, str] | None,
        body: dict[str, Any] | None,
        timeout: int | float | None = None,
    ) -> requests.Response:
        with without_proxy_env():
            return self.session.request(
                method,
                api_url,
                headers=headers or None,
                json=body if method in {"POST", "PUT", "PATCH"} else None,
                timeout=timeout or self.timeout,
                proxies=self._build_proxy_bypass(),
            )

    def fetch(self, url: str, site_rule: dict, context: dict[str, Any] | None = None) -> FetchResult:
        method = str(site_rule.get("api_method") or "GET").upper()
        headers = dict(self.headers)
        custom_headers = site_rule.get("api_headers") or {}
        if isinstance(custom_headers, dict):
            headers.update(self._render_template(custom_headers, context) or {})

        body = self._render_template(site_rule.get("api_body_template"), context)
        api_url = self._render_template(str(site_rule.get("api_url") or url), context)
        timeout = self._resolve_timeout(site_rule)
        retries = self._resolve_retries(site_rule)
        for attempt in range(1, retries + 2):
            try:
                response = self._request_once(method, api_url, headers, body, timeout=timeout)
                response.raise_for_status()
                json_body = response.json()
                return FetchResult(
                    url=api_url,
                    status_code=response.status_code,
                    html=None,
                    metadata={
                        "fetch_mode": "api",
                        "attempt": attempt,
                        "response_headers": dict(response.headers),
                        "json_body": json_body,
                    },
                )
            except (requests.RequestException, ValueError) as exc:
                self.logger.warning("接口抓取失败: %s | attempt=%s | error=%s", api_url, attempt, exc)
                last_error = str(exc)
        return FetchResult(
            url=api_url,
            status_code=None,
            html=None,
            error=last_error,
            metadata={"fetch_mode": "api", "suggestion": "接口抓取失败，已准备回退页面抓取。"},
        )

    def fetch_all_pages(self, url: str, site_rule: dict, context: dict[str, Any] | None = None) -> list[FetchResult]:
        method = str(site_rule.get("api_method") or "GET").upper()
        headers = dict(self.headers)
        custom_headers = site_rule.get("api_headers") or {}
        if isinstance(custom_headers, dict):
            headers.update(self._render_template(custom_headers, context) or {})

        api_url = self._render_template(str(site_rule.get("api_url") or url), context)
        base_body = self._render_template(site_rule.get("api_body_template"), context)
        if not isinstance(base_body, dict):
            return [self.fetch(url, site_rule, context=context)]

        page_key = "page" if "page" in base_body else ("pageNum" if "pageNum" in base_body else None)
        if page_key is None:
            return [self.fetch(url, site_rule, context=context)]

        limit_key = "limit" if "limit" in base_body else ("pageSize" if "pageSize" in base_body else None)
        page_value = base_body.get(page_key)
        try:
            current_page = int(page_value or 1)
        except (TypeError, ValueError):
            current_page = 1

        results: list[FetchResult] = []
        max_pages = self._resolve_max_pages(site_rule)
        timeout = self._resolve_timeout(site_rule)
        retries = self._resolve_retries(site_rule)
        while len(results) < max_pages:
            request_body = dict(base_body)
            request_body[page_key] = current_page
            page_result = self._fetch_once(method, api_url, headers, request_body, timeout=timeout, retries=retries)
            results.append(page_result)
            json_body = ((page_result.metadata or {}).get("json_body") or {}) if not page_result.error else {}
            paging = json_body.get("data") if isinstance(json_body, dict) else {}
            total_pages = self._resolve_total_pages(paging, request_body, limit_key)
            detail = f"接口分页 {len(results)}/{total_pages}" if total_pages else f"接口分页已抓取 {len(results)} 页"
            self._report_progress(
                completed=len(results),
                total=total_pages,
                detail=detail,
            )
            if page_result.error:
                break

            if not isinstance(paging, dict):
                break

            has_next = paging.get("hasNext")
            if has_next is False:
                break
            if has_next is True:
                current_page += 1
                continue

            page_num = paging.get("pageNum", current_page)
            page_size = paging.get("pageSize", request_body.get(limit_key) if limit_key else None)
            total = paging.get("total")
            try:
                page_num_int = int(page_num)
                page_size_int = int(page_size)
                total_int = int(total)
            except (TypeError, ValueError):
                break
            if page_num_int * page_size_int >= total_int:
                break
            current_page = page_num_int + 1

        if len(results) >= max_pages:
            self.logger.warning("接口分页达到上限后停止: %s | max_pages=%s", api_url, max_pages)

        return results

    def _report_progress(
        self,
        *,
        completed: int,
        total: int | None = None,
        detail: str | None = None,
    ) -> None:
        if not callable(self.progress_callback):
            return
        normalized_total = total if isinstance(total, int) and total > 0 else None
        progress = None
        if normalized_total:
            progress = min(max(completed / normalized_total, 0.0), 1.0)
        self.progress_callback(
            {
                "completed": completed,
                "total": normalized_total,
                "progress": progress,
                "detail": detail,
            }
        )

    @staticmethod
    def _resolve_total_pages(
        paging: Any,
        request_body: dict[str, Any],
        limit_key: str | None,
    ) -> int | None:
        if not isinstance(paging, dict):
            return None
        page_size = paging.get("pageSize", request_body.get(limit_key) if limit_key else None)
        total = paging.get("total")
        try:
            page_size_int = int(page_size)
            total_int = int(total)
        except (TypeError, ValueError):
            return None
        if page_size_int <= 0 or total_int <= 0:
            return None
        return max(1, math.ceil(total_int / page_size_int))

    def _fetch_once(
        self,
        method: str,
        api_url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        timeout: int | float | None = None,
        retries: int | None = None,
    ) -> FetchResult:
        last_error = None
        resolved_retries = self.retries if retries is None else retries
        for attempt in range(1, resolved_retries + 2):
            try:
                response = self._request_once(method, api_url, headers, body, timeout=timeout)
                response.raise_for_status()
                json_body = response.json()
                return FetchResult(
                    url=api_url,
                    status_code=response.status_code,
                    html=None,
                    metadata={
                        "fetch_mode": "api",
                        "attempt": attempt,
                        "response_headers": dict(response.headers),
                        "json_body": json_body,
                    },
                )
            except (requests.RequestException, ValueError) as exc:
                self.logger.warning("接口抓取失败: %s | attempt=%s | error=%s", api_url, attempt, exc)
                last_error = str(exc)
        return FetchResult(
            url=api_url,
            status_code=None,
            html=None,
            error=last_error,
            metadata={"fetch_mode": "api", "suggestion": "接口抓取失败，已准备回退页面抓取。"},
        )

    def close(self) -> None:
        self.session.close()

    def _render_template(self, value: Any, context: dict[str, Any] | None) -> Any:
        if context is None:
            context = {}
        variables = self._build_context(context)
        if isinstance(value, dict):
            return {key: self._render_template(item, variables) for key, item in value.items()}
        if isinstance(value, list):
            return [self._render_template(item, variables) for item in value]
        if not isinstance(value, str):
            return value

        rendered = value
        for key, variable in variables.items():
            rendered = rendered.replace(f"${{{key}}}", str(variable))
            rendered = rendered.replace(f"{{{{{key}}}}}", str(variable))
        return rendered

    @staticmethod
    def _build_context(context: dict[str, Any]) -> dict[str, Any]:
        now_ms = int(time.time() * 1000)
        today_start_ms = int(datetime.combine(datetime.today().date(), datetime.min.time()).timestamp() * 1000)
        yesterday_start_ms = today_start_ms - 24 * 60 * 60 * 1000
        last_7d_start_ms = today_start_ms - 7 * 24 * 60 * 60 * 1000
        merged = dict(context)
        merged.setdefault("now_ms", now_ms)
        merged.setdefault("today_start_ms", today_start_ms)
        merged.setdefault("yesterday_start_ms", yesterday_start_ms)
        merged.setdefault("last_7d_start_ms", last_7d_start_ms)
        return merged

    @staticmethod
    def _resolve_max_pages(site_rule: dict[str, Any]) -> int:
        try:
            max_pages = int(site_rule.get("max_pages") or 200)
        except (TypeError, ValueError):
            return 200
        return max_pages if max_pages > 0 else 200

    def _resolve_timeout(self, site_rule: dict[str, Any]) -> int | float:
        try:
            timeout = float(site_rule.get("timeout_seconds") or self.timeout)
        except (TypeError, ValueError):
            return self.timeout
        return timeout if timeout > 0 else self.timeout

    def _resolve_retries(self, site_rule: dict[str, Any]) -> int:
        try:
            retries = int(site_rule.get("retry_count") if site_rule.get("retry_count") is not None else self.retries)
        except (TypeError, ValueError):
            return self.retries
        return max(0, retries)
