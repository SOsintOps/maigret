"""Tests for web-enhanced scanner module: STAB-02, STAB-04."""
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

# Stub out maigret and its transitive deps before importing scanner,
# so the test file works without the full maigret dependency tree installed.
_maigret_stubs = {
    "maigret": MagicMock(),
    "maigret.sites": MagicMock(),
    "maigret.notify": MagicMock(),
    "maigret.result": MagicMock(),
    "maigret.checking": MagicMock(),
    "maigret.report": MagicMock(),
}
for _name, _mod in _maigret_stubs.items():
    sys.modules.setdefault(_name, _mod)

# Provide the sentinel enum value that scanner.py tests against
import enum as _enum
class _FakeStatus(_enum.Enum):
    CLAIMED = "claimed"
sys.modules["maigret.result"].MaigretCheckStatus = _FakeStatus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scanner import _safe_url, generate_export, ScanJob


# --- STAB-02: URL sanitization ---

def test_safe_url_rejects_javascript():
    assert _safe_url("javascript:alert(1)") == ""

def test_safe_url_rejects_data_uri():
    assert _safe_url("data:text/html,<h1>hi</h1>") == ""

def test_safe_url_rejects_vbscript():
    assert _safe_url("vbscript:msgbox") == ""

def test_safe_url_rejects_file():
    assert _safe_url("file:///etc/passwd") == ""

def test_safe_url_allows_https():
    assert _safe_url("https://github.com/user") == "https://github.com/user"

def test_safe_url_allows_http():
    assert _safe_url("http://example.com") == "http://example.com"

def test_safe_url_empty_string():
    assert _safe_url("") == ""

def test_safe_url_none():
    assert _safe_url(None) == ""


# --- STAB-04: Temp file cleanup on exception ---

def test_export_pdf_tmp_cleanup_on_exception():
    """Temp file must not persist when save_pdf_report raises."""
    job = ScanJob(id="test", username="testuser")
    job.status = "done"
    job.general_results = [("testuser", "username", {})]

    leaked_paths = []

    def fake_save_pdf(path, context):
        leaked_paths.append(path)
        raise RuntimeError("simulated pdf failure")

    with patch("scanner.report") as mock_report:
        mock_report.generate_report_context.return_value = {}
        mock_report.save_pdf_report.side_effect = fake_save_pdf
        with pytest.raises(RuntimeError, match="simulated pdf failure"):
            generate_export(job, "pdf")

    for path in leaked_paths:
        assert not os.path.exists(path), f"Leaked temp file: {path}"


def test_export_html_tmp_cleanup_on_exception():
    """Temp file must not persist when save_html_report raises."""
    job = ScanJob(id="test", username="testuser")
    job.status = "done"
    job.general_results = [("testuser", "username", {})]

    leaked_paths = []

    def fake_save_html(path, context):
        leaked_paths.append(path)
        raise RuntimeError("simulated html failure")

    with patch("scanner.report") as mock_report:
        mock_report.generate_report_context.return_value = {}
        mock_report.save_html_report.side_effect = fake_save_html
        with pytest.raises(RuntimeError, match="simulated html failure"):
            generate_export(job, "html")

    for path in leaked_paths:
        assert not os.path.exists(path), f"Leaked temp file: {path}"
