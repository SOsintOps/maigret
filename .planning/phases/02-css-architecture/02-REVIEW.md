---
phase: 02-css-architecture
reviewed: 2026-05-09T00:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - web-enhanced/static/index.html
  - web-enhanced/static/style.css
  - web-enhanced/static/mockup.html
findings:
  critical: 2
  warning: 7
  info: 5
  total: 14
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-09
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Three files were reviewed: the production HTML template (`index.html`), the design mockup (`mockup.html`), and the shared CSS architecture (`style.css`). The CSS layer architecture is well-structured and the token system is comprehensive. However, two critical issues were found — an XSS vulnerability in the mockup's DOM rendering pattern, and a missing SRI hash on a CDN-loaded dependency — along with several layout/structural bugs and code quality problems.

---

## Critical Issues

### CR-01: XSS via Unescaped HTML Injection in `renderProfiles`

**File:** `web-enhanced/static/mockup.html:224-234`
**Issue:** `renderProfiles` constructs table rows using template literals that inject `p.site`, `p.url`, and tag values directly into `innerHTML` without HTML-escaping. If any server-returned value contains HTML metacharacters (e.g. `<script>alert(1)</script>` in a site name, or a crafted URL), it will execute in the user's browser. This is the established pattern for the real `app.js` as well — the mockup demonstrates the unsafe approach that the production code is expected to follow.

```js
// UNSAFE — current code
body.innerHTML = list.map(p => {
  const tags = p.tags.map(t => `<span class="profile-tag">${t}</span>`).join('');
  return `<tr>
    <td><button ... >${p.starred?'★':'☆'}</button></td>
    <td>${p.site}</td>
    <td><a href="${p.url}" target="_blank">${p.url}</a></td>
    ...
  </tr>`;
}).join('');

// SAFE — escape all server-supplied strings before inserting into HTML
function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
// Then use: <td>${esc(p.site)}</td>
//           <a href="${esc(p.url)}" ...>${esc(p.url)}</a>
```

**Fix:** Create an `esc()` helper and wrap every server-supplied interpolation. Alternatively, build rows via `document.createElement` and set `textContent`/`href` properties directly.

---

### CR-02: No Subresource Integrity (SRI) on CDN Script

**File:** `web-enhanced/static/index.html:8`, `web-enhanced/static/mockup.html:8`
**Issue:** D3 v7 is loaded from `https://d3js.org/d3.v7.min.js` with no `integrity` attribute. If the CDN is compromised or the URL is hijacked (supply-chain attack), arbitrary JavaScript executes with full access to the OSINT investigation data. This is especially sensitive given the nature of the application (OSINT data about real people).

```html
<!-- UNSAFE — current -->
<script src="https://d3js.org/d3.v7.min.js"></script>

<!-- SAFE — add SRI hash -->
<script src="https://d3js.org/d3.v7.min.js"
        integrity="sha384-<hash>"
        crossorigin="anonymous"></script>
```

**Fix:** Generate the SHA-384 hash of the pinned d3 bundle (`openssl dgst -sha384 -binary d3.v7.min.js | openssl base64 -A`) and add it as the `integrity` attribute. Better: vendor the library into `/static/vendor/` to eliminate the CDN dependency entirely.

---

## Warnings

### WR-01: `.target-bar` Has Duplicate `display` Property — Second Value Silently Wins

**File:** `web-enhanced/static/style.css:173-176`
**Issue:** The `.target-bar` rule sets `display: flex` on line 173 and then immediately `display: none` on line 175 within the same declaration block. The second declaration overrides the first, making `display: flex` a dead property. The intent is clearly to hide it by default and show it with `.active`, but the dead `display: flex` implies a developer intended to set the flex layout on this element while hidden. The `display: flex` applied by `.target-bar.active` in the utilities layer (line 581) provides the correct flex value when active, so this is currently harmless, but it creates confusion and a latent risk if the rule order is ever changed.

```css
/* CURRENT — display: flex is dead */
.target-bar {
  ...
  display: flex;   /* line 173 — overridden immediately */
  overflow-x: auto;
  display: none;   /* line 175 — this wins */
}

/* FIX — remove the duplicate, keep only the default hidden state */
.target-bar {
  ...
  overflow-x: auto;
  display: none;
}
```

