# Phase 2: CSS Architecture - Research

**Researched:** 2026-05-08
**Domain:** CSS Cascade Layers, Font Self-Hosting, Design Tokens
**Confidence:** HIGH

## Summary

Phase 2 restructures `web-enhanced/static/style.css` (537 lines, no @layer, no @font-face) to have a proper cascade layer architecture, eliminates two Google Fonts CDN requests, and expands the existing 20 custom properties into a full design token set covering spacing, typography, shadows, and existing colors/radii.

The stylesheet is vanilla CSS with no build tools. All changes are purely to `style.css`, `index.html`, and `mockup.html`. No new visual rules are written — this phase only reorganises and tokens-ifies what already exists and adds `@font-face` declarations.

The single most important pitfall: CSS rules **outside** any `@layer` block automatically win over rules inside layers, regardless of specificity. Since the existing 537 lines are entirely unlayered, a **full migration** (wrapping all existing rules into the appropriate layers) is the only safe strategy. A partial migration creates a split-specificity system where the old unlayered rules silently override the new layered ones.

**Primary recommendation:** Declare all six named layers in a single ordering statement at line 1 of style.css; fully migrate all existing rules into their layers in that same file edit; add `@font-face` blocks; expand `:root` tokens; remove Google Fonts `<link>` tags from both HTML files.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None — all implementation details are delegated to Claude.

### Claude's Discretion
- **D-01:** Font hosting details — file location, subsetting strategy (Latin subset, weights 400/500/600/700 per existing Google Fonts request), and @font-face declarations. The Google Fonts `<link>` tags in both `index.html` and `mockup.html` must be removed after self-hosting.
- **D-02:** Migration scope — whether to fully migrate all 537 existing lines into the 6 layers or declare layer order and selectively migrate. Decision should be based on regression risk assessment. The `@layer` declaration listing all six layers in order must appear at the top of style.css regardless of migration scope (per CSSF-01).
- **D-03:** Extract ALL token categories from mockup.html values: spacing scale, typography scale (font sizes, weights), shadows/effects, plus existing colors and radii. Claude decides naming convention and scope. Every hardcoded value in style.css that matches a mockup value should become a custom property where practical.
- **D-04:** Verification approach. mockup.html is the visual reference — any pixel drift from pre-migration appearance is a bug. No build tools.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CSSF-01 | Stylesheet uses CSS @layer with six named layers (reset, tokens, base, layout, components, utilities) | @layer ordering statement at line 1 + full migration of existing rules into layers |
| CSSF-02 | Inter font is self-hosted as WOFF2 (Latin subset, weights 400, 500, 600, 700) | Download 4 WOFF2 files from rsms/inter v4.1, place in static/fonts/, add @font-face in tokens layer |
| CSSF-03 | CSS design tokens (colours, spacing, radii, typography) match mockup.html values exactly | Expand :root block in tokens layer — confirmed existing 20 props correct + extract spacing/typography values |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CSS layer ordering | Browser / Client | — | Pure CSS declaration, no server involvement |
| Font self-hosting | CDN / Static (static/ dir) | Browser / Client | WOFF2 files served as static assets; @font-face in CSS parsed by browser |
| Design tokens (:root) | Browser / Client | — | CSS custom properties resolved at render time |
| HTML link tag removal | Frontend Server (HTML) | — | Edit index.html and mockup.html to remove `<link>` tags |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| CSS @layer (native) | Browser-native (Chromium 99+, Firefox 97+, Safari 15.4+) | Cascade ordering with explicit layer priority | Eliminates specificity conflicts; all target browsers support it [VERIFIED: MDN] |
| CSS custom properties (native) | Browser-native | Design tokens in :root | Zero runtime cost; already used in project [VERIFIED: codebase] |
| Inter font (rsms/inter) | v4.1 (2024-11-16) | Primary UI typeface | Project already uses Inter via CDN; official source [VERIFIED: GitHub API] |
| WOFF2 | — | Font file format | Best compression (~30% smaller than WOFF), 96%+ browser support, no IE dependency [CITED: MDN @font-face] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| google-webfonts-helper (gwfh.mranftl.com) | Web tool | Generate @font-face CSS + download WOFF2 files | Use if direct rsms download is insufficient or subsetting is needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Full migration to @layer | Declare order only, leave rules unlayered | Unlayered rules override all layered rules — creates broken specificity if any rule later moves into a layer. Full migration is the only safe path. |
| rsms/inter v4.1 direct download | Variable font (inter.woff2 single file) | Variable font is 1 file but larger; 4 static weight files are smaller per weight and match exactly what the Google Fonts request already loaded |
| font-display: swap | font-display: optional | `swap` prevents FOIT; `optional` avoids layout shift but may show system font — swap is correct for this dark-themed OSINT tool |

