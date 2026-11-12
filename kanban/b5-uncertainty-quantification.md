---
id: 41
status: backlog
priority: Normal
blocked_by: [29, 31, 36, 37]
tags: [tier-b, uq]
---

# B5: grounding and uncertainty quantification

The scientific goal of Tier B: fuel failure as a prediction with uncertainty. Morris screening then Sobol
on the survivors, a Turing.jl posterior conditioned on recorded data only (t = 0 shapes, the 01:22:30 rod
pattern, the 01:23:43 alarms; the post-AZ-5 record as a check), fuel failure reported as a probability against
the sourced criteria with its sensitivities. Uncertain inputs include burnup placement, starting shape, void
worth (brackets A/B), CPS worth, flow, subcooling, B₄C density, pin peaking, steam volume/τ, Qg, hsh.

**Sources:** `docs/history/TIER_B_WORKPLAN.md` (B5); PROGRESS (47) for the criteria.

## Acceptance Criteria
- An ensemble driver with an asserted memory budget (≤ 64 members on device), the input ranges sourced, Morris results, then Sobol and the posterior.

## Narrative
- 2026-11-08: Carried over from the retired Tier B workplan; the failure criterion there (920 kJ/kg) is superseded by PROGRESS (47)'s 120–325 cal/g set. (by @assistant)
- 2026-11-09: New rod-model brackets from #44 (all generator options; off = byte-identical):
  - `U4_LARDSP=0` (ЛАР without displacer): static AZ-5 ramp peak +407 against +521 pcm nominal (−22 %), the largest rod bracket;
  - `U4_RODDEPTH=sources/derived/karpan_vk_fig3_roddepth.txt` (Karpan depths; 49.1 m of rods against 43.5 m): the (27) refit is equally good (rms 0.0193);
  - `U4_ABSLEN=6` (6 m absorber, 3 m УСП; start-up act).

  Each bracket needs its own (27) refit (`insag7_fig_II9_t0_axburn_fit_f11{nl,kv}.txt`), since the effective burnup is conditioned on the rod state. (by @assistant)
- 2026-11-09 (later), from #44:
  - Karpan depths: static AZ-5 ramp peak +485 against +521 pcm (−7 %), with `tools/a8_ramp.py A8_DEPTH=…`.
  - `U4_ABSLEN=6` is **nil** to 7 s (newton B4 identical to the 6th figure; first static effect at 600 cm of travel, about 14 s). Drop it as a B5 dimension.
  - The АР-channel bottom displacer has no sourced geometry, so it is not a dimension until one is found.
  - Ranking of the rod brackets so far by ramp peak: ЛАР displacer (−114 pcm) > Karpan depths (−36) > rod re-typing (+10) > absorber length (0). (by @assistant)
- 2026-11-10: **The ЛАР displacer decides whether there is an excursion.**
  - Run: `U4_LARDSP=0` newton B4 to 7 s with `B4_CLAMP=1`. Stem `rbmk_unit4_a7_acco668_pc53421d_dev_ax4a638a_kin700v40g12shvdfr025fi60cc01dt001_vB65c86e_cB4af83e_rt9f0a8fnl`. Its own refit is `…_fit_f11nl.txt` (k 1.025156), with POWER-CHAN in `sources/derived/a8_fit_pchan_f11nl.txt`.
  - Result: power rises slowly to a **peak of 10.05 P0 at 6.39 s** and is falling by 7 s (9.35 P0). E(7 s) is 6.57 GJ, TFmax 809 K and max Eadia 29 cal/g. Every failure criterion in `b4_fuel_…_newton_cl.txt` is zero.
  - Nominal (ЛАР with displacers, same build) gives 244.5 P0 at 5.15 s, 66.76 GJ and 264 cal/g.
  - The static ramp peaks bracket a threshold: +521 pcm gives a prompt excursion, +407 pcm a sub-prompt rise that the rods turn over. The nominal therefore sits **≤ ~110 pcm (≈ 0.2 β) above the no-excursion branch**, and any input of that size can switch the outcome.
  - Such inputs:
    - Karpan depths (−36 pcm static);
    - the CPS worth corrections (`U4_CPSB`, gap 2);
    - void-worth gap 3;
    - rod speed;
    - the TH feedback items of #33.
  - Consequence for B5: the output is bimodal, not a spread around one value. Sampling must resolve the threshold, and the ЛАР case must be weighted by its sources, not 50/50. Those sources are NUREG-1250 p. 2-30 and the exact Karpan water-column count for "with displacer"; for "without", only GRS-121's ambiguous "24 without a displacement part".
  - This is a check, not a selection: the post-AZ-5 record (an excursion) is not used to pick the branch. (by @assistant)
- 2026-11-11: **ЛАР displacer settled (user decision).** NUREG-1250 p. 2-30 and Karpan's exact water-column count outweigh GRS-121's ambiguous "24 without a displacement part". ЛАР carries a displacer, and `U4_LARDSP=0` is **not** a B5 dimension. It stays as a documented sensitivity: it shows the nominal is ≤ ~110 pcm static (≈ 0.2 β) above the no-excursion branch. That margin, not the ЛАР question, is what B5 must resolve, using the remaining sourced brackets (Karpan depths, CPS worth gap 2, void gap 3, rod speed, the #33 TH items). Registered in `sources/README.md` "Displacers by type". (by @assistant)
