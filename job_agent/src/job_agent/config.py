from __future__ import annotations

import json
from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text())


def load_profile(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())
