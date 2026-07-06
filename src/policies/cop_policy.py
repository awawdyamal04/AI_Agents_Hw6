"""Deterministic placeholder Cop policy: greedy pursuit + occasional barrier.

The Cop minimizes Chebyshev distance to the (observed) Thief each turn. It
occasionally spends a turn placing a barrier on a cell behind itself to
exercise the barrier mechanic and its logging. Strategy quality is not the
point of Phase 2 — running the full pipeline is.
"""

from __future__ import annotations

from typing import Optional, Tuple

from src.engine.rules import chebyshev, manhattan
from src.policies.common import legal_targets

Cell = Tuple[int, int]


def choose_action(obs: dict, barriers_left: int, config: dict) -> dict:
    """Return an action dict: {"type": "move", "to": [r, c]} or
    {"type": "barrier", "cell": [r, c]}."""
    self_pos = tuple(obs["self"])
    opp = tuple(obs["opponent"])
    targets = legal_targets(obs)

    barrier_cell = _maybe_barrier(obs, self_pos, opp, barriers_left, config)
    if barrier_cell is not None:
        return {"type": "barrier", "cell": [barrier_cell[0], barrier_cell[1]]}

    best = min(targets, key=lambda t: (chebyshev(t, opp), manhattan(t, opp), t))
    return {"type": "move", "to": [best[0], best[1]]}


def _maybe_barrier(obs, self_pos, opp, barriers_left, config) -> Optional[Cell]:
    """Decide whether to drop a barrier this turn (deterministic)."""
    if not config.get("cop_uses_barriers", True) or barriers_left <= 0:
        return None
    interval = config.get("barrier_interval", 4)
    # Only when the Thief is far (>=3) so we do not sacrifice the chase, and
    # only on every `interval`-th move.
    if chebyshev(self_pos, opp) < 3:
        return None
    if interval <= 0 or obs["move_index"] % interval != interval - 1:
        return None

    candidates = [
        t for t in legal_targets(obs) if t != self_pos and t != opp
    ]
    if not candidates:
        return None
    # Place it on the reachable cell farthest from the Thief (behind us).
    return max(candidates, key=lambda t: (chebyshev(t, opp), manhattan(t, opp), t))
