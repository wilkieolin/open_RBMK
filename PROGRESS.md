# RBMK-1000 Coupled Neutronics/TH Model — Progress Log

> **2026-09-22 (1): rewritten after an audit.** The previous version reported Stages 1–3
> complete and Stage 4 blocked on SPH. That status did not survive inspection — most of the
> claimed validation traced to fabricated cross sections or misdiagnosed failures. Full
> audit: `EVALUATION.md`. Work order: `TIER_A_WORKPLAN.md`.
>
> **2026-09-22 (2): A3 rebuilt, A5 gate passed.** Every RBMK lattice deck in the repo,
> including the one the audit above called legitimate, turned out to be a CANDU-6 bundle.
> The cell has been rebuilt on RBMK dimensions and now gives a positive void coefficient
> rising to ~4 β at discharge burnup *(the ~4 β figure was retracted the next day — see the
> 2026-09-23 entry)*. Current decks: `Dragon/data/rbmk_cell_a3.x2m`,
> `rbmk_a5_void.x2m`, `rbmk_proc/RbmkLib.c2m`. Details in the last section of this file.
>
> **2026-09-23: cross-checked against OpenMC. The A5 number did not survive.** OpenMC is now
> working (source build, ENDF/B-VIII.0 and VIII.1 data). The RBMK geometry is confirmed
> exactly. The positive void coefficient rising with burnup is confirmed. The *value* is not:
> OpenMC gives roughly **twice** DRAGON's void reactivity at every burnup, and the two codes
> differ by 12× at fresh fuel. A CANDU-6 control run in both codes agrees to 1.3 %, so this
> is an RBMK-specific method difference, not an OpenMC modelling error. One real bug was
> found in the deck. See "OpenMC cross-check" below.

> **2026-09-23 (2): Phase 0 corrections.** The free-gas hydrogen bug is fixed:
> `RbmkLib.c2m` now uses bound `H1_H2O`, and `rbmk_cell_a3.x2m` returns
> **k∞ = 1.310172**, matching the value `rbmk_h2otest.x2m` had already measured
> independently. `RbmkLibH.c2m` is retired (it was the fix in a second file); the old
> free-gas composition is preserved as `RbmkLibF.c2m` so the comparison stays
> reproducible. Two records were also found to be wrong in the other direction — the
> A2 units bug is already fixed in the generator, and the "not reachable from the deck"
> claim was overstated. Both corrected below. Next steps: `plans/` (A5b MULTICOMPO first).

> **2026-09-24 (2): cell geometry pinned to the designer's own monograph.** Dollezhal &
> Emelyanov (Atomizdat, 1980) settles three of the four open geometry questions. The
> pressure tube **88 × 4 is confirmed** — the Wikipedia 92 × 4 reading is wrong, closing a
> 10 % coolant-area ambiguity. The **carrier was wrong** (a 15 × 1.25 central tube with a
> solid 12 mm rod inside, not a 13 mm hollow tube) and the **clad was wrong** (13.5 × 0.9,
> not 13.6 × 0.825). Ring radii remain open and are deliberately unchanged. Coolant −3.2 %,
> Zr +9.3 %; graphite and fuel untouched. **k∞, the A5 void curve and the A5b MULTICOMPO are
> all superseded and must be re-run.** See the last section before "Standing rules".

> **2026-09-24 (3): the cell geometry is closed.** Eight sources the project had not used
> settle the remaining open items:
> - **Ring radii 1.60 / 3.10 confirmed**: rod circles ⌀32 / ⌀62 mm, in two independent sources.
> - **2 mm pellet hole confirmed**: three sources, plus a uranium-mass check against Unit 4's
>   114.7 kg U per assembly.
> - **Ring phase confirmed** off Dollezhal's own drawing.
> - **Graphite gas gap confirmed** as a valid idealisation.
> - **Burnup axis confirmed** as per tonne U.
> - **Clad OD refined 13.5 → 13.58**, the drawing nominal. ID 11.7 is unchanged.
>
> `rbmk_cell_a3.x2m` on the pinned draglib: **k∞ = 1.304123**, guardrail passed, DRAGON
> fractions equal the analytic ones.
>
> One finding reaches past geometry. **Unit 4 at the accident averaged 10.9 MWd/kgU, not 20.**
> The DRAGON/OpenMC bracket has been read at the wrong burnup. See "Cell geometry closed" below
> and `sources/README.md`.

> **2026-09-24 (4): re-baselined in both codes on the closed geometry. The bracket now
> straddles prompt criticality at the accident state.**
> - DRAGON: k∞ 1.304123, COMPO rebuilt (round trip 6.6 pcm, off-grid 26.5 pcm, now reproducible), β curve unchanged.
> - OpenMC: re-run on VIII.1.
> - The geometry fixes cut DRAGON's void worth at every burnup and left OpenMC's nearly unchanged, so the method gap widened.
> - At 10–15 MWd/kgU, where Unit 4 was, full voiding is +0.4–1.65 $ in DRAGON and +2.25–4.6 $ in OpenMC.
> - The ~1.9 multiplier held only at 20 MWd/kg.
> - Resolving the method gap moves ahead of A6. See "Re-baseline on the closed geometry" near the end.

> **2026-09-25: the method gap is mostly DRAGON not being converged, and the prompt-critical
> straddle is gone.** The four-factor split puts the whole DRAGON/OpenMC disagreement in
> resonance absorption (U-238 and Zr); everything thermal agrees.
> - Converging DRAGON against itself closes ~75 % of the fresh-fuel gap. The energy mesh
>   (172 → SHEM-361) dominates, then Zr self-shielding, then the spatial mesh.
> - On the converged library, full voiding at the Unit 4 average burnup is **≈ +1.96 $
>   (DRAGON) vs ≈ +2.7 $ (OpenMC)**: both above prompt critical, reached without using the
>   historical outcome.
> - DRAGON's 5 MWd/kg dip was a 172-group artifact.
> - See "Method gap: hypothesis register". The production COMPO is still on 172 groups and
>   now known to be unconverged.

> **2026-09-25 (2): third-party check.** On the RBMK Safety Review Project cell from Alexeev
> et al. (1998):
> - Our OpenMC reproduces MCNP and MCU (watered k∞ within 0.1–0.4 %).
> - Production DRAGON gives half their void effect (Δk 2.46 vs 4.80–4.85 %); SHEM-361 + Zr
>   self-shielding gives 3.45.
> - Parisi & D'Auria (2007) independently found DRAGON 21 % low against MCNP.
> - The Kurchatov critical experiments aren't specified in that paper, and are impurity-limited.
> - Local runs were stopped to move to the GB10; see the hand-off at the end of "Third-party
>   benchmark".

> **2026-09-25 (3): the void gap closes to within its criterion.**
> - **Hot cell, fresh fuel.** DRAGON on SHEM-361 + Zr self-shielding + 4× mesh + MOC with P1
>   scattering gives full-void Δρ **+763 vs OpenMC +821 ± 21** (inside 2σ + 5 %). At 0.35 g/cm³
>   it is +553 vs +533.
> - **SRP-1994 cell.** DRAGON is within 4 % of OpenMC (4.59 / 5.04 vs 4.77 / 5.24 %Δk); it was
>   42–48 % low in production.
> - **What's left.** Nominal k∞ is still 240 pcm apart (resonance escape); that residual is
>   attributed, not closed.
> - **Pellet-rim self-shielding.** The per-ring treatment is a USS artefact (−890 pcm, the wrong
>   direction), not missing physics.
> - **Depletion.** 60–70 % of the DRAGON/OpenMC depletion difference is a burnup-normalisation
>   convention: OpenMC's fission-Q mode books ~5 % more fissions per MWd than DRAGON.
> - **SRP cell, 8× mesh.** DRAGON gives 4.80 / 5.27 %Δk, matching OpenMC (4.77 / 5.24) and MCNP.
> - **Accident state (Gate B).** On matched burnup scales and identical fuel, DRAGON is within 6–9 %
>   of OpenMC. Full voiding at 10.9 MWd/kgU is **+2.4 to +2.75 $** across both codes. See "Phase A–B
>   on the GB10".

> **2026-09-26: Phase C done: production is on the converged library.**
> - **Library.** SHEM-361 with Zr self-shielded in `RbmkLib`; k∞ 1.313968.
> - **COMPO.** Rebuilt at 840 points with burnup nodes at 7.5 and 12.5. Round trip 6.7 pcm, off-grid
>   21 pcm, β monotone.
> - **Full-void worth at 10.9 MWd/kgU:** +1.95 $ (production COMPO), +2.42 $ (plus the measured
>   mesh/MOC correction), +2.72 $ (OpenMC matched).
> - **Depletion step size.** 5 MWd/kg steps overstated nominal k∞ by ~200–530 pcm; the void worth
>   was converged.
> - **What's next.** The method-convergence segment is closed. Next is A6 (CPS channel cells),
>   after a check-in. See "Phase C".

> **2026-09-26 (2): the plan is reordered.** The lattice gap is closed, but nothing whole-core is
> built or validated yet. New order: A6 (CPS cells) → A6b (Xe axis + COMPO rebuild) → A6c
> (Smolensk-3 start-up, the first measured core-level reference) → A6d (Unit 4 state at 01:22:30)
> → A7 → A8 → A9. See "Where the project stands".

> **2026-09-27: A6 — the CPS channel is built and verified, and homogenisation is where it
> breaks.** The rod, displacer and water sections exist in both codes from one transcription
> (`openmc/cps_common.py`), and every section worth is now measured against OpenMC.
> - **A6.2 passed.** The 3×3 supercell reproduces the single cell to +2.8 pcm (DRAGON), +2 (OpenMC).
> - **A6.3 missed its gate.** Production DRAGON is 9–17 % low on every section worth; converging it
>   (4× mesh, MOC P1) leaves 5–11 %. The residual is tabulated per state as the A′ correction
>   (+60 to +1107 pcm), not fitted.
> - **A6.4: the transport-to-diffusion step is exact; the neighbour data is not.** With all nine
>   cells from the CPS MULTICOMPO, DONJON reproduces DRAGON to ~1 pcm. With the eight fuel cells
>   taken from the *fuel* COMPO — what the core will actually do — the displacer and drained-channel
>   worths fall 7–10 % short. An infinite-lattice fuel cell is not a fuel cell next to a rod.
> - **A6.4b chosen:** an explicit equivalence on the rod cell. DRAGON's own normalisations were
>   measured out first; none of them closes it.
> - **A6d done, and it is the strongest result here.** Two independent digitisations — Dollezhal
>   Fig. 2.3 (Leningrad-2) and INSAG-7 Fig. II-6 (Unit 4 at 01:22:30) — register exactly, all 223
>   sites at one offset. Unit 4's channel map is now sourced rather than assumed: 1661 fuel,
>   211 rods, 12 ДКЭ(в), 4 start-up chambers, 1888 positions, each count closing against a
>   different source.
> - **Fuel COMPO rebuilt** on a corrected depletion grid (a dropped 500 MWd/t node had biased the
>   whole trajectory 45–75 pcm low). Gates: round trip 0.9 pcm, off-grid 23.9. The void bracket at
>   10.9 MWd/kgU is unchanged to within a few pcm: **+1.94 / +2.41 / +2.72 $**.
> - See "A6: the CPS channel".

## Objective

3-D spatially-resolved coupled neutronics/TH RBMK-1000 model, driving a historically
accurate **RBMK mnemonic display** (1661 channel outlet temperatures, 211 rod positions,
in-core detector readings). Accident scenario runs to **fuel failure** and stops.

---

## Architecture (three tiers)

| Tier | What | Status |
|---|---|---|
| **A — offline physics** | DRAGON5 lattice → MULTICOMPO → DONJON5 3-D steady + reference AZ-5 transient. Source of truth. | **In progress.** A3–A5b done and method-converged (SHEM-361 + Zr SS, 840-point COMPO, void bracket). A6 cells built and verified, homogenisation open (A6.4b); A6d channel map sourced. A6.5 core, A6b Xe, A6c Smolensk-3, A7–A9 to go. |
| **B — online engine** | Standalone 2-group nodal/FD diffusion + 6 precursor groups + 1-D per-channel TH on the GB10 GPU, reading Tier A cross sections, validated against Tier A. | Not started |
| **C — mnemonic panel** | Driven by Tier B. | Not started |

DONJON cannot be the live engine: single-threaded, no GPU path, ~0.2–3 s per flux solve.
It is the offline reference that makes Tier B trustworthy.

---

## Toolchain: OPERATIONAL

| Component | Version | Location | Status |
|-----------|---------|----------|--------|
| DRAGON5 | 5.1.0 | `5.1/Dragon` | Built |
| DONJON5 | 5.1.0 | `5.1/Donjon` | Built |
| TRIVAC5 / GANLIB5 | 5.1.0 | `install/bin/` | Built |

- Build: sequential `make` (parallel fails on Makefile target naming). Prefix `install/`.
- Platform dir is `Linux_<arch>`: `Linux_aarch64` on the GB10, `Linux_x86_64` on the WSL
  box. Results land in `5.1/<code>/Linux_<arch>/*.result`.
- **Compiled at `-O` (i.e. `-O1`)** and there are **zero OpenMP directives in Trivac/Donjon**
  — `-fopenmp` only activates Dragon's MOC/S_N lattice solvers. Rebuilding with
  `-O3 -march=native` is free performance.

## Nuclear data: AVAILABLE

| Library | Location | Notes |
|---|---|---|
| APOLIB99 (ENDF/B-VIII.0r1) | `libraries/l_endian/draglibendfb8r1Apolib99_v5p1` | **172 groups, not 99** despite the filename and every deck comment (`NGRO 172` in the run log). Carries `NDEL 6` precursor data. |
| ENDF/B-VIII.0 HDF5 | `libraries/hdf5/gal_xs_99g.h5` | unused so far |

Verified isotope names: `Zr90 Zr91 Zr92 Zr94 Zr96`, `C12_GR`, `Nb93`, `He4`.
Access via the per-deck `<name>.access` script, which symlinks `DLIB_99`.

---

> **2026-09-30: `KINSOL:` runs, and a hard time step costs 4.8× a quiet one.** The first time
> step the project has ever advanced. On the full `DUAL 1 1` core a severe transient costs
> **0.430 s/step** against 0.090 s/step with a frozen macrolib — so the easy measurement, which
> is the one a probe naturally produces, understates A8 five-fold. Budget: ~29 min of neutronics
> for a 4 s transient, ~4 h per scenario once the thermal-hydraulic Picard loop is included.
> Peak memory 105 MB. Tier B stays parallel rather than urgent. Two `KINSOL:` prerequisites are
> undocumented and were found in source: `OVERV` (`KINXSD.f:152`) and `UNIT` on `TRIVAA:`.
>
> **2026-09-30 (2): A6.4b is disproved, and the real cause of A6.4 is named.** The rod-cell
> equivalence cannot close the gate — not "is hard", cannot. Matching the rod's flux makes the
> worth error worse (VOID −14 % against −10 % at unit factors), matching its removal rate will
> not converge because a black absorber's reaction rate is nearly invariant to its own SPH
> factor, and sweeping the factors over ±20 % never brings the worth within −3.45 % of a gate
> that wants 1 %. The cause is not the rod: **the eight fuel cells around it differ from
> infinite-lattice fuel by ±3 % at zero burnup**, because the rod perturbs the spectrum across
> the whole 75 cm supercell. Fitting four factors to one worth would hit the gate and was not
> done. Carried as a measured one-signed bias, mechanism named.

## Validated results

| Item | Result | Status |
|---|---|---|
| IAEA-3D benchmark, `Donjon/data/iaea3d_fuelmap.x2m` | k_eff = 1.028980 (ref 1.029069, **−8.9 pcm**) | ✅ Genuine. Standing regression test and the structural template for the core workflow. |
| RBMK lattice cell, `Dragon/data/rbmk_cell_a3.x2m` | **k∞ = 1.313968** (2026-09-26, SHEM-361 with Zr self-shielded, `RbmkLib`) | ✅ Geometry closed against sources, guardrail passed, DRAGON's fractions equal the analytic ones. **Superseded:** 1.304123 on the pinned 172-group draglib (2026-09-24 (3)); the +985 pcm is the converged library, not a geometry change. Lineage of the geometry corrections before that: 1.310172 → 1.308679 (library, −87) → 1.304717 (Dollezhal carrier and clad, −232) → 1.304123 (clad OD 13.58, −35). The value is post-hydrogen-fix (2026-09-23) and was matched independently by `rbmk_h2otest.x2m`. |
| Void coefficient vs burnup, `Dragon/data/rbmk_a5_void.x2m` + A5b COMPO | full void at the Unit 4 average burnup, 10.9 MWd/kgU: **+1024 pcm (+1.94 $) production, +1273 (+2.41 $) with the measured method correction, +1437 (+2.72 $) OpenMC matched**. At 15 MWd/kgU: +1666 / +1932 / +2254. 2026-09-27 | ✅ **Sign, trend and magnitude now agree between two codes and a third-party benchmark**, after the method-convergence segment; the 38 % spread fell to 13 %. Carried as a three-variant bracket (`openmc/void_bracket.py`), not a single number. Superseded: the 2026-09-24 (4) reading of +0.39 / +1.65 $ (DRAGON) against +2.25 / +4.60 $ (OpenMC), which came from the unconverged 172-group library. |
| CPS section worths, `openmc/cps_verify.py table` | 3×3 supercell, six states: converged DRAGON is **5–11 % low** against OpenMC on absorber, displacer and drained-channel worth (production 9–17 % low) | ⚠️ Measured against an independent method (rule 4) and **not closed**. The production-minus-converged difference is tabulated per state as the A′ correction, +60 to +1107 pcm. Two of twelve states still computing. |
| CPS homogenisation, `openmc/cps_verify.py a64` | DONJON on the homogenised supercell vs DRAGON: **~1 pcm with CPS-COMPO neighbours; −7 to −10 % on the displacer and drained channel with fuel-COMPO neighbours** | ⚠️ Gate A6.4 fails, cause identified: the homogenisation, SPH equivalence and solver are exact, the neighbour data is not. **A6.4b, the rod-cell equivalence proposed to close it, is disproved (2026-09-30):** the flux target makes the gate worse, the removal-rate target will not converge because a black absorber's reaction rate is nearly invariant to its own SPH factor, and a ±20 % sweep of the rod factors never brings the worth error within −3.45 %. The neighbour fuel constants differ by ±3 % **at zero burnup** — the rod perturbs the spectrum across the whole 75 cm supercell. Carried as a measured one-signed bias unless A8 proves sensitive. |
| Unit 4 channel map, `tools/build_unit4_map.py` | 1661 fuel + 211 rods + 12 ДКЭ(в) + 4 start-up chambers = 1888 positions; 47 rods inserted at 01:22:30, 4346 cm | ✅ Two independent digitisations register exactly (all 223 rod sites at one offset), and every count closes against a separate source — INSAG-7 pp. 43/103, [PAV] Table 1, [D] p. 57. The rod *types* of 32 sites remain an assumption, recorded per row. |
| Kinetics cost, `tools/kin_cost.sh` | `KINSOL:` on the 49×49×32 `DUAL 1 1` core: **0.430 s/step** under a severe transient, 0.090 s/step with a frozen macrolib; max RSS 105 MB | ✅ Per-step cost measured by *differencing* 10-step and 110-step runs, so the fixed setup cancels rather than being estimated. Self-checked two ways: the unperturbed transient holds power to 1.4e-4, and the severe one obeys the prompt-jump relation at step 1 (−0.20 $ for P/P₀ = 0.836 at β = 0.007219). On IAEA PWR constants — this is the solver, not the reactor. |
| CANDU-6 control, `Dragon/data/rbmk_candu.x2m` + `openmc/candu_cell.py` | DRAGON +1624 pcm vs OpenMC +1603 pcm full-void | ✅ Same geometry, library and compositions in both codes; **agree to 22 pcm (1.3 %)**. This is what validates the OpenMC model and localises the RBMK disagreement. |
| Cell volume fractions, analytic vs DRAGON tracking | graphite 89.5938 % vs 89.594 %, coolant 3.7721 % vs 3.772 %, fuel 2.9009 % vs 2.901 % | ✅ Method sound and independent of DRAGON (`openmc/volcheck.py`). **Current geometry (2026-09-24 (3))**: analytic graphite 89.5938, coolant 3.6037, fuel 2.9009, Zr 3.0313, gas 0.8702; DRAGON 89.594 / 3.604 / 2.901 / 3.031 / 0.870. Match to every printed digit again. |

**Retracted claims.** The first three were retracted by the audit; the fourth is a
retraction of the audit's own finding; the fifth is a retraction of the A5 result recorded
one day earlier in this same file.

- ~~"RBMK cell k∞ = 1.030601 (Δ = 8×10⁻⁷)"~~ — `rbmk_cell_iaea_xs.dra` contains no nuclear
  data. It is a hand-typed `MAC:` block of IAEA PWR constants with νΣf raised 0.135→0.160,
  carrying the comment *"tuned for k_inf ~1.03"*, asserted against 1.0306. Graphite was given
  negative implied absorption to hold k above 1. The agreement is a tautology.
- ~~"LMW 2-D kinetics benchmark passed"~~ — the cited file `Donjon/data/lmw_kinetics.x2m`
  **does not exist anywhere on the filesystem**. The only LMW artifact is the stock TRIVAC
  procedure `Trivac/data/Ktests_proc/lmw2D.c2m`, never run as part of this project.
- ~~"3-D core converges, k=0.054, 973 outers"~~ — log says
  `THE MAXIMUM NUMBER OF OUTER ITERATIONS IS REACHED` at 999/1000, then `TEST FAILURE`.
- ~~"Transient framework ready"~~ — all five transient decks abort. `KINSOL:` has never run.
  *(Update 2026-09-30: the retraction stands — those five decks still abort and were never
  fixed. But `KINSOL:` is no longer unrun: `rbmk_kin_probe`/`_ramp`/`_pert` advance 110 time
  steps on the full core. See "Phase 0 of the transient".)*
- ~~"`rbmk_cell_dlib99_v2.x2m`, k∞ = 1.050768, is the only legitimate RBMK physics result in
  the repo"~~ — **wrong, and this one was the audit's own error.** That deck carries the
  CANDU-6 cluster from `twlup_proc/TCWU07.c2m` verbatim: pin radii 0.612/0.654, ring radii
  1.4885 / 2.8755 / 4.3305, 37 pins in four rings, and the 6.5875 cm boundary. It is a CANDU
  bundle at RBMK pitch with 10×-under-dense zirconium and no self-shielding. The number was
  real in the sense that DRAGON computed it; it was not an RBMK.
- ~~"+1957 pcm (~4 β) at 20 MWd/kg — reproduces the historically quoted Chernobyl
  magnitude"~~ — **the agreement was a coincidence.** The deck specifies coolant hydrogen as
  bare `H1`, which is free-gas hydrogen; every bundled reference deck uses `H1_H2O`, the
  bound evaluation, and `DLIB_99` contains both. Correcting that alone raises the fresh-fuel
  full-void worth from +82 to +222 pcm. An independent OpenMC calculation of the same cell
  gives +4007 pcm (~8 β) at 20 MWd/kg. The trend is right; the number that matched history
  was produced by a coolant bug in a code that under-predicts this quantity throughout.

---

## Current state of the RBMK decks

