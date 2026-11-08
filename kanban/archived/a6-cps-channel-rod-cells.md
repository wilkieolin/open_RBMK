---
id: 8
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, openmc, rods, numerics, infra, sourcing]
---

# A6: the CPS channel, rod cells, and the rod-cell equivalence

Build the CPS (control-rod) channel as DRAGON cells verified against OpenMC, turn them into core data, map the Unit 4 channels, and price a transient time step. The rod cells were built and verified, and the Unit 4 channel map was sourced and closed. Turning the cells into core data broke on the neighbour fuel data. The planned rod-cell equivalence (A6.4b) was then shown by measurement to be impossible, and the bias is carried as a measured, one-signed band. The same span decided not to port DRAGON/DONJON out of Fortran, and measured what a `KINSOL:` step costs.

**Sources:** PROGRESS "A6: the CPS channel" (2026-09-27), "Should we port DRAGON/DONJON out of Fortran?" (2026-09-29), "Phase 0 of the transient" (2026-09-30), "A6.4b: the rod-cell equivalence cannot work" (2026-09-30); key files: `A6_CPS_PLAN.md`, `openmc/cps_common.py`, `openmc/cps_verify.py`, `openmc/rbmk_cell.py`, `openmc/a64b.py`, `openmc/a64b_findings.txt`, `openmc/sup5.py`, `rbmk_cps_a63_twat.x2m`, `rbmk_cps_a64_smkm.x2m`, `rbmk_cps_a64b_smk.don`, `decks/Donjon/data/rbmk_core_3d_dual.don`, `decks/Donjon/data/gen_kin_probe.py`, `tools/kin_cost.sh`, `decks/Donjon/data/kin_cost.txt`, `tools/render_core_layout.py`, `tools/build_unit4_map.py`, `tools/digitise_fig_II6.py`, `sources/derived/core_layout.xlsx`, `sources/derived/unit4_channel_map.csv`, `5.1/PyGan/`.

## Outcome
- A6.1 sources PASSED. B₄C density 2.0 g/cm³ (bracket 1.7–2.3) was found in no source and is carried as an open input.
- Gate A6.2 passed: the 3×3 supercell reproduces the single cell to +2.8 pcm (DRAGON) and +2 pcm (OpenMC).
- Gate A6.3 missed: production DRAGON is 9–17 % low on every section worth, and 5–12 % low after convergence. The residual is attributed and carried as the A′ correction (+60 to +1107 pcm). Its source: the WAT baseline is 450–620 pcm too reactive, and the absorber over-absorbs by −630 to −1130 pcm. CPS water temperature interpolation was eliminated as the cause.
- A6.4: homogenisation is exact (A64S ≤ 0.1 % on worths). Using fuel-COMPO neighbours (A64V) leaves the displacer −7 to −9 % and the drained channel −9 to −10.5 %.
- `MCFD 1` loses +30.6 to +34.4 % of absorber worth and cannot carry a converged SPH. `DUAL 1 1` costs 8 % more wall time (2.11 s vs 1.95 s) and 17 MB, and agrees with MCFD to 0.7 pcm on a rod-free core. From A6.5 on, the core uses `DUAL 1 1`.
- Channel map: 1661 fuel + 211 rods + 12 DKE(v) + 4 start-up chambers = 1888 positions. Fig. II-6 registers onto Fig. 2.3 at a single offset (1, 1). 47 rods were inserted at 01:22:30, 4346 cm in total. The types of 32 rods remain an assumption.
- Depletion grid: restoring the 500 MWd/t node brought the 840-point COMPO to 1 pcm of the reference. Round trip 0.9 pcm, off-grid 23.9 pcm. Void bracket at 10 900 MWd/t: A/A′/B = +1.94/+2.41/+2.72 $.
- Port decision: do not port. Build PyGan, generate CLE-2000, stop parsing `.result` text, compile at `-O3 -march=native`, and spend the rewrite budget on Tier B.
- Phase 0: a severe transient costs 0.4301 s/step, against 0.0903 s/step frozen (4.8×), at ≤ 105 MB. That is ~29 min of neutronics for 4 s at 1 ms, and roughly 4 hours per scenario with TH Picard. These numbers are on IAEA PWR constants.
- A6.4b disproved:
  - Flux-matched factors make the gate worse.
  - A removal-rate target will not converge.
  - A ±20 % sweep of the VOID rod-cell factors never straddles zero (best −3.45 %).
  - The cause is neighbour SPH factors, which span 1.00–1.56 in a 5×5 supercell and are set to 1.0 in the core.
  - Of the ~9 % error, ~3 points are recoverable and ~6 points depend on the centre.
  - The bias is carried as one-signed: displacer and drained channel 7–10 % low, absorber within ±3 %.
- Corrected within the A6.4b section (item 5): item 3's per-cell cross-section numbers came from a parser bug. Redone, the edge cell is the perturbed one (−2.9 to +5.2 %). The k-based results were unaffected.

## Narrative
- 2026-09-27: Built the CPS channel from a single transcription (`cps_common.py`) that generates the DRAGON, DONJON and OpenMC inputs, so the codes cannot drift apart.
  - Gate A6.2 passed. A6.3 missed and its residual was carried as A′.
  - 2026-09-28 follow-ups: absolute supercell k located the error in the WAT baseline and in the absorber, and a draglib temperature-node test eliminated S(α,β) interpolation as the cause.
  - A6.4 showed homogenisation is exact and the neighbour fuel data is wrong. MCFD was found to lose a third of absorber worth, so `DUAL 1 1` was adopted at 8 % cost.
  - A rod-cell equivalence via `SPH: … SPRD` was planned, after a source read showed `EQUI` aborts on a MULTICOMPO.
  - A6d registered INSAG-7 Fig. II-6 onto Dollezhal Fig. 2.3 exactly, closing five counts that were not inputs. This unblocked A6.5.
  - Recorded a list of CLE-2000/DRAGON traps, plus a parser bug of my own that had withdrawn some quoted percentages. (by @assistant)
- 2026-09-29: Assessed porting DRAGON/DONJON out of Fortran. Of the obstacles this project actually hit, the domain model accounted for 6, against 3 for Fortran and 4 for CLE-2000. A rewrite would reproduce those and start at zero validation, so the decision was not to port. Instead: PyGan, generated decks, structured results, and Tier B as the rewrite. (by @assistant)
- 2026-09-30 (Phase 0): Ran the first time step, on IAEA constants, with three generated kinetics decks. `KINSOL:` needed `OVERV` and `UNIT` on `TRIVAA:`. The quiet-variant cost flattered the solver five-fold, so the budget uses the severe 0.4301 s/step. Checks: the null transient drifts 1.4e-4, and the severe step obeys the prompt-jump relation (ρ = −0.20 $). Conclusion: A8 is hours, and Tier B stays parallel rather than urgent. (by @assistant)
- 2026-09-30 (A6.4b): The `SPRD`/`OUT: INTG` machinery was proved by an on/off pair before use.
  - Solving the rod-cell factors against flux made worths worse, because SPH preserves reaction rates and a black absorber's rate is nearly invariant to its own factor.
  - A 5×5 factor sweep never reached zero error, so the equivalence is impossible.
  - The defect is the neighbours' spectrum: 82.3 % of fuel channels have a CPS in the eight-ring.
  - A 5×5 two-rod supercell (`sup5.py`) showed the neighbour SPH factors are large, sub-additive (ratios 0.64/0.55), and ordered by Σ1/d² rather than by eight-ring count.
  - Closed as a design. The default is to carry the bias as a one-signed band; fitting the four factors was rejected as a fudge. (by @assistant)
