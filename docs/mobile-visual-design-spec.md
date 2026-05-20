# 移动端视觉优化复盘与设计规范

## 1. 本次优化的负面影响总览

本次移动端 UI 优化主要通过 `web/src/styles.css:3478` 之后新增一整段 `@media (max-width: 720px)` 覆盖规则完成。该方式虽然没有改动业务逻辑，但在视觉上存在明显风险：它不是替换原有移动端样式，而是在 `web/src/styles.css:2795` 之后已有移动端规则的基础上再次叠加，因此容易造成颜色、圆角、阴影、间距和层级重复加强。

核心结论：本次变丑的主要原因不是某一个颜色错误，而是“高饱和渐变 + 大圆角 + 强阴影 + 半透明毛玻璃 + 多层伪元素”同时叠加，导致界面从原先偏清爽、轻量的移动工作台，变成视觉噪音较高、层级过重、信息密度下降的界面。

## 2. 逐项问题清单

### 2.1 背景颜色与渐变过度复杂

问题表现：

- 页面背景叠加了多层径向渐变和线性渐变。
- 顶部区域、卡片区域、图表区域又各自叠加渐变。
- 蓝色、青色、橙色同时出现，导致品牌主色不聚焦。
- 在小屏上容易出现“到处都在发光”的廉价感。

问题代码：

```css
.market-mobile-home,
.market-mobile-shell {
  background:
    radial-gradient(circle at -8% -4%, rgba(37, 99, 235, 0.3), transparent 34%),
    radial-gradient(circle at 106% 6%, rgba(245, 158, 11, 0.22), transparent 32%),
    linear-gradient(180deg, #f4f8ff 0%, #eef6ff 42%, #f8fafc 100%);
}
```

建议标准：

- 页面背景只保留 1 个低对比度线性渐变。
- 径向光斑最多保留 1 个，透明度不超过 `0.12`。
- 橙色只用于风险、提醒、价格波动，不用于大面积背景装饰。

### 2.2 Hero 区过度“炫技”，压过业务内容

问题表现：

- Hero 区使用了深蓝、亮蓝、青色大面积渐变。
- `box-shadow: 0 24px 52px` 在移动端过重。
- 伪元素圆形装饰面积过大，容易遮挡或干扰文字区域。
- 标题字号使用 `clamp(25px, 7.2vw, 34px)`，在部分机型上显得过大。

问题代码：

```css
.market-mobile-home-hero,
.market-mobile-workspace-hero,
.trend-workspace-hero {
  border-radius: 30px;
  background:
    radial-gradient(circle at 18% 16%, rgba(255, 255, 255, 0.3), transparent 28%),
    radial-gradient(circle at 92% 12%, rgba(251, 191, 36, 0.32), transparent 28%),
    linear-gradient(135deg, #0f3b91 0%, #2563eb 50%, #38bdf8 100%);
  box-shadow: 0 24px 52px rgba(37, 99, 235, 0.28);
}
```

建议标准：

- Hero 主渐变只使用 `#1d4ed8` 到 `#2563eb`。
- Hero 圆角建议 `22px` 到 `24px`，避免超过卡片系统太多。
- Hero 阴影建议 `0 16px 34px rgba(37, 99, 235, 0.18)`。
- 标题移动端建议 `24px` 到 `28px`，行高 `1.12` 到 `1.18`。

### 2.3 卡片圆角和阴影过重，导致界面“胖”和拥挤

问题表现：

- 多数卡片被统一拉到 `24px` 圆角。
- 次级卡片也被设置到 `20px` 圆角。
- 每层卡片都有阴影，导致滚动页面层级混乱。
- 行情列表、趋势图表、预警卡片失去区分，所有模块都像主卡片。

问题代码：

```css
.market-mobile-section,
.market-mobile-card,
.market-mobile-table-card,
.trend-mobile-table-card,
.trend-list-shell,
.market-mobile-alert-card,
.menu-mobile-card,
.source-coverage-card {
  border-radius: 24px;
  box-shadow: 0 16px 38px rgba(15, 23, 42, 0.08);
}
```

建议标准：

- 页面主容器卡片：`18px` 到 `20px`。
- 信息列表卡片：`14px` 到 `16px`。
- 筛选、标签、按钮：`999px` 或 `12px` 到 `14px`。
- 阴影只允许主卡片使用；列表行优先用边框和背景区分。

