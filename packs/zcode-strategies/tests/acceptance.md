<!-- distill: OKF v0.1 docs/okf-spec.md sections 3, 6, and 7, checked against this pack's manifest and the zcode extraction record dated 2026-09-27 -->

# Pack acceptance — zcode-strategies 0.1.0

Checklist for the pack as shipped. Each item is a pass/fail check a reviewer can run without opening the upstream bundle.

- [ ] Closed manifest. `pack.yaml` contains only the OKF v0.1 fields: `api_version`, `name`, `version`, `targets`, `policies`, `prompt_fragments`, `tool_policy`, `provenance`, `license`, `review`. No extra keys. `api_version` is `"0.1"`. `name` is `zcode-strategies`. `version` is `0.1.0`. `targets` is exactly `[zcode]`.
- [ ] Paths stay inside the pack. Every `policies[].path` is under `policies/` and exists. Every `prompt_fragments[].path` is under `prompts/` and exists. No `..`, no drive letter, no absolute path. `tool_policy.mode` is `allowlist` and `tools` is a non-empty list of strings.
- [ ] No placeholders. No prompt fragment and no policy file contains a mustache placeholder (an opening double brace, a name, and a closing double brace). No fragment declares a placeholders list. Rendering with an empty parameter map must succeed.
- [ ] Render for `target=zcode`. `render_pack` accepts `zcode` and emits the five fragments in manifest order (`base-identity`, `workflow-actor`, `explore-readonly`, `memory-discipline`, `tool-use`), each preceded by an `okf:` provenance header with `target=zcode` and `slot=system`. Any other target is a render error.
- [ ] Provenance is checkable. `provenance.synthetic` is `false`. `provenance.source` names `zcode-app-cli 3.14.3-28`, `vendor/zcode.cjs`, and the string offsets used for extraction. `provenance.method` states distillation by paraphrase, not a verbatim copy. `extracted_at` is `2026-09-27`. `license` is `Apache-2.0`.
- [ ] Not a verbatim copy. Each fragment and the permission policy opens with an HTML comment naming the source section or offset. Body text is an English rewrite. A reviewer who diffs a fragment against the section text at that offset must not find a copied paragraph.
- [ ] Review gate is stated honestly. `review.gate_ref` is `guardrail://local/windev-01/wo-D-02/2026-09-27` (local work-order record, `guardrail://` prefix). `review.evidence_ref` points at this file. `review.approved_at` is `2026-09-27`. `provenance.notes` records that formal GuardrailRun admission and the ablation contrast are still pending the owner process. Do not treat this pack as ablation-passed.
- [ ] Fragment size and topic. Identity, workflow actor, explore, memory, and tool-use fragments are each 20 to 50 lines. The permission-mode policy is 20 to 40 lines and contains the `build` / `edit` / `plan` / `yolo` table plus the `allowedPrompts` rule that entries name action categories, not concrete commands.
- [ ] YAML subset. `pack.yaml` uses spaces only. It has no block scalar (`|` or `>`), no flow mapping, no anchor or alias, no tab, and no multi-document marker.
