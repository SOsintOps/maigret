# Architecture Patterns

**Domain:** FastAPI + vanilla JS real-time OSINT dashboard
**Researched:** 2026-05-06
**Context:** Bringing an existing prototype to visual parity with a mockup. Stack is fixed.

---

## Current Architecture (as-built)

The codebase already implements a working architecture. This document describes what exists, identifies structural problems that explain the visual drift, and recommends the component model for the parity milestone.

```
Browser                           FastAPI (server.py)          Maigret engine
  |                                      |                           |
  |-- POST /api/scan -----------------> |                           |
  |<-- { id, status: "started" } ----  | -- asyncio.create_task -> run_scan()
  |                                      |                           |
  |-- GET /api/scan/{id}/progress -----> |                    ProgressNotify
  |<== SSE stream (tick events) ======= |<== queue.put() ========= |
  |                                      |                           |
  |-- GET /api/scan/{id}/results ------> |                           |
  |<-- { profiles, stats } -----------  |                           |
  |                                      |                           |
  |-- GET /api/scan/{id}/graph --------> |                           |
  |<-- { nodes, links } --------------  |                           |
  |                                      |                           |
  |-- GET /api/scan/{id}/export/{fmt} -> |                           |
  |<-- file download -----------------  |                           |
```

---

## Component Boundaries

### Backend components (server.py + scanner.py)

| Component | File | Responsibility | Communicates With |
|-----------|------|---------------|-------------------|
| HTTP router | server.py | Validate requests, dispatch jobs, serve static files | scanner.py, jobs dict |
| Job store | server.py (in-memory dict) | Hold ScanJob objects keyed by job_id | HTTP router, SSE endpoint |
| SSE endpoint | server.py event_stream() | Drain job.queue, format SSE frames, send keepalives | Job store |
| ScanJob | scanner.py | Carry job state: status, progress, queue, results | HTTP router, ProgressNotify |
| ProgressNotify | scanner.py | Bridge sync maigret callbacks to asyncio Queue | ScanJob.queue, maigret engine |
| run_scan() | scanner.py | Orchestrate maigret call, write results, put done event | ScanJob, maigret engine |
| get_graph_json() | scanner.py | Build NetworkX graph from results, return node-link JSON | ScanJob.results |
| generate_export() | scanner.py | Convert results to requested format using maigret.report | ScanJob, maigret.report |

### Frontend components (app.js)

| Component | Lines (approx) | Responsibility | Reads/Writes |
|-----------|---------------|---------------|--------------|
| Global state object | 1-14 | Single source of truth: targets, activeTarget, starred, sort, tags, simulation | Read by all renderers |
| loadTags() | 36-44 | Fetch /api/tags once on init, populate state.tags | state.tags, renderTagCloud |
| startScan() | 69-112 | Parse inputs, POST /api/scan per username, create target entries, start SSE | state.targets, DOM show/hide |
| listenProgress() | 142-171 | Own the EventSource lifecycle per job, route events, close on terminal event | state.targets, updateProgress, fetchResults |
| updateProgress() | 173-201 | Mutate active target during scan, update progress bar and live-hit toast | DOM (progress bar, count badge), showLiveHit |
| fetchResults() | 208-237 | After SSE done: GET results + graph, write into state.targets | state.targets, renderCurrentTarget |
| renderCurrentTarget() | 239-263 | Orchestrate all renderers for the active target | renderProfiles, renderTagsHeatmap, DOM (summary cards) |
| renderProfiles() | 266-344 | Build profiles table rows from filtered, sorted list | state.starred, state.sortField |
| renderGraph() | 388-464 | Create D3 force simulation and SVG from node-link data | state.simulation, D3 global |
| renderTagsHeatmap() | 483-518 | Build tag-count grid cards | DOM (tagsGrid) |
| showSearch() | 552-562 | Reset to initial state, clear targets, stop simulation | state, DOM |

---

## Data Flow

### Scan initiation and streaming

```
User input
  -> startScan()
  -> POST /api/scan  (one per username)
  -> server creates ScanJob, stores in jobs{}, fires asyncio.create_task(run_scan())
  -> server returns { id }

listenProgress(username, jobId)
  -> new EventSource("/api/scan/{id}/progress")
  -> server: event_stream() drains job.queue
  -> each SSE frame: { completed, total, found, site, status, url }
  -> updateProgress() mutates state.targets[username].profiles (partial, tags absent)
  -> on "done" frame: es.close(), fetchResults()

fetchResults(username, jobId)
  -> GET /api/scan/{id}/results  (full profiles with tags + response_time)
  -> GET /api/scan/{id}/graph    (node-link JSON)
  -> writes into state.targets[username]
  -> calls renderCurrentTarget() if username == state.activeTarget
```

