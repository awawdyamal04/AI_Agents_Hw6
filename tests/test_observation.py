"""Observation + Joker hook tests.

Core invariant: the Joker perturbs only the observation Omega_i, never the
true state S, transitions, or scoring.
"""

from __future__ import annotations

import random

from src.engine.board import Board
from src.engine.observation import build_observation
from src.joker.joker import Joker


def _cfg(enabled):
    return {"joker_protocol": {"enabled": enabled, "max_cards": 1}}


def test_observation_is_partial_and_true():
    board = Board(5, 5, cop=(0, 0), thief=(4, 4))
    obs = build_observation(board, "cop", moves_left=25, move_index=0)
    assert obs["self"] == (0, 0)
    assert obs["opponent"] == (4, 4)     # true opponent when no injection
    assert obs["joker_injected"] is False


def test_disabled_joker_never_grants_or_injects():
    board = Board(5, 5, cop=(0, 0), thief=(4, 4))
    joker = Joker(_cfg(False), random.Random(0))
    joker.grant("cop")
    assert joker.cards == {"cop": 0, "thief": 0}
    assert joker.maybe_inject(board, "cop", move_index=0) is None


def test_enabled_joker_injects_false_signal_without_mutating_state():
    board = Board(5, 5, cop=(0, 0), thief=(4, 4))
    before = board.snapshot()
    joker = Joker(_cfg(True), random.Random(0))
    joker.grant("cop")                      # cop earned a card
    false_cell = joker.maybe_inject(board, "cop", move_index=0)
    assert false_cell is not None
    assert tuple(false_cell) != board.cop   # plausible-but-false cop position
    assert board.snapshot() == before       # true state S untouched
    assert joker.cards["cop"] == 0          # card consumed

    # The false signal reaches the OPPONENT's observation only.
    obs = build_observation(board, "thief", 25, 0, injected_opponent=false_cell)
    assert obs["opponent"] == tuple(false_cell)
    assert obs["joker_injected"] is True


def test_joker_only_plays_on_first_turn():
    board = Board(5, 5, cop=(0, 0), thief=(4, 4))
    joker = Joker(_cfg(True), random.Random(0))
    joker.grant("thief")
    assert joker.maybe_inject(board, "thief", move_index=3) is None  # not turn 0
    assert joker.cards["thief"] == 1                                 # unused
