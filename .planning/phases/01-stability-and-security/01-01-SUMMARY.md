---
phase: 01-stability-and-security
plan: "01"
subsystem: security
tags: [python, xss, url-sanitization, tempfile, scanner, testing, pytest]

requires: []

provides:
  - "_safe_url() allowlist helper in scanner.py: only http/https pass, all other schemes return empty string"
  - "try/finally temp file cleanup in generate_export() pdf and html branches"
  - "Unit test suite for STAB-02 and STAB-04 in web-enhanced/tests/test_scanner.py"

affects:
  - "01-02 (SSE/server.py changes): scanner.py interface unchanged, safe to compose"
  - "phase-02 (visual): profile URL rendering in frontend now receives sanitized URLs"

tech-stack:
  added: [pytest, urllib.parse.urlparse]
  patterns:
    - "URL scheme allowlisting: use urlparse().scheme in ('http','https') not blocklist"
    - "Temp file guard: tmp_path=None before try, finally: os.unlink if exists"
    - "Test isolation: stub sys.modules before importing modules with heavy top-level imports"

key-files:
  created:
    - web-enhanced/tests/__init__.py
    - web-enhanced/tests/test_scanner.py
  modified:
    - web-enhanced/scanner.py

key-decisions:
  - "Allowlist approach for URL sanitization (http/https only) rather than blocklist — allowlist is safer and future-proof"
  - "tmp_path = None before try block ensures finally: is safe even if NamedTemporaryFile() raises"
  - "Stub maigret top-level imports in test file to enable test isolation without full maigret install"
  - "Added from __future__ import annotations to scanner.py for Python 3.9 compatibility in test env"

patterns-established:
  - "_safe_url() pattern: single-responsibility helper wrapping all URL sanitization in one place"
  - "Test isolation pattern: sys.modules stub before heavy-dependency module import"

requirements-completed: [STAB-02, STAB-04]

duration: 12min
completed: "2026-05-08"
---

# Phase 1 Plan 01: XSS URL Sanitization and Temp File Leak Fixes Summary

**_safe_url() http/https allowlist applied to profile URLs in scanner.py, plus try/finally temp file cleanup for PDF and HTML exports, with 10-test pytest suite covering both fixes**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-08T12:59:00Z
- **Completed:** 2026-05-08T13:11:37Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `_safe_url()` helper that allows only http/https schemes — closes the XSS sink where javascript:, data:, vbscript:, file: URLs could reach the browser via profile href attributes
- Applied `_safe_url()` to `status.site_url_user` in `get_found_profiles()`, the single serialization point for profile URLs
- Wrapped PDF and HTML export branches with `try/finally` using `tmp_path = None` guard — temp files in /tmp are deleted even when `save_pdf_report()` or `save_html_report()` raises
- Created 10-test pytest suite covering all URL scheme rejection/allowance cases and both exception-path cleanup scenarios

## Task Commits

Each task was committed atomically:

1. **Task 1: Add _safe_url helper and fix get_found_profiles XSS sink** - `d236afb` (fix)
2. **Task 2: Create test suite for scanner fixes** - `f424103` (test)

**Plan metadata:** (committed with SUMMARY.md)

## Files Created/Modified

- `web-enhanced/scanner.py` - Added `from __future__ import annotations`, `from urllib.parse import urlparse`, `_safe_url()` helper, applied to `get_found_profiles`, wrapped pdf/html export branches with try/finally cleanup
- `web-enhanced/tests/__init__.py` - Package marker (empty file)
- `web-enhanced/tests/test_scanner.py` - 10 tests: 8 for `_safe_url()` (javascript, data, vbscript, file rejection; http, https allowance; empty, None); 2 for temp file cleanup on exception (pdf, html)

## Decisions Made

- **Allowlist over blocklist:** Used `scheme in ("http", "https")` rather than blocking known bad schemes. Allowlists are closed by default — new bad schemes don't slip through.
- **tmp_path = None before try:** Initialising to None before the try block means the finally: clause can safely check `if tmp_path` even when `NamedTemporaryFile()` itself raises.
- **Test stub pattern:** Maigret's `__init__.py` raises `ImportError` if any dependency is missing at import time. Tests stub the entire `maigret.*` namespace in `sys.modules` before importing `scanner`, enabling CI without the full maigret install.
- **from __future__ import annotations:** Added to scanner.py so `list[str] | None` type hints work under Python 3.9 (project targets 3.10+ but test environment was 3.9).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Stubbed maigret sys.modules to unblock test collection**
- **Found during:** Task 2 (Create test suite)
- **Issue:** `scanner.py` imports `from maigret.sites import MaigretDatabase` at module level. `maigret/__init__.py` raises `ImportError` unless all runtime deps (aiodns, aiohttp, curl-cffi, socid-extractor, etc.) are installed. The test environment (Python 3.9, system pip) could not satisfy the full dependency tree.
- **Fix:** Added `sys.modules.setdefault` stubs for `maigret`, `maigret.sites`, `maigret.notify`, `maigret.result`, `maigret.checking`, `maigret.report` at the top of `test_scanner.py` before the `from scanner import ...` line. Also provided a minimal `MaigretCheckStatus` enum stub so scanner internals that compare against it work correctly.
- **Files modified:** `web-enhanced/tests/test_scanner.py`
- **Verification:** `python3 -m pytest web-enhanced/tests/test_scanner.py -x -v --noconftest` — 10 passed
- **Committed in:** f424103 (Task 2 commit)

**2. [Rule 3 - Blocking] Added from __future__ import annotations for Python 3.9 compat**
- **Found during:** Task 2 (first test run)
- **Issue:** `list[str] | None` syntax in scanner.py function signatures raises `TypeError` on Python 3.9 (requires 3.10+). Test environment is Python 3.9.
- **Fix:** Added `from __future__ import annotations` to scanner.py — makes all annotations lazy strings, no runtime evaluation.
- **Files modified:** `web-enhanced/scanner.py`
- **Verification:** Module imports successfully under Python 3.9; all tests pass
- **Committed in:** f424103 (Task 2 commit — scanner.py staged alongside test files)

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking)
**Impact on plan:** Both fixes necessary to unblock test execution. No behavior change to production code. Test isolation is correct — the stubs do not mask real maigret behavior because the tested functions (_safe_url, generate_export) only use maigret as a module-level name; the patch("scanner.report") context manager in cleanup tests overrides it correctly.

## Issues Encountered

None beyond the two Rule 3 deviations documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- STAB-02 (XSS URL sanitization) closed — profile URLs sanitized at serialization point
- STAB-04 (temp file leaks) closed — both pdf and html export paths have try/finally cleanup
- Test suite in `web-enhanced/tests/` is ready for CI integration
- Plan 01-02 (SSE/server.py stability) can execute independently — scanner.py public interface unchanged

---
*Phase: 01-stability-and-security*
*Completed: 2026-05-08*
