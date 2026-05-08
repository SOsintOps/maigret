# Phase 1: Stability and Security - Research

**Researched:** 2026-05-08
**Domain:** FastAPI SSE, asyncio task lifecycle, Python XSS sanitization, temp file management
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** When a client disconnects mid-scan, the SSE generator must stop cleanly, but the scan task continues in background. The operator can reconnect and retrieve results via `/api/scan/{id}/results`. Rationale: a page refresh should not kill a 10-minute scan on a local single-user tool.
- **D-02:** No automatic cleanup of completed jobs from the in-memory `jobs` dict. Jobs persist until server restart. Acceptable for local single-user usage. Already tracked as post-milestone concern in STATE.md.

### Claude's Discretion
- **D-03:** XSS sanitization approach — Claude decides where and how to sanitize profile URLs (backend, frontend, or both) and scope of validation (just `javascript:` protocol or stricter http/https-only allowlist). User noted this is a local tool so risk is low, but good practice to close the sink.
- **D-04:** SSE migration strategy — Claude decides whether to adopt a proper EventSourceResponse or keep StreamingResponse with disconnect detection. `sse-starlette` must be removed from requirements.txt regardless.
- **D-05:** asyncio task GC fix — Claude decides implementation (module-level set vs. task ref on job object).
- **D-06:** Temp file cleanup — Claude decides implementation (try/finally vs. context manager).

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STAB-01 | SSE event_stream generator checks for client disconnect and cleans up the asyncio queue | EventSourceResponse generator pattern; Starlette StreamingResponse has `listen_for_disconnect`; generator teardown via GeneratorExit |
| STAB-02 | All href attributes are sanitised against javascript: protocol XSS | Backend allowlist (http/https only) at serialization point in `get_found_profiles()`; frontend JS sanitizer on innerHTML writes |
| STAB-03 | asyncio background tasks are stored in a module-level set to prevent GC cancellation | Official Python docs pattern: `background_tasks = set(); task.add_done_callback(background_tasks.discard)` |
| STAB-04 | Export temp files are cleaned up in a finally block to prevent leaks on exception | `try/finally` or `contextlib.ExitStack` wrapping the temp file lifecycle |
| BACK-01 | Server uses FastAPI native EventSourceResponse instead of manual StreamingResponse | FastAPI >= 0.135.1 ships `fastapi.sse.EventSourceResponse`; current installed 0.128.8 does not — requires upgrade |
| BACK-02 | requirements.txt pins FastAPI >= 0.135.1 and removes sse-starlette dependency | Pin `fastapi>=0.135.1`; remove `sse-starlette>=2.0.0` line |
</phase_requirements>

---

## Summary

Phase 1 is a hardening pass on six discrete bugs in `web-enhanced/server.py` and `web-enhanced/scanner.py`. Each requirement maps to a specific, well-understood Python/FastAPI pattern — no design work is needed, only targeted code edits. The scope is narrow: nothing in `maigret/` core code is touched; all changes are confined to the two web-enhanced source files plus `requirements.txt`.

The single version constraint that requires advance confirmation: **FastAPI must be upgraded from 0.128.8 (currently installed) to >= 0.135.1** to get the native `fastapi.sse.EventSourceResponse`. Without this upgrade, BACK-01 cannot be satisfied using FastAPI's own module. An alternative is to implement a minimal `EventSourceResponse` shim wrapping `StreamingResponse` — but since the requirement explicitly calls out "FastAPI native EventSourceResponse" and `sse-starlette` must be removed, upgrading FastAPI is the correct path. [VERIFIED: fastapi releases page, pip index versions]

The remaining five fixes (STAB-01 through STAB-04, BACK-02) require only standard Python patterns and no new dependencies.

