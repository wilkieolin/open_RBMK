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
| A2 | Run the corrected core | ✅ **done 2026-09-23** — 49×49×32, 1225 × 1225 × 800 cm, 76 832 regions, converged, **k_eff = 1.123062** on IAEA 2-group constants (geometry/solver check only). `FLUD:` **1 s** at `MCFD 1` vs 729 s at `DUAL 3 3`. Three other generators still carry PITCH in metres |
| A3 | Lattice cell on **RBMK** dimensions + `USS:` + volume-fraction guardrail | ✅ done — **k∞ = 1.310172** (post bound-hydrogen fix, 2026-09-23; 1.3128 before it); graphite 89.6 %, coolant 3.77 % asserted in-deck |
| A4 | SPH homogenization | ✅ resolved — **not applicable at cell level** (`SPHDRV: INVALID NUMBER OF MACRO-REGIONS`); moved to the core reflector and rod cells |
| A5a | Depletion (`EVO:`) + void branches vs burnup | ⚠️ **half-passed.** Sign and burnup trend confirmed independently by OpenMC; **magnitude is not** — OpenMC gives ~2× DRAGON at discharge and ~12× at fresh fuel. The +1957 pcm / ~4 β figure is **retracted** (`PROGRESS.md`). Carried forward as a 2× bracket, by decision |
| A5b | MULTICOMPO export from the corrected cell — **was the biggest structural gap** | ✅ **done 2026-09-23.** `Dragon/compo/_ACompo`, 113.9 MB, 630 points, axes burnup × DCA × TF × TG (Xe deferred). Round trip to DONJON 6.4 pcm worst over 8 nodes spanning every axis; off-grid `LINEAR` interpolation 27 pcm worst. β **measured** from `NDEL 6`: 0.006824 → 0.004680 over 0–20 MWd/t, confirmed against OpenMC prompt-vs-total to −0.5 %. The second COMPO was **replaced by a correction table** (`openmc/void_bracket.py`) — DRAGON has no cross-section scaling facility anywhere in the write path, so it cannot produce one; see PROGRESS.md "A5b.1d". At discharge burnup the bracket collapses to a single multiplier ≈ 1.9. Applying it is the first item of A7. |
| A6 | CPS channel cells: B₄C, graphite displacer, water column | displacer-only insertion gives **positive** reactivity |
| A7 | Couple: 3-D steady state with `NCR:` + `THM:` | converged critical core at 3200 MWth |
| A8 | Reference AZ-5 transient: `INIKIN:`/`KINSOL:` + `DSET:` | prompt power rise before absorber takes over |
| A9 | Detectors: `DETINI:`/`DETECT:` + SPND lag | traces respond to local rod motion, not just global power |

A0–A5 are largely mechanical. A6–A9 require physics judgement — check in before starting them.

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

*Last updated: 2026-09-23 (A5a downgraded to half-passed; A2 restated; hydrogen gotcha and
full standing-rule list added)*
