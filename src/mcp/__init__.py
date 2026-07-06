"""Phase 3 — MCP server layer.

Two separate FastMCP servers (Cop, Thief) that expose TOOLS ONLY over MCP.
No LLM, GUI, or Gmail lives here — the LLM belongs to the client/orchestrator
(Phase 4). Each server wraps the existing engine through a shared GameSession
(see `session.py`); the engine itself is never rewritten.
"""
