"""Cop MCP server (Phase 3) — FastMCP, tools only, no LLM.

Exposes the Cop agent's tools over MCP:
    observe_board, receive_message, send_message, move, place_barrier,
    get_score
The LLM lives in the client/orchestrator (Phase 4); this server only wraps the
existing engine via a `GameSession`.

Run locally (stdio transport by default; local host/port only, no cloud):
    python -m src.mcp.cop_server --config config.json
"""

from __future__ import annotations

import argparse

from src.mcp.session import (DEFAULT_CONFIG, GameSession, load_or_default,
                             require_fastmcp)

AGENT = "cop"
COP_TOOLS = ("observe_board", "receive_message", "send_message",
             "move", "place_barrier", "get_score")


def create_server(config=None):
    """Build (do NOT run) the Cop FastMCP server.

    Returns ``(mcp, session)``. Raises RuntimeError with install guidance if
    FastMCP is unavailable. This never starts a blocking server, so it is safe
    to call from tests.
    """
    FastMCP = require_fastmcp()
    config = load_or_default(config)
    session = GameSession(config)
    mcp = FastMCP("cop-server")

    @mcp.tool()
    def observe_board() -> dict:
        """Return the Cop's partial observation of the board."""
        return session.observe(AGENT)

    @mcp.tool()
    def receive_message() -> dict:
        """Drain the natural-language messages sent to the Cop."""
        return session.receive_message(AGENT)

    @mcp.tool()
    def send_message(text: str) -> dict:
        """Send a free natural-language message to the Thief."""
        return session.send_message(AGENT, text)

    @mcp.tool()
    def move(row: int, col: int) -> dict:
        """Move the Cop to (row, col); reports capture and winner."""
        return session.move(AGENT, (row, col))

    @mcp.tool()
    def place_barrier(row: int, col: int) -> dict:
        """Place a barrier at (row, col) — Cop only, capped per sub-game."""
        return session.place_barrier((row, col))

    @mcp.tool()
    def get_score() -> dict:
        """Return running Cop/Thief totals and game status."""
        return session.get_score()

    return mcp, session


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="src.mcp.cop_server", description="Cop MCP server (local only).")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG),
                        help="Path to config.json (default: project root).")
    args = parser.parse_args()

    from src.config_loader import load_config
    cfg = load_config(args.config)
    mcp, _ = create_server(cfg)
    srv = cfg.get("mcp", {}).get("cop_server", {})
    host, port = srv.get("host", "localhost"), srv.get("port", 8001)
    print(f"[cop-server] starting locally (config target http://{host}:{port})")
    try:
        mcp.run(transport="streamable-http", host=host, port=port)
    except (TypeError, ValueError):
        mcp.run()  # older FastMCP: default stdio transport


if __name__ == "__main__":
    main()