**Primary recommendation:** Upgrade FastAPI to 0.136.1 (latest as of research date), migrate to `from fastapi.sse import EventSourceResponse`, store tasks in a module-level set with `add_done_callback`, add `try/finally` around temp file paths, and sanitize URLs to http/https-only allowlist in `get_found_profiles()`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SSE streaming / disconnect detection | API / Backend (FastAPI) | — | Server-push; client cannot control its own streaming teardown |
| asyncio task lifetime management | API / Backend (server.py) | — | Task references live in module scope or on job object; event loop is backend-owned |
| XSS URL sanitization | API / Backend (scanner.py serializer) | Browser / Client (optional defence-in-depth) | Poisoned URL comes from third-party site data; sanitize at serialization time before it leaves the server |
| Temp file cleanup | API / Backend (scanner.py) | — | File I/O is synchronous in generate_export(); cleanup must happen in the same function's finally block |
| Dependency pinning | Build / Requirements | — | requirements.txt in web-enhanced/ governs the deployed environment |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | >= 0.135.1 (latest: 0.136.1) | Web framework + native SSE | Minimum version shipping `fastapi.sse`; 0.136.1 is latest stable [VERIFIED: pip index versions fastapi; github.com/fastapi/fastapi/releases] |
| starlette | >= 0.40.0 (installed: 0.49.3) | ASGI primitives; StreamingResponse base | FastAPI dependency; installed version is current [VERIFIED: pip3 show starlette] |
| uvicorn | >= 0.34.0 (installed: 0.39.0) | ASGI server | Already in requirements.txt; no change needed [VERIFIED: uvicorn --version] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| contextlib.ExitStack | stdlib | Multi-resource cleanup in finally blocks | When wrapping both pdf and html temp file paths to avoid nested try/finally |
| urllib.parse | stdlib | URL scheme parsing for sanitization | `urllib.parse.urlparse(url).scheme` gives clean scheme string; no import needed beyond stdlib |

### Removed

| Library | Why Removed |
|---------|-------------|
| sse-starlette | Replaced by native `fastapi.sse.EventSourceResponse` in FastAPI >= 0.135.1. Was never actually imported in server.py — listed in requirements.txt but unused. BACK-02 requires its removal. [VERIFIED: grep of server.py shows no import of sse_starlette] |

**Installation / upgrade command:**
```bash
cd web-enhanced
# In requirements.txt: replace fastapi>=0.115.0 with fastapi>=0.135.1
# Remove sse-starlette line
pip install -r requirements.txt --upgrade
```

**Version verification (run before writing Standard Stack table):**
```bash
pip index versions fastapi  # confirmed 0.136.1 latest as of 2026-05-08
```

---

## Architecture Patterns

### System Architecture Diagram

```
Browser (EventSource API)
        |
        | HTTP GET /api/scan/{id}/progress
        |
  FastAPI route handler (server.py)
        |
        | yields ServerSentEvent objects
        |
  EventSourceResponse (fastapi.sse)
        |-- sets Content-Type: text/event-stream
        |-- sends keep-alive ping every 15s
        |-- tears down async generator on client disconnect
        |
  event_stream() async generator
        |-- reads from job.queue (asyncio.Queue)
        |-- exits loop on "done" or "error" event
        |-- exits on GeneratorExit (disconnect teardown)
        |
  asyncio.Queue (per ScanJob)
        ^
        |  (cross-thread push via run_coroutine_threadsafe)
        |
  ProgressNotify.update() (runs in maigret thread)
        ^
        |
  run_scan() asyncio task  <-- held by module-level `_background_tasks` set
        |
  maigret_search() (core scanner)
```

**Disconnect path (D-01):** When client disconnects, FastAPI's EventSourceResponse tears down the async generator by throwing `GeneratorExit` into it. The `event_stream()` generator should handle this (or just not suppress it). The `run_scan` task continues independently because it is owned by `_background_tasks`, not by the generator.

### Recommended Project Structure

No structural changes. All edits are in-place:
```
web-enhanced/
├── server.py        # Fix: task storage, SSE migration
├── scanner.py       # Fix: temp file cleanup, URL sanitization
└── requirements.txt # Fix: upgrade fastapi, remove sse-starlette
```

