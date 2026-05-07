# Coding Conventions

**Analysis Date:** 2026-05-06

## Naming Patterns

**Files:**
- Module files: `snake_case.py` (e.g., `checking.py`, `db_updater.py`)
- Web components: `app.py` for Flask application; feature modules follow snake_case pattern
- Utility modules: `utils.py`, `errors.py`, `result.py` (functional/data-oriented names)

**Functions:**
- Function names: `snake_case` (e.g., `detect_error_page`, `extract_ids_data`, `make_site_result`, `notify_about_errors`)
- Async functions: same `snake_case` convention (e.g., `async def check_site_for_username`)
- Private functions: prefix with underscore (e.g., `_make_request`, `_stream_response`)
- Type validation functions: `<resource>_<action>` (e.g., `timeout_check`)

**Variables:**
- Local variables: `snake_case` (e.g., `site_result`, `search_results`, `error_counts`, `request_method`)
- Module constants: `UPPER_CASE` (e.g., `SUPPORTED_IDS`, `BAD_CHARS`, `THRESHOLD`, `ERRORS_TYPES`)
- Type aliases: `snake_case` (e.g., `QueryResultWrapper`, `QueryOptions`)

**Classes:**
- All classes: `CamelCase` (e.g., `MaigretCheckResult`, `MaigretDatabase`, `CheckError`, `QueryNotify`, `ParsingActivator`)
- Status enums: `CamelCase` with `Status` suffix (e.g., `MaigretCheckStatus`)
- Private class attributes: prefix with underscore (e.g., `_type`, `_desc`, `_HTTP_URL_RE_STR`)

**Type Hints:**
- Use full typing module imports: `from typing import Dict, List, Any, Optional, Tuple`
- Return type hints on all functions: `def function() -> Type:`
- Generic containers: `Dict[str, Any]`, `List[str]`, `Optional[str]`, `Tuple[...]`

## Code Style

**Formatting:**
- Tool: `black` with `--skip-string-normalization` flag (preserves quote style)
- Line length: 127 characters max (per Makefile lint rules)
- Indentation: 4 spaces per level

**Linting:**
- Tool: `flake8`
- Configuration: `flake8 --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --ignore=E731,W503,E501`
- Ignored rules:
  - E731: do not assign lambda (acceptable for short callbacks)
  - W503: line break before binary operator (conflicts with black)
  - E501: line too long (handled by black)
- Type checking: `mypy --check-untyped-defs` enforces full type annotations

**Docstrings:**
- Module level: Triple-quoted strings at module top (e.g., `"""Maigret Sites Information"""`)
- Classes: Docstrings describing the class purpose (e.g., in `result.py`, `"""Describes result of checking a given username on a given site"""`)
- Methods: Detailed docstrings with "Keyword Arguments:" and "Return Value:" sections (see `notify.py` for pattern)
- Functions: Short docstrings for utility functions; no required docstrings for obvious private methods

## Import Organization

**Order (enforced in source files):**
1. Standard library imports (`import ast`, `import asyncio`, `import logging`, `from typing import ...`)
2. Third-party imports (`import aiodns`, `from aiohttp import ...`, `import pytest`)
3. Local imports (project-relative with dot notation: `from . import errors`, `from .sites import MaigretDatabase`)

**Example (from `checking.py`):**
```python
# Standard library imports
import ast
import asyncio
import logging
import random
import re
import ssl
import sys
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

# Third party imports
import aiodns
from alive_progress import alive_bar
from aiohttp import ClientSession, TCPConnector, http_exceptions

try:
    from mock import Mock
except ImportError:
    from unittest.mock import Mock

# Local imports
from . import errors
from .activation import ParsingActivator, import_aiohttp_cookies
from .errors import CheckError
```

**Path Aliases:**
- No path aliases configured; all relative imports use dot notation (`.module_name`)

**Type Hints (Special Imports):**
- `TYPE_CHECKING` used where circular imports would occur (not currently in use)
- String forward references used for self-referential types (e.g., `Optional["MaigretEngine"]`)

## Error Handling

**Patterns:**
- Custom exception classes: `CheckError` in `maigret/errors.py`; stores error type and description
- Error detection: `detect()` function scans HTML response text for known error patterns (cloudflare, bot protection, etc.)
- Error categorization: `ERRORS_TYPES` dict maps error type to user-facing solution text
- Temporary vs permanent errors: `TEMPORARY_ERRORS_TYPES` list identifies transient errors (timeouts, network failures)
- Error aggregation: `extract_and_group()` collects errors across all search results and computes percentages
- Exception handling: Try-catch blocks with specific exception types (`ClientConnectorError`, `ServerDisconnectedError`, `proxy_errors`)

