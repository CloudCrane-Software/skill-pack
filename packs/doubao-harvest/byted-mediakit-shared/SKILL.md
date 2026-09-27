---
name: byted-mediakit-shared
version: '0.2.1'
license: 'MIT'
description: 'MediaKit 是面向音视频与图像处理的专业工具集，覆盖音视频剪辑与合成、音频媒资探测与人声分离、视频理解与增强、图像增强与内容理解等工作流。用户明确提出叠加、字幕压制、滤镜、运镜、提取字幕、语音转字幕、裁剪、拼接、调速、混音、音视频处理、图片增强或擦除、视频分析或画质增强目标时，先加载本 Skill，再按对象和目标选择 audio、editing、image 或 video；仅说明媒体类型而未说明处理目标时先澄清。不承担具体能力参数说明。'
requires:
  bins: ['mediakit-cli']
metadata:
  capability_count: 0
---

# MediaKit 专业媒体处理入口

## jiuwenswarm Harness 适配说明

> 来源：豆包工作客户端（Windows 2.30.5，bundle 20260914T100821Z）收割的 SKILL.md 主文件；改造规则见 `packs/doubao-harvest/CONVERSION.md`（源映射：`skill-mapping.md`，2026-09-26）。
> 资源边界：源包内 `references/`、`scripts/`、`assets/` 未随本收割分发，需回源 zip 补齐；运行时引用路径必须落在 jw workspace 边界内（PermissionEngine external_directory 策略会拦截外部路径）。

### 权限映射

源 frontmatter 声明 `permissions: [shell]`（豆包为声明式提示）。jiuwenswarm Harness PermissionEngine 是执行层拦截，两者不同构，建议按此配置：

```python
create_deep_agent(permissions={"tools": {"bash": "ask", "powershell": "ask"}})
```

正文中标注的「高风险操作」清单原样保留，交由 PermissionEngine / PermissionInterruptRail 执行层兜底。

### 环境依赖检查（before_invoke 建议）

本 skill 依赖外部命令：`mediakit-cli`。建议在 harness 侧挂 before_invoke 环境检查：

```python
import shutil
missing = [b for b in ['mediakit-cli'] if shutil.which(b) is None]
if missing:
    raise RuntimeError(f"缺少外部命令：{missing}；请先安装并确保在 PATH 中")
```

### 工具自发现

源 `metadata.cliHelp`：`mediakit-cli --help`（原样保留；jw 渐进式工具暴露下可用同款命令自发现子命令）。

### 语义重接记录

- 重接点1（身份与凭据）：无命中
- 重接点2（定时任务与会话产物）：无命中
- 重接点3（路径与浏览器约定）：无命中
- 重接点4（安全规则与写操作确认）：无命中
- 平台字样裁定：无


MediaKit 是面向音视频与图像处理的专业工具集。它将常见的媒体加工、内容理解和
智能增强能力统一到 `mediakit-cli`，适合从素材处理到成片制作的完整工作流。

## 能力范围

- **视频剪辑与合成**：裁剪、拼接与转场、调速、音量调整、画面翻转和滤镜、运镜、字幕压制、混音、音视频提取与合流、淡入淡出以及多画面编排。
- **音频与音轨处理**：音频转码与媒资信息探测、语音边界定位，以及人声与背景声分离。
- **图像处理与内容理解**：尺寸缩放与体积治理、元信息探测、裁剪旋转翻转与圆角、颜色与锐化、负片、模糊与打码、水印、背景移除、文字识别、画质评估与智能裁剪等。
- **视频理解与增强**：视频内容理解、剧情/剧本与高光拆条、画质增强与画质检测、抽帧、从视频提取字幕、语音转字幕、字幕识别与擦除、水印与隐私保护、人像或绿幕抠像、媒资探测、场景与语义分段、画面文字识别、转码转封装等。

## 能力选择与优先加载

按用户的处理对象和明确目标选择领域 Skill：

