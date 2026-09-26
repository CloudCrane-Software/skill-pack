# coding: utf-8
"""CLI 集成测试：``python -m skillpack.validate`` 的退出码契约（0=合法 / 2=非法）."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_cli(*args):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "skillpack.validate", *args],
        capture_output=True, text=True, env=env, cwd=str(ROOT),
    )


def test_cli_valid_example_exit_0(hello_policy_dir):
    r = run_cli(str(hello_policy_dir))
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("OK")
    assert "pack=hello-policy@0.1.0" in r.stdout


def test_cli_valid_example_with_target_exit_0(dev_guard_sop_dir):
    r = run_cli(str(dev_guard_sop_dir), "--target", "jiuwen-code")
    assert r.returncode == 0, r.stdout + r.stderr


def test_cli_target_not_declared_exit_2(hello_policy_dir):
    r = run_cli(str(hello_policy_dir), "--target", "unknown-harness")
    assert r.returncode == 2
    assert "INVALID" in r.stdout


def test_cli_invalid_pack_exit_2(tmp_path):
    d = tmp_path / "broken"
    d.mkdir()
    (d / "pack.yaml").write_text("name: broken\n", encoding="utf-8")
    r = run_cli(str(d))
    assert r.returncode == 2
    assert r.stdout.startswith("INVALID")
    assert any("missing required top-level field" in line for line in r.stdout.splitlines())


def test_cli_missing_dir_exit_2(tmp_path):
    r = run_cli(str(tmp_path / "nope"))
    assert r.returncode == 2
    assert "not found" in r.stdout
