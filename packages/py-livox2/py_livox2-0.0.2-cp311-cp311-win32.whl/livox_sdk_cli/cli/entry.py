"""CLI entry point that mirrors the historical ``start.py`` sample."""

from __future__ import annotations

import argparse
from typing import Optional

from .config_store import load_cfg
from .livox_runner import LivoxRunner


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Livox SDK2 Python quick-start CLI.")
    parser.add_argument(
        "--pub-rate",
        type=float,
        help="Override the YAML-defined publish rate (Hz) for this session.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    net_cfg = load_cfg()
    if args.pub_rate:
        net_cfg.pub_rate_hz = args.pub_rate
    runner = LivoxRunner(net_cfg=net_cfg)
    runner.run()


if __name__ == "__main__":
    main()

