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
- [ ] Implement `src/config_loader.py` (load + validate config).  *(Phase 2)*
- [ ] Add empty module stubs (each will stay < 150 lines).  *(Phase 2)*

---

## Phase 2 — Core Engine

- [ ] `engine/board.py` — grid, cells, start positions, state machine.
- [ ] `engine/rules.py` — move legality (incl. diagonals), capture detection.
- [ ] `engine/rules.py` — barrier placement + `max_barriers` cap (Cop only).
- [ ] `engine/scoring.py` — per sub-game table + accumulated totals (30–90).
- [ ] `engine/observation.py` — partial-view builder per agent.
- [ ] `engine/game_loop.py` — sub-game (25 moves) + 6-game series driver.
- [ ] `engine/game_loop.py` — technical-loss detection + re-run.
- [ ] Unit tests: `tests/test_rules.py`, `tests/test_scoring.py`.

---

## Phase 3 — MCP Servers

- [ ] `mcp/tools.py` — shared tool schemas (validate/apply move, barrier,
  send/receive message).
- [ ] `mcp/cop_server.py` — FastMCP server exposing Cop tools (tools only).
- [ ] `mcp/thief_server.py` — FastMCP server exposing Thief tools.
- [ ] Run both servers on separate `localhost` ports.
- [ ] Verify mutual position validation between the two servers.

---

## Phase 4 — Agents & Orchestrator

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

- [ ] `joker/joker.py` — Joker Card lifecycle (grant to sub-game winner).
- [ ] Inject **one plausible false observation signal** into opponent's `Ωᵢ`.
- [ ] Enforce boundaries: no second Thief, no teleport, no scoring change,
  no baseline-rule override.
- [ ] `tests/test_observation.py` — assert true state `S` is never mutated.
- [ ] Confirm baseline mode passes with `joker_enabled: false`.

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
