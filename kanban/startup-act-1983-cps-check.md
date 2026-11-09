---
id: 46
status: backlog
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, rods, sourcing]
---

# Check the CPS model against Unit 4's 1983 physical start-up (act No. 92/IV)

Unit 4's physical start-up act (No. 92/IV, 18.12.1983, reproduced in Dyatlov, *Чернобыль. Как это было*,
`sources/ChNPP.pdf` pp. 80–84, [DYAT]) gives plant measurements of the rod and channel worths. The model
checks those worths only against OpenMC (gap 2, PROGRESS (35)), so the act is the one independent measured
check. The measurements are:
- АЗ worth 2.5 β;
- CPS-circuit voiding effect +0.1 β;
- a **positive** reactivity spike when the 2АР rods are inserted 0–2 m from the upper limit switch (§2.8). The
  same is seen, smaller, for single РР and АЗ rods, but not for groups of 15–18 РР;
- reactivity margin of the initial load ~40 rods (§2.9).

The core then was the 1983 initial load: 1386 ТВС, 234 ДП (additional absorbers) and 41 water columns (§3.1),
with fresh fuel. In that core the АР rods still had displacers; §3.4 recommends moving them to the channel
bottoms, as on Unit 3. So this is a different core from 1986. It tests the CPS **channel models** (absorber,
displacer, water column worths, and the positive-scram geometry), not the 1986 state.

Found 2026-11-08/09 while sourcing #44.

**Sources:** [DYAT] pp. 80–84; INSAG-7 §2 for the initial load enrichment; [D] for the ДП design.

## Acceptance Criteria
- Sourced or bracketed:
  - the initial-load layout (ДП and water-column positions; if unsourced, an ASSUMPTION and bracketed over
    plausible layouts);
  - the ДП construction;
  - the fresh-fuel enrichment;
  - the 1983 rod types and lengths (6 m absorber, 3 m УСП per the act).
- A ДП lattice COMPO (DRAGON) if none exists.
- Computed and compared with the act:
  - АЗ worth;
  - CPS voiding effect;
  - the sign and size of the 2АР 0–2 m spike;
  - the group-РР no-spike result.
- A disagreement goes to #44 / gap 2 as a statement about the CPS model, with brackets. It is not tuned away.

## Narrative
- 2026-11-09: Opened from #44's sourcing. The act is the only plant measurement of CPS worths in hand; the core differs from 1986, so this is a model check, not a state input. (by @assistant)
