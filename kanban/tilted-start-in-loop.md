---
id: 27
status: todo
priority: High
blocked_by: []
tags: [tier-b, loop, neutronics]
---

# Run the Fig. II-7 "as printed" starting state through the loop model

The planar burnup tilt fitted to INSAG-7 Fig. II-7 as printed (`U4_BURNMAP=pl2p8_0p4`, re-valved deck
`…pc193dcb…_bpl2p8_0p4`) puts 62 % of the t = 0 power in the right half (left share 0.381). At fixed pressure
it gives Kv ~5 at 7–37× (Ref. [28]: 5.5 at ~30×) and a 254× peak at 4.91 s. Whether the right drum then
rises faster than the left after AZ-5, as DREG records (R 80.1 against L 74.0 kgf/cm² at +7 s), is a test
of the figure's orientation that the fixed-pressure model cannot make.

**Sources:** PROGRESS (49); `sources/derived/insag7_fig_II7_lattice.csv`, `sources/derived/a8_pchan_cB_pl2p8_0p4.txt`.

## Acceptance Criteria
- Loop run (τ 3 s, V 296 m³, Qg 34 MW) from the tilted deck's own pre-run to 7 s, with `B4_CLAMP=1` if T-FUEL passes 2000 K (an upper estimate after it).
- Left/right drum pressures and pump flows at +5…+7 s compared with DREG and with the base loop case.
- Peak, energy, hottest bundle, Kv against the base loop case; result recorded in this card's narrative.

## Narrative
- 2026-11-08: Opened from PROGRESS (49) "Next (1)". The rotated orientation already matches the model's untilted field (r 0.885), so this run is the other branch of the orientation question. (by @assistant)
