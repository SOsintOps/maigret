# Codebase Structure

**Analysis Date:** 2026-05-06

## Directory Layout

```
maigret/ (project root)
├── maigret/                    # Main package
│   ├── __init__.py             # Public API exports (search, cli, MaigretDatabase)
│   ├── __main__.py             # Entry point (python -m maigret)
│   ├── maigret.py              # CLI main function, argument parsing
│   ├── checking.py             # Core search orchestration and checkers
│   ├── sites.py                # Site database and models
│   ├── result.py               # Result/status enums and MaigretCheckResult
│   ├── errors.py               # Error detection and classification
│   ├── notify.py               # Progress and result notifications
│   ├── report.py               # Report generation (HTML, PDF, CSV, JSON, etc.)
│   ├── executors.py            # Async task execution (queue, semaphore)
│   ├── settings.py             # Settings loader from JSON files
│   ├── submit.py               # Site database submission tool
│   ├── db_updater.py           # Auto-update checker for site database
│   ├── activation.py           # Site-specific activation (Twitter guest token, etc.)
│   ├── ai.py                   # AI analysis (OpenAI-compatible API)
│   ├── permutator.py           # Username permutation (john doe → johndoe, etc.)
│   ├── utils.py                # Utilities (case conversion, URL parsing, etc.)
│   ├── types.py                # Type aliases
│   ├── resources/              # Data and templates
│   │   ├── data.json           # Site database (3000+ sites)
│   │   ├── db_meta.json        # Database metadata (version, update timestamp)
│   │   ├── settings.json       # Default settings
│   │   ├── ai_prompt.txt       # Prompt for AI analysis
│   │   ├── simple_report.tpl   # HTML report template
│   │   └── simple_report_pdf.tpl  # PDF report template
│   └── web/                    # Flask web UI
│       ├── app.py              # Flask application
│       ├── templates/          # Jinja2 templates
│       │   ├── base.html       # Base template
│       │   ├── index.html      # Search form
│       │   ├── results.html    # Results display
│       │   └── status.html     # Status page
│       └── static/             # Static assets
│           └── maigret.png     # Logo
├── web-enhanced/               # New FastAPI web UI (WIP)
│   ├── server.py               # FastAPI application
│   ├── scanner.py              # Search engine interface
│   └── static/                 # Frontend assets
├── tests/                      # Test suite
│   ├── test_maigret.py         # CLI and main function tests
│   ├── test_checking.py        # Checker and search logic tests
│   ├── test_sites.py           # Site database tests
│   ├── test_submit.py          # Submit tool tests
│   ├── test_report.py          # Report generation tests
│   ├── test_web.py             # Web UI tests
│   ├── test_db_updater.py      # Database updater tests
│   └── data.json               # Test site database
├── docs/                       # Sphinx documentation
│   ├── source/                 # RST documentation files
│   │   ├── conf.py             # Sphinx config
│   │   ├── installation.rst
│   │   ├── usage-examples.rst
│   │   ├── features.rst
│   │   └── ...
│   └── Makefile                # Build documentation
├── utils/                      # Utility scripts for maintainers
│   ├── update_site_data.py     # Generate sites.md and db metadata
│   ├── site_check.py           # Test site configuration
│   ├── import_sites.py         # Convert from Sherlock format
│   ├── check_top_n.py          # Rank sites by traffic
│   └── fp_probe_top_sites.py   # Fingerprint top sites
├── pyinstaller/                # PyInstaller config for EXE builds
├── static/                     # Static assets (logo, samples)
├── pyproject.toml              # Poetry dependency spec
├── poetry.lock                 # Locked dependency versions
├── pytest.ini                  # Pytest configuration
├── Makefile                    # Build targets
├── Dockerfile                  # Docker image config
├── CHANGELOG.md                # Release history
├── CONTRIBUTING.md             # Contributing guide
└── sites.md                    # Auto-generated site list
```

## Directory Purposes

**`maigret/`:**
- Purpose: Main package with all search logic
- Contains: Core async search, checkers, site database, reports
- Key files: `checking.py` (the heart), `sites.py` (site data model), `maigret.py` (CLI)

**`maigret/resources/`:**
- Purpose: Bundled data and templates
- Contains: `data.json` (3000+ site configurations), report templates, AI prompt
- Key files: `data.json` (required for all searches), `simple_report.tpl` (HTML template)

