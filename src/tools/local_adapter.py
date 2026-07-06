"""Local, in-process implementation of the agent tools (Phase 4).

`LocalToolAdapter` mirrors the FastMCP servers' tool surface but calls the
EXISTING engine directly — no network, no LLM. The true state S stays in the
engine's `Board`; the adapter only reads/writes it through the same
`rules`/`observation` functions the MCP `GameSession` uses. Scoring and the
sub-game winner stay in the game loop. A Joker play never mutates true state —
it only perturbs the opponent's next observation (a false signal).

This is the *local tool adapter*: same tool names as the MCP servers, but the
calls happen in-process instead of over an MCP transport.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from src.engine import observation, rules

Cell = Tuple[int, int]


class LocalToolAdapter:
    """Backend the local dispatcher routes tool calls to (wraps one sub-game)."""

    def __init__(self, board, joker, config: dict):
        self.board = board
        self.joker = joker
        self.config = config
        self.max_moves = config["max_moves_per_subgame"]
        self.barriers_left = config["max_cop_barriers"]
        self.move_index = 0
        self.inbox: Dict[str, List[str]] = {"cop": [], "thief": []}
        self.pending_injection: Dict[str, Cell] = {}

    # --- observation (partial view Omega_i) ---
    def observe_board(self, role: str) -> dict:
        inj = self.pending_injection.pop(role, None)
        moves_left = self.max_moves - self.move_index
        return observation.build_observation(
            self.board, role, moves_left, self.move_index, inj)

    # --- free natural-language messaging ---
    def send_message(self, role: str, text: str) -> dict:
        target = "thief" if role == "cop" else "cop"
        self.inbox[target].append(text)
        return {"delivered_to": target, "queued": len(self.inbox[target])}

    def receive_message(self, role: str) -> dict:
        drained = list(self.inbox[role])
        self.inbox[role].clear()
        return {"agent": role, "messages": drained}

    # --- transitions P (true state changes stay in the engine) ---
    def move(self, role: str, to: Cell) -> dict:
        cell = (int(to[0]), int(to[1]))
        if role == "cop":
            rules.apply_cop_move(self.board, cell)
        else:
            rules.apply_thief_move(self.board, cell)
        captured = rules.is_capture(self.board)
        return {"agent": role, "position": list(cell),
                "captured": captured, "state": self.board.snapshot()}

    def place_barrier(self, cell: Cell) -> dict:
        target = (int(cell[0]), int(cell[1]))
        if not rules.can_place_barrier(self.board, target, self.barriers_left):
            return {"placed": False, "reason": "illegal or no barriers left",
                    "barriers_left": self.barriers_left}
        rules.place_barrier(self.board, target)
        self.barriers_left -= 1
        return {"placed": True, "cell": list(target),
                "barriers_left": self.barriers_left,
                "state": self.board.snapshot()}

    # --- Joker Protocol (observation-only; never mutates true state S) ---
    def use_joker_card(self, holder: str) -> dict:
        inj = self.joker.maybe_inject(self.board, holder, self.move_index)
        if inj is None:
            return {"played": False,
                    "reason": "joker disabled, no card, or not the play turn"}
        observer = "thief" if holder == "cop" else "cop"
        self.pending_injection[observer] = tuple(inj)
        return {"played": True, "injected_false_position": list(inj)}

    def get_score(self, role: str) -> dict:
        """Status only — scoring/winner live in the game loop, not here."""
        return {"role": role, "move_index": self.move_index,
                "moves_left": self.max_moves - self.move_index,
                "barriers_left": self.barriers_left}
