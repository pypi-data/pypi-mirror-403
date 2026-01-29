"""Utility CLI for exporting and persisting Livox YAML configs."""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

import yaml

from ..cfg import LivoxNetworkConfig
from .config_store import load_cfg_dict, normalize_cfg_payload, save_cfg_dict

DEFAULT_FILENAME = "livox_start.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Livox YAML configuration.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="Export the current config into the working directory.")
    new_parser.add_argument(
        "--filename",
        default=DEFAULT_FILENAME,
        help=f"Output YAML filename (default: {DEFAULT_FILENAME}).",
    )
    new_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the target file if it already exists.",
    )

    set_parser = subparsers.add_parser("set", help="Persist a modified YAML back into the package store.")
    set_parser.add_argument("path", help="Path to the edited YAML file.")

    subparsers.add_parser("cat", help="Print the currently stored YAML to stdout.")

    return parser


def _write_yaml(path: Path, payload: Dict[str, Any], overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists. Pass --overwrite to replace it.")
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False)


def _read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


def handle_new(args: argparse.Namespace) -> None:
    payload = load_cfg_dict()
    target = Path.cwd() / args.filename
    _write_yaml(target, payload, overwrite=args.overwrite)
    print(f"Exported config to {target}")


def handle_set(args: argparse.Namespace) -> None:
    src = Path(args.path)
    if not src.exists():
        raise FileNotFoundError(f"{src} does not exist.")
    data = _read_yaml(src)
    cfg = LivoxNetworkConfig(**normalize_cfg_payload(data))
    save_cfg_dict(asdict(cfg))
    src.unlink()
    print("Updated package config and removed the local YAML file.")


def handle_cat(_: argparse.Namespace) -> None:
    payload = load_cfg_dict()
    print(yaml.safe_dump(payload, sort_keys=False))


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "new":
            handle_new(args)
        elif args.command == "set":
            handle_set(args)
        elif args.command == "cat":
            handle_cat(args)
    except Exception as exc:  # pragma: no cover - CLI ergonomics
        parser.error(str(exc))


if __name__ == "__main__":
    main(sys.argv[1:])


