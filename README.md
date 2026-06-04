# 商品价格对比分析程序

一个基于 Python 的商品价格对比分析项目，当前以前后端分离模式运行：后端使用 FastAPI 提供真实报价与菜单采购接口，前端使用 Vue3 + Vite 展示市场汇总、趋势和采购建议。

项目运行时已收口为 MySQL 云库模式；本地 SQLite 仅保留给测试、迁移脚本和显式传入 `db_path` 的离线场景，不再作为运行时回退方案。

## 新增 Vue3 + FastAPI 终端版

项目当前使用的前后端结构：

- 后端 API：`FastAPI`
- 前端终端版：`Vue3 + Vite + Element Plus + ECharts`
- 已移除旧 `Streamlit` 页面，统一以 Vue 界面为准

### 后端启动

安装新增依赖后执行：

```bash
uvicorn main_api:app --reload --port 8000
```

### 前端启动

进入 `web/` 后执行：

```bash
npm install
npm run dev
```

前端默认通过 `/api` 访问后端；本地开发时由 Vite 自动代理到 `http://127.0.0.1:8000`。如需自定义，可参考 `web/.env.example`。

默认地址：

- API: `http://127.0.0.1:8000`
- Vue: `http://127.0.0.1:4273`

## 部署说明

推荐使用 `Nginx + Uvicorn` 部署：

- 前端：`web/` 下执行 `npm run build`，将 `web/dist/` 作为静态资源目录
- 后端：执行 `uvicorn main_api:app --host 127.0.0.1 --port 8000`
- 统一入口：由 Nginx 将 `/api/*` 反代到 FastAPI，将其余路径指向前端静态文件

Linux 部署如果不想写死 Python 绝对路径，优先使用根目录的 `start_backend.sh`：

```bash
chmod +x start_backend.sh
./start_backend.sh
```

如果你部署在宝塔面板，启动命令直接改成：

```bash
/bin/bash /lhcos-data/battel/backend/start_backend.sh
```

如果当前解释器里还没装 `uvicorn`，这个脚本会自动创建 `.venv` 并安装 `requirements.txt`。

完整部署清单见 `docs/deployment.md`。

## 2026-04 产品化升级

本轮不再把项目仅描述成“价格对比工具”，而是升级成可直接销售演示的经营决策产品：

- 新增品牌化销售首页，首次打开先进入销售化 Landing，再进入工作台
- 新增老板驾驶舱 / 经营信号页，优先展示“今天该关注什么、为什么、下一步怎么做”
- 后端新增统一决策接口，补齐信号概览、单品建议、采购增强建议、演示内容和套餐接口
- 菜单采购从“生成采购清单”升级为“时机 + 风险 + 推荐动作”的复合建议
- 前端移动端回归已覆盖销售首页进入工作台、老板驾驶舱和菜单采购增强路径

适合对外演示的主线已经变成：

1. 销售首页
2. 老板驾驶舱
3. 经营信号 / 单品时机建议
4. 菜单采购增强建议
5. 套餐报价与交付承接

演示脚本、套餐定位和新增接口说明见 `docs/sales-demo-playbook.md`。
如准备正式出售，建议同时阅读 `docs/commercial-boundary.md` 与 `docs/delivery-checklist.md`。

