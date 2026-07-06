"""Phase 1 smoke tests: verify skeleton + config are in place.

These do NOT test game logic (none exists yet). They only assert the
project structure and configuration required by Phase 1.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_expected_directories_exist():
    for rel in ("src", "results/logs", "results/reports", "results/plots"):
        assert (ROOT / rel).is_dir(), f"missing directory: {rel}"


def test_config_has_required_keys():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    assert config["project_name"] == "MCP Chase: Joker Protocol"
    assert config["grid_size"] == {"rows": 5, "cols": 5}
    assert config["max_moves_per_subgame"] == 25
    assert config["num_subgames"] == 6
    assert config["max_cop_barriers"] == 5
    assert config["scoring"] == {
        "cop_win": 20,
        "thief_win": 10,
        "cop_loss": 5,
        "thief_loss": 5,
    }
    assert config["joker_protocol"]["enabled"] is False
    assert config["reporting"]["send_email"] is False
    assert "cop_server" in config["mcp"] and "thief_server" in config["mcp"]
