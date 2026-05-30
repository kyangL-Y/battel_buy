from __future__ import annotations

from tools.extract_meicai_ui_goods import parse_meicai_ui_goods


def test_parse_meicai_ui_goods_extracts_visible_names_and_units(tmp_path):
    xml_path = tmp_path / "meicai.xml"
    xml_path.write_text(
        """
        <hierarchy>
          <node text="蔬果豆类" resource-id="com.meicai.mall:id/categoryText" class="android.widget.TextView" bounds="[0,360][186,407]" />
          <node text="叶菜花菜" resource-id="com.meicai.mall:id/cate_tv" class="android.widget.TextView" bounds="[23,483][171,526]" />
          <node text="紫甘蓝 普通" resource-id="com.meicai.mall:id/tvGoodsName" class="android.widget.TextView" bounds="[518,447][1045,505]" />
          <node text="1斤" resource-id="com.meicai.mall:id/ssuFormatUnit" class="android.widget.TextView" bounds="[518,708][600,759]" />
          <node text="" resource-id="com.meicai.mall:id/tv_commodity_now_price" class="android.widget.ImageView" bounds="[606,707][801,771]" />
          <node text="小白菜 普通 水洗" resource-id="com.meicai.mall:id/tvGoodsName" class="android.widget.TextView" bounds="[518,809][1045,867]" />
          <node text="2斤" resource-id="com.meicai.mall:id/ssuFormatUnit" class="android.widget.TextView" bounds="[518,1070][600,1121]" />
        </hierarchy>
        """,
        encoding="utf-8",
    )

    report = parse_meicai_ui_goods(xml_path)

    assert report["counts"]["visible_goods"] == 2
    assert report["counts"]["price_image_nodes"] == 1
    assert report["visible_categories"] == ["蔬果豆类", "叶菜花菜"]
    assert report["visible_goods"][0]["name"] == "紫甘蓝 普通"
    assert report["visible_goods"][0]["spec_text"] == "1斤"
    assert report["visible_goods"][1]["identity"] == "小白菜 普通 水洗|2斤"
    assert report["price_text_available"] is False
