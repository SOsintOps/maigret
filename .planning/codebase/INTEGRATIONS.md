# External Integrations

**Analysis Date:** 2026-05-06

## APIs & External Services

**Social Media & Web Profiles:**
- 3154+ external websites checked for username presence
  - SDK/Client: Custom aiohttp-based checker (`maigret/checking.py`)
  - Sites database: `maigret/resources/data.json`
  - Examples: Facebook, Twitter, LinkedIn, Instagram, GitHub, etc.

**Site-Specific Activation:**
- Twitter (X) - Guest token acquisition for API access
  - Implementation: `maigret/activation.py:ParsingActivator.twitter()`
- Vimeo - JWT token authentication
  - Implementation: `maigret/activation.py:ParsingActivator.vimeo()`
- OnlyFans - HMAC-SHA1 signature generation with timestamp
  - Implementation: `maigret/activation.py:ParsingActivator.onlyfans()`
  - Signing rules rotated upstream weekly; cached in activation data
- Weibo - Multi-stage visitor token generation
  - Implementation: `maigret/activation.py:ParsingActivator.weibo()`

**Profile Data Extraction:**
- socid-extractor 0.0.27-0.0.28 - Extract profile information from discovered pages
  - SDK: `socid_extractor` Python package
  - Usage: `maigret/maigret.py:extract_ids_from_page()`
  - Extracts: usernames, user IDs, email addresses, phone numbers

**Anti-Bot Detection & Bypass:**
- cloudscraper 1.2.71 - Bypass Cloudflare DDoS protection
  - Used in: `maigret/submit.py`
  - Handles: Cloudflare challenges, bot detection evasion
- curl-cffi 0.14+ - TLS fingerprinting and JA3 spoofing
  - Used for: Realistic client simulation, anti-fingerprinting

## Data Storage

**Databases:**
- No persistent database - In-memory site definitions from JSON
  - Sites database: `maigret/resources/data.json` (embedded, ~1.2 MB)
  - Format: JSON with sites, engines, tags sections
  - Load mechanism: `maigret/sites.py:MaigretDatabase.load_from_path()`
  - Update source: GitHub raw content endpoint (configurable)

**File Storage:**
- Local filesystem only
  - Reports: Configurable output directory (default: `./reports`)
  - Settings: User config in `~/.maigret/settings.json` (XDG/home-based)
  - Cookies: Mozilla cookie jar format from `cookies.txt`

**Caching:**
- None - No external cache service used
- In-memory result caching during search session only

## Authentication & Identity

**Site Activation:**
- Custom activation handlers for protected sites
  - Location: `maigret/activation.py`
  - Methods: Token fetching, signature generation, cookie handling
  - Sites supported: Twitter, Vimeo, OnlyFans, Weibo

**Cookie Management:**
- Mozilla format cookie jar import (`http.cookiejar.MozillaCookieJar`)
- aiohttp cookie jar conversion (`aiohttp.CookieJar`)
- Import mechanism: `maigret/activation.py:import_aiohttp_cookies()`
- Persisted in: `cookies.txt` (Netscape format)

**Proxy Authentication:**
- SOCKS5/SOCKS4 via aiohttp-socks
- Support for authenticated proxies (username:password in URL)
- Tor proxy: `socks5://127.0.0.1:9050` (default)
- I2P proxy: `http://127.0.0.1:4444` (default)

**API Keys:**
- OpenAI API integration (optional AI analysis feature)
  - Key source: `OPENAI_API_KEY` environment variable or `settings.json`
  - Model: `gpt-4o` (configurable as `openai_model`)
  - Endpoint: `https://api.openai.com/v1` (configurable as `openai_api_base_url`)
  - Usage: `maigret/ai.py` - Post-search analysis and summarization

## Monitoring & Observability

**Error Tracking:**
- None detected - No external error tracking service (Sentry, Rollbar, etc.)
- Local logging via Python `logging` module

**Logs:**
- Console output via `logging` module
- Colored output support via `colorama`
- Configurable log level: `logging.WARNING` (default in web), adjustable
- Logging location: `maigret/maigret.py` (CLI), `maigret/web/app.py` (Flask)

**Progress Tracking:**
- Terminal progress bar via `alive-progress` library
- Toggleable via `show_progressbar` setting

## CI/CD & Deployment

**Hosting:**
- PyPI package distribution
- GitHub releases (source + wheels)
- Docker images via GitHub Actions workflow
- Snap packages (snapcraft.yaml)

**CI Pipeline:**
- GitHub Actions: `.github/workflows/`
  - `python-package.yml` - Linting, testing across Python 3.10-3.14
  - `python-publish.yml` - PyPI package publication
  - `pyinstaller.yml` - Standalone executable build
  - `build-docker-image.yml` - Docker container builds
  - `update-site-data.yml` - Automated site database refresh
  - `codeql-analysis.yml` - Security code analysis

**Package Distribution:**
- PyPI: `maigret` package
- Executable command: `maigret` (via setuptools entry point)
- Utility command: `update_sitesmd` (for manual database updates)

## Environment Configuration

**Required env vars:**
- `OPENAI_API_KEY` - Optional, for AI analysis feature only

**Optional env vars:**
- `FLASK_HOST` - Web interface bind address (default: `127.0.0.1`)
- `FLASK_PORT` - Web interface port (default: `5000`)
- `FLASK_SECRET_KEY` - Flask session encryption key (auto-generated if not set)
- `FLASK_DEBUG` - Debug mode toggle (default: `False`)

**Secrets location:**
- `.env` file support: Not detected in codebase
- Settings file: User-provided `settings.json` may contain `openai_api_key`
- Recommendation: Exclude `settings.json` with secrets from version control

## Webhooks & Callbacks

**Incoming:**
- Web interface form submission: Flask routes in `maigret/web/app.py`
  - `/search` - Username search form
  - `/submit` - Database submission form
  - Report download endpoints

**Outgoing:**
- None detected - No outbound webhooks or callbacks
- GitHub API calls for site database updates (via URL fetch, not webhooks)

## Data Flow Integrations

**Search Pipeline:**
1. User submits username via CLI or web interface
2. Username validated against configured patterns
3. Sites fetched from `maigret/resources/data.json`
4. Concurrent aiohttp requests to 3154+ sites (configurable subset)
5. Responses parsed by `SimpleAiohttpChecker` or engine-specific handlers
6. Extracted data via `socid_extractor` (optional)
7. Reports generated in multiple formats (HTML, PDF, JSON, CSV, etc.)
8. Optional AI analysis via OpenAI API

**Site Protection Handling:**
- Cloudflare: `cloudscraper` bypass
- TLS fingerprinting: `curl-cffi` JA3 spoofing
- Rate limiting: Configurable timeouts and retries
- User-Agent rotation: Random agents from `utils.get_random_user_agent()`

**Database Auto-Update:**
- Remote check: `https://raw.githubusercontent.com/soxoj/maigret/main/maigret/resources/db_meta.json`
- Frequency: Configurable via `autoupdate_check_interval_hours` (default: 24)
- Disabled by default: `no_autoupdate` setting
- Integrity check: SHA256 hash verification (`data_sha256` in meta)

---

*Integration audit: 2026-05-06*