### 新增接口

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/signals/overview`
- `GET /api/signals/{identity_key}`
- `POST /api/procurement/recommend`
- `GET /api/sales/demo-content`
- `GET /api/pricing/packages`
- `GET /api/suppliers`
- `GET /api/suppliers/overview`
- `POST /api/suppliers`
- `PUT /api/suppliers/{supplier_id}`
- `GET /api/suppliers/{supplier_id}/quotes`
- `POST /api/supplier-prices`
- `POST /api/supplier-prices/{record_id}/invalidate`
- `GET /api/product/{identity_key}/supplier-quotes`

其中供应商相关接口当前分工如下：

- `GET /api/suppliers`：按启用状态返回供应商列表，前端用于后台供应商列表、筛选器和快速录价下拉数据源。
- `GET /api/suppliers/overview`：返回供应商管理台总览，包括启用数、分类覆盖、累计报价、分类统计和全局最近录价列表。
- `POST /api/suppliers`：新建供应商基础资料，包含联系人、电话、市场范围、主营分类、默认渠道、备注和启停状态。
- `PUT /api/suppliers/{supplier_id}`：更新指定供应商资料、启停状态以及已绑定账号信息，供应商管理台编辑表单直接调用该接口保存。
- `GET /api/suppliers/{supplier_id}/quotes`：获取指定供应商最近报价记录，支持后台查看该供应商的最近录价明细。
- `GET /api/suppliers/{supplier_id}/settlements`：获取指定供应商的结算台账列表，支持按状态、关键词分页筛选。
- `GET /api/supplier-settlements/{record_id}`：获取单张结算单详情及其关联报价记录，供后台详情弹窗查看。
- `POST /api/suppliers/{supplier_id}/settlements`：手工创建供应商结算单，可直接录入账期、总额、已付金额和付款信息。
- `PUT /api/supplier-settlements/{record_id}`：更新结算单的已付金额、状态、付款日期和备注。
- `POST /api/suppliers/{supplier_id}/settlements/build-from-quotes`：基于已选历史报价快速生成结算单，自动汇总报价条数、账期与金额。
- `POST /api/supplier-prices`：为指定供应商或临时供应商录入报价；未提供 `supplier_id` 时可按 `supplier_name` 自动补建供应商。
- `POST /api/supplier-prices/{record_id}/invalidate`：将历史报价标记为作废，保留审计记录，但默认不再参与前台公开价对比和后台有效报价统计。
- `GET /api/product/{identity_key}/supplier-quotes`：按商品聚合同步本地供应商报价、公开最低价、公开均价和价差标签，用于前台商品维度对比。

### 供应商 identity 审计与回填

供应商历史报价在早期可能存在“旧商品键”和“统一商品键”混用的情况，例如：

- 旧键：`一级豆油`
- 统一键：`一级豆油|公斤`

当前后端已兼容这两类键的查询，但为了让数据库状态更统一，仓库内额外提供了两类工具：

- `tools/audit_supplier_identity_keys.py`
  - 只读审计当前 `supplier_price_records.price_identity_key`
  - 输出哪些键仍是旧键、可映射到哪个统一键、涉及多少条报价记录
- `tools/backfill_supplier_identity_keys.py`
  - 默认只预览回填计划
  - 只有显式加 `--apply` 时才真正更新数据库

示例命令：

```bash
python -X utf8 tools/audit_supplier_identity_keys.py --json
python -X utf8 tools/backfill_supplier_identity_keys.py --json
python -X utf8 tools/backfill_supplier_identity_keys.py --apply
```

建议执行顺序：

1. 先跑 `audit` 确认旧键和候选统一键
2. 再跑 `backfill --json` 预览计划
3. 最后确认无误后执行 `backfill --apply`

这两个工具默认针对当前运行时数据库配置执行；如果你通过环境变量切到 MySQL，它们也会跟随当前配置工作。

### 账号与权限

当前版本已经补齐后台账号登录能力，默认规则如下：

- `POST /api/auth/login`：账号密码登录，返回 JWT Bearer token 与当前用户资料。
- `GET /api/auth/me`：读取当前登录用户，用于前端恢复登录态和权限边界。
- 默认管理员账号会在数据库初始化时自动创建：
  - 用户名：`admin`
  - 开发默认密码：`admin123`
  - 展示名：`系统管理员`
- 生产或预发环境必须设置 `BATTEL_ENV=production` 或 `BATTEL_ENV=staging`，并通过环境变量覆盖 `BATTEL_AUTH_SECRET` 与 `BATTEL_DEFAULT_ADMIN_PASSWORD`；否则认证模块会拒绝启动。
- 管理员账号可查看全部供应商、全部报价、全部日志与结算台账。
- 供应商账号只能查看并操作自己绑定的供应商资料、报价记录、操作日志和结算数据。
- 账号被停用后，登录接口会直接返回“当前账号已停用”；已有 token 再访问受保护接口时也会被后端拒绝。
- JWT 会由前端自动写入本地存储，并在后续请求里自动附带 `Authorization: Bearer ...`。
- 供应商资料创建/编辑时可直接绑定账号字段：`account_username`、`account_password`、`account_display_name`、`account_is_active`。
- 报价导入、复制、作废、结算创建/更新等后台审计动作，后端统一以当前登录账号作为操作人，不再信任前端直接透传的操作人名称。

### 当前已接通的 Vue 首版能力

- 地区筛选
- 市场汇总表
- 单品选择
- 单品跨市场趋势 / 单市场趋势接口
- 菜单采购方案 API
- 供应商报价录入与本地报价对比

### 供应商管理台能力

当前桌面端“供应商管理台”已经覆盖以下能力：

- 当前前端已拆成四个独立入口：采购前端 `/`、供应商门户 `/supplier-portal`、供应商管理台 `/supplier-backend`、平台后台 `/admin`。四端边界见 `docs/product-surface-architecture.md`。
- 进入供应商管理台前需先登录账号；当前供应商管理台已作为独立管理界面，通过按钮点击进入，而不是只在主工作区里切换标签。
- 主站 `App.vue` 已不再内嵌供应商管理台登录页或管理页，只保留“进入供应商管理台”入口；旧的 `?mode=supplier` / `?tab=supplier` 链路会自动跳转到 `/supplier-backend`。
- 供应商管理台登录页会明确提示：供应商日常自助录价、批量导入和查看自己的报价记录应进入 `/supplier-portal`，管理台只保留管理、审计和必要的管理员代录能力。
- 独立后台根层已强化为更完整的后台壳层，包含顶部状态栏、左侧后台导航、页面头和页面级摘要区，后台感不再依赖主站布局。
- 管理员登录后可看全局，供应商账号登录后默认只看到自己的数据。
- 后台根层会自动恢复本地 token，登录失效时会提示重新登录。
- 登录后会在后台头部明确显示当前账号、角色权限和当前数据范围，便于切换管理员/供应商账号时快速确认当前视角。
- 供应商列表浏览，支持按关键词、主营分类、启停状态筛选。
- 供应商基础资料维护，包括供应商名称、联系人、联系电话、市场范围、主营分类、默认渠道、备注和启停状态。
- 供应商资料维护时可直接创建或更新绑定账号，包括登录名、密码、展示名和启停状态。
- 管理员可直接在供应商管理里停用供应商账号；账号一旦停用，将无法继续登录，已有 token 访问受保护接口也会被拒绝。
- 供应商指标概览，展示启用供应商数、已覆盖分类数、最近录价时间和累计报价数。
- 分类概览区自动按干调类、蔬菜类等市场分类汇总供应商数量、启用数量、报价数和最近更新时间。
- 在后台直接为当前选中的供应商录入商品报价，填写报价、单位、箱价、含税价、库存状态和报价备注。
- 供应商管理台支持填写“操作人”，并自动记住本机最近一次填写的名称，用于录价、作废、导出等动作留痕。
- 录价前可先看到当前商品的公开最低价、供应商最低价和当前供应商最近报价，便于边录边比。
- 查看指定供应商最近报价记录，按商品展示最近录入的报价明细，并显示有效/作废状态。
- 历史报价支持“复制为新报价”，可将旧报价一键回填到录价表单后重新提交。
- 历史报价支持按有效/作废状态筛选，方便后台单独复查已作废记录。
- 历史报价支持按关键词搜索，并可切换“仅看当前商品”的历史记录，方便围绕单个商品连续录价。
- 历史报价支持按日期范围筛选，并可对当前筛选结果执行批量选择。
- 历史报价提供“今天 / 近7天 / 近30天”快捷日期筛选，并会高亮当前供应商的最新有效报价。
- 历史报价支持分页浏览，筛选条件改为后端执行，避免数据变多后前端只看到最近几十条。
- 历史报价支持“作废”与“修改作废原因”，作废后记录仍保留在后台历史中，但不会继续参与有效报价对比。
- 历史报价复制时会自动补充“复制自历史报价”的备注来源，便于区分人工新录与历史复用。
- 历史报价支持批量复制为新报价、批量作废，优先复用现有录价与作废接口完成连续操作。
- 历史报价支持下载 Excel 导入模板，并对当前选中供应商批量导入 Excel / CSV 报价，按对比键或商品名称匹配现有商品；导入前可先预览待导入行，并可选择“追加导入 / 跳过重复 / 覆盖最新”三种导入模式，预览阶段会提前诊断哪些行将被跳过或覆盖，失败行支持单独导出继续修正。
- 导入预览支持按“全部 / 将新增 / 将跳过 / 将覆盖 / 待修正 / 波动异常”分组查看，并补充当前有效报价详情，方便对干调类、蔬菜类等本地细分类商品快速排查风险。
- 批量导入支持配置重复判定字段和异常波动阈值，前端会把同一组规则同时用于预诊断与正式导入，避免预览与提交结果不一致。
- 新增供应商结算台账区，可查看当前供应商的结算单列表、账期、总额、已付、未付和付款状态。
- 支持手工创建结算单，也支持基于已选有效历史报价直接生成结算单，自动汇总报价条数与报价金额。
- 支持在台账列表内直接更新已付金额和付款日期，后端会自动重算未付金额并推导待付款 / 部分付款 / 已结清状态。
- 结算台账区顶部提供当前页统计卡，实时汇总待付款单数、部分付款单数、已结清单数、本页结算总额和未付金额，便于采购与财务快速对账。
- 支持将当前供应商结算台账直接导出为 Excel / CSV，方便采购、对账和财务留档。
- 结算台账支持按账期开始 / 结束日期做区间筛选，便于回看某个对账周期内的结算单。
- 支持打开单张结算单详情，查看账期、金额、创建人以及关联报价记录快照。
- 历史报价支持按当前筛选结果或已选记录导出 Excel / CSV，并保留最近导出、复制、作废、修改作废原因等后台操作日志。
- 最近操作日志支持按动作类型、操作人、关键词和日期范围筛选，方便单独查看导出、批量导入、复制、作废或修改作废原因记录。
- 最近操作日志会把当前筛选条件直接显示为标签，并支持一键清空，方便在手机端快速回到默认日志视图。
- 最近操作日志会把 `action_payload` 里的导入文件名、导入模式、总行数、成功/跳过/失败数、失败示例、成功记录 ID，以及导出范围、格式、行数等关键信息可视化展示，并支持单条详情弹窗。
- 日志详情弹窗已补齐“复制为新报价 / 作废报价 / 修改作废原因”的结构化信息，支持直接查看源记录、目标记录、作废前状态、旧原因和新原因，便于移动端审计回看。
- 日志详情弹窗已补齐“创建结算单 / 更新结算单 / 作废结算单 / 从报价生成结算单 / 导出结算台账”的结构化信息，可直接查看结算单标题、金额、条数、状态、作废原因与付款变化。
- 结算单创建、从报价生成、付款进度更新、作废也会进入统一的后台操作日志，便于供应商协同与账务审计。
- 最近操作日志支持分页浏览，并由后端按动作类型筛选后返回结果。
- 历史报价复制为新报价、批量导入、作废和导出日志都会记录真实操作人，便于后续审计和责任追溯。
- 批量导入、批量复制为新报价、批量作废完成后，后台会保留“最近一批操作结果”摘要，并支持导出 Excel / CSV 复盘或留档。
- “最近一批操作结果”区域会直接预览前几条处理结果，不必先导出文件才能确认本次操作影响。
- 查看后台全局最近录价列表，并可一键切换到对应供应商和商品继续处理。
- 商品选择与供应商录价联动，支持从商品列表切换目标商品后直接提交报价。

### 移动端供应商门户与管理台入口

移动端当前已按“采购端 / 供应商门户 / 供应商管理台 / 平台后台”拆分入口，适合在手机端快速补价，同时避免把管理导航混入采购工作区：

- 移动端底部导航只保留采购端核心路径：首页、行情、单品。
- 可从移动端首页“供应商门户”入口进入 `/supplier-portal`，用于供应商自助录价、批量导入和查看自己的报价记录。
- 可从移动端系统入口条进入 `/supplier-backend`，处理供应商管理、结算台账、操作日志和账号权限。
- 可从移动端系统入口条进入 `/admin`，处理平台抓取、来源覆盖和调度状态。
- 未登录时供应商门户或后台会先显示登录面板；登录后再进入对应角色的数据范围。
- 支持按当前商品查看本地供应商报价汇总、最低本地价、公开最低价、公开均价和最近录价时间。
- 支持选择已有供应商或临时填写供应商信息后快速录价。
- 支持录入联系人、市场分类、来源渠道、库存状态、报价、计价单位、箱价、含税价和备注。
- 支持查看当前商品下的供应商报价卡片列表，并显示比对标签、箱价、含税价、库存状态和录价时间。
- 支持在移动端用卡片方式查看批量导入预诊断结果，而不是依赖横向大表格；同样能看到当前有效报价、导入决定和异常波动提示。
- 支持移动端下按操作人、关键词、日期范围筛选最近操作日志，并将批量操作结果、日志详情和筛选表单压成单列布局，方便手机端连续审计。
- 支持在移动端以卡片方式查看供应商结算台账，并直接更新付款进度，无需切回桌面端。
- 供应商账号如果未绑定供应商，或绑定的供应商资料暂未同步到管理列表，会直接显示明确空状态和处理提示，而不是展示不可操作的录价表单。

## 合规提醒

请在抓取前遵守目标网站服务条款、robots 协议及相关法律法规。对于存在反爬限制、登录鉴权、动态渲染或禁止自动访问的网站，请不要绕过网站保护措施。本文项目仅提供面向自有页面、测试页面或明确允许抓取页面的基础实现。

## 商用与交付入口

如果项目已经进入出售或报价阶段，建议把以下文档作为标准附件一起给客户或内部销售同事：

- `docs/sales-demo-playbook.md`：销售演示顺序与套餐承接
- `docs/commercial-boundary.md`：商用边界、授权口径与签约前检查点
- `docs/delivery-checklist.md`：标准交付清单、验收路径与责任拆分

当前仓库适合出售的方式，建议优先采用“软件授权 + 私有部署 + 实施服务”的模式，而不是默认直接完整转让源码。

## 开发约定

提交代码前，请先阅读根目录 `AGENTS.md` 与项目级 `.helloagents/guidelines.md`。

- 代码以可读、可审阅为优先，保持命名清晰、逻辑分段明确，避免为了炫技做过度抽象。
- 仅在业务规则、边界条件和外部约定处补充简短注释，重点说明“为什么这样做”。
- 默认不为单次使用逻辑强行拆分细碎私有方法，只有存在明确复用价值时才提炼方法。

如果这两份文档与其他说明存在冲突，以 `AGENTS.md` 作为当前项目的规则来源。

## 设计工具链

项目当前采用三工具协同：

- `Figma`：团队设计真源与开发交接入口
- `Stitch`：AI 设计生成与方向探索
- `Pencil`：本地设计与个人实验

进入开发前的定稿必须回收进 Figma。完整规则、Codex MCP 接入模板和检查脚本见 `docs/design-toolchain.md` 与 `tools/design-mcp/`。

## MVP 功能

- 支持从 `config/products.json` 批量读取商品链接
- 支持通过 Vue 页面录入菜单并生成采购建议
- 支持侧边栏保存“常驻链接”并重复抓取
- 支持手动选择 `Requests` 静态抓取或 `Playwright` 动态抓取
- 支持设置默认抓取频率、抓取方式、超时、重试、请求间隔
- 支持站点级覆盖超时、重试、请求间隔、受限状态码与优先抓取方式
- 支持在页面直接编辑已有站点规则
- 失败抓取支持按类型自动诊断（限流/拦截、超时、规则失配、动态渲染、链接失效等）
- 失败诊断支持按类型汇总展示，并可按诊断类型、抓取方式筛选
- 站点规则管理页支持查看失败记录持久化后的站点失败概览
- 最近一次抓取结果支持展示实际生效的抓取参数
- 支持静态抓取失败后安全回退到 Playwright
- 自动抓取商品名称、当前价格、原价、促销信息、抓取时间、网站来源
- 支持录入商品品类、品牌、系列、规格
- 自动解析规格并计算单位价：
  - `500ml`
  - `1L`
  - `200ml*2`
  - `250g×4`
- SQLite 存储历史价格数据
- pandas 统计分析：
  - 当前最低价平台
  - 历史最低价
  - 平均价格
  - 价格波动幅度
  - 趋势判断
  - 当前最低单位价
  - 历史最低单位价
- plotly 图表：
  - 历史价格折线图
  - 平台当前价格柱状图
  - 最低价趋势图
  - 单位价对比图
  - 单位价历史趋势图
  - 最低单位价趋势图
- 支持导出 CSV / Excel
- 支持上传本地 CSV / Excel，与最近抓取结果自动匹配并生成对比结果
- 支持本地报价单启用 AI 辅助拆分，自动补全品类、品牌、系列、规格等空字段
- AI 辅助拆分默认关闭；未配置 API Key、请求失败或返回异常时会自动回退到基础规则解析
- 提供命令行抓取与 Vue 工作台
- 提供基础日志记录、超时处理与解析失败提示

## 项目目录结构

```text
battel/
├─ main.py
├─ main_api.py
├─ requirements.txt
├─ README.md
├─ pytest.ini
├─ config/
│  ├─ products.json
│  ├─ sites.json
│  ├─ runtime.json
│  └─ alerts.json
├─ crawler/
│  ├─ __init__.py
│  ├─ base.py
│  ├─ fetcher.py
│  ├─ requests_fetcher.py
│  └─ playwright_fetcher.py
├─ parsers/
│  ├─ __init__.py
│  ├─ normalizer.py
│  └─ site_parser.py
├─ storage/
│  ├─ __init__.py
│  └─ database.py
├─ analysis/
│  ├─ __init__.py
│  ├─ metrics.py
│  └─ alerts.py
├─ visualization/
│  ├─ __init__.py
│  └─ charts.py
├─ ui/
│  ├─ __init__.py
│  └─ components.py
├─ utils/
│  ├─ __init__.py
│  ├─ config_loader.py
│  ├─ logger.py
│  └─ scheduler.py
├─ services/
│  ├─ __init__.py
│  └─ ai_extractor.py
└─ tests/
   ├─ test_metrics.py
   └─ test_normalizer.py
