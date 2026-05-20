from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LiancaiCategoryMapping:
    top_category: str | None
    subcategory: str | None
    source: str


SUBCATEGORY_ALIAS_MAP: dict[str, tuple[str, str]] = {
    "根和根茎类": ("蔬菜类", "根茎类"),
    "根茎类": ("蔬菜类", "根茎类"),
    "薯类": ("蔬菜类", "根茎类"),
    "葱姜蒜": ("蔬菜类", "葱姜蒜"),
    "叶菜类": ("蔬菜类", "叶菜类"),
    "芽、花类": ("蔬菜类", "叶菜类"),
    "椒类": ("蔬菜类", "椒类"),
    "茄瓜果类": ("蔬菜类", "茄瓜果类"),
    "盘饰品": ("蔬菜类", "盘饰品"),
    "其他蔬菜": ("蔬菜类", "全部"),
    "净菜": ("净菜类", "净菜"),
    "食用菌类": ("菌菇类", "菌菇类"),
    "菌菇类": ("菌菇类", "菌菇类"),
    "瓜类水果": ("水果类", "瓜果类"),
    "瓜果类": ("水果类", "瓜果类"),
    "浆果类": ("水果类", "其他水果"),
    "仁果类": ("水果类", "苹果类"),
    "核果类": ("水果类", "桃、李、杏、枣"),
    "柑果类": ("水果类", "桔▪橙▪柚"),
    "苹果类": ("水果类", "苹果类"),
    "梨类": ("水果类", "梨类"),
    "蕉类": ("水果类", "蕉类"),
    "热带水果": ("水果类", "热带水果"),
    "热带及亚热带水果": ("水果类", "热带水果"),
    "桔▪橙▪柚": ("水果类", "桔▪橙▪柚"),
    "应季优果": ("水果类", "应季优果"),
    "其他水果": ("水果类", "其他水果"),
    "干果类": ("水果类", "干果类"),
    "坚果类": ("水果类", "干果类"),
    "豆芽类": ("豆制品", "豆芽类"),
    "豆腐类": ("豆制品", "豆腐类"),
    "豆浆类": ("豆制品", "豆浆类"),
    "豆干、豆皮、豆泡、腐竹类": ("豆制品", "豆干、豆皮、豆泡、腐竹类"),
    "其他豆制品": ("豆制品", "其他豆制品"),
    "果饮/茶饮": ("酒水饮料", "果饮/茶饮"),
    "碳酸饮料": ("酒水饮料", "碳酸饮料"),
    "功能饮料": ("酒水饮料", "功能饮料"),
    "饮用水": ("酒水饮料", "饮用水"),
    "冲饮/茶叶/咖啡": ("酒水饮料", "冲饮/茶叶/咖啡"),
    "猪肉类": ("鲜猪肉", "猪肉类"),
    "猪排类": ("鲜猪肉", "猪排类"),
    "猪骨类": ("鲜猪肉", "猪骨类"),
    "猪副类": ("鲜猪肉", "猪副类"),
    "鲜鸡鸭": ("鲜禽类", "鲜鸡鸭"),
    "鸡鸭副类": ("鲜禽类", "鸡鸭副类"),
    "牛肉类": ("牛羊肉", "牛肉类"),
    "羊肉类": ("牛羊肉", "羊肉类"),
    "羊排类": ("牛羊肉", "羊排类"),
    "大米": ("米面粮油", "大米"),
    "杂粮": ("米面粮油", "杂粮"),
    "面粉": ("米面粮油", "面粉"),
    "食用油": ("米面粮油", "食用油"),
    "食用植物油": ("米面粮油", "食用油"),
    "挂面": ("米面粮油", "挂面"),
    "馒头花卷烧饼": ("米面粮油", "馒头花卷烧饼"),
    "面条": ("米面粮油", "面条"),
    "面片": ("米面粮油", "面片"),
    "鲜冻水产": ("鲜活水产", "鲜冻水产"),
    "加工水产": ("鲜活水产", "加工水产"),
    "水产类": ("鲜活水产", "鲜冻水产"),
    "冻猪肉": ("冻品类", "冻猪肉"),
    "冻鸡鸭": ("冻品类", "冻鸡鸭"),
    "冻牛羊": ("冻品类", "冻牛羊"),
    "面点类": ("冻品类", "面点类"),
    "饺子馄饨": ("冻品类", "饺子馄饨"),
    "丸子类": ("冻品类", "丸子类"),
    "调理类": ("冻品类", "调理类"),
    "果蔬类": ("冻品类", "果蔬类"),
    "肠类制品": ("冻品类", "肠类制品"),
    "特色食材": ("冻品类", "特色食材"),
    "南北干货": ("干调类", "南北干货"),
    "香辛料": ("干调类", "香辛料"),
    "调味酱/汁": ("调味品", "调味酱/汁"),
    "调味料": ("调味品", "调味料"),
    "淀粉/生粉": ("调味品", "淀粉/生粉"),
    "罐头/其他": ("调味品", "罐头/其他"),
    "西餐调料": ("调味品", "西餐调料"),
    "冲调/剂类": ("调味品", "冲调/剂类"),
    "鲜鸡蛋": ("禽蛋类", "鲜鸡蛋"),
    "鲜蛋类": ("禽蛋类", "鲜蛋类"),
    "加工蛋制品": ("禽蛋类", "加工蛋制品"),
    "其他卤制品": ("卤味类", "其他卤制品"),
    "牛肉卤制品": ("卤味类", "牛肉卤制品"),
    "羊肉卤制品": ("卤味类", "羊肉卤制品"),
    "鸡肉卤制品": ("卤味类", "鸡肉卤制品"),
    "凉菜系列": ("卤味类", "凉菜系列"),
    "烧烤工具": ("易耗类", "烧烤工具"),
    "圆形餐盒": ("易耗类", "圆形餐盒"),
    "方形餐盒": ("易耗类", "方形餐盒"),
    "打包系列": ("易耗类", "打包系列"),
    "纸品湿巾": ("易耗类", "纸品湿巾"),
    "餐厨用品": ("易耗类", "餐厨用品"),
    "清洁用品": ("易耗类", "清洁用品"),
    "一次性用品": ("易耗类", "一次性用品"),
    "锡纸保鲜膜": ("易耗类", "锡纸保鲜膜"),
    "意境盘饰": ("易耗类", "意境盘饰"),
    "厨房设备": ("易耗类", "厨房设备"),
    "蔬果类": ("信阳菜", "蔬果类"),
    "河鲜类": ("信阳菜", "河鲜类"),
    "蛋品类": ("信阳菜", "蛋品类"),
    "干货类": ("信阳菜", "干货类"),
    "肉禽类": ("信阳菜", "肉禽类"),
    "米面油": ("信阳菜", "米面油"),
    "牛排披萨类": ("西餐", "牛排披萨类"),
    "慕斯大福三文治类": ("西餐", "慕斯大福三文治类"),
    "调味品酱料类": ("西餐", "调味品酱料类"),
    "冲调饮品类": ("西餐", "冲调饮品类"),
    "烘焙蛋挞类": ("西餐", "烘焙蛋挞类"),
    "油炸小吃类": ("西餐", "油炸小吃类"),
    "其他原料类": ("西餐", "其他原料类"),
    "腌腊肠类": ("腌腊类", "腌腊肠类"),
    "腌腊猪肉类": ("腌腊类", "腌腊猪肉类"),
    "其它腌腊制品类": ("腌腊类", "其它腌腊制品类"),
}

