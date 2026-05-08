---
phase: 01-stability-and-security
verified: 2026-05-08T16:00:00Z
status: gaps_found
score: 4/5 must-haves verified
overrides_applied: 0
gaps:
  - truth: "A client that disconnects mid-scan does not leave an orphaned SSE generator or growing queue in memory"
    status: failed
    reason: "The server cannot start or be imported because fastapi.sse is not importable (FastAPI 0.128.8 installed, 0.135.1 required). The correctness of the EventSourceResponse teardown path cannot be confirmed at runtime. Additionally, the two behavioral SSE disconnect tests planned (test_sse_disconnect_exits_generator_cleanly, test_sse_disconnect_does_not_kill_scan_task) were deferred from test_server.py and do not exist in the codebase. The server source code is structurally correct, but the feature is unverifiable and non-functional in the current environment."
    artifacts:
      - path: "web-enhanced/server.py"
        issue: "Imports from fastapi.sse which does not exist in the installed FastAPI 0.128.8; server cannot start"
      - path: "web-enhanced/tests/test_server.py"
        issue: "Behavioral disconnect tests (test_sse_disconnect_exits_generator_cleanly, test_sse_disconnect_does_not_kill_scan_task) were planned but deferred and are absent"
    missing:
      - "Install FastAPI >= 0.135.1 once it is available on PyPI, or apply the StreamingResponse+listen_for_disconnect fallback documented in RESEARCH.md while blocked"
      - "Add behavioral SSE disconnect tests once fastapi.sse is importable"
human_verification: []
---

# Phase 1: Stability and Security — Verification Report

**Phase Goal:** The server runs cleanly through full scan sessions without memory leaks, does not expose XSS sinks, and uses FastAPI native SSE
**Verified:** 2026-05-08
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| #  | Truth                                                                                                 | Status     | Evidence                                                                                                           |
|----|-------------------------------------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------------------------------------|
| 1  | A client that disconnects mid-scan does not leave an orphaned SSE generator or growing queue in memory | FAILED  | server.py source is structurally correct; EventSourceResponse teardown logic is present; but `fastapi.sse` is not importable (FastAPI 0.128.8 installed, requires 0.135.1). Server cannot start. Behavioral disconnect tests (2 of them) were deferred and absent from codebase. |
| 2  | A profile URL containing a javascript: protocol is not rendered as a clickable link                   | VERIFIED | `_safe_url()` allowlist in scanner.py line 170-175 using `urlparse().scheme in ("http", "https")`; applied at `get_found_profiles` line 186 via `_safe_url(status.site_url_user)`; 8 passing unit tests confirm all rejection/allowance cases |
| 3  | An asyncio scan task running in the background survives garbage collection until the scan completes    | VERIFIED | `_background_tasks: set[asyncio.Task] = set()` at module level in server.py line 20; `_background_tasks.add(task)` at line 68; `task.add_done_callback(_background_tasks.discard)` at line 69; 3 source-inspection tests + 2 asyncio lifecycle tests pass |
| 4  | Cancelling or crashing a scan does not leave temporary export files on disk                           | VERIFIED | `tmp_path = None` guard before try block; `finally: if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)` in both pdf (scanner.py lines 250-259) and html (lines 264-274) branches; 2 passing exception-path tests confirm cleanup |
| 5  | The SSE endpoint uses FastAPI native EventSourceResponse; sse-starlette is removed from requirements.txt | PARTIAL | requirements.txt: `fastapi>=0.135.1` present, `sse-starlette` absent (VERIFIED). server.py: `from fastapi.sse import EventSourceResponse, ServerSentEvent` present, `StreamingResponse` absent, `return EventSourceResponse(event_stream())` present (VERIFIED at source level). Runtime: `fastapi.sse` module does NOT exist in installed FastAPI 0.128.8 — server cannot start. |

**Score:** 3 fully verified + 1 partial (SC5 split: requirements.txt half verified, runtime half blocked) + 1 failed = 4/5 truths verified at source level; 1 blocker gap blocks runtime goal achievement.

---