```

## 技术选型

- Python 3.8+
- requests + BeautifulSoup：静态页面抓取
- Playwright：动态页面扩展抓取
- SQLite：本地存储
- pandas：数据分析
- plotly：可视化
- FastAPI + Vue：页面展示与接口联动
- Anthropic SDK：可选 AI 辅助拆分

## 数据库设计

### 表一：products

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| product_key | TEXT | 商品唯一标识 |
| group_name | TEXT | 商品分组，用于同款跨平台对比 |
| product_name | TEXT | 商品名称 |
| source_url | TEXT | 商品链接 |
| site_name | TEXT | 平台名称 |
| category | TEXT | 商品品类，如酱油 |
| brand | TEXT | 品牌，如海天 |
| product_series | TEXT | 系列/型号 |
| spec_text | TEXT | 规格原文，如 500ml |
| compare_key | TEXT | 精确对比键 |
| created_at | TEXT | 创建时间 |

### 表二：price_records

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| product_id | INTEGER | 关联商品 |
| captured_at | TEXT | 抓取时间 |
| current_price | REAL | 当前价格 |
| original_price | REAL | 原价 |
| promotion_text | TEXT | 促销信息 |
| currency | TEXT | 币种 |
| availability | TEXT | 可用状态 |
| raw_payload | TEXT | 原始解析结果 |
| unit_name | TEXT | 标准单位，当前支持 ml / g |
| unit_value | REAL | 标准化规格数值 |
| unit_price | REAL | 单位价，按每 100ml 或每 100g |

### 表三：failed_crawl_records

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| product_key | TEXT | 商品唯一标识 |
| captured_at | TEXT | 失败抓取时间 |
| group_name | TEXT | 商品分组 |
| product_name | TEXT | 商品名称 |
| source_url | TEXT | 抓取链接 |
| site_name | TEXT | 站点名称 |
| fetch_mode | TEXT | 实际抓取方式 |
| status_code | INTEGER | HTTP 状态码 |
| error | TEXT | 失败原因 |
| suggestion | TEXT | 建议处理方式 |
| fallback_used | INTEGER | 是否使用回退抓取 |
| raw_payload | TEXT | 原始失败信息 |

### 表四：local_compare_records

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| captured_at | TEXT | 对比时间 |
| batch_name | TEXT | 对比批次名 |
| match_status | TEXT | 匹配状态 |
| matched_by | TEXT | 匹配方式 |
| price_relation | TEXT | 抓取价与本地价关系 |
| source_row_no | TEXT | 本地报价单原始序号 |
| group_name | TEXT | 本地商品分组 |
| product_name | TEXT | 本地商品名称 |
| category | TEXT | 本地品类 |
| brand | TEXT | 本地品牌 |
| product_series | TEXT | 本地系列 |
| spec_text | TEXT | 本地规格 |
| site_name | TEXT | 本地来源平台 |
| local_price | REAL | 本地价格 |
| box_price | REAL | 整箱/整件报价 |
| tax_price | REAL | 含税报价 |
| remarks | TEXT | 本地报价备注 |
| market_category | TEXT | 本地市场细分类别，如干调类/蔬菜类 |
| channel | TEXT | 本地报价来源渠道，如微信小程序/Excel |
| matched_group_name | TEXT | 抓取匹配分组 |
| matched_product_name | TEXT | 抓取匹配商品名称 |
| matched_site_name | TEXT | 抓取匹配平台 |
| current_price | REAL | 抓取价格 |
| price_diff | REAL | 抓取价 - 本地价 |
| price_diff_rate | REAL | 价差比例 |
| promotion_text | TEXT | 抓取促销信息 |
| raw_payload | TEXT | 原始对比结果 |

### 表五：suppliers

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| supplier_name | TEXT | 供应商名称 |
| contact_name | TEXT | 联系人 |
| contact_phone | TEXT | 联系电话 |
| market_scope | TEXT | 市场范围，如本地市场 |
| market_category | TEXT | 供应商主营分类，如干调类/蔬菜类 |
| channel | TEXT | 默认报价渠道，如微信小程序/门店直报 |
| notes | TEXT | 备注 |
| is_active | INTEGER | 是否启用 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 最近更新时间 |

### 表六：supplier_price_records

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| supplier_id | INTEGER | 关联供应商 |
| price_identity_key | TEXT | 当前系统商品对比键 |
| price_identity_label | TEXT | 商品展示名 |
| product_name | TEXT | 商品名称 |
| category | TEXT | 商品分类 |
| spec_text | TEXT | 商品规格 |
| market_category | TEXT | 本地市场细分类别 |
| channel | TEXT | 本次报价渠道 |
| quote_price | REAL | 供应商报价 |
| quote_unit | TEXT | 报价单位 |
| box_price | REAL | 箱价/件价 |
| tax_price | REAL | 含税价 |
| inventory_status | TEXT | 库存状态 |
| remarks | TEXT | 备注 |
| quoted_by | TEXT | 报价人 |
| quoted_at | TEXT | 报价时间 |
| updated_at | TEXT | 写入更新时间 |

### 表七：supplier_settlement_records

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| supplier_id | INTEGER | 关联供应商 |
| settlement_title | TEXT | 结算单标题 |
| period_start | TEXT | 结算周期开始 |
| period_end | TEXT | 结算周期结束 |
| quote_record_ids | TEXT | 关联的历史报价记录 ID 列表 |
| record_count | INTEGER | 关联报价条数 |
| total_amount | REAL | 结算总金额 |
| paid_amount | REAL | 已付金额 |
| pending_amount | REAL | 未付金额 |
| status | TEXT | 付款状态：pending / partial / paid / cancelled |
| payment_due_date | TEXT | 应付日期 |
| payment_date | TEXT | 实付日期 |
| remarks | TEXT | 备注 |
| created_by | TEXT | 创建人 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 最近更新时间 |

## 抓取流程说明

1. 从页面输入、侧边栏常驻链接或 `config/products.json` 读取商品链接。
2. 根据 URL 域名匹配 `config/sites.json` 中的站点规则。
3. 使用 `requests` 发起请求，设置超时、User-Agent，并记录异常；若站点规则要求，也可优先走 Playwright。
4. 使用 BeautifulSoup 按 CSS 选择器提取名称、价格、原价、促销信息。
5. 清洗价格文本，统一为数值类型。
6. 对规格文本做标准化，计算 `unit_name`、`unit_value`、`unit_price`。
7. 将商品与价格记录保存到 SQLite，同时保存本次抓取的 `fetch_metadata` 便于后续核对。
8. 从数据库读取历史数据并生成统计结果与图表，最近一次抓取结果表可直接查看实际生效的抓取参数。

## 分析逻辑说明

`analysis/metrics.py` 主要实现：

- `summarize_latest_prices`：提取每个商品最近一次价格
- `current_lowest_price_platform`：按同款商品找当前最低价平台
- `compute_group_metrics`：计算历史最低价、最高价、平均价、波动幅度
- `summarize_latest_unit_prices`：提取可用单位价的最新记录
- `current_lowest_unit_price`：按品类找当前最低单位价商品
- `compute_unit_metrics`：计算单位价的历史最低值、平均值、波动幅度
- `detect_trend` / `detect_unit_trend`：根据最近 2~3 次记录判断上涨、下降、平稳或波动
- `standardize_local_compare_file`：标准化上传的本地对比文件字段
- `apply_ai_structured_enrichment`：按需调用 AI 补全本地报价单中的结构化字段，并在失败时保留原始结果
- `build_local_compare_result`：将本地文件与最近抓取结果自动匹配并计算价差
- `export_dataframe`：导出 CSV / Excel

### AI 辅助拆分说明

- 入口：Vue 菜单采购页导入或录入菜单后触发 AI 辅助拆分
- 处理范围：仅处理 `category`、`brand`、`product_series`、`spec_text` 等为空的行
- 覆盖策略：只补空值，不覆盖用户在文件中已经提供的字段
- 失败策略：AI 未启用、未配置 `ANTHROPIC_API_KEY`、接口报错或返回异常时，自动回退到基础规则解析
- 结果标记：标准化预览表会额外展示 `ai_enriched` 和 `ai_remarks`

## 图表生成逻辑

`visualization/charts.py` 提供：

- `build_price_history_chart`：历史价格折线图
- `build_platform_bar_chart`：当前平台价格柱状图
- `build_lowest_price_trend_chart`：最低价趋势图
- `build_unit_price_bar_chart`：单位价对比图
- `build_unit_price_history_chart`：单位价历史趋势图
- `build_lowest_unit_price_trend_chart`：最低单位价趋势图

## 配置说明

### 1. 商品配置 `config/products.json`

```json
[
  {
    "product_key": "lencai-miniapp-dried-goods",
    "group_name": "本地市场源",
    "product_name": "莲菜网小程序·干调类",
    "source_name": "莲菜网",
    "category": "干调类",
    "source_type": "batch",
    "strategy": "liancai_h5_batch",
    "url": "http://m.liancaiwang.cn",
    "enabled": false,
    "market_scope": "本地市场",
    "market_category": "干调类",
    "channel": "微信H5",
    "notes": "启用前需设置 LIANCAI_PHONE / LIANCAI_PASSWORD 环境变量"
  }
]
```

字段说明：

- `group_name`：同款跨平台对比时使用
- `category`：同类商品对比时使用
- `brand`：品牌
- `product_series`：系列/型号
- `spec_text`：规格文本，系统会自动尝试换算单位价
- `enabled`：是否参与抓取；对需要账号环境变量或仍在观察的本地来源建议先设为 `false`
- `source_name`：来源名称，来源覆盖区会优先展示该值
- `market_scope`：来源范围，例如 `全国公开市场`、`本地市场`
- `market_category`：来源细分类目，例如 `干调类`、`蔬菜类`
- `channel`：来源渠道，例如 `公开接口`、`微信H5`
- `notes`：来源接入说明或限制说明

对于像“莲菜网”这样的本地市场来源，当前可以优先接入其 H5 分类抓取链路；运行前通过环境变量提供测试账号，确认分类和分页稳定后再启用到正式调度。

莲菜网 H5 抓取链路的上线建议：

- 在线上环境设置 `LIANCAI_PHONE` / `LIANCAI_PASSWORD`
- 先保持 `config/products.json` 中对应来源 `enabled=false`
- 先用工具脚本验证分类和分页：

```bash
python -X utf8 tools/fetch_liancai_h5.py --phone "$LIANCAI_PHONE" --password "$LIANCAI_PASSWORD" --list-categories
python -X utf8 tools/fetch_liancai_h5.py --phone "$LIANCAI_PHONE" --password "$LIANCAI_PASSWORD" --category-id 6 --page-from 1 --page-to 2
```

- 确认输出正常后，再将对应来源切为 `enabled=true`
- 生产建议使用专用采集账号，不要直接使用个人常用账号

对于“郑州中部两岸海鲜物流园”这类本地批发市场，如果暂未找到稳定公开实时价格接口，应先按 `manual_quote` 登记为禁用来源，沉淀市场名称、地址、经营品类和接入备注；后续通过人工录价、商户授权数据或正式接口再启用。

### 2. 站点规则 `config/sites.json`

```json
[
  {
    "site_name": "示例商城A",
    "domains": ["example.com"],
    "name_selectors": ["h1.product-title", "title"],
    "price_selectors": [".price-current", ".sale-price"],
    "original_price_selectors": [".price-original"],
    "promotion_selectors": [".promotion"],
    "preferred_fetch_mode": "requests",
    "timeout_seconds": 15,
    "retry_count": 2,
    "request_delay_seconds": 1.0,
    "blocked_status_codes": [403, 429],
    "notes": "静态页优先 Requests"
  }
]
```

站点规则除了解析选择器外，还支持基础抓取策略字段，并且这些字段会在实际抓取时按站点生效：

- `preferred_fetch_mode`：`requests` / `playwright` / `requests_only`
- `timeout_seconds`：站点建议超时
- `retry_count`：站点建议重试次数
- `request_delay_seconds`：站点建议请求间隔
- `blocked_status_codes`：判定可能受限的状态码
- `playwright_wait_until`：Playwright 页面等待策略
- `custom_headers`：站点级自定义请求头
- `notes`：站点备注

页面中的“站点规则管理”除了新增、删除、导入、导出外，也支持直接编辑已有规则，并展示数据库中最近失败记录汇总出的站点失败概览，适合在站点结构变化后快速修正。

如果某个网站页面结构发生变化，只需要调整 `sites.json` 的 CSS 选择器；如果网站是动态渲染，应改用可替换的浏览器抓取器。

### 3. 运行时配置 `config/runtime.json`

```json
{
  "schedule": {
    "enabled": false,
    "interval_seconds": 3600,
    "fetch_mode": "requests",
    "target_scope": "all_saved"
  },
  "crawler": {
    "default_timeout": 15,
    "default_retries": 2,
    "default_delay": 1.0,
    "fallback_to_playwright": true,
    "blocked_status_codes": [403, 429]
  },
  "ai": {
    "enabled": false,
    "provider": "anthropic",
    "model": "claude-opus-4-6",
    "api_key_env": "ANTHROPIC_API_KEY",
    "timeout_seconds": 20,
    "max_rows_per_run": 20,
    "batch_size": 5
  }
}
```

该文件用于保存页面里的默认定时抓取、基础反爬配置以及可选 AI 辅助拆分配置。最近一次手动抓取结果表也会展示本次实际生效的 `timeout`、`retries`、`delay`、`timeout_ms` 与 `blocked_status_codes`，便于核对站点级覆盖是否生效。

如需启用 AI 辅助拆分，请先设置环境变量：

```bash
export ANTHROPIC_API_KEY="你的密钥"
```

Windows PowerShell 可使用：

```powershell
$env:ANTHROPIC_API_KEY="你的密钥"
```

## 安装方式

推荐统一使用 `py -3.8`，避免系统默认 `python` 指向其他版本导致依赖装错环境。

```bash
py -3.8 -m pip install -r requirements.txt
```

如果需要 Playwright：

```bash
py -3.8 -m playwright install chromium
```

## 启动方式

### 1. 初始化数据库

```bash
py -3.8 main.py init-db
```

### 2. 执行一次抓取

```bash
py -3.8 main.py crawl --config config/products.json --sites config/sites.json
```

如果目标页面依赖 JavaScript 渲染，可切换为 Playwright：

```bash
py -3.8 main.py crawl --config config/products.json --sites config/sites.json --fetch-mode playwright
```

### 3. 导出统计结果

```bash
py -3.8 main.py export --output exports/price_analysis.csv
```

### 4. 启动 Vue 页面

```bash
cd web
npm install
npm run dev
```

默认本地地址为 `http://127.0.0.1:4273`。