---

### Pattern 1: asyncio Task GC Prevention (STAB-03)

**What:** Store a strong reference to every `asyncio.create_task()` result to prevent CPython's garbage collector from collecting the task before completion.

**When to use:** Any "fire and forget" task created with `create_task()` where the caller does not `await` it.

**Official recommendation (from Python docs):**
```python
# Source: https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
# Module-level set — strong reference prevents GC
_background_tasks: set[asyncio.Task] = set()

task = asyncio.create_task(run_scan(job, ...))
_background_tasks.add(task)
task.add_done_callback(_background_tasks.discard)
```

**Applied to server.py `start_scan()`:**
```python
# Add near top of server.py, after jobs dict:
_background_tasks: set[asyncio.Task] = set()

# Inside start_scan():
task = asyncio.create_task(run_scan(job, ...))
_background_tasks.add(task)
task.add_done_callback(_background_tasks.discard)
```

The `add_done_callback(discard)` removes the task from the set when it completes, so the set does not grow without bound. [VERIFIED: docs.python.org/3/library/asyncio-task.html]

---

### Pattern 2: FastAPI Native SSE with EventSourceResponse (BACK-01, STAB-01)

**What:** Replace `StreamingResponse` with `fastapi.sse.EventSourceResponse`. Requires FastAPI >= 0.135.1.

**When to use:** Any endpoint that streams text/event-stream data.

**Import and usage:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/server-sent-events/
from fastapi.sse import EventSourceResponse, ServerSentEvent
from collections.abc import AsyncIterable

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
                # EventSourceResponse sends its own keep-alive ping every 15s;
                # this is an additional application-level keepalive if desired.
                # Can yield a comment or simply continue.
                continue

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

**Disconnect handling:** When the client disconnects, FastAPI's EventSourceResponse throws `GeneratorExit` into the async generator. The generator exits cleanly. The `asyncio.Queue` items for that job are left in memory (acceptable per D-02: jobs persist until restart). The `run_scan` task continues because it holds its own reference in `_background_tasks`. [VERIFIED: github.com/fastapi/fastapi/blob/master/fastapi/sse.py, fastapi.tiangolo.com/tutorial/server-sent-events/]

**Alternative (if FastAPI upgrade is blocked):** Keep `StreamingResponse` but add explicit disconnect detection:
```python
# Starlette 0.49.3 StreamingResponse has listen_for_disconnect() built-in
# but the generator approach above cannot directly access `receive`.
# Would require restructuring to use Request object.
# NOT recommended — upgrade FastAPI instead.
```

---

### Pattern 3: Temp File Cleanup with try/finally (STAB-04)

**What:** Wrap temp file path in `try/finally` to guarantee `os.unlink()` runs even on exception.

**When to use:** Any `tempfile.NamedTemporaryFile(delete=False)` that requires manual cleanup.

**Current buggy pattern (scanner.py lines 239-246, 248-256):**
```python
# pdf path — no try/finally:
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
    tmp_path = f.name
report.save_pdf_report(tmp_path, context)  # if this raises, tmp_path leaks
with open(tmp_path, "rb") as f:
    content = f.read()
os.unlink(tmp_path)  # never reached if above raises
```

**Fixed pattern:**
```python
import tempfile, os

# pdf
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

**Alternative — context manager approach (equally valid):**
```python
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as f:
    tmp_path = f.name
    report.save_pdf_report(tmp_path, context)
    f.seek(0)
    content = f.read()
```
Note: `delete=True` with a context manager auto-deletes on `__exit__`. However, on Windows, the file cannot be opened by another process while it is open (the NamedTemporaryFile is still open). Since maigret targets local Linux/macOS, `delete=True` is safe. The `try/finally` pattern is more explicit and portable. [ASSUMED — Windows compatibility assumption; verified delete=False pattern is current code]

---

### Pattern 4: XSS URL Sanitization (STAB-02)

**What:** Reject any URL whose scheme is not `http` or `https` before it is returned to the browser.

**Where:** In `get_found_profiles()` in `scanner.py` — this is the single serialization point before profile URLs leave the server. Adding sanitization here covers all downstream consumers (REST API, exports, graph). Optionally add a JS guard in the frontend as defence-in-depth.

**Recommended implementation (http/https allowlist, not just javascript: blocklist):**
```python
# Source: stdlib urllib.parse
from urllib.parse import urlparse

