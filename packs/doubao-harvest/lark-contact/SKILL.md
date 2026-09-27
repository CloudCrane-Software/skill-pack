---
name: lark-contact
version: 1.0.0
description: "飞书 / Lark 通讯录:按姓名 / 邮箱解析成 open_id,或按 open_id 反查姓名 / 部门 / 邮箱 / 联系方式 / 个人状态 / 签名,以及按关键词搜索当前用户可见的机器人 / 智能体(agent)。当用户提到一个名字要下一步发消息 / 排日程,或拿到 open_id 想查具体信息时使用。不负责部门树遍历、按部门列员工、组织架构图,这类需求走原生 OpenAPI。"
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

源 `metadata.cliHelp`：`lark-cli contact --help`（原样保留；jw 渐进式工具暴露下可用同款命令自发现子命令）。

### 语义重接记录

- 重接点1（身份与凭据）：首次 `--as user` 示例段后补自建飞书开放平台应用凭据说明；命令语义保留
- 重接点2（定时任务与会话产物）：无命中
- 重接点3（路径与浏览器约定）：无命中
- 重接点4（安全规则与写操作确认）：无命中
- 平台字样裁定：无

## 选哪个命令

统一以 user 身份运行,按下表选命令:

| 想做什么 | 命令 |
|---|---|
| 按姓名 / 邮箱搜员工拿 open_id | [`+search-user`](references/lark-contact-search-user.md) |
| 按关键词搜索当前用户可见的机器人 / 智能体 | [`+search-bot`](references/lark-contact-search-bot.md) |
| 已知 open_id 取他人资料 | `+search-user --user-ids <id>` 或 [`+get-user --user-id <id>`](references/lark-contact-get-user.md) |
| 查看自己 | `+get-user` 或 `+search-user --user-ids me` |
| 查同事的个人状态 / 签名 | `user_profiles batch_query` |

已知 open_id 只是想发消息 / 排日程,不必经过 contact —— 直接 [`lark-im`](../lark-im/SKILL.md) / [`lark-calendar`](../lark-calendar/SKILL.md)。

### 名字没说清是人还是机器人 / 智能体

用户给的名字常常不表明类型。例如「和 reviewDuck 约个会」里的 reviewDuck 可能是同事昵称,也可能是机器人。
- 名字含 bot / agent / AI / 助手 / 机器人 / 智能体 / assistant 等明显特征时,反过来先搜机器人更快
- 不确定的话两边都搜一下

## 典型场景

找张三给他发消息:先搜,确认 open_id,再发:

```bash
lark-cli contact +search-user --query "张三" --has-chatted --as user
lark-cli im +messages-send --user-id ou_xxx --text "Hi!"
```

身份凭据由宿主环境注入（环境变量或 Vault），agent 须使用自建飞书开放平台应用凭据，不得尝试复用豆包工作客户端登录态（违反其 ToS 5.1.1/5.1.2(9)）。

批量查同事的个人状态 / 个性签名(先用 schema 看参数)。

```bash
lark-cli schema contact.user_profiles.batch_query
lark-cli contact user_profiles batch_query \
  --params '{"user_id_type":"open_id"}' \
  --data '{"user_ids":["ou_xxx","ou_yyy"],"query_option":{"include_personal_status":true,"include_description":true}}'
```

搜索命中多条且后续操作有副作用(发消息、邀请会议等),把候选列给用户挑;不要擅自选第一条。

## 搜索机器人 / 智能体

`+search-bot` 使用 user 身份按关键词搜索当前用户可见的机器人,返回 `ou_` 开头的机器人 open_id。参数细节等见 [`lark-contact-search-bot.md`](references/lark-contact-search-bot.md)。

```bash
lark-cli contact +search-bot --query '会议助手' --as user
lark-cli contact +search-bot --queries '会议助手,日报助手,审批助手' --as user
```

## 注意事项

- **41050 / Permission denied** 受当前身份的可见范围限制(三条命令都可能遇到),按错误响应引导用户解决。
- **跨租户用户**(`is_cross_tenant=true`)多数业务字段为空字符串,这是飞书可见性规则,下游做空值兜底。
- **ID 类型**:`+get-user` 可通过 `--user-id-type` 使用 `open_id`、`union_id` 或 `user_id`;`+search-user` 使用用户 open_id;`+search-bot` 不支持按 ID 查询,它按关键词搜索并返回机器人 open_id。

## 不在本 skill 范围

- 发消息 / 查聊天记录 → [`lark-im`](../lark-im/SKILL.md)
- 排日程 / 邀请会议 → [`lark-calendar`](../lark-calendar/SKILL.md)
- 部门树 / 按部门列员工 / 组织架构 → [`lark-openapi-explorer`](../lark-openapi-explorer/SKILL.md) 查找原生接口