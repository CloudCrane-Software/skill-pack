# coding: utf-8
"""校验器正反例测试（manifest 结构 / review 门禁 / 文件存在性 / 版本兼容）."""
from __future__ import annotations

import textwrap

import pytest

from skillpack import ManifestError, load_pack, validate_pack_dir
from skillpack._minyaml import ParseError

MINIMAL_YAML = textwrap.dedent("""\
    api_version: "0.1"
    name: test-pack
    version: 0.1.0
    targets:
      - zcode
    policies:
      - id: p1
        path: policies/p1.md
    prompt_fragments:
      - id: base
        path: prompts/base.md
        placeholders:
          - greeting
    tool_policy:
      mode: allowlist
      tools:
        - read_file
    provenance:
      source: "synthetic test pack"
      method: hand-authored
      synthetic: true
    license: Apache-2.0
    review:
      gate_ref: "guardrail://glue/GuardrailRun/GR-TEST-0001"
      evidence_ref: "cos://bucket/ablation/test-pack.json"
""")

DEFAULT_FILES = {
    "prompts/base.md": "Say {{greeting}} politely.",
    "policies/p1.md": "# policy p1\n",
    "tests/cases.md": "# cases\n",
}


def make_pack(tmp_path, yaml_text=None, files=None, name="test-pack"):
    d = tmp_path / name
    for sub in ("prompts", "policies", "tests"):
        (d / sub).mkdir(parents=True)
    (d / "pack.yaml").write_text(yaml_text if yaml_text is not None else MINIMAL_YAML,
                                 encoding="utf-8")
    merged = dict(DEFAULT_FILES)
    if files is not None:
        for k in list(files):
            if files[k] is None:
                merged.pop(k, None)
            else:
                merged[k] = files[k]
    for rel, content in merged.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return d


def errors_of(tmp_path, **kw):
    _, errs = validate_pack_dir(make_pack(tmp_path, **kw))
    return errs


# ---------------------------------------------------------------- 正例

def test_example_hello_policy_valid(hello_policy_dir):
    pack, errs = validate_pack_dir(hello_policy_dir)
    assert errs == []
    assert pack.name == "hello-policy"
    assert pack.version == "0.1.0"
    assert pack.api_version == "0.1"
    assert pack.review.gate_ref.startswith("guardrail://")


def test_example_dev_guard_sop_valid(dev_guard_sop_dir):
    pack, errs = validate_pack_dir(dev_guard_sop_dir)
    assert errs == []
    assert len(pack.prompt_fragments) == 3


def test_minimal_synthetic_pack_valid(tmp_path):
    pack, errs = validate_pack_dir(make_pack(tmp_path))
    assert errs == []
    assert pack.targets == ("zcode",)
    assert pack.prompt_fragments[0].placeholders == ("greeting",)


def test_load_pack_roundtrip(tmp_path):
    pack = load_pack(make_pack(tmp_path))
    assert pack.resolve("prompts/base.md").is_file()


# ---------------------------------------------------------------- 顶层字段

def test_missing_review_section_invalid(tmp_path):
    yaml = "\n".join(l for l in MINIMAL_YAML.splitlines()
                     if not l.startswith(("review:", "  gate_ref:", "  evidence_ref:")))
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("missing required top-level field: 'review'" in e for e in errs)


def test_review_missing_gate_ref_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace('  gate_ref: "guardrail://glue/GuardrailRun/GR-TEST-0001"\n', "")
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("review: missing field 'gate_ref'" in e for e in errs)


def test_review_missing_evidence_ref_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace('  evidence_ref: "cos://bucket/ablation/test-pack.json"\n', "")
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("review: missing field 'evidence_ref'" in e for e in errs)


def test_gate_ref_wrong_scheme_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace("guardrail://glue/GuardrailRun/GR-TEST-0001",
                                "https://example.com/GR-TEST-0001")
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("gate_ref" in e and "guardrail://" in e for e in errs)


def test_extra_top_level_field_invalid(tmp_path):
    errs = errors_of(tmp_path, yaml_text=MINIMAL_YAML + "extra_field: 1\n")
    assert any("unexpected top-level field: 'extra_field'" in e for e in errs)


def test_missing_required_field_invalid(tmp_path):
    yaml = "\n".join(l for l in MINIMAL_YAML.splitlines() if not l.startswith("name:"))
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("missing required top-level field: 'name'" in e for e in errs)


def test_provenance_missing_method_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace("  method: hand-authored\n", "")
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("provenance: missing field 'method'" in e for e in errs)


def test_all_errors_collected_at_once(tmp_path):
    yaml = MINIMAL_YAML.replace("  method: hand-authored\n", "") + "oops: 1\n"
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("provenance: missing field 'method'" in e for e in errs)
    assert any("unexpected top-level field: 'oops'" in e for e in errs)


# ---------------------------------------------------------------- 值格式

def test_bad_name_invalid(tmp_path):
    errs = errors_of(tmp_path, yaml_text=MINIMAL_YAML.replace("name: test-pack",
                                                              "name: Hello_World"))
    assert any("name must match" in e for e in errs)


