---
phase: 2
slug: css-architecture
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-08
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Shell commands (grep, ls, head) — no test framework needed for CSS-only phase |
| **Config file** | none |
| **Quick run command** | `head -1 web-enhanced/static/style.css` |
| **Full suite command** | See per-task automated commands below |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `head -1 web-enhanced/static/style.css` to verify layer ordering
- **After every plan wave:** Run all automated commands from the Per-Task Verification Map
- **Before `/gsd-verify-work`:** Full suite must be green + visual parity confirmed
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CSSF-02 | T-02-01 | Font files from official rsms/inter repo, size > 10KB | unit | `ls -la web-enhanced/static/fonts/inter-*.woff2 && test $(stat -f%z web-enhanced/static/fonts/inter-regular.woff2) -gt 10000 && echo PASS` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | CSSF-02 | T-02-02 | No Google Fonts CDN requests (IP leakage eliminated) | unit | `test $(grep -c 'fonts.googleapis.com' web-enhanced/static/index.html) -eq 0 && test $(grep -c 'fonts.googleapis.com' web-enhanced/static/mockup.html) -eq 0 && echo PASS` | ✅ | ⬜ pending |
| 02-02-01 | 02 | 2 | CSSF-01, CSSF-02, CSSF-03 | T-02-03 | Full migration prevents specificity overrides; no !important | unit | `head -1 web-enhanced/static/style.css \| grep -q "@layer reset, tokens, base, layout, components, utilities;" && grep -c "@font-face" web-enhanced/static/style.css \| grep -q "4" && test $(grep -c "\\-\\-space-" web-enhanced/static/style.css) -ge 6 && test $(grep -c "\\-\\-font-size-" web-enhanced/static/style.css) -ge 6 && test $(grep -c "!important" web-enhanced/static/style.css) -eq 0 && echo PASS` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Font download URLs validated (rsms/inter official repo)
- [x] Screenshot baseline — take browser screenshot of mockup.html before any CSS change (Plan 02-02 Task 2 checkpoint)
- [x] No framework install needed — shell commands only

*Wave 0 pre-conditions are handled by Plan 02-01 (font downloads) and the visual checkpoint in Plan 02-02 Task 2.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual parity after migration | CSSF-01, CSSF-03 | CSS visual regression cannot be verified by grep alone | Open mockup.html in browser, compare appearance before/after. Check hover states, transitions, font rendering. |
| Font loading from local files | CSSF-02 | Network panel inspection required | Open DevTools Network tab, reload mockup.html, verify no requests to fonts.googleapis.com, verify Inter loads from /static/fonts/*.woff2 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 2s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved
