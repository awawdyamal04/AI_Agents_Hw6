"""Engine rule tests: movement (incl. diagonals), capture, barriers."""

from __future__ import annotations

from src.engine.board import Board
from src.engine import rules


def test_diagonal_moves_are_legal():
    board = Board(5, 5, cop=(2, 2), thief=(0, 0))
    targets = rules.legal_targets(board, (2, 2))
    assert (1, 1) in targets and (3, 3) in targets  # diagonals
    assert (2, 2) in targets                          # staying
    assert len(targets) == 9                          # 8 neighbors + stay


def test_moves_off_board_and_into_barriers_excluded():
    board = Board(5, 5, cop=(0, 0), thief=(4, 4), barriers={(0, 1)})
    targets = rules.legal_targets(board, (0, 0))
    assert (-1, 0) not in targets and (0, -1) not in targets
    assert (0, 1) not in targets                       # barrier blocks
    assert (1, 1) in targets and (1, 0) in targets


def test_capture_detection():
    board = Board(5, 5, cop=(1, 1), thief=(1, 2))
    assert not rules.is_capture(board)
    rules.apply_cop_move(board, (1, 2))
    assert rules.is_capture(board)


def test_barrier_cap_and_occupied_cell_rules():
    board = Board(5, 5, cop=(2, 2), thief=(4, 4))
    assert rules.can_place_barrier(board, (2, 3), barriers_left=1)
    assert not rules.can_place_barrier(board, (2, 3), barriers_left=0)  # cap
    assert not rules.can_place_barrier(board, (2, 2), barriers_left=1)  # on cop
    assert not rules.can_place_barrier(board, (4, 4), barriers_left=1)  # on thief


def test_barrier_blocks_both_agents():
    board = Board(5, 5, cop=(2, 2), thief=(2, 4), barriers={(2, 3)})
    assert (2, 3) not in rules.legal_targets(board, (2, 2))   # cop blocked
    assert (2, 3) not in rules.legal_targets(board, (2, 4))   # thief blocked


def test_distance_helpers():
    assert rules.chebyshev((0, 0), (2, 3)) == 3
    assert rules.manhattan((0, 0), (2, 3)) == 5
