---
name: doubao-record
description: 启动当前飞书会话的录音。当用户需要发起录音，或对录音进行中的内容询问的时候，可以使用此技能。用户如果选择了该技能但未做任何输入则默认用户意图为启动录音。
---

## jiuwenswarm Harness 适配说明

> 来源：豆包工作客户端（Windows 2.30.5，bundle 20260914T100821Z）收割的 SKILL.md 主文件；改造规则见 `packs/doubao-harvest/CONVERSION.md`（源映射：`skill-mapping.md`，2026-09-26）。
> 资源边界：源包内 `references/`、`scripts/`、`assets/` 未随本收割分发，需回源 zip 补齐；运行时引用路径必须落在 jw workspace 边界内（PermissionEngine external_directory 策略会拦截外部路径）。

### 语义重接记录

- 重接点1（身份与凭据）：无命中
- 重接点2（定时任务与会话产物）：无命中（「飞书会话」是飞书录音会话，不是豆包会话）
- 重接点3（路径与浏览器约定）：无命中
- 重接点4（安全规则与写操作确认）：无命中
- 平台字样裁定：无（标题 `doubao-record` 为技能名，保留）

## doubao-record（录音转写）
一句话描述：用户是想「发起录音」还是「录音过程中，询问录音相关问题」
- 想要发起录音 → 用 start_recording
- 录音过程中，用户询问与录音内容相关的问题 → 用 get_recording


## 工具是什么
- start_recording：启动当前飞书会话的录音，成功后立即返回 record_id 作为后续查询的唯一句柄。
- get_recording：按 record_id 查询指定录音的聚合信息，返回录音元信息(创建时间、创建地点、录音状态、创建人)、录音内容。录音过程中，当用户问『刚才说了什么』或『这场会的纪要给我』时，或需要判断录音状态时调用。不要用它启动录音；不要传编造的 record_id。

## 使用场景
- 用户明确有语音记录/开始录音记录 → start_recording
- 用户录音中，要读取、查看、总结录音相关内容时 → get_recording

## 核心流程
- 调用 start_recording 时，成功后立即返回 record_id 作为后续查询的唯一句柄
- 使用 start_recording 成功发起录音后，请用自然语言告知用户录音过程中会记录说话内容、录音结束后会为用户生成纪要文档。
- get_recording 是判断录音的状态的重要依据，你需要使用 get_recording 获取、更新准确的录音状态，不能根据对话上下文自行假设。
- 调用 get_recording 时，按 record_id 查询指定录音的聚合信息，返回录音元信息(创建时间、创建地点、录音状态、创建人)、录音内容