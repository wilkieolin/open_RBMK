# Design sources for the RBMK-1000 cell

The tags are the ones cited in `decks/Dragon/data/rbmk_cell_a3.x2m`, `openmc/rbmk_cell.py`,
`openmc/volcheck.py` and `PROGRESS.md`. Page numbers are **PDF pages** unless stated.

The files themselves are not committed (`.gitignore`). They are third-party and some are
copyrighted. Each entry says where to get it again.

| Tag | Citation | File | Where to get it |
|---|---|---|---|
| **[D]** | Доллежаль Н.А., Емельянов И.Я., *Канальный ядерный энергетический реактор*. Атомиздат, Москва, 1980. Chief designer's monograph, pre-1986. | `Dollezhal-Emelyanov-…-1980_1.pdf` | DjVu scan, converted with OCR layer re-injected |
| **[TD722]** | IAEA-TECDOC-722/R, *Оценка безопасности проектных решений … третьего блока Смоленской АЭС с реактором РБМК*. IAEA, Vienna, 1995 (NIKIET translation). | `TD722_IAEA-TECDOC-722-R_Smolensk3_1995.pdf` | INIS XA0054406 |
| **[LEI05]** | Poškas P. et al., *Investigations of possibilities to dispose of spent nuclear fuel in Lithuania: a model case*, Vol. 2. RATA / LEI / SKB, 2005. Describes RBMK-1500 fuel. | `LEI05_Poskas_2005_SNF_disposal_Lithuania_vol2.pdf` | https://www.osti.gov/etdeweb/servlets/purl/20710056 (LT0600033) |
| **[BIB]** | Bibilashvili Yu.K. et al. (VNIINM Bochvar; NIIAR), *Status and development of RBMK fuel rods and reactor materials*. IAEA meeting paper, ~1998. | `BIB_Bibilashvili_RBMK_fuel_rods_status.pdf` | https://www.osti.gov/etdeweb/servlets/purl/352053 (XA9846756) |
| **[CAST]** | CAST project, D5.3, *Report on graphite categories in the RBMK reactor*. EU FP7 grant 604779, 2016. | `CAST_2016_D5.3_RBMK_graphite_categories.pdf` | https://igdtp.eu/wp-content/uploads/2017/10/CAST-2016-03-D5.3-ReportOnGraphiteCategoriesInTheRBMKreactor.pdf |
| **[PAV]** | Pavlovych V.M., *Nuclear fuel in the destroyed 4th unit of Chernobyl NPP*. In KURRI-KR-79, Kyoto University Research Reactor Institute, 2002. | `PAV_Pavlovych_KURRI-KR-79_fuel_in_destroyed_unit4.pdf` | https://www.rri.kyoto-u.ac.jp/NSRG/reports/kr79/kr79pdf/Pavlovych.pdf |
| **[USP]** | Ušpuras E. et al., *State of the art of the Ignalina RBMK-1500 safety*. Sci. Technol. Nucl. Install. 2010, 102078. | `USP_Uspuras_2010_Ignalina_RBMK1500_safety_STNI.pdf` | doi:10.1155/2010/102078 (open access; the publisher blocks scripted download) |
| **[RU-A]** | «Реактор Большой Мощности Канальный (РБМК)», fuel-assembly page. Anonymous educational site describing RBMK-1000 and quoting drawing tolerances. | `RU-A_dvoika_net_Reactor_assembly.htm` | http://dvoika.net/Reactor/assembly.htm (saved 2026-09-24) |
| **[RU-B]** | «Конструкция реактора РБМК-1000». Reference text mirrored on wdcb.ru and reactors.narod.ru. Its burnup figures match [D] p.95, so it is probably derived from [D]. Treat it as secondary. | `RU-B_wdcb_ru_rbmk4.html` | http://www.wdcb.ru/mining/sprav/document/rbmk/rbmk4.html (cp1251), https://reactors.narod.ru/rbmk/03_rbmk.htm |
| **[ALX98]** | Alexeev N., Behrens D., Davydova G., Donderer R., von Ehrenstein D., Krayushkin A., Meyer S., Schumacher O., *The Monte Carlo codes MCNP and MCU for RBMK criticality calculations*. Nucl. Eng. Des. **183** (1998) 287–302. | `ALX98_Alexeev_1998_NED183_MCNP_MCU_RBMK_criticality.pdf` | doi:10.1016/S0029-5493(98)00163-0 (paywalled; user-supplied) |
| **[PAR07]** | Parisi C., D'Auria F., *RBMK fuel channel blockage analysis by MCNP5, DRAGON and RELAP5-3D codes*. Proc. Int. Conf. Nuclear Energy for New Europe 2007, Portorož, paper 105. | `PAR07_Parisi_DAuria_2007_RBMK_FC_blockage_MCNP5_DRAGON.pdf` | user-supplied |
| **[BEH96]** | Behrens D., Meyer S., von Ehrenstein D., Donderer R., Schumacher O., Davydova G., Krayushkin A., *Validation of MCNP for RBMK criticality calculations*. Nucl. Technol. **114**(1) (1996) 1–11. | `BEH96_Behrens_1996_NuclTechnol114_Validation_MCNP_RBMK.pdf` | doi:10.13182/NT96-A35219 (user-supplied) |
| **[INSAG7]** | INSAG, *The Chernobyl Accident: Updating of INSAG-1*. Safety Series No. 75-INSAG-7, IAEA, Vienna, 1992. | `INSAG7_IAEA_1992_Chernobyl_update.pdf` | https://www-pub.iaea.org/MTCD/publications/PDF/Pub913e_web.pdf |
| **[ZJ02]** | Zemulis G., Jasiulevicius A., *Development of thermal hydraulic models for main circulation circuit of RBMK-1500 reactor using APROS and CATHARE 2 codes*. Kaunas Univ. Technol., FR0200406, ~2001. RBMK-1500 loop geometry, given as approximate values. | `FR0200406_osti20241670.pdf` | https://www.osti.gov/etdeweb/servlets/purl/20241670 |
| [W] | Wikipedia, *RBMK*, fetched 2026-09-22. Superseded for every cell dimension. | — | — |

