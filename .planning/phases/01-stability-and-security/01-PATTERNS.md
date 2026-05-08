# Phase 1: Stability and Security - Pattern Map

**Mapped:** 2026-05-08
**Files analyzed:** 3 source files (2 modified + 1 config) + 2 new test files
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `web-enhanced/server.py` | controller | request-response + streaming | `web-enhanced/server.py` (self — in-place edits) | self |
| `web-enhanced/scanner.py` | service | batch + file-I/O | `web-enhanced/scanner.py` (self — in-place edits) | self |
| `web-enhanced/requirements.txt` | config | n/a | `web-enhanced/requirements.txt` (self) | self |
| `web-enhanced/tests/test_server.py` | test | request-response + streaming | `tests/test_web.py` | role-match |
| `web-enhanced/tests/test_scanner.py` | test | batch + file-I/O | `tests/test_report.py` | role-match |

---

## Pattern Assignments

### `web-enhanced/server.py` — Fix 1: asyncio Task GC (STAB-03)

**Location of bug:** lines 58–65 (`start_scan` route)

**Current buggy pattern** (lines 52–67):
```python
@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    job_id = str(uuid.uuid4())[:8]
    job = ScanJob(id=job_id, username=req.username)
    jobs[job_id] = job

    asyncio.create_task(run_scan(          # <-- return value discarded; GC can collect
        job,
        top_sites=req.top_sites,
        timeout=req.timeout,
        tags=req.tags,
        excluded_tags=req.excluded_tags,
        recursive=req.recursive,
    ))

    return {"id": job_id, "username": req.username, "status": "started"}
```

**Fixed pattern — add module-level set near line 18 (after `jobs` dict), rewrite task creation in `start_scan`:**
```python
# After line 18 — strong reference to prevent GC
_background_tasks: set[asyncio.Task] = set()

# Inside start_scan() — replace the bare create_task call:
task = asyncio.create_task(run_scan(
    job,
    top_sites=req.top_sites,
    timeout=req.timeout,
    tags=req.tags,
    excluded_tags=req.excluded_tags,
    recursive=req.recursive,
))
_background_tasks.add(task)
task.add_done_callback(_background_tasks.discard)
```

---

### `web-enhanced/server.py` — Fix 2: SSE Migration (BACK-01, STAB-01)

**Location of bug:** lines 1–14 (imports), lines 70–96 (`scan_progress` route)

**Current import block** (lines 7–9 and line 12):
```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, StreamingResponse
```

**Fixed import block — replace `StreamingResponse` with SSE imports:**
```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.sse import EventSourceResponse, ServerSentEvent
from collections.abc import AsyncIterable
```

**Current buggy `scan_progress` handler** (lines 70–96):
```python
@app.get("/api/scan/{job_id}/progress")
async def scan_progress(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    async def event_stream():
        while True:
            try:
                event = await asyncio.wait_for(job.queue.get(), timeout=60)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue

            if event.get("type") == "done":
                yield f"data: {json.dumps({'type': 'done', 'found': job.progress.found})}\n\n"
                break
            elif event.get("type") == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': event.get('message', 'Unknown error')})}\n\n"
                break
            else:
                job.progress.completed = event["completed"]
                job.progress.total = event["total"]
                job.progress.found = event["found"]
                yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**Fixed pattern — replace entire `scan_progress` function:**
```python
@app.get("/api/scan/{job_id}/progress")
async def scan_progress(job_id: str) -> EventSourceResponse:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    async def event_stream() -> AsyncIterable[ServerSentEvent]:
        while True:
            try:
                event = await asyncio.wait_for(job.queue.get(), timeout=60)
            except asyncio.TimeoutError:
                continue  # EventSourceResponse sends its own keep-alive ping every 15s

            if event.get("type") in ("done", "error"):
                yield ServerSentEvent(data=json.dumps(event), event=event["type"])
                break
            else:
                job.progress.completed = event["completed"]
                job.progress.total = event["total"]
                job.progress.found = event["found"]
                yield ServerSentEvent(data=json.dumps(event))

    return EventSourceResponse(event_stream())
```

**Key behavior difference:** `EventSourceResponse` throws `GeneratorExit` into the async generator when the client disconnects (D-01 compliance). The `_background_tasks` set ensures `run_scan` continues independently. Do NOT add a `try/except GeneratorExit` block — let it propagate normally.

---

### `web-enhanced/scanner.py` — Fix 3: Temp File Cleanup (STAB-04)

**Location of bugs:** lines 237–246 (pdf branch) and lines 248–257 (html branch)

**Current buggy pdf pattern** (lines 237–246):
```python
elif fmt == "pdf":
    import tempfile
    context = report.generate_report_context(job.general_results)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_path = f.name
    report.save_pdf_report(tmp_path, context)   # raises → tmp_path leaks
    with open(tmp_path, "rb") as f:
        content = f.read()
    os.unlink(tmp_path)                          # never reached on exception
    return content, "application/pdf", f"{username}-maigret.pdf"
