---
id: 33
status: todo
priority: Normal
blocked_by: []
tags: [tier-a, tier-b, neutronics]
---

# Axial power peak in the excursion sits ~0.9 m above the fuel bottom against INSAG's ~2 m

During the excursion the model's hottest plane is 0.9 m above the fuel bottom (both TH models); INSAG-7
p. 66 puts the shift "at a height of about 2 m". The 4–7 s shape comparison of PROGRESS (27) already had
the flux ~35 cm too deep. The axial location sets where the void feedback and the fuel damage occur.

**Sources:** PROGRESS (27), (48); INSAG-7 Figs. II-8/II-9.

## Acceptance Criteria
- The offset decomposed (initial axial burnup inversion, rod insertion depth/speed, CPS worth, TH feedback), each by a run or a measured sensitivity.
- Any correction sourced, not fitted to the post-AZ-5 record.

## Narrative
- 2026-11-08: Opened from PROGRESS (48). (by @assistant)
- 2026-11-08: Input audit against the user's source survey (claude.ai doc "Chernobyl Unit 4 pre-accident core state: sources and data"); sources registered in `sources/README.md` § "Core state at 01:22:30". Three new data sets bear on this card. (by @assistant)
  1. **Measured axial field at 01:22:30.** accidont Figs 9–10 [ACC] are the SKALA ДКЭв readings: 12 strings × 7 sections, labelled with plant coordinates that are exactly the 12 DKEV cells of `unit4_channel_map.csv`. Digitised by `tools/digitise_accidont_dkev.py` → `sources/derived/accidont_fig9_10_dkev_axial.csv` (84 values, ±5; 63 ring markers, 16 curve traces, 5 coincident markers read from zooms; overlay checked). INSAG-7 Fig. II-8 is the same 12 shapes, unlabelled and laid out 2-3-2-3-2 like the cells.
  2. **Model t = 0 against it** (`tools/a8_dkev_compare.py <dumpdir>`; model = mean BUND-PW of the face-neighbour fuel channels per 1 m section), band-B deck `…_vB65c86e_cB4af83e`: the 12-string mean shape is **reproduced** — measured 1.01 1.43 1.14 0.97 0.96 0.92 0.57 vs model 0.99 1.40 1.21 0.94 0.90 0.90 0.66 at H 0.5…6.5 m below the top, both peaking at 1.5 m, rms 0.054. So the Fig. II-9 t = 0 curve used for the axial-burnup inversion (PROGRESS (27)) agrees with the measured mean, and the 0.9 m vs 2 m offset is **not** a mismatch of the mean initial shape. Per string the rms is 0.05–0.24; the model's bottom section is too high in most strings (mean 0.66 vs 0.57), worst at 6047 (model 0.66 / measured 0.33), 3057 (0.76 / 0.44), 4047 (0.84 / 0.45) — each beside partly inserted УСП rods (64-33, 64-43; 34-53; 44-53, 34-43) — while 5017, with no УСП inserted near it, reads high at the bottom (0.77 vs 0.51). String levels (radial, 12 points) do not correlate (r 0.13).
  3. **Rod types are wrong in the model.** accidont Fig. 11 gives Unit 4's own rod types (cell colours: 115 РР, 24 АЗ, 24 ПК, 24 УСП, 12 АР, 12 ЛАР) → `sources/derived/accidont_fig11_cps.csv` (`tools/digitise_accidont_fig11.py`), cross-checked against a transcription of Karpan's maps [SKSIM] (same 24 УСП sites; its 211 depths equal our Fig. II-6 digitisation). None of the map's 21 УСП (from Leningrad-2's Fig. 2.3) is an УСП. At 01:22:30, **716 cm of bottom-entry УСП absorber is modelled as top-entry rods** (64-33, 64-43, 44-53, 44-63, 34-13, 34-43, 34-53) and 350 cm of top-entry rods as УСП from below (46-21, 46-61, 36-41). The net error puts absorber at the top that is really at the bottom — the direction that pushes the model's flux, and the AZ-5 excursion, downward. Also 3 displacer-carrying rods too many are driven at AZ-5 and the displacer sites are misplaced. Correction is card #44; the inversion (27) must be redone after it, since it absorbed the wrong rods into the effective axial burnup.
  4. [AECL88] quotes Dollezhal: axial burnup maximum 22 GWd/t at about 5 m above the core bottom (upper-heavy). The (27) inversion's effective profile is "slightly heavier in the lower half" — a tension to re-check after #44.
  Next: #44 (re-type the rods, regenerate the band-B deck, redo the (27) inversion against the DKEV data as well as Fig. II-9), then rerun newton and compare the excursion's axial peak; then the remaining decomposition items (rod speed, CPS worth, TH feedback).
- 2026-11-09: Item 3 tested (#44): the Fig. 11 rod types do **not** lift the axial peak.
  - The (27) refit with the new types gives nearly the same effective profile (bottom bundle 0.468 → 0.466; rms 0.0192).
  - The newton B4 excursion peak stays in bundle 4, with Kz at peak 2.49 → 2.45.
  - ДКЭв axial rms gets slightly worse (0.054 → 0.058).
  - Hypothesis 3 is retracted as an explanation of the depth. The 716 cm УСП mis-typing is real, but the refit absorbs it. (by @assistant)
