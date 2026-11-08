---
id: 29
status: todo
priority: High
blocked_by: []
tags: [tier-b, loop, fuel, th]
---

# Close (or explain) the post-AZ-5 drum-pressure and core-flow gap

After AZ-5 the record has the drums rising far faster than any model case and the core flow falling ~40 %
(INSAG-7); the loop model gives a drum rise 2.5–3× too slow from +5 to +6 s, the right drum ~7 kgf/cm² low at
+7 s, and a flow drop of 10–20 %. The energy bound (PROGRESS (46)) says the record needs ~30–40 % of the
released energy in the water within a second — dispersed fuel (~8–19 t UO₂) — while no model case reaches
fragmentation (hottest bundle 105–158 cal/g against 240–270). Every sourced starting-state corner, the drum
model, the steam volume and post-CHF have been tried (PROGRESS (44)–(49)); the remaining levers are the radial
start (cards 27, 28), local energy concentration and the dispersal heat transfer itself.

**Sources:** PROGRESS (43)–(49); `sources/derived/dreg_mfcc_full.csv`; `test/drum_energy_bound.jl`.

## Acceptance Criteria
- A model case, or a sourced bracket of cases, whose +5…+8 s drum pressures and core flow are compared with DREG/INSAG-7 per half, with the energy reaching the water accounted for; or
- a documented conclusion that the model class cannot reproduce them without a fuel-dispersal model (card 40), with the evidence.

## Narrative
- 2026-11-08: Opened as the umbrella for the post-AZ-5 mismatch carried since PROGRESS (43). (by @assistant)
