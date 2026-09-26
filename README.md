# skill-pack

验证经验的对外打包与外发。一句话：**原生自演进通道产出的经验，经消融验证与准入记录后，从这里出库。**

## 定位

- 依据《建设方案-多Agent系统与GitOps》（PROP-0001）第 4.9 节 #9 与 WO-0007（v1.6 收缩）：**经验库不自建**。原生 Skill 自演进 / SwarmSkills / TTSE / AutoHarness 直接产出经验；glue 只补三件原生没有的事：
  1. 消融验证（原生只有置信度阈值与审批，无对照实验）；
  2. GuardrailRun 准入记录（经验生效绑定 Spec 版本与证据）；
  3. **验证后外发**——即本仓库：技能包（Package）发布与对 openJiuwen 上游的反馈 PR。
- 红线：`auto_save` 保持 false；消融验证为准入硬门槛；未过准入的经验不出库。
- v1.7 §12.1 A 路线（提示词策略包，**合规 ✅**）：OKF 策略包格式落在本仓。
- v1.7 §12.7（骨架人设计、血肉 agent 生长）：**生长产物必过门禁**固化为 manifest 的 `review` 段——`gate_ref` 缺失即 invalid。

## 现状（格式 v0.1）

| 组件 | 说明 |
| --- | --- |
| `docs/okf-spec.md` | OKF（Open Knowledge Format）v0.1 规范：manifest 字段表（字段集封闭，缺失/多余即 invalid）、目录结构（prompts/ policies/ tests/）、版本兼容规则、渲染语义、review 门禁约束 |
| `src/skillpack/manifest.py` | pack.yaml 加载 + 严格校验：一次收集全部错误（含路径逃逸、占位符双向一致性、api_version 兼容） |
| `src/skillpack/validate.py` | CLI：`python -m skillpack.validate <dir> [--target NAME]`，退出码 0=合法 / 2=非法 |
| `src/skillpack/render.py` | 渲染为注入 harness 的 system-prompt 片段：按 targets 过滤、`{{占位符}}` 替换（严格参数模式保证产物逐字节确定）；`render_tool_policy` 输出工具约束文本块 |
| `src/skillpack/_minyaml.py` | OKF 专用严格 YAML 子集解析器——零第三方依赖；不支持的语法显式报错（见 spec §4） |
| `packs/examples/hello-policy/` | 最小合法 pack（**synthetic**） |
| `packs/examples/dev-guard-sop/` | Team Skill SOP 形态：dev 团队三铁律提示词包（转述自 PROP-0001 §4.3，**synthetic**；含片段级 targets 过尾示例） |
| `tests/` | pytest：校验器正反例（结构 / review 门禁 / 文件存在性 / 占位符契约 / YAML 解析）+ 渲染用例 + CLI 退出码集成测试 |

## 用法

```bash
# 校验
python -m skillpack.validate packs/examples/hello-policy          # exit 0
python -m skillpack.validate packs/examples/dev-guard-sop         # exit 0

# 渲染（PYTHONPATH=src）
PYTHONPATH=src python -c "
from skillpack import load_pack, render_pack, render_tool_policy
pack = load_pack('packs/examples/hello-policy')
print(render_pack(pack, 'zcode', {'assistant_name': 'Ada'}))
print(render_tool_policy(pack))
"

# 测试
python -m pytest
```

零第三方依赖：Python 3.9+ 标准库即可运行。

## 合规分级（PROP-0001 §12.1 三路线）

| 路线 | 状态 | 与本仓关系 |
| --- | --- | --- |
| A 提示词策略包 | ✅ 合规 | **本仓范围**：格式 + 校验 + 渲染 |
| B provider 包装 | ✅ 合规 | 不在本仓（harness_protocol 侧） |
| C OAuth 中继 | ⚠️ 逐家 ToS 评审后才可激活 | 不在本仓（session-broker 仓） |

**纪律（PROP-0002）**：必须有真软件在手才能拆。本仓**未拆任何厂商真软件**；
`packs/examples/` 全部为 synthetic，`provenance` 段如实标注来源与提炼方法。

## 外发目标

1. 对 openJiuwen 上游的反馈 PR（原生 harness 可直接采纳的提示词/工具策略）；
2. 本仓的 skill-pack 发布（release tag 级依赖，供各 harness 引用）。

## 状态

- ~~M0 骨架（README / LICENSE / .gitignore）~~
- **M3/WO-0007（本次）：OKF v0.1 格式 spec + 校验器 + 渲染器 + 两个 synthetic 示例包 + pytest 全绿。边界如实：渲染输出尚未被任何真实 harness 消费（注入链路是下一步）；门禁校验只查引用格式，不联网核实 GuardrailRun 记录真伪。**

## License

Apache-2.0
