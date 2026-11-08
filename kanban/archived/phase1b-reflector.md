---
id: 9
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, openmc, sourcing]
---

# Phase 1b: the reflector, and a DRAGON fault OpenMC caught

Source the graphite reflector geometry and build reflector cross sections for the core. The geometry closed against two sources. The first write-up blamed diffusion theory for a 14× flux discrepancy, and that was wrong. OpenMC showed instead that DRAGON's own open-boundary solution is wrong on this problem. The reflector COMPO was rebuilt on a closed geometry, with a bounded interface error.

**Sources:** PROGRESS "Phase 1b: the reflector, and a DRAGON fault OpenMC caught" (2026-10-01; supersedes the earlier entry in commit `ca5b4a6`); key files: `openmc/refl.py`, `openmc/slab.py`, `_RCompo`.

## Outcome
- Geometry from [D] p.9: core 11.8 m across and 7 m high, a 1 m lateral reflector, and 0.5 m end reflectors. `NZ_ACTIVE = 28` and `NZ_REFL = 2` were confirmed. `NREF = 2` was wrong and is now 4.
- Reflector column count: [D]'s 2488 stack columns minus the 1888 channel-map positions gives 600, which matches [BEH96]'s 444 + 156 = 600. A circle at R = 28.14 cells reproduces 2488 to 0.3 %. The core grid becomes 58 × 58.
- Trap avoided: the "32 cm axial reflector" in [BEH96]/[ALX98] belongs to the RRC critical facility, not a power reactor.
- DRAGON open-boundary fault, 4 fuel cells with one vacuum face:

  | | k |
  |---|---|
  | OpenMC | 1.198662 ± 0.000691 |
  | DONJON | 1.191992 |
  | DRAGON | 0.849315 (34 000 pcm away) |

- What the fault is not: the boundary keywords, geometry/tracking, the leakage model, tracking density, mesh, and self-shielding were each excluded. The cause is not identified. The remaining suspect is CP versus MOC, which could not be tested because `MCCGF: INVALID TRACKING FILE` occurs without the `CTRA NONE` library. No published DRAGON result is affected, since all were on fully reflected geometry. Open-boundary DRAGON is now a standing trap.
- On the closed geometry, transport gives 1.155893 against diffusion's 1.260055, a gap of 7152 pcm. This was stated as an upper bound on the core-level error. **Later resolved in PROGRESS (4):** the whole radial reflector is worth 131 pcm at core level, so the 7152 pcm does not propagate.
- SPH will not converge on the reflector across seven variants. `MCFD 1` segfaults.
- `_RCompo` was rebuilt on the closed geometry. Diffusion coefficients are 1.14 / 0.79 cm in fuel and ~1.03 / 0.83 in graphite. It is usable and no longer a placeholder.

## Narrative
- 2026-10-01: Sourced the reflector as four rings and two materials, and corrected `NREF` to 4. The reflector supercell needed vacuum outside, and its k fell far below what diffusion could reproduce. The first entry (`ca5b4a6`) read that as diffusion lacking a streaming tail. Per standing rule 4, an independent OpenMC check overturned it: OpenMC sided with DONJON, and DRAGON was 34 000 pcm off.
  - Every plausible input error was eliminated one at a time, and the hunt was stopped because the fault is avoidable.
  - Closing the boundary costs only 21 pcm in diffusion, because the flux at the outer face is ~1 % of the core's.
  - The remaining 7152 pcm was measured on a test that over-weights the reflector. It was recorded as an upper bound, with core-level measurement or an albedo boundary as the next options. (by @assistant)
