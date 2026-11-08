---
id: 16
status: done
priority: Normal
blocked_by: []
tags: [tier-a, rods, neutronics, numerics, infra, sourcing]
---

# A8: rods as devices, the sourced inputs, the AZ-5 ramp, and its sign

Make the 211 CPS rods movable DONJON devices, source A8's last two inputs, and measure the AZ-5 ramp and the first transient. Three silent bugs stood between the base map and a moving rod, one of them five copies of an upstream axis formula. A fake 9.3 % power rise was retracted. With the fixes, devices and base map agree to seven figures. The sourced 01:22:30 state gives a negative, point-kinetic scram. The axial probe then showed the ramp's sign follows the axial flux peak, ranging from +400 to −1400 pcm.

**Sources:** PROGRESS (22), (23), (24), (25), (26); key files: `patches/0002-NEWMAC-multi-isotope-macrolib`, `patches/0003-DEVINI-MOVDEV-axis-indexed-core-limits`, `tools/apply_patches.sh`, `gen_rbmk_unit4.py` (`U4_DEV`, `U4_RODFULL`, `U4_DEVQ`, `U4_DEVADV`, `U4_AXBURN`, `U4_PBUND`, `col32()`, `insag_col()`), `tools/a8_ramp.py`, `tools/a8_pk.py`, `tools/a8_axial.py`, `A8KFINAL`, `PROJECT_PLAN.md`.

## Outcome
- (22) 389 ROD-DEVICES: two single-part devices per rod, with `XFAC 1.0`, `MOVE`, and `MOVDEV: … SPEED`. Each choice was forced by the source.
- (22) Bug 1: `DEVINI:` must precede `RESINI:`. Otherwise device cross sections are silently zero and fission records are mis-strided.
- (22) Bug 2: `U4_RODS=wat` double-counted AZOC displacers, giving a negative removal cross section.
- (22) Bug 3: rod positions were computed from the X limits regardless of `AXIS`, with five copies in upstream source (`DEVGET.f`, `MOVPOS.f`, `MOVGRP.f`, `DSETGR.f`, `DSET1D.f`).
  - **Retracted in (22):** the first transient's 9.3 % rise was absorbers being deleted from the core by unpatched `MOVGRP.f`.
  - Anchor check: 1.043293 from the transient equals the static deck at +40 cm.
- (22) Patches 0002 and 0003: bundled device decks, 18 423 lines, 0 differences.
- (22) Gate: devices equal the base map to seven figures (1.044046; 0.9407398 at 24 planes). Sub-node interpolation is unverified.
- (23) Fuel-failure criterion from INSAG-7 p. 67: 220 cal/g = 920.5 kJ/kg (disintegrate), 285 = 1192.4 (rupture), 320 = 1338.9 (disperse). **Later re-sourced in PROGRESS (47):** 220 cal/g is a disintegration threshold, not the onset of failure.
- (23) The comparison target is a band: 31×–64× at 6.5 s and 400–1000 MW/s. Ref. [17] is disclaimed by INSAG-7.
- (24) Static AZ-5 ramp from the sourced pattern: monotonically negative, −72.2 pcm at 40 cm and −293.1 at 100 cm.
  - Decomposition at 40 cm: absorbers −51.7, displacers −20.5, USP −11.2. Non-additivity is +11.3 (14 %).
  - A 25 cm sawtooth comes from simultaneous node crossings.
  - A bug in my 0003 extension (`IAXIS` read after use in `DSETGR`/`DSET1D`) was caught by `AFMtest.x2m`.
- (25) 1 s AZ-5 transient: P/P₀ 0.86929 at 1.00 s, with an exact anchor (−72.2 pcm). dt 10 vs 5 ms differ by at most 0.00173, so 10 ms is adequate here. Point kinetics agrees within the Λ spread (0.0386), so this shows no spatial effect.
- **(24)/(25) corrected by (26):** the claim that the real core was bottom-peaked at t = 0 was wrong. INSAG-7 Fig. II-5/II-9 show a double-peaked field with a larger upper maximum; the bottom peak is what the transient produced. **Also later:** (29) found that the USP rods were not driven by AZ-5 in 1986, while these runs moved all three groups.
- (26) Axial probe via `INST-BVAL BUND`. The regression reproduces the `CHAN` route exactly.
  - Symmetric `cos` sends the peak to the bottom, showing near-degenerate axial modes.
  - Ramp at 80 cm: +358.1 (tilt +0.4), +407.5 (cos:1), −1407.9 (tilt −0.4).
  - The sign follows the peak both ways.

## Narrative
- 2026-10-05 (22): A base-map rod cannot move, so all rods became devices. Bug 1 was caught by the NBFIS guard and bug 2 by `TRISYS:`.
  - I attributed a +55 pcm offset to reflector overhang. Measuring it (−1.3 pcm) proved me wrong, and a macrolib diff found that every top-entry absorber was misplaced: the X-limit formula.
  - Patching two of five copies produced a convincing but fake power rise. The static-anchor check `A8KFINAL` caught it and is now on every transient.
  - Lesson: grep for the expression, not the routine. (by @assistant)
- 2026-10-05 (23): Found both "missing" inputs already on disk.
  - Fuel-enthalpy thresholds are in INSAG-7 p. 67, with its caveat carried verbatim.
  - The comparison target is a band, and INSAG-7 itself says the initial-state uncertainty dominates. That makes the (21) placement-band decision the only comparable form. (by @assistant)
- 2026-10-05 (24): The static ramp from the sourced state is negative, consistent with A6.5's condition, since the axial peak sat at mid-plane.
  - Decomposed it by device group; the parts are sub-additive.
  - Read the 25 cm sawtooth as evidence that sub-node interpolation is smooth.
  - The bundled-deck regression caught my patch bug.
  - The first draft's bottom-peak claim was later corrected in (26). (by @assistant)
- 2026-10-05 (25): Ran the first transient with a timestep study and an independent point-kinetics cross-check. I declined to read the 3-D residual as a spatial effect, because the Λ sweep spans it.
  - The spatial content of the accident is in the initial state, not in the rod motion.
  - Identified the missing axial shape and the unused `INST-BVAL BUND` / `AXIAL-PFORM` route. (by @assistant)
- 2026-10-06 (26): Tested the sign claim directly with an axial burnup multiplier in the device model. The sign follows the peak, and the core's axial near-degeneracy means the initial shape must be sourced, not chosen.
  - Next: digitise Fig. II-9, invert t = 0, and test against the 4/6/7 s curves. (by @assistant)
