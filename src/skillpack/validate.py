# coding: utf-8
"""CLI 入口：``python -m skillpack.validate <pack-dir> [--target NAME]``.

退出码：0 = 合法；2 = 非法（结构 / review 门禁 / 文件存在性 / 版本兼容等任一失败）。
"""
from __future__ import annotations

import argparse
import sys

from .manifest import validate_pack_dir

__all__ = ["main"]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m skillpack.validate",
        description="Validate an OKF strategy pack directory (exit 0=valid, 2=invalid).",
    )
    parser.add_argument("pack_dir", help="path to the pack directory containing pack.yaml")
    parser.add_argument(
        "--target",
        help="additionally check that this harness name is declared in pack targets",
    )
    args = parser.parse_args(argv)

    pack, errors = validate_pack_dir(args.pack_dir)
    if errors:
        print("INVALID %s" % args.pack_dir)
        for e in errors:
            print("  - %s" % e)
        return 2
    if args.target is not None and args.target not in pack.targets:
        print("INVALID %s" % args.pack_dir)
        print("  - target %r is not declared in pack targets %s"
              % (args.target, list(pack.targets)))
        return 2
    print(
        "OK %s  pack=%s@%s api=%s targets=%s fragments=%d policies=%d review.gate_ref=%s"
        % (
            args.pack_dir,
            pack.name,
            pack.version,
            pack.api_version,
            ",".join(pack.targets),
            len(pack.prompt_fragments),
            len(pack.policies),
            pack.review.gate_ref,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