### 2.4 首个卡片强行高亮，破坏信息优先级

问题表现：

- 所有 `.first-child` 被统一高亮为蓝色渐变。
- 第一个卡片并不一定是最重要的信息。
- 预警 KPI 第一个卡片被强行变成主色，可能弱化真实的上涨、下跌、风险语义。
- 业务语义色被视觉装饰色覆盖。

问题代码：

```css
.market-mobile-task-card:first-child,
.market-mobile-system-card:first-child,
.trend-mobile-pill:first-child,
.market-mobile-alert-kpis article:first-child {
  background: linear-gradient(135deg, #1d4ed8, #2563eb 62%, #0ea5e9);
}
```

建议标准：

- 不使用结构选择器决定视觉优先级。
- 只有业务明确标记为“重点”“推荐”“风险最高”的组件才可高亮。
- KPI 颜色必须跟随业务语义：上涨用红色，下跌用绿色，预警用橙色，普通指标用蓝灰。

### 2.5 行情卡片新增左侧装饰条，可能干扰点击列表

问题表现：

- `.market-mobile-table-row::after` 给每条行情都加了蓝色竖条。
- 蓝色竖条会让所有商品看起来都是重点状态。
- 列表密集时，竖条形成视觉噪音。
- 如果卡片本身已有商品图标和价格强调，竖条属于重复强调。

问题代码：

```css
.market-mobile-product-card::after,
.market-mobile-table-row::after {
  inset: 10px auto 10px 0;
  width: 4px;
  background: linear-gradient(180deg, #2563eb, #38bdf8);
}
```

建议标准：

- 普通列表行不加装饰条。
- 只有预警、推荐采购、异常波动等状态才出现左侧状态条。
- 状态条颜色跟随状态，而不是固定蓝色。

### 2.6 价格字号过大，压缩商品信息空间

问题表现：

- 移动端价格被放大到 `24px`。
- 价格、单位、市场、时间会在小屏上互相挤压。
- 价格成为唯一视觉焦点，削弱商品名和来源信息。

问题代码：

```css
.market-mobile-product-price b,
.market-mobile-product-middle b {
  font-size: 24px;
  letter-spacing: -0.04em;
}
```

建议标准：

- 列表卡片价格建议 `20px` 到 `22px`。
- 详情或 Hero 中的核心价格可用 `24px`。
- 单位文字应为 `11px` 到 `12px`，颜色 `#64748b`。

### 2.7 底部导航过重，占用过多可视空间

问题表现：

- 底部导航高度提升到 `56px`，外加容器 padding 和阴影，整体视觉占位过大。
- `backdrop-filter: blur(22px)` 在低端机上可能影响性能。
- 激活态为深蓝到亮青渐变，和 Hero、卡片高亮重复。

问题代码：

```css
.market-mobile-bottom-nav {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 20px 46px rgba(15, 23, 42, 0.16);
  backdrop-filter: blur(22px);
}

.market-mobile-bottom-item {
  min-height: 56px;
}
```

建议标准：

- 底部导航容器高度控制在 `64px` 到 `72px`。
- 单项最小高度 `48px` 到 `52px`。
- 阴影不超过 `0 12px 28px rgba(15, 23, 42, 0.12)`。
- 毛玻璃模糊建议 `12px` 到 `16px`。

### 2.8 透明与毛玻璃使用过多，降低阅读稳定性

问题表现：

- 多个容器同时使用 `rgba` 背景和 `backdrop-filter`。
- 背景渐变透到内容层，导致文字对比度不稳定。
- 在截图中可能显得高级，但在真实数据长列表中容易疲劳。

问题代码：

```css
background: rgba(255, 255, 255, 0.78);
backdrop-filter: blur(14px);
```

建议标准：

- 只有固定导航、顶部浮层可使用毛玻璃。
- 内容卡片背景应接近不透明，建议 `rgba(255, 255, 255, 0.96)` 或纯白。
- 正文文本对比度需始终满足深色文字在浅底上清晰可读。

### 2.9 代码组织方式增加后续维护风险

问题表现：

- 新增覆盖块位于文件末尾，优先级天然高于前面所有移动端规则。
- 同一选择器在多个 `@media (max-width: 720px)` 中重复定义。
- 后续开发者难以判断哪个规则才是最终视觉标准。

