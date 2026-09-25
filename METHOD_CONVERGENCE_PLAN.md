# Converging DRAGON and OpenMC on the RBMK void effect

*(Paths are relative to the repository root. Evidence and numbers: `PROGRESS.md`, "Method gap:
hypothesis register — 2026-09-25".)*

**Audience: an implementing agent or a reviewer.** Phases run in order. Each has a **GATE**: do
not start the next phase until it passes. If a gate fails twice, stop and report. Don't
improvise, and don't move on.

## Why

Tier A needs a void reactivity it can defend. At the accident state (Unit 4 average burnup
10.9 MWd/kgU) the two codes give, for complete voiding of a single channel:

| | full-void worth | in dollars |
|---|---|---|
| DRAGON, production (172 groups) | ~+320 pcm | ~+0.6 $ |
| DRAGON, converged library (SHEM-361 + Zr self-shielded) | ~+1030 pcm | ~+1.96 $ |
| OpenMC | ~+1400 pcm | ~+2.7 $ |

## The rule this plan exists to enforce

**Neither code is right because its answer matches history.** "Unit 4 went prompt critical" is
a whole-core statement, made with that night's rod pattern; it is not a cell k∞, and it must
never be used to choose between codes. A value becomes trustworthy in one of two ways only:
- **verification**: two independent methods, each converged against itself, agree; or
- **validation**: a method reproduces a measurement it was not tuned to.

## Where we are (fresh fuel, identical compositions)

| | nominal k∞ gap (OpenMC − DRAGON) | full-void Δρ gap |
|---|---|---|
| production DRAGON | 705 pcm | 759 pcm |
| best-converged DRAGON (`rbmk_meth_best361`) | **191 pcm** | **188 pcm** |

The four-factor split (`openmc/fourfactor.py`) puts the whole disagreement in resonance escape,
carried by U-238 and Zr. Everything thermal agrees. Causes found so far, largest first:
1. the 172-group structure
2. Zr left at infinite dilution
3. the flat-flux spatial mesh
4. the graphite scattering table (small)
5. the boundary condition (small)

## Closure criteria (fixed now, before any more runs)

| | criterion |
|---|---|
| **Verified** at a state | nominal k∞ within **100 pcm**, and full-void Δρ within **2σ + 5 %** of OpenMC's value, with OpenMC's σ ≤ 20 pcm on the difference |
| **Accident state** | the two codes' full-void worth at 10 and 15 MWd/kgU within **10 %**, and on the same side of 1 $ |
| **Referenced** | both codes reproduce the MCNP / MCU void Δk of the RBMK Safety Review Project cell ([ALX98], Phase D0) within their spread plus the VIII.1-vs-B-VI data effect |
| **Validated** | both codes reproduce a measured void effect of a Kurchatov critical experiment (Phase D2), if its specifications can be obtained |

A residual that can't be closed is reported with its size and the mechanism it is attributed
to. It is **not** absorbed into a fudge factor.

---

## Phase A — close the fresh-fuel residual (~190 pcm)

Run every Phase A test on **both** cells: our hot cell (`rbmk_meth_*`), and the Safety Review
Project cell (`rbmk_srp94_*`, Phase D0). On the SRP cell, production DRAGON's void Δk is half of
MCNP/MCU's, so the residual there is proportionally larger and the test is sharper.

All DRAGON variants go through `decks/scripts/gen_meth.py`, one change against a control, with
the result tabulated by `openmc/method_table.py`. OpenMC runs through `openmc/method_study.py`,
seed-matched.

| Step | Hypothesis | What to do | Expected cost |
|---|---|---|---|
| A1 | **H5** isotropic scattering + transport correction in the collision-probability solver | Solve the flux with MOC (`MCCG:`) instead of `ASM:`/CP, with anisotropic scattering (`ANIS 2`, then 3) and `CTRA NONE`. Pattern: an upstream MCCG deck in `5.1/Dragon/data`. | a day |
| A2 | **H6** no radial self-shielding profile in the pellet | Split the pellet into 4 equal-volume rings, each its own mixture and self-shielding set (a `RbmkLibRim` + `RbmkGeoRim` pair) | a day |
| A3 | Group convergence, one more point | SHEM-370 (`draglibendfb8r1SHEM370_v5p1`, on disk): 361 → 370 must move k and Δρ by < 20 pcm | hour |
| A4 | Mesh convergence, one more point | `RbmkGeoFine` k = 8 on the SHEM-361 + Zr case; k 4 → 8 must move Δρ by < 20 pcm. If not, fit the 1/2/4/8 series and report the limit. | overnight |
| A5 | **H11** temperature interpolation | Both codes at library-grid temperatures (coolant 600, graphite 700 / 800, fuel 900 K) | hours |
| A6 | Leftover DRAGON approximations | (a) Nb-93 unshielded: the library lacks subgroup data (`LIBSUB: NOT ENOUGH DILUTIONS`), so bound it by removing Nb and noting the change. (b) Where DRAGON's library differs from what OpenMC reads, e.g. the graphite table, move OpenMC onto DRAGON's evaluation for the verification runs. | hours |
| A7 | Final OpenMC reference | Raise OpenMC's statistics until σ on the difference is ≤ 20 pcm, on DRAGON's graphite table (`c_Graphite_10p`) | hours |

Also re-run `openmc/fourfactor.py` on the best DRAGON case. Resonance escape p should now agree.
If it does and k still doesn't, the residual has moved into another factor, and that factor
names the next hypothesis.

**GATE A:** fresh fuel meets the "verified" criterion, **or** every remaining hypothesis is
tested and the residual is attributed and bounded.

## Phase B — the accident state (burnup)

| Step | What to do |
|---|---|
| B1 | **H10, depletion vs transport.** Export OpenMC's fuel isotopics at 10 MWd/kg (`openmc.deplete.Results.export_to_materials`) and run them in DRAGON at fixed composition, nominal and voided. The difference against DRAGON's own depleted branch is the depletion-trajectory effect. What remains is transport. |
| B2 | Four-factor split at 10 MWd/kg in both codes (`rates.py` on depleted fuel; `rbmk_rates`-style deck at burnup). Check whether Pu-239's 0.3 eV resonance introduces a thermal disagreement that fresh fuel couldn't show. |
| B3 | Repeat the Phase A best settings at 10 and 15 MWd/kg (`rbmk_meth_buzr361` is the start). |

**GATE B:** the accident-state criterion is met, or the residual is attributed and bounded.

## Phase C — make the converged settings the production settings

Only after Gates A and B. Standing rule 6 applies: fix the file everything calls.

| Step | What to do | Gate |
|---|---|---|
| C1 | `RbmkLib.c2m`: give Zr its self-shielding sets (as `RbmkLibZ`). Retire `RbmkLibZ` / `RbmkLibP` into comments or `quarantine/`. | `rbmk_cell_a3` guardrail passes; new k∞ recorded |
| C2 | Production library → SHEM-361: a `decks/common/` access hook, and `USS: ... PASS 2 MAXST 300` everywhere (drop `GRMIN 18`, a 172-group index) | h2otest, a3 and the A5 void deck reproduce the `rbmk_meth_*` values exactly |
| C3 | Spatial mesh: keep production `RbmkGeo` at every branch and carry the measured mesh correction as a documented additive term per state. Or, if Phase A finds a cheaper refinement (e.g. graphite rings only), adopt that. | the correction is documented and bounded |
| C4 | Rebuild the COMPO on the new settings (~3.5× the current CPU: about 4.5–5 h on the GB10, run alone). Round-trip ≤ 10 pcm, off-grid ≤ 30 pcm, β monotone. **Add burnup nodes at 7.5 and 12.5 MWd/kg** (1113 of Unit 4's 1659 assemblies sat at 12.3–13.7). | `openmc/a5b_interp_check.py` |
| C5 | Recompute the bracket (`extract_a5btab.py` → `void_bracket.py`) and the dollars table. **Variant B replaces DRAGON's void Δρ with OpenMC's** rather than scaling it (PROGRESS.md, 09-24 (4)). | the new table is recorded in PROGRESS.md |

**GATE C:** every production number regenerated, and every superseded one marked as superseded.

## Phase D — independent references

*Revised 2026-09-25 after reading [ALX98] and [PAR07] (`sources/README.md`).*

The Kurchatov critical experiments are **not** specified in [ALX98]. Its authors also say the
unknown graphite B/Cd impurity (≈ 1 % in k, tuned per code) keeps them from being a benchmark.
So the reference ladder is:

| Step | What to do |
|---|---|
| **D0** | **RBMK Safety Review Project single cell** ([ALX98] Tables 3–4): fully specified, with MCNP4A and MCU-3 answers. Transcribed in `openmc/srp94_common.py`; DRAGON decks `rbmk_srp94_*.x2m`. **Gate:** OpenMC reproduces MCNP/MCU's void Δk within their spread plus data effects (VIII.1 vs B-VI). The converged DRAGON is then held to the same bar. Status: OpenMC watered k∞ agrees (1.27655 vs 1.2778–1.2806). DRAGON void Δk is 2.46 on 172 groups, 3.45 on SHEM-361 + Zr, against 4.80–4.85. **This cell is now the primary test for Phase A.** |
| D1 | Obtain Behrens, Meyer, von Ehrenstein, *Validation of MCNP for RBMK criticality calculations*, Nucl. Technol. **114** (1996) 1–11. It is the published source of the critical-facility modelling detail and the impurity analysis. The 1993 Kuzmin and 1994 Bremen reports are unlikely to be obtainable. |
| D2 | If D1 specifies at least one flooded/voided pair, model it in both codes and compare the **void effect** (voided − watered), which is much less sensitive to the unknown impurity than absolute k. Also report the impurity sensitivity of the void effect by varying B-10 across the paper's range. |
| D3 | If a code misses a measured void effect beyond its uncertainty, return to Phase A for that code with the experiment as the reference. |

**GATE D:** D0 closed for the code Tier A relies on; D2 attempted if D1 yields specifications.

## Decisions this plan does not pre-empt
- **Which code feeds Tier B.** If A–D close, DRAGON (with the converged settings) stays the
  lattice code, because it produces the COMPO DONJON needs. If DRAGON can't be closed, the
  fallback is OpenMC-derived void branches applied through `MAC: ADD`: variant B, made the default.
- **Physical graphite porosity.** RBMK graphite at 1.65 g/cm³ is ~27 % porous. Only 10P is
  in DRAGON's library, while OpenMC has 30P. Moving to 30P is a data-fidelity question for after
  verification, not part of it.

## Files
- **Existing:**
  - `decks/scripts/gen_meth.py`: variant generator, with a burnup mode.
  - `decks/Dragon/data/rbmk_proc/RbmkGeoFine.c2m`, `RbmkLibZ.c2m`, `RbmkLibP.c2m`.
  - `openmc/method_study.py`, `method_table.py`, `fourfactor.py`, `rates.py`.
- **New:**
  - `RbmkLibRim.c2m` / `RbmkGeoRim.c2m` (A2).
  - An MCCG variant template in `gen_meth.py` (A1).
  - `openmc/isotopics_to_dragon.py` (B1).
  - `decks/common/shem361.access` promoted to production (C2).
