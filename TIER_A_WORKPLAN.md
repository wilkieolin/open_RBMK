# Tier A Work Order — Offline RBMK Physics (DRAGON5 / DONJON5)

> **Draglib caveat (2026-09-24).** Every DRAGON number in this document was measured
> against a draglib that is not the one the `libraries` submodule pins — a decompressed
> leftover from an earlier revision that the `.access` hook preferred because it was
> already on disk. The offset is −87 pcm on the A3 cell (1.310172 → 1.308679). The hook is
> fixed; the numbers are not yet re-baselined. See the 2026-09-24 entry in `PROGRESS.md`.


*(Paths in this document are relative to the repository root.)*

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
export PATH="$PWD/install/bin:$PATH"
export LD_LIBRARY_PATH="$PWD/install/lib:$LD_LIBRARY_PATH"
```

Decks are authored in `decks/`, not in the submodule. `tools/link_decks.sh` symlinks
them into `5.1/{Dragon,Donjon}/data/`, which is where rdragon insists on finding them —
see README.md for why. Run the script after adding a deck.

Running a deck (output lands in `Linux_<arch>/<name>.result`):

```bash
cd 5.1/Dragon  && ./rdragon -c custom -p 1 -w rbmk_<name>.x2m
cd 5.1/Donjon  && ./rdonjon -c custom -p 1 -w rbmk_<name>.don
```

A deck that needs the nuclear-data library must have a sibling `<name>.access` hook. Do
not copy one: symlink it to the shared script, which is the only copy of that logic.

```bash
ln -s ../../common/dlib99.access decks/Dragon/data/<name>.access   # stages DLIB_99
ln -s ../../common/compo.access  decks/Donjon/data/<name>.don.access   # stages the COMPO
```

Reading results — always check the tail, not just the exit code:

```bash
tail -30 5.1/Dragon/Linux_aarch64/<name>.result
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
mkdir -p quarantine
```

Move into `quarantine/` (do **not** delete — they are evidence):

- `5.1/Dragon/data/rbmk_cell_iaea_xs.dra` — hand-tuned `MAC:` block, no nuclear data
- `5.1/Dragon/data/rbmk_cell.x2m`, `rbmk_cell_iaea_sph*.x2m`, `rbmk_cell_sph.x2m`,
  `rbmk_cell_sph2.x2m`, `rbmk_cell_sph_save.x2m`, `rbmk_cell_realistic.dra`
- `rbmk_cell_simple.dra` and `rbmk_cell.dra`
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

- ~~`TRIVAT: ... DUAL 3 3` → `TRIVAT: ... MCFD 1`~~ (≈40× fewer unknowns; precedent `AFMtest_proc/Pcalflu.c2m:45`)
- `FLUD:` / solver block: `EPSOUT 1.0E-7` → `1.0E-5`

> **SUPERSEDED 2026-09-28 — use `TRIVAT: ... DUAL 1 1`.** The MCFD recommendation was made before
> any rod cell existed and is wrong once one does. Measured on the A6.4 gate over 18 states,
> `MCFD 1` loses **31–34 % of the absorber worth**: one mesh-centred point per 25 cm node cannot
> represent the flux depression in a black absorber. It also cannot carry a converged SPH
> equivalence at all — it oscillates from iteration 5 and hits the 200-iteration cap, where
> `DUAL 1 1` converges in 40 on identical transport, and on the full deck it ended in a segfault
> in `TRI1GSO`.
>
> The speed argument that motivated MCFD does not survive either, because **`DUAL 1 1` is not
> `DUAL 3 3`**. Matched runs on the same core, same machine: MCFD 1.95 s / 39 MB,
> DUAL 1 1 2.11 s / 56 MB — 8 % — and the two agree to 0.7 pcm where no absorber is present.
> `decks/Donjon/data/rbmk_core_3d_dual.don` is the timing probe; A6.5's generator
> (`gen_rbmk_unit4.py`) already emits `DUAL 1 1`.

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

**The export is a plain assignment, and it is the step that has never been done.**
(2026-09-23 (3): **superseded.** The second COMPO is not producible — DRAGON has no
cross-section scaling facility in `LIB:`, `EDI:` or `COMPO:`, the whole write path. The
bracket is carried instead as a ratio table, `openmc/void_bracket.py`, and applied in the
consuming deck. Still the branch *ratio* k_void/k_nom, never absolute k: the two codes'
depletion trajectories diverge, so correcting absolute k would fold a depletion difference
into a void correction. A8 still runs under both variants.) After all
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

**GATE A5 — this is the most important gate in Tier A: PASSED 2026-09-23 (3).**
- `_ACompo` exists on disk and `UTL: ... DIR` lists the parameter tree — ✅ 113.9 MB, 630
  points, `burnup × TF × TG × DCA`. Xe axis deferred.
- **the void coefficient is positive and rises steeply with burnup** — ✅ in both codes.
  DRAGON +222 → +2190 pcm, OpenMC +1030 → +4007 pcm, fresh → 20 MWd/t at full void.
- β_eff comes out of the library as a **burnup curve**, not a scalar — ✅ 0.006824 → 0.004680,
  and it agrees with OpenMC's prompt-vs-total to −0.5 % at the one state both can reach.

Two checks not in the original gate, added because "a COMPO exists on disk" is not evidence
of anything: the DRAGON→DONJON round trip is **6.4 pcm** worst-case over eight nodes spanning
every axis extreme (not the 0.4 pcm of the corner point), and off-grid `LINEAR` interpolation
— which is what the transient will actually use — is **27 pcm** worst-case.

A negative or near-zero void coefficient at operating burnup means the model is not an RBMK.
**Stop and report** — do not proceed, and do not adjust anything to force the sign.

> **Both numeric targets originally written here were wrong. Corrected 2026-09-23.**
>
> *"+2 to +5 pcm/%void"* was low by an order of magnitude. It was corrected once, to
> "+1 to +3 % Δk/k for near-complete voiding", and that is wrong too — OpenMC gives +4.0 %
> at 20 MWd/kg. The magnitude is genuinely uncertain: DRAGON and OpenMC differ by 2× at
> discharge, and the disagreement is not resolved. (The "12× at fresh fuel" figure quoted
> here was computed before the `H1_H2O` fix; with bound hydrogen it is 4.6×, and with four
> OpenMC densities instead of two it is clear the *shapes* differ at fresh fuel, so no single
> fresh-fuel ratio is meaningful. At discharge the shapes agree and the ratio is a stable
> 1.83–1.98.) **Do not gate on a number.** Gate on the sign and the trend, and carry the magnitude as a bracket between the
> two codes. Setting a numeric target here is what standing rule 1 exists to prevent: the
> only way to hit a target of unknown correctness is to tune toward it.
>
> *"β_eff ≈ 0.0065–0.0075"* is a fresh-fuel figure. β_eff **falls** with burnup as Pu-239
> (β ≈ 0.0021) displaces U-235 (β ≈ 0.0065), so a single number cannot be right across the
> burnup axis — and the state that matters is discharge burnup, where it is nearer 0.0045.
> This compounds: the void worth in dollars grows twice over with burnup, numerator up and
> denominator down. Extract the curve. Cheap independent check: OpenMC gives
> β_eff ≈ 1 − k_prompt/k_total via `settings.create_delayed_neutrons = False`.
>
> **Done 2026-09-23 (3).** Measured: 0.006824, 0.006361, 0.005877, 0.005358, 0.004985,
> 0.004680 at 0/2/5/10/15/20 MWd/t. The guess above was good — 0.0068 fresh, 0.0047 at
> discharge. OpenMC's independent check gives 0.006856 ± 0.000162 at fresh fuel, −0.5 % from
> DRAGON. The compounding is real: full-void worth goes from +0.33 $ to +4.68 $ (DRAGON) or
> +1.51 $ to +8.56 $ (OpenMC) over life — **prompt-supercritical at discharge either way.**

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

## A6–A9 — outline

*Order from 2026-09-26: A6 → A6b → A6c → A6d → A7 → A8 → A9 (PROJECT_PLAN.md, roadmap).*

- **A6 CPS channel cells.** B₄C absorber, graphite displacer, water column. Gate:
  displacer-only insertion from below gives **positive** reactivity.
  **Work order: `A6_CPS_PLAN.md`** (started 2026-09-26, on the A′ basis).
  *Status 2026-09-29: A6.1 passed; A6.2 passed; A6.3 gate missed at 5–12 % with the residual
  measured and localised; A6.4 gate failed with the cause identified and A6.4b chosen to close
  it; A6.5's core exists on the sourced map, with a placeholder reflector and no rods.
  **Superseded 2026-09-30: A6.4b is disproved.** No rod-only SPH factor closes gate A6.4 at any
  value — a ±20 % sweep never brings the worth error within −3.45 % of a 1 % gate — because the
  cause is not the rod cell. The eight fuel cells around it differ from infinite-lattice fuel by
  ±3 % at zero burnup, the rod having perturbed the spectrum across the whole 75 cm supercell.
  Carried as a measured one-signed bias unless A8 proves sensitive; see `A6_CPS_PLAN.md`.
  **Updated 2026-10-01: A6.5's core now solves the whole chain** — `NCR:` ×2 → `MACINI:` →
  `TRIVAT: DUAL 1 1` → `TRIVAA:` → `FLUD:` → `FLPOW:` on 58 × 58 × 32 with real cross sections in
  every mixture, including a sourced 4-column radial reflector from `_RCompo`, in 8.1 s;
  k = 1.018278, reported not asserted. The radial reflector is worth 131 pcm and only 2.6 pcm
  leaks past it, which closes the Phase 1b question.
  **Gate A6.5 measured 2026-10-01: the mechanism is confirmed and the positive sign is
  confirmed conditionally.** The 4.5 m displacer is worth +2060 pcm against a water column;
  the first 1.25 m of travel is -175 pcm with a centre-peaked flux and +177 pcm once the
  axial peak is driven below the mid-plane, the sign tracking the peak in both directions.
  So **A6b (xenon) and A6d (burnup placement) are on the critical path to A8** by
  measurement: they are what supplies the bottom-skew for real. See PROGRESS.md "Gate A6.5".
  Still open: `DEVINI:`/`DSET:` devices for A8's *moving* rods, and the RR stroke.
  The "no rod sites" problem above is solved — `gen_rbmk_unit4.py` places all 227 CPS channels
  at their real positions.*
- **A6b Xenon axis and fuel COMPO rebuild.**
  **Scope grew 2026-10-01: the rebuild must also widen two existing axes, measured by running
  the coupled core (PROGRESS.md "A7b").** The A5b axes were built around a lattice-cell nominal
  state and a real core leaves the box at both ends, so A7 cannot converge on them:
  `DCA` tops out at 0.72 g/cm3 while a 265 C channel inlet is subcooled at **0.778**, and `TF`
  floors at 600 K while the ends of a low-power channel sit at **586 K** — a zero-power fuel
  node is at coolant temperature by definition, so this is not specific to our core. `NCR:` has
  no clamp, so there is no deck-level workaround. Add **~0.80 g/cm3** to `dcalist`
  (`rbmk_a5b_compo.x2m:99`, 7 values, so one more is 1/7 of the branch tensor) and **~530 K**
  below the `TF` floor. Pinning `DCA` instead costs 103 pcm core-wide, an upper bound.
  Then: add a Xe branch axis (equilibrium Xe at the branch
  power, plus a zero-Xe and a peak-Xe point) and switch depletion to `EVO: EXTR 1` with
  ≤ 2.5 MWd/kg steps; test that combination against `rbmk_meth_dstep125` first. Gates as A5b
  (≤ 10 / ≤ 30 pcm), plus an OpenMC check of the Xe worth at 10.9 MWd/kgU.
- **A6c Smolensk-3 cold zero-power start-up ([BEH96]).** Build the first-core loading in the
  3-D DONJON model with the A6 rods and reproduce the two measured critical states and the
  ordering of the two subcritical ones. Cold, zero power, no TH: a test of the core model
  alone. Report the graphite-impurity sensitivity; do not tune it.
- **A6d Unit 4 initial state at 01:22:30.** A sourced deliverable, not a step inside A8.
  *Status 2026-09-27: the channel map and the rod pattern are DONE and sourced — registering
  Dollezhal Fig. 2.3 against INSAG-7 Fig. II-6 is exact (all 223 rod sites at one offset), and
  every count closes against an independent source. `sources/derived/unit4_channel_map.csv`.
  The remaining items below are still open.*
  - channel map;
  - burnup distribution consistent with [PAV];
  - rod pattern digitised from INSAG-7 Fig. II-6;
  - power, flow, inlet subcooling and xenon state;
  - the radial and axial shapes of INSAG-7 Figs. II-7 / II-8.

  Record a range for every uncertain input; A8 runs its sensitivity over them.
- **A7 Steady-state coupling.** `NCR:` + `THM:` Picard loop to a critical 3200 MWth core.
  Reference: `Donjon/data/channel_mphy.x2m` steady section.
  *Prerequisite done 2026-10-01: `THM:` now takes per-channel inlet flow,
  `SPEED CHAN <list>` (`patches/0001-THM-per-channel-inlet-velocity.patch`, verified by
  `tools/thm_chan_check.sh` and `tools/thm_chan_regress.sh`).*
  **A7 must converge under `DFM 0`:** `THMTRS.f:157` assigns `IDFM = 0` unconditionally, so a
  core converged with drift flux changes void model at t = 0 — unacceptable for a reactor whose
  whole accident is a void feedback. Drift flux is a steady-state sensitivity only.
  *A7a done 2026-10-01: one channel against [D] p.95 -- outlet temperature 289.47 against
  289.3, exit quality 16.50 % against a published 19.6 % that lies outside the box [D]'s own
  power and flow ranges allow. The `THM:` block is now determined except for the flow
  distribution: `CLUSTER 1.7639e-2 18`, `RADIUS` from the A6.1 cell, `SAHA` (NOT the default
  Bowring), `DFM 0`, and `HGAP` set explicitly from the sourced 100 um gap. See PROGRESS.md
  "A7a" and `tools/a7a_check.sh`.*
  Geometry is `CLUSTER <pitch> 18`, not `ASSMB` (`THM.f:460`). Graphite temperature has to be
  supplied from outside: nothing in DONJON computes it, yet the fuel COMPO carries a `TG` axis
  (`rbmk_a5b_compo.x2m:133`, pinned at 750 K today).
- **A8 Reference AZ-5 transient.** Starts from the A6d state; runs under bracket variants A′
  and B (`openmc/void_bracket.corrections`); stops at a sourced fuel-failure criterion;
  compared, not tuned, with INSAG-7 Appendix II's three reconstructions. `INIKIN:` → time loop → `DSET:` → `MACINI:` → `NEWMAC:` →
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
| **`VOID` boundaries in DRAGON are not trustworthy here** (2–5× over-leakage; reflected geometries are fine) | `openmc/slab.py`, 2026-10-01 |

## If you get stuck

Find a **bundled deck that runs** and does the thing you need, and copy its exact syntax:

```bash
grep -rl "MODULE_YOU_NEED:" 5.1/*/data/ | head
ls 5.1/Dragon/Linux_aarch64/*.result   # decks that have run
```

Or read the module's Fortran header under `5.1/<code>/src/<MODULE>.f` — every module
documents its calling signature there. Do not guess keywords.