问题位置：

- 原移动端规则：`web/src/styles.css:2795`
- 第一轮移动端增强规则：`web/src/styles.css:3285`
- 本次新增覆盖规则：`web/src/styles.css:3478`

建议标准：

- 合并重复移动端规则，避免文件末尾追加式覆盖。
- 按模块分组：页面背景、Hero、卡片、列表、趋势、预警、底部导航。
- 每个组件选择器只保留一个最终定义块。

## 3. 优化前后对比依据

### 3.1 可用截图依据

当前仓库中已有移动端截图位于：

- `e:\battel\.tmp\ui-screenshots\mobile-landing.png`
- `e:\battel\.tmp\ui-screenshots\mobile-workbench-summary.png`
- `e:\battel\.tmp\ui-screenshots\mobile-workbench-trend.png`
- `e:\battel\.tmp\ui-screenshots\mobile-workbench-trend-current.png`
- `e:\battel\.tmp\ui-screenshots\mobile-workbench-alerts.png`

这些截图可以作为“优化前或上一轮稳定状态”的参考基线。由于当前不能在不启动 dev 服务的情况下生成最新截图，建议在允许启动服务后重新生成一组当前截图，并与上述文件进行并排对比。

### 3.2 代码片段对比

优化前的移动端基础规则更克制：

```css
.market-mobile-home,
.market-mobile-shell {
  background:
    radial-gradient(circle at 14% 0, rgba(37, 99, 235, 0.18), transparent 34%),
    radial-gradient(circle at 90% 12%, rgba(245, 158, 11, 0.16), transparent 30%),
    linear-gradient(180deg, #f7fbff 0%, #eef5fb 52%, #e7eef7 100%);
}
```

本次新增规则进一步加深光斑和色彩：

```css
.market-mobile-home,
.market-mobile-shell {
  background:
    radial-gradient(circle at -8% -4%, rgba(37, 99, 235, 0.3), transparent 34%),
    radial-gradient(circle at 106% 6%, rgba(245, 158, 11, 0.22), transparent 32%),
    linear-gradient(180deg, #f4f8ff 0%, #eef6ff 42%, #f8fafc 100%);
}
```

优化前 Hero 规则较统一：

```css
.market-mobile-home-hero,
.market-mobile-workspace-hero,
.trend-workspace-hero {
  border-radius: 24px;
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 52%, #60a5fa 100%);
  box-shadow: 0 20px 44px rgba(37, 99, 235, 0.22);
}
```

本次新增 Hero 规则更复杂、更重：

```css
.market-mobile-home-hero,
.market-mobile-workspace-hero,
.trend-workspace-hero {
  border-radius: 30px;
  background:
    radial-gradient(circle at 18% 16%, rgba(255, 255, 255, 0.3), transparent 28%),
    radial-gradient(circle at 92% 12%, rgba(251, 191, 36, 0.32), transparent 28%),
    linear-gradient(135deg, #0f3b91 0%, #2563eb 50%, #38bdf8 100%);
  box-shadow: 0 24px 52px rgba(37, 99, 235, 0.28);
}
```

## 4. 可执行修复步骤

### 4.1 立即回退方案

目标：快速恢复到上一轮较稳定视觉。

步骤：

1. 删除 `web/src/styles.css:3478` 到文件末尾的新增 `@media (max-width: 720px)` 覆盖块。
2. 保留 `web/src/styles.css:3285` 起的上一轮移动端增强规则。
3. 运行 CSS 诊断。
4. 运行 `pnpm run build`。
5. 在允许启动服务后重新生成移动端截图，并与 `e:\battel\.tmp\ui-screenshots` 中旧截图对比。

适用场景：

- 当前视觉明显变丑且需要立刻止损。
- 尚未有 Figma 定稿确认新风格。

### 4.2 推荐改进方案

目标：不是简单回退，而是在原版基础上小幅提升品质。

步骤：

