---
id: 4
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, numerics, infra]
---

# Phase 0 corrections (bound hydrogen) and A2 first run of the 3-D core

Before building the MULTICOMPO, the known-wrong pieces were fixed on 2026-09-23: coolant hydrogen moved to the bound `H1_H2O` evaluation in the single composition file, the variant procedure files were made to differ in exactly one line, and two over-strong records were corrected. In the same period A2 ran the corrected 3-D core deck for the first time and passed its gate as a geometry/solver check, with an unexpectedly fast `MCFD 1` solve.

**Sources:** PROGRESS header blockquote 2026-09-23 (2); sections "Phase 0 corrections — 2026-09-23" and "A2 — the 3-D core, run at last — 2026-09-23"; root cause 2 correction in "Root causes". Key files: `rbmk_proc/RbmkLib.c2m`, `RbmkLibF.c2m`, `RbmkLibH.c2m` (retired), `RbmkLibN`/`RbmkLibW`, `Dragon/data/rbmk_cell_a3.x2m`, `rbmk_h2otest.x2m`, `rbmk_ussopt.x2m`, `quarantine/orphaned_access/`, `Donjon/data/rbmk_core_3d_realistic.don`, `gen_rbmk_realistic.py`, `gen_rbmk_donjon.py`, `gen_rbmk_geo.py`, `gen_rbmk_simple.py`, `TIER_A_WORKPLAN.md`, `plans/`.

## Outcome
- `RbmkLib.c2m:44` → `H1_H2O`; `rbmk_cell_a3.x2m` re-run from a deleted `.result` gives **k∞ = 1.310172**, matching the value `rbmk_h2otest.x2m` had measured independently; guardrail passes (89.594 / 3.772 / 2.901 %). Later superseded by the draglib and geometry changes (cards 5, 6).
- Reshuffle verified physics-neutral: `rbmk_h2otest` reproduces bit for bit — free gas 1.312816 / 1.316728 / 1.314234 and bound 1.310172 / 1.314718 / 1.313999 at dca 0.72 / 0.35 / 0.02, i.e. +226 / +82 and +264 / +222 pcm.
- `RbmkLibH.c2m` retired; `RbmkLibF.c2m` kept with a do-not-use banner; `RbmkLibN`/`RbmkLibW` headers corrected to describe `CTRA`. Each variant differs from `RbmkLib` in exactly one non-comment line (checked mechanically). Six diagnostic decks repointed.
- Housekeeping: 21 orphaned `.access` scripts moved to `quarantine/orphaned_access/`; `rbmk_ussopt.x2m` header corrected.
- Live hazard left: ~16 legacy `rbmk_cell_*` decks hardcode free-gas `H1` and coolant density `4.90E-2` (vs `4.81360E-2`); `rbmk_cell_dlib99_v2.x2m` (the retracted CANDU bundle) was still named as the A0 baseline in `TIER_A_WORKPLAN.md`.
- Nothing was under version control (`5.1/` an upstream submodule; RBMK decks, `quarantine/`, `openmc/` untracked).
- A2: 49 × 49 × 32, 25 cm pitch, extent 1225 cm × 1225 cm × 800 cm, 76 832 regions, IAEA 2-group PWR cross sections (geometry and solver check only): **k_eff = 1.123062**, converged; `FLUD:` **1 s** at `MCFD 1` against 729 s for `DUAL 3 3` (~700×, not the ~40× estimated). Gate A2 passed.
- Record corrections: the generator units bug had already been fixed on 09-22; the deck's `assertS ... 1.123062` was first read as inherited, but running the deck reproduces it exactly, so the deck had been run on 09-22 without leaving a `.result` — "never been run" overstated what timestamps showed. The assert was removed anyway because A2 must report, not expect, k_eff.
- Still open after A2: `gen_rbmk_donjon.py`, `gen_rbmk_geo.py`, `gen_rbmk_simple.py` carry PITCH in metres; the core mix map has no rod sites (A6).

## Narrative
- 2026-09-23: Applied the hydrogen fix before A5b so the MULTICOMPO would not be built on a known-wrong cell, and treated the re-run as a regression check against the independently measured 1.310172 rather than a new claim. Removed the duplicate-file fix (`RbmkLibH`) because keeping a fix in a second file was what let A3 and A5 run the wrong composition for a day; kept the free-gas file only so the comparison stays reproducible. Recorded, but did not act on, the legacy decks that bypass the single source of truth, and the absence of version control that made timestamps the only evidence of what had run. (by @assistant)
- 2026-09-23: Ran A2. The 1.123062 is physically right for the wrong-on-purpose constants (k∞ ≈ 1.12, a 12.25 m core leaks almost nothing), which is the whole content of the test; the old 0.054 was a 12 cm cube. The 1 s solve does not change the Tier B conclusion (still two orders off a 10 Hz panel) but makes a DONJON-in-the-loop quasi-static fallback far more viable and the offline A8 transient much cheaper than budgeted. Corrected the earlier reading of the assert and of "never been run". (by @assistant)
