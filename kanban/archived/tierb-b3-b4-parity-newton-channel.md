---
id: 20
status: done
priority: Normal
blocked_by: []
tags: [tier-b, th, numerics, neutronics]
---

# Tier B B3/B4: THM port, coupled band parity, and the B3b simultaneous Newton channel solver

THM was ported line by line into Julia (B3) and checked against DONJON THM on a steady state and a x128 power ramp. Coupled to the GPU RT0 kinetics, it passes all three B4 gates on all five band cases. The inherited THMTRS flow fixed point (and a marching replacement) failed after the peak in some cases. The B3b simultaneous Newton channel solver, with four of THM's closures smoothed, replaced it and ran band A to 6.91 s.

**Sources:** PROGRESS (39) (B3, B4 parts), (40), (41); key files: `tierb/RBMKCore.jl/src/Channel.jl` (`RBMKCore.Channel`), `src/Water.jl`, `src/Column.jl`, `Lines.col_step_loop` / `Lines.col_step_newton` / `col_step_newton_flux`, `tools/tierb_thmref.py`, `tools/tierb_bandcmp.py`, `test/b3b_lines.jl`, `test/b4_coupled.jl`, `sources/derived/b3b_loop_data.md`.

## Outcome
- B3 port (THMDRV/THMTRS with patches 0005, 0006, 0009-0015; THMH2O, THMPH, THMROD; freesteam from DONJON's tree) vs DONJON THM over 1661 x 28 bundles: **T-FUEL rms 0.0045 K, max 0.035 K** (inside ERMAXT 0.05 K). **D-COOL rms <= 1.6e-5 g/cm3**, max <= 2.6e-3 at the Saha-Zuber onset switch (REAL*4 vs Float64).
- B4 band B (GPU RT0 + THM port): 530 MW at **2.59 s in both**. Peak **182.75x at 5.33 s vs 181.66x at 5.32 s (+0.6 %)**. Energy to peak 24.83 vs 25.55 GJ (-2.8 %), and to 6.97 s 54.94 vs 55.29 GJ (-0.6 %). The feedback-limited peak is far less sensitive to the KINSOL bias than the frozen-TH runaway (0.6 % vs 6 %).
- (40) all five cases pass all three gates: 530 MW times identical in all five, peaks within 1.4 %, energy within 4.5 %.

| case | 530 MW | peak DONJON | peak Tier B | energy to DONJON's peak | reached |
|---|---|---|---|---|---|
| B | 2.59 / 2.59 s | 181.66x at 5.32 s | 182.75x at 5.33 s | -2.8 % | 6.97 s |
| A | 2.59 / 2.59 s | 78.29x at 5.28 s | 79.18x at 5.29 s | -1.4 % | 5.86 s |
| flow x0.85 | 2.60 / 2.60 s | 228.43x at 5.21 s | 228.22x at 5.23 s | -3.4 % | 6.64 s |
| tilt top | 3.10 / 3.10 s | 8.09x at 5.93 s | 8.17x at 6.04 s | -0.1 % | 7.00 s |
| tilt bottom | 2.29 / 2.29 s | 417.65x at 4.42 s | 415.07x at 4.43 s | -4.5 % | 7.00 s |

- The energy is consistently a few % low, which is the sign of the KINSOL bias. Bottom tilt ends at 105.2 GJ vs DONJON's 106 GJ.
- THMTRS flow fixed-point failures: B at 6.98 s, A at 5.86 s, flow x0.85 at 6.64 s. The column march (`B4_TH=col`) failed earlier, in A at 4.80 s.
- Shooting the inlet flux to the drum pressure (`Lines.col_step_loop`) fails structurally near saturation: the gain is about 0.3 at 10 ms and 1.25 at 5 ms. Its 77 -> 89 kgf/cm2 "pressure spike" was an artefact.
- Simultaneous Newton (x = [Gin; (h, p, G) per cell; p_top], banded FD Jacobian, chord Newton, dense 86x86 LU per channel). It needed four non-smooth THM closures fixed on the Newton path only:
  - the local-conditions Saha-Zuber onset, a **modelling change** worth up to 2.4e-3 g/cm3 D-COOL and 0.09 K T-FUEL;
  - inner tolerances iterated to fixed points;
  - a bracketed wall root in place of the sticky KWA = 0 iteration;
  - `prop_pT` never evaluated at exactly T_sat.
- Single channel (geometry and pressures are placeholders, `sourced=false`): valve closure 9.6 kgf/cm2 across a 1.40 cm2 throat, inside [D] Table 3.1. The null transient is exact over 1 s. Under power x20, dt = 10/5/2.5 ms agree to 1 kg/m2/s in Gin. Heating throttles Gin 2587 -> 2498 kg/m2/s.
- Band A with Newton (`B4_TH=newton`): 530 MW at 2.59 s, peak **75.97x at 5.31 s vs 78.29x at 5.28 s (-3.0 %)**, energy -5.0 %, gates pass. It **runs to 6.91 s** and tracks DONJON after the peak (23.10x vs 23.17x at 6.85 s). It stopped at 6.91 s on a probable fifth non-smooth closure (KWA = 3 post-dryout branch).

## Narrative
- 2026-10-18: (39) The THM port was verified against DONJON THM on a frozen power shape: steady state, then 35 steps of 0.01 s with power doubling every 5. In B4 band B the TH added no discrepancy of its own (812 K vs 819 K fuel at 4.5 s), and all three B4 gates passed. The run stopped at 6.98 s when one channel's THMTRS flow iteration failed the CYCLE-OK 0.1 cap in 60 iterations. That made the fixed-point flow solver the fragile part of the inherited TH. (by @assistant)
- 2026-10-18: (40) All five band cases were rerun coupled and compared with `tools/tierb_bandcmp.py`. Every case passed every gate. A and flow x0.85 stopped after their peaks in THMTRS. The B3b column march, tried as a replacement, failed earlier ("reversed-flow sweeps did not converge"), so marching doesn't survive post-peak flow reversals. (by @assistant)
- 2026-10-18: (41) Three solvers were built on the finite-volume column: the march, shooting, and simultaneous Newton. Shooting was rejected after showing its loop gain grows with smaller dt. Newton needed THM's closures to be smooth, and four non-smooth places were found by scanning the residual along failed Newton directions. The local-onset change is a modelling change and explains the extra -3 % vs the THMTRS port from 4 s. Newton ran band A past both THMTRS's and DONJON's own end points. It costs about 6 s per core step for the TH, and B6 will need an analytic/AD Jacobian. Core-wide loop boundary conditions were left waiting on sourcing (gaps 1, 2, 5, 6). (by @assistant)