**Installation:** No npm. Font files downloaded manually and placed in `web-enhanced/static/fonts/`.

**Version verification:** Inter v4.1 released 2024-11-16. [VERIFIED: GitHub API `api.github.com/repos/rsms/inter/releases/latest`]

## Architecture Patterns

### System Architecture Diagram

```
index.html / mockup.html
       |
       | <link rel="stylesheet" href="/static/style.css">
       | (Google Fonts <link> tags REMOVED)
       v
  style.css  ←────────────────────────────────────────────┐
       |                                                    |
  @layer reset, tokens, base, layout, components, utilities│
       |                                                    |
  ┌────┴─────────────────────────────────────────────────┐ │
  │  @layer reset        box-sizing, margin/padding 0    │ │
  │  @layer tokens       :root { custom properties }     │ │
  │                      @font-face { Inter weights }    │ │
  │  @layer base         body, * selectors               │ │
  │  @layer layout       .header, .main, .search-panel   │ │
  │                      .progress-container, .target-bar│ │
  │  @layer components   .btn, .form-input, .tag-chip,   │ │
  │                      .result-tab, .profiles-table,   │ │
  │                      .summary-card, .export-card,    │ │
  │                      .graph-container, etc.          │ │
  │  @layer utilities    .active, .open, @media query,   │ │
  │                      @keyframes animations           │ │
  └──────────────────────────────────────────────────────┘ │
                                                            │
  static/fonts/                                             │
       ├── inter-regular.woff2  (weight 400)  ─────────────┘
       ├── inter-medium.woff2   (weight 500)
       ├── inter-semibold.woff2 (weight 600)
       └── inter-bold.woff2     (weight 700)
```

### Recommended Project Structure
```
web-enhanced/static/
├── fonts/
│   ├── inter-regular.woff2      # weight 400
│   ├── inter-medium.woff2       # weight 500
│   ├── inter-semibold.woff2     # weight 600
│   └── inter-bold.woff2         # weight 700
├── style.css                    # restructured with @layer
├── index.html                   # Google Fonts <link> removed
├── mockup.html                  # Google Fonts <link> removed
└── app.js                       # unchanged
```

### Pattern 1: Layer Order Declaration
**What:** A single `@layer` statement at line 1 establishes cascade priority for all six layers. Last layer listed wins conflicts.
**When to use:** Always — must be the very first CSS rule in the file.
**Example:**
```css
/* Source: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer */
@layer reset, tokens, base, layout, components, utilities;
```

### Pattern 2: Layer Block Structure
**What:** Each layer wraps its rules in a named `@layer` block. Rules in later layers override rules in earlier layers regardless of specificity.
**When to use:** All existing rules must be placed inside exactly one layer block.
**Example:**
```css
/* Source: https://css-tricks.com/almanac/rules/l/layer/ */
@layer reset {
  * { box-sizing: border-box; margin: 0; padding: 0; }
}

@layer tokens {
  :root {
    --bg-primary: #0f0f14;
    /* ... all custom properties ... */
    --space-1: 4px;
    --font-size-sm: 12px;
  }
}

@layer base {
  body {
    background: var(--bg-primary);
    font-family: 'Inter', -apple-system, sans-serif;
  }
}
```

### Pattern 3: @font-face in Tokens Layer
**What:** `@font-face` declarations placed inside the `@layer tokens` block, one per weight.
**When to use:** Self-hosted fonts always. `font-display: swap` prevents invisible text during load.
**Example:**
```css
/* Source: https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face */
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
}
```

**Note on `local()`:** Omitting `local()` is acceptable for a dark-themed internal tool. Including it (`local('Inter')`) allows the browser to skip download if Inter is installed locally — a minor optimization, safe to add.

