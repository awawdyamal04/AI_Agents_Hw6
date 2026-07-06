"""CLI entry point — Phase 2 local deterministic simulation.

Runs a full game (6 sub-games) of the Cop-vs-Thief pursuit using
deterministic placeholder policies, writes the per-move JSONL trace and the
final JSON report, and prints a summary.

Run with:
    python -m src.main

Phase 2 limits: no real MCP servers, no LLM calls, no GUI, no Gmail. All
parameters come from config.json.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.config_loader import load_config
from src.engine.game_loop import run_series
from src.reporting.report_builder import build_report, write_report
from src.util.logging_util import JsonlLogger

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"


def _resolve(root: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else root / p


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="src.main",
        description="MCP Chase: Joker Protocol — Phase 2 local simulation.",
    )
    parser.add_argument("--config", type=Path, default=CONFIG_PATH,
                        help="Path to config.json (default: project root).")
    args = parser.parse_args()

    config = load_config(args.config)
    rep = config.get("reporting", {})
    log_path = _resolve(ROOT, rep.get("game_log_path",
                                      "results/logs/game_log.jsonl"))
    report_path = _resolve(ROOT, rep.get("final_report_path",
                                         "results/reports/final_report.json"))

    logger = JsonlLogger(log_path)
    try:
        results, totals = run_series(config, logger)
    finally:
        logger.close()

    report = build_report(config, results, totals)
    write_report(report, report_path)
    _print_summary(config, results, totals, log_path, report_path)


def _print_summary(config, results, totals, log_path, report_path) -> None:
    print(f"[{config.get('project_name')}] Phase 2 local simulation complete.")
    grid = config["grid_size"]
    print(f"Grid {grid['rows']}x{grid['cols']}, {len(results)} sub-games, "
          f"joker_enabled={config.get('joker_protocol', {}).get('enabled')}")
    for r in results:
        print(f"  sub-game {r['subgame']}: winner={r['winner']:<5} "
              f"moves={r['moves_played']:>2}  "
              f"cop+{r['cop_score']:<2} thief+{r['thief_score']:<2} "
              f"barriers_used={r['barriers_used']}")
    print(f"Totals: cop={totals.cop}  thief={totals.thief}")
    print(f"Log:    {log_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
