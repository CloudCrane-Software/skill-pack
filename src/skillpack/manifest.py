# coding: utf-8
"""OKF（Open Knowledge Format）策略包 manifest：加载 + 严格校验.

规则（与 docs/okf-spec.md 一一对应）：

- 顶层字段**缺失或多余**都报错（字段集封闭）；
- ``api_version`` 不在 :data:`SUPPORTED_API_VERSIONS` 内直接 invalid（版本兼容规则）；
- prompt/policy 引用的文件必须存在、必须落在对应目录内、不得路径逃逸；
- 占位符：片段文件里出现的 ``{{name}}`` 与 manifest 声明的 ``placeholders``
  必须**双向一致**，格式不合法的占位符报错；
- ``review`` 段（gate_ref/evidence_ref）必填——"生长必过门禁"，缺失即 invalid；
- 所有错误**一次收集**（不遇错即停），便于校验器一次性给出完整清单。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from . import _minyaml

__all__ = [
    "API_VERSION",
    "SUPPORTED_API_VERSIONS",
    "ManifestError",
    "Pack",
    "PromptFragment",
    "Review",
    "PolicyRef",
    "load_pack",
    "validate_manifest",
    "validate_pack_dir",
    "PLACEHOLDER_RE",
]

# OKF 格式版本：本实现支持的集合。manifest 的 api_version 不在其中 → invalid。
API_VERSION = "0.1"
SUPPORTED_API_VERSIONS = ("0.1",)

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}")
_RAW_PLACEHOLDER_RE = re.compile(r"\{\{\s*([^{}]*?)\s*\}\}")

_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
_TARGET_RE = re.compile(r"^[a-z][a-z0-9._-]{0,62}$")
_PARAM_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_URI_RE = re.compile(r"^[a-z][a-z0-9+.\-]*://\S+$", re.IGNORECASE)
_GATE_REF_RE = re.compile(r"^guardrail://\S+$")

TOP_REQUIRED = {
    "api_version", "name", "version", "targets", "policies",
    "prompt_fragments", "tool_policy", "provenance", "license", "review",
}

POLICY_KEYS = {"id", "path", "description"}
POLICY_REQUIRED = {"id", "path"}

FRAGMENT_KEYS = {"id", "path", "slot", "targets", "placeholders"}
FRAGMENT_REQUIRED = {"id", "path"}
SLOTS = ("system", "developer")

TOOL_POLICY_KEYS = {"mode", "tools", "notes"}
TOOL_POLICY_REQUIRED = {"mode", "tools"}
TOOL_MODES = ("allowlist", "denylist")

PROVENANCE_KEYS = {"source", "method", "extracted_at", "synthetic", "notes"}
PROVENANCE_REQUIRED = {"source", "method"}

REVIEW_KEYS = {"gate_ref", "evidence_ref", "approved_at"}
REVIEW_REQUIRED = {"gate_ref", "evidence_ref"}


class ManifestError(ValueError):
    """manifest 非法。``errors`` 为全部错误清单。"""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


# ---------------------------------------------------------------------------
# 数据对象
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PolicyRef:
    id: str
    path: str
    description: str = ""


@dataclass(frozen=True)
class PromptFragment:
    id: str
    path: str
    slot: str = "system"
    targets: tuple = ()
    placeholders: tuple = ()
    content: str = ""


@dataclass(frozen=True)
class Review:
    gate_ref: str
    evidence_ref: str
    approved_at: str = ""


@dataclass(frozen=True)
class Pack:
    pack_dir: Path
    api_version: str
    name: str
    version: str
    targets: tuple
    policies: tuple
    prompt_fragments: tuple
    tool_policy: dict
    provenance: dict
    license: str
    review: Review

    def fragments_for(self, target):
        """按 target 过滤片段：片段未声明 targets 时继承包级 targets。"""
        return tuple(f for f in self.prompt_fragments if target in f.targets)

    def resolve(self, rel_path):
        return self.pack_dir.joinpath(*PurePosixPath(rel_path.replace("\\", "/")).parts)


# ---------------------------------------------------------------------------
# 校验
# ---------------------------------------------------------------------------

def validate_pack_dir(pack_dir):
    """校验一个 pack 目录。返回 ``(Pack | None, errors)``。

    ``errors`` 非空即 invalid；``Pack`` 仅在零错误时返回。
    """
    errors = []
    pack_dir = Path(pack_dir)
    if not pack_dir.is_dir():
        return None, ["pack directory not found: %s" % pack_dir]
    pack_yaml = pack_dir / "pack.yaml"
    if not pack_yaml.is_file():
        return None, ["missing pack.yaml"]
    try:
        text = pack_yaml.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, ["pack.yaml unreadable: %s" % exc]
    try:
        data = _minyaml.loads(text)
    except _minyaml.ParseError as exc:
        return None, ["pack.yaml parse error: %s" % exc]
    if not isinstance(data, dict):
        return None, ["pack.yaml must be a mapping at top level"]
    return validate_manifest(data, pack_dir)


def validate_manifest(data, pack_dir):
    """严格校验 manifest dict。返回 ``(Pack | None, errors)``，错误全量收集。"""
    errors = []
    pack_dir = Path(pack_dir)

    extra = sorted(set(data) - TOP_REQUIRED)
    missing = sorted(TOP_REQUIRED - set(data))
    for k in extra:
        errors.append("unexpected top-level field: %r" % k)
    for k in missing:
        errors.append("missing required top-level field: %r" % k)

    api_version = data.get("api_version")
    if api_version is not None and not isinstance(api_version, str):
        errors.append("api_version must be a string")
    elif isinstance(api_version, str) and api_version not in SUPPORTED_API_VERSIONS:
        errors.append(
            "unsupported api_version %r (supported: %s)"
            % (api_version, ", ".join(SUPPORTED_API_VERSIONS))
        )

    name = _check_str(data, "name", errors)
    if name is not None and not _NAME_RE.match(name):
        errors.append("name must match %s (got %r)" % (_NAME_RE.pattern, name))

    version = _check_str(data, "version", errors)
    if version is not None and not _VERSION_RE.match(version):
        errors.append("version must be semver 'MAJOR.MINOR.PATCH' (got %r)" % version)

    targets = _check_list(data, "targets", errors)
    target_list = ()
    if targets is not None:
        seen = set()
        ok = True
        for t in targets:
            if not isinstance(t, str) or not _TARGET_RE.match(t):
                errors.append("targets: invalid harness name %r" % (t,))
                ok = False
            elif t in seen:
                errors.append("targets: duplicate harness name %r" % t)
            else:
                seen.add(t)
        if ok and not targets:
            errors.append("targets must not be empty")
        if ok:
            target_list = tuple(targets)

    license_ = _check_str(data, "license", errors)
    if license_ is not None and not license_.strip():
        errors.append("license must be a non-empty SPDX identifier")

    policies = _validate_policies(data.get("policies"), pack_dir, errors)
    fragments = _validate_fragments(
        data.get("prompt_fragments"), pack_dir, target_list, errors
    )
    tool_policy = _validate_tool_policy(data.get("tool_policy"), errors)
    provenance = _validate_provenance(data.get("provenance"), errors)
    review = _validate_review(data.get("review"), errors)

    for sub in ("prompts", "policies", "tests"):
        if not (pack_dir / sub).is_dir():
            errors.append("missing required directory: %s/" % sub)
    tests_dir = pack_dir / "tests"
    if tests_dir.is_dir() and not any(tests_dir.iterdir()):
        errors.append("tests/ must contain at least one case file")

    if errors:
        return None, errors
    pack = Pack(
        pack_dir=pack_dir,
        api_version=api_version,
        name=name,
        version=version,
        targets=target_list,
        policies=tuple(policies),
        prompt_fragments=tuple(fragments),
        tool_policy=tool_policy,
        provenance=provenance,
        license=license_,
        review=review,
    )
    return pack, []


def _check_str(data, key, errors):
    v = data.get(key)
    if v is not None and not isinstance(v, str):
        errors.append("%s must be a string" % key)
        return None
    return v


def _check_list(data, key, errors):
    v = data.get(key)
    if v is not None and not isinstance(v, list):
        errors.append("%s must be a list" % key)
        return None
    return v


def _check_mapping(data, key, errors):
    v = data.get(key)
    if v is not None and not isinstance(v, dict):
        errors.append("%s must be a mapping" % key)
        return None
    return v


def _safe_rel(pack_dir, what, rel, errors, required_parent=None):
    """相对路径安全解析：拒绝绝对路径/盘符/``..`` 逃逸；校验顶层目录。"""
    posix = rel.replace("\\", "/")
    p = PurePosixPath(posix)
    if p.is_absolute() or ":" in posix.split("/")[0] or ".." in p.parts:
        errors.append("%s path escapes pack dir: %r" % (what, rel))
        return None
    if required_parent is not None and (not p.parts or p.parts[0] != required_parent):
        errors.append("%s must live under %s/ (got %r)" % (what, required_parent, rel))
        return None
    return pack_dir.joinpath(*p.parts)


def _validate_policies(raw, pack_dir, errors):
    if raw is None:
        return []
    if not isinstance(raw, list):
        errors.append("policies must be a list")
        return []
    seen = set()
    out = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append("policies[%d] must be a mapping" % idx)
            continue
        for k in sorted(set(item) - POLICY_KEYS):
            errors.append("policies[%d]: unexpected field %r" % (idx, k))
        for k in sorted(POLICY_REQUIRED - set(item)):
            errors.append("policies[%d]: missing field %r" % (idx, k))
        pid = item.get("id")
        path = item.get("path")
        if isinstance(pid, str) and _ID_RE.match(pid):
            if pid in seen:
                errors.append("policies[%d]: duplicate id %r" % (idx, pid))
            seen.add(pid)
        elif isinstance(pid, str):
            errors.append("policies[%d]: invalid id %r" % (idx, pid))
        if isinstance(path, str):
            resolved = _safe_rel(pack_dir, "policies[%d]" % idx, path, errors, "policies")
            if resolved is not None and not resolved.is_file():
                errors.append("policies[%d]: file not found: %s" % (idx, path))
        out.append(PolicyRef(
            id=pid if isinstance(pid, str) else "",
            path=path if isinstance(path, str) else "",
            description=item.get("description") if isinstance(item.get("description"), str) else "",
        ))
    return out


def _validate_fragments(raw, pack_dir, target_list, errors):
    if raw is None:
        return []
    if not isinstance(raw, list):
        errors.append("prompt_fragments must be a list")
        return []
    if not raw:
        errors.append("prompt_fragments must not be empty")
    seen = set()
    out = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append("prompt_fragments[%d] must be a mapping" % idx)
            continue
        for k in sorted(set(item) - FRAGMENT_KEYS):
            errors.append("prompt_fragments[%d]: unexpected field %r" % (idx, k))
        for k in sorted(FRAGMENT_REQUIRED - set(item)):
            errors.append("prompt_fragments[%d]: missing field %r" % (idx, k))
        fid = item.get("id")
        if isinstance(fid, str) and _ID_RE.match(fid):
            if fid in seen:
                errors.append("prompt_fragments[%d]: duplicate id %r" % (idx, fid))
            seen.add(fid)
        elif isinstance(fid, str):
            errors.append("prompt_fragments[%d]: invalid id %r" % (idx, fid))

        slot = item.get("slot", "system")
        if slot is not None and slot not in SLOTS:
            errors.append("prompt_fragments[%d]: slot must be one of %s (got %r)"
                          % (idx, "|".join(SLOTS), slot))
            slot = None
        if slot is None:
            slot = "system"

        ftargets = item.get("targets")
        if ftargets is None:
            resolved_targets = tuple(target_list)
        elif isinstance(ftargets, list) and all(isinstance(t, str) for t in ftargets):
            unknown = [t for t in ftargets if t not in target_list]
            if unknown:
                errors.append(
                    "prompt_fragments[%d]: targets %s not declared in pack targets"
                    % (idx, ", ".join(sorted(unknown)))
                )
            resolved_targets = tuple(ftargets)
        else:
            errors.append("prompt_fragments[%d]: targets must be a list of strings" % idx)
            resolved_targets = tuple(target_list)

        placeholders = item.get("placeholders", [])
        declared = ()
        if placeholders is not None:
            if not isinstance(placeholders, list) or not all(
                isinstance(p, str) for p in placeholders
            ):
                errors.append("prompt_fragments[%d]: placeholders must be a list of strings" % idx)
            else:
                for p in placeholders:
                    if not _PARAM_RE.match(p):
                        errors.append(
                            "prompt_fragments[%d]: invalid placeholder name %r" % (idx, p)
                        )
                declared = tuple(placeholders)

        content = ""
        path = item.get("path")
        if isinstance(path, str):
            resolved = _safe_rel(
                pack_dir, "prompt_fragments[%d]" % idx, path, errors, "prompts"
            )
            if resolved is not None:
                if not resolved.is_file():
                    errors.append("prompt_fragments[%d]: file not found: %s" % (idx, path))
                else:
                    try:
                        content = resolved.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError) as exc:
                        errors.append("prompt_fragments[%d]: unreadable: %s" % (idx, exc))
                    else:
                        _check_placeholders(idx, content, declared, errors)
        out.append(PromptFragment(
            id=fid if isinstance(fid, str) else "",
            path=path if isinstance(path, str) else "",
            slot=slot,
            targets=resolved_targets,
            placeholders=declared,
            content=content,
        ))
    return out


def _check_placeholders(idx, content, declared, errors):
    raw_tokens = {t.strip() for t in _RAW_PLACEHOLDER_RE.findall(content)}
    used = {t for t in raw_tokens if _PARAM_RE.match(t)}
    malformed = raw_tokens - used
    for tok in sorted(malformed):
        errors.append(
            "prompt_fragments[%d]: malformed placeholder {{%s}} "
            "(expected lowercase snake_case)" % (idx, tok)
        )
    declared_set = set(declared)
    for name in sorted(used - declared_set):
        errors.append(
            "prompt_fragments[%d]: placeholder {{%s}} used in file but not declared "
            "in placeholders" % (idx, name)
        )
    for name in sorted(declared_set - used):
        errors.append(
            "prompt_fragments[%d]: placeholder %r declared but never used in file"
            % (idx, name)
        )


def _validate_tool_policy(raw, errors):
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        errors.append("tool_policy must be a mapping")
        return {}
    for k in sorted(set(raw) - TOOL_POLICY_KEYS):
        errors.append("tool_policy: unexpected field %r" % k)
    for k in sorted(TOOL_POLICY_REQUIRED - set(raw)):
        errors.append("tool_policy: missing field %r" % k)
    mode = raw.get("mode")
    if mode is not None and mode not in TOOL_MODES:
        errors.append("tool_policy.mode must be one of %s (got %r)"
                      % ("|".join(TOOL_MODES), mode))
    tools = raw.get("tools")
    if tools is not None:
        if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
            errors.append("tool_policy.tools must be a list of strings")
        elif not tools:
            errors.append("tool_policy.tools must not be empty")
    notes = raw.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append("tool_policy.notes must be a string")
    return dict(raw)


def _validate_provenance(raw, errors):
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        errors.append("provenance must be a mapping")
        return {}
    for k in sorted(set(raw) - PROVENANCE_KEYS):
        errors.append("provenance: unexpected field %r" % k)
    for k in sorted(PROVENANCE_REQUIRED - set(raw)):
        errors.append("provenance: missing field %r" % k)
    for key in ("source", "method"):
        v = raw.get(key)
        if isinstance(v, str) and not v.strip():
            errors.append("provenance.%s must be non-empty" % key)
    synthetic = raw.get("synthetic")
    if synthetic is not None and not isinstance(synthetic, bool):
        errors.append("provenance.synthetic must be a boolean")
    return dict(raw)


def _validate_review(raw, errors):
    """生长必过门禁：review 段缺失 / gate_ref 或 evidence_ref 缺失 → invalid。"""
    if raw is None:
        return Review(gate_ref="", evidence_ref="")
    if not isinstance(raw, dict):
        errors.append("review must be a mapping")
        return Review(gate_ref="", evidence_ref="")
    for k in sorted(set(raw) - REVIEW_KEYS):
        errors.append("review: unexpected field %r" % k)
    for k in sorted(REVIEW_REQUIRED - set(raw)):
        errors.append("review: missing field %r" % k)
    gate_ref = raw.get("gate_ref")
    if isinstance(gate_ref, str) and gate_ref and not _GATE_REF_RE.match(gate_ref):
        errors.append(
            "review.gate_ref must be a GuardrailRun admission record URI "
            "starting with 'guardrail://' (got %r)" % gate_ref
        )
    evidence_ref = raw.get("evidence_ref")
    if isinstance(evidence_ref, str) and evidence_ref and not _URI_RE.match(evidence_ref):
        errors.append(
            "review.evidence_ref must be a URI (e.g. cos://bucket/ablation.json) "
            "(got %r)" % evidence_ref
        )
    approved_at = raw.get("approved_at")
    if approved_at is not None and (
        not isinstance(approved_at, str) or not _DATE_RE.match(approved_at)
    ):
        errors.append("review.approved_at must be an ISO date YYYY-MM-DD")
        approved_at = None
    return Review(
        gate_ref=gate_ref if isinstance(gate_ref, str) else "",
        evidence_ref=evidence_ref if isinstance(evidence_ref, str) else "",
        approved_at=approved_at or "",
    )


def load_pack(pack_dir):
    """加载并严格校验一个 pack。非法抛 :class:`ManifestError`（含全部错误）。"""
    pack, errors = validate_pack_dir(pack_dir)
    if errors:
        raise ManifestError(errors)
    return pack
