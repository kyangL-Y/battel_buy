# PC 工作台续对话交接

更新时间：2026-04-28

## 当前任务

继续细磨 PC 端“市场价格工作台”页面。用户要求按设计稿和现有实现逐屏、逐元素优化，重点是 1:1 还原感、真实数据对接、空态、间距、侧边栏、交互细节和回归验证。

当前主要工作文件：

- `web/src/components/PcPriceWorkbench.vue`

注意：当前工作区较脏，不要回滚用户或其他任务已有改动。最近 `git status --short -- web/src/components/PcPriceWorkbench.vue` 显示该组件为未跟踪文件，后续处理前应先确认仓库状态。

## 已完成内容

- 汇总行情页已基本完成：
  - 侧边栏品牌区增加副标题。
  - 侧边栏底部增加真实数据源摘要。
  - 顶部预警按钮改为真实预警数量，点击进入预警页。
  - 菜单按钮改为返回汇总行情。
  - 筛选栏高度和主区排列修正。
  - 今日行情、今日报价、市场动态、预警信息补充空态。

- 单品趋势页已完成一轮细化：
  - 主趋势图无数据时显示空态。
  - 今日报价、市场价格对比、市场动态、同类商品对比补充空态。
  - 右侧卡片和表格密度收紧。
  - 交互按钮补齐 `type="button"`。

- 价格预警页已完成一轮细化：
  - 预警任务表、高优先级预警、预警趋势图、规则配置、最近处理记录补充空态。
  - 增加 `hasAlertSignals` 判断真实预警信号。
  - 补充空态样式，避免被列表样式污染。

- 通用模块页已完成最新一轮细化：
  - 表格不再把“等待真实数据”占位当作真实行渲染。
  - 新增真实数据判断：
    - `moduleTableRows`
    - `moduleSideItems`
    - `moduleFlowItems`
    - `moduleHasTableRows`
    - `moduleHasSideItems`
    - `moduleHasFlowItems`
    - `moduleHasChartData`
  - 通用模块表格、右侧面板、流程卡片、趋势图、流转明细都补了正式空态。
  - 无真实数据时，模块趋势图不再画假柱状图和假折线。
  - 补了模块空态 CSS，避免继承表格首列、侧栏列表和活动列表样式。

## 最近验证

在 `web/` 目录下已通过：

```bash
npm run build
npm run test:e2e -- tests/desktop-regression.spec.ts
npm run test:e2e
```

结果：

- 构建通过。
- 桌面回归 8/8 通过。
- 完整 e2e 11/11 通过。

## 下一步建议

继续按“一个页面、一组元素、一轮验证”的节奏推进：

- 优先继续看通用模块页：
  - 筛选栏按钮的交互状态和选中态。
  - 模块 hero 区操作按钮间距、主次按钮层级。
  - 各模块之间的差异化内容密度，避免所有页面看起来完全一样。
  - 右侧面板 `更多`、`查看全部` 等按钮是否需要接入实际跳转或禁用态。

- 然后回看侧边栏：
  - 菜单组间距、active 指示、徽标数量和真实数据同步。
  - 底部三个系统入口的 hover、focus、点击行为。
  - 低宽度桌面下侧边栏是否仍然稳定。

- 再做真实数据和交互验证：
  - 切换每个导航项，看是否只展示真实接口返回的数据。
  - 空数据场景下，不应出现假趋势、假条数、假流程。
  - 点击刷新、预警、返回汇总行情、供应商前端/后台/平台后台是否都符合预期。

## 重要约束

- 不要再处理 MCP、image2、API key 或密钥写入相关事项。
- 不要把任何密钥写入代码、文档、环境提交文件或测试夹具。
- 文件编辑优先使用 `apply_patch`。
- 不要无故修改：
  - `web/playwright.config.ts`
  - `web/tests/desktop-regression.spec.ts`
  - `web/tests/mobile-regression.spec.ts`
- 每轮改动后至少跑：

```bash
npm run build
npm run test:e2e -- tests/desktop-regression.spec.ts
```

涉及跨端布局或公共组件时再跑：

```bash
npm run test:e2e
```

## 新对话开场建议

可以直接发送：

“继续 PC 工作台细磨，先读 `docs/pc-workbench-continuation.md`，按里面的下一步继续，不要处理 MCP/key。”
