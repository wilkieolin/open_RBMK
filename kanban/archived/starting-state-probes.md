---
id: 26
status: done
priority: Normal
blocked_by: []
tags: [tier-b, loop, th, infra]
---

# Starting-state probes in the loop: recorded flow, Psd as gauge, Qg 26 MW

This is step (3) of the plan from (47)/(48): the sourced starting-state corners, run through AZ-5 in the loop (tau 3 s, V 296 m3). The corners are the recorded pre-AZ-5 flow, the DREG drum pressure read as gauge, and the low end of the graphite heat. Together they move the peak by -3 to +7 % and the hottest bundle by +-3 cal/g. None approaches fragmentation or closes the post-AZ-5 drum and flow gaps. The runs were made on a shared, memory-contended machine and resumed from checkpoints.

**Sources:** PROGRESS (49) (starting-state probe, running conditions); key files: `tools/graphite_heat.py`, `test/b4_coupled.jl` (`LOOP_WREC=1`, `LOOP_PSD_GAUGE=1`, `B4_CKPT_FILE`), `tierb/RBMKCore.jl/src/Loop.jl`.

## Outcome
- *Recorded flow imposed* (`LOOP_WREC=1`):
  - The recorded -12/-14 % needs the leg loss x1.82 (L) / x1.94 (R), a large unsourced resistance or head loss.
  - At AZ-5: W 5271/5198 kg/s vs 5919/5951, minimum D-COOL 0.639 vs 0.654, drum pressures unchanged.
  - The excursion rises more slowly (3.4x at 3 s vs 4.0; 32.5x at 5 s vs 38.8) and peaks **85.4x at 6.02 s** (base 80.0x at 5.90 s).
  - Core flow at 7 s is 4856/4809 kg/s, 20 % below 01:23:04 (INSAG-7: about 40 %). Drums 72.6/73.3 vs DREG 74.0/80.1.
  - Imposing the recorded pre-AZ-5 flow does not close the post-AZ-5 gaps.
- *Psd as gauge* (`LOOP_PSD_GAUGE=1`, +1.033 kgf/cm2): the pre-run sits 1 kgf/cm2 higher (subcooling +1 K). Peak **77.7x at 5.91 s** (-3 %). The gap to the shifted record is unchanged (74.6 vs 81.1 at 7 s, R).
- *Qg 26 MW* (vs 34): peak **85.1x at 5.86 s** (+6 %), 33.0 GJ, 109.3 cal/g; drums as base.

| starting state | peak | E at 7 s | hottest bundle 7 s | R drum 7 s (DREG) | core flow 7 s vs 01:23:04 |
|---|---|---|---|---|---|
| base | 80.0x at 5.90 s | 31.4 GJ | 106.2 cal/g | 73.6 (80.1) | -10 % |
| Psd as gauge | 77.7x at 5.91 s | 30.7 GJ | 104.8 | 74.6 (81.1) | -10 % |
| Qg 26 MW | 85.1x at 5.86 s | 33.0 GJ | 109.3 | 73.7 (80.1) | -10 % |
| recorded flow imposed | 85.4x at 6.02 s | 31.0 GJ | 106.2 | 73.3 (80.1) | -20 % |

- Of everything tried in (49), only the radial field (the "as printed" tilt, card 24) moves the local energy materially.
- Running conditions: another job held 35-66 GB of GPU memory all night. A memory guard (kill the newest run if MemAvailable < 12 GB, later < 8 GB) stopped runs three times. Loop runs resumed from their 50-step checkpoints (`B4_CKPT_FILE`); fixed-pressure runs were restarted.

## Narrative
- 2026-10-24: (49) The starting state was the dominant term of (46), so its three sourced corners were probed in the loop. Forcing the recorded pre-AZ-5 flow drop needs an unsourced leg loss of about 1.8-1.9x. It gives more void at AZ-5 but a slower rise, a peak only 7 % higher, and still half the recorded post-AZ-5 flow drop. The gauge reading of Psd and the low graphite heat each move the peak by a few %. The conclusion: within its sourced ranges, the starting state doesn't explain the fragmentation or drum-record gaps, and the remaining open lever is the orientation of Fig. II-7. Runs were interrupted by a memory guard on a shared machine and resumed from checkpoints. (by @assistant)
