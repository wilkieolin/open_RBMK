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
