"""Deterministic placeholder Thief policy: wall-aware evasion.

A naive "maximize distance from the Cop" evader flees straight into a corner
and gets trapped on a bounded grid. This placeholder instead keeps a safe
gap from the Cop while staying central (and therefore mobile), which lets it
survive when it has room. It cannot place barriers. Deterministic given the
observation.
"""

from __future__ import annotations

from src.engine.rules import chebyshev
from src.policies.common import legal_targets


def choose_action(obs: dict, config: dict) -> dict:
    """Return a move action dict: {"type": "move", "to": [r, c]}.

    Staying in place is expressed as a move to the current cell.

    Because the Cop moves second and closes one cell per round, the Thief
    must maximize the gap every round to preserve it; among equally distant
    moves it stays central so it keeps room to keep running instead of being
    herded into a corner.
    """
    opp = tuple(obs["opponent"])
    rows, cols = obs["rows"], obs["cols"]
    center = ((rows - 1) / 2.0, (cols - 1) / 2.0)
    targets = legal_targets(obs)

    def key(t):
        dist = chebyshev(t, opp)
        to_center = abs(t[0] - center[0]) + abs(t[1] - center[1])
        # Prefer: farther from the Cop > more central (more room) > stable tie.
        return (-dist, to_center, t)

    best = min(targets, key=key)
    return {"type": "move", "to": [best[0], best[1]]}