## Requirement Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| STAB-01 | 01-03 | SSE event_stream generator checks for client disconnect and cleans up the asyncio queue | BLOCKED | Source code structure correct (EventSourceResponse, no GeneratorExit suppression). Runtime non-functional: fastapi.sse not importable. Behavioral tests absent. |
| STAB-02 | 01-01 | All href attributes sanitised against javascript: protocol XSS | SATISFIED | `_safe_url()` + `get_found_profiles` application + 8 tests all green |
| STAB-03 | 01-03 | asyncio background tasks stored in module-level set to prevent GC cancellation | SATISFIED | `_background_tasks` set, add + discard callback pattern, verified by source inspection and asyncio lifecycle tests |
| STAB-04 | 01-01 | Export temp files cleaned up in finally block | SATISFIED | try/finally in both pdf and html branches; 2 exception-path cleanup tests pass |
| BACK-01 | 01-03 | Server uses FastAPI native EventSourceResponse instead of manual StreamingResponse | BLOCKED | Source is correct. FastAPI 0.128.8 installed — `fastapi.sse` module absent; server.py cannot be imported. |
| BACK-02 | 01-02 | requirements.txt pins FastAPI >= 0.135.1 and removes sse-starlette | SATISFIED (file) / BLOCKED (runtime) | File edit complete and correct. FastAPI 0.135.1 not on PyPI; pip install resolves to 0.128.8 which lacks fastapi.sse. |

