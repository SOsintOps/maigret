# Technology Stack

**Project:** Maigret Web Enhanced — OSINT real-time dashboard
**Researched:** 2026-05-06
**Milestone context:** Bringing existing FastAPI + vanilla JS + D3.js prototype to production quality. No framework migration. No build tooling.

---

## Recommended Stack

### Backend

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | >=0.135.1 | ASGI web framework, API routes | 0.135.0 ships native SSE support via `fastapi.sse`. Eliminates sse-starlette dependency. Rust-side Pydantic serialisation is faster than `json.dumps()`. |
| Uvicorn | >=0.41.0 | ASGI server | Latest stable as of Feb 2026. Install with `uvicorn[standard]` to enable uvloop + httptools for maximum throughput. Single-user local tool; no gunicorn workers needed. |
| Python | >=3.10 | Runtime | Required by Uvicorn >=0.40.0 and already the project minimum. |

**SSE approach — migrate from `sse-starlette` to `fastapi.sse`:**

The prototype uses `StreamingResponse` with manual `text/event-stream` formatting. FastAPI 0.135.1 provides `EventSourceResponse` and `ServerSentEvent` directly from `fastapi.sse`. Benefits:

- Automatic keep-alive ping every 15 seconds (no manual `": keepalive\n\n"` hack)
- `Cache-Control: no-cache` and `X-Accel-Buffering: no` set automatically
- `Last-Event-ID` header support for reconnection resume
- Pydantic model serialisation at Rust speed
- `retry` field support, allowing client-side reconnect interval control

The current `server.py` keepalive implementation (`yield ": keepalive\n\n"`) is fragile. `EventSourceResponse` replaces it cleanly.

**Minimum viable migration:**
```python
# Before (current prototype)
from fastapi.responses import StreamingResponse
return StreamingResponse(event_stream(), media_type="text/event-stream")

# After (0.135+)
from fastapi.sse import EventSourceResponse, ServerSentEvent
return EventSourceResponse(event_stream())
# Yield ServerSentEvent(data=json.dumps(event), id=str(seq), retry=3000) inside
```

Confidence: HIGH — verified against official FastAPI docs (fastapi.tiangolo.com/tutorial/server-sent-events/) and commit 2238155.

---

### Frontend

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| D3.js | 7.9.0 | Force-directed graph, data binding | Current stable. No v8 yet. `d3-force` module via CDN import is sufficient; no full bundle needed. |
| Inter (font) | 4.x (via rsms.me or self-hosted WOFF2) | UI typography | Already referenced in `style.css`. Self-host WOFF2 subset to avoid Google Fonts DNS lookup and reduce payload from 95 KB to ~16 KB for Latin subset. |
| No framework | — | State management, DOM | Stack constraint from PROJECT.md. Vanilla JS ES modules cover all requirements. |

**No additions needed.** The existing prototype dependency surface (D3, Inter, browser EventSource API) is correct and complete for this scope.

---

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sse-starlette | REMOVE | Previously provided SSE | Drop once FastAPI >=0.135.1 is pinned. Native `fastapi.sse` is a direct replacement with better DX. |

---

## Detailed Recommendations by Domain

### 1. SSE — Server Side

**Use `fastapi.sse.EventSourceResponse` with `ServerSentEvent` objects.**

Assign sequential integer IDs to events. The browser sends `Last-Event-ID` on reconnect, allowing the server to replay missed events from the in-memory job queue.

Keep-alive is automatic at 15-second intervals. Remove the manual `asyncio.wait_for(..., timeout=60)` / `": keepalive\n\n"` pattern in `server.py`. The built-in ping handles proxy keep-alives correctly.

Set `retry=3000` (3 seconds) on the first event per stream so the browser reconnects quickly after network interruptions. The browser's default is 3 seconds but making it explicit is correct form.

Error events: yield a `ServerSentEvent(data=..., event="error")` before closing the generator. The client can dispatch on named event types.

Confidence: HIGH — official docs confirm all of the above.

---

### 2. SSE — Client Side (EventSource)

**Use the browser's native `EventSource` API. No reconnecting-eventsource wrapper needed.**

Reason: scans run 30–300 seconds and complete. The client does not need long-lived persistent connections. The current `done`/`error` flag + `es.close()` pattern in `app.js` is correct.

One improvement: listen for named event types rather than only `onmessage`. With `ServerSentEvent(event="hit")`, the client uses `es.addEventListener('hit', handler)`. This allows the server to send typed events (progress, hit, done, error) without embedding a `type` field in every JSON body, which eliminates the `if (!data.type)` branching in `listenProgress`.

