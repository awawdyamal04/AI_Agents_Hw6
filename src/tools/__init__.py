"""Local tool layer (Phase 4).

In-process adapters that mirror the FastMCP servers' tool surface so the local
game loop routes every Cop/Thief action through explicit, MCP-shaped tool calls
(e.g. ``cop.move``, ``thief.use_joker_card``). This makes local mode and real
MCP mode share one tool vocabulary; the true state S still lives in the engine.
"""
