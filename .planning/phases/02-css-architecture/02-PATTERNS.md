# Phase 2: CSS Architecture - Pattern Map

**Mapped:** 2026-05-08
**Files analyzed:** 3 modified files + 1 new directory
**Analogs found:** 3 / 3 (self-analog — single-file project; patterns extracted from the files being modified)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `web-enhanced/static/style.css` | config (stylesheet) | transform (restructure-in-place) | itself (current state, lines 1-537) | self |
| `web-enhanced/static/index.html` | config (markup) | transform (tag removal) | `web-enhanced/static/mockup.html` | role-match |
| `web-enhanced/static/mockup.html` | config (markup) | transform (tag removal) | `web-enhanced/static/index.html` | role-match |
| `web-enhanced/static/fonts/` | config (static assets) | file-I/O (download + serve) | none (new directory) | no analog |

---

## Pattern Assignments

### `web-enhanced/static/style.css` (stylesheet, transform)

**Analog:** itself — current content is the source of truth for what gets restructured.

**Current :root block** (lines 1-20) — PRESERVE ALL 20 PROPERTIES, ADD NEW TOKENS ALONGSIDE:
```css
:root {
  --bg-primary: #0f0f14;
  --bg-secondary: #1a1a24;
  --bg-card: #22222e;
  --bg-input: #2a2a38;
  --border: #3a3a4a;
  --text-primary: #e4e4ef;
  --text-secondary: #8888a0;
  --text-muted: #55556a;
  --accent: #7c3aed;
  --accent-hover: #9b5cf6;
  --green: #22c55e;
  --green-dim: #166534;
  --red: #ef4444;
  --orange: #f59e0b;
  --blue: #3b82f6;
  --cyan: #06b6d4;
  --radius: 8px;
  --radius-lg: 12px;
}
```
**Rule:** Do NOT rename any of these. New tokens are additive only.

**Layer ordering statement** (must be line 1 of the restructured file):
```css
@layer reset, tokens, base, layout, components, utilities;
```

**Layer: reset** — source: style.css line 22:
```css
@layer reset {
  * { box-sizing: border-box; margin: 0; padding: 0; }
}
```

**Layer: tokens** — source: style.css lines 1-20 (expanded with new tokens) + all four @font-face blocks:
```css
@layer tokens {
  @font-face {
    font-family: 'Inter';
    src: url('/static/fonts/inter-regular.woff2') format('woff2');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
  }
  @font-face {
    font-family: 'Inter';
    src: url('/static/fonts/inter-medium.woff2') format('woff2');
    font-weight: 500;
    font-style: normal;
    font-display: swap;
  }
  @font-face {
    font-family: 'Inter';
    src: url('/static/fonts/inter-semibold.woff2') format('woff2');
    font-weight: 600;
    font-style: normal;
    font-display: swap;
  }
  @font-face {
    font-family: 'Inter';
    src: url('/static/fonts/inter-bold.woff2') format('woff2');
    font-weight: 700;
    font-style: normal;
    font-display: swap;
  }

  :root {
    /* --- Colors (existing 16, verbatim) --- */
    --bg-primary: #0f0f14;
    --bg-secondary: #1a1a24;
    --bg-card: #22222e;
    --bg-input: #2a2a38;
    --border: #3a3a4a;
    --text-primary: #e4e4ef;
    --text-secondary: #8888a0;
    --text-muted: #55556a;
    --accent: #7c3aed;
    --accent-hover: #9b5cf6;
    --green: #22c55e;
    --green-dim: #166534;
    --red: #ef4444;
    --orange: #f59e0b;
    --blue: #3b82f6;
    --cyan: #06b6d4;

    /* --- Radii (existing 2 + 2 new) --- */
    --radius: 8px;
    --radius-lg: 12px;
    --radius-sm: 3px;    /* progress-bar-track (lines 65-66) */
    --radius-pill: 10px; /* .count badge (line 115) */

    /* --- Spacing scale (extracted from recurring px values) --- */
    --space-1: 4px;   /* tag-chip padding-top/bottom (line 174) */
    --space-2: 6px;   /* gap values, margin-top (lines 78, 116) */
    --space-3: 8px;   /* padding, margin, gap (lines 37, 57) */
    --space-4: 12px;  /* padding-x, gap (lines 37, 58, 278) */
    --space-5: 16px;  /* padding, gap (lines 189, 429, 512) */
    --space-6: 20px;  /* export-card padding (line 429) */
    --space-7: 24px;  /* .main padding, .header padding-x (lines 37, 120) */
    --space-8: 32px;  /* .search-panel padding (line 129) */

    /* --- Typography: font sizes --- */
    --font-size-xs: 10px;   /* .count, .badge, .profile-tag (lines 114, 262, 323) */
    --font-size-sm: 11px;   /* .profiles-table th, .summary-card .label (lines 297, 516) */
    --font-size-base: 12px; /* body default used widely (line 28 comment; many rules) */
    --font-size-md: 13px;   /* .target-tab, .result-tab, .tag-card .tag-name (lines 98, 251, 399) */
    --font-size-lg: 14px;   /* body, .form-input, .btn, .graph-btn (lines 28, 157, 193, 380) */
    --font-size-xl: 18px;   /* .header-title (line 47) */
    --font-size-2xl: 22px;  /* .search-panel h2 (line 133) */
    --font-size-3xl: 28px;  /* .summary-card .value (line 522) */

    /* --- Typography: font weights --- */
    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;

    /* --- Transitions --- */
    --transition-fast: 0.15s;  /* .tag-chip (line 181) */
    --transition-base: 0.2s;   /* most hover transitions (lines 103, 159, 195, 214, 257, 337) */
    --transition-slow: 0.3s;   /* .progress-bar-fill, .live-hit animation (lines 73, 489) */

    /* --- Z-index scale --- */
    --z-header: 100;           /* .header (line 43) */
    --z-graph-controls: 10;    /* .graph-controls (line 367) */
    --z-graph-fullscreen: 200; /* .graph-container.fullscreen (line 358) */
    --z-toast: 300;            /* .live-hit (line 491) */
  }
}
```