## What each source was used for

| Quantity | Value in the deck | Sources, quoted |
|---|---|---|
| Pressure tube | OD 88, wall 4 | [D] p.54 «наружным диаметром 88 и толщиной стенки 4 мм»; [RU-B] «трубы d=88х4» |
| Central tube / carrier | 15 × 1.25 tube, ⌀12 solid rod | [D] p.11; [LEI05] p.8 "15 mm diameter tube with a 1.25 mm wall" |
| Rod circles | ⌀32 (6 rods), ⌀62 (12 rods) | [RU-A] «6 шт. по окружности диаметром 32 мм и 12 штук — диаметром 62 мм»; [LEI05] p.8 "inner circle, with a diameter of 3.2 cm … outer circle with a diameter of 6.2 cm" |
| Ring phase | outer ring offset π/12 | [D] p.96, fig 5.1 section Б-Б. This is a topology read (inner rods on the axes, outer rods straddling them), not a measurement. |
| Clad | OD 13.58, ID 11.7 | [RU-A] «наружный диаметр − 13,58 +0,05/−0,07 мм; внутренний диаметр − 11,7 +0,1 мм»; [LEI05] Table 1: 13.6 / 11.7; [D] p.11: 13.5 × 0.9 (ID 11.7) |
| Clad-to-wall gap (check) | 2.21 mm computed | [TD722] p.107 «номинальный зазор между канальной трубой и оболочками, равный 2,2 мм» |
| Pellet | ⌀11.5, 2 mm hole | [D] p.11 «таблетками диаметром 11,5 мм»; [RU-A] «осевое отверстие диаметром 2 мм»; [LEI05] Table 1: 11.52 / 2.0; [BIB] p.7 "use of fuel pellets with central holes" (RBMK-1000 design features) |
| U per assembly (check) | 115.3 kg computed | [PAV] p.1: 0.1147 t U per assembly, 1659 assemblies; [D] p.97: active length 6920–6954 mm, 125–135 kg UO₂ per cassette |
| Graphite rings, gas gap | 1.5 mm He at the tube | [CAST] p.11: 20 mm split rings, alternately tight on the tube (1.5 mm to the block) or on the block (1.3 mm to the tube); [TD722] p.76: total annular clearance 3 mm; [USP]: 2.7–3 mm initial |
| Graphite block | 250 × 250, bore 114, 1.65 g/cm³ | [D] p.11; [RU-B]; [CAST] p.11 |

