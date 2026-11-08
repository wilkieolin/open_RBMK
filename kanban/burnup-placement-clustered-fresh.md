---
id: 36
status: backlog
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, burnup, uq]
---

# Burnup placement: clustered fresh fuel and Ref. [28]'s radial power peaking 2.0

INSAG-7 quotes Ref. [28]'s radial power peaking 2.0 at the initial state, while Fig. II-7's flux peaks at
1.54 and the model at 1.60. Channel-scale heterogeneity within [PAV]'s 1.2–13.7 MWd/kgU reaches only 1.69
(chk25); [PAV]'s histogram alternated (chess) gives 3.47. Power peaking 2.0 with Fig. II-7's flux needs fresh
assemblies clustered in the high-flux region — the placement problem PROGRESS (13)/(21) found undecidable from
the sources (placement worth up to +10 860 pcm). Enters B5 as an uncertain input.

**Sources:** PROGRESS (13), (21), (49); generator `U4_BURNMAP`.

## Acceptance Criteria
- A parametrised placement family consistent with [PAV]'s histogram, Fig. II-7 and the 01:22:30 rod pattern, usable as a B5 input with its range.

## Narrative
- 2026-11-08: Opened from PROGRESS (49). (by @assistant)