The browser auto-reconnects with a 3-second delay by default. Because each scan is a unique job ID, reconnection after a network drop is safe — the server still holds the queue.

Confidence: HIGH — MDN EventSource API documentation is authoritative; no library required.

---

### 3. D3.js Force Graph Performance

**Keep SVG for this use case. Canvas is not warranted.**

Maigret scans typically return 10–300 found profiles. The SVG DOM performance threshold is around 1,000 nodes before frame rate drops. An OSINT scan hitting 500+ sites (all nodes + the username centre node) with 300 found profiles will produce at most ~300 site nodes plus tag nodes — well within SVG limits.

Specific optimisations to apply to the current `renderGraph`:

**Alpha decay** — The simulation runs 300 ticks by default. Increase `alphaDecay` to settle faster for dense graphs:
```javascript
.alphaDecay(0.05)   // settles in ~90 ticks instead of 300
```

**Stop on settle** — The current code does not stop the simulation once alpha < alphaMin. Add:
```javascript
state.simulation.on('end', () => state.simulation.stop());
```
Without this, `requestAnimationFrame` runs indefinitely at idle.

**Avoid re-rendering labels per tick** — Move `text` elements to a separate SVG `<g>` updated only on `end`, not on every `tick`. Label positions can lag slightly behind nodes; users will not notice on settle.

**Re-render strategy** — The `renderGraph` call inside `toggleFullscreen` using `setTimeout(100)` is a workaround. Use `ResizeObserver` on the container instead:
```javascript
new ResizeObserver(() => { if (t?.graphData) renderGraph(t.graphData); })
  .observe(document.getElementById('graphContainer'));
```

**Node hit-testing** — Add `tabindex` and keyboard interaction to nodes for accessibility (OSINT analysts may want to navigate graph with keyboard).

Confidence: MEDIUM — SVG threshold from D3 community documentation and research paper (PMC12061801); specific optimisation values from d3-force official docs.

---

### 4. CSS Architecture

**Keep the existing CSS custom properties token approach. Add `@layer` structure.**

The current `style.css` is 538 lines with a flat structure. It works but will become brittle as visual polish work adds overrides. Introduce CSS `@layer` to make specificity explicit without a preprocessor:

```css
@layer reset, tokens, base, layout, components, utilities;
```

Layer order (lowest to highest specificity):
- `reset` — `* { box-sizing: border-box; margin: 0; padding: 0; }`
- `tokens` — `:root { --bg-primary: ... }` design token declarations
- `base` — `body`, `a`, typography defaults
- `layout` — `.header`, `.main`, `.target-bar`, `.results-container`
- `components` — `.search-panel`, `.profiles-table`, `.graph-container`, `.export-card`, `.live-hit`
- `utilities` — `.active`, `.open`, `.fullscreen`, modifier classes

This eliminates specificity battles when patching visual drift against `mockup.html`. Overriding a component style from a utility class is safe because `utilities` wins in layer order.

Browser support: all modern browsers since 2022 (Chrome 99, Firefox 97, Safari 15.4). PROJECT.md requires Chrome, Firefox, Edge — fully supported.

Confidence: HIGH — MDN `@layer` documentation; CSS-Tricks cascade layers guide; Smashing Magazine article (Sep 2025).

**Dark-first, not dark-override.** The current stylesheet is already dark-first with correct token naming (`--bg-primary`, `--text-secondary`, etc.). Keep this approach. If a light mode is ever added, it adds a `[data-theme="light"]` block overriding tokens — not a `prefers-color-scheme` inversion of the entire stylesheet.

**Font loading** — Replace the Google Fonts link for Inter with a self-hosted WOFF2 subset. Inter at full weight is 95 KB; Latin-only WOFF2 subset is ~16 KB. Add `font-display: swap` and a `<link rel="preload">` in the `<head>` for the primary weight (400 and 600 are sufficient). This prevents a flash of unstyled text during initial load.

Confidence: HIGH — Inter font project documentation at rsms.me; web font performance literature.

---

### 5. Vanilla JS State Management

**Use the existing module-scope singleton object pattern (`const state = {}`). Do not introduce Proxy reactivity.**

The current `state` object in `app.js` is a plain object mutated directly, with explicit re-render calls. This is the correct pattern for this scope. Proxy-based reactivity (Vue 3 model, valtio) is appropriate when the application has many components sharing state. This application has one page with one state object and explicit render paths — Proxy adds complexity without benefit.

The `state` object design is sound. One structural improvement: split `state` into two concerns.

