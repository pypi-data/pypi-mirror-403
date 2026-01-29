"""Shared config loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_config(config_name: str) -> dict[str, Any]:
    """Load a YAML config file from configs/ directory."""
    path = Path(__file__).resolve().parents[2] / "configs" / f"{config_name}.yml"
    data = yaml.safe_load(path.read_text())
    return data or {}
