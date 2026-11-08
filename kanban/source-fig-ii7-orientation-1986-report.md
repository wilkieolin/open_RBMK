---
id: 28
status: todo
priority: High
blocked_by: []
tags: [sourcing, tier-b, neutronics]
---

# Source the orientation of INSAG-7 Fig. II-7 (Ref. [28]; the 1986 USSR report)

The model's radial field matches Fig. II-7 rotated 90° (r 0.885) but not as printed (0.60), and the two
orientations give very different excursions (the "as printed" tilt: Kv ~5, 254×). No source states the
figure's orientation. Candidates: Ref. [28] itself (VNIIAES / Kurchatov full-scale RBMK-1000 dynamics models),
and INSAG-7's Ref. [1], *The Accident at the Chernobyl AES and Its Consequences* (USSR State Committee on the
Utilization of Atomic Energy, IAEA experts' meeting, Vienna, 25–29 August 1986, Parts 1 and 2) — the user has
a hard copy. The same report may also carry radial/axial distributions, the rod pattern and recorded
parameter plots that independently check INSAG-7 and DREG.

**Sources:** PROGRESS (49); `tools/digitise_fig_II7.py`; `tools/build_unit4_map.py` (Fig. II-6 registration).

## Acceptance Criteria
- Pages of the 1986 report with core plan views identified (from the user's copy: scans or photographs).
- The report registered in `sources/README.md` with page references; any core map digitised and registered to the lattice as Fig. II-6 was.
- The orientation of Fig. II-7 (or an equivalent map) decided from a source, or stated as unresolvable.
- Other figures that bear on the model (power distributions, rod pattern, parameter records) listed with pages.

## Narrative
- 2026-11-08: Opened. The user reports a hard copy of the 1986 report; none of its figures have been sourced so far (INSAG-7's Ref. [1]). (by @assistant)
- 2026-11-08: A plant-labelled measured radial field exists: accidont Fig. 8 [ACC], the ДКЭр readings at 01:22:30 on squares labelled with plant X/Y → `sources/derived/accidont_fig8_dker_radial.csv` (126 values, by eye). Our map's plant labels are confirmed by Fig. 11 (12/12 ДКЭв cells and all УСП depths at asymmetric sites, e.g. 44-63 1.9 m, 34-13 1.8 m, land on the map's sites). Correlations under the 8 square symmetries (`tools/a8_fig8_orient.py [dumpdir]`, squares centred on the labels; inner = squares with N ≥ 100): (by @assistant)
  - **Fig. II-7 (as digitised in (49)) vs Fig. 8:** identity r 0.821 (inner 0.40), mirror-Y 0.821 (0.48), rot90 0.739 (0.55), others 0.70–0.74. Weakly favours II-7 **as printed** being in plant orientation; not decisive (II-7 is read to 10 % bands).
  - **Model band-B t = 0 channel power vs Fig. 8:** identity is the *worst* (r 0.764, inner 0.40); antitranspose 0.866 (0.68), rot90 0.860 (0.50), rot180 0.841 (0.58). So the (49) result "model matches II-7 rotated 90°" more likely says the **model's** radial field is mis-arranged (unsourced burnup placement #36; wrong rod types #44) than that II-7 is rotated. This bears on #27: the "as printed" tilt may be the correct one.
  - Still open: the 1986 report's maps (user's copy) would settle it; Fig. 8 is uncalibrated detector readings, so it constrains shape, not level.
