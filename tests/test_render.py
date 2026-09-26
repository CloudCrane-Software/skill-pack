# coding: utf-8
"""渲染器测试：targets 过滤、占位符替换、参数严格性、tool_policy 文本."""
from __future__ import annotations

import pytest

from skillpack import RenderError, load_pack, render_pack, render_tool_policy, render_fragment


@pytest.fixture(scope="module")
def hello(hello_policy_dir):
    return load_pack(hello_policy_dir)


@pytest.fixture(scope="module")
def sop(dev_guard_sop_dir):
    return load_pack(dev_guard_sop_dir)


def test_render_hello_policy_contains_content(hello):
    out = render_pack(hello, "zcode", {"assistant_name": "Ada"})
    assert "You are Ada, a helpful assistant." in out
    assert "okf:hello-policy@0.1.0 target=zcode fragment=base slot=system" in out
    assert out.endswith("\n")


def test_render_replaces_all_occurrences(hello):
    out = render_pack(hello, "jiuwen-code", {"assistant_name": "Ada"})
    assert "{{" not in out and "}}" not in out
    assert out.count("Ada") == 1


def test_render_missing_param_raises(hello):
    with pytest.raises(RenderError, match="missing params"):
        render_pack(hello, "zcode", {})


def test_render_extra_param_raises_strict(hello):
    with pytest.raises(RenderError, match="unused params"):
        render_pack(hello, "zcode", {"assistant_name": "Ada", "extra": "x"})


def test_render_extra_param_allowed_non_strict(hello):
    out = render_pack(hello, "zcode", {"assistant_name": "Ada", "extra": "x"},
                      strict_params=False)
    assert "You are Ada" in out


def test_render_target_not_in_pack_raises(hello):
    with pytest.raises(RenderError, match="not in pack"):
        render_pack(hello, "unknown-harness", {})


def test_render_deterministic(hello):
    a = render_pack(hello, "zcode", {"assistant_name": "Ada"})
    b = render_pack(hello, "zcode", {"assistant_name": "Ada"})
    assert a == b


def test_render_fragment_level_target_filtering(sop):
    """sop-meta 片段仅声明 jiuwen-code：zcode 渲染 2 段，jiuwen-code 渲染 3 段."""
    out_z = render_pack(sop, "zcode", {"team_name": "Dev"})
    out_j = render_pack(sop, "jiuwen-code", {"team_name": "Dev"})
    assert out_z.count("<!-- okf:dev-guard-sop@0.1.0") == 2
    assert out_j.count("<!-- okf:dev-guard-sop@0.1.0") == 3
    assert "SOP 元信息" not in out_z
    assert "SOP 元信息" in out_j
    # 其余片段对两个 target 一致（头部的 target= 字段归一后，out_z 是 out_j 的前缀）
    assert out_j.replace("target=jiuwen-code", "target=zcode").startswith(out_z)


def test_render_sop_iron_rules_paraphrased(sop):
    out = render_pack(sop, "zcode", {"team_name": "Core"})
    assert "You are a dev-team agent of Core." in out
    assert "消息 ≠ 承接" in out
    assert "对话历史 ≠ Team State" in out


def test_render_tool_policy_text(hello):
    txt = render_tool_policy(hello)
    assert txt == (
        "<!-- okf:hello-policy@0.1.0 tool-policy -->\n"
        "tool_policy.mode: allowlist\n"
        "tool_policy.tools: read_file, web_search\n"
        "tool_policy.notes: 最小权限：只读与检索类工具\n"
    )


def test_render_fragment_helper_direct(hello):
    frag = hello.prompt_fragments[0]
    assert render_fragment(frag, {"assistant_name": "X"}) .startswith("You are X,")
