---
phase: 01-stability-and-security
verified: 2026-05-08T18:00:00Z
status: human_needed
score: 4/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  gaps_closed:
    - "server.py can be imported without error — fastapi.sse blocker resolved by Plan 04 (StreamingResponse fallback)"
    - "Behavioral SSE disconnect tests added and passing (test_sse_disconnect_exits_generator_cleanly, test_sse_disconnect_does_not_kill_scan_task)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Accept the SC5 deviation: ROADMAP SC5 says 'uses FastAPI native EventSourceResponse' but the implementation uses StreamingResponse with manual SSE formatting, because fastapi.sse does not exist in any published FastAPI version. Verify the intent is satisfied (proper SSE with disconnect handling, no sse-starlette) and add an override if acceptable."
    expected: "Decision: either (a) add override accepting StreamingResponse as equivalent to SC5 intent, or (b) require the roadmap SC5 wording to be updated to reflect the StreamingResponse approach."
    why_human: "SC5 as literally written in ROADMAP.md is not satisfied — EventSourceResponse is not used. The deviation was accepted by Plan 04 executor (gap_closure plan) because fastapi.sse does not exist on PyPI. The behavioral intent is verified by 26 passing tests. A human must decide whether to override SC5 or update the roadmap."
---

# Phase 1: Stability and Security — Verification Report (Re-verification)

**Phase Goal:** The server runs cleanly through full scan sessions without memory leaks, does not expose XSS sinks, and uses FastAPI native SSE
**Verified:** 2026-05-08
**Status:** human_needed
**Re-verification:** Yes — after Plan 04 gap closure

---

## Re-verification Context

The previous verification (2026-05-08) found one blocker gap: `fastapi.sse` was not importable because FastAPI 0.135.1 (the minimum version shipping `fastapi.sse`) does not exist on PyPI. Plan 04 was executed as a gap closure plan, reverting server.py to `StreamingResponse`-based SSE with proper SSE formatting and adding the two deferred behavioral SSE disconnect tests.

**Gap closure outcome:** The import blocker is resolved. The server imports cleanly. All 26 tests pass. The behavioral disconnect tests that were absent in the initial verification are now present and passing.

**Residual concern:** ROADMAP SC5 literally states "uses FastAPI native EventSourceResponse." The implementation uses `StreamingResponse`. This is a documented, intentional deviation (Plan 04, gap_closure: true) — the intent of SC5 is achieved, but the literal wording references a non-existent module. A human decision is required to formally accept or reject this deviation.

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | A client that disconnects mid-scan does not leave an orphaned SSE generator or growing queue in memory | VERIFIED | Behavioral test `test_sse_disconnect_exits_generator_cleanly` confirms generator exits cleanly via `aclose()`, queue item remains unconsumed after teardown. `test_sse_disconnect_does_not_kill_scan_task` confirms scan task survives SSE disconnect. Both pass. Starlette's StreamingResponse throws `GeneratorExit` into the async generator on client disconnect — identical teardown behavior to EventSourceResponse. |
| 2  | A profile URL containing a javascript: protocol is not rendered as a clickable link | VERIFIED | `_safe_url()` allowlist at `scanner.py:170-175` using `urlparse().scheme in ("http", "https")` applied at `get_found_profiles` line 186. 8 passing unit tests confirm all scheme rejection/allowance cases including `javascript:`, `data:`, `vbscript:`, `file:`. |
| 3  | An asyncio scan task running in the background survives garbage collection until the scan completes | VERIFIED | `_background_tasks: set[asyncio.Task] = set()` at `server.py:21`. `_background_tasks.add(task)` at line 69. `task.add_done_callback(_background_tasks.discard)` at line 70. Confirmed by 3 source-inspection tests + 2 asyncio lifecycle tests (stored in set, removed after completion). |
| 4  | Cancelling or crashing a scan does not leave temporary export files on disk | VERIFIED | `tmp_path = None` guard before try block; `finally: if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)` in both pdf (`scanner.py:257-259`) and html (`scanner.py:273-275`) branches. 2 exception-path tests pass confirming cleanup on raised RuntimeError. |
| 5  | The SSE endpoint uses FastAPI native EventSourceResponse; sse-starlette is removed from requirements.txt | UNCERTAIN | **sse-starlette removal:** VERIFIED — `requirements.txt` contains no `sse-starlette` line. **EventSourceResponse:** NOT USED — implementation uses `StreamingResponse` with manual SSE formatting (`f"data: {json.dumps(event)}\n\n"`, `f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"`, `":\n\n"` keep-alive). This is a documented intentional deviation: `fastapi.sse` does not exist in any published FastAPI version. The behavioral intent of SC5 (clean disconnect handling, proper SSE format, no third-party SSE library) is fully achieved and verified. |

