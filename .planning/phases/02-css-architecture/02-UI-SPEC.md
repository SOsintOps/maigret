---
phase: 2
slug: css-architecture
status: draft
shadcn_initialized: false
preset: none
created: 2026-05-08
---

# Phase 2 — UI Design Contract

> Visual and interaction contract for Phase 2: CSS Architecture.
> This phase has NO new UI features. It restructures the existing flat stylesheet
> into @layer blocks, self-hosts the Inter font, and expands the :root token set.
> All values below are extracted directly from the existing codebase and mockup.html.
> No user-visible appearance may change as a result of this phase.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (vanilla CSS, no component framework) |
| Preset | not applicable |
| Component library | none |
| Icon library | none |
| Font | Inter (self-hosted WOFF2, Latin subset, weights 400/500/600/700) |

**Source:** REQUIREMENTS.md CSSF-02, CONTEXT.md D-01, RESEARCH.md Standard Stack

---

## Spacing Scale

All spacing values below are extracted from the existing `style.css` hardcoded usages.
Tokens use a compact numeric suffix convention (not xs/sm/md) to match the project's
existing custom property naming style (`--bg-primary`, `--radius`, etc.).

| Token | Value | Usage in existing CSS |
|-------|-------|----------------------|
| --space-1 | 4px | Tag chip padding-top/bottom, summary-card value margin-top, tag-count margin-top |
| --space-2 | 6px | Tag chip padding-left/right, form-group label margin-bottom, tag-cloud gap, checkbox-row margin-bottom, progress-stats margin-top |
| --space-3 | 8px | Progress bar padding vertical, tag-card padding vertical, profiles-table th padding, star-btn font-size context, tags-grid gap, btn-primary margin-top, advanced-toggle margin-bottom |
| --space-4 | 12px | Header padding vertical, form-input padding vertical, profiles-toolbar margin-bottom, export-grid gap, filter-input padding, notes-area padding, graph-controls top/right, summary-row gap |
| --space-5 | 16px | Summary-card padding, live-hit padding horizontal, raw-json padding, progress-container padding vertical, result-tab padding vertical |
| --space-6 | 20px | Export-card padding, result-tab padding horizontal, header-title font indent |
| --space-7 | 24px | Main padding, header padding horizontal, progress-container padding horizontal, search-panel margin-bottom, live-hit bottom/right |
| --space-8 | 32px | Search-panel padding |

Exceptions:
- 80px: search-panel margin-top (layout constant, no token — phase 3 scope)
- 600px: graph-container height (layout constant, no token — phase 5 scope)
- 1400px: main max-width (layout constant, no token — phase 3 scope)

**Source:** Extracted from style.css lines 37–537 (direct codebase read). RESEARCH.md Pattern 4.

---

## Typography

All sizes are extracted verbatim from the existing style.css. Weights extracted from
existing @font-face requirements (CSSF-02) and usage in style.css.

| Role | CSS Token | Size | Weight | Line Height | Where used |
|------|-----------|------|--------|-------------|------------|
| Display | --font-size-3xl | 28px | 700 (--font-weight-bold) | 1.2 | .summary-card .value |
| Heading | --font-size-xl | 18px | 700 (--font-weight-bold) | 1.2 | .header-title |
| Subheading | --font-size-2xl | 22px | 400 (--font-weight-normal) | 1.2 | .search-panel h2, .tag-card .tag-count |
| Body | --font-size-lg | 14px | 400 (--font-weight-normal) | 1.5 | body, .form-input, .btn |
| UI / default | --font-size-md | 13px | 400–500 | 1.5 | .result-tab, .profiles-table td, .target-tab, .notes-area, .filter-input |
| Small | --font-size-base | 12px | 400 | 1.5 | .progress-stats, .btn-sm, .star-btn context, .header-title span, .response-time, .raw-json |
| Micro | --font-size-sm | 11px | 600 (--font-weight-semibold) | 1.5 | .form-group label, .profiles-table th, .summary-card .label, .tag-chip |
| Tiny | --font-size-xs | 10px | 400 | 1.5 | .target-tab .count, .result-tab .badge, .profile-tag |

Weight tokens:
| Token | Value |
|-------|-------|
| --font-weight-normal | 400 |
| --font-weight-medium | 500 |
| --font-weight-semibold | 600 |
| --font-weight-bold | 700 |

Monospace font (raw JSON panel only): `'JetBrains Mono', 'Fira Code', monospace` — no token
required; this is a single-use stack for the `.raw-json` component.

**Source:** Extracted from style.css. REQUIREMENTS.md CSSF-02 (Inter weights 400/500/600/700).
RESEARCH.md Pattern 4.

---

## Color

