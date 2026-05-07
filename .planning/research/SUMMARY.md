# Project Research Summary

**Project:** Maigret Web Enhanced — OSINT real-time dashboard
**Domain:** FastAPI + vanilla JS SSE dashboard with D3.js network graph
**Researched:** 2026-05-06
**Confidence:** HIGH

## Executive Summary

Maigret Web Enhanced is a single-user, locally-hosted OSINT scanning dashboard that wraps the maigret CLI engine in a FastAPI server, streams progress over SSE, and visualises results in a D3.js force-directed graph. The prototype is functionally complete. The milestone goal is visual parity with mockup.html, not new features. Research confirms the stack is correct and requires no migration; the primary work is CSS layout refinement, one targeted SSE backend refactor, and a handful of stability fixes.

The recommended approach is to address two backend stability issues before any visual work: the SSE generator memory leak on client disconnect, and the fire-and-forget asyncio task lacking a strong reference. Both are small, targeted fixes. Visual parity work should then proceed in dependency order: design tokens first, then layout shells, then the search panel modal (the largest structural gap), then tabs and components in render-layer order. Upgrading FastAPI to 0.135.1 and migrating to native `fastapi.sse.EventSourceResponse` eliminates the `sse-starlette` dependency and gives automatic keepalives, typed events, and reconnect control.

The main risks are a `javascript:` XSS sink in all anchor `href` assignments (one-line fix, must happen before any sharing), CSS specificity debt accumulating during the visual parity phase (prevent by adopting `@layer` and a single-tier selector budget before writing new rules), and D3 simulation ghost-ticking on removed SVG nodes when the graph tab is re-entered (fix by stopping and nulling the simulation before creating a new one). None of these block progress if addressed in the correct phase order.

---

## Key Findings

### Recommended Stack

The existing stack (FastAPI, Uvicorn, D3.js 7, vanilla ES modules) is correct and requires no additions. The one meaningful upgrade is pinning FastAPI to 0.135.1, which ships native SSE support via `fastapi.sse`. This allows removal of `sse-starlette`, replaces the manual keepalive hack with an automatic 15-second ping, and adds typed event support (`ServerSentEvent(event="hit")`). Uvicorn should be upgraded to 0.41.0 with `[standard]` extras for uvloop and httptools. All other dependencies remain unchanged.

On the frontend, D3.js SVG rendering is appropriate for OSINT scan sizes (10-300 nodes); Canvas is not warranted. CSS `@layer` gives specificity control without a preprocessor, fitting the no-build-tooling constraint. Self-hosting Inter WOFF2 Latin subset (16 KB vs 95 KB) removes the Google Fonts DNS lookup.

**Core technologies:**
- FastAPI 0.135.1: ASGI framework with native SSE via `fastapi.sse` — eliminates sse-starlette dependency
- Uvicorn 0.41.0 [standard]: ASGI server with uvloop for local single-user throughput
- D3.js 7.9.0: Force-directed graph via CDN — SVG sufficient for scan node counts
- Vanilla JS ES modules: Single state singleton; no reactive framework warranted at this scope
- CSS `@layer`: Specificity control without a preprocessor or build step

### Expected Features

The prototype already implements all core features. Research identified one missing interaction (node hover tooltip on the graph) and several visual parity gaps between the functional app and mockup.html. The milestone scope is correcting those gaps, not adding new capability.

**Must have (table stakes — visual parity blockers):**
- Progress bar running/complete colour states matching mockup
- Target tab styling and live count badges
- Summary cards grid layout per target
- Profiles table column widths, hover states, and response time colour coding (green under 0.5s, amber 0.5-1.0s, red over 1.0s)
- Export cards grid with hover states and loading feedback
- Tags heatmap cards matching mockup
- Search panel as centred modal overlay (currently inline — largest structural gap)
- Live hit toast with correct position, animation, and link behaviour
- Node hover tooltip on graph (absent from prototype; most critical missing interaction)

**Should have (differentiators, this milestone where present in mockup):**
- Category colour coding on graph nodes by tag group
- Star filter ("Starred" button) actually filtering the table
- Notes scoped per target tab (currently shared textarea)

**Defer to future milestone:**
- Notes per target (requires state restructure)
- Scan parameter presets as saved profiles
- Recursive account discovery visualised in graph
- Any feature not present in mockup.html

### Architecture Approach

The architecture is a REST + SSE hybrid: POST to create a job, GET SSE stream for progress, REST endpoints for results, graph JSON, and exports. This is sound and well-structured. The critical patterns to preserve are: SSE lifecycle with explicit terminal state and `done` boolean guard; single active-target render dispatch through `renderCurrentTarget()`; D3 simulation full teardown before re-render; and the two-phase profile population (live partial objects during scan, full objects from REST after completion).