**Score:** 4/5 truths verified (SC5 is UNCERTAIN — intent achieved, literal wording not met)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web-enhanced/scanner.py` | `_safe_url` helper, try/finally temp cleanup | VERIFIED | `def _safe_url` at line 170; `_safe_url(status.site_url_user)` at line 186; `finally:` at lines 257 and 273; `tmp_path = None` guards at lines 250 and 264 |
| `web-enhanced/tests/__init__.py` | Package marker | VERIFIED | File exists |
| `web-enhanced/tests/test_scanner.py` | Unit tests for STAB-02, STAB-04 | VERIFIED | 10 tests present and passing: 8 `_safe_url` scheme tests + 2 exception-path cleanup tests |
| `web-enhanced/requirements.txt` | No sse-starlette, valid FastAPI pin | VERIFIED | Contains `fastapi>=0.128.0`, `uvicorn>=0.34.0`, `maigret>=0.6.0`; no `sse-starlette`; no `0.135.1` |
| `web-enhanced/server.py` | SSE endpoint, `_background_tasks` set, importable | VERIFIED | Imports cleanly (confirmed by `test_server_importable`); `StreamingResponse` SSE with proper formatting; `_background_tasks` set with done callback; no `fastapi.sse` import |
| `web-enhanced/tests/test_server.py` | Tests for STAB-01, STAB-03, BACK-01, BACK-02 | VERIFIED | 16 tests present and passing including both behavioral SSE disconnect tests previously absent |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `web-enhanced/scanner.py` | `get_found_profiles` | `_safe_url(status.site_url_user)` | VERIFIED | Line 186: `"url": _safe_url(status.site_url_user),` |
| `web-enhanced/scanner.py` pdf branch | try/finally cleanup | `finally:` + `os.unlink` | VERIFIED | Lines 257-259 |
| `web-enhanced/scanner.py` html branch | try/finally cleanup | `finally:` + `os.unlink` | VERIFIED | Lines 273-275 |
| `web-enhanced/server.py` | `fastapi.responses.StreamingResponse` | `from fastapi.responses import FileResponse, Response, StreamingResponse` | VERIFIED | Line 10; no `from fastapi.sse` anywhere |
| `web-enhanced/server.py scan_progress` | `StreamingResponse` | `return StreamingResponse(event_stream(), media_type="text/event-stream")` | VERIFIED | Line 98 |
| `web-enhanced/server.py start_scan` | `_background_tasks` set | `add + add_done_callback(discard)` | VERIFIED | Lines 69-70 |

---

## Data-Flow Trace (Level 4)

Not applicable. Phase 1 delivers security fixes and infrastructure changes, not components that render dynamic data from a database.

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `_safe_url` rejects javascript: | `python3 -m pytest web-enhanced/tests/test_scanner.py -x -v` | 10 passed | PASS |
| Temp file cleanup on exception | (same run) | 10 passed | PASS |
| server.py source-level tests | `python3 -m pytest web-enhanced/tests/test_server.py -x -v` | 16 passed | PASS |
| Behavioral SSE disconnect (generator cleanup) | `test_sse_disconnect_exits_generator_cleanly` | PASSED | PASS |
| Behavioral SSE disconnect (scan task survives) | `test_sse_disconnect_does_not_kill_scan_task` | PASSED | PASS |
| Full test suite | `python3 -m pytest web-enhanced/tests/ -x` | 26/26 passed | PASS |
| server.py importable | `test_server_importable` (reloads module, checks attributes) | PASSED | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| STAB-01 | 01-03, 01-04 | SSE event_stream generator checks for client disconnect and cleans up the asyncio queue | SATISFIED | Behavioral tests confirm generator exits cleanly on `aclose()`, no orphaned queue reader, scan task survives disconnect |
| STAB-02 | 01-01 | All href attributes sanitised against javascript: protocol XSS | SATISFIED | `_safe_url()` + `get_found_profiles` application + 8 passing tests |
| STAB-03 | 01-03 | asyncio background tasks stored in module-level set to prevent GC cancellation | SATISFIED | `_background_tasks` set, add + discard callback pattern; confirmed by source inspection and asyncio lifecycle tests |
| STAB-04 | 01-01 | Export temp files cleaned up in finally block | SATISFIED | try/finally in both pdf and html branches; 2 exception-path cleanup tests pass |
| BACK-01 | 01-03, 01-04 | Server uses FastAPI native EventSourceResponse instead of manual StreamingResponse | PARTIAL (intent satisfied, literal not) | Implementation uses StreamingResponse with manual SSE formatting. FastAPI native EventSourceResponse not used because `fastapi.sse` does not exist in any published FastAPI version. Proper SSE format and disconnect handling verified. Deviation documented and accepted in Plan 04. |
| BACK-02 | 01-02, 01-04 | requirements.txt pins FastAPI >= 0.135.1 and removes sse-starlette dependency | PARTIAL (intent satisfied, literal not) | `sse-starlette` removed (SATISFIED). Pin is `fastapi>=0.128.0` not `>=0.135.1` (FastAPI 0.135.1 does not exist on PyPI). Installed 0.128.8 is functional. Deviation documented and accepted in Plan 04. |

**Orphaned requirements:** None. All 6 IDs (STAB-01, STAB-02, STAB-03, STAB-04, BACK-01, BACK-02) are claimed by plans and covered above.

**Note on REQUIREMENTS.md:** The REQUIREMENTS.md file still contains the original wording for BACK-01 ("EventSourceResponse") and BACK-02 (">=0.135.1"). These descriptions no longer match the implemented solution. REQUIREMENTS.md should be updated to reflect the StreamingResponse approach and `>=0.128.0` pin, or marked as intentionally deviated.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `web-enhanced/scanner.py` | 72 | `url=result.site_url_user` in `ProgressNotify.update()` — URL placed in SSE progress events without `_safe_url` | Warning | In-progress SSE events carry unsanitized URLs. `_safe_url` only applies to final results via `get_found_profiles`. If the frontend renders the `url` field from progress events as an href, the XSS sink persists for in-flight events. Low risk (in-progress URL is the currently-being-checked site, not a confirmed profile) but outside STAB-02 scope. |
| `web-enhanced/scanner.py` | 212 | `url=status.site_url_user` in `get_graph_json()` — URL placed in graph node without `_safe_url` | Warning | Graph node data contains unsanitized profile URLs. If D3 renders these as clickable links, XSS sink is present in graph view. Outside STAB-02 scope per Plan 01-01. |

Neither anti-pattern is a blocker for Phase 1 goal (scope is `get_found_profiles`), but both should be addressed in a future phase when the frontend rendering of these fields is implemented.

---

## Human Verification Required

### 1. Accept or reject SC5 deviation (StreamingResponse vs EventSourceResponse)

**Test:** Review the Phase 1 ROADMAP SC5 deviation documented in Plan 04 and decide whether to formally accept it.

**Context:**
- ROADMAP SC5 says: "The SSE endpoint uses FastAPI native EventSourceResponse; sse-starlette is removed from requirements.txt"
- Implementation uses: `StreamingResponse` with manual `"data: {...}\n\n"` SSE formatting
- Reason: `fastapi.sse` does not exist in any published FastAPI version (confirmed by Plan 04 research)
- `sse-starlette` IS removed (that half of SC5 is satisfied)
- SSE disconnect behavior IS verified by behavioral tests
- BACK-01 and BACK-02 in REQUIREMENTS.md still reference EventSourceResponse and fastapi>=0.135.1

**Expected:** One of:
  - (a) Add an override to this VERIFICATION.md frontmatter accepting StreamingResponse as satisfying SC5 intent, AND update REQUIREMENTS.md BACK-01/BACK-02 descriptions to reflect the actual implementation
  - (b) Require a new gap closure plan that monitors PyPI for a FastAPI release that includes `fastapi.sse` and migrates when available

**Why human:** SC5 as literally written in the ROADMAP is not satisfied. The deviation was made by the executor in good faith (the module simply does not exist), and the behavioral intent is fully verified. Only a human can formally accept or reject this deviation and decide whether REQUIREMENTS.md needs updating.

**Override template (to add to VERIFICATION.md frontmatter if accepting):**
```yaml
overrides:
  - must_have: "The SSE endpoint uses FastAPI native EventSourceResponse; sse-starlette is removed from requirements.txt"
    reason: "fastapi.sse does not exist in any published FastAPI version. StreamingResponse with manual SSE formatting achieves identical disconnect behavior (verified by behavioral tests). sse-starlette is removed. The intent of SC5 is fully satisfied."
    accepted_by: "<your-name>"
    accepted_at: "<ISO timestamp>"
```

---

## Gaps Summary

No blocking technical gaps remain. The previous gap (fastapi.sse import blocker) is fully closed by Plan 04:

- server.py imports cleanly
- SSE endpoint returns proper SSE-formatted events
- Client disconnect tears down the generator cleanly (behavioral tests pass)
- Scan task survives SSE disconnect (behavioral test passes)
- All 26 tests pass

**One human decision is pending:** Whether to formally accept the SC5 deviation (StreamingResponse vs EventSourceResponse) and update REQUIREMENTS.md accordingly. This is a documentation/governance decision, not a technical gap.

---

_Verified: 2026-05-08_
_Verifier: Claude (gsd-verifier)_
