---
id: 12
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, th, numerics]
---

# A7: the coupled core (A7b), its convergence, and the K0 switch

Close the neutronics/`THM:` Picard loop on the Unit 4 core and measure the steady-state feedbacks. The loop ran, but it first left the cross-section table at both the `DCA` and `TF` axis ends, which drove the COMPO widening. Once the table was widened, the loop's residual plateau turned out to be a limit cycle from the boiling-onset switch `K0`, not a tolerance problem. The loop now converges on the eigenvalue, and the Doppler, density and flow-spread feedbacks were measured.

**Sources:** PROGRESS (8), (11); key files: `tools/a7b_check.sh`, `decks/Donjon/data/a7b_check.txt`, `rbmk_a5b_compo.x2m`, `rbmk_unit4_core_out.don`, `THMH2O.f`, `THM.f`.

## Outcome
- A7b loop over four passes: k 1.038874 → 1.036625, contraction ratio r ≈ 0.40, extrapolated to k = 1.036471, with "Doppler −240 pcm". **Superseded by (11):** run to convergence it is k = 1.036433, and the −240 was Δk × 10⁵. As reactivity it is −227 pcm.
- The table runs out: the core asks for `DCA` 0.778 (subcooled inlet) and `TF` 586 K (cool channel ends). `NCR:` has no clamp. Pinning `DCA` at 0.72 costs ≤ 103 pcm. Both axis extensions were batched into the A6b rebuild (card 13).
- With density pinned, `prop` and `unif` flows agree to 1 pcm (−240 vs −241), which confirms the pin.
- Mechanics:
  - `UTL:` must be in the `MODULE` list.
  - The A7 flow handover uses `POWER-CHAN`, in channel order.
  - Cost is 42.6 s for four passes at 829 MB.
- (11) diagnosis: the plateau is a limit cycle on `K0` (`THMH2O.f:383`, `:276`, `:147`), whose `DTSUB` depends on heat flux and so sits inside the Picard loop. Tightening `ERMAXT` (the earlier recorded fix) was wrong.
- Relaxation at `RELAX` 1.0/0.5/0.2 gives bit-identical k = 1.039735. Pinning density removes the cycle (fuel-T residual 0.031 K, dk = 0.0).
- A latent defect was fixed: `FLUX` was deleted on the last pass, so the power-shape block had never run (kernel error 666 after the results printed).
- Converged feedbacks on the 1152-point table:

  | | value |
  |---|---|
  | Doppler | −227 pcm |
  | density/void | +306 pcm |
  | net, flow valved to power | +80 pcm |
  | net, uniform flow | +139 pcm |
  | flow-distribution spread | 59.4 pcm |
  | pinned-pair agreement | 0.5 pcm |

- Power shape: channel MAX/AVG falls from 1.8289 (cold) to 1.5719 (coupled), and peak channel power from 3517.1 to 3022.2 kW. The hottest channel is 3434 in both.
- **Later re-based:** by (12)'s 1728-point table (absolute k −19 to −21 pcm, feedbacks within 2 pcm), and by (14)'s AZOC displacer fix (Doppler −230, density +331, net +101, spread 64.2 pcm). (10) also notes that k = 1.039735 is a k at TG = 750 K and should not be quoted as the core eigenvalue.

## Narrative
- 2026-10-01 (8): Closed the Picard loop with coolant density and fuel temperature as local fuel-map parameters. It converged geometrically, then left the table at both the `DCA` and `TF` ends. Neither was a modelling error: a subcooled inlet is denser than the lattice nominal, and a zero-power node sits at coolant temperature.
  - Priced the `DCA` pin at ≤ 103 pcm and batched both extensions into the rebuild A6b already needed.
  - Ran with density pinned to get iterations at all. The two flow brackets agreeing to 1 pcm proved the pin is not leaky. (by @assistant)
- 2026-10-02 (11): Found the previous night's tolerance fix was wrong: a residual plateau with bit-identical k is a limit cycle.
  - Reading the coolant-density residual localised it.
  - The `K0` onset switch inside the loop is the mechanism, attributed by two experiments: relaxation never removes the plateau and never changes k, while pinning density removes the cycle.
  - Switched the convergence criterion to dk < 1e-6, and fixed the `FLUX` deletion that had hidden the power-shape block.
  - Measured the converged feedbacks and the first coupled power shape. Fixed the A7b units inconsistency (Δk vs Δρ).
  - The 59 pcm flow spread is the honest cost of having no sourced total core flow. (by @assistant)