## Not geometry, recorded because it matters

- **Unit 4 burnup at the accident** [PAV] Table 1: average **10.9 MWd/kgU**. 721 of 1659
  assemblies were at 13.7 and 172 were at 1.2. It was still mostly the first core.
- **Design discharge burnup.** [D] p.95 gives 19.5–24.4 GWd/t **UO₂**, which is 22–28 GWd/tU.
  [BIB] Table 1 gives an RBMK-1000 figure of ~26 000 MWd/tU.
- **Measured void coefficient** [TD722] p.64: at Leningrad, 1.8 % enrichment, approaching
  equilibrium burnup, the steam void coefficient was 4–5 β. That is a core value with
  additional absorbers present, so it is not comparable to a k∞ branch.

## Method verification: what [ALX98] and [PAR07] provide

**[ALX98] — the Kurchatov critical experiments are NOT specified here.**
- The paper describes the RRC-KI critical facility (p.6): 18 × 18 graphite columns of
  25 × 25 × 410 cm, aluminium channel tubes, half-height fuel bundles, 32 cm top and bottom
  reflector slices.
- It lists seven configurations (Table 1) and plots measured k_eff and void effects (Figs 4, 7)
  without tabulating them.
- Full specifications are in Behrens, Donderer, von Ehrenstein, *RBMK void reactivity effects,
  final report* (Univ. Bremen, 1994); Kuzmin, *Some experimental data obtained in the RBMK
  critical test facility* (RRC-KI, 1993); and Behrens, Meyer, von Ehrenstein, *Validation of
  MCNP for RBMK criticality calculations*, Nucl. Technol. **114** (1996) 1–11.
- Crucially, p.8: the graphite's B/Cd impurity content is unknown and worth **≈ 1 % in k_eff**.
  The authors tuned it separately for each code/library, and state that this *"keeps the
  critical facility experiments from being utilized as a benchmark."* Relative (voided −
  watered) effects are less affected than absolute k.

**[ALX98] — a fully specified single-cell code benchmark (RBMK Safety Review Project 1994):**
- Table 3 (dimensions) and Table 4 (number densities) define a cold, fresh, 2 %-enriched
  infinite-lattice cell, with zircaloy and aluminium tube variants.
- Figs 8–9 give k∞ watered / voided and void Δk from MCNP4A (four libraries), MCU-3, MONK-5W,
  WIMS-D, WIMS-E and APOLLO-2.
- Transcribed once in `openmc/srp94_common.py` (the `PUBLISHED` list, read off the plots to
  ±0.001 in k); the DRAGON decks `rbmk_srp94_*.x2m` are generated from it.
- Headline: MCNP/ENDF-B-VI and MCU agree on the Zr-tube void Δk within 0.05 % (4.80–4.85 %),
  while the deterministic codes sit 12–18 % lower (Al tube).

**[PAR07] — an independent DRAGON-vs-MCNP result on an RBMK cell** (300 K, NIKIET data):

| | MCNP4C | DRAGON, 172 groups |
|---|---|---|
| void Δk | 0.04924 | 0.03883 (**−21 %**) |

DRAGON is the collision-probability solver (EXCELL) on the IAEA WLUP 172-group library; the
69-group library gives −32 %. It uses a different library from ours, but shows the same
deficit, and the same dependence on group structure.

