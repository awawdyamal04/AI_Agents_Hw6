"""Board state for the pursuit game — the true state S of the Dec-POMDP.

State = grid dimensions + Cop cell + Thief cell + barrier cells. Movement is
8-directional (includes diagonals) per the assignment docs (prd.md 7.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set, Tuple

Cell = Tuple[int, int]


@dataclass
class Board:
    rows: int
    cols: int
    cop: Cell
    thief: Cell
    barriers: Set[Cell] = field(default_factory=set)

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_barrier(self, cell: Cell) -> bool:
        return cell in self.barriers

    def is_free(self, cell: Cell) -> bool:
        """A cell an agent may occupy: on the board and not a barrier."""
        return self.in_bounds(cell) and not self.is_barrier(cell)

    def neighbors(self, cell: Cell, include_stay: bool = True) -> List[Cell]:
        """Reachable cells (8 directions + optional stay), barriers excluded."""
        r, c = cell
        out: List[Cell] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nxt = (r + dr, c + dc)
                if dr == 0 and dc == 0:
                    if include_stay:
                        out.append(nxt)
                    continue
                if self.is_free(nxt):
                    out.append(nxt)
        return out

    def snapshot(self) -> dict:
        """JSON-serializable copy of the current true state."""
        return {
            "cop": list(self.cop),
            "thief": list(self.thief),
            "barriers": sorted(list(b) for b in self.barriers),
        }
