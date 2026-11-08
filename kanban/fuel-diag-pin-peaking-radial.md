---
id: 34
status: todo
priority: Normal
blocked_by: []
tags: [tier-b, fuel]
---

# Fuel diagnostics on the quantity the failure criteria are defined on

`test/fuel_diag.jl` reports a bundle-average, pellet-averaged enthalpy; the criteria (120–325 cal/g,
PROGRESS (47)) are peak radial-average enthalpy of the hottest rod. The OpenMC rod-to-rod peaking
(1.02–1.05, PROGRESS (37)) and the pellet radial profile in a fast pulse are not applied.

**Sources:** PROGRESS (37), (47); `test/fuel_diag.jl`, `openmc/pin_peaking.json`.

## Acceptance Criteria
- Hottest-rod enthalpy (pin peaking applied, by burnup and density) reported alongside the bundle average.
- Statement of how the radial profile is treated (the rod mesh already resolves it; the reported quantity is the radial average).

## Narrative
- 2026-11-08: Opened from PROGRESS (47)/(48). (by @assistant)