**Layer: base** — source: style.css lines 24-31:
```css
@layer base {
  body {
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.5;
    min-height: 100vh;
  }
}
```

**Layer: layout** — source: style.css lines 34-121 (header, progress bar, target bar, main). Key selectors:
```
.header, .header-title, .header-title span,
.progress-container, .progress-container.active,
.progress-bar-track, .progress-bar-fill,
.progress-stats, .progress-stats .found, .progress-stats .checking,
.target-bar, .target-bar.active, .target-tab, .target-tab:hover,
.target-tab.active, .target-tab .count,
.main,
.summary-row,
@media (max-width: 768px) { ... }
```

**Layer: components** — source: style.css lines 123-500 (all component classes). Key selectors:
```
.search-panel, .search-panel h2, .search-panel .subtitle,
.form-group, .form-group label, .form-input, .form-input:focus,
.form-input::placeholder, .form-row, .form-row .form-group,
.tag-cloud, .tag-chip, .tag-chip:hover, .tag-chip.included,
.tag-chip.excluded,
.btn, .btn-primary, .btn-primary:hover, .btn-primary:disabled,
.btn-sm, .btn-outline, .btn-outline:hover,
.advanced-toggle, .advanced-toggle:hover, .advanced-body,
.advanced-body.open,
.checkbox-row, .checkbox-row input[type="checkbox"],
.results-container, .results-container.active,
.result-tabs, .result-tab, .result-tab:hover, .result-tab.active,
.result-tab .badge, .tab-panel, .tab-panel.active,
.profiles-toolbar, .filter-input, .filter-input:focus,
.profiles-table, .profiles-table th, .profiles-table th:hover,
.profiles-table td, .profiles-table tr:hover,
.profiles-table a, .profiles-table a:hover,
.profile-tags, .profile-tag,
.star-btn, .star-btn:hover, .star-btn.starred,
.response-time, .response-time.fast, .response-time.slow,
.graph-container, .graph-container.fullscreen,
.graph-controls, .graph-btn, .graph-btn:hover,
.tags-grid, .tag-card, .tag-card:hover,
.tag-card .tag-name, .tag-card .tag-count,
.tag-card .tag-bar, .tag-card .tag-bar-fill,
.export-grid, .export-card, .export-card:hover,
.export-card .format, .export-card .desc,
.notes-area, .notes-area:focus,
.raw-json,
.live-hit,
.summary-card, .summary-card .label, .summary-card .value,
.summary-card .value.green, .summary-card .value.accent,
.summary-card .value.blue, .summary-card .value.orange
```

