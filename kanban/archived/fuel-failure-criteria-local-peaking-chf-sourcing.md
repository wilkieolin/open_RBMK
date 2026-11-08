---
id: 23
status: done
priority: Normal
blocked_by: []
tags: [tier-b, fuel, chf, sourcing, neutronics]
---

# Fuel failure criteria sourced; local peaking against INSAG-7's Kv; CHF/post-CHF sourced

INSAG-7's 920 kJ/kg (220 cal/g) is a disintegration threshold, not the onset of failure. Sourced criteria show that no model case fragments or disperses fuel. Shape diagnostics then showed that the excursion concentrates axially as INSAG-7 describes but is about 1.4-1.6x too flat radially, while the fuel stays nearly adiabatic, so no heat-transfer model can close the gap. The CHF and post-CHF correlations needed for physical cladding temperatures were sourced.

**Sources:** PROGRESS (47), (48); key files: `sources/derived/fuel_failure_criteria.md`, `sources/derived/chf_postchf_correlations.md`, `sources/README.md`, `test/fuel_diag.jl`, `test/shape_diag.jl`, `test/b4_coupled.jl` (`b4_shape_*.txt`, `b4_pw_*.bin`).

## Outcome
- INSAG-7 p. 67: disintegration at 220 cal/g, rupture at 285, explosion at 320 (NSRR fresh fuel). With THM's UO2 c_p, 220 cal/g is about 2800 K pellet average, not 3300 K. The log had called it "fuel failure" since (24).
- Sourced thresholds ([HOZ], [NEA10]), in peak radial-average enthalpy:
  - about 120 cal/g: PCMI dispersal, a lower bound only for Unit 4;
  - about 160: Zr-1%Nb ballooning;
  - 193-195: failure correlations at 10 MWd/kgU;
  - 240-270: fragmentation;
  - 285-325: molten fuel expelled.
- Cladding limits: 1200 C / 18 % oxidation, 700 C operational. The drum record needs dispersed fuel (240-325 cal/g).
- Model (band B `...acco668...`): fixed pressure 230.2x, hottest bundle 156 cal/g, 31 t above 120 cal/g, cladding max 438 C. Loop (tau 3 s, V 296): 80.0x, 106 cal/g, 0 t above 120, 400 C. Nothing reaches 160/240/285. **No case disperses fuel.**
- THM's `CRITFL` (1.8 MW/m2) only aborts the steady solve, and transients have no CHF dryout, so the cladding temperatures are not physics.
- **Kv correction:** INSAG-7 Ref. [28] gives Kv = **5.5** at about 30x (p. 67). (47) first wrote 5.8 from an OCR misread, corrected in (48). The INSAG Models give "approximately 6.0" (p. 121), and the initial radial peaking is 2.0 (p. 66).
- Shape at 30x: Kv 3.98 / 3.99 (fixed p / loop), Kz 2.61 / 2.64. Hottest bundle 121 / 120 x the initial mean vs 5.5 x 30 = about 165. Lower-half share at the peak 0.909 / 0.929. The peak plane is at 0.9 m vs INSAG's about 2 m (the flux shift of (27)).
- Radially broad and flattening (Kr 1.60 -> 1.44-1.46). The top 1000 bundles are within 10 % of the hottest. Kv falls short by 5.5 / 3.5-4.0 = about 1.4-1.55, similar in size to the fragmentation shortfall, but that is a coincidence in size, not a demonstrated cause.
- The fuel is nearly adiabatic: 77 % / 76 % of the local energy is still in the hottest bundle at the peak. Even fully adiabatic, only 0.12 t passes 240 cal/g.
- Fig. II-7 first look: highest contour 160, vs the model's t = 0 channel max of 160 %. The figure's high region is narrower and off-centre (digitised in card 24).
- CHF: [D] p. 70 critical-power formula. At 30 t/h it gives q_cr about 0.66 MW/m2, N_cr about 3.5 MW, critical exit quality about 0.28. The printed 4.07 subcooling coefficient is a misprint for 41.2. At low quality, min with the 2006 LUT x bundle factors. Post-CHF: the RELAP5/MOD3 set [R5V4], Groeneveld-Stewart T_min. Transient CHF: steady CHF, with x2 as the sensitivity bound ([TD1203]).

## Narrative
- 2026-10-23: (47) The 920 kJ/kg threshold was traced to its INSAG-7 source and re-labelled as disintegration. Graded criteria were sourced for Zr-1%Nb fuel and applied in `test/fuel_diag.jl`: no case disperses fuel, consistent with (46). The transient THM had no boiling crisis, so the cladding temperatures were flagged as unphysical. Planned order: CHF/post-CHF, local peaking vs Kv, then the starting-state probe. (by @assistant)
- 2026-10-23: (48) Shape diagnostics were added (trace, fuel and loop files byte-identical to (47)). INSAG-7's numbers were read from the page images, which corrected Kv 5.8 -> 5.5. The deficit is located: energy reaches the fuel about 1.4-1.6x too uniformly across the radius, while axial concentration and adiabatic retention match INSAG-7. CHF/post-CHF will give physical cladding temperatures but can't close the fragmentation gap. The plan was re-ordered so the Fig. II-7 radial comparison comes first. (by @assistant)
