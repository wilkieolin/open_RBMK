---
id: 44
status: todo
priority: High
blocked_by: []
tags: [tier-a, tier-b, neutronics, rods, sourcing]
---

# Re-type the CPS rods from accidont Fig. 11 (УСП, ЛАР, ПК) and rebuild the band

`sources/derived/unit4_channel_map.csv` carries Leningrad-2's rod types (Dollezhal Fig. 2.3) plus assumed
types on the 32 extra sites. accidont Fig. 11 [ACC] gives Unit 4's own types at 01:22:30 (115 РР, 24 АЗ,
24 ПК, 24 УСП, 12 АР, 12 ЛАР), and none of the map's 21 УСП sites is an УСП there. At 01:22:30 716 cm of
bottom-entry УСП absorber is modelled as top-entry rods and 350 cm of top-entry rods as УСП. Found in the
#33 audit; likely part of #33's too-deep peak and of the per-string bottom deficits in the DKEV data.

**Sources:** `sources/derived/accidont_fig11_cps.csv` (`tools/digitise_accidont_fig11.py`); [SKSIM] cross-check;
INSAG-7 p. 43 (24 АЗ, 24 УСП for second-stage units); card #33 narrative 2026-11-08; PROGRESS (22)–(29) for the
device model (`ROD_DSP`, `ROD_ABS`, `ROD_BOT`, AZ-5 groups) in `decks/Donjon/data/gen_rbmk_unit4.py`.

## Acceptance Criteria
- The map's `type` column set from Fig. 11 for all 211 rods (with `type_source`), depths unchanged (they already agree with Fig. II-6 and Fig. 11).
- Device classes for the new types sourced or labelled ASSUMPTION and bracketed: whether ЛАР and ПК carry displacers, which groups AZ-5 drives in 1986 (УСП not driven, PROGRESS (29)), rod speeds.
- The old map reproducible (an option, off = byte-identical decks), per the "new option leaves results unchanged" rule.
- Band-B deck regenerated; t = 0 dump; the (27) axial inversion redone, now also checked against `accidont_fig9_10_dkev_axial.csv` (`tools/a8_dkev_compare.py`); static AZ-5 ramp and a newton B4 run compared with the old ones (axial peak, Kv, peak power).

## Narrative
- 2026-11-08: Opened from the #33 input audit. ПК not yet identified (a top-entry type, not РР or АЗ); the type-to-device mapping is the open sourcing question. (by @assistant)
