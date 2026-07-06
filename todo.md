# TODO — MCP Chase: Joker Protocol

Phased checklist following the Vibe Coding lifecycle and the assignment's
recommended development order (logic → MCP infra → local run → strategy →
natural language → GUI → cloud → Gmail). **Documentation comes first.**

Legend: `[ ]` open · `[x]` done · ⭐ optional / bonus.

---

## Phase 0 — Documentation (current)

- [x] Read both assignment source PDFs.
- [x] `prd.md` — requirements, rules, Joker Protocol, evaluation.
- [x] `plan.md` — architecture, data/execution flow, testing, submission.
- [x] `todo.md` — this phased checklist.
- [x] `README.md` — overview, diagram, CLI, current status.
- [ ] Review docs for alignment with EX06 (no invented results).

---

## Phase 1 — Project Skeleton

- [x] Create folder structure (`src/`, `results/logs|reports|plots/`, `tests/`).
- [x] Add `requirements.txt` (FastMCP, LLM SDK, numpy, google-api-client).
- [x] Add `.gitignore` (exclude secrets, tokens, caches, generated results).
- [x] Create `config.json` with all parameters + defaults.
- [x] Add `src/main.py` CLI placeholder (`python -m src.main`, no game logic).
- [x] Add Phase 1 smoke test (`tests/test_skeleton.py`) for structure + config.
- [x] Implement `src/config_loader.py` (load + validate config).
- [x] Add engine/policy/joker/reporting modules (each stays < 150 lines).

---

## Phase 2 — Core Engine

- [x] `engine/board.py` — grid, cells, start positions, state machine.
- [x] `engine/rules.py` — move legality (incl. diagonals), capture detection.
- [x] `engine/rules.py` — barrier placement + `max_barriers` cap (Cop only).
- [x] `engine/scoring.py` — per sub-game table + accumulated totals.
- [x] `engine/observation.py` — partial-view builder per agent.
- [x] `engine/game_loop.py` — sub-game (25 moves) + 6-game series driver.
- [x] Deterministic placeholder policies (`policies/cop_policy.py`,
  `policies/thief_policy.py`) so the sim runs end-to-end without LLM/MCP.
- [x] Local run entry point `python -m src.main` + JSONL log + JSON report.
- [ ] `engine/game_loop.py` — technical-loss detection + re-run.
- [x] Unit tests: `tests/test_rules.py`, `tests/test_scoring.py`,
  `tests/test_observation.py`, `tests/test_game_loop.py` (both win paths).

---

## Phase 3 — MCP Servers

- [x] `mcp/session.py` — shared FastMCP loader + `GameSession` wrapping the
  engine (observe, move, barrier, send/receive message, joker, score).
  *(implemented as `session.py` rather than `tools.py`)*
- [x] `mcp/cop_server.py` — FastMCP server exposing Cop tools (tools only):
  observe_board, receive_message, send_message, move, place_barrier, get_score.
- [x] `mcp/thief_server.py` — FastMCP server exposing Thief tools: observe_board,
  receive_message, send_message, move, use_joker_card, get_score.
- [x] Fail clearly (`pip install mcp` / `fastmcp`) when FastMCP is unavailable;
  `create_server()` builds but never runs, so imports stay non-blocking.
- [x] `tests/test_mcp_servers.py` — tool surfaces + `GameSession` behavior
  (import without starting a blocking server).
- [x] CLI entry points: `python -m src.mcp.cop_server` /
  `python -m src.mcp.thief_server` with local `localhost` host/port from config.
- [ ] Actually run both servers on separate `localhost` ports (needs FastMCP
  installed; not yet verified live).
- [ ] Verify mutual position validation between the two servers (Phase 4
  orchestrator drives one shared board).

---

## Phase 4 — Agents & Orchestrator

### Phase 4a — Local tool integration (done)

- [x] `tools/local_adapter.py` — `LocalToolAdapter`: in-process tools that
  mirror the MCP servers' surface and call the engine directly (no network,
  no LLM). True state changes stay in `Board` + `rules`.
- [x] `tools/dispatcher.py` — `ToolDispatcher`: validates, routes, and logs
  every `cop.*` / `thief.*` tool call. Tool names imported from the Phase 3
  server modules (`COP_TOOLS`, `THIEF_TOOLS`) so local and MCP modes share one
  vocabulary.
