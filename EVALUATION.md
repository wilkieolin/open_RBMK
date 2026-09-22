# RBMK-1000 / AZ-5 Simulation — Feasibility Evaluation

*Audit date: 2026-09-22. Supersedes the status claims previously in PROGRESS.md and PROJECT_PLAN.md.*

## Context

`PROJECT_PLAN.md` and `PROGRESS.md` state the goal as a 3-D spatially-resolved coupled
neutronics/TH RBMK-1000 model in DRAGON5/DONJON5 for **real-time** transient simulation,
capable of reproducing Chernobyl conditions including the AZ-5 positive-scram transient.
The docs report Stages 0–3 complete and Stage 4 blocked on SPH homogenization.

Clarified during this review: the end product is a **historically accurate RBMK mnemonic
display** — 1661 channel outlet temperatures, 211 rod positions, in-core detector readings —
driven live by the simulation, with the accident scenario **stopping at fuel failure**.

I audited the decks, the run logs in `5.1/*/Linux_aarch64/*.result`, and the
DRAGON/DONJON/TRIVAC sources.

**Two findings drive everything below.** First, the reported status does not match the
disk: none of the three reported blockers is a real capability limit, and most of the
claimed validation does not survive inspection. Second, the toolchain is considerably more
capable than the project has assumed, but it cannot itself be the live engine behind the
panel — that needs a separate online solver, with DONJON as its source of truth.

---

## Verdict

| Goal | Verdict |
|---|---|
| 3-D coupled neutronics/TH RBMK model | **Achievable.** Every required module exists, is compiled, and has a working bundled example. |
| Void-driven excursion, Doppler feedback | **Achievable**, with one caveat: transient TH is homogeneous-equilibrium only (see below). |
| AZ-5 with graphite-displacer positive scram | **Achievable.** `DEVINI:` supports multi-part rods with per-part mixtures — displacer + absorber is the designed use case. One code bug to route around. |
| **Real-time, spatially resolved** (for the mnemonic panel) | **Achievable, but not inside DONJON.** Requires a purpose-built online solver; DONJON is the offline source of truth. See "Driving the mnemonic panel" below. |
| Full 3-D coupled transient in real time *in DONJON* | **No.** ~30–100× slower than real time at best. Fine offline; not interactive. |
| Scope: stop at fuel failure (confirmed) | **Achievable.** Power excursion, feedbacks, energy deposition and timing up to loss of fuel integrity are all within DRAGON/DONJON. |
| Progress so far | **Near zero validated RBMK physics**, though the toolchain and benchmark work are real. |

**Bottom line: the project goals are reachable, the toolchain is not the obstacle, and the
current roadmap is pointed at the wrong problems.** The main cost is that most of the
RBMK-specific work to date needs to be redone rather than repaired.

---

## What genuinely works

- **Toolchain build.** ganlib/trivac/dragon/donjon built and linked on aarch64. Non-trivial.
- **IAEA-3D benchmark.** `Donjon/data/iaea3d_fuelmap.x2m` → k_eff = 1.028980, **−8.9 pcm**. Genuine and reproducible; it is also the correct structural template for the core workflow.
- **APOLIB99 isotope naming resolved** (`Zr90`, `C12_GR`, `Nb93`, `He4`). Real finding.
- **One working real-nuclear-data cell solve.** `Dragon/data/rbmk_cell_dlib99_v2.x2m` runs `LIB: → NXT: → ASM: → FLU: → EDI:` clean, giving **k∞ = 1.050768** for the 18-rod cluster. This is the only legitimate RBMK physics result in the repo and the right foundation.
- **Geometry generator concept** — `gen_rbmk_realistic.py` builds the 1661-channel cylindrical map correctly.

---

## Record vs. disk

