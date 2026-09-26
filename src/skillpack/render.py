# coding: utf-8
"""OKF 策略包 → harness system-prompt 片段渲染.

语义（docs/okf-spec.md「渲染」一节）：

- **按 targets 过滤**：目标 harness 必须在包级 ``targets`` 内；片段若声明了
  片段级 ``targets``，只对其中列出的 harness 注入；
- **占位符替换**：``{{name}}`` 由 ``params[name]`` 替换；缺失参数报错；
  严格模式下多余参数也报错（渲染产物确定性，便于 diff 审查）；
- 输出为带 ``<!-- okf:… -->`` 溯源头的单个 system-prompt 片段字符串。
"""
from __future__ import annotations

from .manifest import PLACEHOLDER_RE

__all__ = ["RenderError", "render_fragment", "render_pack", "render_tool_policy"]


class RenderError(ValueError):
    pass


def render_fragment(fragment, params):
    """渲染单个片段：``{{name}}`` → ``params[name]``。"""
    params = dict(params or {})

    def _sub(match):
        return str(params[match.group(1)])

    return PLACEHOLDER_RE.sub(_sub, fragment.content)


def render_pack(pack, target, params=None, *, strict_params=True):
    """把 pack 渲染为注入 harness 的 system-prompt 片段字符串.

    - ``target`` 不在包级 targets → :class:`RenderError`；
    - 过滤后没有片段 → :class:`RenderError`；
    - 参数缺失 / （严格模式下）参数多余 → :class:`RenderError`。
    """
    params = dict(params or {})
    if target not in pack.targets:
        raise RenderError(
            "target %r is not in pack %s targets %s"
            % (target, pack.name, list(pack.targets))
        )
    fragments = pack.fragments_for(target)
    if not fragments:
        raise RenderError("pack %s has no fragments for target %r" % (pack.name, target))

    needed = set()
    for f in fragments:
        needed |= set(f.placeholders)
    missing = sorted(needed - set(params))
    extra = sorted(set(params) - needed)
    if missing:
        raise RenderError("missing params for pack %s: %s" % (pack.name, ", ".join(missing)))
    if extra and strict_params:
        raise RenderError(
            "unused params for pack %s (strict_params=True): %s"
            % (pack.name, ", ".join(extra))
        )

    blocks = []
    for f in fragments:
        header = "<!-- okf:%s@%s target=%s fragment=%s slot=%s -->" % (
            pack.name, pack.version, target, f.id, f.slot,
        )
        body = render_fragment(f, params).rstrip("\n")
        blocks.append(header + "\n" + body)
    return "\n\n".join(blocks) + "\n"


def render_tool_policy(pack):
    """把 tool_policy 渲染为确定性的文本块（供 harness 注入工具约束区）."""
    tp = pack.tool_policy
    lines = ["<!-- okf:%s@%s tool-policy -->" % (pack.name, pack.version)]
    lines.append("tool_policy.mode: %s" % tp.get("mode"))
    lines.append("tool_policy.tools: %s" % ", ".join(tp.get("tools", [])))
    notes = tp.get("notes")
    if notes:
        lines.append("tool_policy.notes: %s" % notes)
    return "\n".join(lines) + "\n"