如需覆盖默认联调目标，可在 `web/` 目录下配置环境变量：

```bash
VITE_API_BASE_URL=/api
VITE_DEV_API_TARGET=http://127.0.0.1:8000
```

### 5. 基础定时抓取

```bash
py -3.8 main.py schedule --seconds 3600
```

也可以按分钟指定：

```bash
py -3.8 main.py schedule --minutes 30
```

如需定时抓取动态页面：

```bash
py -3.8 main.py schedule --minutes 60 --fetch-mode playwright
```

如果不传 `--seconds` / `--minutes` / `--fetch-mode`，CLI 会自动读取 `config/runtime.json` 中的默认值。

> 说明：当前定时任务是基础循环版本，适合本地 MVP 演示。生产环境建议使用 APScheduler、Windows 任务计划程序、cron 或容器调度。

## 页面功能

- 侧边栏支持保存“常驻链接”，写入 `config/products.json`
- 抓取与结果页支持设置默认抓取频率、抓取方式、超时、重试和请求间隔
- 页面会生成对应的 CLI 定时抓取命令，便于长期运行
- 支持录入品类、品牌、系列、规格
- 支持从侧边栏选择常驻链接并抓取选中/全部商品
- 支持切换抓取方式：
  - Requests 静态抓取
  - Playwright 动态抓取
