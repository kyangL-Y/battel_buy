import subprocess

from crawler.public_source_crawlers import PublicSourceCrawler


def test_extract_chinaprice_row_parses_summary_html():
    crawler = PublicSourceCrawler()
    payload = {
        "fhxx": (
            "<tr>"
            "<td>大白菜</td>"
            "<td>全国</td>"
            "<td>元/500克</td>"
            "<td>2025-12-31</td>"
            "<td>全国</td>"
            "<td>总平均价</td>"
            "<td>1.07</td>"
            "</tr>"
        )
    }
    item = {"canonical_name": "白菜", "category": "蔬菜类"}

    result = crawler.extract_chinaprice_row(payload, item)

    assert result is not None
    assert result["site_name"] == "Chinaprice | 总平均价"
    assert result["product_name"] == "白菜"
    assert result["current_price"] == 1.07
    assert result["extra_fields"]["spec_text"] == "元/500克"
    assert result["extra_fields"]["region_label"] == "全国"


def test_build_pfsc_rows_expands_markets():
    crawler = PublicSourceCrawler()
    chart_data = {
        "date": "2026-04-06",
        "x": ["北京新发地", "河南万邦"],
        "y": ["1.50", "1.20"],
    }
    item = {"canonical_name": "白菜", "category": "蔬菜类"}

    result = crawler.build_pfsc_rows(chart_data, item)

    assert len(result) == 2
    assert result[0]["site_name"] == "PFSC | 北京新发地"
    assert result[1]["site_name"] == "PFSC | 河南万邦"
    assert result[0]["extra_fields"]["spec_text"] == "公斤"
    assert result[0]["extra_fields"]["province"] == "北京市"


def test_extract_chinaprice_rows_supports_multiple_rows():
    crawler = PublicSourceCrawler()
    payload = {
        "fhxx": (
            "<tr><td>大白菜</td><td>全国</td><td>元/500克</td><td>2025-12-31</td><td>全国</td><td>总平均价</td><td>1.07</td></tr>"
            "<tr><td>大白菜</td><td>北京</td><td>元/500克</td><td>2025-12-31</td><td>北京</td><td>新发地</td><td>1.20</td></tr>"
        )
    }
    item = {"canonical_name": "白菜", "category": "蔬菜类"}

    result = crawler.extract_chinaprice_rows(payload, item)

    assert len(result) == 2
    assert result[0]["site_name"] == "Chinaprice | 总平均价"
    assert result[1]["site_name"] == "Chinaprice | 新发地"


def test_extract_chinaprice_rows_handles_unclosed_tr_markup():
    crawler = PublicSourceCrawler()
    payload = {
        "fhxx": (
            "<tr><td>鲜猪肉</td><td>精瘦肉</td><td>元/500克</td><td>20260325</td><td>全国</td><td>集市</td><td>14.49</td>"
            "<tr><td>鲜猪肉</td><td>精瘦肉</td><td>元/500克</td><td>20260325</td><td>全国</td><td>超市</td><td>14.83</td>"
            "<tr><td>鲜猪肉</td><td>精瘦肉</td><td>元/500克</td><td>20260325</td><td>全国</td><td>总平均价</td><td>14.65</td>"
        )
    }
    item = {
        "canonical_name": "鲜猪肉（精瘦肉）",
        "category": "肉禽蛋",
        "menu_name": "肉禽蛋汇总价格",
        "tree_label": "食品（全国-省）汇总树",
    }

    result = crawler.extract_chinaprice_rows(payload, item)

    assert len(result) == 3
    assert result[0]["site_name"] == "Chinaprice | 集市 | 肉禽蛋汇总价格 | 食品（全国-省）汇总树"
    assert result[1]["site_name"] == "Chinaprice | 超市 | 肉禽蛋汇总价格 | 食品（全国-省）汇总树"
    assert result[2]["site_name"] == "Chinaprice | 总平均价 | 肉禽蛋汇总价格 | 食品（全国-省）汇总树"


