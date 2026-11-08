---
id: 5
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, numerics, infra, openmc]
---

# A5b MULTICOMPO, the measured β curve, and the unprovenanced draglib

A5b (2026-09-23) wrote cross sections to disk for the first time, connecting the lattice work to the core: a 630-point, four-axis MULTICOMPO, gated by round-trip and off-grid interpolation tests and a β_eff burnup curve extracted from the library and checked against OpenMC. The DRAGON/OpenMC disagreement was carried as a data bracket rather than a second database. On 2026-09-24 a repo restructuring showed every DRAGON number to date had been computed on a decompressed draglib that was not the pinned one (−87 pcm on k∞), and the library cache was made content-addressed.

**Sources:** PROGRESS sections "A5b — the MULTICOMPO — 2026-09-23" (incl. "The full run … — 2026-09-23 (3)", "A5b.1d", and its revision dated 2026-09-24 (3)); "The draglib the whole project was running on is not the one it ships — 2026-09-24". Key files: `Dragon/data/rbmk_a5b_compo.x2m`, `Dragon/compo/_ACompo`, `Donjon/data/rbmk_a5b_verify.don`, `rbmk_a5b_sweep.don`, `rbmk_a5b_offgrid.x2m`, `rbmk_chainprobe.x2m`, `rbmk_micrprobe.x2m`, `rbmk_deldiag.x2m`, `openmc/compare_bu.py`, `branch_mid.py`, `openmc/void_bracket.py`, `decks/common/dlib99.access`, `tools/tidy_libraries.sh`, `.cache/draglib/`.

## Outcome
- Axes: burnup 0, 2, 5, 10, 15, 20 MWd/kg; `DCA` 0.72 … 0.02 g/cm³ (7 values); `TF` 600–2000 K (5); `TG` 500, 750, 900 K — **630 branch points**, self-shielding redone at each. Xe deliberately not an axis yet.
- Two non-obvious requirements found by writing the verify deck first: `EDI: GOLVER` alone silently drops diffusion coefficients (flag `IDATA(9)` set only under a leakage model, `EDIPXS.f:413-419`; stored as `STRD`, `COMACR.f:246`); fix is `FLU: ... TYPE K B1 SIGS BUCK 0.0` (k∞ 1.310172 → 1.310173). `rdragon` discarded `_ACompo` with the scratch dir; `data/<deck>.save` hook now lands it in `Dragon/compo/`.
- `MICR` list of 31 nuclides derived, closed under `EDILUM.f`'s lumping rule (`Ru103` the only addition). `LAMBDA-D` carries library decay constants 0.013336 … 2.85300 s⁻¹.
- Full run: **1 h 21 min**, 113.9 MB, 630/630 rows. Round trip over 8 nodes: worst **6.4 pcm** (the earlier 0.4 pcm corner figure was optimistic by 16×). Off-grid `LINEAR`: worst **27 pcm**.
- β(BU): 0.006824, 0.006361, 0.005877, 0.005358, 0.004985, 0.004680 at 0/2/5/10/15/20 MWd/kg; Pu-239 0.002254 vs U-235 0.006524 in `DLIB_99`. OpenMC prompt-vs-total β_eff 0.006856 ± 0.000162 (−0.5 %). The assumed 0.0048 is wrong by +42 % at fresh fuel.
- Trap caught: first extraction gave 0.006524 everywhere because `GETVAL 'NUSIGF' 1` reads one element and `NBFIS = 18`; fixed with `MEAN 'NUSIGF' 1 18`.
- Dollars at full void: DRAGON +4.68 $ / OpenMC +8.56 $ at 20 MWd/kg. *Pre-geometry-fix and read at the wrong burnup; superseded 09-24 (3)/(4) (card 6).*
- A5b.1d: a second, rescaled COMPO cannot be produced (no scaling hook in `LIB:`/`EDI:`/`COMPO:`; `MAC: ADD` is update-mode only); bracket carried as data r(BU, v) in `void_bracket.py`. At 20000 MWd/t r = 1.83–1.98, a single multiplier near **1.9**. *Revised 2026-09-24 (3): Unit 4 averaged 10.9 MWd/kgU ([PAV] Table 1), so the ~1.9 describes a core Unit 4 never was; the multiplier design was replaced by additive variants (09-24 (4) recommendation, Phase C, card 7).*
- Draglib: in-place gunzip cached a pre-upgrade file (134,497,940 bytes, k∞ **1.310172**) against the pinned `cb1395ffbb65…` (83,700,460 bytes, k∞ **1.308679**): **−87 pcm** under every recorded DRAGON result. Second mismatch: `ecco1962_light` 317,833,351 vs 161,707,708 bytes. Provenance unestablished.
- Fix: `dlib99.access` content-addresses the cache to `.cache/draglib/<lib>.<sha12>`; `tidy_libraries.sh` moves non-matching leftovers to `unprovenanced/`. Re-baseline owed (done 09-24 (4), card 6). Standing rule 7: a cache without a key is a silent substitution.

## Narrative
- 2026-09-23: Built the MULTICOMPO, wrote the round-trip deck before the long run, and caught the missing diffusion coefficients and the discarded output before they cost two hours of CPU. First smoke round trip agreed to 0.4 pcm. (by @assistant)
- 2026-09-23 (3): Ran the full 630 points and tested the full database: round trip worst 6.4 pcm, off-grid 27 pcm, both far below the physics uncertainties. Extracted β as a curve; a flat first result was treated as a defect because β must fall with burnup, which exposed the `GETVAL` index trap. OpenMC confirmed β at fresh fuel to 0.5 %. Added OpenMC branches at 0.35 and 0.15 g/cm³: at discharge the void shapes agree and only the magnitude differs (ratio 1.8–2.0×); at fresh fuel the shapes disagree. Found a second COMPO infeasible and carried the bracket as data, to be applied via `MAC: ADD` in A7. (by @assistant)
- 2026-09-24: Restructuring for a clean clone revealed the uncached-key draglib substitution live since 19 September, worth −87 pcm and invisible because everything kept working. Made the cache content-addressed, preserved the unprovenanced files rather than deleting them, and recorded that every DRAGON figure and the DRAGON/OpenMC bracket must be recomputed, not relabelled. (by @assistant)
- 2026-09-24 (3): [PAV] showed Unit 4 at 10.9 MWd/kgU on average, nothing near 20; the bracket and dollars table were re-scoped to roughly 5–15 MWd/kgU (consequences acted on in card 6). Burnup basis confirmed per tonne U in both codes. (by @assistant)