### Pattern 4: Design Token Naming Convention
**What:** Expand `:root` with categorical prefixes. Existing color tokens are already correct. Add spacing, font-size, font-weight, z-index, transition, shadow tokens.
**When to use:** Every hardcoded pixel/value that appears 2+ times or matches a mockup structural value.
**Example:**
```css
/* Source: ASSUMED — naming convention based on project patterns */
:root {
  /* --- Existing colors (verified correct) --- */
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

  /* --- Radii (existing) --- */
  --radius: 8px;
  --radius-lg: 12px;
  --radius-sm: 3px;   /* new: used for progress-bar-track */
  --radius-pill: 10px; /* new: used for .count badge */

  /* --- Spacing scale (extract from recurring values) --- */
  --space-1: 4px;
  --space-2: 6px;
  --space-3: 8px;
  --space-4: 12px;
  --space-5: 16px;
  --space-6: 20px;
  --space-7: 24px;
  --space-8: 32px;

  /* --- Typography: font sizes --- */
  --font-size-xs: 10px;
  --font-size-sm: 11px;
  --font-size-base: 12px;
  --font-size-md: 13px;
  --font-size-lg: 14px;
  --font-size-xl: 18px;
  --font-size-2xl: 22px;
  --font-size-3xl: 28px;

  /* --- Typography: weights --- */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* --- Transitions --- */
  --transition-fast: 0.15s;
  --transition-base: 0.2s;
  --transition-slow: 0.3s;

  /* --- Z-index scale --- */
  --z-header: 100;
  --z-graph-controls: 10;
  --z-graph-fullscreen: 200;
  --z-toast: 300;
  --z-search-panel: 500;
}
```

### Pattern 5: Layer Assignment Guide for Existing Rules
**What:** Which existing selector blocks belong in which layer.
**When to use:** During the single style.css rewrite.

| Layer | What goes in it |
|-------|----------------|
| `reset` | `* { box-sizing... }` (line 22) |
| `tokens` | `:root { }` (lines 1-20) + all `@font-face` declarations |
| `base` | `body { }` (lines 24-31) |
| `layout` | `.header`, `.header-title`, `.progress-container`, `.progress-bar-*`, `.progress-stats`, `.target-bar`, `.target-tab`, `.main`, `.search-panel`, `.results-container`, `.summary-row`, `@media` |
| `components` | All component-specific class selectors: `.btn`, `.form-group`, `.form-input`, `.tag-chip`, `.result-tabs`, `.result-tab`, `.profiles-table`, `.summary-card`, `.graph-container`, `.graph-controls`, `.tags-grid`, `.tag-card`, `.export-grid`, `.export-card`, `.notes-area`, `.raw-json`, `.live-hit`, `.star-btn`, `.response-time`, `.checkbox-row`, `.advanced-toggle`, `.filter-input` |
| `utilities` | `.active`, `.open`, `.starred`, `.fast`, `.slow`, `.found`, `.checking`, `@keyframes fadeInUp`, `@keyframes fadeOut` |

**Note on @keyframes in layers:** `@keyframes` declared inside a `@layer` block are scoped to that layer. Animations referenced via `animation:` properties in other layers can still reference them. Place keyframes in `utilities` with the classes that trigger them. [CITED: MDN @layer]

### Anti-Patterns to Avoid
- **Partial migration (some rules layered, some not):** Unlayered rules always beat layered rules. Any rule left outside a layer will override its layered equivalents silently, causing invisible regressions. [VERIFIED: MDN @layer]
- **!important in layers:** `!important` reverses the layer priority — earlier layers win for !important. The project has no `!important` currently (verified by grep), so do not introduce any during migration. [CITED: Smashing Magazine layer migration guide]
- **@font-face outside layers:** @font-face works identically inside or outside a layer block; it is not a style rule that participates in specificity. Either placement is fine — inside `tokens` layer keeps things organised.
- **Forgetting mockup.html double-import:** mockup.html loads style.css twice (once via `<link>`, once via `@import` in inline `<style>`). This was already the case before the phase and is harmless — the double-import produces no cascade conflict because the file is identical each time. Do not attempt to "fix" this; it is intentional for mockup-only reasons.
- **Using Google Fonts variable font when 4 static weights suffice:** The variable font is one file but ~3x larger. The 4-file approach matches exactly what was previously loaded.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Font subsetting | Python/Node subsetting script | Pre-subset WOFF2 files from rsms/inter (already Latin-only) | rsms provides per-weight WOFF2 files already subsetted; manual subsetting adds toolchain with no benefit |
| Specificity management | ID selectors, !important overrides | @layer ordering | @layer is exactly the native solution for this — any custom hack predates and is inferior to native cascade control |
| Design token documentation | Separate token JSON / doc file | In-file comments in :root block | Project has no build step; a separate token file creates drift risk |

