from services.liancai_category_mapping import suggest_liancai_mapping


def test_suggest_liancai_mapping_prefers_liancai_site_name():
    result = suggest_liancai_mapping(
        category="南北干货",
        product_name="佐味鹰嘴豆2斤",
        site_name="莲菜网H5 | 干调类",
    )

    assert result.top_category == "干调类"
    assert result.subcategory == "南北干货"
    assert result.source == "liancai_site_name"


def test_suggest_liancai_mapping_handles_exact_aliases():
    result = suggest_liancai_mapping(category="根和根茎类", product_name="白萝卜", site_name="其他站点")

    assert result.top_category == "蔬菜类"
    assert result.subcategory == "根茎类"
    assert result.source == "exact_subcategory"


def test_suggest_liancai_mapping_handles_keyword_rules():
    result = suggest_liancai_mapping(category="家畜", product_name="肥膘", site_name="其他站点")

    assert result.top_category == "鲜猪肉"
    assert result.subcategory == "全部"
    assert result.source == "exact_top_category"
