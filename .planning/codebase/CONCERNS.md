# Codebase Concerns

**Analysis Date:** 2026-05-06

## Tech Debt

**Inconsistent HTTP Client Usage:**
- Issue: Codebase mixes async (aiohttp) and synchronous (requests) HTTP clients. The primary checking logic uses async aiohttp, but multiple modules use synchronous requests for specific operations.
- Files: `maigret/activation.py`, `maigret/db_updater.py`, `maigret/sites.py`, `maigret/submit.py`
- Impact: Creates threading/event loop complications, potential deadlocks when async code calls sync requests, reduced performance in async context, harder to maintain concurrent request handling.
- Fix approach: Convert all synchronous requests to async using aiohttp ClientSession. Prioritize `activation.py` (Twitter, Vimeo, OnlyFans, Weibo activation methods) and `db_updater.py` (database update fetches). This requires refactoring activation methods to be async.

**Deprecated Executor Classes:**
- Issue: Multiple executor classes in `maigret/executors.py` are marked as deprecated but still present (AsyncExecutor, AsyncioSimpleExecutor, AsyncioProgressbarExecutor, AsyncioProgressbarSemaphoreExecutor).
- Files: `maigret/executors.py` lines 23-100
- Impact: Dead code path, maintenance burden, potential confusion for future developers, unclear which executor should be used.
- Fix approach: Remove deprecated classes once verification confirms `AsyncioProgressbarQueueExecutor` handles all use cases. Update any code still referencing old classes.

**Incomplete Async Implementation in Activation:**
- Issue: ParsingActivator methods that require HTTP requests are marked with TODO comments for async conversion (`# TODO: async call` at line 397 in checking.py). Currently blocking synchronous activation happens during async checking flow.
- Files: `maigret/checking.py` line 397, `maigret/activation.py`
- Impact: Blocks event loop during site activation, prevents effective parallelization, degrades performance when activation is needed.
- Fix approach: Convert ParsingActivator methods to async, replace synchronous requests with aiohttp. Test thoroughly with Twitter and OnlyFans where activation is common.

**Mixed Event Loop Access Patterns:**
- Issue: Both `asyncio.run()` and `asyncio.get_event_loop()` used in different files, inconsistent patterns for obtaining event loop.
- Files: `maigret/maigret.py` lines 960-962, `maigret/executors.py` line 17, `maigret/checking.py` line 188, `maigret/__main__.py` line 12
- Impact: Python 3.10+ deprecation warnings, fragile behavior across Python versions, potential "no running event loop" errors in nested async contexts.
- Fix approach: Use `asyncio.run()` consistently at entry points. For library code, use `asyncio.get_running_loop()` to access the current loop instead of creating new ones.

## Security Issues

**SSL Certificate Verification Disabled:**
- Issue: Multiple locations disable SSL certificate verification with `ssl.CERT_NONE`.
- Files: `maigret/checking.py` line 145, `maigret/submit.py` lines 70-72
- Impact: Vulnerability to man-in-the-middle (MITM) attacks. Credentials, search results, and personal information transmitted over HTTPS can be intercepted and modified.
- Fix approach: Remove `ssl.CERT_NONE` settings. If certificate validation fails for legitimate sites, use proper certificate bundling (certifi) or site-specific workarounds. Document any sites requiring SSL bypass and explore alternatives (proxies, cookies, different endpoints).

**Synchronous Requests Used for SSL Bypass:**
- Issue: CloudflareSession in `maigret/submit.py` uses `cloudscraper` library which manages cloudflare challenges but mixes async/sync context.
- Files: `maigret/submit.py` lines 21-40
- Impact: SSL bypass workaround potentially compromised if requests are not properly validated. Complicates audit of security practices.
- Fix approach: Evaluate curl-cffi (already in dependencies at line 82 of pyproject.toml) as async alternative to cloudscraper. Use curl_cffi.requests.AsyncSession for Cloudflare handling.

**Dynamic Import Usage:**
- Issue: `__import__('ssl')` used instead of standard import.
- Files: `maigret/submit.py` lines 70, 72
- Impact: Code obfuscation, harder to trace dependencies, potential avenue for code injection if input is ever used (currently safe but bad practice).
- Fix approach: Replace `__import__('ssl')` with standard `import ssl` at module level.

## Known Issues and Bugs

**Error Type Checking Incomplete:**
- Issue: `detect()` function in `maigret/errors.py` checks for error indicators using simple string containment in HTML. Multiple error detection patterns are strings but no regex support.
- Files: `maigret/errors.py` lines 107-111, 31-70
- Impact: Fragile error detection, prone to false positives/negatives. Bot protection changes slightly and detection breaks. Service-specific error messages may be missed.
- Trigger: Sites update error page templates, new bot protection added, HTML structure changes.
- Workaround: Manually update error strings in COMMON_ERRORS dict, but this requires ongoing maintenance.