**Major components:**
1. HTTP router + job store (server.py) — request validation, job dispatch, in-memory ScanJob registry
2. SSE endpoint + ProgressNotify (server.py + scanner.py) — async queue drain, event formatting, keepalive
3. run_scan / get_graph_json / generate_export (scanner.py) — maigret engine orchestration, NetworkX graph build, report generation
4. Global state object + render pipeline (app.js) — single source of truth, explicit re-render dispatch on state change
5. D3 force graph component (app.js renderGraph) — simulation lifecycle, SVG teardown, node interaction

### Critical Pitfalls

1. **SSE generator memory leak on client disconnect** — `event_stream()` has no disconnect check; orphaned generators hold unbounded queues. Add `await request.is_disconnected()` poll inside the loop. Fix before any visual work.

2. **`javascript:` XSS in anchor href assignments** — Profile URLs are assigned directly to `a.href` without protocol validation. A modified `data.json` can inject executable code. Add a `safeHref()` wrapper that rejects any URL not starting with `http://` or `https://`. Fix before sharing.

3. **SSE onerror closes permanently on transient network errors** — Setting `done = true` on first `onerror` suppresses browser reconnection. Implement a reconnect counter with backoff before marking permanent failure.

4. **D3 simulation ghost-ticking after view switch** — The old simulation's `tick` closure fires on removed DOM nodes after re-render. Stop and null the simulation before creating a new one in `renderGraph()`.

5. **CSS specificity debt during visual parity work** — Without `@layer` and a single-tier selector budget, fixes compound into `!important` chains. Establish selector rules before writing any new CSS.

---

## Implications for Roadmap

Based on research, the dependency structure and pitfall severity dictate a clear phase order. Visual work is invalid if the server leaks memory and crashes mid-session. Security fixes are trivially small and must precede any sharing. CSS architecture must be agreed before writing new rules.

### Phase 1: Stability and Security Baseline

**Rationale:** Pitfalls 1, 2, 3, 8, and 10 are backend and security issues that corrupt testing if left unfixed. A memory-leaking server invalidates all visual testing. The XSS fix is one line. These must be resolved first.
**Delivers:** Reliable server that handles disconnect cleanly, safe URL rendering, reconnect-resilient SSE client, no temp file leaks.
**Addresses:** Pitfalls 1, 2, 3, 8, 10 from PITFALLS.md.
**Stack changes:** Pin FastAPI to 0.135.1; replace `sse-starlette` with `fastapi.sse.EventSourceResponse`; store asyncio task reference on ScanJob.
**Avoids:** Memory exhaustion mid-session, analyst data exfiltration, orphaned temp files.

### Phase 2: CSS Architecture Foundation

**Rationale:** All visual parity work depends on a stable CSS base. Adding rules to a flat 538-line file without a specificity plan creates Pitfall 7 (specificity debt). This phase sets `@layer`, section comments, and selector conventions before any component work begins.
**Delivers:** Layered CSS architecture (`@layer reset, tokens, base, layout, components, utilities`), agreed selector budget (max two-level descendant selectors, no `!important` except `.hidden`), self-hosted Inter WOFF2 subset replacing Google Fonts CDN link.
**Addresses:** Pitfall 7; STACK.md CSS architecture recommendation.
**Avoids:** Breaking component styles during later visual parity work.

### Phase 3: Visual Parity — Layout Shells and Search Panel

**Rationale:** ARCHITECTURE.md build order establishes tokens then shells then search panel as the critical path. The search panel modal positioning is the largest structural gap between prototype and mockup. All downstream components sit inside the results container that only appears after a scan; fixing shells first gives a stable frame.
**Delivers:** Header, progress bar, and target bar matching mockup. Search panel rendered as centred modal overlay (not inline). Design token values aligned to mockup colour palette.
**Addresses:** Top visual parity blockers from FEATURES.md MVP list (items 1-2).
**Avoids:** Layout shift when components are added in later phases.

### Phase 4: Visual Parity — Results Components

**Rationale:** All results components (summary cards, tabs, profiles table, export cards, tags heatmap, notes, raw JSON) depend on the layout shells and tab structure being stable. They are independent of each other within this phase and can be completed in any order once the tab container is correct.
**Delivers:** Summary cards per target, result tabs with active states and badges, profiles table with column widths/hover/response time colour coding, export cards grid, tags heatmap, notes textarea, raw JSON viewer — all matching mockup.html. Toast position and animation corrected.
**Addresses:** FEATURES.md MVP list items 3-9.
**Avoids:** Re-laying out components when tab structure changes (fixed in Phase 3).

### Phase 5: Graph Polish

