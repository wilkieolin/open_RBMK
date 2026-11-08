---
id: 30
status: todo
priority: Normal
blocked_by: []
tags: [tier-b, numerics, th]
---

# Give the fixed-pressure Newton channel path the loop path's failure fallback

`B4_TH=newton` (`col_step_newton_flux`) has no retry when a channel step fails; `Loop.loop_step!` retries
without the chord cache and then accepts the best iterate below `LOOSE` (counted). The tilted fixed-pressure
run stopped at 5.56 s on an iterate at h = −1.1e7 J/kg (THMPH convergence failure) after its peak.

**Sources:** PROGRESS (49); `tierb/RBMKCore.jl/src/Loop.jl` (loop_step!), `src/Column.jl`, `test/b4_coupled.jl`.

## Acceptance Criteria
- The newton path in `b4_coupled.jl` retries a failed channel step as the loop path does (no cache, then loose, counted and reported per step).
- With no failure, results byte-identical to before (B4 newton 30-step trace check).
- The tilted case (`…_bpl2p8_0p4`, `B4_CLAMP=1`) rerun to 7 s.

## Narrative
- 2026-11-08: Opened from PROGRESS (49) "Next (2)". (by @assistant)
