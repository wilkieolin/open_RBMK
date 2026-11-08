---
id: 17
status: done
priority: Normal
blocked_by: []
tags: [tier-a, th, rods, neutronics, numerics, infra, xenon, burnup]
---

# A8: the measured initial shape, TH feedback in the transient, and why the surge stayed small

Invert INSAG-7 Fig. II-9's t = 0 axial shape into the model, couple `THM:` into every kinetics step (A8.3), and find out why the INSAG-7 surge did not appear.

Results in order:
- The inverted state reproduces the bottom shift of the flux by rod motion alone.
- With feedback, the first coupled transient was a monotonic shutdown.
- Holding the USP rods (as in 1986) made the scram positive, peaking at 1.976×. INSAG-7's models give 3.5×–80×.

Bracket B, subcooling, flow and pressure each moved that peak by only a few percent, or lowered it. The one large lever found was the initial axial shape.

**Sources:** PROGRESS (27)–(33); key files: `tools/digitise_fig_II9.py`, `sources/derived/insag7_fig_II9_axial.csv`, `tools/a8_axinvert.py`, `sources/derived/insag7_fig_II9_t0_axburn_fit.txt`, `sources/derived/insag7_fig_II9_t0_axburn_fit_xe.txt`, patches 0004 (`HISTORY n`), 0005, 0006 (`FLOW-RELAX w`), 0007 (`redget_c.c` ECHO buffer), 0008 (THMH2O at |G|), `tools/a8_ramp.py`, `tools/a8_thcheck.py`, `tools/compo_voidB.py` (`_ACompoVB`), `tools/a8_voidz.py`, `tools/a8_zonevoid.py`, `tools/a6b_xenon.py`, env `U4_TH=acc`, `U4_MOVGRP`, `A8_USP`, `U4_PACC`, `U4_THDUMP`, `U4_VOIDB`, `U4_KINVOID`, `U4_XEAX`, `U4_SUBC`, `U4_KINFB`, `U4_QFRAC`.

## Outcome
- (27) Digitised 37 markers. The six-mode Legendre LM fit reached RMS 0.020 (k 1.023557), with burnup ×1.22 mid and ×0.50–0.52 at the ends. This is a fit, not a validation.
  - Static rod advance reproduces the bottom shift: 4 s ↔ 160 cm, 6 s ↔ 240 cm. The model peak sits ~35 cm deeper than measured.
  - The ramp stays negative throughout: −141 at 40 cm, recovering to −78 at 80 cm.
- (28) Initial state from INSAG-7 p. 64: 200 MW, 56 000 m³/h, 3 °C subcooling.
  - Three driver defects fixed: memory (77 GB → patch 0004), tolerance (1e-3), and the fixed-point gain ∝ 1/dt (0006, with 0005 accepting residual cycling).
  - 5 ms converged to ~0.03 %. Cost 17 s/step.
  - Result: monotonic shutdown to 0.111 at 7 s, with feedback +0.41 %. **Superseded by (29):** USP was wrongly driven.
- (29) In 1986 the USP rods were not on EPS (INSAG-7 p. 46), so `U4_MOVGRP=12`. Holding them makes the static ramp positive from ~50 cm, peaking at +281.0 pcm = +0.53 $ at 160 cm. This matches INSAG-7 p. 39's "first eight seconds … positive".
  - 7 s transient: minimum 0.714 at ~1.1 s, peak 1.976× at 4.43 s. Fig. II-9 peaks 2.50/2.74/2.86 vs measured 2.49/2.67/2.80.
  - Net feedback is negative: the frozen twin reaches 2.18×. Static power coefficient is −0.57 × 10⁻⁴ β/MW, against INSAG-7's positive +0.6 × 10⁻⁴.
  - The old CPS-worth candidate was dropped here; it was reinstated in (33) and closed in (35).
- (30) THM places the 01:23 steam correctly: onset at bundle 25–26, top 3–4 bundles only. Added power puts steam in the upper half only.
  - Core void worth is +1242 pcm = +2.35 β, against ~5 β sourced.
  - No further burnup data was found.
