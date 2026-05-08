# Phase 2: CSS Architecture - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure `style.css` with CSS `@layer` ordering, self-host the Inter font as WOFF2 (eliminating the Google Fonts CDN dependency), and extract/align design tokens (colors, spacing, typography, shadows) with mockup.html values. No new visual features — establish the CSS foundation that Phases 3-5 build upon.

</domain>

<decisions>
## Implementation Decisions

### Font Self-Hosting
- **D-01:** Claude's discretion on font hosting details — file location, subsetting strategy (Latin subset, weights 400/500/600/700 per existing Google Fonts request), and @font-face declarations. The Google Fonts `<link>` tags in both `index.html` and `mockup.html` must be removed after self-hosting.

### Layer Ordering Strategy
- **D-02:** Claude's discretion on migration scope — whether to fully migrate all 537 existing lines into the 6 layers (reset, tokens, base, layout, components, utilities) or declare the layer order and selectively migrate. Decision should be based on regression risk assessment. The `@layer` declaration listing all six layers in order must appear at the top of style.css regardless of migration scope (per CSSF-01).

### Token Extraction
- **D-03:** Extract ALL token categories from mockup.html values: spacing scale, typography scale (font sizes, weights), shadows/effects, plus existing colors and radii. Claude decides naming convention and scope. Every hardcoded value in style.css that matches a mockup value should become a custom property where practical.

### Migration Safety
- **D-04:** Claude's discretion on verification approach. mockup.html is the visual reference — any pixel drift from pre-migration appearance is a bug. The project has a vanilla JS / no build tools constraint, so verification approach must respect that.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CSS Source
- `web-enhanced/static/style.css` — 537-line flat CSS, 20 existing custom properties in :root, no @layer, no @font-face
- `web-enhanced/static/index.html` — Lines 8-9 have Google Fonts CDN links to remove
- `web-enhanced/static/mockup.html` — Lines 7-8 have Google Fonts CDN link; this is the visual design reference

### Design Reference
- `web-enhanced/static/mockup.html` — THE authoritative visual spec. All token values must be extracted from this file's inline styles and the shared style.css.

### Requirements
- `.planning/REQUIREMENTS.md` — CSSF-01, CSSF-02, CSSF-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Current State
- `:root` block (style.css:1-20): 20 custom properties — 10 colors, 2 radii. No spacing, no typography tokens.
- `font-family: 'Inter'` (style.css:27): Referenced but loaded via Google Fonts CDN, not self-hosted.
- No `@layer` declarations anywhere in the CSS.
- No `@font-face` declarations.
- No font files on disk (no `static/fonts/` directory).
- `mockup.html` and `index.html` both load `style.css` and both have Google Fonts `<link>` tags.

### Established Patterns
- Dark theme only (--bg-primary: #0f0f14 through --bg-input: #2a2a38)
- Purple accent (--accent: #7c3aed, --accent-hover: #9b5cf6)
- Status colors (--green, --red, --orange, --blue, --cyan)
- Consistent border color (--border: #3a3a4a)

### Risk Areas
- `mockup.html` imports `style.css` twice (via `<link>` and `@import` in inline `<style>`) — restructuring must not break this dual-import
- Unlayered CSS has higher specificity than layered CSS — full migration is safer than partial (mixed state can cause specificity conflicts)

</code_context>

<specifics>
## Specific Ideas

- Both HTML files reference the same style.css — changes affect both simultaneously, which is the desired behavior
- Inter weights 400, 500, 600, 700 are used (matching current Google Fonts request)
- Latin subset is sufficient (OSINT tool, English UI)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 2-CSS Architecture*
*Context gathered: 2026-05-08*
