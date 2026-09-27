---
name: lark-markdown
version: 1.2.2
description: "飞书 Markdown：查看、创建、上传、编辑和比较飞书中的原生 Markdown 文件。当用户要操作飞书 Markdown 文件，或比较其远端版本及本地草稿时使用。纯本地 Markdown 文件操作不触发本 skill。不负责将 Markdown 导入为飞书在线文档，也不负责文件搜索、权限、评论、移动、删除等云空间管理操作。"
requires:
  bins: ["lark-cli"]
---

# markdown (v1)

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

源 `metadata.cliHelp`：`lark-cli markdown --help`（原样保留；jw 渐进式工具暴露下可用同款命令自发现子命令）。

### 语义重接记录

- 重接点1（身份与凭据）：快速决策「身份」条（首次 `--as user`）后补自建飞书开放平台应用凭据说明；命令语义保留
- 重接点2（定时任务与会话产物）：无命中
- 重接点3（路径与浏览器约定）：无命中
- 重接点4（安全规则与写操作确认）：无命中
- 平台字样裁定：无


## 快速决策

- 身份：Markdown 文件属于用户云空间资源，统一使用 `--as user`。

身份凭据由宿主环境注入（环境变量或 Vault），agent 须使用自建飞书开放平台应用凭据，不得尝试复用豆包工作客户端登录态（违反其 ToS 5.1.1/5.1.2(9)）。

- `markdown +create` / `+overwrite` 失败时，先判断是不是权限问题：常见的是用户授权或目标目录 ACL 不足，按错误响应引导用户解决。

- 用户要**上传、创建一个原生 `.md` 文件**，使用 `lark-cli markdown +create`
- 用户要**比较原生 `.md` 文件的历史版本差异**，或比较远端 Markdown 与本地草稿，使用 `lark-cli markdown +diff`
- 用户要**读取 Drive 里某个 `.md` 文件内容**，使用 `lark-cli markdown +fetch`
- 用户要对 Markdown 文件做**局部文本替换 / 正则替换**，优先使用 `lark-cli markdown +patch`
- 用户要**覆盖更新 Drive 里某个 `.md` 文件内容**，使用 `lark-cli markdown +overwrite`
- 用户要先拿 Markdown 文件的历史版本号，再做比较/下载/回滚，先用 [`lark-drive`](../lark-drive/SKILL.md) 的 `lark-cli drive +version-history`
- 用户要把本地 Markdown **导入成在线新版文档（docx）**，不要用本 skill，改用 [`lark-drive`](../lark-drive/SKILL.md) 的 `lark-cli drive +import --type docx`
- 用户要对 Markdown 文件做**rename / move / delete / 搜索 / 权限 / 评论**等云空间（云盘/云存储）操作，不要留在本 skill，切到 [`lark-drive`](../lark-drive/SKILL.md)
- `markdown +create` / `+overwrite` 命中 `missing scope`、`permission denied`、`not found`、`quota_exceeded`、`version limit` 时，默认停止重试并按报错 hint 处理；只有 `rate_limit`、`server_error` 或临时网络错误才做有限退避重试。
- `markdown +create` 的目标参数不要猜：Drive 文件夹用 `--folder-token`，Wiki 节点用 `--wiki-token`。如果用户给的是 URL，可以直接传完整 URL；CLI 会归一成 token。不要把 doc/sheet/wiki URL 放进 `--folder-token` 试错。

## 核心边界

- 本 skill 处理的是 **Drive 中作为普通文件存储的 Markdown**，不是 docx 文档
- `--name` 和本地 `--file` 文件名都必须显式带 `.md` 后缀；不满足时 shortcut 会直接报错
- `--content` 支持：
  - 直接传字符串
  - `@file` 从本地文件读取内容
  - `-` 从 stdin 读取内容
- `markdown +patch` 的内部语义是：**先完整下载 Markdown，再本地替换，再整文件覆盖上传**
- `markdown +patch` 不是服务端原子 patch；它是 CLI 侧编排出来的局部更新能力
- `markdown +patch` 当前只支持**单组** `--pattern` / `--content`
- `markdown +patch` 替换后的最终内容**不能为空**；CLI 会拒绝上传空文件，因为 Drive 不支持零字节 Markdown，且空文件通常是误操作
- `--file` 只接受本地 `.md` 文件路径

正则替换时要特别注意 `--pattern` 的转义：

```bash
# BAD: 未转义正则特殊字符，可能匹配到错误位置
lark-cli markdown +patch --file-token boxcnxxxx --regex --pattern "version (1.0)" --content "version (2.0)"

# GOOD: 显式转义括号和点号
lark-cli markdown +patch --file-token boxcnxxxx --regex --pattern "version \\(1\\.0\\)" --content "version (2.0)"
```

## Shortcuts（推荐优先使用）

Shortcut 是对常用操作的高级封装（`lark-cli markdown +<verb> [flags]`）。有 Shortcut 的操作优先使用。

| Shortcut | 说明 |
|----------|------|
| [`+create`](references/lark-markdown-create.md) | Create a Markdown file in Drive |
| [`+diff`](references/lark-markdown-diff.md) | Compare two remote Markdown versions, or compare remote Markdown against a local file |
| [`+fetch`](references/lark-markdown-fetch.md) | Fetch a Markdown file from Drive |
| [`+patch`](references/lark-markdown-patch.md) | Patch a Markdown file in Drive via fetch-local-replace-overwrite |
| [`+overwrite`](references/lark-markdown-overwrite.md) | Overwrite an existing Markdown file in Drive |

## 参考

- [lark-drive](../lark-drive/SKILL.md) — Drive 文件管理、导入 docx、move/delete/search 等
