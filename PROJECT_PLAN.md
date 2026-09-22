# RBMK-1000 Coupled Neutronics/TH — Project Plan

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
| A2 | Fix units bug; reflector; `MCFD 1`; re-baseline core | core is 1225 cm across; solver converges |
| A3 | Lattice cell: `SEQ_BINARY` tracking, self-shielding, `COND 0.625`, `MERG COMP` | k∞ with self-shielding, 2 groups, correct thermal cut |
| A4 | SPH homogenization | `SPH:` completes; no `MISSING TRACKING FILE` |
| A5 | Branch calculations + MULTICOMPO export | **positive void coefficient**, +2…+5 pcm/%void |
| A6 | CPS channel cells: B₄C, graphite displacer, water column | displacer-only insertion gives **positive** reactivity |
| A7 | Couple: 3-D steady state with `NCR:` + `THM:` | converged critical core at 3200 MWth |
| A8 | Reference AZ-5 transient: `INIKIN:`/`KINSOL:` + `DSET:` | prompt power rise before absorber takes over |
| A9 | Detectors: `DETINI:`/`DETECT:` + SPND lag | traces respond to local rod motion, not just global power |

A0–A5 are largely mechanical. A6–A9 require physics judgement — check in before starting them.

### Tier B — online engine
Standalone GPU solver reading the A5 MULTICOMPO, validated against the A8 transient and A9
detector traces, including through the excursion rather than only at steady state.

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
| Graphite must actually moderate | check `SCAT` has non-zero σ(1→2) in every moderator mixture |

---

## Standing rule

**Every asserted value must come from a calculation, never from a constant chosen to make the
assert pass.**

---

*Last updated: 2026-09-22 (post-audit rewrite)*