**[BEH96] — the critical-facility measurements, tabulated.** This is the source [ALX98] defers to.
- **Table I, measured k_eff and void effects for 11 RRC-KI critical assemblies** (1, 1a, 2, 3,
  3a, 4–9). Examples:
  - assembly 1: 18 fuel channels, 2 %, watered, k_eff 1.0026, void effect −3.1 % (fuel
    channels voided);
  - 5: +0.001; 6: −0.5 (fuel) / −1.1 (additional absorbers); 7: −1.5; 8: −0.28 (control rod
    simulators); 9 (1.8 %): −1.4.
  - The maximum experimental error on k_eff is 0.3 % (their ref. 7).
- **Facility** (p.3): 18 × 18 graphite blocks of 25 × 25 × 410 cm; aluminium-alloy channel
  tubes, 8.8 / 8.0 cm diameter; pellets ⌀1.152 cm in a 346 cm column with 32 cm axial graphite
  reflector each end; 0.5 mm Cd side layer; graphite taken as 1700 kg/m³. Loading maps are
  figures only (Fig. 1).
- **Impurities** (p.6): only B-10 and Cd-113 matter. B-10 atom fraction 8.79e-8 to 6.54e-7;
  Cd-113 < 3.86e-8. Diffusion-length measurements narrow this to 20–60 % of maximum. Four
  impurity sets are defined (maximum / medium / minimum / pure). The void effect is reported to
  be less impurity-sensitive than k_eff.
- **Smolensk-3, cold zero-power start-up** (p.6): four measured core states (two critical, two
  subcritical at 1.25 % and 2.84 %), with a full initial-loading description. That's a
  whole-core reference for later.
- **Caveat for the method gap:** these are small, leakage-dominated, cold assemblies with
  *negative* measured void effects. Comparing against them needs a full 3-D model of the
  facility in each code, not a cell k∞.


## Control and protection system (CPS / СУЗ) rods — for A6 (`A6_CPS_PLAN.md`)

**[D] p. 12, the 1980 design description:**
- 179 CPS channels on a 700 mm square lattice, rotated 45° to the fuel lattice.
- CPS channel: same Zr alloy as the fuel channels, ⌀88 mm, 3 mm wall, graphite rings outside.
- Absorber link: B₄C bushings 65 × 7.5 mm, 984 mm per link, sealed in the annulus between
  Al-alloy tubes 70 × 2 and 50 × 2.
- RR / AZ rods: 5 links; the total length is OCR-garbled as "…120 mm", most likely 5120.
  USP: 3 links, 3050 mm.
- Displacer: 5 hinged links, 5000 mm in total. Each link is an Al-alloy tube 74 × 2.5 mm, sealed;
  one is hollow, the rest are graphite-filled. AR rods have no displacer.
- Coolant: a separate circuit, water top-down at 40–60 °C. The channel is water-filled whatever
  the rod position.

**[INSAG7]:**
- §2.2 (pdf p. 14): control and safety rods enter from above, except 24 shortened rods from
  below. Every rod except the 12 AR has a graphite displacer on a 1.25 m water-filled "telescope".
  Fully withdrawn, the displacer sits centrally in the core with 1.25 m of water at either end.
  So the graphite is 4.5 m, which resolves [D]'s "5 links, one hollow".
- p. 43: history of the design. Draft 212 rods at 7 m; technical design 179 rods; final design
  179 rods with 5 m absorbers, except 21 shortened rods at 3.5 m. EPS rods: 21 in first-stage
  units, 24 in second-stage. Second-stage units have **211 rods** with no design change.
- p. 103: the RCPS has 211 movable solid absorber rods in channels cooled by an independent
  water circuit; EPS insertion speed 0.4 m/s; 24 shortened rods from below.
- Fig. II-6 (p. 119): plan of the core with the **insertion depth (cm) of every RCPS rod at
  01:22:30**. The text layer is OCR-noisy, so digitise from the image. It is A8's initial rod
  state and A6's site map.

**[TD722] §3.1 item 12:** B₄C runs at ≈ 350 °C; the Al cladding is held at 40–80 °C. Its "7 kg of
B₄C per section" is the redesigned post-1986 Smolensk-3 rod. On the 1980 geometry that mass would
imply > 5 g/cm³, twice B₄C's theoretical density, so it does **not** set the 1986 density.

