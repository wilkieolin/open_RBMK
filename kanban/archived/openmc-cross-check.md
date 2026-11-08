---
id: 3
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, openmc]
---

# OpenMC cross-check of the RBMK cell

The first independent check of any RBMK physics in the project (2026-09-23). The same cell was rebuilt in OpenMC from the same number densities and dimensions, run in continuous energy on ENDF/B-VIII.1, and compared with DRAGON. The geometry and the positive, burnup-rising void coefficient were confirmed; the magnitude was not — OpenMC gave roughly twice DRAGON's void reactivity at discharge and 12× at fresh fuel — while a CANDU-6 control agreed to 1.3 %, localising the disagreement to the RBMK lattice. One real deck bug (free-gas hydrogen) was found.

**Sources:** PROGRESS header blockquote 2026-09-23; section "OpenMC cross-check — 2026-09-23"; "OpenMC status: WORKING" in "Validation risk"; CANDU-6 row of "Validated results". Key files: `openmc/rbmk_cell.py`, `volcheck.py`, `rates.py`, `deplete_void.py`, `compare_bu.py`, `candu_common.py`, `candu_cell.py`; `Dragon/data/rbmk_candu.x2m`, `rbmk_proc/CanduLib.c2m`, `rbmk_h2otest.x2m`, `rbmk_proc/RbmkLib.c2m`, `RbmkLibH.c2m`, `RbmkLibF.c2m`.

## Outcome
- Geometry confirmed: analytic fractions match DRAGON `MIXTURESVOL` to every printed digit (graphite 89.5938 vs 89.594 %, coolant 3.7721 vs 3.772 %, fuel 2.9009 vs 2.901 %, Zr 2.7292 vs 2.729 %, gas 1.0040 vs 1.004 %); all 18 rod clearances positive (1.4–2.7 mm); implied HM density 9.167 g/cm³.
- Full-void reactivity (dca 0.72 → 0.02), OpenMC vs DRAGON: 0 MWd/t +1030 ± 66 vs +82 (12.5×); 2000 +919 ± 81 vs +103 (9.0×); 5000 +852 ± 79 vs −10 (sign differs); 10000 +1473 ± 92 vs +303 (4.9×); 15000 +2650 ± 121 vs +985 (2.7×); **20000 +4007 ± 117 vs +1951 (2.1×)** — ~8 β vs ~4 β at the then-assumed β 0.0048.
- High-statistics fresh sweep: OpenMC k∞ = 1.319690 ± 0.000139; void +578 pcm at 51.4 %, +912 at 97.2 %, against DRAGON +264 / +222 with bound hydrogen.
- **Bug:** `RbmkLib.c2m` used bare `H1` (free gas); every bundled reference deck uses `H1_H2O`. `rbmk_h2otest.x2m`: free gas k∞ 1.312816, +226 / +82; bound 1.310172, +264 / +222. Fixed 2026-09-23 (`RbmkLib.c2m:44`); `RbmkLibH.c2m` retired, `RbmkLibF.c2m` kept do-not-use (see card 4).
- Eliminated by measurement: geometry/composition; VIII.0 vs VIII.1 (37 pcm on k∞); `GRMIN 18` (bit-identical); `USS:` options (< 0.5 pcm); `CTRA` (+76 pcm, real but small); free-gas H (+140 pcm, 17 % of the gap). SHEM-361 was untestable then (`USS:` would not converge).
- Running account at fresh fuel: +82 → +222 (bound H) → +299 (CTRA NONE) → OpenMC +912; 614 pcm, 74 % of the gap, unreached. "Not reachable from the deck" was qualified the same day: four discretisation/self-shielding knobs were untested (unsplit pellet, coarse tracking, Zr at infinite dilution, `ANIS 2`). Diagnosis deferred by decision until A8 showed the bracket mattered (trigger later met on 09-24 (4), card 6).
- Decomposition: the whole difference attributed to U-235 fission production under spectral hardening (DRAGON −0.200 pp, OpenMC +0.746 pp). **Retired 2026-09-25** by the four-factor split, which places it in resonance absorption (card 7).
- CANDU-6 control (`TCWU07.c2m`, shared compositions): k∞ nominal 1.124669 vs 1.125691, voided 1.145597 vs 1.146371, void **+1624 vs +1603 pcm (−22 pcm, −1.3 %)**.
- Caveats: depletion trajectories diverge (+268 pcm at 5000 MWd/t, −2084 at 20000; VIII.0 chain); neither code established as right; steam treated with liquid-water S(α,β) in both.
- OpenMC environment: venv `.venv-openmc`, `~/nucdata/endfb-viii.{0,1}-hdf5`, ~80 k particles/s on 20 threads, peak RSS 879 MB fresh (1.6 GB depleted).

## Narrative
- 2026-09-23: Got OpenMC running from an existing source build and rebuilt the cell from DRAGON's own inputs on the same evaluation so the comparison isolates method. Geometry matched to every digit and the void sign and trend held, but the magnitude was ~2× at discharge and 12.5× fresh, and the 5 MWd/kg dip did not appear at all. (by @assistant)
- 2026-09-23: Hunted the gap one variable at a time. Found the one real bug — free-gas `H1` coolant hydrogen — worth +140 pcm (17 % of the gap), fixed it in the single source of truth, and showed every other data/library option tested was small or bit-identical. Recognised that "not reachable from the deck" overstated the evidence since no discretisation or self-shielding knob had been tried, and that the highest-information test would be a 172-group spectrum and per-nuclide rate comparison. Deferred that by decision. (by @assistant)
- 2026-09-23: Ran a CANDU-6 control in both codes from one generated composition to answer the objection that the OpenMC model is wrong; it agreed to 22 pcm on void, so the RBMK disagreement is lattice-specific and DRAGON is the more likely source, though that is inference, not measurement. Explained why the quantity is fragile: the void coefficient is a few-hundred-pcm residual between ~3800 pcm terms. (by @assistant)
