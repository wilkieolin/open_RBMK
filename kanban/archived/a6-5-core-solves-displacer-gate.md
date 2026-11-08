---
id: 10
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, rods, sourcing]
---

# A6.5: the Unit 4 core solves, and gate A6.5 (the positive displacer)

Run the full DONJON chain on the sourced 1888-channel map inside the sourced graphite stack, with real cross sections, and answer gate A6.5: does inserting the displacer alone give positive reactivity with a bottom-skewed flux? The core solves, and the reflector question closes at 131 pcm. The displacer sweep turned out positive only when the axial flux is bottom-skewed, with its sign following the axial peak in both directions. That made xenon (A6b) and burnup placement (A6d) critical-path inputs for A8.

**Sources:** PROGRESS (4), (5); key files: `rbmk_unit4_core.don`, `gen_rbmk_unit4.py` (`stack(n)`), `tools/u4_leakage.sh`, `decks/Donjon/data/u4_leakage.txt`, `tools/u4_rods.sh`, `decks/Donjon/data/u4_rods.txt`, `_ACompo`, `_CCompoWAT`/`_CCompoABS`/`_CCompoDSP`, `_RCompo`.

## Outcome
- The core solves: k = 1.018278, at uniform burnup with rods withdrawn and no xenon. Run cost 8.1 s, 691 MB, 141 outer iterations.
- Stack counts close against sources: 2480 vs 2488 columns, 592 vs 600 reflector columns, and 436 vs 444 pure graphite columns. The face-connected outer ring comes out at exactly 156, [BEH96]'s cooled-channel count, with nothing fitted.
- Reflector worth is 131 pcm, and only 2.6 pcm leaks past it. A mirror at the core edge is worth 1111 pcm. Collapsing the rings onto one dataset moves k by 3.9 pcm, while misplacing the cooled ring moves it by 88–91 pcm. This closes Phase 1b's 7152 pcm as not propagating.
- Axial peaking is 2.78/1.90 = 1.46, against the bare cosine's 1.57.
- Channel peaking is 1.90 against a design ~1.4. The gap is attributed to the missing burnup flattening.
- Displacer and sweep:
  - The displacer is worth +2060 pcm against a water column.
  - The displacer-only sweep (`dsp`) is −175 pcm with a centre-peaked flux.
  - Imposing a tilt with the AZOC bank, the sweep goes +14 at K = 14, +125, and +177 at K = 13, then reverses to −321 when the peak returns to K = 18.
  - So the sweep turns positive only once the bottom is weighted ~3.2× the interior band.
- Insertion curve: −7049 pcm at 24 planes and −5095 fully in. The reversal depends on an unsourced 700 cm stroke.
- Absorber worths are lower bounds because of the A6.4 neighbour bias. The displacer is not biased by it.

## Narrative
- 2026-10-01 (4): Ran `GEO:` through `FLPOW:` on the sourced map with `TRIVAT: DUAL 1 1`.
  - Fixed the reflector at four rings from [D], with mixture 0 as virtual volume. k was bit-identical across padding values.
  - `USPLIT:` requires `NREFL + NFUEL` to equal the highest material index, so reflectors are numbered first and fuel last.
  - Measured the reflector at core level instead of in a strip: 131 pcm, which a diffusion reflector-saving estimate (~155 pcm) corroborates.
  - A 1.9 pcm "axial anomaly" was understood rather than chased: the axial reflectors are already present in every case.
  - Burnup is flat pending A6d. Rods, xenon and TH feedback are absent. (by @assistant)
- 2026-10-01 (5): Built the rod as a 43-plane stack: 5 m absorber, 1.25 m water, 4.5 m displacer. The withdrawn geometry fills the 7.00 m core exactly, which checks three sourced lengths.
  - The displacer-only sweep came out negative. The reason is geometric: the gain is in the low-flux bottom and the loss is inside the high-flux interior.
  - An AZOC bank stepped into the core made the sign follow the axial peak both ways, an internal consistency check.
  - Gate A6.5's mechanism is present and conditional exactly as the gate states. That puts A6b/A6d on A8's critical path.
  - Open items: the RR stroke, `DEVINI:`/`DSET:` devices for moving rods, and the 01:23 rod pattern. (by @assistant)
