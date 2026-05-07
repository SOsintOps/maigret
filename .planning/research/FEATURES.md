# Feature Landscape: OSINT Web Dashboard (Maigret Enhanced)

**Domain:** Real-time OSINT username scanning interface
**Researched:** 2026-05-06
**Context:** Milestone is visual parity with mockup.html. This document maps what the domain expects against what exists, to guide requirements prioritisation.

---

## Current Feature Inventory

The functional prototype (`index.html` + `app.js`) already implements the following. These are included for dependency mapping, not as open work items.

| Feature | Status |
|---------|--------|
| SSE progress streaming (checked/total, found count, current site) | Implemented |
| Multi-username scan with target tabs | Implemented |
| Summary cards (sites checked, profiles found, categories, elapsed) | Implemented |
| Found profiles table (star, site, URL, tags, response time) | Implemented |
| Table filter (text search) | Implemented |
| Table sort (A-Z, speed) | Implemented |
| Star/bookmark rows | Implemented |
| D3.js force-directed network graph | Implemented |
| Graph controls (zoom in/out, reset, fullscreen) | Implemented |
| Tags heatmap grid | Implemented |
| Export in CSV, JSON, TXT, PDF, HTML | Implemented |
| Raw JSON viewer | Implemented |
| Investigation notes textarea | Implemented |
| Live hit toast notifications | Implemented |
| Tag-based site filtering (include/exclude in scan form) | Implemented |
| Advanced scan options (recursive parsing, top sites, timeout) | Implemented |

---

## Table Stakes

Features users expect in this class of tool. Missing means the product feels unfinished or unprofessional to an OSINT analyst. Confidence: HIGH (corroborated by SpiderFoot, Maltego conventions, OSINT Industries patterns, and general dashboard UX literature).

### Results Display

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| Real-time row insertion as results arrive | Analysts need to see activity, not wait for completion | Low | SSE already in place; rows must appear as events fire, not batch at end |
| Clickable URLs opening in new tab | Core to investigation — analyst must visit profiles | Low | Already present; must be correct target="_blank" with rel="noopener" |
| Response time colour coding (fast/slow) | OSINT analysts assess site reliability; slow responses suggest blocks or bans | Low | Pattern: green under 0.5s, amber 0.5–1.0s, red over 1.0s |
| Category/tag labels on each row | Analysts filter by platform type (social, coding, forum) | Low | Already present as tag chips |
| Empty state message when no results yet | Blank table with no context is disorienting | Low | "No profiles found yet. Scan in progress..." |
| Count badge on Found tab updating live | Analysts track progress without switching tabs | Low | Already exists as badgeFound; must update on every hit |
| Starred row persistence within session | Analysts bookmark key findings during review | Low | Already implemented; must survive tab switches |

### Progress and Status UX

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| Progress bar with percentage fill | Standard scan UX; users need spatial sense of completion | Low | Already exists; fill width must track checked/total |
| Sites checked / total counter | Analysts want exact numbers, not just a bar | Low | Already present in progress-stats |
| Current site name during scan | Confirms scanner is running; catches obvious hangs | Low | Already in progressSite span |
| Distinct visual states: idle / running / complete | Bar colour or style change signals state changes clearly | Low | Complete state = full bar, different colour or "Done" label |
| Disable Scan button during active scan | Prevents double-submit | Low | Button must disable on scan start, re-enable on completion or error |
| Error state display | Scanner can fail (timeout, network, maigret crash) | Medium | Toast or inline message with error text; progress bar goes red |
| New Scan button visible after completion | Analysts run multiple targets; must be able to re-enter | Low | btnNewScan currently hidden until results exist |

### Graph Visualisation

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| Node hover tooltip showing site name and URL | Standard in every link analysis tool; without it the graph is illegible | Low | Absent from current prototype — most critical missing interaction |
| Node click opens profile URL | Maltego convention; direct pivot from graph to evidence | Low | Already in prototype; must work for site nodes |
| Drag to rearrange nodes | Standard D3 force-graph interaction; analysts explore clusters | Low | Already implemented |
| Zoom/pan controls | Essential for graphs with 20+ nodes | Low | Already implemented |
| Fullscreen mode | Analysts need full viewport for complex graphs | Low | Already implemented |
| Central subject node visually distinct | Analyst must identify the target at a glance | Low | Already implemented (purple, size 25) |
| Site nodes coloured by category or hit type | Visual grouping; faster pattern recognition | Medium | Not in current prototype; colour by tag group (social, coding, etc.) |