| Area | State |
|---|---|
| Lattice cell, real data | ✅ `rbmk_cell_a3.x2m` — RBMK geometry, `USS:` self-shielded, self-verifying |
| Self-shielding on the cluster | ✅ `USS:` with `SUBG`, separate coarse SS tracking, per-ring sets |
| SPH homogenization | ✅ resolved — **not applicable** to a single-region cell homogenization; belongs at core level |
| 2-group condensation | ✅ `COND 0.625` (eV), `MERG COMP` and `MERG MIX` editions |
| Burnup (`EVO:`) | ✅ 0 → 20 MWd/kg at 16.7 MW/t |
| Void branches | ✅ three densities × seven burnup points |
| MULTICOMPO / SAPHYB / CPO | ⬜ exported once from the CANDU cell (quarantined); **not yet rebuilt** on the corrected cell |
| β_eff, λ from library | ⬜ still never extracted; `NDEL 6` is present and unused. Must be a **burnup curve**, not a scalar — β_eff falls as Pu-239 (β ≈ 0.0021) builds in |
| Doppler / graphite-temp branches | ⬜ axes exist in `RbmkLib` but only coolant density has been swept |
| CPS channel cells (B₄C, displacer, water) | ⬜ none |
| 3-D core | ⬜ generator **fixed** (`PITCH = 25.0 # cm`, 49×49×32, 1225 cm mesh, `MCFD 1`); the corrected deck has **never been run** — that is what A2 now is |
| Transient | ⬜ no time loop in any deck; `KINSOL:` never executed |
| TH coupling | ⬜ `THM:` never called from any RBMK deck |
| Detectors | ⬜ `DETINI:`/`DETECT:` never used |

Deck sprawl: ~86 `rbmk_cell_*` variants were generated, ~10 ever ran, and all of them
carried the same CANDU geometry. The superseded A3/A5 decks and the negative-void
MULTICOMPO are in `quarantine/a5_candu_cell/` with a README.
2 of 19 DONJON RBMK decks ever produced a k_eff; both ≈ 0.05 (the units bug).

---

## Root causes (all fixable, none are capability limits)

1. **The lattice cell was never an RBMK.** Every `rbmk_cell_*` deck inherited the CANDU-6
   cluster from `twlup_proc/TCWU07.c2m` — 37 pins in four rings, a 3.85 cm zirconium
   calandria tube, 45 % graphite where an RBMK has ~90 %. Compounded by zirconium number
   densities 10× below metallic Zr and no self-shielding anywhere. This is what produced the
   negative void coefficient, and nothing in the workflow could have caught it, because no
   deck ever checked its own volume fractions. **Fixed:** `rbmk_cell_a3.x2m` plus an in-deck
   guardrail that aborts if the cell is not an RBMK (negative control verified).

2. **Units bug in the core geometry.** `gen_rbmk_realistic.py` had `PITCH = 0.25  # meters`;
   DONJON `GEO:` mesh coordinates are **centimetres**. The modelled core was
   12.25 cm × 12.25 cm × 7 cm with VOID on all six faces. The XS used give k∞ = 1.12 —
   everything down to 0.054 was leakage. Cross-check: `rbmk_core_3d_simple.don` has a
   different mesh but the same physical size and identical XS → k_eff = 0.060.

   **Corrected 2026-09-23 (record, not code).** The generator was already fixed on 09-22:
   `gen_rbmk_realistic.py:6` reads `PITCH = 25.0  # cm`, `NX,NY,NZ = 49,49,32` with two
   axial reflector planes per end, the emitted deck meshes to 1225 cm, and the solver is
   already `MCFD 1` (`rbmk_core_3d_realistic.don:1691`). What is actually open is that
   **the corrected deck has never been run**: its `.result` is dated 09-19, three days
   older than the deck — standing rule 5, caught by its own rule. Two further live defects:
   `rbmk_core_3d_realistic.don:1710` carried `assertS ... 'K-EFFECTIVE' 1 1.123062`, and
   `gen_rbmk_donjon.py:10`, `gen_rbmk_geo.py:8`, `gen_rbmk_simple.py:6` still carry PITCH
   in metres.

   *Correction, same day:* I first read that assert as a target inherited from a
   differently-sized core, on the strength of the timestamp gap. **That was wrong.** Running
   the deck reproduces 1.123062 exactly, so it came from a run of this very deck — one that
   left no `.result` behind. The deck had therefore been run on 09-22; only the evidence was
   missing. Removing the assert was still right, for the other reason: the workplan requires
   A2 to *report* k_eff, not to expect one, and a target taken from the answer you got is not
   a gate. But "never been run" overstated what the timestamps could show.

3. **Errors misread as tool limitations.** Three separate "blockers" were ordinary input
   mistakes, each demonstrated correctly in a bundled reference deck: the missing
   `SEQ_BINARY` tracking declaration for SPH (`SPH.F:140`, `SPH.F:239`; pattern in
   `twimsE_proc/TCWE13.c2m`), a 13-character procedure name against GANLIB's 12-character
   limit (`objstk.c:189`), and `DELETE X ;` instead of `X := DELETE: X ;`
   (`rep900_mco.x2m:409`). Each was reported as a defect in DRAGON.

4. **The right reference deck was copied for the wrong thing.** `TCWU07.c2m` was used as a
   *geometry* template — which is precisely what should not have been copied, since a CANDU
   channel and an RBMK channel differ in exactly the moderator arrangement that matters.
   Its actually transferable content — `SHI:`/`USS:` self-shielding, the coarse-SS /
   refined-transport two-geometry pattern, and side-by-side void branches — was ignored.
   (The audit stated these decks "were never used." That was wrong: the geometry was taken
   verbatim and the methodology was not.)

---

## Toolchain capability (confirmed present; `USS:` and `EVO:` now in use, the rest not yet)

| Need | Module | Note |
|---|---|---|
| Space-time kinetics | `INIKIN:` / `KINSOL:` (in Trivac) | θ-method; no improved-quasi-static. `TRIVAA:` needs `UNIT`. |
| Transient TH | `THM:` → `THMTRS.f` | 1-D per channel — correct topology for RBMK pressure tubes |
| Void / boiling | `THMDFM.f90`, `BOWR`/`SAHA` | ⚠ **transient path is HEM-only**: `THMTRS.f:157` hardcodes `IDFM=0` and `THM.f:1102` passes neither `IPRES` nor `IDFM`. Drift-flux is steady-state only. |
| XS feedback | `NCR:` + `COMPO:` | up to 10 dimensions, linear or cubic Ceschino, plus `ADD` delta-sigma branches |
| Graphite displacer + absorber | `DEVINI:` / `DEVGET.f` | up to 10 contiguous rod **parts**, each with its own `DMIX` pair; volume-weighted partial insertion |
| Rod motion | `DSET:` (level) or `MOVDEV:` (speed) | ⚠ **`MOVDEV:` is broken for multi-part rods**: `DEVGET.f:246` stores `6*NPART` positions, `MOVPOS.f:159` / `MOVGRP.f:175` store only `6`, `NEWMDV.f:97` reads all `NPART`. No bundled deck calls `MOVDEV:`. Use `DSET:` with a computed level. |
| | | ⚠ `NEWMDV.f:92` skips any rod with `LEVEL < 1e-4` — cannot represent "displacer parked, absorber out", i.e. the pre-scram configuration. Put the parked displacer in the base fuel map and let the device carry only the difference. |
| Xenon | `XENON:` / `XENCAL.f` | **equilibrium only** — no iodine inventory, no post-shutdown build-up. Fine for a 4 s transient; matters for the pre-accident state. Add Xe as an explicit COMPO axis. |
| Detectors | `DETINI:` / `DETECT:` | probe positions + PARAB/SPLINE flux interpolation; **no detector response model** — add SPND lag downstream |
| Point kinetics | `PKINI:` / `PKINS:` / `PKIRHO.f` | Runge-Kutta + `ALPHA` feedback tables + `PTIME` rod law; ms/step but amplitude only |

**Reference decks to copy from:** `Dragon/data/rep900_mco.x2m` (multi-parameter COMPO;
also the canonical `X := DELETE: X ;` and procedure-per-branch idioms),
`Dragon/data/pincell_mco.x2m` (depletion + density branches + COMPO, the pattern `rbmk_a5_void.x2m` follows),
`Dragon/data/twimsE_proc/TCWE13.c2m` (NXT + `SEQ_BINARY` + SPH),
`Dragon/data/twlup_proc/TCWU07.c2m` — **methodology only.** Copy its two-geometry
self-shielding pattern and its void branches; do **not** copy its geometry. Taking the
CANDU cluster verbatim is the single error this project spent the most time on.
`Donjon/data/channel_mphy.x2m` (THM ↔ NCR ↔ KINSOL loop),
`Donjon/data/AFMtest.x2m` (3-D core + moving devices + kinetics, `MCFD 1`),
`Donjon/data/pulseTHM_0d.x2m` (PKINS + THM, adaptive dt).

---

## Performance

| Run | Discretization | Unknowns/group | FLUD CPU |
|---|---|---|---|
| `rbmk_core_3d_realistic.don` 49×49×28 | `DUAL 3 3` | 2,683,917 | **729 s** (did not converge) |
| `rbmk_core_3d_simple.don` 25×25×14 | `DUAL 3 3` | 484,425 | 23 s |

`DUAL 3 3` is ~40 unknowns per node. **`MCFD 1`** is the documented default (and what
`AFMtest_proc/Pcalflu.c2m:45` uses for a real 3-D core) at ~1 unknown per node — a ~40× smaller problem.
Expected with `MCFD 1` at 49×49×28, 2 groups: steady solve order 5–30 s, one `KINSOL:` step
order 0.2–3 s, a 20 s AZ-5 transient at Δt = 10 ms in tens of minutes to a few hours.
Also loosen `EPSOUT` from 1e-7 (absurd for a transient step) to 1e-5.

Memory is never a constraint: largest solve used ~1.4 GB against a ~110 GB budget.

---

## Validation risk

**This is the open problem.** There is no open RBMK benchmark of IAEA-3D quality. The
previously cited "Kozlowski RBMK benchmarks" appears to be a misattribution — Kozlowski &
Downar authored the OECD/NEA **PWR MOX/UO₂** transient benchmark. Verify before relying on it.

Twice now the project has produced a confident, plausible, wrong result — the tuned `MAC:`
block, and then a CANDU bundle reported as an RBMK channel — and both passed every check
that existed at the time. The corrected cell is internally consistent and reproduces the
right void behaviour, but *internally consistent* is exactly what the previous two were.

Checks now in place:

| Check | Status |
|---|---|
| In-deck volume fractions, with a verified negative control | ✅ `rbmk_cell_a3.x2m` |
| Graphite mass: 11.4 cm bore on 25 cm pitch, ~2000 bored columns, 1.65 g/cm³ → 1763 t vs published ~1700 t | ✅ agrees to 4 % |
| Void coefficient **sign and burnup trend** | ✅ confirmed independently by OpenMC |
| Void coefficient **magnitude** | ❌ **not confirmed — the two codes differ by 2–12×** |
| Independent Monte Carlo | ✅ done 2026-09-23, see below |
| Cell geometry, analytic vs DRAGON tracking volumes | ✅ match to every printed digit — but see below, the DRAGON side is now stale |
| Method validated on a non-RBMK lattice (CANDU-6, both codes) | ✅ agree to 22 pcm on the void coefficient |
| Cell dimensions against a primary design source | ✅ 2026-09-24, Dollezhal & Emelyanov (1980) — two corrections found, one confirmation |
| Every cell dimension sourced, with published clearances and mass as checks | ✅ 2026-09-24 (3) — see `sources/README.md`. Clad-to-wall gap 2.21 mm vs published 2.2; U per assembly 115.3 vs 114.7 kg |

**OpenMC status: WORKING.** The earlier note that conda-forge has no linux-aarch64 build was
correct, but a source build already existed at `~/code/openmc` (v0.16.1-dev46) with the
binary installed and only the Python bindings and data missing. Both are now in place:

- venv at `.venv-openmc` (Python 3.12), package installed from the source tree
- `~/nucdata/endfb-viii.0-hdf5` and `~/nucdata/endfb-viii.1-hdf5`, plus the VIII.0 chain
- **VIII.1 is the one to use** — `DLIB_99` is `draglibendfb8r1Apolib99_v5p1`, i.e. the same
  ENDF/B-VIII.1 evaluation, so the comparison isolates method rather than data
- run with `OPENMC_CROSS_SECTIONS=~/nucdata/endfb-viii.1-hdf5/cross_sections.xml`
- cost: ~80 k particles/s on 20 threads, **peak RSS 879 MB** for the fresh cell (1.6 GB
  depleted). No GPU use, no memory risk on the ~110 GB budget.

Open geometry questions that an MC cross-check would not settle either — these need a
primary source. **Items 1 and 3 were resolved 2026-09-24 against Dollezhal & Emelyanov
(1980); see "Cell geometry pinned to a primary source" below. Items 2 and 3b were resolved
2026-09-24 (3); see "Cell geometry closed" below. Item 4 was never geometry and was measured
on 2026-09-23 (A5b). No geometry question remains open.**

1. ~~**Pressure tube 88 × 4 mm vs 92 × 4 mm.**~~ **RESOLVED: 88 × 4 is correct**, stated
   explicitly as *outer* diameter 88 with a 4 mm wall [D p.54]. The deck already had it.
   The Wikipedia "8.4 cm ID" reading is wrong. Guardrail tightened to reject 92 × 4.
2. ~~**Fuel rod ring radii 1.60 / 3.10 cm**~~ **RESOLVED 2026-09-24 (3): correct as they
   were.** Rod circles ⌀32 / ⌀62 mm in [RU-A] and [LEI05]. The earlier measurement off
   fig 5.1 (inner 17–18 mm) was wrong. Refusing to substitute it was the right call.
3. ~~**Carrier rod wall** — only the 13 mm OD is sourced.~~ **RESOLVED, and the deck was
   wrong**: a 15 × 1.25 mm central tube with a solid 12 mm carrier rod inside [D p.11],
   not a 13 mm hollow tube. Corrected. The fuel clad was wrong too (13.5 × 0.9, not
   13.6 × 0.825).
3b. ~~**Pellet central hole (2 mm)**~~ **RESOLVED 2026-09-24 (3): the hole is real.**
   [RU-A], [LEI05], [BIB], plus the Unit 4 uranium-mass check.
4. ~~**β_eff**~~ **MEASURED 2026-09-23** as a burnup curve (A5b, below). It needs re-running
   on the current geometry, like everything downstream. Original note: assumed 0.0048 for the β-equivalent column. The library carries `NDEL 6`
   delayed data and it has never been extracted. It must come out as a **burnup curve**,
   not a scalar: β_eff falls as Pu-239 (β ≈ 0.0021) displaces U-235 (β ≈ 0.0065), so the
   void worth in dollars grows twice over with burnup — numerator up, denominator down.
   `TIER_A_WORKPLAN.md`'s gate of 0.0065–0.0075 is a fresh-fuel figure and is wrong for
   the state that matters. An independent check is cheap: OpenMC gives β_eff ≈ 1 − k_p/k
   by re-running with `settings.create_delayed_neutrons = False`.

---

## A3 rebuild and A5 void coefficient — 2026-09-22

The delegated agent's A5 report claimed a parse-time blocker in the GAN parser.
That diagnosis was wrong; the real problem was upstream in A3. Both are now fixed
and the cell reproduces RBMK void behaviour.

### The claimed A5 blocker was three syntax errors (retracted)

| Claimed | Actual cause |
|---|---|
| "GAN parser validates PROCEDURE names at parse time" | `MakeBranchLib` is **13 characters**; GANLIB caps names at 12 (`Ganlib/src/objstk.c:189`). Renaming to `MkBranchLib` cleared it. |
| "`rep900_mco.x2m` uses built-in PROCEDUREs" | False. `Mix_UOX_32` is a plain user `.c2m` in `rep900_mco_proc/`, copied by `rdragon:102` exactly like ours. |
| `DELETE LIBRARY` → not declared | Missing colon and missing assignment. The idiom is `X := DELETE: X ;` (`rep900_mco.x2m:409`). |
| `LINKED_LIST ALREADY EXISTS` | Same fix; the reference deck reassigns `LIBRARY` five times, deleting between each. |

Also: a stale extensionless `data/rbmk_cell_v3_branch` shadowed the `.x2m`, because
`rdragon` copies the **bare argument** (`rdragon:99`). Always pass `.x2m`.

After those fixes the old deck ran 7/7 branches and exported an 11 MB MULTICOMPO —
carrying a void coefficient of **−183 to −621 pcm/%void**. Wrong sign, two orders
of magnitude out. The mechanics worked; the cell was not an RBMK.

### Root cause: the lattice cell was a CANDU-6 bundle

`rbmk_cell_v3.x2m` was `twlup_proc/TCWU07.c2m` with the outer square resized — same
pin radii (0.6122/0.6540), same ring radii (1.4885/2.8755/4.3305), same mixture
numbering. Measured region volumes showed:

- a **3.85 cm solid zirconium "calandria tube"** at 32.9 % of the cell — an RBMK has
  graphite rings there, not a calandria tube
- **37 pins in 4 rings** (1+6+12+18), a CANDU-37 bundle; RBMK has **18 rods in 2 rings**
- graphite 45.2 % where it should be ~90 %; water 9.2 % where it should be ~3.8 %
- **every zirconium mixture at 4.3E-3 /b-cm, a factor of 10 below metallic Zr**
- **no self-shielding anywhere** — no `USS:`/`SHI:` in any file, so all resonance
  absorption was at infinite dilution
- SPH computed and discarded; the COMPO call passed the SPH edit into the *group
  form factor* slot (`COMCAL.f:24`), which the run confirms was ignored (`NGFF 0`)

### A3 rebuilt: `rbmk_cell_a3.x2m`

Geometry from the Wikipedia RBMK article (fetched 2026-09-22): 250 mm pitch,
114 mm graphite bore, graphite split rings, 18 rods of 13.6 mm OD with 11.5 mm
pellets and a 2 mm central hole, 13 mm carrier rod, 2.0 wt% U-235 (the April 1986
Chernobyl loading — the old deck was at 2.36 wt%, the later upgrade).

Independent confirmation of pitch, bore and graphite density: a 11.4 cm bore on a
25 cm pitch leaves 83.7 % block graphite; with ~2000 bored columns in the 14 m
stack that is ~86.8 % stack-average, and at 1.65 g/cm³ gives 1763 t against the
published ~1700 t. Agreement to 4 %.

Materials now live in one place, `rbmk_proc/RbmkLib.c2m`, shared by both decks —
the old deck kept two copies of the `LIB:` block and they disagreed about whether
the coolant-density argument was absolute or relative, which silently mislabelled
every point on the void axis.

Added `USS:` self-shielding (needs `SUBG` in `LIB:`) on a separate coarse tracking.

**Result: k∞ = 1.310172**, self-shielded, 2 groups, cut at 0.625 eV.
*(1.312816 as originally run, with free-gas hydrogen — corrected 2026-09-23.)*

### Volume-fraction guardrail (new, and the point of the exercise)

The deck now measures what it built and aborts if it is not an RBMK:

| | measured | design |
|---|---|---|
| cell area | 625.0001 cm² | 625.0 |
| graphite | 89.594 % | 89.6 |
| coolant | 3.772 % | 3.77 |
| fuel | 2.901 % | 2.90 |
| zirconium | 2.729 % | 2.73 |
| gas | 1.004 % | 1.00 |

Negative control run: replacing the graphite rings with zirconium (the CANDU
failure mode) drops graphite to 83.7 % and raises Zr to 8.65 %, and the deck
aborts with `FAIL: graphite fraction too low -- this is not an RBMK cell`.
**The guardrail fires.** This check costs nothing and would have caught the CANDU
bundle in one run instead of six branch calculations later.

### SPH: task A4 was aimed at the wrong place

`SPH: EDIHOM ...` → `SPHDRV: INVALID NUMBER OF MACRO-REGIONS (9 1)`. SPH needs one
homogenized region per tracking macro-region, so it **cannot** be applied to a
full-cell (`MERG COMP`) homogenization at all. For the DONJON model — one node per
channel — the `MERG COMP` edition is used directly and needs no SPH: flux-volume
weighting under reflective boundaries already preserves k∞ exactly. SPH belongs at
the **core** level, for the graphite reflector and control-rod cells. The original
"Stage 4 SPH blocker" was chasing a correction that step does not need.

### A5: void coefficient vs burnup — `rbmk_a5_void.x2m`

The A5 gate as written (positive void coefficient at zero burnup) tests the wrong
state. The RBMK's positive void coefficient is a high-burnup phenomenon — it needs
the Pu-239 inventory whose 0.3 eV fission resonance makes spectrum hardening
reactivity-positive. Depletion (`EVO:`, never previously run) now precedes the gate.

Specific power 16.7 MW/t (3200 MWth / 192 t U). Self-shielding redone at every
branch, since voiding hardens the spectrum into exactly the resonances `USS:` treats.

| BU (MWd/kg) | k∞ | Δρ at 51 % void | Δρ at 97 % void | ≈ β |
|---|---|---|---|---|
| 0.0 | 1.3128 | +226 pcm | +82 pcm | +0.17 |   <!-- pre-fix, free-gas H -->
| 0.5 | 1.2590 | +250 pcm | +193 pcm | +0.40 |
| 2.0 | 1.2368 | +202 pcm | +103 pcm | +0.21 |
| 5.0 | 1.1855 | +128 pcm | −11 pcm | −0.02 |
| 10.0 | 1.0987 | +200 pcm | +304 pcm | +0.63 |
| 15.0 | 1.0118 | +435 pcm | +986 pcm | +2.05 |
| 20.0 | 0.9282 | +787 pcm | **+1957 pcm** | **+4.08** |

(β-equivalent at β_eff ≈ 0.0048, assumed — β must still be taken from the library's
`NDEL 6` data, which has never been extracted.)

**Positive, and growing with burnup.** At design discharge burnup the full-void
worth is ~4 β, which is the figure historically quoted for Chernobyl conditions.
The near-zero dip around 5 MWd/kg is the U-235/Pu-239 crossover region; it looks
physical but is not yet understood in detail and is worth confirming.

> **SUPERSEDED 2026-09-23.** The sign and the growth with burnup hold up. The two
> specific claims in this paragraph do not. OpenMC gives ~8 β at 20 MWd/kg, not ~4,
> so the match to the historical figure was a coincidence produced by the free-gas
> hydrogen bug. And the 5 MWd/kg dip is *not* physical — it was worth confirming, it
> was confirmed, and it failed: OpenMC gives +852 pcm there, not −10. See the OpenMC
> cross-check section.

**The A5 gate in `PROJECT_PLAN.md` said +2 to +5 pcm/%void. That number was mine and
it was too low** — the RBMK full-void worth is several β, i.e. tens of pcm/%void.
Corrected in the plan.

### What this does not yet establish

*(Superseded in part by the OpenMC cross-check below — the first bullet is now done, and it
overturned the A5 magnitude.)*

- ~~**No independent cross-check.**~~ Done 2026-09-23. It confirmed the geometry and the
  void trend and contradicted the magnitude by ~2×. See "OpenMC cross-check".
- **Pressure tube dimension unresolved**: 88 × 4 mm used; the source states 8.4 cm ID
  (i.e. 92 × 4). Changes coolant area by 10 %. One constant in `rbmk_cell_a3.x2m`.
- **Fuel rod ring radii (1.60 / 3.10 cm) are inferred**, not sourced.
- Single cell, no absorber, no leakage. Core void coefficient depends strongly on
  rods inserted (the ORM) — that is A6.
- β_eff still assumed rather than taken from the library.
- No MULTICOMPO exported yet from the corrected cell.

### Status

| Task | Was | Now |
|---|---|---|
| A3 lattice cell | "done" — was a CANDU bundle | **rebuilt, self-verifying, k∞ = 1.310172** (1.3128 before the hydrogen fix) |
| A4 SPH | "blocked", then "done" but discarded | **not applicable at cell level** — moved to core level |
| A5 void gate | "blocked" by a 13-character name | **sign and trend pass; magnitude contradicted by OpenMC (2026-09-23)** |
| A5 MULTICOMPO export | exported from the wrong cell | to redo on the corrected cell — and see the cross-check first |

