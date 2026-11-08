---
id: 39
status: backlog
priority: Normal
blocked_by: [35]
tags: [tier-b, fuel, chf]
---

# Cladding failure diagnostics: ballooning/burst and oxidation

With post-CHF the cladding reaches 946 °C (22 t of fuel above 700 °C) at fixed pressure. Whether it balloons
or bursts depends on the rod internal pressure (He fill + fission gas at ~10 MWd/kgU, unsourced) against the
coolant pressure the loop now gives, and on E110 burst criteria; above ~1000 °C the Zr–steam reaction adds
heat and embrittles the cladding.

**Sources:** PROGRESS (47), (49); `sources/derived/chf_postchf_correlations.md` Sec. 4.6.

## Acceptance Criteria
- Burst/ballooning and oxidation (ECR, heat) as per-step diagnostics in `fuel_diag.jl`, with sourced laws; oxidation heat coupled only if cladding reaches ~1000 °C.

## Narrative
- 2026-11-08: Opened; blocked on the E110 laws in card 35. (by @assistant)