| Claim | Reality |
|---|---|
| "Stage 3 ✅ k∞ = 1.030601 (target 1.0306, Δ = 8×10⁻⁷)" | `rbmk_cell_iaea_xs.dra` contains **no nuclear data**. It is a hand-typed `MAC:` block of IAEA PWR constants with νΣf bumped 0.135→0.160, carrying the deck comment *"tuned for k_inf ~1.03"*. The assert is the target, so the agreement is a tautology. Graphite is given negative implied absorption to hold k above 1. |
| "Stage 2 ✅ LMW kinetics, `Donjon/data/lmw_kinetics.x2m`" | **That file does not exist anywhere on the filesystem.** The only LMW artifact is the stock TRIVAC procedure `Trivac/data/Ktests_proc/lmw2D.c2m`. |
| "✅ Converges (k=0.054), 973 outer iterations" | Log reads `THE MAXIMUM NUMBER OF OUTER ITERATIONS IS REACHED` at 999/1000, then `TEST FAILURE`. |
| "k_eff = 0.054 due to XS mismatch; FLUD requires SPH for large cores" | **Misdiagnosis** — units bug, see below. |
| "SPH blocked: NXT creates text tracking, SPH needs binary" | **Misdiagnosis** — SPH explicitly supports NXT, see below. |
| "Transient framework ready" | All 5 transient decks abort. `rbmk_transient.don` is written in **invented syntax** (`REACTIVITY ::`, `XENON_FEEDBACK ON`, `BETA`, `DOPPLER`, `VOID_FRACTION` — none exist in DONJON). No time loop exists anywhere. `KINSOL:` has never executed once. |
| "Corrected diffusion coefficients from DRAGON5 homogenization" | Graphite D₁ = 0.022 cm where ≈ 8 cm is right, and the graphite `SCAT` line has σ(1→2) = 0 — **the moderator does not moderate.** |

Only 2 of 19 DONJON RBMK decks ever produced a k_eff. Both ≈ 0.05.

---

## The three "blockers" are input-syntax errors

### 1. The core is 12.25 cm across, not 12.25 m — this is all of k_eff = 0.054

`gen_rbmk_realistic.py` sets `PITCH = 0.25  # meters` and writes mesh coordinates directly.
DONJON `GEO:` coordinates are **centimetres**:

```
rbmk_core_3d_realistic.don:1417   MESHX 0.00 0.25 0.50 ... 12.25
iaea3d_fuelmap.x2m:99             MESHX 0.0 20.0 40.0 ... 340.0     <- correct, cm
```

The modelled object is a 12.25 cm × 12.25 cm × 7 cm block with VOID on all six faces; cell
size 2.5 mm. The XS that ran give k∞ = 1.12 — everything down to 0.054 is leakage out of a
12-centimetre reactor.

Decisive cross-check: `rbmk_core_3d_simple.don` uses a *different* mesh (25×25×14) but the
*same* physical size and identical XS, and returns k_eff = 0.0600. Same size → same answer.

**SPH factors are O(1) corrections; they cannot move k_eff from 0.054 to 1.0.** The whole
Stage 4 blocker and the priority list in `PROJECT_PLAN.md` are chasing the wrong problem.
`rbmk_medium_test.don` is the only core deck with a correct cm-scale mesh, and it has never
been run.

### 2. SPH is not incompatible with NXT — the tracking file was never declared

`Dragon/src/SPH.F:239-242` explicitly supports NXT:

```fortran
ELSE IF(CNDOOR.EQ.'NXT') THEN
*   NXT TRANSPORT-TRANSPORT EQUIVALENCE
    NSPH=3
    IF(IFTRK.EQ.0) CALL XABORT('SPH: MISSING TRACKING FILE')
```

`IFTRK` is set at `SPH.F:140` only when an entry of type 3 (**sequential binary file**) is
passed, and `NXT.f:42` documents `[ TRKFIL ] VOLTRK := NXT: GEOMETRY ::` — the binary file
is an optional first LHS output.

Across ~40 RBMK cell decks, **not one declares a tracking file as `SEQ_BINARY`.** The two
that name a `TRKFILE` declare it in `LINKED_LIST`, which is the bug. Every SPH failure is
this same error in a different costume. The bundled `Dragon/data/twimsE_proc/TCWE13.c2m`
shows the fix in three lines:

```
SEQ_BINARY FILTRK ;
DISCR2 FILTRK := NXT: ASSMB :: ALLG BATCH 100 TISO 10 20.0 ;
CP     := ASM: LIBRARY DISCR2 FILTRK ;
```

The sub-blockers are likewise syntax: `rbmk_cell_sph_excelt.x2m` fails with `EXCELT: TISO IS
AN INVALID KEY WORD` because `TISO` must follow `TRAK`; the "fixed" version then sets
`ANIS 15` and crashes. `EXCELT:` handles `CARCEL`+`CLUSTER` fine.

### 3. The closest analogue reactor ships with the distribution and was never used

