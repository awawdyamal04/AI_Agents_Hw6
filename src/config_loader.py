"""Load and validate config.json.

All game parameters come from config.json — nothing is hard-coded in the
engine. This module loads the file and checks the keys Phase 2 relies on.
"""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_KEYS = (
    "grid_size",
    "max_moves_per_subgame",
    "num_subgames",
    "max_cop_barriers",
    "scoring",
)

REQUIRED_SCORING = ("cop_win", "thief_win", "cop_loss", "thief_loss")


def load_config(path) -> dict:
    """Read and validate config.json, returning the parsed dict."""
    with Path(path).open(encoding="utf-8") as fh:
        config = json.load(fh)
    validate(config)
    return config


def validate(config: dict) -> bool:
    """Raise ValueError if a required parameter is missing or invalid."""
    for key in REQUIRED_KEYS:
        if key not in config:
            raise ValueError(f"config missing required key: {key}")

    grid = config["grid_size"]
    if grid.get("rows", 0) < 1 or grid.get("cols", 0) < 1:
        raise ValueError("grid_size.rows and grid_size.cols must be >= 1")

    if config["max_moves_per_subgame"] < 1:
        raise ValueError("max_moves_per_subgame must be >= 1")
    if config["num_subgames"] < 1:
        raise ValueError("num_subgames must be >= 1")
    if config["max_cop_barriers"] < 0:
        raise ValueError("max_cop_barriers must be >= 0")

    for key in REQUIRED_SCORING:
        if key not in config["scoring"]:
            raise ValueError(f"scoring missing required key: {key}")
    return True
