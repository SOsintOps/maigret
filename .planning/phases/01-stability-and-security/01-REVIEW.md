---
phase: 01-stability-and-security
reviewed: 2026-05-08T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - web-enhanced/server.py
  - web-enhanced/scanner.py
  - web-enhanced/requirements.txt
  - web-enhanced/tests/test_server.py
  - web-enhanced/tests/test_scanner.py
findings:
  critical: 2
  warning: 6
  info: 3
  total: 11
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-08
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the web-enhanced FastAPI server and scanner module implementing SSE-based progress streaming for maigret username scans. The code handles temp file cleanup, URL sanitization, and asyncio task lifecycle reasonably well. However, two critical issues were found: the SSE progress endpoint hangs permanently for reconnecting clients because the terminal event is consumed from the queue and never recoverable, and passing `logger=None` to the maigret core search function causes `AttributeError` crashes at runtime. Six warnings cover unbounded job storage, job ID collision risk, missing URL sanitization in the graph endpoint, double-event emission, unvalidated input bounds, and an unquoted Content-Disposition header.

---

## Critical Issues

### CR-01: SSE done/error Event Is Single-Consumer -- Reconnecting Client Hangs Forever

**File:** `web-enhanced/server.py:80-96`
**Issue:** The progress endpoint reads from `job.queue` (a standard `asyncio.Queue`). The terminal event (`{"type": "done"}` or `{"type": "error"}`) is placed on the queue exactly once by `run_scan`'s finally/except blocks (scanner.py:163-167). The first SSE client to connect consumes this sentinel and exits the generator loop (server.py:89-91). If that client disconnects before the scan finishes and reconnects, or if any second client connects to the same job ID, the new `event_stream` generator blocks on `job.queue.get()` forever, cycling through 60-second timeouts with keep-alive pings but never receiving the terminal event. The job is complete but the client is stuck in an infinite loop.

This is a data loss and availability bug: a browser that experiences a momentary network hiccup during a scan will reconnect (standard SSE `EventSource` behavior) and hang indefinitely, with no way to retrieve results through this endpoint.

**Fix:** Store the terminal event on the `ScanJob` dataclass and check job status before blocking on the queue:
```python
@dataclass
class ScanJob:
    # ... existing fields ...
    terminal_event: Optional[dict] = None

# In run_scan, store the terminal event:
    finally:
        job.finished_at = time.time()
        terminal = {"type": "done" if job.status == "done" else "error"}
        if job.error:
            terminal["message"] = job.error
        job.terminal_event = terminal
        await job.queue.put(terminal)

# In event_stream, check for already-finished jobs:
async def event_stream():
    while True:
        if job.terminal_event and job.queue.empty():
            yield f"event: {job.terminal_event['type']}\ndata: {json.dumps(job.terminal_event)}\n\n"
            break
        try:
            event = await asyncio.wait_for(job.queue.get(), timeout=5)
        except asyncio.TimeoutError:
            yield ":\n\n"
            continue
        # ... rest of handler ...
```

---

### CR-02: `logger=None` Passed to `maigret_search` Causes AttributeError at Runtime

**File:** `web-enhanced/scanner.py:148-149`
**Issue:** `run_scan` passes `logger=None` to `maigret_search`. Tracing through `maigret/checking.py`, the logger is passed to `SimpleAiohttpChecker(logger=logger)` on line 815 and used unconditionally throughout the checker methods (e.g., `logger.debug()` on line 111, `logger.info()` on line 356, `logger.error()` on line 370, `logger.warning()` on lines 400, 405, 447, 555). Any scan that hits these code paths will raise `AttributeError: 'NoneType' object has no attribute 'debug'` (or 'info', 'warning', 'error'), converting the scan to error status. This will affect virtually every scan since `logger.info(url)` on line 358 runs for every site checked.

**Fix:**
```python
import logging

_logger = logging.getLogger("maigret.web")
_logger.addHandler(logging.NullHandler())

# In run_scan:
results = await maigret_search(
    username=job.username,
    site_dict=sites_dict,
    logger=_logger,
    # ...
)
```

---

## Warnings

### WR-01: Unbounded In-Memory Job Store -- Memory Grows Without Limit

**File:** `web-enhanced/server.py:19`
**Issue:** `jobs: dict[str, ScanJob]` accumulates every scan job forever. Each `ScanJob` holds the full `results` dict (one entry per site checked, potentially 500+), a `MaigretDatabase` reference, an `asyncio.Queue`, and `general_results`. There is no TTL, LRU eviction, or max-size enforcement. A long-running server's memory consumption will grow monotonically.

**Fix:** Add periodic cleanup in the lifespan context:
```python
async def _cleanup_jobs():
    while True:
        await asyncio.sleep(300)
        cutoff = time.time() - 3600
        stale = [jid for jid, j in jobs.items()
                 if j.finished_at and j.finished_at < cutoff]
        for jid in stale:
            del jobs[jid]
```

---

### WR-02: Truncated UUID Job IDs Allow Silent Overwrites on Collision

