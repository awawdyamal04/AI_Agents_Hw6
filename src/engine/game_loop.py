"""Sub-game and 6-game series driver — Phase 4 routes every action through the
local tool layer.

Turn order per sub-game (prd.md 7.1): the Thief moves first, then the Cop, for
up to max_moves rounds. The Cop wins by landing on the Thief's cell; otherwise
the Thief survives and wins. Every action is executed as an explicit,
MCP-shaped tool call (``cop.*`` / ``thief.*``) via `ToolDispatcher`, and each
call — with its tool input, tool result, and any natural-language message — is
written to the JSONL trace. True state changes still happen only in the engine
(`Board` + `rules`); the tool layer is the access path, not a second state.
"""

from __future__ import annotations

import random

from src.engine import rules, scoring
from src.engine.board import Board
from src.joker.joker import Joker
from src.policies import cop_policy, thief_policy
from src.tools import messages
from src.tools.dispatcher import ToolDispatcher
from src.tools.local_adapter import LocalToolAdapter


def random_start(rng, rows, cols):
    """Pick two distinct valid start cells at least 2 apart."""
    if rows * cols < 2:
        raise ValueError("grid too small for two agents")
    while True:
        cop = (rng.randrange(rows), rng.randrange(cols))
        thief = (rng.randrange(rows), rng.randrange(cols))
        if rules.chebyshev(cop, thief) >= 2:
            return cop, thief


def _thief_turn(disp, adapter, config) -> bool:
    """Run the Thief's turn via tool calls; return True on capture."""
    obs = disp.call("thief", "observe_board")
    if config.get("joker_protocol", {}).get("enabled"):
        # No-op unless the Thief holds a card and it is the play turn.
        disp.call("thief", "use_joker_card")
    action = thief_policy.choose_action(obs, config)
    to = action["to"]
    msg = messages.move_message("thief", to)
    disp.call("thief", "send_message", {"text": msg}, message=msg)
    return disp.call("thief", "move", {"to": to})["captured"]


def _cop_turn(disp, adapter, config) -> bool:
    """Run the Cop's turn via tool calls; return True on capture."""
    obs = disp.call("cop", "observe_board")
    action = cop_policy.choose_action(obs, adapter.barriers_left, config)
    if action["type"] == "barrier":
        cell = action["cell"]
        msg = messages.barrier_message(cell)
        disp.call("cop", "send_message", {"text": msg}, message=msg)
        disp.call("cop", "place_barrier", {"cell": cell})
        return False
    to = action["to"]
    msg = messages.move_message("cop", to)
    disp.call("cop", "send_message", {"text": msg}, message=msg)
    return disp.call("cop", "move", {"to": to})["captured"]


def run_subgame(config, rng, joker, logger, subgame_index):
    grid = config["grid_size"]
    rows, cols = grid["rows"], grid["cols"]
    board = Board(rows, cols, *random_start(rng, rows, cols))
    max_moves = config["max_moves_per_subgame"]
    adapter = LocalToolAdapter(board, joker, config)
    disp = ToolDispatcher(adapter, logger, subgame_index)
    logger.log({"type": "subgame_start", "subgame": subgame_index,
                "state": board.snapshot(), "max_moves": max_moves})

    winner = None
    move_index = 0
    for move_index in range(max_moves):
        adapter.move_index = move_index
        if _thief_turn(disp, adapter, config):
            winner = "cop"
            break
        if _cop_turn(disp, adapter, config):
            winner = "cop"
            break

    if winner is None:
        winner = "thief"
    cop_pts, thief_pts = scoring.score_subgame(winner, config["scoring"])
    joker.grant(winner)
    result = {
        "subgame": subgame_index,
        "winner": winner,
        "moves_played": move_index + 1,
        "cop_score": cop_pts,
        "thief_score": thief_pts,
        "barriers_used": config["max_cop_barriers"] - adapter.barriers_left,
        "final_state": board.snapshot(),
    }
    logger.log({"type": "subgame_result", **result})
    return result


def run_series(config, logger):
    """Run the full game (num_subgames sub-games) and accumulate totals."""
    rng = random.Random(config.get("random_seed", 42))
    joker = Joker(config, rng)
    totals = scoring.Totals()
    results = []
    for i in range(config["num_subgames"]):
        res = run_subgame(config, rng, joker, logger, i)
        totals.add(res["cop_score"], res["thief_score"])
        results.append(res)
    return results, totals
