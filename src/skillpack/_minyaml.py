# coding: utf-8
"""OKF v0.1 专用最小 YAML 子集解析器（纯标准库，零第三方依赖）.

只支持 OKF 策略包 manifest 所需的严格子集（见 docs/okf-spec.md「YAML 子集」一节）：

- 缩进式映射与序列（仅空格缩进，禁 Tab；序列相对其键缩进一级，或与键同级）
- 标量：带引号字符串（'…' / "…"，分别支持 '' 与 \" 转义）、plain 标量
  （true/false/null/~/int/float，其余一律按字符串）
- 行内流式列表 [a, b, c]（仅一层，元素为标量，不允许嵌套）
- 注释：整行 ``#``，以及引号外的 `` #``（井号前有空白）

遇到以下语法直接抛 :class:`ParseError`（不猜测、不降级）：
锚点/别名、块标量 ``|`` 与 ``>``、流式映射 ``{…}``、多文档 ``---``、标签、复杂键。
"""
from __future__ import annotations

import re

__all__ = ["loads", "ParseError"]

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?$")


class ParseError(ValueError):
    """YAML 子集解析失败。``line_no`` 为 1 起始行号。"""

    def __init__(self, line_no, message):
        self.line_no = line_no
        super().__init__("line %d: %s" % (line_no, message))


def loads(text):
    """解析 OKF v0.1 YAML 子集，返回 dict/list/标量。空文档返回 {}。"""
    if not isinstance(text, str):
        raise TypeError("expected str, got %r" % type(text).__name__)
    lines = _scan(text)
    if not lines:
        return {}
    value, i = _parse_block(lines, 0, lines[0][0])
    if i != len(lines):
        _, content, line_no = lines[i]
        raise ParseError(line_no, "unexpected content after top-level block: %r" % content)
    return value


# ---------------------------------------------------------------------------
# 扫描：去空行/注释，产出 (indent, content, line_no) 三元组
# ---------------------------------------------------------------------------

def _scan(text):
    lines = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        leading = raw[: len(raw) - len(raw.lstrip(" "))]
        if "\t" in leading or raw.lstrip(" ").startswith("\t"):
            raise ParseError(line_no, "tab characters are not allowed for indentation")
        content = _strip_comment(stripped)
        if not content:
            continue
        lines.append((len(leading), content, line_no))
    return lines


def _strip_comment(s):
    """去掉引号外、且前方有空白的 ``#`` 注释部分。"""
    quote = None
    i = 0
    while i < len(s):
        ch = s[i]
        if quote == "'":
            if ch == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    i += 2
                    continue
                quote = None
        elif quote == '"':
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                quote = None
        else:
            if ch in ("'", '"'):
                quote = ch
            elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
                return s[:i].rstrip()
        i += 1
    return s.rstrip()


# ---------------------------------------------------------------------------
# 键拆分与标量
# ---------------------------------------------------------------------------

def _split_key(content, line_no):
    """在已去注释的行内容中拆 ``key: rest``。无键结构返回 None。"""
    quote = None
    i = 0
    while i < len(content):
        ch = content[i]
        if quote == "'":
            if ch == "'":
                if i + 1 < len(content) and content[i + 1] == "'":
                    i += 2
                    continue
                quote = None
        elif quote == '"':
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                quote = None
        else:
            if ch in ("'", '"'):
                quote = ch
            elif ch == ":" and (i + 1 == len(content) or content[i + 1] in " \t"):
                key = content[:i].strip()
                rest = content[i + 1:].strip()
                if not key or key[0] in "-?@":
                    return None
                if not _KEY_RE.match(key):
                    raise ParseError(line_no, "invalid key %r" % key)
                return key, rest
        i += 1
    return None


def _parse_inline(s, line_no):
    s = s.strip()
    if not s:
        return None
    c0 = s[0]
    if c0 in ("'", '"'):
        return _parse_quoted(s, line_no)
    if c0 == "[":
        return _parse_flow_list(s, line_no)
    if c0 in "{&*!|>%`":
        raise ParseError(line_no, "unsupported YAML syntax in OKF v0.1 subset: %r" % s[:24])
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s in ("null", "Null", "NULL", "~"):
        return None
    if _INT_RE.match(s):
        return int(s)
    if _FLOAT_RE.match(s):
        return float(s)
    return s


