---
id: 32
status: todo
priority: Normal
blocked_by: []
tags: [tier-b, loop, sourcing]
---

# Find the cause of the recorded pre-AZ-5 flow drop (and the pump assumptions)

DREG has each half's pump flow falling −12/−14 % from 01:23:04 to AZ-5; the loop model gives ~−1 % for any
head curve. Imposing the record needs the leg loss ×1.82 (L) / ×1.94 (R) — a large unsourced resistance or
head loss — and still leaves the post-AZ-5 flow at −20 % against INSAG-7's ~−40 %. Related unsourced pump
inputs: the head-curve shut-off ratio hsh = 1.2 (ASSUMPTION) and the trip/coast-down times of pumps 3, 4
after AZ-5 (the DREG-fitted run-down is extrapolated).

**Sources:** PROGRESS (43), (44), (49); `test/loop_setup.jl` (infer_rundown), `src/Loop.jl` (pumps, leg).

## Acceptance Criteria
- A sourced mechanism (e.g. pump cavitation at reduced suction subcooling, head degradation, valve action) with its magnitude, or a documented negative search.
- Sourced values or brackets for hsh and the post-AZ-5 pump behaviour, entered as labelled assumptions.

## Narrative
- 2026-11-08: Opened from PROGRESS (43) and (49). (by @assistant)