- 支持手动输入商品链接并立即抓取
- 支持查看最近一次抓取结果
- 最近抓取失败会显示诊断类型、诊断结论与处理建议
- 失败诊断区支持按诊断类型汇总，并可按诊断类型、抓取方式、站点筛选
- 站点规则管理页支持查看数据库中的站点失败概览与失败历史导出
- 支持在价格分析页切换：
  - 总价对比
  - 单位价对比
- 支持按商品分组、品类、品牌筛选
- 支持查看商品历史价格曲线
- 支持上传本地 CSV / Excel 文件，自动匹配相同商品并生成本地价与抓取价对比结果
- 本地对比结果自动入库，可按批次查看历史对比记录
- 支持查看历史批次摘要、当前批次价差图，并可删除指定历史批次
- 支持对比结果导出为 CSV 或 Excel
- 支持总价提醒与单位价提醒
- 支持导出分析结果为 CSV 或 Excel

## 示例输入输出

### 输入
- `config/products.json` 中配置多个商品链接
- `config/sites.json` 中配置各平台选择器规则
- 在页面录入：分组、品类、品牌、系列、规格、链接

### 输出
- SQLite 历史价格库：`data/price_tracker.db`
- 日志文件：`logs/app.log`
- 导出文件：`exports/price_analysis.csv`
- 本地对比导出文件：`local_compare_result.csv` / `local_compare_result.xlsx`
- 页面图表：历史价格曲线、平台价格柱状图、最低价趋势图、单位价趋势图

