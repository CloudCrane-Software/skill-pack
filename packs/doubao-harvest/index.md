# doubao-harvest pack — 豆包工作 SKILL.md 改造索引

- **来源**：豆包工作客户端收割（Windows 2.30.5，bundle 20260914T100821Z），只含 SKILL.md 主文件；`references/`、`scripts/`、`assets/` 未展开，改造单个 skill 时回源 zip 补齐。
- **改造规则**：`skill-mapping.md`（2026-09-26）→ 可执行化为 `CONVERSION.md`；机械 frontmatter 映射由 `src/skillpack/doubao_convert.py` 完成，4 个重接点语义改写由批量编辑代理按 CONVERSION.md 分批完成。
- **license 口径**：以各 skill frontmatter 为准；未声明者按字节版权 material 处理，仅内部研究参考，对外分发前逐一核 LICENSE。

| skill | version | license | requires.bins | 源permissions | 重接点命中 |
|---|---|---|---|---|---|
| artifact-preview | 2.1 | Proprietary — internal use only. | — | — | — |
| browser-record-replay | — | 未声明 | — | — | platform-word, doubao-word |
| browser-use-automation | — | 未声明 | — | — | browser |
| byted-mediakit-audio | 0.2.1 | MIT | — | shell | — |
| byted-mediakit-editing | 0.2.1 | MIT | — | shell | — |
| byted-mediakit-image | 0.2.1 | MIT | — | shell | — |
| byted-mediakit-shared | 0.2.1 | MIT | mediakit-cli | shell | — |
| byted-mediakit-video | 0.2.1 | MIT | — | shell | — |
| computer-use-automation | — | 未声明 | — | — | browser |
| doubao-academic-evaluator | — | 未声明 | — | — | — |
| doubao-academic-polish | — | 未声明 | — | — | — |
| doubao-academic-researcher | — | 未声明 | — | — | injection |
| doubao-announcement-analysis | — | 未声明 | — | — | — |
| doubao-answer-with-medical-evidence | — | 未声明 | — | — | — |
| doubao-app-builder | — | 未声明 | — | — | — |
| doubao-book-writer | — | 未声明 | — | — | doubao-word |
| doubao-clinical-decision-support | — | 未声明 | — | — | — |
| doubao-compliance-assessment-public | — | 未声明 | — | — | doubao-word |
| doubao-contract-amendment | — | 未声明 | — | — | — |
| doubao-contract-drafting | — | 未声明 | — | — | — |
| doubao-contract-reviewer | — | 未声明 | — | — | doubao-word |
| doubao-creative-design | — | 未声明 | — | — | — |
| doubao-creative-drama | — | 未声明 | — | — | — |
| doubao-creative-video | — | 未声明 | — | — | doubao-word |
| doubao-critical-reading-companion | — | 未声明 | — | — | — |
| doubao-cron-scheduler | — | 未声明 | — | — | cron |
| doubao-cross-border-growth-content | — | 未声明 | — | — | — |
| doubao-customer-service | — | 未声明 | — | — | — |
| doubao-daily-stock | — | 未声明 | — | — | doubao-word |
| doubao-data-analysis | — | 未声明 | — | — | injection |
| doubao-dpa-drafter | — | 未声明 | — | — | — |
| doubao-earnings-analysis | — | 未声明 | — | — | doubao-word |
| doubao-ecommerce-compliance-tax-logistics | — | 未声明 | — | — | — |
| doubao-ecommerce-proposal | — | 未声明 | — | — | — |
| doubao-enterprise-search | — | 未声明 | — | — | doubao-word |
| doubao-finance-model-builder | — | 未声明 | — | — | — |
| doubao-game-designer | — | 未声明 | — | — | doubao-word |
| doubao-headlines-calendar | — | 未声明 | — | — | — |
| doubao-human-signal | — | 未声明 | — | — | injection |
| doubao-identity | — | 未声明 | — | — | cron, platform-word, doubao-word |
| doubao-industry-analysis | — | 未声明 | — | — | — |
| doubao-journal-format | — | 未声明 | — | — | — |
| doubao-listing-localization | — | 未声明 | — | — | — |
| doubao-market-hotspot | — | 未声明 | — | — | injection, doubao-word |
| doubao-marketing-material-review | 1.0 | Proprietary | — | — | — |
| doubao-marketing-plan | — | 未声明 | — | — | — |
| doubao-medical-literature-interpretation | — | 未声明 | — | — | — |
| doubao-medical-literature-monitoring | — | 未声明 | — | — | cron |
| doubao-medical-literature-search | — | 未声明 | — | — | — |
| doubao-medical-literature-translation | — | 未声明 | — | — | — |
| doubao-medical-report | — | 未声明 | — | — | — |
| doubao-multiplatform-rewrite | — | 未声明 | — | — | — |
| doubao-newmedia-writing | — | 未声明 | — | — | doubao-word |
| doubao-novel-writing | — | 未声明 | — | — | injection |
| doubao-oceanengine-adops-agent | — | 未声明 | — | — | — |
| doubao-paper-close-reading | — | 未声明 | — | — | doubao-word |
| doubao-patent-drafting | — | 未声明 | — | — | doubao-word |
| doubao-pc-optimizer | — | 未声明 | — | — | injection |
| doubao-pdf | — | 未声明 | — | — | — |
| doubao-personal-info-audit | — | 未声明 | — | — | — |
| doubao-private-company | — | 未声明 | — | — | injection, doubao-word |
| doubao-product-analysis | — | 未声明 | — | — | — |
| doubao-product-content | — | 未声明 | — | — | doubao-word |
| doubao-product-manager | — | 未声明 | — | — | — |
| doubao-product-qa | — | 未声明 | — | — | doubao-word |
| doubao-product-selection | — | 未声明 | — | — | — |
| doubao-public-company-analysis | — | 未声明 | — | — | injection, doubao-word |
| doubao-questionnaire-designer | — | 未声明 | — | — | — |
| doubao-record | — | 未声明 | — | — | — |
| doubao-reference-audit | — | 未声明 | — | — | doubao-word |
| doubao-research-proposal | — | 未声明 | — | — | doubao-word |
| doubao-sentiment-tracker | — | 未声明 | — | — | doubao-word |
| doubao-stock-screening | — | 未声明 | — | — | doubao-word |
| doubao-ultimate-guide | — | 未声明 | — | — | — |
| doubao-video-extract | — | 未声明 | — | — | doubao-word |
| doubao-visualization | — | 未声明 | — | — | — |
| doubao-wealth-planning | — | 未声明 | — | — | injection, doubao-word |
| gift-card-redemption | — | 未声明 | — | — | doubao-word |
| html | — | 未声明 | — | — | browser |
| lark-approval | 1.2.0 | 未声明 | lark-cli | — | as-user |
| lark-attendance | 1.0.0 | 未声明 | lark-cli | — | injection |
| lark-base | 1.4.1 | 未声明 | lark-cli | — | as-user, cron, platform-word, injection, doubao-word |
| lark-calendar | 1.0.0 | 未声明 | lark-cli | — | as-user |
| lark-contact | 1.0.0 | 未声明 | lark-cli | — | as-user |
| lark-doc | — | 未声明 | lark-cli | — | as-user, doubao-word |
| lark-drive | 1.0.0 | 未声明 | lark-cli | — | doubao-word |
| lark-im | 1.0.0 | 未声明 | lark-cli | — | — |
| lark-mail | 1.0.0 | 未声明 | lark-cli | — | as-user, injection |
| lark-markdown | 1.2.2 | 未声明 | lark-cli | — | as-user |
| lark-meeting | 1.0.0 | 未声明 | lark-cli | — | — |
| lark-okr | 1.0.0 | 未声明 | lark-cli | — | as-user |
| lark-openapi-explorer | 1.0.0 | 未声明 | lark-cli | — | — |
| lark-task | 1.0.0 | 未声明 | lark-cli | — | as-user |
| lark-whiteboard | 1.0.0 | 未声明 | lark-cli | — | as-user |
| lark-wiki | 1.0.3 | 未声明 | lark-cli | — | as-user |
| lark-workflow-standup-report | 1.0.0 | 未声明 | lark-cli | — | injection |
| multi-stock-comparison | — | 未声明 | — | — | — |
| ppt | 1.0.13 | 未声明 | lark-cli | — | — |
| seed-audio | 0.2.0 | 未声明 | — | — | — |
| seedance-25 | — | 未声明 | — | — | doubao-word |
| seedream-50 | — | 未声明 | — | — | — |
| sheet | 3.2.3 | 未声明 | lark-cli, python3 | — | platform-word, injection, doubao-word |
| skill-creator-for-work | — | Complete terms in LICENSE.txt | — | — | user_skills, browser |
| student-discount-application | — | 未声明 | — | — | doubao-word |
| verifier-hub | 2.1 | Proprietary — internal use only. | — | — | — |
| word | 1.0.30 | 未声明 | python | — | doubao-word |

共 106 个 skill。