**Timeout Handling Inconsistency:**
- Issue: Default timeout of 0 in SimpleAiohttpChecker (line 63, 71) means "no timeout". CurlCffiChecker defaults to 10 seconds (line 260). Tests use various timeout values without documented defaults.
- Files: `maigret/checking.py` lines 63, 71, 231, 239, 260
- Impact: Some requests may hang indefinitely, inconsistent behavior across checker types, testing may not reflect production timeouts.
- Fix approach: Define timeout constants at module level. Use consistent defaults (suggest 10-15 seconds for web requests). Document timeout semantics (0 = no limit, or use None explicitly for clarity).

**Incomplete Result Logging:**
- Issue: `debug_response_logging()` function at line 334 of checking.py writes debug info to a file 'debug.log' in current working directory without path validation.
- Files: `maigret/checking.py` lines 334-339
- Impact: Hardcoded path, debug logs may end up in wrong location, log file grows unbounded, potential permission errors in restricted directories.
- Fix approach: Use standard logging module with file handler instead of manual file I/O. Configure via logging.config.

**Self-Check Auto-Disable Logic:**
- Issue: Auto-disable feature in `checking.py` can disable sites without user confirmation, but disabled state not always persisted correctly.
- Files: `maigret/checking.py` lines 1121-1199, especially 1194-1199
- Impact: Sites may be unexpectedly disabled on next run. The logic at lines 1195-1199 has unclear intent (checking if total_disabled >= 0 but disabling/enabling based on sign).
- Fix approach: Clarify intent. If purpose is to show difference (disabled-disabled_old_count), fix logic. Add explicit user confirmation for auto-disable. Add undo mechanism or backup of original state.

## Performance Bottlenecks

**Large Files with Mixed Concerns:**
- Issue: `maigret/checking.py` is 1255 lines, `maigret/maigret.py` is 970 lines, `maigret/report.py` is 718 lines. These modules mix multiple concerns.
- Files: `maigret/checking.py`, `maigret/maigret.py`, `maigret/report.py`
- Impact: Difficult to test individual components, high cognitive load, slow to navigate, changes in one area affect many functions.
- Improvement path: Extract checker implementations into separate files per checker type (SimpleAiohttpChecker, CurlCffiChecker). Extract report generation into focused modules. Consider extracting CLI argument parsing into separate module.

**Synchronous String Checking in Event Loop:**
- Issue: `detect_error_page()` at line 306 uses simple string matching on full HTML response synchronously while called from async context.
- Files: `maigret/checking.py` lines 306-331, called from line 383
- Impact: Blocks event loop momentarily for large HTML responses. With thousands of concurrent requests, these small blocks compound.
- Improvement path: Compile regex patterns instead of substring matching. Cache compiled patterns at module level. Consider moving pattern matching to async task if response is very large.

**Database Loading at Runtime:**
- Issue: MaigretDatabase loaded from JSON file for every request in web app (line 46 of `maigret/web/app.py`) instead of once at startup.
- Files: `maigret/web/app.py` lines 43-65
- Impact: Redundant JSON parsing on every search request, file I/O overhead, wasted computation.
- Improvement path: Load database once during Flask app initialization. Use Blueprints or app context to share database instance.

## Fragile Areas

**Activation Marker Detection:**
- Issue: ParsingActivator checks for activation marks (strings in HTML) at line 388. If HTML doesn't contain expected marks but site still needs activation, it won't trigger.
- Files: `maigret/checking.py` lines 388-398
- Impact: Activation may silently fail for some sites. Results may be marked as "not found" when they're actually inaccessible due to missing activation.
- Safe modification: Add explicit activation logging, compare expected vs actual behavior. Test against live sites. Add fallback activation if first attempt fails.
- Test coverage: Minimal coverage for activation path. Test only covers twitter in `tests/test_activation.py`.

**Site Engine Updates:**
- Issue: Site inherits from engine definition at line 507 in `sites.py`. If engine properties conflict with site-specific properties, order of application unclear.
- Files: `maigret/sites.py` lines 500-516, especially `update_from_engine()` method
- Impact: Unexpected property values, inheritance surprises when modifying data.json or adding sites.
- Safe modification: Document property inheritance order explicitly. Add tests for property precedence. Consider making engine properties immutable after site creation.

**JSON Parsing with ast.literal_eval:**
- Issue: Uses `ast.literal_eval()` instead of proper JSON parsing in multiple places (maigret.py line 90, report.py line 191, checking.py line 1238, utils.py line 75).
- Files: `maigret/maigret.py` line 90, `maigret/report.py` line 191, `maigret/checking.py` line 1238, `maigret/utils.py` line 75
- Impact: ast.literal_eval doesn't properly handle JSON strings with escaped characters. Works only for Python literals, not all valid JSON. Confusing to maintainers.
- Safe modification: Use `json.loads()` for JSON data. Reserve ast.literal_eval only for Python code parsing if needed.

**Flask Secret Key Generation:**
- Issue: `maigret/web/app.py` line 24 generates random secret key on each app restart if FLASK_SECRET_KEY not set.
- Files: `maigret/web/app.py` line 24
- Impact: Session tokens invalid after app restart, user sessions lost, debugging harder, security implications if sessions store credentials.
- Safe modification: Generate secret key once at startup and store in configuration file or use secure environment variable. Add warning if key not set explicitly.

## Test Coverage Gaps

