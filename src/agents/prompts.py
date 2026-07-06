"""Prompt construction for the LLM (Ollama) agents.

Two personas — a focused detective (Cop) and a playful trickster (Thief) — both
instructed to return JSON ONLY. The schema mirrors the structured decision the
rest of the pipeline consumes, so a well-behaved model response maps straight
onto an MCP-shaped tool call.
"""

from __future__ import annotations

import json

PERSONAS = {
    "cop": ("You are the COP: a focused, methodical detective hunting the "
            "Thief on a grid. You speak in short, confident deductions and "
            "close the distance every turn."),
    "thief": ("You are the THIEF: a playful, teasing trickster slipping away "
              "from the Cop on a grid. You speak with cheeky misdirection while "
              "keeping a safe gap."),
}

_SCHEMA = ('{"natural_language_message": "<in-character taunt or deduction>", '
           '"chosen_tool": "<one of the available tools>", '
           '"tool_input": {"to": [row, col]}  (use {"cell": [row, col]} for '
           'place_barrier), '
           '"reasoning_summary": "<one short sentence>"}')


def build_prompt(role: str, ctx: dict) -> tuple:
    """Return ``(system, user)`` prompt strings for ``role`` given context."""
    persona = PERSONAS.get(role, PERSONAS["cop"])
    system = (
        f"{persona}\n"
        f"Objective: {ctx['objective']}\n"
        "You must reply with a SINGLE JSON object and NOTHING else — no prose, "
        "no markdown, no code fences.\n"
        f"JSON schema: {_SCHEMA}\n"
        "chosen_tool MUST be one of the available tools. The move/barrier cell "
        "MUST be one of the legal targets listed. Stay fully in character."
    )
    user = _describe(role, ctx)
    return system, user


def _describe(role: str, ctx: dict) -> str:
    obs = ctx["observation"]
    lines = [
        f"You are the {role}.",
        f"Board: {obs['rows']} rows x {obs['cols']} cols.",
        f"Your position: {list(obs['self'])}.",
        f"Believed opponent position: {list(obs['opponent'])} "
        f"(joker_injected={obs['joker_injected']}).",
        f"Barriers on board: {obs['barriers']}.",
        f"Move index: {obs['move_index']}, moves left: {obs['moves_left']}.",
        f"Available tools: {ctx['available_tools']}.",
        f"Legal move targets: {ctx['legal_targets']}.",
    ]
    if ctx.get("last_opponent_message"):
        lines.append(f"Opponent just said: \"{ctx['last_opponent_message']}\".")
    joker = ctx.get("joker") or {}
    if joker.get("available"):
        lines.append("You are holding a Joker card this sub-game.")
    lines.append("Respond with the JSON object now.")
    return "\n".join(lines)


def combined_prompt(system: str, user: str) -> str:
    """Flatten system+user into one prompt for the Ollama /api/generate call."""
    return f"{system}\n\n{user}\n\nJSON:"


def as_json_hint() -> str:
    """Example object used only in docs/tests to show the expected shape."""
    return json.dumps({
        "natural_language_message": "Closing in.",
        "chosen_tool": "move",
        "tool_input": {"to": [1, 1]},
        "reasoning_summary": "Step toward the opponent.",
    })
