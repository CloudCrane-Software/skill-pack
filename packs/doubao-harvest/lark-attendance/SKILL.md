---
name: lark-attendance
version: 1.0.0
description: "飞书考勤打卡：查询自己的考勤打卡记录"
requires:
  bins: ["lark-cli"]
---

# attendance (v1)

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

源 `metadata.cliHelp`：`lark-cli attendance --help`（原样保留；jw 渐进式工具暴露下可用同款命令自发现子命令）。

### 语义重接记录

- 重接点1（身份与凭据）：无命中（「自动注入」是 employee_type / user_ids 参数填充，无 `--as user`，也未写认证/UAT 由平台注入）
- 重接点2（定时任务与会话产物）：无命中
- 重接点3（路径与浏览器约定）：无命中
- 重接点4（安全规则与写操作确认）：无命中（「自动注入」不是反 prompt-injection 段，也没有写前确认矩阵）
- 平台字样裁定：无


## 默认参数自动填充规则

调用任何 API 时，以下参数 **必须自动填充，禁止向用户询问**：

| 参数 | 固定值 | 说明                                 |
|------|--------|------------------------------------|
| `employee_type` | `"employee_no"` | `employee_type`始终等于`"employee_no"` |
| `user_ids` | `[]`（空数组） | `user_ids`始终等于`[]`                 |

### 填充示例

当构建 `--params` 参数时，自动注入上述字段：
- `employee_type` 保持 `"employee_no"` 不变

当构建 `--data` 参数时，自动注入上述字段：
```json
{
  "user_ids": [],
  ...用户提供的参数
}
```

> **注意**：`user_ids` 数组保持为空[]，`employee_type` 保持 `"employee_no"` 不变。

## API Resources

```bash
lark-cli schema attendance.<resource>.<method>   # 调用 API 前必须先查看参数结构
lark-cli attendance <resource> <method> [flags]  # 调用 API
```

> **重要**：使用原生 API 时，必须先运行 `schema` 查看 `--data` / `--params` 参数结构，不要猜测字段格式。

### user_tasks

- `query` — 查询用户考勤打卡记录

## 权限表

| 方法 | 所需 scope |
|------|-----------|
| `user_tasks.query` | `attendance:task:readonly` |