**File:** `web-enhanced/server.py:57`
**Issue:** `str(uuid.uuid4())[:8]` truncates a UUID to 8 hex characters (~32 bits of entropy). On collision, line 59 (`jobs[job_id] = job`) silently overwrites the existing job, destroying its results and orphaning its background task. No error is reported to either the original or the new client. While the birthday paradox collision probability is low for small volumes (~65,000 jobs for 50% collision), the silent data loss on collision makes this a correctness risk.

**Fix:** Use the full UUID or check for collisions:
```python
job_id = str(uuid.uuid4())
```

---

### WR-03: Graph Endpoint Bypasses URL Sanitization -- Potential Stored XSS

**File:** `web-enhanced/scanner.py:211`
**Issue:** `get_graph_json` adds `url=status.site_url_user` directly to graph nodes without passing it through the `_safe_url` sanitizer. The `_safe_url` function (line 170-175) exists specifically to strip `javascript:`, `data:`, and other dangerous URI schemes. If the graph JSON is rendered in a frontend that uses `node.url` as an `<a href>`, a malicious site could inject a `javascript:` URL via `site_url_user` and achieve XSS. The `get_found_profiles` function correctly uses `_safe_url` on line 186, but `get_graph_json` does not.

**Fix:**
```python
G.add_node(node_id, size=12, group=2, color="#22c55e",
           url=_safe_url(status.site_url_user), tags=tags)
```

---

### WR-04: Double Event Emission on Error Path

**File:** `web-enhanced/scanner.py:160-167`
**Issue:** On the error path, `run_scan` puts both `{"type": "error", "message": str(e)}` (line 163) and `{"type": "done"}` (line 167, from the `finally` block) onto the job queue. The SSE consumer in `server.py:89-91` breaks on the first terminal event (whichever it sees first), leaving the second event permanently unconsumed. This interacts with CR-01: a reconnecting client will consume the leftover "done" event, receiving an incomplete terminal event instead of the error details.

**Fix:** Only emit the done event on the success path:
```python
    except Exception as e:
        job.status = "error"
        job.error = str(e)
        await job.queue.put({"type": "error", "message": str(e)})
    finally:
        job.finished_at = time.time()
        if job.status != "error":
            await job.queue.put({"type": "done"})
```

---

### WR-05: No Upper-Bound Validation on `top_sites` and `timeout`

**File:** `web-enhanced/server.py:35-38`
**Issue:** `top_sites` and `timeout` accept any integer value. A client can send `top_sites=999999` or `timeout=999999`, causing excessive resource consumption. The `top_sites` value is passed to `db.ranked_sites_dict(names_top=top_sites)` and `timeout` to `maigret_search(timeout=timeout)`, with no server-side capping.

**Fix:** Add field validators with reasonable bounds:
```python
from pydantic import field_validator

@field_validator("top_sites")
@classmethod
def validate_top_sites(cls, v):
    if v < 1 or v > 5000:
        raise ValueError("top_sites must be between 1 and 5000")
    return v

@field_validator("timeout")
@classmethod
def validate_timeout(cls, v):
    if v < 1 or v > 300:
        raise ValueError("timeout must be between 1 and 300")
    return v
```

---

### WR-06: Content-Disposition Header Filename Not Quoted

**File:** `web-enhanced/server.py:147`
**Issue:** The header value `f"attachment; filename={filename}"` does not quote the filename. Per RFC 6266, the filename parameter value should be a quoted-string: `filename="value"`. While the current username validation restricts characters to `[a-zA-Z0-9._-]`, which are safe, the missing quotes mean this is one validation change away from becoming an HTTP response header injection vector.

**Fix:**
```python
headers={"Content-Disposition": f'attachment; filename="{filename}"'},
```

---

## Info

### IN-01: Tests Validate Source Text Rather Than Runtime Behavior

**File:** `web-enhanced/tests/test_server.py:42-105`
**Issue:** Many tests read `server.py` as a string and assert on literal substrings (e.g., `assert "_background_tasks: set[asyncio.Task] = set()" in source`). These are brittle -- any cosmetic refactoring breaks them even if behavior is preserved. They also produce false confidence because they would pass if the matched text appeared in a comment or dead code. The behavioral tests later in the file (lines 109+) test the same properties more robustly.

**Fix:** Replace source-text tests with behavioral tests that import and exercise the module.

---

### IN-02: Unused Import `json` in scanner.py

**File:** `web-enhanced/scanner.py:7`
**Issue:** `import json` is present but `json` is never used in scanner.py. All `json.dumps` calls are in server.py.

**Fix:** Remove `import json` from scanner.py.

---

### IN-03: `_safe_url` Type Annotation Does Not Match Actual Usage

**File:** `web-enhanced/scanner.py:170`
**Issue:** `_safe_url(url: str)` is annotated to accept `str` only, but `test_scanner.py:55` calls it with `None` and the function handles `None` correctly via `if not url:`. The annotation is incorrect and will produce false negatives from type checkers.

**Fix:**
```python
def _safe_url(url: str | None) -> str:
```

---

_Reviewed: 2026-05-08_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
