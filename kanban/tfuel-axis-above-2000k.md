---
id: 31
status: todo
priority: Normal
blocked_by: []
tags: [tier-b, neutronics, numerics]
---

# T-FUEL above 2000 K: extend the COMPO axis or adopt CLAMP as the reading

The fuel COMPO's T-FUEL axis ends at 2000 K. The fixed-pressure post-CHF case (6.0 s) and the tilted case
(5.30 s) stopped there; `B4_CLAMP=1` holds the parameter at the axis end, which freezes Doppler above 2000 K
and makes the power after that an upper estimate. Cases that concentrate more energy will all reach it.

**Sources:** PROGRESS (36) (patch 0014 CLAMP), (49); `tierb/RBMKCore.jl/src/XS.jl`, `test/b4_coupled.jl`.

## Acceptance Criteria
- Either: a COMPO rebuild with T-FUEL branch points above 2000 K (memory/time estimated first), exported and gated as B0 was; or a measured bound on what CLAMP changes (e.g. Doppler extrapolation sensitivity) so CLAMP results can be quoted with an error.
- Decision recorded here.

## Narrative
- 2026-11-08: Opened from PROGRESS (49) "Next (2)". (by @assistant)
- 2026-11-09: The #44 Fig. 11 deck (newton, no CHF) hits the axis at **6.00 s** (2000.3 K): its excursion is 6 % larger than the old deck's. Every band-B run on the re-typed deck now needs this card or `B4_CLAMP=1` to reach 7 s. (by @assistant)
