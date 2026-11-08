---
id: 25
status: done
priority: Normal
blocked_by: []
tags: [tier-b, chf, th, fuel, numerics]
---

# Boiling crisis and post-CHF heat transfer on the Newton path, in one channel and the core

A sourced CHF and post-CHF model, `ThmOpts.postchf`, was added to the Newton channel path. It needed two cladding fixes: continuous Zircaloy rho c_p segments, and enthalpy-difference heat storage (`zr_csec`). At fixed pressure the core dries out from the peak onward, and the cladding passes 700 C in 21.9 t of fuel, though none reaches 1200 C. The fuel enthalpy barely moves, so CHF cannot cause fragmentation. In the loop no channel reaches CHF. The +5-6 % change in the peak comes from the cladding heat-storage form, not from CHF.

**Sources:** PROGRESS (49) (boiling crisis / post-CHF parts); key files: `sources/derived/chf_postchf_correlations.md`, `ThmOpts.postchf`, `ThmOpts.zrsec`, `zr_csec`, `test/b4_coupled.jl` (`B4_CHF=1`, `B4_CLAMP`), `test/chf_single.jl` (the single-channel check).

## Outcome
- Model:
  - CHF = min([D] p. 70 in local form, 2006 LUT x K1 K2);
  - Bjornard-Griffith transition boiling between T_CHF and T_min, continuous at both ends (RELAP5's Chen form as printed jumps at CHF);
  - modified Bromley film boiling + vapour convection + radiation;
  - T_min Groeneveld-Stewart (411 C at 7 MPa);
  - wall-root hysteresis (the root nearest the step-start wall temperature).
- At 7 MPa, 3729 kg/m2s: CHF 3.4 MW/m2 at x = 0, 0.96 at x = 0.25. Film boiling carries 0.1-0.7 MW/m2, so the wall flux falls about 10x at the crisis.
- Numerical fixes (only under `postchf`):
  - THM's Zircaloy rho c_p segments are discontinuous at 1090 and 1243 K, now joined continuously.
  - THM's c(T1)T1 - c(T0)T0 storage has an effective capacity about 21x the true one in the alpha-beta spike, and overstates it by about 20 % even at 560 K. It is replaced by H(T1) - H(T0) (`zr_csec`; also alone as `ThmOpts.zrsec`).
- With `postchf` off, every result is unchanged (30-step B4 newton trace byte-identical).
- Single channel 604 (the base case's hottest, driven by its recorded bundle powers):

| | first dry node | cladding max at 6 / 7 s | fuel centre at 7 s |
|---|---|---|---|
| no CHF | - | 309 / 308 C | 2238 K |
| CHF x1 | 5.30 s | 713 / 893 C | 2238 K |
| CHF x2 | 5.63 s | 323 / 458 C (most nodes rewet by 7 s) | 2238 K |

- Core, fixed pressure (band B):
  - base (48): 230.2x at 5.24 s, 63.5 GJ, 155.7 cal/g, 430 C;
  - `zrsec` only: 242.7x at 5.21 s, 65.3 GJ, 157.9 cal/g, 432 C;
  - `postchf` (+ `B4_CLAMP` after 6.0 s): 242.7x at 5.21 s, 61.3 GJ, 156.4 cal/g, **946 C**, **21.9 t** above 700 C, 7617 dry nodes (37 t) at 6 s.
- The +5 % peak is the heat-storage form: `zrsec` alone gives the same peak to the digit, because heat leaves the cladding about 20 % faster.
- Dryout starts at the peak (49 nodes at 5.25 s) and spreads to 37 t of fuel by 5.75 s. It lowers post-peak power (-6 % energy at 7 s). Fuel enthalpy moves -1.5 cal/g.
- The CHF x2 result (458 C) shows the cladding outcome is set by the unsourced transient-CHF enhancement.
- Loop (tau 3 s, V 296, `B4_CHF=1`, resumed from step 450): **no channel reaches CHF**. Peak 85.0x at 5.88 s (base 80.0x, +6 %), 32.6 GJ at 7 s (31.4), hottest bundle 108.7 cal/g (106.2), cladding max 402 C, drums at 7 s 73.2/73.9 (72.9/73.6) kgf/cm2.

## Narrative
- 2026-10-24: (49) This implemented step (2) of (48)'s plan, using the sourced set. Two smoothness requirements of the Newton solver drove choices: the transition-boiling form had to be continuous at both ends, and the cladding heat storage had to be fixed because its fixed point couldn't converge through the alpha-beta spike. That fix turned out to raise the peak by itself. At fixed pressure CHF gives physical cladding temperatures (21.9 t of fuel above 700 C, none above 1200 C) but leaves the fuel adiabatic, confirming (48) that CHF cannot cause fragmentation. In the loop, at 80-85x and higher pressures, nothing reaches CHF. (by @assistant)
