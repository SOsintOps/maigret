# Phase 2: CSS Architecture - Discussion Log

**Date:** 2026-05-08
**Participants:** User, Claude

## Areas Discussed

### 1. Font Self-Hosting Approach
**Options presented:** web-enhanced/static/fonts/ | web-enhanced/static/ | Claude decides
**User selected:** Claude decides
**Notes:** User trusts Claude to pick location and subsetting. Latin subset, weights 400/500/600/700.

### 2. Layer Ordering Strategy
**Options presented:** Full migration | Declare + wrap new only | Claude decides
**User selected:** Claude decides
**Notes:** User wants Claude to assess regression risk and choose migration scope. @layer declaration at top is required by CSSF-01 regardless.

### 3. Token Extraction from Mockup
**Options presented:** Spacing scale | Typography scale | Shadows and effects | Claude decides scope
**User selected:** All four (spacing, typography, shadows, plus Claude decides scope)
**Notes:** User wants comprehensive tokenization. Every mockup value should become a custom property where practical.

### 4. Migration Safety
**Options presented:** Manual browser check | Automated screenshot diff | Claude decides
**User selected:** Claude decides
**Notes:** Must respect vanilla JS / no build tools constraint. mockup.html is the visual reference.

## Deferred Ideas

None

## Claude's Discretion Items

- D-01: Font file location and subsetting strategy
- D-02: Layer migration scope (full vs partial)
- D-03: Token naming convention and extraction scope
- D-04: Verification approach for visual regression

---
*Discussion completed: 2026-05-08*