---

### WR-02: `index.html` Missing `.main` Wrapper — Layout Differs from Mockup

**File:** `web-enhanced/static/index.html:77-170`
**Issue:** In `mockup.html`, the summary cards and tabs are wrapped in `<div class="main">` (line 47), which applies `max-width: 1400px; margin: 0 auto; padding: var(--space-7)` via `style.css:196`. In `index.html`, `.results-container` directly contains `.summary-row` without any `.main` wrapper. This means the live production template renders full-width content with no padding or max-width centering, visually diverging from the intended design. The `.main` class defined in `style.css` is unused in the live template.

**Fix:** Wrap the contents of `#resultsContainer` in a `<div class="main">` in `index.html`:
```html
<div class="results-container" id="resultsContainer">
  <div class="main">
    <div class="summary-row" id="summaryRow">...
    ...
  </div>
</div>
```

---

### WR-03: `mockup.html` Double-Loads `style.css`

**File:** `web-enhanced/static/mockup.html:7-11`
**Issue:** `style.css` is loaded twice: once via `<link rel="stylesheet" href="/static/style.css">` (line 7) and again via `@import url('style.css')` inside an inline `<style>` block (line 11). The `@import` uses a relative path that will resolve differently than the absolute `/static/` path depending on how the file is served. This causes style.css to be fetched twice, and the `@import` version with a relative path will fail when served through the Flask app (the URL `style.css` without `/static/` prefix will 404), leaving a dangling import that may cause browser warnings.

```html
<!-- CURRENT — double-load -->
<link rel="stylesheet" href="/static/style.css">
<style>
  /* inline override: load style.css via relative path too */
  @import url('style.css');   <!-- this is redundant and breaks when served -->
</style>

<!-- FIX — remove the <style> block entirely -->
<link rel="stylesheet" href="/static/style.css">
```

---

### WR-04: Star Button Toggle Does Not Update Glyph Text

**File:** `web-enhanced/static/mockup.html:228`
**Issue:** The star button in `renderProfiles` sets its text to `★` or `☆` at render time based on `p.starred`, but the `onclick` handler only toggles the CSS class `starred` — it does not update the button's text content. After clicking, the visual glyph stays fixed (either `★` or `☆` based on initial render) while the class state toggles. The CSS `.star-btn.starred` rule only changes the color, not the character. The starred/unstarred visual state is therefore partially broken.

```js
// CURRENT — glyph never changes on click
<button class="star-btn ${p.starred?'starred':''}"
        onclick="this.classList.toggle('starred')">
  ${p.starred?'★':'☆'}
</button>

// FIX — update text content on toggle
onclick="this.classList.toggle('starred'); this.textContent = this.classList.contains('starred') ? '★' : '☆';"
```

---

### WR-05: `results-container` Hidden in `components` Layer Cannot Be Shown from `index.html` JS

**File:** `web-enhanced/static/style.css:325`, `web-enhanced/static/index.html:77`
**Issue:** `.results-container { display: none; }` is set in the `components` layer. The `.results-container.active { display: block; }` override is in the `utilities` layer (line 592), which has higher layer precedence. This pattern is correct. However, in `index.html`, the element has `id="resultsContainer"` and the production JavaScript (`app.js`) is expected to add the `active` class to show it. If `app.js` instead uses inline style `element.style.display = 'block'`, the inline style will win over the layer — but it also means the `display: flex` used for the mockup `.main` wrapping (which is absent here) creates inconsistent rendering. The interaction between the missing `.main` wrapper (WR-02) and the visibility toggle compounds into a layout where padding and centering are missing when results appear.

**Fix:** Resolve WR-02 first. Then confirm `app.js` uses `element.classList.add('active')` rather than inline style manipulation.

---

### WR-06: Inline Styles Bypass Token System in Both HTML Files

**File:** `web-enhanced/static/index.html:15,101`, `web-enhanced/static/mockup.html:19,69`
**Issue:** Several `<div>` containers use inline `style="display:flex;gap:8px;align-items:center;"` and `style="display:flex;gap:6px;"`. These use raw pixel values that bypass the CSS token system (e.g. `gap:8px` should be `var(--space-3)`, `gap:6px` should be `var(--space-2)`). Inline styles cannot be overridden by utility classes or media queries without `!important`, breaking responsive behavior.

