"""Thief agent — playful trickster reasoning over the placeholder evasion policy.

The deterministic candidate comes from ``thief_policy`` (maximize the gap while
staying central). The Thief cannot place barriers. In ollama mode the model may
re-word the taunt and pick a legal move; illegal or malformed responses fall
back to this candidate. Joker availability is surfaced in the agent input but
the Joker play itself stays in the tool layer (``thief.use_joker_card``).
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.policies import thief_policy
from src.tools import messages


class ThiefAgent(BaseAgent):
    role = "thief"
    objective_text = ("Survive by evading the Cop for the whole sub-game; keep "
                      "a safe gap while staying central and mobile.")

    def available_tools(self, extra: dict) -> list:
        return ["move"]

    def candidate(self, obs: dict, extra: dict) -> dict:
        action = thief_policy.choose_action(obs, self.config)
        to = action["to"]
        return {
            "natural_language_message": messages.move_message("thief", to),
            "chosen_tool": "move",
            "tool_input": {"to": to},
            "reasoning_summary": ("Deterministic evasion: maximize the gap from "
                                  "the Cop while staying central and mobile."),
        }