1. 合并所有移动端 `@media (max-width: 720px)` 样式，移除重复覆盖。
2. 页面背景只保留低饱和蓝灰渐变。
3. Hero 保留蓝色主渐变，但去掉橙色光斑。
4. 主卡片圆角统一为 `18px` 或 `20px`。
5. 列表卡片圆角统一为 `14px` 或 `16px`。
6. 阴影分为三级：页面浮层、主卡片、普通卡片，普通列表行默认不用阴影。
7. 移除 `.first-child` 结构性高亮，改为业务状态类控制。
8. 底部导航降低高度和阴影，激活态使用纯蓝浅底或蓝色文字，不使用强渐变。
9. 行情列表去掉默认蓝色竖条，仅在状态异常时出现。
10. 建立截图基线，将移动端首页、行情、趋势、预警纳入视觉回归。

### 4.3 建议的目标代码方向

```css
@media (max-width: 720px) {
  .market-mobile-home,
  .market-mobile-shell {
    background: linear-gradient(180deg, #f7faff 0%, #eef5fb 54%, #f8fafc 100%);
  }

  .market-mobile-home-hero,
  .market-mobile-workspace-hero,
  .trend-workspace-hero {
    border-radius: 24px;
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 58%, #60a5fa 100%);
    box-shadow: 0 16px 34px rgba(37, 99, 235, 0.18);
  }

  .market-mobile-card,
  .market-mobile-table-card,
  .trend-list-shell,
  .market-mobile-alert-card {
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
  }

  .market-mobile-table-row {
    border-radius: 14px;
    background: #ffffff;
    box-shadow: none;
  }
}
```

## 5. 视觉回归测试清单

### 5.1 截图页面范围

每次移动端样式改动后至少采集以下截图：

1. 移动端首页：`mobile-landing`
2. 移动端行情汇总：`mobile-workbench-summary`
3. 移动端趋势页：`mobile-workbench-trend`
4. 移动端当前趋势状态：`mobile-workbench-trend-current`
5. 移动端预警页：`mobile-workbench-alerts`

### 5.2 视觉检查项

颜色：

- 页面背景是否低饱和、无明显色块污染。
- 主色是否集中在 Hero、主按钮、激活导航。
- 预警色是否只用于风险语义。
- 文本颜色是否有足够对比度。

间距：

- 页面左右安全边距是否为 `12px` 到 `16px`。
- 卡片内边距是否为 `12px` 到 `16px`。
- 卡片之间间距是否为 `10px` 到 `14px`。
- 底部导航是否遮挡内容。

字体：

- 一级标题是否为 `24px` 到 `28px`。
- 二级标题是否为 `16px` 到 `18px`。
- 卡片标题是否为 `13px` 到 `15px`。
- 辅助文字是否不小于 `10px`。

布局：

- 是否无横向滚动。
- 筛选条是否可横向滑动但不破坏页面宽度。
- 列表卡片是否在 375px 宽度下可完整阅读。
- 图表区是否没有挤压按钮和图例。

组件：

- Hero 是否只有一个主视觉焦点。
- 普通卡片是否不抢主卡片视觉权重。
- 底部导航激活态是否清晰但不过亮。
- 预警列表是否区分上涨、下跌、提醒状态。

性能：

- 固定导航之外不使用大面积 `backdrop-filter`。
- 同屏阴影层数不超过 3 类。
- 不使用过多大尺寸伪元素装饰。

### 5.3 自动化建议

现有测试 `web/tests/mobile-regression.spec.ts` 已覆盖移动端主流程和横向溢出，但它偏功能验证，不能保证美观。建议新增或扩展截图断言：

- 对关键页面保存截图。
- 与基线截图进行视觉差异比较。
- 设置差异阈值，建议首轮阈值 `0.02` 到 `0.04`。
- 任何移动端样式 PR 必须附带截图对比。

## 6. 移动端设计规范

### 6.1 色彩规范

基础色：

| 用途 | 色值 | 说明 |
|------|------|------|
| 页面背景顶部 | `#f7faff` | 浅蓝白背景 |
| 页面背景中段 | `#eef5fb` | 冷静浅蓝灰 |
| 卡片背景 | `#ffffff` 或 `rgba(255,255,255,0.96)` | 内容阅读底色 |
| 主品牌蓝 | `#2563eb` | 按钮、激活态、关键强调 |
| 深品牌蓝 | `#1d4ed8` | Hero 起始色、重点文字 |
| 辅助浅蓝 | `#60a5fa` | 渐变终点或轻强调 |
| 正文深色 | `#0f172a` | 主标题 |
| 正文色 | `#334155` | 正文说明 |
| 辅助文字 | `#64748b` | 次级信息 |
| 边框色 | `#dbeafe` 或 `rgba(148,163,184,0.24)` | 轻边框 |
| 上涨/风险 | `#ef4444` | 价格上涨、风险 |
| 下跌/利好 | `#16a34a` | 价格下降、利好 |
| 提醒/波动 | `#f97316` | 告警、波动 |