def test_parse_chinaprice_items_supports_auto_discovery():
    crawler = PublicSourceCrawler()
    html = """
    <script>
    var vm1 =  new Vue({
        el:'#vm1',
        data:{
            options:[{"id":"cat-1","label":"蔬菜类","children":[{"id":"a1","label":"大白菜-新鲜一级-元/500克"},{"id":"a2","label":"洋葱(元葱)-新鲜一级-元/500克"}]}],
            value:[]
        }
    })
    </script>
    """

    result = crawler.parse_chinaprice_items(html)

    assert len(result) == 2
    assert result[0]["canonical_name"] == "白菜"
    assert result[0]["source_name"] == "大白菜"
    assert result[1]["canonical_name"] == "洋葱"
    assert result[1]["category"] == "蔬菜类"


def test_parse_chinaprice_items_disambiguates_duplicate_canonical_names():
    crawler = PublicSourceCrawler()
    html = """
    <script>
    var vm1 =  new Vue({
        el:'#vm1',
        data:{
            options:[{"id":"cat-1","label":"肉禽蛋","children":[
                {"id":"a1","label":"鲜猪肉-精瘦肉-元/500克"},
                {"id":"a2","label":"鲜猪肉-肋排-元/500克"},
                {"id":"a3","label":"活鸡-元/500克"}
            ]}],
            value:[]
        }
    })
    </script>
    """

    result = crawler.parse_chinaprice_items(html)

    assert [item["canonical_name"] for item in result] == [
        "鲜猪肉（精瘦肉）",
        "鲜猪肉（肋排）",
        "活鸡",
    ]


def test_extract_chinaprice_menu_codes_supports_index_discovery():
    html = """
    <script>
    function moreFind(code) {}
    moreFind('syyhzjg');
    moreFind('twphzjg');
    </script>
    <a href="/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg">批发市场食品汇总价格</a>
    """

    result = PublicSourceCrawler._extract_chinaprice_menu_codes(html)

    assert result[:3] == ["syyhzjg", "twphzjg", "pfscsphzjg"]
    assert "sclhzjg" in result


def test_get_chinaprice_queries_uses_discovered_menu_codes(monkeypatch):
    crawler = PublicSourceCrawler()
    product = {"url": "https://www.chinaprice.cn/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg"}

    monkeypatch.setattr(crawler, "discover_chinaprice_menu_codes", lambda: ["twphzjg"])

    def fake_state(menu_code, lanmu="pl", subtask_id=None, tree_id=None):
        return {
            "menu_code": menu_code,
            "menu_name": "调味品汇总价格" if menu_code == "twphzjg" else "批发市场食品汇总价格",
            "subtask_options": [{"id": "task-1", "label": "旬报", "selected": True}],
            "tree_options": [{"id": "tree-1", "label": "全国树", "selected": True}],
            "current_subtask_id": "task-1",
            "current_subtask_label": "旬报",
            "current_tree_id": "tree-1",
            "current_tree_label": "全国树",
            "area_id": "3435",
            "area_child_ids": [],
            "area_value": "3435",
            "price_values": ["JIAGE"],
            "items": [
                {
                    "canonical_name": f"{menu_code}-商品",
                    "source_name": f"{menu_code}-商品",
                    "category": "测试类",
                    "item_id": f"{menu_code}-item",
                    "spec_text": "元/500克",
                }
            ],
        }

    monkeypatch.setattr(crawler, "get_chinaprice_page_state", fake_state)

    result = crawler.get_chinaprice_queries(product)

    assert {(item["menu_code"], item["item"]["item_id"]) for item in result} == {
        ("twphzjg", "twphzjg-item"),
        ("pfscsphzjg", "pfscsphzjg-item"),
    }


