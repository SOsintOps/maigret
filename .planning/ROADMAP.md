# Roadmap: Maigret Web Enhanced

## Overview

The prototype is functionally complete. This milestone delivers visual parity with mockup.html and a stable, secure server. Work proceeds in strict dependency order: server stability and security first (a leaking server makes visual testing impossible), CSS architecture second (writing new rules into a flat file without @layer creates debt that blocks later phases), then layout shells, results components, and finally the D3 graph which requires stable container dimensions.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Stability and Security** - Fix SSE memory leak, XSS sink, asyncio task reference, and temp file leaks; migrate to FastAPI native SSE
- [ ] **Phase 2: CSS Architecture** - Establish @layer foundation, self-host Inter font, and set design tokens before any visual parity work
- [ ] **Phase 3: Layout and Search Panel** - Match header, progress bar, target tabs, and search modal overlay to mockup
- [ ] **Phase 4: Results Components** - Match summary cards, result tabs, profiles table, export cards, tags heatmap, notes, raw JSON, and toasts to mockup
- [ ] **Phase 5: Graph Polish** - Fix D3 simulation teardown, add node tooltip, and match graph controls to mockup

## Phase Details

### Phase 1: Stability and Security
**Goal**: The server runs cleanly through full scan sessions without memory leaks, does not expose XSS sinks, and uses FastAPI native SSE
**Depends on**: Nothing (first phase)
**Requirements**: STAB-01, STAB-02, STAB-03, STAB-04, BACK-01, BACK-02
**Success Criteria** (what must be TRUE):
  1. A client that disconnects mid-scan does not leave an orphaned SSE generator or growing queue in memory
  2. A profile URL containing a javascript: protocol is not rendered as a clickable link
  3. An asyncio scan task running in the background survives garbage collection until the scan completes
  4. Cancelling or crashing a scan does not leave temporary export files on disk
  5. The SSE endpoint uses FastAPI native EventSourceResponse; sse-starlette is removed from requirements.txt
**Plans:** 4 plans

Plans:
**Wave 1**
- [x] 01-01-PLAN.md — XSS URL sanitization and temp file cleanup in scanner.py
- [x] 01-02-PLAN.md — Update requirements.txt (pin FastAPI, remove sse-starlette)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-03-PLAN.md — SSE migration to EventSourceResponse and asyncio task GC fix in server.py

**Wave 3** *(gap closure — blocked on Wave 2 completion)*
- [ ] 01-04-PLAN.md — Fix fastapi.sse blocker: revert SSE to StreamingResponse, add behavioral disconnect tests

**Wave 3 — Gap Closure** *(fixes verification blocker from 01-03)*
- [ ] 01-04-PLAN.md — Fix fastapi.sse import blocker: revert to StreamingResponse SSE, update requirements.txt pin, add behavioral disconnect tests

### Phase 2: CSS Architecture
**Goal**: The stylesheet is structured with named @layer blocks and verified design tokens before any new visual rules are written
**Depends on**: Phase 1
**Requirements**: CSSF-01, CSSF-02, CSSF-03
**Success Criteria** (what must be TRUE):
  1. style.css opens with a single @layer declaration listing all six named layers in order
  2. The Inter font loads from a local WOFF2 file with no Google Fonts network request
  3. Every colour, spacing, radius, and typography value in the stylesheet matches the corresponding value in mockup.html
**Plans**: TBD
**UI hint**: yes

### Phase 3: Layout and Search Panel
**Goal**: The header, progress bar, target tabs, and search panel modal match the mockup layout exactly
**Depends on**: Phase 2
**Requirements**: LAYT-01, LAYT-02, LAYT-03, LAYT-04, LAYT-05
**Success Criteria** (what must be TRUE):
  1. The header title, subtitle, and New Scan button are positioned and styled identically to the mockup
  2. The progress bar shows a gradient fill, correct stats row, and transitions cleanly between running and complete states as in the mockup
  3. Target tabs display count badges with purple background and correct hover and active states matching the mockup
  4. Clicking New Scan opens the search panel as a centred modal overlay, not inline, matching mockup positioning
  5. Tag cloud chips in the search panel display included tags in purple and excluded tags in red with strikethrough
**Plans**: TBD
**UI hint**: yes

### Phase 4: Results Components
**Goal**: Every results component (summary cards, tabs, profiles table, export cards, tags heatmap, notes, raw JSON, toasts) matches the mockup visually and interactively
**Depends on**: Phase 3
**Requirements**: RESL-01, RESL-02, RESL-03, RESL-04, RESL-05, RESL-06, RESL-07, RESL-08
**Success Criteria** (what must be TRUE):
  1. Summary cards render in a 4-column grid with correct label sizing and colour coding matching the mockup
  2. Result tabs show a purple underline on the active tab and a green badge on the Found tab as in the mockup
  3. The profiles table has correct column widths, row hover state, star button, and response time colour coding (green under 0.5s, amber 0.5-1.0s, red over 1.0s)
  4. Export cards render in a grid with format title, description, and correct hover state; tags heatmap cards show tag name, count, and proportional bar
  5. Live hit toasts appear at bottom-right, animate with fadeInUp and fadeOut, and show no more than 2 at a time
**Plans**: TBD
**UI hint**: yes

### Phase 5: Graph Polish
**Goal**: The D3 graph tears down cleanly on re-render, shows a node hover tooltip, and matches mockup controls and fullscreen behaviour
**Depends on**: Phase 4
**Requirements**: GRPH-01, GRPH-02, GRPH-03
**Success Criteria** (what must be TRUE):
  1. Switching away from the graph tab and back does not produce ghost-ticking or jank from a previous simulation
  2. Hovering a graph node shows a tooltip with the node ID and URL where available
  3. The zoom in, zoom out, reset, and fullscreen controls match mockup positioning and styling
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Stability and Security | 3/4 | Gap closure planned | - |
| 2. CSS Architecture | 0/TBD | Not started | - |
| 3. Layout and Search Panel | 0/TBD | Not started | - |
| 4. Results Components | 0/TBD | Not started | - |
| 5. Graph Polish | 0/TBD | Not started | - |