def _safe_url(url: str) -> str:
    """Return url only if scheme is http or https; otherwise return empty string."""
    if not url:
        return ""
    scheme = urlparse(url).scheme.lower()
    return url if scheme in ("http", "https") else ""
```

Apply in `get_found_profiles()`:
```python
profiles.append({
    "site": site_name,
    "url": _safe_url(status.site_url_user),
    ...
})
```

**Rationale for allowlist over blocklist:** Blocking only `javascript:` still allows `data:`, `vbscript:`, `file:`, and other potentially dangerous schemes. An http/https allowlist is two lines of code and closes all current and future protocol injection vectors. [CITED: OWASP XSS Prevention Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html]

**Frontend defence-in-depth (optional, not required for STAB-02):** In `static/index.html`, wherever profile URLs are written into `href` attributes via JavaScript:
```javascript
function safeHref(url) {
    try {
        const u = new URL(url);
        return (u.protocol === 'http:' || u.protocol === 'https:') ? url : '#';
    } catch { return '#'; }
}
```

---

### Anti-Patterns to Avoid

- **Cancelling the scan task on disconnect:** Decision D-01 locks this out. The `event_stream` generator must NOT hold a reference to the scan task, and must NOT cancel it on `GeneratorExit`. The scan task must be owned exclusively by `_background_tasks`.

- **Using `asyncio.Queue.empty()` to check for events:** `empty()` has a race condition. Always use `await queue.get()` with a timeout.

- **Blocking `javascript:` only in URL sanitization:** Use an http/https allowlist instead. Blocklists miss `data:`, `vbscript:`, etc.

- **Using `sse-starlette` as a shim:** BACK-02 requires removing it. Do not replace it with another third-party SSE library.

- **Using `delete=True` on Windows:** The temp file pattern with `delete=True` has Windows locking issues. Use `try/finally` with `delete=False` for portability.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE response type | Custom StreamingResponse subclass | `fastapi.sse.EventSourceResponse` | Handles keep-alive, Content-Type headers, cache headers, disconnect teardown; available in FastAPI >= 0.135.1 |
| URL scheme validation | Regex against `^javascript:` | `urllib.parse.urlparse().scheme` | Stdlib handles edge cases (uppercase, whitespace prefix); regex is brittle |
| Task cleanup on completion | Manual tracking dict + explicit delete | `task.add_done_callback(set.discard)` | Correct memory lifecycle; runs on both success and exception completion |

---

## Common Pitfalls

### Pitfall 1: asyncio Task Silently Cancelled by GC

**What goes wrong:** `asyncio.create_task(run_scan(...))` returns a `Task` object. If no code holds a strong reference, CPython's GC collects it. The event loop holds only a *weak* reference. The task stops mid-execution with no error logged (Python 3.12+ may log a warning; 3.9 does not).

**Why it happens:** Python's task system relies on the caller maintaining a strong reference for the lifetime of the task. The current `server.py` line 58 discards the return value of `create_task`.

**How to avoid:** Module-level `_background_tasks: set[asyncio.Task] = set()` pattern. Add task immediately after `create_task`, with `add_done_callback(discard)` for automatic cleanup. [VERIFIED: docs.python.org/3/library/asyncio-task.html]

**Warning signs:** Scans that start but never complete; no error in logs; `job.status` stays `"running"` indefinitely.

---

### Pitfall 2: SSE Queue Leak on Client Disconnect

**What goes wrong:** Current `event_stream()` in `server.py` runs an infinite loop reading from `job.queue`. When a client disconnects, `StreamingResponse` stops consuming from the generator, but does not necessarily throw `GeneratorExit` into it immediately. Events pushed by `ProgressNotify` accumulate in the queue. If the browser reconnects, a new `event_stream()` generator is created, but the old one may still be reading from the same queue.

**Why it happens:** `StreamingResponse` in Starlette 0.49.3 uses `anyio.create_task_group` to race `stream_response` vs `listen_for_disconnect`. When disconnect wins, the task group cancels `stream_response`, which throws `GeneratorExit` into the generator. However, the generator's `asyncio.wait_for` call may be mid-flight and the cleanup may not run promptly.

**How to avoid:** `EventSourceResponse` handles the teardown cleanly. Additionally, ensure the generator does not hold external resources (file handles, locks) that need explicit cleanup — the queue is already safe to abandon.

**Warning signs:** Memory growth during many sequential scans; queue depth growing after client has closed the tab.

---

### Pitfall 3: Temp File Leak on Export Exception

**What goes wrong:** `generate_export()` for `pdf` and `html` formats creates a `NamedTemporaryFile(delete=False)`, writes to it, reads it back, then calls `os.unlink()`. If `save_pdf_report()` or `save_html_report()` raises, `os.unlink()` is never reached. The file sits in `/tmp` until the OS cleans temp dirs.

**Why it happens:** No `try/finally` wrapper. The exception propagates past the `os.unlink()` call.

**How to avoid:** Wrap with `try/finally`: set `tmp_path = None`, assign it inside the `with` block, run `os.unlink` in `finally` with a `None` guard.

**Warning signs:** Growing `/tmp` during repeated failed PDF/HTML exports.

---

### Pitfall 4: FastAPI Version Mismatch for `fastapi.sse`

**What goes wrong:** `from fastapi.sse import EventSourceResponse` raises `ModuleNotFoundError` if FastAPI < 0.135.1 is installed. The currently installed version is 0.128.8.

**Why it happens:** `fastapi.sse` was added in 0.135.0 / formally released in 0.135.1. PyPI index shows 0.128.8 as the last release at the time of that installation.

**How to avoid:** Pin `fastapi>=0.135.1` in `requirements.txt`. Run `pip install -r requirements.txt --upgrade` in the `web-enhanced/` directory before running the server.

**Warning signs:** `ModuleNotFoundError: No module named 'fastapi.sse'` at server startup.

---

### Pitfall 5: Reconnect Creates Duplicate Queue Consumer

**What goes wrong (D-01 implementation):** If a client reconnects after disconnecting mid-scan, a new `event_stream()` generator starts reading from `job.queue`. The old generator may still be alive (pending GC). Both generators compete for items from the same queue — events are split between them.

**How to avoid:** The old generator should exit promptly on `GeneratorExit` (which `EventSourceResponse` guarantees). Verify there is no `try/except GeneratorExit: pass` in the generator body that would suppress teardown.

---

## Code Examples

### Complete Fixed `start_scan` (STAB-03)
```python
# Source: docs.python.org/3/library/asyncio-task.html
_background_tasks: set[asyncio.Task] = set()