Dark theme only. No light theme. No theme toggle (REQUIREMENTS.md Out of Scope).

### Background / Surface tokens (existing — do not rename)

| Token | Value | Role | 60/30/10 |
|-------|-------|------|---------|
| --bg-primary | #0f0f14 | Page background, dominant surface | 60% |
| --bg-secondary | #1a1a24 | Header, progress bar, target bar | 30% |
| --bg-card | #22222e | Cards, panels, graph container | 30% |
| --bg-input | #2a2a38 | Inputs, hover rows, secondary fills | 30% |

### Text tokens (existing — do not rename)

| Token | Value | Usage |
|-------|-------|-------|
| --text-primary | #e4e4ef | Default body text |
| --text-secondary | #8888a0 | Labels, secondary copy, muted interactive states |
| --text-muted | #55556a | Placeholder text, disabled, metadata |

### Border token (existing — do not rename)

| Token | Value |
|-------|-------|
| --border | #3a3a4a |

### Accent (10%) — existing tokens, do not rename

| Token | Value | Reserved for |
|-------|-------|-------------|
| --accent | #7c3aed | Active tab underline, .target-tab .count badge background, .tag-chip.included background, .btn-primary background, focus border on inputs, .result-tab.active underline, .tag-card hover border, .tag-bar-fill, .export-card format text, checkbox accent-color, .header-title text color |
| --accent-hover | #9b5cf6 | .btn-primary:hover background only |

### Status / semantic colors (existing — do not rename)

| Token | Value | Reserved for |
|-------|-------|-------------|
| --green | #22c55e | .progress-stats .found text, .response-time.fast, .live-hit text, .summary-card .value.green, .result-tab .badge text |
| --green-dim | #166534 | .result-tab .badge background, .live-hit background |
| --red | #ef4444 | .tag-chip.excluded background |
| --orange | #f59e0b | .response-time.slow, .star-btn.starred, .summary-card .value.orange |
| --blue | #3b82f6 | .summary-card .value.blue |
| --cyan | #06b6d4 | .profiles-table a links |

### Radius tokens (existing + additions)

| Token | Value | Usage |
|-------|-------|-------|
| --radius | 8px | Buttons, inputs, cards, table, notes, live-hit |
| --radius-lg | 12px | Search panel, graph container, export panel |
| --radius-sm | 3px | Progress bar track and fill |
| --radius-pill | 10px | .target-tab .count badge |

Note: `--radius-sm` and `--radius-pill` are NEW additions to the existing 20 tokens.
They replace the two hardcoded values `3px` (progress bar, line 65, 73) and `10px`
(.target-tab .count, line 115).

**Source:** style.css lines 1–20 (existing :root), lines 22–537 (all usages).
CONTEXT.md code_context. RESEARCH.md Pattern 4.

---

## Transition tokens (new additions)

| Token | Value | Usage |
|-------|-------|-------|
| --transition-fast | 0.15s | .tag-chip transition, .star-btn transition |
| --transition-base | 0.2s | .target-tab, .btn, .form-input, .result-tab, .tag-card, .export-card, .notes-area, .filter-input, .graph-btn transitions |
| --transition-slow | 0.3s | .progress-bar-fill width transition, animation duration reference |

**Source:** Extracted from all `transition:` declarations in style.css lines 103, 159, 183, 195, 258, 338, 397, 432.

---

## Z-index tokens (new additions)

| Token | Value | Usage |
|-------|-------|-------|
| --z-header | 100 | .header position:sticky z-index |
| --z-graph-controls | 10 | .graph-controls z-index |
| --z-graph-fullscreen | 200 | .graph-container.fullscreen z-index |
| --z-toast | 300 | .live-hit z-index |

Note: Search panel modal overlay z-index is NOT tokenised here — it is a Phase 3
concern (CONTEXT.md "Blockers/Concerns" note about Phase 3 z-index verification).

**Source:** style.css lines 43, 360, 368, 491.

---

## Copywriting Contract

Phase 2 introduces NO new user-visible copy. This phase is an infrastructure
restructure with zero feature changes. No new CTAs, states, or destructive actions.

| Element | Copy | Note |
|---------|------|------|
| Primary CTA | "Start Scan" (existing) | Not modified in this phase |
| Empty state | (existing, not modified) | Phase 3/4 scope |
| Error state | (existing, not modified) | Phase 3/4 scope |
| Destructive confirmation | none | No destructive actions in this phase |

---

## Layer Architecture Contract

This section is unique to Phase 2 and defines the mandatory structural outcome.

### @layer Declaration (line 1 of style.css)

```css
@layer reset, tokens, base, layout, components, utilities;
```

### Layer Assignment