**Scan-level state** (per username, cleared between scans):
- `targets` map (already exists)
- `activeTarget` (already exists)

**UI-level state** (persists between scans):
- `starred` Set
- `sortField`, `sortAsc`
- `filterStarred`
- `tags`, `includedTags`, `excludedTags`

Moving `starred` and filter state into a separate `uiState` object signals intent: these persist when `showSearch()` resets `state.targets`. The current `showSearch()` wipes `state.targets` and `state.activeTarget` but not `state.starred` or sort preferences — which is correct, but the intent is hidden.

Event handling: use event delegation on the table body (`profilesBody`) rather than attaching individual click handlers per row. The `renderProfiles` function re-creates all `tr` elements and re-attaches handlers each call. With 300 rows and frequent progress updates, this is unnecessary DOM churn. A single `click` delegate on the table body handles star toggles cleanly.

Confidence: HIGH — based on direct code review of `app.js`.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| SSE (server) | `fastapi.sse.EventSourceResponse` | `sse-starlette` | sse-starlette is now a redundant dependency; native FastAPI support is more maintainable |
| SSE (server) | `fastapi.sse.EventSourceResponse` | `StreamingResponse` with manual formatting | Manual formatting has no keepalive, no typed events, no retry field |
| Force graph | D3.js SVG (existing) | Canvas with D3 layout | Canvas adds ~100 lines of rendering code; not warranted below 1,000 nodes |
| Force graph | D3.js (existing) | Cytoscape.js or vis.js | D3 is already in use; switching adds a dependency for no functional gain at this scale |
| State | Plain object (existing) | Proxy-reactive store | Proxy is appropriate for multi-component apps; this is a single-page tool with explicit render paths |
| CSS | Flat file + `@layer` | Sass/PostCSS | No build step is a hard constraint (PROJECT.md); `@layer` achieves the same organisational goals natively |
| Fonts | Self-hosted WOFF2 | Google Fonts CDN | Self-hosting avoids external DNS lookup and gives cache-control; 16 KB vs 95 KB for Latin subset |

---

## Current requirements.txt — Recommended Update

```
# Current (web-enhanced/requirements.txt)
fastapi>=0.115.0        →  fastapi>=0.135.1
uvicorn>=0.34.0         →  uvicorn[standard]>=0.41.0
maigret>=0.6.0          →  (unchanged)
sse-starlette>=2.0.0    →  (REMOVE — native FastAPI SSE replaces it)
```

Removing `sse-starlette` requires updating `server.py` imports. The SSE streaming logic in `scan_progress` must be refactored to yield `ServerSentEvent` objects and use `EventSourceResponse`. This is a targeted change: one endpoint, one function, roughly 20 lines.

---

## Confidence Assessment

| Area | Confidence | Source |
|------|------------|--------|
| FastAPI 0.135 SSE native support | HIGH | Official FastAPI docs + GitHub commit 2238155 |
| `sse-starlette` removal | HIGH | FastAPI changelog; sse-starlette README acknowledges redundancy |
| Uvicorn 0.41 version | HIGH | Uvicorn release page (Feb 2026) |
| D3.js 7.9.0 current stable | HIGH | d3js.org; jsDelivr CDN |
| SVG vs Canvas threshold | MEDIUM | PMC paper on graph library efficiency; D3 community posts |
| `@layer` browser support | HIGH | MDN; can-i-use confirms all required browsers |
| Inter font self-host savings | HIGH | Inter project homepage; web font performance literature |
| Proxy state pattern verdict | HIGH | Direct code review of app.js |

---

## Sources

- FastAPI SSE docs: https://fastapi.tiangolo.com/tutorial/server-sent-events/
- FastAPI SSE commit: https://github.com/fastapi/fastapi/commit/22381558446c5d1ac376680a6581dd63b3a04119
- FastAPI releases: https://github.com/fastapi/fastapi/releases
- sse-starlette: https://github.com/sysid/sse-starlette
- Uvicorn deployment: https://uvicorn.dev/deployment/
- D3.js force docs: https://d3js.org/d3-force
- D3.js force simulation: https://d3js.org/d3-force/simulation
- Graph efficiency paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC12061801/
- CSS @layer MDN: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer
- CSS @layer Smashing Magazine: https://smashingmagazine.com/2025/09/integrating-css-cascade-layers-existing-project/
- Inter font: https://rsms.me/inter/
- EventSource MDN: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
- Vanilla JS reactive patterns: https://gomakethings.com/simple-reactive-data-stores-with-vanilla-javascript-and-proxies/

---

*Research complete: 2026-05-06*
