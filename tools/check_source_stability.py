from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests
import urllib3
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, SSLError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_loader import load_json_config, resolve_config_path


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

KEYWORDS = ["价格", "行情", "监测", "均价", "最高价", "最低价", "公斤", "元/斤", "元/公斤"]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class ProbeResult:
    name: str
    url: str
    strict_get_ok: bool
    strict_get_status: int | None
    head_status: int | None
    insecure_get_status: int | None
    ssl_error: bool
    blocked: bool
    dynamic_heavy: bool
    has_table: bool
    title: str | None
    content_length: int
    keyword_hits: dict[str, int]
    classification: str
    summary: str


def build_session() -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=8, pool_maxsize=8, pool_block=False)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    return session


def extract_page_features(html: str) -> tuple[str | None, bool, bool, dict[str, int]]:
    soup = BeautifulSoup(html or "", "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    lowered = html.lower()
    has_table = bool(soup.select_one("table, tbody, thead")) or "el-table" in lowered
    dynamic_heavy = any(marker in lowered for marker in ("__next_data__", 'id="app"', "window.__", "vue"))
    keyword_hits = {keyword: len(re.findall(re.escape(keyword), html)) for keyword in KEYWORDS}
    return title, has_table, dynamic_heavy, keyword_hits


def classify_probe(
    *,
    strict_get_ok: bool,
    strict_get_status: int | None,
    head_status: int | None,
    insecure_get_status: int | None,
    ssl_error: bool,
    blocked: bool,
    dynamic_heavy: bool,
    has_table: bool,
    keyword_hits: dict[str, int],
) -> tuple[str, str]:
    if ssl_error:
        return "ssl_issue", "严格 HTTPS 校验失败，当前环境下证书不可信。"
    if blocked:
        return "blocked", "访问被限制或返回了明显的反爬/拒绝状态。"
    if not strict_get_ok:
        return "flaky", "基础 GET 不稳定，当前环境下无法稳定取回页面。"
    if dynamic_heavy:
        return "dynamic_heavy", "页面明显依赖前端脚本或重渲染，后续维护成本较高。"
    if has_table and sum(keyword_hits.values()) >= 4:
        return "stable", "页面可直接访问，且存在较明显的表格/价格文本特征。"
    if strict_get_status == 200 or head_status == 200 or insecure_get_status == 200:
        return "article_reference", "页面可访问，但更像文章/列表页，适合作参考源。"
    return "flaky", "页面表现不稳定，建议继续观察后再启用。"


def probe_url(name: str, url: str, timeout: int = 20) -> ProbeResult:
    session = build_session()
    strict_get_ok = False
    strict_get_status: int | None = None
    head_status: int | None = None
    insecure_get_status: int | None = None
    ssl_error = False
    blocked = False
    dynamic_heavy = False
    has_table = False
    title: str | None = None
    content_length = 0
    keyword_hits: dict[str, int] = {keyword: 0 for keyword in KEYWORDS}

    try:
        head_response = session.head(url, timeout=timeout, allow_redirects=True)
        head_status = head_response.status_code
        if head_status in {401, 403, 429}:
            blocked = True
    except RequestException:
        head_status = None

    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        strict_get_status = response.status_code
        strict_get_ok = response.ok
        blocked = blocked or response.status_code in {401, 403, 429}
        if response.text:
            content_length = len(response.text)
            title, has_table, dynamic_heavy, keyword_hits = extract_page_features(response.text)
    except SSLError:
        ssl_error = True
        try:
            insecure_response = session.get(url, timeout=timeout, allow_redirects=True, verify=False)
            insecure_get_status = insecure_response.status_code
            blocked = blocked or insecure_response.status_code in {401, 403, 429}
            if insecure_response.text:
                content_length = len(insecure_response.text)
                title, has_table, dynamic_heavy, keyword_hits = extract_page_features(insecure_response.text)
        except RequestException:
            insecure_get_status = None
    except RequestException as exc:
        strict_get_status = getattr(getattr(exc, "response", None), "status_code", None)
        blocked = blocked or strict_get_status in {401, 403, 429}

    classification, summary = classify_probe(
        strict_get_ok=strict_get_ok,
        strict_get_status=strict_get_status,
        head_status=head_status,
        insecure_get_status=insecure_get_status,
        ssl_error=ssl_error,
        blocked=blocked,
        dynamic_heavy=dynamic_heavy,
        has_table=has_table,
        keyword_hits=keyword_hits,
    )
    return ProbeResult(
        name=name,
        url=url,
        strict_get_ok=strict_get_ok,
        strict_get_status=strict_get_status,
        head_status=head_status,
        insecure_get_status=insecure_get_status,
        ssl_error=ssl_error,
        blocked=blocked,
        dynamic_heavy=dynamic_heavy,
        has_table=has_table,
        title=title,
        content_length=content_length,
        keyword_hits=keyword_hits,
        classification=classification,
        summary=summary,
    )


def load_targets(products_path: str, names: list[str] | None = None) -> list[tuple[str, str]]:
    products = load_json_config(resolve_config_path(products_path))
    selected: list[tuple[str, str]] = []
    wanted = {name.strip() for name in names or [] if name.strip()}
    for item in products:
        source_name = str(item.get("source_name") or item.get("product_name") or "").strip()
        url = str(item.get("url") or "").strip()
        if not source_name or not url:
            continue
        if wanted and source_name not in wanted:
            continue
        selected.append((source_name, url))
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description="检查来源页面稳定性")
    parser.add_argument("--config", default="config/products.json", help="来源配置文件路径")
    parser.add_argument("--source", action="append", help="只检查指定来源名称，可重复传入")
    parser.add_argument("--timeout", type=int, default=20, help="请求超时时间（秒）")
    args = parser.parse_args()

    targets = load_targets(args.config, args.source)
    results = [asdict(probe_url(name, url, timeout=args.timeout)) for name, url in targets]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
