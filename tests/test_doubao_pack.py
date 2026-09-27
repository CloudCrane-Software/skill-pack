# coding: utf-8
"""packs/doubao-harvest 产物结构守卫（WO D-04 验收）.

对 106 个转换产物做结构断言：frontmatter 必需字段、禁删字段已清除、
适配说明与语义重接记录存在、index.md 汇总一致、无密钥泄漏。
"""
from __future__ import annotations

import re
from pathlib import Path

PACK_DIR = Path(__file__).resolve().parents[1] / "packs" / "doubao-harvest"

# 拼接构造，避免按字面命中本文件自身的密钥扫描
_SECRET_RE = re.compile(
    "|".join(["gh" + "p_", "github" + "_pat_", "sk-[A-Za-z0-9]{16,}", "Bearer [A-Za-z0-9]{16,}"])
)
_FM_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")


def _frontmatter_lines(text):
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "缺少 frontmatter"
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    raise AssertionError("frontmatter 未闭合")


def _fm_value(fm_lines, key):
    for line in fm_lines:
        m = _FM_KEY_RE.match(line)
        if m and m.group(1) == key:
            return m.group(2).strip().strip("'\"")
    return None


def _iter_skill_dirs():
    return sorted(p for p in PACK_DIR.iterdir() if p.is_dir())


def test_pack_dir_exists():
    assert PACK_DIR.is_dir()


def test_106_skill_dirs_with_skill_md():
    dirs = _iter_skill_dirs()
    assert len(dirs) == 106, "期望 106 个 skill 目录，实际 %d" % len(dirs)
    for d in dirs:
        assert (d / "SKILL.md").is_file(), "%s 缺 SKILL.md" % d.name


def test_frontmatter_required_fields_and_name_matches_dir():
    for d in _iter_skill_dirs():
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        fm = _frontmatter_lines(text)
        name = _fm_value(fm, "name")
        desc = _fm_value(fm, "description")
        assert name == d.name, "%s: name(%r) 与目录名不一致" % (d.name, name)
        assert desc, "%s: description 为空" % d.name


def test_doubao_specific_fields_removed():
    for d in _iter_skill_dirs():
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        fm = _frontmatter_lines(text)
        for line in fm:
            m = _FM_KEY_RE.match(line)
            if m and m.group(1) == "metadata":
                continue
            key = m.group(1) if m else ""
            assert key not in ("permissions",), "%s: permissions 未按映射处理" % d.name
        fm_text = "\n".join(fm)
        for bad in ("  product:", "  domain:", "  cliHelp:", "  requires:"):
            assert bad not in fm_text, "%s: metadata.%s 未清除/上提" % (d.name, bad.strip())


def test_adaptation_and_semantic_record_present():
    for d in _iter_skill_dirs():
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        assert "## jiuwenswarm Harness 适配说明" in text, d.name
        assert "### 语义重接记录" in text, d.name
        assert "（待语义改写批次填写" not in text, "%s: 语义重接记录仍是占位符" % d.name


def test_index_md_summary():
    index = (PACK_DIR / "index.md").read_text(encoding="utf-8")
    assert "共 106 个 skill。" in index
    assert "豆包工作客户端" in index and "skill-mapping.md" in index
    for d in _iter_skill_dirs():
        assert ("| %s |" % d.name) in index, "%s 未列入 index.md" % d.name


def test_no_secrets_in_pack():
    for p in PACK_DIR.rglob("*"):
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            assert not _SECRET_RE.search(text), "疑似密钥命中: %s" % p