**Example (from `errors.py`):**
```python
class CheckError:
    _type = 'Unknown'
    _desc = ''

    def __init__(self, typename, desc=''):
        self._type = typename
        self._desc = desc

    @property
    def type(self):
        return self._type

    @property
    def desc(self):
        return self._desc
```

## Logging

**Framework:** Python's built-in `logging` module

**Patterns:**
- Logger obtained via `Mock()` in test contexts (from `maigret.checking` imports)
- Debug response logging via `debug_response_logging(url, html_text, status_code, check_error)` function
- Progress tracking via `alive_progress` library's `alive_bar` context manager
- Logging levels follow standard hierarchy: DEBUG for verbose traces, INFO for user-facing messages, WARNING/ERROR for issues

## Comments

**When to Comment:**
- Explain *why* a decision was made, not *what* the code does (code should be self-documenting)
- Mark incomplete or known-issue areas with `# TODO:` or `# FIXME:` (search reveals ~20 TODO comments in codebase)
- Note non-obvious algorithm choices or workarounds (e.g., "TODO: checking for reason" in errors.py)

**Example (from `errors.py`):**
```python
# TODO: checking for reason
ERRORS_REASONS = {
    'Login required': 'Add authorization cookies through `--cookies-jar-file` (see cookies.txt)',
}
```

## Function Design

**Size:** No strict limit, but files with 1200+ lines (e.g., `checking.py` at 1255 lines) indicate dense, feature-rich modules that could benefit from refactoring; most utility functions are 10-50 lines

**Parameters:**
- Prefer explicit named parameters over `*args` or `**kwargs` where possible
- Use type hints for all parameters (e.g., `def prepare(self, url: str, headers=None, allow_redirects=True, timeout=0, method='get', payload=None)`)
- Keyword-only arguments for optional configuration (no leading `*` observed; positional args are acceptable for simple cases)

**Return Values:**
- Use type hints: `-> Optional[str]`, `-> List[Dict[str, Any]]`, `-> Tuple[Optional[str], int, Optional[CheckError]]`
- Return tuples for multiple values when related (e.g., response text, HTTP status, error object)
- Return None explicitly for no-op methods (e.g., `return None` in `prepare()`)

## Module Design

**Exports:**
- No explicit `__all__` declarations; all public symbols are importable
- Private modules/utilities not typically prefixed with underscore (convention is single-letter prefix for truly private classes/functions)

**Barrel Files:**
- No barrel files observed; imports use direct module paths (e.g., `from .sites import MaigretDatabase`)
- `__init__.py` in package directories typically empty or import CLI entry point

**Class Attributes:**
- Class-level defaults used to document expected attributes (e.g., in `MaigretSite`, all expected fields are declared as class variables with defaults)
- Attributes documented via inline comments (e.g., `# Username known to exist on the site`)

## Async/Await Patterns

**Async Functions:**
- Async context managers: `async def __aenter__()` and `async def __aexit__()` (see test fixtures)
- Task decoration: `@pytest.mark.asyncio` on all async test functions
- Execution: `AsyncioQueueGeneratorExecutor` for parallel site checks

**Example:**
```python
async def _make_request(self, session, url, headers, allow_redirects, timeout, method, logger, payload=None) -> Tuple[Optional[str], int, Optional[CheckError]]:
    # Implementation with await calls
```

## API/Data Structures

**Type Aliases (from `types.py`):**
- `QueryDraft = Tuple[Callable, List, Dict]` — a task tuple (function, args, kwargs)
- `QueryOptions = Dict[str, Any]` — flexible configuration dict
- `QueryResultWrapper = Dict[str, Any]` — search results dict (TODO: marked for refactor)

**Common Patterns:**
- Site data represented as `MaigretSite` objects with camelCase JSON field mapping (e.g., `urlMain` in JSON → `url_main` attribute via `CaseConverter`)
- Results represented as `MaigretCheckResult` objects with `json()` method for serialization
- Status represented as `MaigretCheckStatus` enum (CLAIMED, AVAILABLE, UNKNOWN, ILLEGAL)

---

*Convention analysis: 2026-05-06*
