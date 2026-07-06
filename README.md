# MCP Chase: Joker Protocol

> **Course:** Orchestration of AI Agents · **Assignment:** EX06 — Dual AI
> Agent Conversation via MCP Servers
> **Current status:** 🟢 **Phase 3 — MCP server layer.** Two separate FastMCP
> servers (Cop, Thief) now expose the agent tools over MCP, wrapping the
> existing Phase 2 engine (board, rules, capture, barriers, scoring,
> observation, Joker hooks). The servers are **tools only** — no LLM.
> **Not yet implemented: LLM calls, orchestrator/client, GUI, Gmail.**

A dual autonomous AI-agent pursuit game. A **Cop** and a **Thief**, each
running behind its **own MCP server**, converse in **free natural language**
and chase each other on a grid under **partial observation**. The point of
the assignment is **orchestration** — wiring up two autonomous agents that
understand each other and act — not winning the game.

---

## Project Overview

- Two agents: **Cop** (captures) and **Thief** (evades).
- Two **independent MCP servers** (FastMCP), one per agent, exposing **tools
  only**.
- One **MCP client / orchestrator** that owns the dialogue loop and the LLM.
- A turn-based chase on a configurable grid (default **5×5**), modeled
  formally as a **Dec-POMDP**.
- A structured **JSON report** at the end, optionally emailed via the Gmail
  API.
- An **optional creative extension**: the **Joker Protocol** (see below),
  which is off by default and never breaks the baseline rules.

---

## Assignment Summary

Two autonomous AI agents must:

1. **Decipher** each other's natural-language messages.
2. **Infer** the opponent's location under partial observation.
3. **Translate** those inferences into grid moves.

A full **game** is **6 sub-games**; each **sub-game** runs up to **25 moves**.
In a full game a group plays 3 sub-games as Cop and 3 as Thief. The graded
value is the working end-to-end orchestration pipeline running autonomously —
not the strategy or the score.

---

## Baseline Requirements (EX06)

| Area | Requirement |
|------|-------------|
| **Agents** | Two autonomous agents: Cop and Thief |
| **MCP** | Two separate FastMCP servers; LLM lives in the **client**, servers expose tools only |
| **Communication** | Free **natural language**, not a rigid numeric protocol |
| **Board** | Configurable grid, default 5×5; movement in all directions incl. diagonals |
| **Sub-game** | Up to 25 moves; turn-based (Thief first, then Cop) |
| **Game** | 6 consecutive sub-games; results accumulate |
| **Win** | Cop wins by landing on the Thief's cell; Thief wins by surviving 25 moves |
| **Barriers** | Cop may place up to 5 barriers/sub-game; Thief cannot |
| **Scoring** | Cop win → Cop 20 / Thief 5 · Thief win → Cop 5 / Thief 10 (max 90, min 30) |
| **Config** | All parameters in `config.json` — **no hard-coding** |
| **Report** | Structured **JSON only**; optional Gmail API delivery |
| **Deployment** | Local (`localhost`) → cloud, with token auth + firewall/tunnel |
| **Code style** | Every Python file under **150 lines** |

The pursuit is formalized as a **Dec-POMDP**:
`⟨ n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ ⟩` — see `prd.md` §3 for the full mapping.

---

## Joker Protocol (Optional Extension)

Our optional creative extension, **off by default** (`joker_enabled: false`).
With it disabled, the project follows EX06 exactly.

- The **winner of a sub-game** receives **one Joker Card** for the **next
  sub-game**.
- Playing the Joker **injects one plausible false observation signal** into
  the opponent's partial observation for a single turn.
- It is a pure **observation-layer** extension — a one-shot perturbation of
  the Dec-POMDP observation function `O`.

**It must never:** create a second physical Thief · teleport an agent ·
change scoring · replace any baseline rule. True state `S`, transitions `P`,
and rewards `R` are untouched — only the observation `Ωᵢ` is affected.

In **Phase 2 only the data hooks** exist: card lifecycle (grant to the
sub-game winner) and one-shot false-signal injection into the opponent's
observation, with logging. It is **disabled by default**, so the default run
follows the EX06 baseline exactly. A unit test asserts the injection never
mutates the true state `S`.

---

## Phase 2 — Local Simulation

Phase 2 implements the **core game engine** and a **local, playable
simulation** that runs entirely offline — no network, no LLM, no MCP.

- **Engine (true state `S`)** — `src/engine/`: `board.py` (grid + state),
  `rules.py` (legal moves, capture, barriers), `observation.py` (partial
  view `Ωᵢ`), `scoring.py` (scoring table + totals), `game_loop.py` (sub-game
  + 6-game series driver).
- **Deterministic placeholder policies** — `src/policies/`: a greedy-pursuit
  Cop and a distance-maximizing, centre-seeking Thief. These are **stand-ins
  for the future LLM/MCP agents** so the pipeline can run end-to-end; they are
  not optimized strategy (strategy quality is explicitly *not* graded).
- **Joker data hooks** — `src/joker/joker.py` (disabled by default).
- **Config-driven** — every parameter comes from `config.json`; nothing is
  hard-coded. Phase 2 added `random_seed`, `cop_uses_barriers`,
  `barrier_interval`, `diagonal_movement`, and the output paths.