### Render pipeline

```
state.activeTarget changes (tab click, or first scan)
  -> selectTarget(username)
  -> renderCurrentTarget()
     |- renderProfiles(t.profiles)       -- writes tbody innerHTML via createElement
     |- renderTagsHeatmap(t.profiles)    -- writes tagsGrid innerHTML via createElement
     |- document.getElementById updates  -- summary card values
     |- (graph deferred until tab click)
```

### D3 graph data flow

```
User clicks Graph tab
  -> switchTab()
  -> renderGraph(state.targets[activeTarget].graphData)
     |- svg.selectAll('*').remove()      -- full teardown
     |- new forceSimulation()            -- replaces previous
     |- state.simulation = sim           -- stored for external controls
     |- sim.on('tick') -> updates SVG attrs
     |- sim runs to alpha < alphaMin, fires 'end'
```

---

## Structural Patterns to Follow

### Pattern 1: SSE lifecycle with explicit terminal state

The current code handles this correctly. The pattern to preserve:

- Set a `done` boolean flag before calling `es.close()`. The `onerror` handler fires after close and must not trigger a second fetch.
- Only call `es.close()` inside the `onmessage` handler when `data.type === 'done'` or `data.type === 'error'`.
- In `onerror`, check `done` first. If the connection dropped mid-scan with `t.status === 'running'`, set status to `'error'`. Do not attempt a reconnect because the job is already running on the server and the queue is unbuffered.
- Do NOT rely on the browser's automatic reconnect for job progress streams. Each SSE endpoint is a unique, one-shot job stream. Reconnection to the same endpoint after a network drop means missed events.

```javascript
function listenProgress(username, jobId) {
  const es = new EventSource(`/api/scan/${jobId}/progress`);
  let done = false;

  es.onmessage = (evt) => {
    if (done) return;
    const data = JSON.parse(evt.data);
    if (data.type === 'done' || data.type === 'error') {
      done = true;
      es.close();
      // transition state here
    } else {
      updateProgress(username, data);
    }
  };

  es.onerror = () => {
    if (done) return;   // onerror fires after close(); ignore it
    done = true;
    es.close();
    state.targets[username].status = 'error';
  };
}
```

### Pattern 2: Single active-target render dispatch

All rendering passes through one function. No component renders itself; the dispatcher decides what to render based on state. This is already the pattern in `renderCurrentTarget()`. Preserve it strictly: every DOM write is initiated from this function or from `updateProgress()` (which handles in-progress-only updates).

```javascript
function renderCurrentTarget() {
  const t = state.targets[state.activeTarget];
  if (!t) return;
  // all DOM updates for the active target live here
}
```

Never call `renderProfiles()` or `renderTagsHeatmap()` directly from event handlers. Call `renderCurrentTarget()` instead to keep render logic in one place.

### Pattern 3: D3 simulation teardown before re-render

The current code calls `svg.selectAll('*').remove()` and creates a new simulation each time. This is correct for this use case (graph data is not incrementally updated, only loaded once after scan completes).

The critical requirement is stopping the old simulation before creating a new one, or the old physics loop continues running and manipulates nodes that no longer have SVG elements:

```javascript
function renderGraph(data) {
  if (state.simulation) {
    state.simulation.stop();
    state.simulation.on('tick', null);
    state.simulation.on('end', null);
    state.simulation = null;
  }

  const svg = d3.select('#graphSvg');
  svg.selectAll('*').remove();
  // ... create new simulation
}
```

The `showSearch()` reset function already calls `state.simulation.stop()`. This must remain, and the `on()` listener removal must be added to prevent the tick callback referencing a detached SVG.

### Pattern 4: Profiles populated twice — live then final

During a scan, `updateProgress()` pushes partial profile objects `{ site, url, tags: [], response_time: null }` to `t.profiles`. After the scan, `fetchResults()` replaces `t.profiles` entirely with the full array from the REST endpoint (which includes tags, response_time, ids_data).

This two-phase write is intentional and correct. It provides live feedback during the scan. The risk is that `renderCurrentTarget()` could fire between phases and show partial data in the summary cards. The current code guards this correctly by checking `t.status === 'done'` before rendering summary cards.

