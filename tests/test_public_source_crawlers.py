import subprocess

from crawler.public_source_crawlers import PublicSourceCrawler
from crawler.liancai_h5 import LiancaiCategory


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


def test_get_chinaprice_queries_fast_snapshot_uses_current_page_state(monkeypatch):
    crawler = PublicSourceCrawler()
    product = {"url": "https://www.chinaprice.cn/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg"}

    monkeypatch.setattr(crawler, "discover_chinaprice_menu_codes", lambda: ["twphzjg", "sclhzjg"])

    def fake_state(menu_code, lanmu="pl", subtask_id=None, tree_id=None):
        return {
            "menu_code": menu_code,
            "menu_name": f"{menu_code}-菜单",
            "subtask_options": [
                {"id": "current-task", "label": "当前旬报", "selected": True},
                {"id": "other-task", "label": "其他旬报", "selected": False},
            ],
            "tree_options": [
                {"id": "current-tree", "label": "当前树", "selected": True},
                {"id": "other-tree", "label": "其他树", "selected": False},
            ],
            "current_subtask_id": subtask_id or "current-task",
            "current_subtask_label": "当前旬报",
            "current_tree_id": tree_id or "current-tree",
            "current_tree_label": "当前树",
            "area_id": "3435",
            "area_child_ids": [],
            "area_value": "3435",
            "price_values": ["JIAGE"],
            "items": [
                {
                    "canonical_name": "白菜",
                    "source_name": "白菜",
                    "category": "测试类",
                    "item_id": "item-1",
                    "spec_text": "元/500克",
                }
            ],
        }

    monkeypatch.setattr(crawler, "get_chinaprice_page_state", fake_state)

    result = crawler.get_chinaprice_queries(product, {"chinaprice_query_mode": "fast_snapshot"})

    assert len(result) == 1
    assert result[0]["menu_code"] == "pfscsphzjg"
    assert result[0]["subtask_id"] == "current-task"
    assert result[0]["tree_id"] == "current-tree"


def test_get_chinaprice_queries_menu_snapshot_expands_current_menu_only(monkeypatch):
    crawler = PublicSourceCrawler()
    product = {"url": "https://www.chinaprice.cn/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg"}

    monkeypatch.setattr(crawler, "discover_chinaprice_menu_codes", lambda: ["twphzjg"])

    def fake_state(menu_code, lanmu="pl", subtask_id=None, tree_id=None):
        return {
            "menu_code": menu_code,
            "menu_name": f"{menu_code}-菜单",
            "subtask_options": [
                {"id": "task-a", "label": "旬报A", "selected": True},
                {"id": "task-b", "label": "旬报B", "selected": False},
            ],
            "tree_options": [
                {"id": "tree-a", "label": "树A", "selected": True},
                {"id": "tree-b", "label": "树B", "selected": False},
            ],
            "current_subtask_id": subtask_id or "task-a",
            "current_subtask_label": subtask_id or "旬报A",
            "current_tree_id": tree_id or "tree-a",
            "current_tree_label": tree_id or "树A",
            "area_id": "3435",
            "area_child_ids": [],
            "area_value": "3435",
            "price_values": ["JIAGE"],
            "items": [
                {
                    "canonical_name": f"{subtask_id or 'task-a'}-{tree_id or 'tree-a'}",
                    "source_name": "白菜",
                    "category": "测试类",
                    "item_id": f"{subtask_id or 'task-a'}-{tree_id or 'tree-a'}",
                    "spec_text": "元/500克",
                }
            ],
        }

    monkeypatch.setattr(crawler, "get_chinaprice_page_state", fake_state)

    result = crawler.get_chinaprice_queries(product, {"chinaprice_query_mode": "menu_snapshot"})

    assert {item["menu_code"] for item in result} == {"pfscsphzjg"}
    assert {item["item"]["item_id"] for item in result} == {
        "task-a-tree-a",
        "task-a-tree-b",
        "task-b-tree-a",
        "task-b-tree-b",
    }


