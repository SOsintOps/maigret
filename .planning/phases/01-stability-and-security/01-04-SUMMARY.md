---
phase: 01-stability-and-security
plan: "04"
subsystem: web-enhanced/server
tags: [sse, streaming, fastapi, testing, gap-closure]
dependency_graph:
  requires: [01-03]
  provides: [importable-server, sse-streaming, behavioral-sse-tests]
  affects: [web-enhanced/server.py, web-enhanced/requirements.txt, web-enhanced/tests/test_server.py]
tech_stack:
  added: []
  patterns: [StreamingResponse SSE, asyncio Queue drain, SSE keep-alive comment line]
key_files:
  modified:
    - web-enhanced/server.py
    - web-enhanced/requirements.txt
    - web-enhanced/tests/test_server.py
decisions:
  - "StreamingResponse with manual SSE formatting chosen over EventSourceResponse (D-04: fastapi.sse does not exist in any published FastAPI version)"
  - "SSE keep-alive uses comment line (:\\n\\n) yielded on asyncio.TimeoutError; no external ping mechanism needed"
  - "Optional[List[str]] used instead of list[str] | None in Pydantic model for Python 3.9 compatibility"
  - "Maigret dependency stubbed in test_server.py (same pattern as test_scanner.py) to allow behavioral tests without full maigret install"
metrics:
  duration: "~15 minutes"
  completed: "2026-05-08"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 3
---

# Phase 01 Plan 04: Fix fastapi.sse Import Blocker — StreamingResponse SSE Summary

One-liner: Fixed server.py import blocker by replacing nonexistent fastapi.sse with StreamingResponse-based SSE using manual SSE formatting and Starlette disconnect teardown.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix server.py — revert SSE to StreamingResponse | 1a8082d | web-enhanced/server.py, web-enhanced/requirements.txt |
| 2 | Rewrite test_server.py — update assertions and add behavioral SSE disconnect tests | 528b317 | web-enhanced/server.py (Python 3.9 fix), web-enhanced/tests/test_server.py |

## What Was Built

### Task 1: server.py + requirements.txt

Replaced the broken `from fastapi.sse import EventSourceResponse, ServerSentEvent` import with `StreamingResponse` from `fastapi.responses`. Rewrote `scan_progress` to:

- Yield SSE-formatted strings (`f"data: {json.dumps(event)}\n\n"`) instead of `ServerSentEvent` objects
- Yield named event strings (`f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"`) for done/error
- Yield `":\n\n"` (SSE comment as keep-alive) on `asyncio.TimeoutError` instead of relying on auto-ping
- Return `StreamingResponse(event_stream(), media_type="text/event-stream")`

Fixed `requirements.txt` to pin `fastapi>=0.128.0` (the installed 0.128.8 satisfies this; the previous `>=0.135.1` does not exist on PyPI).

### Task 2: test_server.py

Complete rewrite of the test suite to match the StreamingResponse approach. 16 tests total:

- 4 BACK-01 source-level tests (StreamingResponse import, no fastapi.sse, SSE data format, keep-alive)
- 2 BACK-02 requirements.txt validity tests
- 1 STAB-01 source guard (no GeneratorExit handling)
- 3 STAB-03 source guards (_background_tasks declaration, add, callback)
- 2 STAB-03 asyncio lifecycle tests (task stored/removed)
- 2 STAB-01 behavioral disconnect tests (generator teardown, scan task survives)
- 1 STAB-03 runtime check (_background_tasks is set)
- 1 import blocker resolution test (server importable)

Full test suite (test_server.py + test_scanner.py): 26/26 passing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed "GeneratorExit" string from comment in server.py**
- **Found during:** Task 2 test run
- **Issue:** The plan's comment text included "GeneratorExit" which caused `test_no_generator_exit_handling` to fail (the test uses a simple string search on the source)
- **Fix:** Changed comment from "handles disconnect via GeneratorExit" to "cancels the generator on disconnect" — preserves intent, removes the string that triggers the guard
- **Files modified:** web-enhanced/server.py

**2. [Rule 3 - Blocking] Added maigret stubs to test_server.py for Python import compatibility**
- **Found during:** Task 2 behavioral test execution
- **Issue:** `from server import scan_progress, jobs` triggered scanner.py which imports from maigret; maigret's `socid_extractor` dependency is not installed in this environment
- **Fix:** Added module-level maigret stubs (same pattern as test_scanner.py) before path insertion. This allows server.py to be imported in tests without the full maigret tree installed.
- **Files modified:** web-enhanced/tests/test_server.py

**3. [Rule 3 - Blocking] Fixed Python 3.9 type annotation incompatibility in server.py**
- **Found during:** Task 2 behavioral test execution after stub fix
- **Issue:** Pydantic v2 cannot evaluate `list[str] | None` as a ForwardRef in Python 3.9 even with `from __future__ import annotations`. Error: "Unable to evaluate type annotation 'list[str] | None'"
- **Fix:** Added `from typing import List, Optional` and changed `tags: list[str] | None = None` / `excluded_tags: list[str] | None = None` to `Optional[List[str]] = None` in `ScanRequest`
- **Files modified:** web-enhanced/server.py
- **Note:** The `from __future__ import annotations` added as an intermediate attempt was also removed since it's not needed with the typing imports

## Verification

All checks passing:

```
grep -c "from fastapi.sse" web-enhanced/server.py  → 0
grep -c "StreamingResponse" web-enhanced/server.py → 3 (import line + return statement + comment)
grep -c "_background_tasks" web-enhanced/server.py → 3 (declaration + add + callback)
grep -c "0.135.1" web-enhanced/requirements.txt    → 0
grep -c "fastapi>=0.128.0" web-enhanced/requirements.txt → 1
python3 -m pytest web-enhanced/tests/test_server.py -x -v → 16 passed
python3 -m pytest web-enhanced/tests/ -x            → 26 passed
```

## Known Stubs

None — all data flows are wired. The maigret stubs in tests are test infrastructure, not product stubs.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced. Changes are internal to the SSE generator implementation.

## Self-Check: PASSED

- FOUND: web-enhanced/server.py
- FOUND: web-enhanced/requirements.txt
- FOUND: web-enhanced/tests/test_server.py
- FOUND: task1 commit 1a8082d
- FOUND: task2 commit 528b317
- no fastapi.sse in server.py: confirmed (0 matches)
- StreamingResponse in server.py: confirmed (3 matches)
- fastapi>=0.128.0 in requirements.txt: confirmed
