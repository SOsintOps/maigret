# Architecture

**Analysis Date:** 2026-05-06

## System Overview

Maigret is an asynchronous OSINT tool that searches for usernames across 3000+ websites. It operates as a pipeline that orchestrates HTTP checks against a large site database, extracts information from discovered profiles, and generates multi-format reports.

```text
┌──────────────────────────────────────────────────────────────────────┐
│                          CLI / Web Interfaces                         │
│          `maigret.maigret` (CLI) / `maigret.web.app` (Flask)         │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Check Orchestrator                               │
│  `checking.maigret()` - Core async search function                   │
│  Executes checks, retries failures, aggregates results               │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    ┌─────────────────────────────────────────────┐
    │          Checker Implementations             │
    │  SimpleAiohttpChecker | ProxiedAiohttp      │
    │  AiodnsDomainResolver | CheckerMock         │
    │  `checking.py`                              │
    └──────────────┬──────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │   aiohttp ClientSession      │
        │   (with proxy support)       │
        └──────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │    Website Network Requests   │
        │    (HTTP/HTTPS/Tor/I2P)      │
        └──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────────┐  ┌──────────────────────┐
│ Information      │  │ Result Classification │
│ Extraction       │  │ (Claimed/Available)   │
│ socid_extractor  │  │ `result.py`           │
└──────────────────┘  └──────────────────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
        ┌──────────────────────────┐
        │  Recursive Search (opt)   │
        │  Extract new usernames    │
        │  Feed back to checker     │
        └──────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Report Generation                                 │
│   `report.py` - Multi-format outputs                                │
│   HTML | PDF | CSV | JSON | TXT | XMind | Graph                     │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **CLI Entry** | Argument parsing, invoke search | `maigret.maigret:main()` |
| **Search Orchestrator** | Coordinate checks across sites, manage retries, aggregate results | `checking.maigret()` |
| **Site Database** | Load site metadata, filter by tags/rank, manage site list | `sites.MaigretDatabase` |
| **HTTP Checkers** | Make requests to sites, handle proxies/Tor/I2P | `checking.SimpleAiohttpChecker`, `ProxiedAiohttpChecker` |
| **Executor** | Manage concurrent connections, queue tasks, track progress | `executors.AsyncioQueueGeneratorExecutor` |
| **Info Extractor** | Parse HTML responses for username/ID extraction | `socid_extractor` (external) |
| **Result Handler** | Store check outcomes (found/not found/error) | `result.MaigretCheckResult` |
| **Notifier** | Display progress and results to user | `notify.QueryNotifyPrint` |
| **Report Generator** | Convert results to HTML/PDF/CSV/JSON/etc. | `report.py` |
| **Settings Manager** | Load configuration from JSON files | `settings.Settings` |
| **Web UI** | Flask interface for running searches | `web.app` |

## Pattern Overview

**Overall:** Async producer-consumer with pluggable checkers and multi-format output generation.

**Key Characteristics:**
- **Asynchronous throughout** — `asyncio` event loop, all I/O is non-blocking
- **Pluggable checker architecture** — Swap HTTP checkers for Tor/I2P/DNS without changing core logic
- **Declarative site database** — 3000+ site configurations in `data.json`, no hardcoded URLs
- **Retry-on-failure** — Configurable retries for transient errors
- **Information extraction** — Leverages external `socid_extractor` to parse profiles and find additional IDs
- **Multi-protocol support** — Clearweb, Tor (SOCKS5), I2P, domain-level DNS checks

## Layers

**CLI/API Layer:**
- Purpose: User interaction entry points (command-line and web UI)
- Location: `maigret.maigret:main()`, `web.app`
- Contains: Argument parsing, request handling, output formatting
- Depends on: Core search function, settings, report generators
- Used by: End users, integrators (library imports)

**Search Orchestration Layer:**
- Purpose: Coordinate parallel checks, manage retries, aggregate results
- Location: `checking.maigret()`
- Contains: Task scheduling, progress tracking, result collection
- Depends on: Checkers, executors, notifiers
- Used by: CLI/Web interface

**Checking/Protocol Layer:**
- Purpose: Execute individual site checks via HTTP/Tor/I2P/DNS
- Location: `checking.SimpleAiohttpChecker`, `ProxiedAiohttpChecker`, `AiodnsDomainResolver`
- Contains: HTTP request logic, error detection, activation hooks
- Depends on: aiohttp, python_socks, aiodns
- Used by: Search orchestration layer

**Data Layer:**
- Purpose: Site metadata, results, settings
- Location: `sites.MaigretDatabase` (in-memory), `settings.Settings`, `resources/data.json`
- Contains: Site definitions, database update logic, user configuration
- Depends on: JSON file I/O, HTTP updates for auto-update
- Used by: Orchestration and checker layers

**Output Layer:**
- Purpose: Convert raw results to user-friendly formats
- Location: `report.py`, `notify.py`
- Contains: Report rendering (HTML/PDF/CSV), progress display
- Depends on: Jinja2 (templates), reportlab (PDF)
- Used by: CLI/Web interface

## Data Flow

### Primary Request Path

1. **Entry** (`maigret.main()` @ `maigret.py:350`) — Parse CLI args, load settings/database
2. **Database Load** (`sites.MaigretDatabase.load_from_path()` @ `sites.py:290`) — Read `data.json`, filter by tags/rank
3. **Search Invocation** (`checking.maigret()` @ `checking.py:746`) — Create executor, build check tasks
4. **Checker Preparation** (`SimpleAiohttpChecker.prepare()` @ `checking.py:67`) — Set up HTTP parameters per site
5. **Parallel Execution** (`AsyncioQueueGeneratorExecutor.run()` @ `executors.py:200+`) — Run concurrent checks with semaphore
6. **Per-Site Check** (`check_site_for_username()` @ `checking.py:350+`) — Issue HTTP request, classify response
7. **Result Classification** (`MaigretCheckResult` @ `result.py:32+`) — Mark as CLAIMED/AVAILABLE/UNKNOWN/ILLEGAL
8. **Extraction** (if enabled) — Pass HTML to `socid_extractor.extract()`, parse usernames/IDs (`checking.extract_ids_data()` @ `checking.py:1223`)
9. **Aggregation** (`checking.maigret()` return) — Collect all site results into dictionary
10. **Report Generation** (`report.save_html_report()` etc. @ `report.py:74+`) — Render output format
11. **Display** (`notify.QueryNotifyPrint.finish()` @ `notify.py:80+`) — Output results to user

**Key Variables:**
- `all_results: Dict[str, QueryResultWrapper]` — Site name → result object (populated incrementally)
- `tasks_dict: Dict[str, QueryDraft]` — Site name → (function, args, kwargs) tuples for executor

### Recursive Search Flow

1. Extract usernames from found profiles (`extract_ids_from_results()` @ `maigret.py:102`)
2. Parse URLs to find additional IDs (`db.extract_ids_from_url()` @ `sites.py:360+`)
3. Re-feed new IDs into search orchestrator with `--no-recursion` flag check
4. Repeat until no new IDs discovered

**State Management:**
- Mutable: `all_results` accumulates across retry attempts and recursive iterations
- Session-based: One `aiohttp.ClientSession` per checker, reused across all checks
- Async context: No thread-local state; task scheduling via `asyncio.gather()` with semaphore

## Key Abstractions

**MaigretSite:**
- Purpose: Represents a single site's check configuration
- Examples: `Facebook`, `Twitter`, `YouTube` in `data.json`
- Pattern: Dataclass-like with ~25 optional fields (url, headers, regex_check, tags, etc.)
- Location: `sites.MaigretSite` @ `sites.py:23`

**MaigretCheckResult:**
- Purpose: Outcome of a single site check
- Fields: username, site_name, url, status (enum), ids_data, error
- Pattern: Value object; one created per site per search
- Location: `result.MaigretCheckResult` @ `result.py:32`

**QueryResultWrapper:**
- Purpose: Type alias for aggregated search results
- Structure: `Dict[str, Dict[...]]` — site name to result metadata
- Pattern: Generic dict; not strongly typed
- Location: `types.QueryResultWrapper` @ `types.py:11`

**Checker Interface:**
- Purpose: Abstract protocol for site-checking implementations
- Implementations: `SimpleAiohttpChecker`, `ProxiedAiohttpChecker`, `AiodnsDomainResolver`, `CheckerMock`
- Pattern: Base `CheckerBase` class; overridden methods `prepare()`, `check()`, `close()`
- Location: `checking.CheckerBase` @ `checking.py:51+`

## Entry Points

**CLI:**
- Location: `maigret.maigret:main()` @ `maigret.py:350+`
- Triggers: `python -m maigret <username>` or direct execution
- Responsibilities: Parse args, load DB/settings, invoke search, handle output, manage web UI

**Library:**
- Location: `maigret.search()` (alias for `checking.maigret()`) @ `__init__.py:11`
- Triggers: `from maigret import search; await search(...)`
- Responsibilities: Core async search; returns `QueryResultWrapper` dict

**Web Interface:**
- Location: `maigret.web.app:maigret_search()` @ `web/app.py:43`
- Triggers: Flask HTTP POST to `/api/search`
- Responsibilities: Async search execution in background, progress tracking

## Architectural Constraints

- **Threading:** Single-threaded event loop (`asyncio`); all I/O via `aiohttp` (non-blocking). Web UI uses threads for background jobs.
- **Global state:** One-time DB load per run; site database is immutable after initialization. Settings are read-once.
- **Circular imports:** None detected; clean layering (maigret.py → checking.py → sites.py, no reverse dependencies).
- **Session reuse:** `aiohttp.ClientSession` created once per checker and reused for all site checks (connection pooling).
- **Semaphore-based concurrency:** `AsyncioQueueGeneratorExecutor` uses `asyncio.Semaphore` to limit simultaneous connections (default 100).
- **No shared mutable state across tasks:** Each site check is independent; results collected into thread-safe dict at end.

## Anti-Patterns

### Unbounded Concurrency Without Pool

**What happens:** Early versions allowed unlimited concurrent connections.  
**Why it's wrong:** Causes connection pool exhaustion, timeouts on large site databases.  
**Do this instead:** Use `AsyncioQueueGeneratorExecutor` with configurable `in_parallel` semaphore (default 100, tunable via `-n` flag).

### Synchronous Extraction in Async Loop

**What happens:** If `socid_extractor.extract()` were synchronous and long-running, it would block the event loop.  
**Why it's wrong:** Eliminates concurrency gains; stalls other site checks.  
**Do this instead:** Wrap in `asyncio.to_thread()` if extraction becomes blocking (not yet needed; extraction is fast).

### Hard-Coded Site URLs

**What happens:** Sites change URLs frequently; hard-coding breaks maintenance.  
**Why it's wrong:** Requires code changes for every site update.  
**Do this instead:** Externalize to `data.json`; auto-update via `db_updater.py` from GitHub (once per 24 hours by default).

### Retry Logic at Wrong Layer

**What happens:** If retries were per-task instead of orchestrated loop.  
**Why it's wrong:** Duplicate work; no centralized control; harder to reason about.  
**Do this instead:** Orchestrate retries in `checking.maigret()` loop (lines 869–914); check only failed sites on next attempt.

## Error Handling

**Strategy:** Graceful degradation with detailed error classification.

**Patterns:**
- **Detection:** `errors.detect()` scans response body for known error signatures (Cloudflare CAPTCHA, bot protection, censorship)
- **Tracking:** Each result includes optional `CheckError` object with `type` and `desc` fields
- **User feedback:** CLI displays error summary (% of checks affected) with mitigation suggestions
- **Temporary vs. permanent:** `errors.TEMPORARY_ERRORS_TYPES` list distinguishes retry-able failures (timeout, connection) from permanent (403, regex mismatch)

**Common Errors:**
- Cloudflare CAPTCHA/challenge → suggest different IP or proxy
- Bot protection → suggest timeout increase or reduced connections
- Censorship → suggest VPN or proxy
- HTTP 403 (Forbidden) → site may require auth; suggest cookies file

## Cross-Cutting Concerns

**Logging:** Python `logging` module; `logger` param passed through all functions. Set via `--debug` flag (sets `logging.DEBUG`).

**Validation:** URL regex via `MaigretSite.regex_check` (JavaScript regex); username validation before checking sites.

**Authentication:** Via cookies jar file (`--cookies-jar-file`); loaded into `aiohttp.CookieJar` and reused across all requests.

**Progress Tracking:** `alive_progress` library shows real-time progress bar during checks; disabled with `--no-progressbar` or in non-TTY environments.

**Rate Limiting:** Implicit via concurrency semaphore; no explicit per-site rate limiting (respects site robots.txt implicitly via user-agent and timeout).

---

*Architecture analysis: 2026-05-06*
