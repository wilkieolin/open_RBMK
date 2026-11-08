---
id: 22
status: done
priority: Normal
blocked_by: []
tags: [tier-b, loop, th, fuel]
---

# Non-equilibrium two-region drum, the energy the drum record needs, and the four-way loop decomposition

A two-region (vapour/liquid) drum, `Loop.Drum2`, replaced the equilibrium drum. Conditioned on the pre-AZ-5 record alone, it multiplies the post-AZ-5 pressure rise by 1.7-3 but leaves the peak at 80-96x. An energy bound then showed that the recorded drum rise needs 30-40 % of the core's release to reach the drums within a second, which points to fragmented fuel. The 76 % term from (44) was also split: starting state 46 %, channel hydraulics 29 %.

**Sources:** PROGRESS (45), (46); key files: `tierb/RBMKCore.jl/src/Loop.jl` (`Loop.Drum2`, `DRUM_TAU`, `freeze=:chan`, `col_step_newton_frozen`), `test/drum_energy_bound.jl`.

## Outcome
- Drum2: dH - V dp = sum h dm per region, condensation Gamma = M_l c_p (T_sat - T_l)/(h_fg tau), immediate flashing, conservation to 1e-11. tau -> 0 tracks the equilibrium drum (4 % over 10 s). **tau is an ASSUMPTION** (no RBMK value found).
- 1 s 2000 MW pulse: +1.7 (equilibrium), +3.2 (tau 1 s), +6.6 (10 s), +7.6 kgf/cm2 (frozen liquid).
- Pre-AZ-5 conditioning (DREG mean rise 3.55): frozen liquid excluded. The ridge runs (tau 1 s, V about 150), (tau 3-4 s, V about 296), (tau 10 s, V >= 450), and the record can't separate tau from V.
- AZ-5 along the ridge: tau 1 s / V 150: 96.3x at 5.80 s; tau 3 s / V 296: **80.0x at 5.90 s**, 30.7 GJ at 6.9 s; tau 10 s / V 450: 88.5x at 5.81 s (equilibrium 84.7x).
- Post-AZ-5 rise x1.7-3. L at +7 s is 72.7-74.2 vs the record's 75.2 at +8 s. The +5 -> +6 s rise (+5.3 recorded) is still 2.5-3x faster than any case, and R (80.1 at +7 s, 88.4 at +8 s) is out of reach. Core flow at +7 s is -8.1 to -9.8 % vs about -40 %.
- B5: Drum2 with (tau, V) on the ridge as one input. Its effect on the peak is +-10 %, below the starting state's.
- Energy bound (from saturated regions, a lower bound), per half:
  - L, +5 -> +6 s: the record needs 2.0-2.8 GW (model 0.7-0.9 GW, extra 1.2-1.9 GW).
  - R, +7 -> +8 s: the record needs 3.0-3.9 GW (model 1.0-1.3 GW).
- The core releases 12.8-15.9 GJ between +5 and +6 s, of which about 11-13 % reaches the drums vs the 30-40 % needed. That points to prompt fuel-to-coolant transfer from fragmented fuel: the extra 2.5-5.7 GJ is about 8-19 t of UO2 (about 35-80 channels). No fuel nears 920 kJ/kg by +6 s, so the record also needs more deposited energy. Channel ruptures cannot make the rise.
- Four-way split of ln(230/84.7): **46 % starting state** (D-A, flows and pressure fields frozen: 144.9x at 5.62 s, 43.5 GJ), **29 % channel hydraulics** (D-B 108.2x), 19 % header/pumps/flow (D-C 89.2x), 5 % drum (L0 84.7x).
- **Correction to (44):** channel hydraulics lower the peak (by 29 %) rather than raise it. The reading is negative void feedback through the local pressure, low in the core. That mechanism is a reading, not yet shown cell by cell.

## Narrative
- 2026-10-21: (45) (44) had pointed at the equilibrium drum, which shares every joule with about 170 t of saturated liquid before the pressure moves. That is the wrong limit for a 1-2 s excursion. The two-region drum was built, and (tau, V) were conditioned only on the pre-AZ-5 rise, keeping the post-AZ-5 record as an independent check. The drum is judged the right model form, but the peak doesn't move with it: the fast rise starts as the power peaks, too late to collapse void. What the model misses after AZ-5 is in the core. (by @assistant)
- 2026-10-22: (46) The drum's own energy demand was bounded. The record asks for several times more energy reaching the water than any loop case delivers, which suggests fragmented fuel plus more deposited energy. D-A (`freeze=:chan`) split the 76 % term and corrected (44)'s sign guess for channel hydraulics. Every loop effect lowers the peak, while the record needs more energy, faster. Only fragmentation with prompt fuel-coolant heat transfer, or a starting state with less steam, reconciles them. (by @assistant)
