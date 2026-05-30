# 美菜分类口径边界

## 判定

美菜当前至少有三套容易混淆的分类字段，不能混用：

| 口径 | 来源 | 当前状态 | 用途 |
| --- | --- | --- | --- |
| 导航类目 | `/entrance/dishes/saleClass` | 明文可抓 | App 分类页导航，当前南京地址实测为 20 个一级、197 个二级 |
| 销售类目 | 商品字段 `saleC1Id` / `saleC2Id` | 明文商品流里可见 | 与导航类目 ID 有交集，可用于接口入参和内部大类映射 |
| 商品品类 | 商品字段 `biName` / `biAliasName` | 仅在明文商品返回中可见 | 更细的商品品类，数量会远多于导航类目 |

## 已验证接口

- `POST /entrance/dishes/saleClass`
  - 明文返回导航类目树。
  - 二级类目下继续请求无三级返回。
  - 不能代表完整商品品类。

- `POST /entrance/recommend/xbFeed`
  - 明文返回推荐/瀑布流商品。
  - 商品中可解析 `skuBase.biName`、`skuBase.biAliasName`、`skuBase.saleC1Id`、`skuBase.saleC2Id`。
  - 即使传入 `class1Id/class2Id`，当前实测也不能稳定枚举完整分类页商品。

- `POST /entrance/dishes/getSpusByClass`
  - 分类页真实商品列表入口。
  - 当前响应 `data` 为加密字符串。
  - 按当前约束，不做验证码/设备指纹规避，不做 OCR，不把加密 data 当已解析数据。

## 采集边界

当前可生产落地的是：

- 抓 `saleClass` 得到导航类目与销售类目入口。
- 按 `saleClass` 二级类目批量抓 `getSpusByClass`，这条链路形态与莲菜网 `classify → goodslist(term_id,page)` 对齐。
- 若 `getSpusByClass` 返回明文结构化 `data`，直接归一化商品、价格、SKU、`biName/biAliasName`。
- 若 `getSpusByClass` 仍返回加密字符串，抓取按约定失败，不转 UI 滚动或 OCR。
- 本地已验证 App 运行态可接住 `CategoryViewModel.c(BaseResult,String,String)` 解密后的 `AllGoodsListResult`，商品位于 `data.refeactorSkus`。
- 用 `biName/biAliasName` 建立“已见商品品类候选表”。

当前不可声称的是：

- 不可声称 `saleClass` 的 197 个二级类目就是完整商品品类。
- 不可声称 `xbFeed` 可覆盖全部分类商品。
- 不可在未解析 `getSpusByClass` 加密 data 前声称已完成分类页全量商品抓取。

## 当前抓取规模配置

正式抓取配置通过 `config/sites.json` 的 `sale_class_tree_path` 读取 `tmp/meicai_sale_class_tree.json`，按南京当前 `197` 个二级类目逐个请求 `getSpusByClass`。若服务端直接请求仍得到加密 `data`，本链路会中止并提示登录态/运行态解密问题。

运行态验证命令：

```powershell
python tools\collect_meicai_runtime_class_products.py --limit-categories 0 --max-pages 2 --page-size 20 --wait-seconds 650
python tools\collect_meicai_runtime_class_products.py --summarize-only --output .local-secrets\meicai_runtime_class_products.jsonl --export-rows .local-secrets\meicai_runtime_price_rows.json
```

2026-05-30 南京登录态实测结果：

- `trigger_count=394`
- `decoded_pages=391`
- `decoded_category_count=196`
- `unique_goods_count=1081`
- `export_row_count=1081`

该验证不使用 UI 滚动采集，不使用 OCR；只利用 App 已登录运行态触发分类分页请求并读取 App 自己解密后的结构化对象。

## 内部字段映射契约

`meicai_app_gateway_batch` 当前只把明文商品流写入内部价格行，字段边界如下：

| 内部字段 | 美菜来源 | 说明 |
| --- | --- | --- |
| `product_name` | `skuBase.skuName` / `skuBase.spuName` | 商品展示名 |
| `current_price` | `skuPrice.minPrice` / `unitPrice` / `price` | 当前可见价格 |
| `original_price` | `skuPrice.marketPrice` / `originPrice` | 原价，可能为空 |
| `extra_fields.spec_text` | `skuPrice.priceUnit` / `unit` | 价格单位或规格 |
| `extra_fields.product_series` | `skuId` / `spuId` | 内部去重与身份辅助 |
| `extra_fields.brand` | `brandName` | 品牌，可能为空 |
| `extra_fields.cover` | `skuImg.imgUrl` / `url` | 商品图片 |
| `extra_fields.meicai_sku_id` | `skuBase.skuId` | 美菜 SKU ID |
| `extra_fields.meicai_spu_id` | `skuBase.spuId` | 美菜 SPU ID |
| `extra_fields.meicai_sale_c1_id/name` | `saleC1Id` / `saleC1Name` | 美菜销售一级类目 |
| `extra_fields.meicai_sale_c2_id/name` | `saleC2Id` / `saleC2Name` | 美菜销售二级类目 |
| `extra_fields.meicai_bi_name` | `biName` | 美菜商品品类候选 |
| `extra_fields.meicai_bi_alias_name` | `biAliasName` | 商品品类别名候选 |
| `extra_fields.liancai_top_category` | 映射推断 | 内部大类 |
| `extra_fields.liancai_subcategory` | 映射推断 | 内部小类 |
| `extra_fields.liancai_mapping_source` | 映射推断 | 写入现有 `products.liancai_mapping_source` |
| `extra_fields.meicai_internal_mapping_source` | 映射推断 | `biName exact > liancai mapping > saleC2Id > saleC1Id > unmapped` |
| `extra_fields.meicai_internal_mapping_confidence` | 映射推断 | 映射置信度 |