**`maigret/web/`:**
- Purpose: Flask-based web UI (original)
- Contains: Flask app, Jinja2 templates, static assets
- Key files: `app.py` (Flask routes), `templates/results.html` (results display)

**`web-enhanced/`:**
- Purpose: Modern FastAPI replacement (work-in-progress)
- Contains: FastAPI server, real-time progress via SSE, modern frontend
- Key files: `server.py` (FastAPI app), `scanner.py` (search interface)
- Status: Not yet integrated into CLI; separate startup required

**`tests/`:**
- Purpose: Unit and integration tests
- Contains: Test files mirroring package structure
- Key files: `test_checking.py` (largest, core logic), `test_report.py` (report tests)

**`docs/`:**
- Purpose: Sphinx documentation (published to ReadTheDocs)
- Contains: RST files for installation, usage, API docs
- Key files: `source/conf.py` (build config), `source/index.rst` (main doc)

**`utils/`:**
- Purpose: Maintenance and build scripts for developers
- Contains: Site data updater, site testers, importers
- Key files: `update_site_data.py` (regenerate metadata from `data.json`)

## Key File Locations

**Entry Points:**
- `maigret/__main__.py` — `python -m maigret`; imports and runs `maigret.main()`
- `maigret/maigret.py:main()` — Main CLI function; argument parsing, search invocation
- `maigret/__init__.py` — Public API exports; `from maigret import search`
- `maigret/web/app.py` — Flask web UI; `maigret --web 5000`

**Configuration:**
- `maigret/resources/settings.json` — Default settings (timeout, retries, proxy, etc.)
- `maigret/settings.py` — Settings loader; searches `~/.maigret/settings.json`, CWD, package defaults
- `pyproject.toml` — Dependency spec; Python 3.10+, aiohttp, socid_extractor, Jinja2, reportlab
- `pytest.ini` — Pytest config; test discovery, markers

**Core Logic:**
- `maigret/checking.py` — Search orchestration, HTTP checkers, site checks (1255 lines)
- `maigret/sites.py` — Site database, MaigretSite model, filtering by tags/rank (716 lines)
- `maigret/result.py` — MaigretCheckResult and MaigretCheckStatus enum
- `maigret/errors.py` — Error detection, classification, user solutions

**Data Processing:**
- `maigret/resources/data.json` — Site database (3000+ sites); loaded at startup
- `maigret/resources/db_meta.json` — Metadata (version, last update, download URL)
- `maigret/db_updater.py` — Auto-update logic; checks for newer DB once per 24 hours

**Reports:**
- `maigret/report.py` — Report generation (HTML, PDF, CSV, JSON, TXT, XMind, Graph) (718 lines)
- `maigret/resources/simple_report.tpl` — Jinja2 HTML report template
- `maigret/resources/simple_report_pdf.tpl` — WeasyPrint PDF template
- `maigret/resources/simple_report_pdf.css` — PDF styling

**Notifications & Output:**
- `maigret/notify.py` — Progress bars, result display via QueryNotify interface
- `maigret/utils.py` — ASCII tree display, case conversion, URL utilities

**Special Features:**
- `maigret/ai.py` — OpenAI-compatible API client for result summarization
- `maigret/activation.py` — Site-specific setup (Twitter guest token, OnlyFans signing)
- `maigret/permutator.py` — Username permutation (e.g., "john doe" → "johndoe", "john_doe")
- `maigret/submit.py` — Tool for submitting new site data to upstream

**Testing:**
- `tests/test_checking.py` — Core search logic (467 lines)
- `tests/test_report.py` — Report generation tests (685 lines)
- `tests/test_sites.py` — Site database tests
- `tests/data.json` — Mock site database for tests

## Naming Conventions

**Files:**
- `maigret.py` — Main module (singular, semantic name)
- `checking.py` — Logic domain (verb-based, semantic)
- `report.py` — Output domain (singular)
- `test_*.py` — Tests mirror source structure (test_checking.py → checking.py)

**Directories:**
- `maigret/` — Package (single underscore-free name)
- `resources/` — Data/templates directory
- `tests/` — Test root
- `web/` — Web UI sub-package
- `utils/` — Utility scripts

**Functions:**
- `async def maigret(...)` — Main async search function
- `def main()` — CLI entry point
- `async def check_site_for_username(...)` — Per-site checker
- `async def _make_request(...)` — Private helper (underscore prefix)