## 反爬与失败处理说明

当前版本仅提供合规、基础的失败处理能力：

- 合理的超时、重试、请求间隔
- 对 `403`、`429` 等状态码给出受限提示
- 对疑似 JavaScript 骨架页自动回退到 Playwright
- 页面展示失败原因、状态码、建议处理方式
- 失败诊断支持汇总各类型失败次数与占比，并支持页面筛选查看
- 通过站点规则记录“推荐抓取方式”和备注
- 对常见失败自动归类为：
  - 限流/拦截
  - 鉴权/访问限制
  - 链接失效
  - 站点异常
  - 超时
  - 规则失配
  - 动态渲染
  - 通用失败

不提供以下能力：

- 验证码绕过
- 代理池轮换
- 指纹伪装
- 登录态盗用
- 高频并发抓取

## 运行测试

```bash
py -3.8 -m pytest
```

前端移动端回归可单独执行：

```bash
cd web
npx playwright test tests/mobile-regression.spec.ts
```

如果本机前端不是默认 `http://127.0.0.1:4273`，可显式指定 Playwright 联调地址；后端地址也可按需覆盖：

```bash
cd web
PLAYWRIGHT_BASE_URL=http://127.0.0.1:5173 PLAYWRIGHT_BACKEND_URL=http://127.0.0.1:8000 npx playwright test tests/mobile-regression.spec.ts
```

