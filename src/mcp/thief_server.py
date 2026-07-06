"""Thief MCP server (Phase 3) — FastMCP, tools only, no LLM.

Exposes the Thief agent's tools over MCP:
    observe_board, receive_message, send_message, move, use_joker_card,
    get_score
The LLM lives in the client/orchestrator (Phase 4); this server only wraps the
existing engine via a `GameSession`.

Run locally (stdio transport by default; local host/port only, no cloud):
    python -m src.mcp.thief_server --config config.json
"""

from __future__ import annotations

import argparse

from src.mcp.session import (DEFAULT_CONFIG, GameSession, load_or_default,
                             require_fastmcp)

AGENT = "thief"
THIEF_TOOLS = ("observe_board", "receive_message", "send_message",
               "move", "use_joker_card", "get_score")


def create_server(config=None):
    """Build (do NOT run) the Thief FastMCP server.

    Returns ``(mcp, session)``. Raises RuntimeError with install guidance if
    FastMCP is unavailable. This never starts a blocking server, so it is safe
    to call from tests.
    """
    FastMCP = require_fastmcp()
    config = load_or_default(config)
    session = GameSession(config)
    mcp = FastMCP("thief-server")

    @mcp.tool()
    def observe_board() -> dict:
        """Return the Thief's partial observation of the board."""
        return session.observe(AGENT)

    @mcp.tool()
    def receive_message() -> dict:
        """Drain the natural-language messages sent to the Thief."""
        return session.receive_message(AGENT)

    @mcp.tool()
    def send_message(text: str) -> dict:
        """Send a free natural-language message to the Cop."""
        return session.send_message(AGENT, text)

    @mcp.tool()
    def move(row: int, col: int) -> dict:
        """Move the Thief to (row, col); reports capture and winner."""
        return session.move(AGENT, (row, col))

    @mcp.tool()
    def use_joker_card() -> dict:
        """Play the Thief's Joker card (one false signal into the Cop's view).

        No-op unless the Joker Protocol is enabled and a card is held; the
        true board state is never mutated.
        """
        return session.use_joker(AGENT)

    @mcp.tool()
    def get_score() -> dict:
        """Return running Cop/Thief totals and game status."""
        return session.get_score()

    return mcp, session


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="src.mcp.thief_server", description="Thief MCP server (local).")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG),
                        help="Path to config.json (default: project root).")
    args = parser.parse_args()

    from src.config_loader import load_config
    cfg = load_config(args.config)
    mcp, _ = create_server(cfg)
    srv = cfg.get("mcp", {}).get("thief_server", {})
    host, port = srv.get("host", "localhost"), srv.get("port", 8002)
    print(f"[thief-server] starting locally (config target http://{host}:{port})")
    try:
        mcp.run(transport="streamable-http", host=host, port=port)
    except (TypeError, ValueError):
        mcp.run()  # older FastMCP: default stdio transport


if __name__ == "__main__":
    main()