### Run it

```bash
python -m src.main                       # uses ./config.json
python -m src.main --config config.json  # explicit config
pytest tests/                            # unit tests
```

### Movement rule (per the docs)

The assignment docs (`prd.md` §7.2, and the board row of the baseline table
above) **explicitly allow diagonal movement**. The engine therefore uses
**8-directional (king-move) movement** plus staying in place — *not*
4-directional. This is surfaced in the report as `"diagonal_movement": true`.

### Outputs

- `results/logs/game_log.jsonl` — per-move trace (start state, each agent's
  action + resulting state, any Joker injection, per-sub-game result).
- `results/reports/final_report.json` — structured summary of all 6 sub-games
  plus accumulated totals.

### Observed baseline result (not invented — produced by a real run)

With the baseline `config.json` (5×5 grid, 25 moves, `random_seed: 42`) the
Cop captures the Thief in every sub-game (each in 3–4 moves), giving totals
**Cop = 120, Thief = 30**. This is the expected outcome of *simple* deterministic
policies: in discrete king-move pursuit on a bounded grid, a pursuer that moves
second corners a myopic (one-step-greedy) evader — increasing the grid size does
not help the greedy Thief. The Thief-win branch and its `5 / 10` scoring are
verified through the real game loop by `tests/test_game_loop.py`
(short-horizon sub-game). These placeholder policies will be replaced by
LLM-driven MCP agents in later phases, where deception and inference make the
outcome non-trivial.

> Note: the 30–90 score band in `prd.md` §7.4 describes a **group** that plays
> 3 sub-games as Cop and 3 as Thief. The Phase-2 self-play run instead uses one
> policy as Cop and one as Thief for all 6 sub-games, so its per-side totals are
> not bounded by that band.

---

## Phase 3 — MCP Server Layer

Phase 3 adds two **independent FastMCP servers**, one per agent. Each server
**exposes tools only** and wraps the existing engine through a shared
`GameSession` (`src/mcp/session.py`) — the engine is **not** rewritten. There
is still **no LLM** here: the LLM belongs to the client/orchestrator (Phase 4).

- **`src/mcp/cop_server.py`** — Cop tools: `observe_board`, `receive_message`,
  `send_message`, `move`, `place_barrier`, `get_score`.
- **`src/mcp/thief_server.py`** — Thief tools: `observe_board`,
  `receive_message`, `send_message`, `move`, `use_joker_card`, `get_score`.
- **`src/mcp/session.py`** — FastMCP loader (`require_fastmcp`) + `GameSession`
  wrapping `Board`, `rules`, `observation`, `scoring`, and `Joker`.

`create_server()` **builds but never runs** the server, so tests can import and
construct it without blocking. If FastMCP is missing, `require_fastmcp()` (and
therefore `create_server()`) raises a clear error naming the package to
install (`pip install mcp`, or `pip install fastmcp`). Imports of the modules
themselves succeed regardless — the FastMCP dependency is loaded lazily.

### Run the servers (local only)

```bash
# Cop and Thief MCP servers — separate localhost ports from config.json
python -m src.mcp.cop_server   --config config.json   # localhost:8001
python -m src.mcp.thief_server --config config.json   # localhost:8002
```

> Transport defaults to FastMCP's stdio; the `mcp.cop_server` / `mcp.thief_server`
> host+port in `config.json` are **local `localhost` URLs only** — no cloud URLs
> are configured or faked. Cloud deployment (token auth + firewall/tunnel) is a
> later phase.

### Smoke check (no blocking server started)

```bash
python -c "from src.mcp.cop_server import create_server; \
from src.mcp.thief_server import create_server; print('mcp imports ok')"
pytest tests/test_mcp_servers.py     # tool surfaces + GameSession behavior
```

**State-sync note:** in Phase 3 each server owns its own `GameSession` so its
tools are functional and independently testable. Driving one shared board
across both servers (mutual position validation) is the **orchestrator's** job
in Phase 4.

---

## Architecture

```mermaid
flowchart TD
    CFG[config.json] --> LOADER[config_loader]
    LOADER --> ENGINE

    subgraph ENGINE[Engine - true state S]
        BOARD[board.py]
        RULES[rules.py]
        SCORE[scoring.py]
        LOOP[game_loop.py]
    end

    ENGINE --> OBS[observation.py<br/>partial view Ωᵢ]
    JOKER[joker.py<br/>optional false signal] -.-> OBS

    OBS --> ORCH[orchestrator.py<br/>MCP client + LLM]
    LLM[LLM backend<br/>cloud API / Ollama / hybrid] <--> ORCH

    ORCH <-->|Tool Call / NL messages| COP[cop_server.py<br/>FastMCP - tools only]
    ORCH <-->|Tool Call / NL messages| THIEF[thief_server.py<br/>FastMCP - tools only]

    COP --> ENGINE
    THIEF --> ENGINE

    SCORE --> REPORT[report_builder.py]
    REPORT --> JSON[(results/reports/<br/>game_report.json)]
    REPORT -.optional.-> GMAIL[gmail_sender.py<br/>Gmail API]
    ENGINE -.optional.-> GUI[dashboard.py]
```