@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    job_id = str(uuid.uuid4())[:8]
    job = ScanJob(id=job_id, username=req.username)
    jobs[job_id] = job

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

    return {"id": job_id, "username": req.username, "status": "started"}
```

### Complete Fixed `scan_progress` (BACK-01, STAB-01)
```python
# Source: fastapi.tiangolo.com/tutorial/server-sent-events/
from fastapi.sse import EventSourceResponse, ServerSentEvent

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
                continue  # EventSourceResponse sends its own keep-alive ping

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

### Fixed `generate_export` PDF/HTML branches (STAB-04)
```python
# try/finally ensures tmp_path cleanup even on exception
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

### Fixed `get_found_profiles` URL sanitization (STAB-02)
```python
# Source: OWASP XSS Prevention Cheat Sheet; stdlib urllib.parse
from urllib.parse import urlparse

def _safe_url(url: str) -> str:
    """Allow only http and https URLs; return empty string otherwise."""
    if not url:
        return ""
    scheme = urlparse(url).scheme.lower()
    return url if scheme in ("http", "https") else ""

def get_found_profiles(results: dict) -> list[dict]:
    profiles = []
    for site_name, data in results.items():
        status = data.get("status")
        if status and status.status == MaigretCheckStatus.CLAIMED:
            profiles.append({
                "site": site_name,
                "url": _safe_url(status.site_url_user),  # sanitized
                "tags": list(status.tags) if status.tags else [],
                "response_time": round(status.query_time, 2) if status.query_time else None,
                "http_status": data.get("http_status"),
                "ids_data": status.ids_data or {},
            })
    return sorted(profiles, key=lambda p: p["site"].lower())
