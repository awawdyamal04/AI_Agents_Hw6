"""Scoring function R and accumulated totals.

Per the assignment scoring table (config.json.scoring):
  Cop win  -> Cop cop_win (20),  Thief thief_loss (5)
  Thief win-> Cop cop_loss (5),  Thief thief_win  (10)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Totals:
    cop: int = 0
    thief: int = 0

    def add(self, cop_points: int, thief_points: int) -> None:
        self.cop += cop_points
        self.thief += thief_points


def score_subgame(winner: str, scoring: dict) -> Tuple[int, int]:
    """Return (cop_points, thief_points) for a finished sub-game."""
    if winner == "cop":
        return scoring["cop_win"], scoring["thief_loss"]
    if winner == "thief":
        return scoring["cop_loss"], scoring["thief_win"]
    raise ValueError(f"unknown winner: {winner!r}")