**Rationale:** The D3 graph depends on the tab container having correct CSS height before `renderGraph()` is called. Fixing graph styles and interactions after the tab panel is stable avoids Pitfall 4 (ghost simulation) and Pitfall 5 (label tick overhead) being masked by layout issues.
**Delivers:** Node hover tooltip (missing from prototype), correct graph container height in CSS, simulation stop-and-null before re-render, labels deferred to simulation end, `ResizeObserver`-based fullscreen re-render replacing `setTimeout(100)` workaround, node category colour coding if present in mockup.
**Addresses:** FEATURES.md missing interaction (node hover tooltip); Pitfalls 4, 5, 9 from PITFALLS.md; STACK.md D3 optimisation recommendations.
**Avoids:** Pitfall 4 ghost-tick jank, Pitfall 5 label overhead at 100+ nodes.

### Phase Ordering Rationale

- Phase 1 before all visual work: a leaking server will crash during visual testing, making fixes impossible to verify.
- Phase 2 before new CSS: writing 200+ lines of visual parity CSS into a flat file without `@layer` will require a rewrite when specificity conflicts emerge.
- Phase 3 before Phase 4: results components are nested inside layout shells; their positioning is relative to the container established in Phase 3.
- Phase 5 last: D3 graph reads container dimensions at render time; the container CSS height must be stable before graph interaction work begins.

### Research Flags

Phases with standard, well-documented patterns (deep research not needed during planning):
- **Phase 1 (Stability):** FastAPI disconnect detection and `asyncio` task reference patterns are fully documented in official sources. Implementation is mechanical.
- **Phase 2 (CSS architecture):** `@layer` browser support is confirmed for all target browsers. MDN documentation is authoritative.
- **Phase 3 (Layout shells):** CSS layout is design-driven work against mockup.html; no domain research needed.
- **Phase 4 (Results components):** All components exist in mockup.html. Work is visual matching, not design.

Phases that may warrant deeper research during planning:
- **Phase 5 (Graph polish):** Node category colour mapping requires auditing the full tag category set from maigret's `data.json`. Category count affects legend design and colour scheme decisions.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations verified against official FastAPI docs, D3 docs, MDN, and direct code review. SVG threshold estimate is MEDIUM (research paper + community) but does not affect the recommendation. |
| Features | HIGH | Table stakes derived from SpiderFoot, Maltego, and OSINT industry conventions. MVP priority list is unambiguous given the milestone goal. |
| Architecture | HIGH | Current architecture is sound. Structural patterns derived from direct code review and official platform documentation (MDN, CPython issue tracker, D3 docs). |
| Pitfalls | HIGH | Critical pitfalls confirmed against FastAPI GitHub discussions, CPython bug tracker, OWASP DOM XSS cheatsheet, and PortSwigger. D3 ghost-tick confirmed against D3 GitHub issues. |

**Overall confidence:** HIGH

### Gaps to Address

- **Tag category set for graph colour coding:** The full list of tag categories in `maigret/data.json` has not been audited. Phase 5 planning should enumerate categories and assign colours before implementation.
- **Search panel modal positioning specifics:** The exact CSS for the centred modal overlay (z-index stack, backdrop, animation) should be verified against `mockup.html` computed styles before Phase 3 implementation begins.
- **Job cleanup mechanism:** The in-memory `jobs` dict grows without bound. Not blocking the parity milestone but should be flagged for a post-milestone hygiene pass.

---

## Sources

### Primary (HIGH confidence)
- https://fastapi.tiangolo.com/tutorial/server-sent-events/ — FastAPI native SSE API
- https://github.com/fastapi/fastapi/commit/22381558446c5d1ac376680a6581dd63b3a04119 — FastAPI SSE commit confirming 0.135+ support
- https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events — EventSource API
- https://d3js.org/d3-force/simulation — D3 force simulation API
- https://github.com/python/cpython/issues/91887 — asyncio dangling task GC risk
- https://docs.astral.sh/ruff/rules/asyncio-dangling-task/ — RUF006 confirms task GC risk
- https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html — href XSS sink
- https://portswigger.net/web-security/cross-site-scripting/contexts/lab-href-attribute-double-quotes-html-encoded — javascript: protocol XSS
- https://github.com/fastapi/fastapi/discussions/7572 — SSE disconnect handling in FastAPI
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer — CSS @layer

### Secondary (MEDIUM confidence)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12061801/ — SVG vs Canvas node count threshold (~1,000 node SVG limit)
- https://github.com/d3/d3/issues/1936 — D3 large graph performance
- https://smashingmagazine.com/2025/09/ux-strategies-real-time-dashboards/ — real-time dashboard UX conventions
- https://cambridge-intelligence.com/due-diligence-investigations/ — OSINT visualisation patterns
- https://css-tricks.com/css-cascade-layers/ — CSS @layer methodology

### Tertiary (reference)
- https://spiderfoot.org/ — table stakes feature comparison
- https://www.maltego.com/ — graph interaction conventions
- https://rsms.me/inter/ — Inter font subset sizing
- https://jasoncameron.dev/posts/fastapi-cancel-on-disconnect — SSE cancel-on-disconnect pattern

---
*Research completed: 2026-05-06*
*Ready for roadmap: yes*
