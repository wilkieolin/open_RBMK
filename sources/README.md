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
