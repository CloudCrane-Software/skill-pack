# coding: utf-8
"""豆包工作 SKILL.md → jiuwenswarm Harness SKILL.md 机械转换器.

只做机械部分（WO D-04）：
- frontmatter 字段映射：name/description 原样；version/license/compatibility 原样保留；
  ``metadata.requires`` 上提为顶层 ``requires``；``metadata.version`` 在无顶层 version 时上提；
  ``metadata.product`` / ``metadata.domain`` 删除（skill-mapping.md §2）；``metadata.cliHelp``
  移入正文；``permissions: [shell]`` 不照搬（jw 是执行层拦截），翻译为正文中的
  ``create_deep_agent(permissions=...)`` 建议配置。
- body 在首个一级标题后插入「jiuwenswarm Harness 适配说明」机械段（来源标注、
  资源边界提醒、权限映射、环境检查、CLI 自发现）。

语义改写（4 个重接点 + 平台字样裁定）不在本脚本内，由批量编辑代理按
``packs/doubao-harvest/CONVERSION.md`` 分批完成。

纯标准库。用法：
    python -m skillpack.doubao_convert --src <skills-harvest> --dst <packs/doubao-harvest> \
        --index <packs/doubao-harvest/index.md>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

__all__ = ["convert_skill_md", "build_index", "main"]

_TOP_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")
_NEST_KEY_RE = re.compile(r"^([ ]+)([A-Za-z_][A-Za-z0-9_-]*):(.*)$")
_H1_RE = re.compile(r"^# .*$")
_LIST_ITEM_RE = re.compile(r"^\s*-\s+(.+?)\s*$")

# frontmatter 中原样保留的顶层字段
_CARRY_FIELDS = ("name", "description", "version", "Version", "license", "compatibility")
# metadata 子键处置：drop=删除；hoist_requires=上提顶层 requires；
# to_body=移入正文；hoist_version=无顶层 version 时上提；keep=残留保留
_META_ACTIONS = {
    "product": "drop",
    "domain": "drop",
    "requires": "hoist_requires",
    "cliHelp": "to_body",
    "version": "hoist_version",
}

_ADAPT_TITLE = "## jiuwenswarm Harness 适配说明"
_SEMANTIC_RECORD = """### 语义重接记录

（待语义改写批次填写：4 个重接点命中情况 + 平台字样裁定；规则见 CONVERSION.md）
"""


def split_frontmatter(text: str):
    """按首个 ``---`` 对拆分，返回 (frontmatter 行列表, 正文, 是否有 frontmatter)。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text, False
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:]), True
    return [], text, False


def split_top_fields(fm_lines):
    """把 frontmatter 行按顶层键分桶，保持顺序。返回 [(key, rest, 行列表), ...]。"""
    fields = []
    cur = None
    for line in fm_lines:
        m = _TOP_KEY_RE.match(line)
        if m:
            cur = (m.group(1), m.group(2).strip(), [])
            fields.append(cur)
        elif cur is not None:
            cur[2].append(line)
        # 无所属键的散行（不应出现）忽略
    return fields


def split_meta_subfields(meta_lines):
    """把 ``metadata:`` 块按二级键分桶。返回 [(key, rest, 行列表), ...]（行含原缩进）。"""
    subs = []
    cur = None
    for line in meta_lines:
        m = _NEST_KEY_RE.match(line)
        if m and len(m.group(1)) <= 2:
            cur = (m.group(2), m.group(3).strip(), [])
            subs.append(cur)
        elif cur is not None:
            cur[2].append(line)
    return subs


def parse_list_items(lines, rest):
    """解析 YAML 简单列表（流式 ``[a, b]`` 或块式 ``- x``）。"""
    if rest.startswith("[") and rest.endswith("]"):
        inner = rest[1:-1].strip()
        if not inner:
            return []
        return [p.strip().strip("'\"") for p in inner.split(",") if p.strip()]
    items = []
    for line in lines:
        m = _LIST_ITEM_RE.match(line)
        if m:
            items.append(m.group(1).strip("'\""))
    return items


def strip_quotes(value):
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    return v


def _dedent2(lines):
    return [ln[2:] if ln.startswith("  ") else ln for ln in lines]


_BINS_RE = re.compile(r"^\s+bins:\s*(.+?)\s*$")


def extract_bins(lines):
    """从 requires 子块原始行中提取 bins 流式列表（任意缩进）。"""
    for line in lines:
        m = _BINS_RE.match(line)
        if m:
            return parse_list_items([], m.group(1))
    return []


