"""Deliver the final report by email — dry-run (default) or real Gmail send.

Dry-run never touches the network: it validates the report, builds the full
payload, and writes a summary. Real send uses the Gmail API over OAuth and
only runs when the caller explicitly asks for it. Credentials/token are read
from local paths or environment variables — never hard-coded — and a missing
credentials file fails loudly with setup instructions rather than faking a send.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.gmail.message_builder import (build_mime, build_payload, encode_raw,
                                       load_report)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

SETUP_INSTRUCTIONS = (
    "Gmail credentials are missing. To enable real sending:\n"
    "  1. In Google Cloud Console create an OAuth 2.0 Client ID (Desktop app)\n"
    "     with the Gmail API enabled. See main-google-api-installtion-guid.pdf.\n"
    "  2. Download the client secret JSON and save it as ./credentials.json\n"
    "     (or set GMAIL_CREDENTIALS_PATH to its location).\n"
    "  3. Run:  python -m src.gmail.cli --send\n"
    "     A browser opens once for consent; the resulting token is cached at\n"
    "     ./token.json (or GMAIL_TOKEN_PATH).\n"
    "  credentials.json and token.json are gitignored and never committed."
)


def resolve_paths(credentials_path=None, token_path=None):
    """Resolve credential/token paths from args, then env, then defaults."""
    cred = (credentials_path or os.environ.get("GMAIL_CREDENTIALS_PATH")
            or "credentials.json")
    token = (token_path or os.environ.get("GMAIL_TOKEN_PATH") or "token.json")
    return Path(cred), Path(token)


def _write_summary(out_path, summary: dict) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                 encoding="utf-8")
    return p


def dry_run(report_path, recipient, out_path) -> dict:
    """Validate + build the email offline and write a dry-run summary."""
    report = load_report(report_path)
    payload = build_payload(report, report_path, recipient)
    summary = {
        "mode": "dry-run",
        "contacted_gmail_api": False,
        "report_path": str(Path(report_path)),
        "recipient": recipient,
        "email": payload,
        "note": ("No email was sent. Re-run with --send and valid OAuth "
                 "credentials to deliver for real."),
    }
    _write_summary(out_path, summary)
    return summary


class CredentialsMissingError(RuntimeError):
    """Raised when real send is requested without OAuth credentials."""


def _load_google():
    """Lazily import the Google client libraries with a clear error."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise CredentialsMissingError(
            "Google API libraries are not installed. Install them with:\n"
            "  pip install google-api-python-client google-auth-oauthlib\n"
            f"(import error: {exc})")
    return Request, Credentials, InstalledAppFlow, build


def _get_credentials(cred_path: Path, token_path: Path):
    Request, Credentials, InstalledAppFlow, _ = _load_google()
    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not cred_path.is_file():
            raise CredentialsMissingError(SETUP_INSTRUCTIONS)
        flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
        creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def send(report_path, recipient, out_path,
         credentials_path=None, token_path=None) -> dict:
    """Send the report via the Gmail API. Never fakes success."""
    report = load_report(report_path)
    cred_path, tok_path = resolve_paths(credentials_path, token_path)
    if not cred_path.is_file() and not tok_path.is_file():
        raise CredentialsMissingError(SETUP_INSTRUCTIONS)

    _, _, _, build = _load_google()
    creds = _get_credentials(cred_path, tok_path)
    service = build("gmail", "v1", credentials=creds)
    msg = build_mime(report, report_path, recipient)
    sent = service.users().messages().send(
        userId="me", body={"raw": encode_raw(msg)}).execute()

    summary = {
        "mode": "send",
        "contacted_gmail_api": True,
        "report_path": str(Path(report_path)),
        "recipient": recipient,
        "message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "label_ids": sent.get("labelIds"),
        "status": "sent",
    }
    _write_summary(out_path, summary)
    return summary
