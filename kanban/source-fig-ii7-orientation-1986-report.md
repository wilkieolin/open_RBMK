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