- [x] `tools/messages.py` — deterministic natural-language message templates
  (still no LLM).
- [x] Route `engine/game_loop.py` actions through the tool layer
  (`observe_board`, `send_message`, `move`, `place_barrier`,
  `use_joker_card`) without rewriting the engine.
- [x] `game_log.jsonl`: per-action `tool_call` record with agent role, tool
  name, tool input, tool result, and NL message.
- [x] Keep MCP server modules separate; do **not** start blocking servers in a
  normal `python -m src.main` run.
- [x] Joker routed via `thief.use_joker_card`; tool never mutates true state
  `S` (only injects the opponent's next observation).
- [x] `tests/test_tool_layer.py` — dispatcher routing, log tool-name coverage,
  Joker observation-only effect, normal run writes report + logs.
- [x] Baseline behavior preserved (Cop 120 / Thief 30 on default config).

### Phase 4b — LLM agents over MCP (not started)

- [ ] `agents/llm_client.py` — backend abstraction (cloud API / Ollama / hybrid).
- [ ] `agents/prompts.py` — prompt templates for Cop and Thief.
- [ ] `agents/cop_agent.py` — reasoning + natural-language message generation.
- [ ] `agents/thief_agent.py` — reasoning + natural-language message generation.
- [ ] `client/orchestrator.py` — MCP client, dialogue loop, Tool Call wiring.
- [ ] Confirm LLM lives in the **client**, not in the MCP servers.
- [ ] Full local end-to-end run of one sub-game, then all 6.
- [ ] Replace any numeric handshake with **free natural-language** messages.
- [ ] ⭐ Strategy: heuristic / Manhattan distance / decision tree.
- [ ] ⭐ Strategy: tabular Q-Learning (state/action/reward, Bellman update).

---

## Phase 5 — Joker Protocol (optional extension)

- [x] `joker/joker.py` — Joker Card lifecycle (grant to sub-game winner).
  *(data hooks only, added in Phase 2)*
- [x] Inject **one plausible false observation signal** into opponent's `Ωᵢ`,
  logged. *(deterministic placeholder trigger; not a full strategy yet)*
- [x] Enforce boundaries: no second Thief, no teleport, no scoring change,
  no baseline-rule override.
- [x] `tests/test_observation.py` — assert true state `S` is never mutated.
- [x] Confirm baseline mode passes with `joker_enabled: false`.

---

## Phase 6 — GUI / Dashboard (optional, if time)

- [ ] `gui/dashboard.py` — visualize board, agent movement, barriers.
- [ ] ⭐ Show Q-Table (if Q-Learning used).
- [ ] ⭐ Capture a screenshot for the README.

---

## Phase 7 — Reporting

- [ ] `reporting/report_builder.py` — build Internal Game JSON (schema §9).
- [ ] Write report to `results/reports/game_report.json`.
- [ ] Ensure report body is **structured JSON only** (no free text).
- [ ] ⭐ `reporting/gmail_sender.py` — Gmail API (OAuth token) send.
- [ ] ⭐ Cop agent auto-emails report to `rmisegal+uoh26b@gmail.com`.
- [ ] ⭐ Build Inter-Group Bonus JSON for the bonus tournament.

---

## Phase 8 — Verification

- [ ] Sanity check 2×2 (pipeline + message transfer).
- [ ] Sanity check 3×3 / 3×2 (coordination convergence).
- [ ] Sanity check 4×4 / 4×3 (partial-observation ambiguity).
- [ ] Sanity check 5×5 (final full-game run + graphs).
- [ ] Confirm every Python file is under 150 lines.
- [ ] Confirm correct win/barrier/scoring behavior.
- [ ] ⭐ Cloud deployment with token auth + firewall/tunnel.

---

## Phase 9 — GitHub Submission

- [ ] Public repo `mcp-chase-joker-protocol` with all source under `src/`.
- [ ] `README.md` in root (scientific: Dec-POMDP + orchestration analysis).
- [ ] `config.json` committed; secrets excluded.
- [ ] `results/` contains the generated JSON report.
- [ ] Embed repo URL in the Internal Game JSON.
- [ ] Final review against `prd.md` success criteria.
- [ ] ⭐ Submit Inter-Group Bonus report within one week of publication.
