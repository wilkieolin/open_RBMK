---
id: 44
status: done
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
- 2026-11-09: **Built and run.**
  - **Map:** `tools/retype_unit4_map.py` → `sources/derived/unit4_channel_map_fig11.csv`. Same rows and depths; `type` from Fig. 11 on all 211 rods, old type kept in `type_dollezhal`. Counts: RR 115, AZ 24, PK 24, USP 24, LAR 12, AR 12 (+ 12 DKEV, 4 KD, 1661 FUEL). The tool checks that Karpan's УСП / АР / ДКЭв sites are the same sites.
  - **Generator options** (`gen_rbmk_unit4.py`):
    - `U4_RODTYPE=fig11`: the new map. The stem gets `_rt<md5[:6] of the map>`.
    - `U4_LARDSP=0`: ЛАР without displacer, a B5 bracket. Stem `nl`.
    - `U4_ABSLEN=6`: 6 m absorber and 3 m УСП (start-up act). Stem `_L6`.
    - ПК and ЛАР are built as РР-construction displacer rods, giving 386 devices (was 389).
  - **Off path:** the old band-B deck and `rbmk_unit4_core_dev.don` regenerate byte-identical. The old newton B4 run, rerun today, gives a trace and shape byte-identical to the 2026-10-23 output.
  - **Not built: the АР-channel bottom displacer.** [DYAT] §3.4 says only "демонтировать вытеснители стержней АР, установив их в нижние части каналов". It gives no length or position, and a fixed in-core displacer would block the АР stroke. That leaves nothing to build without inventing geometry; the reasoning is in `sources/README.md`.
  - **(27) axial inversion redone** (`tools/a8_axinvert.py`, Fig. II-9 target):
    - Old map refit reproduces rms 0.0194, k 1.027709.
    - Re-typing on the old fit alone gives rms 0.0266.
    - Refitted, rms 0.0192, k 1.027323, 65 solves → `insag7_fig_II9_t0_axburn_fit_f11.txt`. The effective profile barely moves (bottom bundle g 0.468 → 0.466).
    - Brackets: ЛАР without displacer (`…_fit_f11nl.txt`) rms 0.0192, k 1.025156; Karpan depths (`…_fit_f11kv.txt`) rms 0.0193, k 1.027234.
    - Channel powers → `a8_fit_pchan_f11.txt`. New/old normalised ratio is 0.762–1.298 (rms 0.104); Kr 1.618 → 1.663.
  - **ДКЭв check** (`tools/a8_dkev_compare.py`, accidont Figs 9/10):
    - axial rms over the 12 strings: 0.054 old → 0.058 new;
    - string-level r: 0.126 → 0.001.
    - Fig. 8 radial: r 0.764 → 0.766 (identity), 0.860 → 0.866 (rot90).
    - So the correct rod types do **not** fix the radial or string-level mismatch. Burnup placement (#36) remains the likely cause.
  - **Static AZ-5 ramp** (`tools/a8_ramp.py`, `A8_USP=0`), ρ in pcm:

    | advance (cm) | 10 | 25 | 40 | 80 | 160 | 240 | 280 |
    |---|---|---|---|---|---|---|---|
    | old (= PROGRESS (35)) | −86.1 | −83.9 | −17.9 | +302.4 | +511.0 | +379.0 | +258.1 |
    | fig11 | −84.0 | −81.2 | −15.1 | +307.4 | +521.1 | +396.3 | +281.4 |
    | fig11, ЛАР no displacer | −82.7 | −91.3 | −43.8 | +229.4 | +407.4 | +280.9 | +166.9 |

    Re-typing moves the positive scram by only +10 pcm. The ЛАР-displacer question is worth −114 pcm at the peak (−22 %), the largest rod-model bracket so far.
  - **Newton B4** (new stem `rbmk_unit4_a7_acco668_pc9f6a01_dev_ax980df8_kin700v40g12shvdfr025fi60cc01dt001_vB65c86e_cB4af83e_rt9f0a8f`, 700 × 0.01 s), old → new:

    | quantity | old | new |
    |---|---|---|
    | peak P/P0 | 230.2 at 5.24 s | 244.5 at 5.15 s (+6 %) |
    | P > 10 P0 from | 3.43 s | 3.38 s |
    | E(4 s) | 3.19 GJ | 3.42 GJ |
    | E(6 s) | 52.1 GJ | 55.7 GJ (+7 %) |
    | Kv at peak | 3.55 | 3.61 |
    | Kr at peak | 1.44 | 1.47 |
    | Kz at peak | 2.49 | 2.45 |
    | max Eadia (6 s) | 200 cal/g | 220 cal/g |
    | m(Eadia > 100) | 53.0 | 56.6 |
    | m(Eadia > 160) | 14.4 | 20.1 |

    - The axial peak stays in **bundle 4** in both runs, so re-typing does not lift it (#33).
    - The new run stopped at **6.00 s**: T-FUEL left the COMPO axis (2000.3 K > 2000 K, `XS.bracket`), as in card #31. A full 7 s run needs `B4_CLAMP=1` or that card.
  - **Still open:**
    - an AZ-5 run with `U4_ABSLEN=6` (no effect at t = 0, since the deepest rod is at 2.64 m);
    - the Karpan-depth AZ-5 ramp (`a8_ramp` takes depths from the map, so it needs a depth override).
  - **New cards from the sourcing:** #45 (accidont Fig. 7 measured channel flows) and #46 (1983 start-up act CPS check). (by @assistant)
- 2026-11-09 (later): **Open items closed.**
  - **Karpan-depth ramp.** `tools/a8_ramp.py` takes a new `A8_DEPTH=<file>` (base depths in `U4_RODDEPTH` format; unset = unchanged). Run with `sources/derived/karpan_vk_fig3_roddepth.txt` and the `…_fit_f11kv.txt` refit; ρ in pcm:

    | advance (cm) | 10 | 25 | 40 | 80 | 160 | 240 | 280 |
    |---|---|---|---|---|---|---|---|
    | fig11 nominal | −84.0 | −81.2 | −15.1 | +307.4 | +521.1 | +396.3 | +281.4 |
    | Karpan depths | −86.3 | −85.1 | −21.0 | +290.2 | +484.9 | +354.3 | +236.9 |

    Karpan's extra 3.6 m of top absorber costs −36 pcm at the peak (−7 %).
  - **`U4_ABSLEN=6` static ramp.** k is identical to seven significant figures with the nominal at 0–280 cm, and also at 400 and 500 cm. The device input does differ: MAXPOS z 0–600 against 0–500, and DEVGET / MOVCHK / NEWMDV place the absorber at [DELH, DELH + L], read in the Fortran. The difference is invisible because the top is flux-starved: at 500 cm the 164 rods that started at 0 cm cover the top 2.5 m. The bundle shape (`U4_PBUND=1`) puts 0.3–0.6 % of the mean power in the top 1.5 m, which is where the extra metre would sit. The first real difference is at 600 cm, where every rod exposes the core top: −7292 against −4536 pcm. At 40 cm/s that is about 14 s after AZ-5.
  - **`U4_ABSLEN=6` newton B4**, stem `…_rt9f0a8f_L6`, `B4_CLAMP=1`, against the fig11 nominal also clamped:
    - the t = 0 dumps (`fmap0.asc`) are byte-identical;
    - the traces first differ at 5.61 s, in the 7th significant figure;
    - at 7.00 s, P/P0 37.2697 against 37.2696; E 66.757 GJ in both; shape rows identical.

    The 1983-act absorber length is therefore **nil within the 7 s window**. It is not a B5 dimension for the excursion.
  - **Fig. 11 deck to 7 s** (clamped): peak 244.5 P0 at 5.15 s (unchanged; the unclamped trace is byte-identical through 5.59 s). E(7 s) 66.76 GJ. TFmax 2025 K. At 7 s: Kv 4.02, max Eadia 264 cal/g, m(Eadia > 100) 68.9, m(Eadia > 160) 35.2, m(Eadia > 240) 3.0. The axial peak is still bundle 4.
  - **АР-channel bottom displacer:** not built (see the entry above, and `sources/README.md`). It stays unbuildable until a source gives its length and position.
  - **Acceptance criteria all met** except that bracket, which is recorded as unbuildable rather than assumed. Card closed. (by @assistant)