**Layer: utilities** — source: style.css lines 60, 81-82, 95, 106-109, 184-186, 203-204, 227, 241, 259, 270, 313, 338, 341-342, 354, 526-529, 532-537. Key selectors and note on @keyframes:
```
.progress-container.active, .progress-stats .found, .progress-stats .checking,
.target-bar.active, .target-tab.active,
.tag-chip.included, .tag-chip.excluded,
.btn-primary:disabled,
.advanced-body.open,
.results-container.active, .result-tab.active,
.tab-panel.active,
.profiles-table tr:hover,
.star-btn.starred,
.response-time.fast, .response-time.slow,
.graph-container.fullscreen,
.summary-card .value.green/accent/blue/orange
```

**@keyframes placement** — OUTSIDE all @layer blocks (unlayered), placed at the very end of the file. This guarantees cross-browser animation accessibility (see A2 / Open Question 1 in RESEARCH.md):
```css
/* OUTSIDE all @layer blocks — unlayered to guarantee cross-browser keyframe accessibility */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
```

**Token substitution pass** — after all rules are placed in layers, substitute hardcoded values with new tokens in the rule bodies. Priority targets (values appearing 3+ times):
- `0.2s` → `var(--transition-base)` (appears in ~8 rules: lines 103, 159, 195, 215, 257, 337, 396, 433)
- `z-index: 100` → `var(--z-header)` (line 43)
- `z-index: 200` → `var(--z-graph-fullscreen)` (line 358)
- `z-index: 300` → `var(--z-toast)` (line 491)
- `z-index: 10` → `var(--z-graph-controls)` (line 367)
- `border-radius: 3px` → `var(--radius-sm)` (lines 65, 73)
- `border-radius: 10px` → `var(--radius-pill)` (line 115)

---

### `web-enhanced/static/index.html` (markup, transform)

**Analog:** `web-enhanced/static/mockup.html` (same role, different content)

**Lines to REMOVE** (index.html lines 8-9):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Result after removal** (lines 7-10 become):
```html
<link rel="stylesheet" href="/static/style.css">
<script src="https://d3js.org/d3.v7.min.js"></script>
```
No other changes to index.html.

---

### `web-enhanced/static/mockup.html` (markup, transform)

**Analog:** `web-enhanced/static/index.html` (same role, different content)

**Line to REMOVE** (mockup.html line 8 only — no preconnect tag in this file):
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Line to PRESERVE** (mockup.html line 11-13 inline style block — do NOT touch):
```html
<style>
  /* inline override: load style.css via relative path too */
  @import url('style.css');
</style>
```
This double-import is intentional. Do not remove or "fix" it.

**Result after removal** (lines 7-9 become):
```html
<link rel="stylesheet" href="/static/style.css">
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
```

---

### `web-enhanced/static/fonts/` (static assets, file-I/O)

**No analog** — new directory. See "No Analog Found" section.

---

## Shared Patterns

### Full Migration Mandate
**Source:** RESEARCH.md "The single most important pitfall"
**Apply to:** style.css restructuring
Every rule must land inside exactly one `@layer { }` block. The only content permitted outside any layer block is:
1. The `@layer reset, tokens, base, layout, components, utilities;` ordering statement (line 1)
2. The two `@keyframes` blocks (end of file, unlayered by design)

### Token Preservation
**Source:** RESEARCH.md Pitfall 5 / style.css lines 1-20
**Apply to:** `:root` block in `@layer tokens`
All 20 existing custom property names are load-bearing — they are referenced throughout all 537 lines of style.css. New tokens are additions alongside them, never renames.

### Font URL Scheme
**Source:** RESEARCH.md Pitfall 2
**Apply to:** All four `@font-face` src declarations in `@layer tokens`
Use server-root-relative paths, not bare-relative paths:
```css
/* CORRECT */
src: url('/static/fonts/inter-regular.woff2') format('woff2');

/* WRONG — breaks when mockup.html is served from a different path */
src: url('fonts/inter-regular.woff2') format('woff2');
```

