"""End-to-end game-loop tests using deterministic placeholder policies.

Both win conditions are exercised through the REAL loop:
- Cop win: the baseline 5x5 config (greedy pursuit corners the evader).
- Thief win: a one-round horizon so the Thief survives on time.
"""

from __future__ import annotations

import copy

from src.engine.game_loop import run_series

BASE = {
    "grid_size": {"rows": 5, "cols": 5},
    "max_moves_per_subgame": 25,
    "num_subgames": 6,
    "max_cop_barriers": 5,
    "cop_uses_barriers": True,
    "barrier_interval": 4,
    "random_seed": 42,
    "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    "joker_protocol": {"enabled": False, "max_cards": 1},
}


class _MemLogger:
    def __init__(self):
        self.records = []

    def log(self, record):
        self.records.append(record)


def test_series_runs_all_subgames_and_scores_consistently():
    results, totals = run_series(copy.deepcopy(BASE), _MemLogger())
    assert len(results) == BASE["num_subgames"]
    cop = thief = 0
    for r in results:
        assert r["winner"] in ("cop", "thief")
        assert 1 <= r["moves_played"] <= BASE["max_moves_per_subgame"]
        cop += r["cop_score"]
        thief += r["thief_score"]
    assert (totals.cop, totals.thief) == (cop, thief)


def test_short_horizon_yields_thief_win_and_scoring():
    cfg = copy.deepcopy(BASE)
    cfg["max_moves_per_subgame"] = 1  # one round: Thief survives on time
    results, _ = run_series(cfg, _MemLogger())
    assert all(r["winner"] == "thief" for r in results)
    assert all((r["cop_score"], r["thief_score"]) == (5, 10) for r in results)


def test_barriers_respect_the_cap():
    results, _ = run_series(copy.deepcopy(BASE), _MemLogger())
    assert all(r["barriers_used"] <= BASE["max_cop_barriers"] for r in results)