TOP_CATEGORY_ALIAS_MAP: dict[str, str] = {
    "蔬菜类": "蔬菜类",
    "水果类": "水果类",
    "豆制品": "豆制品",
    "酒水饮料": "酒水饮料",
    "鲜猪肉": "鲜猪肉",
    "鲜禽类": "鲜禽类",
    "牛羊肉": "牛羊肉",
    "米面粮油": "米面粮油",
    "鲜活水产": "鲜活水产",
    "冻品类": "冻品类",
    "干调类": "干调类",
    "调味品": "调味品",
    "禽蛋类": "禽蛋类",
    "卤味类": "卤味类",
    "易耗类": "易耗类",
    "信阳菜": "信阳菜",
    "西餐": "西餐",
    "腌腊类": "腌腊类",
    "净菜类": "净菜类",
    "菌菇类": "菌菇类",
    "果品类": "水果类",
    "谷物": "米面粮油",
    "豆类": "米面粮油",
    "粮油": "米面粮油",
    "水产品": "鲜活水产",
    "畜禽蛋品": "禽蛋类",
    "禽蛋": "禽蛋类",
    "副食": "调味品",
    "水果": "水果类",
    "糖料": "水果类",
    "家畜": "鲜猪肉",
    "加工副产品": "调味品",
    "其他食品": "调味品",
    "种子果实类": "干调类",
}


def normalize_mapping_text(value: Any) -> str:
    return str(value or "").strip()