def test_get_chinaprice_queries_respects_max_queries(monkeypatch):
    crawler = PublicSourceCrawler()
    product = {"url": "https://www.chinaprice.cn/viewPage/toSummarySearchMore?lanmu=pl&MENUNAME=pfscsphzjg"}

    def fake_state(menu_code, lanmu="pl", subtask_id=None, tree_id=None):
        return {
            "menu_code": menu_code,
            "menu_name": "批发市场食品汇总价格",
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
                    "canonical_name": f"商品-{index}",
                    "source_name": f"商品-{index}",
                    "category": "测试类",
                    "item_id": f"item-{index}",
                    "spec_text": "元/500克",
                }
                for index in range(3)
            ],
        }

    monkeypatch.setattr(crawler, "get_chinaprice_page_state", fake_state)

    result = crawler.get_chinaprice_queries(
        product,
        {
            "chinaprice_query_mode": "fast_snapshot",
            "chinaprice_max_queries": 2,
        },
    )

    assert [item["item"]["item_id"] for item in result] == ["item-0", "item-1"]


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


def test_parse_hnnhgsc_rows_supports_spec_fallback_price():
    crawler = PublicSourceCrawler()
    html = """
    <div id="p_productslist">
      <li class="tab-body">
        <ul>
          <li class="name">尖椒</li>
          <li><span class="atname">品名</span><span class="atvalue">尖椒</span></li>
          <li><span class="atname">产地</span><span class="atvalue">/</span></li>
          <li><span class="atname">规格</span><span class="atvalue">1.8</span></li>
          <li><span class="atname">单位</span><span class="atvalue">/</span></li>
          <li><span class="atname">最高价</span><span class="atvalue"></span></li>
          <li><span class="atname">最低价</span><span class="atvalue"></span></li>
          <li><span class="atname">均价</span><span class="atvalue"></span></li>
        </ul>
      </li>
    </div>
    """

    result = crawler.parse_hnnhgsc_rows(html)

    assert len(result) == 1
    assert result[0]["site_name"] == "河南内黄果蔬城"
    assert result[0]["product_name"] == "尖椒"
    assert result[0]["current_price"] == 1.8
    assert result[0]["extra_fields"]["spec_text"] == "公斤"
    assert "规格字段推断价格" in result[0]["promotion_text"]


def test_build_henan_fgw_rows_uses_latest_price_and_category():
    crawler = PublicSourceCrawler()
    category_items = [
        {"code": "JCSP-ZYSP", "varietyName": "主要食品", "indexPid": "-1"},
        {
            "code": "FHSP-00020",
            "varietyName": " 大白菜",
            "unitName": "元/500克",
            "targetName": "销售价格",
            "indexPid": "JCSP-ZYSP",
            "dataSources": "河南省价格监测中心",
        },
    ]
    price_items = [
        {
            "varietyName": "大白菜",
            "varietyCode": "FHSP-00020",
            "priceList": [
                {"priceDate": "2026-04-24", "price": 0.94},
                {"priceDate": "2026-04-17", "price": 0.99},
            ],
        }
    ]

    result = crawler.build_henan_fgw_rows(price_items, category_items)

    assert len(result) == 1
    assert result[0]["site_name"] == "河南省发改委价格监测 | 全省均价"
    assert result[0]["product_name"] == "白菜"
    assert result[0]["current_price"] == 0.94
    assert result[0]["extra_fields"]["group_name"] == "主要食品"
    assert result[0]["extra_fields"]["market_name"] == "全省均价"


