"""Cop agent — focused detective reasoning over the placeholder pursuit policy.

The deterministic candidate comes straight from ``cop_policy`` (greedy Chebyshev
pursuit + occasional barrier), so the game stays reliable and offline. In
ollama mode the model may re-word the message and pick a legal tool; illegal or
malformed responses fall back to this candidate.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.policies import cop_policy
from src.tools import messages


class CopAgent(BaseAgent):
    role = "cop"
    objective_text = ("Capture the Thief by landing on its cell; close the "
                      "Chebyshev distance and use barriers to cut escapes.")

    def available_tools(self, extra: dict) -> list:
        tools = ["move"]
        barriers_left = extra.get("barriers_left", 0)
        if self.config.get("cop_uses_barriers", True) and barriers_left > 0:
            tools.append("place_barrier")
        return tools

    def candidate(self, obs: dict, extra: dict) -> dict:
        barriers_left = extra.get("barriers_left", 0)
        action = cop_policy.choose_action(obs, barriers_left, self.config)
        if action["type"] == "barrier":
            cell = action["cell"]
            return {
                "natural_language_message": messages.barrier_message(cell),
                "chosen_tool": "place_barrier",
                "tool_input": {"cell": cell},
                "reasoning_summary": ("Deterministic pursuit: drop a barrier to "
                                      "cut off the Thief's escape route."),
            }
        to = action["to"]
        return {
            "natural_language_message": messages.move_message("cop", to),
            "chosen_tool": "move",
            "tool_input": {"to": to},
            "reasoning_summary": ("Deterministic pursuit: step to minimize "
                                  "Chebyshev distance to the Thief."),
        }
