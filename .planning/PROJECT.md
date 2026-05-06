# Maigret Web Enhanced

## What This Is

A standalone FastAPI web interface for maigret that provides real-time OSINT username scanning with SSE progress streaming, D3.js network graph visualisation, and multi-format report export. Lives in `web-enhanced/` alongside the existing Flask UI without replacing it.

## Core Value

An OSINT analyst can scan usernames across thousands of sites through a browser, see results appear in real time, and export findings, all without touching the command line.

## Requirements

### Validated

- ✓ FastAPI server with SSE progress streaming — existing
- ✓ Maigret scanner wrapper with async queue-based progress — existing
- ✓ Multi-username scanning with target tabs — existing
- ✓ Found profiles table with star, site, URL, tags, response time — existing
- ✓ D3.js force-directed network graph — existing
- ✓ Tag-based site filtering (include/exclude) — existing
- ✓ Export in CSV, JSON, TXT, PDF, HTML — existing
- ✓ Raw JSON viewer — existing
- ✓ Investigation notes textarea — existing
- ✓ Live hit toast notifications — existing
- ✓ Advanced options (recursive parsing, top sites, timeout) — existing

### Active

- [ ] Visual parity with mockup.html (layout, spacing, colours, interactions)
- [ ] Search panel centred modal behaviour matching mockup
- [ ] Progress bar states (running, complete) matching mockup presentation
- [ ] Target tab styling and count badges matching mockup
- [ ] Summary cards grid layout matching mockup
- [ ] Result tabs styling and active states matching mockup
- [ ] Profiles table column widths and hover states matching mockup
- [ ] Graph panel controls and fullscreen behaviour matching mockup
- [ ] Tags heatmap grid cards matching mockup
- [ ] Export cards grid layout matching mockup
- [ ] Notes textarea styling matching mockup
- [ ] Live hit toast position and animation matching mockup
- [ ] Search panel advanced options (tag clouds, checkboxes) matching mockup
- [ ] Stability and error handling for all scan states

### Out of Scope

- Replacing or modifying the existing Flask UI in `maigret/web/` — separate project
- New features not present in the mockup — future milestone
- Mobile-first responsive redesign — mockup is desktop-focused
- Authentication or multi-user sessions — single-user local tool
- Persistent storage of scan results — in-memory only, matching current behaviour

## Context

The `web-enhanced/` directory contains a working FastAPI prototype built against the mockup design. The functional code (`index.html` + `app.js` + `server.py` + `scanner.py`) implements all features but has visual drift from the mockup reference (`mockup.html`). The CSS (`style.css`) is shared between both.

The maigret engine is fully async (`checking.maigret()`), making FastAPI + SSE the natural fit. The existing `scanner.py` wraps maigret's `QueryNotify` interface to push per-site progress events through an `asyncio.Queue`.

Key files:
- `web-enhanced/server.py` — FastAPI routes, SSE endpoint, export handler
- `web-enhanced/scanner.py` — Maigret wrapper, progress tracking, graph/export generation
- `web-enhanced/static/index.html` — Functional frontend
- `web-enhanced/static/mockup.html` — Visual reference (static, fake data)
- `web-enhanced/static/app.js` — Frontend application logic
- `web-enhanced/static/style.css` — Shared stylesheet
- `web-enhanced/requirements.txt` — Python dependencies

## Constraints

- **Stack**: FastAPI + vanilla JS + D3.js. No frontend build tools, no npm, no React/Vue.
- **Dependency**: Must use maigret's public API (`maigret.checking.maigret()`, `maigret.sites.MaigretDatabase`, `maigret.report`). No monkey-patching internals.
- **Standalone**: Runs independently of the Flask UI. No shared state between the two.
- **Visual fidelity**: The mockup.html is the design spec. The final product must match it closely.
- **Browser support**: Modern browsers (Chrome, Firefox, Edge). No IE11.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI over Flask | Maigret engine is async; FastAPI avoids thread bridging hacks | — Pending |
| Standalone in web-enhanced/ | Avoids breaking upstream Flask UI; can be merged later | — Pending |
| Vanilla JS, no framework | Mockup is already vanilla; no build step needed | — Pending |
| Mockup as design spec | Single source of truth for visual design | — Pending |
| Improve existing code, not rewrite from mockup | Functional code is 90% there; less rework | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason
2. Requirements validated? Move to Validated with phase reference
3. New requirements emerged? Add to Active
4. Decisions to log? Add to Key Decisions
5. "What This Is" still accurate? Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check, still the right priority?
3. Audit Out of Scope, reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-06 after initialisation*