| Layer | Contents |
|-------|----------|
| reset | `* { box-sizing: border-box; margin: 0; padding: 0; }` (style.css line 22) |
| tokens | `:root { }` with all expanded custom properties + all 4 `@font-face` declarations |
| base | `body { }` block (style.css lines 24–31) |
| layout | `.header`, `.header-title`, `.progress-container`, `.progress-bar-*`, `.progress-stats`, `.target-bar`, `.target-tab`, `.main`, `.search-panel`, `.results-container`, `.summary-row`, `@media (max-width: 768px)` |
| components | All component selectors: `.btn`, `.btn-primary`, `.btn-sm`, `.btn-outline`, `.form-group`, `.form-input`, `.form-row`, `.tag-cloud`, `.tag-chip`, `.advanced-toggle`, `.advanced-body`, `.checkbox-row`, `.result-tabs`, `.result-tab`, `.tab-panel`, `.profiles-toolbar`, `.filter-input`, `.profiles-table`, `.profile-tags`, `.profile-tag`, `.star-btn`, `.response-time`, `.graph-container`, `.graph-controls`, `.graph-btn`, `.tags-grid`, `.tag-card`, `.export-grid`, `.export-card`, `.notes-area`, `.raw-json`, `.live-hit`, `.summary-card` |
| utilities | `.active`, `.open`, `.starred`, `.fast`, `.slow`, `.found`, `.checking` state classes |

### @keyframes Placement

`@keyframes fadeInUp` and `@keyframes fadeOut` MUST be placed OUTSIDE all @layer
blocks. Place them at the end of style.css after the closing brace of the last
@layer block. This avoids cross-layer keyframe accessibility inconsistencies
documented in RESEARCH.md Assumptions Log A2.

### Font File Locations

```
web-enhanced/static/fonts/
  inter-regular.woff2    (weight 400)
  inter-medium.woff2     (weight 500)
  inter-semibold.woff2   (weight 600)
  inter-bold.woff2       (weight 700)
```

Source: rsms/inter v4.1 official release. URL pattern:
`https://github.com/rsms/inter/raw/refs/heads/master/docs/font-files/Inter-{Weight}.woff2`

### @font-face src URL pattern

Use server-root-relative paths:
```css
src: url('/static/fonts/inter-regular.woff2') format('woff2');
```
Rationale: mockup.html loads style.css via both `<link>` and `@import` — absolute
paths prevent 404 if either load origin differs. See RESEARCH.md Pitfall 2.

### Google Fonts Tag Removal

| File | Lines to remove | Tags to remove |
|------|----------------|----------------|
| index.html | lines 8–9 | `<link rel="preconnect" href="https://fonts.googleapis.com">` AND `<link href="https://fonts.googleapis.com/css2?...">` |
| mockup.html | line 8 | `<link href="https://fonts.googleapis.com/css2?...">` only (no preconnect tag) |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable — no shadcn |
| third-party | none | not applicable |

No component registry is used. This is a vanilla CSS project with no npm components.

---

## Verification Contract

Visual regression is the primary risk. The following checks define phase acceptance.

| Check | Command | Pass condition |
|-------|---------|----------------|
| Layer order line 1 | `head -1 web-enhanced/static/style.css` | Exactly: `@layer reset, tokens, base, layout, components, utilities;` |
| No unlayered rules | `grep -c "fonts.googleapis.com" web-enhanced/static/index.html` | 0 |
| No Google Fonts (index) | `grep -c "fonts.googleapis.com" web-enhanced/static/index.html` | 0 |
| No Google Fonts (mockup) | `grep -c "fonts.googleapis.com" web-enhanced/static/mockup.html` | 0 |
| Font files exist | `ls web-enhanced/static/fonts/inter-{regular,medium,semibold,bold}.woff2` | All 4 files present |
| Existing color tokens preserved | `grep -c "\-\-bg-primary" web-enhanced/static/style.css` | >= 1 |
| Spacing tokens added | `grep -c "\-\-space-" web-enhanced/static/style.css` | >= 6 |
| Typography tokens added | `grep -c "\-\-font-size-" web-enhanced/static/style.css` | >= 6 |
| Visual parity | Open mockup.html in browser before and after | No visible difference |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS (no new copy; existing copy unchanged)
- [ ] Dimension 2 Visuals: PASS (zero visual change required — parity is the spec)
- [ ] Dimension 3 Color: PASS (60/30/10 contract documented; no values changed)
- [ ] Dimension 4 Typography: PASS (8 size roles declared; 4 weight tokens declared)
- [ ] Dimension 5 Spacing: PASS (8 spacing tokens declared from extracted values)
- [ ] Dimension 6 Registry Safety: PASS (no registry; vanilla CSS)

**Approval:** pending