def adaptation_section(record):
    """生成「jiuwenswarm Harness 适配说明」机械段。"""
    parts = [_ADAPT_TITLE, ""]
    parts.append(
        "> 来源：豆包工作客户端（Windows 2.30.5，bundle 20260914T100821Z）收割的 SKILL.md 主文件；"
        "改造规则见 `packs/doubao-harvest/CONVERSION.md`（源映射：`skill-mapping.md`，2026-09-26）。"
    )
    parts.append(
        "> 资源边界：源包内 `references/`、`scripts/`、`assets/` 未随本收割分发，需回源 zip 补齐；"
        "运行时引用路径必须落在 jw workspace 边界内（PermissionEngine external_directory 策略会拦截外部路径）。"
    )
    parts.append("")
    if record["permissions"]:
        parts.append("### 权限映射")
        parts.append("")
        parts.append(
            "源 frontmatter 声明 `permissions: [%s]`（豆包为声明式提示）。jiuwenswarm Harness "
            "PermissionEngine 是执行层拦截，两者不同构，建议按此配置："
            % ", ".join(record["permissions"])
        )
        parts.append("")
        parts.append("```python")
        parts.append(
            'create_deep_agent(permissions={"tools": {"bash": "ask", "powershell": "ask"}})'
        )
        parts.append("```")
        parts.append("")
        parts.append(
            "正文中标注的「高风险操作」清单原样保留，交由 PermissionEngine / "
            "PermissionInterruptRail 执行层兜底。"
        )
        parts.append("")
    if record["requires_bins"]:
        bins = record["requires_bins"]
        parts.append("### 环境依赖检查（before_invoke 建议）")
        parts.append("")
        parts.append(
            "本 skill 依赖外部命令：%s。建议在 harness 侧挂 before_invoke 环境检查："
            % "、".join("`%s`" % b for b in bins)
        )
        parts.append("")
        parts.append("```python")
        parts.append("import shutil")
        parts.append("missing = [b for b in %r if shutil.which(b) is None]" % (bins,))
        parts.append("if missing:")
        parts.append('    raise RuntimeError(f"缺少外部命令：{missing}；请先安装并确保在 PATH 中")')
        parts.append("```")
        parts.append("")
    if record["cli_help"]:
        parts.append("### 工具自发现")
        parts.append("")
        parts.append(
            "源 `metadata.cliHelp`：`%s`（原样保留；jw 渐进式工具暴露下可用同款命令自发现子命令）。"
            % record["cli_help"]
        )
        parts.append("")
    parts.append(_SEMANTIC_RECORD.rstrip())
    return "\n".join(parts)


def insert_after_h1(body, section):
    """在首个一级标题后插入 section；无一级标题则插到正文最前。"""
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if _H1_RE.match(line):
            head, tail = lines[: i + 1], lines[i + 1:]
            out = head + [""] + section.splitlines() + [""]
            return "\n".join(out + tail).rstrip() + "\n"
    return section.rstrip() + "\n\n" + "\n".join(lines).lstrip("\n")


def convert_skill_md(text, skill_name):
    """转换单个 SKILL.md 文本。返回 (新文本, record)；record 供 index 与测试断言。"""
    record = {
        "skill": skill_name,
        "version": "",
        "license": "",
        "requires_bins": [],
        "cli_help": "",
        "permissions": [],
        "dropped": [],
        "hoisted": [],
        "to_body": [],
        "had_frontmatter": False,
    }
    fm_lines, body, had_fm = split_frontmatter(text)
    if not had_fm:
        raise ValueError("SKILL.md 缺少 frontmatter: %s" % skill_name)
    record["had_frontmatter"] = True

    out_lines = []
    meta_blocks = {}  # key -> (rest, lines) 保留残留下
    for key, rest, sub in split_top_fields(fm_lines):
        if key in _CARRY_FIELDS:
            out_lines.append("%s:%s" % (key, (" " + rest) if rest else ""))
            out_lines.extend(sub)
            if key == "version":
                record["version"] = strip_quotes(rest)
            elif key == "license":
                record["license"] = strip_quotes(rest)
        elif key == "permissions":
            items = parse_list_items(sub, rest)
            record["permissions"] = items
            if not items:
                # 无法解析的 permissions 原样保留，宁多勿丢
                out_lines.append("permissions:%s" % ((" " + rest) if rest else ""))
                out_lines.extend(sub)
            # 可解析则不照搬进 frontmatter（进正文权限映射段）
        elif key == "metadata":
            meta_blocks = {k: (r, s) for k, r, s in split_meta_subfields(sub)}
        else:
            # 未知顶层字段：原样保留（jw 容忍额外字段，已由源码证实）
            out_lines.append("%s:%s" % (key, (" " + rest) if rest else ""))
            out_lines.extend(sub)

    # metadata 子键处置
    residue = []
    hoisted_version = False
    for key, (rest, sub) in meta_blocks.items():
        action = _META_ACTIONS.get(key, "keep")
        if action == "drop":
            record["dropped"].append("metadata.%s" % key)
        elif action == "hoist_requires":
            out_lines.append("requires:")
            out_lines.extend(_dedent2(sub))
            record["hoisted"].append("metadata.requires")
            record["requires_bins"] = extract_bins(sub)
        elif action == "to_body":
            record["cli_help"] = strip_quotes(rest)
            record["to_body"].append("metadata.cliHelp")
        elif action == "hoist_version":
            if record["version"]:
                residue.append((key, rest, sub))  # 双 version 共存：残留保留
            else:
                out_lines.append("version: %s" % rest)
                record["version"] = strip_quotes(rest)
                record["hoisted"].append("metadata.version")
                hoisted_version = True
        else:
            residue.append((key, rest, sub))
    if residue:
        out_lines.append("metadata:")
        for key, rest, sub in residue:
            out_lines.append("  %s:%s" % (key, (" " + rest) if rest else ""))
            out_lines.extend(sub)

    # bins 提取兜底：requires 未带 bins（或残留场景）时仍尽力提取供正文段使用
    if not record["requires_bins"]:
        req = meta_blocks.get("requires")
        if req:
            record["requires_bins"] = extract_bins(req[1])

    new_fm = "\n".join(out_lines).rstrip()
    section = adaptation_section(record)
    new_body = insert_after_h1(body, section)
    text_out = "---\n%s\n---\n\n%s" % (new_fm, new_body.lstrip("\n") if body.startswith("\n") else new_body)
    return text_out, record


