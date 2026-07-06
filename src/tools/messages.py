"""Deterministic natural-language message templates (Phase 4 — NO LLM).

The tool-call log needs a human-readable ``message`` field alongside each
communicating action. Phase 4 fills it with simple templated strings so the
pipeline demonstrably carries free natural language; LLM-authored messages
arrive in a later phase. These are plain string formatters, not model calls.
"""

from __future__ import annotations


def move_message(role: str, to) -> str:
    cell = (int(to[0]), int(to[1]))
    if role == "thief":
        return f"Thief sliding to {cell} to keep the gap open."
    return f"Cop advancing to {cell} to close the distance."


def barrier_message(cell) -> str:
    target = (int(cell[0]), int(cell[1]))
    return f"Cop dropping a barrier at {target} to cut off an escape route."