限制：

- 大面积背景不使用橙色。
- 单个组件内渐变色不超过 3 个。
- 除图表外，不同时使用蓝、青、橙三类高饱和色。

### 6.2 字体规范

| 层级 | 字号 | 行高 | 字重 |
|------|------|------|------|
| 移动端一级标题 | `24px - 28px` | `1.12 - 1.18` | `700` |
| 模块标题 | `16px - 18px` | `1.25` | `700` |
| 卡片标题 | `13px - 15px` | `1.3` | `700` |
| 正文说明 | `12px - 13px` | `1.5 - 1.7` | `400 - 500` |
| 辅助文字 | `10px - 11px` | `1.3 - 1.45` | `400 - 600` |
| 价格数字 | `20px - 22px` | `1` | `800` |
| 详情核心数字 | `24px - 28px` | `1` | `800` |

限制：

- 普通列表价格不超过 `22px`。
- 辅助文字不小于 `10px`。
- 标题不使用小于 `-0.04em` 的字距压缩。

### 6.3 圆角规范

| 组件 | 圆角 |
|------|------|
| 页面 Hero | `22px - 24px` |
| 主模块卡片 | `18px - 20px` |
| 列表卡片 | `14px - 16px` |
| KPI 小卡 | `14px - 16px` |
| 输入框/按钮 | `12px - 14px` |
| 胶囊标签 | `999px` |
| 底部导航容器 | `20px - 22px` |

限制：

- 移动端普通业务卡片不超过 `20px`。
- 只有 Hero 或底部导航可达到 `24px`。

### 6.4 阴影规范

| 层级 | 阴影 |
|------|------|
| Hero | `0 16px 34px rgba(37, 99, 235, 0.18)` |
| 主卡片 | `0 10px 24px rgba(15, 23, 42, 0.06)` |
| 浮动导航 | `0 12px 28px rgba(15, 23, 42, 0.12)` |
| 普通列表行 | 默认无阴影 |

限制：

- 不使用超过 `46px` 扩散感的移动端阴影。
- 同屏不超过 3 种阴影层级。
- 列表行优先使用边框和背景，不使用大阴影。

### 6.5 间距规范

| 场景 | 数值 |
|------|------|
| 页面左右边距 | `12px - 16px` |
| 页面顶部边距 | `14px - 18px` |
| 主模块间距 | `12px - 16px` |
| 卡片内边距 | `12px - 16px` |
| 列表行内边距 | `10px - 12px` |
| 标签间距 | `6px - 8px` |
| 底部内容避让 | 至少 `96px + safe-area` |

### 6.6 组件规范

Hero：

- 只承载页面名称、核心说明和 1 到 2 个关键指标。
- 不使用超过 2 个伪元素装饰。
- 背景渐变必须保证白字清晰。

行情卡片：

- 商品名优先，价格其次，来源和时间弱化。
- 普通商品不加状态竖条。
- 只有异常波动、推荐采购、重点关注才使用状态色。

趋势页：

- 图表容器保持清爽，不能被多层渐变抢焦点。
- 趋势模式切换应像分段控件，不像多枚强按钮。
- 空状态要轻，不应比真实图表更抢眼。

预警页：

- KPI 卡片颜色必须遵循业务语义。
- 上涨为红，下跌为绿，提醒为橙，普通为蓝灰。
- 列表状态条只用于预警项，不用于普通行情项。

底部导航：

- 激活态清晰但不使用强烈多色渐变。
- 单项高度控制在 `48px - 52px`。
- 不遮挡页面主要操作按钮。

## 7. 后续落地建议

建议下一步按以下顺序处理：

1. 删除或替换 `web/src/styles.css:3478` 起的新增覆盖块。
2. 按本规范合并移动端样式，避免继续追加覆盖。
3. 重新生成移动端截图并存入 `.tmp/ui-screenshots`。
4. 将最终确认稿同步回 Figma，确保符合项目设计真源规则。
5. 将移动端截图对比纳入后续样式修改的验收流程。