A CANDU channel — pressure tube, calandria tube, gas gap, cluster fuel, non-light-water
moderator — is topologically the same problem as an RBMK channel. The tree ships ~24
validated CANDU decks under `Dragon/data/twlup_proc/`, **including coolant-void branches**
(`TCWU07.c2m` runs voided and unvoided cases side by side with `SHI:` self-shielding and
asserted k∞ values).

Instead, ~86 RBMK deck variants were generated by permuting tracking modules against a
template carrying one unfixed declaration error. That methodology is the real roadblock and
the first thing worth changing.

---

## Capability assessment: the toolchain is not the limitation

Everything required exists, is compiled into `install/bin/donjon`, and has a bundled working
example. None of it is used by any RBMK deck.

| Requirement | Module | Notes |
|---|---|---|
| Space-time kinetics | `INIKIN:` / `KINSOL:` (in **Trivac**, callable from DONJON) | θ-method: implicit / Crank-Nicolson / general θ, plus exponential transform and analytic precursor integration. **No improved-quasi-static** — every step is a full fixed-source flux solve. `TRIVAA:` needs `UNIT`. |
| Transient TH | `THM:` → `THMTRS.f` | 1-D per-channel — which is the physically correct topology for RBMK pressure tubes. |
| Void fraction / boiling | `THMDFM.f90`, subcooled models `BOWR`/`SAHA` | See caveat below. |
| XS feedback on state | `NCR:` + `COMPO:` | Up to 10 interpolation dimensions, linear or cubic Ceschino, plus superposed `ADD` delta-sigma branches. Carries `LAMBDA-D` through to the macrolib. |
| **Graphite displacer + absorber** | `DEVINI:` / `DEVGET.f` | Up to 10 contiguous rod **parts**, each with its own `DMIX` (inserted/extracted mixture pair); volume-fraction-weighted partial insertion. |
| Rod motion | `DSET:` (level) or `MOVDEV:` (speed) | See bug below. |
| Xenon | `XENON:` / `XENCAL.f` | **Equilibrium Xe only** — no iodine inventory, no time derivative, no post-shutdown build-up. |
| **Point kinetics (real-time)** | `PKINI:` / `PKINS:` / `PKIRHO.f` | Runge-Kutta, feedback `ALPHA` tables on `T-FUEL`/`T-COOL`/`D-COOL`, and a `PTIME` reactivity-vs-time law. Milliseconds per step. |

**Reference decks to build from (all bundled):**

- `Dragon/data/rep900_mco.x2m` — builds a multi-parameter MULTICOMPO (`PARA 'burnup' IRRA`, `'TF' TEMP`, `'TCA' TEMP`, `'DCA' VALU REAL`).
- `Donjon/data/channel_mphy.x2m` — the full coupled transient loop: `THM: TIME` → `NCR:` → `MACINI:` → `TRIVAA: UNIT` → `KINSOL: SCHEME FLUX CRANK PREC EXPON` → `FLPOW:`.
- `Donjon/data/AFMtest.x2m` — 3-D core (`CAR3D 26 26 12`, `MCFD 1`) with `DEVINI:` rods moving under kinetics. **This is the AZ-5 skeleton.**
- `Donjon/data/pulseTHM_0d.x2m` — `PKINI:`/`PKINS:` + `THM:` with adaptive Δt. **This is the real-time skeleton.**

The RBMK work never produced the artifact that connects these: **no COMPO, SAPHYB, or CPO
exists in any RBMK deck, and nothing is ever written to disk.** The one good cell
calculation leaves its result in an in-memory LCM directory discarded at `END:`.

### Three real limitations to design around

1. **Transient TH is HEM-only.** `THMTRS.f:157` hardcodes `IDFM = 0` and `THM.f:1102` passes neither `IPRES` nor `IDFM`. Drift-flux and pressure-drop are steady-state-only. Transient void is still computed, but without drift velocity. For a positive-void-coefficient reactor this is a genuine accuracy caveat — workable as a first pass, worth quantifying against the steady drift-flux solution.
2. **`MOVDEV:` truncates multi-part rods.** `DEVGET.f:246` stores `6*NPART` positions; `MOVPOS.f:159` and `MOVGRP.f:175` store only `6`, while `NEWMDV.f:97` reads and loops over all `NPART`. No bundled deck calls `MOVDEV:` at all, so this path is untested. **Route around it**: drive the rod with `DSET: ... ROD n LEVEL <lvl>` and compute `lvl = v·t/H` in CLE-2000, as `AFMtest.x2m` does.
3. **`NEWMDV.f:92` skips any rod with `LEVEL < 1e-4`.** A fully withdrawn multi-part rod contributes nothing — so you cannot represent "displacer parked in the lower core, absorber out," which is exactly the pre-scram Chernobyl configuration. Model the parked displacer as a distinct mixture in the base fuel map and let the device carry only the difference.

