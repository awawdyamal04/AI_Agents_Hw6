"""Phase 6 — Gmail final-report delivery layer (safe by default).

Loads the structured ``results/reports/final_report.json`` produced by
``python -m src.main`` and prepares an email that carries it (as a JSON
attachment) to the course recipient.

Safety model:
- **Dry-run is the default.** It validates the report, builds the full email
  payload/metadata, and writes ``results/reports/email_dry_run.json`` WITHOUT
  ever contacting the Gmail API.
- **Real send happens only with an explicit ``--send`` flag** and real OAuth
  credentials. If credentials are missing the run fails clearly with setup
  instructions — success is never faked.

No credentials, tokens, or API keys are hard-coded. The recipient comes from
``config.json`` (``reporting.gmail_recipient``); credential/token paths come
from local files or environment variables. The normal project run is still
``python -m src.main`` — this layer never runs the game.
"""
