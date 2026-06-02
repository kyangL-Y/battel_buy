# 快驴 H5 接入判定

## 判定

快驴可接入方向是 H5 分类页接口，不是 OCR、截图、滚动采集，也不是裸接口抓取。

当前已确认：

- 南京自助注册开关开放：`cityId=320100` 的 `/api/register/check/open` 返回 `openRegister=true`。
- 分类页真实 H5 base URL：`https://klmall.meituan.com/wxmall`。
- 未登录或非快驴商城账号时，分类接口返回 `103000 无权限访问`。
- 商品列表裸请求会被边缘层拒绝，不能在服务器上无登录态直接抓。
- 登录态必须是快驴商城采购/商家账号，并且需要南京可服务地址上下文。

当前不能声称：

- 不能声称普通美团账号可抓快驴商品。
- 不能声称无 `selectedPoiAddressId` / 销售网格上下文可全量抓商品。
- 不能声称已经完成正式 `kuailv_h5_batch`，因为还缺真实商家账号返回 `goodsList` 的验证。

## 已还原接口

| 用途 | Method | URL | 状态 |
| --- | --- | --- | --- |
| 注册开放检查 | `GET` | `/api/register/check/open?cityId=320100` | 无登录可测，南京开放 |
| 一级分类 | `GET` | `/api/goods/category/first/list` | 需快驴登录态 |
| 二级分类 | `GET` | `/api/goods/category/second/list` | 需快驴登录态和 `cat1Id` |
| 分类筛选 | `GET` | `/api/goods/category/filter` | 需快驴登录态、`cat1Id`、`cat2Id` |
| 分类 banner | `GET` | `/api/goods/category/banner/list` | 无登录可返回空 banner，不代表商品可抓 |
| 商品列表 | `POST` | `/api/goods/list` | 需快驴登录态、地址上下文、分类入参 |

商品列表 body 形态来自 H5 bundle：

```json
{
  "cat1Id": "9",
  "cat2Id": "91",
  "foodTagIds": null,
  "sortIds": null,
  "pageSize": 20,
  "data": {
    "common": {
      "uuid": "...",
      "timestamp": 1780297018362
    },
    "context": {
      "recent_click_goods": [],
      "recent_add_cart_goods": []
    }
  },
  "taken": null
}
```

分页依赖响应里的 `page.taken` 和 `page.hasNextPage`。

## H5 请求上下文

H5 请求层会追加或使用下列上下文：

| 字段 | 来源 | 用途 |
| --- | --- | --- |
| `uaWeb=44500` | H5 bundle 版本 `4.45.0` | 请求版本标识 |
| `uaEnv` | 运行环境 | `kuailv` / `wxmp` / `other` 等 |
| `loginAcctType` | 登录账号类型 | 快驴、外卖、微信等账号来源 |
| `uuid` | `_lxsdk` / `_lxsdk_cuid` / App uuid | 风控与请求标识 |
| `selectedPoiAddressId` | 已选收货地址 | 商品和配送网格上下文 |
| `selectedSalesGridId` | 销售网格 | 部分账号/地址路由需要 |
| `gtCityId` | 城市 | 南京为 `320100` |

服务端正式抓取必须保存的是合法登录态和地址上下文，不保存明文手机号、收货人、详细地址或验证码。

## 私密 env

把私密文件放在仓库外或 `.local-secrets/` 下，不提交：

```bash
KUAILV_COOKIES='{"token_cookie_name":"..."}'
KUAILV_REQUEST_HEADERS='{"x-auth-header":"..."}'
KUAILV_ADDRESS_CONTEXT='{"selectedPoiAddressId":"...","selectedSalesGridId":"...","uuid":"...","uaEnv":"other","loginAcctType":"99"}'
KUAILV_CITY_ID=320100
```

字段值需要来自魔尊自己登录后的合法会话。不要把 cookie、token、手机号、验证码或地址明文发到聊天里。

## 从真实手机抓包生成 env

快驴没有稳定桌面网页版时，用真实手机 App / 小程序抓包，不走模拟器环境绕过。

1. 启动快驴专用 mitm 过滤器：

```powershell
.\tools\start_kuailv_capture.ps1 -AllowSecretCapture -Port 8888
```

2. 手机和电脑在同一局域网，手机 Wi-Fi 代理指向电脑 IP，端口 `8888`。
3. 手机安装 mitmproxy CA 证书。若 App / 小程序仍提示证书、环境或网络异常，则停止该路线，不继续绕风控。
4. 用合法快驴采购/商家账号登录，选择南京可服务地址，进入商品分类并点开一到两个分类。
5. 停止抓包：

```powershell
.\tools\stop_kuailv_capture.ps1
```

6. 从私密抓包生成 env：

```powershell
python tools\extract_kuailv_h5_context.py --input .local-secrets\kuailv_capture\kuailv_secret_flows.jsonl --output .local-secrets\kuailv.env
```

普通脱敏日志在 `tmp\kuailv_capture\kuailv_flows.jsonl`，只用于看 `path`、`code/status/message`、`goods_count`，不能生成 env。

## 从浏览器 HAR 生成 env

如果桌面 Chrome 能完成快驴商家账号登录、选择南京可服务地址：

1. 打开 `https://klmall.meituan.com/m/category`。
2. DevTools → Network，刷新分类页或点一个分类。
3. 过滤 `wxmall/api/goods`，确认有 `category/first/list`、`category/second/list` 或 `goods/list` 请求。
4. 右键请求列表，选择 `Save all as HAR with content`，保存到 `.local-secrets/kuailv.har`。
5. 执行：

```powershell
python tools\extract_kuailv_h5_context.py --input .local-secrets\kuailv.har --output .local-secrets\kuailv.env
```

提取器支持 HAR 和 JSONL flow。它会把 cookie、必要 header、`selectedPoiAddressId`、`selectedSalesGridId`、`gtCityId`、`cat1Id/cat2Id` 写入 env 文件；命令行只打印输出路径、请求路径、是否命中商品请求和上下文字段名，不打印 secret 值。

## Readiness Probe

当前探针：

```powershell
python tools\check_kuailv_h5_readiness.py --secret-env-file .local-secrets\kuailv.env
```

安全约束：

- 只打印 env 顶层 key，不打印 cookie/token 值。
- 无登录态时预期 `ready=false`。
- 商品接口返回 `goodsList` 且 `goods_count > 0` 时才判定 `ready=true`。

无网络预检查：

```powershell
python tools\check_kuailv_h5_readiness.py --secret-env-file .local-secrets\kuailv.env --skip-network
```

当前无登录态实测：

```text
register_open: code=200 status=1 data_keys=["openRegister"]
category_first: code=103000 status=0 message="无权限访问"
ready=false
```

## 后续接入门槛

只有 readiness probe 满足以下条件，才新增正式 crawler strategy：

- `ready=true`
- `category_first_count > 0`
- 自动解析出 `resolved_cat1_id` 和 `resolved_cat2_id`
- `goods_list.goods_count > 0`
- `goods_list.taken_present` 可用于翻页，或 `has_next_page=false` 说明单页结束

正式策略建议名：

```text
kuailv_h5_batch
```

正式字段映射先按接口返回实际结构落地；未拿到 `goodsList` 样本前不提前猜字段。

## 风险边界

- 不绕验证码、Yoda、设备指纹或风控。
- 不使用截图/OCR/滚动采集做服务器正式链路。
- 登录态过期时抓取失败并提示刷新，不自动处罚式重试。
- 高频请求、并发翻页、复用过期 token 都可能触发风控；正式接入应按莲菜/美菜同类低并发策略执行。
