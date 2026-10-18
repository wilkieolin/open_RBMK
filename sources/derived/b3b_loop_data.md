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
