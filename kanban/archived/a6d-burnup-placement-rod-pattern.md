---
id: 14
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, burnup, rods, sourcing, numerics]
---

# A6d: burnup placement, the 01:22:30 rod pattern, the rod response matrix, and the A8 boundary

Build the A8 initial state:
- per-channel burnup from [PAV]'s histogram,
- the sourced 01:22:30 rod pattern,
- a test of whether any burnup placement is operable at full power.

The placement turned out to be the largest unknown in the model, with up to +10 860 pcm across orderings. Most orderings are excluded by their own peak channel power. The per-rod pattern exposed 36 missing AZOC displacers (+609 pcm), and the real pattern is worth only −110 pcm. A measured rod response matrix showed the rods mostly tilt the core: 92 % of their authority is in the first azimuthal mode. Sequential LP brought the chequerboard placement to 3.7 % outside the ceiling, which retracted the earlier "falsified" verdict. The section ends with the A8-boundary review: A8 does not wait for the placement.

**Sources:** PROGRESS (13), (14), (17), (18), (19), (20), (21); key files: `tools/a6d_place.py`, `sources/derived/unit4_channel_map.csv` (`depth_cm`), `gen_rbmk_unit4.py` (`U4_RODS=insag`, `U4_BURNMAP`, `U4_RODDEPTH`, `BANKCOL`), `PROJECT_PLAN.md`.

## Outcome
- (13) Per-channel burnup is wired through `INST-BVAL CHAN` + `INST-BURN`. The [PAV] histogram reproduces 10.869 vs 10.9 MWd/kgU.
- (13) Placements at the same histogram span up to +10 860 pcm, with peaks of 14.6–19.5 MW for the core-scale orderings. The effect is flux redistribution, not Jensen's inequality (6 pcm).
- (13) The fixed-point refuelling solve diverges. The chequerboard gives +250 pcm and MAX/AVG 2.72. **(13)'s k and power numbers are superseded by (14)**; the ordering and conclusions survive.
- (14) `BANKCOL` bug: 36 AZOC channels were modelled as water. With the displacers restored, the effect is +609 pcm (independent prediction +522) and MAX/AVG 1.829 → 1.590. Absolute k from `U4_TILT=0` decks shifts by ~+600 pcm.
- (14) The 01:22:30 pattern (47 rods, 4346 cm) is worth −110 pcm, or 2.3 pcm per rod. Flat burnup with the real rods gives 3025 kW, MAX/AVG 1.573, inside [D]'s 3000–3200 kW. On a realistic spread the rods make peaking slightly worse.
- (14) A7 re-run: Doppler −230, density +331, net +101 pcm, spread 64.2 pcm.
- (17) Retraction of the first commit (`edfac73`): only the `U4_XEHIST=0123` runs mix states. The equilibrium-field chequerboard (4722.3 kW, 2.4556) is valid and 1.5× the ceiling.
- (17) Fully inserting all 211 rods costs −5552 pcm and raises MAX/AVG to 2.249.
- (18) Two-parameter rod solve. Best chequerboard MAX/AVG 2.2398; flat-burnup control 1.5347. Flatness and criticality are opposed.
  - Per-rod refinement walks uphill to 4.28. The response is a global radial redistribution.
  - Rod worth is non-monotone in depth: the last four planes give +2000 pcm.
  - The claim of "no local shape authority" was withdrawn in the same section.
- (19) Response matrix structure:
  - One rod moves channels 29–33 pitches away.
  - The response factorises into a fixed direction (cosine ≥ 0.9975) and a shared amplitude curve (within 0.054), so 190 runs are needed, not 1520.
  - The first azimuthal pair carries 91.8 % of the variance. No rod class escapes the tilt.
- (20) Full 1661 × 190 matrix: effective rank 2.09, mode 1 66.0 %. The unconstrained LP verified at 2.8285 (97 % model error), because the responses are non-additive.
  - A trust region fixes it: step 1 at 250 pcm reaches 1.7791 on 17 rods.
  - SLP 2.7702 → 1.7791 → 1.7419 → 1.7226. Best: 3312.4 kW, k = 1.042069, 31 rods. Extrapolated limit ≈1.702.