**Key insight:** @layer is a browser-native feature; no toolchain is needed. Font files are static assets; no build step is needed.

## Common Pitfalls

### Pitfall 1: Unlayered Rule Wins Silently
**What goes wrong:** If even one rule is accidentally left outside any @layer block, it will have higher specificity than all layered rules — including utilities — and the visual output will differ from the pre-migration state in subtle, hard-to-debug ways.
**Why it happens:** The spec says unlayered styles occupy an implicit layer above all named layers.
**How to avoid:** After migration, grep for selectors that appear in style.css but are not inside a `@layer { }` block. The only things permitted outside a layer block should be the `@layer reset, tokens, base, layout, components, utilities;` ordering statement itself.
**Warning signs:** Any visual difference between mockup.html before and after the migration, especially hover states or button styles appearing slightly off.

### Pitfall 2: @font-face Relative URL Breaks in mockup.html
**What goes wrong:** mockup.html is served from `/static/mockup.html`. If the `@font-face` src uses `url('fonts/inter-regular.woff2')` (relative, no leading slash), it resolves correctly. But if a test opens the file from a different path, it may 404.
**Why it happens:** The mockup.html `@import url('style.css')` in the inline style tag loads the CSS relative to the HTML document location. As long as both files are in `static/`, relative paths `fonts/inter-regular.woff2` work. Absolute paths `/static/fonts/inter-regular.woff2` are safer.
**How to avoid:** Use server-root-relative paths (`/static/fonts/inter-regular.woff2`) in @font-face src. This is consistent with how style.css is already linked in both HTML files.
**Warning signs:** Network panel shows 404 for font files when viewing mockup.html.

### Pitfall 3: Google Fonts <link> Tags Removed from Wrong File
**What goes wrong:** index.html has TWO Google Fonts tags (lines 8-9: `preconnect` + font CSS link). mockup.html has ONE (line 8: font CSS link only). Removing only one or removing from only one file leaves a CDN request or a duplicate font definition.
**Why it happens:** The two HTML files have different link structures.
**How to avoid:** Remove from both files. In index.html: remove both the `preconnect` and the `fonts.googleapis.com/css2` link. In mockup.html: remove only the `fonts.googleapis.com/css2` link.
**Warning signs:** Network panel shows any request to `fonts.googleapis.com` or `fonts.gstatic.com`.

### Pitfall 4: Font File Download — Outdated Source
**What goes wrong:** Using the Google Fonts CDN download (gwfh.mranftl.com) may serve Inter v3.x rather than v4.1; the official rsms/inter GitHub provides v4.1.
**Why it happens:** Third-party helpers may lag behind upstream releases.
**How to avoid:** Download from official rsms/inter v4.1 release at `https://github.com/rsms/inter/releases/tag/v4.1` or from `https://github.com/rsms/inter/raw/refs/heads/master/docs/font-files/Inter-{Weight}.woff2`.
**Warning signs:** File sizes outside expected range (Regular should be ~100-120 KB for full Latin WOFF2).

### Pitfall 5: Token Naming Conflicts with Existing 20 Properties
**What goes wrong:** The existing 20 custom properties (`--bg-primary`, `--accent`, etc.) must not be renamed — they are referenced throughout all 537 lines of style.css. New tokens are additions only.
**Why it happens:** D-03 says "extract ALL token categories" which could be misread as "rename everything."
**How to avoid:** Add new tokens (spacing, typography, z-index, transitions) alongside the existing 20 — do not rename existing ones. Then do a second pass replacing hardcoded values in the rule blocks with the new tokens.
**Warning signs:** Any `var(--old-name)` reference returning an undefined custom property after the edit.

## Code Examples

Verified patterns from official sources:

### @layer Ordering Statement (must be line 1)
```css
/* Source: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer */
@layer reset, tokens, base, layout, components, utilities;
```

### Verifying No Unlayered Rules Remain (verification command)
```bash
# After migration, this should output ONLY the @layer ordering statement line
grep -v "^@layer" web-enhanced/static/style.css | grep -v "^$" | grep -v "^  " | grep -v "^}"
# Or more simply: look for top-level selector blocks outside @layer { }
```

### @font-face with font-display (canonical form)
```css
/* Source: https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face */
@font-face {
  font-family: 'Inter';
  src: url('/static/fonts/inter-regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
```

### Download Inter v4.1 WOFF2 files (curl commands for Wave 0)
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

