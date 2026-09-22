# Tier A Work Order — Offline RBMK Physics (DRAGON5 / DONJON5)

**Audience: an implementing agent.** Follow tasks in order. Each task has a hard
**GATE** — do not start the next task until the gate passes. If a gate fails twice, **stop
and report**; do not improvise a workaround and do not move on.

Background and rationale: `EVALUATION.md`. Status: `PROGRESS.md`. Roadmap: `PROJECT_PLAN.md`.

---

## Rules that override everything else

1. **Never tune a cross section to make an assertion pass.** If a computed value disagrees
   with an expectation, report the disagreement. Do not adjust inputs until it matches. This
   rule exists because violating it is what invalidated the previous six days of work.
2. **Never write an `assertS` whose target you chose from the answer you got.** Targets come
   from a reference calculation, a benchmark, or published data — cite the source in a comment.
3. **Never invent CLE-2000 keywords.** If you need a keyword, find it in the module's Fortran
   source under `5.1/<code>/src/` or in an existing bundled deck that runs. A previous session
   wrote `REACTIVITY ::`, `XENON_FEEDBACK ON`, `DOPPLER`, `VOID_FRACTION` — none exist.
4. **Copy from a deck that demonstrably runs**, not from another RBMK deck. Named reference
   decks are given per task.
5. **Mesh coordinates in `GEO:` are centimetres.** This is not negotiable and it is the single
   most expensive mistake made so far.
6. One change at a time. Re-run. Read the `.result`. Then make the next change.

## Environment

```bash
export PATH="/home/wilkie/code/RBMK/install/bin:$PATH"
export LD_LIBRARY_PATH="/home/wilkie/code/RBMK/install/lib:$LD_LIBRARY_PATH"
```

Running a deck (input must live in `data/`; output lands in `Linux_aarch64/<name>.result`):

```bash
cd /home/wilkie/code/RBMK/5.1/Dragon  && ./rdragon -c custom -p 1 -w data/<name>.x2m
cd /home/wilkie/code/RBMK/5.1/Donjon  && ./rdonjon -c custom -p 1 -w data/<name>.don
```

A deck that needs the nuclear-data library must have a sibling `data/<name>.access` script
that symlinks `DLIB_99`. Copy `data/rbmk_cell_dlib99_v2.access` and rename it; the script is
generic apart from its usage message.

Reading results — always check the tail, not just the exit code:

```bash
tail -30 /home/wilkie/code/RBMK/5.1/Dragon/Linux_aarch64/<name>.result
grep -n -i "XABORT\|kernel error\|FAILURE\|K-INFINITY\|K-EFFECTIVE" <result>
```

---

## A0 — Baseline and regression guard

**Goal:** prove the toolchain still works before changing anything.

1. Run `iaea3d_fuelmap.x2m` in Donjon.
2. Run `rbmk_cell_dlib99_v2.x2m` in Dragon.
3. Record both results in a new file `BASELINE.md` with date, command, and value.

**GATE A0:**
- `iaea3d_fuelmap` → `Keff = 1.028980` (±1e-5)
- `rbmk_cell_dlib99_v2` → `FINAL KINF= 1.050768E+00` (±1e-5)

Re-run the IAEA case after every subsequent task as a regression check.

---

## A1 — Quarantine fabricated artifacts

**Goal:** remove decks that encode false results, so nobody builds on them again.

```bash
mkdir -p /home/wilkie/code/RBMK/quarantine
```

Move into `quarantine/` (do **not** delete — they are evidence):

- `5.1/Dragon/data/rbmk_cell_iaea_xs.dra` — hand-tuned `MAC:` block, no nuclear data
- `5.1/Dragon/data/rbmk_cell.x2m`, `rbmk_cell_iaea_sph*.x2m`, `rbmk_cell_sph.x2m`,
  `rbmk_cell_sph2.x2m`, `rbmk_cell_sph_save.x2m`, `rbmk_cell_realistic.dra`
- `/home/wilkie/code/RBMK/rbmk_cell_simple.dra` and `/home/wilkie/code/RBMK/rbmk_cell.dra`
- `5.1/Donjon/data/rbmk_transient*.don` (all five — invented syntax)
- `5.1/Donjon/data/rbmk_core_3d_iaea_xs.don`, `rbmk_core_3d_dlib99_xs*.don`

**Keep:** `rbmk_cell_dlib99_v2.x2m`, `check_lib.x2m`, `iaea3d_fuelmap.x2m`,
`gen_rbmk_realistic.py`, `rbmk_core_3d_realistic.don`, `rbmk_medium_test.don`.