### No !important
**Source:** RESEARCH.md Anti-Patterns
**Apply to:** All layers
The current codebase has zero `!important` declarations. Do not introduce any. `!important` reverses layer priority and creates invisible bugs.

### No Partial Migration
**Source:** RESEARCH.md Standard Stack alternatives table
**Apply to:** style.css restructuring
Unlayered rules beat all layered rules per the CSS spec. A mixed state (some rules in layers, some outside) produces silent specificity regressions indistinguishable from correctness until visual inspection reveals them.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `web-enhanced/static/fonts/inter-regular.woff2` | static asset | file-I/O | No font files exist on disk; new download |
| `web-enhanced/static/fonts/inter-medium.woff2` | static asset | file-I/O | No font files exist on disk; new download |
| `web-enhanced/static/fonts/inter-semibold.woff2` | static asset | file-I/O | No font files exist on disk; new download |
| `web-enhanced/static/fonts/inter-bold.woff2` | static asset | file-I/O | No font files exist on disk; new download |

**Font acquisition commands** (from RESEARCH.md Code Examples):
```bash
mkdir -p web-enhanced/static/fonts
curl -L -o web-enhanced/static/fonts/inter-regular.woff2 \
  "https://github.com/rsms/inter/raw/refs/heads/master/docs/font-files/Inter-Regular.woff2"
curl -L -o web-enhanced/static/fonts/inter-medium.woff2 \
  "https://github.com/rsms/inter/raw/refs/heads/master/docs/font-files/Inter-Medium.woff2"
curl -L -o web-enhanced/static/fonts/inter-semibold.woff2 \
  "https://github.com/rsms/inter/raw/refs/heads/master/docs/font-files/Inter-SemiBold.woff2"
curl -L -o web-enhanced/static/fonts/inter-bold.woff2 \
  "https://github.com/rsms/inter/raw/refs/heads/master/docs/font-files/Inter-Bold.woff2"
```
Expected file size: ~100-120 KB for Regular weight. Sizes outside this range indicate the wrong source.

---

## Selector → Layer Assignment Quick Reference

| Selector(s) | Layer | Source Lines |
|-------------|-------|-------------|
| `* { box-sizing... }` | reset | 22 |
| `:root { }`, `@font-face` | tokens | 1-20 + new |
| `body { }` | base | 24-31 |
| `.header`, `.header-title`, `.progress-container`, `.progress-bar-*`, `.progress-stats`, `.target-bar`, `.target-tab`, `.target-tab .count`, `.main`, `.summary-row`, `@media` | layout | 34-121, 503-508, 532-537 |
| `.search-panel`, `.form-*`, `.tag-cloud`, `.tag-chip`, `.btn*`, `.advanced-*`, `.checkbox-row`, `.results-container`, `.result-tab*`, `.tab-panel`, `.profiles-toolbar`, `.filter-input`, `.profiles-table`, `.profile-tag*`, `.star-btn`, `.response-time`, `.graph-container`, `.graph-controls`, `.graph-btn`, `.tags-grid`, `.tag-card`, `.export-grid`, `.export-card`, `.notes-area`, `.raw-json`, `.live-hit`, `.summary-card` | components | 123-500, 503-530 |
| State modifiers: `.active`, `.open`, `.starred`, `.fast`, `.slow`, `.found`, `.checking`, `.fullscreen`, color variants (`.green`, `.accent`, `.blue`, `.orange`) | utilities | scattered throughout |
| `@keyframes fadeInUp`, `@keyframes fadeOut` | UNLAYERED (end of file) | 493-500 |

---

## Metadata

**Analog search scope:** `web-enhanced/static/` (only directory with CSS/HTML source)
**Files scanned:** 3 (style.css, index.html, mockup.html)
**Pattern extraction date:** 2026-05-08
**Self-analog note:** This is a single-file CSS project with no framework. The "analog" is the current state of the file being transformed. All patterns are extracted directly from style.css lines 1-537 and the two HTML files.
