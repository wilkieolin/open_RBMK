---
id: 47
status: doing
priority: High
blocked_by: []
tags: [tier-a, tier-b, neutronics, rods, uq]
---

# Excursion threshold scan: which sourced brackets can move the core across the prompt-excursion line

#41 (2026-11-10) found the nominal band-B state (Fig. 11 rod types, ЛАР with displacers) is a prompt
excursion: 244.5 P0, 66.8 GJ to 7 s. The ЛАР-without-displacer sensitivity, 114 pcm less static positive
scram, is a sub-prompt rise to 10 P0 that the rods turn over. So the nominal sits ≤ ~110 pcm (≈ 0.2 β)
static above a no-excursion branch. This card runs each registered, buildable bracket **one at a time** from
the nominal through newton B4, to find which of them can switch the outcome.

Each member is a full re-conditioning, not a perturbation of the nominal:
1. the (27) Fig. II-9 axial inversion redone under the member's inputs (`tools/a8_axinvert.py`);
2. its POWER-CHAN for `U4_FLOW=prop`;
3. its band-B deck and t = 0 dump;
4. newton B4 to 7 s with `B4_CLAMP=1`.

The post-AZ-5 record is not used to weight or select members.

**Sources / inputs:** `sources/README.md` (brackets); PROGRESS (34)–(36) (gap 2 CPS worth: `U4_CPSB`; gap 3
void worth: `U4_VOIDB`); #44 (Karpan depths `sources/derived/karpan_vk_fig3_roddepth.txt`).

## Acceptance Criteria
- **Run 1 members** (from the nominal `…_rt9f0a8f` stem), each with peak P/P0 and time, E(7 s), max Eadia, failure-criterion masses, Kv at peak, and the static AZ-5 ramp peak (`tools/a8_ramp.py`):
  - **K:** Karpan depths (`U4_RODDEPTH`).
  - **VA:** void-worth bracket A (`U4_VOIDB=0`, DRAGON void worth 2.35 β against OpenMC-corrected 3.22 β).
  - **CA:** CPS-worth bracket A (`U4_CPSB=0`, DRAGON CPS worths against OpenMC-corrected).
- Each member classified as excursion or no excursion, with the static-ramp peak of each set against the 407–521 pcm interval that holds the threshold.
- **Not buildable yet**, recorded with what each needs:
  - rod speed (only 0.4 m/s is sourced; no bracket source);
  - B₄C density 1.7–2.3 and displacer graphite 1.50–1.73 g/cm³ (a CPS COMPO rebuild each);
  - the #33 TH items;
  - the sourced ~5 β void worth (#37: no construction reaches it).
- A statement for B5: which dimensions straddle the threshold, and so must be sampled densely there.

## Narrative
- 2026-11-11: Opened at the user's request after #41's ЛАР result; run 1 (K, VA, CA) launched overnight. (by @assistant)
- 2026-11-12: **Run 1 results.** Each member was refitted to Fig. II-9 and given its own POWER-CHAN, band-B deck and t = 0 dump, then run in newton B4 with `B4_CLAMP=1`. Script: session scratchpad `scan/run1.sh`. New derived files: `a8_fit_pchan_f11kv.txt`, `insag7_fig_II9_t0_axburn_fit_f11vA.txt`, `a8_fit_pchan_f11vA.txt`.

  | member | static ramp peak | peak P/P0 (t) | P > 10 P0 from | E | max Eadia | m(>100 / >160 / >240) | outcome |
  |---|---|---|---|---|---|---|---|
  | nominal `…_rt9f0a8f` | +521 pcm | 244.5 (5.15 s) | 3.38 s | 66.76 GJ (7 s) | 264 cal/g | 68.9 / 35.2 / 3.0 | excursion |
  | **K** Karpan depths `…pcae4d98…_rd603001ac_rt9f0a8f` | +485 pcm | 150.1 (5.63 s) | 3.65 s | 45.88 GJ (7 s) | 187 | 44.3 / 7.2 / 0 | excursion |
  | **VA** void bracket A `…pc09539f_dev_ax05f2bf…_cB4af83e_rt9f0a8f` | +521 pcm (by construction) | 109.3 (5.12 s) | 3.38 s | 37.91 GJ (6.93 s) | 156 | 27.9 / 0 / 0 | excursion |
  | ЛАР no displacer (#41 sensitivity) | +407 pcm | 10.05 (6.39 s) | — | 6.57 GJ (7 s) | 29 | 0 | **none** |

  - **Neither sourced bracket crosses the threshold.** Both shrink the excursion: K by −39 % in peak and −31 % in energy, VA by −55 % and −43 %. The ЛАР sensitivity, settled out of B5, is still the only input found that switches it off.
  - **The static ramp is blind to void worth.** `compo_voidB.py`'s correction is zero at and above 0.72 g/cm³, so VA's (27) refit and static ramp equal the nominal's to every digit (k 1.027323, rms 0.0192). That is by construction, not an error. VA differs only once the coolant voids: its rise matches the nominal to 3.38 s, then is damped. So "≤ ~110 pcm above the threshold" (#41, 2026-11-10) is a margin in **rod-ramp** units only. The dynamic threshold also moves with the void worth, and VA halves the peak without touching the ramp.
  - **VA stopped at 6.93 s** on a THMPH convergence failure in the newton TH: h = −354 kJ/kg, a state below 0 °C liquid. That is a solver defect, not physics; it is noted on #30. The peak (5.12 s) and the classification are unaffected.
  - **CA (`U4_CPSB=0`) is withdrawn as a member.** Gap 2 was a corrected **defect**, not a bracket: PROGRESS (35) found production DRAGON 17 % too strong on absorbers and 10 % too weak on displacers against OpenMC, the second method. The uncertainty left on f_ABS / f_DSP is not yet quantified here; it is the proper CPS-worth bracket. Tier B also refuses non-cB decks by design (`b4_coupled.jl:33`). Its static ramp is kept as a check only: +295 pcm peak (k 1.022941, refit rms 0.0194; its fit files are not kept). That agrees with PROGRESS (34): no surge before the correction.
  - **For B5:**
    - void worth (gap 3) and rod depths are continuous dimensions with large leverage on the size of the excursion (factor ~2 in peak), but within run 1 they do not decide whether it happens;
    - the remaining sourced bracket in the threshold direction is their combination;
    - the sourced ~5 β void worth lies on the other side of B and would enlarge the excursion.
  - **Next (run 2):** K + VA combined, one newton run; then the members listed as not buildable. (by @assistant)
