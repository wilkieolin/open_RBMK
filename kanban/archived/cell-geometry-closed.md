---
id: 6
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, sourcing, openmc]
---

# Cell geometry pinned to primary sources, closed, and re-baselined

Between 2026-09-24 (2) and (4) every RBMK cell dimension was settled against primary sources: Dollezhal & Emelyanov (1980) corrected the carrier and clad and confirmed the 88 × 4 pressure tube, then eight further sources confirmed ring radii, ring phase, pellet hole, gas gap and burnup basis and refined the clad OD. The geometry was moved into one shared procedure and both codes were re-run on the pinned draglib. The re-baseline widened the DRAGON/OpenMC method gap and showed the bracket straddled prompt criticality at Unit 4's actual burnup, which moved the method gap ahead of A6.

**Sources:** PROGRESS header blockquotes 2026-09-24 (2), (3), (4); sections "Cell geometry pinned to a primary source — 2026-09-24 (2)", "Cell geometry closed — 2026-09-24 (3)", "Re-baseline on the closed geometry — 2026-09-24 (4)". Key files: `sources/README.md`, `Dragon/data/rbmk_cell_a3.x2m`, `rbmk_a5_void.x2m`, `rbmk_a5b_compo.x2m`, `rbmk_h2otest.x2m`, `rbmk_proc/RbmkGeo.c2m`, `openmc/rbmk_cell.py`, `openmc/volcheck.py`, `rbmk_a5b_sweep.don`, `openmc/a5b_interp_check.py`, `openmc/extract_a5btab.py`, `openmc/void_bracket.py`, `branch_results81*.json`.

## Outcome
- [D] (Dollezhal & Emelyanov, Atomizdat 1980, pre-1986): pressure tube **OD 88 × 4 confirmed** (Wikipedia 92 × 4 reading wrong); guardrail coolant band tightened 3.0–4.5 % → 3.4–4.0 %.
- Carrier **corrected**: solid Zr rod r 0–0.600, water r 0.600/0.625, central tube 15 × 1.25 (r 0.625/0.750), replacing a 13 mm hollow tube. Clad **corrected** to 13.5 × 0.9: `RADIUS 0.0000 0.1000 0.5750 0.5850 0.6750`.
- Fractions after [D]: coolant 3.7721 → 3.6527 % (−3.2 %), Zr 2.7292 → 2.9823 % (+9.3 %), gas 1.0040 → 0.8702 %; graphite and fuel unchanged.
- Closed 09-24 (3): ring radii 1.60 / 3.10 correct (⌀32 / ⌀62, [RU-A], [LEI05]); ring phase π/12 correct ([D] fig 5.1, topology read); 2 mm pellet hole real ([RU-A], [LEI05], [BIB]; mass check 115.3 kg with hole vs [PAV] 114.7 kg, 118.9 kg solid); gas gap a valid idealisation; burnup per t U, no trap; **clad OD 13.5 → 13.58** (r 0.6790), ID 11.7 unchanged. Coolant → 3.6037 %, Zr → 3.0313 %.
- `rbmk_cell_a3` on pinned draglib `cb1395ffbb65`: **k∞ = 1.304123**; DRAGON fractions 89.594 / 3.604 / 2.901 / 3.031 / 0.870 equal analytic. Lineage: 1.310172 → 1.308679 (library, −87) → 1.304717 (carrier and clad, −232) → 1.304123 (clad OD, −35). *Superseded 2026-09-26 by 1.313968 on SHEM-361 + Zr SS (card 7).*
- Unit 4 at the accident averaged **10.9 MWd/kgU**, not 20 ([PAV]). [TD722] p.64 gives the first measured void coefficient, 4–5 β at Leningrad (a core value, not comparable to k∞).
- Geometry moved to `rbmk_proc/RbmkGeo.c2m`, called by all 13 lattice decks; reproduces 1.304123 bit for bit.
- Re-baseline (09-24 (4)): `rbmk_h2otest` bound fresh full void **+62**; COMPO 630 points, 5 h 21 min wall, 108 MB; round trip worst **6.6 pcm**, off-grid **26.5 pcm** (now reproducible); β 0.006825 → 0.004671, essentially unchanged.
- DRAGON full-void worth fell 150–520 pcm (+222 → +62 fresh, +499 → +207 at 10, +2190 → +1672 at 20); OpenMC barely moved (+1030 → +901, +1473 → +1202, 4007 → 3757). The method gap widened, as predicted.
- Dollars: 10 MWd/kg **+0.39 $ vs +2.25 $**, 15 **+1.65 $ vs +4.60 $**; at 10.9 MWd/kgU ~+0.6 $ (DRAGON) vs ~+2.7 $ (OpenMC) — the bracket straddled prompt criticality. *Superseded by the converged library on 09-25/09-26 (card 7).*
- r = Δρ_OpenMC/Δρ_DRAGON runs 2.7–6.6 at 10–15 MWd/kg and goes negative at 5; the ~1.9 "collapse" was a 20 MWd/kg property. Recommendation: variant B should replace, not scale, DRAGON's void Δρ.
- OpenMC fresh: k∞ 1.316220 ± 0.000225 (+705 pcm vs DRAGON); Δρ +527 ± 19 at 0.35, +799 ± 19 at 0.02; β_eff 0.006739 ± 0.000166 vs 0.006825 (−1.3 %, 0.5σ).

## Narrative
- 2026-09-24 (2): Converted a DjVu scan of the chief designer's monograph to a searchable PDF and pinned three of four geometry questions. One confirmation (88 × 4), two corrections (carrier ~3× understated in metal; clad wall making the gap ~2.3× too thick). Measured ring radii off fig 5.1 (inner 17–18 mm) but deliberately did not substitute them, since a number off a scanned drawing would look like sourcing without being sourcing. Flagged the pellet hole as newly suspect. Applied to four decks plus OpenMC and noted the geometry was copy-pasted into at least 13 decks; recommended a shared `RbmkGeo.c2m` but did not do an untested refactor without a DRAGON build. Predicted that less coolant would widen the DRAGON/OpenMC gap. (by @assistant)
- 2026-09-24 (3): Eight new sources (one, IAEA-TECDOC-722/R, already on disk and never cited) closed the geometry. The restraint on ring radii was vindicated: the real inner value is 16.0 mm, not 17–18 — topology off a figure is reliable, dimensions are not. The per-assembly uranium mass, not the UO₂ mass range, decided the pellet hole. Re-ran k∞ on the pinned draglib and found the Unit 4 burnup distribution, which re-framed the bracket at 10–14 MWd/kgU. (by @assistant)
- 2026-09-24 (4): Extracted the geometry into `RbmkGeo.c2m` for all 13 decks and re-ran everything in both codes on the x86_64 box. DRAGON's void worth fell, OpenMC's did not, and at the burnups Unit 4 had the two codes disagreed on whether voiding average fuel is prompt critical. That met the deferred-diagnosis trigger without waiting for A8, so the method gap became the top physics priority ahead of A6, with the four untested DRAGON knobs as first candidates. Also planned burnup nodes at 7.5 and 12.5 for the next rebuild, and noted COMPO/OpenMC co-scheduling cost (5 h 21 min vs 81 min). (by @assistant)