def test_bad_version_invalid(tmp_path):
    # 带引号的非 SemVer 字符串 → 格式错误；不带引号的 1.0 会被解析为 float → 类型错误
    errs = errors_of(tmp_path, name="v1",
                     yaml_text=MINIMAL_YAML.replace("version: 0.1.0", 'version: "1.0"'))
    assert any("version must be semver" in e for e in errs)
    errs = errors_of(tmp_path, name="v2",
                     yaml_text=MINIMAL_YAML.replace("version: 0.1.0", "version: 1.0"))
    assert any("version must be a string" in e for e in errs)


def test_unsupported_api_version_invalid(tmp_path):
    errs = errors_of(tmp_path, yaml_text=MINIMAL_YAML.replace('api_version: "0.1"',
                                                              'api_version: "9.9"'))
    assert any("unsupported api_version" in e for e in errs)


def test_targets_empty_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace("targets:\n  - zcode\n", "targets: []\n")
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("targets must not be empty" in e for e in errs)


def test_duplicate_target_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace("targets:\n  - zcode\n",
                                "targets:\n  - zcode\n  - zcode\n")
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("duplicate harness name" in e for e in errs)


def test_tool_policy_bad_mode_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace("mode: allowlist", "mode: yolo")
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("tool_policy.mode must be one of" in e for e in errs)


def test_duplicate_fragment_id_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace(
        "prompt_fragments:\n",
        "prompt_fragments:\n  - id: base\n    path: prompts/base.md\n"
        "    placeholders:\n      - greeting\n",
    )
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("duplicate id 'base'" in e for e in errs)


# ---------------------------------------------------------------- 文件存在性与路径安全

def test_prompt_file_missing_invalid(tmp_path):
    errs = errors_of(tmp_path, files={"prompts/base.md": None})
    assert any("file not found: prompts/base.md" in e for e in errs)


def test_policy_file_missing_invalid(tmp_path):
    errs = errors_of(tmp_path, files={"policies/p1.md": None})
    assert any("policies[0]: file not found: policies/p1.md" in e for e in errs)


def test_path_traversal_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace("path: prompts/base.md", "path: ../secrets/base.md")
    errs = errors_of(tmp_path, yaml_text=yaml, files={})
    assert any("escapes pack dir" in e for e in errs)


def test_prompt_outside_prompts_dir_invalid(tmp_path):
    yaml = MINIMAL_YAML.replace("path: prompts/base.md", "path: tests/cases.md")
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("must live under prompts/" in e for e in errs)


def test_missing_tests_dir_invalid(tmp_path):
    d = make_pack(tmp_path, files={"tests/cases.md": None})
    (d / "tests").rmdir()
    _, errs = validate_pack_dir(d)
    assert any("missing required directory: tests/" in e for e in errs)


def test_empty_tests_dir_invalid(tmp_path):
    d = make_pack(tmp_path, files={"tests/cases.md": None})
    (d / "tests").mkdir(exist_ok=True)
    _, errs = validate_pack_dir(d)
    assert any("tests/ must contain at least one case file" in e for e in errs)


# ---------------------------------------------------------------- 占位符契约

def test_placeholder_used_but_undeclared_invalid(tmp_path):
    errs = errors_of(tmp_path, files={"prompts/base.md": "Say {{greeting}} to {{who}}."})
    assert any("{{who}} used in file but not declared" in e for e in errs)


def test_placeholder_declared_but_unused_invalid(tmp_path):
    errs = errors_of(tmp_path, files={"prompts/base.md": "No placeholder here."})
    assert any("declared but never used" in e for e in errs)


def test_malformed_placeholder_invalid(tmp_path):
    errs = errors_of(tmp_path,
                     files={"prompts/base.md": "Say {{Greeting}} to {{a b}}.",
                            "tests/cases.md": "# c\n"})
    # greeting 声明了但文件里用的 {{Greeting}} 不匹配 snake_case → 双向都会报
    assert any("malformed placeholder" in e for e in errs)


# ---------------------------------------------------------------- YAML 解析

def test_yaml_parse_error_invalid(tmp_path):
    # Tab 缩进：子集解析器直接拒绝
    yaml = MINIMAL_YAML.replace("  - zcode", "\t- zcode")
    from skillpack import _minyaml
    with pytest.raises(ParseError):
        _minyaml.loads(yaml)
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("pack.yaml parse error" in e for e in errs)


def test_yaml_duplicate_key_invalid(tmp_path):
    yaml = MINIMAL_YAML + "version: 9.9.9\n"
    errs = errors_of(tmp_path, yaml_text=yaml)
    assert any("pack.yaml parse error" in e and "duplicate key" in e for e in errs)


def test_top_level_list_invalid(tmp_path):
    _, errs = validate_pack_dir(make_pack(tmp_path, yaml_text="- a\n- b\n"))
    assert any("must be a mapping" in e for e in errs)


def test_pack_yaml_missing_invalid(tmp_path):
    d = tmp_path / "empty-pack"
    d.mkdir()
    _, errs = validate_pack_dir(d)
    assert errs == ["missing pack.yaml"]


def test_dir_missing_invalid(tmp_path):
    _, errs = validate_pack_dir(tmp_path / "nope")
    assert len(errs) == 1 and "not found" in errs[0]