---

## OpenMC cross-check — 2026-09-23

The first independent check of any RBMK physics in this project. Method: rebuild the same
cell in OpenMC from the *same* number densities and dimensions the DRAGON decks use, run it
in continuous energy on the same ENDF/B-VIII.1 evaluation, and compare. Files under
`openmc/`: `rbmk_cell.py`, `volcheck.py`, `rates.py`, `deplete_void.py`, `compare_bu.py`,
`candu_common.py`, `candu_cell.py`.

### What was confirmed

**The geometry is right.** `openmc/volcheck.py` computes the cell volume fractions
analytically, with no DRAGON involvement, and they match DRAGON's `MIXTURESVOL` to every
printed digit: graphite 89.5938 vs 89.594 %, coolant 3.7721 vs 3.772 %, fuel 2.9009 vs
2.901 %, Zr 2.7292 vs 2.729 %, gas 1.0040 vs 1.004 %. All 18 rod clearances are positive
(1.4–2.7 mm). The implied heavy-metal density is 9.167 g/cm³ — exactly 10.4 g/cm³ UO₂.

**The positive void coefficient rising with burnup is real.** Both codes give it, in both
sign and trend, over the whole burnup range.

### What was not confirmed: the magnitude

Full-void reactivity (dca 0.72 → 0.02 g/cm³):

| BU (MWd/t) | OpenMC | DRAGON | ratio |
|---|---|---|---|
| 0 | +1030 ± 66 | +82 | 12.5× |
| 2000 | +919 ± 81 | +103 | 9.0× |
| 5000 | +852 ± 79 | **−10** | sign differs |
| 10000 | +1473 ± 92 | +303 | 4.9× |
| 15000 | +2650 ± 121 | +985 | 2.7× |
| **20000** | **+4007 ± 117** | **+1951** | **2.1×** |

At 20 MWd/kg that is **~8 β vs ~4 β** (β = 0.0048 assumed, same for both, so the ratio is
unaffected). DRAGON's dip to −10 pcm at 5000 MWd/t is not reproduced at all.

A dedicated high-statistics fresh-fuel sweep (100 M active particles/point) gives the same
picture more precisely: k∞ = 1.319690 ± 0.000139 nominal, void +578 pcm at 51.4 % and
+912 pcm at 97.2 %, against DRAGON's +264 and +222 with bound hydrogen.

### The one real bug: free-gas coolant hydrogen

`rbmk_proc/RbmkLib.c2m` specifies coolant hydrogen as bare `H1`. That is **free-gas**
hydrogen with no bound-water thermal scattering. Every bundled reference deck in the
distribution (`twlup_proc/`, `rep900_mco_proc/`) uses `H1_H2O`, and `DLIB_99` contains both.
Free-gas hydrogen overstates water's moderating power, which suppresses the positive void
coefficient — the right direction, but only part of the size.

Measured with `rbmk_h2otest.x2m` (both treatments, nothing else changed; the free-gas branch
reproduces `rbmk_a5_void.x2m` exactly, which validates the test):

| | k∞ nominal | void 51.4 % | void 97.2 % |
|---|---|---|---|
| `H1` free gas (as written) | 1.312816 | +226 | +82 |
| `H1_H2O` bound | 1.310172 | +264 | +222 |

**FIXED 2026-09-23.** `RbmkLib.c2m:44` now reads `H1_H2O = H1_H2O <<nH1>>`, and
`rbmk_cell_a3.x2m` re-run from a deleted `.result` returns **k∞ = 1.310172** — the value
the table above had already measured independently, so this is a regression check rather
than a new claim. The volume-fraction guardrail still passes (89.594 / 3.772 / 2.901 %).

`RbmkLibH.c2m` is **retired**: keeping the fix in a second file was the duplication that
let A3 and A5 keep running the wrong composition for a day. There is one source of truth
again. The old free-gas composition is preserved as `RbmkLibF.c2m`, marked do-not-use,
solely so `rbmk_h2otest.x2m` still reproduces this comparison; every other diagnostic deck
now calls `RbmkLib`. `RbmkLibN`/`RbmkLibW` remain, with their headers corrected to say what
they actually vary (`CTRA NONE` / `CTRA WIMS`, not the hydrogen treatment).

**Everything computed with DRAGON before this date used free-gas hydrogen**, including the
A5 void-vs-burnup table below and the DRAGON column of the OpenMC comparison. Those numbers
have not been re-run; the ~+140 pcm correction at full void is a floor on how much they
move, and the direction is toward OpenMC.

### Everything else was eliminated by measurement

| candidate | verdict |
|---|---|
| geometry, composition | match to 4+ digits — not it |
| nuclear data VIII.0 vs VIII.1 | 37 pcm on k∞ — not it |
| `GRMIN 18` vs library default | **bit-identical** — not a bug, contrary to first suspicion |
| `USS:` options (`TRAN PASS 4 NOCO`) | < 0.5 pcm — not it |
| transport correction `CTRA APOL`→`NONE`/`WIMS` | +76 pcm — real but small |
| free-gas `H1` | +140 pcm — real, 17 % of the gap |
| group structure (SHEM-361) | **untestable** — `USS:` will not converge on this cell at 361 groups under any option tried |

Running account of the fresh-fuel full-void worth: +82 (as written) → +222 (bound H) → +299
(CTRA NONE) → OpenMC +912. **614 pcm, 74 % of the gap, was not reached by anything tested.**

> **Qualified 2026-09-23.** The original wording — "not reachable from the deck" — claimed
> more than the evidence. Every candidate in the table above is a **data or library**
> option. Nothing tested discretization or self-shielding geometry, and four such knobs are
> untested, all of which bite harder in a voided channel than a flooded one, which is the
> signature this disagreement has:
>
> - `USS:` runs on the **unsplit** geometry `GEOSS`, so the pellet is flat — there is no
>   radial self-shielding profile. Splitting the pellet for self-shielding is standard
>   practice and is worth hundreds of pcm.
> - Tracking is coarse: `TISO 8 15.0` for self-shielding, `TISO 15 30.0` for flux, with
>   `SPLITR 4 1 1 2 6`. A voided channel is nearly transparent, and flat-flux collision
>   probability on coarse regions gets streaming wrong exactly there.
> - Every Zr isotope in MIX 2/8/9 is at **infinite dilution** — no self-shielding set.
>   That overestimates Zr resonance absorption, and the error grows as voiding pushes flux
>   into those resonances. Right direction; probably small (Zr RI ~1 b vs U-238 ~275 b).
> - `ANIS 2` (P1) only.
>
> The highest-information test is none of these: a **172-group spectrum and per-nuclide
> reaction-rate comparison** against OpenMC. The 2-group comparison cannot see the cause.
> Both codes agree the thermal fraction goes 53.0 → 46.3 % yet disagree on the *sign* of the
> U-235 production change, so the difference is in spectrum *shape* — most likely 0.2–5 eV,
> where U-235 has low-lying resonances and, at burnup, Pu-239 has its 0.3 eV resonance.
>
> **Deferred by decision**, not by impossibility. The trigger to pick it up is A8 showing
> that the two bracketed cross-section sets give materially different transients.

### Where the disagreement actually lives

k = ν-fission / absorption, so the void effect decomposes exactly. Of the 0.880 pp
difference in the k-ratio on voiding, ν-fission contributes +0.906 pp and absorption −0.026.
Splitting the production term by nuclide:

| | share | DRAGON | OpenMC | diff |
|---|---|---|---|---|
| U-235 | 0.969 | −0.200 pp | +0.746 pp | **+0.946** |
| U-238 | 0.031 | +0.494 pp | +0.452 pp | −0.042 |

**The entire disagreement is U-235 fission production under spectral hardening.** When the
coolant goes, DRAGON says U-235 production *falls* 0.20 %; OpenMC says it *rises* 0.75 %.
Both codes harden the spectrum identically (thermal flux fraction 53.0 → 46.3 %); they
disagree on whether the epithermal U-235 fission gain beats the thermal loss. Since U-235 is
97 % of production, that one sign disagreement is the whole void coefficient.

Why this is so sensitive: voiding removes 4.9 % of all absorption with the water (worth
+3793 pcm on its own), and U-238 resonance capture grows back nearly all of it — total
absorption moves only 1.000477 → 1.000737. **The void coefficient is a few-hundred-pcm
residual between ~3800 pcm terms.** A 20 % method difference in the cancellation becomes a
4× difference in the answer.

### The CANDU-6 control — why the OpenMC model can be trusted

The obvious objection is that the OpenMC model is simply wrong. `twlup_proc/TCWU07.c2m` is
the bundled CANDU-6 cell: cluster-in-channel geometry, non-light-water moderator, low
enrichment, positive void coefficient — the same *kind* of problem, different reactor. It was
run in both codes on `DLIB_99`, with compositions generated for both from one source
(`openmc/candu_common.py` → `rbmk_proc/CanduLib.c2m`) so a transcription error cancels.

| | DRAGON | OpenMC | diff |
|---|---|---|---|
| k∞ nominal | 1.124669 | 1.125691 | +81 pcm |
| k∞ voided | 1.145597 | 1.146371 | +59 pcm |
| **void reactivity** | **+1624** | **+1603** | **−22 pcm (−1.3 %)** |

Compare the RBMK: +550 pcm on k∞ and +690 pcm (+310 %) on the void coefficient. The same
OpenMC methodology reproduces DRAGON's CANDU void coefficient to 1.3 %. **The RBMK
disagreement is specific to the RBMK lattice**, not an artifact of the comparison.

### Caveats on this cross-check

- **The depletion trajectories diverge.** OpenMC k∞ is +268 pcm above DRAGON at 5000 MWd/t
  but −2084 pcm below at 20000. Different chains, fission yields and Q-value normalisation,
  and OpenMC used the VIII.0 chain (no VIII.1 chain is published) with VIII.1 transport data.
  So at discharge the two codes are not at the same core state, and the 2.1× ratio there is
  less clean than the 12.5× at fresh fuel, where compositions are identical by construction.
- **Neither code is established as right.** The CANDU control shows OpenMC is not
  misconfigured, which makes DRAGON the more likely source of the RBMK error, but that is an
  inference, not a measurement. Settling it needs a third code or an experiment.
- β_eff is still assumed 0.0048, not extracted from the library's `NDEL 6` data.
- Single cell, no absorbers, no leakage. The *core* void coefficient depends strongly on rod
  insertion (the ORM) — that is A6, and it is where the accident conditions actually live.
- The steam at 0.02 g/cm³ is treated with liquid-water thermal scattering in both codes
  (`H1_H2O` / `c_H_in_H2O`). Shared approximation, cancels in the comparison, wrong in both.


---

## A5b — the MULTICOMPO — 2026-09-23

`Dragon/data/rbmk_a5b_compo.x2m` → `Dragon/compo/_ACompo`.

**This closes the structural gap.** Until now nothing in the project had ever written cross
sections to disk: every good cell calculation left its result in an in-memory LCM directory
that `END:` discarded, and the DONJON core decks ran on generic IAEA 2-group PWR constants.
The lattice work and the core work were not connected at all.

### Axes

| axis | type | values |
|---|---|---|
| `burnup` | `IRRA` | 0, 2, 5, 10, 15, 20 MWd/kg at 16.7 MW/t |
| `DCA` | `VALU REAL` | 0.72, 0.60, 0.45, 0.30, 0.15, 0.05, 0.02 g/cm³ — the void axis |
| `TF` | `TEMP LIBRARY 6` | 600, 900, 1200, 1500, 2000 K — Doppler |
| `TG` | `TEMP LIBRARY 5` | 500, 750, 900 K — graphite is 89.6 % of the cell |

Full tensor product: **630 branch points**, each a fresh `LIB:` → isotopic restore → `USS:`
→ `ASM:` → `FLU:` → `EDI:` → `COMPO:`. Self-shielding is redone at every point, which is not
optional: voiding hardens the spectrum into the U-238 resonances, which is exactly where
self-shielding acts.

Xe is deliberately **not** an axis yet. `XENON:` in DONJON gives equilibrium xenon only, so an
explicit Xe axis is needed for the ORM story, but it multiplies the grid by ~4. That is
A5b.2, after the four-axis file is proven in DONJON.

### The gate is the round trip, not the file

"A COMPO exists on disk" is not evidence of anything. `Donjon/data/rbmk_a5b_verify.don` closes
the loop: it reads `_ACompo`, interpolates at an exact grid point with `NCR:`, and solves a
single homogeneous 25 cm cube with reflective boundaries on all six faces — no leakage, so the
diffusion eigenvalue reduces exactly to k∞.

| | k∞ |
|---|---|
| DRAGON, 172-group transport | 1.310173 |
| DONJON, via COMPO → `NCR:` → `TRIVAA:` → `FLUD:` | **1.310166** |
| difference | **0.4 pcm** |

Condensation, homogenisation, the on-disk database and the interpolation together lose under
half a pcm **at this one point**. That is the corner of the grid and it turned out to be the
best case by a factor of 16 — see the eight-node sweep below, where the worst case is 6.4 pcm.
Writing this deck **before** the long run is what caught the two defects below; both would
otherwise have surfaced after two hours of CPU as an unusable artifact.

### Two non-obvious requirements, both found by the verification deck

1. **`EDI: ... GOLVER` is not sufficient to get diffusion coefficients into a COMPO.**
   `EDIPXS.f:344` writes a `DIFF` block under `GOLVER`, but the state-vector flag that
   `COMPO:` checks is set only under a *leakage model* (`EDIPXS.f:413-419` sets `IDATA(9)`;
   `COMACR.f:91,169` reads it). So with `GOLVER` alone the coefficients are computed and then
   silently dropped, and DONJON stops at `TRISYS: NO DIFFUSION COEFFICIENTS` — a COMPO that
   exists but cannot be solved with.

2. **The fix is a leakage model at zero buckling**: `FLU: ... TYPE K B1 SIGS BUCK 0.0`.
   That activates the B1 machinery without perturbing the spectrum. Checked, not assumed:
   k∞ came out 1.310173 against 1.310172 for plain `TYPE K`, a 1e-6 difference at the
   convergence tolerance. A critical-buckling search (`TYPE B B1`, as the bundled
   `rep900_mco_proc/CalcFlux.c2m:87` uses) would instead reweight the spectrum for ~24 %
   leakage, which is wrong for a channel inside a 12.25 m core whose real geometric buckling
   is ~3 × 10⁻⁵ cm⁻².

### Supporting work

- **`rdragon` discards everything but the `.result`.** The deck ran, wrote `_ACompo` into the
  scratch directory, and the scratch directory was deleted — the in-memory failure mode, one
  step later. `data/<deck>.save` is the documented hook (`rdragon:137-143`); `_ACompo` now
  lands in `Dragon/compo/`, deliberately not in `Linux_aarch64/`, which is treated as
  disposable.
- **The `MICR` list is 31 nuclides, and it was derived, not recalled.** `MICR ALL` would carry
  all 299 depleting isotopes at all 630 points. Every name was first verified to exist in the
  DLIB_99 chain (`rbmk_chainprobe.x2m`), then the list was closed under `EDI:`'s own lumping
  rule by driving `rbmk_micrprobe.x2m` to a fixed point: `EDILUM.f:230-254` refuses to lump
  any isotope whose maximum fission yield exceeds 1 % and which is stable or has a half-life
  over 30 days. `Ru103` is the only one that rule adds beyond the physically-motivated list.
- **`LAMBDA-D` is present and carries real library data** — the six decay constants are
  0.013336, 0.032739, 0.120780, 0.302780, 0.849490, 2.85300 s⁻¹, read from `NDEL 6`, not
  hardcoded. `INIKIN:` needs this and will find it.

### The full run, and what it is actually worth — 2026-09-23 (3)

The 630-point run completed in **1 h 21 min** (4881 s CPU, single thread, peak RSS well under
1 GB — no GPU, nothing near the 110 GB ceiling). `compo/_ACompo` is 113.9 MB, all 630
`A5BTAB` rows present, no aborts and no non-convergence in the listing.

"A COMPO exists on disk" is still not evidence of anything, so three separate checks were run
against the *full* database rather than the 4-point smoke one.

**1. Round trip, at grid nodes spanning every axis.** `rbmk_a5b_sweep.don` interpolates at
eight nodes — including all four axis extremes at once — and solves the same homogeneous
reflective cube. Against the DRAGON 172-group transport values from the same run:

| BU | dca | TF | TG | DRAGON | DONJON via COMPO | delta, pcm |
|---|---|---|---|---|---|---|
| 0 | 0.72 | 900 | 750 | 1.310173 | 1.310166 | -0.4 |
| 20000 | 0.02 | 2000 | 900 | 0.950288 | 0.950330 | +4.7 |
| 10000 | 0.30 | 1200 | 750 | 1.094708 | 1.094746 | +3.2 |
| 5000 | 0.72 | 600 | 500 | 1.175726 | 1.175756 | +2.2 |
| 15000 | 0.15 | 1500 | 900 | 1.020717 | 1.020745 | +2.7 |
| 2000 | 0.45 | 900 | 500 | 1.228206 | 1.228303 | +6.4 |
| 20000 | 0.72 | 600 | 900 | 0.940046 | 0.940085 | +4.4 |
| 0 | 0.02 | 2000 | 500 | 1.296603 | 1.296600 | -0.2 |

**Worst case 6.4 pcm.** The 0.4 pcm figure recorded earlier was the corner point only, and was
optimistic by a factor of 16; condensation + homogenisation + disk + interpolation cost about
6 pcm, not half of one. Still two orders below the physics uncertainties here.

**2. Off-grid interpolation.** The transient will never land on a grid node, so `LINEAR`
interpolation error is the number that matters. `rbmk_a5b_offgrid.x2m` runs DRAGON at eight
points with DCA, TF and TG all at axis *midpoints*; burnup is left on nodes deliberately,
because burnup does not change on transient timescales while all three others swing hard.

**Worst case 27 pcm** (range -27 to +21). Acceptable: it is 0.006 $ at discharge burnup, and
smaller than the DRAGON/OpenMC void disagreement by a factor of 50.

**3. beta_eff as a curve, extracted rather than assumed.** This was the gate item most likely
to be quietly faked, and the first attempt *did* produce a fake -- see the trap below.

| BU, MWd/kg | 0 | 2 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|
| beta | 0.006824 | 0.006361 | 0.005877 | 0.005358 | 0.004985 | 0.004680 |

Beta falls by 31 % over life, as it must: the library's own Pu-239 delayed fractions sum to
**0.002254** against U-235's **0.006524** (measured directly from `DLIB_99`,
`rbmk_deldiag.x2m`), so beta tracks the U-235 -> Pu-239 shift. Second-order dependences at
20 MWd/kg: full voiding -4.5 % (0.004468), TF 2000 K + TG 900 K -1.9 % (0.004593).

