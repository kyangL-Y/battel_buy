from __future__ import annotations

import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from api.deps import clear_dataframe_cache, get_db
from crawler.fetcher import PriceCrawlerService
from crawler.playwright_fetcher import PlaywrightFetcher
from crawler.requests_fetcher import RequestsFetcher
from services.site_rule_registry import load_site_rules, upsert_site_rule
from utils.config_loader import BASE_DIR, load_json_config, load_runtime_config, save_runtime_config
from utils.source_config import filter_enabled_sources, filter_sources_by_region, get_source_name


RUNTIME_CONFIG_PATH = BASE_DIR / "config" / "runtime.json"
PRODUCTS_CONFIG_PATH = BASE_DIR / "config" / "products.json"
SITES_CONFIG_PATH = BASE_DIR / "config" / "sites.json"


def _now() -> datetime:
    return datetime.now().astimezone()


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat(timespec="seconds")


def _safe_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _normalize_schedule_mode(value: Any) -> str:
    normalized = str(value or "").strip()
    return normalized if normalized in {"interval", "daily_time"} else "interval"


def _normalize_daily_run_time(value: Any, default: str = "03:30") -> str:
    text = str(value or "").strip()
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (TypeError, ValueError):
        return default
    if 0 <= hour <= 23 and 0 <= minute <= 59 and len(hour_text) == 2 and len(minute_text) == 2:
        return f"{hour:02d}:{minute:02d}"
    return default


def _next_daily_run_at(now: datetime, run_time: str) -> datetime:
    normalized_time = _normalize_daily_run_time(run_time)
    hour, minute = (int(part) for part in normalized_time.split(":", 1))
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def build_crawler_service(fetch_mode: str, runtime_settings: dict[str, Any]) -> PriceCrawlerService:
    crawler_config = runtime_settings.get("crawler", {})
    timeout = _safe_int(crawler_config.get("default_timeout"), 15)
    retries = _safe_int(crawler_config.get("default_retries"), 2)
    delay = float(crawler_config.get("default_delay") or 1.0)
    blocked_status_codes = crawler_config.get("blocked_status_codes", [403, 429])
    fallback_to_playwright = bool(crawler_config.get("fallback_to_playwright", False))
    auto_learn_site_rules = bool(crawler_config.get("auto_learn_site_rules", True))
    enable_api_discovery = bool(crawler_config.get("enable_api_discovery", False))
    api_timeout = _safe_int(crawler_config.get("api_timeout"), timeout)
    api_retries = _safe_int(crawler_config.get("api_retries"), 1)
    public_source_max_workers = _safe_int(crawler_config.get("public_source_max_workers"), 1)
    playwright_block_resource_types = tuple(
        crawler_config.get("playwright_block_resource_types", ["image", "media", "font"])
        or ["image", "media", "font"]
    )
    site_rules = load_site_rules(SITES_CONFIG_PATH)

    if fetch_mode == "playwright":
        fetcher = PlaywrightFetcher(
            timeout_ms=timeout * 1000,
            block_resource_types=playwright_block_resource_types,
        )
    else:
        fetcher = RequestsFetcher(
            timeout=timeout,
            retries=retries,
            delay=delay,
            blocked_status_codes=blocked_status_codes,
        )

    return PriceCrawlerService(
        get_db(),
        site_rules,
        fetcher=fetcher,
        fallback_to_playwright=fallback_to_playwright,
        site_rule_store=lambda rule: upsert_site_rule(SITES_CONFIG_PATH, rule),
        auto_learn_site_rules=auto_learn_site_rules,
        enable_api_discovery=enable_api_discovery,
        api_timeout=api_timeout,
        api_retries=api_retries,
        public_source_max_workers=public_source_max_workers,
    )


