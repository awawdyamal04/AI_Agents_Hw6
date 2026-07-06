"""Joker Protocol data hooks (optional, disabled by default).

Rules implemented as HOOKS ONLY for Phase 2:
- The winner of a sub-game receives one Joker Card for the next sub-game.
- Playing a card injects ONE plausible-but-false observation signal into the
  opponent's partial observation for a single turn.
- It must NOT change true physical state, transition rules, or scoring.

When disabled (config default), no card is ever granted or played, so the
baseline EX06 rules are followed exactly.
"""

from __future__ import annotations

import random
from typing import Dict, Optional, Tuple

from src.engine.board import Board, Cell


class Joker:
    def __init__(self, config: dict, rng: random.Random):
        jp = config.get("joker_protocol", {})
        self.enabled: bool = bool(jp.get("enabled", False))
        self.max_cards: int = int(jp.get("max_cards", 1))
        self.rng = rng
        self.cards: Dict[str, int] = {"cop": 0, "thief": 0}

    def grant(self, winner: Optional[str]) -> None:
        """Grant the sub-game winner a card for the next sub-game."""
        if not self.enabled or winner not in ("cop", "thief"):
            return
        self.cards[winner] = min(self.max_cards, self.cards[winner] + 1)

    def maybe_inject(
        self, board: Board, holder: str, move_index: int
    ) -> Optional[Cell]:
        """If `holder` plays a card this turn, return a false position of the
        holder to inject into the OPPONENT's observation. Deterministic
        placeholder: play the card on the first turn of the sub-game.

        Returns None if disabled, no card held, or not the play turn. Never
        mutates the board (true state S is untouched).
        """
        if not self.enabled or self.cards.get(holder, 0) <= 0:
            return None
        if move_index != 0:
            return None
        self.cards[holder] -= 1
        holder_true = board.cop if holder == "cop" else board.thief
        return self._plausible_false(board, holder_true)

    def _plausible_false(self, board: Board, true_cell: Cell) -> Cell:
        """A plausible-but-false cell near the true one (never the true cell)."""
        candidates = [
            c for c in board.neighbors(true_cell, include_stay=False)
            if c != true_cell
        ]
        if not candidates:
            return true_cell
        return self.rng.choice(sorted(candidates))
