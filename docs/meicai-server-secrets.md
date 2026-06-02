# 美菜服务器抓取登录态

美菜 `meicai_h5_decrypt_batch` 不在服务器上自动控制模拟器登录。服务器抓取只读取已授权登录态：

- `MEICAI_REQUEST_HEADERS`
- `MEICAI_COMMON_BODY`
- `MEICAI_ADDRESS_CONTEXT`（可选，用于抓取前切换到指定收货地址）

也可以设置 `MEICAI_SECRET_ENV_FILE` 指向服务器上的 env 文件。进程启动或抓取时会读取该文件；系统环境变量优先，不会被文件覆盖。

## env 文件示例

把文件放在仓库外或 `.local-secrets/` 这类不会提交的位置：

```bash
MEICAI_REQUEST_HEADERS='{"Device-Token":"...","Company-Token":"...","Passport-Token":"...","x-mc-city":"17","x-mc-area":"4402"}'
MEICAI_COMMON_BODY='{"tickets":"...","time_stamp":1780104178770,"salt_index":89,"mallSaltSign":"...","salt_sign":"...","_ENV_":{"source":"android","app_version":"8.7.0","city_id":"17","area_id":"4402"}}'
MEICAI_ADDRESS_CONTEXT='{"request_body":{"locationTo":"...","city_id":"17","area_id":"4402","tickets":"...","time_stamp":1780109580000,"salt_index":12,"mallSaltSign":"...","salt_sign":"...","_ENV_":{"source":"android","app_version":"8.7.0","city_id":"17","area_id":"4402","location":"..."}}}'
```

推荐直接保存 App 选择收货地址后的 `/api/auth/changeaddress` 脱敏请求 body 到 `MEICAI_ADDRESS_CONTEXT.request_body`，因为 `salt_sign` 通常和请求 body 绑定。`locationTo` 和 `_ENV_.location` 是美菜生成的地址上下文密文。不要在服务器 env 中保存明文收货地址、收货人、手机号或经纬度。

## 从抓包生成地址上下文

默认抓包工具会脱敏敏感字段，适合排查接口，不适合直接生成服务器可用 env。要生成 `MEICAI_ADDRESS_CONTEXT`，需要在私有环境保存一次未脱敏的 `/api/auth/changeaddress` 请求，然后执行：

```powershell
.\tools\start_meicai_capture.ps1 -AllowSecretCapture
adb shell settings put global http_proxy 192.168.3.108:8888
# 在美菜 App 里进入“选择地址”，点一次要抓取的收货地址
adb shell settings put global http_proxy :0
.\tools\stop_meicai_capture.ps1
```

私有模式只会把 `/api/auth/changeaddress` 原始请求额外写入 `.local-secrets/meicai_capture/meicai_secret_flows.jsonl`；普通抓包文件仍会脱敏。

```bash
python tools/extract_meicai_address_context.py \
  --input .local-secrets/meicai_capture/meicai_secret_flows.jsonl \
  --output .local-secrets/meicai_address_context.env
```

生成后把 `.local-secrets/meicai_address_context.env` 合并到服务器 `MEICAI_SECRET_ENV_FILE` 指向的文件中，或让进程启动脚本加载它。工具只会在命令行打印输出路径、`city_id` 和 `area_id`，不会打印 token 或签名。

## systemd 注入示例

```ini
[Service]
Environment=MEICAI_SECRET_ENV_FILE=/opt/battel-secrets/meicai.env
```

登录态过期、签名失效或接口返回加密 `data` 时，抓取会失败并提示刷新登录态；不会转 OCR。

当前正式链路会按 H5 bundle 重新生成 `mallSaltSign` / `salt_sign`，并解密 `getSpusByClass` 的 `encryption.type=3` 响应。服务器还需要带上 `tmp/meicai_h5_salts.json`，配置项为 `h5_salts_path`。

## 正式抓取与落库验收

确认登录态、地址上下文、分类树和 H5 salts 都齐全后，执行：

```powershell
python tools\validate_meicai_h5_server_crawl.py --secret-env-file .local-secrets\meicai_address_context.env
```

该工具会读取当前 `meicai_h5_decrypt_batch` 配置，跑一次正式服务器抓取，并核对：

- `price_records` 本轮新增数量是否等于抓取成功行数
- `tmp/meicai_crawl_audit.json` 中的分类数是否等于 `saleClass` 二级类目数
- 是否有分类命中 `max_pages` 截断

输出只包含统计与字段名，不打印 token、签名或地址密文。
