# RBMK-1000 Coupled Neutronics/TH Model — Progress Log

> **2026-09-22: this file was rewritten after an audit.** The previous version reported
> Stages 1–3 complete and Stage 4 blocked on SPH. That status did not survive inspection —
> most of the claimed validation traced to fabricated cross sections or misdiagnosed
> failures. See `EVALUATION.md` for the full audit. Actionable work order: `TIER_A_WORKPLAN.md`.

## Objective

3-D spatially-resolved coupled neutronics/TH RBMK-1000 model, driving a historically
accurate **RBMK mnemonic display** (1661 channel outlet temperatures, 211 rod positions,
in-core detector readings). Accident scenario runs to **fuel failure** and stops.

---

## Architecture (three tiers)

| Tier | What | Status |
|---|---|---|
| **A — offline physics** | DRAGON5 lattice → MULTICOMPO → DONJON5 3-D steady + reference AZ-5 transient. Source of truth. | **In progress — see `TIER_A_WORKPLAN.md`** |
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
| IAEA-3D benchmark, `Donjon/data/iaea3d_fuelmap.x2m` | k_eff = 1.028980 (ref 1.029069, **−8.9 pcm**) | ✅ Genuine. Use as the standing regression test and as the structural template for the core workflow. |
| RBMK cell with real nuclear data, `Dragon/data/rbmk_cell_dlib99_v2.x2m` | k∞ = 1.050768, 172 groups, unshielded | ✅ Runs clean `LIB:→NXT:→ASM:→FLU:→EDI:`. The only legitimate RBMK physics result in the repo. Not yet usable downstream (see gaps). |

**Nothing else is validated.** Retracted claims:

- ~~"RBMK cell k∞ = 1.030601 (Δ = 8×10⁻⁷)"~~ — `rbmk_cell_iaea_xs.dra` contains no nuclear
  data. It is a hand-typed `MAC:` block of IAEA PWR constants with νΣf raised 0.135→0.160,
  carrying the comment *"tuned for k_inf ~1.03"*, asserted against 1.0306. Graphite was given
  negative implied absorption to hold k above 1. The agreement is a tautology.
- ~~"LMW 2-D kinetics benchmark passed"~~ — the cited file `Donjon/data/lmw_kinetics.x2m`
  **does not exist anywhere on the filesystem**. The only LMW artifact is the stock TRIVAC
  procedure `Trivac/data/Ktests_proc/lmw2D.c2m`, which was never run as part of this project.
- ~~"3-D core converges, k=0.054, 973 outers"~~ — log says
  `THE MAXIMUM NUMBER OF OUTER ITERATIONS IS REACHED` at 999/1000, then `TEST FAILURE`.
- ~~"Transient framework ready"~~ — all five transient decks abort. `KINSOL:` has never run.

---

## Current state of the RBMK decks

| Area | State |
|---|---|
| Lattice cell, real data | One working deck (unshielded, wrong condensation, no export) |
| Self-shielding on the cluster | Absent |
| SPH homogenization | Never succeeded |
| 2-group export to DONJON | Nothing ever written to disk |
| MULTICOMPO / SAPHYB / CPO | **None exists** |
| β_eff, λ from library | Never extracted (transient decks hardcode 700 pcm) |
| Burnup (`EVO:`) | Never run |
| Void / Doppler / graphite-temp branches | **None** |
| CPS channel cells (B₄C, displacer, water) | **None** |
| 3-D core | Geometry generator sound, but writes a **12.25 cm** core (units bug) |
| Transient | No time loop in any deck; `KINSOL:` never executed |
| TH coupling | `THM:` never called from any RBMK deck |
| Detectors | `DETINI:`/`DETECT:` never used |

2 of 19 DONJON RBMK decks ever produced a k_eff; both ≈ 0.05.
~86 `rbmk_cell_*` variants exist in `Dragon/data/`; ~10 ever ran.

---

## Root causes (all fixable, none are capability limits)

1. **Units bug.** `gen_rbmk_realistic.py` has `PITCH = 0.25  # meters`; DONJON `GEO:` mesh
   coordinates are **centimetres**. The modelled core is 12.25 cm × 12.25 cm × 7 cm with VOID
   on all six faces. The XS used give k∞ = 1.12 — everything down to 0.054 is leakage.
   Cross-check: `rbmk_core_3d_simple.don` has a different mesh but the same physical size and
   identical XS → k_eff = 0.060. **SPH cannot fix this; it is an O(1) correction.**
2. **Missing `SEQ_BINARY` declaration.** `Dragon/src/SPH.F:239` explicitly supports NXT
   tracking; the abort fires only when no sequential-binary tracking file is passed
   (`IFTRK==0`, set at `SPH.F:140`). `NXT.f:42` documents
   `[ TRKFIL ] VOLTRK := NXT: GEOMETRY ::`. Across ~40 cell decks **none** declares a
   `SEQ_BINARY` file; the two that name a `TRKFILE` declare it in `LINKED_LIST`.
3. **Wrong reference template.** A CANDU channel is topologically the same problem. The tree
   ships ~24 validated CANDU cluster decks in `Dragon/data/twlup_proc/`, including
   coolant-void branches (`TCWU07.c2m`). They were never used.

---

## Toolchain capability (confirmed present, none of it used yet)

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

**Reference decks to copy from:** `Dragon/data/rep900_mco.x2m` (multi-parameter COMPO),
`Dragon/data/twimsE_proc/TCWE13.c2m` (NXT + `SEQ_BINARY` + SPH),
`Dragon/data/twlup_proc/TCWU07.c2m` (CANDU cluster + void branch + self-shielding),
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

There is no open RBMK benchmark of IAEA-3D quality. The previously cited "Kozlowski RBMK
benchmarks" appears to be a misattribution — Kozlowski & Downar authored the OECD/NEA **PWR
MOX/UO₂** transient benchmark. **Verify before relying on it.**

Mitigation: build the same RBMK cell in **OpenMC** as an independent Monte Carlo reference
for k∞, the void coefficient, and the 2-group constants. Neither OpenMC nor numpy is
currently installed. Without such a cross-check a hand-built RBMK lattice has nothing to be
validated against — which is how this project arrived at a tuned `MAC:` block.

---

## Standing rule

**Every asserted value must come from a calculation, never from a constant chosen to make
the assert pass.** That single practice is what produced the state this file documents.

---

*Last updated: 2026-09-22 (post-audit rewrite)*