### Export Workflow

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| Download triggered on card click | Standard expectation; click = download, no confirmation dialogs | Low | Already implemented |
| Export scoped to selected target | Multi-target scans; analyst exports one subject at a time | Low | Must pass active target to export endpoint |
| Format descriptions on export cards | Analysts unfamiliar with formats need a one-line explanation | Low | Already present in mockup (e.g. "Spreadsheet-ready table") |
| Visual feedback on export click (brief loading state) | Prevents double-click and confirms action was received | Low | Export can take 1–2s for PDF; button or card should show loading state |

### Dark Theme Conventions

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| Background in near-black range (#0d1117 to #1a1a24) | Industry standard for security tooling; reduces eye strain in long sessions | Low | style.css already targets this range |
| Single primary accent colour (violet/purple) | Provides visual identity without noise; maigret's brand colour is in this range | Low | Already established as #7c3aed in graph and UI elements |
| Semantic colour for state: green = found, amber = warning, red = error | Analyst reads colour as signal, not decoration | Low | green for hits, amber for slow response, red for error state |
| Muted secondary text (#888–#aaa range) | Data-heavy tables need hierarchy; all labels at same weight = illegible | Low | Already present in mockup as #8888a0 for graph labels |
| High contrast for interactive elements on hover | Accessibility and discoverability in dark UIs | Low | Table row hover, export card hover must lift contrast clearly |
| Consistent border colour (#2a2a3a range) | Card and panel separation without harsh lines | Low | Already present in mockup styling |

### Investigation Notes

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| Freeform textarea for analyst notes | OSINT workflow always involves noting hypotheses, pivots, observations | Low | Already implemented |
| Notes scoped per target tab | Multi-target scans require separate notes per subject | Medium | Currently a single shared textarea; must associate notes with active target |
| Notes persist within session when switching tabs | Losing notes on tab switch is a trust-breaking experience | Low | Notes content must survive tab switching |

### Live Hit Toast Notifications

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| Toast appears bottom-right with site name and URL | Standard real-time feedback pattern for scanning tools | Low | Already implemented |
| Auto-dismiss after ~3 seconds | Toasts must not accumulate and block content | Low | Already implemented (3500ms) |
| Toast is clickable to open URL | Analyst may want to act immediately on a hit | Low | Already in mockup; anchor tag wraps URL |
| Toast limited to one or two visible at a time | More than two simultaneous toasts = cognitive overload | Low | Queue toasts with short overlap; do not stack more than two |

---

## Differentiators

Features that distinguish Maigret Enhanced from vanilla CLI output or generic scanning tools. These create real value for analysts without being strictly expected. Confidence: MEDIUM (derived from OSINT domain conventions and gap analysis against SpiderFoot/Maltego patterns).

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Tags heatmap grid | Visual summary of which platform categories the target uses; faster than reading a table | Low | Already implemented; needs visual polish to match mockup |
| Recursive account discovery visualised in graph | Shows second-order accounts linked from primary profiles; Maltego-style pivot | High | Depends on maigret recursive flag; already supported by scanner |
| Multi-target tab comparison | Analyst can compare two usernames side by side without re-running scans | Medium | Tab switching already works; summary cards per target needed |
| Star filter to show only bookmarked rows | Analyst curates key findings during scan, then reviews only those | Low | Already in prototype; "★ Starred" filter button must actually filter |
| Category colour coding on graph nodes | Colour by tag group (social=blue, coding=green, forum=amber) creates instant visual clustering | Medium | Extends existing graph implementation; requires tag-to-colour map |
| Response time as investigative signal | Slow responses may indicate geo-blocking or username claimed but inactive | Low | Already colour-coded in mockup; analysts can infer from patterns |
| Scan parameter presets (tag-cloud include/exclude) | Analyst scans only social platforms for one investigation, only coding for another | Low | Already in mockup advanced options; needs real implementation |
| Standalone HTML report export | Analyst sends a self-contained evidence file with no server dependency | Low | Already implemented via HTML export format |

---

## Anti-Features

Features to deliberately not build in this milestone. Either they contradict the project constraints or they add scope without corresponding value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Authentication / login | Out of scope per PROJECT.md; single-user local tool | None needed; tool runs locally only |
| Persistent scan history / database | Out of scope per PROJECT.md; in-memory only | Session data lives in memory; user exports what they need |
| Mobile-responsive layout | Mockup is desktop-focused; analyst workflows are desktop | Keep fixed-width desktop layout; do not add breakpoints |
| Auto-refresh or polling for scan state | SSE already provides push; polling adds load and complexity | Rely entirely on SSE event stream |
| Multi-user sessions or concurrent scan isolation | Not a multi-user tool | Single active scan per server instance |
| WebSocket upgrade | SSE covers all one-directional requirements with less operational complexity | Keep SSE; no reason to add WebSocket |
| Third-party analytics or telemetry | OSINT tool; users are privacy-conscious professionals | No external scripts beyond CDN fonts and D3 |
| Wizard or onboarding flow | Single-purpose tool; users are analysts who understand it | Keep the direct search panel as the entry point |
| Dark/light mode toggle | Mockup is dark-only; adding a toggle doubles CSS maintenance | Ship dark mode only |
| Server-side result persistence between restarts | Out of scope; adds database dependency | Results are in-memory, lost on server restart |
| Graph layout algorithms beyond force-directed | Force-directed is standard for OSINT link graphs; others add complexity without analyst benefit | Keep D3 force simulation |

---

## Feature Dependencies

```
SSE progress stream
  → Real-time row insertion (live data feed)
  → Progress bar fill and counter updates
  → Live hit toasts
  → Count badge on Found tab

Target tabs
  → Summary cards per target (sites checked, found, categories, elapsed)
  → Export scoped to selected target
  → Notes per target

Found profiles table
  → Filter input
  → Sort (A-Z, Speed)
  → Star/bookmark rows
    → Star filter ("★ Starred" button)

Profiles data (all found rows)
  → D3 graph nodes and links
    → Node hover tooltip
    → Node click opens URL
  → Tags heatmap grid
  → Raw JSON viewer
  → Export formats (CSV, JSON, TXT, PDF, HTML)

Scan form
  → Tag-cloud include/exclude → scan parameter filtering
  → Recursive flag → recursive account discovery in graph
```

---

## MVP Recommendation

The milestone goal is visual parity with mockup.html, not new functionality. The priority order follows that goal.

**Highest priority (visual parity blockers):**
1. Progress bar states (running / complete) matching mockup colours and labels
2. Target tab styling and count badges matching mockup
3. Summary cards grid layout matching mockup
4. Result tab styling and active states matching mockup
5. Profiles table column widths, hover states, response time colour coding
6. Export cards grid layout and hover states matching mockup
7. Tags heatmap cards matching mockup
8. Search panel centred modal behaviour and tag-cloud chips matching mockup
9. Live hit toast position, animation and link matching mockup

**Missing interaction (not in current prototype, present in mockup):**
- Node hover tooltip on graph (the most functionally absent item identified by research)

**Defer to future milestone:**
- Notes scoped per target (requires state restructure)
- Category colour coding on graph nodes (new visual layer)
- Scan parameter presets as saved profiles
- Any feature not present in mockup.html

---

## Sources

- SpiderFoot UI feature documentation: https://spiderfoot.org/
- Maltego link analysis conventions: https://www.maltego.com/
- Cambridge Intelligence OSINT visualisation patterns: https://cambridge-intelligence.com/due-diligence-investigations/
- OSINT Combine data visualisation: https://www.osintcombine.com/post/rapid-data-visualization
- Toast notification UX best practices: https://blog.logrocket.com/ux-design/toast-notifications/
- Smashing Magazine real-time dashboard UX: https://www.smashingmagazine.com/2025/09/ux-strategies-real-time-dashboards/
- Data table UX patterns: https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables
- Cybersecurity dashboard UX guide: https://www.aufaitux.com/blog/cybersecurity-dashboard-ui-ux-design/
- Dark mode colour palette conventions: https://blog.zeplin.io/dark-mode-color-palette/
- OSINT investigation workflow standards: https://sosintel.co.uk/osint-essentials-planning-recording-and-evaluating-intelligence/
- D3.js force graph interaction patterns: https://moldstud.com/articles/p-advanced-techniques-for-customizing-force-directed-graphs-in-d3js-a-comprehensive-guide
- Maigret upstream documentation: https://maigret.readthedocs.io/
