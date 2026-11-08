---
id: 24
status: done
priority: Normal
blocked_by: []
tags: [tier-b, neutronics, sourcing]
---

# INSAG-7 Fig. II-7 digitised, radial starting states, and the tilted start in AZ-5

INSAG-7 Fig. II-7, the initial radial neutron field, was digitised at every fuel channel. Its peaking is 1.54, against the model's 1.60. The model's radial field matches the figure rotated by 90 degrees (r = 0.885) much better than as printed (r = 0.60), so the figure's orientation decides the comparison and is left open. Of the radial starting states probed, only a planar tilt solved to the figure as printed fits it (r = 0.913). In AZ-5 that tilt raises Kv to about 5 and the peak to 253.8x, but its fuel still stops short of fragmentation.

**Sources:** PROGRESS (49) (Fig. II-7, radial starting states, tilted start); key files: `tools/digitise_fig_II7.py`, `sources/derived/insag7_fig_II7_lattice.csv`, generator `U4_BURNMAP`, `test/b4_coupled.jl` (`B4_CLAMP=1`).

## Outcome
- Digitisation: contours every 10, labels every 20 (15-17 lines from the outline to the 160 loop). Read as the median line count over 72 rays. The field averages 104 over 1661 channels, so the levels are % of the core mean. Precision: one band, about one cell.
- **Fig. II-7 peaking 1.54** vs the model's t = 0 channel peaking 1.60. INSAG's "radial peaking 2.0" (p. 66) is a power figure that the printed flux map doesn't reach.
- Orientation vs Fig. II-6 (the model lattice is registered to all 1888 positions):
  - as printed (assumed): r 0.60, rms 31 %;
  - **rotated 90 degrees: r 0.885**, rms 17 %;
  - mirrored: r 0.861, rms 19 %.
  - This suggests the figure is printed rotated. Not decided; both are carried.
- Radial starting states (DONJON t = 0 dumps):
  - base: Kr 1.60, Kv 2.52;
  - `chess`: Kr 3.47, Kv 5.10, r 0.05. **Excluded.**
  - `chk25` (+-25 %): Kr 1.69, r 0.58. The flux smooths channel-scale variation, so 2.0 can't be reached this way.
  - `pl2p8_0p4` (planar tilt to Fig. II-7 as printed, re-valved): Kr 1.78, Kv 2.45, **r 0.913, rms 18 %**. This is the "as printed" bracket.
- The planar response is strongly non-linear (a 10 % tilt gives Kr 3.2-3.6, near a first-azimuthal-mode degeneracy as in (21)). The fit was linearised from +-10 % runs and verified in DONJON. Reaching Kr 2.0 with Fig. II-7's flux would need fresh assemblies clustered in the high-flux region, which is the unsourced placement problem.
- Tilted start in AZ-5 (fixed pressure, Newton, band B):
  - Kv 4.94-4.96 at 3-4 s; hottest bundle 184x the initial mean at 37x (Ref. [28]: about 165x). Base: 3.98 and 121x.
  - Peak **253.8x at 4.91 s** (base 230.2x at 5.24 s).
  - Hottest bundle 158.5 cal/g at 5.5 s and still rising (base 127); 24.5 t above 120 cal/g; adiabatic integral 225 cal/g by 5.5 s.
- The run stops at 5.30 s on the COMPO's 2000 K T-FUEL axis. With `B4_CLAMP=1` (an upper estimate after that point) it stops at 5.56 s in a channel Newton: an iterate at h = -1.1e7 J/kg, and the fixed-pressure path has no loose fallback. The end state isn't reached; the trend is about 160-170 cal/g, short of fragmentation (240-270).
- Next from (49): the tilted start in the loop (the right half carries 62 % of the power, a test of the orientation); the fixed-pressure fallback and the 2000 K axis; a source for Fig. II-7's orientation or Ref. [28] itself.

## Narrative
- 2026-10-24: (49) (48) had located the deficit as a too-flat radial field, so Fig. II-7 was digitised. Its level basis was inferred from the field's 104 mean. The comparison flipped on orientation: as printed it disagrees with the model's rod-pattern-driven field, and rotated by 90 degrees it agrees well. Both orientations are carried until a source settles it. Burnup checkerboards were tried: the full [PAV] histogram contradicts the figure, and the +-25 % pattern is smoothed out by the flux. A planar tilt solved to the figure as printed fits it best. In AZ-5 it brings Kv and the hottest bundle close to Ref. [28]. It is the only change tried that moves the local energy materially, but it still trends short of fragmentation before the run stops on the T-FUEL axis and a Newton failure. (by @assistant)