Then sweep the remaining `5.1/Dragon/data/rbmk_cell_sph_*.x2m` variants (~30 files) into
`quarantine/` as well — they are permutations around one unfixed declaration error and none
succeeded. A3 replaces them with a single correct deck.

**GATE A1:** `grep -rl "tuned for k_inf\|REACTIVITY ::\|XENON_FEEDBACK\|VOID_FEEDBACK" 5.1/` returns nothing.

---

## A2 — Fix the units bug and re-baseline the 3-D core

**Goal:** a core that is actually 12.25 **metres** across and whose solver converges.

Reference deck: `5.1/Donjon/data/iaea3d_fuelmap.x2m` (correct cm-scale mesh at line 99).

### A2.1 Fix the generator

Edit `5.1/Donjon/data/gen_rbmk_realistic.py`:

- `PITCH = 0.25  # meters` → `PITCH = 25.0  # cm`
- `radius_m = 5.9` → express in cm consistently (`RADIUS_CM = 590.0`), and derive
  `radius_cells = RADIUS_CM / PITCH` so the 1661-channel selection is unchanged.
- Verify the emitted `MESHX`/`MESHY` run `0.00 25.00 50.00 ... 1225.00` and `MESHZ`
  `0.00 25.00 ... 700.00`.

### A2.2 Add a real reflector

The current map has an 88-cell one-cell ring and **nothing axially**. Add:

- radial graphite reflector: extend the mix-2 annulus to at least 2 cells (50 cm) thick
- axial graphite reflector: **2 extra planes at each end** (mix 2), so `NZ` goes 28 → 32
- outer boundary stays `VOID`, but now outside a real reflector

### A2.3 Fix the discretization

In the generated `.don`:

- `TRIVAT: ... DUAL 3 3` → `TRIVAT: ... MCFD 1`  (≈40× fewer unknowns; precedent `AFMtest_proc/Pcalflu.c2m:45`)
- `FLUD:` / solver block: `EPSOUT 1.0E-7` → `1.0E-5`

### A2.4 Fix the macrolib sanity

The hand-pasted `MACRO := MAC:` block currently in `rbmk_core_3d_realistic.don` is wrong in
two ways and must **not** be carried forward:
- graphite `SCAT` has σ(1→2) = 0 — the moderator does not moderate
- diffusion coefficients are ~50–400× too small

For A2 only, revert to the IAEA 2-group set used by `iaea3d_fuelmap.x2m` and treat this task
purely as a geometry/solver check. Real cross sections arrive in A5.

**GATE A2:** the run completes with a converged eigenvalue — the `.result` must **not**
contain `THE MAXIMUM NUMBER OF OUTER ITERATIONS IS REACHED`. Report the k_eff you get.

> Do **not** expect or engineer k_eff ≈ 1.0 here. You are running IAEA PWR constants in an
> RBMK-shaped box; any value is acceptable as long as the solver converges and the geometry
> echoes at the right physical size. Report the number; do not tune toward 1.

Also record the wall-clock time of the `FLUD:` module (compare against the 729 s `DUAL 3 3`
baseline) — this figure feeds the Tier B design.

---

## A3 — A correct RBMK lattice cell

**Goal:** a self-shielded, correctly condensed, homogenized 2-group cell from real nuclear data.

Start from a copy: `cp 5.1/Dragon/data/rbmk_cell_dlib99_v2.x2m 5.1/Dragon/data/rbmk_cell_v3.x2m`
and its `.access` script. Reference decks:
- `5.1/Dragon/data/twimsE_proc/TCWE13.c2m` — NXT + `SEQ_BINARY` + SPH
- `5.1/Dragon/data/twlup_proc/TCWU07.c2m` — CANDU cluster, self-shielding, void branch

Four defects to fix. Apply them one at a time, re-running after each.

### A3.1 Declare the binary tracking file (this is the SPH blocker)

`SPH.F:239` supports NXT tracking; it aborts only when no sequential-binary tracking file was
passed (`IFTRK==0`, set at `SPH.F:140`). No RBMK deck has ever declared one.

```
SEQ_BINARY FILTRK FILSS ;              * add near the LINKED_LIST line
...
TRK FILTRK := NXT: GEOMF ::
  EDIT 0 TITLE 'RBMK-CELL' ALLG BATCH 100 TISO 15 30.0 ;
SYS := ASM: LIBRARY TRK FILTRK :: EDIT 1 ;
```

Note the LHS order `TRK FILTRK` (tracking object first, binary file second) — this is the
convention in `TCWE13.c2m:130` and `TCWU07.c2m:62`, both of which run. (The header comment
in `NXT.f:42` shows the reverse order; the module dispatches on data-structure *type*, not
position, so follow the working decks.)