```

**Fixed pdf pattern — wrap in try/finally:**
```python
elif fmt == "pdf":
    import tempfile
    context = report.generate_report_context(job.general_results)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name
        report.save_pdf_report(tmp_path, context)
        with open(tmp_path, "rb") as f:
            content = f.read()
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return content, "application/pdf", f"{username}-maigret.pdf"
```

**Current buggy html pattern** (lines 248–257):
```python
elif fmt == "html":
    import tempfile
    context = report.generate_report_context(job.general_results)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        tmp_path = f.name
    report.save_html_report(tmp_path, context)   # raises → tmp_path leaks
    with open(tmp_path, "r") as f:
        content = f.read().encode()
    os.unlink(tmp_path)                           # never reached on exception
    return content, "text/html", f"{username}-maigret.html"
```

**Fixed html pattern — same try/finally structure:**
```python
elif fmt == "html":
    import tempfile
    context = report.generate_report_context(job.general_results)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            tmp_path = f.name
        report.save_html_report(tmp_path, context)
        with open(tmp_path, "r") as f:
            content = f.read().encode()
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return content, "text/html", f"{username}-maigret.html"
```

---

### `web-enhanced/scanner.py` — Fix 4: XSS URL Sanitization (STAB-02)

**Location of bug:** lines 168–182 (`get_found_profiles` function)

**New helper function — insert before `get_found_profiles` at line 168:**
```python
from urllib.parse import urlparse

def _safe_url(url: str) -> str:
    """Allow only http and https URLs; return empty string for anything else."""
    if not url:
        return ""
    scheme = urlparse(url).scheme.lower()
    return url if scheme in ("http", "https") else ""
```

**The `urlparse` import belongs at the top of scanner.py** alongside the existing stdlib imports (lines 1–9). Replace the deferred `from urllib.parse import urlparse` at the helper with a top-of-file import.

**Current `get_found_profiles`** (lines 168–182):
```python
def get_found_profiles(results: dict) -> list[dict]:
    """Extract claimed profiles from results."""
    profiles = []
    for site_name, data in results.items():
        status = data.get("status")
        if status and status.status == MaigretCheckStatus.CLAIMED:
            profiles.append({
                "site": site_name,
                "url": status.site_url_user,   # <-- unsanitized
                ...
            })
    return sorted(profiles, key=lambda p: p["site"].lower())
```

**Fixed `get_found_profiles` — change the `url` field only:**
```python
profiles.append({
    "site": site_name,
    "url": _safe_url(status.site_url_user),   # sanitized: http/https only
    "tags": list(status.tags) if status.tags else [],
    "response_time": round(status.query_time, 2) if status.query_time else None,
    "http_status": data.get("http_status"),
    "ids_data": status.ids_data or {},
})
```

---

### `web-enhanced/requirements.txt` — Fix 5: Dependency Pin (BACK-02)

**Current file** (lines 1–4):
```text
fastapi>=0.115.0
uvicorn>=0.34.0
maigret>=0.6.0
sse-starlette>=2.0.0
```

**Fixed file — upgrade fastapi floor, remove sse-starlette:**
```text
fastapi>=0.135.1
uvicorn>=0.34.0
maigret>=0.6.0
```

---

### `web-enhanced/tests/test_server.py` (new test file)

**Analog:** `tests/test_web.py` (lines 1–173)

**Test file structure — copy from analog:**

*Imports pattern* (from `tests/test_web.py` lines 1–17):
```python
"""Tests for web-enhanced FastAPI server: STAB-01, STAB-03, BACK-01."""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from fastapi.sse import EventSourceResponse

# Import the app and shared state
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from server import app, jobs, _background_tasks
from scanner import ScanJob
```

*Fixture pattern* (from `tests/test_web.py` lines 34–51 — `web_app` and `client` fixtures):
```python
@pytest.fixture(autouse=True)
def clear_state():
    """Reset module-level state between tests."""
    jobs.clear()
    _background_tasks.clear()
    yield
    jobs.clear()
    _background_tasks.clear()

@pytest.fixture
def client():
    return TestClient(app)
```

*Test naming and assertion pattern* (from `tests/test_web.py` — functions start at line 54):
```python
def test_task_stored_in_set(client, monkeypatch):
    """STAB-03: start_scan must add task to _background_tasks."""
    # monkeypatch run_scan to a no-op coroutine
    ...
    assert len(_background_tasks) == 1

def test_progress_uses_event_source_response(client):
    """BACK-01: scan_progress endpoint returns EventSourceResponse."""
    ...
    # Verify response type, not just content-type header
    assert isinstance(response, EventSourceResponse)

def test_sse_disconnect(client):
    """STAB-01: SSE generator exits cleanly on client disconnect."""
    ...