- (31) Bracket B (`_ACompoVB`, worst miss 0.014 pcm): void worth +1702 pcm = 3.22 β, power coefficient +2.7 pcm / 100 MW.
  - In the transient it changes ≤ 0.009 %. The lower half (89–95 % of the power) never boils within the window, so the limit is thermal-hydraulic.
  - Per-bundle xenon refit gives rms 0.0201 with the bottom burnup barely changed, so the bottom is not a xenon artefact.
  - Two defects fixed: `xenon_at_0123` start state (invalidating the earlier per-channel xenon numbers) and the ECHO overflow (patch 0007).
  - The 1 °C run aborted at 2.01 s.
- (32) Abort diagnosed as a reversed G → NaN `REL**0.8` → 273.15 K wall. Patch 0008 evaluates at |G|, and no earlier result moves.
  - 1 °C reaches 7 s, peak 1.326 at 4.35 s.
  - **Corrected 2026-10-09:** the reduction comes from the starting state, not from feedback (frozen 1 °C peak 1.332; fb/frozen 0.995–1.004).
- (33) Zone void worths are all positive and near-additive. Per φ², the bottom is worth 1/3 (B) to 1/5 (A) of mid-core; the end-zone deficit is partly reflector leakage.
  - At 1 °C, a 1.4-point shift in lower-half share cuts the frozen peak from 2.18 to 1.33.
  - Flow ×0.85 gives −2.5 %.
  - Pressure: IPRES=0 already bounds bottom boiling, and the sourced drum pressure was rising.

## Narrative
- 2026-10-06 (27): Digitised Fig. II-9 and inverted its t = 0 curve. A simple multiplicative fixed point fails on axial near-degeneracy, so LM with a trust region was used, stopping before it fitted noise.
  - Used the never-fitted 4/6/7 s curves as the test. Rod motion alone reproduces the shift at the sourced speed, but no positive net ramp; void feedback (A8.3) is the next step. (by @assistant)
- 2026-10-07 (28): Coupled `THM:` per step from the sourced 01:23 state.
  - Fixed three driver defects by measurement, including a deterministic boiling-node fixed-point instability that no tolerance can fix.
  - Verified with a null transient, a timestep study and reproducibility.
  - The result reproduced INSAG-7's first-second drop and redistribution but not the surge. Four candidate causes were listed. (by @assistant)
- 2026-10-07 (29): Found in INSAG-7 p. 46 that USP rods were not on the EPS signal in 1986, so the "only physical case" comment was wrong. Holding them made the scram positive and matched p. 39 and the Fig. II-9 peaks to 3 %.
  - The remaining disagreement is the sign of the net power coefficient, so the void side is ranked next. (by @assistant)
- 2026-10-07 (30): Checked where THM puts the steam before touching cross sections. It is correct at 01:23 and consistent with the energy balance and the nominal checks.
  - New steam stays in the upper half with the shape held.
  - Core void worth is about half the sourced value.
  - Noted the `IPRES=0` simplification, and ordered the next steps. (by @assistant)
- 2026-10-08 (31): Built and gated bracket B in the core. It flips the static power coefficient positive but changes nothing in the transient: void dumps show the lower half stays subcooled through the window.
  - Separated xenon from burnup in the inversion. The bottom depletion is real.
  - Fixed the xenon start-state defect and the ECHO overflow.
  - The 1 °C sensitivity aborted. (by @assistant)
- 2026-10-08 (32): Traced the abort to a momentary flow reversal producing a NaN Dittus–Boelter. Patched to |G|. The reversal itself remains an artefact.
  - The 1 °C transient ran and its surge was smaller.
  - First read the gap as void collapse; the next day's frozen-TH twin corrected that to a starting-state effect. (by @assistant)
- 2026-10-09 (33): Measured void worth by height (new zone-perturbation tool, 0.00 pcm re-import control) and t = 0 shapes. The surge is hypersensitive to initial bottom flux, as INSAG-7 p. 69 says of its own answer.
  - Ran the sourced flow band. The sourced pressure direction rules out a depressurisation patch.
  - Open: the radial/rod initial state and the CPS water/graphite worth. (by @assistant)
