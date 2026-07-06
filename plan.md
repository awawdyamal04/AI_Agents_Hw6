# Plan — MCP Chase: Joker Protocol

**Status:** Phase 0 — documentation only. No Python files exist yet.

This plan defines the modular architecture, folder layout, data/execution
flow, MCP client/server separation, reporting, the optional Gmail flow, the
testing strategy, and the GitHub submission plan.

**Global constraint:** every future Python file stays **under 150 lines**.
Source code goes in `src/`; generated outputs go in `results/`.

---

## 1. Modular Architecture

The system is split into small, single-responsibility modules so no file
exceeds 150 lines. Six layers:

1. **Engine** — pure game logic (board, rules, scoring, observation). No LLM,
   no network. Deterministic and unit-testable.
2. **Observation layer** — builds each agent's partial view; hosts the
   optional Joker false-signal injection.
3. **MCP servers** — two independent FastMCP servers (Cop, Thief) exposing
   tools only. They never run an LLM.
4. **Agents** — reasoning + natural-language message generation, backed by an
   LLM client abstraction.
5. **Client / Orchestrator** — the MCP client (game engine driver). Owns the
   dialogue loop, calls MCP tools, holds the LLM.
6. **Reporting** — builds JSON reports and optionally emails them via Gmail.

Optional: **GUI/dashboard** and **strategy (Q-Learning / heuristics)**.

---

## 2. File / Folder Structure

```
mcp-chase-joker-protocol/
├── README.md                 # scientific overview + diagram
├── prd.md                    # product requirements
├── plan.md                   # this file
├── todo.md                   # phased checklist
├── config.json               # ALL parameters (no hard-coding)
├── requirements.txt
├── .env.example              # API keys / OAuth paths (never commit secrets)
├── src/
│   ├── config_loader.py      # load + validate config.json
│   ├── engine/
│   │   ├── board.py          # grid, cells, state machine
│   │   ├── rules.py          # move legality, capture, barriers
│   │   ├── scoring.py        # per sub-game + accumulated totals
│   │   ├── observation.py    # partial view builder
│   │   └── game_loop.py      # sub-game + 6-game series driver
│   ├── mcp/
│   │   ├── cop_server.py     # FastMCP server (Cop tools)
│   │   ├── thief_server.py   # FastMCP server (Thief tools)
│   │   └── tools.py          # shared tool schemas/handlers
│   ├── agents/
│   │   ├── llm_client.py     # backend abstraction (API/Ollama/hybrid)
│   │   ├── cop_agent.py      # cop reasoning + message generation
│   │   ├── thief_agent.py    # thief reasoning + message generation
│   │   └── prompts.py        # prompt templates
│   ├── client/
│   │   └── orchestrator.py   # MCP client, dialogue manager, main entry
│   ├── joker/
│   │   └── joker.py          # Joker card lifecycle + false-signal
│   ├── reporting/
│   │   ├── report_builder.py # build internal / bonus JSON
│   │   └── gmail_sender.py   # Gmail API send (optional)
│   └── gui/
│       └── dashboard.py      # optional visualization
├── results/
│   ├── reports/              # game_report.json
│   └── logs/                 # per-move dialogue + board snapshots
└── tests/
    ├── test_rules.py
    ├── test_scoring.py
    └── test_observation.py
```

If any module risks exceeding 150 lines, it is split further (e.g.
`rules.py` → `rules.py` + `barriers.py`).

---

## 3. Data Flow

```
config.json ──► config_loader ──► engine (board/rules/scoring)
                                        │
                                 true state S
                                        │
                              observation.py ──► partial view Ωᵢ
                                        │              │
                                 (joker.py optional) ──┘  false signal
                                        │
                       orchestrator (MCP client) ── LLM ──► agent message (NL)
                                        │
                              MCP server tool call ──► validated action
                                        │
                                 engine applies action ──► new state S′
                                        │
                        game_loop repeats until sub-game ends
                                        │
                        scoring ──► report_builder ──► JSON
                                        │
                             gmail_sender (optional) ──► email
```

Key rule: the **engine holds the only true state `S`**. Agents receive only
`Ωᵢ` (partial view). The Joker perturbs `Ωᵢ`, never `S`.

---

## 4. Execution Flow

1. `orchestrator.py` loads `config.json` and initializes the engine.
2. Both MCP servers (Cop, Thief) are started on separate `localhost` ports.
3. For each of the **6 sub-games**:
   1. Board is initialized (start positions, barrier count reset).
   2. Loop up to **25 moves**, alternating turns (Thief first, then Cop):
      - Build the active agent's partial observation (+ Joker if held).
      - Agent (via LLM in the client) reads the opponent's last message,
        reasons, and emits a natural-language message + intended action.
      - Orchestrator calls the agent's MCP server tool to validate/apply the
        action against engine rules.
      - Engine updates state; check win/capture/barrier conditions.
   3. Determine sub-game result and apply the scoring table.
   4. If Joker enabled: grant the winner a Joker Card for the next sub-game.
   5. If technical loss: mark void and re-run.
