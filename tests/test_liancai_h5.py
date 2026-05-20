from crawler.liancai_h5 import (
    LiancaiCategory,
    parse_goods_list_page,
    parse_goods_list_payload,
    parse_h5_categories,
    parse_h5_subcategories,
    parse_login_response,
)


def test_parse_login_response_supports_success_payload():
    payload = '{"code":200,"redirect":"","message":"登录验证成功！"}'

    result = parse_login_response(payload)

    assert result["code"] == 200
    assert result["message"] == "登录验证成功！"


def test_parse_h5_categories_extracts_fid_name_and_url():
    html = """
    <div class="category-header">
      <span data-id="6" data-url="/list/index/id/6.html" class="s-category-item current"><a href="javascript:;">蔬菜类</a></span>
      <span data-id="709" data-url="/list/index/id/709.html" class="s-category-item"><a href="javascript:;">净菜类</a></span>
    </div>
    """

    result = parse_h5_categories(html)

    assert result == [
        LiancaiCategory(fid="6", name="蔬菜类", page_url="http://m.liancaiwang.cn/list/index/id/6.html"),
        LiancaiCategory(fid="709", name="净菜类", page_url="http://m.liancaiwang.cn/list/index/id/709.html"),
    ]


def test_parse_h5_categories_supports_type_list_page():
    html = """
    <ul class="type-list">
      <li data-fid="774" data-url="/list/index/id/774.html">干调类</li>
      <li data-fid="10" data-url="/list/index/id/10.html">调味品</li>
    </ul>
    """

    result = parse_h5_categories(html)

    assert result == [
        LiancaiCategory(fid="774", name="干调类", page_url="http://m.liancaiwang.cn/list/index/id/774.html"),
        LiancaiCategory(fid="10", name="调味品", page_url="http://m.liancaiwang.cn/list/index/id/10.html"),
    ]


def test_parse_goods_list_payload_extracts_core_fields():
    payload = {
        "code": 200,
        "value": [
            {
                "id": "120395",
                "termid": "909",
                "title": "众客鸭块(排腿肉块)10kg",
                "subtitle": "鸭排腿切块",
                "price": 63,
                "marketPrice": 0,
                "size": "10kg/件",
                "unit": "件",
                "inv": "剩余库存16件",
                "cover": "http://mst.liancaiwang.cn/upload/a.jpg",
            }
        ],
    }

    result = parse_goods_list_payload(payload)

    assert len(result) == 1
    assert result[0]["product_id"] == "120395"
    assert result[0]["termid"] == "909"
    assert result[0]["title"] == "众客鸭块(排腿肉块)10kg"
    assert result[0]["price"] == 63
    assert result[0]["inventory_text"] == "剩余库存16件"


def test_parse_goods_list_page_extracts_goodsinfo_json():
    html = """
    <div data-goodsId="91702" data-catId="6" class="goods-item">
      <div class="goods-thumb"><img src="/upload/a.jpg"></div>
      <div data-goodsInfo="{&quot;id&quot;:&quot;91702&quot;,&quot;termid&quot;:&quot;102&quot;,&quot;title&quot;:&quot;绿包菜 青甘蓝 10斤&quot;,&quot;subtitle&quot;:&quot;叶片浅绿色&quot;,&quot;price&quot;:7.8,&quot;marketPrice&quot;:0,&quot;size&quot;:&quot;10斤/袋&quot;,&quot;unit&quot;:&quot;袋&quot;,&quot;inv&quot;:&quot;剩余库存16件&quot;,&quot;cover&quot;:&quot;http://mst.liancaiwang.cn/upload/uploads/cabbage.jpg&quot;}" data-goodsId="91702" class="counter">
        <span class="action jian"></span>
        <span class="number">0</span>
        <span class="action jia"></span>
      </div>
      <div class="price"><span>¥7.8</span><del>元/袋</del></div>
    </div>
    """

    result = parse_goods_list_page(html)

    assert len(result) == 1
    assert result[0]["product_id"] == "91702"
    assert result[0]["category_id"] == "6"
    assert result[0]["termid"] == "102"
    assert result[0]["title"] == "绿包菜 青甘蓝 10斤"
    assert result[0]["subtitle"] == "叶片浅绿色"
    assert result[0]["price"] == 7.8
    assert result[0]["cover"] == "http://mst.liancaiwang.cn/upload/uploads/cabbage.jpg"


def test_parse_h5_subcategories_extracts_nested_terms():
    html = """
    <ul class="child_terms child_terms_6">
      <li data-id="6" data-url="/list/index/id/6.html" class="current">全部</li>
      <li data-id="99" data-url="/list/index/id/99.html">根茎类</li>
      <li data-id="101" data-url="/list/index/id/101.html">葱姜蒜</li>
      <li data-id="102" data-url="/list/index/id/102.html">叶菜类</li>
    </ul>
    """

    result = parse_h5_subcategories(html, parent_fid="6", parent_name="蔬菜类")

    assert result == [
        LiancaiCategory(fid="6", name="全部", page_url="http://m.liancaiwang.cn/list/index/id/6.html", parent_fid="6", parent_name="蔬菜类"),
        LiancaiCategory(fid="99", name="根茎类", page_url="http://m.liancaiwang.cn/list/index/id/99.html", parent_fid="6", parent_name="蔬菜类"),
        LiancaiCategory(fid="101", name="葱姜蒜", page_url="http://m.liancaiwang.cn/list/index/id/101.html", parent_fid="6", parent_name="蔬菜类"),
        LiancaiCategory(fid="102", name="叶菜类", page_url="http://m.liancaiwang.cn/list/index/id/102.html", parent_fid="6", parent_name="蔬菜类"),
    ]