| 用户目标                                                                                                         | 优先加载                 |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 对现有素材进行裁剪、拼接或转场、调速、滤镜、运镜、字幕压制、混音或合流                                     | `byted-mediakit-editing` |
| 探测音频媒资信息、音频转码，或分离音频或视频中的人声与背景声                                                     | `byted-mediakit-audio`   |
| 处理单张图片的尺寸体积治理、增强擦除、打码水印、文字识别、画质评估或背景移除                                     | `byted-mediakit-image`   |
| 进行视频理解或高光拆条、抽帧、提取字幕、语音转字幕、字幕识别或擦除、画质增强或检测、抠像、媒资探测或场景分段 | `byted-mediakit-video`   |

如果一个请求同时包含多个阶段，先加载与主要产出最匹配的领域 Skill，再按工作流
需要加载其他领域 Skill。只说明“处理一个视频”或“处理一张图片”而没有说明目标
时，先向用户澄清，不要根据媒体类型猜测具体能力。

选定领域后，必须先读取该领域 Skill，再读取最终选定工具的完整 reference，最后
依据当前 CLI 的机器合同构造参数。共享入口只负责能力导航和通用 CLI 使用方式，
不重复具体工具的参数、枚举或结果字段。

## 可用性检查

```bash
mediakit-cli --version
mediakit-cli --help
mediakit-cli --domains
```

## 使用流程

1. 按对象和目标选择领域 Skill；只说明媒体类型而未说明目标时，先向用户澄清。
2. 选定工具后，先读取该工具的完整 reference，再读取实时 `--help` 与 `--schema`。
3. 必填参数必须来自用户真实输入；可选参数只在用户明确提供，或可从意图准确确定时填写。不能准确确定时省略，确为完成任务所必需时先澄清；不得伪造 URL、文件、枚举或业务参数。
4. 对象或对象数组参数按下方「JSON 参数传参」构造；Windows PowerShell 不得套用 bash 单引号。

## 命令发现

```bash
mediakit-cli --domains
mediakit-cli <domain> --help
mediakit-cli <domain> <tool> --help
mediakit-cli <domain> <tool> --schema
```

`--schema` 只读取当前 Cloud 机器合同，不发起业务调用；顶层包含 `name`、
`description`、`input_schema` 和 `output_schema`。

## 媒体输入

当业务参数需要公网可访问媒体，而用户仅提供本机文件路径时，CLI
的 Cloud 输入适配器会处理上传。无需新增上传命令或上传参数。

## JSON 参数传参

对象或对象数组参数必须传合法 JSON 字符串，不能用逗号分隔或裸文本。
`array<string>` 仍用逗号分隔或重复 flag，不要套用本节。

POSIX / bash / zsh：用单引号整体包裹，保留 JSON 内部双引号。

```bash
mediakit-cli editing add-subtitle-to-video --video-url "<url>" --subtitles '[{"start_time":0,"end_time":3,"subtitle_text":"大家好"}]'
```

Windows PowerShell：单引号或 `$json` 变量都会把 JSON 里的 `"` 剥掉，CLI 会报
`invalid character 's'` / `'t'`。必须把 JSON flag 放在 `--%` 之后；整段 JSON
用双引号包裹，JSON 内部的 `"` 写成 `\"`。带空格的路径等普通参数放在 `--%`
之前。`--%` 之后不要使用 PowerShell 变量。

```powershell
mediakit-cli editing add-subtitle-to-video --video-url "C:\path\video.mp4" --% --subtitles "[{\"start_time\":0,\"end_time\":3,\"subtitle_text\":\"大家好\"}]"
mediakit-cli video erase-video-subtitle-pro --video-url "C:\path\video.mp4" --mode Text --% --erase-ratio-location "[{\"top_left_x\":0,\"top_left_y\":0,\"bottom_right_x\":1,\"bottom_right_y\":0.2}]"
```

禁止（Windows 上均会失败）：

- `'[{...}]'` 单引号 JSON
- `--flag $json` 或 `--flag "$json"`
- `Get-Content` 读出 JSON 后再当 flag 传入
- `--flag @C:\file.json`
- `cmd /c` 多层转义

## 异步任务

异步工具返回 `task_id` 后，使用：

```bash
mediakit-cli shared query-task --task-id <task_id>
```

完整轮询与结果约定见 [reference/query_task.md](reference/query_task.md)。
