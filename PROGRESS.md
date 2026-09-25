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

> **2026-09-24 (4): re-baselined in both codes on the closed geometry. The bracket now
> straddles prompt criticality at the accident state.**
> - DRAGON: k∞ 1.304123, COMPO rebuilt (round trip 6.6 pcm, off-grid 26.5 pcm, now reproducible), β curve unchanged.
> - OpenMC: re-run on VIII.1.
> - The geometry fixes cut DRAGON's void worth at every burnup and left OpenMC's nearly unchanged, so the method gap widened.
> - At 10–15 MWd/kgU, where Unit 4 was, full voiding is +0.4–1.65 $ in DRAGON and +2.25–4.6 $ in OpenMC.
> - The ~1.9 multiplier held only at 20 MWd/kg.
> - Resolving the method gap moves ahead of A6. See "Re-baseline on the closed geometry" near the end.

## Objective

3-D spatially-resolved coupled neutronics/TH RBMK-1000 model, driving a historically
accurate **RBMK mnemonic display** (1661 channel outlet temperatures, 211 rod positions,
in-core detector readings). Accident scenario runs to **fuel failure** and stops.

---

## Architecture (three tiers)

| Tier | What | Status |
|---|---|---|
| **A — offline physics** | DRAGON5 lattice → MULTICOMPO → DONJON5 3-D steady + reference AZ-5 transient. Source of truth. | **In progress.** A3/A4/A5a done; A5b (MULTICOMPO export) next, then A6–A9. |
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

## Validated results

| Item | Result | Status |
|---|---|---|
| IAEA-3D benchmark, `Donjon/data/iaea3d_fuelmap.x2m` | k_eff = 1.028980 (ref 1.029069, **−8.9 pcm**) | ✅ Genuine. Standing regression test and the structural template for the core workflow. |
| RBMK lattice cell, `Dragon/data/rbmk_cell_a3.x2m` | **k∞ = 1.304123** (2026-09-24 (3), pinned draglib `cb1395ffbb65`, x86_64) | ✅ Geometry closed against sources, guardrail passed, fractions match analytic. Steps from the last recorded value: 1.310172 → 1.308679 is the library (−87 pcm), → 1.304717 is the Dollezhal carrier and clad (−232 pcm), → 1.304123 is clad OD 13.58 (−35 pcm). Not independently checked: the OpenMC side has not been re-run on this geometry. Earlier: correct RBMK geometry, verified in-deck against design volume fractions. Value is post-hydrogen-fix (2026-09-23) and matches what `rbmk_h2otest.x2m` measured independently; the old free-gas value was 1.312816. |
| Void coefficient vs burnup, `Dragon/data/rbmk_a5_void.x2m` + A5b COMPO | full void at 10 / 15 MWd/kg: **+207 / +819 pcm** (+0.39 / +1.65 $); OpenMC **+1202 / +2288** (+2.25 / +4.60 $). 2026-09-24 (4) | ⚠️ Re-baselined on the sourced geometry. **Sign and trend confirmed by OpenMC; magnitude is not, and the gap widened** (DRAGON fell 150–520 pcm, OpenMC barely moved). At the Unit 4 average burnup, 10.9, the two codes put full voiding either side of prompt critical: ~0.6 $ vs ~2.7 $. See "Re-baseline on the closed geometry". |
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
3. **Measured data.** Alexeev et al., *Nucl. Eng. Des.* 183 (1998) 287: seven Kurchatov RBMK
   critical experiments, where MCNP and MCU matched measured k and void effect and WIMS-D4 did
   not. Getting those specifications is the only way to validate rather than verify.
4. **The production library.** The COMPO, the A5 deck and every downstream number are on the
   172-group library, which this study shows is not converged for this cell. Rebuilding on
   SHEM-361 + Zr is the obvious consequence, but it should wait for (2).

---

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

*Last updated: 2026-09-24 (4) (re-baselined in both codes on the closed geometry; the
bracket straddles prompt criticality at the accident burnup, ~0.6 $ DRAGON vs ~2.7 $ OpenMC;
OpenMC β_eff 0.006739 confirms DRAGON to −1.3 %). Previously: 2026-09-24 (3) (cell geometry closed against eight new sources; clad OD 13.58;
k∞ 1.304123 on the pinned library; Unit 4 accident burnup 10.9 MWd/kgU, not 20 — the bracket
needs re-framing). Previously: 2026-09-24 (repo restructured for a clean clone; found that every DRAGON
number below was produced against a draglib the repo does not ship — −87 pcm on the A3 cell,
re-baseline pending — see the 2026-09-24 entry). Previously: 2026-09-23 (3) (A5b full 630-point COMPO built and verified: round trip
6.4 pcm worst, off-grid interpolation 27 pcm worst, β curve 0.006824 → 0.004680 measured and
confirmed against OpenMC to −0.5 %; full-void worth at discharge +4.7 $ (DRAGON) / +8.6 $
(OpenMC) — prompt-supercritical at both ends of the bracket)*
