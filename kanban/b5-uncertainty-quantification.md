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
