"""Build and write the Phase 2 final JSON report.

The report body is structured JSON only (no free text needed to parse it).
Results are taken verbatim from the engine — nothing is invented.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def build_report(config: dict, results: list, totals) -> dict:
    joker = config.get("joker_protocol", {})
    provider = config.get("agent_provider", "deterministic")
    return {
        "project_name": config.get("project_name"),
        "phase": "phase-5-agent-reasoning-layer",
        "execution": {"mode": "local",
                      "tool_layer": "local-adapter",
                      "tool_names": "mcp-shaped (cop.* / thief.*)",
                      "agent_provider": provider,
                      "ollama_model": config.get("ollama_model")
                      if provider == "ollama" else None},
        "generated_at": datetime.now().astimezone().isoformat(),
        "timezone": "Asia/Jerusalem",
        "grid_size": config["grid_size"],
        "num_subgames": config["num_subgames"],
        "max_moves_per_subgame": config["max_moves_per_subgame"],
        "max_cop_barriers": config["max_cop_barriers"],
        "diagonal_movement": config.get("diagonal_movement", True),
        "scoring_table": config["scoring"],
        "joker_enabled": bool(joker.get("enabled", False)),
        "policies": {"cop": "deterministic-greedy-pursuit",
                     "thief": "deterministic-greedy-evasion"},
        "sub_games": results,
        "totals": {"cop": totals.cop, "thief": totals.thief},
        "notes": ("Agent reasoning layer decides each turn (provider: "
                  f"{provider}); actions routed through the local MCP-shaped "
                  "tool layer (cop.*/thief.*). No GUI, no Gmail, no blocking "
                  "MCP servers in this run."),
    }


def write_report(report: dict, path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                 encoding="utf-8")
    return p