def test_build_henan_fgw_rows_skips_statistical_indicators_and_average_baskets():
    crawler = PublicSourceCrawler()
    category_items = [
        {"code": "JCSP-ZYSP", "varietyName": "主要食品", "indexPid": "-1"},
        {"code": "JCSP-ZLBJ", "varietyName": "猪粮比价", "indexPid": "-1"},
        {
            "code": "FHSP-00020",
            "varietyName": " 大白菜",
            "unitName": "元/500克",
            "targetName": "销售价格",
            "indexPid": "JCSP-ZYSP",
        },
        {
            "code": "FHSP-00045",
            "varietyName": " 11 种蔬菜均价",
            "unitName": "元/500克",
            "targetName": "销售价格",
            "indexPid": "JCSP-ZYSP",
        },
        {
            "code": "JCSP-00551",
            "varietyName": "生猪存栏量月度环比变化率",
            "unitName": "百分比（%）",
            "targetName": "月度变化率",
            "indexPid": "JCSP-ZLBJ",
        },
        {
            "code": "JCSP-00556",
            "varietyName": "全省生猪存栏量",
            "unitName": "万头",
            "targetName": "存栏量",
            "indexPid": "JCSP-ZLBJ",
        },
    ]
    price_items = [
        {"varietyName": "大白菜", "varietyCode": "FHSP-00020", "priceList": [{"priceDate": "2026-05-05", "price": 0.94}]},
        {"varietyName": "11 种蔬菜均价", "varietyCode": "FHSP-00045", "priceList": [{"priceDate": "2026-05-05", "price": 2.18}]},
        {"varietyName": "生猪存栏量月度环比变化率", "varietyCode": "JCSP-00551", "priceList": [{"priceDate": "2026-05-01", "price": -1.9}]},
        {"varietyName": "全省生猪存栏量", "varietyCode": "JCSP-00556", "priceList": [{"priceDate": "2026年一季度末", "price": 4017.89}]},
    ]

    result = crawler.build_henan_fgw_rows(price_items, category_items)

    assert [row["product_name"] for row in result] == ["白菜"]


def test_build_henan_fgw_rows_skips_industrial_and_energy_products():
    crawler = PublicSourceCrawler()
    category_items = [
        {"code": "JCSP-ZYSP", "varietyName": "主要食品", "indexPid": "-1"},
        {"code": "JCSP-DZSP", "varietyName": "大宗商品", "indexPid": "-1"},
        {
            "code": "FHSP-00020",
            "varietyName": " 大白菜",
            "unitName": "元/500克",
            "targetName": "销售价格",
            "indexPid": "JCSP-ZYSP",
        },
        {
            "code": "JCSP-00828",
            "varietyName": "现货动力煤",
            "unitName": "元/吨",
            "targetName": "现货出矿价格",
            "indexPid": "JCSP-DZSP",
        },
        {
            "code": "JCSP-00052",
            "varietyName": "螺纹钢",
            "unitName": "元/吨",
            "targetName": "市场收购价格",
            "indexPid": "JCSP-DZSP",
        },
        {
            "code": "JCSP-YY",
            "varietyName": "原油",
            "unitName": "美元/桶",
            "targetName": "市场价格",
            "indexPid": "JCSP-DZSP",
        },
    ]
    price_items = [
        {"varietyName": "大白菜", "varietyCode": "FHSP-00020", "priceList": [{"priceDate": "2026-05-05", "price": 0.94}]},
        {"varietyName": "现货动力煤", "varietyCode": "JCSP-00828", "priceList": [{"priceDate": "2026-05-05", "price": 600}]},
        {"varietyName": "螺纹钢", "varietyCode": "JCSP-00052", "priceList": [{"priceDate": "2026-05-05", "price": 3300}]},
        {"varietyName": "原油", "varietyCode": "JCSP-YY", "priceList": [{"priceDate": "2026-05-05", "price": 70}]},
    ]

    result = crawler.build_henan_fgw_rows(price_items, category_items)

    assert [row["product_name"] for row in result] == ["白菜"]