Windows PowerShell 示例：

```powershell
cd web
$env:PLAYWRIGHT_BASE_URL="http://127.0.0.1:5173"; $env:PLAYWRIGHT_BACKEND_URL="http://127.0.0.1:8000"; npx playwright test tests/mobile-regression.spec.ts
```

如需跑“真实数据页面回归”，可执行：

```bash
cd web
npm run test:e2e:real
```

这组用例会：

- 先构建 `web/dist`
- 自动启动本地 FastAPI 后端与静态前端
- 使用真实管理员账号登录
- 对真实数据执行页面回归，而不是走 mock API

当前已固定的真实样本包括：

- `三黄鸡 | 公斤`：验证趋势页能同时展示“官方参考源”和“主价格源”
- `一级豆油 | 公斤`：验证供应商报价对照页能显示真实本地报价，并且公开来源摘要不会重复拼接

当前这组用例已覆盖：

- 移动端首页到汇总行情、单品趋势、供应商门户入口的主路径
- 管理员账号登录并进入供应商门户
- 供应商账号未绑定供应商时的明确空状态提示
- 桌面端管理员登录进入供应商管理台
- 桌面端供应商门户独立承载供应商录价前端
- 桌面端平台后台独立承载抓取和来源治理
- 桌面端供应商账号进入受限后台视图
- 桌面端停用账号登录时的明确错误提示
- 桌面端管理员停用供应商账号并保存后的交互链路

