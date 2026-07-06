"""Scoring tests: per-sub-game table and accumulated totals."""

from __future__ import annotations

from src.engine.scoring import Totals, score_subgame

SCORING = {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}


def test_cop_win_scores():
    assert score_subgame("cop", SCORING) == (20, 5)


def test_thief_win_scores():
    assert score_subgame("thief", SCORING) == (5, 10)


def test_totals_accumulate():
    totals = Totals()
    for _ in range(3):
        totals.add(*score_subgame("cop", SCORING))
    for _ in range(3):
        totals.add(*score_subgame("thief", SCORING))
    # 3 cop wins + 3 thief wins from one side's perspective.
    assert totals.cop == 3 * 20 + 3 * 5
    assert totals.thief == 3 * 5 + 3 * 10


def test_role_split_bounds():
    """A group playing 3 as Cop and 3 as Thief: min 30, max 90 (prd.md 7.4)."""
    best = 3 * SCORING["cop_win"] + 3 * SCORING["thief_win"]
    worst = 3 * SCORING["thief_loss"] + 3 * SCORING["cop_loss"]
    assert best == 90 and worst == 30
