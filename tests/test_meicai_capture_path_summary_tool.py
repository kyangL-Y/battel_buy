from __future__ import annotations

import json

from tools.summarize_meicai_capture_paths import summarize_capture_paths


def test_summarize_capture_paths_counts_response_endpoints(tmp_path):
    capture_path = tmp_path / "meicai_flows.jsonl"
    capture_path.write_text(
        "\n".join(
            [
                json.dumps({"event": "request", "method": "POST", "path": "/ignored"}),
                json.dumps(
                    {
                        "event": "response",
                        "method": "POST",
                        "path": "/entrance/dishes/getSpusByClass",
                        "status_code": 200,
                        "response_text": json.dumps({"data": "cipher", "encryption": {"type": 3}}),
                    }
                ),
                json.dumps(
                    {
                        "event": "response",
                        "method": "POST",
                        "path": "/entrance/recommend/xbFeed",
                        "status_code": 200,
                        "response_text": json.dumps({"data": {"rows": []}, "encryption": {"type": 1}}),
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    report = summarize_capture_paths(capture_path)

    assert report["endpoint_count"] == 2
    assert report["endpoints"][0]["path"] == "/entrance/dishes/getSpusByClass"
    assert report["endpoints"][0]["encrypted"] is True
    assert report["endpoints"][1]["path"] == "/entrance/recommend/xbFeed"
    assert report["endpoints"][1]["encrypted"] is False