## 常见问题

### 1. 默认 `python` 与项目依赖环境不一致

如果执行 `python main.py` 或 `uvicorn main_api:app` 提示缺少 `pandas` 或 `anthropic`，通常是系统默认解释器不是项目实际安装依赖的版本。优先改用 `py -3.8` 运行全部命令。

### 2. Playwright 已安装但仍无法抓取动态页面

除安装 Python 包外，还需要执行：

```bash
py -3.8 -m playwright install chromium
```

### 3. pip 或 requests 出现代理异常

如出现 `ProxyError`、`Cannot connect to proxy`、下载中断等问题，请先检查系统代理、pip 镜像或本机网络配置，再重试依赖安装或抓取。

### 4. 示例链接抓取失败或提示无站点规则

示例配置主要用于演示流程，实际抓取前请根据目标页面补充 `config/sites.json` 的域名规则、选择器和抓取方式。

## 最小可运行版本说明

当前版本是 MVP，重点是：

- 跑通配置读取 → 抓取 → 清洗 → 存储 → 分析 → 展示 → 导出 全链路
- 支持同款商品跨平台总价对比
- 支持同类商品按单位价做合理比较
- 使用配置化选择器支持后续扩展更多站点
- 保持抓取器可替换，便于接入 Playwright / Selenium

## 后续扩展建议

1. 增加更丰富的规格识别规则，如盒、袋、片、支
2. 支持单位价换算策略配置
3. 增加 Playwright 抓取器自动切换
4. 增加价格预警通知
5. 增加 FastAPI 服务接口
6. 增加更完整的异常分类与重试策略

## 注意事项

- 示例配置中的链接为演示用途，不保证存在真实可抓取页面。
- 对无法直接抓取的网站，应通过合法授权接口、自有数据源或可替换抓取器接入，不应绕过站点限制。
