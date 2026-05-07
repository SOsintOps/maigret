# Testing Patterns

**Analysis Date:** 2026-05-06

## Test Framework

**Runner:**
- `pytest` (latest 8.3.4–9.x compatible; specified in `pyproject.toml`)
- Config: `pytest.ini` in repo root
- Config: `asyncio_mode=auto` enables automatic event loop handling for async tests

**Assertion Library:**
- Python's built-in `assert` statements (no pytest-specific assertion library)
- Comparison: `assert result == expected_value`

**Mocking:**
- `mock` library (fallback to `unittest.mock.Mock` if unavailable; pattern in `checking.py`)
- `pytest-httpserver` for HTTP mocking (used in `test_checking.py`)
- Custom async mock contexts (see `test_checking.py` fixture pattern)

**Run Commands:**
```bash
coverage run --source=./maigret,./maigret/web -m pytest tests       # Run all tests with coverage
pytest --lf -vv                                                       # Rerun last failed tests verbosely
coverage report -m                                                    # View coverage summary
coverage html                                                         # Generate HTML coverage report
```

**Coverage Tool:**
- `pytest-cov` (version 6–7)
- Coverage sources: `./maigret` and `./maigret/web` directories
- Output: terminal report and HTML report in `htmlcov/` directory

## Test File Organization

**Location:**
- Tests co-located in `/mnt/h/github/maigret/tests/` directory (separate from source)
- One test file per major module: `test_checking.py`, `test_sites.py`, `test_errors.py`, etc.

**Naming:**
- Test files: `test_<module>.py` (e.g., `test_maigret.py`, `test_checking.py`)
- Test functions: `test_<feature_or_behavior>()` (e.g., `test_checking_by_status_code`, `test_notify_about_errors`)
- Test fixtures: declared with `@pytest.fixture` decorator (see `conftest.py`)

**Structure:**
```
tests/
├── conftest.py                # Shared fixtures (db, settings, httpserver)
├── test_activation.py         # Activation parsing tests
├── test_checking.py           # Site checking logic tests (async)
├── test_cli.py                # CLI argument parsing tests
├── test_data.py               # Data loading/validation tests
├── test_db_updater.py         # Database update mechanism tests
├── test_errors.py             # Error detection and grouping tests
├── test_executors.py          # Async executor tests
├── test_maigret.py            # Main search logic tests (async)
├── test_notify.py             # Result notification tests
├── test_permutator.py         # Username permutation tests
├── test_report.py             # Report generation tests
├── test_settings.py           # Settings loading tests
├── test_sites.py              # Site database tests
├── test_submit.py             # Site submission tests
├── test_twitter.py            # Twitter-specific tests
├── test_utils.py              # Utility function tests
├── test_web.py                # Web interface tests
├── db.json                    # Test database (small, ~100 sites)
├── local.json                 # Local server test database (minimal)
└── __init__.py
```

## Test Structure

**Suite Organization:**

Test files use a flat function-per-feature structure with pytest markers for categorization:

```python
# From test_checking.py
@pytest.mark.slow
@pytest.mark.asyncio
async def test_checking_by_status_code(httpserver, local_test_db):
    sites_dict = local_test_db.sites_dict
    
    site_result_except(httpserver, 'claimed', status=200)
    site_result_except(httpserver, 'unclaimed', status=404)
    
    result = await search('claimed', site_dict=sites_dict, logger=Mock())
    assert result['StatusCode']['status'].is_found() is True
```

**Patterns:**
- Setup: Fixtures inject dependencies (test databases, HTTP servers, loggers)
- Execution: Call the function under test with fixtures
- Assertion: Use simple `assert` statements to verify behavior
- Teardown: Automatic via fixture scope (`@pytest.fixture(scope='function')`)

**Fixture Types (from `conftest.py`):**

1. **Database fixtures:**
   - `default_db()` — Full production database (`scope='session'`)
   - `test_db()` — Test database from `tests/db.json` (`scope='function'`)
   - `local_test_db()` — Minimal local test database (`scope='function'`)

2. **Configuration fixtures:**
   - `settings()` — Loaded settings object (`scope='session'`)
   - `argparser()` — CLI argument parser (`scope='session'`)

3. **Server fixtures:**
   - `httpserver` — pytest-httpserver mock HTTP server (auto-provided)
   - `httpserver_listen_address()` — Configure server port (custom override for port 8989)
   - `cookie_test_server()` — Async aiohttp test server for cookie tests

4. **Cleanup fixtures:**
   - `reports_autoclean()` — Auto-removes test report files before/after each test (`autouse=True`)

**Example fixture:**
```python
@pytest.fixture(scope='function')
def test_db():
    return MaigretDatabase().load_from_file(TEST_JSON_FILE)

@pytest.fixture(autouse=True)
def reports_autoclean():
    remove_test_reports()
    yield
    remove_test_reports()
```

## Mocking

**Framework:** `mock` library (fallback to `unittest.mock`)

**Patterns:**

1. **Logger mocking (most common):**
   ```python
   from mock import Mock
   logger = Mock()
   result = await search('username', site_dict=sites_dict, logger=logger)
   ```

2. **HTTP server mocking:**
   ```python
   def site_result_except(server, username, **kwargs):
       query = f'id={username}'
       server.expect_request('/url', query_string=query).respond_with_data(**kwargs)
   
   @pytest.mark.asyncio
   async def test_checking_by_status_code(httpserver, local_test_db):
       site_result_except(httpserver, 'claimed', status=200)
       # Test code follows
   ```

3. **Async mock contexts (custom pattern):**
   ```python
   class FakeSession:
       async def __aenter__(self):
           return self
       
       async def __aexit__(self, exc_type, exc, tb):
           pass
       
       async def get(self, **kwargs):
           return FakeResponse(...)
   ```

