# coding: utf-8
"""pytest 共享夹具：把 src/ 加入 sys.path，并提供示例 pack 路径."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

EXAMPLES = ROOT / "packs" / "examples"


@pytest.fixture(scope="session")
def examples_dir():
    return EXAMPLES


@pytest.fixture(scope="session")
def hello_policy_dir():
    return EXAMPLES / "hello-policy"


@pytest.fixture(scope="session")
def dev_guard_sop_dir():
    return EXAMPLES / "dev-guard-sop"
