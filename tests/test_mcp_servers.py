"""Phase 3 smoke checks for the MCP server layer.

These import the MCP server modules and exercise the underlying GameSession
WITHOUT starting a blocking server. Building a real FastMCP server is only
attempted when FastMCP is installed; otherwise we assert the failure message
names the package to install.
"""

from __future__ import annotations

import copy

import pytest

from src.config_loader import load_config
from src.mcp import cop_server, thief_server
from src.mcp.session import DEFAULT_CONFIG, GameSession, require_fastmcp

CFG = load_config(DEFAULT_CONFIG)


def _has_fastmcp() -> bool:
    try:
        require_fastmcp()
        return True
    except RuntimeError:
        return False


# --- required tool surfaces (always checkable, no FastMCP needed) ---

def test_cop_exposes_required_tools():
    required = {"observe_board", "receive_message", "send_message",
                "move", "place_barrier", "get_score"}
    assert required.issubset(set(cop_server.COP_TOOLS))


def test_thief_exposes_required_tools():
    required = {"observe_board", "receive_message", "send_message",
                "move", "use_joker_card", "get_score"}
    assert required.issubset(set(thief_server.THIEF_TOOLS))


# --- FastMCP loader behavior ---

def test_create_server_requires_fastmcp():
    if _has_fastmcp():
        pytest.skip("FastMCP is installed")
    with pytest.raises(RuntimeError) as exc:
        cop_server.create_server(CFG)
    assert "pip install" in str(exc.value)


@pytest.mark.skipif(not _has_fastmcp(), reason="FastMCP not installed")
def test_servers_build_without_running():
    mcp_cop, sess_cop = cop_server.create_server(CFG)
    mcp_thief, sess_thief = thief_server.create_server(CFG)
    assert mcp_cop is not None and isinstance(sess_cop, GameSession)
    assert mcp_thief is not None and isinstance(sess_thief, GameSession)


# --- GameSession behavior (wraps the existing engine) ---

def test_observe_returns_partial_view():
    obs = GameSession(CFG).observe("cop")
    assert obs["agent"] == "cop"
    assert "self" in obs and "opponent" in obs


def test_messaging_delivers_and_drains():
    s = GameSession(CFG)
    s.send_message("cop", "heading north")
    assert s.receive_message("thief")["messages"] == ["heading north"]
    assert s.receive_message("thief")["messages"] == []  # drained


def test_move_capture_updates_score():
    s = GameSession(CFG)
    s.board.cop, s.board.thief = (0, 0), (0, 1)
    res = s.move("cop", (0, 1))
    assert res["captured"] is True and res["winner"] == "cop"
    score = s.get_score()
    assert score["cop"] == CFG["scoring"]["cop_win"]
    assert score["thief"] == CFG["scoring"]["thief_loss"]


def test_illegal_move_raises():
    s = GameSession(CFG)
    s.board.cop = (0, 0)
    with pytest.raises(ValueError):
        s.move("cop", (3, 3))


def test_place_barrier_legal_and_illegal():
    s = GameSession(CFG)
    s.board.cop, s.board.thief = (0, 0), (4, 4)
    assert s.place_barrier((2, 2))["placed"] is True
    assert s.board.is_barrier((2, 2))
    assert s.place_barrier((0, 0))["placed"] is False  # occupied by cop


def test_use_joker_injects_only_when_enabled():
    s = GameSession(CFG)  # joker disabled by default
    assert s.use_joker("thief")["played"] is False

    cfg = copy.deepcopy(CFG)
    cfg["joker_protocol"]["enabled"] = True
    s2 = GameSession(cfg)
    assert s2.use_joker("thief")["played"] is False  # no card yet
    s2.joker.grant("thief")
    s2.move_index = 0
    assert s2.use_joker("thief")["played"] is True
    assert s2.observe("cop")["joker_injected"] is True
