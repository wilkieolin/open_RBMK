---
id: 15
status: done
priority: Normal
blocked_by: []
tags: [tier-a, xenon, neutronics, burnup]
---

# A6b: the xenon level at 01:23, and binned xenon fields as a flattening agent

Measure what xenon is worth in the core, solve the 01:23 xenon level from the sourced power history instead of assuming it, and build the machinery to carry a per-channel xenon field. Equilibrium xenon turned out to be worth −2352 pcm. The 01:23 level is 1.039 × equilibrium (−92 pcm more), and it was rising steeply at the time. A binned-mixture field reduces chequerboard peaking 16 %. The field's shape barely depends on which field is used, but its reactivity cost does.

**Sources:** PROGRESS (15), (16); key files: `tools/a6b_xenon.py`, `gen_rbmk_unit4.py` (`U4_XENON`, `U4_XEBINS`, `U4_XERELAX`, `U4_XESTATE`, `U4_XEHIST`), COMPO `DEPL-CHAIN/DEPLETE-DECA`, `DEPL-CHAIN/FISSIONYIELD`, `ISOTOPESDENS`.

## Outcome
- Equilibrium Xe-135 is worth −2352 pcm (about −3.1 $). The power shape barely moves (MAX/AVG 1.5722 vs 1.5730).
- `MICRO` usage: `ALL` is required (`ONLY` discards the other isotopes), and `MICRO` must come last in `MIX`.
- Library constants are read back as 6.570 h / 9.140 h and γ 6.2805E-02 / 2.5610E-03. σφ₀ is calibrated from the stored equilibrium: 6.35E-05 /s = 3.0 λ_Xe.
- 01:23 level: Xe/Xe_eq = 1.039, worth −92 pcm (1.044059 → 1.043056). The quasi-static target is 1.502 × (≈ −1180 pcm), and the core was 8 % of the way there.
- Reference error caught by its own control: using the node instead of interpolating gave −49 pcm. Corrected, the control is +0.0 pcm, and the worth is linear (−92 measured vs −91 predicted).
- Bin machinery:
  - `U4_XEBINS=1` is byte-identical to the old deck. Four identical bins give a bit-identical k.
  - A padded/unpadded coordinate bug was found and now fails loudly.
- Level vs shape: a uniform +4.3 % costs −102 pcm with an identical shape. A same-mean field costs a further −84 pcm and lowers the peak 7.6 %.
- On the chequerboard with the 01:22:30 rods, a self-consistent field brings MAX/AVG from 2.9164 to 2.4600 (−16 %, −193 pcm). The undamped fixed point diverges; w = 0.35 converges in six passes.
- The 3200 MW equilibrium field gives MAX/AVG 2.4556 (−73 pcm). The shape matches the 01:23 field to 0.2 %, against the predicted 3.4× weaker flattening.
- **Later corrections:**
  - (17) showed the 01:23-field run (4730.9 kW, 2.4600) mixes a 200 MW poison with a 3200 MW normalisation. The equilibrium-field run is the valid one.
  - (31) found `xenon_at_0123` started every channel at core-average equilibrium, so the per-channel fields understated the spread. Their flattening numbers (4731 kW, 2.460) need re-measuring before they are quoted again.

## Narrative
- 2026-10-05 (15): First priced the stored equilibrium xenon nobody had measured: −2352 pcm.
  - Integrated the I/Xe pair over INSAG-7's power history with every constant read from the library. The only soft input is r = γ_Xe/γ_I, and the answer moves by 0.001 across it. The initial condition is exactly at rest by construction.
  - The 01:23 level is nearly equilibrium, but the slope matters: the core was early on a climb toward ~−1180 pcm while the inserted rods held −110 pcm.
  - Caught a −49 pcm reference error with a write-back no-op control.
  - Recorded INSAG-7's statement that no calculational studies of the field dynamics were made for that period. (by @assistant)
- 2026-10-05 (16): Built the binned-mixture field. Regressions passed before any physics.
  - Showed level and shape separate cleanly.
  - Xenon is the flattening agent (13) lacked, since high-power channels carry more poison.
  - Under-relaxation is physical, not a convenience, given the 9.14 h time constant.
  - Built the full-power equilibrium field in closed form; it reproduces the stored density exactly.
  - My 3.4× prediction was wrong: the flattening comes from the low-power valleys. The choice of field is worth 120 pcm on k and essentially nothing on the shape.
  - The chequerboard is still not operable. (by @assistant)