- (20) **Overturns (17)/(18):** the chequerboard is 3.7 % outside the 3200 kW ceiling (MAX/AVG ≤ 1.557–1.661), within model error. Verdict: marginal and undecidable. The core-scale placements stay ruled out.
- (20) Rebasing bug fixed: rods can now be withdrawn. A provenance hazard was caught (step 3 overwrote the step-2 base), and patterns are now content-addressed via `base_id()`.
- (21) Closure table and carried biases:

  | bias | size |
  |---|---|
  | `TG` pin | +500 pcm |
  | A6.4 neighbour spectrum | 7–10 % |
  | A6.3 section worths | 5–12 % |
  | placement | up to +10 860 pcm |

  Decision: A8 runs the placement as a band. Sequencing: source the fuel-failure criterion, source the `TG` range, build the A8 deck, Phase 2c, and formally defer A6c.

## Narrative
- 2026-10-04 (13): Fed [PAV]'s eight-group histogram per channel. The four placements spanned 10 900 pcm, yet the model rejects its own extremes through impossible channel powers. Even random scatter peaks at 1.7× the limit.
  - Tried solving for a flattening placement. The refuelling fixed point diverges (loop gain > 1), and a chequerboard barely helps.
  - Concluded that placement has to be solved jointly with rods and xenon.
  - Caveat recorded: the falsification holds only at full power, not for the 200 MW accident state. (by @assistant)
- 2026-10-04 (14): Used the channel map's sourced per-rod depths (`U4_RODS=insag`), adding AR (no displacer) and bottom-entry USP constructions. Quantisation adds +1.8 %.
  - Comparing the routes exposed the 36 missing AZOC displacers, corroborated against A6.5's bank worth.
  - The real pattern's −110 pcm is the operating-margin problem, derived from geometry. It is static and not a scram calculation.
  - Re-ran A7. Also recorded that the A6b xenon conclusion holds for a level but not a field. (by @assistant)
- 2026-10-05 (17): Narrowed an over-broad retraction: only the 0123-xenon runs at 3200 MW normalisation are mixed-state. The unpoisoned control shows a uniform poison does not reshape the core.
  - Showed uniform insertion makes the core less flat.
  - Defined the admissibility test as an inverse problem on 211 rod depths. (by @assistant)
- 2026-10-05 (18): Solved the shape at a stated insertion budget, deliberately not targeting k = 1, since that would compensate a known bias with absorber (rule 1).
  - The two-parameter family improved the chequerboard 23 %. Per-rod refinement failed because the response is global.
  - Withdrew the "no local authority" claim as statistically unsupported.
  - Corrected a mis-attribution to A6.4b.
  - Recorded core-scale non-monotone rod worth. (by @assistant)
- 2026-10-05 (19): Measured single-rod responses. The far-field response showed near-degenerate azimuthal-mode rotation, which explained (18).
  - Found the direction × amplitude factorisation that makes a 190-run matrix affordable.
  - The rods are a two-dimensional tilt control. Combinations with cancelling m = 1 are the only lever.
  - Formulated an exact LP with 191 variables and 1661 constraints. (by @assistant)
- 2026-10-05 (20): Measured the full matrix (190 runs at 48 min). The unconstrained LP failed because responses are not additive at −2659 pcm, and a trust region made it work.
  - Ran three SLP steps. The trust region shrinks as the core flattens.
  - Retracted the chequerboard "falsified" verdict, committed twice that day.
  - Fixed rebasing and provenance with content addressing (rule 7).
  - Durable finding: the control is most useful exactly where it is least linear. (by @assistant)
- 2026-10-05 (21): Reviewed Tier A at the A8 boundary. Recorded what is closed, the four disproved items, the one-signed carried biases, and the decision to run the placement as a band rather than wait for a source that does not exist. (by @assistant)