Do not change this pattern. The live profiles push is what drives the toast notifications and the in-progress count badges.

### Pattern 5: asyncio task reference management

The current server.py uses `asyncio.create_task(run_scan(...))` without storing the returned Task object. Python's asyncio event loop holds only weak references to tasks; CPython 3.12+ may garbage-collect fire-and-forget tasks before they complete.

The recommended fix is the strong-reference set pattern:

```python
# server.py — module level
_background_tasks: set = set()

@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    ...
    task = asyncio.create_task(run_scan(...))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return {"id": job_id, ...}
```

This has no functional impact during testing (CPython typically doesn't GC tasks that are actively awaiting I/O) but is a correctness requirement for production.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Querying the DOM to derive state

**What happens:** `document.getElementById('filterInput').value` is read inside `renderProfiles()`, tying render logic to DOM state rather than JS state.

**Why bad:** Renders become order-dependent. Testing is harder. Bugs emerge when the element does not exist yet or is in the wrong tab.

**Instead:** Keep `filterText` in the global state object. Update it in the `oninput` handler. Read from state in the render function.

### Anti-Pattern 2: Inline styles for visibility toggling

**What happens:** Several places use `element.style.display = 'none'` and `'inline-block'` to show and hide elements (header `+ New Scan` button, search panel).

**Why bad:** Inline styles override stylesheet rules silently. When the mockup CSS specifies a different display value (e.g. `flex`), restoring `display: block` produces wrong layout. Visibility state is split between CSS and JS.

**Instead:** Use a CSS class with the stylesheet as the authority. Toggle `element.classList.add('hidden')` and `.remove('hidden')`, with `.hidden { display: none !important; }` in the stylesheet.

### Anti-Pattern 3: D3 simulation running after tab switch

**What happens:** If the user switches away from the Graph tab and back, `renderGraph()` creates a second simulation without stopping the first, because the guard only checks `state.simulation` which was already set during the previous render.

**Why bad:** Two simulations tick simultaneously, fighting over the same node objects. Visual jitter and incorrect node positions.

**Instead:** The `renderGraph()` teardown must always stop and null the previous simulation before creating a new one, as shown in Pattern 3 above.

### Anti-Pattern 4: Stacking live-hit toasts off-screen

**What happens:** `showLiveHit()` appends a new `.live-hit` div directly to `document.body` and removes it after 3.5 seconds. Fast scans produce many concurrent toasts stacked at the same `bottom: 24px; right: 24px` position.

**Why bad:** Toasts overlap. The mockup shows a single toast at a time.

**Instead:** Either queue toasts and show one at a time, or stack them with `transform: translateY()` offset based on how many are currently visible. The simpler fix is to cap concurrent toasts and discard excess.

### Anti-Pattern 5: Shared style.css with inline overrides in mockup.html

**What happens:** `mockup.html` has `<style>@import url('style.css');</style>` as a fallback, and also links the stylesheet via `<link>`. The functional `index.html` only uses the `<link>` tag. Both files share `style.css` and rely on it for all component styles.

**Why bad:** Editing `style.css` to match the mockup affects both files simultaneously. Divergences between mockup and functional app cannot be tested in isolation. The `@import` in mockup is double-loading the stylesheet.

**Instead:** Treat `style.css` as the single authority. Remove the `@import` from `mockup.html`. All visual changes go into `style.css`. Visual parity is achieved when `index.html` and `mockup.html` look identical when given the same data.

---

## CSS Organisation for Component-Heavy Dashboard

The current `style.css` is a flat, 537-line single file with no preprocessor. This is correct for the constraints (no build tools). The recommended organisation is section comments as delimiters, matching the component hierarchy in the HTML.

Recommended section order (matching render layer order):

```css
/* 1. Design tokens  — :root CSS variables only */
/* 2. Reset          — *, body baseline */
/* 3. Layout shells  — .header, .progress-container, .target-bar, .results-container */
/* 4. Search panel   — .search-panel, .form-group, .form-input, .tag-cloud, .btn */
/* 5. Summary cards  — .summary-row, .summary-card */
/* 6. Tabs           — .result-tabs, .result-tab, .tab-panel, .badge */
/* 7. Profiles table — .profiles-toolbar, .profiles-table, .star-btn, .profile-tag */
/* 8. Graph panel    — .graph-container, .graph-controls, .graph-btn */
/* 9. Tags heatmap   — .tags-grid, .tag-card */
/* 10. Export panel  — .export-grid, .export-card */
/* 11. Notes + Raw   — .notes-area, .raw-json */
/* 12. Toast         — .live-hit, @keyframes */
/* 13. Responsive    — @media queries */
```

The current file already follows this pattern roughly. The main gap is that some component-specific overrides are missing. When adding styles for the mockup parity work, add them to the correct section rather than appending to the bottom of the file.

Use component-scoped CSS variable overrides for state variants rather than new classes. For example:

```css
/* In the design tokens section */
:root {
  --progress-fill-width: 0%;
}

/* In the progress section */
.progress-bar-fill {
  width: var(--progress-fill-width);
}
```

Set `--progress-fill-width` via JS rather than `element.style.width` where possible.

---

## API Design

The current REST + SSE hybrid is well-structured. The endpoint contract is:

| Endpoint | Method | When to call | Returns |
|----------|--------|-------------|---------|
| POST /api/scan | REST | User submits form | `{ id, username, status }` |
| GET /api/scan/{id}/progress | SSE | Immediately after POST, keep open | Tick events until done/error |
| GET /api/scan/{id}/results | REST | After SSE done event | Full profiles + stats |
| GET /api/scan/{id}/graph | REST | After results | Node-link JSON |
| GET /api/scan/{id}/export/{fmt} | REST | User clicks export card | File download |
| GET /api/tags | REST | On page load | Tag list with counts |
| GET /api/sites | REST | On demand (not used yet) | Site list |

The only design gap is the absence of a job cleanup mechanism. The in-memory `jobs` dict grows without bound. For a single-user local tool this is acceptable, but the parity milestone should note it as a future concern.

The SSE `keepalive` frame is sent as `: keepalive\n\n` (a comment, not a `data:` frame) so the browser's EventSource parser ignores it without firing `onmessage`. This is correct.

---

## Suggested Build Order (Dependencies)

The parity milestone is CSS and HTML layout work, not architectural change. The components have hard dependencies that constrain order:

```
1. Design tokens (CSS :root variables)
   No dependencies. Everything else inherits from here.
   Change colour, spacing, typography values here first.

2. Layout shells (header, progress bar, target bar)
   Depend only on design tokens.
   These are always visible; fix them before tabs.

3. Search panel
   Depends on layout shells for z-index context (mockup uses position:fixed centered modal).
   The mockup shows the search panel as a centred modal overlay; the functional app shows it inline.
   This is the largest structural gap between mockup and functional app.

4. Summary cards
   Depend on results-container visibility. Fix after search panel.

5. Result tabs + tab panels
   Depend on summary cards being in the correct flow.

6. Profiles table
   Depends on tab panel being active and visible.
   Table column widths, hover states, tag chip styles.

7. Graph panel
   Depends on tab panel. The D3 simulation reads container dimensions at render time;
   the container must have correct CSS height before renderGraph() is called.
   Fullscreen mode depends on z-index stack being correct.

8. Tags heatmap, Export grid, Notes, Raw JSON
   Independent of each other. Can be fixed in any order after tabs are stable.

9. Toast notifications
   Independent of all panels. Fix stacking and animation last.
```

The critical path is: tokens → shells → search panel (modal positioning) → tabs → graph container height.

---

## Sources

- [MDN: Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) — HIGH confidence (official spec)
- [D3 force simulation API](https://d3js.org/d3-force/simulation) — HIGH confidence (official docs)
- [Python asyncio CPython issue: strong references for free-flying tasks](https://github.com/python/cpython/issues/91887) — HIGH confidence (CPython bug tracker)
- [Ruff rule RUF006: asyncio dangling task](https://docs.astral.sh/ruff/rules/asyncio-dangling-task/) — HIGH confidence (static analysis rule, confirms the GC risk)
- [CSS-Tricks: Build a state management system with vanilla JavaScript](https://css-tricks.com/build-a-state-management-system-with-vanilla-javascript/) — MEDIUM confidence (well-known source, pattern widely adopted)
- [CSS-Tricks: Scalable CSS architecture with BEM and utility classes](https://css-tricks.com/building-a-scalable-css-architecture-with-bem-and-utility-classes/) — MEDIUM confidence (methodology reference)
- [Sara Soueidan: Global and component style settings with CSS variables](https://www.sarasoueidan.com/blog/style-settings-with-css-variables/) — MEDIUM confidence (practitioner reference)
