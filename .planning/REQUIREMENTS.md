# Requirements: Maigret Web Enhanced

**Defined:** 2026-05-07
**Core Value:** An OSINT analyst can scan usernames via browser, see results in real time, and export findings, all matching the mockup design.

## v1 Requirements

Requirements for mockup visual parity plus stability baseline.

### Stability and Security

- [ ] **STAB-01**: SSE event_stream generator checks for client disconnect and cleans up the asyncio queue
- [ ] **STAB-02**: All href attributes are sanitised against javascript: protocol XSS
- [ ] **STAB-03**: asyncio background tasks are stored in a module-level set to prevent GC cancellation
- [ ] **STAB-04**: Export temp files are cleaned up in a finally block to prevent leaks on exception

### Backend

- [ ] **BACK-01**: Server uses FastAPI native EventSourceResponse instead of manual StreamingResponse
- [ ] **BACK-02**: requirements.txt pins FastAPI >= 0.135.1 and removes sse-starlette dependency

### CSS Foundation

- [ ] **CSSF-01**: Stylesheet uses CSS @layer with six named layers (reset, tokens, base, layout, components, utilities)
- [ ] **CSSF-02**: Inter font is self-hosted as WOFF2 (Latin subset, weights 400, 500, 600, 700)
- [ ] **CSSF-03**: CSS design tokens (colours, spacing, radii, typography) match mockup.html values exactly

### Visual Parity: Layout

- [ ] **LAYT-01**: Header matches mockup (title, subtitle, New Scan button position and styling)
- [ ] **LAYT-02**: Progress bar matches mockup (track, fill gradient, stats row with found/checking text)
- [ ] **LAYT-03**: Target tabs match mockup (active state, count badges with purple background, hover states)
- [ ] **LAYT-04**: Search panel renders as centred modal overlay matching mockup positioning
- [ ] **LAYT-05**: Search panel tag clouds render as pill chips with included (purple) and excluded (red strikethrough) states

### Visual Parity: Results

- [ ] **RESL-01**: Summary cards render in a 4-column grid with correct label/value sizing and colour coding
- [ ] **RESL-02**: Result tabs match mockup active state (purple underline, green badge on Found tab)
- [ ] **RESL-03**: Profiles table has correct column widths, row hover state, star button, and response time colour coding (green < 0.5s, orange > 1.0s)
- [ ] **RESL-04**: Export cards render in a responsive grid with format title, description, and hover state
- [ ] **RESL-05**: Tags heatmap renders as a grid of cards with tag name, count, and proportional bar
- [ ] **RESL-06**: Notes textarea matches mockup styling (background, border, focus state, placeholder)
- [ ] **RESL-07**: Raw JSON panel matches mockup styling (monospace font, background, border, scroll)
- [ ] **RESL-08**: Live hit toasts appear bottom-right with fadeInUp/fadeOut animation, max 2 visible at a time

### Graph

- [ ] **GRPH-01**: D3 simulation is properly torn down (stop, null tick listener) before re-rendering
- [ ] **GRPH-02**: Graph nodes show a tooltip on hover with node ID and URL (if available)
- [ ] **GRPH-03**: Graph controls (zoom in, zoom out, reset, fullscreen) match mockup positioning and styling

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Maigret Features

- **PRXY-01**: User can configure HTTP/SOCKS5/Tor/I2P proxy for scans
- **IDTY-01**: User can search by identifier type (email, phone, not just username)
- **PARS-01**: User can paste a URL to extract and search usernames from it
- **COOK-01**: User can upload a cookies jar file for authenticated site checks
- **PERM-01**: User can auto-generate username permutations from multiple inputs
- **AIAN-01**: User can trigger AI-powered analysis of scan results

### UX Enhancements

- **NOTE-01**: Investigation notes are scoped per target username
- **GCLR-01**: Graph nodes are colour-coded by tag category
- **EXPO-01**: XMind and Markdown export formats available
- **HIST-01**: Scan history persisted across sessions
- **RESP-01**: Mobile-responsive layout

## Out of Scope

| Feature | Reason |
|---------|--------|
| Replace Flask UI in maigret/web/ | Separate project, upstream compatibility |
| Authentication or multi-user sessions | Single-user local tool |
| Persistent storage (database) | In-memory only, matching current design |
| Dark/light theme toggle | Mockup is dark only |
| WebSocket replacement for SSE | SSE is sufficient for one-way progress streaming |
| Mobile-first responsive redesign | Mockup is desktop-focused |
| Framework migration (React/Vue) | Vanilla JS constraint, no build step |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAB-01 | Phase 1 | Pending |
| STAB-02 | Phase 1 | Pending |
| STAB-03 | Phase 1 | Pending |
| STAB-04 | Phase 1 | Pending |
| BACK-01 | Phase 1 | Pending |
| BACK-02 | Phase 1 | Pending |
| CSSF-01 | Phase 2 | Pending |
| CSSF-02 | Phase 2 | Pending |
| CSSF-03 | Phase 2 | Pending |
| LAYT-01 | Phase 3 | Pending |
| LAYT-02 | Phase 3 | Pending |
| LAYT-03 | Phase 3 | Pending |
| LAYT-04 | Phase 3 | Pending |
| LAYT-05 | Phase 3 | Pending |
| RESL-01 | Phase 4 | Pending |
| RESL-02 | Phase 4 | Pending |
| RESL-03 | Phase 4 | Pending |
| RESL-04 | Phase 4 | Pending |
| RESL-05 | Phase 4 | Pending |
| RESL-06 | Phase 4 | Pending |
| RESL-07 | Phase 4 | Pending |
| RESL-08 | Phase 4 | Pending |
| GRPH-01 | Phase 5 | Pending |
| GRPH-02 | Phase 5 | Pending |
| GRPH-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-05-07*
*Last updated: 2026-05-07 after roadmap creation*
