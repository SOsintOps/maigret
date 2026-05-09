---
phase: 02-css-architecture
plan: "02"
subsystem: frontend/css
tags: [css-layers, design-tokens, font-face, cascade, refactor]
dependency_graph:
  requires: [web-enhanced/static/fonts/inter-regular.woff2, web-enhanced/static/fonts/inter-medium.woff2, web-enhanced/static/fonts/inter-semibold.woff2, web-enhanced/static/fonts/inter-bold.woff2]
  provides: [web-enhanced/static/style.css]
  affects: [web-enhanced/static/index.html, web-enhanced/static/mockup.html]
tech_stack:
  added: [CSS @layer cascade ordering, CSS custom properties expanded (42 tokens)]
  patterns: [@layer six-layer architecture, design token system, @font-face self-hosted fonts, unlayered @keyframes for cross-browser compatibility]
key_files:
  created: []
  modified:
    - web-enhanced/static/style.css
decisions:
  - "Full migration of all 537 lines into @layer blocks — no partial migration (follows RESEARCH.md mandate: unlayered rules override all layered rules)"
  - "@keyframes placed outside all @layer blocks for cross-browser keyframe accessibility (RESEARCH.md Open Question 1 resolution)"
  - "Token substitution applied to all hardcoded values that have clean token equivalents; single-use values (tag-chip border-radius:12px, tag-count font-size:20px, export-card .format font-size:24px, star-btn font-size:16px, 10px paddings) left as hardcoded px per plan rule 5/6"
  - "Existing 20 custom property names preserved verbatim — new tokens are additive only (RESEARCH.md Pitfall 5)"
metrics:
  duration: "~15 minutes"
  completed: "2026-05-09"
  tasks_completed: 1
  tasks_total: 2
  tasks_pending: 1 (Task 2: human-verify checkpoint)
requirements_satisfied: [CSSF-01, CSSF-03]
---

# Phase 02 Plan 02: CSS @layer Architecture and Expanded Tokens Summary

Full rewrite of style.css from flat 537-line CSS into a six-layer @layer cascade architecture with 4 @font-face declarations for self-hosted Inter font and 42 design tokens expanded from the original 18 custom properties.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rewrite style.css with @layer architecture and expanded tokens | b58732a | web-enhanced/static/style.css |

## Tasks Pending

| Task | Name | Type | Status |
|------|------|------|--------|
| 2 | Visual regression check | checkpoint:human-verify | Awaiting human verification |

## Verification Results

All automated acceptance criteria passed:

| Check | Result |
|-------|--------|
| `head -1 style.css` is exactly the @layer ordering statement | PASS |
| `grep -c "@font-face" style.css` returns 4 | PASS |
| `grep -c "--space-" style.css` returns >= 6 (actual: 58) | PASS |
| `grep -c "--font-size-" style.css` returns >= 6 (actual: 38) | PASS |
| `grep -c "--font-weight-" style.css` returns >= 4 (actual: 15) | PASS |
| `grep -c "--transition-" style.css` returns >= 3 (actual: 12) | PASS |
| `grep -c "--z-" style.css` returns >= 4 (actual: 8) | PASS |
| `grep -c "--radius-sm" style.css` returns >= 1 (actual: 3) | PASS |
| `grep -c "--radius-pill" style.css` returns >= 1 (actual: 2) | PASS |
| `grep -c "--bg-primary" style.css` returns >= 1 (actual: 2) | PASS |
| `grep -c "!important" style.css` returns 0 | PASS |
| `grep -c "@keyframes fadeInUp" style.css` returns 1 | PASS |
| `grep -c "@keyframes fadeOut" style.css` returns 1 | PASS |
| `url('/static/fonts/inter-regular.woff2')` server-root-relative URL present | PASS |

## New File Structure

The rewritten style.css follows this structure:

```
Line 1:   @layer reset, tokens, base, layout, components, utilities;
          @layer reset { * { box-sizing... } }
          @layer tokens { @font-face x4, :root { 42 tokens } }
          @layer base { body { } }
          @layer layout { .header, .progress-*, .target-*, .main, .summary-row, @media }
          @layer components { .search-panel, .form-*, .btn*, .tag-*, .result-*, .profiles-*, .graph-*, .export-*, .notes-area, .raw-json, .live-hit, .summary-card }
          @layer utilities { state modifiers: .active, .open, :hover, .fast, .slow, .found, .checking, .fullscreen, color variants }
(end):    @keyframes fadeInUp, @keyframes fadeOut (unlayered)
```

## Token Expansion Summary

| Category | Before | After |
|----------|--------|-------|
| Colors | 16 | 16 (unchanged, verbatim) |
| Radii | 2 (--radius, --radius-lg) | 4 (+--radius-sm, +--radius-pill) |
| Spacing | 0 | 8 (--space-1 through --space-8) |
| Font sizes | 0 | 8 (--font-size-xs through --font-size-3xl) |
| Font weights | 0 | 4 (--font-weight-normal/medium/semibold/bold) |
| Transitions | 0 | 3 (--transition-fast/base/slow) |
| Z-index | 0 | 4 (--z-header/graph-controls/graph-fullscreen/toast) |
| **Total** | **18** | **47** |

## Hardcoded Values Intentionally Left As-Is

Per plan rules 5 and 6, these values have no clean token match and are single-use:
- `.tag-chip`: `border-radius: 12px` (single-use, unique shape)
- `.tag-card .tag-count`: `font-size: 20px` (between --font-size-lg:14px and --font-size-xl:18px)
- `.export-card .format`: `font-size: 24px` (between --font-size-2xl:22px and --font-size-3xl:28px)
- `.star-btn`: `font-size: 16px` (between --font-size-lg:14px and --font-size-xl:18px)
- `.form-input`, `.btn`, `.result-tab`: `padding: 10px ...` (10px has no token)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — this plan is a pure CSS restructuring. No data rendering, no UI state, no placeholder content introduced.

## Threat Model Coverage

| Threat ID | Status | Notes |
|-----------|--------|-------|
| T-02-03 (Migration correctness) | MITIGATED | Full migration (zero unlayered rules except @keyframes); all 14 automated grep gates passed; visual checkpoint pending |
| T-02-04 (Missing font files) | ACCEPTED | Font files from Plan 01 exist; @font-face uses font-display:swap for graceful fallback |

## Threat Flags

No new threat surface introduced. This plan restructures existing CSS rules only — no new endpoints, no auth paths, no file access patterns, no schema changes.

## Self-Check: PASSED

- web-enhanced/static/style.css: FOUND (592 lines, @layer structure verified)
- Commit b58732a (Task 1): FOUND
- All 14 acceptance criteria: PASSED
