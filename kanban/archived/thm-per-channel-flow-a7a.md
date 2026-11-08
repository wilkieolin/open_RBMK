---
id: 11
status: done
priority: Normal
blocked_by: []
tags: [tier-a, th, infra, sourcing]
---

# Phase 2b + A7a: `THM:` per-channel inlet flow, and one channel against operating data

Patch `THM:` so each of the 1661 fuel channels can have its own inlet velocity, then run the first comparison in the project against published operating data: a single channel against [D] p.95. The patch is invisible when unused and provably per-channel when used. The channel passes to the precision at which [D]'s own numbers are self-consistent. Two `THM:` defaults were found to be wrong for an RBMK, and the A7 `THM:` block was fixed apart from the flow distribution.

**Sources:** PROGRESS (6), (7); key files: `patches/0001-THM-per-channel-inlet-velocity.patch`, `tools/apply_patches.sh`, `tools/bootstrap.sh`, `tools/thm_chan_regress.sh`, `tools/thm_chan_check.sh`, `decks/Donjon/data/rbmk_thm_chan.x2m`, `decks/Donjon/data/gen_rbmk_a7a.py`, `tools/a7a_check.sh`, `decks/Donjon/data/a7a_check.txt`, `docs/report.html`.

## Outcome
- `THM:` accepts `SPEED CHAN <one value per channel>`. The main risk was `THMDRV` overwriting its `SPEED` argument, which is handled with a scratch copy.
- The patch lives in `patches/`, because `5.1/` is gitignored.
- Regression on `channel_mphy.x2m`: 2 597 833 comparable lines, 0 differences. The digest is `f9f3849d…` before and after the patch.
- Proof on four channels:
  - Scalar and uniform `CHAN` agree with delta = 0.000000e+00.
  - Graded `SPEED CHAN 4 6 10 12` moves max fuel T by 28.7 K, and per-channel temperatures fall monotonically (933.8 → 908.9 K).
  - Upstream's 1143.495 is reproduced at 1143.501.
- Transient `THM:` is HEM-only (`THMTRS.f:157`), so A7 must converge under `DFM 0`.
- A7a, model vs [D] p.95:

  | | model | [D] p.95 |
  |---|---|---|
  | exit quality | 16.50 % | 19.6 % |
  | T-out | 289.47 °C | 289.3 °C |
  | v-max | 14.78 m/s | 18.5 m/s |
  | centreline | 1315.8 °C | 2100 °C |

- 19.6 % lies outside the 15.29–17.75 % box that [D]'s own ranges allow. The model closes its energy balance to 1.2 %.
- Wrong defaults found:
  - Default Bowring `XFL` is not the thermodynamic quality, so use `SAHA`.
  - `SET-PARAM` addresses parameters by `P-NAME`, and LOCAL parameters need `SAME`/`CHAN`/`BUND`.
- Equivalent pitch: `area` (1.7639 cm) is the nominal, because hydraulic diameter reaches no compared quantity.
- The centreline gap is gap conductance. Bare helium conduction gives 2800 W/m²/K, and [D]'s centreline implies ≈1700, so HGAP is to be set explicitly.
- The A7 `THM:` block is `CLUSTER 1.7639e-2 18`, `SAHA`, `DFM 0`, with HGAP from the gap width.

## Narrative
- 2026-10-01 (6): The source survey showed the single-velocity limit lived only in the parser, so the patch is small.
  - Scratch copy: needed because `THMDRV` reassigns `SPEED` to the outlet velocity, which would silently feed Picard pass 2.
  - Backward compatibility: a pre-patch THM object falls back to scalar `STATE(4)`.
  - Patch infrastructure: canonical patch file, idempotent apply script, bootstrap step 3a, and a verified round trip.
  - Regression: a whole-listing digest. It first false-failed because the digest and the noise filter did not travel together; now they do. (by @assistant)
- 2026-10-01 (7): [D] p.95 gives an over-determined single-channel operating point, so power, flow and inlet were prescribed and the rest compared.
  - Outlet temperature only confirms saturation. Quality is the real test, and [D]'s 19.6 % is internally inconsistent by 8–10 %.
  - Found that Bowring's Π does not vanish at saturation, and that `SET-PARAM` uses `P-NAME`.
  - Ran both equivalent-pitch fits. The flow-area match is nominal at no penalty.
  - Swept HGAP and reconciled the centreline through two independent routes.
  - This narrows the report's "no comparison against measurement" gap for TH only. Neutronics still has none. (by @assistant)