---

## Performance: real-time is reachable, but not from the 3-D solver

**No parallelism where it matters.** Zero OpenMP directives in `Trivac/src` and
`Donjon/src`; the `-fopenmp` flag only activates Dragon's MOC/S_N lattice solvers. The core
flux solve, the THM channel loop, and XS interpolation are all single-threaded. The 20 CPU
cores do not help, and the GB10 GPU is unreachable — there is no offload path, and adding
one is a rewrite. (Memory is a non-issue: the largest solve used ~1.4 GB.)

**But the 738 s figure is a discretization choice, not a mesh limit.** That run used
`DUAL 3 3` — Raviart-Thomas mixed-dual, ~40 unknowns per node, **2,683,917 unknowns/group**
on 67,228 nodes. `MCFD 1` (mesh-centred finite difference, the documented default, and what
`AFMtest_proc/Pcalflu.c2m:45` uses for a real 3-D core) gives ~1 unknown per node — a ~40× smaller problem.

Revised estimates for 49×49×28, 2 groups, `MCFD 1`:

- Steady eigenvalue solve: **order 5–30 s**
- One `KINSOL:` step: **order 0.2–3 s** (fixed-source, warm-started, not an eigenvalue problem)
- A 20 s AZ-5 transient at Δt = 10 ms with 2–3 Picard iterations: **roughly tens of minutes to a few hours**

So the full 3-D coupled transient is ~30–100× slower than real time — comfortably usable
offline, not interactive. Free levers before optimizing anything else: drop `DUAL 3 3` →
`MCFD 1`; loosen `EPSOUT` from 1e-7 to 1e-5 (1e-7 is absurd for a transient step); rebuild
with `-O3 -march=native` (the Makefiles currently use `-O`, i.e. `-O1`).

DONJON's built-in point-kinetics engine (`PKINI:`/`PKINS:`, Runge-Kutta with `ALPHA` feedback
tables and a `PTIME` rod law, demonstrated in `pulseTHM_0d.x2m`) runs at milliseconds per
step — but it produces a single amplitude, which is not enough for the panel. See below.

---

## Driving the mnemonic panel — assessment

**You are right that this needs 3-D spatial detail. I agree, and for a stronger reason than
display fidelity.**

Each of the three instruments is a spatial measurement:

- **Channel outlet temperatures** — 1661 thermocouples. THM is already 1-D per channel, but it needs a per-channel power distribution to integrate. That is a radial spatial field.
- **In-core detector counts** — local flux at fixed probe points. Historically these were self-powered neutron detectors (~130 radial positions plus axial strings), with lateral ionization chambers outside the core; "scintillator" isn't quite the RBMK instrument, and worth confirming against your source if historical accuracy is the goal. SPNDs also have a *delayed activation response*, which is itself historically significant — indicated power lagged actual power. DONJON's `DETINI:`/`DETECT:` gives probe positions and PARAB/SPLINE flux interpolation but no response model; the lag is a first-order filter you add downstream.
- **Rod positions** — 211 values, state rather than physics output, but they only mean anything against a spatially resolved flux.

The deeper reason is physics, not display. The RBMK's neutron migration length (~1 m) is
small against its 12 m diameter, so the core is weakly coupled and behaves as semi-autonomous
regions — that is the origin of its first-azimuthal-mode xenon instability and of the local
criticality excursion that actually initiated the accident. **A point-kinetics model would
not merely miss panel detail; it would miss the phenomenon that made the accident possible.**
The mnemonic panel exists precisely because the reactor was spatially unstable. So spatial
resolution is a correctness requirement here, not a fidelity upgrade.

**However, full-fidelity 3-D at display rate is not required.** Panel instruments are slow:
channel-outlet thermocouples have multi-second thermal time constants, and SPND response is
delayed by design. A flux *shape* update at ~1–10 Hz with the *amplitude* integrated at
higher rate is physically adequate and is the standard quasi-static factorization.

### Recommended architecture — three tiers