```

### Fixed `requirements.txt` (BACK-02)
```text
fastapi>=0.135.1
uvicorn>=0.34.0
maigret>=0.6.0
```
(sse-starlette line removed)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `sse-starlette` third-party lib for SSE | `fastapi.sse.EventSourceResponse` native | FastAPI 0.135.0 (released ~2026) | Remove one dependency; gain Pydantic Rust serialization, built-in keep-alive, built-in `X-Accel-Buffering: no` |
| `StreamingResponse(media_type="text/event-stream")` | `EventSourceResponse` with `yield ServerSentEvent(...)` | FastAPI 0.135.0 | Cleaner API; automatic keep-alive pings every 15s |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `delete=True` on NamedTemporaryFile works correctly on macOS/Linux for read-back; Windows has locking issues | Pattern 3 (Temp File) | Low risk: project targets local macOS/Linux; Windows is not a stated target |
| A2 | `sse-starlette` is not imported anywhere in server.py or scanner.py (confirmed by reading both files) | BACK-02 | None — verified by reading files |

---

## Open Questions

1. **FastAPI 0.136.1 vs 0.135.1 — which to pin?**
   - What we know: 0.135.1 is the minimum required for `fastapi.sse`; 0.136.1 is the latest stable as of 2026-05-08.
   - What's unclear: Whether any breaking changes between 0.135.1 and 0.136.1 affect the existing routes.
   - Recommendation: Pin `>=0.135.1` (floor) rather than exact version, so future patch releases install automatically. The planner should choose this floor.

2. **`asyncio.TimeoutError` vs `TimeoutError` (Python 3.11+)**
   - What we know: Python 3.11 aliased `asyncio.TimeoutError` to the builtin `TimeoutError`. The project targets Python 3.10+.
   - What's unclear: The maigret venv Python version in this environment is 3.9.6 (system). Poetry requires 3.10+.
   - Recommendation: Use `asyncio.TimeoutError` to be safe on 3.10+. This is a one-line concern for the implementer.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.9 (system) | Code execution | ✓ | 3.9.6 | — |
| FastAPI 0.135.1+ | BACK-01 | ✗ (0.128.8 installed) | 0.128.8 | Must upgrade; no acceptable fallback |
| Starlette 0.40+ | FastAPI dependency | ✓ | 0.49.3 | — |
| uvicorn | Server | ✓ | 0.39.0 | — |
| urllib.parse | URL sanitization | ✓ | stdlib | — |
| pytest | Test suite | ✗ | not installed | Install via pyproject.toml dev deps |
| httpx | FastAPI TestClient | ✗ | not installed | Install as test dependency |

**Missing dependencies with no fallback:**
- `fastapi>=0.135.1` — must be upgraded; BACK-01 cannot be satisfied without it.

**Missing dependencies with fallback:**
- `pytest`, `httpx`, `pytest-asyncio` — not globally installed, but defined in `pyproject.toml` dev deps. Plan must include an install step before running tests.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >= 8.3.4 (defined in pyproject.toml) |
| Config file | `pytest.ini` at project root (asyncio_mode=auto) |
| Quick run command | `pytest tests/test_server.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STAB-01 | SSE generator exits on client disconnect without leaving orphaned queue reader | unit + integration | `pytest web-enhanced/tests/test_server.py::test_sse_disconnect -x` | ❌ Wave 0 |
| STAB-02 | `javascript:` URL in profile data is returned as empty string by get_found_profiles() | unit | `pytest web-enhanced/tests/test_scanner.py::test_safe_url_rejects_javascript -x` | ❌ Wave 0 |
| STAB-03 | Task created in start_scan() exists in `_background_tasks` set until completion | unit | `pytest web-enhanced/tests/test_server.py::test_task_stored_in_set -x` | ❌ Wave 0 |
| STAB-04 | Exception in save_pdf_report() does not leave tmp file on disk | unit | `pytest web-enhanced/tests/test_scanner.py::test_export_tmp_cleanup_on_exception -x` | ❌ Wave 0 |
| BACK-01 | scan_progress endpoint returns EventSourceResponse not StreamingResponse | unit | `pytest web-enhanced/tests/test_server.py::test_progress_uses_event_source_response -x` | ❌ Wave 0 |
| BACK-02 | requirements.txt does not contain sse-starlette | static | `grep -c sse-starlette web-enhanced/requirements.txt; test $? -ne 0` (or pytest file parse test) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest web-enhanced/tests/ -x -q`
- **Per wave merge:** `pytest web-enhanced/tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `web-enhanced/tests/__init__.py` — make tests directory a package
- [ ] `web-enhanced/tests/test_server.py` — covers STAB-01, STAB-03, BACK-01
- [ ] `web-enhanced/tests/test_scanner.py` — covers STAB-02, STAB-04
- [ ] Install test deps: `pip install pytest httpx pytest-asyncio` (or `poetry install --with dev`)

