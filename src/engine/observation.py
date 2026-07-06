"""Observation function O: builds each agent's partial view Omega_i.

The engine holds the only true state S. A policy receives ONLY this
observation, never the Board object. The Joker Protocol perturbs the
observation here (via injected_opponent) without ever touching S.
"""

from __future__ import annotations

from typing import Optional

from src.engine.board import Board, Cell


def build_observation(
    board: Board,
    agent: str,
    moves_left: int,
    move_index: int,
    injected_opponent: Optional[Cell] = None,
) -> dict:
    """Return the partial view for `agent` ("cop" or "thief").

    `opponent` is the position the agent *believes* the other agent is at.
    Normally it is the true position; if the Joker injected a false signal,
    it is a plausible-but-false cell instead.
    """
    if agent == "cop":
        self_pos = board.cop
    else:
        self_pos = board.thief

    reported_opponent = injected_opponent if injected_opponent is not None else (
        board.thief if agent == "cop" else board.cop
    )

    return {
        "agent": agent,
        "self": tuple(self_pos),
        "opponent": tuple(reported_opponent),
        "barriers": sorted(tuple(b) for b in board.barriers),
        "rows": board.rows,
        "cols": board.cols,
        "moves_left": moves_left,
        "move_index": move_index,
        "joker_injected": injected_opponent is not None,
    }
