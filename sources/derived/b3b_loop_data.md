# B3b loop data: what is sourced, and what is not yet

Every number the momentum and loop model uses must come from here, with its source and page.
Page numbers are **PDF pages**.

## RBMK-1000 (primary: [D] Dollezhal & Emelyanov 1980)

| quantity | value | source |
|---|---|---|
| nominal thermal power, flow | 3140 MW, 37 500 t/h | [D] p. 50 |
| separator (drum) pressure, nominal | 70 kgf/cm² | [D] p. 50 (69 at Leningrad-1, p. 73) |
| group distribution header pressure, nominal | 82.7 kgf/cm² | [D] p. 50 |
| inlet / outlet temperature, nominal | 270 / 284 °C | [D] p. 50 |
| mean exit quality, nominal | 14.5 % | [D] p. 50 |
| channel-outlet mixture | 285 °C, 72 kgf/cm² | [D] p. 82 |
| loops | 2 independent; per loop 2 separators, 4 MCPs, 22 group headers | [D] pp. 59–60, 80, 82 |
| downcomers | 12 per separator; Ø 300 mm inside | [D] p. 80, p. 176 |
| MCP (ЦВН-7) rated point | 8000 m³/h, 203 m w.c. (~2 MPa) head, suction 72 kgf/cm² | [D] p. 80 |
| MCP motor, flywheel | 5500 kW, GD² = 15 t·m² | [D] p. 80 |
| pressure header | OD 1040 × 70 mm | [D] p. 82 |
| group distribution header | OD 325 × 15 mm | [D] p. 82 |
| water line (header → channel) | 57 × 3.5 mm | [D] p. 60 |
| steam-water line (channel → drum) | 76 × 4 mm | [D] p. 60 |
| feedwater lines | 426 × 22 mm | [D] p. 82 |
| ZRK valve (Table 3.1) | flow 30.6–12.0 t/h; Δp 6.2–13.9 (calc.), 7.6–14.0 (meas.) kgf/cm²; throat 2.5–0.9 cm²; throat velocity 44–48 m/s; throat dynamic head 7.7–9.0 kgf/cm² | [D] p. 62 |
| valve characteristic | Q/√ΔP = f(h), identical for all valves | [D] p. 69 |
| channel ΔP(Q) with inlet sections, measured, Leningrad-1 | Fig. 3.10 → `D_fig3_10_channel_dp.csv` | [D] p. 70 |
| two-phase friction method, slip | formulas on pp. 68–69 (OCR garbled; re-read from page images) | [D] pp. 68–69 |
| CHF correlation | p. 70 | [D] p. 70 |
| ECCS trigger | header–separator Δp falling to ~4 kgf/cm² | [D] p. 179 |
| pump coastdown at constant pressure, with inertia | 25 s | [TD722] p. ~163 (text l. 7557) |

## RBMK-1500 (secondary, values given as "around": [ZJ02] Zemulis & Jasiulevicius, FR0200406)

