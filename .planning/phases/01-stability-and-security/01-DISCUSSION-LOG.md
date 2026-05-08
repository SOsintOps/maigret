# Phase 1: Stability and Security - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 1-Stability and Security
**Areas discussed:** Stabilita (disconnect, job cleanup)

---

## Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Disconnect e cancellazione scan | Cosa succede al task di scan quando client si disconnette da SSE | |
| Sanitizzazione URL profili | Scope e posizione della sanitizzazione XSS | |
| Migrazione SSE nativa | Rimuovere sse-starlette e/o adottare EventSourceResponse | |

**User's choice:** Solo stabilita — sicurezza e pulizia tecnica delegate a Claude
**Notes:** User ha chiarito che il tool gira in locale (127.0.0.1), single-user. Threat model basso.

---

## Disconnect e Lifecycle Scan

| Option | Description | Selected |
|--------|-------------|----------|
| Cancella scan | Client disconnette, scan si ferma. Risparmia risorse. | |
| Scan continua | Scan finisce in background, risultati recuperabili. | |
| Tu decidi | Claude sceglie l'approccio piu sensato per tool locale. | ✓ |

**User's choice:** Tu decidi
**Notes:** Claude ha scelto "scan continua" — un refresh non deve uccidere una scan di 10 minuti.

---

## Job Cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Cleanup dopo 1 ora | Job completati rimossi dopo 1h. | |
| Nessun cleanup | Job restano fino a restart server. | ✓ |
| Tu decidi | Claude sceglie. | |

**User's choice:** Nessun cleanup
**Notes:** Accettabile per uso locale. Gia segnalato come concern post-milestone.

---

## Claude's Discretion

- XSS sanitization approach (scope and location)
- SSE migration strategy (EventSourceResponse vs StreamingResponse with disconnect detection)
- asyncio task GC fix implementation
- Temp file cleanup implementation

## Deferred Ideas

None — discussion stayed within phase scope
