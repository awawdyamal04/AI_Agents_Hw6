# PRD — MCP Chase: Joker Protocol

**Course:** Orchestration of AI Agents
**Assignment:** EX06 — Dual AI Agent Conversation via MCP Servers
**Project name:** MCP Chase: Joker Protocol
**Status:** Phase 0 — documentation only (no code yet)

---

## 1. Project Title

**MCP Chase: Joker Protocol** — a dual autonomous AI-agent pursuit game
(Cop vs. Thief) played over two independent MCP servers, communicating in
free natural language under partial observation.

---

## 2. Assignment Goal

The goal of EX06 is **orchestration**, not winning. The graded value is the
ability to stand up **two autonomous AI agents** — a *Cop* and a *Thief* —
that:

1. **Decipher** each other's natural-language messages.
2. **Infer** the opponent's location from **partial observation**.
3. **Translate** those inferences into concrete moves on a grid.

Each agent runs behind its **own separate MCP server**. The agents talk to
each other in **free natural language** (not a rigid numeric protocol). The
measure of success is that the orchestration pipeline runs end-to-end — from
initialization through the automatic JSON report — **fully autonomously, with
no human intervention**. The game outcome and the strategy quality are *not*
the primary grading criteria.

---

## 3. Exact Problem Definition

Two agents play a turn-based chase on a 2-D grid (default 5×5).

- The **Thief** tries to survive; the **Cop** tries to capture.
- Neither agent has full visibility of the other — the world is **partially
  observable**.
- Agents exchange **natural-language messages** each turn (intentions,
  observations, or deliberate deception) and act on their interpretation.

The problem is formally modeled as a **Dec-POMDP**
(Decentralized Partially Observable Markov Decision Process):

```
⟨ n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ ⟩
```

| Symbol | Meaning in this project |
|--------|-------------------------|
| `n`    | Number of agents = 2 (Cop, Thief) |
| `S`    | State space: positions of both agents + barrier cells |
| `{Aᵢ}` | Actions per agent: move (incl. diagonal) or, for the Cop, place a barrier |
| `P`    | Transition function: how a chosen action changes the board state |
| `R`    | Reward / scoring function (see §7) |
| `{Ωᵢ}` | Partial-observation space available to each agent |
| `O`    | Observation function mapping true state → each agent's observation |
| `γ`    | Discount factor (used only if optional Q-Learning is added) |

The **Joker Protocol** (§8) is an optional, principled extension of the
observation function `O`.

---

## 4. Inputs

- **`config.json`** — all runtime parameters (no hard-coding):
  - `grid_size` (default `[5, 5]`)
  - `max_moves` (default `25` per sub-game)
  - `num_games` (default `6` sub-games per full game)
  - `max_barriers` (default `5`, Cop only)
  - `scoring.cop_win` (`20`), `scoring.thief_win` (`10`),
    `scoring.cop_loss` (`5`), `scoring.thief_loss` (`5`)
  - Optional flags: `joker_enabled`, `llm_backend`, `gmail_enabled`
- **LLM backend** — one of: cloud API key (OpenAI / Anthropic / Gemini),
  local Ollama (secured tunnel), or hybrid (local LLM, cloud MCP).
- **Group metadata** — group name, students, GitHub repo URL, MCP server URLs.
- **Gmail OAuth client secret** — optional, only for automatic reporting.

---

## 5. Outputs

- **Live game trace** — per-move natural-language dialogue + board state,
  written to `results/logs/`.
- **Internal Game JSON report** — `results/reports/game_report.json`, the
  structured summary of all 6 sub-games (schema in §9 below).
- **Optional Inter-Group Bonus JSON report** — for the bonus tournament.
- **Optional automatic email** — the Cop agent emails the JSON report to
  `rmisegal+uoh26b@gmail.com` via the Gmail API. The email body contains
  **only** the structured JSON (no free text).
- **Optional GUI / dashboard** — visual playback of agent movement, barriers,
  and (if used) the Q-Table.

---

## 6. Required Models / Tools

| Category | Requirement |
|----------|-------------|
| **MCP framework** | `FastMCP` — two separate MCP servers (Cop, Thief) |
| **LLM** | Cloud API *or* local Ollama *or* hybrid; the LLM lives in the **client**, never inside the MCP server |
| **Orchestrator** | MCP **client** (game engine) that manages the dialogue and calls MCP tools |
| **Config** | `config.json` / `config.yaml` — mandatory, no hard-coded parameters |
| **Reporting** | JSON report; optional Gmail API (Google API Client) |
| **Deployment** | Local (`localhost`, separate ports) → cloud (e.g. Prefect Cloud) |
| **Security** | Token-based auth (revocable), firewall/tunnel for cloud MCP URLs |
| **Strategy (optional)** | Heuristic / Manhattan distance / decision tree / tabular Q-Learning |

---

## 7. Game Rules

### 7.1 Structure (two levels)

- **Sub-game:** one pursuit round, up to **25 moves**. Turn-based; the Thief
  usually moves first, then the Cop, repeating. Each move a player either
  changes position or performs a special action.
- **Game:** a full series of **6 consecutive sub-games**. Results accumulate
  and are reported together at the end.