### Removing Google Fonts tags from index.html (lines 8-9)
```html
<!-- REMOVE these two lines from index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Removing Google Fonts tag from mockup.html (line 8 only)
```html
<!-- REMOVE this one line from mockup.html -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat CSS with specificity hacks | CSS @layer cascade ordering | Chromium 99 / Firefox 97 / Safari 15.4 (2022) | Specificity conflicts resolved at layer declaration, not selector level |
| Multiple font format fallbacks (eot, ttf, woff, woff2) | WOFF2-only | ~2022 (IE EOL June 2022) | Simpler @font-face, ~30% smaller font payloads |
| Google Fonts CDN | Self-hosted WOFF2 | Ongoing shift post-GDPR | No external request, no privacy concerns, works offline |

**Deprecated/outdated:**
- `format('truetype')` fallback in @font-face: Not needed; IE is EOL, all target browsers support WOFF2 natively.
- `font-variant` subsetting hack: The rsms/inter Latin-subset WOFF2 files are already subset by the source; no CSS `unicode-range` trick needed.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Spacing token names (`--space-1` through `--space-8`) are a reasonable convention for this project | Pattern 4 / Token naming | Low — names are internal and not user-visible; can be renamed at any time without visual regression |
| A2 | @keyframes placed inside `@layer utilities` are accessible to animation rules in other layers | Anti-patterns | Medium — if animations stop working, move @keyframes outside all layers (spec says keyframes in a layer are only accessible within that layer per some interpretations) |
| A3 | rsms/inter GitHub raw file URLs (`/raw/refs/heads/master/...`) are stable and serve v4.1 | Code Examples | Low — these are official GitHub raw URLs; alternatively use the tagged release download |

**A2 clarification (important):** MDN notes that `@keyframes` inside a `@layer` block behave differently across browsers in early implementations. The safe approach is to place `@keyframes` **outside** all `@layer` blocks at the bottom of the file, or in an anonymous unlayered block, to ensure universal accessibility. The planner should account for this and place `@keyframes fadeInUp` and `@keyframes fadeOut` outside any layer.

## Open Questions (RESOLVED)

1. **RESOLVED: @keyframes inside vs outside @layer**
   - What we know: The spec says @keyframes inside a layer should be scoped to that layer. MDN warns browser implementation consistency is imperfect.
   - What's unclear: Whether Chrome/Firefox/Safari all correctly allow cross-layer keyframe references.
   - Resolution: Place `@keyframes` outside all `@layer` blocks (unlayered) to guarantee animation works across all browsers. Since only 2 keyframe blocks exist in the project, this is a minimal footprint. **Implemented in Plan 02-02 Task 1.**

2. **RESOLVED: mockup.html dual CSS import visual fidelity**
   - What we know: mockup.html loads style.css via `<link>` AND via `@import` in an inline `<style>`. This was true before Phase 2.
   - What's unclear: Whether the layered CSS correctly handles the de-duplication when the same file is imported twice.
   - Resolution: Both imports produce identical layer declarations from the same file; browsers deduplicate by source. Verify post-migration by opening mockup.html and checking the Network panel shows only one style.css parse (not two conflicting ones). No action needed unless a visual anomaly appears. **Verified by Plan 02-02 Task 2 visual checkpoint.**

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| curl | Download Inter WOFF2 files | ✓ | system curl | wget (also available) |
| Python 3 | Font subsetting (if needed) | ✓ | 3.9.6 | Not needed — rsms files are pre-subset |
| Node.js | N/A | ✓ | v22.22.2 | N/A |
| Browser (Chrome/Firefox) | Visual verification of mockup.html | [ASSUMED] | — | Any modern browser |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

