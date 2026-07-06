"""Local in-process tool dispatcher (Phase 4).

Routes every Cop/Thief action through explicit, MCP-shaped tool calls. The tool
NAMES are the exact ones the FastMCP servers expose (imported from the server
modules, so local mode and real MCP mode share one vocabulary). Each call is
logged with: agent role, tool name (``role.tool``), tool input, tool result,
and any natural-language message.

Local vs real MCP: here the calls hit a `LocalToolAdapter` in-process; the real
`src/mcp/*` servers expose the same tool names over an MCP transport. The
dispatcher never starts a server and never runs an LLM.
"""

from __future__ import annotations

from typing import Optional


class ToolDispatcher:
    """Validate + route + log named tool calls against a local adapter."""

    def __init__(self, adapter, logger, subgame_index: int):
        # Lazy import keeps the MCP modules separate and avoids an import cycle
        # (mcp.session imports engine.game_loop, which imports this dispatcher).
        from src.mcp.cop_server import COP_TOOLS
        from src.mcp.thief_server import THIEF_TOOLS

        self.adapter = adapter
        self.logger = logger
        self.subgame = subgame_index
        self._names = {"cop": set(COP_TOOLS), "thief": set(THIEF_TOOLS)}
        self._handlers = {
            ("cop", "observe_board"): lambda a, i: a.observe_board("cop"),
            ("cop", "receive_message"): lambda a, i: a.receive_message("cop"),
            ("cop", "send_message"): lambda a, i: a.send_message("cop", i["text"]),
            ("cop", "move"): lambda a, i: a.move("cop", i["to"]),
            ("cop", "place_barrier"): lambda a, i: a.place_barrier(i["cell"]),
            ("cop", "get_score"): lambda a, i: a.get_score("cop"),
            ("thief", "observe_board"): lambda a, i: a.observe_board("thief"),
            ("thief", "receive_message"): lambda a, i: a.receive_message("thief"),
            ("thief", "send_message"): lambda a, i: a.send_message("thief", i["text"]),
            ("thief", "move"): lambda a, i: a.move("thief", i["to"]),
            ("thief", "use_joker_card"): lambda a, i: a.use_joker_card("thief"),
            ("thief", "get_score"): lambda a, i: a.get_score("thief"),
        }

    def call(self, role: str, tool: str, tool_input: Optional[dict] = None,
             message: Optional[str] = None):
        """Invoke ``role.tool`` on the adapter, log it, and return the result."""
        if role not in self._names or tool not in self._names[role]:
            raise KeyError(f"unknown tool for role: {role}.{tool}")
        handler = self._handlers.get((role, tool))
        if handler is None:
            raise KeyError(f"no local handler for tool: {role}.{tool}")
        tool_input = dict(tool_input or {})
        result = handler(self.adapter, tool_input)
        self.logger.log({
            "type": "tool_call",
            "subgame": self.subgame,
            "move_index": self.adapter.move_index,
            "agent": role,
            "tool": f"{role}.{tool}",
            "tool_input": tool_input,
            "tool_result": result,
            "message": message,
        })
        return result
