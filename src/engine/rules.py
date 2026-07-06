"""Transition rules P: legal moves, capture detection, and barriers.

- Movement is 8-directional (diagonals allowed) per prd.md 7.2.
- Barriers block BOTH agents and cannot be placed on an occupied cell.
- The Cop is capped at max_cop_barriers per sub-game; the Thief cannot
  place barriers.
"""

from __future__ import annotations

from typing import List

from src.engine.board import Board, Cell


def chebyshev(a: Cell, b: Cell) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def legal_targets(board: Board, pos: Cell) -> List[Cell]:
    """Cells the agent at pos may move to (includes staying in place)."""
    return board.neighbors(pos, include_stay=True)


def apply_cop_move(board: Board, target: Cell) -> None:
    if target not in legal_targets(board, board.cop):
        raise ValueError(f"illegal cop move: {board.cop} -> {target}")
    board.cop = target


def apply_thief_move(board: Board, target: Cell) -> None:
    if target not in legal_targets(board, board.thief):
        raise ValueError(f"illegal thief move: {board.thief} -> {target}")
    board.thief = target


def can_place_barrier(board: Board, cell: Cell, barriers_left: int) -> bool:
    """A barrier is legal only on an empty, in-bounds, unoccupied cell."""
    return (
        barriers_left > 0
        and board.in_bounds(cell)
        and cell not in board.barriers
        and cell != board.cop
        and cell != board.thief
    )


def place_barrier(board: Board, cell: Cell) -> None:
    board.barriers.add(cell)


def is_capture(board: Board) -> bool:
    """Cop wins iff it shares the exact cell with the Thief."""
    return board.cop == board.thief
