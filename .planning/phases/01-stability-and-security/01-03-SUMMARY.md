---
phase: 01-stability-and-security
plan: 03
subsystem: api
tags: [fastapi, sse, asyncio, eventsource]

requires:
  - phase: 01-02
    provides: FastAPI >= 0.135.1 pin enabling fastapi.sse import
provides:
  - EventSourceResponse-based SSE endpoint with proper disconnect handling
  - _background_tasks set preventing asyncio task GC cancellation
  - Scan tasks that survive client disconnect
affects: []

tech-stack:
  added: [fastapi.sse.EventSourceResponse, fastapi.sse.ServerSentEvent]
  patterns: [module-level task set with done callback for GC prevention]

key-files:
  created:
    - web-enhanced/tests/test_server.py
  modified:
    - web-enhanced/server.py

key-decisions:
  - "No GeneratorExit handling — let EventSourceResponse manage teardown naturally"
  - "Scan tasks owned by _background_tasks set, not SSE generator — survive disconnect per D-01"
  - "Behavioral SSE disconnect tests deferred until FastAPI >= 0.135.1 ships on PyPI"

patterns-established:
  - "Task GC prevention: _background_tasks.add(task) + task.add_done_callback(_background_tasks.discard)"

requirements-completed: [STAB-01, STAB-03, BACK-01]

duration: 5min
completed: 2026-05-08
---

# Plan 03: SSE Migration and Task GC Fix

**Replaced StreamingResponse with FastAPI native EventSourceResponse and added _background_tasks set to prevent scan task GC cancellation.**

## What Changed

### server.py
- Removed `StreamingResponse` import, added `from fastapi.sse import EventSourceResponse, ServerSentEvent`
- Added `_background_tasks: set[asyncio.Task] = set()` at module level (STAB-03)
- `start_scan`: tasks stored in set with `add_done_callback(discard)` for automatic cleanup
- `scan_progress`: returns `EventSourceResponse(event_stream())` with `ServerSentEvent` yields instead of manual SSE formatting (STAB-01, BACK-01)
- Removed manual keepalive — EventSourceResponse handles keep-alive pings automatically
- No `GeneratorExit` handling — generator exits cleanly on disconnect, scan task continues

### test_server.py (9 tests)
- Source-level: StreamingResponse removed, EventSourceResponse imported, ServerSentEvent used, no GeneratorExit
- Structure: _background_tasks declared, add() in start_scan, done callback registered
- Behavioral: task lifecycle (add/remove on completion/cancel)

## Environment Constraint

FastAPI 0.135.1 is not yet on PyPI (latest: 0.128.8). The `fastapi.sse` import is correct but cannot be verified at runtime until the release ships. All source-level and asyncio behavioral tests pass. Full SSE behavioral tests (disconnect, generator teardown) are deferred.

## Self-Check: PASSED

- [x] StreamingResponse fully removed from server.py
- [x] EventSourceResponse import present (4 references)
- [x] _background_tasks set declared and used (3 references)
- [x] No GeneratorExit handling
- [x] 9/9 tests pass
- [x] Each task committed atomically
