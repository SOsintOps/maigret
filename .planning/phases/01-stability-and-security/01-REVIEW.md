---
phase: 01-stability-and-security
reviewed: 2026-05-08T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - web-enhanced/scanner.py
  - web-enhanced/server.py
  - web-enhanced/tests/__init__.py
  - web-enhanced/tests/test_scanner.py
  - web-enhanced/tests/test_server.py
findings:
  critical: 3
  warning: 6
  info: 3
  total: 12
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-08
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the web-enhanced scanner and FastAPI server implementation. The code addresses the stated stability and security goals but contains three blockers: a race condition on the global database singleton, a Pydantic v2 validation bypass that turns input errors into 500s, and a SSE one-shot sentinel bug that causes permanent hangs for reconnecting clients. Six additional warnings cover memory growth, type safety, fragile error handling, and test reliability.

---

## Critical Issues

### CR-01: Race Condition on Global `_db` Singleton

**File:** `web-enhanced/scanner.py:85-96`
**Issue:** `get_db()` is called concurrently from the lifespan handler AND from the first `run_scan` call. The guard `if _db is None` is not protected by a lock. Two concurrent callers can both pass the `None` check, both open and parse `data.json`, and one overwrites the other's result. In CPython the GIL provides some protection, but `asyncio` can context-switch between the `open()` call and the assignment, and if `get_db()` is ever called from a thread pool (e.g. via `run_in_executor`) the race is fully exposed.

**Fix:**
```python
import threading
_db_lock = threading.Lock()

def get_db() -> MaigretDatabase:
    global _db
    if _db is not None:
        return _db
    with _db_lock:
        if _db is None:  # double-checked locking
            db = MaigretDatabase()
            data_path = os.path.join(
                os.path.dirname(__import__("maigret").__file__),
                "resources",
                "data.json",
            )
            with open(data_path) as f:
                db.load_from_str(f.read())
            _db = db
    return _db
```

---

### CR-02: `model_post_init` Validation Errors Surface as HTTP 500, Not 422

**File:** `web-enhanced/server.py:41-46`
**Issue:** In Pydantic v2, `model_post_init` is called after model construction succeeds. A `ValueError` raised inside it is **not** automatically wrapped in a `ValidationError`, so FastAPI does not catch it as a validation error and returns HTTP 500 (Internal Server Error) instead of HTTP 422 (Unprocessable Entity). Sending `{"username": ""}` or `{"username": "a".repeat(65)}` crashes the server with an unhandled exception visible in logs.

**Fix:** Move validation into a `@field_validator` (Pydantic v2) so it is part of the validation pipeline and produces a proper 422:
```python
from pydantic import BaseModel, field_validator

class ScanRequest(BaseModel):
    username: str
    top_sites: int = 500
    timeout: int = 30
    tags: list[str] | None = None
    excluded_tags: list[str] | None = None
    recursive: bool = False

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 64:
            raise ValueError("Username must be 1-64 characters")
        if not all(c.isalnum() or c in "._-" for c in v):
            raise ValueError("Username contains invalid characters")
        return v
```

---

### CR-03: SSE `done` Event Is a One-Shot Sentinel — Reconnecting Client Hangs Forever

**File:** `web-enhanced/server.py:80-96`
**Issue:** The progress endpoint uses `job.queue` (a standard `asyncio.Queue`). The `done` event is placed on the queue exactly once by `run_scan`'s `finally` block. The first SSE client to connect consumes this sentinel and exits. If that client disconnects before the scan finishes and a second client connects (or the browser reconnects after a network hiccup), the new `event_stream` generator blocks forever on `job.queue.get()` with 60-second timeouts, never receiving the sentinel. The job is complete but the client is stuck.

This also means the `continue` on `TimeoutError` (line 85) provides no escape hatch — the generator loops indefinitely once the sentinel has been consumed.

**Fix:** Replace the single-consumer `asyncio.Queue` with a broadcast mechanism. The simplest approach is to store the terminal event on the job and check job status before blocking:
```python
async def event_stream():
    while True:
        # Fast exit if job already finished and queue is empty
        if job.status in ("done", "error") and job.queue.empty():
            final = {"type": job.status}
            if job.status == "error":
                final["message"] = job.error or ""
            yield ServerSentEvent(data=json.dumps(final), event=job.status)
            break

        try:
            event = await asyncio.wait_for(job.queue.get(), timeout=5)
        except asyncio.TimeoutError:
            continue

        if event.get("type") in ("done", "error"):
            yield ServerSentEvent(data=json.dumps(event), event=event["type"])
            break
        else:
            job.progress.completed = event["completed"]
            job.progress.total = event["total"]
            job.progress.found = event["found"]
            yield ServerSentEvent(data=json.dumps(event))
```
Alternatively, store `job.terminal_event` on the `ScanJob` dataclass and yield it directly for late-arriving clients.

---

## Warnings

### WR-01: Unbounded In-Memory Job Store — Memory Grows Without Limit

**File:** `web-enhanced/server.py:19`
**Issue:** `jobs: dict[str, ScanJob]` accumulates every scan job forever. Each `ScanJob` holds the full `results` dict (one entry per site checked, up to 500+), the `MaigretDatabase` reference, and an `asyncio.Queue`. A busy server leaks memory continuously. There is no TTL, LRU eviction, or max-size enforcement.

**Fix:** Add a periodic cleanup task in the lifespan that removes jobs older than a configurable TTL (e.g. 1 hour):
```python
async def _cleanup_jobs():
    while True:
        await asyncio.sleep(300)
        cutoff = time.time() - 3600
        stale = [jid for jid, j in jobs.items() if j.finished_at and j.finished_at < cutoff]
        for jid in stale:
            del jobs[jid]

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_db()
    task = asyncio.create_task(_cleanup_jobs())
    yield
    task.cancel()
```