def suggest_liancai_mapping(
    *,
    category: Any,
    product_name: Any = None,
    site_name: Any = None,
) -> LiancaiCategoryMapping:
    normalized_category = normalize_mapping_text(category)
    normalized_product_name = normalize_mapping_text(product_name)
    normalized_site_name = normalize_mapping_text(site_name)

    if normalized_site_name.startswith("莲菜网H5 | "):
        top_category = normalized_site_name.split("|", 1)[1].strip()
        subcategory = normalized_category or "全部"
        return LiancaiCategoryMapping(top_category=top_category, subcategory=subcategory, source="liancai_site_name")

    if normalized_category in SUBCATEGORY_ALIAS_MAP:
        top_category, subcategory = SUBCATEGORY_ALIAS_MAP[normalized_category]
        return LiancaiCategoryMapping(top_category=top_category, subcategory=subcategory, source="exact_subcategory")

    if normalized_category in TOP_CATEGORY_ALIAS_MAP:
        top_category = TOP_CATEGORY_ALIAS_MAP[normalized_category]
        return LiancaiCategoryMapping(top_category=top_category, subcategory="全部", source="exact_top_category")

    inferred = _infer_by_keywords(normalized_category, normalized_product_name)
    if inferred is not None:
        return inferred

    return LiancaiCategoryMapping(top_category=None, subcategory=None, source="unmapped")


def _infer_by_keywords(category: str, product_name: str) -> LiancaiCategoryMapping | None:
    text = f"{category} {product_name}"
    if any(keyword in text for keyword in ["苹果", "梨", "橙", "柚", "橘", "桔", "香蕉", "菠萝", "榴莲", "草莓", "蓝莓", "葡萄", "西瓜", "甜瓜", "哈密瓜", "火龙果"]):
        return LiancaiCategoryMapping("水果类", "全部", "keyword_fruit")
    if any(keyword in text for keyword in ["豆腐", "豆皮", "腐竹", "豆芽", "豆浆", "豆干", "豆泡"]):
        return LiancaiCategoryMapping("豆制品", "全部", "keyword_bean")
    if any(keyword in text for keyword in ["辣椒面", "花椒", "胡椒", "香叶", "桂皮", "八角", "孜然", "木耳", "香菇", "红枣", "桂圆", "干货"]):
        return LiancaiCategoryMapping("干调类", "全部", "keyword_dried_goods")
    if any(keyword in text for keyword in ["饮料", "可乐", "雪碧", "矿泉水", "苏打水", "咖啡", "茶叶", "果汁"]):
        return LiancaiCategoryMapping("酒水饮料", "全部", "keyword_drink")
    if any(keyword in text for keyword in ["猪", "排骨", "五花", "前腿", "后腿", "里脊", "肘子"]):
        return LiancaiCategoryMapping("鲜猪肉", "全部", "keyword_pork")
    if any(keyword in text for keyword in ["牛", "羊", "毛肚", "百叶", "肥牛", "肥羊"]):
        return LiancaiCategoryMapping("牛羊肉", "全部", "keyword_beef_lamb")
    if any(keyword in text for keyword in ["鸡", "鸭", "鹅", "翅", "翅根", "鸡腿", "鸡胸", "鸭腿", "鸭块"]):
        return LiancaiCategoryMapping("鲜禽类", "全部", "keyword_poultry")
    if any(keyword in text for keyword in ["鱼", "虾", "蟹", "贝", "蛤", "蚬", "鱿鱼", "墨鱼", "带鱼", "鳕鱼", "鲈鱼", "鲤鱼"]):
        return LiancaiCategoryMapping("鲜活水产", "全部", "keyword_seafood")
    if any(keyword in text for keyword in ["面粉", "大米", "面条", "挂面", "花卷", "烧饼", "食用油", "杂粮", "小米", "糯米"]):
        return LiancaiCategoryMapping("米面粮油", "全部", "keyword_grain")
    if any(keyword in text for keyword in ["鸡蛋", "鸭蛋", "鹅蛋", "鹌鹑蛋", "皮蛋", "咸蛋"]):
        return LiancaiCategoryMapping("禽蛋类", "全部", "keyword_egg")
    if any(keyword in text for keyword in ["冻", "丸子", "水饺", "馄饨", "面点", "披萨", "薯条", "鸡柳", "半成品"]):
        return LiancaiCategoryMapping("冻品类", "全部", "keyword_frozen")
    if any(keyword in text for keyword in ["包装", "餐盒", "湿巾", "锡纸", "保鲜膜", "清洁", "纸巾", "一次性"]):
        return LiancaiCategoryMapping("易耗类", "全部", "keyword_consumable")
    if any(keyword in text for keyword in ["卤", "凉菜", "酱牛肉", "鸭脖", "鸭货"]):
        return LiancaiCategoryMapping("卤味类", "全部", "keyword_braised")
    return None