```

*Async test pattern* (from `tests/test_checking.py` lines 29–39):
```python
@pytest.mark.asyncio
async def test_sse_disconnect_allows_scan_to_continue():
    # asyncio_mode=auto in pytest.ini means @pytest.mark.asyncio can be omitted,
    # but explicit marking is clearer for async tests
    ...
```

**Note:** `asyncio_mode=auto` is set in project's `pytest.ini` (line 7) — async test functions run without needing `@pytest.mark.asyncio`.

---

### `web-enhanced/tests/test_scanner.py` (new test file)

**Analog:** `tests/test_report.py` (lines 1–686)

*Imports pattern* (from `tests/test_report.py` lines 1–31):
```python
"""Tests for web-enhanced scanner module: STAB-02, STAB-04."""
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scanner import _safe_url, get_found_profiles, generate_export, ScanJob
from maigret.result import MaigretCheckStatus
```

*Test fixture pattern for scanner* (from `tests/test_report.py` lines 33–55 — EXAMPLE_RESULTS dict):
```python
# Minimal results dict for testing get_found_profiles
CLAIMED_RESULT = MaigretCheckResult('user', 'GitHub', 'https://github.com/user', MaigretCheckStatus.CLAIMED)
CLAIMED_RESULT.tags = ['code']
CLAIMED_RESULT.ids_data = {}
CLAIMED_RESULT.query_time = 0.5

EXAMPLE_RESULTS = {
    'GitHub': {
        'status': CLAIMED_RESULT,
        'http_status': 200,
    }
}
```

*Unit test for URL sanitization* (STAB-02):
```python
def test_safe_url_rejects_javascript():
    assert _safe_url("javascript:alert(1)") == ""

def test_safe_url_rejects_data_uri():
    assert _safe_url("data:text/html,<h1>hi</h1>") == ""

def test_safe_url_allows_https():
    assert _safe_url("https://github.com/user") == "https://github.com/user"

def test_safe_url_allows_http():
    assert _safe_url("http://example.com") == "http://example.com"

def test_safe_url_empty_string():
    assert _safe_url("") == ""
```

*Unit test for temp file cleanup* (STAB-04 — follows pattern from `tests/test_report.py` lines 409–416):
```python
def test_export_tmp_cleanup_on_exception(tmp_path):
    """STAB-04: temp file must not persist when save_pdf_report raises."""
    job = ScanJob(id="test", username="testuser", status="done")
    job.general_results = [("testuser", "username", {})]

    leaked_paths = []

    def fake_save_pdf(path, context):
        leaked_paths.append(path)
        raise RuntimeError("simulated pdf failure")

    with patch("scanner.report.save_pdf_report", fake_save_pdf):
        with pytest.raises(RuntimeError):
            generate_export(job, "pdf")

    # The file must have been cleaned up despite the exception
    for path in leaked_paths:
        assert not os.path.exists(path), f"Leaked temp file: {path}"
```

---

### `web-enhanced/tests/__init__.py` (new, empty package marker)

No pattern needed. Empty file to make `web-enhanced/tests/` a Python package.

---

## Shared Patterns

### asyncio Test Mode
**Source:** `/Users/sitticus/github/maigret/pytest.ini` (line 7)
**Apply to:** All async test functions in `web-enhanced/tests/`
```ini
asyncio_mode=auto
```
This setting applies project-wide. Async def test functions execute automatically without `@pytest.mark.asyncio`. A separate `pytest.ini` or `pyproject.toml` config may be needed inside `web-enhanced/` if tests are run from that subdirectory.

### Monkeypatch for External Calls
**Source:** `tests/test_web.py` lines 68–70, 100–111, 152–165
**Apply to:** Any test that calls `start_scan` (which internally calls `run_scan` → maigret core)
```python
# Pattern: replace slow/external async functions with no-op coroutines
async def fake_run_scan(job, **kwargs):
    job.status = "done"

monkeypatch.setattr("server.run_scan", fake_run_scan)
```

### State Reset Between Tests
**Source:** `tests/test_web.py` lines 40–46 (`web_app` fixture with `clear()` calls)
**Apply to:** All test functions touching `jobs` or `_background_tasks` module globals
```python
@pytest.fixture(autouse=True)
def clear_state():
    jobs.clear()
    _background_tasks.clear()
    yield
    jobs.clear()
    _background_tasks.clear()
```

### Error Type in try/except Blocks
**Source:** `web-enhanced/scanner.py` lines 158–161 (existing pattern in `run_scan`)
```python
except Exception as e:
    job.status = "error"
    job.error = str(e)
```
**Apply to:** Test assertions that check `pytest.raises(RuntimeError)` for export failures.

---

## No Analog Found

No files in this phase lack an analog. All fixes are in-place edits on two well-understood files. Test patterns are covered by the two existing test analogs.

---

## Metadata

**Analog search scope:** `/Users/sitticus/github/maigret/web-enhanced/`, `/Users/sitticus/github/maigret/tests/`
**Files scanned:** 5 source files read in full
**Pattern extraction date:** 2026-05-08