**Classes:**
- `MaigretCheckResult` — Result data class (CamelCase)
- `MaigretSite` — Site model (CamelCase)
- `MaigretDatabase` — Site database manager (CamelCase)
- `QueryNotifyPrint` — Notification interface implementation (CamelCase)

**Type Aliases:**
- `QueryResultWrapper = Dict[str, Any]` — Results dictionary
- `QueryOptions = Dict[str, Any]` — Search options
- `QueryDraft = Tuple[Callable, List, Dict]` — Task tuple for executor

## Where to Add New Code

**New Search Feature (e.g., additional ID extraction):**
- Primary code: `maigret/checking.py` — Add logic to `extract_ids_data()` or `update_results_info()`
- Tests: `tests/test_checking.py` — Add test for new extraction logic
- Site data: `maigret/resources/data.json` — If requires new site fields (e.g., "extract_email")

**New Checker Implementation (e.g., SOCKS support):**
- Primary code: `maigret/checking.py` — Subclass `CheckerBase`, implement `prepare()` and `check()` methods
- Integrate: `checking.maigret()` function (lines 814–835) — Add to `options["checkers"]` dict
- Tests: `tests/test_checking.py` — Mock the new checker class

**New Report Format (e.g., YAML export):**
- Primary code: `maigret/report.py` — Add `save_yaml_report()` function
- Template: `maigret/resources/` (if needed) — Add YAML template file
- CLI integration: `maigret/maigret.py` — Add `--yaml` argument and invoke `save_yaml_report()`
- Tests: `tests/test_report.py` — Test YAML generation

**New CLI Flag or Option:**
- Argument parser: `maigret/maigret.py:setup_arguments_parser()` (line 121) — Add `parser.add_argument()`
- Settings integration: `maigret/settings.py` — Add field to `Settings` class if user-configurable
- Pass through: `checking.maigret()` — Add parameter if affects search behavior
- Implementation: Wire in appropriate layer (checker, executor, report generator)

**Utilities/Helpers:**
- Shared helpers: `maigret/utils.py` — Case conversion, URL utilities
- Testing fixtures: `tests/conftest.py` (create if needed) — Shared test setup

**New Site Configuration:**
- Edit: `maigret/resources/data.json` — Add new site entry under "sites" key
- Format: Follow existing site structure (url, regexCheck, presenseStrs, absenceStrs, tags, etc.)
- Validation: Run `python utils/site_check.py` to validate
- Update: Run `python utils/update_site_data.py` to regenerate `sites.md` and metadata
- PR: Submit PR to main repo following CONTRIBUTING.md

## Special Directories

**`maigret/resources/`:**
- Purpose: Bundled data and templates
- Generated: No (hand-maintained)
- Committed: Yes
- Auto-update: `data.json` auto-downloads newer version if available (once per 24 hours); fallback to bundled copy

**`tests/`:**
- Purpose: Test suite
- Generated: No
- Committed: Yes
- Run: `pytest` (all tests) or `pytest tests/test_checking.py` (single test file)

**`web-enhanced/`:**
- Purpose: Next-generation web UI
- Generated: No
- Committed: Yes
- Status: Work-in-progress; not yet integrated into main CLI

**Build Artifacts:**
- `.planning/` — (Not in original repo; created during session)
- `dist/`, `build/`, `*.egg-info/` — Generated by build system; in `.gitignore`
- `htmlcov/`, `.coverage` — Generated by pytest coverage; in `.gitignore`
- `sites.md` — Auto-generated by `utils/update_site_data.py`; committed for reference

## Module Import Patterns

**CLI entry imports core:**
```python
from .checking import maigret as search
from .sites import MaigretDatabase
from .settings import Settings
from .report import save_html_report
```

**Checkers import base:**
```python
from .checking import CheckerBase, SimpleAiohttpChecker, ProxiedAiohttpChecker
```

**Reports import utilities:**
```python
from .utils import CaseConverter, URLMatcher, is_country_tag
from .result import MaigretCheckStatus
```

**Avoid circular dependencies:**
- `checking.py` may import `sites.py` (one-way dependency)
- `sites.py` does not import `checking.py` (no reverse)
- `utils.py` imports nothing from package (self-contained)
- `result.py` is standalone (defines result models only)

---

*Structure analysis: 2026-05-06*
