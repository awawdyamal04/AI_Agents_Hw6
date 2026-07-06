"""Phase 5 tests: the agent provider parser and Ollama fallback.

Cover that the provider parser degrades safely on malformed JSON, accepts
valid model JSON, and that the Ollama provider fails clearly when the server
is unreachable. All tests run fully offline.
"""

from __future__ import annotations

import pytest

from src.agents.provider import (OllamaProvider, OllamaUnavailable,
                                 parse_decision)

DECISION_KEYS = {"natural_language_message", "chosen_tool", "tool_input",
                 "reasoning_summary", "provider_used"}

COP_OBS = {"agent": "cop", "self": (0, 0), "opponent": (2, 2), "barriers": [],
           "rows": 5, "cols": 5, "moves_left": 25, "move_index": 0,
           "joker_injected": False}


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
