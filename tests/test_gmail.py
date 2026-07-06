"""Phase 6 tests: the safe Gmail delivery layer.

Covers the message builder on a sample report, that dry-run writes the expected
summary WITHOUT contacting Gmail, that a missing report fails clearly, and that
the real send path refuses to run when OAuth credentials are absent (it never
fakes success).
"""

from __future__ import annotations

import json

import pytest

from src.gmail import message_builder as mb
from src.gmail.message_builder import ReportNotFoundError, load_report
from src.gmail.sender import CredentialsMissingError, dry_run, send

SAMPLE = {
    "project_name": "MCP Chase: Joker Protocol",
    "phase": "phase-5-agent-reasoning-layer",
    "grid_size": {"rows": 5, "cols": 5},
    "num_subgames": 6,
    "execution": {"agent_provider": "deterministic"},
    "totals": {"cop": 120, "thief": 30},
}


def _write_report(tmp_path):
    p = tmp_path / "final_report.json"
    p.write_text(json.dumps(SAMPLE), encoding="utf-8")
    return p


# --- message builder ---

def test_build_payload_from_sample_report(tmp_path):
    report_path = _write_report(tmp_path)
    report = load_report(report_path)
    payload = mb.build_payload(report, report_path, mb.DEFAULT_RECIPIENT)

    assert payload["to"] == mb.DEFAULT_RECIPIENT
    assert "120" in payload["subject"] and "30" in payload["subject"]
    assert payload["attachment"]["filename"] == mb.ATTACHMENT_NAME
    assert payload["attachment"]["mime_type"] == "application/json"
    assert payload["attachment"]["size_bytes"] == report_path.stat().st_size


def test_build_mime_carries_json_attachment(tmp_path):
    report_path = _write_report(tmp_path)
    report = load_report(report_path)
    msg = mb.build_mime(report, report_path, "someone@example.com")

    assert msg["To"] == "someone@example.com"
    attachments = [p for p in msg.iter_attachments()]
    assert len(attachments) == 1
    assert attachments[0].get_filename() == mb.ATTACHMENT_NAME
    raw = mb.encode_raw(msg)
    assert isinstance(raw, str) and raw  # base64url, url-safe


# --- dry-run ---

def test_dry_run_writes_summary_and_skips_gmail(tmp_path):
    report_path = _write_report(tmp_path)
    out_path = tmp_path / "email_dry_run.json"
    summary = dry_run(report_path, mb.DEFAULT_RECIPIENT, out_path)

    assert summary["mode"] == "dry-run"
    assert summary["contacted_gmail_api"] is False
    assert out_path.is_file()
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["recipient"] == mb.DEFAULT_RECIPIENT
    assert written["email"]["attachment"]["filename"] == mb.ATTACHMENT_NAME


# --- missing report fails clearly ---

def test_missing_report_fails_clearly(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(ReportNotFoundError) as exc:
        load_report(missing)
    assert "python -m src.main" in str(exc.value)

    with pytest.raises(ReportNotFoundError):
        dry_run(missing, mb.DEFAULT_RECIPIENT, tmp_path / "out.json")


# --- real send refuses without credentials ---

def test_send_refuses_when_credentials_missing(tmp_path):
    report_path = _write_report(tmp_path)
    out_path = tmp_path / "email_send_result.json"
    with pytest.raises(CredentialsMissingError) as exc:
        send(report_path, mb.DEFAULT_RECIPIENT, out_path,
             credentials_path=str(tmp_path / "nope-credentials.json"),
             token_path=str(tmp_path / "nope-token.json"))
    assert "credentials" in str(exc.value).lower()
    assert not out_path.exists()  # no fake success artifact