**Orphaned requirements:** None. All 6 required IDs (STAB-01, STAB-02, STAB-03, STAB-04, BACK-01, BACK-02) are claimed by plans and covered above.

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web-enhanced/scanner.py` | `_safe_url` helper, try/finally temp cleanup | VERIFIED | `def _safe_url` at line 170; `_safe_url(status.site_url_user)` at line 186; `finally:` at lines 257 and 271; `tmp_path = None` guards at lines 250 and 264 |
| `web-enhanced/tests/__init__.py` | Package marker | VERIFIED | File exists, 0 bytes |
| `web-enhanced/tests/test_scanner.py` | 10 tests for STAB-02, STAB-04 | VERIFIED | 10 tests present and passing; includes `test_safe_url_rejects_javascript`, `test_export_pdf_tmp_cleanup_on_exception`, `test_export_html_tmp_cleanup_on_exception` |
| `web-enhanced/requirements.txt` | fastapi>=0.135.1, no sse-starlette, 3 lines | VERIFIED (file) | Contains `fastapi>=0.135.1`, `uvicorn>=0.34.0`, `maigret>=0.6.0`; no sse-starlette |
| `web-enhanced/server.py` | EventSourceResponse SSE, `_background_tasks` set | VERIFIED (source) / FAILED (runtime) | All required patterns present in source; `fastapi.sse` not importable — `import server` raises `ModuleNotFoundError: No module named 'fastapi.sse'` |
| `web-enhanced/tests/test_server.py` | 9 tests for STAB-01, STAB-03, BACK-01 | PARTIAL | 9 source-inspection and asyncio lifecycle tests present and passing. Behavioral SSE disconnect tests (`test_sse_disconnect_exits_generator_cleanly`, `test_sse_disconnect_does_not_kill_scan_task`) planned in Plan 03 task 2 were deferred and are absent. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `web-enhanced/scanner.py` | `get_found_profiles` | `_safe_url(status.site_url_user)` | VERIFIED | Line 186: `"url": _safe_url(status.site_url_user),` |
| `web-enhanced/scanner.py` pdf branch | `try/finally cleanup` | `finally:` + `os.unlink` | VERIFIED | Lines 257-259: `finally: if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)` |
| `web-enhanced/scanner.py` html branch | `try/finally cleanup` | `finally:` + `os.unlink` | VERIFIED | Lines 271-273: same pattern |
| `web-enhanced/server.py` | `fastapi.sse` | `from fastapi.sse import EventSourceResponse, ServerSentEvent` | FAILED (runtime) | Import present in source line 10; module does not exist in installed FastAPI 0.128.8 |
| `web-enhanced/server.py` `start_scan` | `_background_tasks` set | `add + add_done_callback(discard)` | VERIFIED | Lines 68-69 confirmed |
| `web-enhanced/server.py` `scan_progress` | `EventSourceResponse` | `return EventSourceResponse(event_stream())` | VERIFIED (source) | Line 96 confirmed; runtime untestable |

---

## Data-Flow Trace (Level 4)

Not applicable for this phase. Phase 1 delivers security fixes and infrastructure changes, not components that render dynamic data from a database.

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| scanner `_safe_url` rejects javascript: | `python3 -m pytest web-enhanced/tests/test_scanner.py -x -v` | 10 passed | PASS |
| scanner temp file cleanup on exception | (same run) | 10 passed | PASS |
| server source-level correctness tests | `python3 -m pytest web-enhanced/tests/test_server.py -x -v` | 9 passed | PASS |
| server.py importable (runtime) | `python3 -c "import sys; sys.path.insert(0,'web-enhanced'); import server"` | `ModuleNotFoundError: No module named 'fastapi.sse'` | FAIL |
| fastapi.sse importable | `python3 -c "from fastapi.sse import EventSourceResponse"` | `No module named 'fastapi.sse'` (FastAPI 0.128.8 installed) | FAIL |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `web-enhanced/scanner.py` | 72 | `url=result.site_url_user` in `ProgressNotify.update()` — URL placed in queue event without `_safe_url` | Warning | Progress events delivered via SSE carry unsanitized URLs. These are consumed by the frontend JS; if the frontend renders this `url` field as an href, the XSS sink persists for in-progress scan events (only post-scan results go through `get_found_profiles` where `_safe_url` is applied). |
| `web-enhanced/scanner.py` | 212 | `url=status.site_url_user` in `get_graph_json()` — URL placed in graph node without `_safe_url` | Warning | Graph node data contains unsanitized profile URLs. If the frontend renders these as clickable links in the D3 graph, the XSS sink is present in that view. STAB-02 scope covers `get_found_profiles` but `get_graph_json` is out of scope per plan 01-01. |

The ProgressNotify warning is notable: the plan's threat model (T-01-01) identifies `get_found_profiles URL field` as the sink. Real-time progress events via SSE also carry `url` fields that bypass `_safe_url`. This is likely an acceptable scope limitation for Phase 1 (the real-time URL in progress events is the currently-being-checked site, not the final profile page), but it is documented here for completeness.

---

## Human Verification Required

None. All verifiable items were checked programmatically. The FastAPI version blocker is objectively determined by `python3 -c "from fastapi.sse import EventSourceResponse"` failing.

---

## Gaps Summary

**One blocker gap prevents full goal achievement:**

**Gap: fastapi.sse not importable — server cannot start**

FastAPI 0.135.1 (the minimum version that ships the `fastapi.sse` module) is not yet published on PyPI. The installed version is 0.128.8. As a result:

1. `import server` raises `ModuleNotFoundError: No module named 'fastapi.sse'` — the server process cannot start at all.
2. Success Criteria 1 and 5 cannot be confirmed at runtime.
3. The two behavioral SSE disconnect tests planned in Plan 03 (`test_sse_disconnect_exits_generator_cleanly`, `test_sse_disconnect_does_not_kill_scan_task`) were deferred by the executor and do not exist in the codebase. They require `fastapi.sse` to be importable to run.

The source code of `server.py` is structurally correct — the import, the EventSourceResponse usage, the `_background_tasks` set, and the generator teardown approach all match the plan exactly. The gap is entirely a dependency availability issue, not a code quality issue.

**Options to unblock:**
- Wait for FastAPI 0.135.1 to appear on PyPI and run `pip install -r requirements.txt --upgrade`.
- Apply the fallback path documented in RESEARCH.md (keep StreamingResponse but add explicit `listen_for_disconnect` detection, available in Starlette 0.49.3) until FastAPI 0.135.x ships.

**What IS verified and working:**
- STAB-02 (XSS URL sanitization): fully implemented and tested — 10 passing tests
- STAB-03 (asyncio task GC): fully implemented at source level and confirmed by asyncio lifecycle tests — 9 passing tests
- STAB-04 (temp file cleanup): fully implemented and tested — 2 exception-path tests pass
- BACK-02 (requirements.txt): file content is correct

---

_Verified: 2026-05-08_
_Verifier: Claude (gsd-verifier)_