def test_parse_zzny_clz_article_parses_weekly_section_prices():
    crawler = PublicSourceCrawler()
    html = """
    <html>
      <head>
        <meta name="ArticleTitle" content="2025年7月份郑州市 生鲜乳、鸡蛋、白羽肉鸡、生猪价格 走势分析" />
        <meta name="PubDate" content="2025-08-04 15:31" />
        <meta name="ContentSource" content="郑州市农业技术推广中心" />
      </head>
      <body>
        <div class="news_content_content">
          <p>生鲜乳</p>
          <p>第1周收购均价为3.04元/公斤、第2周收购均价为3.04元/公斤、第3周收购均价为3.04元/公斤、第4周收购均价为3.03元/公斤。</p>
          <p>鸡蛋</p>
          <p>第1周收购均价为5.20元/公斤、第2周收购均价为5.60元/公斤、第3周收购均价为6.60元/公斤、第4周收购均价为6.26元/公斤。</p>
          <p>免责声明：测试</p>
        </div>
      </body>
    </html>
    """

    result = crawler.parse_zzny_clz_article(html, "https://zzny.zhengzhou.gov.cn/clzxx/9517363.jhtml")

    assert len(result) == 2
    assert result[0]["product_name"] == "生鲜乳"
    assert result[0]["current_price"] == 3.03
    assert result[0]["extra_fields"]["spec_text"] == "元/公斤"
    assert "第4周" in result[0]["promotion_text"]
    assert result[1]["product_name"] == "鸡蛋"
    assert result[1]["current_price"] == 6.26


def test_parse_zzny_clz_article_skips_generic_vegetable_average():
    crawler = PublicSourceCrawler()
    html = """
    <html>
      <head>
        <meta name="ArticleTitle" content="蔬菜周均价八连降  预计近期将反转重回升势" />
        <meta name="PubDate" content="2025-06-13 11:11" />
        <meta name="ContentSource" content="郑州市农业技术推广中心" />
      </head>
      <body>
        <div class="news_content_content">
          <p>本周重点监测的11种蔬菜平均价格为2.34元/公斤，较上周下降0.05元/公斤。</p>
        </div>
      </body>
    </html>
    """

    result = crawler.parse_zzny_clz_article(html, "https://zzny.zhengzhou.gov.cn/clzxx/9389212.jhtml")

    assert result == []


def test_parse_zzny_clz_article_supports_numbered_headings_and_tank_price():
    crawler = PublicSourceCrawler()
    html = """
    <html>
      <head>
        <meta name="ArticleTitle" content="2025年9月份郑州市 斑点叉尾鮰、鲤鱼、大口黑鲈、黄颡 价格走势分析" />
        <meta name="PubDate" content="2025-10-09 11:00" />
      </head>
      <body>
        <div class="news_content_content">
          <p>一、斑点叉尾鮰</p>
          <p>9月份整体平稳，价格约12.5元/千克左右。</p>
          <p>二、鲤鱼</p>
          <p>塘口价格在整个9月份一直处在下行状态，最低塘口价9.6元/千克左右。</p>
        </div>
      </body>
    </html>
    """

    result = crawler.parse_zzny_clz_article(html, "https://zzny.zhengzhou.gov.cn/clzxx/9652743.jhtml")

    assert len(result) == 2
    assert result[0]["product_name"] == "斑点叉尾鮰"
    assert result[0]["current_price"] == 12.5
    assert result[1]["product_name"] == "鲤鱼"
    assert result[1]["current_price"] == 9.6


def test_parse_zzny_clz_article_skips_market_average_fruit_article():
    crawler = PublicSourceCrawler()
    html = """
    <html>
      <head>
        <meta name="ArticleTitle" content="果品市场价格整体微降 本地大樱桃采收结束，收益低于预期 中牟小吊瓜接近尾声，整体价格不甚理想" />
        <meta name="PubDate" content="2025-06-13 10:00" />
      </head>
      <body>
        <div class="news_content_content">
          <p>一、水果市场价格表现</p>
          <p>2025年5月，本月万邦市场果品价格与上月相比基本持平略有下降。根据监测数据，在万邦市场监测的44种常见水果品种，5月份平均价约8.69元/公斤,上月平均价约10.73元/公斤。</p>
        </div>
      </body>
    </html>
    """

    result = crawler.parse_zzny_clz_article(html, "https://zzny.zhengzhou.gov.cn/clzxx/9389144.jhtml")

    assert result == []


