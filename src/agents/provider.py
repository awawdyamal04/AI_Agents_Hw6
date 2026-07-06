"""Decision providers: deterministic (default) and real local Ollama.

- ``DeterministicProvider`` never touches the network; the agent just uses its
  placeholder-policy candidate. Default for tests.
- ``OllamaProvider`` calls the local Ollama HTTP API with the standard library
  only (urllib/json). If the server is unreachable it raises
  ``OllamaUnavailable`` — we NEVER fake Ollama output when ollama is selected.

``parse_decision`` turns raw model text into the structured decision, and
falls back to the deterministic candidate ONLY for malformed/invalid JSON
(recording that in ``reasoning_summary``), never for a missing server.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "smollm2:135m"


class OllamaUnavailable(RuntimeError):
    """Raised when the selected Ollama server cannot be reached."""


class DeterministicProvider:
    name = "deterministic"

    def complete(self, system: str, user: str):  # noqa: D401 - no model text
        return None


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url=DEFAULT_BASE_URL, model=DEFAULT_MODEL,
                 timeout: float = 60.0):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.model = model or DEFAULT_MODEL
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        from src.agents.prompts import combined_prompt
        payload = json.dumps({
            "model": self.model,
            "prompt": combined_prompt(system, user),
            "stream": False,
            "format": "json",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate", data=payload,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise OllamaUnavailable(
                f"Cannot reach Ollama at {self.base_url} (model={self.model}). "
                f"Start it with 'ollama serve' and 'ollama pull {self.model}'. "
                f"Underlying error: {exc}") from exc
        return body.get("response", "")


def make_provider(config: dict):
    """Build the provider named by ``config['agent_provider']`` (default det.)."""
    name = (config.get("agent_provider") or "deterministic").lower()
    if name == "deterministic":
        return DeterministicProvider()
    if name == "ollama":
        return OllamaProvider(config.get("ollama_base_url", DEFAULT_BASE_URL),
                              config.get("ollama_model", DEFAULT_MODEL))
    raise ValueError(
        f"unknown agent_provider: {name!r} (use 'deterministic' or 'ollama')")


def extract_json(raw) -> dict:
    """Best-effort parse of a JSON object from model text; None if impossible."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except ValueError:
        pass
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        obj = json.loads(raw[start:end + 1])
        return obj if isinstance(obj, dict) else None
    except ValueError:
        return None


def _cell_of(tool_input: dict):
    if not isinstance(tool_input, dict):
        return None
    raw = tool_input.get("to", tool_input.get("cell"))
    try:
        return (int(raw[0]), int(raw[1]))
    except (TypeError, ValueError, IndexError):
        return None


def _validate(obj: dict, ctx: dict):
    """Return (chosen_tool, tool_input) if valid, else (None, reason)."""
    tool = obj.get("chosen_tool")
    if tool not in ctx["available_tools"]:
        return None, f"tool {tool!r} not available"
    cell = _cell_of(obj.get("tool_input"))
    if cell is None:
        return None, "missing/invalid tool_input cell"
    if cell not in {tuple(t) for t in ctx["legal_targets"]}:
        return None, f"cell {list(cell)} not a legal target"
    key = "cell" if tool == "place_barrier" else "to"
    return tool, {key: [cell[0], cell[1]]}


def parse_decision(raw, ctx: dict, candidate: dict) -> dict:
    """Structured decision from model text; deterministic fallback on bad JSON."""
    obj = extract_json(raw)
    if obj is None:
        return _fallback(candidate, "Ollama returned non-JSON; used "
                         "deterministic policy.")
    tool, info = _validate(obj, ctx)
    if tool is None:
        return _fallback(candidate, f"Ollama JSON invalid ({info}); used "
                         "deterministic policy.")
    msg = obj.get("natural_language_message") or candidate[
        "natural_language_message"]
    reasoning = obj.get("reasoning_summary") or "Ollama chose a legal action."
    return {"natural_language_message": str(msg), "chosen_tool": tool,
            "tool_input": info, "reasoning_summary": str(reasoning),
            "provider_used": "ollama"}


def _fallback(candidate: dict, note: str) -> dict:
    out = dict(candidate)
    out["reasoning_summary"] = f"{candidate['reasoning_summary']} [{note}]"
    out["provider_used"] = "ollama"
    return out