def _parse_quoted(s, line_no):
    q = s[0]
    if len(s) < 2 or not s.endswith(q):
        raise ParseError(line_no, "invalid quoted scalar: %s" % s[:24])
    body = s[1:-1]
    if q == "'":
        if "''" in body:
            body = body.replace("''", "\x00")
            if "'" in body:
                raise ParseError(line_no, "invalid quoted scalar: %s" % s[:24])
            body = body.replace("\x00", "'")
        elif "'" in body:
            raise ParseError(line_no, "invalid quoted scalar: %s" % s[:24])
        return body
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _parse_flow_list(s, line_no):
    if not s.endswith("]"):
        raise ParseError(line_no, "unterminated flow list: %s" % s[:24])
    inner = s[1:-1].strip()
    if not inner:
        return []
    items = []
    for part in _split_flow(inner, line_no):
        if not part:
            raise ParseError(line_no, "empty item in flow list")
        items.append(_parse_inline(part, line_no))
    return items


def _split_flow(s, line_no):
    parts, buf, quote = [], [], None
    i = 0
    while i < len(s):
        ch = s[i]
        if quote == "'":
            buf.append(ch)
            if ch == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                quote = None
        elif quote == '"':
            buf.append(ch)
            if ch == "\\":
                buf.append(s[i + 1] if i + 1 < len(s) else "")
                i += 2
                continue
            if ch == '"':
                quote = None
        else:
            if ch in ("'", '"'):
                quote = ch
                buf.append(ch)
            elif ch == ",":
                parts.append("".join(buf).strip())
                buf = []
            elif ch in "[]{}":
                raise ParseError(line_no, "nested flow collections are not supported")
            else:
                buf.append(ch)
        i += 1
    if quote:
        raise ParseError(line_no, "unterminated quote in flow list")
    parts.append("".join(buf).strip())
    return parts


# ---------------------------------------------------------------------------
# 块结构：映射与序列
# ---------------------------------------------------------------------------

def _is_item(content):
    return content == "-" or content.startswith("- ")


def _parse_block(lines, i, indent):
    if _is_item(lines[i][1]):
        return _parse_list(lines, i, indent)
    return _parse_dict(lines, i, indent)


def _parse_dict(lines, i, indent):
    out = {}
    n = len(lines)
    while i < n:
        cur_indent, content, line_no = lines[i]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise ParseError(line_no, "unexpected indentation")
        if _is_item(content):
            raise ParseError(line_no, "unexpected sequence item in mapping")
        kv = _split_key(content, line_no)
        if kv is None:
            raise ParseError(line_no, "expected 'key: value' entry, got %r" % content)
        key, rest = kv
        if key in out:
            raise ParseError(line_no, "duplicate key %r" % key)
        if rest:
            out[key] = _parse_inline(rest, line_no)
            i += 1
            if i < n and lines[i][0] > indent:
                raise ParseError(lines[i][2],
                                 "unexpected nested block under scalar value of key %r" % key)
        else:
            i += 1
            if i < n and lines[i][0] > indent:
                out[key], i = _parse_block(lines, i, lines[i][0])
            elif i < n and lines[i][0] == indent and _is_item(lines[i][1]):
                out[key], i = _parse_list(lines, i, indent)
            else:
                out[key] = None
    return out, i


def _parse_list(lines, i, indent):
    out = []
    n = len(lines)
    while i < n:
        cur_indent, content, line_no = lines[i]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise ParseError(line_no, "unexpected indentation")
        if not _is_item(content):
            break
        if content == "-":
            i += 1
            if i < n and lines[i][0] > indent:
                val, i = _parse_block(lines, i, lines[i][0])
            else:
                val = None
            out.append(val)
            continue
        after_dash = content[1:]
        if after_dash[:1] == "\t":
            raise ParseError(line_no, "tab characters are not allowed after '-'")
        rest = after_dash.strip()
        rest_col = cur_indent + 1 + (len(after_dash) - len(after_dash.lstrip(" ")))
        kv = _split_key(rest, line_no)
        if kv is None:
            out.append(_parse_inline(rest, line_no))
            i += 1
            if i < n and lines[i][0] > indent:
                raise ParseError(lines[i][2], "unexpected nested block under scalar list item")
            continue
        key, krest = kv
        item = {}
        if krest:
            item[key] = _parse_inline(krest, line_no)
            i += 1
            if i < n and lines[i][0] > rest_col:
                raise ParseError(lines[i][2],
                                 "unexpected nested block under scalar value in list item")
        else:
            i += 1
            if i < n and lines[i][0] > rest_col:
                item[key], i = _parse_block(lines, i, lines[i][0])
            elif i < n and lines[i][0] == rest_col and _is_item(lines[i][1]):
                item[key], i = _parse_list(lines, i, rest_col)
            else:
                item[key] = None
        more, i = _parse_dict(lines, i, rest_col)
        item.update(more)
        out.append(item)
    return out, i
