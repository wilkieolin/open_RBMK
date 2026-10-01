# RBMK-1000 Coupled Neutronics/TH — Project Plan

> **Draglib caveat (2026-09-24).** Every DRAGON number in this document was measured
> against a draglib that is not the one the `libraries` submodule pins — a decompressed
> leftover from an earlier revision that the `.access` hook preferred because it was
> already on disk. The offset is −87 pcm on the A3 cell (1.310172 → 1.308679). The hook is
> fixed; the numbers are not yet re-baselined. See the 2026-09-24 entry in `PROGRESS.md`.


> **Rewritten 2026-09-22 after an audit.** The previous plan's Stage 4 blocker (SPH
> homogenization) was a misdiagnosis, and its priority list was aimed at the wrong problems.
> Full audit: `EVALUATION.md`. Current work order: `TIER_A_WORKPLAN.md`.

## Objective

A 3-D spatially-resolved coupled neutronics/thermal-hydraulics RBMK-1000 model driving a
historically accurate **RBMK mnemonic display** — 1661 channel outlet temperatures, 211 rod
positions, in-core detector readings — in real time, capable of reproducing the Chernobyl
accident conditions including the **AZ-5 positive-scram transient**.

**Scope boundary:** the scenario runs to **fuel failure** and stops. Fuel disassembly, the
steam explosion, and core destruction are out of scope (they require MELCOR or RELAP-SCDAP).

## Why spatial resolution is mandatory

The RBMK's neutron migration length (~1 m) is small against its 12 m diameter, so the core is
weakly coupled and behaves as semi-autonomous regions. That is the origin of its
first-azimuthal-mode xenon instability and of the local excursion that initiated the accident.
A point-kinetics model would not merely miss panel detail — it would miss the phenomenon that
made the accident possible. The mnemonic panel exists *because* the reactor was spatially
unstable.

---

## Architecture

| Tier | Contents | Runs |
|---|---|---|
| **A — offline physics** | DRAGON5 lattice cells → MULTICOMPO → DONJON5 3-D steady state + reference AZ-5 `KINSOL:` transient + `DETECT:` traces | minutes–hours per case |
| **B — online engine** | Standalone 2-group nodal/FD diffusion, 6 delayed-precursor groups, 1-D per-channel TH. GB10 GPU. Reads Tier A cross sections; validated against Tier A. | kHz target; shape ≥10 Hz |
| **C — mnemonic panel** | Channel temps, rod positions, detector signals with SPND response lag | display rate |

**DONJON cannot be the live engine.** It is single-threaded with no GPU path, and one shape
solve is 0.2–3 s — enough for channel temperatures at ~1 Hz, but it would step straight over
the ~4-second excursion that is the point of the scenario. Tier A is what makes Tier B
trustworthy, not what runs the display.

Working-set estimate for Tier B: 67 k nodes × 2 groups ≈ a few MB, plus ~1.6 MB of precursors
and a smaller TH state. Well under 100 MB — no memory risk on the ~110 GB budget.

---

## Roadmap

### Tier A — offline physics (current work; see `TIER_A_WORKPLAN.md`)