**A6.1 search, 2026-09-26** (transcribed into `openmc/cps_common.py`):
- **Al alloy — closed.** An RBMK operator training text ([SF] below, p. 10) says each absorber link is
  "internal (50×2 mm) and external (70×2 mm) tubes of aluminium alloy **САВ-1**". [OST] gives САВ-1:
  Si 0.7–1.2, Mg 0.45–0.9 (the page prints "0.045–0.9"; either reading moves Mg by < 0.5 wt%, σₐ
  0.06 b), Fe ≤ 0.2, B ≤ 1.2 ppm, Cd ≤ 1 ppm, Al the rest. Modelled at the range midpoints, 2.70 g/cm³;
  the trace B and Cd are ≤ 1 % of the tubes' own absorption and are omitted. [SF] describes the
  post-1986 rod (6772 mm absorber), so it is taken for the tube material only.
- **Rod count and lattice — closed.** [INSAG7] Fig. II-6, digitised by `tools/digitise_fig_II6.py`
  into `sources/derived/insag7_fig_II6_012230.csv`: 211 rods on a 45°-rotated lattice (2-cell rows,
  4-cell spacing in a row; nearest sites 707 mm apart, [D]'s "700 mm"), plus 12 empty lattice sites in a
  symmetric pattern (consistent with [D] p. 12's 12 in-core monitoring channels; the figure does not
  label them). 47 rods are partly inserted, 43.5 m in total. A reactor-kinetics textbook
  ([LEG] below) gives the fuel : CPS channel ratio as 7 : 1, which the rotated lattice reproduces.
- **Rod types — still open.** Fig. II-6 gives depths, not types. [LEG] Fig. 6.7 is a type cartogram
  (RR, AZ, USP, AR1–3, LAR) of a generic RBMK, of unstated unit and date, and at a resolution
  that doesn't separate every symbol. The Karpan cartograms (accidont.ru) are blocked by this
  network's DNS policy. Needed by A6.5 / A6c / A6d, not by the supercells.
- **B₄C density — still open**, no source found. Bracket 1.7–2.3 g/cm³ (nominal 2.0), natural B.
- **Displacer graphite — bracketed.** 1.65 nominal ([D] p. 11), 1.73 upper ([D] p. 47), 1.50 lower
  (a 90 % fill of "bushings and blocks"). [CAST] names the grade GR-93. Temperature: the CPS water's,
  with [CAST]'s "≤ 500 °C" as the upper case.
- **Additional absorbers (ДП) in Unit 4 — closed: one.** [INSAG7] p. 67 ("the total lack of black
  absorbers (only one additional absorber) in the core") and p. 107 (the reference state "10.3 MW·d/kg,
  one additional absorber, and one empty fuel channel").
- **Qualitative checks from [D] p. 20 (critical-assembly experiments):** water inside a
  B₄C rod raises its worth by ~5 %; an outer water layer of 2 / 4 / 6 mm lowers it by ~5 / 9 / 13 %;
  the epithermal share of the rod's absorption with water inside is 18–20 %. Used as sanity checks
  on the A6.3 section worths, not as targets.

**[D] Fig. 2.3 (PDF p. 25), digitised — the first sourced core cartogram (2026-09-26).**
"Начальная загрузка реактора второго блока Ленинградской АЭС": the initial loading of Leningrad
Unit 2, a first-stage RBMK-1000. It was digitised by hand into `sources/derived/core_layout.xlsx`,
checked against the scan with the overlay from `tools/render_core_layout.py`
(`core_layout_overlay.svg`), and corrected (see that script's header). It closes on every count
the book's text gives (p. 57 and the parameter table): **1693 technological channels, 179 CPS
rods, 12 ДКЭ(в), 4 start-up chambers, 1888 positions**. The rod types are 89 РР, 21 УСП, 12 АР,
21 АЗ and 36 АЗ over-compensation; 21 УСП and 21 АЗ agree with INSAG-7 p. 43 for first-stage
units. Fuel with radial detectors: 282 in the figure, 270 in the text. That is recorded as a
figure/text difference (no misreadings found); it doesn't affect the model.
It is Leningrad-2's first core, not Chernobyl-4's: 179 rods, not 211, and 240 additional
absorbers of the first loading. So it gives the sourced **core outline** and the **rod-type
pattern**, and mapping it onto Unit 4's 211 sites (Fig. II-6) is a stated assumption for
A6.5 / A6d.

| Tag | Source | Used for |
|---|---|---|
| [OST] | ОСТ 1 90048-90, САВ-1 composition, as reproduced at evek.org/materials/splav-sav1.html (fetched 2026-09-26) | CPS tube alloy |
| [SF] | RBMK operator training text, studfile.net/preview/16424193/page:10 (fetched 2026-09-26) | absorber tubes are САВ-1 |
| [LEG] | *Кинетика и регулирование ядерных реакторов*, ch. "Органы управления и защиты канальных реакторов", leg.co.ua (fetched 2026-09-26), Fig. 6.7 | fuel : CPS = 7 : 1; generic type cartogram |
| [DREG] | Dmitriev V. (VNIIAES), "Data on Chernobyl accident in a digital form" (SKALA/DREG and PRIZMA listings), accidont.ru; local Wayback copies in `accidont/` (md5 in `derived/dreg_0123_mfcc.csv`) | 01:00–01:23:48 drum pressures, levels, feedwater, MCP flows; per-channel flows at 01:00 |
| [MOC07] | Mochizuki H., Nucl. Eng. Des. 237 (2007) 300–307, doi:10.1016/j.nucengdes.2006.07.002; `1-s2.0-S0029549306004626-main.pdf` | quarter-loop geometry and elevations (Fig. 1), 01:19 state, pump ns/NPSH; transcribed in `derived/mochizuki2007_loop.csv` |
| [ALM98] | Almenas K., Kaliatka A., Ušpuras E., *Ignalina RBMK-1500: A Source Book*, LEI 1998; `ignalina-rbmk-1500-source-book_compress.pdf` (md5 115aa3ff…) | MCC chapter 5: pump (J = 3741 kg·m², n_s 102), drum, headers, elevations, ZRK valve curves (`derived/ignalina_zrk_valve.csv`) |
| [HOZ] | Hózer Z., "Review of RIA and LOCA criteria for VVER fuel", KFKI AEKI (ETDE 20796265), https://www.osti.gov/etdeweb/servlets/purl/20796265; `HOZ_Hozer_RIA_LOCA_criteria_VVER.pdf` (md5 b274659d…) | Zr-1%Nb (E110) RIA failure from IGR/BIGR/GIDRA: ballooning lower boundary ~160 cal/g, no pulse-width effect to 950 ms; Vitanza/KAERI correlations (eqs 4, 5) |
| [NEA10] | OECD/NEA CSNI, *Nuclear Fuel Behaviour under Reactivity-initiated Accident (RIA) Conditions*, State-of-the-art Report, NEA/CSNI/R(2010)1, https://oecd-nea.org/upload/docs/application/pdf/2021-03/csni-r2010-1.pdf; `NEA10_csni-r2010-1_RIA_SOAR.pdf` (md5 13769495…) | fragmentation thresholds (Table 12: 1005–1130 J/g fresh), molten-fuel FCI 1190–1360 J/g (Sec. 7.1.2), irradiated-fuel dispersal ≈500 J/g above 40 MWd/kgU (Ch. 7) |
| [SKI05] | SKI Report 2005:16, *Research Assessment of Core Failure Limits*, https://www.osti.gov/etdeweb/servlets/purl/20633267; `SKI05_core_failure_limits.pdf` (md5 3f2852aa…) | background on RIA/LOCA failure limits (not yet used) |
| [JAS03] | Jasiulevicius A., *Analysis methodology for RBMK-1500 core safety and investigations on corium coolability during a LWR severe accident*, Doctoral thesis, KTH Stockholm, 2003 (ISSN 1403-1701 Kärnkraftsäkerhet 10), https://www.osti.gov/etdeweb/servlets/purl/20468669; `JAS03_Jasiulevicius_2003_KTH_thesis_RBMK1500_core_safety_CHF.pdf` (md5 ff4a854a…). Appendices C–H (the papers) are not in this copy | secondary source for the Osmachkin (RBMK lower assembly), RRC KI and Khabenski CHF correlations (§3.6, eqs 17–34) and for the KTH/E-108/RRC KI assessment at 7 MPa (§3.7, Table 7) |
| [VTT03] | Jasiulevicius A., "Reactor physics calculations and core analysis at the Nuclear Power Safety Division, KTH", in *VTT Symposium 230* (Espoo 2003), starting printed p. 11 (PDF p. 13), https://sarjaweb.vtt.fi/pdf/symposiums/2003/S230.pdf; `VTT03_VTT_Symposium_230_2003_Jasiulevicius_KTH_RBMK.pdf` (md5 059ee795…) | EPRI CHF recommended for RBMK-1000 subchannel analysis; Khabenski good only to ~1100 kg/m²s (PDF pp. 22–23) |
| [ADE98] | Aden V.G., Nikitin Yu.M., Bek E.G. (RDIPE / MSZ), "Development of RBMK fuel assemblies. Features of design, research findings", IAEA meeting paper XA9846747 (~1998), https://www.osti.gov/etdeweb/servlets/purl/352044; `ADE98_Aden_Nikitin_Bek_RDIPE_RBMK_fuel_assemblies.pdf` (md5 e29a1c9f…) | RBMK-1000/1500 assembly CHF test findings: heated-length and axial-shape effects (p. 39), q_cr vs x plots (Fig. 2a/2b, p. 41) |
| [TD1203] | IAEA-TECDOC-1203, *Thermohydraulic relationships for advanced water cooled reactors*, IAEA, Vienna, 2001, https://www-pub.iaea.org/MTCD/Publications/PDF/te_1203_prn.pdf; `TD1203_IAEA-TECDOC-1203_thermohydraulic_relationships_2001.pdf` (md5 43e1e40a…) | CHF look-up-table method and K1–K8 bundle factors (Ch. 3, Table 3.3), transient CHF (§3.7.3), film boiling (Ch. 4), 1995 CHF LUT (App. II, image tables), IPPE WWER bundle LUT (App. III), AECL film-boiling LUT (App. IV), IPPE film-boiling table (App. V) |
| [R5V4] | NUREG/CR-5535 / INEL-95/0174 Vol. 4, *RELAP5/MOD3 Code Manual, Vol. IV: Models and Correlations* (page headers read RELAP5/MOD3.2), 1995, OSTI 106466; scanned copy with OCR layer from UNT Digital Library https://digital.library.unt.edu/ark:/67531/metadc622908/; `R5V4_NUREG-CR-5535_Vol4_RELAP5_MOD3_models_correlations.pdf` (md5 8ef1f12f…) | RELAP5 post-CHF set: Chen transition boiling (eqs 4.2-16 to 4.2-20), modified Bromley film boiling (4.2-21 to 4.2-26), 1986 AECL-UO CHF table and multipliers (4.2-32/33, Table 4.2-8), PDF pp. 140–150 |
| [CTF23] | Salko R., Avramova M., Wysocki A., Hizoum B., Hu J., Abarca A., *CTF Theory Manual: Version 4.4*, ORNL/SPR-2023/3125, 2023, https://info.ornl.gov/sites/publications/Files/Pub203334.pdf; `CTF23_ORNL-SPR-2023-3125_CTF_theory_manual_v4.4.pdf` (md5 a739ff71…) | minimum film boiling temperature (eqs 466–470, PDF p. 159–160), Groeneveld LUT use (eq 562, PDF p. 184), Bjornard–Griffith transition boiling (eqs 587–590, PDF p. 189) |
| [DUA18] | Duarte J.P., *Understanding the Minimum Film Boiling Temperature in Two-Phase Flow*, PhD thesis, Univ. Wisconsin–Madison, 2018, https://asset.library.wisc.edu/1711.dl/DWROWJG4AHS3B8F/R/file-41954.pdf; `DUA18_Duarte_2018_UW_thesis_minimum_film_boiling_temperature.pdf` (md5 675b07b8…) | secondary transcription of the Groeneveld–Stewart (1982) T_MFB correlation (eqs 2-11 to 2-13, PDF pp. 39–40) |
| [LEE21] | Lee S.K., Brown N.R., "Flow boiling transient critical heat flux tests with stainless steel and FeCrAl: transient correlation implementation, model calibration, and sensitivity analysis", accepted manuscript of Int. J. Heat Mass Transfer (2021); VoR https://www.sciencedirect.com/science/article/pii/S001793102100836X, https://www.osti.gov/pages/biblio/1881166; `LEE21_Lee_Brown_2021_transient_CHF_manuscript.pdf` (md5 fc9a8b84…) | exponential-period transient CHF multipliers: Sakurai pool correlations (eqs 6, 7), Hata flow form (eq 10, Table 3); all at ~0.1 MPa (PDF pp. 13–15) |
| [FUJ81] | Fujishiro T., Hirose M., Kobayashi S., Tanzawa S., "Effects of coolant flow on light water reactor fuel behaviors during reactivity initiated accident", J. Nucl. Sci. Technol. 18(3) (1981) 196–205, J-STAGE open https://www.jstage.jst.go.jp/article/jnst1964/18/3/18_3_196/_pdf; `FUJ81_Fujishiro_1981_JNST18_NSRR_coolant_flow_RIA.pdf` (md5 f57554c7…) | NSRR, 0.1 MPa, 0.3–1.8 m/s: DNB ~20 ms after peak power, < 2 % of heat transferred before DNB (p. 201) |
| [CP77] | Cathcart J.V., Pawel R.E. et al., *Zirconium Metal-Water Oxidation Kinetics IV. Reaction Rate Studies*, ORNL/NUREG-17, 1977, https://www.osti.gov/servlets/purl/7317596; `CP77_Cathcart_Pawel_ORNL-NUREG-17_Zr_oxidation_kinetics_IV.pdf` (md5 662b007f…) | Zircaloy-4 parabolic rate constants, Summary p. vii (PDF p. 9) |
| [BJ62] | Baker L. Jr., Just L.C., *Studies of Metal-Water Reactions at High Temperatures III*, ANL-6548, 1962, https://www.osti.gov/servlets/purl/4781681; `BJ62_Baker_Just_ANL-6548_Zr_water_reaction.pdf` (md5 65dbbbcb…) | Baker–Just parabolic rate law (abstract, PDF p. 10) |
| [GRO06T] | 2006 Groeneveld CHF look-up table as tabulated in the GitHub repository greenwoodms06/2006_Groeneveld_CriticalHeatFlux_LUT (MIT licence for the code), file `2006LUTdata.txt`, https://raw.githubusercontent.com/greenwoodms06/2006_Groeneveld_CriticalHeatFlux_LUT/master/2006LUTdata.txt (fetched 2026-10-23); `GRO06T_2006LUTdata_greenwoodms06.txt` (md5 c212f5dd…). **Third-party transcription**; the primary is Groeneveld D.C. et al., *The 2006 CHF look-up table*, Nucl. Eng. Des. 237 (2007) 1909–1922 (paywalled, not obtained) | 504 × 23 = 24 pressures × 21 mass fluxes × 23 qualities, kW/m²; grid from the repo's `Groeneveld_LUT.m`. Not verified against the primary |
| [GRO03T] | Film-boiling heat-transfer-coefficient look-up table as tabulated in the same repository, file `2001LUT_FilmBoilingCoef.txt` (fetched 2026-10-23); `GRO03T_2001LUT_FilmBoilingCoef_greenwoodms06.txt` (md5 1edc12ac…). **Third-party transcription**; primary is Groeneveld D.C. et al., *A look-up table for fully developed film-boiling heat transfer*, Nucl. Eng. Des. 225 (2003) 83–97 (paywalled; the repo says the paper prints only part of the table) | not used yet; grid and units undocumented in the file itself |