**Font files to create:** `web-enhanced/static/fonts/` directory does not yet exist. Create it as part of Wave 0.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None detected — CSS/HTML-only phase |
| Config file | N/A |
| Quick run command | `open web-enhanced/static/mockup.html` (visual) |
| Full suite command | Visual diff: open mockup.html before and after, compare against screenshot baseline |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CSSF-01 | style.css line 1 is `@layer reset, tokens, base, layout, components, utilities;` | unit (grep) | `head -1 web-enhanced/static/style.css \| grep "@layer reset, tokens, base, layout, components, utilities"` | ❌ Wave 0 |
| CSSF-01 | No rules exist outside @layer blocks (except ordering stmt) | unit (grep) | `python3 -c "import re, sys; css=open('web-enhanced/static/style.css').read(); unlayered=re.findall(r'(?<!@layer [a-z, ]+\n)\.[a-z]', css); print(len(unlayered)==0)"` | ❌ Wave 0 |
| CSSF-02 | Inter font files exist on disk (all 4 weights) | unit (file check) | `ls web-enhanced/static/fonts/inter-{regular,medium,semibold,bold}.woff2` | ❌ Wave 0 |
| CSSF-02 | No Google Fonts network request in index.html | unit (grep) | `grep -c "fonts.googleapis.com" web-enhanced/static/index.html` (expect 0) | ❌ Wave 0 |
| CSSF-02 | No Google Fonts network request in mockup.html | unit (grep) | `grep -c "fonts.googleapis.com" web-enhanced/static/mockup.html` (expect 0) | ❌ Wave 0 |
| CSSF-03 | All 20 existing color/radius custom properties preserved | unit (grep) | `grep -c "\-\-bg-primary\|\-\-accent\|\-\-green\|\-\-border\|\-\-radius" web-enhanced/static/style.css` (expect >= 20) | ❌ Wave 0 |
| CSSF-03 | Spacing tokens present | unit (grep) | `grep -c "\-\-space-" web-enhanced/static/style.css` (expect >= 6) | ❌ Wave 0 |
| CSSF-03 | Typography tokens present | unit (grep) | `grep -c "\-\-font-size-" web-enhanced/static/style.css` (expect >= 6) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `head -1 web-enhanced/static/style.css` to verify layer ordering line
- **Per wave merge:** All grep checks above
- **Phase gate:** Visual verification — open mockup.html, confirm it looks identical to pre-migration screenshot

### Wave 0 Gaps
- [ ] `web-enhanced/static/fonts/` directory — create before font download
- [ ] Font files (4x WOFF2) — download before style.css @font-face can be tested
- [ ] Snapshot of current mockup.html appearance — take browser screenshot before any CSS change to use as regression baseline

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — CSS-only phase |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | no | N/A — no user input processed |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for Static CSS / Font Self-Hosting

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Serving fonts from external CDN (Google Fonts) | Information Disclosure (IP leakage to Google) | Self-hosting eliminates third-party tracking — this phase resolves it |
| Malicious WOFF2 font file (supply chain) | Tampering | Download from official rsms/inter repo only; verify file size (~100-120 KB for Regular) |

**Security note:** Phase 2 is a net security improvement — removing the Google Fonts CDN dependency eliminates one third-party data exfiltration vector (user IP sent to Google on each page load).

## Sources

### Primary (HIGH confidence)
- MDN Web Docs `@layer` — syntax, specificity behavior, unlayered override rule [VERIFIED: fetched directly]
- CSS-Tricks Almanac `/layer` — layer ordering examples [VERIFIED: fetched via Context7]
- MDN Web Docs `@font-face` — font-display, format() hint, src syntax [CITED: fetched via WebSearch]
- GitHub API `api.github.com/repos/rsms/inter/releases/latest` — v4.1 release date 2024-11-16 [VERIFIED: live API call]
- Codebase (`style.css`, `index.html`, `mockup.html`) — current state, 20 existing tokens, no @layer, no @font-face [VERIFIED: direct file read]

### Secondary (MEDIUM confidence)
- Smashing Magazine "Integrating CSS Cascade Layers To An Existing Project" (2025) — full vs partial migration recommendation [CITED: fetched]
- CSS-Tricks "CSS Cascade Layers" guide — migration strategy for existing projects
- rsms/inter GitHub `docs/font-files/` — WOFF2 file paths and availability [CITED: WebSearch + GitHub raw URL verified]

### Tertiary (LOW confidence)
- Claim about @keyframes cross-layer accessibility — conflicting browser implementations; recommend placing outside layers as precaution [A2 in Assumptions Log]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — @layer and WOFF2 are browser-native, well-documented, verified against MDN
- Architecture: HIGH — direct code inspection of style.css confirms current state; layer assignment map is deterministic
- Pitfalls: HIGH — unlayered override behavior confirmed by MDN spec; other pitfalls confirmed by direct inspection of the two HTML files
- Font download: HIGH — rsms/inter v4.1 confirmed via GitHub API; file URLs confirmed via GitHub web UI

**Research date:** 2026-05-08
**Valid until:** 2026-08-08 (CSS @layer is stable; Inter font may release v4.2+ but v4.1 is fine)
