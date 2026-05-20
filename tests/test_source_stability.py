from tools.check_source_stability import classify_probe, extract_page_features


def test_extract_page_features_detects_table_and_keywords():
    html = """
    <html>
      <head><title>价格监测</title></head>
      <body>
        <table><tr><td>均价</td><td>元/公斤</td></tr></table>
      </body>
    </html>
    """

    title, has_table, dynamic_heavy, keyword_hits = extract_page_features(html)

    assert title == "价格监测"
    assert has_table is True
    assert dynamic_heavy is False
    assert keyword_hits["均价"] == 1
    assert keyword_hits["元/公斤"] == 1


def test_classify_probe_marks_ssl_issue_first():
    classification, summary = classify_probe(
        strict_get_ok=False,
        strict_get_status=None,
        head_status=None,
        insecure_get_status=403,
        ssl_error=True,
        blocked=True,
        dynamic_heavy=False,
        has_table=False,
        keyword_hits={"价格": 0},
    )

    assert classification == "ssl_issue"
    assert "证书" in summary


def test_classify_probe_marks_dynamic_heavy():
    classification, summary = classify_probe(
        strict_get_ok=True,
        strict_get_status=200,
        head_status=200,
        insecure_get_status=None,
        ssl_error=False,
        blocked=False,
        dynamic_heavy=True,
        has_table=False,
        keyword_hits={"价格": 10, "行情": 4},
    )

    assert classification == "dynamic_heavy"
    assert "前端脚本" in summary


def test_classify_probe_marks_stable_when_table_and_keywords_exist():
    classification, summary = classify_probe(
        strict_get_ok=True,
        strict_get_status=200,
        head_status=200,
        insecure_get_status=None,
        ssl_error=False,
        blocked=False,
        dynamic_heavy=False,
        has_table=True,
        keyword_hits={"价格": 2, "监测": 1, "均价": 1, "元/公斤": 1},
    )

    assert classification == "stable"
    assert "表格" in summary