def test_parse_chinaprice_page_state_supports_multi_tree_pages():
    crawler = PublicSourceCrawler()
    html = """
    <select id="subtask">
        <option value="d4-task" selected="selected">城市居民食品价格监测旬报</option>
    </select>
    <select id="tree">
        <option value="tree-a" selected="selected">食品（全国-省）汇总树</option>
        <option value="tree-b">食品（36大中城市）汇总树</option>
    </select>
    <input type="checkbox" name="jg" value="JIAGE" />
    <script>
    var vm =  new Vue({
        el:'#area',
        data:{
            options:[{"id":"3435","label":"全国","children":[{"id":"2","label":"北京市"}]}]
        }
    })
    var vm1 =  new Vue({
        el:'#pz',
        data:{
            options:[{"id":"cat-1","label":"蔬菜类","children":[{"id":"a1","label":"大白菜-新鲜一级-元/500克"}]}],
            value:[]
        }
    })
    </script>
    <script type="text/javascript">
    var menuname='蔬菜类汇总价格';
    </script>
    """

    result = crawler.parse_chinaprice_page_state(html, menu_code="sclhzjg")

    assert result["menu_name"] == "蔬菜类汇总价格"
    assert result["current_subtask_id"] == "d4-task"
    assert result["current_tree_id"] == "tree-a"
    assert result["area_id"] == "3435"
    assert result["area_child_ids"] == ["2"]
    assert result["area_value"] == "3435"
    assert result["price_values"] == ["JIAGE"]
    assert len(result["items"]) == 1
    assert result["items"][0]["canonical_name"] == "白菜"


def test_resolve_chinaprice_area_value_uses_children_for_36_city_tree():
    result = PublicSourceCrawler._resolve_chinaprice_area_value(
        {
            "current_tree_label": "食品（36大中城市）汇总树",
            "area_id": "3435",
            "area_child_ids": ["2", "23", "45"],
        }
    )

    assert result == "'2','23','45'"


def test_extract_chinaprice_area_child_ids_supports_36_city_root():
    area_options = [
        {
            "id": "root-36",
            "label": "36大中城市",
            "children": [
                {"id": "2", "label": "北京市"},
                {"id": "23", "label": "天津市"},
            ],
        }
    ]

    result = PublicSourceCrawler._extract_chinaprice_area_child_ids(area_options)

    assert result == ["2", "23"]


def test_resolve_pfsc_variety_id_matches_alias():
    variety_map = {
        "大白菜": "1001",
        "猪肉(白条猪)": "1492",
    }

    assert PublicSourceCrawler.resolve_pfsc_variety_id(variety_map, ["白菜", "大白菜"]) == "1001"
    assert PublicSourceCrawler.resolve_pfsc_variety_id(variety_map, ["白条猪", "猪肉(白条猪)"]) == "1492"


def test_parse_pfsc_table_rows_supports_market_rows():
    crawler = PublicSourceCrawler()

    result = crawler.parse_pfsc_table_rows(
        [
            {
                "categoryName": "蔬菜类",
                "productName": "大白菜",
                "priceAvg": 1.23,
                "marketName": "北京新发地",
                "recordDate": "2026-04-06",
                "unit": "公斤",
            }
        ]
    )

    assert len(result) == 1
    assert result[0]["site_name"] == "PFSC | 北京新发地"
    assert result[0]["product_name"] == "白菜"
    assert result[0]["extra_fields"]["compare_key"] == "白菜"
    assert result[0]["extra_fields"]["market_name"] == "北京新发地"


def test_build_moa_wholesale_rows_expands_markets():
    crawler = PublicSourceCrawler()
    chart_data = {
        "date": "2026-04-11",
        "x": ["北京新发地农副产品批发市场信息中心", "河南万邦国际农产品物流股份有限公司"],
        "y": [12.5, 11.7],
    }
    item = {"canonical_name": "白条猪", "category": "家畜", "variety_id": "AL01002001"}

    result = crawler.build_moa_wholesale_rows(chart_data, item)

    assert len(result) == 2
    assert result[0]["site_name"] == "重点农产品平台 | 北京新发地农副产品批发市场信息中心"
    assert result[0]["product_name"] == "白条猪"
    assert result[0]["extra_fields"]["spec_text"] == "公斤"
    assert result[1]["extra_fields"]["market_name"] == "河南万邦国际农产品物流股份有限公司"