def scan_reconnect_tags(body):
    """重接点命中标签（供 index 与批量编辑代理分批参考）。"""
    tags = []
    if "--as user" in body:
        tags.append("as-user")
    if re.search(r"定时任务|cron", body):
        tags.append("cron")
    if "user_skills" in body:
        tags.append("user_skills")
    if re.search(r"browser use|browser_agent|computer_use_tool|seed_browser_use", body, re.I):
        tags.append("browser")
    if re.search(r"豆包工作|豆包会话|豆包客户端|豆包平台|豆包定时|豆包侧", body):
        tags.append("platform-word")
    if re.search(r"不可信|注入|prompt.injection", body):
        tags.append("injection")
    if re.search(r"豆包", body):
        tags.append("doubao-word")
    return tags


def convert_tree(src_dir, dst_dir):
    """转换 src 下全部 <skill>/SKILL.md。返回 (records, errors)。"""
    src, dst = Path(src_dir), Path(dst_dir)
    records, errors = [], []
    for skill_dir in sorted(p for p in src.iterdir() if p.is_dir()):
        src_md = skill_dir / "SKILL.md"
        if not src_md.is_file():
            continue
        try:
            text = src_md.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append("%s: 读取失败 %s" % (skill_dir.name, exc))
            continue
        try:
            out_text, record = convert_skill_md(text, skill_dir.name)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        record["reconnect_tags"] = scan_reconnect_tags(
            text.split("---", 2)[-1] if text.count("---") >= 2 else text
        )
        out_dir = dst / skill_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "SKILL.md").write_text(out_text, encoding="utf-8", newline="\n")
        records.append(record)
    return records, errors


def build_index(records):
    lines = [
        "# doubao-harvest pack — 豆包工作 SKILL.md 改造索引",
        "",
        "- **来源**：豆包工作客户端收割（Windows 2.30.5，bundle 20260914T100821Z），只含 SKILL.md 主文件；"
        "`references/`、`scripts/`、`assets/` 未展开，改造单个 skill 时回源 zip 补齐。",
        "- **改造规则**：`skill-mapping.md`（2026-09-26）→ 可执行化为 `CONVERSION.md`；"
        "机械 frontmatter 映射由 `src/skillpack/doubao_convert.py` 完成，4 个重接点语义改写由 "
        "批量编辑代理按 CONVERSION.md 分批完成。",
        "- **license 口径**：以各 skill frontmatter 为准；未声明者按字节版权 material 处理，"
        "仅内部研究参考，对外分发前逐一核 LICENSE。",
        "",
        "| skill | version | license | requires.bins | 源permissions | 重接点命中 |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(records, key=lambda x: x["skill"]):
        lines.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (
                r["skill"],
                r["version"] or "—",
                (r["license"] or "未声明").replace("|", "\\|"),
                ", ".join(r["requires_bins"]) or "—",
                ", ".join(r["permissions"]) or "—",
                ", ".join(r["reconnect_tags"]) or "—",
            )
        )
    lines.append("")
    lines.append("共 %d 个 skill。" % len(records))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="doubao SKILL.md mechanical converter")
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--index", default=None)
    ap.add_argument("--expect", type=int, default=106)
    args = ap.parse_args(argv)
    records, errors = convert_tree(args.src, args.dst)
    if errors:
        for e in errors:
            print("ERROR: %s" % e, file=sys.stderr)
    if args.index:
        Path(args.index).parent.mkdir(parents=True, exist_ok=True)
        Path(args.index).write_text(build_index(records), encoding="utf-8", newline="\n")
    summary = {"converted": len(records), "errors": errors, "expected": args.expect}
    print(json.dumps(summary, ensure_ascii=False))
    if len(records) != args.expect or errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