---

### WR-02: Truncated UUID Job IDs Are Collision-Prone

**File:** `web-enhanced/server.py:56`
**Issue:** `str(uuid.uuid4())[:8]` produces an 8-character hex prefix from a 32-character UUID, giving only ~4.3 billion possible values (2^32 before considering hex distribution). Under moderate load or with an adversarial client submitting jobs rapidly, collisions overwrite existing jobs in the `jobs` dict without notice. The overwritten job's queue and results are permanently lost.

**Fix:** Use the full UUID:
```python
job_id = str(uuid.uuid4())
```
Or if short IDs are desired for UX, use `secrets.token_hex(8)` (64-bit entropy) and check for collisions before inserting.

---

### WR-03: `logger=None` Passed to `maigret_search` — Likely AttributeError at Runtime

**File:** `web-enhanced/scanner.py:149`
**Issue:** `maigret_search` is called with `logger=None`. Inspection of the maigret codebase shows `maigret.checking.maigret` calls `logger.debug(...)` and `logger.warning(...)` unconditionally in several code paths. Passing `None` causes `AttributeError: 'NoneType' object has no attribute 'debug'` during normal operation, converting scan jobs to `error` status silently.

**Fix:** Pass a real (or no-op) logger:
```python
import logging
_null_logger = logging.getLogger("maigret.web")
_null_logger.addHandler(logging.NullHandler())

# then in run_scan:
results = await maigret_search(
    ...
    logger=_null_logger,
    ...
)
```

---

### WR-04: `get_db()` Does Not Handle Missing `data.json` Gracefully

**File:** `web-enhanced/scanner.py:89-95`
**Issue:** If `data.json` is absent (packaging error, wrong working directory), `open(data_path)` raises `FileNotFoundError`. This propagates out of `get_db()`, through the lifespan handler, and crashes the server at startup with a Python traceback — no user-friendly message is produced. Worse, if the crash happens during a `run_scan` call rather than lifespan, the job is put into `error` state with a raw filesystem path in the error message, which leaks internal directory structure.

**Fix:**
```python
if not os.path.exists(data_path):
    raise RuntimeError(
        f"Maigret database not found at {data_path!r}. "
        "Ensure maigret is installed correctly."
    )
```

---

### WR-05: `get_found_profiles` Accesses `status.tags` Without Guarding Against Non-Iterable

**File:** `web-enhanced/scanner.py:186-187`
**Issue:** `list(status.tags) if status.tags else []` — if `status.tags` is a non-iterable truthy object (e.g. a sentinel object from a maigret version change), `list()` raises `TypeError`. Similarly `status.ids_data or {}` on line 190 will fail if `ids_data` is a non-mapping truthy type. This is a defensive coding gap at an external library boundary.

**Fix:**
```python
"tags": list(status.tags) if isinstance(status.tags, (list, set, tuple)) else [],
"ids_data": dict(status.ids_data) if isinstance(status.ids_data, dict) else {},
```

---

### WR-06: `scan_graph` Endpoint Returns Unvalidated `site_url_user` in Graph Nodes

**File:** `web-enhanced/scanner.py:211`
**Issue:** `get_graph_json` adds `url=status.site_url_user` directly to graph nodes without passing it through `_safe_url`. The `_safe_url` sanitizer exists specifically to strip `javascript:` and `data:` URIs from URLs that may be rendered in a browser UI. If the graph JSON is rendered in a frontend that uses `node.url` as a hyperlink `href`, a malicious site response could inject a `javascript:` URL into the graph and achieve XSS.

**Fix:**
```python
G.add_node(node_id, size=12, group=2, color="#22c55e",
           url=_safe_url(status.site_url_user), tags=tags)
```

---

## Info

### IN-01: Test Suite Uses Source-String Matching — Brittle and Misleading

**File:** `web-enhanced/tests/test_server.py:19-70`
**Issue:** The majority of `test_server.py` tests work by reading `server.py` as a string and asserting that specific literal substrings are present (e.g. `assert "_background_tasks: set[asyncio.Task] = set()" in source`). These tests pass even if the matched code is inside a comment or dead code branch. They fail on trivially equivalent reformatting (e.g. adding a space). They do not test behavior — they test source text.

**Fix:** Import and test the actual module behavior wherever possible. For the `_background_tasks` lifecycle, patch `run_scan` and use a FastAPI `TestClient` to call `/api/scan` and verify the task set membership.

---

### IN-02: `_safe_url` Type Annotation Does Not Match Accepted Input

**File:** `web-enhanced/scanner.py:170`
**Issue:** `_safe_url(url: str)` is annotated to accept `str`, but `test_scanner.py:55` calls it with `None`. The function works because `if not url` is falsy for `None`, but the type annotation is incorrect and mypy/pyright would flag callers passing `Optional[str]`.

**Fix:**
```python
def _safe_url(url: str | None) -> str:
```

---

### IN-03: Magic Number `50` for `max_connections` with No Documentation

**File:** `web-enhanced/scanner.py:153`
**Issue:** `max_connections=50` is a hardcoded magic number with no comment explaining the rationale or how it interacts with server resources. It is also not exposed through `ScanRequest` or `run_scan`'s parameters, preventing operators from tuning it.

**Fix:** Define a named constant with a comment:
```python
# Limit concurrent HTTP connections per scan to avoid overwhelming the host network stack
_MAX_SCAN_CONNECTIONS = 50
```
and pass `max_connections=_MAX_SCAN_CONNECTIONS` at the call site.

---

_Reviewed: 2026-05-08_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