| # | Task | Gate |
|---|---|---|
| A0 | Environment + regression baseline | `iaea3d_fuelmap.x2m` → 1.028980 |
| A1 | Quarantine fabricated artifacts | tree contains no tuned-`MAC:` or invented-syntax decks |
| A2 | Run the corrected core | ✅ **done 2026-09-23** — 49×49×32, 1225 × 1225 × 800 cm, 76 832 regions, converged, **k_eff = 1.123062** on IAEA 2-group constants (geometry/solver check only). `FLUD:` **1 s** at `MCFD 1` vs 729 s at `DUAL 3 3`. Three other generators still carry PITCH in metres. <br>**Solver superseded 2026-09-28:** `MCFD 1` loses 31–34 % of absorber worth once a rod cell exists and cannot carry a converged SPH equivalence at all. Production is `DUAL 1 1`, which is **not** `DUAL 3 3` — 2.11 s / 56 MB against MCFD's 1.95 s / 39 MB on this same core, agreeing to 0.7 pcm with no absorber present. |
| A3 | Lattice cell on **RBMK** dimensions + `USS:` + volume-fraction guardrail | ✅ done — **k∞ = 1.313968** on the production SHEM-361 + Zr-SS library (2026-09-26); history: **k∞ = 1.310172** (post bound-hydrogen fix, 2026-09-23; 1.3128 before it); graphite 89.6 %, coolant 3.77 % asserted in-deck |
| A4 | SPH homogenization | ✅ resolved — **not applicable at cell level** (`SPHDRV: INVALID NUMBER OF MACRO-REGIONS`); moved to the core reflector and rod cells |
| A5a | Depletion (`EVO:`) + void branches vs burnup | ✅ **closed 2026-09-26** by the method-convergence segment (`METHOD_CONVERGENCE_PLAN.md`): converged DRAGON and matched OpenMC agree within the plan's criteria; full voiding at 10.9 MWd/kgU is +2.4 to +2.75 $ in every variant. *History:* ⚠️ **half-passed.** Sign and burnup trend confirmed independently by OpenMC; **magnitude is not** — OpenMC gives ~2× DRAGON at discharge and ~12× at fresh fuel. The +1957 pcm / ~4 β figure is **retracted** (`PROGRESS.md`). Carried forward as a 2× bracket, by decision |
| A5b | MULTICOMPO export from the corrected cell — **was the biggest structural gap** | ✅ **done 2026-09-23.** `Dragon/compo/_ACompo`, 113.9 MB, 630 points, axes burnup × DCA × TF × TG (Xe deferred). Round trip to DONJON 6.4 pcm worst over 8 nodes spanning every axis; off-grid `LINEAR` interpolation 27 pcm worst. β **measured** from `NDEL 6`: 0.006824 → 0.004680 over 0–20 MWd/t, confirmed against OpenMC prompt-vs-total to −0.5 %. The second COMPO was **replaced by a correction table** (`openmc/void_bracket.py`) — DRAGON has no cross-section scaling facility anywhere in the write path, so it cannot produce one; see PROGRESS.md "A5b.1d". At discharge burnup the bracket collapses to a single multiplier ≈ 1.9. Applying it is the first item of A7. **Superseded 2026-09-26:** rebuilt on SHEM-361 + Zr self-shielding, 840 points (nodes 7.5 / 12.5 added), 152 MB, round trip 6.7 pcm, off-grid 21.2 pcm; the multiplier is replaced by additive variants A / A′ / B (full void at 10.9 MWd/kgU: +1.95 / +2.42 / +2.72 $); see PROGRESS.md "Phase C". |
| A6 | CPS channel cells: B₄C, graphite displacer, water column, on the A′ basis (`A6_CPS_PLAN.md`) | displacer-only insertion gives **positive** reactivity <br>**Status 2026-09-29:** A6.1 and A6.2 passed (supercell reproduces the single cell to +2.8 pcm). **A6.3 gate missed:** converged DRAGON is 5–12 % from OpenMC on the section worths, carried as the measured A′ correction (+60 to +1107 pcm) and localised — the absolute-k comparison shows convergence fixes the water column at dca 0.72 and the absorber at 0.02, so the residual is spectral, not a single data error. **A6.4 gate failed with the cause found:** homogenisation, SPH and the solver are exact (~1 pcm) but fuel-COMPO neighbours cost 7–10 % on the displacer and drained-channel worths; A6.4b (an explicit rod-cell equivalence) was chosen, built and **disproved 2026-09-30**: matching the rod's flux makes the worth error worse, matching its removal rate will not converge, and a +/-20 % sweep of the rod factors never brings the worth within -3.45 % of a 1 % gate. The cause is not the rod cell -- the eight fuel cells around it differ from infinite-lattice fuel by +/-3 % at zero burnup, because the rod perturbs the spectrum across the whole 75 cm supercell. Carried as a measured one-signed bias (displacer and drained channel low 7-10 %, absorber within +/-3 %) unless A8 proves sensitive. **A6.5:** the core exists on the sourced map (`gen_rbmk_unit4.py`, 52×52×32, all 227 CPS channels placed) but has placeholder reflector data and no rod devices. |
| A6b | **Xenon axis + fuel COMPO rebuild** (new, 2026-09-26). Add a Xe branch axis, and deplete with `EXTR 1` (the step study showed 5 MWd/kg `NOEX` overstates k∞ by 200–530 pcm). Unit 4 was heavily Xe-poisoned at 01:23 after ~12 h at half power and a drop to near zero. | round trip ≤ 10 pcm, off-grid ≤ 30 pcm; Xe worth at equilibrium confirmed against OpenMC |
| A6c | **Smolensk-3 cold zero-power start-up** ([BEH96]; promoted from the deferred Phase D, 2026-09-26). The first core-level measured reference: two critical and two subcritical states with the initial loading described. Tests the 3-D DONJON core with rods, before thermal hydraulics are added. | measured critical states reproduced within the graphite-impurity band; subcriticals ordered correctly; result reported, not tuned <br>**Blocked on an input (2026-09-26):** [BEH96] gives the four states and measured k, but the loading map, including which 28 rods were withdrawn, is in its Ref. 5 (Behrens et al., Kurchatov/Bremen, 1993–94). That report is not online (OSTI/ETDEWEB hold abstracts only). Needs the report, or a substitute from the same group ([ALX98] cites the same sources). The measured rod references that *are* in hand are [BEH96] Table I: critical assemblies 1→1a and 3→3a (4 rods to 148 / 168 cm, −0.26 / −0.15 %Δk) and assembly 8 (rod simulators voided, −0.28 %). They need the D2 facility model. |
| A6d | **Unit 4 initial state at 01:22:30** as a sourced deliverable (new, 2026-09-26): channel map, burnup distribution consistent with [PAV]'s assembly counts, rod pattern (INSAG-7 Fig. II-6, digitised), power, flow, inlet subcooling, axial and radial shape (INSAG-7 Figs. II-7, II-8). Its uncertainty probably dominates the transient's. | every input traceable to a page; DONJON steady state reproduces INSAG-7's reconstructed shape; input ranges recorded for A8 sensitivity <br>**Sources in hand (2026-09-26):** rod depths and site lattice, digitised (211 rods + 12 empty sites; `sources/derived/insag7_fig_II6_012230.csv`); the burnup histogram in 8 groups, 1659 assemblies averaging 10.9 MWd/kgU ([PAV] Table 1; no spatial map, so placement is a stated rule with a sensitivity); one additional absorber and one empty channel (INSAG-7 pp. 67, 107). Figs. II-7 / II-8 are contour and shape plots: comparison targets, not inputs. **Channel map DONE 2026-09-27:** Dollezhal Fig. 2.3 digitised and registered against INSAG-7 Fig. II-6 — exact, all 223 rod sites at a single offset, nothing left over. 1661 fuel + 211 rods + 12 ДКЭ(в) + 4 start-up chambers = 1888 positions, every count closing against a source that was not used to build it. `sources/derived/unit4_channel_map.csv`. **Still needed:** the burnup *placement* rule, the types of 32 of the 211 rods (recorded per row in `type_source`), and the power/flow/xenon state. |
| A7 | Couple: 3-D steady state with `NCR:` + `THM:` | converged critical core at 3200 MWth |
| A8 | Reference AZ-5 transient: `INIKIN:`/`KINSOL:` + `DSET:`, from the A6d state, under bracket variants A′ and B; stops at a defined **fuel-failure criterion** (to be sourced, e.g. a fuel-enthalpy threshold) | prompt power rise before absorber takes over; compared (not tuned) with INSAG-7 Appendix II's three independent reconstructions |
| A9 | Detectors: `DETINI:`/`DETECT:` + SPND lag | traces respond to local rod motion, not just global power |

