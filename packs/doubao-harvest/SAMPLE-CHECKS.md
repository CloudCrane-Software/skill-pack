# SAMPLE-CHECKS.md — doubao-harvest 转换产物抽样核对记录（WO D-04 验收动作 3）

- 日期：2026-09-27。抽样方式：`random.Random(20260927).sample(106 skill 目录, 10)`，种子固定可复现。
- 核对人：D-04 开发代理（人工阅读每个文件 frontmatter、适配说明、语义重接记录及改写区段原文）。
- 结构判据：jiuwenswarm Harness SkillUseRail 加载要求——frontmatter `name`+`description` 必需
  （额外字段经 jw 源码证实无害：`agents/harness/common/tools/skill_toolkits.py:44-55`、
  `server/runtime/skill/skill_manager.py` `_parse_skill_md`）；4 个重接点按 CONVERSION.md §1 改写。

## 抽样 10 个核对结论（10/10 通过）

| skill | frontmatter | 重接点改写核对 | 结论 |
|---|---|---|---|
| doubao-academic-evaluator | name/description 齐全，与目录名一致 | 4 点均无命中；姊妹 skill 路由名按领域词汇保留，裁定正确 | 通过 |
| doubao-answer-with-medical-evidence | 齐全 | 「文档确认门/交付前确认」裁定为问诊流程而非反注入段/确认矩阵，不误标，正确 | 通过 |
| doubao-book-writer | 齐全 | 运行时主语「给豆包执行」→「给 jw 执行」；标题/目录名等技能标识保留；frontmatter「豆包办公」按禁改规则未动并说明 | 通过 |
| doubao-dpa-drafter | 齐全；`metadata.dependency` 按「未提及则残留保留」规则保留 | 无命中 | 通过 |
| doubao-industry-analysis | 齐全 | 「对话上下文」「general_search/seed_finance_search」均给出非命中理由，裁定有据 | 通过 |
| doubao-medical-literature-interpretation | 齐全 | `doubao-*` 交接技能名保留；「平台已提供的可读正文」未点名豆包故保留 | 通过 |
| doubao-multiplatform-rewrite | 齐全 | 无命中 | 通过 |
| doubao-product-content | 齐全 | 「MainAgent 环境」「ActionHub」标记为源宿主运行面且**如实列入待人工复核**（未乱改） | 通过 |
| doubao-product-manager | 齐全 | 无命中 | 通过 |
| lark-mail | name/version/description + `requires.bins` 上提正确 | 三处全对：反注入段末 SafetyPromptRail/SecurityRail 兜底标注（行 68）；确认矩阵后 PermissionInterruptRail HITL 映射标注（行 105）；「身份」节自建飞书凭据注入说明（行 119），`--as user` 命令语义保留 | 通过 |

## 另附全量机核（同一日）

- `find packs/doubao-harvest -name SKILL.md | wc -l` → **106**。
- 全量基线 diff（内存重放机械转换 vs 批量编辑代理改后）：frontmatter 106/106 逐字节未动；
  占位符 0 残留；5 条语义重接记录 106/106 齐全；净删除行均在阈值内（`build/d04_verify.py`，ok=true, problem_count=0）。
- 每批抽查 ≥2：19 个批次共 38 样本，diff 区域数 1-2（即记录替换 ±1 处正文改写），无越界改动（`build/d04_batch_sampling.txt`，本地工作区产物，不入 git）。

## 遗留待人工复核（不阻塞验收）

- `doubao-product-content`：源宿主运行面词汇（MainAgent 环境 / ActionHub / lark_cli_exec 入口）的 jw 对应关系待 owner 定夺。
- 全仓 `references/`、`scripts/`、`assets/` 未随收割分发（见 index.md），改造单个 skill 落地时回源 zip 补齐。