Independent check: **OpenMC prompt-vs-total gives beta_eff = 0.006856 +/- 0.000162** at fresh
fuel and nominal density, against DRAGON's 0.006824 -- **-0.5 %, inside the Monte Carlo
error.** Two codes, two methods, two different definitions (DRAGON's is the flux-weighted
delayed nu-sigma-f ratio, OpenMC's is 1 - k_prompt/k_total), agreeing to half a percent.

The **0.0048 assumed throughout the project so far is a discharge-burnup number**. It is
correct to within 2 % at 20 MWd/kg and wrong by **+42 %** at fresh fuel. `openmc/compare_bu.py`
has been changed to use the measured curve.

### The trap: `GETVAL 'NUSIGF' 1` does not mean what it looks like

The first beta extraction returned **0.006524 at every burnup, every void fraction and every
temperature, identical to six digits** -- visibly wrong, since the whole point is that beta
falls with burnup. Two independent things were wrong, and either alone would have produced a
plausible-looking number:

1. `GREP: ... GETVAL 'NAME' I [J [K]]` takes a **start index, optional end, optional stride**
   (`DRVGRP.f:182-190`), not a count. `GETVAL 'NUSIGF' 1` reads element 1 only.
2. The macrolib out of `NCR:` has `NMIX = 1` but **`NBFIS = 18`** -- 18 fissile families, one
   per fissioning nuclide in the depleted fuel. `LENGTH 'NUSIGF'` returns 18.

So element 1 was U-235's entry, in *both* numerator and denominator, at every state -- and
0.006524 is exactly U-235's beta. The fix is `MEAN 'NUSIGF' 1 18`: the common factor 18
cancels in the ratio, so the mean is as good as the sum and needs one variable instead of
eighteen.

This is standing rule 1 in a new disguise. The number was not chosen to make an assert pass;
it was produced by a read that silently narrowed to one isotope, and it was *self-consistent
across ten states*, which made it look more trustworthy rather than less. What caught it was
knowing in advance what the physics had to do -- beta must fall -- and treating a flat curve
as a defect to be explained rather than a result to be recorded.

### Why `GOLVER` alone was not enough -- the exact mechanism

Recorded precisely now that the source has been read end to end:

- `EDIPXS.f:344-351` writes the `DIFF` block under `GOLVER` **or** a leakage model, so the
  edit object looks correct either way.
- `EDIPXS.f:413-419` sets the state-vector flag `IDATA(9)` **only** under a leakage model.
- `COMACR.f:91` reads `NLEAK = IPAR(9)`; `COMACR.f:169` copies `DIFF` out of the edit only when
  `NLEAK >= 1`; `COMACR.f:246` stores it in the COMPO under the name **`STRD`**, not `DIFF`.

With `GOLVER` alone the COMPO is written, is a valid `L_MULTICOMPO`, has no `STRD`, and DONJON
stops at `TRISYS: NO DIFFUSION COEFFICIENTS`. That is why `FLU: TYPE K B1 SIGS BUCK 0.0` is
mandatory: the B1 machinery sets the flag, and zero imposed buckling leaves the spectrum
untouched (k-inf 1.310172 -> 1.310173). This is also why a `grep DIFF` on `_ACompo` finds
nothing while the database is perfectly usable -- the block is called `STRD` on disk. The
stale comment in `rbmk_a5b_compo.x2m` that claimed B1 "is NOT used here" has been corrected;
it contradicted the code three lines away from it.

### The void curve, now that both codes have more than two densities

`branch_mid.py` added OpenMC branches at 0.35 and 0.15 g/cm3 across burnup. Reactivity
relative to nominal, pcm:

| BU | 0.60 | 0.45 | 0.35 | 0.30 | 0.15 | 0.05 | 0.02 |
|---|---|---|---|---|---|---|---|
| **DRAGON** 0 | +137 | +239 | -- | +265 | +236 | +220 | +222 |
| **OpenMC** 0 | -- | -- | +566 | -- | +737 | -- | +1030 |
| **DRAGON** 20000 | +313 | +656 | -- | +995 | +1457 | +1973 | +2190 |
| **OpenMC** 20000 | -- | -- | +1722 | -- | +2879 | -- | +4007 |

Two things the old two-point comparison could not see:

- **At discharge burnup the shape agrees and only the magnitude differs** -- the ratio is a
  steady 1.8-2.0x across the whole density range. That is the signature of a systematic
  error in one quantity, not of a modelling difference that varies with void.
- **At fresh fuel the shapes genuinely disagree.** DRAGON is non-monotonic -- it peaks near
  0.30 g/cm3 and falls back -- while OpenMC rises all the way to full void. The fresh-fuel
  ratio therefore runs from 2.2x at 0.35 to 4.6x at 0.02, and quoting a single fresh-fuel
  ratio is meaningless.

Fresh fuel is not the accident condition, so this does not move the bracket for A8. It is
recorded because it narrows where the disagreement lives.

### The void worth in dollars, with the measured beta

Applying beta(BU) -- a property of the fuel, so the same curve applies to both codes:

| BU, MWd/kg | beta | DRAGON pcm | DRAGON $ | OpenMC pcm | OpenMC $ |
|---|---|---|---|---|---|
| 0 | 0.006824 | +222 | +0.33 | +1030 | +1.51 |
| 5000 | 0.005877 | +155 | +0.26 | +852 | +1.45 |
| 10000 | 0.005358 | +499 | +0.93 | +1473 | +2.75 |
| 15000 | 0.004985 | +1204 | +2.42 | +2650 | +5.32 |
| 20000 | 0.004680 | +2190 | +4.68 | +4007 | +8.56 |

The worth in dollars grows **14x (DRAGON) or 5.7x (OpenMC)** from fresh to discharge, because
the numerator rises and beta falls at the same time. Both ends of the bracket put full voiding
at discharge burnup **well above prompt critical** -- 4.7 $ and 8.6 $. That is the first
quantitative statement this project can make about why the reactor was dangerous, and it holds
at both ends of the bracket, which is what the bracket was built to test.

Caveat kept in view: this is the *equilibrium* worth of complete voiding at fixed burnup, not
a transient. A8 is what decides whether the 1.8x matters.

### A5b.1d — the bracket, and why it is a table and not a second COMPO

The plan called for a **second MULTICOMPO** whose void branches are rescaled to OpenMC, the
two differing only on the DCA axis. That artifact cannot be produced. Checked, not assumed:

- `LIB:` has no cross-section scaling facility — its full keyword list is in `LIBINP.f`
  (`APLIB1 APLIB2 APLIB3 APXSM COMB CORR DBYE DRAGON EVOL GAS INF IRSET MACROLIB MATXS
  MATXS2 MICROLIB MIX MIXS NDAS NOEV NOGAS NONE NUMBER PTMC PTSL RESK RSE SAT SHIB TCOH
  TEMP THER WIMSAECL WIMSD4 WIMSE`) and none of them multiplies a cross section.
- `EDI:` and `COMPO:` have no scaling option either; the write path is
  `LIB:` → `USS:` → `ASM:` → `FLU:` → `EDI:` → `COMPO:` with no hook in it.
- `MAC:`'s `ADD` exists but only in **update** mode (`MACDRV.f:253-256`), i.e. on a macrolib
  that already exists in DONJON — it is a consumer-side tool, not a producer-side one. And
  with `NBFIS = 18` a νΣf override needs 18 values per group per mixture.

That leaves patching the DRAGON source — `5.1/` is an upstream submodule — or hand-editing the
114 MB LCM ASCII file, reverse-engineering an undocumented format to produce an opaque derived
artifact that must be regenerated whenever an OpenMC branch point is added. Two were added
today alone.

So the bracket is carried as **data** (`openmc/void_bracket.py`), not as a second database:

r(BU, v) = Δρ_OpenMC(BU, v) / Δρ_DRAGON(BU, v),  v = 1 − dca/0.72

| BU, MWd/t | v = 0.514 | v = 0.792 | v = 0.972 |
|---|---|---|---|
| 0 | 2.21 ± 0.27 | 3.12 ± 0.31 | 4.64 ± 0.30 |
| 2000 | 1.95 ± 0.34 | 2.64 ± 0.33 | 3.71 ± 0.33 |
| 5000 | 3.09 ± 0.46 | 4.80 ± 0.60 | 5.51 ± 0.51 |
| 10000 | 2.07 ± 0.36 | 3.47 ± 0.28 | 2.95 ± 0.18 |
| 15000 | 1.72 ± 0.23 | 2.23 ± 0.14 | 2.20 ± 0.10 |
| **20000** | **1.95 ± 0.14** | **1.98 ± 0.09** | **1.83 ± 0.05** |

Errors are OpenMC's Monte Carlo statistics; DRAGON is deterministic.

**At the accident condition the bracket collapses to one number.** At 20 MWd/t the ratio is
1.83–1.98 across the whole density range — constant within its own error bars — so a single
multiplier near **1.9** describes the entire disagreement. That is a much better-behaved
bracket than the plan assumed, and it is only visible because the density axis now has four
OpenMC points instead of two.

The low-burnup rows carry no information and must not be used: at 5 MWd/t DRAGON's own void
worth dips to +155 pcm, so the ratio is a small number over a smaller one; at fresh fuel the
two curves disagree in *shape*, not just scale. Neither is the state the reactor was in.

> **REVISED 2026-09-24 (3): 20 MWd/kg was not the accident condition.** [PAV] Table 1 gives
> the Unit 4 core on 26 April 1986 as still mostly the first core:
>
> | assemblies | average burnup, MWd/kgU |
> |---|---|
> | 721 | 13.7 |
> | 392 | 12.3 |
> | 154 | 10.5 |
> | 101 | 8.8 |
> | 35 | 7.0 |
> | 43 | 5.4 |
> | 41 | 3.5 |
> | 172 | 1.2 |
> | **1659, whole core** | **10.9** |
>
> Nothing was near 20. The rows that matter are 10000 and 15000, where r is 2.0–3.5 and not
> constant. The single ~1.9 multiplier above describes a core Unit 4 never was. The
> paragraph above claiming "neither is the state the reactor was in" is wrong for 10 MWd/kg.
> Consequences, not yet acted on:
>
> - The bracket for A8 must be evaluated over roughly 5–15 MWd/kgU and weighted by that
>   distribution, not quoted at 20.
> - The OpenMC density axis there needs the same four-point resolution it has at 20.
> - The dollars table above should be read at 10–14 MWd/kgU: +0.9 to +2.4 $ (DRAGON) and
>   +2.8 to +5.3 $ (OpenMC). Those are pre-geometry-fix numbers.
>
> The design discharge burnup is also not 20. [D] p.95 gives 19.5–24.4 GWd/t UO₂, i.e.
> 22–28 GWd/tU, and [BIB] gives ~26. The burnup axis itself is per tonne U (`EVO: POWR` is
> MW per t initial HM), matching [PAV], so there is no unit trap.

Ratios are of **branch** reactivities at the same burnup, never of absolute k — the two codes'
depletion trajectories diverge (+268 pcm at 5 MWd/t, −2084 at 20), so an absolute-k correction
would fold a depletion difference into a void correction.

**What this defers to A7/A8.** Variant A is the COMPO as built. Variant B multiplies the
void-induced reactivity by r. The application point is `MAC: ... ADD` on the void-induced Δ in
the consuming deck — one visible multiplier rather than a second 114 MB binary, and the single
source of truth for the physics stays in `_ACompo`. This preserves the plan's intent (the
variants differ only in how the DCA axis is used) and moves the implementation, not the
science. It is **not yet built or validated** — that is the first item of A7.

## The draglib the whole project was running on is not the one it ships — 2026-09-24

Restructuring the repo for a clean clone turned up a reproducibility defect that had been
live since 19 September and would not have been visible any other way.

`DLIB_99` is `draglibendfb8r1Apolib99_v5p1`, resolved by each deck's `.access` hook out of
the `libraries` submodule. Upstream's hook gunzips it **in place**, which deletes the `.gz`
and leaves the decompressed file in the submodule; on the next run the hook finds the
decompressed file already there and uses it without looking at the `.gz` again. That is a
cache with no key.