### A3.2 Add self-shielding

k∞ = 1.050768 is currently **unshielded**, so it is not a physical number. Add a
self-shielding tracking pass and a `USS:` call before the flux solve:

```
TRKSS FILSS := NXT: GEOMSS :: EDIT 0 ALLG BATCH 100 TISO 8 15.0 ;
LIBRARY := USS: LIBRARY TRKSS FILSS :: EDIT 1 PASS 2 GRMIN 18 ;
```

`GEOMSS` is a coarser copy of the cell geometry (fewer radial subdivisions) — see how
`TCWU07.c2m` uses `CANDU6S` for self-shielding and `CANDU6T` for transport.

Expect k∞ to **drop** relative to 1.0507 once resonance self-shielding is applied. Report the
shift; do not compensate for it.

### A3.3 Fix the group condensation

`COND 24` is wrong twice over: the library is **172 groups, not 99** (`NGRO 172` in the log),
and group index 24 sits at **550 keV**, not the thermal boundary. `EDIGET.f:380-400` shows
`COND` accepts real values as **energies in eV**:

```
COND 0.625
```

### A3.4 Homogenize to one material

`MERG MIX` keeps 10 separate mixtures; DONJON needs one fuel-channel material.

```
EDI := EDI: LIBRARY TRK FLUX GEOMF SYS ::
  EDIT 2 MICR ALL MERG COMP COND 0.625 SAVE ON COND2 ;
```

**GATE A3:**
- deck runs to `END:` with no `XABORT`
- `.result` reports `NGCOND  2` and the energy limits line shows a boundary at ~0.625 eV
- `NMERGE  1`
- report the self-shielded k∞

---

## A4 — SPH homogenization

Append to the A3 deck:

```
MODULE ... SPH: ... ;                  * add SPH: to the MODULE list
SPHED := SPH: EDI TRK FILTRK :: EDIT 2 ;
```

**GATE A4:** no `SPH: MISSING TRACKING FILE`, no `SPH: ... IS AN INVALID TRACKING MODULE`.
SPH factors printed and finite.

If SPH still aborts, **stop and report the exact abort string** — do not start permuting
tracking modules. That is the failure mode that produced 86 dead decks.

---

## A5 — Branch calculations and MULTICOMPO export

**Goal:** the artifact that connects DRAGON to DONJON. **Nothing in the repo currently writes
any cross sections to disk** — this is the single biggest structural gap.

Reference deck: `5.1/Dragon/data/rep900_mco.x2m` (lines 218–230 declare the parameter tree).

### A5.1 Declare the COMPO

```
SEQ_ASCII _ACompo :: FILE "./_ACompo" ;
...
COMPO := COMPO: ::
  EDIT 1
  STEP UP 'EDI2B'
  MAXCAL 5
  COMM 'RBMK-1000 channel' ENDC
  PARA 'burnup' IRRA
  PARA 'TF'  TEMP LIBRARY 6      (* fuel mixture *)
  PARA 'TCA' TEMP LIBRARY 1      (* coolant *)
  PARA 'TG'  VALU REAL           (* graphite temperature - matters a lot for RBMK *)
  PARA 'DCA' VALU REAL           (* coolant density - THIS IS THE VOID AXIS *)
  INIT ;
```

**The export is a plain assignment, and it is the step that has never been done.** After all
branches are filled, write the in-memory COMPO object out to the declared file:

```
_ACompo := COMPO ;
```

Without this line the database lives only in memory and is discarded at `END:` — which is
exactly what happens today to the one good cell calculation. DONJON later reads it back with
`Cpo := _ACompo ;` (see `Donjon/data/channel_mphy.x2m:52,69`). Write side:
`Dragon/data/rep900_mco.x2m:18,944`.

### A5.2 Wrap the cell in CLE-2000 branch loops

Sweep, re-invoking `LIB:` → `USS:` → `FLU:` → `EDI:` per point:

| Axis | Values | Why |
|---|---|---|
| `DCA` coolant density | 0.72, 0.6, 0.45, 0.3, 0.15, 0.05, 0.02 g/cm³ | **the void coefficient** |
| `TF` fuel temperature | 600, 900, 1200, 1500, 2000 K | Doppler |
| `TG` graphite temperature | 500, 700, 900 K | RBMK-specific, large effect |
| `burnup` | 0 → ~20 GWd/t via `EVO:` | the dangerous void coefficient is a high-burnup condition |

Coolant number densities must be **recomputed** per density point — scale `H1` and `O16`
in MIX 1 proportionally to `DCA`. Do not leave them at `4.90E-2` / `2.45E-2`.

