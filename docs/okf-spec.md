# OKF（Open Knowledge Format）策略包格式 v0.1

> skill-pack 仓 · 依据 PROP-0001 v1.7 §12.1（A 路线：提示词策略包，合规 ✅）与
> §12.7（生长产物必过门禁）、PROP-0001 v1.6 WO-0007 收缩版（本仓 = 验证后外发载体）。
>
> **纪律（PROP-0002）**：必须有真软件在手才能拆。本格式仓不拆任何厂商真软件；
> 仓内所有示例 pack 一律标注 `provenance.synthetic: true`。

---

## 1. 范围

OKF 策略包是"读官方提示词/工具策略 → 提炼 → 热插回 harness"的**外发载体格式**：

- 产出方：原生自演进通道（Skill 自演进 / SwarmSkills / TTSE / AutoHarness）产出的经验，
  经消融验证 + GuardrailRun 准入记录后打包出库（WO-0007 三件套之三）；
- 消费方：各 harness（zcode、jiuwen-code 等）在启动/热插时把 pack 渲染为
  system-prompt 片段与工具策略约束注入。

OKF v0.1 **只覆盖**：manifest、目录结构、版本兼容规则、渲染语义、门禁约束。
不覆盖：分发与签名（backlog）、多语言、片段间依赖图。

## 2. 目录结构

```
<pack>/
├── pack.yaml          # manifest（必需，文件名固定）
├── prompts/           # 提示词片段（必需目录；prompt_fragments[].path 必须位于此）
│   ├── base.md
│   └── ...
├── policies/          # 策略文档（必需目录；policies[].path 必须位于此）
│   └── ...
└── tests/             # 包级用例（必需目录，至少 1 个文件；v0.1 不解释其内容，
                       # 供 harness 侧消融/回归使用）
```

## 3. `pack.yaml` manifest

字段集**封闭**：缺失或多余字段都 invalid。

| 字段 | 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `api_version` | str | ✅ | 必须在本实现 `SUPPORTED_API_VERSIONS` 内（当前 `"0.1"`），否则 invalid |
| `name` | str | ✅ | `^[a-z][a-z0-9-]{0,62}$`，全仓唯一 |
| `version` | str | ✅ | SemVer `MAJOR.MINOR.PATCH`（见 §5 兼容规则） |
| `targets` | list[str] | ✅ | 非空；harness 名 `^[a-z][a-z0-9._-]{0,62}$`；不重复；精确匹配、无通配 |
| `policies` | list[map] | ✅ | 每项 `{id*, path*, description}`；`id` 不重复；`path` 必须在 `policies/` 下且文件存在 |
| `prompt_fragments` | list[map] | ✅ | 非空；每项 `{id*, path*, slot, targets, placeholders}`；`id` 不重复；`path` 必须在 `prompts/` 下且文件存在 |
| `tool_policy` | map | ✅ | `{mode*, tools*, notes}`；`mode ∈ {allowlist, denylist}`；`tools` 非空字符串列表 |
| `provenance` | map | ✅ | `{source*, method*, extracted_at, synthetic, notes}`；来源与提炼方法如实填写 |
| `license` | str | ✅ | 非空（SPDX 标识符，如 `Apache-2.0`） |
| `review` | map | ✅ | `{gate_ref*, evidence_ref*, approved_at}`——**生长必过门禁**，见 §6 |

`prompt_fragments[]` 字段说明：

- `slot`：注入槽位，`system`（默认）或 `developer`；
- `targets`：可省略 = 继承包级 targets；声明时必须是包级 targets 的子集；
- `placeholders`：该片段文件中出现的 `{{name}}` 占位符清单，
  **必须与文件内容双向一致**（声明了没用 / 用了没声明 / 格式非
  lowercase snake_case，均 invalid）。

### 路径安全

所有 path 必须是相对路径、不得包含 `..` 或绝对路径/盘符形式（路径逃逸即 invalid）。

## 4. YAML 子集（零第三方依赖的代价与边界）

参考加载器（`src/skillpack/_minyaml.py`）只解析严格子集：

- 支持：缩进式映射/序列（仅空格缩进；序列相对键缩进一级或同级）、
  带引号字符串（`'…'`/`"…"`，支持 `''` 与 `\"` 转义）、plain 标量
  （true/false/null/~/int/float，其余按字符串）、一层行内列表 `[a, b]`、
  整行与行尾注释；
