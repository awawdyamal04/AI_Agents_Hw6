"""Shared FastMCP loader + session state for the Phase 3 MCP servers.

Each MCP server (cop, thief) owns one `GameSession` that wraps the EXISTING
engine (Board, rules, observation, scoring, Joker) — the engine is not
rewritten. The servers expose tools only; no LLM runs here. Synchronizing one
shared board across the two servers is the orchestrator's job (Phase 4); in
Phase 3 each session wraps the engine so every tool is functional and
independently testable.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config_loader import load_config
from src.engine import observation, rules, scoring
from src.engine.board import Board
from src.engine.game_loop import random_start
from src.joker.joker import Joker

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG = ROOT / "config.json"

Cell = Tuple[int, int]


def require_fastmcp():
    """Return the FastMCP class, preferring the official ``mcp`` package.

    Falls back to the standalone ``fastmcp`` package. Raises a clear,
    actionable error naming what to install if neither is available.
    """
    try:
        from mcp.server.fastmcp import FastMCP
        return FastMCP
    except ModuleNotFoundError:
        pass
    try:
        from fastmcp import FastMCP
        return FastMCP
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "FastMCP is not installed. Install the official MCP SDK:\n"
            "    pip install mcp\n"
            "or the standalone package:\n"
            "    pip install fastmcp\n"
            "(both are declared in requirements.txt)."
        ) from exc


def load_or_default(config: Optional[dict]) -> dict:
    """Return the given config, or load ./config.json when None."""
    return config if config is not None else load_config(DEFAULT_CONFIG)


class GameSession:
    """Wraps the engine's true state S for one MCP server."""

    def __init__(self, config: dict, seed: Optional[int] = None):
        self.config = config
        grid = config["grid_size"]
        self.rows, self.cols = grid["rows"], grid["cols"]
        self.rng = random.Random(
            seed if seed is not None else config.get("random_seed", 42))
        self.board = Board(self.rows, self.cols,
                           *random_start(self.rng, self.rows, self.cols))
        self.max_moves = config["max_moves_per_subgame"]
        self.barriers_left = config["max_cop_barriers"]
        self.move_index = 0
        self.totals = scoring.Totals()
        self.winner: Optional[str] = None
        self.joker = Joker(config, self.rng)
        self.inbox: Dict[str, List[str]] = {"cop": [], "thief": []}
        self.injection: Dict[str, Cell] = {}

    # --- observation (partial view Omega_i) ---
    def observe(self, agent: str) -> dict:
        inj = self.injection.pop(agent, None)
        moves_left = self.max_moves - self.move_index
        return observation.build_observation(
            self.board, agent, moves_left, self.move_index, inj)

    # --- free natural-language messaging ---
    def send_message(self, sender: str, text: str) -> dict:
        target = "thief" if sender == "cop" else "cop"
        self.inbox[target].append(text)
        return {"delivered_to": target, "queued": len(self.inbox[target])}

    def receive_message(self, agent: str) -> dict:
        drained = list(self.inbox[agent])
        self.inbox[agent].clear()
        return {"agent": agent, "messages": drained}

    # --- transitions P ---
    def move(self, agent: str, to: Cell) -> dict:
        cell = (int(to[0]), int(to[1]))
        if agent == "cop":
            rules.apply_cop_move(self.board, cell)
        else:
            rules.apply_thief_move(self.board, cell)
            self.move_index += 1
        captured = rules.is_capture(self.board)
        if captured and self.winner is None:
            self._finish("cop")
        elif self.move_index >= self.max_moves and self.winner is None:
            self._finish("thief")
        return {"agent": agent, "position": list(cell),
                "captured": captured, "winner": self.winner}

    def place_barrier(self, cell: Cell) -> dict:
        target = (int(cell[0]), int(cell[1]))
        if not rules.can_place_barrier(self.board, target, self.barriers_left):
            return {"placed": False, "reason": "illegal or no barriers left",
                    "barriers_left": self.barriers_left}
        rules.place_barrier(self.board, target)
        self.barriers_left -= 1
        return {"placed": True, "cell": list(target),
                "barriers_left": self.barriers_left}

    def use_joker(self, holder: str) -> dict:
        """Play ``holder``'s Joker card: inject one false signal into the
        opponent's next observation. Never mutates true state S."""
        inj = self.joker.maybe_inject(self.board, holder, self.move_index)
        if inj is None:
            return {"played": False,
                    "reason": "joker disabled, no card, or not the play turn"}
        observer = "thief" if holder == "cop" else "cop"
        self.injection[observer] = tuple(inj)
        return {"played": True, "injected_false_position": list(inj)}

    def get_score(self) -> dict:
        return {"cop": self.totals.cop, "thief": self.totals.thief,
                "winner": self.winner, "move_index": self.move_index,
                "moves_left": self.max_moves - self.move_index}

    def _finish(self, winner: str) -> None:
        self.winner = winner
        cop_pts, thief_pts = scoring.score_subgame(winner, self.config["scoring"])
        self.totals.add(cop_pts, thief_pts)
        self.joker.grant(winner)
