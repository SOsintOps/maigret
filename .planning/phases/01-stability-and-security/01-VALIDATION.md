---
phase: 1
slug: stability-and-security
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `cd web-enhanced && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd web-enhanced && python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd web-enhanced && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd web-enhanced && python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01 | 1 | STAB-02 | T-01-01 | javascript: URLs not rendered as clickable links | unit | `python -m pytest web-enhanced/tests/test_scanner.py -k safe_url` | Created in Plan 01 | ⬜ pending |
| 01-01-T1 | 01 | 1 | STAB-04 | T-01-02 | No temp files left on disk after export exception | unit | `python -m pytest web-enhanced/tests/test_scanner.py -k tmp_cleanup` | Created in Plan 01 | ⬜ pending |
| 01-01-T2 | 01 | 1 | STAB-02, STAB-04 | — | Test suite for scanner fixes passes | unit | `python -m pytest web-enhanced/tests/test_scanner.py -x -v` | Created in Plan 01 | ⬜ pending |
| 01-02-T1 | 02 | 1 | BACK-02 | T-02-01 | sse-starlette removed from requirements.txt | grep | `grep -v '^#' web-enhanced/requirements.txt \| grep -c sse-starlette; test $? -ne 0` | N/A (static) | ⬜ pending |
| 01-03-T1 | 03 | 2 | STAB-01, STAB-03, BACK-01 | T-03-01..03 | SSE uses EventSourceResponse; tasks in _background_tasks | import check | `python -c "import sys; sys.path.insert(0,'web-enhanced'); from server import app, _background_tasks, scan_progress"` | Created in Plan 03 | ⬜ pending |
| 01-03-T2 | 03 | 2 | STAB-01 | T-03-01 | SSE generator exits cleanly on disconnect, no orphaned queue reader | behavioral | `python -m pytest web-enhanced/tests/test_server.py::test_sse_disconnect_exits_generator_cleanly -x` | Created in Plan 03 | ⬜ pending |
| 01-03-T2 | 03 | 2 | STAB-01 | — | SSE disconnect does not cancel scan task (per D-01) | behavioral | `python -m pytest web-enhanced/tests/test_server.py::test_sse_disconnect_does_not_kill_scan_task -x` | Created in Plan 03 | ⬜ pending |
| 01-03-T2 | 03 | 2 | STAB-03 | T-03-03 | asyncio task survives GC until scan completes | unit | `python -m pytest web-enhanced/tests/test_server.py::test_task_stored_in_set -x` | Created in Plan 03 | ⬜ pending |
| 01-03-T2 | 03 | 2 | BACK-01 | — | SSE uses FastAPI native EventSourceResponse | static + import | `python -m pytest web-enhanced/tests/test_server.py::test_event_source_response_import -x` | Created in Plan 03 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `web-enhanced/tests/__init__.py` — make tests directory a package (created in Plan 01, Task 2)
- [ ] `web-enhanced/tests/test_scanner.py` — covers STAB-02, STAB-04 (created in Plan 01, Task 2)
- [ ] `web-enhanced/tests/test_server.py` — covers STAB-01, STAB-03, BACK-01 (created in Plan 03, Task 2)
- [ ] `pytest` install — add to requirements.txt dev dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full scan session completes without memory growth | STAB-01 | Requires long-running scan with real sites | Run 3-minute scan, monitor RSS via `ps` before/after |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
