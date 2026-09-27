# coding: utf-8
"""doubao_convert 机械转换单元测试（WO D-04）."""
from __future__ import annotations

import textwrap

import pytest

from skillpack.doubao_convert import (
    build_index,
    convert_skill_md,
    convert_tree,
    extract_bins,
    scan_reconnect_tags,
    split_frontmatter,
)

FIXTURE_FULL = textwrap.dedent(
    """\
    ---
    name: lark-demo
    version: 1.4.1
    description: '多维表格：可视化数据库，含冒号与「引号」的触发描述'
    license: MIT
    permissions:
      - shell
    metadata:
      requires:
        bins: ["lark-cli"]
      cliHelp: "lark-cli base --help"
      product: mediakit-cli-doubao/skills
      domain: video
      version: "2.1"
      hub: verifier-hub
      capability_count: 29
      author: CIS AI Application Team
    ---

    # demo

    ## 使用边界

    - Base 业务操作只使用 lark-cli base 命令族。
    - 会话内临时图表不能冒充 Base 交付物。
    """
)

FIXTURE_COMPAT = textwrap.dedent(
    """\
    ---
    name: artifact-preview
    description: "Preview artifacts."
    license: Proprietary — internal use only.
    compatibility: >-
      Linux, macOS or Windows. Needs Python 3.10+ and Pillow; PyMuPDF for pdf.
    ---

    # Artifact Preview

    Render preview files.
    """
)


def _fm_of(text):
    fm, body, had = split_frontmatter(text)
    assert had
    return "\n".join(fm), body


def test_split_frontmatter_basic():
    fm, body, had = split_frontmatter(FIXTURE_FULL)
    assert had
    assert fm[0].startswith("name: lark-demo")
    assert body.lstrip().startswith("# demo")


def test_full_conversion_frontmatter():
    out, rec = convert_skill_md(FIXTURE_FULL, "lark-demo")
    fm, _ = _fm_of(out)
    # name/description/version/license 原样保留
    assert "name: lark-demo" in fm
    assert "description: '多维表格：可视化数据库，含冒号与「引号」的触发描述'" in fm
    assert "version: 1.4.1" in fm
    assert "license: MIT" in fm
    # requires 上提；product/domain/cliHelp 删除；嵌套 version 不重复上提
    assert "requires:" in fm and 'bins: ["lark-cli"]' in fm
    assert "product:" not in fm and "domain:" not in fm and "cliHelp" not in fm
    assert "metadata:" in fm and "hub: verifier-hub" in fm
    assert "capability_count: 29" in fm
    # 顶层 version 已有 → 嵌套 version 不上提也不丢，残留保留
    assert '  version: "2.1"' in fm
    assert fm.count("version:") == 2
    # permissions 不照搬进 frontmatter
    assert "permissions:" not in fm
    assert rec["permissions"] == ["shell"]
    assert rec["dropped"] == ["metadata.product", "metadata.domain"]
    assert rec["hoisted"] == ["metadata.requires"]


def test_full_conversion_body_sections():
    out, rec = convert_skill_md(FIXTURE_FULL, "lark-demo")
    assert "## jiuwenswarm Harness 适配说明" in out
    assert "### 权限映射" in out
    assert 'create_deep_agent(permissions={"tools": {"bash": "ask", "powershell": "ask"}})' in out
    assert "### 环境依赖检查（before_invoke 建议）" in out
    assert "shutil.which" in out
    assert "### 工具自发现" in out and "lark-cli base --help" in out
    assert "### 语义重接记录" in out
    # 适配说明插在首个一级标题之后，领域内容原样保留
    h1 = out.index("# demo")
    adapt = out.index("## jiuwenswarm Harness 适配说明")
    domain = out.index("- Base 业务操作只使用 lark-cli base 命令族。")
    assert h1 < adapt < domain
    assert "会话内临时图表不能冒充 Base 交付物。" in out
    assert rec["requires_bins"] == ["lark-cli"]
    assert rec["cli_help"] == "lark-cli base --help"
    assert rec["version"] == "1.4.1"  # 顶层已有 version，嵌套的不上提


def test_block_scalar_compatibility_carried():
    out, rec = convert_skill_md(FIXTURE_COMPAT, "artifact-preview")
    fm, _ = _fm_of(out)
    assert "compatibility: >-" in fm
    assert "Needs Python 3.10+ and Pillow; PyMuPDF for pdf." in fm
    assert rec["license"] == "Proprietary — internal use only."
    assert rec["permissions"] == []  # 未声明 permissions → 不出现权限映射段
    assert "### 权限映射" not in out
    assert "### 环境依赖检查（before_invoke 建议）" not in out


def test_hoist_metadata_version_when_no_top_level():
    src = FIXTURE_FULL.replace("version: 1.4.1\n", "")
    out, rec = convert_skill_md(src, "lark-demo")
    fm, _ = _fm_of(out)
    assert 'version: "2.1"' in fm
    assert fm.count("version:") == 1
    assert "metadata.version" in rec["hoisted"]


def test_no_frontmatter_raises():
    with pytest.raises(ValueError):
        convert_skill_md("# just body\n", "x")


def test_h1_absent_section_on_top():
    src = "---\nname: x\ndescription: y\n---\n\nbody line\n"
    out, _ = convert_skill_md(src, "x")
    assert out.index("## jiuwenswarm Harness 适配说明") < out.index("body line")
    assert out.index("name: x") < out.index("## jiuwenswarm Harness 适配说明")


def test_extract_bins_variants():
    assert extract_bins(['    bins: ["lark-cli"]']) == ["lark-cli"]
    assert extract_bins(["  bins: [a, b]"]) == ["a", "b"]
    assert extract_bins(["requires: x"]) == []


def test_scan_reconnect_tags():
    body = "用 lark-cli base +url-resolve --as user 打开；豆包定时任务不可用。"
    tags = scan_reconnect_tags(body)
    assert "as-user" in tags and "cron" in tags and "platform-word" in tags
    assert scan_reconnect_tags("普通领域文本") == []


def test_convert_tree(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "s1").mkdir(parents=True)
    (src / "s2").mkdir(parents=True)
    (src / "s1" / "SKILL.md").write_text(FIXTURE_FULL, encoding="utf-8")
    (src / "s2" / "SKILL.md").write_text(FIXTURE_COMPAT, encoding="utf-8")
    (src / "empty-dir").mkdir()  # 无 SKILL.md → 跳过
    records, errors = convert_tree(src, dst)
    assert errors == []
    assert [r["skill"] for r in records] == ["s1", "s2"]
    assert (dst / "s1" / "SKILL.md").read_text(encoding="utf-8").startswith("---")
    index = build_index(records)
    assert "| s1 | 1.4.1 | MIT |" in index
    assert "共 2 个 skill。" in index
    assert "豆包工作客户端" in index and "skill-mapping.md" in index
