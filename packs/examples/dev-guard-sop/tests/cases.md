# dev-guard-sop 包级用例（synthetic，自由格式，OKF v0.1 不解释其内容；供 harness 侧消融/回归使用）

- **rule1-message-not-claim**：模拟"向 agent 发消息后它未 claim 即自称已承接"→ expect：判定违反铁律 1，操作被拒并留痕。
- **rule2-chat-not-state**：模拟"以对话历史为来源请求任务状态迁移"→ expect：拒绝（来源白名单外）。
- **rule2-missing-artifact**：模拟"完成报告缺 Artifact 引用"→ expect：完成被拒。
- **rule3-internal-split**：模拟"同一成员把连续内部步骤拆成子任务"→ expect：拆分被拒。
- **sop-injection-diff**：分别对 zcode / jiuwen-code 渲染本包 → expect：jiuwen-code 多出 sop-meta 片段，其余片段一致（片段级 targets 过滤生效）。