**Checker Implementation Testing:**
- What's not tested: CurlCffiChecker implementation and fallback behavior not covered. Edge cases in timeout handling, error page detection with real site responses limited.
- Files: `maigret/checking.py` lines 200-300 (CurlCffiChecker class)
- Risk: Fallback checker may silently fail, curl-cffi integration broken without detection, Cloudflare challenges not properly handled.
- Priority: High - core checking logic

**Async/Await Patterns:**
- What's not tested: Edge cases in AsyncioProgressbarQueueExecutor worker management, timeout handling in `wait_for()` calls, proper cleanup on exceptions.
- Files: `maigret/executors.py` lines 134-160
- Risk: Resource leaks (unclosed tasks), race conditions in worker shutdown, progress bar hangs.
- Priority: High - affects all parallel operations

**Database Update Logic:**
- What's not tested: Corruption recovery if update partially completes, fallback to bundled database if fetch fails, version comparison edge cases.
- Files: `maigret/db_updater.py` lines 95-175
- Risk: Update process could leave database in bad state, users stuck with old data if update fails.
- Priority: Medium - affects data freshness but not core search

**Activation Methods:**
- What's not tested: Complete test coverage for OnlyFans, Vimeo, Weibo activation (test_activation.py only has twitter and vimeo partial coverage).
- Files: `maigret/activation.py` lines 34-83, 85-118
- Risk: Activation changes upstream, implementation breaks silently, site checking fails for authenticated-required profiles.
- Priority: Medium - affects subset of sites

**Error Page Detection:**
- What's not tested: False positive/negative rates for detect_error_page(), edge cases for custom error messages, 403 handling with ignore403 flag.
- Files: `maigret/checking.py` lines 306-331
- Risk: Sites incorrectly classified as found/not found, false matches on common error patterns.
- Priority: Medium - affects result accuracy

## Dependencies at Risk

**Deprecated Packages:**
- Issue: `requests` library maintained but superseded by `httpx` in many projects. `requests` not async-native.
- Files: Used throughout codebase (maigret/activation.py, maigret/db_updater.py, etc.)
- Impact: Reduces opportunity for parallelization, inconsistent with async design goal.
- Migration plan: Replace with `httpx` which supports both sync and async. Requires API changes but minimal (mostly method names). httpx 1.x is stable.

**curl-cffi Version Pinning:**
- Issue: `curl-cffi` pinned to `>=0.14,<1.0` but major version 1.0 may have breaking changes.
- Files: `pyproject.toml` line 82
- Impact: Fragile version constraint, may break on minor curl-cffi releases, maintenance burden to update.
- Migration plan: Review curl-cffi 1.0 breaking changes when available. Update version constraint and test thoroughly. Consider whether curl-cffi is critical (used only for Cloudflare bypass).

**cloudscraper Library:**
- Issue: `cloudscraper` package at 1.2.71 depends on requests. Maintenance status unclear.
- Files: `maigret/submit.py` line 9, used in CloudflareSession
- Impact: If cloudscraper unmaintained, Cloudflare bypass may break silently when protection updates.
- Migration plan: Evaluate curl-cffi.CloudflareSolver or migrate to puppeteer/playwright for sites requiring JavaScript rendering. Timeline: monitor cloudscraper updates quarterly.

**Future Annotations Import:**
- Issue: `future-annotations` package installed (pyproject.toml line 49) but Python 3.10+ has this built-in via `from __future__ import annotations`.
- Files: Not actively used based on grep
- Impact: Unnecessary dependency, can be removed after removing future-annotations imports.
- Migration plan: Replace with `from __future__ import annotations` at top of files using type hints. Remove future-annotations from dependencies.

## Missing Critical Features

**Structured Logging:**
- Problem: Codebase uses logging module inconsistently. Some modules use print() for output (65 instances found), others use logging. No structured logging framework.
- Blocks: Cannot easily parse logs for monitoring, debugging with logs difficult, no correlation IDs for distributed tracing.
- Fix: Implement structured logging with JSON output option. Replace all print() with logging.info/warning/error. Add request IDs to track searches.

**Configuration Management:**
- Problem: Hardcoded paths (MAIGRET_HOME, CACHED_DB_PATH, BUNDLED_DB_PATH in db_updater.py). Cookies file path hardcoded in web/app.py.
- Blocks: Difficult to deploy in non-standard environments, cannot relocate databases, container deployments need workarounds.
- Fix: Implement proper configuration hierarchy (env vars -> config file -> defaults). Use configparser or similar for config files.

**Result Caching:**
- Problem: No caching of search results. Every re-run fetches from all sites again.
- Blocks: Cannot reuse expensive results, no offline mode, performance poor for repeated searches.
- Fix: Implement optional caching layer with TTL. Store in local SQLite or similar. Consider privacy implications (what to cache, how to encrypt).

**Batch Operations:**
- Problem: Web API accepts single username only (maigret_search takes one username). Must call API repeatedly for multiple usernames.
- Blocks: Inefficient for searches involving lists of usernames, no transaction support.
- Fix: Add batch search endpoint accepting list of usernames, return all results in one response.

---

*Concerns audit: 2026-05-06*
