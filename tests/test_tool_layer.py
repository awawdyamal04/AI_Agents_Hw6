"""Phase 4 tests: the local tool layer.

Every Cop/Thief action is routed through explicit, MCP-shaped tool calls
(``cop.*`` / ``thief.*``). These tests cover dispatcher routing, that log
entries carry the tool names + required fields, that the Joker tool perturbs
only the opponent's observation (never true state S), and that a normal run
still writes both the report and the JSONL log.
"""

from __future__ import annotations

import copy
import json
import random

import pytest

from src.engine.board import Board
from src.engine.game_loop import run_series
from src.joker.joker import Joker
from src.reporting.report_builder import build_report, write_report
from src.tools.dispatcher import ToolDispatcher
from src.tools.local_adapter import LocalToolAdapter
from src.util.logging_util import JsonlLogger

BASE = {
    "grid_size": {"rows": 5, "cols": 5},
    "max_moves_per_subgame": 25,
    "num_subgames": 6,
    "max_cop_barriers": 5,
    "cop_uses_barriers": True,
    "barrier_interval": 4,
    "random_seed": 42,
    "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    "joker_protocol": {"enabled": False, "max_cards": 1},
}


class _MemLogger:
    def __init__(self):
        self.records = []

    def log(self, record):
        self.records.append(record)


def _adapter(cfg=None):
    cfg = copy.deepcopy(BASE) if cfg is None else cfg
    board = Board(5, 5, (0, 0), (4, 4))
    joker = Joker(cfg, random.Random(1))
    return LocalToolAdapter(board, joker, cfg), joker, board


# --- dispatcher routing ---

def test_dispatcher_routes_tool_calls_to_engine():
    adapter, _joker, board = _adapter()
    disp = ToolDispatcher(adapter, _MemLogger(), 0)

    obs = disp.call("cop", "observe_board")
    assert obs["self"] == (0, 0) and obs["opponent"] == (4, 4)

    res = disp.call("cop", "move", {"to": [1, 1]})
    assert board.cop == (1, 1) and res["captured"] is False


def test_dispatcher_rejects_tool_not_on_role_surface():
    adapter, _joker, _board = _adapter()
    disp = ToolDispatcher(adapter, _MemLogger(), 0)
    with pytest.raises(KeyError):
        disp.call("cop", "use_joker_card")  # Cop has no Joker tool


# --- log entries include tool names + required fields ---

def test_log_entries_include_tool_names_and_fields():
    log = _MemLogger()
    run_series(copy.deepcopy(BASE), log)
    calls = [r for r in log.records if r["type"] == "tool_call"]
    assert calls
    names = {r["tool"] for r in calls}
    assert {"cop.observe_board", "cop.move",
            "thief.observe_board", "thief.move"}.issubset(names)
    for r in calls:
        assert {"agent", "tool", "tool_input", "tool_result"}.issubset(r)
        assert "message" in r  # present (may be None for non-message tools)
        assert r["tool"].startswith(r["agent"] + ".")


def test_send_message_carries_natural_language():
    log = _MemLogger()
    run_series(copy.deepcopy(BASE), log)
    sends = [r for r in log.records
             if r["type"] == "tool_call" and r["tool"].endswith("send_message")]
    assert sends
    for r in sends:
        assert isinstance(r["message"], str) and r["message"]
        assert r["tool_input"]["text"] == r["message"]


# --- Joker tool: observation-only, never mutates true state S ---

def test_joker_tool_perturbs_only_observation_not_true_state():
    cfg = copy.deepcopy(BASE)
    cfg["joker_protocol"]["enabled"] = True
    adapter, joker, board = _adapter(cfg)
    disp = ToolDispatcher(adapter, _MemLogger(), 0)

    joker.grant("thief")       # give the Thief a card
    adapter.move_index = 0     # play turn
    before = board.snapshot()

    res = disp.call("thief", "use_joker_card")
    assert res["played"] is True
    assert board.snapshot() == before          # true state S untouched

    cop_obs = disp.call("cop", "observe_board")
    assert cop_obs["joker_injected"] is True
    assert tuple(cop_obs["opponent"]) == tuple(res["injected_false_position"])
    assert tuple(cop_obs["opponent"]) != board.thief  # false, not the truth

    # one-shot: it does not leak into the Thief's own view
    assert disp.call("thief", "observe_board")["joker_injected"] is False


# --- normal run still writes report and logs ---

def test_normal_run_writes_report_and_logs(tmp_path):
    log_path = tmp_path / "game_log.jsonl"
    logger = JsonlLogger(log_path)
    try:
        results, totals = run_series(copy.deepcopy(BASE), logger)
    finally:
        logger.close()

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert lines
    assert json.loads(lines[0])["type"] == "subgame_start"
    assert any(json.loads(ln).get("type") == "tool_call" for ln in lines)

    report_path = tmp_path / "final_report.json"
    write_report(build_report(copy.deepcopy(BASE), results, totals), report_path)
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["totals"] == {"cop": totals.cop, "thief": totals.thief}
