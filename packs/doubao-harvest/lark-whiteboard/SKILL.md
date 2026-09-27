---
name: lark-whiteboard
version: 1.0.0
description: >
  飞书画板：查询和编辑飞书云文档中的画板。支持导出画板为预览图片、导出原始节点结构、使用多种格式更新画板内容。
  当用户需要查看画板内容、导出画板图片、编辑画板时使用此 skill。不负责：飞书云文档内容编辑（lark-doc）、文档内嵌电子表格/Base（sheet / lark-base）。
requires:
  bins: ["lark-cli"]
---

## jiuwenswarm Harness 适配说明

> 来源：豆包工作客户端（Windows 2.30.5，bundle 20260914T100821Z）收割的 SKILL.md 主文件；改造规则见 `packs/doubao-harvest/CONVERSION.md`（源映射：`skill-mapping.md`，2026-09-26）。
> 资源边界：源包内 `references/`、`scripts/`、`assets/` 未随本收割分发，需回源 zip 补齐；运行时引用路径必须落在 jw workspace 边界内（PermissionEngine external_directory 策略会拦截外部路径）。

### 环境依赖检查（before_invoke 建议）

本 skill 依赖外部命令：`lark-cli`。建议在 harness 侧挂 before_invoke 环境检查：

```python
import shutil
missing = [b for b in ['lark-cli'] if shutil.which(b) is None]
if missing:
    raise RuntimeError(f"缺少外部命令：{missing}；请先安装并确保在 PATH 中")
```

### 工具自发现

源 `metadata.cliHelp`：`lark-cli whiteboard --help`（原样保留；jw 渐进式工具暴露下可用同款命令自发现子命令）。

### 语义重接记录

- 重接点1（身份与凭据）：在「快速决策」首次 `--as user` 的身份段后补自建飞书开放平台应用凭据说明；命令语义保留
- 重接点2（定时任务与会话产物）：无命中
- 重接点3（路径与浏览器约定）：无命中
- 重接点4（安全规则与写操作确认）：无命中（overwrite / SVG 有损确认为路由表内动作说明，不是「操作 × 是否需确认」矩阵，也不是反注入段）
- 平台字样裁定：无

> [!IMPORTANT]
> - 运行 `lark-cli --version`，确认可用，无需询问用户。
> - 运行 `npx -y @larksuite/whiteboard-cli@^0.2.13 -v`，确认可用，无需询问用户。

---

## 快速决策

**身份**：画板操作统一使用 `--as user`。

身份凭据由宿主环境注入（环境变量或 Vault），agent 须使用自建飞书开放平台应用凭据，不得尝试复用豆包工作客户端登录态（违反其 ToS 5.1.1/5.1.2(9)）。

> 先判断「只读还是写入」，再在对应表内按上到下匹配，**命中即停**。

### A. 只读 · 查看 / 导出（不改画板）

| 用户需求 | 行动 |
|---|---|
| 查看画板内容 / 导出图片 | [`+export --output-type preview`](references/lark-whiteboard-export.md)                       |
| 导出 SVG 矢量图 | [`+export --output-type svg`](references/lark-whiteboard-export.md)                       |
| 提取画板的 Mermaid/PlantUML 源码 | [`+export --output-type source`](references/lark-whiteboard-export.md) |

### B. 写入 · 创作 / 编辑（会改画板，命中即停）

| 场景 | 行动 | 写入方式 | 对原内容 |
|---|---|---|---|
| 用户**已提供** Mermaid/PlantUML/SVG 代码，或明确指定用该格式 | 使用该代码 → [`+update`](references/lark-whiteboard-update.md)，`--input_format` 取单值 `mermaid` / `plantuml` / `svg`；写入非空已有画板并需要 overwrite 时，先确认会整板重建；若 SVG 用于修改已有画板，先走 [`routes/svg-edit.md`](routes/svg-edit.md) 有损确认 | overwrite / append | 按用户要求 |
| 从零新建复杂图表（架构/流程/组织等） | → **[§ 创作 Workflow](references/lark-whiteboard-workflow.md#创作-workflow)** | 首次写入 | — |
| 修改 / 增补已有画板 | → **[§ 编辑 Workflow](references/lark-whiteboard-workflow.md#编辑-workflow)** | 见该表 | 见该表 |

## Shortcuts

| Shortcut                                          | 说明 |
|---------------------------------------------------|---|
| [`+export`](references/lark-whiteboard-export.md) | 导出画板为预览图片、SVG 矢量图、代码或原始节点结构。 |
| [`+update`](references/lark-whiteboard-update.md) | 更新画板，支持 PlantUML、Mermaid、SVG 或 OpenAPI 原生格式 |

---

## 不在本 skill 范围
- 文档内容编辑 → lark-doc [lark-doc](../lark-doc/SKILL.md)
- 在文档中创建画板 → [lark-doc-whiteboard.md](../lark-doc/references/lark-doc-whiteboard.md)
- 表格 / Base 操作 → [sheet](../sheet/SKILL.md) / [lark-base](../lark-base/SKILL.md)