---
id: 18
status: done
priority: Normal
blocked_by: []
tags: [tier-a, th, rods, openmc, neutronics, numerics]
---

# A8: the gaps, CPS worths corrected to OpenMC, the excursion band, and the Tier B reference

Close A8's ordered gaps and carry the excursion through its peak. Correcting the CPS absorber and displacer worths to OpenMC (gap 2) made the surge appear: 37× at 4.38 s and still rising. The 4.38 s "dry out" that stopped that run was not a boiling crisis. It was one of five transient-only THM defects, now patched. Across bracket A/B, flow and an initial-tilt band, the DONJON band spans 8× to 418× and contains all three INSAG-7 models. No case reaches 920 kJ/kg, even with rod peaking. This band is now Tier B's reference set.

**Sources:** PROGRESS (34), (35), (36), (37); key files: `tools/compo_cpsB.py` (`U4_CPSB`, stem `_cB<md5>`), `openmc/cps_verify.py`, `sources/derived/insag7_fig_II9_t0_axburn_fit_cB.txt`, `a8_fit_pchan_cB.txt`, `tools/a8_insag.py`, `insag7_fig_II11_model1.csv`, patches 0009–0013 and 0015 (THMTRS/THMH2O), 0014 (NCR `CLAMP`, `U4_NCRCLAMP`), `A8_TILT`, `openmc/pin_peaking.py`, `pin_peaking.json`, `TIER_B_WORKPLAN.md`.

## Outcome
- (34) Reproduced so far:
  - the 01:23 steam distribution,
  - the positive scram (+281 pcm),
  - the 0.71 dip,
  - the Fig. II-9 peaks,
  - timestep convergence to 0.7 %.

  Not reproduced: the surge, ≈ 2× against 3.5–80×. Gaps in order: the initial state beyond its axial shape, the CPS water/graphite worth, and the void worth (2.35–3.22 β against ≈ 5 β).
- (35) Gap 1 was already sourced: the 01:22:30 pattern is the AZ-5 pattern (AR at 1.4/1.6/0.2 m, INSAG-7 p. 65).
- (35) Gap 2: production DRAGON is 17 % too strong on the absorber and 10 % too weak on the displacer. Corrected by f_ABS = 0.8026 and f_DSP = 1.2016; f = 1 reproduces the original to 0.0 pcm.
- (35) After the refit (rms 0.0194), the static ramp peaks at +511.0 pcm = +0.97 $ at 160 cm.
- (35) The transient reaches 37.1× at 4.38 s, and the frozen twin 223× at 6.5 s.
  - It crosses 530 MW at 2.59 s, with period < 20 s, reproducing the 01:23:43 signals that INSAG-7 p. 121 says none of its models did.
  - Energy by 4.38 s is 5.2 GJ. The 5 ms twin is converged to a few percent through 4 s.
  - **Corrected in (36):** the stop on `THMH2O: DRY OUT REACHED IN CHANNEL 50 39 24` was written as a physical boiling crisis. It was a 100 J/kg-subcooled slice where the Saha-Zuber fit returned x = 1 and a NaN coefficient.
- (35) Gap 3 narrowed: lattice void worth ≈ 900 pcm (DRAGON) vs ≈ 1500 pcm (OpenMC). INSAG-7's +5 βeff is ≈ 1.6× even OpenMC, so this is a definition/source question.
- (36) Transient-only THMTRS/THMH2O defects, each found by measurement:
  - 0010: the profile fit evaluated below its net-vapour point.
  - 0011: XFL carried upward.
  - 0012: donor-cell faces.
  - 0013(a)–(c): adaptive and in-place flow relaxation, and a relative error criterion.

  0009 prints uncooled slices instead of aborting, and 0014 adds the NCR `CLAMP`. A single-channel replay screened all 1661 channels in 8–12 min: 0 failures with 0013(a)–(c). The `channel_mphy` digest was re-baselined (flow-error 5th digit by design).
- (36) The band, P/P0 at P0 = 200 MW:

  | case | peak | at | energy | hottest fuel |
  |---|---|---|---|---|
  | B | 182× | 5.32 s | 54.6 GJ | 495 kJ/kg |
  | A | 78× | 5.28 s | | 370 kJ/kg |
  | B, flow ×0.85 | 228× | | | |
  | B, tilt toward bottom | 418× | 4.42 s | | 537 kJ/kg, still rising, stopped 4.57/4.58 s |
  | B, tilt toward top | 8.1× | | | |

  All cases cross 530 MW at 2.29–3.10 s. The band spans 8×–418× and contains Models 1/2/3. The ordering of what dominates (initial axial shape, then void worth, then flow) matches INSAG-7 p. 122.
- (36) No case reaches 220 cal/g = 920 kJ/kg. Kv peaks at 3.9–4.2, against ~6.0 / 5.5.
- (37) Patch 0015 floors |G| at ρ_l V_gj in the drift-flux term, giving 0 screen failures. Peaks are unchanged.
  - The bottom-tilted case now runs to 7.00 s: 106.0 GJ, hottest bundle 656 kJ/kg (2300 K).
  - Rod-to-rod peaking is 1.024–1.049, putting the hottest rod at ≈ 680 kJ/kg. Rod peaking is not what separates the band from failure.
  - Kv and the radial initial shape remain the candidates.
- **920 kJ/kg criterion later re-sourced in PROGRESS (47):** INSAG-7's 220 cal/g is a disintegration threshold, not the onset of failure.
- **Closes the DONJON band as Tier B's reference set.** Next is the Julia/CUDA engine (`TIER_B_WORKPLAN.md`).

## Narrative
- 2026-10-09 (34): Took stock of A8. The surge is the one thing not reproduced; every tested lever moved it by a few percent or reduced it. Two findings explain why: steam is worth least where the power goes, and the result is hypersensitive to the initial axial shape. Gaps were ranked, and housekeeping recorded: the 0008 limitation, spark on the old binary, and the xenon numbers needing re-measurement. (by @assistant)
- 2026-10-10 (35): Gap 1 needed nothing new. For gap 2, I acted on OpenMC CPS-worth measurements that had been on file since A6.3: rebuilt the rod COMPOs to the OpenMC worths and refitted the inversion.
  - The scram's peak positive reactivity nearly doubled to +0.97 $, and the surge appeared. It is rod-driven, with net feedback negative early.
  - It reproduced the recorded 530 MW / 20 s signals, which INSAG-7's models did not.
  - The run stopped on a "dry out" that I first called physical; (36) corrected that.
  - Gap 3 was narrowed to a source question. (by @assistant)
- 2026-10-15 (36): Showed the dry-out was a fit artefact, then chased four more transient THM defects. The key method change was a single-channel replay: 3.5 s instead of 3 h, so the whole core screens in minutes, and failures fell 5 → 89 → 16 → 0 across the patches.
  - Ran the band. Its initial-tilt form is my assumption, since the source names none.
  - Compared magnitude, timing, and fuel enthalpy against INSAG-7 and its digitised Fig. II-11, with the caveats stated. (by @assistant)
- 2026-10-16 (37): Fixed the drift-flux void collapse at G → 0 (patch 0015) and carried the bottom-tilted case to 7 s. Measured rod-to-rod peaking in OpenMC: still ≈ 680 kJ/kg against 920. Declared the DONJON band closed as Tier B's reference and moved work to Tier B. (by @assistant)
