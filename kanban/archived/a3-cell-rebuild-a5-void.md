---
id: 2
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, sourcing]
---

# A3 lattice cell rebuilt on RBMK dimensions; A5 void coefficient vs burnup

Every RBMK lattice deck in the repo, including the one the audit had called legitimate, turned out to be a CANDU-6 bundle. On 2026-09-22 the cell was rebuilt on RBMK dimensions with `USS:` self-shielding and a self-verifying volume-fraction guardrail, and the A5 deck depleted it and swept coolant density. The result was a positive void coefficient rising with burnup; the "~4 β at discharge" magnitude and the 5 MWd/kg dip were both retracted the next day by the OpenMC cross-check.

**Sources:** PROGRESS header blockquote 2026-09-22 (2); section "A3 rebuild and A5 void coefficient — 2026-09-22"; retracted-claims entries in "Validated results". Key files: `Dragon/data/rbmk_cell_a3.x2m`, `Dragon/data/rbmk_a5_void.x2m`, `rbmk_proc/RbmkLib.c2m`, old `rbmk_cell_v3.x2m` / `rbmk_cell_v3_branch`, `twlup_proc/TCWU07.c2m`, `Ganlib/src/objstk.c:189`, `rep900_mco.x2m:409`, `rdragon`, `COMCAL.f:24`, `PROJECT_PLAN.md`.

## Outcome
- The claimed A5 "GAN parser" blocker was three syntax errors: `MakeBranchLib` is 13 characters against GANLIB's 12-character cap (renamed `MkBranchLib`); `DELETE LIBRARY` needed `X := DELETE: X ;`; `LINKED_LIST ALREADY EXISTS` had the same fix. A stale extensionless `data/rbmk_cell_v3_branch` shadowed the `.x2m` because `rdragon` copies the bare argument.
- The old deck then ran 7/7 branches and gave a void coefficient of **−183 to −621 pcm/%void** — wrong sign — because it was `TCWU07.c2m` resized: 37 pins in 4 rings, a 3.85 cm solid Zr "calandria tube" at 32.9 % of the cell, graphite 45.2 %, water 9.2 %, Zr at 4.3E-3 /b-cm (10× below metallic), no self-shielding, SPH passed into the group-form-factor slot and ignored (`NGFF 0`).
- A3 rebuilt from the Wikipedia RBMK article: 250 mm pitch, 114 mm bore, 18 rods of 13.6 mm OD, 11.5 mm pellets with 2 mm hole, 13 mm carrier, 2.0 wt% U-235. Materials consolidated into `RbmkLib.c2m` (the old deck's two `LIB:` copies disagreed on absolute vs relative coolant density). `USS:` added on a separate coarse tracking.
- **k∞ = 1.310172** (1.312816 as originally run with free-gas hydrogen; corrected 2026-09-23, card 4). Later superseded by geometry and library changes (cards 5–7).
- Guardrail: graphite 89.594 %, coolant 3.772 %, fuel 2.901 %, Zr 2.729 %, gas 1.004 %, cell 625.0001 cm². Negative control (graphite rings → Zr) drops graphite to 83.7 %, Zr to 8.65 %, and the deck aborts. The guardrail fires.
- A4 SPH: not applicable at cell level (`SPHDRV: INVALID NUMBER OF MACRO-REGIONS (9 1)`); `MERG COMP` preserves k∞ under reflective boundaries; SPH moved to core level.
- A5 (`EVO:` run for the first time, 16.7 MW/t, self-shielding redone per branch): full-void Δρ +82 (0), +193 (0.5), +103 (2), −11 (5), +304 (10), +986 (15), **+1957 pcm (20 MWd/kg) ≈ +4.08 β** at an assumed β_eff 0.0048.
- **Retracted 2026-09-23 (OpenMC cross-check, card 3):** the ~4 β match to the historically quoted figure was a coincidence produced by the free-gas hydrogen bug; OpenMC gives ~8 β (+4007 pcm) at 20 MWd/kg. The 5 MWd/kg dip is not physical (OpenMC +852 pcm there); it was later shown to be a 172-group artifact (card 7).
- The PROJECT_PLAN A5 gate of +2 to +5 pcm/%void was too low (full-void worth is several β, tens of pcm/%void); corrected in the plan.
- Open items left: pressure tube 88 × 4 vs 92 × 4 (resolved 09-24 (2), card 6), ring radii 1.60 / 3.10 inferred (resolved 09-24 (3), card 6), β_eff assumed (measured 09-23, card 5), no MULTICOMPO from the corrected cell (card 5).

## Narrative
- 2026-09-22: Took over a delegated agent's A5 report claiming a parse-time blocker and found it was three syntax errors plus a shadowing stale file. Fixing them let the old deck run, and it gave a negative void coefficient two orders of magnitude out — the mechanics worked, but the cell was not an RBMK. Measuring region volumes exposed the CANDU-6 cluster verbatim, including the deck the audit had called legitimate. (by @assistant)
- 2026-09-22: Rebuilt the cell on RBMK dimensions, cross-checked pitch/bore/density with a graphite-mass estimate (1763 t vs ~1700 t, 4 %), and added a volume-fraction guardrail with a verified negative control, the point being that this check would have caught the CANDU bundle in one run. Determined SPH cannot apply to a full-cell homogenisation, so the old "Stage 4 SPH blocker" was chasing a correction that step does not need. (by @assistant)
- 2026-09-22: Re-framed the A5 gate: the positive void coefficient is a high-burnup phenomenon needing Pu-239's 0.3 eV resonance, so depletion now precedes the gate. Got a positive, burnup-rising void worth reaching +1957 pcm at 20 MWd/kg and read it as ~4 β, matching the historical figure; the 5 MWd/kg dip was flagged as not understood and worth confirming. (by @assistant)
- 2026-09-23: Both specific claims retracted by the OpenMC cross-check: the ~4 β agreement came from free-gas hydrogen in a code that under-predicts the quantity throughout, and the dip failed confirmation. Sign and trend stood. (by @assistant)
