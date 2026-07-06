"""Shared agent scaffolding for the Cop and Thief reasoning layer.

An agent builds a structured INPUT (role, partial observation, last opponent
message, available tools, objective, joker availability), asks its provider for
a decision, and returns a structured OUTPUT. The deterministic provider returns
the placeholder-policy candidate directly; the Ollama provider authors the
message/tool choice and validates it (with a safe fallback for bad JSON).
"""

from __future__ import annotations

from typing import Optional

from src.agents.prompts import build_prompt
from src.agents.provider import make_provider, parse_decision
from src.policies.common import legal_targets


class BaseAgent:
    role: str = ""
    objective_text: str = ""

    def __init__(self, config: dict):
        self.config = config
        self.provider = make_provider(config)

    # --- subclasses implement these two ---
    def available_tools(self, extra: dict) -> list:
        raise NotImplementedError

    def candidate(self, obs: dict, extra: dict) -> dict:
        """Deterministic decision (chosen_tool, tool_input, message, reasoning)."""
        raise NotImplementedError

    # --- shared machinery ---
    def build_context(self, obs: dict, opp_message: Optional[str],
                      extra: dict) -> dict:
        return {
            "role": self.role,
            "observation": obs,
            "last_opponent_message": opp_message,
            "available_tools": self.available_tools(extra),
            "legal_targets": [list(t) for t in legal_targets(obs)],
            "objective": self.objective_text,
            "joker": extra.get("joker", {"available": False}),
        }

    def decide(self, obs: dict, opp_message: Optional[str] = None,
               extra: Optional[dict] = None) -> dict:
        extra = extra or {}
        candidate = self.candidate(obs, extra)
        if self.provider.name == "deterministic":
            candidate["provider_used"] = "deterministic"
            return candidate
        ctx = self.build_context(obs, opp_message, extra)
        system, user = build_prompt(self.role, ctx)
        raw = self.provider.complete(system, user)  # raises OllamaUnavailable
        return parse_decision(raw, ctx, candidate)

    @staticmethod
    def log_record(role: str, subgame: int, move_index: int,
                   decision: dict) -> dict:
        """Build the ``agent_decision`` JSONL record for the game trace."""
        return {
            "type": "agent_decision",
            "subgame": subgame,
            "move_index": move_index,
            "agent": role,
            "provider_used": decision["provider_used"],
            "natural_language_message": decision["natural_language_message"],
            "reasoning_summary": decision["reasoning_summary"],
            "chosen_tool": decision["chosen_tool"],
            "tool_input": decision["tool_input"],
        }