- **Tier A — offline (DRAGON/DONJON).** MULTICOMPO cross sections, validated 3-D steady states, and a reference AZ-5 `KINSOL:` transient. This is ground truth and the validation target. Roadmap steps 1–6 below.
- **Tier B — online engine (GB10 GPU).** A standalone 2-group nodal/finite-difference diffusion solver with 6 delayed-precursor groups and 1-D per-channel TH, reading the *same* XS tables Tier A produced, validated against the Tier A transient. This is what runs live.
- **Tier C — the mnemonic panel**, driven entirely by Tier B: per-channel power → per-channel TH → outlet temps; local flux at detector coordinates → detector signal + response lag; rod positions as state.

**Why a custom online solver rather than DONJON in the loop:** DONJON is single-threaded
with no GPU path, and one shape solve is 0.2–3 s. That supports maybe 0.3–1 Hz — adequate
for channel temperatures, but it would step straight over the ~4-second excursion that is
the entire point of the scenario. The problem itself, though, is small: 49×49×28 ≈ 67 k
nodes × 2 groups is a sparse linear solve that a GB10 handles at kHz rates.

**Memory is a non-issue.** Flux, sources, and XS at 67 k nodes × 2 groups run to a few MB;
6 precursor groups add ~1.6 MB; per-channel TH state is smaller still. Total well under
100 MB — nowhere near the ~110 GB ceiling, so no paging risk.

This is the one place the GB10 genuinely earns its keep, and it does not waste any of the
DONJON work — Tier A is what makes Tier B trustworthy.

**Lower-risk Phase 1, if Tier B is too much scope up front:** quasi-static factorization
using DONJON directly — amplitude from `PKINS:` at ms resolution, shape refreshed by a
DONJON solve every ~1 s. That gets a working panel at low update rate for steady operation,
rod maneuvering, and xenon transients. It will not resolve the AZ-5 excursion itself, so
treat it as a staging step rather than the destination.

---

## Scope (confirmed: stop at fuel failure)

DONJON is a neutronics/TH code. It will model the AZ-5 power excursion, feedbacks, energy
deposition and timing up to loss of fuel integrity, and report where and when that threshold
is crossed. Fuel disassembly, the steam explosion, and core destruction are out of scope and
would need MELCOR or RELAP-SCDAP.

---

## Validation risk

There is no open RBMK benchmark of IAEA-3D quality. `PROGRESS.md` cites "Kozlowski RBMK
benchmarks" — Kozlowski & Downar authored the OECD/NEA **PWR MOX/UO₂** transient benchmark;
verify this reference exists before relying on it.

Practical mitigation: build the same RBMK cell in **OpenMC** (free, Python, runs here) as an
independent Monte Carlo reference for k∞, the void coefficient, and the 2-group constants.
Neither OpenMC nor numpy is currently installed. Without a cross-check of this kind a
hand-built RBMK lattice has nothing to validate against — which is how the project arrived
at a tuned `MAC:` block in the first place.

---

## Corrected roadmap

Steps 1–2 are cheap and should precede any new modelling.

### 1. Fix the units bug and re-baseline the core — hours
- `gen_rbmk_realistic.py`: `PITCH = 25.0  # cm`; add radial and axial graphite reflector regions (the current map has an 88-cell ring and nothing axially).
- Switch `TRIVAT:` from `DUAL 3 3` to `MCFD 1`; loosen `EPSOUT` to 1e-5.
- Replace six-sided `VOID` with a real reflector plus `ALBE`/`VOID` outside it.
- Re-run with IAEA XS purely as a **geometry/solver sanity check**. Do not read physics into the result.

### 2. Delete the fabricated artifacts and correct the docs — hours
Quarantine `rbmk_cell_iaea_xs.dra`, `rbmk_transient*.don`, and the ~80 dead cell variants;
keep `rbmk_cell_dlib99_v2.x2m`. Rewrite the status sections of `PROGRESS.md` and
`PROJECT_PLAN.md` — as written they will mislead every future session.

### 3. Build a real RBMK lattice cell — critical path
From `rbmk_cell_dlib99_v2.x2m` plus the CANDU pattern in `twlup_proc/TCWU07.c2m`:
- `SEQ_BINARY FILTRK ;` and `TRK FILTRK := NXT: GEOMF :: ALLG BATCH 100 TISO 15 30.0 ;`
- Add self-shielding (`USS:` or `SHI:`) — currently absent, so k∞ = 1.0507 is unshielded.
- Fix condensation: `COND 24` cuts at **550 keV**, not thermal. The library is **172 groups, not 99** (`NGRO 172` in the log) despite every comment. Use an energy-valued cut (`COND 0.625`).
- Fix the 26-group boundary list — it runs to group 354 on a 172-group library (pasted SHEM-361 structure).
- `MERG COMP`, not `MERG MIX`, to homogenize to one channel material.
- Then `SPH:` works, given the binary tracking file.