Key separation: the **LLM lives in the client** (`orchestrator.py`); the two
**MCP servers expose tools only** and never run an LLM. The engine holds the
only true state; agents see only their partial observation.

See `plan.md` for the full folder structure and data flow.

---

## Current Folder Structure (Phase 3)

The engine, local simulation, and the two MCP servers are implemented. The
orchestrator/LLM client, GUI, and reporting-to-Gmail arrive in later phases per
`plan.md`.

```
AI_Agents_Hw6/
├── README.md                 # this overview
├── prd.md · plan.md · todo.md# requirements · architecture · checklist
├── config.json               # ALL parameters (no hard-coding)
├── requirements.txt
├── src/
│   ├── main.py               # Phase 2 CLI: runs the local simulation
│   ├── config_loader.py      # load + validate config.json
│   ├── engine/
│   │   ├── board.py          # grid + true state S
│   │   ├── rules.py          # legal moves (diagonal), capture, barriers
│   │   ├── observation.py    # partial view Ωᵢ (+ Joker injection point)
│   │   ├── scoring.py        # scoring table + accumulated totals
│   │   └── game_loop.py      # sub-game + 6-game series driver
│   ├── policies/
│   │   ├── common.py         # shared legal-move helper
│   │   ├── cop_policy.py     # deterministic greedy pursuit + barriers
│   │   └── thief_policy.py   # deterministic evasion
│   ├── mcp/                  # Phase 3: FastMCP servers (tools only, no LLM)
│   │   ├── session.py        # FastMCP loader + GameSession (wraps engine)
│   │   ├── cop_server.py     # Cop tools over MCP
│   │   └── thief_server.py   # Thief tools over MCP
│   ├── joker/joker.py        # Joker data hooks (disabled by default)
│   ├── reporting/report_builder.py  # build final_report.json
│   └── util/logging_util.py  # JSONL trace writer
├── tests/                    # test_rules · test_scoring · test_observation
│   └── ...                   # test_game_loop · test_skeleton · test_mcp_servers
└── results/
    ├── logs/game_log.jsonl       # per-move trace (generated)
    ├── reports/final_report.json # series summary (generated)
    └── plots/                    # optional visualizations (later phase)
```

## Run Command

```bash
python -m src.main
```

This runs the full local simulation (6 sub-games) and writes
`results/logs/game_log.jsonl` and `results/reports/final_report.json`.

## MCP Server Commands (Phase 3 — implemented)

```bash
# Start the two MCP servers (separate localhost ports, tools only, no LLM)
python -m src.mcp.cop_server   --config config.json   # localhost:8001
python -m src.mcp.thief_server --config config.json   # localhost:8002
```

## Planned CLI Commands (later phases)

> These commands are **planned**, not yet implemented (there is no
> orchestrator, LLM, GUI, or Gmail yet).

```bash
# Run a full game (6 sub-games) via the orchestrator / MCP client
python -m src.client.orchestrator --config config.json

# Run a single sanity-check sub-game on a smaller grid
python -m src.client.orchestrator --config config.json --grid 2x2 --games 1

# Enable the optional Joker Protocol
python -m src.client.orchestrator --config config.json --joker

# Build the JSON report only (from the latest run)
python -m src.reporting.report_builder --out results/reports/game_report.json

# Optionally email the report via the Gmail API
python -m src.reporting.gmail_sender --report results/reports/game_report.json

# Run unit tests
pytest tests/
```

---

## Current Status

**Phase 3 — MCP server layer.** On top of the Phase 2 engine, two independent
FastMCP servers now expose the agent tools: `src/mcp/cop_server.py`
(`observe_board`, `receive_message`, `send_message`, `move`, `place_barrier`,
`get_score`) and `src/mcp/thief_server.py` (same, with `use_joker_card` in
place of `place_barrier`). Both wrap the existing engine through
`src/mcp/session.py` — the engine is not rewritten. The servers are **tools
only**; no LLM runs in them. `create_server()` builds but never runs the
server, and FastMCP is imported lazily so the modules import cleanly even when
FastMCP is not installed (`create_server()` then fails with a clear
`pip install mcp` / `pip install fastmcp` message). `pytest tests/` (28 tests)
covers the Phase 2 engine plus the new tool surfaces and `GameSession`
behavior. Every Python file stays under 150 lines.

**Current limitations:** **no LLM calls yet, no orchestrator/client yet, no GUI
yet, and no Gmail sending yet.** MCP host/port settings are **local
`localhost` URLs only** — no cloud URLs are configured or faked. Reported
outcomes come only from real runs (see *Observed baseline result* above);
nothing is invented.

---

## Repository Documents

| File | Purpose |
|------|---------|
| `prd.md` | Product requirements: goal, rules, Joker Protocol, evaluation, deliverables |
| `plan.md` | Architecture, folder structure, data/execution flow, testing, submission |
| `todo.md` | Phased checklist (documentation → skeleton → engine → … → submission) |
| `README.md` | This overview |