At some point the `libraries` submodule moved to `d4456d42` ("Upgrade draglibs to NJOY2016
release 78", 2025-12-24). The decompressed leftover from the previous revision stayed on
disk and kept winning. Every DRAGON number recorded in this file was produced against it.

| | bytes | `rbmk_cell_a3` k∞ |
|---|---|---|
| what was actually used | 134,497,940 | **1.310172** |
| what the submodule pins (LFS `cb1395ffbb65…`) | 83,700,460 | **1.308679** |

**−87 pcm.** Not large, but it is a systematic offset under every recorded DRAGON result,
and a clean clone on another machine would silently have produced the second column while
the documents claimed the first.

The same check found a second one: `draglibendfb8r1ecco1962_light_v5p1`, 317,833,351 bytes on
disk against 161,707,708 pinned. `draglibendfb8r1SHEM361_v5p1` and `draglibJef2p2Apolib99_v5p1`
matched and were fine.

The provenance of the two oversized files could not be established. They are not in the
submodule's LFS object store at any commit in its history, and the older pointer
(`f5cd7e2e…`, 51,120,783 compressed) was never cached locally. They are roughly twice the
size of the pinned builds, which is consistent with a pre-NJOY-78 library carrying more
temperature points, but that is inference, not evidence.

**What changed.** `decks/common/dlib99.access` now content-addresses the cache: it digests
the source `.gz` and decompresses to `.cache/draglib/<lib>.<sha12>`, so bytes from a
different revision land at a different path and can never be picked up in place of the
pinned ones. The run log prints the key and the size. `tools/tidy_libraries.sh` compares
every decompressed leftover against the pinned `.gz` and moves non-matches to
`.cache/draglib/unprovenanced/` rather than deleting them — results were produced with
them and may need reproducing.

**What has not changed, and is now owed.** Every DRAGON figure in this file, in
`PROJECT_PLAN.md`, in `TIER_A_WORKPLAN.md` and in `docs/report.html` — k∞ 1.310172, the
630-point MULTICOMPO, the β curve, the void table, the dollars table — was measured on the
unprovenanced library and has **not** been re-baselined. The OpenMC side is unaffected: it
is continuous-energy ENDF/B-VIII.1 and never touched a draglib, so the DRAGON/OpenMC
bracket has to be recomputed rather than merely relabelled. Re-baselining means rerunning
`rbmk_a5b_compo.x2m` (81 min) and the decks downstream of it.

Standing rule 7, earned here:

7. **A cache without a key is a silent substitution.** Any derived artifact kept beside its
   source must carry a digest of that source in its name. "The file is already there" is not
   evidence that it is the right file, and the failure is invisible precisely because
   everything keeps working.

## A2 — the 3-D core, run at last — 2026-09-23

| | |
|---|---|
| deck | `Donjon/data/rbmk_core_3d_realistic.don` (49 × 49 × 32, 25 cm pitch) |
| extent | MESHX/MESHY 0 → **1225 cm**, MESHZ 0 → **800 cm** (7 m active + 50 cm axial reflector each end) |
| regions | 76 832 |
| cross sections | IAEA 2-group PWR — **geometry and solver check only, no RBMK physics** |
| **k_eff** | **1.123062**, converged |
| `FLUD:` wall clock | **1 s** at `MCFD 1` |

**GATE A2 PASSED.** No `MAXIMUM NUMBER OF OUTER ITERATIONS IS REACHED`, and the value is
physically the right one for the wrong-on-purpose cross sections: those constants have
k∞ ≈ 1.12, and a 12.25 m core behind a 50 cm reflector leaks almost nothing, so k_eff ≈ k∞.
That is the whole content of the test — the old 0.054 was a 12 cm cube leaking almost
everything. Do not read reactor physics into 1.123062; real cross sections arrive with A5b.

**The performance number is the surprising one.** `FLUD:` at `MCFD 1` takes **1 second**
against the 729 s `DUAL 3 3` baseline — ~700×, not the ~40× estimated from the unknown count.
This does not change the Tier B conclusion (1 s per steady solve is still two orders of
magnitude off a 10 Hz panel, and DONJON remains single-threaded with no GPU path), but it
does mean a DONJON-in-the-loop quasi-static fallback is far more viable than the earlier
estimate suggested, and the offline A8 transient will be much cheaper than budgeted.

Still open from the A2 group: `gen_rbmk_donjon.py`, `gen_rbmk_geo.py` and `gen_rbmk_simple.py`
still carry PITCH in metres, and the core mix map still has **no rod sites** (A6).

## Phase 0 corrections — 2026-09-23

Applied before starting A5b, so that the MULTICOMPO is not built on a known-wrong cell.

**The hydrogen fix.** `RbmkLib.c2m:44` → `H1_H2O`. `rbmk_cell_a3.x2m` re-run from a deleted
`.result`: **k∞ = 1.310172**, matching the independently-measured value; volume-fraction
guardrail still passes (89.594 / 3.772 / 2.901 %).

**Verification that the file reshuffle changed no physics.** `rbmk_h2otest.x2m` re-run after
repointing its branches (`RbmkLibF` for free gas, `RbmkLib` for bound) reproduces every value
bit-for-bit:

| branch | dca 0.72 | dca 0.35 | dca 0.02 |
|---|---|---|---|
| `RbmkLibF` free gas (was `RbmkLib`) | 1.312816 | 1.316728 | 1.314234 |
| `RbmkLib` bound (was `RbmkLibH`) | 1.310172 | 1.314718 | 1.313999 |

→ +226 / +82 pcm and +264 / +222 pcm, exactly as recorded before the rename.

**Procedure files.** `RbmkLibH.c2m` retired; `RbmkLibF.c2m` added (free gas, do-not-use
banner, kept only so the comparison above reproduces); `RbmkLibN`/`RbmkLibW` headers corrected
to describe `CTRA`, which is what they actually vary. Each variant now differs from `RbmkLib`
in exactly one non-comment line — checked mechanically. Six diagnostic decks repointed from
`RbmkLibH` to `RbmkLib`.

**Housekeeping.** 21 orphaned `.access` scripts (decks already in `quarantine/`) moved to
`quarantine/orphaned_access/`. `rbmk_ussopt.x2m`'s header was a copy-paste of
`rbmk_grmin.x2m`'s and described the wrong experiment; corrected.

**Not done, and a live hazard.** The ~16 legacy `rbmk_cell_*` decks still in `Dragon/data/`
(`dlib99*`, `print_*`, `save_macrolib*`, `verify_macrolib*`, `2group_correct`, `mac_flux`,
`mccg_test`, `nxt_trkfile`) each hardcode their own `LIB:` block with free-gas `H1` **and a
different coolant number density** (`4.90E-2` vs `RbmkLib`'s `4.81360E-2`). They bypass the
single source of truth entirely. `rbmk_cell_dlib99_v2.x2m` is among them and is the retracted
CANDU bundle — yet `TIER_A_WORKPLAN.md` still names it as the A0 regression baseline. Left in
place pending a decision; do not build on any of them.

**Also unaddressed: none of this is under version control.** `5.1/` is an upstream submodule
(`git.oecd-nea.org/dragon/5.1.git`) and every RBMK deck, procedure and generator in it is
untracked, with no history. The same is true of `quarantine/` and `openmc/`. There is no way
to recover an overwritten deck, and no record of when any of them changed — which is why the
A2 timestamp evidence was the only way to establish that the core deck had never been run.


## Cell geometry pinned to a primary source — 2026-09-24 (2)

Three of the four open geometry questions listed under "Validation risk" are now settled
against the chief designer's own monograph. **One correction, one confirmation, one new
suspect, and every downstream physics number is invalidated pending a re-run.**

### The source

**Доллежаль Н.А., Емельянов И.Я., «Канальный ядерный энергетический реактор»,
Атомиздат, Москва, 1980.** 208 pp. Dollezhal was the RBMK's chief designer (главный
конструктор, НИКИЭТ). The book **pre-dates the 1986 modifications**, so it describes the
as-built Unit 4 configuration rather than the post-accident retrofit that most accessible
literature documents. A DjVu scan was converted to a searchable PDF (the OCR text layer was
re-injected as invisible UTF-8; the `ddjvu -format=pdf` path silently discards it).

Page numbers below are **PDF pages of that scan**, not printed page numbers.

### 1. Pressure tube 88 × 4 — CONFIRMED, no change needed

[D p.54], describing fig 3.3:

> «средняя часть которой состоит из трубы 9 **наружным диаметром 88 и толщиной стенки
> 4 мм**, изготовленной из сплава Zr+2,5% Nb»

— *"the middle part consists of tube 9 with **outer** diameter 88 and wall thickness 4 mm,
of Zr+2.5% Nb."* Repeated at [D p.11]; the 80 mm bore is confirmed twice more elsewhere
(`внутренним диаметром 80 мм`).

So OD 88 → r 4.40, ID 80 → r 4.00 — **exactly what the deck already had**. The Wikipedia
"8.4 cm ID" reading, which would imply OD 92, is wrong. The 10 % coolant-area ambiguity
that fed directly into the void coefficient is closed, and the guardrail's coolant band has
been tightened from 3.0–4.5 % to 3.4–4.0 % accordingly (88 × 4 → 3.653 %, 92 × 4 → 4.437 %,
so the wrong tube is now actively rejected rather than tolerated).

### 2. Ring radii 1.60 / 3.10 — STILL OPEN, deliberately unchanged

> **Resolved 2026-09-24 (3): 1.60 / 3.10 are correct** (⌀32 / ⌀62 mm, [RU-A], [LEI05]). The
> measurement below was wrong by ~1.5 mm, and declining to use it was the right call.

[D] does not state them. Fig 5.1 section Б-Б shows the 6+12 arrangement, confirming the
topology, but carries a single dimension: the grid envelope ⌀79. Measured off that figure
against that scale: **inner 17–18 mm, outer 31–32 mm, ±1.5 mm**. 3.10 sits comfortably
inside that; 1.60 may be ~1.5 mm small.

Geometric bounds, now that the central tube is pinned at ⌀15: inner ≥ 14.25 mm (clear the
tube), outer between 26.1 (rods touching at 30°) and 32.75 (fit inside ⌀79).

**Left at the old values on purpose.** A number measured off a scanned drawing carries false
precision, and substituting it would look like sourcing without being sourcing. Needs the
NIKIET 2006 monograph (Абрамов и др., ISBN 5-98706-018-4), which has dimensioned assembly
drawings.

### 3. Carrier — CORRECTED, the deck was wrong

[D p.11]: the 18 rods are held by spacer grids on a **central tube** of Zr
«размером 15×1,25 мм» (OD 15, ID 12.5); inside that tube runs «либо несущий стержень
диаметром 12 мм, либо несущая труба размером 12×2,5 мм» — *either a 12 mm solid carrier
rod, or a 12 × 2.5 tube*. The solid rod is the standard channel; the tube variant carries
the DKE power sensor and is not the average channel.

The deck modelled a 13 mm OD hollow tube with coolant inside — **matching neither
component**, and understating carrier metal by roughly 3×.

| | was | now |
|---|---|---|
| carrier | Zr tube r 0.500/0.650, coolant inside | solid Zr rod r 0–0.600 |
| water annulus | — | r 0.600/0.625 |
| central tube | — | Zr r 0.625/0.750 |

### 4. Fuel rod — CORRECTED, found while checking the carrier

Same sentence, [D p.11]: clad **OD 13.5 mm, wall 0.9 mm**, pellet **11.5 mm**, UO₂ density
up to 10.5 g/cm³, enrichment **1.8 or 2 % U-235**. The deck had clad OD 13.6 with an
0.825 mm wall, making the pellet–clad gap ~2.3× too thick. Pellet radius 0.5750 was already
right.

`RADIUS 0.0000 0.1000 0.5750 0.5975 0.6800` → `0.0000 0.1000 0.5750 0.5850 0.6750`.

### 5. Pellet central hole — NEWLY SUSPECT

> **Resolved 2026-09-24 (3): the hole is real.** See "Cell geometry closed" below.

The 2 mm central hole is a `[W]` value. [D p.11] describes the pellets only as «таблетками
диаметром 11,5 мм», and no central hole appears anywhere in the book. A solid pellet would
raise fuel volume by ~3.1 %. **Left in place, flagged.** Removing it would also break the
OpenMC volcheck agreement, so it needs deciding deliberately rather than in passing.

### Volume fractions, recomputed

Analytic, and independently reproduced by `openmc/volcheck.py` after the same edits —
both give cell area exactly 625.0000 cm².

| | before | after | change |
|---|---|---|---|
| graphite | 89.5938 % | 89.5938 % | — |
| coolant | 3.7721 % | **3.6527 %** | −3.2 % rel |
| fuel | 2.9009 % | 2.9009 % | — |
| zirconium | 2.7292 % | **2.9823 %** | +9.3 % rel |
| gas | 1.0040 % | **0.8702 %** | −13.3 % rel |

Graphite and fuel are untouched, so the 1763 t graphite cross-check and the fuel fraction
both still stand. All five clearances remain positive (tube→inner ring +1.75 mm, inner
rod-to-rod +2.50, inner→outer +1.50, outer rod-to-rod +2.55, outer→wall +2.25), so the
corrected cell is physically buildable.

### What this invalidates

**Everything downstream of the cell.** Not yet re-run — there is no DRAGON build in the
environment these edits were made in.

- **k∞ = 1.310172** — superseded. Coolant down 3.2 %, Zr (a parasitic absorber) up 9.3 %:
  expect a small decrease.
- **The A5 void curve (+1957 pcm at 20 MWd/kg)** — superseded, and note the *direction*:
  there is now less coolant to void, so the DRAGON void worth should fall, which would
  **widen** the unexplained DRAGON-vs-OpenMC gap rather than close it. That gap is a method
  difference (the CANDU-6 control agrees to 22 pcm) and this correction does not address it.
- **The A5b MULTICOMPO** — built on the old geometry, must be regenerated.
- `openmc/volcheck.py`'s `dragon` dict still holds the 2026-09-22 numbers and is marked
  stale in-file; it will not match until the deck is re-run.

Re-run order: `rbmk_cell_a3.x2m` (guardrail must pass with the new bands) →
`openmc/rbmk_cell.py` at matching burnup → `rbmk_a5_void.x2m` → `rbmk_a5b_compo.x2m`.

### Applied to four decks plus OpenMC, per standing rule 6

The cell geometry is **copy-pasted verbatim** into at least 13 decks. That is the same
hazard as rule 6 ("a fix that lives in a copy of the file is not a fix"), and it is how the
CANDU-6 bundle propagated in the first place. Changed here: `rbmk_cell_a3.x2m`,
`rbmk_a5_void.x2m`, `rbmk_a5b_compo.x2m`, `rbmk_h2otest.x2m`, `openmc/rbmk_cell.py`,
`openmc/volcheck.py`. The remaining diagnostic probes (`rbmk_ctra`, `rbmk_rates`,
`rbmk_sstest`, `rbmk_ussopt`, `rbmk_grmin`, `rbmk_micrprobe`, `rbmk_shem361`,
`rbmk_a5b_smoke`, `rbmk_a5b_offgrid`) still carry the old geometry and are now
inconsistent with the live decks.

**Recommended follow-up:** extract the cluster geometry into a shared
`rbmk_proc/RbmkGeo.c2m`, exactly as `RbmkLib.c2m` already does for compositions and for the
same stated reason — "so the two cannot disagree about what a mixture contains". Not done
here because it cannot be tested without a DRAGON build, and an untested refactor of the
geometry is precisely the class of change this log exists to prevent.

### Also recovered from the same source, not yet used

**A possible unit trap in the burnup axis.** *(Ruled out 2026-09-24 (3): both codes and [PAV]
use per tonne U. The real finding was different: see the A5b.1d revision.)* [D p.95] gives the burnup plateau as
`19,5—24,4 ГВт·сут/т **UO₂**` and the maximum as `24—28`, i.e. **per tonne UO₂, not per
tonne U** — a 13 % offset (÷0.8815 → ~27.7–31.8 GWd/tU). This log quotes the void
coefficient "at 20 MWd/kg" without stating the basis. If DRAGON and OpenMC disagree on that
convention, it would present exactly as a magnitude discrepancy at nominal burnup. Worth
ruling out before hunting the method difference further.

**Operating parameters** [D p.95], for the TH coupling that does not exist yet: channel
power 3000–3200 kW, flow 29.5–30.5 t/h, **exit quality 19.6 %**, inlet 79.6 kgf/cm² / 265 °C,
outlet 75.3 kgf/cm² / 289.3 °C, max coolant velocity 18.5 m/s, clad surface 295 °C / inner
323 °C, axial peaking 1.4, radial 1.06, max linear rating 360–385 W/cm, pellet centreline
2100 °C, channel length 7000 mm, cassette = two 3.5 m TVS with a ~20 mm gap.

**CPS channel** [D p.37]: OD 88 / **ID 82** mm (3 mm wall, not the fuel channel's 4 mm),
Zr alloy grade 125. Needed for `DEVINI:` when control rods are modelled.

**Graphite** [D p.11]: blocks 250 × 250 mm, density 1.65 g/cm³, bore 114 mm, 1693 cells —
all four already match the deck. Note [D] also says graphite **rings** are shrunk onto the
channel tube for thermal contact; the deck models a gas clearance at r 4.40–4.55, which is
an idealisation worth revisiting.

---

## Cell geometry closed — 2026-09-24 (3)

The four items Dollezhal left open are settled against eight sources the project had not
used. Full citations, file names and verbatim quotes are in `sources/README.md`. One was
already on disk: the IAEA-TECDOC-722/R PDF had been downloaded and never cited.

| Item | Verdict | Evidence |
|---|---|---|
| Ring radii 1.60 / 3.10 | **correct, unchanged** | rod circles ⌀32 / ⌀62 in [RU-A] and [LEI05] |
| Ring phase (outer offset π/12) | **correct, unchanged** | [D] p.96 fig 5.1 Б-Б. Inner rods sit on the axes; outer rods straddle them in pairs. This is a topology read, not a measurement. |
| Pellet hole 2 mm | **real, unchanged** | [RU-A] «осевое отверстие диаметром 2 мм»; [LEI05] Table 1; [BIB] lists it among RBMK-1000 rod design features |
| Clad OD | **13.5 → 13.58** (r 0.6750 → 0.6790) | [RU-A] drawing «13,58 +0,05/−0,07, внутренний 11,7 +0,1»; [LEI05] 13.6 / 11.7; [D] 13.5 × 0.9 |
| Graphite gas gap | **valid idealisation, unchanged** | [CAST] p.11; [TD722] p.76; [USP] |
| Burnup basis | **per t U in both codes; no trap** | `EVO: POWR` is MW per t HM; [PAV] uses per kg U |

**Clad OD refined, and why the Dollezhal fix mostly stands.** Every source agrees on ID
11.7 mm, so the pellet–clad gap correction in fee38ff is right. Only the OD moves. The 13.58
comes with drawing tolerances, which is why it's preferred over [D]'s rounded 13.5. The
published nominal clad-to-wall gap, 2.2 mm [TD722] p.107, doesn't discriminate: this cell
gives 2.21, and 2.25 at OD 13.5.

Coolant 3.6527 → 3.6037 % and Zr 2.9823 → 3.0313 %. Graphite, fuel and gas are unchanged.

**The pellet-hole mass check.** [PAV] gives 114.7 kg U per assembly at Unit 4, and [D] p.97
gives an active length of 6920–6954 mm. Over 6937 mm at the deck's 9.167 g HM/cm³, this cell
holds 115.3 kg with the hole (+0.5 %) and 118.9 kg solid (+3.7 %). The same numbers as UO₂,
130.8 vs 134.9 kg, both sit inside [D]'s 125–135 kg, so that range alone would not decide it.
The per-assembly uranium mass does.

**A caution, earned.** On 09-24 (2) the inner ring radius was measured off fig 5.1 at
17–18 mm, "±1.5". The real value is 16.0. The log declined to use the measurement, and that
restraint is the only reason it didn't become a geometry change. Reading *topology* off the
same figure (which rods sit on the axes) is reliable. Reading *dimensions* off it is not.

**Re-run.** `rbmk_cell_a3.x2m` from a deleted `.result`, pinned draglib `cb1395ffbb65`,
x86_64: **k∞ = 1.304123**. The guardrail passed, and DRAGON MIXTURESVOL fractions are
89.594 / 3.604 / 2.901 / 3.031 / 0.870, equal to `volcheck.py`'s analytic values. A second run
after comment-only edits reproduced it bit for bit.

k∞ steps since the last recorded value:
- 1.310172 → 1.308679: library, −87 pcm
- → 1.304717: Dollezhal carrier and clad, −232 pcm
- → 1.304123: clad OD 13.58, −35 pcm

**What remains owed** (unchanged in kind from 09-24 (2), now on a closed geometry):
- `rbmk_a5_void.x2m`, `rbmk_a5b_compo.x2m` (81 min), the β curve, the OpenMC runs and the
  bracket all need re-running.
- The nine diagnostic probes still carry the pre-Dollezhal geometry. The shared
  `rbmk_proc/RbmkGeo.c2m` extraction is still the recommended fix.
- **Re-frame the bracket at 10–14 MWd/kgU, not 20.** See the revision in the A5b.1d section.

**Also found, for later.** [TD722] p.64 gives the one *measured* void coefficient in the
project so far: at Leningrad, 1.8 % enrichment, approaching equilibrium burnup, the steam void
coefficient was **4–5 β**. That is a core value with additional absorbers loaded, so it cannot
be compared with a k∞ branch. It is the first thing A6/A7 can be checked against.

---

## Re-baseline on the closed geometry — 2026-09-24 (4)

Everything downstream of the cell, re-run in both codes on the sourced geometry and the pinned
draglib (`cb1395ffbb65`). The machine was the x86_64 box (Ryzen 5 3600, 6 cores / 12 threads),
with OpenMC 0.16.0 from the `openmc-env` conda env and ENDF/B-VIII.1 HDF5 in `~/nucdata`.
**This supersedes every DRAGON and OpenMC RBMK number recorded earlier in this file.** Those
tables are kept for provenance and are not repeated.

### One geometry, thirteen decks

The cell geometry now lives in `rbmk_proc/RbmkGeo.c2m` (`GEOSS GEOFL := RbmkGeo ;`). All 13
lattice decks call it, including the nine diagnostic probes, which were still on the
pre-Dollezhal carrier and clad. Gate: `rbmk_cell_a3` through the procedure reproduces
k∞ 1.304123 bit for bit.

### DRAGON

| | result |
|---|---|
| `rbmk_cell_a3` k∞ | **1.304123**, guardrail passed |
| `rbmk_h2otest` | bound H: 1.304123 nominal (matches a3); free gas 1.306794. Full void, fresh: bound **+62**, free gas −82 pcm |
| `rbmk_a5b_compo` | 630 points, 5 h 21 min wall (CPU-contended with OpenMC), 211 MB peak, 108 MB `_ACompo`, no aborts |
| Round trip, grid nodes | worst **6.6 pcm** over 8 nodes spanning every axis (was 6.4) |
| Off-grid, `LINEAR` | worst **26.5 pcm** over 8 midpoints (was 27) |
| β(BU) | 0.006825, 0.006359, 0.005872, 0.005350, 0.004975, 0.004671 at 0/2/5/10/15/20 MWd/kg. Essentially unchanged (was 0.006824 → 0.004680), as expected: β is a property of the fuel, which didn't change. |

**The off-grid test is reproducible for the first time.** The DONJON side of it had never been
saved. The eight points are now in `rbmk_a5b_sweep.don`, and `openmc/a5b_interp_check.py`
compares both tests against the DRAGON `.result` files with no expected values in either.
`dragon_a5b_void.json` is now generated by `openmc/extract_a5btab.py` rather than typed.

### The void curve, both codes

Branch reactivity relative to 0.72 g/cm³ at the same burnup, pcm, at TF 900 K / TG 750 K.
DRAGON is from the COMPO; OpenMC is from `branch_results81*.json`.

| BU | code | 0.6 | 0.45 | 0.35 | 0.3 | 0.15 | 0.05 | 0.02 |
|---|---|---|---|---|---|---|---|---|
| 0 | DRAGON | +113 | +185 | -- | +181 | +121 | +72 | +62 |
| 0 | OpenMC | -- | -- | +497 | -- | +789 | -- | +901 |
| 2000 | DRAGON | +104 | +165 | -- | +155 | +96 | +62 | +59 |
| 2000 | OpenMC | -- | -- | +638 | -- | +792 | -- | +1012 |
| 5000 | DRAGON | +82 | +112 | -- | +67 | −21 | −64 | −67 |
| 5000 | OpenMC | -- | -- | +489 | -- | +771 | -- | +862 |
| **10000** | DRAGON | +99 | +153 | -- | +145 | +128 | +172 | **+207** |
| **10000** | OpenMC | -- | -- | +633 | -- | +846 | -- | **+1202** |
| **15000** | DRAGON | +162 | +303 | -- | +403 | +536 | +728 | **+819** |
| **15000** | OpenMC | -- | -- | +999 | -- | +1743 | -- | **+2288** |
| 20000 | DRAGON | +257 | +527 | -- | +782 | +1123 | +1509 | +1672 |
| 20000 | OpenMC | -- | -- | +1555 | -- | +2751 | -- | +3757 |

OpenMC's statistical error on these is ±70–120 pcm.

**What the geometry correction did.** DRAGON's full-void worth fell at every burnup, by
150–520 pcm (+222 → +62 fresh, +499 → +207 at 10 MWd/kg, +2190 → +1672 at 20). OpenMC barely
moved: +1030 → +901 fresh and +1473 → +1202 at 10, both within 2–3σ, and 4007 → 3757 at 20. As
predicted on 09-24 (2), the corrections **widened** the method gap. DRAGON's dip at 5 MWd/kg is
negative again and OpenMC still shows no trace of it.

### In dollars, at the burnups Unit 4 actually had

| BU, MWd/kg | β | DRAGON full void | OpenMC full void |
|---|---|---|---|
| 0 | 0.006825 | +0.09 $ | +1.32 $ |
| 5 | 0.005872 | −0.11 $ | +1.47 $ |
| **10** | 0.005350 | **+0.39 $** | **+2.25 $** |
| **15** | 0.004975 | **+1.65 $** | **+4.60 $** |
| 20 | 0.004671 | +3.58 $ | +8.04 $ |

At the Unit 4 core average of 10.9 MWd/kgU, interpolating gives **~+0.6 $ (DRAGON) against
~+2.7 $ (OpenMC)**.

**The bracket now straddles prompt criticality at the accident state.** Quoted at 20 MWd/kg,
both ends were far above 1 $ and the choice of code looked like a question of degree. At the
burnups the core actually had, DRAGON says completely voiding average fuel stays below prompt
critical; OpenMC says it goes well past it. This is a single-cell k∞ statement, with no
absorbers, no leakage and no spatial weighting, so neither number is the core's. But it means
the DRAGON/OpenMC disagreement is no longer something A8 can be expected to wash out. It sits
on the threshold that governs the transient.

### The bracket as a multiplier is badly conditioned where it matters

`void_bracket.py`, r = Δρ_OpenMC / Δρ_DRAGON:

| BU | v = 0.514 | v = 0.792 | v = 0.972 |
|---|---|---|---|
| 0 | 2.72 ± 0.38 | 6.55 ± 0.62 | 14.63 ± 1.16 |
| 2000 | 4.03 ± 0.48 | 8.23 ± 0.81 | 17.07 ± 1.37 |
| 5000 | 5.97 ± 1.03 | −36.6 ± 4.0 | −13.0 ± 1.2 |
| **10000** | **4.28 ± 0.64** | **6.61 ± 0.71** | **5.81 ± 0.46** |
| **15000** | **2.71 ± 0.29** | **3.25 ± 0.20** | **2.79 ± 0.13** |
| 20000 | 2.23 ± 0.19 | 2.45 ± 0.11 | 2.25 ± 0.07 |

The "collapses to ~1.9" finding was a property of 20 MWd/kg, where DRAGON's denominator is
large. At 10–15 MWd/kg r runs 2.7–6.6 and depends on void fraction. At 5 MWd/kg DRAGON crosses
zero, so r is negative and meaningless. Scaling DRAGON's void-induced Δρ by r would divide by a
small, method-sensitive number exactly where the reactor was.

**Recommendation, replacing the A5b.1d design:** variant B should *replace* DRAGON's
void-induced Δρ(BU, v) with OpenMC's, interpolated on OpenMC's own grid, rather than *scale*
it. Both are additive corrections at the same `MAC: ADD` application point. Replacing avoids
the division and stays finite through DRAGON's zero crossing. Not built; this is a design
change for A7.

### Fresh-fuel reference and β_eff, OpenMC

Fresh fuel, nominal temperatures, 50k × 250 active batches (the GB10 used 100k × 400; this
box is 3× slower, and fresh fuel isn't the accident state):

| | OpenMC | DRAGON | difference |
|---|---|---|---|
| k∞, 0.72 g/cm³ | 1.316220 ± 0.000225 | 1.304123 | +705 pcm (was +551) |
| Δρ at 0.35 | +527 ± 19 pcm | +191 | 2.8× |
| Δρ at 0.02 | +799 ± 19 pcm | +62 | 12.9× |
| β_eff | **0.006739 ± 0.000166** (1 − k_prompt/k_total: 1.307519 / 1.316391) | 0.006825 | **−1.3 %, 0.5σ** |

The β check holds on the new geometry, just as it did before (−0.5 % then). The DRAGON β curve is
confirmed at its fresh-fuel end by a different code with a different definition. OpenMC's
fresh full-void worth fell 912 → 799 pcm with the geometry. DRAGON's fell 222 → 62.

### What this changes in the plan

1. **The method gap is now the top physics priority, ahead of A6.** The trigger recorded on
   09-23 for the deferred diagnosis was "A8 showing that the two bracketed cross-section sets
   give materially different transients". A bracket that straddles 1 $ at the accident
   burnup already establishes that, without waiting for A8. The highest-information next step
   is unchanged: a 172-group flux spectrum and per-nuclide reaction-rate comparison against
   OpenMC at 10 MWd/kg, nominal and voided, and not the 2-group view, which cannot see the
   cause. The four untested DRAGON knobs listed under "Qualified 2026-09-23" (split-pellet
   self-shielding, coarse tracking, unshielded Zr, P1) are the first candidates, and all are
   cheap single-cell runs.
2. **The COMPO burnup axis is too coarse around the accident state.** Nodes at 10 and 15
   bracket 12.3–13.7, where 1113 of the 1659 assemblies sat. Adding 7.5 and 12.5 costs
   ~1.3× the build. Do it the next time the COMPO is rebuilt, rather than as a rebuild of its own.
3. **Performance note.** On this 6-core box the COMPO took 5 h 21 min while sharing a core
   with OpenMC, against 81 min on the GB10. Run the two on separate cores (`taskset`) or in
   sequence.

---

## Method gap: hypothesis register — 2026-09-25

The question was put deliberately: DRAGON and OpenMC disagree about whether voiding at Unit 4's
burnup is prompt critical. **We are not allowed to settle that by knowing the answer.**
History's "it went prompt critical" is a whole-core statement, with the night's rod pattern,
so it isn't comparable to a cell k∞ anyway. Each code has to be driven to its own converged
limit, and the difference explained mechanism by mechanism.

Everything below is fresh fuel, TF 900 K / TG 750 K / coolant 573 K, where both codes have
identical compositions by construction. Tools:
- `decks/scripts/gen_meth.py` generates every DRAGON variant (`rbmk_meth_*.x2m`), each changing
  one thing relative to `ctrl`. `ctrl` reproduces `rbmk_h2otest` bit for bit.
- `openmc/method_study.py` runs the seed-matched OpenMC variants.
- `openmc/method_table.py` collects both into one table.
- `openmc/fourfactor.py` does the exact four-factor split.

### Where the disagreement lives: the four-factor split

k = ε · p · f · η exactly, with the thermal cut at 0.625 eV. Production DRAGON against OpenMC
(on DRAGON's own graphite table), void 0.72 → 0.02, change in ln (pcm):

| | ε | **p** | f | η | k |
|---|---|---|---|---|---|
| DRAGON | +3129 | **−8083** | +5511 | −502 | +55 |
| OpenMC | +3036 | **−6977** | +5587 | −565 | +1081 |
| difference | −93 | **+1106** | +77 | −63 | +1026 |

**Everything thermal agrees.** Thermal utilisation, η, and the thermal absorption shares match
to statistics: U-235 72.61 vs 72.51 %, H 5.70 vs 5.72, C 3.97 vs 4.02, Zr-91 1.82 vs 1.83.
That eliminates every hypothesis about the thermal flux: the voided channel as a streaming
path, the graphite, the water, the boundary.

**The whole disagreement is in p, resonance absorption above 0.625 eV**, and it is also where
the *nominal* k gap lives (p 0.79561 vs 0.80295). By nuclide, production DRAGON over-absorbs,
in % of all absorptions:

| | nominal | voided | growth on voiding |
|---|---|---|---|
| U-238 | +0.50 | +1.02 | +0.52 |
| Zr, mostly Zr-91 | +0.43 | +0.72 | +0.29 |

U-235, H, Nb agree. The C and O rows differ only because `parse_dragon.py` counts capture +
fission and leaves out (n,α).

This retires the 2026-09-23 reading that the disagreement was "U-235 fission production". That
decomposition normalised the rates per unit absorption, so extra resonance absorption showed
up as a lower production share.

### The register

| ID | Hypothesis | Test | Result | Verdict |
|---|---|---|---|---|
| H1 | Graphite scattering table differs (DRAGON 10 %-porosity reactor graphite, OpenMC crystal) | OpenMC on `c_Graphite_10p` / `30p` | nominal +7, void +23 (30 %: −22 / +41) | **real, small.** Mismatch confirmed; ≤ 41 pcm |
| H2 | Boundary: DRAGON `TISO` is white (`NXTTCG.f:464`), OpenMC mirror | OpenMC white; DRAGON `TSPC` | OpenMC −31 / −7; DRAGON −3 / +8 | **real, small** |
| H3 | Flat-flux regions too coarse | `RbmkGeoFine` k = 2, 4 | void +62 → +127 → +151; nominal −60, −83 | **confirmed, moderate**, converging |
| H4 | Flux tracking too sparse | 30/60, 60/120 | < 1 pcm | **ruled out** |
| — | Self-shielding tracking too sparse | 20/40 | +16 / −7 | **ruled out** |
| H7 | Zr at infinite dilution | `RbmkLibZ` (Nb-93 has no subgroup data) | 172 g: nominal +286, void +146; on SHEM-361: +137 / +56 | **confirmed, large on 172 groups** |
| H8 | Depletion Pu isotopes unshielded | `RbmkLibP`, burnup deck | ≤ 3 pcm at every burnup | **ruled out** |
| **H9** | **172 groups too coarse through the U-238 resonances** | SHEM-281 / 295 / 361 (295 and 361 need `USS: MAXST 300`) | nominal +206 / +441 / +438; void 62 → 292 → 482 → 503 | **confirmed, dominant**, converged by 295–361 groups |
| H5 | Isotropic scattering + transport correction | MOC (`MCCG:`) with anisotropy | not run | **open** |
| H6 | Single-region pellet for self-shielding (no rim effect) | pellet split into separate mixtures | not run | **open** |
| H10 | Depletion trajectories differ | transfer isotopics | not run | open (burnup only) |
| H11 | Temperature interpolation | library-grid temperatures | not run | open, expected small |

### The best-converged DRAGON

Everything that converges, together: SHEM-361 + Zr self-shielded + mesh 4× (`best361`).

| fresh fuel | production DRAGON | best DRAGON | OpenMC (10 %-porosity graphite) | gap closed |
|---|---|---|---|---|
| k∞ | 1.304123 | 1.313050 | 1.316350 ± 0.000265 | 705 → **191 pcm** |
| Δρ at 0.35 | +191 | +435 | +533 ± 21 | 342 → **98** |
| Δρ at 0.02 | +62 | +633 | +821 ± 21 | 759 → **188** |

**Three-quarters of the gap was DRAGON not being converged**, mainly in its energy mesh through
the resonances. None of these steps used OpenMC's answer: each is DRAGON refined against
itself until it stopped moving. That DRAGON converges *toward* OpenMC, from below, on the one
quantity that disagrees is evidence about which code is right that doesn't depend on history.
It isn't proof. That needs the remaining 190 pcm explained, and measured data (below).

**Cost.** `best361` takes 83× the production CPU, almost all of it the 4× mesh (SHEM-361 alone
is 2.2×). SHEM-361 + Zr is the affordable production upgrade. The mesh correction (~+75 pcm
on void at fresh fuel) is better measured separately than paid at every branch.

### The accident state, on the converged library

`rbmk_meth_buzr361` is `rbmk_a5_void.x2m` on SHEM-361 with Zr self-shielded, production mesh.
It took 31 min wall, against about 9 min for the production deck. Full-void (0.02 g/cm³) worth, pcm:

| BU, MWd/kg | 172-group DRAGON | **SHEM-361 + Zr DRAGON** | OpenMC | OpenMC / DRAGON | DRAGON $ (β on 172 groups) |
|---|---|---|---|---|---|
| 0 | +62 | **+560** | +901 ± 71 | 1.61 | +0.82 |
| 5 | −71 | **+532** | +862 ± 80 | 1.62 | +0.91 |
| **10** | +203 | **+904** | +1202 ± 95 | **1.33** | **+1.69** |
| **15** | +813 | **+1625** | +2288 ± 105 | **1.41** | **+3.27** |
| 20 | +1666 | **+2617** | +3757 ± 121 | 1.44 | +5.60 |

- **DRAGON's dip at 5 MWd/kg was a 172-group artifact.** It goes from −71 to +532, and OpenMC
  never had it. The old log's "not yet understood in detail; worth confirming" is now answered.
- **At the Unit 4 average of 10.9 MWd/kgU**, converged-library DRAGON gives about +1030 pcm,
  **≈ +1.96 $**, against OpenMC's ≈ +2.7 $. The fine-mesh correction measured at fresh fuel
  (~+75 pcm) would add to DRAGON's figure.
- **The prompt-critical straddle is resolved.** Both codes, each converged against itself, put
  complete voiding of average Unit 4 fuel above prompt critical in a single cell. This was
  reached without using the historical outcome as an input. The earlier ~0.6 $ was the 172-group
  library.
- The leftover ratio at the accident burnups, 1.33–1.41, matches the ~190 pcm residual at fresh
  fuel. That is H5/H6 territory, together with the depletion-trajectory difference (H10).

### Still open
The work order to close these is **`METHOD_CONVERGENCE_PLAN.md`**: gated phases A (fresh-fuel
residual), B (accident state), C (production upgrade), D (validation against the Kurchatov
critical experiments).

1. **The remaining ~190 pcm** (nominal and void): H5 (MOC, anisotropic scattering) and H6
   (radial self-shielding in the pellet) are the next tests.
2. **The accident state** is now bracketed at +1.96 $ (DRAGON, converged library) to +2.7 $
   (OpenMC). H10 (transfer OpenMC's depleted isotopics into DRAGON) would separate the depletion
   difference from the transport difference at 10 MWd/kg.
3. **Measured data.** The Kurchatov critical experiments turn out not to be specified in
   [ALX98], and are impurity-limited. See the next section.
4. **The production library.** The COMPO, the A5 deck and every downstream number are on the
   172-group library, which this study shows is not converged for this cell. Rebuilding on
   SHEM-361 + Zr is the obvious consequence, but it should wait for (2).

## Third-party benchmark: the RBMK Safety Review Project cell — 2026-09-25

Alexeev et al. (1998, [ALX98]) and Parisi & D'Auria (2007, [PAR07]) were obtained and read.
They are catalogued, with what each does and does not provide, in `sources/README.md`.

**The Kurchatov critical experiments are not usable as specified.** [ALX98] describes the
facility and seven configurations but only plots the measured k_eff and void effects. The full
specifications are in three other documents: Behrens et al. 1994 (Bremen report), Kuzmin 1993
(RRC-KI) and Behrens et al., *Nucl. Technol.* 114 (1996) 1. More importantly, the graphite's
B/Cd impurity is unknown and worth ≈ 1 % in k. The authors tuned it per code, and say
themselves that this keeps the experiments from being a benchmark. At best they constrain
*relative* void effects.

**[PAR07] reproduces our finding independently.** Their DRAGON (the same collision-probability
solver, but the IAEA WLUP 172-group library) against NIKIET's MCNP4C gives a void Δk of 0.03883
vs 0.04924, **−21 %**, and −32 % on 69 groups. That's a different group with a different library,
and the same deficit with the same dependence on group structure.

**[ALX98] Tables 3–4 fully specify a single-cell benchmark** (cold, fresh, 2 %, water at
1 g/cm³, Zr or Al tube), with answers from MCNP4A, MCU-3, MONK, WIMS-D/E and APOLLO-2. It is
transcribed once in `openmc/srp94_common.py`, which builds the OpenMC model and generates
`rbmk_srp94_*.x2m`. The assumptions the paper doesn't settle are stated in that file, and none
are tuned: 300 K throughout; "voided" removes the water but keeps the spacer steel; rod phase
π/12. Void effect here is Δk × 100, as the paper plots it.

| Zr tube | k∞ watered | k∞ voided | void Δk (%) |
|---|---|---|---|
| MCNP4A, ENDF/B-VI/L | 1.2778 | 1.3263 | 4.85 ± 0.04 |
| MCNP4A, ENDF/B-VI/B | 1.2806 | 1.3285 | 4.81 ± 0.04 |
| MCU-3 | 1.2800 | 1.3280 | 4.80 ± 0.05 |
| **OpenMC, VIII.1** | **1.27655 ± 0.00025** | *killed, re-run on GB10* | — |
| DRAGON, 172 groups | 1.2759 | 1.3005 | **2.46** |
| DRAGON, SHEM-361 + Zr self-shielded | 1.2829 | 1.3174 | **3.45** |

| Al tube | k∞ watered | k∞ voided | void Δk (%) |
|---|---|---|---|
| MCNP4A, ENDF/B-VI/L | 1.2714 | 1.3247 | 5.33 ± 0.04 |
| MCU-3 (3lib / 2lib) | 1.2740 / 1.2733 | 1.3283 / 1.3280 | 5.43 / 5.47 |
| MONK-5W · WIMS-E · WIMS-D · APOLLO-2 | 1.2838 · 1.2884 · 1.2925 · 1.2946 | 1.3310 · 1.3355 · 1.3371 · 1.3404 | 4.72 · 4.71 · 4.45 · 4.57 |
| DRAGON, 172 groups | 1.2717 | 1.3020 | **3.03** |
| DRAGON, SHEM-361 | 1.2756 | 1.3134 | **3.77** |

The published values were read off [ALX98] Figs 8–9 to ±0.001 in k; its error bars are 3σ, and
±σ is shown above.

What this shows:
- **Our OpenMC reproduces two independent Monte Carlo codes.** Watered k∞ 1.27655 is within
  0.1–0.4 % of MCNP and MCU, on different data (ENDF/B-VI against VIII.1).
- **Production DRAGON gives half the Monte Carlo void effect on a third-party cell** (2.46 vs
  4.80–4.85 %). On the Al variant it sits well below even the 1990s deterministic codes (3.03
  vs 4.45–4.72).
- **The converged-library settings close part of it** (2.46 → 3.45, Zr tube). The 4× mesh
  (`best_zr`, `best_al`) was killed before finishing. The residual on this cold, fully-watered
  cell is proportionally larger than on our hot cell, which makes this cell the sharper test
  for Phase A (MOC, rim self-shielding).
- The deterministic codes' higher k∞ in [ALX98] contrasts with our DRAGON, whose k∞ is close
  to OpenMC's on this cell (1.2759 vs 1.2766), yet whose void effect is far lower. Here too the
  gap is in how the codes respond to voiding, not in the base k.

### Hand-off to the GB10 (runs killed on the x86 box, 2026-09-25)
- `rbmk_srp94_best_zr`, `rbmk_srp94_best_al` (SHEM-361, Zr self-shielded, 4× mesh): about 1.5 h
  each on this box.
- OpenMC benchmark cell, Zr and Al, watered and voided: `openmc/srp94_run.py run Zr`, then `run
  Al`. Then `srp94_run.py table`.
- Everything is generated. Regenerate first with `python openmc/srp94_common.py` and `python
  decks/scripts/gen_meth.py`, then `tools/link_decks.sh`.
- Don't co-schedule DRAGON with a multi-threaded OpenMC on the same physical cores. On the x86
  box that made the COMPO 4× slower.

*Done on the GB10, 2026-09-25 (3); see the next section. The GB10 reproduces the x86 DRAGON
numbers to every printed digit (`ctrl` 1.304123, `buzr361`'s void row, the SRP `d172` / `d361`
decks).*

## Phase A–B on the GB10: the void gap closes to within its criterion — 2026-09-25 (3)

The work order is `METHOD_CONVERGENCE_PLAN.md`. Every number below regenerates from a script:
- `openmc/method_table.py`: the hot cell, fresh fuel, `rbmk_meth_*`, plus OpenMC's `method_study.json`;
- `openmc/srp94_run.py table`: the SRP-1994 cell;
- the `VOIDTAB` rows of `rbmk_meth_buzr361`, for burnup.

The machine is the GB10 (20 cores). DRAGON runs one job per core on cores 0–7, and OpenMC runs
12 threads on cores 8–19.

### The register, closed out

Every row is one change against `zr361`: SHEM-361, Zr self-shielded, production mesh and
solver. Δ is the change in pcm of ρ.

| ID | Hypothesis | Variant | Δ nominal | Δ full void | Verdict |
|---|---|---|---|---|---|
| A3 | groups converged at 361 | `zr370` (SHEM-370) | +15 | +2 | **converged** (< 20 pcm) |
| H5 | isotropic scattering + transport correction | `moc1` (MOC, same physics) | −1 | +5 | MOC reproduces CP |
| | | `moc2` (MOC, P1, `CTRA NONE`) | +1 | **+79** | **confirmed** |
| | | `moc3` (P2) | 0 | +80 | P1 is enough |
| H6 | single-region pellet self-shielding | `rim361` (4 rings, own sets) | **−891** | −361 | **artefact, rejected** (below) |
| | | `rim361s` (4 rings, shared sets) | +21 | −4 | geometry alone is neutral |
| | | `rim361t2` (SS tracking 20/60) | −892 | — | not a tracking effect |
| H11 | temperature interpolation | `tgrid` (900 / 800 / 600 K, both codes) | DRAGON +16, OpenMC +12 | DRAGON −41, OpenMC −23 ± ~10 | **ruled out** (18 pcm) |
| A6a | Nb-93 unshielded | `zr361nonb` (Nb removed) | +361 | +59 | bound: ≤ 59 pcm on void |
| A6b | graphite table | SRP cell, OpenMC 10P vs crystal | — | Zr +0.06, Al +0.08 %Δk | small (as H1) |
| H12 | the subgroup method itself | `shi361`, `tone361` | — | — | **untested**: `SHI:`/`TONE:` stop without a message on this `SUBG` library; not pursued |

**H6 is rejected as an artefact, not as physics.** Resolving the pellet rim moves k *away* from
OpenMC by 890 pcm, and continuous-energy Monte Carlo has no pellet self-shielding approximation to
refine. The same rings with one shared self-shielding set per rod (`rim361s`) reproduce `zr361`.
So the whole shift comes from USS giving each ring its own set, which is less accurate in this
cell than the single region production uses.

**Mesh and anisotropy are not additive.** On the fine mesh, MOC's anisotropy correction is bigger
than on the production mesh. The combined variant has to be run, not assembled from the parts.

### The best-converged DRAGON, fresh fuel

`bestmoc` is SHEM-361, Zr self-shielded, flat-flux regions split 4×, and MOC with P1
scattering.

| hot cell | production | `best361` (09-25) | **`bestmoc`** | OpenMC, 10P graphite | criterion |
|---|---|---|---|---|---|
| k∞ | 1.304123 | 1.313050 | **1.312198** | 1.316350 ± 0.000265 | gap 240 pcm: **fails** 100 |
| Δρ, 0.35 g/cm³ | +191 | +435 | **+553** | +533 ± 21 | gap −20: **passes** |
| Δρ, 0.02 g/cm³ | +62 | +633 | **+763** | +821 ± 21 | gap 58 < 2σ + 5 % = 83: **passes** |

| SRP-1994 cell, void Δk (%) | Zr tube | Al tube |
|---|---|---|
| DRAGON production (172 groups) | 2.46 | 3.03 |
| DRAGON SHEM-361 (+ Zr self-shielded, Zr tube) | 3.45 | 3.77 |
| DRAGON + 4× mesh | 4.03 | 4.42 |
| DRAGON + MOC P1 | 3.76 | 4.11 |
| **DRAGON `bestmoc` (all of the above)** | **4.59** | **5.04** |
| OpenMC VIII.1, crystal / 10P graphite | 4.71 / 4.77 ± 0.04 | 5.16 / 5.24 ± 0.04 |
| OpenMC VIII.0, crystal | 4.71 | 5.11 |
| MCNP4A (ENDF/B-VI) / MCU-3, [ALX98] | 4.81–4.85 / 4.80 | 5.28–5.33 / 5.43–5.47 |
| MCNP4A (ENDF/B-IV), [ALX98] | 4.29 | — |

- **D0 passes for OpenMC.** Its void Δk is 2–6 % below MCNP/MCU on ENDF/B-VI. VIII.0 and VIII.1
  agree to 0.05, but [ALX98]'s own MCNP moves 0.56 %Δk between ENDF/B-IV and B-VI, so a 0.1–0.2
  offset from B-VI is inside the data effect.
- **The earlier x86 watered k∞ of 1.27655 was a transcription error.** The GB10 run, same seed,
  gives 1.2756503, which is the same digits with two of them transposed.
- **DRAGON's residual on the SRP cell is now 4 %** (0.18–0.20 %Δk against OpenMC on the same
  graphite), down from 48 % / 42 % in production. The 4× mesh alone was worth +0.6 %Δk here,
  against +75 pcm on the hot cell: the cold cell with full-density water is much more
  mesh-sensitive.
- **The 8× mesh (A4), on the MOC lineage, closes the SRP gap.** CP at 8× didn't finish its first
  `ASM:` in 3 h, so it was stopped.

  | SRP void Δk (%) | 1× | 4× | **8×** | OpenMC 10P | MCNP/MCU |
  |---|---|---|---|---|---|
  | Zr tube (MOC P1) | 3.76 | 4.59 | **4.80** | 4.77 ± 0.04 | 4.80–4.85 |
  | Al tube (MOC P1) | 4.11 | 5.04 | **5.27** | 5.24 ± 0.04 | 5.28–5.47 |

  DRAGON now meets the "referenced" criterion on the third-party cell. The mesh is *not*
  converged by the plan's 20 pcm test, though: 4→8 still moved void by +0.21 / +0.23 %Δk
  (1→4: +0.58 / +0.62). A geometric extrapolation puts the limit near 4.92 / 5.41, about 3 %
  above OpenMC. So the exact 8× match is partly where the sequence happens to sit. Watered k∞
  at 8× is 1.2712 / 1.2625, against OpenMC's 1.2753 / 1.2673: the same ~250–300 pcm nominal
  residual as the hot cell. The hot-cell `bestmoc8` is still running (> 7 h).

**The nominal-k residual (~240 pcm) is attributed, not closed.** It sits in resonance escape,
from U-238 and Zr, as the 09-25 four-factor split showed. None of H1–H11 closes it. The rim
refinement went the wrong way. The only hypothesis left is the subgroup method itself (H12), and
that couldn't be tested on this library. The void effect is the quantity Tier A needs, and it
passes, so per the Gate A decision the residual is reported and bounded rather than chased.

### The accident state: depletion vs transport (B1, H10)

`openmc/isotopics_to_dragon.py` writes OpenMC's depleted fuel into `RbmkLibOMC<bu>.c2m`, and
DRAGON runs it at fixed composition (`omc10`, `omc15`). Nominal k∞ and full-void Δρ, with
DRAGON on `zr361` settings:

| | 10 MWd/kg: k∞ | Δρ | 15 MWd/kg: k∞ | Δρ |
|---|---|---|---|---|
| DRAGON, own depletion (`buzr361`) | 1.09903 | +904 | 1.01234 | +1625 |
| DRAGON, OpenMC fuel, OpenMC normalised on deposited energy (`oed`) | 1.09585 | +952 | 1.00541 | +1781 |
| DRAGON, OpenMC fuel, OpenMC normalised on fission Q (`omc`) | 1.08903 | +1000 | 0.99504 | +1901 |
| OpenMC, fission Q, crystal graphite (x86 and GB10 runs) | 1.0932 / 1.0916 | +1202 / +1336 ± 100 | 0.9985 / 0.9976 | +2288 / +2554 ± 105 |
| DRAGON, OpenMC fuel (fission Q), MOC P1 (`omc*moc`) | 1.08937 | +1097 | 0.99539 | +2013 |

- **Transport, on identical fuel.** DRAGON sits ~350 pcm below OpenMC in nominal k at 10 and 15
  MWd/kg, the same as fresh (330 pcm with crystal graphite). The transport difference doesn't
  grow with burnup.
- **Depletion: most of it is a burnup-scale convention.** OpenMC's default normalisation
  (`fission-q`) counts 193.4 MeV per U-235 fission and no capture energy. DRAGON normalises on its
  library's H-factor. Re-depleting OpenMC on deposited energy (`RBMK_NORM=energy-deposition`)
  cuts the fuel-composition difference from 835 → 264 pcm (10 MWd/kg) and 1718 → 680 pcm (15).
  So **60–70 % of the depletion-trajectory effect is how many fissions each code books per
  MWd**, not physics. For comparing against Unit 4's 10.9 MWd/kgU, which is thermal energy, the
  deposited-energy scale is the right one. Every OpenMC burnup result before today is on the
  fission-Q scale, and so sits at slightly higher effective burnup than its label.
- What remains of the depletion difference (+48 pcm on void at 10 MWd/kg, +156 at 15) is
  chains and yields, and is left attributed at that size.
- **H5 at burnup:** MOC P1 adds +97 (10) and +112 (15), against +79 fresh.
- **Gate B: the matched comparison.** `openmc/accident_ref.py` (→ `accident_ref.json`) gives
  OpenMC on deposited-energy depletion and 10P graphite, 50k × 250 active. `oedbest<bu>` is
  DRAGON's `bestmoc` settings (SHEM-361, Zr SS, 4× mesh, MOC P1) on *the same fuel*.

  | full-void Δρ (pcm) | 10 MWd/kg | 15 MWd/kg | 10.9 MWd/kgU (Unit 4) |
  |---|---|---|---|
  | OpenMC, matched | +1275 ± 29 (k 1.09929) | +2253 ± 33 (k 1.00902) | +1451 = **2.75 $** |
  | DRAGON `oedbest`, same fuel | +1196 (k 1.09485), **−6.2 %** | +2047 (k 1.00463), **−9.1 %** | +1349 = **2.55 $** |
  | DRAGON best, own depletion (`oedbest` − (`oed` − `buzr361`)) | +1148, −10.0 % | +1891, −16.1 % | +1282 = **2.43 $** |

  The 10.9 MWd/kgU column interpolates linearly, with β 528 pcm from the 172-group β curve.
  - **Transport meets Gate B:** within 10 % at both burnups.
  - **With each code's own depletion it misses at 15 MWd/kg** (−16 %). The excess is the
    depletion difference left after the burnup scales are matched: 48 / 156 pcm of void, from
    chains and yields. Per the Gate B decision, that residual is attributed and bounded, not
    chased.
  - **Nominal k on identical depleted fuel:** DRAGON is 370 / 430 pcm below OpenMC, against
    240 fresh. The resonance-escape residual grows a little with Pu.
  - **The headline.** At Unit 4's average burnup, complete voiding of one channel is **+2.4 to
    +2.75 $** across every converged variant of both codes. The accident-state bracket (+1.96 $
    DRAGON / +2.7 $ OpenMC on 09-25) has narrowed from a 38 % spread to 13 %, and every point in
    it is above prompt critical.


### Depletion step size — 2026-09-26

The rebuilt COMPO deck (2.5 MWd/kg steps through 5–15) gave k∞ 1.097439 at 10 MWd/kg, against
`rbmk_a5_void`'s 1.099025 on identical settings. `rbmk_meth_dstep*` are `rbmk_a5_void` with
only the burnup list, or `EVO:` extrapolation, changed. They ran on `spark` (the partner GB10),
which reproduces this machine bit for bit.

| k∞ / full-void Δρ (pcm) | 10 MWd/kg | 15 | 20 |
|---|---|---|---|
| 5 MWd/kg steps, `NOEX` (production to date) | 1.09903 / +904 | 1.01234 / +1625 | 0.92900 / +2617 |
| 2.5, `NOEX` (`dstep25`) | 1.09791 / +907 | 1.00939 / +1652 | 0.92462 / +2680 |
| 1.25, `NOEX` (`dstep125`) | 1.09746 / +908 | 1.00819 / +1663 | 0.92290 / +2705 |
| 5, `EXTR 1` (`dstep50x`) | 1.09839 / +887 | 1.00735 / +1650 | 0.92135 / +2701 |

- **Void worth is nearly step-converged:** within 0.5 % at 10 MWd/kg and 3 % at 15.
- **Nominal k∞ is not.** 5 MWd/kg `NOEX` steps overstate it by ~200 pcm (10 MWd/kg) and ~530 pcm
  (15). The error is first order; the limit is ≈ 1.0970 / 1.0070.
- **Consequence for B1.** Step-converged DRAGON sits ~190–200 pcm below OpenMC's matched
  depletion at both burnups, a steady offset. The fuel-composition residual is ~100 / 160 pcm of
  nominal ρ, not 264 / 680; much of the earlier number was DRAGON's step error. On void worth
  the chain/yield residual is 44 / 111 pcm (was 48 / 156). DRAGON's own-depletion full-void worth
  becomes 1152 / 1936 pcm, −9.7 % / −14.1 % from OpenMC. The transport-only Gate B verdict is
  unaffected.
- **The rebuilt COMPO** (`NOEX`, 2.5 MWd/kg steps in 5–15) carries ~75–130 pcm of step error in
  nominal k over the accident range, and < 1 % in void worth. 2.5 MWd/kg with `EXTR 1` is the
  candidate for the next rebuild (untested).

## Phase C: production on the converged library — 2026-09-26

`METHOD_CONVERGENCE_PLAN.md` C1–C5. Gate C (every production number regenerated) is met for
the lattice level. **Superseded:** every production number before this section was computed on
the 172-group library with Zr unshielded. That covers k∞ 1.304123, the 630-point COMPO, the
"~1.9 multiplier", and the 09-24 (4) dollars table. For the record only.

| Step | What changed | Gate |
|---|---|---|
| C1 | `RbmkLib.c2m` gives the Zr of MIX 2 / 8 / 9 self-shielding sets 3 / 4 / 5. The old composition is kept only as `RbmkLibU.c2m` (do-not-use banner) for the 172-group method-study controls. `RbmkLibZ` and `RbmkLibP` are in `quarantine/method_study/`. | `rbmk_cell_a3` **k∞ 1.313968** (was 1.304123), guardrail passed |
| C2 | `decks/common/rbmk.access` binds the seven production decks to SHEM-361, with `USS: PASS 2 MAXST 300`. Control decks keep their own hooks. | `h2otest` = `zr361` and `a5_void` = `buzr361`, both bit for bit |
| C3 | Mesh and MOC are **not** in production: MOC at 4× costs ~2 h per state, which is impossible at 840 points. They are carried as a measured additive correction, variant A′ in `openmc/void_bracket.py`: +204 / +244 / +266 pcm on full void at 0 / 10 / 15 MWd/kg. | measured, never fitted |
| C4 | COMPO rebuilt with burnup nodes at 7.5 and 12.5: 8 × 7 × 5 × 3 = **840 points**, `_ACompo` 152 MB, 14.7 h on the GB10. The off-grid deck's burnup indices were remapped (10 → 5, 20 → 8). | round trip **6.7 pcm** worst (≤ 10); off-grid **21.2 pcm** worst (≤ 30); β monotone 0.006822 → 0.004677 |
| C5 | `void_bracket.py` rewritten: additive variants instead of the r multiplier (below). | table below |

**The void bracket at nominal temperatures** (`python openmc/void_bracket.py`; β from
`rbmk_a5b_beta.don` on the new COMPO):

| BU, MWd/kg | A: DRAGON COMPO | A′: + mesh/MOC | B: OpenMC matched | β |
|---|---|---|---|---|
| 0 | +560 = +0.82 $ | +764 = +1.12 $ | +821 = +1.20 $ | 0.006822 |
| 5 | +537 = +0.91 $ | +761 = +1.29 $ | +849 = +1.44 $ | 0.005877 |
| 10 | +913 = +1.71 $ | +1157 = +2.16 $ | +1276 = +2.38 $ | 0.005355 |
| **10.9 (Unit 4 average)** | **+1034 = +1.95 $** | **+1282 = +2.42 $** | **+1438 = +2.72 $** | 0.005288 |
| 12.5 | +1248 = +2.41 $ | +1503 = +2.91 $ | +1725 = +3.34 $ | 0.005169 |
| 15 | +1661 = +3.33 $ | +1927 = +3.87 $ | +2254 = +4.52 $ | 0.004983 |
| 20 | +2645 = +5.66 $ | +2911 = +6.22 $ ‡ | +3238 = +6.92 $ ‡ | 0.004677 |

‡ Corrections above 15 MWd/kg are held at their 15 MWd/kg values: there is no matched point at
20. OpenMC's unmatched energy-deposition branch at 20 gives +3671 ± 127 (crystal graphite), so
B is likely low there. Unit 4 had nothing near 20.

- **A′ is the converged-DRAGON answer, and it is the one Tier A should carry**, with B as the
  bracket's upper end.
- **A is the production COMPO as it stands.** It is now above 1 $ at the Unit 4 average, where the
  172-group COMPO gave ~0.6 $.
- **Every variant puts full voiding of average Unit 4 fuel above prompt critical.**
- For A7/A8: the corrections are additive in Δρ, as functions of (BU, void fraction), applied on
  top of the COMPO's void branch. `void_bracket.corrections(bu, dca)` returns all three.

## Where the project stands, and the reordered plan — 2026-09-26 (2)

**What the method-convergence segment bought.**
- **Before:** DRAGON and OpenMC disagreed on whether voiding average Unit 4 fuel is prompt critical
  (+0.6 $ vs +2.7 $).
- **Now:** every converged variant of both codes gives +2.4 to +2.75 $. The spread fell from
  38 % to 13 %, and the historical outcome was never an input.
- **Checked against a third party.** Our OpenMC reproduces the 1990s MCNP / MCU results on the
  SRP-1994 cell.
- **In production.** The fixes are in `RbmkLib` and the 840-point COMPO.

**What caused the gap, largest first:**
1. The 172-group energy mesh through the U-238 resonances.
2. Zr left at infinite dilution.
3. The flat-flux mesh.
4. Isotropic scattering with a transport correction.
5. The two codes' different burnup scales (fission-Q vs H-factor).
6. DRAGON's 5 MWd/kg depletion steps. These affect nominal k only.

**Confidence now:**

| Level | Confidence | Basis |
|---|---|---|
| Fuel-cell void worth | **good, about ±10 %** | two methods plus a third-party benchmark |
| Fuel-cell absolute k∞ | **moderate, a few hundred pcm** | 240–430 pcm DRAGON/OpenMC residual (attributed); 75–130 pcm step error in the COMPO |
| Whole core: rods, map, TH, transient | **none yet** | not built, or not verified |
| Against measurement | **none at any level** | everything so far is verification |

The single-channel full-void worth is not the core void reactivity. That also depends on leakage,
the rod pattern and the axial power shape: exactly the parts still to build.

**Reordered Tier A** (PROJECT_PLAN.md roadmap; TIER_A_WORKPLAN.md):
- **A6** — CPS channel cells, on the A′ basis (`A6_CPS_PLAN.md`).
- **A6b** — Xe axis + fuel COMPO rebuild with `EXTR` depletion. Unit 4 was heavily
  Xe-poisoned at 01:23.
- **A6c** — Smolensk-3 cold start-up ([BEH96]), promoted from the deferred Phase D: the first
  measured core-level reference.
- **A6d** — Unit 4 initial state at 01:22:30 as a sourced deliverable. It is likely the dominant
  uncertainty in A8.
- **A7, A8, A9** — then Tier B. A8 now runs under bracket variants A′ and B, stops at a sourced
  fuel-failure criterion, and is compared (not tuned) with INSAG-7 Appendix II's three
  reconstructions.

---

## A6: the CPS channel — 2026-09-27

Work order `A6_CPS_PLAN.md`. Branch `tier-a/a6`, six commits, nothing pushed. The rod cells are
built and verified against an independent method; the step that turns them into core data is
where it breaks, and the cause is identified rather than papered over.

### A6.1 — the sources

| Input | Value used | Source / status |
|---|---|---|
| Absorber | B₄C in an aluminium sleeve, САВ-1 alloy | closed: [SF] + [OST] agree on the alloy |
| B₄C density | 2.0 g/cm³, bracket **1.7–2.3** | **found in no source.** The single largest open input for rod worth |
| Displacer graphite | 1.65 g/cm³, bracket 1.50–1.73, grade GR-93 | [CAST] |
| Additional absorbers in Unit 4, 1986 | one | INSAG-7 printed pp. 67 and 107 |
| Rod and displacer geometry | as in `openmc/cps_common.py` | [D], [SF] |

Status **PASSED**, with the B₄C density and the rod types carried as open inputs for A8's
sensitivity rather than guessed at.

### A6.2 — one transcription, two codes

`openmc/cps_common.py` is the only place the CPS channel is written down. It generates the DRAGON
library and geometry procedures, the A6.3 supercell decks, the A6.4 COMPO decks, the DONJON gate
decks and the OpenMC supercells, so the two codes cannot drift apart by transcription. It reads
the Zr-2.5Nb composition out of `RbmkLib.c2m` by regex rather than copying it (standing rule 6).
`openmc/rbmk_cell.py` was refactored so the single cell and the supercells share `fuel_cells()`;
the refactor is bit-identical on k (1.3138603888586933 vs …668).

**GATE A6.2 passed.** The 3×3 FUEL-centre supercell reproduces the single cell to **+2.8 pcm**
in DRAGON and **+2 pcm** in OpenMC (1.31638 vs 1.31635).

### A6.3 — section worths against OpenMC, and the A′ correction

`python openmc/cps_verify.py table`. Worths are Δρ(type − WAT) on the 3×3 supercell; "prod" is the
production settings, "conv" is 4× mesh with MOC P1.

```
 BU   dca     worth  OpenMC   sd    prod    conv  prod%  conv%  A-corr
  0  0.72   ABS-WAT   -7511   26   -8706   -8236    -16    -10    +470
  0  0.72   DSP-WAT   +3285   22   +3000   +3084     -9     -6     +84
  0  0.72  VOID-WAT   +4363   21   +3954   +4112     -9     -6    +158
  0  0.02   ABS-WAT  -10236   26  -11764  -10834    -15     -6    +931
  0  0.02   DSP-WAT   +4209   22   +3702   +3762    -12    -11     +60
  0  0.02  VOID-WAT   +5397   21   +4703   +4796    -13    -11     +93
 10  0.72   ABS-WAT   -8955   32  -10454   -9890    -17    -10    +564
 10  0.72   DSP-WAT   +3964   29   +3553   +3671    -10     -7    +117
 10  0.72  VOID-WAT   +5155   28   +4644   +4857    -10     -6    +214
 10  0.02   ABS-WAT  -12158   36  -13873  -12766    -14     -5   +1107
 10  0.02   DSP-WAT   +4871   29   +4258   +4360    -13    -10    +102
 10  0.02  VOID-WAT   +6189   29   +5317   +5463    -14    -12    +147
```

**GATE A6.3 missed, now on the complete table** (the last two converged states landed
2026-09-29 after ~44 h each on `spark`). Production DRAGON is 9–17 % low on every section worth.
Convergence closes roughly half the absorber gap but leaves 5–12 %, so the 5 % criterion is met
in one of twelve cells. Per the standing decision for Gate A, the residual is **attributed and carried, not
fitted**: the production-minus-converged difference is the A′ correction for CPS sections,
+60 to +1107 pcm, tabulated per state.

The sign is consistent with everything found in the method-convergence segment — DRAGON
under-predicts reactivity differences that depend on resonance absorption and on flux depression
next to a strong absorber — and with [PAR07]'s independent −21 % against MCNP.

**The 3×3 supercell is not spatially converged either.** A wider OpenMC supercell moves the
worths substantially:

```
Supercell shape (OpenMC r45 minus 3x3 worth), fresh, pcm
  dca 0.72: ABS-WAT   -1236  DSP-WAT    +471  VOID-WAT    +648
  dca 0.02: ABS-WAT   -1748  DSP-WAT    +616  VOID-WAT    +829
```

The rod's influence reaches past the first ring of fuel. That is not an error in the supercell —
the core solve is what resolves it — but it is the same physics that breaks A6.4 below, and it
sets the scale of the neighbour effect: of order 1000 pcm, not 100.

**Where the residual actually lives — 2026-09-28.** A worth is a difference of two k's, so a
worth error says nothing about *which* of the two states is wrong. Comparing absolute supercell
k does (`cps_verify.py table`, last block):

```
 BU   dca  type  OpenMC k    prod k   d_rho    conv k   d_rho
  0  0.72   WAT   1.24292   1.24995    +452   1.24437     +93
  0  0.72   ABS   1.13679   1.12728    -743   1.12868    -632
  0  0.72   DSP   1.29584   1.29864    +167   1.29402    -108
  0  0.72  VOID   1.31418   1.31493     +43   1.31147    -157
  0  0.02   WAT   1.24752   1.25718    +616   1.25665    +582
  0  0.02   ABS   1.10626   1.09520    -912   1.10607     -15
  0  0.02   DSP   1.31665   1.31854    +109   1.31901    +136
  0  0.02  VOID   1.33757   1.33619     -77   1.33725     -18
 10  0.72   WAT   1.04025   1.04557    +489   1.04090     +60
 10  0.72   ABS   0.95161   0.94254   -1010   0.94375    -875
 10  0.72   DSP   1.08499   1.08591     +78   1.08225    -233
 10  0.72  VOID   1.09920   1.09892     -23   1.09633    -238
 10  0.02   WAT   1.05277   1.05934    +589   1.05882    +543
 10  0.02   ABS   0.93331   0.92360   -1126   0.93274     -66
 10  0.02   DSP   1.10967   1.10938     -24   1.11006     +31
 10  0.02  VOID   1.12615   1.12256    -284   1.12383    -183
```

Converged DRAGON reproduces OpenMC's **displacer and drained-channel** supercells to 100–240 pcm.
The −7 to −10 % worth errors are almost entirely the **WAT baseline being 450–620 pcm too
reactive**, and at voided coolant the converged settings do not touch it at all (+616 → +582).
The absorber is a separate, genuine −630 to −1130 pcm over-absorption.

So A6.3 is not one diffuse method gap but two specific findable things, and the larger of them
sits in the water-filled CPS channel — a single cheap cell, not a 30-hour supercell. That
reopens the gate as something to close rather than attribute.

**The WAT/VOID pair is already the isolating experiment.** `SECTIONS['WAT']` and
`SECTIONS['VOID']` are the *same* geometry — one annulus out to the tube, split four ways —
differing only in whether it holds water or helium. Same Zr tube, same graphite, same eight fuel
neighbours. Water is 450–620 pcm off; helium is 43 to −157. The error is in the water column and
nothing else.

**First hypothesis: eliminated.** The draglib carries `H1_H2O` at only 293.6 / 350 / 400 / 450 /
500 / 600 K, and `LIBDRA.f:68` interpolates cubically in √T (`NOTX=3`), so the nominal 323.15 K
sits 29.5 K off the nearest node in the steepest part of the bound-hydrogen kernel — while
OpenMC's `c_H_in_H2O` has points at 320 and 324 K. That is a clean mechanism, and it is wrong.
Running both codes with the CPS water at exactly 293.6 K, where `LIBLEX.f:46` returns `TERP = 1`
and DRAGON interpolates nothing at all (`rbmk_cps_a63_twat.x2m`, and the matching OpenMC cases):

```
Track C: CPS water on a draglib temperature node vs interpolated
  dca   T_wat    DRAGON    OpenMC   d_rho
 0.72  323.15   1.24995   1.24292    +452
 0.72  293.60   1.24788   1.24000    +509
 0.02  323.15   1.25718   1.24752    +616
 0.02  293.60   1.25453   1.24360    +701
```

The gap does not close at either density; it grows, 452 → 509 and 616 → 701. Temperature
interpolation of the thermal scattering law is **not** the mechanism. The CPS water temperature
stays a free argument only because the test needed it.

**What the completed table points at instead.** With all twelve converged states in, the
residual has a structure that a single localised data error would not produce — convergence
fixes each state at one coolant density and not the other, and the two types fail on opposite
sides:

| | dca 0.72 | dca 0.02 |
|---|---|---|
| WAT, converged | **+93 / +60** (fixed) | +582 / +543 (untouched) |
| ABS, converged | −632 / −875 (barely moved) | **−15 / −66** (fixed) |

So it is not "the water column is wrong". It is that the converged settings — 4× mesh, MOC with
P1, finer tracking, all changed together — help the water when the surrounding fuel is wet and
help the absorber when it is voided. Both are spectral: what changes between dca 0.72 and 0.02
is how hard the thermal flux is driven into the CPS channel from outside.

Next candidates, in order: separate the converged bundle, since it changes four things at once
and the answer is evidently in which one (cheapest first — mesh alone, then MOC alone); the
transport treatment of the column, production being collision probabilities with a transport
correction through 8.2 cm of bound hydrogen; then the multigroup thermal scattering data.

### A6.4 — the homogenisation is exact; the neighbour data is not

`python openmc/cps_verify.py a64`, 18 states (BU 0 / 10.9 / 15 MWd/kg × dca 0.72 / 0.35 / 0.02 ×
T_F 900 / 1500 K). Two configurations of the same DONJON supercell:

| Configuration | vs DRAGON's supercell |
|---|---|
| **A64S** — all nine cells from the CPS MULTICOMPO | **≤ 0.1 % on every worth, ~1 pcm on k** |
| **A64V** — the eight fuel cells from the fuel COMPO (what the core will do) | absorber −2.5 to +2.6 %, displacer **−7 to −9 %**, drained channel **−9 to −10.5 %** |

So the two-group collapse, the SPH equivalence and the DONJON solver are all exact. The entire
error is the neighbour data: an infinite-lattice fuel cell is not a fuel cell sitting next to a
rod, and the fuel COMPO has no axis that could know which it is. It is worst on the *positive*
worths — the displacer effect the whole of A8 turns on — so it cannot be carried as a correction
and ignored.

One detail worth keeping: the absorber error **changes sign with coolant density** (−2.5 % at
0.72, ≈ 0 at 0.35, +2.4 % at 0.02) and passes the 1 % gate at 0.35 by coincidence. A correction
table fitted at one density would have the wrong sign at another. The displacer and void errors
do not change sign and barely move with burnup or fuel temperature, which is what makes them look
like a fixed geometric defect rather than a data-range problem.

Two method choices were settled on the way, neither by fitting:

- **SPH normalisation `ASYM 1`** (pin a fuel cell's factor to 1, so the rod cell carries the
  correction) over `STD` (average over all nine). Chosen on that principle; it also happens to be
  3× better.
- **`TRIVAT: DUAL 1 1`, not the core's `MCFD 1`.** Under MCFD the SPH iteration oscillates and
  never converges in 200 iterations under any normalisation, and on the full deck it ended in a
  segfault in `TRI1GSO`. DUAL converges in 18–41. A2 chose MCFD for speed, before any rod cell
  existed; **from A6.5 on the core must use the discretisation SPH was computed with.**

**How much that second choice was worth — 2026-09-28.** The gate decks had been computing an
MCFD variant (`A64M`) all along and nobody had read it out. Over all 18 states
(`cps_verify.py a64`, last block):

```
  DISCRETISATION: worth error vs DRAGON over all states, %
      worth        DUAL 1 1 (A64V)          MCFD 1 (A64M)
    ABS-WAT           -2.8 to +3.2         +30.6 to +34.4
    DSP-WAT           -9.1 to -6.8           -7.2 to -1.1
   VOID-WAT          -10.5 to -8.5           -5.0 to +3.1
```

**`MCFD 1` loses a third of the absorber worth**, consistently, at every burnup, coolant density
and fuel temperature. One mesh-centred point per 25 cm node cannot represent the flux depression
in a black absorber. The switch was adopted to make SPH converge; it turns out to be mandatory on
accuracy grounds, and the old setting would have cost ~1/3 of all-rods-in worth without ever
failing a gate.

**The control, and it closes the question harder than the number does.** `A64M` applies
DUAL-derived SPH factors to an MCFD solve, so part of that 31 % could have been the mismatch
rather than MCFD itself. `rbmk_cps_a64_smkm.x2m` is the same smoke deck with SPH computed under
`MCFD 1` too — identical transport (both print k∞ 1.127280), differing only in the discretisation
the equivalence is built on:

| SPH discretisation | outcome |
|---|---|
| `DUAL 1 1` | oscillation warnings early, **converged in 40 iterations** |
| `MCFD 1` | oscillates from iteration 5, hits the 200 cap, `SPHEQU: MAX. NUMBER OF ITERATIONS IS REACHED` |

So there is no clean MCFD number to quote, because **MCFD cannot carry a converged SPH
equivalence on this geometry at all**. The 31–34 % is the best available measure of what it
costs; the operative fact is that the core could not have used MCFD with rod data whatever the
size of the error.

**And it costs nothing to leave.** `decks/Donjon/data/rbmk_core_3d_dual.don` is
`rbmk_core_3d_realistic.don` with the tracking line changed and nothing else (still A2's
wrong-on-purpose IAEA constants — this is solver timing, not physics). Matched runs, same
machine, same day:

| solver | wall | max RSS | k | unknowns/group |
|---|---|---|---|---|
| `MCFD 1` | 1.95 s | 39 MB | 1.123062 | — |
| `DUAL 1 1` | 2.11 s | 56 MB | 1.123053 | 263 329 |

**8 % more wall clock and 17 MB.** A2's note that `DUAL 3 3` took 729 s against MCFD's 1 s had
made the mixed-dual family look unaffordable; `DUAL 1 1` is not `DUAL 3 3`. A8's transient
multiplies this by a few hundred steps and remains cheap, and 56 MB raises no memory question.

The two also agree to **0.7 pcm** on this rod-free core — which is the other half of the control.
MCFD is not generally wrong; it fails specifically when a black absorber sits inside a node,
which is exactly the claimed mechanism.

### A6.4b — the rod-cell equivalence, chosen after measuring the alternatives out

DRAGON's built-in normalisations were exhausted first, on the smoke case (DRAGON 1.126503):

| SPH normalisation | A64V error |
|---|---|
| `ASYM 1`, nine cell regions | **+135 pcm** |
| `STD`, nine cell regions | +394 pcm |
| `ASYM 1`, fuel merged to one region (`MERG CELL … REMIX`) | +254 pcm |
| `SELE_FD` / `SELE_EDF` / `STD_FISS` | refuse: no ADF directory in the macrolib |

Merging the fuel is *worse*, because the rod's factor then compensates against an eight-cell
average that matches the per-cell fuel COMPO even less well. Discontinuity factors (the textbook
fix, and DONJON reads them at `NCRLIB.f:561`) need `EDI: … ADF`, which wants named boundary
regions; our cells have no gap mixture, so the outermost graphite ring would have to serve.

**Decision: an explicit equivalence on the rod cell alone.** Per-group factors, computed per
state, that make the DONJON supercell reproduce DRAGON's with the fuel data the core actually
uses. The fuel COMPO stays untouched and there stays one dataset per rod type.

> **Corrected 2026-09-28, before anything was built.** The implementation first recorded here —
> a `SPHPicardRT`-style loop, then `SPH: <compo> OPTIM :: IDEM SPOP EQUI 'EQV_CPS'` to store the
> factors in the CPS MULTICOMPO — **would have aborted.** A read of the vendored source settles
> three things:
>
> - **`EQUI` is rejected for a MULTICOMPO.** `Dragon/src/SPH.F:440-442` aborts unless the
>   database is a SAPHYB or an APEX/MPO. What a MULTICOMPO does instead (`SPH.F:801-806` →
>   `SPHSCO.f`) is bake the factors *destructively* into the stored cross sections of that
>   calculation point — unnamed and one-way. For us that is the wanted behaviour, because the
>   CPS COMPO holds nothing but rod cells, and `NCR:` then needs no change at all.
> - **`FPSPH:` really has no mixture selection.** Its whole vocabulary is `EDIT`, `SPH PN|SN`,
>   `GRPMIN`, `GRPMAX`, `OUT-STEP-EPS`, `VAR-VAL-MIN`, `VAR-VAL-MAX`, `OUT-CONV-TST`, `ANDERSON`
>   (`FPSPH.f:192-265`); anything else hits `XABORT`, and its normalisation averages over every
>   mixture (`FPSPH.f:324-336`). Neighbours can only be held at 1 by pre-seeding per-variable
>   bounds through `UTL: OPTIM :: CREA` (`FPSPH.f:271-284, 386-389`).
> - **`SPH: … MACRO SPRD <nmerge> <ngcond> <values>`** (`SPH.F:325-348`) applies an explicit
>   per-mixture, per-group table with no optimiser at all. That is the clean lever, and it is
>   what the rod-cell equivalence will use.
>
> One trap recorded so it is not walked into twice: `ASYM <mix>` pins a mixture's factor to 1
> exactly, so merging the eight fuel cells into one macro-mixture and using `ASYM 2` looks like
> the answer. It is not — it still normalises against DRAGON's *own* fuel data, not the fuel
> COMPO's, which is the whole problem. The measurement above already shows that merge is worse.

**The plan, as corrected.** Solve the two per-group factors directly — two unknowns against two
conditions (the rod cell's group-wise volume-integrated flux, as DRAGON's transport supercell
gives it), with k left free as the check, since every worth is a k difference. Apply trial
factors through `SPRD`, drive the loop from Python (the 3×3 two-group DONJON solve takes
milliseconds), and cross-check the smoke case against upstream's own `FPSPH:` machinery with the
neighbour variables clamped. Persist by applying the converged table with a second
`SPH: EDIOBJ :: IDEM SPRD …` in the A64 DRAGON deck before `COMPO:` stores it.

### A6d — the Unit 4 channel map, from registering two digitisations

**The cartogram.** Dollezhal & Emelyanov Fig. 2.3 (Leningrad-2's initial loading) is the first
sourced RBMK core cartogram in the project. The legend OCR was deciphered and cross-checked
against the body text; the figure was then hand-digitised into `sources/derived/core_layout.xlsx`
and read back by `tools/render_core_layout.py`, which also draws a layered overlay SVG for
checking against the scan. Six digitisation errors were found by mirror and rotation symmetry
checks and each was confirmed on the scan. After correction every count closes against
Dollezhal's own text:

```
  technological channels     digitised  1693   text  1693   OK
  CPS rods                   digitised   179   text   179   OK
  DKE(v) channels            digitised    12   text    12   OK
  start-up chambers (KD)     digitised     4   text     4   OK
```

with rod types 89 РР, 21 УСП, 12 АР, 21 АЗ and 36 АЗ over-compensation — and the 21 УСП and
21 АЗ independently match INSAG-7 p. 43, which was not used to build the digitisation. One
disagreement is recorded and left standing: 282 fuel channels carry a radial detector in the
figure against 270 in the text. The overlay shows no mismatches that could account for twelve,
so it is a figure/text difference in the source.

**The registration, which is the real result.** `tools/build_unit4_map.py` places INSAG-7
Fig. II-6 (Unit 4 at 01:22:30, digitised separately by glyph detection in
`tools/digitise_fig_II6.py`) onto the Fig. 2.3 lattice. It fits **exactly**: all 223 sites at a
single offset (1, 1), nothing left over on the Unit 4 side. Two figures, twelve years and two
reactors apart, digitised by different means — each is now a check on the other.

What falls out:

- Fig. II-6's 12 blank sites are Fig. 2.3's 12 ДКЭ(в) axial-detector channels. All twelve. That
  had been an inference; it is now a measurement.
- Unit 4's 211 rods sit on Leningrad-2's 179 rod sites plus 32 that Leningrad-2 used for
  additional absorbers, unloaded channels and one fuel channel. 179 + 32 = 211, the second-stage
  rod count, with no site left to guess at.

```
  rods                 211 vs   211  OK   INSAG-7 pp. 43, 103
  fuel channels       1661 vs  1661  OK   [PAV] Table 1
  DKE(v)                12 vs    12  OK   [D] p. 57
  start-up chambers      4 vs     4  OK   [D] p. 57
  positions           1888 vs  1888  OK   sum of the above
  47 rods inserted at 01:22:30, 4346 cm in total
```

None of those five counts was an input to the map. `sources/derived/unit4_channel_map.csv` is the
deliverable. **What is still an assumption** is not *which* sites hold rods — that is measured —
but what *type* the 32 extra rods are. INSAG-7 p. 43 gives second-stage units 24 АЗ and 24 УСП
against Leningrad-2's 21 and 21, so at least 3 + 3 of the 32 are АЗ and УСП and the rest are
manual by elimination. The choice is recorded per row in `type_source` so A8 can vary it.

This also unblocks A6.5, which had been stopped by the core generator: its core is the 1661 cells
nearest the centre of a 590 cm circle, and no centred circle reproduces 1888 interspersed
positions, because circle cell counts step by 8.

### The depletion grid, and the COMPO rebuilt on it

A regression of my own, caught by the interpolation gate: the rebuilt COMPO grid had dropped the
500 MWd/t node, so the opening depletion step ran 0 → 2000. With `EXTR 1` extrapolating from the
step history, that put the whole trajectory 45–75 pcm below the `dstep25x` reference. Restoring
the node brought the rebuild to **1 pcm** of it (1.007263 vs 1.007262 at 15 MWd/kg). The opening
step matters more than any later one.

Gates on the rebuilt 840-point COMPO: **round trip 0.9 pcm** (was 6.7), **off-grid 23.9 pcm**,
β monotone 0.006822 → 0.004677. The void bracket is essentially unchanged by the rebuild:

| BU, MWd/t | A | A′ | B | A $ | A′ $ | B $ |
|---|---|---|---|---|---|---|
| 0 | +560 | +764 | +821 | +0.82 | +1.12 | +1.20 |
| 10 000 | +901 | +1145 | +1276 | +1.69 | +2.14 | +2.39 |
| **10 900** (Unit 4 average) | **+1024** | **+1273** | **+1437** | **+1.94** | **+2.41** | **+2.72** |
| 15 000 | +1666 | +1932 | +2254 | +3.35 | +3.88 | +4.53 |

### Machinery and traps found along the way

Recorded because each cost real time and each is a statement about the input, not the tool
(standing rule 3):

- `EDI: MERG CELL` with NXT tracking merges the cells but **builds no macro-geometry**
  (`EDI.f:449`); `MGEO` must be supplied explicitly.
- `SEQ_ASCII _CCompo ;` without `:: FILE './_CCompo'` is a **scratch file, deleted at `END:`**.
- `LIB:` accepts `MIX` blocks only after a `MIXS` line (`LIB.f:451`), even on an update.
- `MIXTURESVOL` is written only by the micro edit (`EDIMIC.f:925`), so the volume-fraction
  guardrail needs `MICR ALL`.
- The `MERG MIX` list must run to the highest mixture index in the geometry.
- CLE-2000 reads **columns 1–120 only** (`clelog.c:31`); the generator now asserts it and names
  the offending line.
- `rdragon` races on `/tmp/rundirN` when decks are launched simultaneously; stagger by ~10 s.
- A parser bug of my own: the CPSTAB type index prints as a bare integer, not in E-format, so the
  DRAGON columns of the A6.3 table were silently empty for a while and percentages I had quoted
  from hand arithmetic were withdrawn. The table above comes from the script.

### Where this leaves the core model

| Piece | State |
|---|---|
| Fuel-cell physics | verified in two codes plus a third-party benchmark; bracketed |
| CPS cell physics | built, verified against OpenMC, **5–11 % low and attributed** |
| CPS core data (homogenised) | **blocked on A6.4b**, −7 to −10 % on the positive worths |
| Channel map | **sourced and closed**, except the type of 32 rods |
| Core geometry and rod sites (A6.5) | unblocked, not built; needs the `DUAL 1 1` switch |
| Xe axis (A6b) | not built. Unit 4 was heavily poisoned at 01:23 |
| Measured core-level reference (A6c) | **blocked**: the Behrens/Kurchatov 1993–94 Smolensk-3 loading map is not available online |
| Coupling, transient, detectors (A7–A9) | not started |

Confidence at core level is still *none* — everything to date is verification, not validation
against measurement. The single-channel void worth is not the core void reactivity; that also
depends on leakage, the rod pattern and the axial shape, which are exactly the parts A6.5 onward
build.

**The converged runs are in.** `fresh_conv_ABS` and `oed10_conv_VOID` finished on `spark` after
roughly 44 h each (two coolant densities apiece), and the A6.3 table above is complete for the
first time. They changed nothing about the verdict — the A′ trend was already established by the
other ten — but they close the gate properly rather than on ten twelfths of the evidence.

Nearly all of that time is `FLU:`: MOC source iteration converging slowly next to B₄C with one
inner per outer in the upstream template. The cost sits in the tracking — the converged decks use
`TISO 30 120.0` against production's `TISO 15 30.0`, on 4× the mesh with `ANIS 2` — and
`cps_common.py` already exposes both knobs, so a convergence ladder on one cheap state is the way
to stop paying 44 h for a data point.

---

## Should we port DRAGON/DONJON out of Fortran? — assessed 2026-09-29

Recorded because the question will come back, and because the answer is not the obvious one.
Prompted by how often this project has been slowed by something that looked like a Fortran or
CLE-2000 limitation.

**Scale.** ~407 000 lines across Ganlib 19.5k, Utilib 13.6k, Trivac 57.2k, Dragon 239.8k,
Donjon 76.9k, plus 920 shipped `.c2m` procedures. Inside Dragon: `LIB` 31.7k, `NXT` 29.7k,
`EDI` 12.0k, `SPH` 6.7k, `USS` 6.3k. Against that, **the CLE-2000 interpreter is 8 220 lines —
2 % of the tree.**

**But the difficulties are mostly not the language.** Sorting every obstacle this project has
actually hit:

| class | count | examples |
|---|---|---|
| Fortran the language | 3 | the `TRI1GSO` segfault; `SPH.F:377` and `SPH.F:818` using unassigned integers (implicit typing, `-O1`, no warnings) |
| CLE-2000 the language | 4 | the 120-column limit; 12-character procedure names; `MODULE` declarations; `ERROR NUMBER (5000)` naming nothing |
| the shell drivers | 2 | `/tmp/rundirN` races; stale `.result` files |
| **the domain model** | **6** | `MERG CELL` + NXT building no macro-geometry; `MIXTURESVOL` only under `MICR ALL`; `LIB:` needing `MIXS` first; `B-ZONE` being an NCH-list not a grid; `FPSPH:` having no mixture selection; `SPH: … EQUI` rejected for a MULTICOMPO |

The last group is where the days went, and **a rewrite reproduces every one of it** unless it
also redesigns the physics data model — which is the actual hard part and is orthogonal to
language choice. The pain has been epistemic, not syntactic.

**What makes a port expensive is not the code.** DRAGON's value is thirty years of comparison
against measurement; a port starts at zero validation. This project has just spent a whole
segment establishing agreement with OpenMC on one cell type and is still 5–12 % out on the CPS
sections. Revalidating a ported lattice code is a bigger job than writing it. And the
performance argument is weak: the bottleneck is `FLU:` MOC source iteration, which well-tuned
Fortran wins — and we are still compiling at `-O1` with no `-march=native`.

**The ladder, and where we already are on it.**

0. Replace the shell drivers — trivial, partly done.
1. **Never hand-write CLE-2000; generate it.** `cps_common.py` and `gen_rbmk_unit4.py` already
   do, and it converts the whole syntax class into generator assertions: the column-120 failure
   of 2026-09-28 was caught by an `assert`, named its own line, and cost two minutes.
2. **Stop parsing `.result` text.** This is the remaining fragility — the CPSTAB parser silently
   matched nothing for a day, and the variant-overwrite bug in `cps_verify.table` was the same
   species.
3. **Rewrite the nodal core solver** — Tier B. Small, well understood, and validated against
   DONJON itself. Worth doing; already the plan.
4. Rewrite lattice transport — multi-year, no payoff.

**The unused lever: `5.1/PyGan/`**, in our tree and unbuilt. Upstream's own Python binding to the
Ganlib object stack: push objects onto a LIFO, call modules, get LCM objects back subscriptable
(`Fmap["STATE-VECTOR"]`). That is rung 2 and most of rung 1 while keeping every Fortran kernel
and its validation, and it would have made the `MIXTURESVOL` and `B-ZONE` discoveries a `dir()`
instead of a source read. Half a day to try building it (C extension modules against the
Fortran, so it may fight back) before entertaining any port.

**Decision: do not port.** Build PyGan, finish moving deck generation and result parsing into
Python, turn on `-O3 -march=native`, and spend the rewrite budget on Tier B, where a new
implementation has a clear validation reference and a real reason to exist (GPU, 10 Hz). The one
thing worth coveting from Julia — autodiff for adjoint and sensitivity work in A8 — is worth
revisiting only if uncertainty analysis becomes the bottleneck.

---
## Phase 0 of the transient: what a time step costs — 2026-09-30

Everything built until now was static. This is the first time the model has advanced a time
step, and the point was to find out what one costs before A8's design is built around a guess.

Three decks, all from one generator (`decks/Donjon/data/gen_kin_probe.py`) that reads
`rbmk_core_3d_dual.don` so the geometry stays single-sourced: `rbmk_kin_probe` (step form),
`rbmk_kin_ramp` (the 6-entry ramp form, keeping `MACRO_0`/`SYST_0`), and `rbmk_kin_pert`
(macrolib rebuilt and ramped every step). Cross sections are still the wrong-on-purpose IAEA
PWR constants of A2 — this measures the solver, not the reactor.

Two things had to be added to make `KINSOL:` run at all, and both are worth recording because
neither is documented where a reader would look:

* **`OVERV`, the reciprocal neutron speeds.** `KINXSD.f:152` aborts with `MISSING OVERV DATA`
  and `MAC:` supplies no default. The probe carries textbook two-group values; A8 will not
  need them, because `EDI:` writes `OVERV` (`Dragon/src/EDIPXS.f`) and `NCR:` propagates it
  (`Donjon/src/NCRMAC.f`), so the real speeds arrive from the MULTICOMPO. That path was
  checked in source before relying on it.
* **`UNIT` on `TRIVAA:`** (`TRIVAA.f:174`). It only *adds* a unitary weighting matrix, so one
  system object still serves `FLUD:` as well — no second assembly is needed.

### The measurement

`tools/kin_cost.sh`, regenerating `decks/Donjon/data/kin_cost.txt`. Each variant runs at 10 and
at 110 steps and the per-step cost is the **difference**, which cancels the fixed setup
(geometry, tracking, the `FLUD:` eigenvalue solve) exactly rather than estimating it.

| variant | s/step | max RSS | what it is |
|---|---|---|---|
| frozen-step | 0.0903 | 90.3 MB | macrolib frozen, 4-entry `KINSOL:` |
| frozen-ramp | 0.0911 | 104.7 MB | macrolib frozen, 6-entry form |
| mild-mix4 | 0.0967 | 88.0 MB | bottom inner reflector ramped; power moves 2.4e-4 |
| **severe-mix1** | **0.4301** | 88.0 MB | fuel absorption ramped; power falls 3200 → 16 MW |

**The finding that matters: a hard transient costs 4.8× a quiet one.** The first two variants
flatter the solver — with a frozen macrolib `KINSOL:` starts each step from the exact answer and
converges immediately. Quoting 0.09 s/step would have understated A8 by five-fold. Only the
severe variant is a usable number, and it is the one the budget should use.

Also measured: the **ramp form costs +14.4 MB and no time at all**, so A8 can use it freely;
and `TRIVAA:` re-assembly is ~3 ms against `KINSOL:`'s hundreds, so rebuilding the system every
step — which A8 must do, since its cross sections change every step — is not where the cost is.

### What it means for A8

4 s of transient at 1 ms is 4000 steps ≈ **29 minutes of neutronics**. At the 8–12
thermal-hydraulic Picard iterations per step that `channel_mphy.x2m` uses, that is **roughly 4
hours per scenario**, 8 for both bracket variants, plus `THM:` on 1661 channels, which is not
yet measured. A8 is hours, not days. **Tier B stays parallel rather than urgent**, which is the
question Phase 0 existed to answer.

Memory never exceeded **105 MB** in any variant, against the ~110 GB budget. The transient is
not a memory risk; the only component that could be is the Tier B GPU solver, and the arithmetic
for that is in the plan.

### Two correctness checks, not one

Nothing about the cost would be trustworthy if the kinetics were assembled wrong, so the decks
check themselves:

1. **The unperturbed transient holds power.** 3200.000 → 3199.550 MW over 110 steps, a drift of
   1.4e-4 relative — the residual of `FLUD:`'s own `EXTE 1.0E-5` convergence, not a defect.
2. **The severe transient obeys the prompt-jump relation.** Step 1 takes 3200 → 2674 MW. With
   the deck's β = 0.007219, P/P₀ = β/(β−ρ) gives ρ = −0.20 $ for that first step, and the
   power then decays on the precursor timescale rather than collapsing. Both the size of the
   prompt drop and the shape of what follows are right, which is stronger evidence than the
   flat-power check alone.

The pre-existing `FLDDIR: FAILURE OF THE NEWTON-RAPHTON ALGORIHTHM` warning appears once in
these results and once in `rbmk_core_3d_dual.don.result` — it predates the kinetics work and is
not a regression from it. k = 1.123053 against the static deck's 1.123062, 0.9 pcm apart and
inside the flux tolerance.

**Not yet established:** every number here is on IAEA PWR constants in an RBMK-shaped box. The
per-step cost should hold — it is set by the matrix structure, which the real cross sections do
not change — but the iteration counts could move, so A8 re-measures rather than assuming.

## A6.4b: the rod-cell equivalence cannot work, and here is why — 2026-09-30

The design recorded in `A6_CPS_PLAN.md` and in the A6 section above is **disproved**. Not
abandoned for effort — measured, and it fails. Three results, in the order they were found;
everything regenerates from `openmc/a64b.py` and is recorded in `openmc/a64b_findings.txt`.

### The machinery works, and was proved to before anything was built on it

`SPH:` and `OUT:` are not in DONJON's own module table (`DONDRV.F`), but `DONDRV` falls
through to `KDRDRV` and both symbols are in the binary. Confirmed on the cheapest state there
is (`rbmk_cps_a64b_smk.don`):

* `SPH: <macrolib> :: MACRO SPRD <nmix> <ngrp> <values>` applies an explicit per-mixture,
  per-group table, values in mixture-major order (`SPH.F:325-348`). **Proved applied rather
  than silently ignored by a pair of runs**, because all-factors-1.0 alone proves nothing —
  an ignored `SPRD` would also leave k unchanged. All 1.0 reproduces k exactly; 1.05/0.95 on
  the centre moves it +208 pcm. Only the pair is conclusive.
* `OUT: FLUX TRACK MACRO GEOM :: INTG MIX` integrates over the geometry's `MIX` zones
  (`OUTHOM.f:162`) and prints VOLUME, FLUX-INTG, NTOT0, SIGW00 per zone per group. Give it no
  `COND`, or it silently condenses to one group.

The new tooling reproduces the previously recorded A6.4 failure to the decimal — ABS −3.24 to
+2.84 %, DSP −9.10 to −6.72 %, VOID −10.56 to −8.48 % — which is the check that it is measuring
the same thing the old measurement did.

### 1. The recorded target is the wrong target

Solving the two rod-cell factors against the rod cell's group-wise volume-integrated flux
converges cleanly — three Newton iterations, factors remarkably consistent across all 18
states (ABS: f₁ 0.956–0.959, f₂ 0.910–0.928) — and **makes the gate worse**:

| worth | at unit factors | flux-matched |
|---|---|---|
| ABS | −3.2 to +2.8 % | −9.6 to −4.4 % |
| DSP | −9.1 to −6.7 % | −13.7 to −9.3 % |
| VOID | −10.6 to −8.5 % | −14.2 to −10.1 % |

The reason is not subtle once seen. **SPH equivalence preserves reaction rates, not fluxes.**
The rod cell's flux is low because its *neighbours* are wrong; forcing it up by lowering the
rod's own cross sections buys the flux at the cost of the absorption — and absorption is what
a rod worth is made of. The flux was made right by making the cross section wrong.

Targeting the removal rate instead, `(NTOT0 − SIGW00) × FLUX-INTG`, is the physically correct
invariant and **will not converge**: the residual stalls around 2e-4 through twenty damped
Newton iterations. That is a statement about the physics, not the solver. Raising a black
absorber's cross section depresses its flux almost proportionally, so its reaction rate — and
with it its effect on the core — is nearly invariant to its own SPH factor.

### 2. So no rod-only equivalence can close the gate, at any factor

If the rate is nearly invariant, the worth should be too. Tested directly rather than argued:
sweep the VOID rod cell's two factors over **±20 %**, a 5 × 5 grid, holding the water reference
cell at 1.0, and record the worth error over the whole grid.

```
  bu      0 dca 0.72: REF worth  3954 pcm, err over the grid  -13.26 to  -3.71 %
  bu      0 dca 0.02: REF worth  4702 pcm, err over the grid  -15.27 to  -3.52 %
  bu  10900 dca 0.72: REF worth  4704 pcm, err over the grid  -14.70 to  -3.45 %
```

**The range never straddles zero.** The gate wants 1 %; the best any rod-cell factor achieves
is −3.45 %, and that is at the edge of a deliberately wide sweep. A6.4b as conceived is not
hard, it is impossible.

### 3. What is actually wrong: the neighbours, spectrally

Comparing the supercell's own fuel-cell constants against the fuel COMPO's, cell by cell:

```
 centre VOID, bu 0, dca 0.72      NTOT0 ref   NTOT0 tri      d%
   corner cell (mix 1), group 1     5.89140     6.01834  +2.155
   corner cell (mix 1), group 2     8.33873     8.14683  -2.301
   edge   cell (mix 2), group 1     5.81617     5.84696  +0.529
   edge   cell (mix 2), group 2     8.42977     8.40410  -0.305
```

Two things to read here. First, the neighbour fuel constants differ by **up to ±3 %** — and
this is at **zero burnup**, where the supercell's fuel and the fuel COMPO's fuel are the same
material. So it is not a depletion-history difference; the worth error is fully present at
bu = 0 (VOID −8.48 to −9.56 %) and barely changes by 15 MWd/kg. Second, `NTOT0` and `SIGW00`
shift by almost exactly the same relative amount (+2.155 vs +2.160), so the whole set is
scaled rather than reshaped.

The corner cell — the one *farthest* from the rod — differs *most*, which looks backwards
until you remember `ASYM 1` pins merged region 1, the corner, to a factor of exactly 1. Its
numbers are therefore the raw homogenised supercell values, and they are 2–3 % from
infinite-lattice fuel because **the rod perturbs the spectrum across the whole 75 cm
supercell**. The RBMK's migration length is ~1 m; a 25 cm cell two cells from an absorber is
not in an infinite lattice.

**That is the finding.** This was never a rod-cell problem. The core gives every fuel channel
infinite-lattice constants, including the ~8 neighbours of each of the 211 rods, and fuel next
to a rod genuinely does not have infinite-lattice constants. The error depends on what is in
the centre — water, graphite or helium perturb the neighbouring spectrum differently — which
is exactly why it does not cancel in a worth, and why ABS (±3 %) fares better than DSP and
VOID (−7 to −10 %): the absorber's neighbour perturbation is closer to the water case it is
differenced against.

### Where this leaves A6.4

Two sound ways out, and one that is not.

* **Give the rod's neighbours their own mixtures in the core.** Principled, and the data
  already exists — the CPS MULTICOMPO stores all nine cells, and the core currently uses only
  mixture 5. It is real work: a channel can neighbour more than one rod, it has its own
  burnup, and the correction depends on the rod's insertion state, which moves during the
  transient.
* **Carry it as a measured, one-signed bias**, the way A6.3's residual is carried as the A′
  correction: displacer and drained-channel worth low by 7–10 %, absorber worth within ±3 %,
  mechanism named, present at all burnups, and propagated into A8's uncertainty band.
* **Not acceptable:** fitting the four factors of the rod and reference cells to hit the
  worth. Four parameters against one number is not an equivalence, it is a fudge, and standing
  rule 1 forbids it. It was not done.

A6.4b is closed as a design. The choice between the two survivors is a scoping decision, and
the honest default until A8 shows sensitivity is the second.

## Standing rules

1. **Every asserted value must come from a calculation, never from a constant chosen to
   make the assert pass.** Violating this produced the tuned `MAC:` block.

2. **Every deck must verify what it actually built, not what it was meant to build.**
   Violating this produced a CANDU-6 bundle that survived ~86 deck variants, a full audit,
   and six branch calculations before anyone measured its volume fractions. The check that
   caught it costs one run and eight lines of CLE-2000.

3. **An error message from DRAGON is a statement about the input until proven otherwise.**
   Three separate "tool limitations" were a missing declaration, a 13-character name, and a
   missing colon — each demonstrated correctly in a bundled reference deck.

4. **No physics number is validated until a second, independent method reproduces it.**
   Internal consistency is not validation: the tuned `MAC:` block, the CANDU bundle, and the
   +1957 pcm void coefficient were each internally consistent and each wrong. Rule 2 catches
   *building the wrong thing*; only an independent method catches *computing the right thing
   wrongly*. The CANDU-6 control is the template — run the new method on a case where the old
   one is trusted, before trusting the new method on the case you care about.

5. **A DRAGON `.result` is not evidence unless it postdates the deck.** Delete it before
   re-running. A stale result reporting the previous run's failure is indistinguishable from
   a real one, and it fooled this session's monitor once. Related: `cd X && cmd &` puts the
   `cd` inside the background subshell, so a following command runs from the wrong directory
   and silently does nothing.

6. **A fix that lives in a copy of the file is not a fix.** The bound-hydrogen correction
   existed as `RbmkLibH.c2m` for a full day while `rbmk_cell_a3.x2m` and `rbmk_a5_void.x2m`
   — the only two decks whose numbers were being quoted — kept calling the broken original.
   Six diagnostic decks were written against the corrected copy, which made the fix look
   applied. Correct the file everything calls; if a deliberately-wrong variant is needed for
   a comparison, that is the one that gets the new name and the do-not-use banner.

7. **A cache without a key is a silent substitution.** A derived artifact kept beside its
   source must carry a digest of that source in its name. The decompressed draglib sat in
   the `libraries` submodule for five days after the submodule moved to a different library
   revision, and every run preferred it because it was already there — see the 2026-09-24
   entry. "The file is already there" is not evidence that it is the right file.

---

*Last updated: 2026-09-30 (2) (A6.4b disproved: no rod-only SPH equivalence can close gate A6.4,
shown by a ±20 % factor sweep that never reaches the gate; the cause is the rod perturbing its
neighbours' spectrum by ±3 % at zero burnup, not the rod cell itself; carried as a measured
one-signed bias). Previously: 2026-09-30 (Phase 0 of the transient: `KINSOL:` runs on the full core for the first time; a severe step costs 0.430 s against 0.090 s frozen, so A8 is hours not days and Tier B stays parallel; `OVERV` and `TRIVAA: UNIT` found to be undocumented prerequisites). Previously: 2026-09-29 (A6.3 table complete, gate missed at 5-12 %; MCFD 1 shown to lose 31-34 % of absorber worth and to be unable to carry an SPH equivalence at all, while DUAL 1 1 costs 8 %; the thermal-scattering interpolation hypothesis for the WAT residual eliminated by measurement; Unit 4 core geometry and 1661-channel fuel map generated from the sourced map and accepted by DONJON; recommendation recorded against porting out of Fortran). Previously: 2026-09-27 (A6: CPS cells built and verified in both codes; A6.3 gate missed, residual carried as the A′ correction; A6.4 homogenisation exact but neighbour data 7–10 % low, closing via a rod-cell equivalence; A6d Unit 4 channel map sourced by registering two digitisations, all counts closing; fuel COMPO rebuilt on the corrected depletion grid, bracket +1.94 / +2.41 / +2.72 $ at 10.9 MWd/kgU). Previously: 2026-09-26 (2) (project assessment; Tier A reordered: A6 → A6b Xe → A6c Smolensk-3 → A6d initial state → A7–A9). Previously: 2026-09-26 (Phase C: SHEM-361 + Zr SS production, 840-point COMPO, void bracket +1.95 / +2.42 / +2.72 $ at 10.9 MWd/kgU; depletion step study). Previously: 2026-09-25 (3) (Phase A–B on the GB10: void gap within criterion on both cells; nominal 240 pcm residual attributed; burnup-normalisation convention found; 8× mesh and accident reference pending). Previously: 2026-09-24 (4) (re-baselined in both codes on the closed geometry; the
bracket straddles prompt criticality at the accident burnup, ~0.6 $ DRAGON vs ~2.7 $ OpenMC;
OpenMC β_eff 0.006739 confirms DRAGON to −1.3 %). Previously: 2026-09-24 (3) (cell geometry closed against eight new sources; clad OD 13.58;
k∞ 1.304123 on the pinned library; Unit 4 accident burnup 10.9 MWd/kgU, not 20 — the bracket
needs re-framing). Previously: 2026-09-24 (repo restructured for a clean clone; found that every DRAGON
number below was produced against a draglib the repo does not ship — −87 pcm on the A3 cell,
re-baseline pending — see the 2026-09-24 entry). Previously: 2026-09-23 (3) (A5b full 630-point COMPO built and verified: round trip
6.4 pcm worst, off-grid interpolation 27 pcm worst, β curve 0.006824 → 0.004680 measured and
confirmed against OpenMC to −0.5 %; full-void worth at discharge +4.7 $ (DRAGON) / +8.6 $
(OpenMC) — prompt-supercritical at both ends of the bracket)*
