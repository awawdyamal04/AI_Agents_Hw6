"""Phase 5 tests: the agent reasoning layer.

Cover the deterministic decision structure, Cop/Thief output shapes, that a
normal run logs ``agent_decision`` records, that deterministic mode needs no
Ollama server, and that the provider parser degrades safely on malformed JSON.
All tests run fully offline (deterministic provider is the default).
"""

from __future__ import annotations

import copy

import pytest

from src.agents.cop_agent import CopAgent
from src.agents.provider import (DeterministicProvider, OllamaProvider,
                                 OllamaUnavailable, make_provider,
                                 parse_decision)
from src.agents.thief_agent import ThiefAgent
from src.engine.game_loop import run_series

BASE = {
    "grid_size": {"rows": 5, "cols": 5},
    "max_moves_per_subgame": 25,
    "num_subgames": 6,
    "max_cop_barriers": 5,
    "cop_uses_barriers": True,
    "barrier_interval": 4,
    "random_seed": 42,
    "agent_provider": "deterministic",
    "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    "joker_protocol": {"enabled": False, "max_cards": 1},
}

DECISION_KEYS = {"natural_language_message", "chosen_tool", "tool_input",
                 "reasoning_summary", "provider_used"}

COP_OBS = {"agent": "cop", "self": (0, 0), "opponent": (2, 2), "barriers": [],
           "rows": 5, "cols": 5, "moves_left": 25, "move_index": 0,
           "joker_injected": False}
THIEF_OBS = {"agent": "thief", "self": (4, 4), "opponent": (0, 0),
             "barriers": [], "rows": 5, "cols": 5, "moves_left": 25,
             "move_index": 0, "joker_injected": False}


class _MemLogger:
    def __init__(self):
        self.records = []

    def log(self, record):
        self.records.append(record)


# --- deterministic decision structure ---

def test_deterministic_provider_is_default():
    assert isinstance(make_provider(copy.deepcopy(BASE)), DeterministicProvider)


def test_deterministic_decision_has_full_structure():
    decision = CopAgent(copy.deepcopy(BASE)).decide(
        COP_OBS, None, {"barriers_left": 5})
    assert DECISION_KEYS == set(decision)
    assert decision["provider_used"] == "deterministic"
    assert isinstance(decision["natural_language_message"], str)
    assert isinstance(decision["reasoning_summary"], str)


# --- Cop / Thief output shapes ---

def test_cop_agent_output_shape():
    decision = CopAgent(copy.deepcopy(BASE)).decide(
        COP_OBS, "catch me!", {"barriers_left": 5})
    assert decision["chosen_tool"] in ("move", "place_barrier")
    key = "cell" if decision["chosen_tool"] == "place_barrier" else "to"
    assert key in decision["tool_input"]
    assert len(decision["tool_input"][key]) == 2


def test_thief_agent_output_shape():
    decision = ThiefAgent(copy.deepcopy(BASE)).decide(
        THIEF_OBS, None, {"joker": {"available": True}})
    assert decision["chosen_tool"] == "move"
    assert "to" in decision["tool_input"]
    assert len(decision["tool_input"]["to"]) == 2


# --- game log includes agent_decision records ---

def test_game_log_includes_agent_decision_records():
    log = _MemLogger()
    run_series(copy.deepcopy(BASE), log)
    decisions = [r for r in log.records if r["type"] == "agent_decision"]
    assert decisions
    agents = {r["agent"] for r in decisions}
    assert {"cop", "thief"}.issubset(agents)
    for r in decisions:
        assert r["provider_used"] == "deterministic"
        assert {"agent", "provider_used", "natural_language_message",
                "reasoning_summary", "chosen_tool", "tool_input"}.issubset(r)


# --- deterministic mode works without Ollama ---

def test_deterministic_mode_runs_without_ollama():
    # No network provider is constructed; a full series completes offline.
    results, totals = run_series(copy.deepcopy(BASE), _MemLogger())
    assert len(results) == BASE["num_subgames"]
    assert (totals.cop, totals.thief) == (120, 30)


# --- provider parser handles malformed JSON safely ---

def _ctx():
    return {"role": "cop", "observation": COP_OBS,
            "available_tools": ["move", "place_barrier"],
            "legal_targets": [[0, 0], [0, 1], [1, 0], [1, 1]],
            "objective": "capture", "joker": {"available": False}}


def _candidate():
    return {"natural_language_message": "Advancing.", "chosen_tool": "move",
            "tool_input": {"to": [1, 1]},
            "reasoning_summary": "Deterministic pursuit."}


@pytest.mark.parametrize("raw", ["", "not json at all", "{broken",
                                 '{"chosen_tool": "teleport"}',
                                 '{"chosen_tool": "move", "tool_input": '
                                 '{"to": [9, 9]}}'])
def test_parse_decision_falls_back_on_bad_json(raw):
    decision = parse_decision(raw, _ctx(), _candidate())
    assert DECISION_KEYS == set(decision)
    assert decision["provider_used"] == "ollama"
    assert decision["tool_input"] == {"to": [1, 1]}  # candidate action reused
    assert "deterministic policy" in decision["reasoning_summary"]


def test_parse_decision_accepts_valid_model_json():
    raw = ('{"natural_language_message": "Gotcha.", "chosen_tool": "move", '
           '"tool_input": {"to": [0, 1]}, "reasoning_summary": "step in"}')
    decision = parse_decision(raw, _ctx(), _candidate())
    assert decision["chosen_tool"] == "move"
    assert decision["tool_input"] == {"to": [0, 1]}
    assert decision["provider_used"] == "ollama"


# --- ollama provider fails clearly when the server is unreachable ---

def test_ollama_provider_raises_when_unavailable():
    provider = OllamaProvider("http://127.0.0.1:9", "smollm2:135m", timeout=2)
    with pytest.raises(OllamaUnavailable):
        provider.complete("sys", "user")
