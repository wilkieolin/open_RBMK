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
- Platform dir is `Linux_aarch64`; results land in `5.1/<code>/Linux_aarch64/*.result`.
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
| RBMK lattice cell, `Dragon/data/rbmk_cell_a3.x2m` | **k∞ = 1.310172**, self-shielded, 2 groups | ✅ Correct RBMK geometry, verified in-deck against design volume fractions. Value is post-hydrogen-fix (2026-09-23) and matches what `rbmk_h2otest.x2m` measured independently; the old free-gas value was 1.312816. |
| Void coefficient vs burnup, `Dragon/data/rbmk_a5_void.x2m` | +1957 pcm (~4 β) full-void at 20 MWd/kg, rising with burnup | ⚠️ **Sign and trend confirmed by OpenMC; magnitude is not.** OpenMC gives +4007 pcm (~8 β) at the same burnup and +1030 vs +82 pcm at fresh fuel. Treat the DRAGON value as a lower bound of unknown tightness. |
| CANDU-6 control, `Dragon/data/rbmk_candu.x2m` + `openmc/candu_cell.py` | DRAGON +1624 pcm vs OpenMC +1603 pcm full-void | ✅ Same geometry, library and compositions in both codes; **agree to 22 pcm (1.3 %)**. This is what validates the OpenMC model and localises the RBMK disagreement. |
| Cell volume fractions, analytic vs DRAGON tracking | graphite 89.5938 % vs 89.594 %, coolant 3.7721 % vs 3.772 %, fuel 2.9009 % vs 2.901 % | ✅ Independent of DRAGON entirely (`openmc/volcheck.py`). The geometry is right. |

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
| Cell geometry, analytic vs DRAGON tracking volumes | ✅ match to every printed digit |
| Method validated on a non-RBMK lattice (CANDU-6, both codes) | ✅ agree to 22 pcm on the void coefficient |

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
primary source:

1. **Pressure tube 88 × 4 mm vs 92 × 4 mm.** `rbmk_cell_a3.x2m` uses 88 × 4 (r 4.00/4.40).
   The Wikipedia article states 8.4 cm ID with a 4 mm wall. The choice moves coolant area
   by 10 %, which matters directly for the void coefficient. One constant in the deck.
2. **Fuel rod ring radii 1.60 / 3.10 cm** — inferred from fit constraints, not sourced.
3. **Carrier rod wall** — only the 13 mm OD is sourced.
4. **β_eff** — assumed 0.0048 for the β-equivalent column. The library carries `NDEL 6`
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

Ratios are of **branch** reactivities at the same burnup, never of absolute k — the two codes'
depletion trajectories diverge (+268 pcm at 5 MWd/t, −2084 at 20), so an absolute-k correction
would fold a depletion difference into a void correction.

**What this defers to A7/A8.** Variant A is the COMPO as built. Variant B multiplies the
void-induced reactivity by r. The application point is `MAC: ... ADD` on the void-induced Δ in
the consuming deck — one visible multiplier rather than a second 114 MB binary, and the single
source of truth for the physics stays in `_ACompo`. This preserves the plan's intent (the
variants differ only in how the DCA axis is used) and moves the implementation, not the
science. It is **not yet built or validated** — that is the first item of A7.

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

---

*Last updated: 2026-09-23 (3) (A5b full 630-point COMPO built and verified: round trip
6.4 pcm worst, off-grid interpolation 27 pcm worst, β curve 0.006824 → 0.004680 measured and
confirmed against OpenMC to −0.5 %; full-void worth at discharge +4.7 $ (DRAGON) / +8.6 $
(OpenMC) — prompt-supercritical at both ends of the bracket)*
