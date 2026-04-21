import json
import pandas as pd

import services.menu_planner as menu_planner
from services.menu_planner import build_procurement_plan, enrich_menu_items_with_ai, parse_menu_dataframe, parse_menu_text


def test_parse_menu_text_supports_line_based_input():
    rows = parse_menu_text("1. 蒜蓉西兰花\n2. 清蒸鲈鱼\n")
    assert len(rows) == 2
    assert rows[0]["menu_name"] == "蒜蓉西兰花"
    assert rows[1]["menu_name"] == "清蒸鲈鱼"


def test_parse_menu_dataframe_uses_first_column_as_menu_name():
    df = pd.DataFrame([{"菜名": "红烧排骨", "备注": "少辣"}])
    rows = parse_menu_dataframe(df)
    assert rows[0]["menu_name"] == "红烧排骨"
    assert rows[0]["remarks"] == "少辣"


def test_build_procurement_plan_returns_costs_and_market_recommendation():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "西兰花",
                "group_name": "西兰花",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 4.0,
            },
            {
                "product_name": "鲈鱼",
                "group_name": "鲈鱼",
                "category": "水产类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 18.0,
            },
        ]
    )

    ingredient_df, plan_df = build_procurement_plan(
        [
            {"menu_name": "西兰花", "ingredient_name": "西兰花"},
            {"menu_name": "鲈鱼", "ingredient_name": "鲈鱼"},
        ],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert len(ingredient_df) == 2
    assert len(plan_df) == 2
    assert plan_df.iloc[0]["recommended_market"] == "北京新发地"
    assert plan_df.iloc[0]["price_status"] == "已匹配报价"
    assert plan_df.iloc[0]["price_unit_basis"] == "原始报价"
    assert plan_df.attrs["total_cost"] is not None
    assert plan_df.iloc[0]["distance_label"] == "同城优先"


def test_build_procurement_plan_matches_after_ai_style_menu_mapping():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "西兰花",
                "group_name": "西兰花",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 4.0,
            }
        ]
    )

    _, plan_df = build_procurement_plan(
        [{"menu_name": "蒜蓉西兰花", "ingredient_name": "西兰花"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert len(plan_df) == 1
    assert plan_df.iloc[0]["ingredient_name"] == "西兰花"
    assert plan_df.iloc[0]["price_status"] == "已匹配报价"


def test_build_procurement_plan_expands_ai_returned_composite_ingredients():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "土豆",
                "group_name": "土豆",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 2.5,
            },
            {
                "product_name": "茄子",
                "group_name": "茄子",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 3.0,
            },
            {
                "product_name": "青椒",
                "group_name": "青椒",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 4.0,
            },
        ]
    )

    ingredient_df, plan_df = build_procurement_plan(
        [{"menu_name": "地三鲜", "ingredient_name": "土豆、茄子、青椒"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert len(ingredient_df) == 3
    assert len(plan_df) == 3
    assert sorted(ingredient_df["ingredient_name"].tolist()) == ["土豆", "茄子", "青椒"]
    assert set(plan_df["price_status"].tolist()) == {"已匹配报价"}
    assert set(plan_df["menu_name"].tolist()) == {"地三鲜"}


def test_build_procurement_plan_no_longer_uses_local_composite_mapping():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "土豆",
                "group_name": "土豆",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 2.5,
            }
        ]
    )

    ingredient_df, plan_df = build_procurement_plan(
        [{"menu_name": "地三鲜", "ingredient_name": "地三鲜"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert len(ingredient_df) == 1
    assert len(plan_df) == 1
    assert ingredient_df.iloc[0]["ingredient_name"] == "地三鲜"
    assert plan_df.iloc[0]["price_status"] == "缺报价/待确认"


def test_build_procurement_plan_prefers_kg_price_when_spec_allows_conversion():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "土豆",
                "group_name": "土豆",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "spec_text": "500g",
                "current_price": 3.0,
            }
        ]
    )

    _, plan_df = build_procurement_plan(
        [{"menu_name": "土豆", "ingredient_name": "土豆"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert plan_df.iloc[0]["reference_price"] == 6.0
    assert plan_df.iloc[0]["price_unit_basis"] == "元/公斤"


def test_enrich_menu_items_with_ai_enables_search_and_writes_log(monkeypatch, tmp_path):
    captured_request: dict[str, object] = {}
    log_path = tmp_path / "menu_ai_history.jsonl"
    monkeypatch.setattr(menu_planner, "MENU_AI_LOG_PATH", log_path)

    def fake_completion_text(*, messages, api_key, model, timeout_seconds, base_url, temperature, response_format, enable_search):
        captured_request["messages"] = messages
        captured_request["api_key"] = api_key
        captured_request["model"] = model
        captured_request["timeout_seconds"] = timeout_seconds
        captured_request["base_url"] = base_url
        captured_request["temperature"] = temperature
        captured_request["response_format"] = response_format
        captured_request["enable_search"] = enable_search
        return json.dumps(
            {
                "items": [
                    {"menu_name": "地三鲜", "ingredient_name": "土豆、茄子、青椒", "remarks": "联网搜索补全"}
                ]
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(menu_planner, "call_qwen_chat_completion_text", fake_completion_text)
    monkeypatch.setattr(menu_planner, "get_api_key", lambda runtime_config: "demo-key")

    result = enrich_menu_items_with_ai(
        [{"menu_name": "地三鲜", "remarks": None}],
        runtime_config={
            "ai": {
                "enabled": True,
                "provider": "qwen",
                "model": "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "timeout_seconds": 20,
                "menu_enable_search": True,
            }
        },
    )

    assert result[0]["ingredient_name"] == "土豆、茄子、青椒"
    assert captured_request["enable_search"] is True
    assert log_path.exists()
    log_lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 1
    log_record = json.loads(log_lines[0])
    assert log_record["status"] == "success"
    assert log_record["enable_search"] is True


def test_enrich_menu_items_with_ai_accepts_single_object_ingredients_field(monkeypatch, tmp_path):
    log_path = tmp_path / "menu_ai_history.jsonl"
    monkeypatch.setattr(menu_planner, "MENU_AI_LOG_PATH", log_path)

    monkeypatch.setattr(
        menu_planner,
        "call_qwen_chat_completion_text",
        lambda **kwargs: json.dumps(
            {
                "menu_name": "佛跳墙",
                "ingredients": "鲍鱼、海参、鱼翅、花胶",
            },
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(menu_planner, "get_api_key", lambda runtime_config: "demo-key")

    result = enrich_menu_items_with_ai(
        [{"menu_name": "佛跳墙", "remarks": None}],
        runtime_config={
            "ai": {
                "enabled": True,
                "provider": "qwen",
                "model": "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "timeout_seconds": 20,
                "menu_enable_search": True,
            }
        },
    )

    assert result[0]["ingredient_name"] == "鲍鱼、海参、鱼翅、花胶"


def test_enrich_menu_items_with_ai_accepts_top_level_array_payload(monkeypatch, tmp_path):
    log_path = tmp_path / "menu_ai_history.jsonl"
    monkeypatch.setattr(menu_planner, "MENU_AI_LOG_PATH", log_path)

    monkeypatch.setattr(
        menu_planner,
        "call_qwen_chat_completion_text",
        lambda **kwargs: json.dumps(
            [
                {"menu_name": "蒜蓉西兰花", "ingredients": "西兰花"},
            ],
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(menu_planner, "get_api_key", lambda runtime_config: "demo-key")

    result = enrich_menu_items_with_ai(
        [{"menu_name": "蒜蓉西兰花", "remarks": None}],
        runtime_config={
            "ai": {
                "enabled": True,
                "provider": "qwen",
                "model": "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "timeout_seconds": 20,
                "menu_enable_search": True,
            }
        },
    )

    assert result[0]["ingredient_name"] == "西兰花"


def test_enrich_menu_items_with_ai_falls_back_to_core_ingredient_when_model_echoes_menu_name(monkeypatch, tmp_path):
    log_path = tmp_path / "menu_ai_history.jsonl"
    monkeypatch.setattr(menu_planner, "MENU_AI_LOG_PATH", log_path)

    monkeypatch.setattr(
        menu_planner,
        "call_qwen_chat_completion_text",
        lambda **kwargs: json.dumps(
            {
                "items": [
                    {"menu_name": "蒜蓉西兰花", "ingredient_name": "蒜蓉西兰花", "remarks": "原样返回"},
                ]
            },
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(menu_planner, "get_api_key", lambda runtime_config: "demo-key")

    result = enrich_menu_items_with_ai(
        [{"menu_name": "蒜蓉西兰花", "remarks": None}],
        runtime_config={
            "ai": {
                "enabled": True,
                "provider": "qwen",
                "model": "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "timeout_seconds": 20,
                "menu_enable_search": True,
            }
        },
    )

    assert result[0]["ingredient_name"] == "西兰花"


def test_enrich_menu_items_with_ai_parses_json_inside_markdown_code_block(monkeypatch, tmp_path):
    log_path = tmp_path / "menu_ai_history.jsonl"
    monkeypatch.setattr(menu_planner, "MENU_AI_LOG_PATH", log_path)

    monkeypatch.setattr(
        menu_planner,
        "call_qwen_chat_completion_text",
        lambda **kwargs: """```json
{
  "items": [
    {"menu_name": "番茄炒蛋", "ingredient_name": "番茄、鸡蛋", "remarks": "联网搜索补全"}
  ]
}
```""",
    )
    monkeypatch.setattr(menu_planner, "get_api_key", lambda runtime_config: "demo-key")

    result = enrich_menu_items_with_ai(
        [{"menu_name": "番茄炒蛋", "remarks": None}],
        runtime_config={
            "ai": {
                "enabled": True,
                "provider": "qwen",
                "model": "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "timeout_seconds": 20,
                "menu_enable_search": True,
            }
        },
    )

    assert result[0]["ingredient_name"] == "番茄、鸡蛋"


def test_enrich_menu_items_with_ai_falls_back_to_local_heuristic_when_ai_errors(monkeypatch, tmp_path):
    log_path = tmp_path / "menu_ai_history.jsonl"
    monkeypatch.setattr(menu_planner, "MENU_AI_LOG_PATH", log_path)

    def _raise_error(**kwargs):
        raise RuntimeError("upstream timeout")

    monkeypatch.setattr(menu_planner, "call_qwen_chat_completion_text", _raise_error)
    monkeypatch.setattr(menu_planner, "get_api_key", lambda runtime_config: "demo-key")

    result = enrich_menu_items_with_ai(
        [{"menu_name": "番茄炒蛋", "remarks": None}],
        runtime_config={
            "ai": {
                "enabled": True,
                "provider": "qwen",
                "model": "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "timeout_seconds": 20,
                "menu_enable_search": True,
            }
        },
    )

    assert result[0]["ingredient_name"] == "番茄、鸡蛋"
    assert "启发式拆分" in str(result[0]["remarks"])


def test_enrich_menu_items_with_ai_uses_heuristic_recipe_for_gongbaojiding_when_ai_echoes(monkeypatch, tmp_path):
    log_path = tmp_path / "menu_ai_history.jsonl"
    monkeypatch.setattr(menu_planner, "MENU_AI_LOG_PATH", log_path)

    monkeypatch.setattr(
        menu_planner,
        "call_qwen_chat_completion_text",
        lambda **kwargs: json.dumps(
            {
                "items": [
                    {"menu_name": "宫保鸡丁", "ingredient_name": "宫保鸡丁", "remarks": None},
                ]
            },
            ensure_ascii=False,
        ),
    )
    monkeypatch.setattr(menu_planner, "get_api_key", lambda runtime_config: "demo-key")

    result = enrich_menu_items_with_ai(
        [{"menu_name": "宫保鸡丁", "remarks": None}],
        runtime_config={
            "ai": {
                "enabled": True,
                "provider": "qwen",
                "model": "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "timeout_seconds": 20,
                "menu_enable_search": True,
            }
        },
    )

    assert result[0]["ingredient_name"] == "鸡丁、花生米、黄瓜"


def test_build_procurement_plan_prefers_location_alias_when_price_close():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "西兰花",
                "group_name": "西兰花",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京顺鑫石门国际农产品批发市场集团有限公司",
                "market_name": "北京顺鑫石门国际农产品批发市场集团有限公司",
                "province": "北京市",
                "city": "北京市",
                "current_price": 4.2,
            },
            {
                "product_name": "西兰花",
                "group_name": "西兰花",
                "category": "蔬菜类",
                "site_name": "PFSC | 云南通海金山蔬菜批发市场",
                "market_name": "云南通海金山蔬菜批发市场",
                "province": "云南省",
                "city": "通海",
                "current_price": 4.1,
            },
        ]
    )

    _, plan_df = build_procurement_plan(
        [{"menu_name": "蒜蓉西兰花", "ingredient_name": "西兰花"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_location="当前位置",
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert plan_df.iloc[0]["recommended_market"] == "北京顺鑫石门国际农产品批发市场集团有限公司"
    assert plan_df.iloc[0]["distance_label"] == "同城优先"


def test_build_procurement_plan_prefers_pfsc_for_vegetable_over_lower_chinaprice():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "西兰花",
                "group_name": "西兰花",
                "category": "蔬菜类",
                "site_name": "Chinaprice | 全国蔬菜平均价",
                "market_name": "全国蔬菜平均价",
                "province": "全国",
                "city": "",
                "current_price": 3.6,
            },
            {
                "product_name": "西兰花",
                "group_name": "西兰花",
                "category": "蔬菜类",
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 4.1,
            },
        ]
    )

    _, plan_df = build_procurement_plan(
        [{"menu_name": "蒜蓉西兰花", "ingredient_name": "西兰花"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert plan_df.iloc[0]["recommended_market"] == "北京新发地"
    assert plan_df.iloc[0]["source_priority_label"] == "蔬菜明细市场优先"
    assert "来源策略" in str(plan_df.iloc[0]["remarks"])


def test_build_procurement_plan_prefers_pfsc_aquatic_market_over_lower_chinaprice():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "鲈鱼",
                "group_name": "鲈鱼",
                "category": "水产类",
                "site_name": "Chinaprice | 全国水产平均价",
                "market_name": "全国水产平均价",
                "province": "全国",
                "city": "",
                "current_price": 16.2,
            },
            {
                "product_name": "鲈鱼",
                "group_name": "鲈鱼",
                "category": "水产类",
                "site_name": "PFSC | 北京八里桥水产市场",
                "market_name": "北京八里桥水产市场",
                "province": "北京市",
                "city": "北京市",
                "current_price": 17.0,
            },
        ]
    )

    _, plan_df = build_procurement_plan(
        [{"menu_name": "清蒸鲈鱼", "ingredient_name": "鲈鱼"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert plan_df.iloc[0]["recommended_market"] == "北京八里桥水产市场"
    assert plan_df.iloc[0]["source_priority_label"] == "水产明细市场优先"


def test_build_procurement_plan_prefers_meat_reference_over_irrelevant_pfsc_market():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "鲜猪肉（肋排）",
                "group_name": "肉禽蛋",
                "category": "肉禽蛋",
                "site_name": "Chinaprice | 集市 | 肉禽蛋汇总价格 | 食品（36大中城市）汇总树",
                "market_name": "集市",
                "province": "北京市",
                "city": "北京市",
                "current_price": 15.0,
            },
            {
                "product_name": "猪肋排",
                "group_name": "家畜",
                "category": "家畜",
                "site_name": "PFSC | 宁夏海吉星国际农产品物流有限公司",
                "market_name": "宁夏海吉星国际农产品物流有限公司",
                "province": None,
                "city": None,
                "current_price": 28.0,
            },
        ]
    )

    _, plan_df = build_procurement_plan(
        [{"menu_name": "红烧排骨", "ingredient_name": "猪排骨"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert "Chinaprice" in str(plan_df.iloc[0]["recommended_site"])
    assert plan_df.iloc[0]["source_priority_label"] == "同城肉禽蛋参考价优先"
    assert plan_df.iloc[0]["backup_source_priority_label"] == "市场明细报价优先"


def test_build_procurement_plan_meat_quantity_uses_family_when_category_missing():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "猪肋排",
                "group_name": "家畜",
                "category": None,
                "site_name": "PFSC | 北京新发地",
                "market_name": "北京新发地",
                "province": "北京市",
                "city": "北京市",
                "current_price": 28.0,
            }
        ]
    )

    ingredient_df, plan_df = build_procurement_plan(
        [{"menu_name": "红烧排骨", "ingredient_name": "猪排骨"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert ingredient_df.iloc[0]["estimated_quantity"] == 17.0
    assert plan_df.iloc[0]["estimated_quantity"] == 17.0


def test_build_procurement_plan_ignores_nan_location_for_meat_source_priority():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "鲜猪肉（肋排）",
                "group_name": "肉禽蛋",
                "category": "肉禽蛋",
                "site_name": "Chinaprice | 集市 | 肉禽蛋汇总价格 | 食品（36大中城市）汇总树",
                "market_name": "集市",
                "province": "乌鲁木齐市",
                "city": "乌鲁木齐市",
                "current_price": 15.0,
            },
            {
                "product_name": "猪肋排",
                "group_name": "家畜",
                "category": "家畜",
                "site_name": "PFSC | 宁夏海吉星国际农产品物流有限公司",
                "market_name": "宁夏海吉星国际农产品物流有限公司",
                "province": float('nan'),
                "city": float('nan'),
                "current_price": 28.0,
            },
        ]
    )

    _, plan_df = build_procurement_plan(
        [{"menu_name": "红烧排骨", "ingredient_name": "猪排骨"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
        preferred_city="北京市",
    )

    assert "Chinaprice" in str(plan_df.iloc[0]["recommended_site"])


def test_build_procurement_plan_marks_same_province_meat_reference_label():
    latest_df = pd.DataFrame(
        [
            {
                "product_name": "鲜猪肉（肋排）",
                "group_name": "肉禽蛋",
                "category": "肉禽蛋",
                "site_name": "Chinaprice | 集市 | 肉禽蛋汇总价格 | 食品（36大中城市）汇总树",
                "market_name": "集市",
                "province": "北京市",
                "city": "",
                "current_price": 15.0,
            }
        ]
    )

    _, plan_df = build_procurement_plan(
        [{"menu_name": "红烧排骨", "ingredient_name": "猪排骨"}],
        latest_df,
        diners=100,
        tables=10,
        preferred_province="北京市",
    )

    assert plan_df.iloc[0]["source_priority_label"] == "同省肉禽蛋参考价优先"
