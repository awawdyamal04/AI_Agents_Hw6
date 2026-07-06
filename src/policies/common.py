"""Shared helpers for the deterministic placeholder policies.

Policies see ONLY the observation dict (partial view), never the Board.
"""

from __future__ import annotations

from typing import List, Tuple

Cell = Tuple[int, int]


def legal_targets(obs: dict) -> List[Cell]:
    """8-directional moves + stay, from the observation alone.

    Barriers and off-board cells are excluded; staying in place is always
    allowed (the agent's own cell is never a barrier).
    """
    rows, cols = obs["rows"], obs["cols"]
    barriers = {tuple(b) for b in obs["barriers"]}
    r, c = obs["self"]
    out: List[Cell] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            nxt = (r + dr, c + dc)
            if not (0 <= nxt[0] < rows and 0 <= nxt[1] < cols):
                continue
            if nxt != (r, c) and nxt in barriers:
                continue
            out.append(nxt)
    return out