def test_parse_zzny_clz_article_skips_market_monitoring_heading():
    crawler = PublicSourceCrawler()
    html = """
    <html>
      <head>
        <meta name="ArticleTitle" content="郑州市菜篮子市场价格监测情况" />
        <meta name="PubDate" content="2026-05-08 11:45" />
      </head>
      <body>
        <div class="news_content_content">
          <p>一、万邦市场价格监测情况</p>
          <p>本周万邦市场价格平均为3.20元/公斤。</p>
        </div>
      </body>
    </html>
    """

    result = crawler.parse_zzny_clz_article(html, "https://zzny.zhengzhou.gov.cn/clzxx/test.jhtml")

    assert result == []


def test_parse_zzny_clz_article_skips_topic_and_reason_headings():
    crawler = PublicSourceCrawler()
    html = """
    <html>
      <head>
        <meta name="ArticleTitle" content="菜篮子信息-市场热点分析" />
        <meta name="PubDate" content="2026-05-08 11:45" />
      </head>
      <body>
        <div class="news_content_content">
          <p>一、市场基本概况</p>
          <p>市场均价为3.20元/公斤。</p>
          <p>二、本周市场热点话题</p>
          <p>价格约4.10元/公斤。</p>
          <p>三、上市量影响</p>
          <p>价格约5.20元/公斤。</p>
        </div>
      </body>
    </html>
    """

    result = crawler.parse_zzny_clz_article(html, "https://zzny.zhengzhou.gov.cn/clzxx/topic.jhtml")

    assert result == []


def test_discover_zzny_max_pages_from_pagination_links():
    html = """
    <div class="page">
      <a href="index_2.jhtml">2</a>
      <a href="index_3.jhtml">3</a>
      <a href="index_4.jhtml">4</a>
      <a href="index_8.jhtml">8</a>
    </div>
    """

    result = PublicSourceCrawler._discover_zzny_max_pages(html, fallback=3)

    assert result == 8


def test_build_cnhnb_rows_extracts_supply_prices():
    crawler = PublicSourceCrawler()
    state = {
        "selected": {
            "area": {
                "province": {
                    "provinceName": "河南省",
                }
            }
        },
        "marketRelevantSulllys": [
            {
                "customTitle": "香菇",
                "cateName": "香菇",
                "price": 20,
                "originPrice": 21,
                "unit": "斤",
                "shopName": "山里人干货",
                "address": "鲁山县",
                "timeStr": "2小时前",
                "title": "精品香菇干货",
                "supplyId": 8574501,
            }
        ],
    }

    result = crawler.build_cnhnb_rows(state)

    assert len(result) == 1
    assert result[0]["site_name"] == "惠农网行情 | 山里人干货"
    assert result[0]["product_name"] == "香菇"
    assert result[0]["current_price"] == 20.0
    assert result[0]["original_price"] == 21.0
    assert result[0]["extra_fields"]["market_name"] == "鲁山县"


def test_build_cnhnb_rows_falls_back_to_market_list():
    crawler = PublicSourceCrawler()
    state = {
        "selected": {
            "area": {
                "province": {
                    "provinceName": "河南省",
                }
            }
        },
        "marketRelevantSulllys": [],
        "market": {
            "list": [
                {
                    "cateName": "木耳",
                    "breedName": "木耳",
                    "weighting_avgPrice": 19.35,
                    "avgPrice": 22.76,
                    "minPrice": 18.0,
                    "unit": "斤",
                    "addressDetail": "河南平顶山市鲁山县",
                    "collectDate": 1715846400000,
                }
            ]
        },
    }

    result = crawler.build_cnhnb_rows(state)

    assert len(result) == 1
    assert result[0]["site_name"] == "惠农网行情 | 河南平顶山市鲁山县"
    assert result[0]["product_name"] == "木耳"
    assert result[0]["current_price"] == 19.35
    assert result[0]["raw_extract"] == {}


