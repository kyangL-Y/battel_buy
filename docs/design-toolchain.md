# 设计工具链协同规范

本文档定义项目中 `Figma`、`Stitch`、`Pencil` 与 `Image2` 四套设计能力的协同方式。

如果本文件与 [AGENTS.md](/E:/battel/AGENTS.md) 或 [.helloagents/guidelines.md](/E:/battel/.helloagents/guidelines.md) 存在差异，以真源规则和本文件中的职责边界为准；如果仍有冲突，以 `Figma` 作为设计真源的原则优先。

## 核心原则

- `Figma` 是团队唯一设计真源，所有进入开发的定稿必须沉淀回 Figma。
- `Stitch` 与 `Image2` 只用于 AI 生成候选稿、探索方向和快速产出高保真变体，不直接作为最终交付源。
- `Pencil` 只用于个人本地设计、design-as-code 实验和快速改稿，不绕过 Figma 成为团队真源。
- 开发实现默认优先参考 Figma；`Stitch`、`Image2` 和 `Pencil` 只作为补充参考或起草来源。

## 三者分工

| 工具 | 角色 | 适用场景 | 不应该做什么 |
|------|------|----------|--------------|
| Figma | 团队真源 | 定稿、评审、设计系统、开发交接、组件规范 | 不把外部候选稿直接当真源而不回收整理 |
| Stitch | AI 设计生成器 | 快速出页面方向稿、批量变体、探索布局与风格 | 不直接充当最终设计交付 |
| Image2 | AI 图片生成网关 | 生成可落地 UI 参考稿、视觉素材、设计方向图 | 不把网关密钥写入仓库，不生成无法前端复刻的炫技稿 |
| Pencil | 本地设计工作台 | 工程师本地做 design-as-code、草图和结构调整 | 不在团队流程中替代 Figma |

## 推荐工作流

### 流程 A：AI 先出方向，再进入开发

1. 用 Stitch 生成 1-3 个页面方向稿。
2. 需要更具体的静态 UI 参考稿时，可用 Image2 生成单页候选稿。
3. 选定方向后，把结果整理进 Figma。
4. 在 Figma 中完成团队评审、设计系统对齐和最终定稿。
5. 前端开发与代理实现统一以 Figma 为准。

### 流程 B：工程师本地快速实验

1. 在 Pencil 中快速尝试布局、层级或组件结构。
2. 确认可行方案后，把结果整理回 Figma。
3. 只有 Figma 中的版本可以进入开发交付。

### 流程 C：设计系统维护

1. Figma 维护组件、变量、设计规范。
2. Stitch 可以用于探索新页面风格，但不直接更改系统规则。
3. Pencil 可以本地验证 design-as-code 表达是否顺手，但不替代系统级规范定义。

## 冲突处理

- 如果同一页面在多个工具中出现不同版本，以 Figma 最后确认版本为准。
- 如果 Stitch、Image2 或 Pencil 中的结果更好，先同步回 Figma，再进入开发。
- 如果代理拿到多个来源的设计上下文，必须优先读取 Figma，并把其他来源标记为参考稿。

## Codex 中的使用顺序

- 需要实现设计稿时：先 Figma
- 需要探索多个视觉方向时：先 Stitch 或 Image2，再回收进 Figma
- 需要本地快速试验或个人改稿时：先 Pencil，再回收进 Figma

## 接入说明

### Figma

- 推荐通过官方远程 MCP 接入 `Codex`
- 需要 `FIGMA_OAUTH_TOKEN`
- 需要在 `~/.codex/config.toml` 中启用 `rmcp_client`
- 未配置 `FIGMA_OAUTH_TOKEN` 时，不要保留 `[mcp_servers.figma]`，否则 `Codex` 启动时会直接报错

### Stitch

- 推荐通过项目内 `tools/design-mcp/stitch-proxy.mjs` 以 stdio MCP 形式接入 `Codex`
- 需要 `STITCH_API_KEY` 或 `STITCH_ACCESS_TOKEN`
- 首次需要在 `tools/design-mcp/` 内安装 npm 依赖
- 未配置 Stitch 凭据时，不要保留 `[mcp_servers.stitch]`，否则代理会在握手前退出

### Image2

- 推荐通过项目内 `tools/design-mcp/image2-mcp.mjs` 以 stdio MCP 形式接入 `Codex`
- 需要 `IMAGE2_API_KEY`
- 可选配置 `IMAGE2_BASE_URL`，默认 `https://ai.emqo.top`
- 可选配置 `IMAGE2_MODEL`，默认 `gpt-image-2`
- 生成结果默认保存到 `E:/battel/.tmp/image2`
- 未配置 `IMAGE2_API_KEY` 时，不要保留 `[mcp_servers.image2]`，否则实际调用生成工具时会失败

### 条件同步配置

- 推荐运行 `tools/design-mcp/apply-codex-mcp.ps1`
- 该脚本会先备份 `~/.codex/config.toml`，然后按当前环境变量自动启用或移除 `figma` / `stitch` / `image2`
- 当前环境无凭据时，脚本会自动移除对应 MCP 块，避免 `Codex` 启动出现 `MCP startup incomplete`
- 凭据补齐后再次运行脚本，会重新写回对应 MCP 配置

### Pencil

- Pencil 官方文档说明其 MCP 在应用运行后自动启动
- 启动 Pencil 后，打开 `Codex` 并运行 `/mcp`，应能看到 Pencil
- 如果没出现，优先排查 Pencil 是否已安装、激活且正在运行

## 验收清单

- `Codex /mcp` 中能看到 Figma
- `Codex /mcp` 中能看到 Stitch
- 设置 `IMAGE2_API_KEY` 后，`Codex /mcp` 中能看到 Image2
- 启动 Pencil 后，`Codex /mcp` 中能看到 Pencil
- 团队成员知道进入开发前必须以 Figma 定稿
- 项目规范文件中已经明确这些设计工具的边界

## 官方参考

- Figma MCP: https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server
- Stitch 官方博客: https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-ai-ui-design/
- Stitch SDK: https://github.com/google-labs-code/stitch-sdk
- Pencil AI Integration: https://docs.pencil.dev/getting-started/ai-integration
- Pencil Installation: https://docs.pencil.dev/getting-started/installation
