from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CAPTURE_PATH = Path("tmp/meicai_capture/meicai_flows.jsonl")


def summarize_capture_paths(capture_path: Path) -> dict[str, Any]:
    if not capture_path.exists():
        raise RuntimeError(f"capture file not found: {capture_path}")
    endpoint_counter: Counter[tuple[str, str, int | None, bool]] = Counter()
    for raw_line in capture_path.read_text(encoding="utf-8-sig").splitlines():
        if not raw_line.strip():
            continue
        record = json.loads(raw_line)
        if not isinstance(record, dict) or record.get("event") != "response":
            continue
        path = str(record.get("path") or "").strip()
        method = str(record.get("method") or "").strip()
        status_code = record.get("status_code") if isinstance(record.get("status_code"), int) else None
        encrypted = response_is_encrypted(record)
        endpoint_counter[(method, path, status_code, encrypted)] += 1
    endpoints = [
        {
            "method": method,
            "path": path,
            "status_code": status_code,
            "encrypted": encrypted,
            "count": count,
        }
        for (method, path, status_code, encrypted), count in endpoint_counter.most_common()
    ]
    return {"capture_path": str(capture_path), "endpoint_count": len(endpoints), "endpoints": endpoints}


def response_is_encrypted(record: dict[str, Any]) -> bool:
    response_text = record.get("response_text")
    if not isinstance(response_text, str) or not response_text.strip():
        return False
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False
    encryption = payload.get("encryption")
    return (
        isinstance(payload.get("data"), str)
        and isinstance(encryption, dict)
        and int(encryption.get("type") or 0) > 1
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize redacted Meicai capture paths without printing bodies.")
    parser.add_argument("--input", "-i", default=str(DEFAULT_CAPTURE_PATH))
    parsed_args = parser.parse_args()

    try:
        report = summarize_capture_paths(Path(parsed_args.input))
    except RuntimeError as exc:
        report = {"ready": False, "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
