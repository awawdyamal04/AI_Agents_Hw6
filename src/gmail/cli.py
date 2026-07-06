"""Phase 6 CLI — deliver the final JSON report by email (safe by default).

    python -m src.gmail.cli --dry-run   # default: validate + build, NO send
    python -m src.gmail.cli --send      # real Gmail API send (needs OAuth)

Dry-run is the default even with no flag. The recipient and report path come
from config.json; credential/token paths come from flags or environment
variables (never hard-coded). A real send with missing credentials fails
clearly with setup instructions — success is never faked.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.config_loader import load_config
from src.gmail.message_builder import DEFAULT_RECIPIENT, ReportNotFoundError
from src.gmail.sender import CredentialsMissingError, dry_run, send

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "config.json"


def _resolve(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def _paths(config: dict):
    rep = config.get("reporting", {})
    report = _resolve(rep.get("final_report_path",
                              "results/reports/final_report.json"))
    recipient = rep.get("gmail_recipient", DEFAULT_RECIPIENT)
    dry_out = _resolve("results/reports/email_dry_run.json")
    send_out = _resolve("results/reports/email_send_result.json")
    return report, recipient, dry_out, send_out


def _run_send(args, report, recipient, send_out) -> int:
    try:
        summary = send(report, recipient, send_out,
                       credentials_path=args.credentials, token_path=args.token)
    except CredentialsMissingError as exc:
        print("[gmail] real send aborted — no email was sent.\n")
        print(exc)
        return 2
    print("[gmail] SENT via Gmail API.")
    print(f"  recipient : {summary['recipient']}")
    print(f"  message_id: {summary['message_id']}")
    print(f"  result    : {send_out}")
    return 0


def _run_dry(report, recipient, dry_out) -> int:
    summary = dry_run(report, recipient, dry_out)
    email = summary["email"]
    print("[gmail] DRY-RUN ok — validated report, built email, sent nothing.")
    print(f"  recipient : {email['to']}")
    print(f"  subject   : {email['subject']}")
    print(f"  attachment: {email['attachment']['filename']} "
          f"({email['attachment']['size_bytes']} bytes)")
    print(f"  summary   : {dry_out}")
    print("  To send for real:  python -m src.gmail.cli --send")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="src.gmail.cli",
        description="Deliver the final JSON report by email (dry-run default).")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="Validate + build the email only (default).")
    mode.add_argument("--send", action="store_true",
                      help="Actually send via the Gmail API (needs OAuth).")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH,
                        help="Path to config.json (default: project root).")
    parser.add_argument("--credentials", default=None,
                        help="OAuth client secret path (or GMAIL_CREDENTIALS_PATH).")
    parser.add_argument("--token", default=None,
                        help="Cached token path (or GMAIL_TOKEN_PATH).")
    args = parser.parse_args()

    config = load_config(args.config)
    report, recipient, dry_out, send_out = _paths(config)

    try:
        if args.send:
            return _run_send(args, report, recipient, send_out)
        return _run_dry(report, recipient, dry_out)
    except ReportNotFoundError as exc:
        print(f"[gmail] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