def test_discover_cnhnb_max_pages_from_pagination_links():
    html = """
    <div class="page-wrap">
      <a href="/hangqing/cdlist-0-0-16-0-0-1/">1</a>
      <a href="/hangqing/cdlist-0-0-16-0-0-2/">2</a>
      <a href="/hangqing/cdlist-0-0-16-0-0-6/">6</a>
      <a href="/hangqing/cdlist-0-0-16-0-0-364/">364</a>
      <span>共 5452 条</span>
    </div>
    """

    result = PublicSourceCrawler._discover_cnhnb_max_pages(html, fallback=1)

    assert result == 364


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
    assert "menu_name" not in result["extra_fields"]
    assert "tree_label" not in result["extra_fields"]


def test_build_liancai_h5_rows_maps_subcategory_and_metadata():
    crawler = PublicSourceCrawler()
    selected = LiancaiCategory(fid="6", name="蔬菜类", page_url="http://m.liancaiwang.cn/list/index/id/6.html")
    subcategories = [
        LiancaiCategory(fid="102", name="叶菜类", page_url="http://m.liancaiwang.cn/list/index/id/102.html", parent_fid="6", parent_name="蔬菜类")
    ]
    product = {"group_name": "本地市场源", "category": "蔬菜类"}
    items = [
        {
            "product_id": "91702",
            "category_id": "6",
            "termid": "102",
            "title": "绿包菜 青甘蓝 10斤",
            "subtitle": "叶片浅绿色",
            "price": 7.8,
            "market_price": 0,
            "size": "10斤/袋(合每斤0.78元)",
            "unit": "袋",
            "inventory_text": "剩余库存16件",
            "cover": "http://mst.liancaiwang.cn/upload/uploads/cabbage.jpg",
        }
    ]

    result = crawler.build_liancai_h5_rows(items, selected, product, subcategories, page=2)

    assert len(result) == 1
    assert result[0]["site_name"] == "莲菜网H5 | 蔬菜类"
    assert result[0]["product_name"] == "绿包菜 青甘蓝 10斤"
    assert result[0]["current_price"] == 7.8
    assert result[0]["extra_fields"]["group_name"] == "莲菜网"
    assert result[0]["extra_fields"]["category"] == "叶菜类"
    assert result[0]["extra_fields"]["liancai_top_category"] == "蔬菜类"
    assert result[0]["extra_fields"]["liancai_subcategory"] == "叶菜类"
    assert result[0]["extra_fields"]["product_series"] == "102"
    assert "source_item_id" not in result[0]["extra_fields"]


def test_build_cnhnb_rows_skips_agricultural_inputs():
    crawler = PublicSourceCrawler()
    state = {
        "selected": {
            "area": {
                "province": {
                    "provinceName": "河南省",
                }
            }
        },
        "marketRelevantSulllys": [
            {
                "customTitle": "香菇",
                "cateName": "香菇",
                "price": 20,
                "unit": "斤",
                "shopName": "山里人干货",
                "title": "精品香菇干货",
            },
            {
                "customTitle": "除草剂",
                "cateName": "除草剂",
                "price": 18,
                "unit": "瓶",
                "shopName": "放心农资店",
                "title": "农资除草剂批发",
            },
            {
                "customTitle": "叶面肥",
                "cateName": "叶面肥",
                "price": 10,
                "unit": "袋",
                "shopName": "凤翔生物",
                "title": "农资肥料",
            },
        ],
    }

    result = crawler.build_cnhnb_rows(state)

    assert [row["product_name"] for row in result] == ["香菇"]