---

## Security Domain

### Applicable ASVS Categories (Level 1)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | n/a — local single-user tool |
| V3 Session Management | no | n/a |
| V4 Access Control | no | n/a |
| V5 Input Validation | yes | `ScanRequest.model_post_init` already validates username; `_safe_url()` validates profile URLs |
| V6 Cryptography | no | no crypto in phase scope |
| V7 Error Handling | yes | Exceptions in generate_export must not leak tmp paths in response body |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| javascript: URL in profile href | Spoofing / Elevation | http/https allowlist in `_safe_url()` at serialization |
| data: URI injection | Spoofing | Covered by http/https allowlist |
| Temp file path disclosure via exception | Information Disclosure | Catch exception in generate_export, return 500 without tmp_path in message |
| SSE queue exhaustion (many disconnects) | Denial of Service | Queue items are small dicts; queue has no maxsize; acceptable for local single-user tool |

---

## Sources

### Primary (HIGH confidence)
- `/fastapi/fastapi` (Context7) — SSE EventSourceResponse docs, usage patterns, keep-alive behavior
- https://fastapi.tiangolo.com/tutorial/server-sent-events/ — official FastAPI SSE tutorial with version info
- https://github.com/fastapi/fastapi/releases — confirmed 0.135.0 added SSE; 0.136.1 is latest
- https://docs.python.org/3/library/asyncio-task.html — asyncio.create_task GC documentation and recommended set pattern
- `web-enhanced/server.py`, `web-enhanced/scanner.py`, `web-enhanced/requirements.txt` — read directly [VERIFIED: via Read tool]
- `pip3 show fastapi starlette`, `pip index versions fastapi` — version verification [VERIFIED]

### Secondary (MEDIUM confidence)
- https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html — URL allowlist recommendation for XSS prevention

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against pip registry and release notes
- Architecture: HIGH — based on reading actual source files
- Pitfalls: HIGH — based on reading actual code and Python/FastAPI official docs
- Validation: MEDIUM — test file paths are projections; actual execution depends on dev env setup

**Research date:** 2026-05-08
**Valid until:** 2026-08-08 (FastAPI minor versions move quickly; re-verify fastapi.sse API if > 30 days)
