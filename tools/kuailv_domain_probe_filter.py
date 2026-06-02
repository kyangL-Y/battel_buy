from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from mitmproxy import http


OUTPUT_DIR = Path("E:/battel/tmp/kuailv_capture")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "kuailv_domain_probe.jsonl"
HOST_KEYWORDS = (
    "kuailv",
    "klmall",
    "meituan",
    "sankuai",
    "dianping",
    "waimai",
)


def request(flow: http.HTTPFlow) -> None:
    host = (flow.request.pretty_host or "").lower()
    if not any(keyword in host for keyword in HOST_KEYWORDS):
        return
    parsed_url = urlparse(flow.request.pretty_url)
    payload = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "method": flow.request.method,
        "scheme": parsed_url.scheme,
        "host": flow.request.pretty_host,
        "path": parsed_url.path,
        "query_keys": sorted(key for key in flow.request.query.keys()),
    }
    with OUTPUT_FILE.open("a", encoding="utf-8") as output_file:
        output_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