class CrawlManager:
    def __init__(
        self,
        runtime_path: str | Path = RUNTIME_CONFIG_PATH,
        products_path: str | Path = PRODUCTS_CONFIG_PATH,
    ) -> None:
        self.runtime_path = Path(runtime_path)
        self.products_path = Path(products_path)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._scheduler_thread: threading.Thread | None = None
        self._job_thread: threading.Thread | None = None
        self._schedule_signature: tuple[Any, ...] | None = None
        self._next_run_at: datetime | None = None
        self._state: dict[str, Any] = {
            "is_running": False,
            "last_run_source": None,
            "last_started_at": None,
            "last_finished_at": None,
            "last_success_at": None,
            "last_error": "",
            "current_source_name": "",
            "current_source_index": 0,
            "current_source_progress": 0.0,
            "current_source_detail": "",
            "completed_sources": 0,
            "progress_percent": 0,
            "last_total_sources": 0,
            "last_total_results": 0,
            "last_success_count": 0,
            "last_failed_count": 0,
            "target_scope": "all_saved",
            "target_province": None,
            "target_city": None,
        }

    def start(self) -> None:
        with self._lock:
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                return
            self._stop_event.clear()
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name="crawl-scheduler",
                daemon=True,
            )
            self._scheduler_thread.start()

    def shutdown(self) -> None:
        self._stop_event.set()

    def get_status(self) -> dict[str, Any]:
        runtime_settings = load_runtime_config(self.runtime_path)
        schedule = runtime_settings.get("schedule", {})
        with self._lock:
            state = dict(self._state)
            next_run_at = self._next_run_at
        return {
            "is_running": bool(state["is_running"]),
            "last_run_source": state["last_run_source"],
            "last_started_at": _to_iso(state["last_started_at"]),
            "last_finished_at": _to_iso(state["last_finished_at"]),
            "last_success_at": _to_iso(state["last_success_at"]),
            "last_error": state["last_error"] or None,
            "current_source_name": state["current_source_name"] or None,
            "current_source_index": int(state["current_source_index"] or 0),
            "current_source_progress": round(float(state["current_source_progress"] or 0.0), 4),
            "current_source_detail": state["current_source_detail"] or None,
            "completed_sources": int(state["completed_sources"] or 0),
            "progress_percent": int(state["progress_percent"] or 0),
            "last_total_sources": int(state["last_total_sources"] or 0),
            "last_total_results": int(state["last_total_results"] or 0),
            "last_success_count": int(state["last_success_count"] or 0),
            "last_failed_count": int(state["last_failed_count"] or 0),
            "next_run_at": _to_iso(next_run_at),
            "schedule_enabled": bool(schedule.get("enabled", False)),
            "schedule_mode": _normalize_schedule_mode(schedule.get("mode")),
            "schedule_daily_run_time": _normalize_daily_run_time(schedule.get("daily_run_time")),
            "schedule_interval_seconds": _safe_int(schedule.get("interval_seconds"), 3600),
            "schedule_fetch_mode": str(schedule.get("fetch_mode") or "requests"),
            "schedule_target_scope": str(schedule.get("target_scope") or "all_saved"),
            "schedule_target_province": str(schedule.get("target_province") or "").strip() or None,
            "schedule_target_city": str(schedule.get("target_city") or "").strip() or None,
            "target_scope": str(state.get("target_scope") or "all_saved"),
            "target_province": state.get("target_province") or None,
            "target_city": state.get("target_city") or None,
            "target_source_url": state.get("target_source_url") or None,
            "target_source_name": state.get("target_source_name") or None,
        }

    def update_schedule(
        self,
        *,
        enabled: bool | None = None,
        mode: str | None = None,
        daily_run_time: str | None = None,
        interval_seconds: int | None = None,
        fetch_mode: str | None = None,
        target_scope: str | None = None,
        target_province: str | None = None,
        target_city: str | None = None,
    ) -> dict[str, Any]:
        runtime_settings = load_runtime_config(self.runtime_path)
        schedule = dict(runtime_settings.get("schedule", {}))
        if enabled is not None:
            schedule["enabled"] = bool(enabled)
        if mode is not None:
            schedule["mode"] = _normalize_schedule_mode(mode)
        if daily_run_time is not None:
            schedule["daily_run_time"] = _normalize_daily_run_time(daily_run_time)
        if interval_seconds is not None:
            schedule["interval_seconds"] = _safe_int(interval_seconds, 3600)
        if fetch_mode is not None:
            schedule["fetch_mode"] = fetch_mode
        if target_scope is not None:
            schedule["target_scope"] = str(target_scope).strip() or "all_saved"
        if target_province is not None:
            schedule["target_province"] = str(target_province).strip() or None
        if target_city is not None:
            schedule["target_city"] = str(target_city).strip() or None
        runtime_settings["schedule"] = schedule
        save_runtime_config(runtime_settings, self.runtime_path)

        with self._lock:
            self._schedule_signature = None
        return self.get_status()

    def trigger_run(
        self,
        source: str = "manual",
        *,
        target_scope: str | None = None,
        target_province: str | None = None,
        target_city: str | None = None,
        source_url: str | None = None,
        source_name: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        with self._lock:
            if self._state["is_running"]:
                return False, self.get_status()

            started_at = _now()
            self._state.update(
                {
                    "is_running": True,
                    "last_run_source": source,
                    "last_started_at": started_at,
                    "last_error": "",
                    "current_source_name": "",
                    "current_source_index": 0,
                    "current_source_progress": 0.0,
                    "current_source_detail": "",
                    "completed_sources": 0,
                    "progress_percent": 0,
                    "last_total_sources": 0,
                    "last_total_results": 0,
                    "last_success_count": 0,
                    "last_failed_count": 0,
                    "target_scope": str(target_scope or "all_saved").strip() or "all_saved",
                    "target_province": str(target_province or "").strip() or None,
                    "target_city": str(target_city or "").strip() or None,
                    "target_source_url": str(source_url or "").strip() or None,
                    "target_source_name": str(source_name or "").strip() or None,
                }
            )
            self._job_thread = threading.Thread(
                target=self._run_crawl_job,
                args=(
                    source,
                    self._state["target_scope"],
                    self._state["target_province"],
                    self._state["target_city"],
                    self._state["target_source_url"],
                    self._state["target_source_name"],
                ),
                name=f"crawl-job-{source}",
                daemon=True,
            )
            self._job_thread.start()
        return True, self.get_status()

    def _scheduler_loop(self) -> None:
        while not self._stop_event.is_set():
            runtime_settings = load_runtime_config(self.runtime_path)
            schedule = runtime_settings.get("schedule", {})
            enabled = bool(schedule.get("enabled", False))
            mode = _normalize_schedule_mode(schedule.get("mode"))
            daily_run_time = _normalize_daily_run_time(schedule.get("daily_run_time"))
            interval_seconds = _safe_int(schedule.get("interval_seconds"), 3600)
            fetch_mode = str(schedule.get("fetch_mode") or "requests")
            target_scope = str(schedule.get("target_scope") or "all_saved")
            target_province = str(schedule.get("target_province") or "").strip() or None
            target_city = str(schedule.get("target_city") or "").strip() or None
            signature = (enabled, mode, daily_run_time, interval_seconds, fetch_mode, target_scope, target_province, target_city)

            with self._lock:
                if signature != self._schedule_signature:
                    self._schedule_signature = signature
                    now = _now()
                    self._next_run_at = (
                        _next_daily_run_at(now, daily_run_time)
                        if enabled and mode == "daily_time"
                        else now + timedelta(seconds=interval_seconds)
                        if enabled
                        else None
                    )
                is_running = bool(self._state["is_running"])
                next_run_at = self._next_run_at

            if enabled and not is_running and next_run_at and _now() >= next_run_at:
                self.trigger_run(
                    "schedule",
                    target_scope=target_scope,
                    target_province=target_province,
                    target_city=target_city,
                )

            self._stop_event.wait(1.0)

    def _run_crawl_job(
        self,
        source: str,
        target_scope: str = "all_saved",
        target_province: str | None = None,
        target_city: str | None = None,
        target_source_url: str | None = None,
        target_source_name: str | None = None,
    ) -> None:
        started_at = _now()
        last_error = ""
        success_count = 0
        failed_count = 0
        total_results = 0
        total_sources = 0

        try:
            products = load_json_config(self.products_path)
            if not isinstance(products, list):
                raise ValueError("config/products.json 格式错误，应为数组。")
            products = filter_sources_by_region(
                products,
                province=target_province,
                city=target_city,
                target_scope=target_scope,
            )
            if target_source_url:
                products = [
                    item for item in products
                    if str(item.get("url") or "").strip() == str(target_source_url).strip()
                ]
            elif target_source_name:
                normalized_target_name = str(target_source_name).strip()
                products = [
                    item for item in products
                    if get_source_name(item, fallback="").strip() == normalized_target_name
                ]
            total_sources = len(products)
            if total_sources <= 0:
                raise ValueError("未找到可执行的来源配置")
            runtime_settings = load_runtime_config(self.runtime_path)
            fetch_mode = str(runtime_settings.get("schedule", {}).get("fetch_mode") or "requests")
            service = build_crawler_service(fetch_mode, runtime_settings)
            with self._lock:
                self._state["last_total_sources"] = total_sources
            service.set_progress_callback(self._make_progress_callback(total_sources))
            for index, product in enumerate(products, start=1):
                source_name = get_source_name(product, fallback=f"来源 {index}")
                with self._lock:
                    self._state["current_source_name"] = source_name
                    self._state["current_source_index"] = index
                    self._state["current_source_progress"] = 0.0
                    self._state["current_source_detail"] = "准备抓取"
                    self._refresh_progress_locked(total_sources)
                results = service.crawl_source(product)
                batch_success_count = len([item for item in results if item.get("status") == "success"])
                total_results += len(results)
                success_count += batch_success_count
                failed_count += len(results) - batch_success_count
                completed_sources = index
                with self._lock:
                    self._state["completed_sources"] = completed_sources
                    self._state["current_source_progress"] = 0.0
                    self._state["current_source_detail"] = f"已完成 {completed_sources}/{total_sources} 个报价源"
                    self._refresh_progress_locked(total_sources)
                    self._state["last_total_results"] = total_results
                    self._state["last_success_count"] = success_count
                    self._state["last_failed_count"] = failed_count
            clear_dataframe_cache()
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        finally:
            finished_at = _now()
            runtime_settings = load_runtime_config(self.runtime_path)
            schedule = runtime_settings.get("schedule", {})
            mode = _normalize_schedule_mode(schedule.get("mode"))
            daily_run_time = _normalize_daily_run_time(schedule.get("daily_run_time"))
            interval_seconds = _safe_int(schedule.get("interval_seconds"), 3600)
            with self._lock:
                self._state.update(
                    {
                        "is_running": False,
                        "last_run_source": source,
                        "last_started_at": started_at,
                        "last_finished_at": finished_at,
                        "last_success_at": finished_at if not last_error else self._state.get("last_success_at"),
                        "last_error": last_error,
                        "current_source_name": "",
                        "current_source_index": 0,
                        "current_source_progress": 0.0,
                        "current_source_detail": "",
                        "completed_sources": total_sources if not last_error else self._state.get("completed_sources", 0),
                        "progress_percent": 100 if total_sources and not last_error else self._state.get("progress_percent", 0),
                        "last_total_sources": total_sources,
                        "last_total_results": total_results,
                        "last_success_count": success_count,
                        "last_failed_count": failed_count,
                    }
                )
                self._next_run_at = (
                    _next_daily_run_at(finished_at, daily_run_time)
                    if bool(schedule.get("enabled", False)) and mode == "daily_time"
                    else finished_at + timedelta(seconds=interval_seconds)
                    if bool(schedule.get("enabled", False))
                    else None
                )

    def _make_progress_callback(self, total_sources: int):
        def update(payload: dict[str, Any]) -> None:
            progress = payload.get("progress")
            detail = str(payload.get("detail") or "").strip()
            with self._lock:
                if progress is not None:
                    try:
                        self._state["current_source_progress"] = min(max(float(progress), 0.0), 0.999)
                    except (TypeError, ValueError):
                        pass
                if detail:
                    self._state["current_source_detail"] = detail
                self._refresh_progress_locked(total_sources)

        return update

    def _refresh_progress_locked(self, total_sources: int) -> None:
        if total_sources <= 0:
            self._state["progress_percent"] = 0
            return
        completed_sources = int(self._state.get("completed_sources") or 0)
        current_source_progress = float(self._state.get("current_source_progress") or 0.0)
        overall_progress = (completed_sources + min(max(current_source_progress, 0.0), 0.999)) / total_sources
        self._state["progress_percent"] = int(round(min(max(overall_progress, 0.0), 1.0) * 100))
