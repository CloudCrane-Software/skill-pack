# skill-pack

验证经验的对外打包与外发。一句话：**原生自演进通道产出的经验，经消融验证与准入记录后，从这里出库。**

## 定位

- 依据《建设方案-多Agent系统与GitOps》（PROP-0001）第 4.9 节 #9 与 WO-0007（v1.6 收缩）：**经验库不自建**。原生 Skill 自演进 / SwarmSkills / TTSE / AutoHarness 直接产出经验；glue 只补三件原生没有的事：
  1. 消融验证（原生只有置信度阈值与审批，无对照实验）；
  2. GuardrailRun 准入记录（经验生效绑定 Spec 版本与证据）；
  3. **验证后外发**——即本仓库：技能包（Package）发布与对 openJiuwen 上游的反馈 PR。
- 红线：`auto_save` 保持 false；消融验证为准入硬门槛；未过准入的经验不出库。

## 状态

M0 骨架（README / LICENSE / .gitignore）。

## License

Apache-2.0