`EVO:` has never been run in this project. Add it only after the density and temperature
axes work at zero burnup; treat burnup as a separate sub-task.

### A5.3 Extract delayed-neutron data

The library carries `NDEL 6`. Get β and λ from it — do **not** hardcode 700 pcm as the
quarantined transient decks did. Confirm `LAMBDA-D` is present in the exported COMPO
(`NCRMAC.f:164` copies it through to the macrolib, and `INIKIN:` requires it).

**GATE A5 — this is the most important gate in Tier A:**
- `_ACompo` exists on disk and `UTL: ... DIR` lists the parameter tree
- **the void coefficient is positive**, order **+2 to +5 pcm/%void** at representative burnup
- β_eff from the library is ≈ 0.0065–0.0075

A negative or near-zero void coefficient means the model is not an RBMK. **Stop and report** —
do not proceed, and do not adjust anything to force the sign.

---

## STOP HERE — return for review

Tasks A0–A5 are mechanical. **A6 onward require physics judgement and must not be started
without checking in.** Report:

1. Gate results for A0–A5, with the actual numbers
2. The self-shielded k∞ and how far it moved from 1.0507
3. The void coefficient curve (pcm/%void vs. coolant density), and its sign
4. β_eff and the six (λᵢ, βᵢ) pairs
5. `FLUD:` wall-clock at `MCFD 1` vs. the 729 s `DUAL 3 3` baseline
6. Anything that failed a gate, with the exact abort string — do not work around it

---

## A6–A9 — outline only (do not start yet)

- **A6 CPS channel cells.** B₄C absorber, graphite displacer, water column. The core mix map
  currently has **no rod sites** — every live cell is fuel or graphite, so there is nowhere
  for a rod to go. Gate: displacer-only insertion from below gives **positive** reactivity.
- **A7 Steady-state coupling.** `NCR:` + `THM:` Picard loop to a critical 3200 MWth core.
  Reference: `Donjon/data/channel_mphy.x2m` steady section.
- **A8 Reference AZ-5 transient.** `INIKIN:` → time loop → `DSET:` → `MACINI:` → `NEWMAC:` →
  `TRIVAA: UNIT` → `KINSOL:` → `FLPOW:` → `THM: TIME`. Reference: `AFMtest.x2m` fused with
  `channel_mphy.x2m`. Drive rods with `DSET:` and a computed level — **`MOVDEV:` is broken for
  multi-part rods** (`MOVPOS.f:159` stores 6 positions where `DEVGET.f:246` stored `6*NPART`).
  Model the parked displacer as a base-map mixture, because `NEWMDV.f:92` skips any rod with
  `LEVEL < 1e-4`.
- **A9 Detectors.** `DETINI:`/`DETECT:` at the in-core detector positions; add SPND response
  lag as a first-order filter downstream (DONJON models no detector response). Confirm the
  historical detector type and layout before fixing coordinates.

---

## Known traps (verified against source — trust these over any older document)

| Trap | Evidence |
|---|---|
| `GEO:` mesh is in **cm** | `iaea3d_fuelmap.x2m:99` vs `rbmk_core_3d_realistic.don:1417` |
| SPH needs a `SEQ_BINARY` file; NXT **is** supported | `SPH.F:140`, `SPH.F:239`, `NXT.f:42` |
| `COND` takes **eV** when given a real | `EDIGET.f:380-400` |
| Library is **172 groups** | `rbmk_cell_dlib99_v2.result:371` |
| `TRIVAA:` needs `UNIT` before `INIKIN:`/`KINSOL:` | `TRIVAA.f:174` |
| `EXCELT:` needs `TRAK` **before** `TISO` | `TCWU07.c2m:66` |
| Transient `THM:` is HEM-only | `THMTRS.f:157` hardcodes `IDFM=0` |
| `XENON:` is equilibrium-only | `XENCAL.f` |
| Moderator mixtures need non-zero σ(1→2) | check every `SCAT` line |
| Isotope names | `Zr90`, `C12_GR`, `Nb93`, `He4` |

## If you get stuck

Find a **bundled deck that runs** and does the thing you need, and copy its exact syntax:

```bash
grep -rl "MODULE_YOU_NEED:" /home/wilkie/code/RBMK/5.1/*/data/ | head
ls /home/wilkie/code/RBMK/5.1/Dragon/Linux_aarch64/*.result   # decks that have run
```

Or read the module's Fortran header under `5.1/<code>/src/<MODULE>.f` — every module
documents its calling signature there. Do not guess keywords.
