---
id: 35
status: todo
priority: Normal
blocked_by: []
tags: [sourcing, chf, fuel]
---

# Close the CHF / post-CHF / cladding-failure sourcing gaps

The post-CHF model (PROGRESS (49)) rests on sources with known gaps
(`sources/derived/chf_postchf_correlations.md` Sec. 6): [D] p. 70 gives no validity range and prints a
subcooling coefficient (4.07) that contradicts the energy balance (41.2); the 2006 CHF LUT is a third-party
transcription not checked against the primary; there are no transient-CHF data near 7 MPa for ~1 s ramps,
and the ×2 bound moves the hottest cladding from 893 to 458 °C; E110 (Zr-1%Nb) burst and oxidation laws are
missing; the film-boiling void factor M_a is interpolated between printed anchors.

**Sources:** PROGRESS (48), (49); `sources/derived/chf_postchf_correlations.md`.

## Acceptance Criteria
- Each gap either sourced (registered in `sources/README.md`) or listed as a carried bracket.
- The 2006 LUT checked against the primary (NUREG/KM-0011 data base or the NED paper) where obtainable.

## Narrative
- 2026-11-08: Opened from the gap list of the CHF write-up. (by @assistant)
