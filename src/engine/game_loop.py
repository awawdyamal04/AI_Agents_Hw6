"""Sub-game and 6-game series driver.

Phase 5 adds the agent reasoning layer. Turn order per sub-game (prd.md 7.1):
the Thief moves first, then the Cop, for up to max_moves rounds. The Cop wins by
landing on the Thief's cell; otherwise the Thief survives and wins.

Each turn the agent layer (`CopAgent`/`ThiefAgent`) produces a STRUCTURED
decision (natural-language message + chosen tool + tool input) via either the
deterministic provider or the real local Ollama API. The decision is logged as
an ``agent_decision`` record, then dispatched as an explicit, MCP-shaped tool
call (``cop.*`` / ``thief.*``). True state changes still happen only in the
engine (`Board` + `rules`); the tool layer is the access path, not a 2nd state.
"""

from __future__ import annotations

import random

from src.agents.cop_agent import CopAgent
from src.agents.base_agent import BaseAgent
from src.agents.thief_agent import ThiefAgent
from src.engine import rules, scoring
from src.engine.board import Board
from src.joker.joker import Joker
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


def _last_message(disp, role):
    """Drain the opponent's messages; return the most recent one (or None)."""
    msgs = disp.call(role, "receive_message")["messages"]
    return msgs[-1] if msgs else None


def _act(disp, role, agent, extra, opp_msg, logger, subgame):
    """Run one agent's turn: decide, log, message, dispatch. Return capture."""
    obs = disp.call(role, "observe_board")
    decision = agent.decide(obs, opp_msg, extra)
    logger.log(BaseAgent.log_record(role, subgame, disp.adapter.move_index,
                                    decision))
    msg = decision["natural_language_message"]
    disp.call(role, "send_message", {"text": msg}, message=msg)
    result = disp.call(role, decision["chosen_tool"], decision["tool_input"])
    return bool(result.get("captured"))


def _thief_turn(disp, adapter, config, agent, logger, subgame) -> bool:
    """Run the Thief's turn via the agent layer + tool calls."""
    opp_msg = _last_message(disp, "thief")
    joker_held = adapter.joker.cards.get("thief", 0) > 0
    if config.get("joker_protocol", {}).get("enabled"):
        disp.call("thief", "use_joker_card")  # no-op unless it is the play turn
    return _act(disp, "thief", agent, {"joker": {"available": joker_held}},
                opp_msg, logger, subgame)


def _cop_turn(disp, adapter, config, agent, logger, subgame) -> bool:
    """Run the Cop's turn via the agent layer + tool calls."""
    opp_msg = _last_message(disp, "cop")
    return _act(disp, "cop", agent, {"barriers_left": adapter.barriers_left},
                opp_msg, logger, subgame)


def run_subgame(config, rng, joker, logger, subgame_index):
    grid = config["grid_size"]
    rows, cols = grid["rows"], grid["cols"]
    board = Board(rows, cols, *random_start(rng, rows, cols))
    max_moves = config["max_moves_per_subgame"]
    adapter = LocalToolAdapter(board, joker, config)
    disp = ToolDispatcher(adapter, logger, subgame_index)
    cop_agent, thief_agent = CopAgent(config), ThiefAgent(config)
    logger.log({"type": "subgame_start", "subgame": subgame_index,
                "state": board.snapshot(), "max_moves": max_moves,
                "agent_provider": config.get("agent_provider", "deterministic")})

    winner = None
    move_index = 0
    for move_index in range(max_moves):
        adapter.move_index = move_index
        if _thief_turn(disp, adapter, config, thief_agent, logger,
                       subgame_index):
            winner = "cop"
            break
        if _cop_turn(disp, adapter, config, cop_agent, logger, subgame_index):
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
