---
id: 1
status: done
priority: Normal
blocked_by: []
tags: [tier-a, neutronics, infra, numerics]
---

# Audit of the earlier status and restart of Tier A

On 2026-09-22 the progress log was rewritten after an audit. The previous version reported Stages 1–3 complete and Stage 4 blocked on SPH; that status did not survive inspection, because most of the claimed validation traced to fabricated cross sections or misdiagnosed failures. The audit re-established what actually existed (toolchain, nuclear data, one genuine benchmark), named the root causes, and set the standing approach of verification against independent methods before any result is trusted.

**Sources:** PROGRESS header blockquote 2026-09-22 (1); sections "Objective", "Architecture (three tiers)", "Toolchain: OPERATIONAL", "Nuclear data: AVAILABLE", "Validated results" (retracted claims), "Current state of the RBMK decks", "Root causes", "Toolchain capability", "Performance", "Validation risk". Key files: `EVALUATION.md` (full audit), `TIER_A_WORKPLAN.md` (work order), `rbmk_cell_iaea_xs.dra`, `Donjon/data/iaea3d_fuelmap.x2m`, `twlup_proc/TCWU07.c2m`, `gen_rbmk_realistic.py`, `rbmk_core_3d_realistic.don`, `rbmk_core_3d_simple.don`, `quarantine/a5_candu_cell/`.

## Outcome
- Objective restated: a 3-D coupled neutronics/TH RBMK-1000 model driving a historically accurate mnemonic display (1661 channel outlet temperatures, 211 rod positions, in-core detectors); the accident scenario runs to fuel failure and stops.
- Three tiers: A offline physics (DRAGON5 → MULTICOMPO → DONJON5, the source of truth), B an online GPU diffusion/TH engine validated against A, C the mnemonic panel. DONJON cannot be the live engine (single-threaded, no GPU path, ~0.2–3 s per flux solve).
- Toolchain operational: DRAGON5 / DONJON5 / TRIVAC5 / GANLIB5 5.1.0 built with sequential `make`; compiled at `-O` with zero OpenMP directives in Trivac/Donjon.
- Nuclear data: APOLIB99 (ENDF/B-VIII.0r1) is **172 groups, not 99** despite its filename; it carries `NDEL 6` precursor data.
- Only genuine validated result: IAEA-3D benchmark k_eff = 1.028980 against 1.029069 (−8.9 pcm), kept as the standing regression test.
- Retracted by the audit: "RBMK cell k∞ = 1.030601" (a hand-typed `MAC:` block of IAEA PWR constants with νΣf raised 0.135→0.160, "tuned for k_inf ~1.03", graphite given negative implied absorption); "LMW 2-D kinetics benchmark passed" (cited file does not exist); "3-D core converges, k=0.054, 973 outers" (log shows max outer iterations reached, then `TEST FAILURE`); "Transient framework ready" (all five transient decks abort; `KINSOL:` had never run).
- The audit's own claim that `rbmk_cell_dlib99_v2.x2m` (k∞ = 1.050768) was the only legitimate RBMK result was itself wrong — it is a CANDU-6 bundle (retracted the same day, see card 2).
- Deck sprawl: ~86 `rbmk_cell_*` variants generated, ~10 ever ran, all on the same CANDU geometry; 2 of 19 DONJON RBMK decks ever produced a k_eff, both ≈ 0.05.
- Root causes, all fixable: (1) the lattice cell was never an RBMK (CANDU-6 cluster from `TCWU07.c2m`, Zr densities 10× low, no self-shielding); (2) units bug, `PITCH = 0.25 # meters` where `GEO:` wants cm, modelling a 12.25 cm × 12.25 cm × 7 cm core; (3) three input mistakes misread as DRAGON defects (missing `SEQ_BINARY`, a 13-character procedure name against GANLIB's 12, `DELETE X ;` instead of `X := DELETE: X ;`); (4) the right reference deck copied for the wrong thing (geometry instead of methodology).
- Tool-capability findings recorded for later tiers: transient `THM:` path is HEM-only (`THMTRS.f:157`); `MOVDEV:` broken for multi-part rods; `NEWMDV.f:92` skips rods with `LEVEL < 1e-4`; `XENON:` equilibrium only; no detector response model.
- Performance: `DUAL 3 3` on 49×49×28 took 729 s and did not converge; `MCFD 1` expected ~40× smaller problem. (A2 later measured 1 s, see card 4.)
- Validation risk: no open RBMK benchmark of IAEA-3D quality; the cited "Kozlowski RBMK benchmarks" appears to be a misattribution (that is the OECD/NEA PWR MOX/UO₂ benchmark).

## Narrative
- 2026-09-22: Audit of the prior status. The headline RBMK cell agreement (Δ = 8×10⁻⁷) was a tautology produced by a `MAC:` block tuned to the asserted value; the LMW benchmark file did not exist; the 3-D core "convergence" was a failed run; the transient framework had never executed. Decided to rewrite the log, move the audit to `EVALUATION.md`, and drive work from `TIER_A_WORKPLAN.md`. Confirmed what was real: a working 5.1.0 build, the 172-group APOLIB99 library (mislabelled as 99 groups), and the IAEA-3D benchmark at −8.9 pcm. (by @assistant)
- 2026-09-22: Root-cause analysis. The negative void coefficient came from a cell that was a CANDU-6 bundle, which nothing in the workflow could catch because no deck checked its own volume fractions; the fix was a rebuilt cell plus an in-deck guardrail (card 2). The 0.054 core k_eff was leakage from a 12 cm core caused by a metres/centimetres bug; `rbmk_core_3d_simple.don` gave 0.060 on the same physical size, confirming it. Three "DRAGON blockers" were ordinary input errors, each demonstrated correctly in a bundled reference deck. `TCWU07.c2m` was to be used for its methodology only (two-geometry self-shielding, void branches), never its geometry. (by @assistant)
- 2026-09-22: Validation-risk stance set. Twice the project had produced a confident, plausible, wrong result that passed every existing check, so "internally consistent" was declared insufficient. Checks put in place: in-deck volume fractions with a negative control, a graphite-mass check (1763 t vs published ~1700 t, 4 %), and an independent Monte Carlo cross-check (done next day, card 3). β_eff was flagged as needing to be a burnup curve from `NDEL 6`, not the assumed 0.0048. (by @assistant)
- 2026-09-23: Root cause 2 corrected in the record: the generator had already been fixed on 09-22 (`PITCH = 25.0 # cm`, 49×49×32, `MCFD 1`); the open item was running the corrected deck, which became A2 (card 4). OpenMC status recorded as working: a source build at `~/code/openmc` (v0.16.1-dev46), venv `.venv-openmc`, ENDF/B-VIII.0 and VIII.1 HDF5 data, VIII.1 chosen so the comparison isolates method from data. (by @assistant)