A0–A5 are largely mechanical. A6–A9 require physics judgement — check in before starting them.

**Order from 2026-09-26:** A6 → A6b → A6c → A6d → A7 → A8 → A9, then Tier B. A6b and A6c come first because xenon and a measured core-level reference both bear on every later step; A6d comes before A7 because the reconstructed initial state is what A7 has to converge to and what A8 starts from.

**Update 2026-09-22:** A3 has been rebuilt on RBMK dimensions (the previous cell was a
CANDU-6 bundle) with `USS:` self-shielding and an in-deck volume-fraction guardrail, and A5
showed a positive void coefficient rising with burnup. A4 turned out not to apply at cell
level. Details and remaining caveats in `PROGRESS.md`.

**Update 2026-09-23 (OpenMC cross-check).** The ~4 β figure quoted in the 09-22 update is
**retracted** — it matched the historically quoted Chernobyl magnitude by coincidence,
produced by a free-gas-hydrogen bug now fixed. OpenMC gives ~8 β at 20 MWd/kg. What survives
independent confirmation is the **sign and the burnup trend**, plus the cell geometry
(analytic volume fractions match DRAGON's tracking to every printed digit) and the method
itself (a CANDU-6 control agrees between the two codes to 1.3 %).

**The A5 gate, restated.** Both earlier numeric targets were wrong: "+2 to +5 pcm/%void" by
an order of magnitude, and the 09-22 correction to "+1 to +3 % Δk/k" is also exceeded —
OpenMC gives +4.0 %. State the gate qualitatively: **positive, and rising steeply with
burnup, at operating burnup**. A fresh unpoisoned cell can legitimately read near zero. The
magnitude is carried as a bracket between the two codes until A8 shows whether it matters.

**Update 2026-09-26 (method convergence closed; the plan reordered).** The lattice-level void gap between DRAGON and OpenMC is closed (PROGRESS.md, "Phase A–B", "Phase C"). Where confidence now stands:

| Level | Confidence |
|---|---|
| Fuel-cell void worth | **good, ±10 %**: two methods plus a third-party benchmark agree |
| Fuel-cell absolute k∞ | **moderate**: DRAGON 240–430 pcm below OpenMC (attributed, not closed), plus ~75–130 pcm depletion step error |
| Anything whole-core (rods, map, TH, transient) | **none yet**: not built or not verified |
| Against measurement | **none at any level**: A6c is the first |

The single-channel full-void figure is not the core void reactivity. That also depends on leakage, rods and the axial shape, which is why A6–A6d come next.

### Tier B — online engine
Standalone GPU solver reading the A5 MULTICOMPO, validated against the A8 transient and A9
detector traces, including through the excursion rather than only at steady state.
Working set is a few MB (76 832 nodes × 2 groups + 6 precursor groups) — no memory risk on
the ~110 GB budget, but never form a dense node-by-node matrix: at 76 832² that is ~47 GB.

### Tier C — mnemonic panel
Driven entirely by Tier B.

---

## Key gotchas (verified against source)

| Gotcha | Evidence |
|---|---|
| `GEO:` mesh coordinates are **centimetres** | contrast `iaea3d_fuelmap.x2m:99` (correct) with `rbmk_core_3d_realistic.don:1417` |
| SPH needs a `SEQ_BINARY` tracking file; NXT **is** supported | `SPH.F:140`, `SPH.F:239`, `NXT.f:42`; pattern in `twimsE_proc/TCWE13.c2m` |
| `EDI: COND` accepts **real energies in eV** as well as group indices | `EDIGET.f:380-400` — use `COND 0.625`, not `COND 24` |
| The APOLIB99 library is **172 groups**, not 99 | `NGRO 172` in `rbmk_cell_dlib99_v2.result:371` |
| `TRIVAA:` requires `UNIT` for anything feeding `INIKIN:`/`KINSOL:` | `TRIVAA.f:174` |
| Use `MCFD 1`, not `DUAL 3 3` | ~40× fewer unknowns; `AFMtest.x2m` precedent |
| Transient THM is **HEM-only** | `THMTRS.f:157` hardcodes `IDFM=0`; `THM.f:1102` passes no `IDFM`/`IPRES` |
| `MOVDEV:` truncates multi-part rods — use `DSET:` | `DEVGET.f:246` vs `MOVPOS.f:159` / `MOVGRP.f:175` vs `NEWMDV.f:97` |
| Rods with `LEVEL < 1e-4` are skipped entirely | `NEWMDV.f:92` — put the parked displacer in the base map |
| `XENON:` is equilibrium-only | `XENCAL.f` — add Xe as an explicit COMPO axis for dynamics |
| `EXCELT:` needs `TRAK` before `TISO` | `twlup_proc/TCWU07.c2m:66` |
| CLE-2000 object/module/procedure names are capped at **12 characters** | `Ganlib/src/objstk.c:189` — longer names give `INVALID OBJECT/MODULE NAME`, which looks like a parser bug and is not |
| Re-creating an existing object needs `X := DELETE: X ;` first | `rep900_mco.x2m:409`; not `DELETE X ;` |
| `rdragon` copies `data/<bare-arg>` — pass the **`.x2m`** or a stale extensionless file shadows the deck | `rdragon:99` |
| COMPO's 2nd `L_EDIT` slot is **group form factors**, not SPH | `COMCAL.f:24`; an SPH edit passed there is silently ignored |
| CLE-2000 inline comments are `!` or `(* *)`; a bare `*` comments only at line start | a trailing `* note` after `;` is parsed as tokens |
| `SPLITR` takes one value per **annulus**, not per region | `CARCEL 5` needs 5 values; the corner region cannot be split |
| `USS:` needs `SUBG` in the `LIB:` block | otherwise `USS: THE INPUT INTERNAL LIBRARY HAS NO SUBGROUPS` |
| SPH cannot correct a `MERG COMP` (single-region) homogenization | `SPHDRV: INVALID NUMBER OF MACRO-REGIONS (9 1)` — needs one region per tracking macro-region |
| Merged volumes live in `MIXTURESVOL`, not `VOLUME` | inside the edition's saved directory |
| Graphite must actually moderate | check `SCAT` has non-zero σ(1→2) in every moderator mixture |
| **A DRAGON geometry with an open (`VOID`) boundary gives a wrong solution here** — 2–5× too much leakage, while fully reflected ones are right to 170 pcm. Geometry, boundary keywords, tracking density and leakage model all eliminated; cause unknown. Close the geometry, or verify against OpenMC. | `openmc/slab.py`: a 1 m fuel slab with one vacuum face is 1.198662 ± 69 pcm in OpenMC, 0.849315 in DRAGON |
| Mixture **0** in a DONJON reactor geometry is a *virtual volume*, and the boundary condition is applied at the **real/virtual interface**, not at the grid edge | `USPMIX.f:52` drops `MAT(IEL)==0`; verified by k being bit-identical for 1, 3 and 5 cells of mixture-0 padding (`tools/u4_leakage.sh`) |
| `USPLIT:` needs `NREFL + NFUEL` to equal the **highest material index** — no gaps | `@USPLIT: WRONG NUMBER OF REFLECTOR OR FUEL TYPES`; put reflector mixtures first and fuel last, as `1Sap_vs_3Sap.x2m:29` does |
| `MACINI:` indexes the non-fuel macrolib by **material number**, and demands an `H-FACTOR` block in the combined macrolib | `MACINI.f:274`; so `MACREF`'s `NMIX` is `max(RMIX)` and every index below it must be defined |
| `NCR:` with a fuel map on the RHS takes `NMIX` from the map (`NCH × NB`), and rejects a smaller explicit one | `NCR.f:127` then `NCR.f:157`; omit `NMIX` on the `TABLE` call |
| `NCR: … TABLE` can `SET` burnup instead of reading it from the map, with no `INST-BURN` | `NCRRGR.f:717` prints "L_MAP values overwritten by the SET option"; `NCRMAP.f` then reads nothing |
| `THMDRV` **overwrites its own `SPEED` argument** (sets it from `MFLOW/DCOOL(1)`, the outlet velocity) | `THMDRV.f:266,286`; hand it a scratch copy or Picard iteration 2 silently runs on iteration 1's outlet velocity. `THMTRS` takes `SPDIN` and is safe |
| `THMINP` has handled the `CHAN <one value per channel>` form since 2018 — only `THM:`'s own parser did not | `THMINP.f:43`; that is why `patches/0001-THM-per-channel-inlet-velocity.patch` is 139 lines and not a rewrite |
| A source change inside `5.1/` is **invisible to this repo and lost by a submodule update** | `5.1/` is pinned upstream and gitignored; patches live in `patches/` and `tools/apply_patches.sh` reapplies them from `bootstrap.sh` |
| `THM:`'s default boiling model never reverts to the thermodynamic quality | Bowring (`ISUBM=1`) damps vapour generation by `1/(1+Π)` and `Π` stays positive after the bulk saturates (`THMH2O.f:161`); use `SAHA` (`ISUBM=2`), whose `F2 = (h-h_f)/h_fg` is the energy balance (`THMH2O.f:165`) |
| `THM:`'s gap correlation implies a much tighter gap than RBMK fuel has | measured against [D] p.95's 2100 C centreline and against bare helium conduction over the sourced 100 um gap, which agree on ~1700-2800 W/m2/K; set `HGAP` explicitly |
| `SET-PARAM` addresses a fuel-map parameter by **`P-NAME`, not `PARKEY`**, and a `LOCAL` one needs `SAME`/`CHAN`/`BUND` before its value | `RESPAR.f:139-176`; only a `GLOBAL` parameter takes a bare number |
| `THM:` writes back only into parameters named `T-FUEL`, `D-COOL`, `T-COOL`, `T-SURF`, `P-COOL` | `THM.f:1172-1174`; `NCR:` then reads them by `PARKEY`, which is why the two names differ |
| `THM:`'s `CLUSTER` is an infinite **triangular** array, so one pitch cannot match an RBMK channel's flow area, hydraulic diameter and heated perimeter | `THM.f:963-971`; match the flow area — measured 2026-10-01, the hydraulic diameter reaches nothing compared once the surface is in nucleate boiling |
| A COMPO built on a lattice-cell *nominal* state will not cover a real core: the subcooled inlet is **denser** than nominal and a low-power channel end is **colder** than the fuel-temperature floor | measured 2026-10-01 by running the A7 Picard loop -- `DCA` wanted 0.778 against an axis top of 0.72, `TF` wanted 586 K against a floor of 600; `NCR:` has no clamp, so the axis has to cover it |
| `UTL:` must be in the `MODULE` list before any `UTL:` call parses | otherwise `objstk: OBJECT/MODULE NOT YET DECLARED`, error 5004, which does not point at the module list |
| The flat `POWER-CHAN` block, not `FLPOW:`'s radial-plane table, is the handover for per-channel data | it is in **channel order** -- what `RESPFM.f:74-82` finds and what `THMINP` reads a `CHAN` list in |

---

## Standing rules

The authoritative list, with the incident behind each one, is in `PROGRESS.md`. In short:

1. **Every asserted value must come from a calculation, never from a constant chosen to make
   the assert pass.**
2. **Every deck must verify what it actually built, not what it was meant to build.**
3. **An error message from DRAGON is a statement about the input until proven otherwise.**
4. **No physics number is validated until a second, independent method reproduces it.**
5. **A DRAGON `.result` is not evidence unless it postdates the deck.** Delete it before
   re-running.
6. **A fix that lives in a copy of the file is not a fix.** Correct the file everything calls.

---

## Key gotcha added 2026-09-23

**Coolant hydrogen must be `H1_H2O`, not `H1`.** `DLIB_99` contains both; bare `H1` is
free-gas, with no bound-water thermal scattering law, and it overstates water's moderating
power — which suppresses the positive void coefficient. Every bundled reference deck
(`twlup_proc/`, `rep900_mco_proc/`) uses the bound form. Worth +140 pcm at full void and
−264 pcm on k∞. Same applies to `H2_D2O` and `C12_GR`.

---

*Last updated: 2026-09-29 (A6 status through A6.5; A2's solver superseded — `DUAL 1 1`, not
`MCFD 1`, because MCFD loses a third of the absorber worth; A6d's channel map closed and
sourced). Previously: 2026-09-23 (A5a downgraded to half-passed; A2 restated; hydrogen gotcha
and full standing-rule list added)*