### 4. Build the MULTICOMPO — the missing artifact
Follow `rep900_mco.x2m`. Loop the cell over:
- coolant density `DCA`, 0.72 → ~0.02 g/cm³ — **this is the void coefficient; nothing in the repo computes one today**
- fuel temperature `TF` (Doppler) and graphite temperature (its own `VALU REAL` axis — it matters a lot for RBMK)
- burnup via `EVO:` — no deck has ever run a burnup step, and the RBMK's dangerous void coefficient is a high-burnup, low-ORM condition. Fresh fuel will not reproduce Chernobyl.
- xenon as an explicit `PARA 'Xe' VALU REAL` axis, since `XENON:` gives equilibrium only

Export with `COMPO:` to disk. Take β/λ from the library (`NDEL 6` is present) instead of hardcoding 700 pcm.

### 5. CPS channel cell calculations
Absent and required for AZ-5: B₄C absorber, **graphite displacer**, and the water column
below it. The core mix map currently has no rod sites — every live cell is fuel or graphite,
so there is nowhere for a rod to go.

### 6. Couple and run the transient
Fuse `channel_mphy.x2m` (THM + NCR loop) with `AFMtest.x2m` (devices + kinetics):
`THM: TIME` → `NCR:` → `MACINI:` → `NEWMAC:` → `TRIVAA: UNIT` → `KINSOL: DELTA dt` →
`FLPOW:`, inside a `REPEAT`/`UNTIL` time loop. Drive AZ-5 via `DSET:` with a level computed
from the real 0.4 m/s insertion — the ~18–20 s full-insertion time is the mechanism.

### 7. Detectors and per-channel instrumentation (still in DONJON)
Place the in-core detector positions with `DETINI:` and read them with `DETECT:` (PARAB or
SPLINE interpolation) against the Tier A transient. Add the SPND response lag as a
first-order filter downstream — DONJON does not model it. Confirm the historical detector
type and layout (SPNDs + lateral ionization chambers, not scintillators) before fixing
positions. This gives the reference traces the online engine must reproduce.

### 8. Tier B online engine (GB10 GPU)
Standalone 2-group nodal/FD diffusion + 6 precursor groups + 1-D per-channel TH, reading the
step-4 MULTICOMPO tables. Validate against the step-6 `KINSOL:` transient and the step-7
detector traces before it drives anything. Few-MB working set; no memory risk.

### 9. Tier C mnemonic panel
Driven by Tier B: 1661 channel outlet temps, 211 rod positions, detector signals with
response lag.

Steps 1–6 are the critical path and must land before 8–9 are worth starting; 7 is what makes
8 verifiable.

---

## Verification

| Step | Check |
|---|---|
| 1 | k_eff physically plausible; `GREP:` reports convergence, not `MAXIMUM NUMBER OF OUTER ITERATIONS REACHED` |
| 3 | `SPH:` completes without `MISSING TRACKING FILE`; k∞ within a few hundred pcm of an OpenMC reference for the same cell |
| 4 | **Void coefficient positive**, order +2 to +5 pcm/%void at representative burnup — the single strongest signal the model is really an RBMK and not a PWR in RBMK clothing |
| 4 | β_eff ≈ 0.0065–0.0075 taken from the library, not hardcoded |
| 5 | Inserting the displacer-only part from the bottom gives **positive** reactivity |
| 6 | AZ-5 from a low-ORM, high-burnup, high-void state produces a prompt power rise before the absorber takes over |
| 6 | Quantify the HEM-only transient-TH error by comparing a steady drift-flux (`DFM 1`) solution against HEM at the same conditions |
| 7 | `DETECT:` traces respond to a local rod insertion, not just to global power |
| 8 | Tier B reproduces the Tier A `KINSOL:` power trace, per-channel power distribution, and detector traces to a stated tolerance — including through the excursion, not just at steady state |
| 9 | Panel updates at ≥10 Hz with the online engine in the loop |
| all | Regression: `iaea3d_fuelmap.x2m` still returns 1.028980 |

**Non-negotiable:** every asserted value must come from a calculation, never from a constant
chosen to make the assert pass. That single practice is what produced the current state.
