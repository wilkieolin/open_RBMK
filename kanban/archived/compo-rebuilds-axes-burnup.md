---
id: 13
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, burnup, xenon, numerics, infra]
---

# Fuel COMPO rebuilds: the axis widenings, the TG finding, and the burnup-node rebuild

Widen the fuel MULTICOMPO to cover the states the coupled core asks for, then fix what the stronger interpolation gates exposed. A6b was scoped down to the axis widenings by dropping the xenon axis. The first rebuild (1152 points) landed and showed that the off-grid gate had been measuring the pinned `TG` axis. It also showed that the never-tested burnup axis carried +2099 pcm at the fresh-fuel knee. A second rebuild (1728 points, 12 burnup nodes) cleared the core's own interval to +8.7 pcm. Absolute k moved ~20 pcm, and the differences A8 relies on moved by ≤ 2 pcm.

**Sources:** PROGRESS (9), (10), (12); key files: `rbmk_a5b_compo.x2m`, `rbmk_a5b_verify.don`, `rbmk_a5b_offgrid.x2m`, `5.1/Dragon/compo/_ACompo`, `_ACompo_pre_axis_20261001`, `_ACompo_pre_bunodes_20261002`, `tools/mk_a5b_smoke.py`, `rbmk_cell_a3.x2m`, `tools/a7b_check.sh`.

## Outcome
- (9) Xenon axis dropped, on the grounds that `NCR: … MICRO` can set Xe135/I135 densities from the core side (`NCRLIB.f:268`, `:533-538`). **Corrected in (14):** that is true of a xenon *level* but not a *field*, because `MICRO` is per mixture. The way through is binned fuel mixtures (card 15).
- (9) `-p` does nothing for this workload: 118.15 s at `-p 1` and 118.18 s at `-p 8`. Rebuilding on `spark` was rejected.
- (10) First rebuild, 1152 points (`DCA` 0.80, `TF` 530 added):
  - 34 408 s CPU. The file grew +37.1 %, matching the tensor's +37.1 %.
  - BU 0 reproduces 1.313968.
  - Round trip over 12 nodes: worst 1.3 pcm.
  - Off-grid: 30.4 pcm against the 30 pcm gate. The old points are unchanged at 23.9.
- (10) Cubic interpolation was rejected: worst case 48.3 pcm at BU 20 000.
- (10) Decomposition: the whole off-grid error is the `TG` axis (−31.1 pcm). `TG` is pinned at a node (750 K) in the core, so the realised error is ~1 pcm.
- (10) Graphite temperature coefficient: positive and rising with burnup (+198 / +600 / +1222 pcm for 750 → 900 K at 0 / 10 000 / 20 000 MWd/t). Pinning `TG` misprices the core by roughly +500 pcm. The `TG` range ("RBMK runs 500-700 C") is an uncited inline comment.
- (10) Burnup axis, tested for the first time: +2099 pcm at 500, −74 at 3500, +171 at 17 500. The core interval at 10 900 is estimated at 2–3 pcm. [PAV]'s 172 assemblies at 1.2 MWd/kgU would be mispriced by about +1170 pcm, which makes this a hard blocker for A6d.
- (12) Second rebuild:
  - 1728 points, nodes + 500, 1000, 3500, 17 500, with 14 depletion points (250 and 11 250 kept off-node as gate points).
  - 18.1 h, 312 731 083 bytes (factor 1.5007).
  - BU 0 invariant 1.313968. Round trip 1.6 pcm.
- (12) The old 11-step depletion grid carried up to 29 pcm of one-signed step error.
- (12) Burnup gate: +8.7 pcm at 11 250, so the blocker is cleared. The 250 point (+1340.9 pcm) was a badly chosen gate point, since no fuel sits there. The 1000–2000 interval is improved but not measured.
- (12) Effect on A7: absolute k −19 to −21 pcm. Doppler −226, density +308, net +82, spread 59.7 pcm. Peaking agrees to the 4th digit.
- (12) General property: a one-signed table error moves k but barely moves differences or shape.

## Narrative
- 2026-10-01 (9): Re-read the COMPO header and the `NCR:` source. The `MICR` list already carries Xe135/I135, so the xenon axis was dropped, with the self-shielding approximation stated. A6b's COMPO work shrank to A7b's two widenings.
  - Launched the 1152-point rebuild, with gates listed in advance and the old table preserved.
  - Measured that threads do not help. Rejected `spark` because its tree was stale. (by @assistant)
- 2026-10-02 (10): The rebuild landed clean.
  - Added round-trip nodes at the new axis values, because a new value is where a storage or ordering error would hide.
  - Off-grid crept to 30.4 pcm, entirely from new points in a harder test. A per-axis decomposition then showed `TG` owns all of it, on an axis the core does not interpolate.
  - Tested burnup off-node using existing non-node depletion points on the same path, and found the +2099 pcm fresh-fuel knee.
  - Scoped the fix: promote 500/3500/17 500 to nodes. Recorded the `TG` coefficient and pin as a prerequisite for Phase 2c. (by @assistant)
- 2026-10-02/03 (12): Rebuilt with 12 burnup nodes. 1000 was added where [PAV]'s fresh group sits, and off-node 250 / 11 250 were added as new gate points. `TG` was left out because its range is unsourced.
  - All structural gates passed, and the depletion-path change was measured at up to 29 pcm.
  - The core-interval gate passed at +8.7 pcm.
  - Owned the poor choice of the 250 gate point, and declined to put a number on the 1000–2000 interval from an estimator that is demonstrably unreliable.
  - Re-ran A7: absolute k shifted, differences did not. (by @assistant)
