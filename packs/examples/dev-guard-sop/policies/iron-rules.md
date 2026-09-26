# 策略：dev 团队三铁律与违规处置（iron-rules-and-violations）

对应 PROP-0001 v1.6 §4.3 的转述（synthetic，非提炼自任何厂商真软件）：

| # | 铁律 | 落地机制（治理层确定性执行） |
| --- | --- | --- |
| 1 | 消息可触发任务或补充信息，但发送成功 ≠ 任务已被承接 | `MessageReceipt` 不携带任务状态语义；承接只有 claim(executor) 一条合法路径 |
| 2 | 不得把对话历史当作 Team State；协作事实由 Task State 与 Artifact 维护 | 状态迁移来源白名单 = claim/run/admin；完成任务必须携带 TaskRun 引用与 Artifact 引用 |
| 3 | 只有独立交付、不同责任或明确依赖才拆子任务 | split_task 校验：独立交付物 +（owner 不同 或 声明 depends_on）；同一成员连续内部步骤拒绝 |

违规处置：每条违规 = 拒绝该次操作 + 追加 violation_log（检测 = 拒绝 + 留痕）。
本策略文本随 pack 注入；执行拦截由 harness 权限层与治理层负责，本 pack 不复制执行逻辑。
