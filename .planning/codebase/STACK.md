# Technology Stack

**Analysis Date:** 2026-05-06

## Languages

**Primary:**
- Python 3.10+ (3.10, 3.11, 3.12, 3.13, 3.14 supported) - Core username reconnaissance engine

## Runtime

**Environment:**
- Python 3.10 and above (CPython)
- Linux, macOS, Windows (via WSL or native)

**Package Manager:**
- Poetry
- Lockfile: `poetry.lock` (present)

## Frameworks

**Core:**
- Flask 3.1.1 (with async extras) - Web interface for search operations
- aiohttp 3.12.14 - Asynchronous HTTP client for concurrent site checking
- asyncio (stdlib) - Async runtime and event loop management

**Web Enhancement:**
- FastAPI 0.115.0+ - Alternative async web framework (in `web-enhanced/`)
- Uvicorn 0.34.0+ - ASGI server for FastAPI
- sse-starlette 2.0.0+ - Server-sent events for streaming responses

**Templating:**
- Jinja2 3.1.6 - HTML templating for reports

**Testing:**
- pytest 8.3.4+ - Test runner and framework
- pytest-asyncio 1.0.0 - Async test support
- pytest-cov 6.0+ - Coverage measurement
- pytest-httpserver 1.0.0 - Mock HTTP server for testing
- pytest-rerunfailures 15.1+ - Flaky test retries

**Build/Dev:**
- black (25.1+) - Code formatter
- flake8 7.1.1 - Linter
- mypy 1.14.1 - Type checker
- tuna 0.5.11 - Profiling visualization

**Documentation:**
- Sphinx - Documentation generation
- sphinx-copybutton - Copy button for code blocks
- sphinx_rtd_theme - ReadTheDocs theme

## Key Dependencies

**Critical:**
- socid-extractor 0.0.27-0.0.28 - Profile data extraction from web pages
- requests 2.32.4 - Synchronous HTTP client for specific operations
- requests-futures 1.0.2 - Concurrent request execution
- aiohttp-socks 0.10.1-0.11.x - SOCKS proxy support for aiohttp
- PySocks 1.7.1 - Low-level SOCKS proxy handling

**HTML/Content Parsing:**
- lxml 6.0.2+ - XML/HTML parsing and processing
- BeautifulSoup4 (via html5lib) - HTML parsing library
- chardet 5-7 - Character encoding detection
- soupsieve 2.6 - CSS selector support for parsing
- html5lib 1.1 - HTML5 parser

**Report Generation:**
- xhtml2pdf 0.2.11 - PDF report generation from HTML
- reportlab 4.4.3 - PDF creation and manipulation
- XMind 1.2.0 - XMind mind map format support
- networkx 2.6.3+ - Graph data structure for relationship mapping
- pyvis 0.3.2 - Network visualization

**Infrastructure:**
- aiohttp-socks 0.10.1+ - SOCKS5/SOCKS4 proxy support
- stem 1.8.1 - Tor network controller and interaction
- torrequest 0.1.0 - Tor-based HTTP requests
- cloudscraper 1.2.71 - Bypass Cloudflare anti-bot protection
- curl-cffi 0.14-0.x - cURL bindings for TLS fingerprinting

**Utilities:**
- colorama 0.4.6 - Cross-platform coloured terminal text
- alive-progress 3.2.0 - Progress bar display
- Markupsafe 3.0.2 - String escaping for templating
- pycountry 24.6.1+ - Country/language data
- python-bidi 0.6.3 - Bi-directional text support
- arabic-reshaper 3.0.0 - Arabic text shaping
- requests-toolbelt 1.0.0 - Extended HTTP utilities
- certifi 2025.6.15+ - Root CA certificate bundle
- idna 3.4 - Internationalized domain names
- multidict 6.6.3 - Multi-value dictionary
- yarl 1.20.1 - URL handling
- webencodings 0.5.1 - Web encoding support
- future 1.0.0 - Python 2/3 compatibility (legacy)
- PyPDF2 3.0.1 - PDF reading/writing
- attrs 25.3-26 - Class decoration utilities
- mock 5.1.0 - Mocking library (fallback for Python <3.3)
- typing-extensions 4.14.1 - Additional typing features
- async-timeout 5.0.1 - Async operation timeouts
- aiodns 3-4 - Async DNS resolution
- asgiref 3.9.1 - ASGI sync/async utilities
- platformdirs 4.3.8 - Platform-specific directory paths
- dateutil - Date parsing and timezone handling
- six 1.17.0 - Python 2/3 compatibility utilities

## Configuration

**Environment:**
- Settings via JSON files: `~/.maigret/settings.json` or project-local `settings.json`
- Fallback: `maigret/resources/settings.json` (bundled defaults)
- Flask web interface: `FLASK_HOST`, `FLASK_PORT`, `FLASK_SECRET_KEY`, `FLASK_DEBUG` env vars
- OpenAI integration: `OPENAI_API_KEY` env var (optional for AI analysis)
- Proxy configuration via environment or settings: `proxy_url`, `tor_proxy_url`, `i2p_proxy_url`

**Build:**
- `pyproject.toml` - Poetry project manifest with all dependencies
- `pytest.ini` - Pytest configuration with filter warnings
- `.readthedocs.yaml` - ReadTheDocs build config (Python 3.10, Sphinx)
- `snapcraft.yaml` - Snap package manifest
- `.github/workflows/` - GitHub Actions CI/CD

**Database:**
- `maigret/resources/data.json` - Embedded site definitions (3154+ sites)
- `maigret/resources/db_meta.json` - Database metadata (version, update info)
- Sites updatable from remote: `https://raw.githubusercontent.com/soxoj/maigret/main/maigret/resources/data.json`

## Platform Requirements

**Development:**
- Python 3.10+ interpreter
- Poetry package manager
- libcairo2-dev (system dependency for reportlab PDF generation on Ubuntu/Linux)
- Git (for repository operations)

**Production:**
- Python 3.10+ runtime
- Access to external sites (unless offline mode)
- Optional: Tor daemon (for Tor proxy functionality)
- Optional: I2P gateway (for I2P proxy functionality)
- Optional: OpenAI API key (for AI analysis features)

---

*Stack analysis: 2026-05-06*
