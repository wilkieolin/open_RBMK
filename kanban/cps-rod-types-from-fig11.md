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
- (added 2026-11-08) ПК and ЛАР built as РР-construction displacer rods (sourced, `sources/README.md` "Rod construction and types"); ЛАР without displacer as a B5 bracket; АР-channel fixed bottom displacer ([DYAT] §3.4) as a B5 bracket.
- (added 2026-11-08) Absorber lengths 6 m / УСП 3 m (Unit 4 start-up act) as an option, with the change shown to be nil at t = 0 and reported for the AZ-5 run.
- (added 2026-11-08) Depth bracket: [KARVK] Fig. 3 depths (`sources/derived/karpan_vk_fig3_012230.csv`) as an alternative 01:22:30 rod state for B5.
- The old map reproducible (an option, off = byte-identical decks), per the "new option leaves results unchanged" rule.
- Band-B deck regenerated; t = 0 dump; the (27) axial inversion redone, now also checked against `accidont_fig9_10_dkev_axial.csv` (`tools/a8_dkev_compare.py`); static AZ-5 ramp and a newton B4 run compared with the old ones (axial peak, Kv, peak power).

## Narrative
- 2026-11-08: Opened from the #33 input audit. ПК not yet identified (a top-entry type, not РР or АЗ); the type-to-device mapping is the open sourcing question. (by @assistant)
- 2026-11-08: The user retrieved the blocked sources (NUREG-1250 was already here as `ML071690245.pdf`); registered in `sources/README.md` "Rod construction and types". Results:
  - **Composition sourced:** NUREG-1250 Table 2.5 gives 139 РР, 12 ЛАР, 12 АР, 24 АЗ, 24 УСП. Fig. 11's 115 РР + 24 ПК = 139. INSAG-7 RU defines ПК-АЗ as the over-compensation group's mode, so **ПК = a 24-rod group of РР rods**.
  - **Types confirmed by a second map:** Karpan's VK Fig. 3 (01:22:30, cm, УСП/АР/ДКЭв marked; transcribed to `sources/derived/karpan_vk_fig3_012230.csv`) puts УСП, АР and ДКЭв on exactly Fig. 11's sites. His АР depths 139/158/20 cm match Dyatlov's DREG 1.4/1.6/0.2 m.
  - **Displacers:** every type but АР has one ([N1250], [D] PDF p. 38, INSAG-7 §2.2). Karpan's counts at 01:22:30 reproduce exactly from Fig. 11 + II-6 *only* with ЛАР and ПК as displacer rods: 11 rods effective for АЗ, and 164 water columns (108 РР + 23 ПК + 22 АЗ + 11 ЛАР). GRS-121's "24 without a displacer" is the lone dissent (bracket).
  - **New questions for the build:**
    - Unit 4's start-up act (Dyatlov pp. 80–84) recommends moving the АР displacers to the channel bottoms; that this was done by 1986 is unsourced (bracket).
    - The same act gives 6 m absorbers and 3 m УСП against the model's INSAG-7 p. 43 values of 5 m and 3.5 m. This changes nothing at t = 0 (deepest rod 2.64 m) and affects AZ-5 only after a rod passes 5 m.
    - The УСП displacer (NUREG Fig. 2.15) is out of the core at every 01:22:30 depth by [D]'s stroke geometry, so the model's water-filled УСП channel stands.
  - **Depth conflict:** at 9 top-entry rods Karpan has 13–80 cm (+3.6 m in all) where Fig. II-6 prints 0. Fig. 11 sides with Karpan at 3 of them and with II-6 at 5. II-6 stays nominal; Karpan becomes a bracket. Extra top absorber pushes flux down, so it does not help #33.
  - **Not useful here:** IBRAE ch. 2 and De Geer 2017 hold no per-channel or rod data. IBRAE confirms 1659 ТВС + 1 ДП + 1 empty channel ([PAV]).
  - **Also in the start-up act** (initial 1983 core, so only a check): АЗ worth 2.5 β; CPS voiding +0.1 β; a positive spike when 2АР was inserted 0–2 m. (by @assistant)
