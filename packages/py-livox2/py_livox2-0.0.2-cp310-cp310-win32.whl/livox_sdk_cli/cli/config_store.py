"""Helpers for persisting Livox startup configuration inside the package."""

from __future__ import annotations

from dataclasses import asdict
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml

from ..cfg import LivoxNetworkConfig

CFG_DIR_NAME = "cfg"
CFG_FILE_NAME = "livox_start.yaml"


def _package_root() -> Path:
    return Path(resources.files("livox_sdk_cli"))


def _cfg_dir() -> Path:
    path = _package_root() / CFG_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def cfg_path() -> Path:
    return _cfg_dir() / CFG_FILE_NAME


def default_cfg_dict() -> Dict[str, Any]:
    return asdict(LivoxNetworkConfig())


def ensure_cfg_file() -> Path:
    path = cfg_path()
    if not path.exists():
        save_cfg_dict(default_cfg_dict())
    return path


def load_cfg_dict() -> Dict[str, Any]:
    path = ensure_cfg_file()
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    merged = default_cfg_dict()
    merged.update(data)
    return merged


def save_cfg_dict(payload: Mapping[str, Any]) -> None:
    cfg = default_cfg_dict()
    cfg.update(payload)
    path = cfg_path()
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(cfg, fh, sort_keys=False)


def normalize_cfg_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    data = dict(payload)
    if "pub_frequency_hz" in data:
        data.setdefault("pub_rate_hz", data["pub_frequency_hz"])
        data.pop("pub_frequency_hz", None)
    data.pop("enable_iceoryx", None)
    return data


def load_cfg() -> LivoxNetworkConfig:
    raw = load_cfg_dict()
    data = normalize_cfg_payload(raw)
    return LivoxNetworkConfig(**data)


