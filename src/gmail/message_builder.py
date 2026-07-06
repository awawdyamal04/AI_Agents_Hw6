"""Build the Gmail email payload from the final JSON report.

Pure/offline: this module never touches the network. It validates that the
report file exists and is valid JSON, then assembles an email that carries the
report as a JSON attachment plus a short human-readable summary in the body.
The same builder is used by both dry-run (metadata only) and real send (which
additionally base64url-encodes the MIME message for the Gmail API).
"""

from __future__ import annotations

import base64
import json
from email.message import EmailMessage
from pathlib import Path

DEFAULT_RECIPIENT = "rmisegal+uoh26b@gmail.com"
ATTACHMENT_NAME = "final_report.json"


class ReportNotFoundError(FileNotFoundError):
    """Raised when the final report is missing or unreadable."""


def load_report(report_path) -> dict:
    """Read + validate the final JSON report, returning the parsed dict.

    Raises ReportNotFoundError if the file is missing and ValueError if it is
    not valid JSON — the caller turns these into clear CLI failures.
    """
    p = Path(report_path)
    if not p.is_file():
        raise ReportNotFoundError(
            f"final report not found: {p}\n"
            "Generate it first with:  python -m src.main")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"final report is not valid JSON ({p}): {exc}")


def build_subject(report: dict) -> str:
    totals = report.get("totals", {})
    name = report.get("project_name", "MCP Chase")
    return (f"{name} — Final Report "
            f"(Cop {totals.get('cop', '?')} / Thief {totals.get('thief', '?')})")


def build_body(report: dict) -> str:
    totals = report.get("totals", {})
    grid = report.get("grid_size", {})
    lines = [
        "Automated final-report delivery for the MCP Chase assignment (EX06).",
        "",
        f"Project : {report.get('project_name', 'MCP Chase')}",
        f"Phase   : {report.get('phase', 'n/a')}",
        f"Grid    : {grid.get('rows', '?')}x{grid.get('cols', '?')}",
        f"Sub-games: {report.get('num_subgames', '?')}",
        f"Provider: {report.get('execution', {}).get('agent_provider', 'n/a')}",
        f"Totals  : Cop {totals.get('cop', '?')} / "
        f"Thief {totals.get('thief', '?')}",
        "",
        "The complete structured report is attached as "
        f"{ATTACHMENT_NAME} (JSON).",
    ]
    return "\n".join(lines)


def build_mime(report: dict, report_path, recipient: str,
               sender: str = "me") -> EmailMessage:
    """Assemble the RFC-5322 email with the JSON report attached."""
    msg = EmailMessage()
    msg["To"] = recipient
    msg["From"] = sender
    msg["Subject"] = build_subject(report)
    msg.set_content(build_body(report))
    data = Path(report_path).read_bytes()
    msg.add_attachment(data, maintype="application", subtype="json",
                       filename=ATTACHMENT_NAME)
    return msg


def build_payload(report: dict, report_path, recipient: str) -> dict:
    """Return email metadata (no encoded body) for dry-run summaries."""
    data = Path(report_path).read_bytes()
    return {
        "to": recipient,
        "subject": build_subject(report),
        "body_preview": build_body(report),
        "attachment": {
            "filename": ATTACHMENT_NAME,
            "mime_type": "application/json",
            "size_bytes": len(data),
            "source_path": str(Path(report_path)),
        },
    }


def encode_raw(msg: EmailMessage) -> str:
    """base64url-encode a MIME message for the Gmail API ``raw`` field."""
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