**What to Mock:**
- External HTTP calls (via `httpserver`)
- Logging (via `Mock()`)
- Time-dependent operations
- File I/O (for data-loading tests)

**What NOT to Mock:**
- Internal business logic (test the actual implementation)
- Database loading (use `test_db` fixture instead)
- Result enumeration (test against real `MaigretCheckStatus` values)

## Fixtures and Factories

**Test Data:**

1. **Example result dict (from `conftest.py`):**
   ```python
   RESULTS_EXAMPLE = {
       'Reddit': {
           'cookies': None,
           'parsing_enabled': False,
           'url_main': 'https://www.reddit.com/',
           'username': 'Skyeng',
       },
       'GooglePlayStore': {
           'cookies': None,
           'http_status': 200,
           'is_similar': False,
           'parsing_enabled': False,
           'rank': 1,
           'url_main': 'https://play.google.com/store',
           'url_user': 'https://play.google.com/store/apps/developer?id=Skyeng',
           'username': 'Skyeng',
       },
   }
   ```

2. **Test database example (from `test_sites.py`):**
   ```python
   EXAMPLE_DB: Dict[str, Any] = {
       'engines': {
           "XenForo": {
               "presenseStrs": ["XenForo"],
               "site": {
                   "absenceStrs": ["The specified member cannot be found."],
                   "checkType": "message",
                   "url": "{urlMain}{urlSubpath}/members/?username={username}",
               },
           },
       },
       'sites': {
           "Amperka": {
               "engine": "XenForo",
               "rank": 121613,
               "tags": ["ru"],
               "urlMain": "http://forum.amperka.ru",
               "usernameClaimed": "adam",
               "usernameUnclaimed": "noonewouldeverusethis7",
           },
       },
   }
   ```

**Location:**
- Shared fixtures in `tests/conftest.py`
- Test data embedded in test files (EXAMPLE_DB in `test_sites.py`)
- Database files in repo: `tests/db.json`, `tests/local.json`

## Coverage

**Requirements:** No explicit target enforced in CI (coverage report generated but not gated)

**View Coverage:**
```bash
make test          # Runs pytest with coverage and prints summary
coverage html      # Generates htmlcov/index.html for detailed reports
```

**Current Coverage (from Makefile):**
- Sources tracked: `./maigret` and `./maigret/web`
- Report shows percentage per module and line-by-line coverage

## Test Types

**Unit Tests:**
- Scope: Individual functions and methods
- Approach: Test utility functions in isolation (e.g., `test_case_convert_*` in `test_utils.py`)
- Example: `test_notify_about_errors()` — tests error grouping and notification logic with pre-built result dicts

**Integration Tests:**
- Scope: Multi-component interactions
- Approach: Use test HTTP server and real database to verify checking logic
- Example: `test_checking_by_status_code()` — verifies HTTP response handling integrates with site detection

**E2E Tests:**
- Framework: Not formally used (no separate e2e test suite)
- Coverage: Manual testing via CLI commands documented in `CONTRIBUTING.md`
- Equivalent: Integration tests with httpserver fixtures approximate E2E behavior

## Common Patterns

**Async Testing:**

All async tests require `@pytest.mark.asyncio` and `async def`:

```python
@pytest.mark.asyncio
async def test_curl_cffi_strips_random_user_agent_to_let_impersonation_drive_ua(fake_curl_cffi):
    checker = CurlCffiChecker()
    checker.prepare(url='https://example.com', headers={'User-Agent': 'Custom'})
    await checker.check()
    # Assertions on checker state
```

**Mark Categories:**

- `@pytest.mark.slow` — Tests that take seconds to run (database self-checks, executor tests)
- `@pytest.mark.asyncio` — Async test functions (required for `async def` tests)
- Marked tests sorted with slow tests deferred via custom `pytest_collection_modifyitems()` hook

**Error Testing:**

Tests verify error detection by building result dicts with `CheckError` objects:

```python
def test_notify_about_errors():
    results = {
        'site1': {
            'status': MaigretCheckResult(
                '', '', '', MaigretCheckStatus.UNKNOWN, error=CheckError('Captcha')
            )
        },
    }
    notifications = notify_about_errors(results, query_notify=None, show_statistics=True)
    assert ('Too many errors of type "Captcha" (25.0%)', '!') in notifications
```

**Executor Testing:**

Tests verify async execution by creating task lists and checking result order/timing:

```python
@pytest.mark.asyncio
async def test_simple_asyncio_executor():
    tasks: List[Tuple[Callable, list, dict]] = [(func, [n], {}) for n in range(10)]
    executor = AsyncioSimpleExecutor(logger=logger)
    assert await executor.run(tasks) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert executor.execution_time > 0.2
    assert executor.execution_time < 1.0
```

## Test Configuration

**pytest.ini:**
```ini
[pytest]
filterwarnings =
    error
    ignore::UserWarning
    ignore:codecs.open\(\) is deprecated:DeprecationWarning:xmind.core.saver
asyncio_mode=auto
```

**Warning filters:**
- `error` — Treat all warnings as errors (strict)
- `ignore::UserWarning` — Suppress UserWarning category
- `ignore:codecs.open...` — Suppress XMind library deprecation warning

**Markers (custom):**
- `slow` — Long-running tests (deferred during collection)
- `asyncio` — Async test functions (pytest-asyncio)

## Imports in Tests

**Standard pattern (from test files):**
```python
import pytest
from mock import Mock
from maigret import search
from maigret.checking import (
    detect_error_page,
    extract_ids_data,
    parse_usernames,
)
from maigret.result import MaigretCheckResult, MaigretCheckStatus
from maigret.sites import MaigretSite
```

---

*Testing analysis: 2026-05-06*
