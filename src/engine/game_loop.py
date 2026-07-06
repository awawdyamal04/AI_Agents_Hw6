"""Sub-game and 6-game series driver (local deterministic simulation).

Turn order per sub-game (prd.md 7.1): the Thief moves first, then the Cop,
repeating for up to max_moves rounds. The Cop wins by landing on the Thief's
cell; otherwise the Thief survives and wins. Every move (and any Joker
injection) is written to the JSONL trace.
"""

from __future__ import annotations

import random

from src.engine import observation, rules, scoring
from src.engine.board import Board
from src.joker.joker import Joker
from src.policies import cop_policy, thief_policy


def random_start(rng, rows, cols):
    """Pick two distinct valid start cells at least 2 apart."""
    if rows * cols < 2:
        raise ValueError("grid too small for two agents")
    while True:
        cop = (rng.randrange(rows), rng.randrange(cols))
        thief = (rng.randrange(rows), rng.randrange(cols))
        if rules.chebyshev(cop, thief) >= 2:
            return cop, thief


def _apply_cop(board, action, barriers_left, record):
    """Apply a cop action, returning the updated barrier count."""
    if action["type"] == "barrier":
        cell = tuple(action["cell"])
        if rules.can_place_barrier(board, cell, barriers_left):
            rules.place_barrier(board, cell)
            record["applied"] = "barrier"
            return barriers_left - 1
        record["applied"] = "barrier_rejected"
        return barriers_left
    rules.apply_cop_move(board, tuple(action["to"]))
    record["applied"] = "move"
    return barriers_left


def _log_joker(logger, subgame, move_index, holder, observer, false_cell):
    logger.log({
        "type": "joker_injection",
        "subgame": subgame,
        "move_index": move_index,
        "holder": holder,
        "observer": observer,
        "injected_false_position": list(false_cell),
    })


def run_subgame(config, rng, joker, logger, subgame_index):
    grid = config["grid_size"]
    rows, cols = grid["rows"], grid["cols"]
    board = Board(rows, cols, *random_start(rng, rows, cols))
    max_moves = config["max_moves_per_subgame"]
    barriers_left = config["max_cop_barriers"]
    logger.log({"type": "subgame_start", "subgame": subgame_index,
                "state": board.snapshot(), "max_moves": max_moves})

    winner = None
    move_index = 0
    for move_index in range(max_moves):
        moves_left = max_moves - move_index

        inj = joker.maybe_inject(board, "cop", move_index)
        if inj is not None:
            _log_joker(logger, subgame_index, move_index, "cop", "thief", inj)
        obs = observation.build_observation(
            board, "thief", moves_left, move_index, inj)
        action = thief_policy.choose_action(obs, config)
        rules.apply_thief_move(board, tuple(action["to"]))
        logger.log({"type": "move", "subgame": subgame_index,
                    "move_index": move_index, "agent": "thief",
                    "action": action, "state": board.snapshot()})
        if rules.is_capture(board):
            winner = "cop"
            break

        inj = joker.maybe_inject(board, "thief", move_index)
        if inj is not None:
            _log_joker(logger, subgame_index, move_index, "thief", "cop", inj)
        obs = observation.build_observation(
            board, "cop", moves_left, move_index, inj)
        action = cop_policy.choose_action(obs, barriers_left, config)
        record = {"type": "move", "subgame": subgame_index,
                  "move_index": move_index, "agent": "cop", "action": action}
        barriers_left = _apply_cop(board, action, barriers_left, record)
        record["state"] = board.snapshot()
        logger.log(record)
        if rules.is_capture(board):
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
        "barriers_used": config["max_cop_barriers"] - barriers_left,
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
