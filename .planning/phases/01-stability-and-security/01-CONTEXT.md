# Phase 1: Stability and Security - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix stability bugs (SSE memory leak, asyncio task GC, temp file leaks) and security sinks (XSS via profile URLs) in the FastAPI web-enhanced server. Migrate to proper SSE handling and clean up dead dependencies. No new features — harden what exists.

</domain>

<decisions>
## Implementation Decisions

### SSE Disconnect Behavior
- **D-01:** When a client disconnects mid-scan, the SSE generator must stop cleanly, but the scan task continues in background. The operator can reconnect and retrieve results via `/api/scan/{id}/results`. Rationale: a page refresh should not kill a 10-minute scan on a local single-user tool.

### Job Lifecycle
- **D-02:** No automatic cleanup of completed jobs from the in-memory `jobs` dict. Jobs persist until server restart. Acceptable for local single-user usage. Already tracked as post-milestone concern in STATE.md.

### Claude's Discretion
- **D-03:** XSS sanitization approach — Claude decides where and how to sanitize profile URLs (backend, frontend, or both) and scope of validation (just `javascript:` protocol or stricter http/https-only allowlist). User noted this is a local tool so risk is low, but good practice to close the sink.
- **D-04:** SSE migration strategy — Claude decides whether to adopt a proper EventSourceResponse or keep StreamingResponse with disconnect detection. `sse-starlette` must be removed from requirements.txt regardless.
- **D-05:** asyncio task GC fix — Claude decides implementation (module-level set vs. task ref on job object).
- **D-06:** Temp file cleanup — Claude decides implementation (try/finally vs. context manager).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Server Implementation
- `web-enhanced/server.py` — FastAPI routes, SSE endpoint (lines 70-96 are the SSE generator with the memory leak)
- `web-enhanced/scanner.py` — Maigret wrapper, progress queue, export generation (lines 239-257 have temp file leak)
- `web-enhanced/requirements.txt` — Dependencies to update (remove sse-starlette, pin FastAPI)

### Design Reference
- `web-enhanced/static/mockup.html` — Visual design spec (not relevant for Phase 1 but context)

### Codebase Analysis
- `.planning/codebase/CONCERNS.md` — Full security and stability concerns audit
- `.planning/codebase/ARCHITECTURE.md` — System architecture overview

### Requirements
- `.planning/REQUIREMENTS.md` — STAB-01 through STAB-04, BACK-01, BACK-02

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScanJob` dataclass (scanner.py:29-40): Already has `queue`, `status`, `error` fields. Can store task reference here.
- `ProgressNotify` (scanner.py:43-77): Uses `asyncio.run_coroutine_threadsafe` to push events — compatible with disconnect-aware generator.

### Established Patterns
- `StreamingResponse` with `text/event-stream` media type (server.py:96) — current SSE pattern to fix or replace.
- `asyncio.Queue` per job (scanner.py:35) — producer-consumer pattern between scan task and SSE generator.
- `tempfile.NamedTemporaryFile(delete=False)` + manual `os.unlink()` (scanner.py:240-246) — pattern to wrap in try/finally.

### Integration Points
- `start_scan()` (server.py:52-67) — where task reference must be stored
- `event_stream()` (server.py:76-95) — where disconnect detection must be added
- `generate_export()` (scanner.py:217-260) — where temp file cleanup must be hardened

</code_context>

<specifics>
## Specific Ideas

- Tool is local-only (127.0.0.1), single-user. Threat model is low — security fixes are good practice, not urgent defense.
- Operator values scan persistence over resource savings — don't kill scans on disconnect.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 1-Stability and Security*
*Context gathered: 2026-05-08*