**Fix:** Extract these into named utility or component classes (e.g. `.flex-row`, `.btn-group`) in `style.css` using token variables.

---

### WR-07: Magic Number Font Sizes Not Using Tokens

**File:** `web-enhanced/static/style.css:411,466,500`
**Issue:** Three font-size values are hardcoded as raw pixel values outside the token system:
- Line 411: `.star-btn { font-size: 16px; }` — no `--font-size-*` token exists for 16px
- Line 466: `.tag-card .tag-count { font-size: 20px; }` — no token for 20px
- Line 500: `.export-card .format { font-size: 24px; }` — no token for 24px

These will not scale if the token scale is updated and create inconsistency with the defined token set.

**Fix:** Add tokens `--font-size-base-icon: 16px`, or map to nearest existing tokens, or add `--font-size-display: 20px` and `--font-size-hero: 24px` to the `:root` block and reference them.

---

## Info

### IN-01: `mockup.html` Contains Investigation Data That Looks Like Real PII

**File:** `web-enhanced/static/mockup.html:125-133,307-319`
**Issue:** The mockup contains fabricated-but-realistic personal data: `email: jdoe@mail.com`, `fullname: John Doe`, `location: Berlin`, and a notes textarea pre-filled with investigation details. If this file is ever served publicly or committed to a public repo, it could be mistaken for real OSINT data. The graph nodes at line 307–319 embed these strings directly into the D3 node data.

**Fix:** Use obviously fake placeholder text (e.g., `email: user@example.com`, `fullname: Example Person`) to make the mock nature unambiguous.

---

### IN-02: `@import` Inside `mockup.html` Has Misleading Comment

**File:** `web-enhanced/static/mockup.html:10`
**Issue:** The comment reads `/* inline override: load style.css via relative path too */` which misrepresents the effect. It does not "override" anything — it attempts to re-import the same stylesheet. The comment will mislead future maintainers about intent.

**Fix:** Remove the entire `<style>` block (as noted in WR-03).

---

### IN-03: Monospace Fonts Referenced in CSS Are Not Declared with `@font-face`

**File:** `web-enhanced/static/style.css:531`
**Issue:** `.raw-json` references `'JetBrains Mono'` and `'Fira Code'` in its font stack, but no `@font-face` declarations exist for these. The browser will fall through to the system `monospace` font. This is functional but the design intent (a specific monospace face) will not be achieved unless these fonts happen to be installed on the user's system. Unlike the Inter declarations at lines 8–35, no web font source is provided for the code font.

**Fix:** Either add `@font-face` declarations pointing to hosted `.woff2` files, use a system font stack only (`ui-monospace, 'Cascadia Code', monospace`), or document the intentional fallback.

---

### IN-04: `live-hit` Toast Appended Directly to `<body>` Without Cleanup Guard

**File:** `web-enhanced/static/mockup.html:363-376`
**Issue:** The demo `setTimeout` callbacks append a `div.live-hit` to `document.body` and schedule removal after 3.5s. If `renderGraph()` or a navigation event reloads the page before the timeout fires, the `div.remove()` call operates on a detached node, which is harmless in modern browsers but is a latent pattern to avoid in production `app.js`. No reference is stored to allow early cleanup.

**Fix:** Store the return value of `setTimeout` and call `clearTimeout` on navigation/cleanup. Store a reference to the div for potential early removal.

---

### IN-05: `progress-container` Requires `.active` Class But `index.html` Never Adds It Explicitly

**File:** `web-enhanced/static/index.html:21-30`
**Issue:** The element `<div class="progress-container" id="progressContainer">` (line 21) has no `active` class in the initial markup, and `style.css:578` shows it only displays when `.active` is present. This is correct — `app.js` adds it. However, the `mockup.html` uses `class="progress-container active"` without the `id`, meaning the mockup bypasses the dynamic show/hide by hard-coding the `active` class. If a developer copies markup patterns from the mockup to production, they may hardcode `active` and break the hide/show behavior.

**Fix:** Add a comment in `mockup.html` on the `progress-container` element noting that the `active` class is for mockup display only and must not be hardcoded in the production template.

---

_Reviewed: 2026-05-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