4. Accumulate totals; `report_builder.py` writes the Internal Game JSON.
5. Optionally, the Cop agent triggers `gmail_sender.py` to email the report.

---

## 5. MCP Client / Server Separation

This is the architectural core of EX06.

- **LLM lives in the client**, never in the MCP server or the engine.
- **MCP client = `orchestrator.py`** — manages the dialogue and the game
  logic. It decides when to call a tool (Tool Call), reads results, and feeds
  them back to the LLM.
- **MCP servers = `cop_server.py`, `thief_server.py`** — built with
  `FastMCP`, each exposes **tools only** (validate position, apply move,
  place barrier, send/receive message). They are independent and autonomous.
- The two agents communicate in **free natural language**, not a rigid
  numeric protocol. Internal implementation differences don't matter as long
  as they understand each other.

Deployment progression:

1. **Local:** both servers on `localhost`, separate ports.
2. **Cloud:** lift servers to a public cloud (e.g. Prefect Cloud) after local
   proof, with **token-based auth** (revocable) and firewall/tunnel
   protection on the MCP URLs.

LLM connection options (choose one via config):

- **Cloud API** (recommended, simplest): client sends HTTPS to OpenAI /
  Anthropic / Gemini with an API key.
- **Secured Ollama** exposed via ngrok / Localtonet / Nginx reverse proxy.
- **Hybrid** (recommended for secure local dev): LLM + client stay local;
  only MCP servers go to cloud; client calls them via **outbound HTTPS**.

---

## 6. Reporting Flow

1. `scoring.py` yields per-sub-game and accumulated totals.
2. `report_builder.py` assembles the **Internal Game JSON** (group metadata,
   MCP URLs, timezone `Asia/Jerusalem`, `sub_games`, `totals`).
3. The report body is **structured JSON only** — no free text — so the grader
   can parse it automatically.
4. Written to `results/reports/game_report.json`.
5. Optional **Inter-Group Bonus JSON** built for the bonus tournament
   (both groups, four MCP URLs, `bonus_claim`, `mutual_agreement`).

---

## 7. Gmail Optional Flow

Off by default (`gmail_enabled: false`). When enabled:

1. Use the **Google API Client** (Gmail API) — chosen for reliability over a
   raw SMTP server.
2. Auth is **OAuth token-based**, preferred over username/password:
   - Download the **client secret JSON** from the Google Cloud console.
   - Generate a token on first connection (short-lived, revocable).
   - Store secrets outside git; reference paths via `.env`.
3. On completion of all 6 valid sub-games, the **Cop agent** triggers
   `gmail_sender.py` to send **one** email to `rmisegal+uoh26b@gmail.com`.
4. The email body contains **only** the Internal Game JSON.

---

## 8. Testing Strategy

Progressive **sanity checks** on growing grids (from the assignment):

| Stage | Grid | Goal |
|-------|------|------|
| 1 | 2×2 | Algorithmic sanity; basic pipeline + message transfer |
| 2 | 3×3 / 3×2 | Coordination convergence; hyperparameter tuning; failure detection |
| 3 | 4×4 / 4×3 | Partial-observation ambiguity (start distance > vision radius) |
| 4 | 5×5 | Final run; generate graphs; analyze the full game |

Unit tests (deterministic, no LLM/network):

- `test_rules.py` — move legality, diagonal moves, capture detection,
  barrier placement + `max_barriers` cap, board-edge behavior.
- `test_scoring.py` — scoring table, accumulated totals, min/max (30/90).
- `test_observation.py` — partial view correctness and Joker false-signal
  injection (asserts true state `S` is never mutated).

Integration: local end-to-end run of a full 6-sub-game series before any
cloud deployment.

---

## 9. GitHub Submission Plan

1. Public GitHub repo named `mcp-chase-joker-protocol`.
2. `README.md` in the root — scientific level: Dec-POMDP formalization,
   orchestration-challenge analysis, architecture diagram, CLI commands.
3. All source under `src/`; every file under 150 lines.
4. `config.json` committed; secrets excluded via `.gitignore` / `.env`.
5. `results/` holds the generated JSON report(s).
6. Commit history follows the phase order in `todo.md` (docs → skeleton →
   engine → MCP → agents → Joker → reporting → verification → submit).
7. The repo URL is embedded in the Internal Game JSON (`github_repo`).