In a full game a group plays **3 sub-games as Cop** and **3 as Thief**.

### 7.2 Board

- 2-D grid, default **5×5**, driven entirely by `config.json` (generic
  architecture; grid size must be changeable — no hard-coding).
- Every cell has coordinates. Cop and Thief start at board positions
  (random or strategic).
- Movement is allowed in all directions, **including diagonals**.
- The board is a **state machine**: each step changes the board state.

### 7.3 Win conditions & barriers

- **Cop wins:** the Cop lands on exactly the Thief's cell (capture).
- **Thief wins:** the Thief survives 25 moves without the Cop landing on its
  cell.
- **Barriers:** as an alternative action to moving, the Cop may place a
  **barrier** on its current cell. That cell then becomes **impassable** to
  the Thief (and behaves like a wall / board edge). The Cop is limited to a
  maximum of **5 barriers per sub-game**. The Thief cannot place barriers.

### 7.4 Scoring (per sub-game)

| Sub-game result | Cop score | Thief score |
|-----------------|-----------|-------------|
| Cop wins        | 20        | 5           |
| Thief wins      | 5         | 10          |

Maximum possible score for a group in a full game = **90**
(`3×20` as Cop + `3×10` as Thief). Minimum = **30**.

### 7.5 Technical loss

A sub-game that fails to complete due to a technical fault is **void** and
must be re-run so that a full set of **6 valid sub-games** is achieved.

---

## 8. Joker Protocol — Optional Creative Extension

The **Joker Protocol** is our optional creative extension. It is strictly
**additive** and off by default (`joker_enabled: false`).

**Baseline guarantee:** when disabled, the project follows EX06 exactly.

**Rule:** the **winner of a sub-game** receives **one Joker Card** to use in
the **next sub-game**. When played, the Joker Card **injects one plausible
false observation signal** into the opponent's partial observation for a
single turn.

**Hard boundaries (what the Joker must NOT do):**

- It must **not** create a physical second Thief.
- It must **not** teleport any agent.
- It must **not** change the scoring table.
- It must **not** replace or override any baseline rule.

**Why it is principled:** the game is already a Dec-POMDP with partial
observation, and natural-language deception is already permitted. The Joker
is therefore modeled as a one-shot perturbation of the **observation function
`O`** — it emits a plausible-but-false observation into `Ωᵢ` for one turn. It
touches only the observation layer, leaving true state `S`, transitions `P`,
and rewards `R` untouched.

---

## 9. JSON Report Schemas

### 9.1 Internal Game JSON (mandatory)

```json
{
  "group_name": "Team-Alpha",
  "students": [],
  "github_repo": "https://github.com/team-alpha/mcp-chase-joker",
  "cop_mcp_url": "https://cop-mcp-alpha.prefect.run",
  "thief_mcp_url": "https://thief-mcp-alpha.prefect.run",
  "timezone": "Asia/Jerusalem",
  "sub_games": [],
  "totals": { "cop": 90, "thief": 40 }
}
```

### 9.2 Inter-Group Bonus JSON (optional)

Contains `report_type`, both groups' names, both GitHub repos, all four MCP
URLs (Cop + Thief per group), `students_group_1/2`, `sub_games`,
`totals_by_group`, `bonus_claim`, and `mutual_agreement`.

---

## 10. Evaluation Method

1. **Orchestration works end-to-end** — two MCP servers + client run a full
   6-sub-game series autonomously.
2. **Natural-language dialogue** — agents genuinely exchange free-text
   messages (not numeric coordinates) and act on interpretation.
3. **Partial observation respected** — neither agent sees full state.
4. **Correct rules & scoring** — capture, survival, barriers, and the scoring
   table match §7.
5. **Structured JSON report** produced (and optionally emailed).
6. **Scientific README** — Dec-POMDP formalization + orchestration analysis.
7. **Progressive sanity checks** pass (2×2 → 3×3 → 4×4 → 5×5).

---

## 11. Success Criteria

- ✅ Two independent MCP servers (Cop, Thief) run and validate positions.
- ✅ Client/LLM separation: the LLM is in the client, the MCP server exposes
  tools only.
- ✅ A full game of 6 sub-games completes locally on `localhost`.
- ✅ Free natural-language protocol between the agents.
- ✅ Correct win detection, barrier logic, and scoring.
- ✅ Valid Internal Game JSON report generated.
- ✅ All Python files stay under **150 lines**.
- ✅ Baseline mode passes with the Joker Protocol disabled.
- ⭐ Optional: cloud deployment, Gmail API report, GUI, Q-Learning, bonus game.

---

## 12. Final Deliverables

1. **Public GitHub repository** with all source code under `src/`.
2. **`README.md`** in the repo root — scientific, Dec-POMDP formalization,
   orchestration analysis, architecture diagram, CLI commands.
3. **`config.json`** — all parameters, no hard-coding.
4. **Internal Game JSON report** in `results/`.
5. **This documentation set** — `prd.md`, `plan.md`, `todo.md`, `README.md`.
6. ⭐ Optional: Gmail API reporting, GUI, and the Inter-Group Bonus report.