def test_decrypt_aes_chart_data_prefers_openssl(monkeypatch):
    crawler = PublicSourceCrawler()
    encrypted_payload = "1234567890abcdefZmFrZS1jaXBoZXI="
    key_text = "1234567890abcdef1234567890abcdef"

    def fake_which(name):
        return {"openssl": "/usr/bin/openssl", "pwsh": "/usr/bin/pwsh"}.get(name)

    def fake_run(command, **kwargs):
        assert command[:4] == ["/usr/bin/openssl", "enc", "-aes-256-cbc", "-d"]
        assert kwargs["input"] == "ZmFrZS1jaXBoZXI=\n"
        assert "-K" in command
        assert "-iv" in command
        return subprocess.CompletedProcess(command, 0, stdout='{"ok":true}\n', stderr="")

    monkeypatch.setattr("crawler.public_source_crawlers.shutil.which", fake_which)
    monkeypatch.setattr("crawler.public_source_crawlers.subprocess.run", fake_run)

    result = crawler.decrypt_aes_chart_data(encrypted_payload, key_text)

    assert result == '{"ok":true}'


def test_decrypt_aes_chart_data_falls_back_to_powershell(monkeypatch):
    crawler = PublicSourceCrawler()
    encrypted_payload = "1234567890abcdefZmFrZS1jaXBoZXI="
    key_text = "1234567890abcdef1234567890abcdef"

    def fake_which(name):
        return {"pwsh": "/usr/bin/pwsh"}.get(name)

    def fake_run(command, **kwargs):
        assert command[:3] == ["/usr/bin/pwsh", "-NoProfile", "-Command"]
        assert kwargs["env"]["PFSC_CIPHER"] == encrypted_payload
        assert key_text in command[3]
        return subprocess.CompletedProcess(command, 0, stdout='{"backend":"pwsh"}\n', stderr="")

    monkeypatch.setattr("crawler.public_source_crawlers.shutil.which", fake_which)
    monkeypatch.setattr("crawler.public_source_crawlers.subprocess.run", fake_run)

    result = crawler.decrypt_aes_chart_data(encrypted_payload, key_text)

    assert result == '{"backend":"pwsh"}'


def test_decrypt_aes_chart_data_requires_available_backend(monkeypatch):
    crawler = PublicSourceCrawler()

    monkeypatch.setattr("crawler.public_source_crawlers.shutil.which", lambda name: None)

    try:
        crawler.decrypt_aes_chart_data("1234567890abcdefZmFrZQ==", "1234567890abcdef1234567890abcdef")
    except RuntimeError as exc:
        assert "openssl / PowerShell" in str(exc)
    else:
        raise AssertionError("expected RuntimeError when no decrypt backend is available")


def test_extract_chinaprice_rows_include_menu_and_tree_labels_in_source():
    crawler = PublicSourceCrawler()
    payload = {
        "fhxx": (
            "<tr>"
            "<td>大白菜</td>"
            "<td>全国</td>"
            "<td>元/500克</td>"
            "<td>2025-12-31</td>"
            "<td>全国</td>"
            "<td>总平均价</td>"
            "<td>1.07</td>"
            "</tr>"
        )
    }
    item = {
        "canonical_name": "白菜",
        "category": "蔬菜类",
        "menu_code": "sclhzjg",
        "menu_name": "蔬菜类汇总价格",
        "subtask_id": "d4-task",
        "subtask_label": "城市居民食品价格监测旬报",
        "tree_id": "tree-a",
        "tree_label": "食品（全国-省）汇总树",
    }

    result = crawler.extract_chinaprice_row(payload, item)

    assert result is not None
    assert result["site_name"] == "Chinaprice | 总平均价 | 蔬菜类汇总价格 | 食品（全国-省）汇总树"
    assert result["extra_fields"]["menu_name"] == "蔬菜类汇总价格"
    assert result["extra_fields"]["tree_label"] == "食品（全国-省）汇总树"
