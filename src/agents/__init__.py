"""Phase 5 agent reasoning layer.

Cop and Thief make STRUCTURED decisions through a pluggable provider:

- ``deterministic`` (default) — wraps the Phase 2 placeholder policies, so
  tests are reliable and need no external service.
- ``ollama`` — calls a real local Ollama HTTP API (default model
  ``smollm2:135m``) to author the natural-language message and choose a tool.

Every agent returns the same structured decision dict:
``natural_language_message``, ``chosen_tool``, ``tool_input``,
``reasoning_summary``, ``provider_used``. The chosen tool is then dispatched
through the existing MCP-shaped tool layer (``cop.*`` / ``thief.*``) — the
agent layer decides, the engine still owns the only true state S.
"""

from src.agents.cop_agent import CopAgent
from src.agents.thief_agent import ThiefAgent

__all__ = ["CopAgent", "ThiefAgent"]