- 不支持（遇到即 parse error）：锚点/别名、块标量 `|`/`>`、流式映射 `{…}`、
  多文档 `---`、标签、Tab 缩进、复杂键。

写 manifest 时请勿使用上述语法；这让校验器在无 PyYAML 的环境（执行面最小镜像）
也能完整工作，且行为完全确定。

## 5. 版本兼容规则

1. **格式版本**：`api_version` 是 pack 与加载器之间的契约。加载器遇到不认识的
   `api_version` 必须**显式报错**，不得静默尝试解析（前向不兼容是显式决策，不是事故）。
2. **包版本（SemVer）**：
   - MAJOR：破坏性变更——删除/更名字段、变更占位符名或语义、变更 targets 语义、
     变更片段顺序语义；下游升级 MAJOR 必须重新过门禁（§6）；
   - MINOR：向后兼容新增（新增片段、新增可选字段值、新增 targets）；
   - PATCH：文案修订、不改变渲染产物的修正。
3. **占位符即契约**：`placeholders` 的名字集合是渲染 API 的一部分，视同函数签名；
   删除/更名占位符 = MAJOR。
4. **targets 精确匹配**：v0.1 不支持通配与版本范围；harness 名大小写敏感。

## 6. "生长必过门禁"：`review` 段

PROP-0001 §12.7：骨架人设计（人锁死状态机/铁律/边界/流程），血肉 agent 生长
（SOP、提示词包、技能链）——**生长产物必过演进审批 + 消融**。

落到 OKF：**每个 pack 必须携带 `review` 段**，校验器强制：

- `gate_ref`：指向 GuardrailRun 准入记录的 URI，格式 `guardrail://…`
  （由 glue 仓的 GuardrailRun 协议聚合层签发；准入 = 演进审批 + 消融对照通过 +
  绑定 Spec 版本）。**缺失或非 `guardrail://` 前缀 → invalid**；
- `evidence_ref`：消融/评审证据的 URI（如 `cos://bucket/ablation/<pack>-<ver>.json`）。
  **缺失 → invalid**；
- `approved_at`：可选，ISO 日期 `YYYY-MM-DD`，供 90 天复审参考（v0.1 校验器
  只查格式，不查时效——时效复核是运行手册职责，见 §8）。

> v0.1 边界：校验器只验证引用**存在且格式正确**；无法（也不应）联网核实
> GuardrailRun 记录真伪。真实性由门禁流程与审计负责。

## 7. 渲染语义（`render.py`）

`render_pack(pack, target, params)`：

1. `target` 必须在包级 `targets` 内，否则 `RenderError`；
2. 片段过滤：片段级 `targets` 声明了的按其过滤，否则随包级 targets 全注入；
3. 占位符替换：`{{name}}` → `params[name]`；缺失参数报错；严格模式
   （默认开）下多余参数报错——保证**同一输入渲染产物逐字节确定**，diff 可审；
4. 输出：片段按 manifest 顺序拼接，每段前置溯源头
   `<!-- okf:<name>@<version> target=<t> fragment=<id> slot=<s> -->`。

`render_tool_policy(pack)`：把 `tool_policy` 渲染为确定性文本块
（mode/tools/notes），供 harness 注入工具约束区；真正的工具执行拦截仍由
harness 权限层负责——本仓不做第二个决策点（PROP-0001 §4.9 #3/#7）。

## 8. 复审

- pack 的 `review` 门禁记录按运行手册周检；GuardrailRun 记录 90 天未复审的
  pack 在控制台标记 stale（v0.1 未实现，backlog：与 glue 台账联动）；
- 经验内容更新 = 新 version + 重新消融 + 新 gate_ref，禁止原地改内容不换版本。

## 9. 示例

- `packs/examples/hello-policy/`：最小合法 pack（synthetic）；
- `packs/examples/dev-guard-sop/`：Team Skill SOP 形态——dev 团队三铁律提示词包
  （内容转述自 PROP-0001 v1.6 §4.3，synthetic；含片段级 targets 过滤示例）。

```bash
python -m skillpack.validate packs/examples/hello-policy    # → exit 0
python -m skillpack.validate packs/examples/dev-guard-sop   # → exit 0
```
