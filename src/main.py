"""CLI entry point (Phase 1 placeholder).

Run with:
    python -m src.main

This does NOT run the game. Phases 2+ (engine, MCP servers, agents,
reporting) are not implemented yet. For now this only confirms that the
project skeleton and configuration are in place.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load config.json if present. Returns {} if missing (Phase 1 tolerant)."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="src.main",
        description="MCP Chase: Joker Protocol — Phase 1 skeleton placeholder.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to config.json (default: project root config.json).",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    project = config.get("project_name", "MCP Chase: Joker Protocol")

    print(f"[{project}] Phase 1 skeleton is ready.")
    print("No game logic, agents, or MCP behavior implemented yet.")
    if config:
        grid = config.get("grid_size", {})
        print(
            f"Config loaded: grid "
            f"{grid.get('rows', '?')}x{grid.get('cols', '?')}, "
            f"{config.get('num_subgames', '?')} sub-games."
        )
    else:
        print(f"No config found at {args.config}.")


if __name__ == "__main__":
    main()
