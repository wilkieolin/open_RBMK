---
id: 21
status: done
priority: Normal
blocked_by: []
tags: [tier-b, loop, th, sourcing, numerics]
---

# The 01:23 drum pressure, the core-wide loop model, and the loop's effect decomposed

The DREG/SKALA record showed that the decks' 75.3 kgf/cm2 was a post-excursion pressure. Rerunning band B at the recorded 66.8 kgf/cm2 raises the peak by +34 %, which retracts (33). A core-wide two-half loop model (B3b-3) was then built and run through AZ-5. Its numbers in (43) were **RETRACTED in (44)** because of two energy errors. With the model corrected, (44) shows that the loop lowers the peak from 230x to 84.7x, mostly through the starting state and per-channel hydraulics, and that the steam volume barely matters.

**Sources:** PROGRESS (42), (43), (44); key files: `tierb/RBMKCore.jl/src/Loop.jl` (`Loop.leg_state`, `Loop.FAILDUMP`, `valve_area`), `test/loop_setup.jl`, `test/b3b_loop_core.jl`, `test/b4_coupled.jl` (`B4_TH=loop`), `tools/graphite_heat.py`, `sources/accidont/`, `sources/derived/{dreg_0123_mfcc.csv,mochizuki2007_loop.csv,ignalina_zrk_valve.csv,b3b_loop_data.md}`.

## Outcome
- Sources: the DREG SKALA record (Dmitriev, VNIIAES), [MOC07] quarter-loop with elevations, and [ALM98] (GD2 = 15 t*m2, drum ID 2.6 m, ZRK xi = 0.63-1.4).
- Pre-AZ-5 drums read 63.2-65.0 (L) and 64.1-68.6 (R) kgf/cm2. The decks' 75.3 kgf/cm2 is INSAG-7's +8 s left-drum reading.
- Band B at 66.8 kgf/cm2 (`U4_POUT=66.8`, deck `...acco668...`), THMTRS port: peak **245.4x at 5.22 s vs 182.8x (+34 %)**, energy at 6.9 s 65.3 vs 54.4 GJ (+20 %), T-FUEL max 1998 vs 1889 K. With the Newton column: 173.1x -> 230.2x (+33 %). **Retracts (33)**'s "pressure moves the surge by a few percent or reduces it".
- Subcooling: `Loop.leg_state` predicts pump-inlet water at 280.7 C vs DREG's 281 C, and **0 K subcooling against the drum pressure** (about 2.9 K against the core bottom). INSAG-7's "3 C" is then a core-bottom figure, and the decks give too much subcooling.
- (43), **numbers RETRACTED in (44)**: "drum pressures follow DREG unfitted" (+2.7 in 36 s vs +2.9 L / +4.2 R) and the loop AZ-5 peak of 110.4x at 5.78 s (38.5 GJ at 6.9 s).
- Still standing from (43): the recorded pre-AZ-5 flow drop (-12.3 % L / -13.5 % R) is not reproduced with any head curve (model -1-2 %, hsh 1.5 gives -2.8 %). The record implies circuit resistance rose about 25-30 %, or the grid pumps slowed, or the flowmeters read low. This is carried to B5 as an ambiguous conditioning datum, not a parameter to tune. The solver changes also stand (0 last-resort acceptances in 700 steps).
- The (44) errors: graphite heat entered at 1/28 (about 1.2 MW instead of 34), and feedwater subcooling (about 22 MW per half) was counted twice. Together they add about 38 MW per half.
- Steam volume: (43)'s scaling by steam flow had no basis (both designs use 600 mm lines). The pre-AZ-5 mean rise (DREG 3.55) gives **V of about 150-450 m3**, excluding 0 and 900.
- Corrected AZ-5 (band B, hsh 1.2, Qg 34 MW): L0 full loop, V = 296: 530 MW at 2.77 s, **84.7x at 5.97 s**, 30.8 GJ at 6.9 s, 1575 K. D-B (loop boundaries frozen) 108.2x; D-C (drum frozen) 89.2x; V = 0 / 450 give 85.5x / 84.4x.
- Decomposition of ln(230/84.7): starting state + channel hydraulics **76 %**, header/pump/flow 19 %, drum pressure 5 % (76 % split further in card 22, (46)).
- Steam volume 0 -> 450 m3 moves the peak by 1 % and the energy by 1.6 %. Even at V = 0 the +6 s rise is +0.9 kgf/cm2/s vs the recorded +5.3 (L), and the core flow falls 10 % vs about 40 %. The drum's model form joins the B5 list.

## Narrative
- 2026-10-19: (42) The DREG record, [MOC07] and [ALM98] were found. The decks' pressure turned out to be the post-excursion reading. Band B was rerun at 66.8 kgf/cm2 (the mean of the last two pre-AZ-5 readings, read as absolute) with both TH solvers, and the peak rose about +33-34 % either way. The first 3 s moved by <= 3 %. The loop scaffold also suggested the subcooling sits at the wrong end of the core, which a single-pressure THM cannot represent. (by @assistant)
- 2026-10-20: (43) The two-half loop was built: lumped saturated drums, four MCPs per half on one pressure rise, a lumped leg, and every channel as a Newton column with its own lines and ZRK throat. Inputs were each sourced or labelled as ASSUMPTION (loop split L 826 / R 835 channels, hsh 1.2, steam volume 296 m3). Pump run-down speed was inferred from DREG per-pump flows. The recorded flow drop was not reproduced, and the post-AZ-5 pressure rise was 5-6x too slow. Four more Newton-path fixes were needed to get through the excursion. The run costs about 4 h for 7 s. (by @assistant)
- 2026-10-21: (44) A steam-volume grid exposed that graphite heat barely moved the drum pressure, and an audit found the two energy errors. The numbers in (43) were retracted. With the model corrected, the record bounds V to about 150-450 m3. The AZ-5 decomposition attributes 76 % of the peak reduction to the starting state and channel hydraulics. Steam volume drops off the first-order excursion uncertainties. (44) guessed the channel hydraulics could only raise the peak; (46) corrected that. (by @assistant)
