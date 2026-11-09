---
id: 45
status: todo
priority: High
blocked_by: []
tags: [tier-a, tier-b, th, loop, sourcing]
---

# Digitise accidont Fig. 7 (measured flow in every channel, 01:22:30) and use it instead of the power-valved flows

Every deck in the band valves each channel's flow to its own power (`U4_FLOW=prop`, `U4_PCHAN`). That is an
ASSUMPTION about how the operators had the channel isolation-control valves set. accidont Fig. 7 [ACC]
(`sources/accidont/picture67.JPG`, registered as "channel flows, not yet digitised") prints the measured
coolant flow Q_кан in m³/h for every fuel channel. It is labelled in plant coordinates and colour-banded against
the core mean (±5 %, 5–25 %, > 25 %). Its cells also name every CPS site's type (РР, ПК, АЗ, УСП, АР, ДКВ, ДП),
which makes it a third independent check of Fig. 11's rod types (card #44).

Found 2026-11-09 while settling #44's sources.

**Sources:** [ACC] Fig. 7; `tools/digitise_accidont_fig11.py` (same grid registration: column X centred at
x = 46.5 + 14.5 (X − 9) px on a 1520-px-wide image, to be re-found on this one, not assumed); [D] p. 95 for the
nominal channel flow; DREG `dreg_0123_mfcc.csv` for the total at 01:23.

## Acceptance Criteria
- `sources/derived/accidont_fig7_channel_flow.csv`: row, col, Q m³/h, colour band and printed type label for
  every site. The digits are read from the image, and the colour band must agree with each value against the
  core mean.
- Type labels checked against `unit4_channel_map_fig11.csv` at all 211 rod sites and the 12 ДКЭв (≠ = report).
- The total and mean flow compared with DREG's 01:22:30 / 01:23 flows and INSAG-7 p. 64 (56 000 m³/h).
- A generator option `U4_FLOW=fig7` (off = byte-identical decks) that sets per-channel inlet velocity from the
  measured flows, scaled to the sourced total. Then:
  - the flow-vs-power correlation of the record against `prop`;
  - the band-B t = 0 TH state;
  - one Newton B4 run compared with `prop`.
- If the record does not follow power, `prop` is retracted as the nominal and kept as a B5 bracket.

## Narrative
- 2026-11-09: Opened while closing #44's sources. accidont Fig. 7 is a full-core cartogram of measured channel flows at 01:22:30, already on disk; no card covered it. (by @assistant)
