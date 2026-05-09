# Phase 3: Layout and Search Panel - Context

**Gathered:** 2026-05-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Match the header, progress bar, target tabs, and search panel modal to the mockup layout exactly. No new features — visual parity only for layout-level components. The CSS @layer foundation from Phase 2 is in place; all new rules go into the appropriate layer blocks.

</domain>

<decisions>
## Implementation Decisions

### Search Panel Modal Behavior
- **D-01:** Search panel renders as a centred modal overlay with a semi-transparent dark backdrop (#000 ~50% opacity). Currently inline in index.html — must be converted to fixed-position modal matching mockup (`position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); z-index:500`).
- **D-02:** Modal has a close button (X) in top-right corner. Claude's discretion on whether ESC key and click-on-backdrop also close the modal.
- **D-03:** Modal opens with fade-in + scale-up animation (opacity 0→1, scale 0.95→1). Closing uses reverse animation.
- **D-04:** On initial page load, the search panel is NOT shown. Page loads with only the header visible and "+ New Scan" button. User must click "+ New Scan" to open the modal. No empty-state message — just the header bar.

### Progress Bar States
- **D-05:** Progress bar fill uses a gradient from --accent (#7c3aed) to --accent-hover (#9b5cf6).
- **D-06:** When scan completes, progress bar stays visible at 100% with final stats. No fade-out, no color change.

### Target Tabs
- **D-07:** Target tabs appear immediately after scan submission, even before first results arrive. Badge count starts at 0.
- **D-08:** Target tab bar is always visible, even for single-username scans. Consistency over minimalism.
- **D-09:** Badge count updates in real-time during scan via SSE events.

### Claude's Discretion
- **D-10:** CSS details for header styling (title, subtitle, New Scan button positioning) — match mockup computed styles.
- **D-11:** Progress bar transition timing and easing — match mockup smoothness.
- **D-12:** Target tab hover/active state animations — match mockup behavior.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Visual Reference
- `web-enhanced/static/mockup.html` — THE authoritative visual spec. Line 140: search panel modal positioning. Lines 25-35: progress bar structure. Lines 37-46: target tabs with badges.

### Source Files to Modify
- `web-enhanced/static/index.html` — Functional frontend, search panel currently inline (lines 36-74)
- `web-enhanced/static/style.css` — Layered stylesheet (Phase 2 output), all new rules go into @layer blocks
- `web-enhanced/static/app.js` — `showSearch()` (line 552), `startScan()`, SSE handlers need modal/tab updates

### Requirements
- `.planning/REQUIREMENTS.md` — LAYT-01 through LAYT-05

### Prior Phase Output
- `.planning/phases/02-css-architecture/02-02-SUMMARY.md` — CSS architecture now in place, 47 design tokens available

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Design tokens: 47 custom properties in :root (spacing, typography, transitions, z-index, radii, colors) — use var() references for all new CSS
- @layer structure: new layout rules go in `@layer layout`, new component rules in `@layer components`, state modifiers in `@layer utilities`
- Existing `@keyframes fadeInUp` and `fadeOut` — can reuse for modal animation or define new ones

### Established Patterns
- Dark theme only (--bg-primary through --bg-input)
- All transitions use token vars (--transition-fast, --transition-base, --transition-slow)
- State visibility via `.active` class toggling (`display:none` → `display:block/flex`)

### Integration Points
- `app.js:startScan()` — needs to close modal, show progress bar + target tabs
- `app.js:showSearch()` — needs to open modal with backdrop + animation instead of simple display toggle
- SSE event handler — needs to update target tab badge counts in real-time
- Progress bar update — already wired via `progressFill`, `progressText`, `progressFound`, `progressSite` IDs

</code_context>

<specifics>
## Specific Ideas

- Modal search panel: position:fixed centered with dark backdrop, X close button, fade+scale animation
- Page loads empty with just header — no inline search form on first visit
- Progress bar gradient fill, stays at 100% when complete
- Target tabs always visible, badge updates live

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-layout-and-search-panel*
*Context gathered: 2026-05-09*