Drum separators 2 per loop, horizontal, length ~30 m, inside Ø 2.6 m; 12 downcomers Ø 0.3 m; suction
and pressure headers inside Ø 0.9 m, ~20 m; 4 MCP pipes ~70 m, Ø 0.75 m; group headers Ø 0.3 m,
~40 channels each; steam-water lines Ø ~0.07 m; MCP coastdown 120–300 s on loss of power.
File `sources/FR0200406_osti20241670.pdf` (https://www.osti.gov/etdeweb/servlets/purl/20241670).

## Accident-time state (INSAG-7)

- 8 MCPs running, 4 per side; MCPs 13, 14, 23, 24 coasting down with TG-8 from 01:23:04.
- 01:23 flow ~56 000 m³/h, 200 MW, 3 °C subcooling (p. 64; A7/A8 decks).
- Drum pressure rising ~6 kPa/s after the turbine stop valve closed (p. 60).
- Feedwater ~120 t/h per side (p. 60).
- +7 s: flow −40 % on MCPs 11, 12, 21, 22, and a sharp drum pressure rise; +8 s: 75.2 (left) / 88.2
  (right) kg/cm² (p. 55).

## Gaps (not yet sourced)

1. **Elevations**: header, core inlet/outlet, drum water level. These set the static heads (Fig. 3.10's
   ~2 kgf/cm² at zero flow is a partial constraint).
2. **Line lengths** of the water and steam-water lines (inertia, friction).
3. **Drum geometry for RBMK-1000** (only the RBMK-1500 "around" values above), and the
   accident-time drum water level.
4. **MCP head curve** beyond the rated point. Plan: homologous (Suter) curves for the pump's
   specific speed, anchored at the rated point, coastdown from GD². This is a modelling assumption,
   to be stated as such.
5. **01:23 header pressure.** Plan: close each channel's valve loss from the sourced steady state
   (flow per channel from the A7 valving, total 56 000 m³/h), with the header pressure from the
   pump curve at 7000 m³/h per pump.
6. **01:23 drum (separator) pressure.** The A7/A8 decks' `INLET 7.384407E+06` (75.3 kgf/cm²) is the
   outlet-pressure boundary of THM, and it was never sourced: INSAG-7 gives the drum pressures only
   at +8 s (75.2 / 88.2 kgf/cm², p. 55) and a rise of ~6 kPa/s after the turbine stop valve closed
   (p. 60). The nominal 70 kgf/cm² ([D] p. 50) is the operating value, not the 01:23 one.

## Placeholders in the B3b-2 mechanics test (`tierb/RBMKCore.jl/test/b3b_lines_setup.jl`)

`ChanLines(sourced=false)`: line lengths 25 m (water) / 30 m (steam-water), elevations 5 m / 18 m,
outlet local losses 2 velocity heads, header − drum 12.7 kgf/cm² (the [D] p. 50 nominal, not 01:23).
They exercise the solver; no result depends on them until gaps 1, 2, 5 and 6 are closed.

## Found 2026-10-18 (research pass)

**The recorded 01:23 MFCC state exists in digital form** — the DREG record from the SKALA tape,
published by V. Dmitriev (VNIIAES) on accidont.ru, local copies in `sources/accidont/`, the drum
pressures transcribed in `dreg_0123_mfcc.csv`. Per loop, from 01:00 to 01:23:48: drum pressure Psd,
drum level, feedwater flow and temperature, MCP-inlet water temperature, and each of the 8 MCP flows;
plus the discrete signals (AZ-5 at 01:23:40, "pressure excess in SD" at 01:23:47). It also has the
PRIZMA cartograms at 01:00 (per channel: power, burnup, **water flow m³/h**; scans
`PRIZMA_01.JPG`/`PRIZMA_02.JPG`, to be OCR'd) and the 01:22:30 rod pattern and DKE readings.

This **closes gap 6 and contradicts the decks**: at 01:23:00–01:23:39 the drums read 63.2–65.0
(left) and 64.1–68.6 (right) kgf/cm², rising only at 01:23:45–48 to 75.2 / 88.4. The decks'
`INLET 7.384407E+06` (75.3 kgf/cm²) is INSAG-7's +8 s left-drum value, ~10 kgf/cm² above the
pre-excursion state. Recorded MCP-inlet temperature is 281 °C on both sides throughout, so the
subcooling is set by pressure at the core inlet (drum + downcomer head + pump head − line losses),
not by the drum. Consequences for A7/A8 and Tier B (THM's single pressure, the 3 K subcooling) are
OPEN and not yet assessed. Whether Psd is gauge or absolute is not stated (1 kgf/cm² either way).

Recorded MCP flows 01:23:00–01:23:43: each pump 5.2–8.0 ×1000 m³/h, the four coasting pumps
(L3, L4, R3, R4) falling from ~7.3–7.9 to ~5.2–5.8 ×1000 m³/h by 01:23:43 — a direct boundary
condition for the loop model, to be transcribed.

**Gaps 1–4 (geometry, pump curve) — candidate sources, not yet obtained:**
- Abramov M.A., Avdeev V.I., Adamov E.O. et al., *Канальный ядерный энергетический реактор РБМК*,
  ed. Yu.M. Cherkashov, GUP NIKIET, Moscow 2006 — the designer's monograph; MFCC layout, elevations,
  pipework, ЦВН-7 characteristics. Library/purchase.
- Mochizuki H., "Analysis of the Chernobyl accident from 1:19:00 to the first power excursion",
  Nucl. Eng. Des. 237 (2007) 300–307, doi:10.1016/j.nucengdes.2006.07.002 — a coupled loop model of
  Unit 4 against the recorded data; its loop inputs (and earlier NETFLOW papers) are the closest
  published geometry set. Paywalled (academia.edu copy exists).
- Fletcher C.D. et al. (INEL), "Simulation of the Chernobyl accident", Nucl. Eng. Des. 105 (1988)
  157–172 — RELAP5/MOD2 Chernobyl-4 model from open literature, with a cavitating-pump model.
- Almenas K., Kaliatka A., Ušpuras E., *Ignalina RBMK-1500: A Source Book*, LEI 1998 (OSTI 58920;
  a Scribd copy exists) — the most complete open elevation/pipe/pump data, for the RBMK-1500 sister
  design (same MFCC topology; ~21 m core-bottom to drum-bottom, >30 m overall).
- Kaliatka et al. (LEI), Ignalina MCP-trip benchmarks (OSTI 20236645, 20529063) — CVN-8 coastdown
  and pump modelling validated on plant data (RBMK-1500 pump, not ЦВН-7).
- Pump rated point corroborated: 8000 m³/h, 200 m, 1000 rpm, inlet 7.2 MPa, 270 °C, 4300 kW
  (Russian textbook summaries citing ЦВН-7; [D] p. 80 gives 203 m). ЦВН-7 cavitation curves exist
  in graphical form (atomas.ru "Атомные станции с реакторами РБМК-1000", ch. 24 — blocked by the
  local network's DNS policy, not accessed).
- RBMK-1000 drum: OD 2300 mm, length 30 480 mm, wall 105 mm (ResearchGate figure caption, seismic
  study of RBMK-1000 drum separators) — to be confirmed from a primary source.
- Leningrad NPP training text (pavrda.cz/cernobyl/rbmk): pressure-header pressure 86.0 kgf/cm²
  nominal (vs [D] p. 50 group-header 82.7).

## [MOC07] Mochizuki 2007 — obtained 2026-10-18 (`mochizuki2007_loop.csv`)

Fig. 1 is a dimensioned quarter-loop model of Unit 4 (drum, downcomers, suction header, pumps,
pressure header, group headers with ZRK valve and flow meter, feeders, channels, outlet pipes) with
elevations. A **secondary compilation** (sources listed, not attributed per number), but published,
used against the recorded DREG trends from 01:19 and the best available. Status of the gaps:
1. **Elevations — closed (secondary):** pump 5.9, pressure header 7.6, feeder low point 6.3,
   group header 12.15, core 11.8–20.0, channel exit 25.6, drum centreline 33.65 m (EL 0 = pump base).
2. **Line lengths — closed as ranges:** feeders 22.5–32.5 m (ID 50 mm), outlet pipes 12.7–23 m
   (ID 68 mm), downcomers 23–33.5 m, headers and pump legs. Per-channel lengths are not given; the
   ranges become a sourced uncertainty in B5. (The B3b test's placeholders 25/30 m fall inside.)
3. **Drum — partly:** 30 m × ID 2.6 m, NWL 1.8 m above bottom. ID 2.6 conflicts with an OD of
   2.30 m quoted for RBMK-1000 elsewhere: OPEN.
4. **Pump — rated point and specific speed only:** 200 m, 1000 rpm, 8000 m³/h, ns = 0.0843, NPSHR
   23 m. **No head-flow curve**; the homologous-curve plan stands, now anchored on ns. **GD² conflict:**
   1500 kg·m² here against 15 t·m² in [D] p. 80; the paper says it had to raise the inertia to match
   the recorded coastdown, which favours [D]. The DREG per-pump flows (01:23:04–01:23:43) constrain it.
5. **01:23 header pressure — not given;** it follows from the loop model with the DREG drum pressure.
   Mochizuki's computed pump-inlet state (6.542 MPa, 277.9 °C) is a model result; DREG measures 281 °C.

New for the model: pump heat 7 MW and graphite-to-coolant heat ~20 MW per quarter-loop at 01:19
("investigated"). The Tier B TH has neither. Steam flow from the drums falls from 01:23:08 and is
zero from 01:23:14 (turbine stop valve), the boundary condition behind the drum-pressure rise.
