# RBMK-1000 Coupled Neutronics/TH Model — Progress Log

> **2026-09-22 (1): rewritten after an audit.** The previous version reported Stages 1–3
> complete and Stage 4 blocked on SPH. That status did not survive inspection — most of the
> claimed validation traced to fabricated cross sections or misdiagnosed failures. Full
> audit: `EVALUATION.md`. Work order: `TIER_A_WORKPLAN.md`.
>
> **2026-09-22 (2): A3 rebuilt, A5 gate passed.** Every RBMK lattice deck in the repo,
> including the one the audit above called legitimate, turned out to be a CANDU-6 bundle.
> The cell has been rebuilt on RBMK dimensions and now gives a positive void coefficient
> rising to ~4 β at discharge burnup *(the ~4 β figure was retracted the next day — see the
> 2026-09-23 entry)*. Current decks: `Dragon/data/rbmk_cell_a3.x2m`,
> `rbmk_a5_void.x2m`, `rbmk_proc/RbmkLib.c2m`. Details in the last section of this file.
>
> **2026-09-23: cross-checked against OpenMC. The A5 number did not survive.** OpenMC is now
> working (source build, ENDF/B-VIII.0 and VIII.1 data). The RBMK geometry is confirmed
> exactly. The positive void coefficient rising with burnup is confirmed. The *value* is not:
> OpenMC gives roughly **twice** DRAGON's void reactivity at every burnup, and the two codes
> differ by 12× at fresh fuel. A CANDU-6 control run in both codes agrees to 1.3 %, so this
> is an RBMK-specific method difference, not an OpenMC modelling error. One real bug was
> found in the deck. See "OpenMC cross-check" below.

> **2026-09-23 (2): Phase 0 corrections.** The free-gas hydrogen bug is fixed:
> `RbmkLib.c2m` now uses bound `H1_H2O`, and `rbmk_cell_a3.x2m` returns
> **k∞ = 1.310172**, matching the value `rbmk_h2otest.x2m` had already measured
> independently. `RbmkLibH.c2m` is retired (it was the fix in a second file); the old
> free-gas composition is preserved as `RbmkLibF.c2m` so the comparison stays
> reproducible. Two records were also found to be wrong in the other direction — the
> A2 units bug is already fixed in the generator, and the "not reachable from the deck"
> claim was overstated. Both corrected below. Next steps: `plans/` (A5b MULTICOMPO first).

> **2026-09-24 (2): cell geometry pinned to the designer's own monograph.** Dollezhal &
> Emelyanov (Atomizdat, 1980) settles three of the four open geometry questions. The
> pressure tube **88 × 4 is confirmed** — the Wikipedia 92 × 4 reading is wrong, closing a
> 10 % coolant-area ambiguity. The **carrier was wrong** (a 15 × 1.25 central tube with a
> solid 12 mm rod inside, not a 13 mm hollow tube) and the **clad was wrong** (13.5 × 0.9,
> not 13.6 × 0.825). Ring radii remain open and are deliberately unchanged. Coolant −3.2 %,
> Zr +9.3 %; graphite and fuel untouched. **k∞, the A5 void curve and the A5b MULTICOMPO are
> all superseded and must be re-run.** See the last section before "Standing rules".

> **2026-09-24 (3): the cell geometry is closed.** Eight sources the project had not used
> settle the remaining open items:
> - **Ring radii 1.60 / 3.10 confirmed**: rod circles ⌀32 / ⌀62 mm, in two independent sources.
> - **2 mm pellet hole confirmed**: three sources, plus a uranium-mass check against Unit 4's
>   114.7 kg U per assembly.
> - **Ring phase confirmed** off Dollezhal's own drawing.
> - **Graphite gas gap confirmed** as a valid idealisation.
> - **Burnup axis confirmed** as per tonne U.
> - **Clad OD refined 13.5 → 13.58**, the drawing nominal. ID 11.7 is unchanged.
>
> `rbmk_cell_a3.x2m` on the pinned draglib: **k∞ = 1.304123**, guardrail passed, DRAGON
> fractions equal the analytic ones.
>
> One finding reaches past geometry. **Unit 4 at the accident averaged 10.9 MWd/kgU, not 20.**
> The DRAGON/OpenMC bracket has been read at the wrong burnup. See "Cell geometry closed" below
> and `sources/README.md`.

> **2026-09-24 (4): re-baselined in both codes on the closed geometry. The bracket now
> straddles prompt criticality at the accident state.**
> - DRAGON: k∞ 1.304123, COMPO rebuilt (round trip 6.6 pcm, off-grid 26.5 pcm, now reproducible), β curve unchanged.
> - OpenMC: re-run on VIII.1.
> - The geometry fixes cut DRAGON's void worth at every burnup and left OpenMC's nearly unchanged, so the method gap widened.
> - At 10–15 MWd/kgU, where Unit 4 was, full voiding is +0.4–1.65 $ in DRAGON and +2.25–4.6 $ in OpenMC.
> - The ~1.9 multiplier held only at 20 MWd/kg.
> - Resolving the method gap moves ahead of A6. See "Re-baseline on the closed geometry" near the end.

> **2026-09-25: the method gap is mostly DRAGON not being converged, and the prompt-critical
> straddle is gone.** The four-factor split puts the whole DRAGON/OpenMC disagreement in
> resonance absorption (U-238 and Zr); everything thermal agrees.
> - Converging DRAGON against itself closes ~75 % of the fresh-fuel gap. The energy mesh
>   (172 → SHEM-361) dominates, then Zr self-shielding, then the spatial mesh.
> - On the converged library, full voiding at the Unit 4 average burnup is **≈ +1.96 $
>   (DRAGON) vs ≈ +2.7 $ (OpenMC)**: both above prompt critical, reached without using the
>   historical outcome.
> - DRAGON's 5 MWd/kg dip was a 172-group artifact.
> - See "Method gap: hypothesis register". The production COMPO is still on 172 groups and
>   now known to be unconverged.

> **2026-09-25 (2): third-party check.** On the RBMK Safety Review Project cell from Alexeev
> et al. (1998):
> - Our OpenMC reproduces MCNP and MCU (watered k∞ within 0.1–0.4 %).
> - Production DRAGON gives half their void effect (Δk 2.46 vs 4.80–4.85 %); SHEM-361 + Zr
>   self-shielding gives 3.45.
> - Parisi & D'Auria (2007) independently found DRAGON 21 % low against MCNP.
> - The Kurchatov critical experiments aren't specified in that paper, and are impurity-limited.
> - Local runs were stopped to move to the GB10; see the hand-off at the end of "Third-party
>   benchmark".

> **2026-09-25 (3): the void gap closes to within its criterion.**
> - **Hot cell, fresh fuel.** DRAGON on SHEM-361 + Zr self-shielding + 4× mesh + MOC with P1
>   scattering gives full-void Δρ **+763 vs OpenMC +821 ± 21** (inside 2σ + 5 %). At 0.35 g/cm³
>   it is +553 vs +533.
> - **SRP-1994 cell.** DRAGON is within 4 % of OpenMC (4.59 / 5.04 vs 4.77 / 5.24 %Δk); it was
>   42–48 % low in production.
> - **What's left.** Nominal k∞ is still 240 pcm apart (resonance escape); that residual is
>   attributed, not closed.
> - **Pellet-rim self-shielding.** The per-ring treatment is a USS artefact (−890 pcm, the wrong
>   direction), not missing physics.
> - **Depletion.** 60–70 % of the DRAGON/OpenMC depletion difference is a burnup-normalisation
>   convention: OpenMC's fission-Q mode books ~5 % more fissions per MWd than DRAGON.
> - **SRP cell, 8× mesh.** DRAGON gives 4.80 / 5.27 %Δk, matching OpenMC (4.77 / 5.24) and MCNP.
> - **Accident state (Gate B).** On matched burnup scales and identical fuel, DRAGON is within 6–9 %
>   of OpenMC. Full voiding at 10.9 MWd/kgU is **+2.4 to +2.75 $** across both codes. See "Phase A–B
>   on the GB10".

> **2026-09-26: Phase C done: production is on the converged library.**
> - **Library.** SHEM-361 with Zr self-shielded in `RbmkLib`; k∞ 1.313968.
> - **COMPO.** Rebuilt at 840 points with burnup nodes at 7.5 and 12.5. Round trip 6.7 pcm, off-grid
>   21 pcm, β monotone.
> - **Full-void worth at 10.9 MWd/kgU:** +1.95 $ (production COMPO), +2.42 $ (plus the measured
>   mesh/MOC correction), +2.72 $ (OpenMC matched).
> - **Depletion step size.** 5 MWd/kg steps overstated nominal k∞ by ~200–530 pcm; the void worth
>   was converged.
> - **What's next.** The method-convergence segment is closed. Next is A6 (CPS channel cells),
>   after a check-in. See "Phase C".

> **2026-09-26 (2): the plan is reordered.** The lattice gap is closed, but nothing whole-core is
> built or validated yet. New order: A6 (CPS cells) → A6b (Xe axis + COMPO rebuild) → A6c
> (Smolensk-3 start-up, the first measured core-level reference) → A6d (Unit 4 state at 01:22:30)
> → A7 → A8 → A9. See "Where the project stands".

> **2026-09-27: A6 — the CPS channel is built and verified, and homogenisation is where it
> breaks.** The rod, displacer and water sections exist in both codes from one transcription
> (`openmc/cps_common.py`), and every section worth is now measured against OpenMC.
> - **A6.2 passed.** The 3×3 supercell reproduces the single cell to +2.8 pcm (DRAGON), +2 (OpenMC).
> - **A6.3 missed its gate.** Production DRAGON is 9–17 % low on every section worth; converging it
>   (4× mesh, MOC P1) leaves 5–11 %. The residual is tabulated per state as the A′ correction
>   (+60 to +1107 pcm), not fitted.
> - **A6.4: the transport-to-diffusion step is exact; the neighbour data is not.** With all nine
>   cells from the CPS MULTICOMPO, DONJON reproduces DRAGON to ~1 pcm. With the eight fuel cells
>   taken from the *fuel* COMPO — what the core will actually do — the displacer and drained-channel
>   worths fall 7–10 % short. An infinite-lattice fuel cell is not a fuel cell next to a rod.
> - **A6.4b chosen:** an explicit equivalence on the rod cell. DRAGON's own normalisations were
>   measured out first; none of them closes it.
> - **A6d done, and it is the strongest result here.** Two independent digitisations — Dollezhal
>   Fig. 2.3 (Leningrad-2) and INSAG-7 Fig. II-6 (Unit 4 at 01:22:30) — register exactly, all 223
>   sites at one offset. Unit 4's channel map is now sourced rather than assumed: 1661 fuel,
>   211 rods, 12 ДКЭ(в), 4 start-up chambers, 1888 positions, each count closing against a
>   different source.
> - **Fuel COMPO rebuilt** on a corrected depletion grid (a dropped 500 MWd/t node had biased the
>   whole trajectory 45–75 pcm low). Gates: round trip 0.9 pcm, off-grid 23.9. The void bracket at
>   10.9 MWd/kgU is unchanged to within a few pcm: **+1.94 / +2.41 / +2.72 $**.
> - See "A6: the CPS channel".

## Objective

3-D spatially-resolved coupled neutronics/TH RBMK-1000 model, driving a historically
accurate **RBMK mnemonic display** (1661 channel outlet temperatures, 211 rod positions,
in-core detector readings). Accident scenario runs to **fuel failure** and stops.

---

## Architecture (three tiers)

| Tier | What | Status |
|---|---|---|
| **A — offline physics** | DRAGON5 lattice → MULTICOMPO → DONJON5 3-D steady + reference AZ-5 transient. Source of truth. | **In progress.** A3–A5b done and method-converged (SHEM-361 + Zr SS, 840-point COMPO, void bracket). A6 cells built and verified, homogenisation open (A6.4b); A6d channel map sourced. A6.5 core, A6b Xe, A6c Smolensk-3, A7–A9 to go. |
| **B — online engine** | Standalone 2-group nodal/FD diffusion + 6 precursor groups + 1-D per-channel TH on the GB10 GPU, reading Tier A cross sections, validated against Tier A. | Not started |
| **C — mnemonic panel** | Driven by Tier B. | Not started |

DONJON cannot be the live engine: single-threaded, no GPU path, ~0.2–3 s per flux solve.
It is the offline reference that makes Tier B trustworthy.

---

## Toolchain: OPERATIONAL

| Component | Version | Location | Status |
|-----------|---------|----------|--------|
| DRAGON5 | 5.1.0 | `5.1/Dragon` | Built |
| DONJON5 | 5.1.0 | `5.1/Donjon` | Built |
| TRIVAC5 / GANLIB5 | 5.1.0 | `install/bin/` | Built |

- Build: sequential `make` (parallel fails on Makefile target naming). Prefix `install/`.
- Platform dir is `Linux_<arch>`: `Linux_aarch64` on the GB10, `Linux_x86_64` on the WSL
  box. Results land in `5.1/<code>/Linux_<arch>/*.result`.
- **Compiled at `-O` (i.e. `-O1`)** and there are **zero OpenMP directives in Trivac/Donjon**
  — `-fopenmp` only activates Dragon's MOC/S_N lattice solvers. Rebuilding with
  `-O3 -march=native` is free performance.

## Nuclear data: AVAILABLE

| Library | Location | Notes |
|---|---|---|
| APOLIB99 (ENDF/B-VIII.0r1) | `libraries/l_endian/draglibendfb8r1Apolib99_v5p1` | **172 groups, not 99** despite the filename and every deck comment (`NGRO 172` in the run log). Carries `NDEL 6` precursor data. |
| ENDF/B-VIII.0 HDF5 | `libraries/hdf5/gal_xs_99g.h5` | unused so far |

Verified isotope names: `Zr90 Zr91 Zr92 Zr94 Zr96`, `C12_GR`, `Nb93`, `He4`.
Access via the per-deck `<name>.access` script, which symlinks `DLIB_99`.

---

> **2026-09-30: `KINSOL:` runs, and a hard time step costs 4.8× a quiet one.** The first time
> step the project has ever advanced. On the full `DUAL 1 1` core a severe transient costs
> **0.430 s/step** against 0.090 s/step with a frozen macrolib — so the easy measurement, which
> is the one a probe naturally produces, understates A8 five-fold. Budget: ~29 min of neutronics
> for a 4 s transient, ~4 h per scenario once the thermal-hydraulic Picard loop is included.
> Peak memory 105 MB. Tier B stays parallel rather than urgent. Two `KINSOL:` prerequisites are
> undocumented and were found in source: `OVERV` (`KINXSD.f:152`) and `UNIT` on `TRIVAA:`.
>
> **2026-09-30 (2): A6.4b is disproved, and the real cause of A6.4 is named.** The rod-cell
> equivalence cannot close the gate — not "is hard", cannot. Matching the rod's flux makes the
> worth error worse (VOID −14 % against −10 % at unit factors), matching its removal rate will
> not converge because a black absorber's reaction rate is nearly invariant to its own SPH
> factor, and sweeping the factors over ±20 % never brings the worth within −3.45 % of a gate
> that wants 1 %. The cause is not the rod: **the eight fuel cells around it differ from
> infinite-lattice fuel by ±3 % at zero burnup**, because the rod perturbs the spectrum across
> the whole 75 cm supercell. Fitting four factors to one worth would hit the gate and was not
> done. Carried as a measured one-signed bias, mechanism named.
>
> **2026-10-01: the environment effect is the SPH factor, and the eight-ring is the wrong
> handle on it.** A 5 x 5 supercell with two CPS channels, holding cells with 0, 1 and 2
> neighbours in one calculation. Raw homogenisation barely moves (<0.3 %); the 3-5 % is the
> **SPH factor**, which the core discards and which spans **1.00 to 1.56** across a realistic
> environment — far wider than the 3 x 3 can show, since all eight of its fuel cells touch the
> rod. The effect is **sub-additive** (increment ratios 0.64 / 0.55) and **not a function of the
> eight-ring count** (within-class spread 0.2471 against a 0.5590 total span); a
> distance-weighted scalar separates every class to 0.0003, so a continuous axis is viable but
> needs a validated descriptor. Weeks, not days. Two bugs in the read-out path were caught by a
> replicate check and corrected — `OUT: INTG` prints rates, not cross sections — which revises
> the per-cell numbers of the 09-30 entry but none of its k-based conclusions.

> **2026-10-01 (4): the core solves, and the reflector question closes.**
> `rbmk_unit4_core.don` runs `GEO:` → `USPLIT:` → `RESINI:` → `NCR:` ×2 → `MACINI:`
> → `TRIVAT: DUAL 1 1` → `TRIVAA:` → `FLUD:` → `FLPOW:` on the sourced 1888-channel
> map inside a sourced graphite stack, with real cross sections in every mixture —
> **k = 1.018278**, reported and not asserted, in 8.1 s. The stack boundary set from
> [D]'s column count independently reproduces [BEH96]'s **156** water-cooled
> reflector channels exactly. And the radial reflector turns out to be worth only
> **131 pcm** in this core with just 2.6 pcm leaking past it, which closes the open
> question Phase 1b left: the 7152 pcm homogenisation error measured on a
> 4-fuel/4-reflector strip does not propagate, because the whole band the dataset
> can move core k in is ~130 pcm wide. See "A6.5" below.

> **2026-10-01 (5): the positive displacer, and the condition it needs.**
> Gate A6.5 has a measured answer. The 4.5 m graphite displacer is worth
> **+2060 pcm** against a water column, and the first 1.25 m of rod travel — the
> displacer alone, absorber suppressed — is **−175 pcm** with a centre-peaked axial
> flux, because the graphite it gains at the core bottom sits in lower flux than the
> graphite it loses near the displacer's top. Tilt the flux down and it turns
> **positive, to +177 pcm**; tilt it back up and it goes negative again. The sign
> tracks the axial peak in both directions, so the gate's mechanism is in the model
> and conditional exactly as the gate words it. That also puts **A6b (xenon) and A6d
> (burnup placement)** on the critical path to A8 by measurement rather than
> preference: they are what supplies the tilt for real. See "Gate A6.5" below.

> **2026-10-01 (6): `THM:` takes per-channel flow.** `SPEED CHAN <one value per
> channel>` now works, routed through the `THMINP` reader that has handled that form
> for `NB-FUEL` since 2018. The drivers were already per-channel, so the patch is the
> parser, a stored vector, and the one scratch copy `THMDRV`'s self-overwrite demands.
> Proved **invisible when unused** — 2 597 833 comparable lines of upstream's
> `channel_mphy.x2m`, zero differences — and **provably per-channel when used**: fuel
> temperature falls monotonically from 933.8 K at 4 m/s to 908.9 K at 12 m/s across
> four channels. The patch lives in `patches/` because `5.1/` is gitignored, and
> `tools/apply_patches.sh` reapplies it from `bootstrap.sh`. See "Phase 2b" below.

> **2026-10-01 (7): the first comparison against measurement.** [D] p.95 gives one
> fuel channel's operating point in full, and it over-determines itself, so A7a
> prescribes power, flow and inlet state and compares the rest. Outlet temperature
> **289.47 °C against 289.3**; exit quality **16.50 % against a published 19.6 %** —
> and 19.6 % lies *outside* the box [D]'s own power and flow ranges allow (15.3–17.8 %),
> needing 3440 kW, or 27.9 t/h, or an inlet 8 K hotter. The model closes its own energy
> balance to 1.2 %, so the residual is the source's internal inconsistency, not ours.
> The centreline gap inverts to a pellet–clad conductance of ~1700 W/m²/K, which bare
> helium conduction across the sourced 100 µm gap independently puts at 2800 — making
> `THM:`'s own gap correlation the outlier. See "A7a" below.

> **2026-10-01 (8): the coupled core runs, and the cross-section table runs out.**
> The A7 Picard loop works — flux to power to thermal-hydraulics and back into the
> interpolation — and converges geometrically at r ≈ 0.40, putting the **Doppler
> feedback at −240 pcm** and the limit at **k = 1.036471**. Then it stops, and why it
> stops is the finding: the A5b MULTICOMPO's branch axes were built around a
> lattice-cell nominal state and a real core leaves the box at **both** ends — the
> subcooled inlet is 0.778 g/cm³ above a `DCA` axis that tops out at 0.72, and the ends
> of a low-power channel sit at 586 K below a `TF` floor of 600 K. Neither is a
> modelling error and neither has a deck-level workaround; both are one more value on
> an existing axis, and both now belong to the A6b rebuild. See "A7b" below.

> **2026-10-01 (9): A6b gets smaller, and the rebuild is running.** The xenon
> *axis* is not needed: Xe135 and I135 are already in the stored `MICR` list, and
> `NCRLIB.f:268` replaces a stored density with a user one before rebuilding the
> embedded macrolib — so a xenon field costs a `MICRO` clause from the core side and no
> rebuild, which is what the COMPO was deliberately built for. That leaves A6b's COMPO
> work as just the two axis widenings A7b found, and the **1152-point rebuild carrying
> them is running** (~10 h), with the working 840-point database preserved. Also
> measured so nobody repeats it: DRAGON's `-p` buys nothing here — 118.15 s at one
> thread against 118.18 s at eight, bit-identical. See "A6b scoped down" below.

> **2026-10-02 (10): the rebuild landed, and the gate had been watching the wrong
> axes.** 1152 points, 9 h 33 min, 208 MB — and the file grew +37.1 % against a
> tensor that grew +37.1 %. Round trip **1.3 pcm** over 12 nodes, now including the
> newly added `DCA` 0.80 and `TF` 530 that the old node set never touched. Off-grid
> **30.4 pcm**, 0.4 over gate — but running states off-grid in one axis at a time
> attributes **31.1 pcm of it to `TG` alone**, against 1.0 for `DCA` and 0.4 for `TF`,
> and the core pins `TG` on a node, so the realised error is ~1 pcm. `CUBIC` rejected
> on measurement. Two things the gate had never tested now are. **The `TG` axis stops
> below the temperature an operating RBMK reaches, and dk/dTG is +400–450 pcm per
> 100 K, so pinning it biases the core by ~+500 pcm — today's core k must not be
> quoted as an eigenvalue.** And **the burnup axis, interpolated in every core
> calculation ever run here, is off by +2099 pcm at 500 MWd/t**: the equilibrium
> xenon knee falls inside the first node interval. The core's own 10 900 is in the
> flat part (2–3 pcm), but [PAV] puts 10.4 % of the core at 1.2 MWd/kgU, mispriced by
> ~+1170 pcm each — a hard A6d blocker. See "The COMPO rebuild landed" below.
>
> **2026-10-02 (11): A7 converges; the thing that does not is a switch.** Last
> night's `ERMAXT` diagnosis was wrong — tightening it ten-fold changed nothing,
> because bit-identical k means bit-identical power and therefore a residual of
> exactly zero, so a plateau is a limit cycle. It is `K0`, the integer index of the
> boiling-onset node, set by the Saha-Zuber test at `THMH2O.f:383` and gating the
> two-phase block at `:147`, with `DTSUB` depending on heat flux so the switch sits
> inside the Picard loop. Proved by pinning the density: the same loop then falls to
> **0.031 K and 1.2e-5 g/cc with dk exactly zero**. k is **bit-identical at `RELAX`
> 1.0, 0.5 and 0.2**, so the loop now converges on the eigenvalue. Also fixed: the
> loop deleted `FLUX` on its last pass, so the power-shape block had **never run** —
> every A7 run died with kernel error 666 after printing its results. Converged
> feedback, exactly rather than extrapolated: Doppler **−227 pcm**, density
> **+306 pcm**, net **+80**. And the first power shape: peaking falls from 1.8289 to
> **1.5719**, peak channel 3517 → **3022 kW**. All four flow × feedback cases now run to
> convergence, which makes the **flow-distribution spread measurable for the first time:
> 59.4 pcm** between valving every channel to its own power and giving them all the core
> average — the honest cost of having no sourced total core flow, and small enough that A6d's
> flow state need not be perfect. The two density-pinned cases agree to 0.5 pcm, which is the
> check that the pin severs the flow-to-k path rather than merely damping it.

> **2026-10-03 (12): the burnup rebuild landed, and it says which numbers to trust.**
> 12 burnup nodes / 1728 points in 18.1 h; 1728/1728 rows, round trip **1.6 pcm**, and
> BU 0 unchanged at 1.313968, which is the invariant a changed depletion path had to
> respect. **The core's own burnup interval now interpolates to +8.7 pcm**, measured,
> on an axis that had never been tested at all — the A6d blocker is cleared where it
> matters. Refining the depletion grid also removed a **systematic 20–29 pcm** step
> error the previous "≤ 2.5 MWd/kg" grid still carried. Re-running A7 against the new
> table then gave the useful result: absolute k moved **−20 pcm** and every feedback
> moved **≤ 2 pcm** — Doppler −226, density +308, net +82, flow spread 59.7. A
> one-signed table error moves the eigenvalue and cancels out of differences, which is
> why the feedback decomposition has been stable across three tables while k has not,
> and why the `TG` pin matters for quoting k far more than for quoting feedbacks.
> **A gate point I chose badly:** the burnup gate sampled 250 MWd/t "where the curve is
> steepest", but [PAV]'s lowest group is 1200, so that 1341 pcm is the error of a state
> the model never evaluates — exactly the mistake the `TG` axis had been making, found
> one day earlier and then repeated. The interval that group does sit in was not
> sampled, so its improvement is real but unmeasured, and no number is claimed for it.

## Validated results

| Item | Result | Status |
|---|---|---|
| IAEA-3D benchmark, `Donjon/data/iaea3d_fuelmap.x2m` | k_eff = 1.028980 (ref 1.029069, **−8.9 pcm**) | ✅ Genuine. Standing regression test and the structural template for the core workflow. |
| RBMK lattice cell, `Dragon/data/rbmk_cell_a3.x2m` | **k∞ = 1.313968** (2026-09-26, SHEM-361 with Zr self-shielded, `RbmkLib`) | ✅ Geometry closed against sources, guardrail passed, DRAGON's fractions equal the analytic ones. **Superseded:** 1.304123 on the pinned 172-group draglib (2026-09-24 (3)); the +985 pcm is the converged library, not a geometry change. Lineage of the geometry corrections before that: 1.310172 → 1.308679 (library, −87) → 1.304717 (Dollezhal carrier and clad, −232) → 1.304123 (clad OD 13.58, −35). The value is post-hydrogen-fix (2026-09-23) and was matched independently by `rbmk_h2otest.x2m`. |
| Void coefficient vs burnup, `Dragon/data/rbmk_a5_void.x2m` + A5b COMPO | full void at the Unit 4 average burnup, 10.9 MWd/kgU: **+1024 pcm (+1.94 $) production, +1273 (+2.41 $) with the measured method correction, +1437 (+2.72 $) OpenMC matched**. At 15 MWd/kgU: +1666 / +1932 / +2254. 2026-09-27 | ✅ **Sign, trend and magnitude now agree between two codes and a third-party benchmark**, after the method-convergence segment; the 38 % spread fell to 13 %. Carried as a three-variant bracket (`openmc/void_bracket.py`), not a single number. Superseded: the 2026-09-24 (4) reading of +0.39 / +1.65 $ (DRAGON) against +2.25 / +4.60 $ (OpenMC), which came from the unconverged 172-group library. |
| CPS section worths, `openmc/cps_verify.py table` | 3×3 supercell, six states: converged DRAGON is **5–11 % low** against OpenMC on absorber, displacer and drained-channel worth (production 9–17 % low) | ⚠️ Measured against an independent method (rule 4) and **not closed**. The production-minus-converged difference is tabulated per state as the A′ correction, +60 to +1107 pcm. Two of twelve states still computing. |
| CPS homogenisation, `openmc/cps_verify.py a64` | DONJON on the homogenised supercell vs DRAGON: **~1 pcm with CPS-COMPO neighbours; −7 to −10 % on the displacer and drained channel with fuel-COMPO neighbours** | ⚠️ Gate A6.4 fails, cause identified: the homogenisation, SPH equivalence and solver are exact, the neighbour data is not. **A6.4b, the rod-cell equivalence proposed to close it, is disproved (2026-09-30):** the flux target makes the gate worse, the removal-rate target will not converge because a black absorber's reaction rate is nearly invariant to its own SPH factor, and a ±20 % sweep of the rod factors never brings the worth error within −3.45 %. The neighbour fuel constants differ by ±3 % **at zero burnup** — the rod perturbs the spectrum across the whole 75 cm supercell. Carried as a measured one-signed bias unless A8 proves sensitive. |
| Unit 4 channel map, `tools/build_unit4_map.py` | 1661 fuel + 211 rods + 12 ДКЭ(в) + 4 start-up chambers = 1888 positions; 47 rods inserted at 01:22:30, 4346 cm | ✅ Two independent digitisations register exactly (all 223 rod sites at one offset), and every count closes against a separate source — INSAG-7 pp. 43/103, [PAV] Table 1, [D] p. 57. The rod *types* of 32 sites remain an assumption, recorded per row. |
| Kinetics cost, `tools/kin_cost.sh` | `KINSOL:` on the 49×49×32 `DUAL 1 1` core: **0.430 s/step** under a severe transient, 0.090 s/step with a frozen macrolib; max RSS 105 MB | ✅ Per-step cost measured by *differencing* 10-step and 110-step runs, so the fixed setup cancels rather than being estimated. Self-checked two ways: the unperturbed transient holds power to 1.4e-4, and the severe one obeys the prompt-jump relation at step 1 (−0.20 $ for P/P₀ = 0.836 at β = 0.007219). On IAEA PWR constants — this is the solver, not the reactor. |
| CANDU-6 control, `Dragon/data/rbmk_candu.x2m` + `openmc/candu_cell.py` | DRAGON +1624 pcm vs OpenMC +1603 pcm full-void | ✅ Same geometry, library and compositions in both codes; **agree to 22 pcm (1.3 %)**. This is what validates the OpenMC model and localises the RBMK disagreement. |
| Cell volume fractions, analytic vs DRAGON tracking | graphite 89.5938 % vs 89.594 %, coolant 3.7721 % vs 3.772 %, fuel 2.9009 % vs 2.901 % | ✅ Method sound and independent of DRAGON (`openmc/volcheck.py`). **Current geometry (2026-09-24 (3))**: analytic graphite 89.5938, coolant 3.6037, fuel 2.9009, Zr 3.0313, gas 0.8702; DRAGON 89.594 / 3.604 / 2.901 / 3.031 / 0.870. Match to every printed digit again. |

**Retracted claims.** The first three were retracted by the audit; the fourth is a
retraction of the audit's own finding; the fifth is a retraction of the A5 result recorded
one day earlier in this same file.

- ~~"RBMK cell k∞ = 1.030601 (Δ = 8×10⁻⁷)"~~ — `rbmk_cell_iaea_xs.dra` contains no nuclear
  data. It is a hand-typed `MAC:` block of IAEA PWR constants with νΣf raised 0.135→0.160,
  carrying the comment *"tuned for k_inf ~1.03"*, asserted against 1.0306. Graphite was given
  negative implied absorption to hold k above 1. The agreement is a tautology.
- ~~"LMW 2-D kinetics benchmark passed"~~ — the cited file `Donjon/data/lmw_kinetics.x2m`
  **does not exist anywhere on the filesystem**. The only LMW artifact is the stock TRIVAC
  procedure `Trivac/data/Ktests_proc/lmw2D.c2m`, never run as part of this project.
- ~~"3-D core converges, k=0.054, 973 outers"~~ — log says
  `THE MAXIMUM NUMBER OF OUTER ITERATIONS IS REACHED` at 999/1000, then `TEST FAILURE`.
- ~~"Transient framework ready"~~ — all five transient decks abort. `KINSOL:` has never run.
  *(Update 2026-09-30: the retraction stands — those five decks still abort and were never
  fixed. But `KINSOL:` is no longer unrun: `rbmk_kin_probe`/`_ramp`/`_pert` advance 110 time
  steps on the full core. See "Phase 0 of the transient".)*
- ~~"`rbmk_cell_dlib99_v2.x2m`, k∞ = 1.050768, is the only legitimate RBMK physics result in
  the repo"~~ — **wrong, and this one was the audit's own error.** That deck carries the
  CANDU-6 cluster from `twlup_proc/TCWU07.c2m` verbatim: pin radii 0.612/0.654, ring radii
  1.4885 / 2.8755 / 4.3305, 37 pins in four rings, and the 6.5875 cm boundary. It is a CANDU
  bundle at RBMK pitch with 10×-under-dense zirconium and no self-shielding. The number was
  real in the sense that DRAGON computed it; it was not an RBMK.
- ~~"+1957 pcm (~4 β) at 20 MWd/kg — reproduces the historically quoted Chernobyl
  magnitude"~~ — **the agreement was a coincidence.** The deck specifies coolant hydrogen as
  bare `H1`, which is free-gas hydrogen; every bundled reference deck uses `H1_H2O`, the
  bound evaluation, and `DLIB_99` contains both. Correcting that alone raises the fresh-fuel
  full-void worth from +82 to +222 pcm. An independent OpenMC calculation of the same cell
  gives +4007 pcm (~8 β) at 20 MWd/kg. The trend is right; the number that matched history
  was produced by a coolant bug in a code that under-predicts this quantity throughout.

---

## Current state of the RBMK decks

| Area | State |
|---|---|
| Lattice cell, real data | ✅ `rbmk_cell_a3.x2m` — RBMK geometry, `USS:` self-shielded, self-verifying |
| Self-shielding on the cluster | ✅ `USS:` with `SUBG`, separate coarse SS tracking, per-ring sets |
| SPH homogenization | ✅ resolved — **not applicable** to a single-region cell homogenization; belongs at core level |
| 2-group condensation | ✅ `COND 0.625` (eV), `MERG COMP` and `MERG MIX` editions |
| Burnup (`EVO:`) | ✅ 0 → 20 MWd/kg at 16.7 MW/t |
| Void branches | ✅ three densities × seven burnup points |
| MULTICOMPO / SAPHYB / CPO | ⬜ exported once from the CANDU cell (quarantined); **not yet rebuilt** on the corrected cell |
| β_eff, λ from library | ⬜ still never extracted; `NDEL 6` is present and unused. Must be a **burnup curve**, not a scalar — β_eff falls as Pu-239 (β ≈ 0.0021) builds in |
| Doppler / graphite-temp branches | ⬜ axes exist in `RbmkLib` but only coolant density has been swept |
| CPS channel cells (B₄C, displacer, water) | ⬜ none |
| 3-D core | ⬜ generator **fixed** (`PITCH = 25.0 # cm`, 49×49×32, 1225 cm mesh, `MCFD 1`); the corrected deck has **never been run** — that is what A2 now is |
| Transient | ⬜ no time loop in any deck; `KINSOL:` never executed |
| TH coupling | ⬜ `THM:` never called from any RBMK deck |
| Detectors | ⬜ `DETINI:`/`DETECT:` never used |

Deck sprawl: ~86 `rbmk_cell_*` variants were generated, ~10 ever ran, and all of them
carried the same CANDU geometry. The superseded A3/A5 decks and the negative-void
MULTICOMPO are in `quarantine/a5_candu_cell/` with a README.
2 of 19 DONJON RBMK decks ever produced a k_eff; both ≈ 0.05 (the units bug).

---

## Root causes (all fixable, none are capability limits)

1. **The lattice cell was never an RBMK.** Every `rbmk_cell_*` deck inherited the CANDU-6
   cluster from `twlup_proc/TCWU07.c2m` — 37 pins in four rings, a 3.85 cm zirconium
   calandria tube, 45 % graphite where an RBMK has ~90 %. Compounded by zirconium number
   densities 10× below metallic Zr and no self-shielding anywhere. This is what produced the
   negative void coefficient, and nothing in the workflow could have caught it, because no
   deck ever checked its own volume fractions. **Fixed:** `rbmk_cell_a3.x2m` plus an in-deck
   guardrail that aborts if the cell is not an RBMK (negative control verified).

2. **Units bug in the core geometry.** `gen_rbmk_realistic.py` had `PITCH = 0.25  # meters`;
   DONJON `GEO:` mesh coordinates are **centimetres**. The modelled core was
   12.25 cm × 12.25 cm × 7 cm with VOID on all six faces. The XS used give k∞ = 1.12 —
   everything down to 0.054 was leakage. Cross-check: `rbmk_core_3d_simple.don` has a
   different mesh but the same physical size and identical XS → k_eff = 0.060.

   **Corrected 2026-09-23 (record, not code).** The generator was already fixed on 09-22:
   `gen_rbmk_realistic.py:6` reads `PITCH = 25.0  # cm`, `NX,NY,NZ = 49,49,32` with two
   axial reflector planes per end, the emitted deck meshes to 1225 cm, and the solver is
   already `MCFD 1` (`rbmk_core_3d_realistic.don:1691`). What is actually open is that
   **the corrected deck has never been run**: its `.result` is dated 09-19, three days
   older than the deck — standing rule 5, caught by its own rule. Two further live defects:
   `rbmk_core_3d_realistic.don:1710` carried `assertS ... 'K-EFFECTIVE' 1 1.123062`, and
   `gen_rbmk_donjon.py:10`, `gen_rbmk_geo.py:8`, `gen_rbmk_simple.py:6` still carry PITCH
   in metres.

   *Correction, same day:* I first read that assert as a target inherited from a
   differently-sized core, on the strength of the timestamp gap. **That was wrong.** Running
   the deck reproduces 1.123062 exactly, so it came from a run of this very deck — one that
   left no `.result` behind. The deck had therefore been run on 09-22; only the evidence was
   missing. Removing the assert was still right, for the other reason: the workplan requires
   A2 to *report* k_eff, not to expect one, and a target taken from the answer you got is not
   a gate. But "never been run" overstated what the timestamps could show.

3. **Errors misread as tool limitations.** Three separate "blockers" were ordinary input
   mistakes, each demonstrated correctly in a bundled reference deck: the missing
   `SEQ_BINARY` tracking declaration for SPH (`SPH.F:140`, `SPH.F:239`; pattern in
   `twimsE_proc/TCWE13.c2m`), a 13-character procedure name against GANLIB's 12-character
   limit (`objstk.c:189`), and `DELETE X ;` instead of `X := DELETE: X ;`
   (`rep900_mco.x2m:409`). Each was reported as a defect in DRAGON.

4. **The right reference deck was copied for the wrong thing.** `TCWU07.c2m` was used as a
   *geometry* template — which is precisely what should not have been copied, since a CANDU
   channel and an RBMK channel differ in exactly the moderator arrangement that matters.
   Its actually transferable content — `SHI:`/`USS:` self-shielding, the coarse-SS /
   refined-transport two-geometry pattern, and side-by-side void branches — was ignored.
   (The audit stated these decks "were never used." That was wrong: the geometry was taken
   verbatim and the methodology was not.)

---

## Toolchain capability (confirmed present; `USS:` and `EVO:` now in use, the rest not yet)

| Need | Module | Note |
|---|---|---|
| Space-time kinetics | `INIKIN:` / `KINSOL:` (in Trivac) | θ-method; no improved-quasi-static. `TRIVAA:` needs `UNIT`. |
| Transient TH | `THM:` → `THMTRS.f` | 1-D per channel — correct topology for RBMK pressure tubes |
| Void / boiling | `THMDFM.f90`, `BOWR`/`SAHA` | ⚠ **transient path is HEM-only**: `THMTRS.f:157` hardcodes `IDFM=0` and `THM.f:1102` passes neither `IPRES` nor `IDFM`. Drift-flux is steady-state only. |
| XS feedback | `NCR:` + `COMPO:` | up to 10 dimensions, linear or cubic Ceschino, plus `ADD` delta-sigma branches |
| Graphite displacer + absorber | `DEVINI:` / `DEVGET.f` | up to 10 contiguous rod **parts**, each with its own `DMIX` pair; volume-weighted partial insertion |
| Rod motion | `DSET:` (level) or `MOVDEV:` (speed) | ⚠ **`MOVDEV:` is broken for multi-part rods**: `DEVGET.f:246` stores `6*NPART` positions, `MOVPOS.f:159` / `MOVGRP.f:175` store only `6`, `NEWMDV.f:97` reads all `NPART`. No bundled deck calls `MOVDEV:`. Use `DSET:` with a computed level. |
| | | ⚠ `NEWMDV.f:92` skips any rod with `LEVEL < 1e-4` — cannot represent "displacer parked, absorber out", i.e. the pre-scram configuration. Put the parked displacer in the base fuel map and let the device carry only the difference. |
| Xenon | `XENON:` / `XENCAL.f` | **equilibrium only** — no iodine inventory, no post-shutdown build-up. Fine for a 4 s transient; matters for the pre-accident state. Add Xe as an explicit COMPO axis. |
| Detectors | `DETINI:` / `DETECT:` | probe positions + PARAB/SPLINE flux interpolation; **no detector response model** — add SPND lag downstream |
| Point kinetics | `PKINI:` / `PKINS:` / `PKIRHO.f` | Runge-Kutta + `ALPHA` feedback tables + `PTIME` rod law; ms/step but amplitude only |

**Reference decks to copy from:** `Dragon/data/rep900_mco.x2m` (multi-parameter COMPO;
also the canonical `X := DELETE: X ;` and procedure-per-branch idioms),
`Dragon/data/pincell_mco.x2m` (depletion + density branches + COMPO, the pattern `rbmk_a5_void.x2m` follows),
`Dragon/data/twimsE_proc/TCWE13.c2m` (NXT + `SEQ_BINARY` + SPH),
`Dragon/data/twlup_proc/TCWU07.c2m` — **methodology only.** Copy its two-geometry
self-shielding pattern and its void branches; do **not** copy its geometry. Taking the
CANDU cluster verbatim is the single error this project spent the most time on.
`Donjon/data/channel_mphy.x2m` (THM ↔ NCR ↔ KINSOL loop),
`Donjon/data/AFMtest.x2m` (3-D core + moving devices + kinetics, `MCFD 1`),
`Donjon/data/pulseTHM_0d.x2m` (PKINS + THM, adaptive dt).

---

## Performance

| Run | Discretization | Unknowns/group | FLUD CPU |
|---|---|---|---|
| `rbmk_core_3d_realistic.don` 49×49×28 | `DUAL 3 3` | 2,683,917 | **729 s** (did not converge) |
| `rbmk_core_3d_simple.don` 25×25×14 | `DUAL 3 3` | 484,425 | 23 s |

`DUAL 3 3` is ~40 unknowns per node. **`MCFD 1`** is the documented default (and what
`AFMtest_proc/Pcalflu.c2m:45` uses for a real 3-D core) at ~1 unknown per node — a ~40× smaller problem.
Expected with `MCFD 1` at 49×49×28, 2 groups: steady solve order 5–30 s, one `KINSOL:` step
order 0.2–3 s, a 20 s AZ-5 transient at Δt = 10 ms in tens of minutes to a few hours.
Also loosen `EPSOUT` from 1e-7 (absurd for a transient step) to 1e-5.

Memory is never a constraint: largest solve used ~1.4 GB against a ~110 GB budget.

---

## Validation risk

**This is the open problem.** There is no open RBMK benchmark of IAEA-3D quality. The
previously cited "Kozlowski RBMK benchmarks" appears to be a misattribution — Kozlowski &
Downar authored the OECD/NEA **PWR MOX/UO₂** transient benchmark. Verify before relying on it.

Twice now the project has produced a confident, plausible, wrong result — the tuned `MAC:`
block, and then a CANDU bundle reported as an RBMK channel — and both passed every check
that existed at the time. The corrected cell is internally consistent and reproduces the
right void behaviour, but *internally consistent* is exactly what the previous two were.

Checks now in place:

| Check | Status |
|---|---|
| In-deck volume fractions, with a verified negative control | ✅ `rbmk_cell_a3.x2m` |
| Graphite mass: 11.4 cm bore on 25 cm pitch, ~2000 bored columns, 1.65 g/cm³ → 1763 t vs published ~1700 t | ✅ agrees to 4 % |
| Void coefficient **sign and burnup trend** | ✅ confirmed independently by OpenMC |
| Void coefficient **magnitude** | ❌ **not confirmed — the two codes differ by 2–12×** |
| Independent Monte Carlo | ✅ done 2026-09-23, see below |
| Cell geometry, analytic vs DRAGON tracking volumes | ✅ match to every printed digit — but see below, the DRAGON side is now stale |
| Method validated on a non-RBMK lattice (CANDU-6, both codes) | ✅ agree to 22 pcm on the void coefficient |
| Cell dimensions against a primary design source | ✅ 2026-09-24, Dollezhal & Emelyanov (1980) — two corrections found, one confirmation |
| Every cell dimension sourced, with published clearances and mass as checks | ✅ 2026-09-24 (3) — see `sources/README.md`. Clad-to-wall gap 2.21 mm vs published 2.2; U per assembly 115.3 vs 114.7 kg |

**OpenMC status: WORKING.** The earlier note that conda-forge has no linux-aarch64 build was
correct, but a source build already existed at `~/code/openmc` (v0.16.1-dev46) with the
binary installed and only the Python bindings and data missing. Both are now in place:

- venv at `.venv-openmc` (Python 3.12), package installed from the source tree
- `~/nucdata/endfb-viii.0-hdf5` and `~/nucdata/endfb-viii.1-hdf5`, plus the VIII.0 chain
- **VIII.1 is the one to use** — `DLIB_99` is `draglibendfb8r1Apolib99_v5p1`, i.e. the same
  ENDF/B-VIII.1 evaluation, so the comparison isolates method rather than data
- run with `OPENMC_CROSS_SECTIONS=~/nucdata/endfb-viii.1-hdf5/cross_sections.xml`
- cost: ~80 k particles/s on 20 threads, **peak RSS 879 MB** for the fresh cell (1.6 GB
  depleted). No GPU use, no memory risk on the ~110 GB budget.

Open geometry questions that an MC cross-check would not settle either — these need a
primary source. **Items 1 and 3 were resolved 2026-09-24 against Dollezhal & Emelyanov
(1980); see "Cell geometry pinned to a primary source" below. Items 2 and 3b were resolved
2026-09-24 (3); see "Cell geometry closed" below. Item 4 was never geometry and was measured
on 2026-09-23 (A5b). No geometry question remains open.**

1. ~~**Pressure tube 88 × 4 mm vs 92 × 4 mm.**~~ **RESOLVED: 88 × 4 is correct**, stated
   explicitly as *outer* diameter 88 with a 4 mm wall [D p.54]. The deck already had it.
   The Wikipedia "8.4 cm ID" reading is wrong. Guardrail tightened to reject 92 × 4.
2. ~~**Fuel rod ring radii 1.60 / 3.10 cm**~~ **RESOLVED 2026-09-24 (3): correct as they
   were.** Rod circles ⌀32 / ⌀62 mm in [RU-A] and [LEI05]. The earlier measurement off
   fig 5.1 (inner 17–18 mm) was wrong. Refusing to substitute it was the right call.
3. ~~**Carrier rod wall** — only the 13 mm OD is sourced.~~ **RESOLVED, and the deck was
   wrong**: a 15 × 1.25 mm central tube with a solid 12 mm carrier rod inside [D p.11],
   not a 13 mm hollow tube. Corrected. The fuel clad was wrong too (13.5 × 0.9, not
   13.6 × 0.825).
3b. ~~**Pellet central hole (2 mm)**~~ **RESOLVED 2026-09-24 (3): the hole is real.**
   [RU-A], [LEI05], [BIB], plus the Unit 4 uranium-mass check.
4. ~~**β_eff**~~ **MEASURED 2026-09-23** as a burnup curve (A5b, below). It needs re-running
   on the current geometry, like everything downstream. Original note: assumed 0.0048 for the β-equivalent column. The library carries `NDEL 6`
   delayed data and it has never been extracted. It must come out as a **burnup curve**,
   not a scalar: β_eff falls as Pu-239 (β ≈ 0.0021) displaces U-235 (β ≈ 0.0065), so the
   void worth in dollars grows twice over with burnup — numerator up, denominator down.
   `TIER_A_WORKPLAN.md`'s gate of 0.0065–0.0075 is a fresh-fuel figure and is wrong for
   the state that matters. An independent check is cheap: OpenMC gives β_eff ≈ 1 − k_p/k
   by re-running with `settings.create_delayed_neutrons = False`.

---

## A3 rebuild and A5 void coefficient — 2026-09-22

The delegated agent's A5 report claimed a parse-time blocker in the GAN parser.
That diagnosis was wrong; the real problem was upstream in A3. Both are now fixed
and the cell reproduces RBMK void behaviour.

### The claimed A5 blocker was three syntax errors (retracted)

| Claimed | Actual cause |
|---|---|
| "GAN parser validates PROCEDURE names at parse time" | `MakeBranchLib` is **13 characters**; GANLIB caps names at 12 (`Ganlib/src/objstk.c:189`). Renaming to `MkBranchLib` cleared it. |
| "`rep900_mco.x2m` uses built-in PROCEDUREs" | False. `Mix_UOX_32` is a plain user `.c2m` in `rep900_mco_proc/`, copied by `rdragon:102` exactly like ours. |
| `DELETE LIBRARY` → not declared | Missing colon and missing assignment. The idiom is `X := DELETE: X ;` (`rep900_mco.x2m:409`). |
| `LINKED_LIST ALREADY EXISTS` | Same fix; the reference deck reassigns `LIBRARY` five times, deleting between each. |

Also: a stale extensionless `data/rbmk_cell_v3_branch` shadowed the `.x2m`, because
`rdragon` copies the **bare argument** (`rdragon:99`). Always pass `.x2m`.

After those fixes the old deck ran 7/7 branches and exported an 11 MB MULTICOMPO —
carrying a void coefficient of **−183 to −621 pcm/%void**. Wrong sign, two orders
of magnitude out. The mechanics worked; the cell was not an RBMK.

### Root cause: the lattice cell was a CANDU-6 bundle

`rbmk_cell_v3.x2m` was `twlup_proc/TCWU07.c2m` with the outer square resized — same
pin radii (0.6122/0.6540), same ring radii (1.4885/2.8755/4.3305), same mixture
numbering. Measured region volumes showed:

- a **3.85 cm solid zirconium "calandria tube"** at 32.9 % of the cell — an RBMK has
  graphite rings there, not a calandria tube
- **37 pins in 4 rings** (1+6+12+18), a CANDU-37 bundle; RBMK has **18 rods in 2 rings**
- graphite 45.2 % where it should be ~90 %; water 9.2 % where it should be ~3.8 %
- **every zirconium mixture at 4.3E-3 /b-cm, a factor of 10 below metallic Zr**
- **no self-shielding anywhere** — no `USS:`/`SHI:` in any file, so all resonance
  absorption was at infinite dilution
- SPH computed and discarded; the COMPO call passed the SPH edit into the *group
  form factor* slot (`COMCAL.f:24`), which the run confirms was ignored (`NGFF 0`)

### A3 rebuilt: `rbmk_cell_a3.x2m`

Geometry from the Wikipedia RBMK article (fetched 2026-09-22): 250 mm pitch,
114 mm graphite bore, graphite split rings, 18 rods of 13.6 mm OD with 11.5 mm
pellets and a 2 mm central hole, 13 mm carrier rod, 2.0 wt% U-235 (the April 1986
Chernobyl loading — the old deck was at 2.36 wt%, the later upgrade).

Independent confirmation of pitch, bore and graphite density: a 11.4 cm bore on a
25 cm pitch leaves 83.7 % block graphite; with ~2000 bored columns in the 14 m
stack that is ~86.8 % stack-average, and at 1.65 g/cm³ gives 1763 t against the
published ~1700 t. Agreement to 4 %.

Materials now live in one place, `rbmk_proc/RbmkLib.c2m`, shared by both decks —
the old deck kept two copies of the `LIB:` block and they disagreed about whether
the coolant-density argument was absolute or relative, which silently mislabelled
every point on the void axis.

Added `USS:` self-shielding (needs `SUBG` in `LIB:`) on a separate coarse tracking.

**Result: k∞ = 1.310172**, self-shielded, 2 groups, cut at 0.625 eV.
*(1.312816 as originally run, with free-gas hydrogen — corrected 2026-09-23.)*

### Volume-fraction guardrail (new, and the point of the exercise)

The deck now measures what it built and aborts if it is not an RBMK:

| | measured | design |
|---|---|---|
| cell area | 625.0001 cm² | 625.0 |
| graphite | 89.594 % | 89.6 |
| coolant | 3.772 % | 3.77 |
| fuel | 2.901 % | 2.90 |
| zirconium | 2.729 % | 2.73 |
| gas | 1.004 % | 1.00 |

Negative control run: replacing the graphite rings with zirconium (the CANDU
failure mode) drops graphite to 83.7 % and raises Zr to 8.65 %, and the deck
aborts with `FAIL: graphite fraction too low -- this is not an RBMK cell`.
**The guardrail fires.** This check costs nothing and would have caught the CANDU
bundle in one run instead of six branch calculations later.

### SPH: task A4 was aimed at the wrong place

`SPH: EDIHOM ...` → `SPHDRV: INVALID NUMBER OF MACRO-REGIONS (9 1)`. SPH needs one
homogenized region per tracking macro-region, so it **cannot** be applied to a
full-cell (`MERG COMP`) homogenization at all. For the DONJON model — one node per
channel — the `MERG COMP` edition is used directly and needs no SPH: flux-volume
weighting under reflective boundaries already preserves k∞ exactly. SPH belongs at
the **core** level, for the graphite reflector and control-rod cells. The original
"Stage 4 SPH blocker" was chasing a correction that step does not need.

### A5: void coefficient vs burnup — `rbmk_a5_void.x2m`

The A5 gate as written (positive void coefficient at zero burnup) tests the wrong
state. The RBMK's positive void coefficient is a high-burnup phenomenon — it needs
the Pu-239 inventory whose 0.3 eV fission resonance makes spectrum hardening
reactivity-positive. Depletion (`EVO:`, never previously run) now precedes the gate.

Specific power 16.7 MW/t (3200 MWth / 192 t U). Self-shielding redone at every
branch, since voiding hardens the spectrum into exactly the resonances `USS:` treats.

| BU (MWd/kg) | k∞ | Δρ at 51 % void | Δρ at 97 % void | ≈ β |
|---|---|---|---|---|
| 0.0 | 1.3128 | +226 pcm | +82 pcm | +0.17 |   <!-- pre-fix, free-gas H -->
| 0.5 | 1.2590 | +250 pcm | +193 pcm | +0.40 |
| 2.0 | 1.2368 | +202 pcm | +103 pcm | +0.21 |
| 5.0 | 1.1855 | +128 pcm | −11 pcm | −0.02 |
| 10.0 | 1.0987 | +200 pcm | +304 pcm | +0.63 |
| 15.0 | 1.0118 | +435 pcm | +986 pcm | +2.05 |
| 20.0 | 0.9282 | +787 pcm | **+1957 pcm** | **+4.08** |

(β-equivalent at β_eff ≈ 0.0048, assumed — β must still be taken from the library's
`NDEL 6` data, which has never been extracted.)

**Positive, and growing with burnup.** At design discharge burnup the full-void
worth is ~4 β, which is the figure historically quoted for Chernobyl conditions.
The near-zero dip around 5 MWd/kg is the U-235/Pu-239 crossover region; it looks
physical but is not yet understood in detail and is worth confirming.

> **SUPERSEDED 2026-09-23.** The sign and the growth with burnup hold up. The two
> specific claims in this paragraph do not. OpenMC gives ~8 β at 20 MWd/kg, not ~4,
> so the match to the historical figure was a coincidence produced by the free-gas
> hydrogen bug. And the 5 MWd/kg dip is *not* physical — it was worth confirming, it
> was confirmed, and it failed: OpenMC gives +852 pcm there, not −10. See the OpenMC
> cross-check section.

**The A5 gate in `PROJECT_PLAN.md` said +2 to +5 pcm/%void. That number was mine and
it was too low** — the RBMK full-void worth is several β, i.e. tens of pcm/%void.
Corrected in the plan.

### What this does not yet establish

*(Superseded in part by the OpenMC cross-check below — the first bullet is now done, and it
overturned the A5 magnitude.)*

- ~~**No independent cross-check.**~~ Done 2026-09-23. It confirmed the geometry and the
  void trend and contradicted the magnitude by ~2×. See "OpenMC cross-check".
- **Pressure tube dimension unresolved**: 88 × 4 mm used; the source states 8.4 cm ID
  (i.e. 92 × 4). Changes coolant area by 10 %. One constant in `rbmk_cell_a3.x2m`.
- **Fuel rod ring radii (1.60 / 3.10 cm) are inferred**, not sourced.
- Single cell, no absorber, no leakage. Core void coefficient depends strongly on
  rods inserted (the ORM) — that is A6.
- β_eff still assumed rather than taken from the library.
- No MULTICOMPO exported yet from the corrected cell.

### Status

| Task | Was | Now |
|---|---|---|
| A3 lattice cell | "done" — was a CANDU bundle | **rebuilt, self-verifying, k∞ = 1.310172** (1.3128 before the hydrogen fix) |
| A4 SPH | "blocked", then "done" but discarded | **not applicable at cell level** — moved to core level |
| A5 void gate | "blocked" by a 13-character name | **sign and trend pass; magnitude contradicted by OpenMC (2026-09-23)** |
| A5 MULTICOMPO export | exported from the wrong cell | to redo on the corrected cell — and see the cross-check first |

---

## OpenMC cross-check — 2026-09-23

The first independent check of any RBMK physics in this project. Method: rebuild the same
cell in OpenMC from the *same* number densities and dimensions the DRAGON decks use, run it
in continuous energy on the same ENDF/B-VIII.1 evaluation, and compare. Files under
`openmc/`: `rbmk_cell.py`, `volcheck.py`, `rates.py`, `deplete_void.py`, `compare_bu.py`,
`candu_common.py`, `candu_cell.py`.

### What was confirmed

**The geometry is right.** `openmc/volcheck.py` computes the cell volume fractions
analytically, with no DRAGON involvement, and they match DRAGON's `MIXTURESVOL` to every
printed digit: graphite 89.5938 vs 89.594 %, coolant 3.7721 vs 3.772 %, fuel 2.9009 vs
2.901 %, Zr 2.7292 vs 2.729 %, gas 1.0040 vs 1.004 %. All 18 rod clearances are positive
(1.4–2.7 mm). The implied heavy-metal density is 9.167 g/cm³ — exactly 10.4 g/cm³ UO₂.

**The positive void coefficient rising with burnup is real.** Both codes give it, in both
sign and trend, over the whole burnup range.

### What was not confirmed: the magnitude

Full-void reactivity (dca 0.72 → 0.02 g/cm³):

| BU (MWd/t) | OpenMC | DRAGON | ratio |
|---|---|---|---|
| 0 | +1030 ± 66 | +82 | 12.5× |
| 2000 | +919 ± 81 | +103 | 9.0× |
| 5000 | +852 ± 79 | **−10** | sign differs |
| 10000 | +1473 ± 92 | +303 | 4.9× |
| 15000 | +2650 ± 121 | +985 | 2.7× |
| **20000** | **+4007 ± 117** | **+1951** | **2.1×** |

At 20 MWd/kg that is **~8 β vs ~4 β** (β = 0.0048 assumed, same for both, so the ratio is
unaffected). DRAGON's dip to −10 pcm at 5000 MWd/t is not reproduced at all.

A dedicated high-statistics fresh-fuel sweep (100 M active particles/point) gives the same
picture more precisely: k∞ = 1.319690 ± 0.000139 nominal, void +578 pcm at 51.4 % and
+912 pcm at 97.2 %, against DRAGON's +264 and +222 with bound hydrogen.

### The one real bug: free-gas coolant hydrogen

`rbmk_proc/RbmkLib.c2m` specifies coolant hydrogen as bare `H1`. That is **free-gas**
hydrogen with no bound-water thermal scattering. Every bundled reference deck in the
distribution (`twlup_proc/`, `rep900_mco_proc/`) uses `H1_H2O`, and `DLIB_99` contains both.
Free-gas hydrogen overstates water's moderating power, which suppresses the positive void
coefficient — the right direction, but only part of the size.

Measured with `rbmk_h2otest.x2m` (both treatments, nothing else changed; the free-gas branch
reproduces `rbmk_a5_void.x2m` exactly, which validates the test):

| | k∞ nominal | void 51.4 % | void 97.2 % |
|---|---|---|---|
| `H1` free gas (as written) | 1.312816 | +226 | +82 |
| `H1_H2O` bound | 1.310172 | +264 | +222 |

**FIXED 2026-09-23.** `RbmkLib.c2m:44` now reads `H1_H2O = H1_H2O <<nH1>>`, and
`rbmk_cell_a3.x2m` re-run from a deleted `.result` returns **k∞ = 1.310172** — the value
the table above had already measured independently, so this is a regression check rather
than a new claim. The volume-fraction guardrail still passes (89.594 / 3.772 / 2.901 %).

`RbmkLibH.c2m` is **retired**: keeping the fix in a second file was the duplication that
let A3 and A5 keep running the wrong composition for a day. There is one source of truth
again. The old free-gas composition is preserved as `RbmkLibF.c2m`, marked do-not-use,
solely so `rbmk_h2otest.x2m` still reproduces this comparison; every other diagnostic deck
now calls `RbmkLib`. `RbmkLibN`/`RbmkLibW` remain, with their headers corrected to say what
they actually vary (`CTRA NONE` / `CTRA WIMS`, not the hydrogen treatment).

**Everything computed with DRAGON before this date used free-gas hydrogen**, including the
A5 void-vs-burnup table below and the DRAGON column of the OpenMC comparison. Those numbers
have not been re-run; the ~+140 pcm correction at full void is a floor on how much they
move, and the direction is toward OpenMC.

### Everything else was eliminated by measurement

| candidate | verdict |
|---|---|
| geometry, composition | match to 4+ digits — not it |
| nuclear data VIII.0 vs VIII.1 | 37 pcm on k∞ — not it |
| `GRMIN 18` vs library default | **bit-identical** — not a bug, contrary to first suspicion |
| `USS:` options (`TRAN PASS 4 NOCO`) | < 0.5 pcm — not it |
| transport correction `CTRA APOL`→`NONE`/`WIMS` | +76 pcm — real but small |
| free-gas `H1` | +140 pcm — real, 17 % of the gap |
| group structure (SHEM-361) | **untestable** — `USS:` will not converge on this cell at 361 groups under any option tried |

Running account of the fresh-fuel full-void worth: +82 (as written) → +222 (bound H) → +299
(CTRA NONE) → OpenMC +912. **614 pcm, 74 % of the gap, was not reached by anything tested.**

> **Qualified 2026-09-23.** The original wording — "not reachable from the deck" — claimed
> more than the evidence. Every candidate in the table above is a **data or library**
> option. Nothing tested discretization or self-shielding geometry, and four such knobs are
> untested, all of which bite harder in a voided channel than a flooded one, which is the
> signature this disagreement has:
>
> - `USS:` runs on the **unsplit** geometry `GEOSS`, so the pellet is flat — there is no
>   radial self-shielding profile. Splitting the pellet for self-shielding is standard
>   practice and is worth hundreds of pcm.
> - Tracking is coarse: `TISO 8 15.0` for self-shielding, `TISO 15 30.0` for flux, with
>   `SPLITR 4 1 1 2 6`. A voided channel is nearly transparent, and flat-flux collision
>   probability on coarse regions gets streaming wrong exactly there.
> - Every Zr isotope in MIX 2/8/9 is at **infinite dilution** — no self-shielding set.
>   That overestimates Zr resonance absorption, and the error grows as voiding pushes flux
>   into those resonances. Right direction; probably small (Zr RI ~1 b vs U-238 ~275 b).
> - `ANIS 2` (P1) only.
>
> The highest-information test is none of these: a **172-group spectrum and per-nuclide
> reaction-rate comparison** against OpenMC. The 2-group comparison cannot see the cause.
> Both codes agree the thermal fraction goes 53.0 → 46.3 % yet disagree on the *sign* of the
> U-235 production change, so the difference is in spectrum *shape* — most likely 0.2–5 eV,
> where U-235 has low-lying resonances and, at burnup, Pu-239 has its 0.3 eV resonance.
>
> **Deferred by decision**, not by impossibility. The trigger to pick it up is A8 showing
> that the two bracketed cross-section sets give materially different transients.

### Where the disagreement actually lives

k = ν-fission / absorption, so the void effect decomposes exactly. Of the 0.880 pp
difference in the k-ratio on voiding, ν-fission contributes +0.906 pp and absorption −0.026.
Splitting the production term by nuclide:

| | share | DRAGON | OpenMC | diff |
|---|---|---|---|---|
| U-235 | 0.969 | −0.200 pp | +0.746 pp | **+0.946** |
| U-238 | 0.031 | +0.494 pp | +0.452 pp | −0.042 |

**The entire disagreement is U-235 fission production under spectral hardening.** When the
coolant goes, DRAGON says U-235 production *falls* 0.20 %; OpenMC says it *rises* 0.75 %.
Both codes harden the spectrum identically (thermal flux fraction 53.0 → 46.3 %); they
disagree on whether the epithermal U-235 fission gain beats the thermal loss. Since U-235 is
97 % of production, that one sign disagreement is the whole void coefficient.

Why this is so sensitive: voiding removes 4.9 % of all absorption with the water (worth
+3793 pcm on its own), and U-238 resonance capture grows back nearly all of it — total
absorption moves only 1.000477 → 1.000737. **The void coefficient is a few-hundred-pcm
residual between ~3800 pcm terms.** A 20 % method difference in the cancellation becomes a
4× difference in the answer.

### The CANDU-6 control — why the OpenMC model can be trusted

The obvious objection is that the OpenMC model is simply wrong. `twlup_proc/TCWU07.c2m` is
the bundled CANDU-6 cell: cluster-in-channel geometry, non-light-water moderator, low
enrichment, positive void coefficient — the same *kind* of problem, different reactor. It was
run in both codes on `DLIB_99`, with compositions generated for both from one source
(`openmc/candu_common.py` → `rbmk_proc/CanduLib.c2m`) so a transcription error cancels.

| | DRAGON | OpenMC | diff |
|---|---|---|---|
| k∞ nominal | 1.124669 | 1.125691 | +81 pcm |
| k∞ voided | 1.145597 | 1.146371 | +59 pcm |
| **void reactivity** | **+1624** | **+1603** | **−22 pcm (−1.3 %)** |

Compare the RBMK: +550 pcm on k∞ and +690 pcm (+310 %) on the void coefficient. The same
OpenMC methodology reproduces DRAGON's CANDU void coefficient to 1.3 %. **The RBMK
disagreement is specific to the RBMK lattice**, not an artifact of the comparison.

### Caveats on this cross-check

- **The depletion trajectories diverge.** OpenMC k∞ is +268 pcm above DRAGON at 5000 MWd/t
  but −2084 pcm below at 20000. Different chains, fission yields and Q-value normalisation,
  and OpenMC used the VIII.0 chain (no VIII.1 chain is published) with VIII.1 transport data.
  So at discharge the two codes are not at the same core state, and the 2.1× ratio there is
  less clean than the 12.5× at fresh fuel, where compositions are identical by construction.
- **Neither code is established as right.** The CANDU control shows OpenMC is not
  misconfigured, which makes DRAGON the more likely source of the RBMK error, but that is an
  inference, not a measurement. Settling it needs a third code or an experiment.
- β_eff is still assumed 0.0048, not extracted from the library's `NDEL 6` data.
- Single cell, no absorbers, no leakage. The *core* void coefficient depends strongly on rod
  insertion (the ORM) — that is A6, and it is where the accident conditions actually live.
- The steam at 0.02 g/cm³ is treated with liquid-water thermal scattering in both codes
  (`H1_H2O` / `c_H_in_H2O`). Shared approximation, cancels in the comparison, wrong in both.


---

## A5b — the MULTICOMPO — 2026-09-23

`Dragon/data/rbmk_a5b_compo.x2m` → `Dragon/compo/_ACompo`.

**This closes the structural gap.** Until now nothing in the project had ever written cross
sections to disk: every good cell calculation left its result in an in-memory LCM directory
that `END:` discarded, and the DONJON core decks ran on generic IAEA 2-group PWR constants.
The lattice work and the core work were not connected at all.

### Axes

| axis | type | values |
|---|---|---|
| `burnup` | `IRRA` | 0, 2, 5, 10, 15, 20 MWd/kg at 16.7 MW/t |
| `DCA` | `VALU REAL` | 0.72, 0.60, 0.45, 0.30, 0.15, 0.05, 0.02 g/cm³ — the void axis |
| `TF` | `TEMP LIBRARY 6` | 600, 900, 1200, 1500, 2000 K — Doppler |
| `TG` | `TEMP LIBRARY 5` | 500, 750, 900 K — graphite is 89.6 % of the cell |

Full tensor product: **630 branch points**, each a fresh `LIB:` → isotopic restore → `USS:`
→ `ASM:` → `FLU:` → `EDI:` → `COMPO:`. Self-shielding is redone at every point, which is not
optional: voiding hardens the spectrum into the U-238 resonances, which is exactly where
self-shielding acts.

Xe is deliberately **not** an axis yet. `XENON:` in DONJON gives equilibrium xenon only, so an
explicit Xe axis is needed for the ORM story, but it multiplies the grid by ~4. That is
A5b.2, after the four-axis file is proven in DONJON.

### The gate is the round trip, not the file

"A COMPO exists on disk" is not evidence of anything. `Donjon/data/rbmk_a5b_verify.don` closes
the loop: it reads `_ACompo`, interpolates at an exact grid point with `NCR:`, and solves a
single homogeneous 25 cm cube with reflective boundaries on all six faces — no leakage, so the
diffusion eigenvalue reduces exactly to k∞.

| | k∞ |
|---|---|
| DRAGON, 172-group transport | 1.310173 |
| DONJON, via COMPO → `NCR:` → `TRIVAA:` → `FLUD:` | **1.310166** |
| difference | **0.4 pcm** |

Condensation, homogenisation, the on-disk database and the interpolation together lose under
half a pcm **at this one point**. That is the corner of the grid and it turned out to be the
best case by a factor of 16 — see the eight-node sweep below, where the worst case is 6.4 pcm.
Writing this deck **before** the long run is what caught the two defects below; both would
otherwise have surfaced after two hours of CPU as an unusable artifact.

### Two non-obvious requirements, both found by the verification deck

1. **`EDI: ... GOLVER` is not sufficient to get diffusion coefficients into a COMPO.**
   `EDIPXS.f:344` writes a `DIFF` block under `GOLVER`, but the state-vector flag that
   `COMPO:` checks is set only under a *leakage model* (`EDIPXS.f:413-419` sets `IDATA(9)`;
   `COMACR.f:91,169` reads it). So with `GOLVER` alone the coefficients are computed and then
   silently dropped, and DONJON stops at `TRISYS: NO DIFFUSION COEFFICIENTS` — a COMPO that
   exists but cannot be solved with.

2. **The fix is a leakage model at zero buckling**: `FLU: ... TYPE K B1 SIGS BUCK 0.0`.
   That activates the B1 machinery without perturbing the spectrum. Checked, not assumed:
   k∞ came out 1.310173 against 1.310172 for plain `TYPE K`, a 1e-6 difference at the
   convergence tolerance. A critical-buckling search (`TYPE B B1`, as the bundled
   `rep900_mco_proc/CalcFlux.c2m:87` uses) would instead reweight the spectrum for ~24 %
   leakage, which is wrong for a channel inside a 12.25 m core whose real geometric buckling
   is ~3 × 10⁻⁵ cm⁻².

### Supporting work

- **`rdragon` discards everything but the `.result`.** The deck ran, wrote `_ACompo` into the
  scratch directory, and the scratch directory was deleted — the in-memory failure mode, one
  step later. `data/<deck>.save` is the documented hook (`rdragon:137-143`); `_ACompo` now
  lands in `Dragon/compo/`, deliberately not in `Linux_aarch64/`, which is treated as
  disposable.
- **The `MICR` list is 31 nuclides, and it was derived, not recalled.** `MICR ALL` would carry
  all 299 depleting isotopes at all 630 points. Every name was first verified to exist in the
  DLIB_99 chain (`rbmk_chainprobe.x2m`), then the list was closed under `EDI:`'s own lumping
  rule by driving `rbmk_micrprobe.x2m` to a fixed point: `EDILUM.f:230-254` refuses to lump
  any isotope whose maximum fission yield exceeds 1 % and which is stable or has a half-life
  over 30 days. `Ru103` is the only one that rule adds beyond the physically-motivated list.
- **`LAMBDA-D` is present and carries real library data** — the six decay constants are
  0.013336, 0.032739, 0.120780, 0.302780, 0.849490, 2.85300 s⁻¹, read from `NDEL 6`, not
  hardcoded. `INIKIN:` needs this and will find it.

### The full run, and what it is actually worth — 2026-09-23 (3)

The 630-point run completed in **1 h 21 min** (4881 s CPU, single thread, peak RSS well under
1 GB — no GPU, nothing near the 110 GB ceiling). `compo/_ACompo` is 113.9 MB, all 630
`A5BTAB` rows present, no aborts and no non-convergence in the listing.

"A COMPO exists on disk" is still not evidence of anything, so three separate checks were run
against the *full* database rather than the 4-point smoke one.

**1. Round trip, at grid nodes spanning every axis.** `rbmk_a5b_sweep.don` interpolates at
eight nodes — including all four axis extremes at once — and solves the same homogeneous
reflective cube. Against the DRAGON 172-group transport values from the same run:

| BU | dca | TF | TG | DRAGON | DONJON via COMPO | delta, pcm |
|---|---|---|---|---|---|---|
| 0 | 0.72 | 900 | 750 | 1.310173 | 1.310166 | -0.4 |
| 20000 | 0.02 | 2000 | 900 | 0.950288 | 0.950330 | +4.7 |
| 10000 | 0.30 | 1200 | 750 | 1.094708 | 1.094746 | +3.2 |
| 5000 | 0.72 | 600 | 500 | 1.175726 | 1.175756 | +2.2 |
| 15000 | 0.15 | 1500 | 900 | 1.020717 | 1.020745 | +2.7 |
| 2000 | 0.45 | 900 | 500 | 1.228206 | 1.228303 | +6.4 |
| 20000 | 0.72 | 600 | 900 | 0.940046 | 0.940085 | +4.4 |
| 0 | 0.02 | 2000 | 500 | 1.296603 | 1.296600 | -0.2 |

**Worst case 6.4 pcm.** The 0.4 pcm figure recorded earlier was the corner point only, and was
optimistic by a factor of 16; condensation + homogenisation + disk + interpolation cost about
6 pcm, not half of one. Still two orders below the physics uncertainties here.

**2. Off-grid interpolation.** The transient will never land on a grid node, so `LINEAR`
interpolation error is the number that matters. `rbmk_a5b_offgrid.x2m` runs DRAGON at eight
points with DCA, TF and TG all at axis *midpoints*; burnup is left on nodes deliberately,
because burnup does not change on transient timescales while all three others swing hard.

**Worst case 27 pcm** (range -27 to +21). Acceptable: it is 0.006 $ at discharge burnup, and
smaller than the DRAGON/OpenMC void disagreement by a factor of 50.

**3. beta_eff as a curve, extracted rather than assumed.** This was the gate item most likely
to be quietly faked, and the first attempt *did* produce a fake -- see the trap below.

| BU, MWd/kg | 0 | 2 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|
| beta | 0.006824 | 0.006361 | 0.005877 | 0.005358 | 0.004985 | 0.004680 |

Beta falls by 31 % over life, as it must: the library's own Pu-239 delayed fractions sum to
**0.002254** against U-235's **0.006524** (measured directly from `DLIB_99`,
`rbmk_deldiag.x2m`), so beta tracks the U-235 -> Pu-239 shift. Second-order dependences at
20 MWd/kg: full voiding -4.5 % (0.004468), TF 2000 K + TG 900 K -1.9 % (0.004593).

Independent check: **OpenMC prompt-vs-total gives beta_eff = 0.006856 +/- 0.000162** at fresh
fuel and nominal density, against DRAGON's 0.006824 -- **-0.5 %, inside the Monte Carlo
error.** Two codes, two methods, two different definitions (DRAGON's is the flux-weighted
delayed nu-sigma-f ratio, OpenMC's is 1 - k_prompt/k_total), agreeing to half a percent.

The **0.0048 assumed throughout the project so far is a discharge-burnup number**. It is
correct to within 2 % at 20 MWd/kg and wrong by **+42 %** at fresh fuel. `openmc/compare_bu.py`
has been changed to use the measured curve.

### The trap: `GETVAL 'NUSIGF' 1` does not mean what it looks like

The first beta extraction returned **0.006524 at every burnup, every void fraction and every
temperature, identical to six digits** -- visibly wrong, since the whole point is that beta
falls with burnup. Two independent things were wrong, and either alone would have produced a
plausible-looking number:

1. `GREP: ... GETVAL 'NAME' I [J [K]]` takes a **start index, optional end, optional stride**
   (`DRVGRP.f:182-190`), not a count. `GETVAL 'NUSIGF' 1` reads element 1 only.
2. The macrolib out of `NCR:` has `NMIX = 1` but **`NBFIS = 18`** -- 18 fissile families, one
   per fissioning nuclide in the depleted fuel. `LENGTH 'NUSIGF'` returns 18.

So element 1 was U-235's entry, in *both* numerator and denominator, at every state -- and
0.006524 is exactly U-235's beta. The fix is `MEAN 'NUSIGF' 1 18`: the common factor 18
cancels in the ratio, so the mean is as good as the sum and needs one variable instead of
eighteen.

This is standing rule 1 in a new disguise. The number was not chosen to make an assert pass;
it was produced by a read that silently narrowed to one isotope, and it was *self-consistent
across ten states*, which made it look more trustworthy rather than less. What caught it was
knowing in advance what the physics had to do -- beta must fall -- and treating a flat curve
as a defect to be explained rather than a result to be recorded.

### Why `GOLVER` alone was not enough -- the exact mechanism

Recorded precisely now that the source has been read end to end:

- `EDIPXS.f:344-351` writes the `DIFF` block under `GOLVER` **or** a leakage model, so the
  edit object looks correct either way.
- `EDIPXS.f:413-419` sets the state-vector flag `IDATA(9)` **only** under a leakage model.
- `COMACR.f:91` reads `NLEAK = IPAR(9)`; `COMACR.f:169` copies `DIFF` out of the edit only when
  `NLEAK >= 1`; `COMACR.f:246` stores it in the COMPO under the name **`STRD`**, not `DIFF`.

With `GOLVER` alone the COMPO is written, is a valid `L_MULTICOMPO`, has no `STRD`, and DONJON
stops at `TRISYS: NO DIFFUSION COEFFICIENTS`. That is why `FLU: TYPE K B1 SIGS BUCK 0.0` is
mandatory: the B1 machinery sets the flag, and zero imposed buckling leaves the spectrum
untouched (k-inf 1.310172 -> 1.310173). This is also why a `grep DIFF` on `_ACompo` finds
nothing while the database is perfectly usable -- the block is called `STRD` on disk. The
stale comment in `rbmk_a5b_compo.x2m` that claimed B1 "is NOT used here" has been corrected;
it contradicted the code three lines away from it.

### The void curve, now that both codes have more than two densities

`branch_mid.py` added OpenMC branches at 0.35 and 0.15 g/cm3 across burnup. Reactivity
relative to nominal, pcm:

| BU | 0.60 | 0.45 | 0.35 | 0.30 | 0.15 | 0.05 | 0.02 |
|---|---|---|---|---|---|---|---|
| **DRAGON** 0 | +137 | +239 | -- | +265 | +236 | +220 | +222 |
| **OpenMC** 0 | -- | -- | +566 | -- | +737 | -- | +1030 |
| **DRAGON** 20000 | +313 | +656 | -- | +995 | +1457 | +1973 | +2190 |
| **OpenMC** 20000 | -- | -- | +1722 | -- | +2879 | -- | +4007 |

Two things the old two-point comparison could not see:

- **At discharge burnup the shape agrees and only the magnitude differs** -- the ratio is a
  steady 1.8-2.0x across the whole density range. That is the signature of a systematic
  error in one quantity, not of a modelling difference that varies with void.
- **At fresh fuel the shapes genuinely disagree.** DRAGON is non-monotonic -- it peaks near
  0.30 g/cm3 and falls back -- while OpenMC rises all the way to full void. The fresh-fuel
  ratio therefore runs from 2.2x at 0.35 to 4.6x at 0.02, and quoting a single fresh-fuel
  ratio is meaningless.

Fresh fuel is not the accident condition, so this does not move the bracket for A8. It is
recorded because it narrows where the disagreement lives.

### The void worth in dollars, with the measured beta

Applying beta(BU) -- a property of the fuel, so the same curve applies to both codes:

| BU, MWd/kg | beta | DRAGON pcm | DRAGON $ | OpenMC pcm | OpenMC $ |
|---|---|---|---|---|---|
| 0 | 0.006824 | +222 | +0.33 | +1030 | +1.51 |
| 5000 | 0.005877 | +155 | +0.26 | +852 | +1.45 |
| 10000 | 0.005358 | +499 | +0.93 | +1473 | +2.75 |
| 15000 | 0.004985 | +1204 | +2.42 | +2650 | +5.32 |
| 20000 | 0.004680 | +2190 | +4.68 | +4007 | +8.56 |

The worth in dollars grows **14x (DRAGON) or 5.7x (OpenMC)** from fresh to discharge, because
the numerator rises and beta falls at the same time. Both ends of the bracket put full voiding
at discharge burnup **well above prompt critical** -- 4.7 $ and 8.6 $. That is the first
quantitative statement this project can make about why the reactor was dangerous, and it holds
at both ends of the bracket, which is what the bracket was built to test.

Caveat kept in view: this is the *equilibrium* worth of complete voiding at fixed burnup, not
a transient. A8 is what decides whether the 1.8x matters.

### A5b.1d — the bracket, and why it is a table and not a second COMPO

The plan called for a **second MULTICOMPO** whose void branches are rescaled to OpenMC, the
two differing only on the DCA axis. That artifact cannot be produced. Checked, not assumed:

- `LIB:` has no cross-section scaling facility — its full keyword list is in `LIBINP.f`
  (`APLIB1 APLIB2 APLIB3 APXSM COMB CORR DBYE DRAGON EVOL GAS INF IRSET MACROLIB MATXS
  MATXS2 MICROLIB MIX MIXS NDAS NOEV NOGAS NONE NUMBER PTMC PTSL RESK RSE SAT SHIB TCOH
  TEMP THER WIMSAECL WIMSD4 WIMSE`) and none of them multiplies a cross section.
- `EDI:` and `COMPO:` have no scaling option either; the write path is
  `LIB:` → `USS:` → `ASM:` → `FLU:` → `EDI:` → `COMPO:` with no hook in it.
- `MAC:`'s `ADD` exists but only in **update** mode (`MACDRV.f:253-256`), i.e. on a macrolib
  that already exists in DONJON — it is a consumer-side tool, not a producer-side one. And
  with `NBFIS = 18` a νΣf override needs 18 values per group per mixture.

That leaves patching the DRAGON source — `5.1/` is an upstream submodule — or hand-editing the
114 MB LCM ASCII file, reverse-engineering an undocumented format to produce an opaque derived
artifact that must be regenerated whenever an OpenMC branch point is added. Two were added
today alone.

So the bracket is carried as **data** (`openmc/void_bracket.py`), not as a second database:

r(BU, v) = Δρ_OpenMC(BU, v) / Δρ_DRAGON(BU, v),  v = 1 − dca/0.72

| BU, MWd/t | v = 0.514 | v = 0.792 | v = 0.972 |
|---|---|---|---|
| 0 | 2.21 ± 0.27 | 3.12 ± 0.31 | 4.64 ± 0.30 |
| 2000 | 1.95 ± 0.34 | 2.64 ± 0.33 | 3.71 ± 0.33 |
| 5000 | 3.09 ± 0.46 | 4.80 ± 0.60 | 5.51 ± 0.51 |
| 10000 | 2.07 ± 0.36 | 3.47 ± 0.28 | 2.95 ± 0.18 |
| 15000 | 1.72 ± 0.23 | 2.23 ± 0.14 | 2.20 ± 0.10 |
| **20000** | **1.95 ± 0.14** | **1.98 ± 0.09** | **1.83 ± 0.05** |

Errors are OpenMC's Monte Carlo statistics; DRAGON is deterministic.

**At the accident condition the bracket collapses to one number.** At 20 MWd/t the ratio is
1.83–1.98 across the whole density range — constant within its own error bars — so a single
multiplier near **1.9** describes the entire disagreement. That is a much better-behaved
bracket than the plan assumed, and it is only visible because the density axis now has four
OpenMC points instead of two.

The low-burnup rows carry no information and must not be used: at 5 MWd/t DRAGON's own void
worth dips to +155 pcm, so the ratio is a small number over a smaller one; at fresh fuel the
two curves disagree in *shape*, not just scale. Neither is the state the reactor was in.

> **REVISED 2026-09-24 (3): 20 MWd/kg was not the accident condition.** [PAV] Table 1 gives
> the Unit 4 core on 26 April 1986 as still mostly the first core:
>
> | assemblies | average burnup, MWd/kgU |
> |---|---|
> | 721 | 13.7 |
> | 392 | 12.3 |
> | 154 | 10.5 |
> | 101 | 8.8 |
> | 35 | 7.0 |
> | 43 | 5.4 |
> | 41 | 3.5 |
> | 172 | 1.2 |
> | **1659, whole core** | **10.9** |
>
> Nothing was near 20. The rows that matter are 10000 and 15000, where r is 2.0–3.5 and not
> constant. The single ~1.9 multiplier above describes a core Unit 4 never was. The
> paragraph above claiming "neither is the state the reactor was in" is wrong for 10 MWd/kg.
> Consequences, not yet acted on:
>
> - The bracket for A8 must be evaluated over roughly 5–15 MWd/kgU and weighted by that
>   distribution, not quoted at 20.
> - The OpenMC density axis there needs the same four-point resolution it has at 20.
> - The dollars table above should be read at 10–14 MWd/kgU: +0.9 to +2.4 $ (DRAGON) and
>   +2.8 to +5.3 $ (OpenMC). Those are pre-geometry-fix numbers.
>
> The design discharge burnup is also not 20. [D] p.95 gives 19.5–24.4 GWd/t UO₂, i.e.
> 22–28 GWd/tU, and [BIB] gives ~26. The burnup axis itself is per tonne U (`EVO: POWR` is
> MW per t initial HM), matching [PAV], so there is no unit trap.

Ratios are of **branch** reactivities at the same burnup, never of absolute k — the two codes'
depletion trajectories diverge (+268 pcm at 5 MWd/t, −2084 at 20), so an absolute-k correction
would fold a depletion difference into a void correction.

**What this defers to A7/A8.** Variant A is the COMPO as built. Variant B multiplies the
void-induced reactivity by r. The application point is `MAC: ... ADD` on the void-induced Δ in
the consuming deck — one visible multiplier rather than a second 114 MB binary, and the single
source of truth for the physics stays in `_ACompo`. This preserves the plan's intent (the
variants differ only in how the DCA axis is used) and moves the implementation, not the
science. It is **not yet built or validated** — that is the first item of A7.

## The draglib the whole project was running on is not the one it ships — 2026-09-24

Restructuring the repo for a clean clone turned up a reproducibility defect that had been
live since 19 September and would not have been visible any other way.

`DLIB_99` is `draglibendfb8r1Apolib99_v5p1`, resolved by each deck's `.access` hook out of
the `libraries` submodule. Upstream's hook gunzips it **in place**, which deletes the `.gz`
and leaves the decompressed file in the submodule; on the next run the hook finds the
decompressed file already there and uses it without looking at the `.gz` again. That is a
cache with no key.

At some point the `libraries` submodule moved to `d4456d42` ("Upgrade draglibs to NJOY2016
release 78", 2025-12-24). The decompressed leftover from the previous revision stayed on
disk and kept winning. Every DRAGON number recorded in this file was produced against it.

| | bytes | `rbmk_cell_a3` k∞ |
|---|---|---|
| what was actually used | 134,497,940 | **1.310172** |
| what the submodule pins (LFS `cb1395ffbb65…`) | 83,700,460 | **1.308679** |

**−87 pcm.** Not large, but it is a systematic offset under every recorded DRAGON result,
and a clean clone on another machine would silently have produced the second column while
the documents claimed the first.

The same check found a second one: `draglibendfb8r1ecco1962_light_v5p1`, 317,833,351 bytes on
disk against 161,707,708 pinned. `draglibendfb8r1SHEM361_v5p1` and `draglibJef2p2Apolib99_v5p1`
matched and were fine.

The provenance of the two oversized files could not be established. They are not in the
submodule's LFS object store at any commit in its history, and the older pointer
(`f5cd7e2e…`, 51,120,783 compressed) was never cached locally. They are roughly twice the
size of the pinned builds, which is consistent with a pre-NJOY-78 library carrying more
temperature points, but that is inference, not evidence.

**What changed.** `decks/common/dlib99.access` now content-addresses the cache: it digests
the source `.gz` and decompresses to `.cache/draglib/<lib>.<sha12>`, so bytes from a
different revision land at a different path and can never be picked up in place of the
pinned ones. The run log prints the key and the size. `tools/tidy_libraries.sh` compares
every decompressed leftover against the pinned `.gz` and moves non-matches to
`.cache/draglib/unprovenanced/` rather than deleting them — results were produced with
them and may need reproducing.

**What has not changed, and is now owed.** Every DRAGON figure in this file, in
`PROJECT_PLAN.md`, in `TIER_A_WORKPLAN.md` and in `docs/report.html` — k∞ 1.310172, the
630-point MULTICOMPO, the β curve, the void table, the dollars table — was measured on the
unprovenanced library and has **not** been re-baselined. The OpenMC side is unaffected: it
is continuous-energy ENDF/B-VIII.1 and never touched a draglib, so the DRAGON/OpenMC
bracket has to be recomputed rather than merely relabelled. Re-baselining means rerunning
`rbmk_a5b_compo.x2m` (81 min) and the decks downstream of it.

Standing rule 7, earned here:

7. **A cache without a key is a silent substitution.** Any derived artifact kept beside its
   source must carry a digest of that source in its name. "The file is already there" is not
   evidence that it is the right file, and the failure is invisible precisely because
   everything keeps working.

## A2 — the 3-D core, run at last — 2026-09-23

| | |
|---|---|
| deck | `Donjon/data/rbmk_core_3d_realistic.don` (49 × 49 × 32, 25 cm pitch) |
| extent | MESHX/MESHY 0 → **1225 cm**, MESHZ 0 → **800 cm** (7 m active + 50 cm axial reflector each end) |
| regions | 76 832 |
| cross sections | IAEA 2-group PWR — **geometry and solver check only, no RBMK physics** |
| **k_eff** | **1.123062**, converged |
| `FLUD:` wall clock | **1 s** at `MCFD 1` |

**GATE A2 PASSED.** No `MAXIMUM NUMBER OF OUTER ITERATIONS IS REACHED`, and the value is
physically the right one for the wrong-on-purpose cross sections: those constants have
k∞ ≈ 1.12, and a 12.25 m core behind a 50 cm reflector leaks almost nothing, so k_eff ≈ k∞.
That is the whole content of the test — the old 0.054 was a 12 cm cube leaking almost
everything. Do not read reactor physics into 1.123062; real cross sections arrive with A5b.

**The performance number is the surprising one.** `FLUD:` at `MCFD 1` takes **1 second**
against the 729 s `DUAL 3 3` baseline — ~700×, not the ~40× estimated from the unknown count.
This does not change the Tier B conclusion (1 s per steady solve is still two orders of
magnitude off a 10 Hz panel, and DONJON remains single-threaded with no GPU path), but it
does mean a DONJON-in-the-loop quasi-static fallback is far more viable than the earlier
estimate suggested, and the offline A8 transient will be much cheaper than budgeted.

Still open from the A2 group: `gen_rbmk_donjon.py`, `gen_rbmk_geo.py` and `gen_rbmk_simple.py`
still carry PITCH in metres, and the core mix map still has **no rod sites** (A6).

## Phase 0 corrections — 2026-09-23

Applied before starting A5b, so that the MULTICOMPO is not built on a known-wrong cell.

**The hydrogen fix.** `RbmkLib.c2m:44` → `H1_H2O`. `rbmk_cell_a3.x2m` re-run from a deleted
`.result`: **k∞ = 1.310172**, matching the independently-measured value; volume-fraction
guardrail still passes (89.594 / 3.772 / 2.901 %).

**Verification that the file reshuffle changed no physics.** `rbmk_h2otest.x2m` re-run after
repointing its branches (`RbmkLibF` for free gas, `RbmkLib` for bound) reproduces every value
bit-for-bit:

| branch | dca 0.72 | dca 0.35 | dca 0.02 |
|---|---|---|---|
| `RbmkLibF` free gas (was `RbmkLib`) | 1.312816 | 1.316728 | 1.314234 |
| `RbmkLib` bound (was `RbmkLibH`) | 1.310172 | 1.314718 | 1.313999 |

→ +226 / +82 pcm and +264 / +222 pcm, exactly as recorded before the rename.

**Procedure files.** `RbmkLibH.c2m` retired; `RbmkLibF.c2m` added (free gas, do-not-use
banner, kept only so the comparison above reproduces); `RbmkLibN`/`RbmkLibW` headers corrected
to describe `CTRA`, which is what they actually vary. Each variant now differs from `RbmkLib`
in exactly one non-comment line — checked mechanically. Six diagnostic decks repointed from
`RbmkLibH` to `RbmkLib`.

**Housekeeping.** 21 orphaned `.access` scripts (decks already in `quarantine/`) moved to
`quarantine/orphaned_access/`. `rbmk_ussopt.x2m`'s header was a copy-paste of
`rbmk_grmin.x2m`'s and described the wrong experiment; corrected.

**Not done, and a live hazard.** The ~16 legacy `rbmk_cell_*` decks still in `Dragon/data/`
(`dlib99*`, `print_*`, `save_macrolib*`, `verify_macrolib*`, `2group_correct`, `mac_flux`,
`mccg_test`, `nxt_trkfile`) each hardcode their own `LIB:` block with free-gas `H1` **and a
different coolant number density** (`4.90E-2` vs `RbmkLib`'s `4.81360E-2`). They bypass the
single source of truth entirely. `rbmk_cell_dlib99_v2.x2m` is among them and is the retracted
CANDU bundle — yet `TIER_A_WORKPLAN.md` still names it as the A0 regression baseline. Left in
place pending a decision; do not build on any of them.

**Also unaddressed: none of this is under version control.** `5.1/` is an upstream submodule
(`git.oecd-nea.org/dragon/5.1.git`) and every RBMK deck, procedure and generator in it is
untracked, with no history. The same is true of `quarantine/` and `openmc/`. There is no way
to recover an overwritten deck, and no record of when any of them changed — which is why the
A2 timestamp evidence was the only way to establish that the core deck had never been run.


## Cell geometry pinned to a primary source — 2026-09-24 (2)

Three of the four open geometry questions listed under "Validation risk" are now settled
against the chief designer's own monograph. **One correction, one confirmation, one new
suspect, and every downstream physics number is invalidated pending a re-run.**

### The source

**Доллежаль Н.А., Емельянов И.Я., «Канальный ядерный энергетический реактор»,
Атомиздат, Москва, 1980.** 208 pp. Dollezhal was the RBMK's chief designer (главный
конструктор, НИКИЭТ). The book **pre-dates the 1986 modifications**, so it describes the
as-built Unit 4 configuration rather than the post-accident retrofit that most accessible
literature documents. A DjVu scan was converted to a searchable PDF (the OCR text layer was
re-injected as invisible UTF-8; the `ddjvu -format=pdf` path silently discards it).

Page numbers below are **PDF pages of that scan**, not printed page numbers.

### 1. Pressure tube 88 × 4 — CONFIRMED, no change needed

[D p.54], describing fig 3.3:

> «средняя часть которой состоит из трубы 9 **наружным диаметром 88 и толщиной стенки
> 4 мм**, изготовленной из сплава Zr+2,5% Nb»

— *"the middle part consists of tube 9 with **outer** diameter 88 and wall thickness 4 mm,
of Zr+2.5% Nb."* Repeated at [D p.11]; the 80 mm bore is confirmed twice more elsewhere
(`внутренним диаметром 80 мм`).

So OD 88 → r 4.40, ID 80 → r 4.00 — **exactly what the deck already had**. The Wikipedia
"8.4 cm ID" reading, which would imply OD 92, is wrong. The 10 % coolant-area ambiguity
that fed directly into the void coefficient is closed, and the guardrail's coolant band has
been tightened from 3.0–4.5 % to 3.4–4.0 % accordingly (88 × 4 → 3.653 %, 92 × 4 → 4.437 %,
so the wrong tube is now actively rejected rather than tolerated).

### 2. Ring radii 1.60 / 3.10 — STILL OPEN, deliberately unchanged

> **Resolved 2026-09-24 (3): 1.60 / 3.10 are correct** (⌀32 / ⌀62 mm, [RU-A], [LEI05]). The
> measurement below was wrong by ~1.5 mm, and declining to use it was the right call.

[D] does not state them. Fig 5.1 section Б-Б shows the 6+12 arrangement, confirming the
topology, but carries a single dimension: the grid envelope ⌀79. Measured off that figure
against that scale: **inner 17–18 mm, outer 31–32 mm, ±1.5 mm**. 3.10 sits comfortably
inside that; 1.60 may be ~1.5 mm small.

Geometric bounds, now that the central tube is pinned at ⌀15: inner ≥ 14.25 mm (clear the
tube), outer between 26.1 (rods touching at 30°) and 32.75 (fit inside ⌀79).

**Left at the old values on purpose.** A number measured off a scanned drawing carries false
precision, and substituting it would look like sourcing without being sourcing. Needs the
NIKIET 2006 monograph (Абрамов и др., ISBN 5-98706-018-4), which has dimensioned assembly
drawings.

### 3. Carrier — CORRECTED, the deck was wrong

[D p.11]: the 18 rods are held by spacer grids on a **central tube** of Zr
«размером 15×1,25 мм» (OD 15, ID 12.5); inside that tube runs «либо несущий стержень
диаметром 12 мм, либо несущая труба размером 12×2,5 мм» — *either a 12 mm solid carrier
rod, or a 12 × 2.5 tube*. The solid rod is the standard channel; the tube variant carries
the DKE power sensor and is not the average channel.

The deck modelled a 13 mm OD hollow tube with coolant inside — **matching neither
component**, and understating carrier metal by roughly 3×.

| | was | now |
|---|---|---|
| carrier | Zr tube r 0.500/0.650, coolant inside | solid Zr rod r 0–0.600 |
| water annulus | — | r 0.600/0.625 |
| central tube | — | Zr r 0.625/0.750 |

### 4. Fuel rod — CORRECTED, found while checking the carrier

Same sentence, [D p.11]: clad **OD 13.5 mm, wall 0.9 mm**, pellet **11.5 mm**, UO₂ density
up to 10.5 g/cm³, enrichment **1.8 or 2 % U-235**. The deck had clad OD 13.6 with an
0.825 mm wall, making the pellet–clad gap ~2.3× too thick. Pellet radius 0.5750 was already
right.

`RADIUS 0.0000 0.1000 0.5750 0.5975 0.6800` → `0.0000 0.1000 0.5750 0.5850 0.6750`.

### 5. Pellet central hole — NEWLY SUSPECT

> **Resolved 2026-09-24 (3): the hole is real.** See "Cell geometry closed" below.

The 2 mm central hole is a `[W]` value. [D p.11] describes the pellets only as «таблетками
диаметром 11,5 мм», and no central hole appears anywhere in the book. A solid pellet would
raise fuel volume by ~3.1 %. **Left in place, flagged.** Removing it would also break the
OpenMC volcheck agreement, so it needs deciding deliberately rather than in passing.

### Volume fractions, recomputed

Analytic, and independently reproduced by `openmc/volcheck.py` after the same edits —
both give cell area exactly 625.0000 cm².

| | before | after | change |
|---|---|---|---|
| graphite | 89.5938 % | 89.5938 % | — |
| coolant | 3.7721 % | **3.6527 %** | −3.2 % rel |
| fuel | 2.9009 % | 2.9009 % | — |
| zirconium | 2.7292 % | **2.9823 %** | +9.3 % rel |
| gas | 1.0040 % | **0.8702 %** | −13.3 % rel |

Graphite and fuel are untouched, so the 1763 t graphite cross-check and the fuel fraction
both still stand. All five clearances remain positive (tube→inner ring +1.75 mm, inner
rod-to-rod +2.50, inner→outer +1.50, outer rod-to-rod +2.55, outer→wall +2.25), so the
corrected cell is physically buildable.

### What this invalidates

**Everything downstream of the cell.** Not yet re-run — there is no DRAGON build in the
environment these edits were made in.

- **k∞ = 1.310172** — superseded. Coolant down 3.2 %, Zr (a parasitic absorber) up 9.3 %:
  expect a small decrease.
- **The A5 void curve (+1957 pcm at 20 MWd/kg)** — superseded, and note the *direction*:
  there is now less coolant to void, so the DRAGON void worth should fall, which would
  **widen** the unexplained DRAGON-vs-OpenMC gap rather than close it. That gap is a method
  difference (the CANDU-6 control agrees to 22 pcm) and this correction does not address it.
- **The A5b MULTICOMPO** — built on the old geometry, must be regenerated.
- `openmc/volcheck.py`'s `dragon` dict still holds the 2026-09-22 numbers and is marked
  stale in-file; it will not match until the deck is re-run.

Re-run order: `rbmk_cell_a3.x2m` (guardrail must pass with the new bands) →
`openmc/rbmk_cell.py` at matching burnup → `rbmk_a5_void.x2m` → `rbmk_a5b_compo.x2m`.

### Applied to four decks plus OpenMC, per standing rule 6

The cell geometry is **copy-pasted verbatim** into at least 13 decks. That is the same
hazard as rule 6 ("a fix that lives in a copy of the file is not a fix"), and it is how the
CANDU-6 bundle propagated in the first place. Changed here: `rbmk_cell_a3.x2m`,
`rbmk_a5_void.x2m`, `rbmk_a5b_compo.x2m`, `rbmk_h2otest.x2m`, `openmc/rbmk_cell.py`,
`openmc/volcheck.py`. The remaining diagnostic probes (`rbmk_ctra`, `rbmk_rates`,
`rbmk_sstest`, `rbmk_ussopt`, `rbmk_grmin`, `rbmk_micrprobe`, `rbmk_shem361`,
`rbmk_a5b_smoke`, `rbmk_a5b_offgrid`) still carry the old geometry and are now
inconsistent with the live decks.

**Recommended follow-up:** extract the cluster geometry into a shared
`rbmk_proc/RbmkGeo.c2m`, exactly as `RbmkLib.c2m` already does for compositions and for the
same stated reason — "so the two cannot disagree about what a mixture contains". Not done
here because it cannot be tested without a DRAGON build, and an untested refactor of the
geometry is precisely the class of change this log exists to prevent.

### Also recovered from the same source, not yet used

**A possible unit trap in the burnup axis.** *(Ruled out 2026-09-24 (3): both codes and [PAV]
use per tonne U. The real finding was different: see the A5b.1d revision.)* [D p.95] gives the burnup plateau as
`19,5—24,4 ГВт·сут/т **UO₂**` and the maximum as `24—28`, i.e. **per tonne UO₂, not per
tonne U** — a 13 % offset (÷0.8815 → ~27.7–31.8 GWd/tU). This log quotes the void
coefficient "at 20 MWd/kg" without stating the basis. If DRAGON and OpenMC disagree on that
convention, it would present exactly as a magnitude discrepancy at nominal burnup. Worth
ruling out before hunting the method difference further.

**Operating parameters** [D p.95], for the TH coupling that does not exist yet: channel
power 3000–3200 kW, flow 29.5–30.5 t/h, **exit quality 19.6 %**, inlet 79.6 kgf/cm² / 265 °C,
outlet 75.3 kgf/cm² / 289.3 °C, max coolant velocity 18.5 m/s, clad surface 295 °C / inner
323 °C, axial peaking 1.4, radial 1.06, max linear rating 360–385 W/cm, pellet centreline
2100 °C, channel length 7000 mm, cassette = two 3.5 m TVS with a ~20 mm gap.

**CPS channel** [D p.37]: OD 88 / **ID 82** mm (3 mm wall, not the fuel channel's 4 mm),
Zr alloy grade 125. Needed for `DEVINI:` when control rods are modelled.

**Graphite** [D p.11]: blocks 250 × 250 mm, density 1.65 g/cm³, bore 114 mm, 1693 cells —
all four already match the deck. Note [D] also says graphite **rings** are shrunk onto the
channel tube for thermal contact; the deck models a gas clearance at r 4.40–4.55, which is
an idealisation worth revisiting.

---

## Cell geometry closed — 2026-09-24 (3)

The four items Dollezhal left open are settled against eight sources the project had not
used. Full citations, file names and verbatim quotes are in `sources/README.md`. One was
already on disk: the IAEA-TECDOC-722/R PDF had been downloaded and never cited.

| Item | Verdict | Evidence |
|---|---|---|
| Ring radii 1.60 / 3.10 | **correct, unchanged** | rod circles ⌀32 / ⌀62 in [RU-A] and [LEI05] |
| Ring phase (outer offset π/12) | **correct, unchanged** | [D] p.96 fig 5.1 Б-Б. Inner rods sit on the axes; outer rods straddle them in pairs. This is a topology read, not a measurement. |
| Pellet hole 2 mm | **real, unchanged** | [RU-A] «осевое отверстие диаметром 2 мм»; [LEI05] Table 1; [BIB] lists it among RBMK-1000 rod design features |
| Clad OD | **13.5 → 13.58** (r 0.6750 → 0.6790) | [RU-A] drawing «13,58 +0,05/−0,07, внутренний 11,7 +0,1»; [LEI05] 13.6 / 11.7; [D] 13.5 × 0.9 |
| Graphite gas gap | **valid idealisation, unchanged** | [CAST] p.11; [TD722] p.76; [USP] |
| Burnup basis | **per t U in both codes; no trap** | `EVO: POWR` is MW per t HM; [PAV] uses per kg U |

**Clad OD refined, and why the Dollezhal fix mostly stands.** Every source agrees on ID
11.7 mm, so the pellet–clad gap correction in fee38ff is right. Only the OD moves. The 13.58
comes with drawing tolerances, which is why it's preferred over [D]'s rounded 13.5. The
published nominal clad-to-wall gap, 2.2 mm [TD722] p.107, doesn't discriminate: this cell
gives 2.21, and 2.25 at OD 13.5.

Coolant 3.6527 → 3.6037 % and Zr 2.9823 → 3.0313 %. Graphite, fuel and gas are unchanged.

**The pellet-hole mass check.** [PAV] gives 114.7 kg U per assembly at Unit 4, and [D] p.97
gives an active length of 6920–6954 mm. Over 6937 mm at the deck's 9.167 g HM/cm³, this cell
holds 115.3 kg with the hole (+0.5 %) and 118.9 kg solid (+3.7 %). The same numbers as UO₂,
130.8 vs 134.9 kg, both sit inside [D]'s 125–135 kg, so that range alone would not decide it.
The per-assembly uranium mass does.

**A caution, earned.** On 09-24 (2) the inner ring radius was measured off fig 5.1 at
17–18 mm, "±1.5". The real value is 16.0. The log declined to use the measurement, and that
restraint is the only reason it didn't become a geometry change. Reading *topology* off the
same figure (which rods sit on the axes) is reliable. Reading *dimensions* off it is not.

**Re-run.** `rbmk_cell_a3.x2m` from a deleted `.result`, pinned draglib `cb1395ffbb65`,
x86_64: **k∞ = 1.304123**. The guardrail passed, and DRAGON MIXTURESVOL fractions are
89.594 / 3.604 / 2.901 / 3.031 / 0.870, equal to `volcheck.py`'s analytic values. A second run
after comment-only edits reproduced it bit for bit.

k∞ steps since the last recorded value:
- 1.310172 → 1.308679: library, −87 pcm
- → 1.304717: Dollezhal carrier and clad, −232 pcm
- → 1.304123: clad OD 13.58, −35 pcm

**What remains owed** (unchanged in kind from 09-24 (2), now on a closed geometry):
- `rbmk_a5_void.x2m`, `rbmk_a5b_compo.x2m` (81 min), the β curve, the OpenMC runs and the
  bracket all need re-running.
- The nine diagnostic probes still carry the pre-Dollezhal geometry. The shared
  `rbmk_proc/RbmkGeo.c2m` extraction is still the recommended fix.
- **Re-frame the bracket at 10–14 MWd/kgU, not 20.** See the revision in the A5b.1d section.

**Also found, for later.** [TD722] p.64 gives the one *measured* void coefficient in the
project so far: at Leningrad, 1.8 % enrichment, approaching equilibrium burnup, the steam void
coefficient was **4–5 β**. That is a core value with additional absorbers loaded, so it cannot
be compared with a k∞ branch. It is the first thing A6/A7 can be checked against.

---

## Re-baseline on the closed geometry — 2026-09-24 (4)

Everything downstream of the cell, re-run in both codes on the sourced geometry and the pinned
draglib (`cb1395ffbb65`). The machine was the x86_64 box (Ryzen 5 3600, 6 cores / 12 threads),
with OpenMC 0.16.0 from the `openmc-env` conda env and ENDF/B-VIII.1 HDF5 in `~/nucdata`.
**This supersedes every DRAGON and OpenMC RBMK number recorded earlier in this file.** Those
tables are kept for provenance and are not repeated.

### One geometry, thirteen decks

The cell geometry now lives in `rbmk_proc/RbmkGeo.c2m` (`GEOSS GEOFL := RbmkGeo ;`). All 13
lattice decks call it, including the nine diagnostic probes, which were still on the
pre-Dollezhal carrier and clad. Gate: `rbmk_cell_a3` through the procedure reproduces
k∞ 1.304123 bit for bit.

### DRAGON

| | result |
|---|---|
| `rbmk_cell_a3` k∞ | **1.304123**, guardrail passed |
| `rbmk_h2otest` | bound H: 1.304123 nominal (matches a3); free gas 1.306794. Full void, fresh: bound **+62**, free gas −82 pcm |
| `rbmk_a5b_compo` | 630 points, 5 h 21 min wall (CPU-contended with OpenMC), 211 MB peak, 108 MB `_ACompo`, no aborts |
| Round trip, grid nodes | worst **6.6 pcm** over 8 nodes spanning every axis (was 6.4) |
| Off-grid, `LINEAR` | worst **26.5 pcm** over 8 midpoints (was 27) |
| β(BU) | 0.006825, 0.006359, 0.005872, 0.005350, 0.004975, 0.004671 at 0/2/5/10/15/20 MWd/kg. Essentially unchanged (was 0.006824 → 0.004680), as expected: β is a property of the fuel, which didn't change. |

**The off-grid test is reproducible for the first time.** The DONJON side of it had never been
saved. The eight points are now in `rbmk_a5b_sweep.don`, and `openmc/a5b_interp_check.py`
compares both tests against the DRAGON `.result` files with no expected values in either.
`dragon_a5b_void.json` is now generated by `openmc/extract_a5btab.py` rather than typed.

### The void curve, both codes

Branch reactivity relative to 0.72 g/cm³ at the same burnup, pcm, at TF 900 K / TG 750 K.
DRAGON is from the COMPO; OpenMC is from `branch_results81*.json`.

| BU | code | 0.6 | 0.45 | 0.35 | 0.3 | 0.15 | 0.05 | 0.02 |
|---|---|---|---|---|---|---|---|---|
| 0 | DRAGON | +113 | +185 | -- | +181 | +121 | +72 | +62 |
| 0 | OpenMC | -- | -- | +497 | -- | +789 | -- | +901 |
| 2000 | DRAGON | +104 | +165 | -- | +155 | +96 | +62 | +59 |
| 2000 | OpenMC | -- | -- | +638 | -- | +792 | -- | +1012 |
| 5000 | DRAGON | +82 | +112 | -- | +67 | −21 | −64 | −67 |
| 5000 | OpenMC | -- | -- | +489 | -- | +771 | -- | +862 |
| **10000** | DRAGON | +99 | +153 | -- | +145 | +128 | +172 | **+207** |
| **10000** | OpenMC | -- | -- | +633 | -- | +846 | -- | **+1202** |
| **15000** | DRAGON | +162 | +303 | -- | +403 | +536 | +728 | **+819** |
| **15000** | OpenMC | -- | -- | +999 | -- | +1743 | -- | **+2288** |
| 20000 | DRAGON | +257 | +527 | -- | +782 | +1123 | +1509 | +1672 |
| 20000 | OpenMC | -- | -- | +1555 | -- | +2751 | -- | +3757 |

OpenMC's statistical error on these is ±70–120 pcm.

**What the geometry correction did.** DRAGON's full-void worth fell at every burnup, by
150–520 pcm (+222 → +62 fresh, +499 → +207 at 10 MWd/kg, +2190 → +1672 at 20). OpenMC barely
moved: +1030 → +901 fresh and +1473 → +1202 at 10, both within 2–3σ, and 4007 → 3757 at 20. As
predicted on 09-24 (2), the corrections **widened** the method gap. DRAGON's dip at 5 MWd/kg is
negative again and OpenMC still shows no trace of it.

### In dollars, at the burnups Unit 4 actually had

| BU, MWd/kg | β | DRAGON full void | OpenMC full void |
|---|---|---|---|
| 0 | 0.006825 | +0.09 $ | +1.32 $ |
| 5 | 0.005872 | −0.11 $ | +1.47 $ |
| **10** | 0.005350 | **+0.39 $** | **+2.25 $** |
| **15** | 0.004975 | **+1.65 $** | **+4.60 $** |
| 20 | 0.004671 | +3.58 $ | +8.04 $ |

At the Unit 4 core average of 10.9 MWd/kgU, interpolating gives **~+0.6 $ (DRAGON) against
~+2.7 $ (OpenMC)**.

**The bracket now straddles prompt criticality at the accident state.** Quoted at 20 MWd/kg,
both ends were far above 1 $ and the choice of code looked like a question of degree. At the
burnups the core actually had, DRAGON says completely voiding average fuel stays below prompt
critical; OpenMC says it goes well past it. This is a single-cell k∞ statement, with no
absorbers, no leakage and no spatial weighting, so neither number is the core's. But it means
the DRAGON/OpenMC disagreement is no longer something A8 can be expected to wash out. It sits
on the threshold that governs the transient.

### The bracket as a multiplier is badly conditioned where it matters

`void_bracket.py`, r = Δρ_OpenMC / Δρ_DRAGON:

| BU | v = 0.514 | v = 0.792 | v = 0.972 |
|---|---|---|---|
| 0 | 2.72 ± 0.38 | 6.55 ± 0.62 | 14.63 ± 1.16 |
| 2000 | 4.03 ± 0.48 | 8.23 ± 0.81 | 17.07 ± 1.37 |
| 5000 | 5.97 ± 1.03 | −36.6 ± 4.0 | −13.0 ± 1.2 |
| **10000** | **4.28 ± 0.64** | **6.61 ± 0.71** | **5.81 ± 0.46** |
| **15000** | **2.71 ± 0.29** | **3.25 ± 0.20** | **2.79 ± 0.13** |
| 20000 | 2.23 ± 0.19 | 2.45 ± 0.11 | 2.25 ± 0.07 |

The "collapses to ~1.9" finding was a property of 20 MWd/kg, where DRAGON's denominator is
large. At 10–15 MWd/kg r runs 2.7–6.6 and depends on void fraction. At 5 MWd/kg DRAGON crosses
zero, so r is negative and meaningless. Scaling DRAGON's void-induced Δρ by r would divide by a
small, method-sensitive number exactly where the reactor was.

**Recommendation, replacing the A5b.1d design:** variant B should *replace* DRAGON's
void-induced Δρ(BU, v) with OpenMC's, interpolated on OpenMC's own grid, rather than *scale*
it. Both are additive corrections at the same `MAC: ADD` application point. Replacing avoids
the division and stays finite through DRAGON's zero crossing. Not built; this is a design
change for A7.

### Fresh-fuel reference and β_eff, OpenMC

Fresh fuel, nominal temperatures, 50k × 250 active batches (the GB10 used 100k × 400; this
box is 3× slower, and fresh fuel isn't the accident state):

| | OpenMC | DRAGON | difference |
|---|---|---|---|
| k∞, 0.72 g/cm³ | 1.316220 ± 0.000225 | 1.304123 | +705 pcm (was +551) |
| Δρ at 0.35 | +527 ± 19 pcm | +191 | 2.8× |
| Δρ at 0.02 | +799 ± 19 pcm | +62 | 12.9× |
| β_eff | **0.006739 ± 0.000166** (1 − k_prompt/k_total: 1.307519 / 1.316391) | 0.006825 | **−1.3 %, 0.5σ** |

The β check holds on the new geometry, just as it did before (−0.5 % then). The DRAGON β curve is
confirmed at its fresh-fuel end by a different code with a different definition. OpenMC's
fresh full-void worth fell 912 → 799 pcm with the geometry. DRAGON's fell 222 → 62.

### What this changes in the plan

1. **The method gap is now the top physics priority, ahead of A6.** The trigger recorded on
   09-23 for the deferred diagnosis was "A8 showing that the two bracketed cross-section sets
   give materially different transients". A bracket that straddles 1 $ at the accident
   burnup already establishes that, without waiting for A8. The highest-information next step
   is unchanged: a 172-group flux spectrum and per-nuclide reaction-rate comparison against
   OpenMC at 10 MWd/kg, nominal and voided, and not the 2-group view, which cannot see the
   cause. The four untested DRAGON knobs listed under "Qualified 2026-09-23" (split-pellet
   self-shielding, coarse tracking, unshielded Zr, P1) are the first candidates, and all are
   cheap single-cell runs.
2. **The COMPO burnup axis is too coarse around the accident state.** Nodes at 10 and 15
   bracket 12.3–13.7, where 1113 of the 1659 assemblies sat. Adding 7.5 and 12.5 costs
   ~1.3× the build. Do it the next time the COMPO is rebuilt, rather than as a rebuild of its own.
3. **Performance note.** On this 6-core box the COMPO took 5 h 21 min while sharing a core
   with OpenMC, against 81 min on the GB10. Run the two on separate cores (`taskset`) or in
   sequence.

---

## Method gap: hypothesis register — 2026-09-25

The question was put deliberately: DRAGON and OpenMC disagree about whether voiding at Unit 4's
burnup is prompt critical. **We are not allowed to settle that by knowing the answer.**
History's "it went prompt critical" is a whole-core statement, with the night's rod pattern,
so it isn't comparable to a cell k∞ anyway. Each code has to be driven to its own converged
limit, and the difference explained mechanism by mechanism.

Everything below is fresh fuel, TF 900 K / TG 750 K / coolant 573 K, where both codes have
identical compositions by construction. Tools:
- `decks/scripts/gen_meth.py` generates every DRAGON variant (`rbmk_meth_*.x2m`), each changing
  one thing relative to `ctrl`. `ctrl` reproduces `rbmk_h2otest` bit for bit.
- `openmc/method_study.py` runs the seed-matched OpenMC variants.
- `openmc/method_table.py` collects both into one table.
- `openmc/fourfactor.py` does the exact four-factor split.

### Where the disagreement lives: the four-factor split

k = ε · p · f · η exactly, with the thermal cut at 0.625 eV. Production DRAGON against OpenMC
(on DRAGON's own graphite table), void 0.72 → 0.02, change in ln (pcm):

| | ε | **p** | f | η | k |
|---|---|---|---|---|---|
| DRAGON | +3129 | **−8083** | +5511 | −502 | +55 |
| OpenMC | +3036 | **−6977** | +5587 | −565 | +1081 |
| difference | −93 | **+1106** | +77 | −63 | +1026 |

**Everything thermal agrees.** Thermal utilisation, η, and the thermal absorption shares match
to statistics: U-235 72.61 vs 72.51 %, H 5.70 vs 5.72, C 3.97 vs 4.02, Zr-91 1.82 vs 1.83.
That eliminates every hypothesis about the thermal flux: the voided channel as a streaming
path, the graphite, the water, the boundary.

**The whole disagreement is in p, resonance absorption above 0.625 eV**, and it is also where
the *nominal* k gap lives (p 0.79561 vs 0.80295). By nuclide, production DRAGON over-absorbs,
in % of all absorptions:

| | nominal | voided | growth on voiding |
|---|---|---|---|
| U-238 | +0.50 | +1.02 | +0.52 |
| Zr, mostly Zr-91 | +0.43 | +0.72 | +0.29 |

U-235, H, Nb agree. The C and O rows differ only because `parse_dragon.py` counts capture +
fission and leaves out (n,α).

This retires the 2026-09-23 reading that the disagreement was "U-235 fission production". That
decomposition normalised the rates per unit absorption, so extra resonance absorption showed
up as a lower production share.

### The register

| ID | Hypothesis | Test | Result | Verdict |
|---|---|---|---|---|
| H1 | Graphite scattering table differs (DRAGON 10 %-porosity reactor graphite, OpenMC crystal) | OpenMC on `c_Graphite_10p` / `30p` | nominal +7, void +23 (30 %: −22 / +41) | **real, small.** Mismatch confirmed; ≤ 41 pcm |
| H2 | Boundary: DRAGON `TISO` is white (`NXTTCG.f:464`), OpenMC mirror | OpenMC white; DRAGON `TSPC` | OpenMC −31 / −7; DRAGON −3 / +8 | **real, small** |
| H3 | Flat-flux regions too coarse | `RbmkGeoFine` k = 2, 4 | void +62 → +127 → +151; nominal −60, −83 | **confirmed, moderate**, converging |
| H4 | Flux tracking too sparse | 30/60, 60/120 | < 1 pcm | **ruled out** |
| — | Self-shielding tracking too sparse | 20/40 | +16 / −7 | **ruled out** |
| H7 | Zr at infinite dilution | `RbmkLibZ` (Nb-93 has no subgroup data) | 172 g: nominal +286, void +146; on SHEM-361: +137 / +56 | **confirmed, large on 172 groups** |
| H8 | Depletion Pu isotopes unshielded | `RbmkLibP`, burnup deck | ≤ 3 pcm at every burnup | **ruled out** |
| **H9** | **172 groups too coarse through the U-238 resonances** | SHEM-281 / 295 / 361 (295 and 361 need `USS: MAXST 300`) | nominal +206 / +441 / +438; void 62 → 292 → 482 → 503 | **confirmed, dominant**, converged by 295–361 groups |
| H5 | Isotropic scattering + transport correction | MOC (`MCCG:`) with anisotropy | not run | **open** |
| H6 | Single-region pellet for self-shielding (no rim effect) | pellet split into separate mixtures | not run | **open** |
| H10 | Depletion trajectories differ | transfer isotopics | not run | open (burnup only) |
| H11 | Temperature interpolation | library-grid temperatures | not run | open, expected small |

### The best-converged DRAGON

Everything that converges, together: SHEM-361 + Zr self-shielded + mesh 4× (`best361`).

| fresh fuel | production DRAGON | best DRAGON | OpenMC (10 %-porosity graphite) | gap closed |
|---|---|---|---|---|
| k∞ | 1.304123 | 1.313050 | 1.316350 ± 0.000265 | 705 → **191 pcm** |
| Δρ at 0.35 | +191 | +435 | +533 ± 21 | 342 → **98** |
| Δρ at 0.02 | +62 | +633 | +821 ± 21 | 759 → **188** |

**Three-quarters of the gap was DRAGON not being converged**, mainly in its energy mesh through
the resonances. None of these steps used OpenMC's answer: each is DRAGON refined against
itself until it stopped moving. That DRAGON converges *toward* OpenMC, from below, on the one
quantity that disagrees is evidence about which code is right that doesn't depend on history.
It isn't proof. That needs the remaining 190 pcm explained, and measured data (below).

**Cost.** `best361` takes 83× the production CPU, almost all of it the 4× mesh (SHEM-361 alone
is 2.2×). SHEM-361 + Zr is the affordable production upgrade. The mesh correction (~+75 pcm
on void at fresh fuel) is better measured separately than paid at every branch.

### The accident state, on the converged library

`rbmk_meth_buzr361` is `rbmk_a5_void.x2m` on SHEM-361 with Zr self-shielded, production mesh.
It took 31 min wall, against about 9 min for the production deck. Full-void (0.02 g/cm³) worth, pcm:

| BU, MWd/kg | 172-group DRAGON | **SHEM-361 + Zr DRAGON** | OpenMC | OpenMC / DRAGON | DRAGON $ (β on 172 groups) |
|---|---|---|---|---|---|
| 0 | +62 | **+560** | +901 ± 71 | 1.61 | +0.82 |
| 5 | −71 | **+532** | +862 ± 80 | 1.62 | +0.91 |
| **10** | +203 | **+904** | +1202 ± 95 | **1.33** | **+1.69** |
| **15** | +813 | **+1625** | +2288 ± 105 | **1.41** | **+3.27** |
| 20 | +1666 | **+2617** | +3757 ± 121 | 1.44 | +5.60 |

- **DRAGON's dip at 5 MWd/kg was a 172-group artifact.** It goes from −71 to +532, and OpenMC
  never had it. The old log's "not yet understood in detail; worth confirming" is now answered.
- **At the Unit 4 average of 10.9 MWd/kgU**, converged-library DRAGON gives about +1030 pcm,
  **≈ +1.96 $**, against OpenMC's ≈ +2.7 $. The fine-mesh correction measured at fresh fuel
  (~+75 pcm) would add to DRAGON's figure.
- **The prompt-critical straddle is resolved.** Both codes, each converged against itself, put
  complete voiding of average Unit 4 fuel above prompt critical in a single cell. This was
  reached without using the historical outcome as an input. The earlier ~0.6 $ was the 172-group
  library.
- The leftover ratio at the accident burnups, 1.33–1.41, matches the ~190 pcm residual at fresh
  fuel. That is H5/H6 territory, together with the depletion-trajectory difference (H10).

### Still open
The work order to close these is **`METHOD_CONVERGENCE_PLAN.md`**: gated phases A (fresh-fuel
residual), B (accident state), C (production upgrade), D (validation against the Kurchatov
critical experiments).

1. **The remaining ~190 pcm** (nominal and void): H5 (MOC, anisotropic scattering) and H6
   (radial self-shielding in the pellet) are the next tests.
2. **The accident state** is now bracketed at +1.96 $ (DRAGON, converged library) to +2.7 $
   (OpenMC). H10 (transfer OpenMC's depleted isotopics into DRAGON) would separate the depletion
   difference from the transport difference at 10 MWd/kg.
3. **Measured data.** The Kurchatov critical experiments turn out not to be specified in
   [ALX98], and are impurity-limited. See the next section.
4. **The production library.** The COMPO, the A5 deck and every downstream number are on the
   172-group library, which this study shows is not converged for this cell. Rebuilding on
   SHEM-361 + Zr is the obvious consequence, but it should wait for (2).

## Third-party benchmark: the RBMK Safety Review Project cell — 2026-09-25

Alexeev et al. (1998, [ALX98]) and Parisi & D'Auria (2007, [PAR07]) were obtained and read.
They are catalogued, with what each does and does not provide, in `sources/README.md`.

**The Kurchatov critical experiments are not usable as specified.** [ALX98] describes the
facility and seven configurations but only plots the measured k_eff and void effects. The full
specifications are in three other documents: Behrens et al. 1994 (Bremen report), Kuzmin 1993
(RRC-KI) and Behrens et al., *Nucl. Technol.* 114 (1996) 1. More importantly, the graphite's
B/Cd impurity is unknown and worth ≈ 1 % in k. The authors tuned it per code, and say
themselves that this keeps the experiments from being a benchmark. At best they constrain
*relative* void effects.

**[PAR07] reproduces our finding independently.** Their DRAGON (the same collision-probability
solver, but the IAEA WLUP 172-group library) against NIKIET's MCNP4C gives a void Δk of 0.03883
vs 0.04924, **−21 %**, and −32 % on 69 groups. That's a different group with a different library,
and the same deficit with the same dependence on group structure.

**[ALX98] Tables 3–4 fully specify a single-cell benchmark** (cold, fresh, 2 %, water at
1 g/cm³, Zr or Al tube), with answers from MCNP4A, MCU-3, MONK, WIMS-D/E and APOLLO-2. It is
transcribed once in `openmc/srp94_common.py`, which builds the OpenMC model and generates
`rbmk_srp94_*.x2m`. The assumptions the paper doesn't settle are stated in that file, and none
are tuned: 300 K throughout; "voided" removes the water but keeps the spacer steel; rod phase
π/12. Void effect here is Δk × 100, as the paper plots it.

| Zr tube | k∞ watered | k∞ voided | void Δk (%) |
|---|---|---|---|
| MCNP4A, ENDF/B-VI/L | 1.2778 | 1.3263 | 4.85 ± 0.04 |
| MCNP4A, ENDF/B-VI/B | 1.2806 | 1.3285 | 4.81 ± 0.04 |
| MCU-3 | 1.2800 | 1.3280 | 4.80 ± 0.05 |
| **OpenMC, VIII.1** | **1.27655 ± 0.00025** | *killed, re-run on GB10* | — |
| DRAGON, 172 groups | 1.2759 | 1.3005 | **2.46** |
| DRAGON, SHEM-361 + Zr self-shielded | 1.2829 | 1.3174 | **3.45** |

| Al tube | k∞ watered | k∞ voided | void Δk (%) |
|---|---|---|---|
| MCNP4A, ENDF/B-VI/L | 1.2714 | 1.3247 | 5.33 ± 0.04 |
| MCU-3 (3lib / 2lib) | 1.2740 / 1.2733 | 1.3283 / 1.3280 | 5.43 / 5.47 |
| MONK-5W · WIMS-E · WIMS-D · APOLLO-2 | 1.2838 · 1.2884 · 1.2925 · 1.2946 | 1.3310 · 1.3355 · 1.3371 · 1.3404 | 4.72 · 4.71 · 4.45 · 4.57 |
| DRAGON, 172 groups | 1.2717 | 1.3020 | **3.03** |
| DRAGON, SHEM-361 | 1.2756 | 1.3134 | **3.77** |

The published values were read off [ALX98] Figs 8–9 to ±0.001 in k; its error bars are 3σ, and
±σ is shown above.

What this shows:
- **Our OpenMC reproduces two independent Monte Carlo codes.** Watered k∞ 1.27655 is within
  0.1–0.4 % of MCNP and MCU, on different data (ENDF/B-VI against VIII.1).
- **Production DRAGON gives half the Monte Carlo void effect on a third-party cell** (2.46 vs
  4.80–4.85 %). On the Al variant it sits well below even the 1990s deterministic codes (3.03
  vs 4.45–4.72).
- **The converged-library settings close part of it** (2.46 → 3.45, Zr tube). The 4× mesh
  (`best_zr`, `best_al`) was killed before finishing. The residual on this cold, fully-watered
  cell is proportionally larger than on our hot cell, which makes this cell the sharper test
  for Phase A (MOC, rim self-shielding).
- The deterministic codes' higher k∞ in [ALX98] contrasts with our DRAGON, whose k∞ is close
  to OpenMC's on this cell (1.2759 vs 1.2766), yet whose void effect is far lower. Here too the
  gap is in how the codes respond to voiding, not in the base k.

### Hand-off to the GB10 (runs killed on the x86 box, 2026-09-25)
- `rbmk_srp94_best_zr`, `rbmk_srp94_best_al` (SHEM-361, Zr self-shielded, 4× mesh): about 1.5 h
  each on this box.
- OpenMC benchmark cell, Zr and Al, watered and voided: `openmc/srp94_run.py run Zr`, then `run
  Al`. Then `srp94_run.py table`.
- Everything is generated. Regenerate first with `python openmc/srp94_common.py` and `python
  decks/scripts/gen_meth.py`, then `tools/link_decks.sh`.
- Don't co-schedule DRAGON with a multi-threaded OpenMC on the same physical cores. On the x86
  box that made the COMPO 4× slower.

*Done on the GB10, 2026-09-25 (3); see the next section. The GB10 reproduces the x86 DRAGON
numbers to every printed digit (`ctrl` 1.304123, `buzr361`'s void row, the SRP `d172` / `d361`
decks).*

## Phase A–B on the GB10: the void gap closes to within its criterion — 2026-09-25 (3)

The work order is `METHOD_CONVERGENCE_PLAN.md`. Every number below regenerates from a script:
- `openmc/method_table.py`: the hot cell, fresh fuel, `rbmk_meth_*`, plus OpenMC's `method_study.json`;
- `openmc/srp94_run.py table`: the SRP-1994 cell;
- the `VOIDTAB` rows of `rbmk_meth_buzr361`, for burnup.

The machine is the GB10 (20 cores). DRAGON runs one job per core on cores 0–7, and OpenMC runs
12 threads on cores 8–19.

### The register, closed out

Every row is one change against `zr361`: SHEM-361, Zr self-shielded, production mesh and
solver. Δ is the change in pcm of ρ.

| ID | Hypothesis | Variant | Δ nominal | Δ full void | Verdict |
|---|---|---|---|---|---|
| A3 | groups converged at 361 | `zr370` (SHEM-370) | +15 | +2 | **converged** (< 20 pcm) |
| H5 | isotropic scattering + transport correction | `moc1` (MOC, same physics) | −1 | +5 | MOC reproduces CP |
| | | `moc2` (MOC, P1, `CTRA NONE`) | +1 | **+79** | **confirmed** |
| | | `moc3` (P2) | 0 | +80 | P1 is enough |
| H6 | single-region pellet self-shielding | `rim361` (4 rings, own sets) | **−891** | −361 | **artefact, rejected** (below) |
| | | `rim361s` (4 rings, shared sets) | +21 | −4 | geometry alone is neutral |
| | | `rim361t2` (SS tracking 20/60) | −892 | — | not a tracking effect |
| H11 | temperature interpolation | `tgrid` (900 / 800 / 600 K, both codes) | DRAGON +16, OpenMC +12 | DRAGON −41, OpenMC −23 ± ~10 | **ruled out** (18 pcm) |
| A6a | Nb-93 unshielded | `zr361nonb` (Nb removed) | +361 | +59 | bound: ≤ 59 pcm on void |
| A6b | graphite table | SRP cell, OpenMC 10P vs crystal | — | Zr +0.06, Al +0.08 %Δk | small (as H1) |
| H12 | the subgroup method itself | `shi361`, `tone361` | — | — | **untested**: `SHI:`/`TONE:` stop without a message on this `SUBG` library; not pursued |

**H6 is rejected as an artefact, not as physics.** Resolving the pellet rim moves k *away* from
OpenMC by 890 pcm, and continuous-energy Monte Carlo has no pellet self-shielding approximation to
refine. The same rings with one shared self-shielding set per rod (`rim361s`) reproduce `zr361`.
So the whole shift comes from USS giving each ring its own set, which is less accurate in this
cell than the single region production uses.

**Mesh and anisotropy are not additive.** On the fine mesh, MOC's anisotropy correction is bigger
than on the production mesh. The combined variant has to be run, not assembled from the parts.

### The best-converged DRAGON, fresh fuel

`bestmoc` is SHEM-361, Zr self-shielded, flat-flux regions split 4×, and MOC with P1
scattering.

| hot cell | production | `best361` (09-25) | **`bestmoc`** | OpenMC, 10P graphite | criterion |
|---|---|---|---|---|---|
| k∞ | 1.304123 | 1.313050 | **1.312198** | 1.316350 ± 0.000265 | gap 240 pcm: **fails** 100 |
| Δρ, 0.35 g/cm³ | +191 | +435 | **+553** | +533 ± 21 | gap −20: **passes** |
| Δρ, 0.02 g/cm³ | +62 | +633 | **+763** | +821 ± 21 | gap 58 < 2σ + 5 % = 83: **passes** |

| SRP-1994 cell, void Δk (%) | Zr tube | Al tube |
|---|---|---|
| DRAGON production (172 groups) | 2.46 | 3.03 |
| DRAGON SHEM-361 (+ Zr self-shielded, Zr tube) | 3.45 | 3.77 |
| DRAGON + 4× mesh | 4.03 | 4.42 |
| DRAGON + MOC P1 | 3.76 | 4.11 |
| **DRAGON `bestmoc` (all of the above)** | **4.59** | **5.04** |
| OpenMC VIII.1, crystal / 10P graphite | 4.71 / 4.77 ± 0.04 | 5.16 / 5.24 ± 0.04 |
| OpenMC VIII.0, crystal | 4.71 | 5.11 |
| MCNP4A (ENDF/B-VI) / MCU-3, [ALX98] | 4.81–4.85 / 4.80 | 5.28–5.33 / 5.43–5.47 |
| MCNP4A (ENDF/B-IV), [ALX98] | 4.29 | — |

- **D0 passes for OpenMC.** Its void Δk is 2–6 % below MCNP/MCU on ENDF/B-VI. VIII.0 and VIII.1
  agree to 0.05, but [ALX98]'s own MCNP moves 0.56 %Δk between ENDF/B-IV and B-VI, so a 0.1–0.2
  offset from B-VI is inside the data effect.
- **The earlier x86 watered k∞ of 1.27655 was a transcription error.** The GB10 run, same seed,
  gives 1.2756503, which is the same digits with two of them transposed.
- **DRAGON's residual on the SRP cell is now 4 %** (0.18–0.20 %Δk against OpenMC on the same
  graphite), down from 48 % / 42 % in production. The 4× mesh alone was worth +0.6 %Δk here,
  against +75 pcm on the hot cell: the cold cell with full-density water is much more
  mesh-sensitive.
- **The 8× mesh (A4), on the MOC lineage, closes the SRP gap.** CP at 8× didn't finish its first
  `ASM:` in 3 h, so it was stopped.

  | SRP void Δk (%) | 1× | 4× | **8×** | OpenMC 10P | MCNP/MCU |
  |---|---|---|---|---|---|
  | Zr tube (MOC P1) | 3.76 | 4.59 | **4.80** | 4.77 ± 0.04 | 4.80–4.85 |
  | Al tube (MOC P1) | 4.11 | 5.04 | **5.27** | 5.24 ± 0.04 | 5.28–5.47 |

  DRAGON now meets the "referenced" criterion on the third-party cell. The mesh is *not*
  converged by the plan's 20 pcm test, though: 4→8 still moved void by +0.21 / +0.23 %Δk
  (1→4: +0.58 / +0.62). A geometric extrapolation puts the limit near 4.92 / 5.41, about 3 %
  above OpenMC. So the exact 8× match is partly where the sequence happens to sit. Watered k∞
  at 8× is 1.2712 / 1.2625, against OpenMC's 1.2753 / 1.2673: the same ~250–300 pcm nominal
  residual as the hot cell. The hot-cell `bestmoc8` is still running (> 7 h).

**The nominal-k residual (~240 pcm) is attributed, not closed.** It sits in resonance escape,
from U-238 and Zr, as the 09-25 four-factor split showed. None of H1–H11 closes it. The rim
refinement went the wrong way. The only hypothesis left is the subgroup method itself (H12), and
that couldn't be tested on this library. The void effect is the quantity Tier A needs, and it
passes, so per the Gate A decision the residual is reported and bounded rather than chased.

### The accident state: depletion vs transport (B1, H10)

`openmc/isotopics_to_dragon.py` writes OpenMC's depleted fuel into `RbmkLibOMC<bu>.c2m`, and
DRAGON runs it at fixed composition (`omc10`, `omc15`). Nominal k∞ and full-void Δρ, with
DRAGON on `zr361` settings:

| | 10 MWd/kg: k∞ | Δρ | 15 MWd/kg: k∞ | Δρ |
|---|---|---|---|---|
| DRAGON, own depletion (`buzr361`) | 1.09903 | +904 | 1.01234 | +1625 |
| DRAGON, OpenMC fuel, OpenMC normalised on deposited energy (`oed`) | 1.09585 | +952 | 1.00541 | +1781 |
| DRAGON, OpenMC fuel, OpenMC normalised on fission Q (`omc`) | 1.08903 | +1000 | 0.99504 | +1901 |
| OpenMC, fission Q, crystal graphite (x86 and GB10 runs) | 1.0932 / 1.0916 | +1202 / +1336 ± 100 | 0.9985 / 0.9976 | +2288 / +2554 ± 105 |
| DRAGON, OpenMC fuel (fission Q), MOC P1 (`omc*moc`) | 1.08937 | +1097 | 0.99539 | +2013 |

- **Transport, on identical fuel.** DRAGON sits ~350 pcm below OpenMC in nominal k at 10 and 15
  MWd/kg, the same as fresh (330 pcm with crystal graphite). The transport difference doesn't
  grow with burnup.
- **Depletion: most of it is a burnup-scale convention.** OpenMC's default normalisation
  (`fission-q`) counts 193.4 MeV per U-235 fission and no capture energy. DRAGON normalises on its
  library's H-factor. Re-depleting OpenMC on deposited energy (`RBMK_NORM=energy-deposition`)
  cuts the fuel-composition difference from 835 → 264 pcm (10 MWd/kg) and 1718 → 680 pcm (15).
  So **60–70 % of the depletion-trajectory effect is how many fissions each code books per
  MWd**, not physics. For comparing against Unit 4's 10.9 MWd/kgU, which is thermal energy, the
  deposited-energy scale is the right one. Every OpenMC burnup result before today is on the
  fission-Q scale, and so sits at slightly higher effective burnup than its label.
- What remains of the depletion difference (+48 pcm on void at 10 MWd/kg, +156 at 15) is
  chains and yields, and is left attributed at that size.
- **H5 at burnup:** MOC P1 adds +97 (10) and +112 (15), against +79 fresh.
- **Gate B: the matched comparison.** `openmc/accident_ref.py` (→ `accident_ref.json`) gives
  OpenMC on deposited-energy depletion and 10P graphite, 50k × 250 active. `oedbest<bu>` is
  DRAGON's `bestmoc` settings (SHEM-361, Zr SS, 4× mesh, MOC P1) on *the same fuel*.

  | full-void Δρ (pcm) | 10 MWd/kg | 15 MWd/kg | 10.9 MWd/kgU (Unit 4) |
  |---|---|---|---|
  | OpenMC, matched | +1275 ± 29 (k 1.09929) | +2253 ± 33 (k 1.00902) | +1451 = **2.75 $** |
  | DRAGON `oedbest`, same fuel | +1196 (k 1.09485), **−6.2 %** | +2047 (k 1.00463), **−9.1 %** | +1349 = **2.55 $** |
  | DRAGON best, own depletion (`oedbest` − (`oed` − `buzr361`)) | +1148, −10.0 % | +1891, −16.1 % | +1282 = **2.43 $** |

  The 10.9 MWd/kgU column interpolates linearly, with β 528 pcm from the 172-group β curve.
  - **Transport meets Gate B:** within 10 % at both burnups.
  - **With each code's own depletion it misses at 15 MWd/kg** (−16 %). The excess is the
    depletion difference left after the burnup scales are matched: 48 / 156 pcm of void, from
    chains and yields. Per the Gate B decision, that residual is attributed and bounded, not
    chased.
  - **Nominal k on identical depleted fuel:** DRAGON is 370 / 430 pcm below OpenMC, against
    240 fresh. The resonance-escape residual grows a little with Pu.
  - **The headline.** At Unit 4's average burnup, complete voiding of one channel is **+2.4 to
    +2.75 $** across every converged variant of both codes. The accident-state bracket (+1.96 $
    DRAGON / +2.7 $ OpenMC on 09-25) has narrowed from a 38 % spread to 13 %, and every point in
    it is above prompt critical.


### Depletion step size — 2026-09-26

The rebuilt COMPO deck (2.5 MWd/kg steps through 5–15) gave k∞ 1.097439 at 10 MWd/kg, against
`rbmk_a5_void`'s 1.099025 on identical settings. `rbmk_meth_dstep*` are `rbmk_a5_void` with
only the burnup list, or `EVO:` extrapolation, changed. They ran on `spark` (the partner GB10),
which reproduces this machine bit for bit.

| k∞ / full-void Δρ (pcm) | 10 MWd/kg | 15 | 20 |
|---|---|---|---|
| 5 MWd/kg steps, `NOEX` (production to date) | 1.09903 / +904 | 1.01234 / +1625 | 0.92900 / +2617 |
| 2.5, `NOEX` (`dstep25`) | 1.09791 / +907 | 1.00939 / +1652 | 0.92462 / +2680 |
| 1.25, `NOEX` (`dstep125`) | 1.09746 / +908 | 1.00819 / +1663 | 0.92290 / +2705 |
| 5, `EXTR 1` (`dstep50x`) | 1.09839 / +887 | 1.00735 / +1650 | 0.92135 / +2701 |

- **Void worth is nearly step-converged:** within 0.5 % at 10 MWd/kg and 3 % at 15.
- **Nominal k∞ is not.** 5 MWd/kg `NOEX` steps overstate it by ~200 pcm (10 MWd/kg) and ~530 pcm
  (15). The error is first order; the limit is ≈ 1.0970 / 1.0070.
- **Consequence for B1.** Step-converged DRAGON sits ~190–200 pcm below OpenMC's matched
  depletion at both burnups, a steady offset. The fuel-composition residual is ~100 / 160 pcm of
  nominal ρ, not 264 / 680; much of the earlier number was DRAGON's step error. On void worth
  the chain/yield residual is 44 / 111 pcm (was 48 / 156). DRAGON's own-depletion full-void worth
  becomes 1152 / 1936 pcm, −9.7 % / −14.1 % from OpenMC. The transport-only Gate B verdict is
  unaffected.
- **The rebuilt COMPO** (`NOEX`, 2.5 MWd/kg steps in 5–15) carries ~75–130 pcm of step error in
  nominal k over the accident range, and < 1 % in void worth. 2.5 MWd/kg with `EXTR 1` is the
  candidate for the next rebuild (untested).

## Phase C: production on the converged library — 2026-09-26

`METHOD_CONVERGENCE_PLAN.md` C1–C5. Gate C (every production number regenerated) is met for
the lattice level. **Superseded:** every production number before this section was computed on
the 172-group library with Zr unshielded. That covers k∞ 1.304123, the 630-point COMPO, the
"~1.9 multiplier", and the 09-24 (4) dollars table. For the record only.

| Step | What changed | Gate |
|---|---|---|
| C1 | `RbmkLib.c2m` gives the Zr of MIX 2 / 8 / 9 self-shielding sets 3 / 4 / 5. The old composition is kept only as `RbmkLibU.c2m` (do-not-use banner) for the 172-group method-study controls. `RbmkLibZ` and `RbmkLibP` are in `quarantine/method_study/`. | `rbmk_cell_a3` **k∞ 1.313968** (was 1.304123), guardrail passed |
| C2 | `decks/common/rbmk.access` binds the seven production decks to SHEM-361, with `USS: PASS 2 MAXST 300`. Control decks keep their own hooks. | `h2otest` = `zr361` and `a5_void` = `buzr361`, both bit for bit |
| C3 | Mesh and MOC are **not** in production: MOC at 4× costs ~2 h per state, which is impossible at 840 points. They are carried as a measured additive correction, variant A′ in `openmc/void_bracket.py`: +204 / +244 / +266 pcm on full void at 0 / 10 / 15 MWd/kg. | measured, never fitted |
| C4 | COMPO rebuilt with burnup nodes at 7.5 and 12.5: 8 × 7 × 5 × 3 = **840 points**, `_ACompo` 152 MB, 14.7 h on the GB10. The off-grid deck's burnup indices were remapped (10 → 5, 20 → 8). | round trip **6.7 pcm** worst (≤ 10); off-grid **21.2 pcm** worst (≤ 30); β monotone 0.006822 → 0.004677 |
| C5 | `void_bracket.py` rewritten: additive variants instead of the r multiplier (below). | table below |

**The void bracket at nominal temperatures** (`python openmc/void_bracket.py`; β from
`rbmk_a5b_beta.don` on the new COMPO):

| BU, MWd/kg | A: DRAGON COMPO | A′: + mesh/MOC | B: OpenMC matched | β |
|---|---|---|---|---|
| 0 | +560 = +0.82 $ | +764 = +1.12 $ | +821 = +1.20 $ | 0.006822 |
| 5 | +537 = +0.91 $ | +761 = +1.29 $ | +849 = +1.44 $ | 0.005877 |
| 10 | +913 = +1.71 $ | +1157 = +2.16 $ | +1276 = +2.38 $ | 0.005355 |
| **10.9 (Unit 4 average)** | **+1034 = +1.95 $** | **+1282 = +2.42 $** | **+1438 = +2.72 $** | 0.005288 |
| 12.5 | +1248 = +2.41 $ | +1503 = +2.91 $ | +1725 = +3.34 $ | 0.005169 |
| 15 | +1661 = +3.33 $ | +1927 = +3.87 $ | +2254 = +4.52 $ | 0.004983 |
| 20 | +2645 = +5.66 $ | +2911 = +6.22 $ ‡ | +3238 = +6.92 $ ‡ | 0.004677 |

‡ Corrections above 15 MWd/kg are held at their 15 MWd/kg values: there is no matched point at
20. OpenMC's unmatched energy-deposition branch at 20 gives +3671 ± 127 (crystal graphite), so
B is likely low there. Unit 4 had nothing near 20.

- **A′ is the converged-DRAGON answer, and it is the one Tier A should carry**, with B as the
  bracket's upper end.
- **A is the production COMPO as it stands.** It is now above 1 $ at the Unit 4 average, where the
  172-group COMPO gave ~0.6 $.
- **Every variant puts full voiding of average Unit 4 fuel above prompt critical.**
- For A7/A8: the corrections are additive in Δρ, as functions of (BU, void fraction), applied on
  top of the COMPO's void branch. `void_bracket.corrections(bu, dca)` returns all three.

## Where the project stands, and the reordered plan — 2026-09-26 (2)

**What the method-convergence segment bought.**
- **Before:** DRAGON and OpenMC disagreed on whether voiding average Unit 4 fuel is prompt critical
  (+0.6 $ vs +2.7 $).
- **Now:** every converged variant of both codes gives +2.4 to +2.75 $. The spread fell from
  38 % to 13 %, and the historical outcome was never an input.
- **Checked against a third party.** Our OpenMC reproduces the 1990s MCNP / MCU results on the
  SRP-1994 cell.
- **In production.** The fixes are in `RbmkLib` and the 840-point COMPO.

**What caused the gap, largest first:**
1. The 172-group energy mesh through the U-238 resonances.
2. Zr left at infinite dilution.
3. The flat-flux mesh.
4. Isotropic scattering with a transport correction.
5. The two codes' different burnup scales (fission-Q vs H-factor).
6. DRAGON's 5 MWd/kg depletion steps. These affect nominal k only.

**Confidence now:**

| Level | Confidence | Basis |
|---|---|---|
| Fuel-cell void worth | **good, about ±10 %** | two methods plus a third-party benchmark |
| Fuel-cell absolute k∞ | **moderate, a few hundred pcm** | 240–430 pcm DRAGON/OpenMC residual (attributed); 75–130 pcm step error in the COMPO |
| Whole core: rods, map, TH, transient | **none yet** | not built, or not verified |
| Against measurement | **none at any level** | everything so far is verification |

The single-channel full-void worth is not the core void reactivity. That also depends on leakage,
the rod pattern and the axial power shape: exactly the parts still to build.

**Reordered Tier A** (PROJECT_PLAN.md roadmap; TIER_A_WORKPLAN.md):
- **A6** — CPS channel cells, on the A′ basis (`A6_CPS_PLAN.md`).
- **A6b** — Xe axis + fuel COMPO rebuild with `EXTR` depletion. Unit 4 was heavily
  Xe-poisoned at 01:23.
- **A6c** — Smolensk-3 cold start-up ([BEH96]), promoted from the deferred Phase D: the first
  measured core-level reference.
- **A6d** — Unit 4 initial state at 01:22:30 as a sourced deliverable. It is likely the dominant
  uncertainty in A8.
- **A7, A8, A9** — then Tier B. A8 now runs under bracket variants A′ and B, stops at a sourced
  fuel-failure criterion, and is compared (not tuned) with INSAG-7 Appendix II's three
  reconstructions.

---

## A6: the CPS channel — 2026-09-27

Work order `A6_CPS_PLAN.md`. Branch `tier-a/a6`, six commits, nothing pushed. The rod cells are
built and verified against an independent method; the step that turns them into core data is
where it breaks, and the cause is identified rather than papered over.

### A6.1 — the sources

| Input | Value used | Source / status |
|---|---|---|
| Absorber | B₄C in an aluminium sleeve, САВ-1 alloy | closed: [SF] + [OST] agree on the alloy |
| B₄C density | 2.0 g/cm³, bracket **1.7–2.3** | **found in no source.** The single largest open input for rod worth |
| Displacer graphite | 1.65 g/cm³, bracket 1.50–1.73, grade GR-93 | [CAST] |
| Additional absorbers in Unit 4, 1986 | one | INSAG-7 printed pp. 67 and 107 |
| Rod and displacer geometry | as in `openmc/cps_common.py` | [D], [SF] |

Status **PASSED**, with the B₄C density and the rod types carried as open inputs for A8's
sensitivity rather than guessed at.

### A6.2 — one transcription, two codes

`openmc/cps_common.py` is the only place the CPS channel is written down. It generates the DRAGON
library and geometry procedures, the A6.3 supercell decks, the A6.4 COMPO decks, the DONJON gate
decks and the OpenMC supercells, so the two codes cannot drift apart by transcription. It reads
the Zr-2.5Nb composition out of `RbmkLib.c2m` by regex rather than copying it (standing rule 6).
`openmc/rbmk_cell.py` was refactored so the single cell and the supercells share `fuel_cells()`;
the refactor is bit-identical on k (1.3138603888586933 vs …668).

**GATE A6.2 passed.** The 3×3 FUEL-centre supercell reproduces the single cell to **+2.8 pcm**
in DRAGON and **+2 pcm** in OpenMC (1.31638 vs 1.31635).

### A6.3 — section worths against OpenMC, and the A′ correction

`python openmc/cps_verify.py table`. Worths are Δρ(type − WAT) on the 3×3 supercell; "prod" is the
production settings, "conv" is 4× mesh with MOC P1.

```
 BU   dca     worth  OpenMC   sd    prod    conv  prod%  conv%  A-corr
  0  0.72   ABS-WAT   -7511   26   -8706   -8236    -16    -10    +470
  0  0.72   DSP-WAT   +3285   22   +3000   +3084     -9     -6     +84
  0  0.72  VOID-WAT   +4363   21   +3954   +4112     -9     -6    +158
  0  0.02   ABS-WAT  -10236   26  -11764  -10834    -15     -6    +931
  0  0.02   DSP-WAT   +4209   22   +3702   +3762    -12    -11     +60
  0  0.02  VOID-WAT   +5397   21   +4703   +4796    -13    -11     +93
 10  0.72   ABS-WAT   -8955   32  -10454   -9890    -17    -10    +564
 10  0.72   DSP-WAT   +3964   29   +3553   +3671    -10     -7    +117
 10  0.72  VOID-WAT   +5155   28   +4644   +4857    -10     -6    +214
 10  0.02   ABS-WAT  -12158   36  -13873  -12766    -14     -5   +1107
 10  0.02   DSP-WAT   +4871   29   +4258   +4360    -13    -10    +102
 10  0.02  VOID-WAT   +6189   29   +5317   +5463    -14    -12    +147
```

**GATE A6.3 missed, now on the complete table** (the last two converged states landed
2026-09-29 after ~44 h each on `spark`). Production DRAGON is 9–17 % low on every section worth.
Convergence closes roughly half the absorber gap but leaves 5–12 %, so the 5 % criterion is met
in one of twelve cells. Per the standing decision for Gate A, the residual is **attributed and carried, not
fitted**: the production-minus-converged difference is the A′ correction for CPS sections,
+60 to +1107 pcm, tabulated per state.

The sign is consistent with everything found in the method-convergence segment — DRAGON
under-predicts reactivity differences that depend on resonance absorption and on flux depression
next to a strong absorber — and with [PAR07]'s independent −21 % against MCNP.

**The 3×3 supercell is not spatially converged either.** A wider OpenMC supercell moves the
worths substantially:

```
Supercell shape (OpenMC r45 minus 3x3 worth), fresh, pcm
  dca 0.72: ABS-WAT   -1236  DSP-WAT    +471  VOID-WAT    +648
  dca 0.02: ABS-WAT   -1748  DSP-WAT    +616  VOID-WAT    +829
```

The rod's influence reaches past the first ring of fuel. That is not an error in the supercell —
the core solve is what resolves it — but it is the same physics that breaks A6.4 below, and it
sets the scale of the neighbour effect: of order 1000 pcm, not 100.

**Where the residual actually lives — 2026-09-28.** A worth is a difference of two k's, so a
worth error says nothing about *which* of the two states is wrong. Comparing absolute supercell
k does (`cps_verify.py table`, last block):

```
 BU   dca  type  OpenMC k    prod k   d_rho    conv k   d_rho
  0  0.72   WAT   1.24292   1.24995    +452   1.24437     +93
  0  0.72   ABS   1.13679   1.12728    -743   1.12868    -632
  0  0.72   DSP   1.29584   1.29864    +167   1.29402    -108
  0  0.72  VOID   1.31418   1.31493     +43   1.31147    -157
  0  0.02   WAT   1.24752   1.25718    +616   1.25665    +582
  0  0.02   ABS   1.10626   1.09520    -912   1.10607     -15
  0  0.02   DSP   1.31665   1.31854    +109   1.31901    +136
  0  0.02  VOID   1.33757   1.33619     -77   1.33725     -18
 10  0.72   WAT   1.04025   1.04557    +489   1.04090     +60
 10  0.72   ABS   0.95161   0.94254   -1010   0.94375    -875
 10  0.72   DSP   1.08499   1.08591     +78   1.08225    -233
 10  0.72  VOID   1.09920   1.09892     -23   1.09633    -238
 10  0.02   WAT   1.05277   1.05934    +589   1.05882    +543
 10  0.02   ABS   0.93331   0.92360   -1126   0.93274     -66
 10  0.02   DSP   1.10967   1.10938     -24   1.11006     +31
 10  0.02  VOID   1.12615   1.12256    -284   1.12383    -183
```

Converged DRAGON reproduces OpenMC's **displacer and drained-channel** supercells to 100–240 pcm.
The −7 to −10 % worth errors are almost entirely the **WAT baseline being 450–620 pcm too
reactive**, and at voided coolant the converged settings do not touch it at all (+616 → +582).
The absorber is a separate, genuine −630 to −1130 pcm over-absorption.

So A6.3 is not one diffuse method gap but two specific findable things, and the larger of them
sits in the water-filled CPS channel — a single cheap cell, not a 30-hour supercell. That
reopens the gate as something to close rather than attribute.

**The WAT/VOID pair is already the isolating experiment.** `SECTIONS['WAT']` and
`SECTIONS['VOID']` are the *same* geometry — one annulus out to the tube, split four ways —
differing only in whether it holds water or helium. Same Zr tube, same graphite, same eight fuel
neighbours. Water is 450–620 pcm off; helium is 43 to −157. The error is in the water column and
nothing else.

**First hypothesis: eliminated.** The draglib carries `H1_H2O` at only 293.6 / 350 / 400 / 450 /
500 / 600 K, and `LIBDRA.f:68` interpolates cubically in √T (`NOTX=3`), so the nominal 323.15 K
sits 29.5 K off the nearest node in the steepest part of the bound-hydrogen kernel — while
OpenMC's `c_H_in_H2O` has points at 320 and 324 K. That is a clean mechanism, and it is wrong.
Running both codes with the CPS water at exactly 293.6 K, where `LIBLEX.f:46` returns `TERP = 1`
and DRAGON interpolates nothing at all (`rbmk_cps_a63_twat.x2m`, and the matching OpenMC cases):

```
Track C: CPS water on a draglib temperature node vs interpolated
  dca   T_wat    DRAGON    OpenMC   d_rho
 0.72  323.15   1.24995   1.24292    +452
 0.72  293.60   1.24788   1.24000    +509
 0.02  323.15   1.25718   1.24752    +616
 0.02  293.60   1.25453   1.24360    +701
```

The gap does not close at either density; it grows, 452 → 509 and 616 → 701. Temperature
interpolation of the thermal scattering law is **not** the mechanism. The CPS water temperature
stays a free argument only because the test needed it.

**What the completed table points at instead.** With all twelve converged states in, the
residual has a structure that a single localised data error would not produce — convergence
fixes each state at one coolant density and not the other, and the two types fail on opposite
sides:

| | dca 0.72 | dca 0.02 |
|---|---|---|
| WAT, converged | **+93 / +60** (fixed) | +582 / +543 (untouched) |
| ABS, converged | −632 / −875 (barely moved) | **−15 / −66** (fixed) |

So it is not "the water column is wrong". It is that the converged settings — 4× mesh, MOC with
P1, finer tracking, all changed together — help the water when the surrounding fuel is wet and
help the absorber when it is voided. Both are spectral: what changes between dca 0.72 and 0.02
is how hard the thermal flux is driven into the CPS channel from outside.

Next candidates, in order: separate the converged bundle, since it changes four things at once
and the answer is evidently in which one (cheapest first — mesh alone, then MOC alone); the
transport treatment of the column, production being collision probabilities with a transport
correction through 8.2 cm of bound hydrogen; then the multigroup thermal scattering data.

### A6.4 — the homogenisation is exact; the neighbour data is not

`python openmc/cps_verify.py a64`, 18 states (BU 0 / 10.9 / 15 MWd/kg × dca 0.72 / 0.35 / 0.02 ×
T_F 900 / 1500 K). Two configurations of the same DONJON supercell:

| Configuration | vs DRAGON's supercell |
|---|---|
| **A64S** — all nine cells from the CPS MULTICOMPO | **≤ 0.1 % on every worth, ~1 pcm on k** |
| **A64V** — the eight fuel cells from the fuel COMPO (what the core will do) | absorber −2.5 to +2.6 %, displacer **−7 to −9 %**, drained channel **−9 to −10.5 %** |

So the two-group collapse, the SPH equivalence and the DONJON solver are all exact. The entire
error is the neighbour data: an infinite-lattice fuel cell is not a fuel cell sitting next to a
rod, and the fuel COMPO has no axis that could know which it is. It is worst on the *positive*
worths — the displacer effect the whole of A8 turns on — so it cannot be carried as a correction
and ignored.

One detail worth keeping: the absorber error **changes sign with coolant density** (−2.5 % at
0.72, ≈ 0 at 0.35, +2.4 % at 0.02) and passes the 1 % gate at 0.35 by coincidence. A correction
table fitted at one density would have the wrong sign at another. The displacer and void errors
do not change sign and barely move with burnup or fuel temperature, which is what makes them look
like a fixed geometric defect rather than a data-range problem.

Two method choices were settled on the way, neither by fitting:

- **SPH normalisation `ASYM 1`** (pin a fuel cell's factor to 1, so the rod cell carries the
  correction) over `STD` (average over all nine). Chosen on that principle; it also happens to be
  3× better.
- **`TRIVAT: DUAL 1 1`, not the core's `MCFD 1`.** Under MCFD the SPH iteration oscillates and
  never converges in 200 iterations under any normalisation, and on the full deck it ended in a
  segfault in `TRI1GSO`. DUAL converges in 18–41. A2 chose MCFD for speed, before any rod cell
  existed; **from A6.5 on the core must use the discretisation SPH was computed with.**

**How much that second choice was worth — 2026-09-28.** The gate decks had been computing an
MCFD variant (`A64M`) all along and nobody had read it out. Over all 18 states
(`cps_verify.py a64`, last block):

```
  DISCRETISATION: worth error vs DRAGON over all states, %
      worth        DUAL 1 1 (A64V)          MCFD 1 (A64M)
    ABS-WAT           -2.8 to +3.2         +30.6 to +34.4
    DSP-WAT           -9.1 to -6.8           -7.2 to -1.1
   VOID-WAT          -10.5 to -8.5           -5.0 to +3.1
```

**`MCFD 1` loses a third of the absorber worth**, consistently, at every burnup, coolant density
and fuel temperature. One mesh-centred point per 25 cm node cannot represent the flux depression
in a black absorber. The switch was adopted to make SPH converge; it turns out to be mandatory on
accuracy grounds, and the old setting would have cost ~1/3 of all-rods-in worth without ever
failing a gate.

**The control, and it closes the question harder than the number does.** `A64M` applies
DUAL-derived SPH factors to an MCFD solve, so part of that 31 % could have been the mismatch
rather than MCFD itself. `rbmk_cps_a64_smkm.x2m` is the same smoke deck with SPH computed under
`MCFD 1` too — identical transport (both print k∞ 1.127280), differing only in the discretisation
the equivalence is built on:

| SPH discretisation | outcome |
|---|---|
| `DUAL 1 1` | oscillation warnings early, **converged in 40 iterations** |
| `MCFD 1` | oscillates from iteration 5, hits the 200 cap, `SPHEQU: MAX. NUMBER OF ITERATIONS IS REACHED` |

So there is no clean MCFD number to quote, because **MCFD cannot carry a converged SPH
equivalence on this geometry at all**. The 31–34 % is the best available measure of what it
costs; the operative fact is that the core could not have used MCFD with rod data whatever the
size of the error.

**And it costs nothing to leave.** `decks/Donjon/data/rbmk_core_3d_dual.don` is
`rbmk_core_3d_realistic.don` with the tracking line changed and nothing else (still A2's
wrong-on-purpose IAEA constants — this is solver timing, not physics). Matched runs, same
machine, same day:

| solver | wall | max RSS | k | unknowns/group |
|---|---|---|---|---|
| `MCFD 1` | 1.95 s | 39 MB | 1.123062 | — |
| `DUAL 1 1` | 2.11 s | 56 MB | 1.123053 | 263 329 |

**8 % more wall clock and 17 MB.** A2's note that `DUAL 3 3` took 729 s against MCFD's 1 s had
made the mixed-dual family look unaffordable; `DUAL 1 1` is not `DUAL 3 3`. A8's transient
multiplies this by a few hundred steps and remains cheap, and 56 MB raises no memory question.

The two also agree to **0.7 pcm** on this rod-free core — which is the other half of the control.
MCFD is not generally wrong; it fails specifically when a black absorber sits inside a node,
which is exactly the claimed mechanism.

### A6.4b — the rod-cell equivalence, chosen after measuring the alternatives out

DRAGON's built-in normalisations were exhausted first, on the smoke case (DRAGON 1.126503):

| SPH normalisation | A64V error |
|---|---|
| `ASYM 1`, nine cell regions | **+135 pcm** |
| `STD`, nine cell regions | +394 pcm |
| `ASYM 1`, fuel merged to one region (`MERG CELL … REMIX`) | +254 pcm |
| `SELE_FD` / `SELE_EDF` / `STD_FISS` | refuse: no ADF directory in the macrolib |

Merging the fuel is *worse*, because the rod's factor then compensates against an eight-cell
average that matches the per-cell fuel COMPO even less well. Discontinuity factors (the textbook
fix, and DONJON reads them at `NCRLIB.f:561`) need `EDI: … ADF`, which wants named boundary
regions; our cells have no gap mixture, so the outermost graphite ring would have to serve.

**Decision: an explicit equivalence on the rod cell alone.** Per-group factors, computed per
state, that make the DONJON supercell reproduce DRAGON's with the fuel data the core actually
uses. The fuel COMPO stays untouched and there stays one dataset per rod type.

> **Corrected 2026-09-28, before anything was built.** The implementation first recorded here —
> a `SPHPicardRT`-style loop, then `SPH: <compo> OPTIM :: IDEM SPOP EQUI 'EQV_CPS'` to store the
> factors in the CPS MULTICOMPO — **would have aborted.** A read of the vendored source settles
> three things:
>
> - **`EQUI` is rejected for a MULTICOMPO.** `Dragon/src/SPH.F:440-442` aborts unless the
>   database is a SAPHYB or an APEX/MPO. What a MULTICOMPO does instead (`SPH.F:801-806` →
>   `SPHSCO.f`) is bake the factors *destructively* into the stored cross sections of that
>   calculation point — unnamed and one-way. For us that is the wanted behaviour, because the
>   CPS COMPO holds nothing but rod cells, and `NCR:` then needs no change at all.
> - **`FPSPH:` really has no mixture selection.** Its whole vocabulary is `EDIT`, `SPH PN|SN`,
>   `GRPMIN`, `GRPMAX`, `OUT-STEP-EPS`, `VAR-VAL-MIN`, `VAR-VAL-MAX`, `OUT-CONV-TST`, `ANDERSON`
>   (`FPSPH.f:192-265`); anything else hits `XABORT`, and its normalisation averages over every
>   mixture (`FPSPH.f:324-336`). Neighbours can only be held at 1 by pre-seeding per-variable
>   bounds through `UTL: OPTIM :: CREA` (`FPSPH.f:271-284, 386-389`).
> - **`SPH: … MACRO SPRD <nmerge> <ngcond> <values>`** (`SPH.F:325-348`) applies an explicit
>   per-mixture, per-group table with no optimiser at all. That is the clean lever, and it is
>   what the rod-cell equivalence will use.
>
> One trap recorded so it is not walked into twice: `ASYM <mix>` pins a mixture's factor to 1
> exactly, so merging the eight fuel cells into one macro-mixture and using `ASYM 2` looks like
> the answer. It is not — it still normalises against DRAGON's *own* fuel data, not the fuel
> COMPO's, which is the whole problem. The measurement above already shows that merge is worse.

**The plan, as corrected.** Solve the two per-group factors directly — two unknowns against two
conditions (the rod cell's group-wise volume-integrated flux, as DRAGON's transport supercell
gives it), with k left free as the check, since every worth is a k difference. Apply trial
factors through `SPRD`, drive the loop from Python (the 3×3 two-group DONJON solve takes
milliseconds), and cross-check the smoke case against upstream's own `FPSPH:` machinery with the
neighbour variables clamped. Persist by applying the converged table with a second
`SPH: EDIOBJ :: IDEM SPRD …` in the A64 DRAGON deck before `COMPO:` stores it.

### A6d — the Unit 4 channel map, from registering two digitisations

**The cartogram.** Dollezhal & Emelyanov Fig. 2.3 (Leningrad-2's initial loading) is the first
sourced RBMK core cartogram in the project. The legend OCR was deciphered and cross-checked
against the body text; the figure was then hand-digitised into `sources/derived/core_layout.xlsx`
and read back by `tools/render_core_layout.py`, which also draws a layered overlay SVG for
checking against the scan. Six digitisation errors were found by mirror and rotation symmetry
checks and each was confirmed on the scan. After correction every count closes against
Dollezhal's own text:

```
  technological channels     digitised  1693   text  1693   OK
  CPS rods                   digitised   179   text   179   OK
  DKE(v) channels            digitised    12   text    12   OK
  start-up chambers (KD)     digitised     4   text     4   OK
```

with rod types 89 РР, 21 УСП, 12 АР, 21 АЗ and 36 АЗ over-compensation — and the 21 УСП and
21 АЗ independently match INSAG-7 p. 43, which was not used to build the digitisation. One
disagreement is recorded and left standing: 282 fuel channels carry a radial detector in the
figure against 270 in the text. The overlay shows no mismatches that could account for twelve,
so it is a figure/text difference in the source.

**The registration, which is the real result.** `tools/build_unit4_map.py` places INSAG-7
Fig. II-6 (Unit 4 at 01:22:30, digitised separately by glyph detection in
`tools/digitise_fig_II6.py`) onto the Fig. 2.3 lattice. It fits **exactly**: all 223 sites at a
single offset (1, 1), nothing left over on the Unit 4 side. Two figures, twelve years and two
reactors apart, digitised by different means — each is now a check on the other.

What falls out:

- Fig. II-6's 12 blank sites are Fig. 2.3's 12 ДКЭ(в) axial-detector channels. All twelve. That
  had been an inference; it is now a measurement.
- Unit 4's 211 rods sit on Leningrad-2's 179 rod sites plus 32 that Leningrad-2 used for
  additional absorbers, unloaded channels and one fuel channel. 179 + 32 = 211, the second-stage
  rod count, with no site left to guess at.

```
  rods                 211 vs   211  OK   INSAG-7 pp. 43, 103
  fuel channels       1661 vs  1661  OK   [PAV] Table 1
  DKE(v)                12 vs    12  OK   [D] p. 57
  start-up chambers      4 vs     4  OK   [D] p. 57
  positions           1888 vs  1888  OK   sum of the above
  47 rods inserted at 01:22:30, 4346 cm in total
```

None of those five counts was an input to the map. `sources/derived/unit4_channel_map.csv` is the
deliverable. **What is still an assumption** is not *which* sites hold rods — that is measured —
but what *type* the 32 extra rods are. INSAG-7 p. 43 gives second-stage units 24 АЗ and 24 УСП
against Leningrad-2's 21 and 21, so at least 3 + 3 of the 32 are АЗ and УСП and the rest are
manual by elimination. The choice is recorded per row in `type_source` so A8 can vary it.

This also unblocks A6.5, which had been stopped by the core generator: its core is the 1661 cells
nearest the centre of a 590 cm circle, and no centred circle reproduces 1888 interspersed
positions, because circle cell counts step by 8.

### The depletion grid, and the COMPO rebuilt on it

A regression of my own, caught by the interpolation gate: the rebuilt COMPO grid had dropped the
500 MWd/t node, so the opening depletion step ran 0 → 2000. With `EXTR 1` extrapolating from the
step history, that put the whole trajectory 45–75 pcm below the `dstep25x` reference. Restoring
the node brought the rebuild to **1 pcm** of it (1.007263 vs 1.007262 at 15 MWd/kg). The opening
step matters more than any later one.

Gates on the rebuilt 840-point COMPO: **round trip 0.9 pcm** (was 6.7), **off-grid 23.9 pcm**,
β monotone 0.006822 → 0.004677. The void bracket is essentially unchanged by the rebuild:

| BU, MWd/t | A | A′ | B | A $ | A′ $ | B $ |
|---|---|---|---|---|---|---|
| 0 | +560 | +764 | +821 | +0.82 | +1.12 | +1.20 |
| 10 000 | +901 | +1145 | +1276 | +1.69 | +2.14 | +2.39 |
| **10 900** (Unit 4 average) | **+1024** | **+1273** | **+1437** | **+1.94** | **+2.41** | **+2.72** |
| 15 000 | +1666 | +1932 | +2254 | +3.35 | +3.88 | +4.53 |

### Machinery and traps found along the way

Recorded because each cost real time and each is a statement about the input, not the tool
(standing rule 3):

- `EDI: MERG CELL` with NXT tracking merges the cells but **builds no macro-geometry**
  (`EDI.f:449`); `MGEO` must be supplied explicitly.
- `SEQ_ASCII _CCompo ;` without `:: FILE './_CCompo'` is a **scratch file, deleted at `END:`**.
- `LIB:` accepts `MIX` blocks only after a `MIXS` line (`LIB.f:451`), even on an update.
- `MIXTURESVOL` is written only by the micro edit (`EDIMIC.f:925`), so the volume-fraction
  guardrail needs `MICR ALL`.
- The `MERG MIX` list must run to the highest mixture index in the geometry.
- CLE-2000 reads **columns 1–120 only** (`clelog.c:31`); the generator now asserts it and names
  the offending line.
- `rdragon` races on `/tmp/rundirN` when decks are launched simultaneously; stagger by ~10 s.
- A parser bug of my own: the CPSTAB type index prints as a bare integer, not in E-format, so the
  DRAGON columns of the A6.3 table were silently empty for a while and percentages I had quoted
  from hand arithmetic were withdrawn. The table above comes from the script.

### Where this leaves the core model

| Piece | State |
|---|---|
| Fuel-cell physics | verified in two codes plus a third-party benchmark; bracketed |
| CPS cell physics | built, verified against OpenMC, **5–11 % low and attributed** |
| CPS core data (homogenised) | **blocked on A6.4b**, −7 to −10 % on the positive worths |
| Channel map | **sourced and closed**, except the type of 32 rods |
| Core geometry and rod sites (A6.5) | unblocked, not built; needs the `DUAL 1 1` switch |
| Xe axis (A6b) | not built. Unit 4 was heavily poisoned at 01:23 |
| Measured core-level reference (A6c) | **blocked**: the Behrens/Kurchatov 1993–94 Smolensk-3 loading map is not available online |
| Coupling, transient, detectors (A7–A9) | not started |

Confidence at core level is still *none* — everything to date is verification, not validation
against measurement. The single-channel void worth is not the core void reactivity; that also
depends on leakage, the rod pattern and the axial shape, which are exactly the parts A6.5 onward
build.

**The converged runs are in.** `fresh_conv_ABS` and `oed10_conv_VOID` finished on `spark` after
roughly 44 h each (two coolant densities apiece), and the A6.3 table above is complete for the
first time. They changed nothing about the verdict — the A′ trend was already established by the
other ten — but they close the gate properly rather than on ten twelfths of the evidence.

Nearly all of that time is `FLU:`: MOC source iteration converging slowly next to B₄C with one
inner per outer in the upstream template. The cost sits in the tracking — the converged decks use
`TISO 30 120.0` against production's `TISO 15 30.0`, on 4× the mesh with `ANIS 2` — and
`cps_common.py` already exposes both knobs, so a convergence ladder on one cheap state is the way
to stop paying 44 h for a data point.

---

## Should we port DRAGON/DONJON out of Fortran? — assessed 2026-09-29

Recorded because the question will come back, and because the answer is not the obvious one.
Prompted by how often this project has been slowed by something that looked like a Fortran or
CLE-2000 limitation.

**Scale.** ~407 000 lines across Ganlib 19.5k, Utilib 13.6k, Trivac 57.2k, Dragon 239.8k,
Donjon 76.9k, plus 920 shipped `.c2m` procedures. Inside Dragon: `LIB` 31.7k, `NXT` 29.7k,
`EDI` 12.0k, `SPH` 6.7k, `USS` 6.3k. Against that, **the CLE-2000 interpreter is 8 220 lines —
2 % of the tree.**

**But the difficulties are mostly not the language.** Sorting every obstacle this project has
actually hit:

| class | count | examples |
|---|---|---|
| Fortran the language | 3 | the `TRI1GSO` segfault; `SPH.F:377` and `SPH.F:818` using unassigned integers (implicit typing, `-O1`, no warnings) |
| CLE-2000 the language | 4 | the 120-column limit; 12-character procedure names; `MODULE` declarations; `ERROR NUMBER (5000)` naming nothing |
| the shell drivers | 2 | `/tmp/rundirN` races; stale `.result` files |
| **the domain model** | **6** | `MERG CELL` + NXT building no macro-geometry; `MIXTURESVOL` only under `MICR ALL`; `LIB:` needing `MIXS` first; `B-ZONE` being an NCH-list not a grid; `FPSPH:` having no mixture selection; `SPH: … EQUI` rejected for a MULTICOMPO |

The last group is where the days went, and **a rewrite reproduces every one of it** unless it
also redesigns the physics data model — which is the actual hard part and is orthogonal to
language choice. The pain has been epistemic, not syntactic.

**What makes a port expensive is not the code.** DRAGON's value is thirty years of comparison
against measurement; a port starts at zero validation. This project has just spent a whole
segment establishing agreement with OpenMC on one cell type and is still 5–12 % out on the CPS
sections. Revalidating a ported lattice code is a bigger job than writing it. And the
performance argument is weak: the bottleneck is `FLU:` MOC source iteration, which well-tuned
Fortran wins — and we are still compiling at `-O1` with no `-march=native`.

**The ladder, and where we already are on it.**

0. Replace the shell drivers — trivial, partly done.
1. **Never hand-write CLE-2000; generate it.** `cps_common.py` and `gen_rbmk_unit4.py` already
   do, and it converts the whole syntax class into generator assertions: the column-120 failure
   of 2026-09-28 was caught by an `assert`, named its own line, and cost two minutes.
2. **Stop parsing `.result` text.** This is the remaining fragility — the CPSTAB parser silently
   matched nothing for a day, and the variant-overwrite bug in `cps_verify.table` was the same
   species.
3. **Rewrite the nodal core solver** — Tier B. Small, well understood, and validated against
   DONJON itself. Worth doing; already the plan.
4. Rewrite lattice transport — multi-year, no payoff.

**The unused lever: `5.1/PyGan/`**, in our tree and unbuilt. Upstream's own Python binding to the
Ganlib object stack: push objects onto a LIFO, call modules, get LCM objects back subscriptable
(`Fmap["STATE-VECTOR"]`). That is rung 2 and most of rung 1 while keeping every Fortran kernel
and its validation, and it would have made the `MIXTURESVOL` and `B-ZONE` discoveries a `dir()`
instead of a source read. Half a day to try building it (C extension modules against the
Fortran, so it may fight back) before entertaining any port.

**Decision: do not port.** Build PyGan, finish moving deck generation and result parsing into
Python, turn on `-O3 -march=native`, and spend the rewrite budget on Tier B, where a new
implementation has a clear validation reference and a real reason to exist (GPU, 10 Hz). The one
thing worth coveting from Julia — autodiff for adjoint and sensitivity work in A8 — is worth
revisiting only if uncertainty analysis becomes the bottleneck.

---
## Phase 0 of the transient: what a time step costs — 2026-09-30

Everything built until now was static. This is the first time the model has advanced a time
step, and the point was to find out what one costs before A8's design is built around a guess.

Three decks, all from one generator (`decks/Donjon/data/gen_kin_probe.py`) that reads
`rbmk_core_3d_dual.don` so the geometry stays single-sourced: `rbmk_kin_probe` (step form),
`rbmk_kin_ramp` (the 6-entry ramp form, keeping `MACRO_0`/`SYST_0`), and `rbmk_kin_pert`
(macrolib rebuilt and ramped every step). Cross sections are still the wrong-on-purpose IAEA
PWR constants of A2 — this measures the solver, not the reactor.

Two things had to be added to make `KINSOL:` run at all, and both are worth recording because
neither is documented where a reader would look:

* **`OVERV`, the reciprocal neutron speeds.** `KINXSD.f:152` aborts with `MISSING OVERV DATA`
  and `MAC:` supplies no default. The probe carries textbook two-group values; A8 will not
  need them, because `EDI:` writes `OVERV` (`Dragon/src/EDIPXS.f`) and `NCR:` propagates it
  (`Donjon/src/NCRMAC.f`), so the real speeds arrive from the MULTICOMPO. That path was
  checked in source before relying on it.
* **`UNIT` on `TRIVAA:`** (`TRIVAA.f:174`). It only *adds* a unitary weighting matrix, so one
  system object still serves `FLUD:` as well — no second assembly is needed.

### The measurement

`tools/kin_cost.sh`, regenerating `decks/Donjon/data/kin_cost.txt`. Each variant runs at 10 and
at 110 steps and the per-step cost is the **difference**, which cancels the fixed setup
(geometry, tracking, the `FLUD:` eigenvalue solve) exactly rather than estimating it.

| variant | s/step | max RSS | what it is |
|---|---|---|---|
| frozen-step | 0.0903 | 90.3 MB | macrolib frozen, 4-entry `KINSOL:` |
| frozen-ramp | 0.0911 | 104.7 MB | macrolib frozen, 6-entry form |
| mild-mix4 | 0.0967 | 88.0 MB | bottom inner reflector ramped; power moves 2.4e-4 |
| **severe-mix1** | **0.4301** | 88.0 MB | fuel absorption ramped; power falls 3200 → 16 MW |

**The finding that matters: a hard transient costs 4.8× a quiet one.** The first two variants
flatter the solver — with a frozen macrolib `KINSOL:` starts each step from the exact answer and
converges immediately. Quoting 0.09 s/step would have understated A8 by five-fold. Only the
severe variant is a usable number, and it is the one the budget should use.

Also measured: the **ramp form costs +14.4 MB and no time at all**, so A8 can use it freely;
and `TRIVAA:` re-assembly is ~3 ms against `KINSOL:`'s hundreds, so rebuilding the system every
step — which A8 must do, since its cross sections change every step — is not where the cost is.

### What it means for A8

4 s of transient at 1 ms is 4000 steps ≈ **29 minutes of neutronics**. At the 8–12
thermal-hydraulic Picard iterations per step that `channel_mphy.x2m` uses, that is **roughly 4
hours per scenario**, 8 for both bracket variants, plus `THM:` on 1661 channels, which is not
yet measured. A8 is hours, not days. **Tier B stays parallel rather than urgent**, which is the
question Phase 0 existed to answer.

Memory never exceeded **105 MB** in any variant, against the ~110 GB budget. The transient is
not a memory risk; the only component that could be is the Tier B GPU solver, and the arithmetic
for that is in the plan.

### Two correctness checks, not one

Nothing about the cost would be trustworthy if the kinetics were assembled wrong, so the decks
check themselves:

1. **The unperturbed transient holds power.** 3200.000 → 3199.550 MW over 110 steps, a drift of
   1.4e-4 relative — the residual of `FLUD:`'s own `EXTE 1.0E-5` convergence, not a defect.
2. **The severe transient obeys the prompt-jump relation.** Step 1 takes 3200 → 2674 MW. With
   the deck's β = 0.007219, P/P₀ = β/(β−ρ) gives ρ = −0.20 $ for that first step, and the
   power then decays on the precursor timescale rather than collapsing. Both the size of the
   prompt drop and the shape of what follows are right, which is stronger evidence than the
   flat-power check alone.

The pre-existing `FLDDIR: FAILURE OF THE NEWTON-RAPHTON ALGORIHTHM` warning appears once in
these results and once in `rbmk_core_3d_dual.don.result` — it predates the kinetics work and is
not a regression from it. k = 1.123053 against the static deck's 1.123062, 0.9 pcm apart and
inside the flux tolerance.

**Not yet established:** every number here is on IAEA PWR constants in an RBMK-shaped box. The
per-step cost should hold — it is set by the matrix structure, which the real cross sections do
not change — but the iteration counts could move, so A8 re-measures rather than assuming.

## A6.4b: the rod-cell equivalence cannot work, and here is why — 2026-09-30

The design recorded in `A6_CPS_PLAN.md` and in the A6 section above is **disproved**. Not
abandoned for effort — measured, and it fails. Three results, in the order they were found;
everything regenerates from `openmc/a64b.py` and is recorded in `openmc/a64b_findings.txt`.

### The machinery works, and was proved to before anything was built on it

`SPH:` and `OUT:` are not in DONJON's own module table (`DONDRV.F`), but `DONDRV` falls
through to `KDRDRV` and both symbols are in the binary. Confirmed on the cheapest state there
is (`rbmk_cps_a64b_smk.don`):

* `SPH: <macrolib> :: MACRO SPRD <nmix> <ngrp> <values>` applies an explicit per-mixture,
  per-group table, values in mixture-major order (`SPH.F:325-348`). **Proved applied rather
  than silently ignored by a pair of runs**, because all-factors-1.0 alone proves nothing —
  an ignored `SPRD` would also leave k unchanged. All 1.0 reproduces k exactly; 1.05/0.95 on
  the centre moves it +208 pcm. Only the pair is conclusive.
* `OUT: FLUX TRACK MACRO GEOM :: INTG MIX` integrates over the geometry's `MIX` zones
  (`OUTHOM.f:162`) and prints VOLUME, FLUX-INTG, NTOT0, SIGW00 per zone per group. Give it no
  `COND`, or it silently condenses to one group.

The new tooling reproduces the previously recorded A6.4 failure to the decimal — ABS −3.24 to
+2.84 %, DSP −9.10 to −6.72 %, VOID −10.56 to −8.48 % — which is the check that it is measuring
the same thing the old measurement did.

### 1. The recorded target is the wrong target

Solving the two rod-cell factors against the rod cell's group-wise volume-integrated flux
converges cleanly — three Newton iterations, factors remarkably consistent across all 18
states (ABS: f₁ 0.956–0.959, f₂ 0.910–0.928) — and **makes the gate worse**:

| worth | at unit factors | flux-matched |
|---|---|---|
| ABS | −3.2 to +2.8 % | −9.6 to −4.4 % |
| DSP | −9.1 to −6.7 % | −13.7 to −9.3 % |
| VOID | −10.6 to −8.5 % | −14.2 to −10.1 % |

The reason is not subtle once seen. **SPH equivalence preserves reaction rates, not fluxes.**
The rod cell's flux is low because its *neighbours* are wrong; forcing it up by lowering the
rod's own cross sections buys the flux at the cost of the absorption — and absorption is what
a rod worth is made of. The flux was made right by making the cross section wrong.

Targeting the removal rate instead, `(NTOT0 − SIGW00) × FLUX-INTG`, is the physically correct
invariant and **will not converge**: the residual stalls around 2e-4 through twenty damped
Newton iterations. That is a statement about the physics, not the solver. Raising a black
absorber's cross section depresses its flux almost proportionally, so its reaction rate — and
with it its effect on the core — is nearly invariant to its own SPH factor.

### 2. So no rod-only equivalence can close the gate, at any factor

If the rate is nearly invariant, the worth should be too. Tested directly rather than argued:
sweep the VOID rod cell's two factors over **±20 %**, a 5 × 5 grid, holding the water reference
cell at 1.0, and record the worth error over the whole grid.

```
  bu      0 dca 0.72: REF worth  3954 pcm, err over the grid  -13.26 to  -3.71 %
  bu      0 dca 0.02: REF worth  4702 pcm, err over the grid  -15.27 to  -3.52 %
  bu  10900 dca 0.72: REF worth  4704 pcm, err over the grid  -14.70 to  -3.45 %
```

**The range never straddles zero.** The gate wants 1 %; the best any rod-cell factor achieves
is −3.45 %, and that is at the edge of a deliberately wide sweep. A6.4b as conceived is not
hard, it is impossible.

### 3. What is actually wrong: the neighbours, spectrally

Comparing the supercell's own fuel-cell constants against the fuel COMPO's, cell by cell:

```
 centre VOID, bu 0, dca 0.72      NTOT0 ref   NTOT0 tri      d%
   corner cell (mix 1), group 1     5.89140     6.01834  +2.155
   corner cell (mix 1), group 2     8.33873     8.14683  -2.301
   edge   cell (mix 2), group 1     5.81617     5.84696  +0.529
   edge   cell (mix 2), group 2     8.42977     8.40410  -0.305
```

Two things to read here. First, the neighbour fuel constants differ by **up to ±3 %** — and
this is at **zero burnup**, where the supercell's fuel and the fuel COMPO's fuel are the same
material. So it is not a depletion-history difference; the worth error is fully present at
bu = 0 (VOID −8.48 to −9.56 %) and barely changes by 15 MWd/kg. Second, `NTOT0` and `SIGW00`
shift by almost exactly the same relative amount (+2.155 vs +2.160), so the whole set is
scaled rather than reshaped.

The corner cell — the one *farthest* from the rod — differs *most*, which looks backwards
until you remember `ASYM 1` pins merged region 1, the corner, to a factor of exactly 1. Its
numbers are therefore the raw homogenised supercell values, and they are 2–3 % from
infinite-lattice fuel because **the rod perturbs the spectrum across the whole 75 cm
supercell**. The RBMK's migration length is ~1 m; a 25 cm cell two cells from an absorber is
not in an infinite lattice.

**That is the finding.** This was never a rod-cell problem. The core gives every fuel channel
infinite-lattice constants, including the ~8 neighbours of each of the 211 rods, and fuel next
to a rod genuinely does not have infinite-lattice constants. The error depends on what is in
the centre — water, graphite or helium perturb the neighbouring spectrum differently — which
is exactly why it does not cancel in a worth, and why ABS (±3 %) fares better than DSP and
VOID (−7 to −10 %): the absorber's neighbour perturbation is closer to the water case it is
differenced against.

### 4. How big is the fixable part? Three of nine points

The framing above — "the rod's neighbours are a special case" — is wrong, and the channel map
says so. Counted on `sources/derived/unit4_channel_map.csv`:

```
  fuel channels                      1661
  with >=1 CPS in the eight-ring     1367   (82.3 %)
  with none                           294   (17.7 %)
  mean CPS count in the eight-ring   1.08
  CPS fraction, 3x3 supercell        1/9      = 11 %
  CPS fraction, Unit 4               227/1888 = 12 %
```

Having a CPS neighbour is not the special case — **not** having one is, at 17.7 %. And the
3 × 3 supercell's CPS fraction matches the core's to one point. So the supercell, not the
single infinite-lattice cell the fuel COMPO is built from, is the representative lattice cell
for this reactor.

Tested by drawing the eight neighbours from the **water** supercell's own fuel cells — the
right reference environment, since a withdrawn rod *is* a water column and only 47 of 211 were
inserted at 01:22:30 (`A64B_NBR=wat`):

| worth | fuel-COMPO neighbours | representative-environment neighbours |
|---|---|---|
| ABS | −3.24 to +2.84 % | −1.93 to +4.07 % |
| DSP | −9.10 to −6.72 % | −5.97 to −4.18 % |
| VOID | −10.56 to −8.48 % | −7.30 to −5.81 % |

**A clean decomposition of the ~9 %:** about 3 points are the fuel being computed in an
unrepresentative environment, and are recoverable. The remaining ~6 points are the
*centre-dependence* — the difference between neighbouring a water column and neighbouring a
graphite displacer or a drained channel — and no single fuel dataset can carry that, because
it changes as the rods move.

Two consequences. First, the recoverable 3 points are not free: `_CCompoWAT` already holds the
right fuel data but only on the coarse A64 grid (3 burnups, 3 densities, no `TG` axis), so
using it in the core means rebuilding the fuel COMPO on the 3 × 3 supercell at the full
840-point grid — expensive, and only sensible batched with A6b's xenon rebuild. Second,
**expect a core-level k bias**: the same substitution moves the supercell k by 38–484 pcm
depending on state, and it applies to 82 % of the core's fuel, so A7's eigenvalue carries it.

### 5. Two corrections to item 3, found by the superposition test — 2026-10-01

Item 3's per-cell numbers above are **wrong**, and the explanation attached to them was a
rationalisation of a bug. Both were caught by a replicate consistency check in
`openmc/sup5.py` — cells that are identical by construction disagreed, and nothing in the
calculation forces them to agree, so the disagreement had to be mine. The k-based results
(items 1, 2, 4, and the whole worth table) are **unaffected**: they never went through this path,
and re-running `a64b.py worths` with the fixed parser reproduces ABS −3.24/+2.84, DSP
−9.10/−6.72, VOID −10.56/−8.48 exactly.

* **`OUT: INTG` prints reaction rates, not cross sections.** Column 3 is the zone's ∫Σφ and
  column 2 its ∫φ; the cross section is the quotient. Comparing the raw column compares flux
  shapes. Verified by reading one mixture through both pipelines: 6.018 against 2.016 before
  the division, 0.3665 against 0.3664 after it.
* **A stray-row match.** The row pattern also matched plain integer grids printed elsewhere in
  the listing, silently overwriting real zones that shared an index. The pattern now requires
  eight E-format fields.

Redone properly, the neighbour cross sections differ by **+0.1 to +0.5 % at the corner and
−2.9 to +5.2 % at the edge** — the cell *next to* the rod is the perturbed one, which is the
sensible ordering and the opposite of what item 3 claims. `NTOT0` and `SIGW00` still shift
together (+0.201 vs +0.207), and that now reads correctly as the signature of a **multiplicative
SPH factor** rather than of reshaped cross sections.

### 6. Where the environment effect actually lives, and whether it is additive

A 5 × 5 supercell with CPS channels at (1,1) and (3,3) — one geometry holding cells with 0, 1
and 2 CPS neighbours, so every comparison is internal. The CPS sit on the diagonal because
{(1,1),(3,3)} is transpose-symmetric, which makes the classification immune to guessing
`EDI: MERG CELL`'s raster order wrong. 1057 s, peak 5.0 GB. Two consistency checks passed
before anything was read from it: the single cell gives k∞ = **1.313968**, the recorded A3
production value exactly, and the fuel COMPO round-trips it to 0.4 pcm.

**The raw homogenisation barely moves.** With no SPH anywhere, the fuel cells' two-group
constants sit within **0.3 %** of infinite-lattice fuel regardless of environment. So the 3–5 %
measured above is not homogenisation — it is the **SPH factor**, which is exactly what the core
discards.

Running `SPH:` on the saved edit object (seconds, because the deck persists its L_EDIT):

```
SPH factor map, group 1   (R marks a CPS channel)
      1.53   1.56   1.31   1.09   1.00
      1.56 R 1.75   1.45   1.16   1.09
      1.31   1.45   1.46   1.45   1.31
      1.09   1.16   1.45 R 1.75   1.56
      1.00   1.09   1.31   1.56   1.53
```

**Three findings.**

1. **Not additive.** The increment for two diagonal neighbours against twice the increment for
   one gives ratios of **0.64 (group 1) and 0.55 (group 2)** — strongly sub-additive. A linear
   environment axis would overcount.
2. **The eight-ring count is the wrong descriptor**, which is the more important result.
   Grouping the cells by it leaves a within-class spread of **0.2471** against a total span of
   0.5590 — it explains under half the variation. Nearest-neighbour distance is no better
   (0.2158). A distance-weighted scalar, Σ1/d² over the CPS channels, separates all eight
   classes with a worst within-class spread of **0.0003**. So the factor *is* a smooth function
   of a low-dimensional geometric descriptor — just not the one the plan assumed. Σ1/d² is not
   yet shown to be the *physical* parameter: it is non-monotonic here, so it may be separating
   the classes by arithmetic coincidence, and it needs a second rod arrangement to confirm.
3. **The corrections are far larger than the 3 × 3 suggests.** Fuel-cell factors span **1.00 to
   1.56** in a realistic environment, and the core sets every one of them to 1.0. The 3 × 3
   supercell cannot show this, because every one of its eight fuel cells touches the rod; its
   factors span only ~5 %. **This weakens item 4's estimate** that three of the nine points are
   recoverable by using `_CCompoWAT`'s fuel: those cells are all rod-adjacent, whereas 17.7 % of
   core channels have no CPS neighbour at all and many more sit further out than any cell the
   3 × 3 contains.

**What it means for the scope.** The continuous-environment axis is viable in principle — the
factor is smooth and low-dimensional — but it is weeks, not days: the descriptor needs
validating on at least two more rod arrangements, it is sub-additive so no simple scaling
works, and the core-side plumbing follows. Against a 6–7 % residual that sits inside bands
already being carried, that is not the next thing to build.

### Where this leaves A6.4

Two sound ways out, and one that is not.

* **Give the rod's neighbours their own mixtures in the core.** Principled, and the data
  already exists — the CPS MULTICOMPO stores all nine cells, and the core currently uses only
  mixture 5. It is real work: a channel can neighbour more than one rod, it has its own
  burnup, and the correction depends on the rod's insertion state, which moves during the
  transient. Item 4 bounds what it buys: the state-dependent part is ~6 of the 9 points.
* **Carry it as a measured, one-signed bias**, the way A6.3's residual is carried as the A′
  correction: displacer and drained-channel worth low by 7–10 %, absorber worth within ±3 %,
  mechanism named, present at all burnups, and propagated into A8's uncertainty band.
* **Not acceptable:** fitting the four factors of the rod and reference cells to hit the
  worth. Four parameters against one number is not an equivalence, it is a fudge, and standing
  rule 1 forbids it. It was not done.

A6.4b is closed as a design. The choice between the two survivors is a scoping decision, and
the honest default until A8 shows sensitivity is the second.

## Phase 1b: the reflector, and a DRAGON fault OpenMC caught — 2026-10-01

**This entry supersedes the one committed earlier today (`ca5b4a6`), whose central conclusion
was wrong.** That entry said diffusion cannot represent a 1 m graphite reflector because it
lacks a streaming tail, and presented a 14× flux discrepancy as the evidence. The evidence was
real; the attribution was not. An independent check overturned it, which is what standing rule
4 exists for. Everything below regenerates from `openmc/refl.py` and `openmc/slab.py`.

### What is solid: the geometry

[D] p.9, primary: *"Активная зона имеет форму вертикального цилиндра эквивалентным диаметром
11,8 и высотой 7 м. Она окружена боковым отражателем толщиной 1 м и торцевыми отражателями
толщиной по 0,5 м."* — core 11.8 m across, 7 m high; **lateral reflector 1 m, end reflectors
0.5 m each**. `NZ_ACTIVE = 28` and `NZ_REFL = 2` confirmed; **`NREF = 2` is wrong, it is 4**.

| source | count |
|---|---|
| [D] graphite stack | 2488 columns, 250 × 250 mm, 1.65 g/cm³ |
| [D] reflector cooling channels | 156 |
| [BEH96] II.B, independently | 444 pure graphite + 156 water-cooled = **600** |
| 2488 − 1888 (our channel map) | **600** |

Four rings, two materials. Bounding the stack by a circle at R = 28.14 cells reproduces 2488 to
0.3 %; dilating the ragged outline gives 833, 39 % too many. That takes the core grid to 58 × 58.

**A trap avoided:** the "32 cm of axial graphite reflector" in [BEH96] and [ALX98] is the **RRC
critical facility** — 18 × 18 blocks 4.1 m tall, 346 cm fuel column — not a power reactor.

### The finding that matters: DRAGON's open-boundary solution is wrong here

The reflector supercell needs a vacuum outside the stack, so it was built that way. Its k came
out far below anything the diffusion model could reproduce, and the first reading of that was
"diffusion cannot do reflectors". OpenMC says otherwise:

| 4 fuel cells, 1 m | reflective | one vacuum face |
|---|---|---|
| **OpenMC** (continuous energy) | 1.316953 ± 0.000611 | **1.198662 ± 0.000691** |
| DONJON diffusion | 1.305690 | 1.191992 |
| **DRAGON transport** | 1.314007 | **0.849315** |

Closed, all three agree to within the known 170 pcm DRAGON/OpenMC lattice offset. Open, OpenMC
sits with **DONJON**, and DRAGON is 34 000 pcm away. OpenMC's leakage curve against slab
thickness is smooth and physical — 0.4712, 0.9409, 1.1987, 1.2837 for 1, 2, 4, 8 cells,
approaching k∞ — while DRAGON reads 0.2071 at one cell and 0.8493 at four.

It is not the input, which is the first thing standing rule 3 would suggest:

* **not the boundary line** — one vacuum face, two, and four give 0.2071, 0.1270, 0.0953:
  distinct and correctly ordered, so the keywords are applied;
* **not the geometry or tracking** — NXT reports exact volume 625.0000 cm² and perimeter
  100.0000 cm, and a fully reflected block reproduces the cell k∞ to 0.1 pcm (1 cell) and
  3 pcm (4 cells);
* **not the leakage model** — with and without `B1 SIGS BUCK 0.0`: 0.849336 and 0.849315;
* **not the tracking density** — `TISO 15 30.0` against `TISO 30 120.0`: 0.849315 and 0.849471;
* **not the transverse shape or the explicit mesh** — 4 × 1 and 4 × 2 agree to 10 pcm, and
  `MESHX` present or absent gives bit-identical 0.2070993.

* **not the self-shielding** — a plausible user error, since `USS:` was being run on the same
  leaking geometry. Closing only the self-shielding geometry and leaving the flux geometry
  open gives 0.849359 against 0.849315: 4 pcm. Not it.

So the geometry, the boundary keywords, the tracking, the leakage model and the self-shielding
are all correct and the **solution** is not. The cause is not identified, and the hunt is
stopped: the fault is avoidable, nothing published depends on it, and the remaining suspect —
that collision probability mishandles the open boundary where the method of characteristics
would not — could not be tested, because the MOC path needs the `CTRA NONE` library variant
and fails with `MCCGF: INVALID TRACKING FILE` without it. That is the first thing to try if
anyone picks this up.

**What this does and does not affect.** Every DRAGON result this project has published —
the lattice cell, the void bracket, the CPS supercells, A6.3, A6.4 — is on a **fully reflected**
geometry, the regime where DRAGON agrees with OpenMC to 170 pcm. None of them is touched. What
it does mean is that **a DRAGON calculation with an open boundary cannot be trusted here until
this is understood**, and that is now a standing trap.

### Where the reflector stands

Closing the supercell's outer boundary avoids the fault, and costs little: in diffusion the
outer face of a 1 m reflector is worth **21 pcm** (`VOID` 1.259789, `REFL` 1.260002, `ZERO`
1.259771), because the flux there is about 1 % of the core's. On the closed geometry, transport
gives 1.155893 against diffusion's 1.260055 — **7152 pcm**, down from 16 187 but still large.

**SPH will not converge on this problem**, now across seven variants: `ASYM 1`, `STD`,
`ASYM 8`; tolerance 1e-6 ×200 and 1e-4 ×500; `DUAL 1 1`, `DUAL 3 3`, and `DUAL 1 1` on a 5 cm
reflector mesh; and once more with the boundary closed, where the unconverged factors corrupt
the stored cross sections badly enough that the DONJON solve returns NaN. `MCFD 1` segfaults,
as it does on the CPS supercell. The open boundary was a plausible cause and is now excluded.

**The 7152 pcm is measured on a test that over-weights the reflector**: four fuel zones against
four reflector zones, where the real core is 1661 fuel channels against a four-column skin. It
is an upper bound on the core-level error, not an estimate of it. The remaining options are to
measure the core-level effect directly, or to use an albedo boundary derived from the same
transport solution and drop the explicit reflector nodes.

**Status:** `_RCompo` is rebuilt on the closed geometry with physically sensible constants
(diffusion coefficients 1.14 / 0.79 cm in fuel, ~1.03 / 0.83 in graphite). It is usable, with
a stated and bounded interface error, and it is no longer a placeholder.

## A6.5: the Unit 4 core solves, and the reflector question closes — 2026-10-01 (4)

`rbmk_unit4_core.don` now runs the whole chain — `GEO:` → `USPLIT:` → `RESINI:` → `NCR:` ×2
→ `MACINI:` → `TRIVAT: DUAL 1 1` → `TRIVAA:` → `FLUD:` → `FLPOW:` — on the sourced
1888-channel map inside a sourced graphite stack, with real cross sections in every
mixture for the first time in the project. **8.1 s, 691 MB peak, 141 outer iterations.**

**k = 1.018278**, reported and not asserted: uniform burnup, all rods withdrawn, no xenon.

### The stack geometry closes a third count, from a source that did not set it

`NREF` went 2 → 4 on [D] p.9 ("боковым отражателем толщиной 1 м"), and the stack is bounded
by a circle of R = 28.14 cells rather than by dilating the core's staircase outline. Four
counts now close against each other:

| quantity | source | model |
|---|---|---|
| graphite stack columns | [D]: 2488 | 2480 (−0.3 %) |
| reflector columns | 2488 − 1888 = 600 | 592 (−1.3 %) |
| water-cooled reflector channels | [BEH96]: 156 | **156** |
| pure graphite reflector columns | [BEH96]: 444 | 436 (−1.8 %) |

The 156 is the one worth noticing. The radius was fixed by [D]'s column count; the cooled
ring is defined independently as the stack's **face-connected** outer layer; and that layer
comes out at exactly 156 columns, which is [BEH96]'s cooled-channel count to the unit.
Nothing was fitted. (The 8-neighbour perimeter gives 220 and is wrong — a diagonal step is
1.41 cells.) The inner three rings are depth into the reflector by face dilation, so ring 1
sits against the core and ring 4 is the cooled skin, matching `_RCompo`'s zone order 5–8.

Two mechanical findings, both now in the gotcha table:

* **Mixture 0 is a virtual volume, and that is the right way to say "not the reactor".**
  `USPMIX.f:52` drops `MAT(IEL) == 0` from the mixture count, and TRIVAC applies the
  geometry's boundary condition at the **real/virtual interface**, not at the edge of the
  rectangular grid. Verified rather than assumed: k is bit-identical for `U4_NPAD` = 1, 3
  and 5, and changing the outer condition with four reflector rings in place moves k by
  2.6 pcm while changing it with no reflector moves k by 1111 pcm.
* **`USPLIT:` requires `NREFL + NFUEL` to equal the highest material index**, so the
  numbering has to close up when a variant drops the rings — hence reflector mixtures first
  (`RMIX 1 2 3 4 5`) and fuel last (`FMIX 6`), which is also upstream's convention
  (`1Sap_vs_3Sap.x2m:29`). Leaving a hole gives
  `@USPLIT: WRONG NUMBER OF REFLECTOR OR FUEL TYPES`.

### The reflector is worth 131 pcm, and that closes the Phase 1b question

Phase 1b priced the reflector's homogenisation error at 7152 pcm but measured it on four
fuel zones against four reflector zones, and said so: *"an upper bound on the core-level
error, not an estimate of it."* The way to get the core-level number was to measure it in
the core. `tools/u4_leakage.sh` regenerates the table; `decks/Donjon/data/u4_leakage.txt`
is its output.

| case | k | pcm |
|---|---|---|
| 4 graphite rings, VOID at the stack edge | 1.018278 | — |
| … mirror at the stack edge | 1.018304 | +2.6 |
| … mirror on the axial faces | 1.018297 | +1.9 |
| no radial reflector, VOID at the core edge | 1.016965 | −131.3 |
| … mirror at the core edge | 1.028080 | +980.2 |
| all four rings = zone 5 (graphite nearest the core) | 1.018317 | +3.9 |
| all four rings = zone 8 (the cooled one) | 1.017372 | −90.6 |
| ring order reversed | 1.017398 | −88.0 |

**The radial reflector is worth 131 pcm, and only 2.6 pcm leaks past it.** A metre of
graphite is already an almost perfect reflector. A *mirror* at the core edge is worth
1111 pcm — the whole radial leakage — and I spent a while thinking those two numbers
contradicted each other. They do not: a mirror sets B²ᵣ = 0, while a real reflector only
extends the effective radius. Diffusion theory with D_r = 0.84 cm and L_r = 54 cm gives a
reflector saving of 49 cm on a 590 cm radius; with M² = 657 cm² read off the
mirror-at-core-edge row, that predicts ~155 pcm against the measured 131. The model is
behaving.

So the band the reflector dataset has to move core k in — from "no reflector at all" to "a
perfect mirror" — is about **130 pcm wide**, and the 7152 pcm does not propagate. Measured
rather than argued: collapsing all four rings onto one dataset moves k by **3.9 pcm**, so
the spectrum-depth resolution `_RCompo` provides is worth almost nothing at core level,
while putting the cooled ring in the wrong place moves it by 88–91 pcm. **Where the water
is matters; the depth does not.** What this does *not* bound is a dataset that got graphite
absorption badly wrong — that would be a sink rather than a reflector and could fall below
the no-reflector row.

I also talked myself into an axial anomaly on the way and out of it again: making the axial
faces reflective moves k by 1.9 pcm, which I first read as "no axial leakage", against an
expected ~1000 pcm. It is neither. The 50 cm axial reflectors are *already there* in every
case, so that row measures only the difference between vacuum and a mirror **beyond** a
reflector, not the axial leakage itself. The axial power shape settles it independently:
peak at K = 16, the exact mid-plane, with an axial peaking of 2.78/1.90 = 1.46 against the
bare-core cosine's 1.57 — flattened by the reflector, which is what a leaking core looks
like.

### What the deck is and is not

* **Real:** the outline, the 1888 positions, which hold fuel and which hold CPS, the 25 cm
  pitch, the stack boundary, the four reflector rings, and the cross sections in all six
  mixtures (`_ACompo` through `NCR: … TABLE`, `_CCompoWAT`, `_RCompo`).
* **Flat, pending A6d:** burnup is uniform at 10900 MWd/t, the Unit 4 core average. The
  per-channel route (`INST-BURN` off the fuel map) is wired and not yet fed, because the
  burnup *placement* map does not exist. Channel-power peaking is 1.90 max/avg against a
  design ~1.4 — that gap is the missing burnup flattening, not a model fault.
* **Not here:** the rods (every CPS channel is a full-height water column), xenon, and any
  thermal-hydraulic feedback. Gate A6.5's rod-insertion test needs `DEVINI:`/`DSET:` next.
* Average channel power 1922 kW against 3200 MW / 1661 = 1927 kW, which is normalisation
  rather than a result. 0.2 % of the power lands outside the 1661 channels, because the
  reflector mixtures carry a non-zero `H-FACTOR` from their COMPOs.

## Gate A6.5: the positive displacer, and the condition it needs — 2026-10-01 (5)

The A6 gate asks whether **inserting only the graphite displacer from below gives positive
reactivity, with a bottom-skewed axial flux**. It now has a measured answer, and the clause
after the comma turns out to decide it. `tools/u4_rods.sh` regenerates everything below;
`decks/Donjon/data/u4_rods.txt` is its output.

### The rod model, and why it checks itself

`gen_rbmk_unit4.py` grew a `stack(n)` function: the rod as A6_CPS_PLAN gives it — 5 m
absorber, 1.25 m water gap, 4.5 m graphite displacer, 43 planes of 25 cm — placed at an
insertion depth of `n` planes, with coolant wherever the rod is not. Three mixtures now
come from the three CPS COMPOs (`_CCompoWAT`, `_CCompoABS`, `_CCompoDSP`, zone 5 of each),
so `NMIX` is 8: water 1, absorber 2, displacer 3, four reflector rings 4–7, fuel 8.

**The withdrawn geometry is self-checking, and it closes.** With the rod fully up the
absorber sits above the core, leaving 1.25 m water / 4.5 m displacer / 1.25 m water — and
1.25 + 4.50 + 1.25 is exactly the 7.00 m core height. Three independently-quoted lengths
filling the core to the centimetre is a check on all three, and it is also precisely the
configuration the positive-scram mechanism needs: a water column at the **bottom** for the
displacer to sweep out. The generator asserts that `stack()` reproduces each hand-derived
configuration rather than carrying both.

### What the displacer is worth, and what the first 1.25 m does

142 RR/AZ channels carry the swept rod; 36 AZOC are a separately-driven bank; the 12 AR,
21 USP and 16 detector tubes are water in every row.

| configuration | k | pcm |
|---|---|---|
| water column full height (reference) | 1.018278 | — |
| rods withdrawn: 4.5 m displacer in core | 1.038874 | **+2060** |
| lower end advances into water (`botD`) | 1.039903 | +103 |
| upper end retreats into water (`topW`) | 1.035589 | −329 |
| both at once — displacer only (`dsp`) | 1.037128 | **−175** |
| … plus the absorber entering (`scram1`) | 1.036682 | −219 |

The displacer is worth **+2060 pcm** against a water column: water is a net absorber in this
lattice, and that is the reservoir the scram's first motion draws on.

**But the sweep itself came out negative, and the reason is geometric rather than a
cancellation.** The displacer is centred in the core when withdrawn. Moving it down 1.25 m
*gains* graphite in the bottom 1.25 m — the lowest-flux band in the core — and *loses* it
five planes below the displacer's top, which is still well inside the high-flux region. So
the sweep is negative for **any** centre-peaked axial flux, and turns positive only once the
bottom is weighted about **3.2×** more heavily than that interior band. I had expected the
two halves to nearly cancel and they do not; the halves are what made the asymmetry legible.

### The sign tracks the axial peak, both ways

The core here cannot supply its own tilt — flat burnup, no xenon — so one was imposed by
inserting the AZOC bank from the top. The bank depth was stepped and the axial peak, as
`FLPOW:` reports it, was read off; nothing was tuned.

| AZOC bank | axial peak K | k(withdrawn) | k(displacer swept) | sweep |
|---|---|---|---|---|
| 0 | 17 | 1.038874 | 1.037128 | −175 |
| 4 planes | 16 | 1.044627 | 1.043651 | −98 |
| 8 planes | **14** | 1.042054 | 1.042194 | **+14** |
| 12 planes | 14 | 1.037646 | 1.038895 | **+125** |
| 16 planes | **13** | 1.031538 | 1.033312 | **+177** |
| 20 planes | 15 | 1.026018 | 1.026624 | +61 |
| 28 planes | 18 | 1.025884 | 1.022675 | −321 |

Planes 3–30 are active, so K = 16/17 is the mid-plane. The sweep is negative while the peak
sits at or above it, crosses zero as the bank drives the peak to K = 14, and is largest where
the flux is most bottom-skewed (K = 13). Then it **reverses**: a deeply-inserted bank puts
its own absorber in the *bottom* of the core, pushes the peak back up past the mid-plane
(K = 18), and the sweep goes negative again. The sign follows the tilt in both directions,
which is the internal consistency check — a one-sided result could have been an artefact.

**So gate A6.5's mechanism is present in the model, and conditional exactly as the gate
says.** Positive reactivity from the displacer alone requires a bottom-skewed flux. That
also settles a scheduling question with a measurement rather than a preference: **A6b
(xenon) and A6d (burnup placement and the 01:23 rod pattern) are on the critical path to
A8**, because they are what supplies the tilt for real. Until they exist, A8 would be run on
a core whose axial shape has the wrong sign for the effect under study.

### The insertion curve, and a reversal worth keeping

| depth | k | pcm vs withdrawn |
|---|---|---|
| 0 | 1.038874 | 0 |
| 2 planes | 1.038486 | −39 |
| 4 | 1.037457 | −142 |
| 6 | 1.035724 | −315 |
| 9 | 1.031987 | −689 |
| 12 | 1.026358 | −1252 |
| 16 | 1.013636 | −2524 |
| 20 | 0.991208 | −4767 |
| 24 | 0.968386 | **−7049** |
| 28 (full) | 0.987927 | **−5095** |

The curve **reverses past 24 planes**, and that is the 5 m absorber in a 7 m core rather than
an error: at full insertion the absorber's top has dropped below the flux peak and the planes
above it revert to water, so the bank is worth less fully in than three-quarters in. It is
the same geometry that makes the displacer sweep positive — a rod that cannot cover its own
core controls the two ends unequally. Where the reversal sits depends on an **unsourced**
700 cm stroke, so the shape is the finding and not the crossover; the `out`, `dsp` and
`scram1` rows do not depend on it.

Absorber worths here are **lower bounds**: A6.4 measured the rod cell's neighbours as 7–10 %
short, one-signed. The displacer is graphite and that bias does not touch it, so the +2060
pcm and the sweep are not biased by it.

### Open

* The RR stroke, and therefore which 5 m of core the absorber covers at full insertion.
* `DEVINI:`/`DSET:` devices, needed for A8's *moving* rods. The static stacks here are what
  the gate needed; `MOVE` mode (`DEVDRV.f:95` → `MOVCHK.f`, `IMODE=2`) stacks multi-part
  rods correctly and is the route, with the rod assembly longer than the 800 cm geometry as
  the obstacle to work out.
* The 01:23 rod pattern itself, which is A8's initial state, not A6's.

## Phase 2b: `THM:` patched for per-channel inlet flow — 2026-10-01 (6)

An RBMK has 1661 independently-valved fuel channels and the 01:23 state is defined partly by
their flow distribution, but `THM:` accepted only one inlet velocity for the whole core.
It now accepts `SPEED CHAN <one value per channel>`.

**The patch is small because the source survey was right.** `THMDRV` and `THMTRS` are both
already called inside `DO 175 ICH` (`THM.f:995`, `THM.f:1102`) with the velocity as a scalar
argument *for that channel*; the single-velocity limitation lived entirely in the parser.
So the change is: a `VSPEED(NCH)` array beside `FNFUCST`, the `SPEED` keyword routed through
the existing `THMINP` (which has handled both the scalar and the `CHAN` list form since
2018 — `THMINP.f:43`), a `SPEED-CH` record on the THM object, and one scratch copy.

**The scratch copy was the whole risk, and the survey called it.** `THMDRV` *overwrites* its
`SPEED` argument — `THMDRV.f:266,286` assign it from `MFLOW/DCOOL(1)`, i.e. the outlet
velocity. Passing `VSPEED(ICH)` straight in would leave Picard iteration 2 running on
iteration 1's outlet velocity, silently and with no error message. `THMTRS` takes the value
as `SPDIN` and never writes it, so there the stored element goes in directly.

Two smaller decisions, both recorded in the patch:

* A THM object written before the patch has no `SPEED-CH` record, so a restore falls back to
  the scalar `STATE(4)` — which is exactly what `SPEED-CH` holds for a scalar input anyway.
* `STATE(4)` is now the channel mean, so the printed "COOLANT VELOCITY IN M/S" is unchanged
  for any scalar input. The zero-velocity check gained a per-channel form: a channel with no
  fuel is skipped by the drivers and is allowed to be zero, any other is an abort naming it.

### Where the patch lives, because `5.1/` is gitignored

A source edit made directly in the submodule is invisible to this repo and is destroyed by a
fresh clone or a `git submodule update --force`. So the canonical copy is
`patches/0001-THM-per-channel-inlet-velocity.patch`, applied by `tools/apply_patches.sh`
(idempotent — it detects an already-applied patch by a reverse dry-run and skips it, and
refuses rather than guessing if the upstream file has moved under it).
`tools/bootstrap.sh` now runs it as step 3a. Verified by round trip: reverted `THM.f` to
upstream, reapplied from the patch, rebuilt, re-ran both checks.

### Verification: invisible when unused, and provably per-channel when used

**The regression.** `tools/thm_chan_regress.sh` runs upstream's `channel_mphy.x2m` — the only
bundled deck that couples `THM:` to `KINSOL:` — and compares the *whole listing*, not just the
reported numbers, against a stored digest. Excluding timing and memory-usage lines, which are
not reproducible: **2 597 833 comparable lines, 0 differences**, and the pre- and post-patch
digests are the same string, `f9f3849d…`.

(The reference digest had to be computed twice. The first one was taken with a narrower noise
filter than the script's own, so the script reported a failure over nothing but which timing
lines were excluded. The digest and the filter have to travel together: the stored file now
carries its provenance, and `--save <listing>` digests the archived pre-patch run with the
same code the check uses. The 0-difference line-by-line comparison was unaffected and is what
established the result independently.) All 65 355 of the deck's own
echo lines are identical too, and its own non-regression assert still passes. The one thing
that did move was `EQU:`'s reported memory usage, 5120 → 5280 words, which is `VSPEED` and
`SPEED-CH` being there.

**The proof.** `decks/Donjon/data/rbmk_thm_chan.x2m` (ours, derived from upstream's
`FourChannels.x2m`, the smallest bundled deck that drives `THM:` with a `CLUSTER` geometry)
runs three `THM:` initialisations on one converged power distribution, differing only in how
the inlet velocity is given. `tools/thm_chan_check.sh` drives it and asserts the result.

| case | max fuel T | per-channel mean fuel T |
|---|---|---|
| scalar `SPEED 8.0436` | 1143.501 | 921.438 921.427 921.427 921.436 |
| `SPEED CHAN` ×4 at 8.0436 | 1143.501 | — |
| `SPEED CHAN 4 6 10 12` | 1172.245 | 933.767 927.298 915.276 908.948 |

Scalar and uniform-`CHAN` agree with **delta = 0.000000e+00**. The graded case moves the
answer by 28.7 K. And the per-channel temperatures fall **monotonically** with velocity —
933.8 K at 4 m/s down to 908.9 K at 12 m/s, a 24.8 K spread — which is what separates "the
vector reached the per-channel driver, element by element, in the right order" from "the
vector was averaged somewhere and the mean happened to move". The scalar case is uniform
across channels to 0.011 K, as a symmetric four-channel core should be.

Upstream's own reference for that deck, 1143.495, is reproduced at 1143.501.

### Still open for A7

* **Transient `THM:` is HEM-only** regardless of the per-channel flow: `THMTRS.f:157` assigns
  `IDFM = 0` unconditionally, after `DFM` has been read. A core converged with `DFM 1` and
  then stepped changes void model at t = 0, which is unacceptable for a reactor whose whole
  accident is a void feedback — so **A7 must converge under `DFM 0`**, with drift flux carried
  as a steady-state sensitivity. Unchanged by this patch; recorded again because it now
  governs A7's setup.
* The channel flows themselves, from the A6d state.
* `CWSECT`'s flow area stays scalar, which is correct here: RBMK channels are identical, so
  only the velocity needed a vector.

## A7a: one channel against published operating data — 2026-10-01 (7)

`docs/report.html`'s first known gap is "no comparison against measurement, at any level":
everything in this project is DRAGON against OpenMC, two codes on the same geometry. [D] p.95
breaks that, and it does so for the thermal-hydraulics. It gives one channel's operating
point in full:

| | |
|---|---|
| channel power | 3000–3200 kW |
| coolant flow | 29.5–30.5 t/h |
| inlet | 79.6 kgf/cm² / 265 °C |
| outlet | 75.3 kgf/cm² / 289.3 °C |
| exit quality | **19.6 %** |
| max coolant velocity | 18.5 m/s |
| clad surface / clad inner | 295 °C / 323 °C |
| pellet centreline | 2100 °C |
| linear rating | 360–385 W/cm |

That set is **over-determined**: given the power, the flow and the inlet state, the exit
quality and the outlet temperature follow from an energy balance and nothing else. So
`decks/Donjon/data/gen_rbmk_a7a.py` prescribes power, flow and inlet state on a single
channel — no neutronics at all, `THM:` reading a power distribution straight off the fuel map
— and compares the rest. `tools/a7a_check.sh` regenerates everything;
`decks/Donjon/data/a7a_check.txt` is its output.

A closure check before any calculation: 3100 kW over 700 cm over 18 rods at peak/mean 1.4 is
**344 W/cm per rod**, against [D]'s own 360–385 W/cm maximum. It sits just below because a
channel-average model carries no rod-to-rod peaking; a 1.07 factor puts it at 368. Power,
length and rod count are mutually consistent, with nothing fitted.

### The result

| | quality % | T-out °C | v-max m/s | clad-o °C | clad-i °C | centreline °C |
|---|---|---|---|---|---|---|
| model | 16.50 | 289.47 | 14.78 | 304.7 | 353.4 | 1315.8 |
| [D] p.95 | 19.6 | 289.3 | 18.5 | 295 | 323 | 2100 |

**The outlet temperature is saturation at the stated outlet pressure**, so agreeing to 0.17 K
confirms the pressure and the steam table and nothing else.

**The quality is the test, and the gap is in [D]'s numbers rather than in the model.** Walking
the corners of [D]'s own ranges, the quality spans 15.29–17.75 %; 19.6 % lies **outside the
box its own power and flow allow**. Reaching it needs 3440 kW at 30 t/h, or 3200 kW at
27.9 t/h, or an inlet about 8 K hotter than the stated 265 °C — an 8–10 % inconsistency in one
of the three. Meanwhile the model closes against its *own* energy balance to 1.2 %:
367.5 kJ/kg × 8.333 kg/s = 3063 kW against 3100 prescribed, the residual being node-centred
versus face-centred enthalpy bookkeeping. So this is a comparison the model passes to the
precision at which the published set is self-consistent, which is the most that can be
claimed from it.

### Two traps found on the way, both in `THM:` defaults

**`XFL` under the default boiling model is not the thermodynamic quality.** The first run gave
7.26 % exit quality where the model's own enthalpy rise demanded 16.4 %, and the model was
right while the reported number was not. `THM:` defaults to Bowring (`ISUBM = 1`), whose
subcooled form is `XFL = XFL0 + Q/(ṁ·h_fg·(1+Π))` with
`Π = ρ_l·c_p·(T_sclad − T_l)/(ρ_g·h_fg)` (`THMH2O.f:161-162`) — and **Π does not go to zero
when the bulk reaches saturation**, because `TSCLAD` is held at `TSAT + DSAT` above the liquid
temperature. So the vapour bookkeeping stays permanently below the energy balance.
Saha–Zuber (`SAHA`, `ISUBM = 2`) is `(F2+F3)/(1+F3)` with `F2 = (h−h_f)/h_fg` the thermodynamic
quality and `F3` vanishing as the bulk heats (`THMH2O.f:165`), so it reverts to the balance.
An RBMK channel exits near 20 % quality, far past bulk boiling, so that is the regime that
matters. Upstream's own `FourChannels.x2m` uses `SAHA`; the default does not.

**`SET-PARAM` addresses a parameter by its `P-NAME`, not its `PARKEY`, and a `LOCAL` one needs
`SAME`/`CHAN`/`BUND` before its value** (`RESPAR.f:139-176`). Only a `GLOBAL` parameter takes a
bare number. The two names exist because `THM:` writes back by `P-NAME` — it recognises
exactly `T-FUEL`, `D-COOL`, `T-COOL`, `T-SURF`, `P-COOL` (`THM.f:1172-1174`) — while `NCR:`
reads by `PARKEY`, which is the COMPO's own axis name.

### The equivalent pitch: a modelling choice, settled by measurement

`THM:`'s `CLUSTER <pitch> <npins>` models a bundle as an infinite **triangular array**
(`THM.f:963-971`: a hexagon of three Wigner–Seitz cells, three rod areas subtracted, perimeter
6πR). An RBMK channel is 18 rods on two rings inside a 4 cm tube around a central carrier
tube, so one pitch cannot reproduce the flow area, the hydraulic diameter and the heated
perimeter at once — and not even nearly, because a triangular array has nowhere to put the
unheated outer annulus or the central tube. Both candidates were derived and **both were run**:

| | pitch | flow area | hydraulic D |
|---|---|---|---|
| real channel | — | 22.4271 cm² | 0.8412 cm |
| `U4A_FIT=area` | 1.7639 cm | 22.4271 (0 %) | 1.1682 (+38.9 %) |
| `U4A_FIT=dh` | 1.6458 cm | 16.1504 (−28.0 %) | 0.8412 (0 %) |

I argued beforehand that the flow area is the one to match, because it sets the coolant
enthalpy rise and so the void distribution, the dominant feedback in this reactor, while the
hydraulic diameter only sets the film coefficient. **The measurement confirms it and goes
further: the hydraulic diameter does not reach any compared quantity at all.** The clad
temperatures move by about one degree between the two fits, where D_h differs by 39 %, because
at this quality the surface is in nucleate boiling and the wall superheat is set by the boiling
correlation rather than by the single-phase film coefficient. So the bracket costs nothing to
carry, and `area` is the nominal without a penalty.

### The centreline is a gap-conductance measurement, not a model failure

1315.8 °C against 2100 °C is a 784 K gap, and it is entirely the pellet–clad gap conductance,
which is in no source we have. Sweeping it:

| HGAP W/m²/K | centreline °C | pellet surface °C |
|---|---|---|
| THM: computes it | 1315.8 | 405.2 |
| 10 000 | 1379.8 | 445.3 |
| 4 000 | 1595.2 | 583.2 |
| **2 800** | **1741.3** | 681.7 |
| 2 000 | 1919.8 | 813.1 |
| **1 700** | **2019.4** | 894.1 |
| 1 000 | 2388.2 | 1272.7 |

The quality is untouched by HGAP at every row, as it must be — the gap moves heat from fuel to
coolant without changing how much arrives — so the quality result and the centreline result
are independent, and only the centreline depends on the unsourced input.

**And two independent routes agree on the value.** The pellet–clad radial gap is 100 µm, from
the A6.1 geometry closed against eight sources (pellet OD 11.50, clad ID 11.70 mm). Bare
conduction across helium at ~700 K, k = 0.28 W/m/K, is h = k/δ = **2800 W/m²/K**. [D]'s 2100 °C
centreline implies **≈1700 W/m²/K**. Those are the same number to within a factor 1.6, from a
geometry and a temperature that have nothing to do with each other — while `THM:`'s own
correlation implies a far tighter gap and is the outlier. So **HGAP should be set explicitly
for A7**, at a value the sourced geometry supports, rather than left to the correlation.

### What this changes

* A7's `THM:` block is now determined except for the flow distribution: `CLUSTER 1.7639e-2 18`,
  `RADIUS` from the A6.1 cell, `SAHA`, `DFM 0`, `HGAP` from the gap width.
* The "no comparison against measurement" gap in `docs/report.html` is narrowed, honestly: the
  thermal-hydraulics now has one, and it passes at the precision the source permits. The
  neutronics still has none.
* `THM:`'s default boiling model is wrong for this application and the default gap correlation
  is wrong for this fuel. Both are now in the gotcha table.

## A7b: the coupled core runs, and the cross-section table runs out — 2026-10-01 (8)

The Picard loop exists and works: `NCR:` → `MACINI:` → `TRIVAA:` → `FLUD:` → `FLPOW:` →
`THM:` → back into `NCR:`, with the coolant density and fuel temperature carried on the fuel
map as local parameters. `tools/a7b_check.sh` regenerates it;
`decks/Donjon/data/a7b_check.txt` is the output.

**It converges geometrically, and then stops because the operating state leaves the
cross-section table.**

| pass | k-eff | Δk pcm | fuel-T error K |
|---|---|---|---|
| 1 | 1.038874 | — | 400.4 |
| 2 | 1.037408 | −146.6 | 133.7 |
| 3 | 1.036857 | −55.1 | 52.9 |
| 4 | 1.036625 | −23.2 | 22.8 |

Contraction ratio 0.376 then 0.421 — clean geometric convergence at r ≈ 0.40, so the limit
extrapolates to **k = 1.036471**, 15 pcm beyond the last pass. **The Doppler feedback alone is
worth −240 pcm** against the 900 K pinned start. *(Both figures superseded 2026-10-02: run to
convergence it is k = 1.036433, and the −240 was Δk × 10⁵ where the rest of this log uses
reactivity, which makes it −227 pcm. See section (11).)* Pass 1 reproduces the single-pass deck's
1.038874 exactly, which is the check that the loop's first iterate is the same calculation.

### Two axis ends, both too narrow for a real core

The A5b MULTICOMPO was built around a lattice-cell *nominal* state, and a core leaves that box
at both ends:

| axis | range built | what the core asks for |
|---|---|---|
| `DCA` | 0.72 … 0.02 g/cm³ (`rbmk_a5b_compo.x2m:99`) | **0.778** at a 265 °C channel inlet |
| `TF` | 600 … 2000 K | **586 K** at the ends of a low-power channel |

Neither is a modelling error. The inlet is *subcooled*, so it is denser than the 0.72 g/cm³
the lattice cell called nominal; and the ends of a 551 kW channel sit near coolant temperature,
below a floor that was set for fuel at power. A zero-power fuel node is at coolant temperature
by definition, so **any** coupled calculation needs the `TF` axis to reach there — this is not
specific to our core. `NCR:` has no clamp, so there is no deck-level workaround: the table has
to cover the state.

**Priced, so the extension is a decision rather than a reflex.** Pinning the coolant density
at 0.72 core-wide costs **103 pcm** — dk/dDCA = −0.01779 from the on-grid 0.60 and 0.72 points,
extrapolated 0.058 past the axis end — and that is an *upper* bound, because only the subcooled
lower part of each channel is above 0.72. The `DCA` axis has 7 values, so one more is 1/7 of the
branch tensor, on a rebuild **A6b already needs for xenon**. Both extensions therefore go into
that one rebuild:

* `DCA`: add ~0.80 g/cm³ above the present top.
* `TF`: add ~530 K below the present floor, i.e. below the coolant inlet temperature.

### The run with the density feedback pinned, and why the two flow cases agreeing matters

To get the loop to iterate at all, `U4_VOIDFB=0` pins the coolant density and leaves the
Doppler feedback live. The flow distribution is bracketed because no total core flow is sourced:
`U4_FLOW=prop` valves every channel to its own power on [D] p.95's pairing of 3100 kW with
30 t/h — which is what an RBMK does, 1661 individually valved channels set to equalise exit
quality, and makes the quality flat by construction — and `U4_FLOW=unif` gives every channel the
core-average velocity, 2.96 m/s, so the hot channels boil much harder. The real reactor is
between them. Velocities under `prop` span 0.85–5.41 m/s for channel powers of 551–3517 kW, and
the total comes to 30 900 t/h against a real RBMK's ~37 500.

**The two cases agree to 1 pcm (−240 against −241), and that is the check on the pinning.**
Those are very different coolant states, but with the density feedback cut the only path from
flow to k is severed, so they *must* give the same eigenvalue. Had they differed, the pin would
have been leaking. It also means these runs say nothing about the flow distribution; that
question reopens when the `DCA` axis reaches the inlet.

### Mechanics, for the record

* `UTL:` has to be in the `MODULE` list before `UTL: POWER :: IMPR POWER-CHAN *` will parse —
  `objstk: OBJECT/MODULE NOT YET DECLARED *UTL:*`, error 5004, which does not name the module
  list as the problem.
* The handover from the core deck to A7's per-channel flow is `POWER-CHAN`, the flat
  1661-value block in **channel order** — the order `RESPFM.f:74-82` finds and the order
  `THMINP` reads a `CHAN` list in. `FLPOW:`'s radial-plane table is the wrong artefact for it.
* Cost: 42.6 s for four coupled passes on 58×58×32, peak 829 MB. A full A7 convergence is
  therefore about a minute and a half, and A8's per-step cost measured in Phase 0 stands.

## A6b scoped down, and the COMPO rebuild launched — 2026-10-01 (9)

### The xenon axis is not needed, and the COMPO was built that way on purpose

A6b has carried "add a Xe branch axis" since the roadmap was written, and gate A6.5 made it
urgent by showing A8 needs a bottom-skewed axial flux. But `rbmk_a5b_compo.x2m`'s own header
says xenon was deliberately left off the axes, and it is right: the `MICR 31` list stored in
every COMPO node includes **Xe135 and I135**, so the densities can be set from the core side.

Verified in source rather than assumed. `NCR:` with a *microlib* output takes
`MICRO ONLY 'Xe135' <n>`, and `NCRLIB.f:268` does `IF(LUSER) DENS1(ISO,ICAL)=CONC(IBM,KSO1)` —
the user concentration **replaces** the stored density — after which `NCRLIB.f:533-538` rebuilds
the embedded macrolib from those densities through `SPHEMB`. So a xenon field costs a `MICRO`
clause and `STEP UP "MACROLIB"`, interpolated at every other axis point, with **no rebuild**.

The approximation it carries, stated: the stored *microscopic* cross sections were self-shielded
at the stored xenon, so changing the density does not re-shield the other isotopes. Xenon is a
strong thermal absorber with its resonance at 0.08 eV, so it does perturb the spectrum. That is
precisely the check the original A6b plan already specified — "A6b checks that route against a
DRAGON branch with the xenon removed" — so the verification exists and only the axis is dropped.

**So A6b's COMPO work is now just the two axis widenings from A7b**, and the rebuild below is
all of it.

### The rebuild is running

Launched 2026-10-01 15:37 local, `rdragon -c custom -p 1 rbmk_a5b_compo.x2m`, log in
`decks/Donjon/data/../Dragon/data/a5b_rebuild.log`. **1152 branch points** (8 burnup nodes ×
8 DCA × 6 TF × 3 TG) against the previous 840. The record for 630 points is 5 h 21 min
CPU-contended, so expect **≈10 h**.

The working 840-point database is preserved as `5.1/Dragon/compo/_ACompo_pre_axis_20261001`
before the `.save` hook overwrites `_ACompo`, alongside the two earlier generations.

**Gates to check when it lands**, all of which the deck already prints:
* `A5BREF` k∞ at the nominal state unchanged against the current `_ACompo` — the reference
  depletion is untouched by the axis change, so any movement is a regression.
* `A5BTAB` rows at 0.80 g/cm³ and 530 K exist and are finite at every burnup node.
* Round trip and off-grid interpolation back within A5b's gates (≤ 10 / ≤ 30 pcm) via
  `rbmk_a5b_verify.don` and `rbmk_a5b_offgrid.x2m`.
* Then `tools/a7b_check.sh` with `U4_VOIDFB=1` — the fully coupled loop, which is the whole
  reason for the widening.

### `-p` does nothing for this workload

Worth recording before anyone spends a day on it: the smoke deck takes **118.15 s at `-p 1`
and 118.18 s at `-p 8`**, with bit-identical `A5BTAB` rows. DRAGON's OpenMP regions are not
where this deck spends its time — the tracking is done once up front and `USS:`/`ASM:`/`FLU:`
per branch run serially. So a 10 h rebuild cannot be shortened by threads, and the honest way
to parallelise it would be to split the burnup nodes across processes, which the deck's
sequential depletion does not allow.

The partner GB10 (`spark`) was considered and rejected for this one: it is reachable with
DRAGON built, but its tree sits ten commits back at `a07157f` with the 630-point `_ACompo`, so
using it means syncing the decks and the library and shipping a 152 MB artefact home — against
a local run that occupies 1 of 20 cores and blocks nothing.

## The COMPO rebuild landed, and the gate was measuring the wrong axis — 2026-10-02 (10)

The 2026-10-01 rebuild finished: **34 408 s of CPU** (9 h 33 min), normal end,
`Dragon/compo/_ACompo` now **208 379 142 bytes** against the previous 151 955 997. That is
+37.1 %, and the branch tensor went 840 → 1152 points, which is +37.1 % — the file grew exactly
in proportion to what was added, which is the cheapest possible check that nothing else moved.
All **1152 branch rows** are present, k spans 0.891580 … 1.334122 with no absurd row, the new
`DCA` 0.80 has its 144 rows and the new `TF` 530 its 192, and the reference depletion at
BU 0 / 0.72 / 900 / 750 gives **1.313968** — the A3 value already on record, to every digit.

### The round trip now tests the values that were added

The eight round-trip nodes were chosen for the 840-point table and **not one of them lands on
`DCA` 0.80 or `TF` 530**. The branch table proves DRAGON *computed* those rows; what was never
tested is that `NCR:` **reads them back**, and a newly added axis value is precisely where a
storage or ordering mistake would hide. Four nodes at the new values cost nothing, because the
references are already in the table. Twelve nodes now, **worst 1.3 pcm** against a ≤ 10 gate.

### Off-grid: 30.4 pcm against a 30 pcm gate, and the two worst points are the new ones

| | worst off-grid |
|---|---|
| the original eight points | **23.9 pcm** |
| plus two points inside the new intervals | **30.4 pcm** |

The 23.9 is **the number recorded for the pre-widening build**, unchanged. Linear interpolation
is local, so widening an axis must leave untouched intervals untouched — and it did, to 0.1 pcm.
The gate did not regress; the test got harder, because the old off-grid points only ever sampled
the old axes and left the region A7 actually interpolates in untested.

**Cubic is not the fix, and that is measured rather than argued.** `NCR.f:139` carries a single
global `LCUBIC`, set by one keyword at `:167-170`, so interpolation cannot be chosen per axis.
Run globally over the same ten states it cuts the error by a factor of 3–6 at BU 0 (19.6 → 4.0,
21.2 → 6.5, 30.4 → 5.4) and is **worse at every one of the four BU 20 000 states**, the worst
going 14.4 → 48.3 pcm. The gate's worst case moves from 30.4 to 48.3. Rejected — and the
burnup dependence of *which* interpolator wins is itself a hint about where the real problem is.

### The decomposition, and why it changes the answer completely

Before widening a grid, find out which axis is paying. Five states at BU 0, each off-grid in at
most one axis:

| dca | TF | TG | off-grid in | delta pcm |
|---|---|---|---|---|
| 0.80 | 600 | 750 | nothing | **−0.1** |
| 0.80 | 600 | 625 | **TG** | **−31.1** |
| 0.80 | 565 | 750 | TF | **+0.4** |
| 0.76 | 600 | 750 | DCA | **−1.0** |
| 0.76 | 565 | 750 | DCA + TF | −0.8 |

**Among the states the gate tested, the entire off-grid error is the graphite-temperature
axis.** The two intervals the rebuild created cost 1.0 and 0.4 pcm; `TG` alone costs 31.1. `TG` has three points — 500, 750, 900 K —
with 250 K gaps, and every off-grid state in the gate sits at 625 or 825.

And the core deck pins `TG` at **750.0**, which *is* a node. So the interpolation error actually
realised in A7 today is of order 1 pcm, not 30, and the gate as written was measuring an axis the
model does not currently interpolate in. The honest statement is therefore both halves: **the
gate is 0.4 pcm over, and the overshoot belongs entirely to an axis that is pinned.**

### And then the axis nobody had ever tested, which is worse than all of them

Every off-grid state in the gate, from the first version of it onward, sits on an exact
**burnup** node. The deck says why, and it is a reasonable argument: burnup does not move on
transient timescales. But it conflates two things. Burnup does not change *during* the
transient — and the steady state the transient starts *from* does not sit on a node either.
The core deck runs at **10 900 MWd/t**, between the 10 000 and 12 500 nodes. The burnup axis has
been interpolated in every core calculation ever run here and was never once tested.

Testing it was free. The depletion grid is finer than the COMPO node set — `isnode` is 0 at
500, 3500 and 17 500 MWd/t — so those three are exact DRAGON isotopics **on the same depletion
path the COMPO was built from**, at burnups the table must interpolate to reach. (A point at
11 250, inside the core's own interval, was considered and rejected: inserting a depletion step
changes the path and would have contaminated every reference after it.)

| BU | interval | DRAGON | from the table | delta |
|---|---|---|---|---|
| 500 | 0 – 2000 | 1.260106 | 1.294338 | **+2099 pcm** |
| 3500 | 2000 – 5000 | 1.213308 | 1.212213 | **−74 pcm** |
| 17 500 | 15 000 – 20 000 | 0.963606 | 0.965194 | **+171 pcm** |

Two to three orders of magnitude above everything the gate had been measuring.

**Where it comes from, and where it does not.** The nodes at 0.72 / 900 / 750 are
1.313968, 1.237577, 1.187035, 1.142442, 1.097458, 1.052316, 1.007452, 0.921779. Across the
core's own interval the successive differences are −0.044984 and −0.045142 — the curve is very
nearly straight there, and a curvature estimate puts interpolation at 10 900 MWd/t at **2–3
pcm**. So A7 as it stands today, at uniform 10 900, is not affected. The 2099 pcm is the
fresh-fuel knee: reactivity falls **3253 pcm between 0 and 500 MWd/t** and only 1445 more
between 500 and 2000, because the whole equilibrium xenon and samarium build-up happens inside
the first node interval and a straight line between 0 and 2000 cannot see it. (Reactivity
throughout this section is Δρ = 1/k₁ − 1/k₂, as in the gate script.)

**It is a hard blocker for A6d, not for A7.** [PAV] Table 1 puts **172 of 1659 assemblies —
10.4 % of the core — at 1.2 MWd/kgU**, i.e. 1200 MWd/t, squarely inside that interval. What the
table hands back there is 1.268133; bracketing the point between the two measured values that
surround it closely gives 1.249592, so every one of those assemblies is mispriced by about
**+1170 pcm**. The next group up, 41 assemblies at 3.5 MWd/kg, sits where the measured error is
−74 pcm; everything from 5 MWd/kg up is in the flat region. So the moment the burnup placement
rule spreads channels over the real histogram instead of pinning them all at the average, a
tenth of the core carries a four-figure error.

The fix is cheap and half-built already: **make the three existing non-node depletion points
into COMPO nodes.** The isotopics are computed in the chain regardless, so the cost is only
their branches — 3 × 144 = 432 points, about 3.6 h at the measured 29.9 s per point — and no
extra depletion at all. That goes into the same rebuild as the `TG` extension.

### What that costs later: a hard prerequisite for Phase 2c

`TG` is pinned because nothing in DONJON computes a graphite temperature (Phase 2c). The moment
it stops being pinned, two things bite at once, and the branch table prices both:

| burnup | k(TG 750) | k(TG 900) | 750 → 900 K |
|---|---|---|---|
| 0 | 1.313968 | 1.317388 | **+198 pcm** |
| 10 000 | 1.097458 | 1.104734 | **+600 pcm** |
| 20 000 | 0.921779 | 0.932282 | **+1222 pcm** |

The graphite temperature coefficient is **positive and rises steeply with burnup** — +132 pcm
per 100 K fresh, **+815 at 20 GWd/t**, about +400–450 at the core's own 10 900. This is our own
table, not a source: no graphite temperature coefficient exists anywhere in the project's
references, and it needs an independent check before it is leaned on.

Two consequences, both concrete:

* **The axis top is probably below the operating range, and the range itself is not sourced.**
  `rbmk_cell_a3.x2m:113` carries "RBMK runs 500-700 C" as a bare inline comment with no reference
  tag — it is an assumption of ours, not a source, and sourcing it is part of this item. Taken at
  face value it is 773–973 K, while the `TG` axis stops at 900 K = **627 °C** and its nominal
  750 K is 477 °C, *under* that range. A real graphite field puts much of the core off the top of
  the axis, where `NCR:` has no clamp and aborts, exactly as `DCA` and `TF` did in A7b.
* **The pin is not free.** At ~450 pcm/100 K, holding `TG` at 750 K while the graphite sits near
  873 K misprices the core by roughly **+500 pcm** — larger than the Doppler (−240) and the
  density feedback (+325) that A7b measured so carefully. It is not a transient effect; graphite's
  time constant is hours, so it is frozen through a 4 s excursion. It is a steady bias on the
  initial condition, which means **k = 1.039735 is a k at TG = 750 K and should not be quoted as
  the core's eigenvalue.**

So the next COMPO rebuild has its scope already set, the same shape as the one just finished:
extend `TG` above 973 K and refine it, and batch it with whatever else needs one.


## A7 converges, and what does not converge is a switch in the void model — 2026-10-02 (11)

### The fix recorded last night was wrong

`A6b` closed with a diagnosis: the Picard loop never met its 1 K criterion because `CONV`'s
fourth argument, THM's *inner* temperature tolerance `ERMAXT`, was left at upstream's 0.5 K
while the outer test asked for 1 K on a max over 46 508 bundles. Tightening it by a factor of
ten changed nothing. The residual still plateaued at 1.7–2.1 K, and the eigenvalue was
bit-identical for twenty-two passes.

That last fact is what gives it away. **Bit-identical k means bit-identical cross sections,
hence bit-identical power, hence — THM being deterministic — a bit-identical temperature
field and a residual of exactly zero.** A residual that instead sits on a plateau is a limit
cycle, not a tolerance floor, and no tolerance will remove it.

### Where it lives, from the source rather than from a guess

THM reports a residual per field (`THM.f:1211`, `MAX|VAL-FLOT|`). The fuel temperature was the
only one the deck read. Reading the coolant density too localises it immediately: **density
swings 0.011–0.032 g/cm³ per pass while both fields' extrema sit frozen to the thousandth.**

The mechanism is an integer. `K0` is the index of the axial node where boiling starts. It is
set by the Saha-Zuber onset test — `IF(TCALO.GE.TSAT-DTSUB) K0=K`, `THMH2O.f:383` — reset to 0
at `:276` when a node falls back to single-phase, and it **gates the entire two-phase block**
at `:147`. A node sitting within rounding of that threshold flips the branch on and off,
moving its density by a finite step every pass. And `DTSUB` is a function of the heat flux
`PHI`, so the switch is not upstream of the coupling: **it sits inside the Picard loop.**

### Two experiments, because a mechanism you cannot vary is a story

**Relaxation.** `THM:` damps all five local feedback fields with one factor (`THM.f:1187`,
applied at `:1207-1245`), so the residual it reports is already scaled by it.

| `RELAX` | fuel-T plateau | D-cool plateau | passes to dk < 1e-6 | converged k |
|---|---|---|---|---|
| 1.0 | ~7 K | ~0.069 | 9 | **1.039735** |
| 0.5 | ~2 K | ~0.024 | 13 | **1.039735** |
| 0.2 | ~0.6 K | ~0.008 | 26 | **1.039735** |

The plateau falls faster than `RELAX` itself, so under-relaxation both rescales the step and
partly damps the switching — and it never reaches zero at any setting. **The eigenvalue is
bit-identical at all three.** The relaxation factor is a solver parameter and the answer does
not depend on it, which is the only thing that had to be true.

**Pin the density and the cycle disappears.** Same deck, same `RELAX 0.5`, coolant density
held at 0.72 so the only live feedback is Doppler:

| | fuel-T residual | D-cool residual | dk |
|---|---|---|---|
| density live, pass 21 | 2.12 K | 2.9e-2 | 1.2e-7 |
| density pinned, pass 21 | **0.031 K** | **1.2e-5** | **0.0** |

Three orders of magnitude, and dk exactly zero from pass 17. Cutting the one link
density → cross sections → power → heat flux → `DTSUB` → `K0` → density removes the cycle
entirely. That is the attribution, not an inference from it.

So the loop now **converges on the eigenvalue** (dk < 1e-6, with a minimum pass count) and
reports the field residuals beside it. The plateau is a property of the void correlation that
A8 will march through, not an unconverged steady state.

### A defect that had been hiding behind its own output

Every A7 run so far ended in `cle2000_c: LINKED_LIST *FLUX* IS NOT DEFINED(2)`, kernel error
666 — **after** printing the loop's results, so the listing looked complete and the failure was
invisible. The loop deletes `FLUX` at the end of every pass, including the last, so nothing
after the loop could run and **the power-shape block had never once executed.** Numbers already
reported are unaffected; they are all from inside the loop. But no converged power distribution
had ever been produced.

The fix re-solves once on the converged field, which is also the more correct order: inside the
loop the power is computed *before* that pass's `THM:` update, so the last in-loop power belongs
to the previous temperature field.

### What the feedback is actually worth, converged rather than extrapolated

`tools/a7b_check.sh` runs all four combinations of {density pinned, density live} ×
{flow valved to power, uniform flow}, each to the new criterion in 12 passes. *(These k values
are on the 1152-point table and were re-based by the 2026-10-03 rebuild — see section (12);
the absolute values move ~20 pcm, the feedbacks move 2.)*

| case | k | reactivity vs cold |
|---|---|---|
| cold, no feedback (`rbmk_unit4_core_out.don`) | 1.038874 | — |
| Doppler only, flow valved to power | 1.036434 | **−227 pcm** |
| Doppler only, uniform flow | 1.036429 | **−227 pcm** |
| Doppler + density, flow valved to power | 1.039734 | **+80 pcm** |
| Doppler + density, uniform flow | 1.040376 | **+139 pcm** |

so the **density/void feedback alone is +306 pcm, positive**, against −227 pcm of Doppler. The
cold deck reproduces the loop's first iterate exactly (1.038874), which is the check that they
are the same calculation. (The 21-pass runs settle one digit further, 1.036433 and 1.039735; the
dk criterion stops 0.1 pcm short of that, which is the price of stopping at all.)

**Both pairs now say something, and one of them is new.** The two *pinned* cases differ by
**0.5 pcm** — with the density held fixed the only path from flow to k is severed, so they must
agree, and that is the measurement that the pin is really a pin rather than a leaky one. The two
*live* cases differ by **59.4 pcm**, because there the flow does reach k, through the coolant
density. That spread could not be measured at all before the rebuild, because the live cases
walked off the end of the `DCA` axis. **It is the width of the flow-distribution assumption on
the core eigenvalue** — no total core flow is sourced, `prop` valves every channel to its own
power and `unif` gives them all the core average, and the real reactor is between. 59 pcm is
therefore the honest uncertainty that the missing flow source costs us, and it is small enough
that A6d's flow state does not need to be perfect.

*Units, because the A7b entry above is inconsistent with this one.* Reactivity here is
Δρ = 1/k₁ − 1/k₂. A7b's "−240 pcm" for the Doppler feedback was Δk × 10⁵ on a four-pass
geometric extrapolation; on the reactivity convention, converged, it is −227.

### And the power shape, for the first time

| | peak channel | channel MAX/AVG | bundle MAX/AVG |
|---|---|---|---|
| cold, no feedback | 3517.1 kW | 1.8289 | 2.9177 |
| coupled | **3022.2 kW** | **1.5719** | **2.4385** |

The feedback flattens the core: channel peaking down 14 %, bundle peaking down 16 %, peak
channel power down 495 kW. The hottest channel is **3434 in both**, which is the sanity check
that the comparison is like-for-like. A negative net effect on peaking from a *positive* net
reactivity feedback is not a contradiction — the density feedback is positive on the core
average but still redistributes power away from the hottest channels, which are the ones
boiling hardest.


## The burnup axis rebuild, launched and landed — 2026-10-02/03 (12)

Section (10) measured the problem; this is the fix, running. **12 burnup nodes instead of 8**,
and the three new ones cost no extra depletion because the chain already passes through them:

| | before | after |
|---|---|---|
| COMPO nodes | 0, 2000, 5000, 7500, 10 000, 12 500, 15 000, 20 000 | **+ 500, 1000, 3500, 17 500** |
| depletion points | 11 | **14** (250 and 11 250 added) |
| branch tensor | 1152 | **1728**, est. 14.4 h at the measured 29.9 s/point |

Three choices worth stating:

* **1000 is a node even though nothing measured it.** 500 was measured at +2099 pcm and 2000 is
  a node, so the knee is bracketed — but [PAV]'s fresh group sits at **1200** MWd/t, between
  them, and a node at 1000 is what makes that group's interval 1000–2000 instead of 0–2000.
  Putting a node where the fuel actually is costs 144 branch points.
* **250 and 11 250 are deliberately *not* nodes.** Promoting 500, 3500 and 17 500 destroys the
  gate that found the problem — they would become exactly-representable and test nothing. A
  burnup gate needs a point the table has to interpolate to reach, so the rebuild adds two
  depletion points that are not nodes: 250, in the steepest part of the curve, and 11 250, in
  the interval the core itself runs in. Both gate decks are remapped onto them.
* **The depletion path changes, and that is fine *this time*.** Adding steps at 250, 1000 and
  11 250 shifts every stored isotopic slightly. When this was considered in section (10) it was
  rejected, because inserting a step into a reference run would have contaminated a comparison
  against an *existing* table. Here the table and its references are rebuilt together on the
  same path, so the comparison stays internally consistent. Every A5b number re-baselines; the
  invariant to check on landing is that BU 0 is still **1.313968**, since nothing has been
  depleted yet at that point.

The deck was smoke-tested before committing the 14 hours — `tools/mk_a5b_smoke.py` derives a
two-node, two-density version that exercises the same `isnode` skip, and it reached normal end
with all four branch points. The working 1152-point database is preserved as
`_ACompo_pre_bunodes_20261002`, and the save hook only `mv`s the new one into place at the very
end, so the old table stays usable for the whole run.

**The `TG` axis is deliberately not in this rebuild.** It needs extending too — section (10)
prices the pin at ~+500 pcm — but its range is set by a bare uncited comment, and widening an
axis to a number nobody sourced is the thing this project does not do. Sourcing it is part of
Phase 2c; the extension goes into whatever rebuild follows.


### It landed, and the structural gates pass

**18.1 h** (65 100.6 s; the 14.4 h estimate did not allow for the unrelated workload sharing
the machine), normal end, MAXRSS 812 MB. `_ACompo` is **312 731 083 bytes** against the
previous 208 379 142 — a factor of **1.5007** against a tensor that grew by exactly 1.5, which
is the same cheap consistency check the last rebuild passed.

| gate | result |
|---|---|
| branch rows | **1728 / 1728**, no absurd row, k 0.891338 … 1.334122 |
| burnup nodes stored | **12**, exactly the intended set |
| **invariant: BU 0 at 0.72 / 900 / 750** | **1.313968** — unchanged to every digit |
| round trip | **1.6 pcm** over 12 nodes (gate ≤ 10) |

The invariant is the one that mattered. Nothing is depleted at BU 0, so a changed depletion
path must leave it alone; had it moved, the path change would have been doing something it had
no business doing.

### What refining the depletion grid was worth, measured

Everything above BU 0 *did* move, and since the old column is on record the shift can be
measured rather than waved at:

| BU | 11-step grid | 14-step grid | Δρ |
|---|---|---|---|
| 0 | 1.313968 | 1.313968 | **+0.0** |
| 2000 | 1.237577 | 1.238014 | +28.5 |
| 5000 | 1.187035 | 1.186767 | −19.0 |
| 7500 | 1.142442 | 1.142208 | −17.9 |
| 10 000 | 1.097458 | 1.097225 | −19.3 |
| 12 500 | 1.052316 | 1.052156 | −14.5 |
| 15 000 | 1.007452 | 1.007269 | −18.0 |
| 20 000 | 0.921779 | 0.921542 | −27.9 |

So the previous grid — already refined once, to the "≤ 2.5 MWd/kg" rule — still carried
**up to 29 pcm of depletion-step error**, systematic and one-signed above 2000: it overstated
k everywhere. That is now the second, independent reason the decision in section (10) was
right. Computing a burnup reference on a *new* path and comparing it against a table built on
the *old* one would have folded ~20 pcm of path difference into a 30 pcm gate and called it
interpolation error. The 500 MWd/t point shows it directly: 1.260106 on the old path,
1.259790 on the new one, a 20 pcm shift in a quantity the gate reads to the pcm.

It also says the step error is converging rather than closed: 11 → 14 points moved k by ~20 pcm,
so the remaining error is smaller than that but not zero, and it is one-signed. Worth one more
halving study if any result ever turns on 20 pcm of absolute k.


### The interpolation gates on the rebuilt table, and a gate point I chose badly

| gate | before | after | verdict |
|---|---|---|---|
| round trip, 12 nodes | 1.3 pcm | **1.6 pcm** | passes (≤ 10) |
| off-grid LINEAR, 10 states | 30.4 pcm | **30.4 pcm** | unchanged, and it should be — `TG` owns it and `TG` was not touched |
| off-grid CUBIC | 48.3 pcm | 34.4 pcm | still worse than LINEAR; still rejected |
| **burnup, core's own interval (11 250)** | — | **+8.7 pcm** | **the blocker is cleared** |
| burnup, 0–500 interval (250) | — | **+1340.9 pcm** | the xenon knee is still inside it |

**+8.7 pcm at 11 250 is the result that matters.** It is a direct measurement in the interval
the core actually runs in, and it replaces an axis that had never been tested at all.

**The 250 point is a gate point I should not have chosen, and the reason is embarrassing.**
I picked it "in the steepest part of the curve", which sounds right and is wrong: [PAV]'s
lowest burnup group is at **1200 MWd/t**, so no Unit 4 assembly is anywhere near 250, and the
1341 pcm it reports is the interpolation error of a state the model never evaluates. That is
*precisely* the error the `TG` axis had been making — a gate measuring somewhere the model does
not go — found and written up one day earlier, and then repeated. The point that needed
sampling was inside **1000–2000**, where the fresh group lives, and the rebuild had the chance
to put a non-node there and did not.

**So the fresh group's interval is improved but not measured, and I am not going to put a
number on it.** The node bracketing it went from 0–2000, spanning the xenon knee, to 1000–2000,
entirely past it, which has to be a large improvement on the ~+1170 pcm of section (10). But
"has to be" is not a measurement. A curvature estimate from the node values would give ~18 pcm,
and that estimator is **demonstrably unreliable here**: calibrated against the two burnups where
truth is now known, it underpredicts by **3.7× at 250 and 17× at 11 250**. A number from it
would be a number with no error bar, which is worse than saying the interval is untested.

Two things follow for the next rebuild, both cheap because they are gate-side:

* move the burnup gate point from 250 into the 1000–2000 interval, which costs one depletion
  point and no nodes;
* keep a point in 0–500 only if something ever puts fuel there, and otherwise record the
  interval as outside the model's range rather than as a failing gate.


### What the rebuild did to A7: moved k by 20 pcm, moved the physics by 2

Every A7 number in section (11) was computed against the 1152-point table. Re-run against the
1728-point one, same decks, same criterion:

| | 1152-point table | 1728-point table | shift |
|---|---|---|---|
| cold, no feedback | 1.038874 | **1.038645** | −21 pcm |
| Doppler only, flow valved to power | 1.036434 | **1.036211** | −21 pcm |
| Doppler only, uniform flow | 1.036429 | **1.036206** | −21 pcm |
| Doppler + density, flow valved | 1.039734 | **1.039528** | −19 pcm |
| Doppler + density, uniform | 1.040376 | **1.040173** | −19 pcm |
| | | | |
| Doppler feedback | −227 pcm | **−226 pcm** | +1 |
| density feedback | +306 pcm | **+308 pcm** | +2 |
| net feedback | +80 pcm | **+82 pcm** | +2 |
| flow-distribution spread | 59.4 pcm | **59.7 pcm** | +0.3 |
| pinned-pair agreement | 0.5 pcm | **0.5 pcm** | — |
| | | | |
| channel peaking, cold → coupled | 1.8289 → 1.5719 | **1.8290 → 1.5717** | 4th digit |
| peak channel power, cold → coupled | 3517.1 → 3022.2 kW | **3517.1 → 3021.9 kW** | 0.3 kW |

(The cold reference was re-run on the new table too, so both halves of the power comparison are
on the same database.)

**The shift in absolute k is the depletion-step error the rebuild removed** — 19–21 pcm, the
same one-signed 20-ish pcm the node column showed — **and it cancels out of every difference.**
Doppler, void, the flow spread and the pin check all survive to within 2 pcm.

The power distribution does not move either — peaking and peak channel power agree to the
fourth digit across the two tables, which is what a uniform one-signed shift in the cross
sections should do to a *shape*.

That is worth stating as a general property of this model rather than as a one-off: a
systematic, one-signed error in the cross-section table moves the eigenvalue and very nearly
does not move reactivity *differences*, nor the power shape. It is why the feedback decomposition has been stable
across three successive tables while the absolute k has not, and it is the reason the `TG` pin
(~+500 pcm, section 10) is a serious problem for quoting k and a much smaller one for quoting
feedbacks. A8 is driven by differences. The eigenvalue is what should be distrusted.

A consequence for everything else in this log: **the fuel COMPO rebuild re-baselines absolute k
wherever it was quoted**, by roughly −20 pcm, while worths and coefficients computed as
differences on the same table are essentially unaffected. Nothing has been re-run beyond A7;
earlier absolute values should be read with that offset in mind rather than taken as
inconsistent.


## A6d: the burnup placement is the biggest unknown, and the model falsifies most of it — 2026-10-04 (13)

The 1728-point COMPO made per-channel burnup worth using, so the core now carries it: RESINI
writes `INST-BVAL CHAN` with one value per channel in B-ZONE order, and the fuel `NCR:` call
declares the burnup PARKEY after the directory name and takes `INST-BURN` inside the `MIX`
clause (`NCRRGR.f:203-217` for the key, `:651` → `IBTYP=2`, used at `:804`). Both halves are
needed: without the PARKEY the keyword binds to nothing, and without `INST-BURN` the
per-channel values sit in the map and are silently ignored.

**What is sourced and what is not.** [PAV] Table 1 gives the Unit 4 core on 26 April 1986 as
1659 assemblies in eight burnup groups; the counts and the values are sourced, and they
reproduce the recorded core average — 10.869 MWd/kgU against the 10.9 on record, which is the
check that the histogram was transcribed correctly. **Where each group sat is not sourced and
no map has been found.** The channel map holds 1661 fuel positions against the histogram's
1659; INSAG-7 (pp. 67, 107) accounts for the difference with one extra absorber and one empty
channel, so two channels take the core average and that is stated rather than smeared.

### Four placements at the same histogram, and a 10 900 pcm spread

Rods withdrawn, no xenon, uniform everything else — so the only thing that differs is *where*
the eight groups sit:

*(Every k and power in this section is superseded by section (14): these runs
carried 36 AZOC channels as pure water instead of as withdrawn rods holding their
graphite displacers, which is worth +609 pcm and a large change in the power shape.
The **ordering** of the placements and the conclusions drawn from it survive; the
numbers do not.)*

| placement | k | Δρ vs flat | peak channel | channel MAX/AVG |
|---|---|---|---|---|
| flat, every channel at the average | 1.038645 | — | 3517 kW | 1.83 |
| most-burnt in the middle | 1.063382 | **+2240 pcm** | 14 626 kW | 7.62 |
| freshest in the middle | 1.170692 | **+10 860 pcm** | 19 547 kW | 10.16 |
| scattered at random | 1.043832 | **+478 pcm** | 5625 kW | 2.93 |

**This is the largest single uncertainty in the core model** — an order of magnitude beyond the
`TG` pin (+500 pcm), the void feedback (+308) or Doppler (−226), and it comes entirely from an
input nobody has sourced.

It is *not* Jensen's inequality on k∞. Weighting the cell k∞ over the eight groups gives
1.08093 against 1.08156 at the mean burnup — 6 pcm. The effect is **flux redistribution**: the
core eigenvalue weights each channel by its own flux, so concentrating fresh fuel anywhere lets
the flux pile onto it, and the more concentrated it is the higher k goes.

### But the model rejects its own extremes, which is the useful part

A peak channel power of 14.6 or 19.5 MW is not a high number, it is an impossible one — [D]
p.95 has the channel operating at 3000–3200 kW and the fuel would be destroyed long before
five times that. So **the two radial orderings are excluded by the model's own output, with no
spatial source needed**, and the 10 900 pcm band is not a real uncertainty band: most of it
describes cores that cannot exist.

What survives is more interesting. Even *random* scatter gives a 5625 kW peak, still 1.7× the
operating limit. So the real placement is not merely unordered — it is ordered in a particular
way, the way an on-power-refuelled reactor orders itself: fresh fuel goes where reactivity is
wanted, and the operators hold the channel power distribution flat because the channel power
limit forces them to. That is a **sourced constraint on an unsourced input**, and it is worth
more than a sensitivity band.

So the next step is not to pick one of these four. It is to **solve for the placement that
flattens the power**, which is what refuelling physically does, and then report how much
freedom is left once that constraint is applied. Rods and xenon both flatten too and are not in
these runs, so they will loosen it; the flat-burnup case already sits at 3517 kW with rods out,
above the limit, which says the same thing from the other direction.

**One consequence for everything already in this log:** the flat-burnup assumption every core
result so far has used is not neutral. Against a merely scattered placement at the same mean it
understates k by ~480 pcm and understates peak channel power by 60 %.


### Solving for the placement: it does not work yet, and why is the finding

The obvious next move was to stop guessing and iterate the refuelling rule to a fixed point —
run the core, rank the channels by power, give the most-burnt fuel to the hottest ones.
`tools/a6d_place.py` does exactly that, and **it diverges**: peaking goes from 1.83 to 13–23
and oscillates, k wandering between 1.088 and 1.167 over ten iterations.

That is not a bug in the rule, it is a property of the core without its other two inputs. The
loop gain is above one. Putting burnt fuel where the power is high drives towards most-burnt
in the middle, which peaks hard at the *edge*, because the fresh fuel pushed out there is
unshielded and the flux piles onto it; the next iteration swings back. Nothing damps it.

A fifth placement was added to test whether local balance is what is missing — fresh and burnt
alternating between neighbouring channels, which is what an operator avoiding clustered fresh
assemblies actually does, and which the flux should partly smooth over since the migration
length is comparable to the 25 cm pitch:

| placement | k | Δρ vs flat | peak channel | MAX/AVG |
|---|---|---|---|---|
| flat | 1.038645 | — | 3517 kW | 1.83 |
| **locally balanced (chequerboard)** | 1.041344 | **+250 pcm** | **5222 kW** | **2.72** |
| scattered at random | 1.043832 | +478 pcm | 5625 kW | 2.93 |
| most-burnt in the middle | 1.063382 | +2240 pcm | 14 626 kW | 7.62 |
| freshest in the middle | 1.170692 | +10 860 pcm | 19 547 kW | 10.16 |

Local balance is the best of them and it barely helps — 2.93 → 2.72. So the peaking is not
driven by neighbouring fresh channels; it is driven by fresh fuel clustering on scales the flux
*can* resolve, which a chequerboard does nothing about.

**The conclusion is structural, and it redirects A6d.** No arrangement of [PAV]'s histogram is
as flat as pretending the fuel is uniform, and the best realistic one still peaks at 1.6× the
operating limit. The flattening agents in a real RBMK are the **control rods** and the **xenon
field** — which are exactly the other two A6d inputs still missing. So the three are not
independent and the placement cannot be pinned down first: it has to be solved jointly with a
rod pattern and a xenon distribution, against a power shape. `a6d_place.py` is kept, with the
divergence recorded in its header, to be re-run when they exist.

*One caveat on the falsification argument, stated because it limits it.* These runs normalise
to 3200 MWth. At 01:23 the reactor was near **200 MW**, where a 5222 kW nominal peak scales to
~330 kW and the channel power limit does not bind at all. The limit excludes the radial
orderings as **full-power** cores — which that fuel did have to be, since the burnup was
accumulated at power — and it says nothing directly about the accident state. For A8 what
matters is not the absolute channel power but the *shape*, and the shape still differs by a
factor of 1.5 between these placements.


## The 01:22:30 rod pattern, and 36 displacers that were not there — 2026-10-04 (14)

### Per-rod depths, from the source that was already in the repository

The channel map has carried a `depth_cm` column since A6d digitised INSAG-7 Fig. II-6 and
registered it against Dollezhal Fig. 2.3 — **211 rods, 47 of them inserted, 4346 cm of total
insertion** — and the generator had been ignoring it, driving every rod channel from one
uniform bank. `U4_RODS=insag` now builds each CPS channel from its own class and its own
sourced depth. That needed two constructions the deck did not have, because the 47 inserted
rods are spread across all four classes (RR 20, AR 12, AZOC 8, AZ 4, USP 3):

* **AR** — top-entry, 5 m absorber, **no displacer** (INSAG-7 §2.2, p. 103). Withdrawn, the
  channel is plain water, so an AR rod contributes nothing at all until it moves. That is the
  opposite of an RR, whose displacer is in the core even when the rod is up.
* **USP** — **bottom-entry**, 3.5 m absorber, no displacer. It suppresses the bottom of the
  flux, the opposite end from everything else in the CPS.

The depths quantise onto the 25 cm axial mesh: 4346 cm of sourced insertion becomes 4425 cm,
**+1.8 %**, and no rod rounds away to nothing (the shallowest, 13 rods at 20 cm, round up to one
plane). That is a real loss of resolution and it is reported rather than absorbed.

### Which immediately found a bug in the uniform bank

Comparing the two ways of building the same core exposed a disagreement, and the per-rod
version was right. `BANKCOL` read `stack(TILT) if TILT else [_W] * NZ_ACTIVE`: with the tilt
off — **every core run to date except the tilt studies** — the 36 AZOC channels were modelled as
pure water columns. But AZOC is the same hardware as RR and AZ, so a withdrawn AZOC channel
contains its 4.5 m graphite displacer exactly as a withdrawn RR does. `stack(0)` *is* the
withdrawn configuration; the special case was not a simplification, it was **36 missing
displacers**.

| rods withdrawn, flat burnup | k | peak channel | MAX/AVG |
|---|---|---|---|
| 36 AZOC as water (as run until now) | 1.038645 | 3517 kW | 1.829 |
| 36 AZOC as withdrawn rods (correct) | **1.045255** | **3058 kW** | **1.590** |
| | **+609 pcm** | −459 kW | −0.24 |

**Corroborated against an independent measurement.** A6.5 put the displacer bank at +2060 pcm
against water columns over the 142 RR/AZ channels; scaled to 36 channels that predicts
**+522 pcm**, against **+609** measured. Same mechanism, right magnitude, the excess being that
the AZOC channels sit at different flux positions from the average RR. It also moves the power
shape a long way — peaking 1.829 → 1.590 — because 36 graphite columns are not a small
perturbation on a core whose moderator is graphite.

Everything in this log that quotes an absolute core k from a `U4_TILT=0` deck is affected by
roughly **+600 pcm**. As section (12) established for the COMPO rebuild, differences fare far
better than absolutes, but this one also moves the power distribution and so is not confined to
k.

### What the real rod pattern is worth: −110 pcm

With the bug fixed, the comparison is finally clean — same deck, same everything, 47 rods moved
from withdrawn to their sourced depths:

| | k | peak channel | MAX/AVG |
|---|---|---|---|
| all rods withdrawn | 1.045255 | 3058 kW | 1.590 |
| **the 01:22:30 pattern** | **1.044059** | **3025 kW** | **1.573** |
| | **−110 pcm** | | |

**47 rods, 4346 cm of absorber, worth 110 pcm — 2.3 pcm per rod.** That is the accident in one
number. The absorber entering the top of each channel is very nearly cancelled by the graphite
displacer sweeping water out of the bottom as the same rod goes down, which is the mechanism
A6.5 measured in isolation and this is it operating across a real rod pattern. A control system
with that little worth in its inserted rods is the operating-reactivity-margin problem the
accident reports describe, arrived at here from the geometry rather than assumed.

It is **not** a scram calculation and must not be read as one: this is a static comparison of
two rod positions, with no rod motion, no time dependence and no xenon.

### And the rods do not rescue a wrong burnup placement

| rod pattern | burnup | k | peak channel | MAX/AVG |
|---|---|---|---|---|
| withdrawn | flat | 1.045255 | 3058 kW | 1.590 |
| **01:22:30** | **flat** | **1.044059** | **3025 kW** | **1.573** |
| withdrawn | locally balanced | 1.048422 | 5368 kW | 2.791 |
| 01:22:30 | locally balanced | 1.047346 | 5609 kW | 2.916 |
| 01:22:30 | scattered | 1.049243 | 5818 kW | 3.025 |

Two things fall out. **The flat-burnup core with the real rod pattern lands at 3025 kW and
MAX/AVG 1.573 — inside [D] p.95's published 3000–3200 kW operating range.** That is the first
time the core model has produced a channel power distribution that an operating RBMK could
actually have had, and it is a check on the rod pattern, the reflector and the geometry
together.

But with a *realistic* burnup spread the same rods leave the peak at 5.4–5.8 MW, and in fact
make the peaking slightly **worse**, not better. The real rod pattern was the pattern for the
real burnup distribution; applied to a scattered one it is not flattening anything. So
section (13)'s conclusion survives the correction intact — the placement is still unresolved,
the rods are now fixed and sourced, and the one remaining flattening agent is **xenon**.


### What the correction does to A7

Every A7 number in sections (11) and (12) came from a `U4_TILT=0` deck and so carried the hole.
Re-run with the 36 displacers restored:

| | 36 AZOC as water | corrected | shift |
|---|---|---|---|
| cold, no feedback | 1.038645 | **1.045255** | +609 pcm |
| Doppler only, flow valved | 1.036211 | **1.042750** | +601 pcm |
| Doppler only, uniform flow | 1.036206 | **1.042745** | +601 pcm |
| Doppler + density, flow valved | 1.039528 | **1.046365** | +628 pcm |
| Doppler + density, uniform | 1.040173 | **1.047068** | +630 pcm |
| | | | |
| Doppler feedback | −226 pcm | **−230 pcm** | −4 |
| density feedback | +308 pcm | **+331 pcm** | +23 |
| net feedback | +82 pcm | **+101 pcm** | +19 |
| flow-distribution spread | 59.7 pcm | **64.2 pcm** | +4.5 |
| pinned-pair agreement | 0.5 pcm | **0.5 pcm** | 0 |

The same pattern as section (12) and a useful contrast with it. There the table rebuild moved k
by −20 pcm and the feedbacks by ≤ 2; here the shift is thirty times bigger, and the feedbacks
move by 4 to 23. **Differences are robust against a systematic error, but not infinitely so** —
roughly 3–4 % of the k shift leaks into them either way, which is invisible at 20 pcm and
visible at 600. The density feedback is the one that moves most, +308 → +331, which is what
thirty-six extra graphite columns should do to a void worth.


### Xenon: a level is free, a field is not — correcting the A6b conclusion

A6b dropped the xenon axis on 2026-10-01 on the grounds that `NCRLIB.f:268` lets `NCR: … MICRO`
replace a stored isotope density before rebuilding the embedded macrolib, so "a xenon field
costs a `MICRO` clause from the core side and no rebuild". Checked properly now that it is
about to be used, **that is true of a xenon *level* and not of a xenon *field*.**

`MICRO` sits inside a `MIX` clause and reads one scalar per isotope — `CONCMI(NISOMI)` at
`NCRRGR.f:326`, stored at `:919` as `CONC(NTOT, ISO)` where `NTOT` indexes the **mixture**.
There is no channel index anywhere on that path. One fuel mixture therefore carries one xenon
concentration, core-wide.

Unit 4 at 01:23 is the opposite of uniform: the xenon was built up from twelve hours at half
power, then the flux collapsed at 00:28 and stopped burning it out while I-135 kept decaying
into it, so the poisoning is strongly shaped by the local power *history*. A single number
cannot represent it.

The way through does not need a rebuild either, and it is worth writing down before it is
built: **bin the xenon field and give each bin its own fuel mixture.** The fuel map already
assigns a mixture per channel through `FMIX`, and `NCR:` already takes several `MIX … ENDMIX`
clauses, so N xenon levels cost N fuel mixtures and N `MICRO` clauses. The axis the A6b
rebuild avoided is still avoided; what it costs instead is mixture count, which is cheap.

That leaves the xenon *field itself* as the input to produce — an I-135/Xe-135 solve per channel
over the published power history (INSAG-7's account of the run-down) rather than an equilibrium
assumption, since the whole point is that the core was far from equilibrium.


## A6b: the xenon level at 01:23, solved rather than assumed — 2026-10-05 (15)

### First, what xenon is worth here at all, because nobody had measured it

The COMPO has carried Xe-135 and I-135 in its `MICR` list since A5b, and the core has been
using the stored densities all along — equilibrium at the depletion power — without anyone
putting a number on them. `MICRO ALL Xe135 0.0` against the stored value:

| | k | peak channel | MAX/AVG |
|---|---|---|---|
| Xe-135 removed | 1.070348 | 3023.6 kW | 1.5722 |
| equilibrium Xe-135 | 1.044059 | 3025.1 kW | 1.5730 |
| | **−2352 pcm** | | |

**Equilibrium xenon is worth −2352 pcm, about −3.1 $.** That is ten times the Doppler feedback
and seven times the void feedback, and it sits in every core result quoted so far. The power
shape barely moves, which is the expected signature of a *uniform* poison and a check that the
override is doing what it claims.

`ALL` is required, not `ONLY`: `NCRLIB.f:364` shows `ONLY` **discards** every isotope not
listed, which would throw away the whole depleted inventory. And `MICRO` must come last in the
`MIX` clause, because `NCRRGR.f:316-335` reads isotope/value pairs until it sees `ENDMIX`.

### Then the 01:23 level, with every constant read out of the library

Equilibrium is not the accident state. Unit 4 had spent most of a day at half power, collapsed
to 30 MW at 00:28, and been dragged back to 200 MW — and with Xe-135 at 9.14 h and I-135 at
6.57 h that history is still in the core. `tools/a6b_xenon.py` integrates the I/Xe pair over it.

Nothing in it is chosen:

| quantity | where it comes from |
|---|---|
| decay constants | the COMPO's own `DEPL-CHAIN/DEPLETE-DECA`, units 1e-8 /s. They return **6.570 h** and **9.140 h** — the accepted half-lives, which is how the units and the indexing were confirmed |
| fission yields | `DEPL-CHAIN/FISSIONYIELD`, 13 products × 16 parents. Groups 4 and 5 are I135 and Xe135; the U235 entries read **6.2805E-02** and **2.5610E-03** against accepted 0.0629 and ~0.0024, which is how the layout was identified |
| equilibrium densities | `ISOTOPESDENS`, interpolated between the 10 000 and 12 500 nodes to the core's own 10 900 MWd/t |
| burnout rate σφ₀ | **calibrated from the stored equilibrium**, not from a flux estimate and a tabulated cross section: σφ₀ = λ_I(I/Xe)(1+r) − λ_Xe. Comes out **6.35E-05 /s = 3.0 λ_Xe**, so burnout-dominated at power, and implies a thermal flux of order 2×10¹³ |
| power history | INSAG-7 Table I-I and §I-4.7.6 |

The only soft input is r = γ_Xe/γ_I, because the fissioning mix at 10.9 MWd/kg is part U235 and
part Pu239. Both library values are carried as bounds and the answer moves by 0.001, because r
itself is small. The initial condition is exactly consistent by construction — substituting the
stored densities at p = 1 gives dI/dt = dXe/dt = 0 identically, since σφ₀ was defined from that
same balance — so the solve starts at rest and every later deviation is the history doing work.

| waypoint | P/P₀ | Xe/Xe_eq | I/I_eq |
|---|---|---|---|
| 25 Apr 01:06, 3200 MW, equilibrium | 1.000 | 1.000 | 1.000 |
| 25 Apr 12:36 | 0.469 | **1.181** | 0.661 |
| 25 Apr 23:10 | 0.469 | 0.969 | 0.532 |
| 26 Apr 00:33, the 30 MW floor | 0.009 | 0.995 | 0.498 |
| 26 Apr 01:00 | 0.062 | 1.022 | 0.477 |
| **26 Apr 01:23** | 0.062 | **1.039** | 0.460 |

**Xe-135 at 01:23 is 1.039 × the equilibrium the table stores, worth −92 pcm more.** Measured
directly: 1.044059 → 1.043056. That is far smaller than the −2352 pcm of the equilibrium itself,
and it is the answer to whether the stored densities were good enough — for the *level*, nearly.

### The number that matters is not the level but the slope

The xenon peaked at **1.18 ×** after the power reduction, decayed back below equilibrium by
23:10, and at 01:23 was **rising**. The quasi-static level for 200 MW with the iodine then in
the core is **1.502 × equilibrium** — worth roughly −1180 pcm — and the core was only **8 % of
the way there**, having entered that transient fifty minutes earlier against a 9.14 h timescale.

So the reactor was early on a steep poisoning curve, climbing towards something worth an order
of magnitude more than it had yet accumulated, while the 47 inserted rods held **−110 pcm**
between them (section 14). The two numbers belong together, and both come out of geometry and
sourced history rather than narrative.

### A reference error, caught by its own control

The first attempt read the densities at burnup **node** 10 000 rather than interpolating to the
core's 10 900. The control for this is obvious in hindsight — write the stored density back
through `MICRO` and the result must be a no-op — and it failed by **−49 pcm**, which also made
the xenon worth look 65 % non-linear. The node values explain it exactly: Xe falls 1.09500 →
1.03440 → 0.97266 E-10 across the 10 000 / 12 500 / 15 000 nodes, so 10 900 interpolates to
1.07318E-10 and the node value is 2.03 % high — predicting 48 pcm against the 49 measured.

With the interpolated reference the control is **bit-exact (+0.0 pcm)** and the worth is linear:
−92 pcm measured against −91 predicted from the equilibrium worth. The override path is
therefore validated rather than merely used.

That burnup dependence is itself a check on the stored data. **I-135 is nearly flat across the
nodes while Xe-135 falls 11 %**, which is what constant specific power demands: Σf·φ is fixed,
so I_eq = γ_I Σf φ/λ_I does not move, while φ must rise as Σf falls, so σφ grows and
Xe_eq = (γ_I+γ_Xe)Σf φ/(λ_Xe+σφ) drops.

### What is still open: the shape

This is a **point** solve, so it gives a level and not a field, and a uniform level is all the
`MICRO` path can carry anyway (section 14: `CONC` is indexed by mixture). For the level that is
now shown to be adequate — the whole core-average effect is −92 pcm.

The shape is the part that matters and the part nobody has. INSAG-7 names it directly: the
00:28–00:33 manoeuvre "gave rise to a new xenon reshaping of the power density fields which the
personnel were unable to control", and then, remarkably, **"no calculational studies have been
made of the power density field dynamics from this time until the time of the accident."** A
per-channel field needs the per-channel *flux* history, which needs the core solved repeatedly
through the run-down — and the binned-mixture machinery to carry it is designed (section 14) but
not yet needed.


## The binned-mixture machinery, and xenon as a flattening agent — 2026-10-05 (16)

### The machinery, with the two regressions it had to pass first

`NCR:`'s `MICRO` clause carries one concentration per **mixture** (section 15), so a per-channel
xenon field costs fuel mixtures rather than a branch axis. `U4_XEBINS=N` now splits the fuel
into N mixtures, `M_FUEL … M_FUEL+N−1`, with `USPLIT:` taking `NFUEL N FMIX 8 9 …` — the
indices must leave no gap, because `USPLIT.f:180` requires `NREFL + NFUEL` to equal the highest
material index exactly. The fuel map's own `MIX` array assigns each channel its bin, and `NCR:`
emits one `MIX … ENDMIX` clause per bin.

Two regressions, run before any new physics:

| | result |
|---|---|
| `U4_XEBINS=1` | the deck is **byte-identical** to before the change — the machinery is invisible unused |
| `U4_XEBINS=4`, all four bins at the same density | **k bit-identical**, +0.00 pcm — splitting the fuel into identical mixtures adds nothing |

The second is the one that matters: it separates "the binning is correct" from "the field does
something". One bug was found getting there, and it is the kind that would have been invisible
later: `plane()` hands its callback **unpadded** lattice coordinates while the channel-number map
is keyed on **padded** ones, so the bin lookup raised a `KeyError` on the first non-fuel cell it
reached. Indexed explicitly rather than given a default, so a future frame mismatch fails loudly
instead of quietly assigning bin 0.

### A uniform level moves k and nothing else — which is the control

| | k | peak channel | MAX/AVG |
|---|---|---|---|
| uniform Xe at equilibrium | 1.044059 | 3025.1 kW | 1.5730 |
| uniform Xe at the field's mean, 1.043× | 1.042949 | **3025.1 kW** | **1.5730** |
| the 8-bin field, identical mean | 1.042037 | 2793.7 kW | 1.4527 |

Raising a *uniform* xenon by 4.3 % costs **−102 pcm** and leaves the power distribution
identical to four decimal places. Replacing it with a field of the **same mean** costs a further
**−84 pcm** and moves the peak channel by −7.6 %. So level and shape are cleanly separable here,
and the uniform case behaving as a pure reactivity shift is the check that the field effect is
real rather than an artefact of having split the mixtures.

### Xenon is the flattening agent section (13) was missing

Section (13) left the burnup placement unresolved because nothing in the model flattened a
realistic placement: the sourced rod pattern did not (section 14), and local balance barely did.
Xenon does, and the mechanism is specific: at 200 MW the burnout term is negligible against
decay, so Xe-135 tracks the iodine left by the **past** power shape — high-power channels carry
more poison. That is negative feedback on the shape.

| realistic burnup (chequerboard) + 01:22:30 rods | k | peak channel | MAX/AVG |
|---|---|---|---|
| uniform xenon | 1.047346 | 5608.8 kW | 2.9164 |
| xenon field, one pass | 1.045153 | 4137.0 kW | 2.1512 |
| xenon field, **self-consistent** | 1.045234 | **4730.9 kW** | **2.4600** |

**−16 % on the peaking, −193 pcm on k.**

### The fixed-point iteration diverges, and under-relaxation is not a convenience

Rebuilding the field from the latest power each pass **diverges**: the peak channel went
5609 → 4137 → 5870 → 4561 → **6568** kW. Loop gain above one, the same shape of failure as the
placement solver in section (13) — the field over-corrects a peaked power, the flattened power
then gives a flat field, and the next pass undoes it.

It is also not the physics. Xenon has a **9.14 h** time constant and cannot respond to a power
it has just changed; an undamped fixed-point iteration asserts that it can. Under-relaxing the
power ratios at w = 0.35 (`U4_XERELAX`, state carried in `U4_XESTATE`) converges in six passes
to 4731 kW, and the one-pass 4137 kW was a 26 % over-correction against the true 16 %.

What the converged number *is* deserves care: it is the field the core would settle into **if
200 MW were held until xenon equilibrated with its own shape**. That is a bounding question, not
the accident state — section (15) measured the real 01:23 xenon at only **8 % of the way** into
that transition.

### Two limits on this, both worth stating

**It does not rescue the placement.** At MAX/AVG 2.46 the chequerboard placement is still far
from the 1.57 the flat-burnup core gives, so a realistic burnup spread plus the real rods plus a
self-consistent xenon field still does not produce an operable full-power shape. Section (13)'s
conclusion survives all three inputs being present: the real placement has to be something more
ordered than any of these guesses.

**And the full-power test needed a different field — which turned out not to matter for shape.**
The channel-power limit binds at full power, not at 200 MW, so the operability argument needs the
full-power equilibrium field rather than the 01:23 one. `U4_XEHIST=equil<f>` builds it from the
same machinery, in closed form, since equilibrium needs no integration:
Xe = (1+r)·λ_I·I_eq·p / (λ_Xe + σφ₀·p). At s = 1, p = 1 it returns the stored density to every
digit — independent confirmation that the COMPO's isotopics really are the 3200 MW equilibrium and
that σφ₀, calibrated from the I/Xe ratio, is consistent with them.

I predicted it would be the weaker flattener by **3.4 ×**, from the shape sensitivity
dln(Xe)/dln(s) = 1/(1 + σφ/λ_Xe), which is 0.841 at 200 MW against 0.249 at 3200 MW because
σφ₀ = 3.015 λ_Xe for this lattice. **The measurement says otherwise:**

| chequerboard + 01:22:30 rods, converged | k | peak channel | MAX/AVG | Δρ |
|---|---|---|---|---|
| uniform xenon | 1.047346 | 5608.8 kW | 2.9164 | — |
| the 01:23 field | 1.045234 | 4730.9 kW | **2.4600** | −193 pcm |
| the 3200 MW equilibrium field | 1.046546 | 4722.3 kW | **2.4556** | **−73 pcm** |

The shapes agree to **0.2 %** while the reactivity costs differ by **120 pcm**. The sensitivity
argument used the wrong lens: it prices the gradient at the *peak*, where the 01:23 field is
indeed ~3.7 × steeper, but the chequerboard spread has a wide **low**-power tail, and there the
equilibrium field collapses to **0.50 ×** equilibrium against the 01:23 field's **0.94 ×** — the
latter cannot fall further in the 24 h available against a 9.14 h constant. The flattening gets
done from the valleys instead of the peak and lands in the same place.

Two consequences. The −73 pcm is nearly **all shape**: the equilibrium field holds *less* total
xenon than the uniform case — Xe(s) is concave, so the channel mean falls below Xe(s̄) — and still
loses reactivity, because the poison sits where the flux is. And for A8, which is driven by
differences, the peaking a xenon field imposes is **robust to which field is used**: the choice is
worth 120 pcm on the eigenvalue and essentially nothing on the shape. The operability conclusion
is unchanged either way — 2.456 against the flat core's 1.573.


## What the operability test does and does not test — 2026-10-05 (17)

### A conflation, narrower than first written

*This section was first committed (`edfac73`) claiming that every core result in sections
(13)–(16) conflated a 200 MW state with a full-power limit. That was an over-correction and is
retracted here; what follows is the narrower claim that survives checking.*

Every core result is normalised to **3200 MW** — `FLPOW: … PTOT 3200.0`. The question is which of
them is a *self-consistent* full-power state, and that turns on the xenon, because
`U4_XENON=stored` (the default) leaves the COMPO's depleted Xe-135 and I-135 in place and those
densities **are the 3200 MW equilibrium**. Section (16) proved it without meaning to: the closed
form `xenon_equilibrium(s=1, p=1)` returns the stored density to every digit.

So the default decks — flat burnup, the placement sweep, chequerboard with uniform xenon — carry
full-power equilibrium poison **and** a full-power normalisation. They are coherent full-power
calculations, and comparing their peak channel power against [D]'s published **3000–3200 kW** is
legitimate. The flat-burnup result stands as section (14) reported it: **3025.1 kW / MAX-AVG
1.5730** for a core at full power with equilibrium xenon and the rods at their 01:22:30 depths.

The conflation is confined to the **`U4_XEHIST=0123`** runs. Those replace the stored equilibrium
with the 200 MW transient field solved in section (15), while leaving the normalisation at
3200 MW — a poison distribution from one power and a power level from another. Section (16)'s
4730.9 kW is therefore not a valid full-power statement, and the sensitivity question that
prompted the equilibrium field turns out to have mattered for a second reason: **the
`U4_XEHIST=equil1.0` run is consistent again**, and it is the one to quote.

### Which restores the placement conclusion

| chequerboard + 01:22:30 rods | xenon | normalisation | peak | MAX/AVG | valid? |
|---|---|---|---|---|---|
| uniform stored | 3200 MW equilibrium | 3200 MW | 5608.8 kW | 2.9164 | yes |
| the 01:23 field | 200 MW transient | 3200 MW | 4730.9 kW | 2.4600 | **no — mixed states** |
| the equilibrium field | 3200 MW | 3200 MW | **4722.3 kW** | **2.4556** | **yes** |

4722 kW is **1.5 ×** the top of [D]'s range on an internally consistent calculation, so the
chequerboard placement *is* falsified, and the core-scale placements (7.615 and 10.159) far more
so. Section (16)'s conclusion survives — it just needed the full-power field to be stated
properly, which is the same correction, arrived at from the other side.

### And the unpoisoned baseline, which is a control rather than a case

`U4_XENON=none` removes Xe-135 and I-135 outright:

| flat burnup + 01:22:30 rods | k | peak | MAX/AVG |
|---|---|---|---|
| no xenon at all | 1.070348 | 3023.6 kW | **1.5722** |
| stored, i.e. 3200 MW equilibrium | 1.044059 | 3025.1 kW | **1.5730** |

**+2352 pcm** of reactivity and **0.05 %** of shape. That reproduces the equilibrium worth of
section (15) exactly, and it is the same signature the level/shape decomposition relies on: a
*uniform* poison is a pure reactivity shift and does not redistribute power. So the unpoisoned
core is not a separate operability case — it has the same shape as the poisoned one, and only its
eigenvalue differs.

### The caveat that is actually left

Not the normalisation but the **criticality**. These cores sit at k ≈ 1.044, so the shape being
compared is a supercritical core's. Holding it at 3200 MW would need enough extra absorber to
bring k to 1, and the shape would move — by how much is unmeasured, and the one measurement
available says uniform insertion moves it the wrong way. That is the honest residual, and it sits
on top of the `TG` pinning already recorded in A7 (worth ~+500 pcm), which is why the eigenvalue
is not quoted as a result.

### The placement sweep, which was never affected

Every variant here runs at `U4_XENON=stored`, so all five are consistent full-power states, and
only the placement moves between them:

| placement, rods out, 3200 MW equilibrium xenon | k | peak at 3200 MW | MAX/AVG |
|---|---|---|---|
| flat, every channel at 10 900 | 1.045255 | 3057.5 kW | **1.590** |
| chequerboard (lattice scale) | 1.048422 | 5367.7 kW | 2.791 |
| random | 1.043832 | 5625.4 kW | 2.925 |
| most-burnt centre, fresh edge | 1.063382 | 14625.6 kW | **7.615** |
| fresh centre, most-burnt edge | 1.170692 | 19546.6 kW | **10.159** |

Both **core-scale** placements are catastrophic, and the one that should flatten by textbook
low-leakage reasoning — burnt fuel inside, fresh at the periphery — is the second worst. [PAV]'s
histogram is simply too wide to be grouped spatially: 172 assemblies at 1.2 MWd/kgU put together
anywhere make a reactivity island, and the burnup axis is steep enough (k = 1.314 fresh) that the
flux goes there. Only placements varying **faster than the migration length** come close, and the
finest such pattern available on a lattice, nearest-neighbour alternation, still gives 2.79 —
4722 kW once its own equilibrium field is added, against [D]'s 3200 kW ceiling.

### Rods are not a generic flattening agent in this model

The obvious objection is that the operating rod pattern would flatten a core-scale placement. The
model says uniform insertion does the opposite — measured on flat burnup, where there is no
placement effect to confuse it:

| flat burnup | k | MAX/AVG |
|---|---|---|
| all rods out | 1.045255 | **1.590** |
| rods at the 01:22:30 depths | 1.044059 | 1.573 |
| all rods fully in | 0.987927 | **2.249** |

Fully inserting all 211 rods costs −5552 pcm and makes the core **less** flat, because the rod
sites are not uniformly distributed and suppressing them all distorts the shape rather than
levelling it. Radial flattening needs rods positioned **individually**, which is an inverse
problem whose answer — the full-power operating rod pattern — is not sourced. So the model cannot
rescue a 7.6 by any rod pattern it is able to construct, and core-scale placement is ruled out.
Lattice-scale placement is ruled out too, but only by its own full-power number — 4722 kW against
3200 — and by a smaller margin, so it is the one an individually-positioned rod pattern could
still in principle recover.

### The test that would actually decide it

A placement is admissible if **some** rod pattern takes it to MAX/AVG ≲ 1.4 at full power with the
full-power xenon field **and** brings k to 1 while doing it — the two are one problem, since the
absorber that flattens is the absorber that holds the core down. That is a well-posed inverse problem on 211 rod depths, it needs no source
beyond the limit itself, and it is the right successor to `tools/a6d_place.py` — which solved the
wrong problem (iterating a refuelling rule) and diverged doing it. Until it is run, the honest
statement is that the placement is bounded below by flat and above by core-scale, and that
everything between is open.


## Solving for the rod pattern — 2026-10-05 (18)

Section (17) left one question: a burnup placement is admissible if **some** rod pattern takes it
inside [D]'s 3000–3200 kW at full power. That is an existence question about 190 rod depths, well
posed without a source because the *target* is sourced even though the pattern is not. What comes
out is not the historical pattern — INSAG-7 gives the 01:22:30 depths and nothing for normal
operation — but whether an admissible pattern exists at all.

### The machinery, and the two regressions it passed first

`U4_RODDEPTH=<file>` replaces the sourced `depth_cm` of the top-entry rods while keeping every
rod's sourced **type** and **site**, checked against the channel map for length and travel before
it is trusted — the same discipline `U4_BURNMAP=file` applies to the burnup histogram. The deck is
content-addressed on the depth file (rule 7) so a pattern can never be served a result built from
a different one.

| | result |
|---|---|
| no `U4_RODDEPTH` | the deck is **byte-identical** to before the change |
| the sourced depths written back through it | **no-op**, identical deck modulo the stem |

190 rods are solved for (RR 121, AZOC 36, AZ 21, AR 12). The 21 bottom-entry USP keep their
sourced depths, being a distinct system on a 3.5 m absorber.

### Criticality was deliberately not used as a target

Reaching k = 1 from the rods-out 1.045255 needs **4330 pcm**, and all 211 rods fully in are worth
5552 pcm, so it takes about **190 rods at four fifths of their travel**. A real RBMK at full power
carries 55–70 inserted. That gap is a statement about the *model's* excess reactivity — `TG` is
pinned ~120 K low, worth about +500 pcm (A6b), and the reflector is still a placeholder — not
about the rods. Driving k to 1 by adding absorber would be compensating a known modelling bias
with physical absorber, which is rule 1. So shape was solved at a stated insertion **budget** and
the resulting k reported as a diagnostic.

### The answer: a best pattern, and it does not reach the target

Ranking the rod sites on local power and laying a monotone depth profile over the ranks reduces
190 unknowns to two — **B**, the budget, and **A**, how hard the pattern discriminates — which
also avoids the fixed-point iteration that diverged twice already in this project.

| | best found | at | k | peak |
|---|---|---|---|---|
| chequerboard burnup | MAX/AVG **2.2398** | A = 4, B = 8 | 1.041362 | 4306.7 kW |
| flat burnup (the control) | MAX/AVG **1.5347** | A = 4, B = 4 | 1.042989 | 2951.3 kW |

Against the sourced pattern's 2.9164 and 1.5730 — a 23 % improvement on the badly peaked core and
**2.4 %** on the flat one. Neither reaches the ≲ 1.4 a full-power core needs, and the chequerboard
is not close. Every deeper budget is worse: at B = 20, where k finally approaches 1
(0.9853–1.0032), MAX/AVG is **3.50 to 10.09**. In this model **flatness and criticality are
opposed**, which is the single most useful thing the solve produced.

### Per-rod refinement fails, and the diagnosis changes the method

Refining per rod from the best chequerboard point made it steadily **worse** and then converged
there: 2.2398 → 2.94 → 3.56 → 4.14 → … → **4.28**, with the number of rods still moving falling to
13. A damped loop converging to a worse answer is not the divergence of sections (13) and (16); it
is a **wrong model of the control** reaching a self-consistent wrong answer. The update rule
assumes a rod's insertion mainly affects the power around that rod.

It does not. Driving 41 mutually well-separated rods (≥ 6 pitches apart) 24 planes in, worth
−1978 pcm, the 100 fuel channels whose relative power falls most sit at a mean distance of
**2.80** pitches from the nearest moved rod against a core-wide mean of **2.75** — uncorrelated
with rod proximity — while their mean radius from the core centre is **21.3** against **17.4**.
The response is a **global radial redistribution**, not a set of local depressions, so a diagonal
per-rod feedback rule is solving the wrong problem and the two-parameter global family beats it.

The right method is therefore a **response matrix** — measure ∂(channel power)/∂(rod depth) and
solve the linear system — rather than local feedback. That is affordable (the responses of
well-separated rods can be measured several at a time) and it is the successor to this work.

### What this does NOT establish, stated because the first draft claimed it

The first version of this section concluded that the rods have **no local shape authority**, from a
near-field mean of +0.2 %. That does not hold up. At −1978 pcm the per-channel scatter is ±35 %,
so a 163-channel bin has a standard error of ~2.7 % and the mean establishes nothing. Repeating it
at 2, 4 and 8 planes (−19, −73, −297 pcm) puts every bin at the 0.01–0.3 % level with strongly
skewed per-channel distributions that a binned mean mishandles — the bin means do not even average
to zero, which is how the skew announces itself.

So **how much local authority the rods have is unmeasured**, and it is exactly what the response
matrix would answer. It was also wrong to attribute the shortfall to a missing A6.4b rod-cell
equivalence: that work was built and **disproved on 2026-09-30**, and it concerned the integral
worth (7–10 % on the displacer and drained channel), not the local shape.

### A second result, from the uniform sweep, which is not about the solve at all

The same data shows **k is not monotone in rod depth**:

| uniform depth | absorber / displacer / water, planes | k | MAX/AVG |
|---|---|---|---|
| 20 | 20 / 3 / 5 | 0.991208 | 2.1201 |
| 24 | 20 / 0 / 8 | **0.968386** | 2.9564 |
| 28 (fully in) | 20 / 0 / 8 | **0.987927** | 2.2488 |

The last four planes of travel are worth **+2000 pcm**. At 24 planes the displacer has been fully
expelled and the absorber spans planes 5–24; at 28 it has relocated to planes 1–20, out of the top
and into the bottom. Moving absorber from the upper core to the lower core *releases* reactivity,
so the axial flux is top-peaked here — and this model therefore reproduces non-monotone rod worth
at **core** scale, not only in the A6.5 single-channel gate. MAX/AVG is non-monotone with it, worst
at 24 planes rather than at full insertion.

And one more, from the shallow end: between 2 and 12 planes of uniform insertion k moves
**1200 pcm** while MAX/AVG sits at 1.82–1.83. Over the range an operator actually works in, these
rods move reactivity and barely touch the radial shape.


## The rod response matrix, and why each rod is its own problem — 2026-10-05 (19)

Section (18) solved for a rod pattern with a local rule and it walked uphill. The diagnosis there
was that the response is not local; this section measures what it actually is, and the answer
reorganises the problem.

### A single rod acts on the far side of the core

Rod 29 is an RR at lattice site (21, 9). Driven 24 planes in on the chequerboard core — worth
**−37.9 pcm**, a small perturbation — the ten channels it moves most are at (25, 38), (24, 39),
(24, 41) and their neighbours: **29 to 33 pitches away**, across the core. And the response has
no distance dependence at all:

| distance from the rod, pitches | 0–1.5 | 1.5–2.5 | 2.5–4 | 4–8 | 8+ |
|---|---|---|---|---|---|
| channels | 8 | 12 | 20 | 132 | 1489 |
| mean \|dP\|, kW | 194.8 | 223.0 | 220.6 | 207.9 | **192.3** |

Half the total \|dP\| is carried by channels at a **mean distance of 25 pitches**. One rod moves a
single channel on the opposite side of the core by **1478 kW**, against that channel's own 2960 kW.
A 38 pcm perturbation is not diffusing outward from the rod — it is rotating a nearly degenerate
flux eigenmode, and the core's peak *rises*, 5326 → 5593 kW, MAX/AVG 2.7694 → 2.9083.

That is the first-azimuthal-mode behaviour this project exists to study, appearing unbidden in a
steady-state rod measurement. It also explains (18) completely: a rule that moves each rod on its
own neighbourhood is reading a signal that carries none of the information.

### The response factorises, which makes the matrix affordable

The worry was cost. A response that is non-monotone in depth seems to need every rod measured at
every depth — 190 × 8 = 1520 runs, about 17 h. It does not, because the response separates into a
fixed direction and a shared amplitude.

**Direction.** For one rod, the cosine similarity between its response vectors at 4, 8, 16 and 24
planes is **≥ 0.9975**, and the single most-affected channel is the same at every depth. Where a
rod pushes power does not change as it goes deeper; only how hard.

**Amplitude.** That "how hard" is one curve, shared by every rod. Measured on five rods (four RR
and one AZ, spread across the core) at eight depths, \|dP(d)\| normalised to its value at 16 planes
agrees to within **0.054 at worst, about 4 %**:

| depth, planes | 2 | 4 | 8 | 12 | 16 | 20 | **24** | 28 |
|---|---|---|---|---|---|---|---|---|
| amplitude | 0.023 | 0.088 | 0.342 | 0.689 | 1.000 | 1.188 | **1.246** | 1.189 |
| worth | 0.018 | 0.074 | 0.288 | 0.576 | 0.821 | 0.960 | **1.000** | 0.959 |

The curve *is* the physics. A top-entry absorber enters the low-flux top of the core, so the first
two planes do **2 %** of what the rod can do; it reaches maximum effect mid-travel; and past 24
planes the displacer has been fully expelled and the absorber relocates toward the bottom, so both
curves **turn over**. That is section (18)'s +2000 pcm over the last four planes, now recovered
per rod rather than in a uniform bank, and it means the response per plane varies by a factor
**5.7** across the travel.

So one run per rod measures the direction and the shared curve carries it everywhere: **190 runs,
not 1520.** The curve is monotone only on [0, 24] planes, so the control is invertible only there,
and the solve is confined to it.

### The control is low-rank but not degenerate, and the rods are not interchangeable

Eight rods spread as widely as the lattice allows, each driven 16 planes in alone:

| rod | site | worth | peak kW | MAX/AVG |
|---|---|---|---|---|
| 131 | (3, 31) | −17.4 pcm | **4828.6** | **2.5107** |
| 33 | (3, 11) | −7.7 | 5192.5 | 2.6999 |
| 0 | (17, 1) | −7.3 | 5371.0 | 2.7927 |
| 96 | (23, 23) | −32.6 | 5579.0 | **2.9009** |

base 5326.1 kW / 2.7694. **One rod** at (3, 31) improves MAX/AVG by 0.26 — more shape than the
entire sixteen-point grid of section (18) found — while a rod worth nearly twice as much at (23, 23)
makes it worse. Their response directions are **anti-correlated**, cosine −0.47 between 131 and 96,
−0.67 between 131 and 68, with positive pairs up to +0.61.

The eight-row response block has an effective rank of **2.83** and its leading mode carries 54 %
of the variance, 74 % for the first two. So the control space is low-dimensional — a handful of
modes, which is why a 190-parameter search found so little — but it is **not** one-dimensional,
and the modes are reachable with opposite signs. There is real authority here; it was simply being
sought in the wrong coordinates.

### What the rods can actually do: 92 % of it is the first azimuthal mode

Decomposing the measured response block on azimuthal harmonics about the core
centre — the fraction of each singular mode's norm captured by cos/sin(mθ), and by a
radial profile:

| mode | % of variance | m = 1 | m = 2 | radial | character |
|---|---|---|---|---|---|
| 1 | 52.2 % | **0.830** | 0.268 | 0.239 | m = 1 |
| 2 | 39.6 % | **0.724** | 0.186 | 0.262 | m = 1 |
| 3 | 3.7 % | 0.142 | 0.593 | 0.017 | m = 2 |
| 4 | 1.3 % | 0.130 | 0.054 | 0.514 | radial |
| 5 | 1.0 % | 0.085 | 0.347 | 0.020 | m = 3 |

Modes 1 and 2 are the two degenerate orientations, cos θ and sin θ, of the **first
azimuthal harmonic**, and together they carry **91.8 %** of everything the rods can
do to this core's power distribution. Everything else — m = 2, the radial profile,
m = 3 — is **6 %** between them.

So the rods **tilt** the core, and essentially nothing else. That is not a defect of
the search, it is the shape of the control, and it explains every result in sections
(18) and (19) at once:

- The effective rank is 2.3 because the control really is two-dimensional: one tilt
  amplitude in each of two orthogonal directions.
- A single rod near the edge (131 at (3, 31)) beat a 190-rod profile because it
  excites the m = 1 pair strongly and in a useful orientation; a rod at the centre
  (96 at (23, 23)), worth nearly twice as much, sits near the mode's node and
  mostly adds reactivity.
- A chequerboard burnup peak is **not a tilt**. Its peaking lives in high azimuthal
  orders and in the radial profile, which is precisely where the rods have 6 % of
  their authority. No rod pattern can flatten it, and the LP will say so.

This is also the mode RBMK cores are known to be unstable in, and the one this
project exists to study — `PROJECT_PLAN.md` names first-azimuthal-mode xenon
instability in its objective. It has now been measured as a property of the rod
control, from a steady-state calculation, before any transient has been run. The
physical reason is size: an 11.8 m core with a migration length of a few tens of
centimetres is neutronically enormous, so the azimuthal harmonics sit very close to
the fundamental in eigenvalue and are the cheapest thing any local perturbation can
excite.

### No rod type or position escapes it — but combinations might

Decomposing each rod's own response, grouped by class and by the rod's radius:

| type | n | mean worth | m = 1 | m = 2 | radial |
|---|---|---|---|---|---|
| AR | 3 | −23.6 pcm | 0.762 | 0.212 | 0.327 |
| AZ | 4 | −29.5 | 0.769 | 0.188 | 0.354 |
| AZOC | 12 | **−35.6** | 0.726 | 0.210 | 0.223 |
| RR | 52 | −21.2 | 0.709 | 0.240 | 0.191 |

| rod radius, pitches | n | m = 1 | m = 2 | radial |
|---|---|---|---|---|
| 8–14 | 4 | 0.690 | 0.139 | **0.458** |
| 14–20 | 19 | 0.724 | 0.179 | 0.284 |
| 20–40 | 48 | 0.718 | **0.259** | 0.162 |

Every class is the same to within 0.06 on m = 1, so **no subset of rods escapes the
tilt**; choosing different hardware is not the lever. (AZOC are the strongest
individually at −35.6 pcm against an RR's −21.2, which fits their being a dedicated
local automatic bank, but their mode content is the same.) Position does
differentiate: inner rods carry the radial content and outer rods the m = 2, so the
two kinds of shaping come from opposite ends of the core.

That leaves one real lever, and it is the whole reason a matrix was worth measuring:
**combinations**. A single rod is 0.71 m = 1 and cannot be anything else, but a
weighted set of rods whose m = 1 components cancel leaves the m ≥ 2 residue behind.
Modes 3 to 5 of the response block carry only 6 % of the variance, so the residue is
small — but it is not zero, and finding it is exactly what a per-rod feedback rule
cannot do and an LP over the full matrix can. Whether 6 % is enough to flatten a
chequerboard peak is the question the solve answers.

### The solve, and why it is an exact linear program

Because the direction is fixed per rod, the model is linear in the **amplitude** even though it is
strongly curved in depth. With u_r = g(d_r) and H the measured response at 16 planes,

    minimise t   subject to   P0_c + Σ_r u_r H[c][r] ≤ t  for all c,   0 ≤ u_r ≤ g(24)

which is an exact LP in 191 variables and 1661 constraints, and the depths come back by inverting
the shared curve. `FLPOW:` holds total power fixed, so every column of H sums to zero and the LP
cannot lower the peak by lowering everything — it can only redistribute. That is checked rather
than assumed: the worst column sum is 2 × 10⁻⁶ of the column norm, i.e. the solver's own
convergence.

H is 1661 × 190 float64 = **2.5 MB** on the CPU. Nothing here approaches the machine's budget.


## The response matrix solved, and the additivity limit it ran into — 2026-10-05 (20)

The full 1661 × 190 matrix took 190 runs at 48 min. Its structure on all columns, against
the 51-column preview of section (19):

| | 51 columns | **190 columns** |
|---|---|---|
| effective rank | 2.32 | **2.09** |
| mode 1 | 52.2 % | **66.0 %** |
| modes 1–5 | 97.9 % | 94.5 % |

and the per-rod worths run −2.0 to −74.6 pcm at 16 planes, −4671 pcm if every rod were
inserted. Mean worth per class: AZ −30.2, AZOC −29.9, AR −24.5, RR −22.0 pcm.

### The unconstrained LP fails the verification, badly

| | peak | MAX/AVG |
|---|---|---|
| base | 5326.1 kW | 2.7702 |
| the LP's linear prediction | 2720.2 kW | **1.4160** |
| rounded to the 25 cm mesh | 2760.4 kW | 1.4369 |
| **DONJON** | **5434.7 kW** | **2.8285** |

The model promised the ≲ 1.4 target and DONJON returned something *worse than the state it
started from*. The reason is in the solution: given all 190 columns the LP chose **93 rods
delivering −2659 pcm**, 33 of them at the depth bound. The per-rod responses are separable —
section (19) measured that — but they are **not additive** at that collective amplitude. The
core's azimuthal modes are nearly degenerate, so a −2659 pcm perturbation moves the very modes
the matrix was measured in. A linear model of a near-degenerate system has a trust region, and
the LP had none.

### With a trust region it works, and the failure is smooth

Capping the total rod worth bounds the perturbation. Every row below is verified in DONJON:

| trust, pcm | rods | mean depth | model MAX/AVG | **DONJON** | model error |
|---|---|---|---|---|---|
| 150 | 10 | 0.37 pl | 1.8513 | **1.8357** | **0.8 %** |
| 250 | 17 | 0.64 | 1.7286 | **1.7791** | 2.9 % |
| 400 | 24 | 1.01 | 1.7003 | 1.7940 | 5.5 % |
| 600 | 34 | 1.51 | 1.6353 | 1.7983 | 10.0 % |
| 900 | 43 | 2.28 | 1.6071 | 1.8949 | 18 % |
| none (−2659) | 93 | 7.77 | 1.4369 | 2.8285 | **97 %** |

The model is good to **0.8 %** at 150 pcm and degrades monotonically. The *verified* optimum is
at **250 pcm**, because beyond it the model's gains are more than cancelled by its growing error
— the classic trust-region trade-off, measured rather than assumed.

### The answer, for one step

**MAX/AVG 1.7791, peak channel 3421.3 kW, k = 1.045552, on 17 rods.**

Against section (18)'s best verified pattern of 2.2398, found by a sixteen-point grid over a
two-parameter family of all 190 depths — a **21 % improvement using 17 rods instead of 190**. The
matrix earned its 190 runs.

It is still **7 % outside** [D]'s 3000–3200 kW, so the chequerboard placement is not yet shown
admissible, and one trust-region step is not the end of the method: this is **sequential linear
programming**, and the next step re-measures the matrix at the new pattern and solves again. Each
step costs another 190 runs.

### Sequential linear programming: it descends, and it decelerates hard

One step is not the method. Re-measuring all 190 columns about the accepted pattern and
solving again — each step another 190 runs at ~48 min — gives, every row verified in DONJON:

Three steps were run. Every row verified in DONJON, best trust region in bold:

| | trust | rods moved | model | **DONJON** | model error |
|---|---|---|---|---|---|
| base | — | — | — | 2.7702 | — |
| **step 1** | **250 pcm** | 17 | 1.7286 | **1.7791** | 2.9 % |
| **step 2** | **150 pcm** | 26 | 1.6701 | **1.7419** | 4.1 % |
| step 2 | 250 pcm | 30 | 1.6287 | 1.8209 | 12 % |
| step 2 | 400 pcm | 37 | 1.5931 | 1.9784 | 24 % |
| step 3 | 75 pcm | 30 | 1.6402 | 1.7259 | 5.0 % |
| **step 3** | **150 pcm** | 31 | 1.6208 | **1.7226** | 5.9 % |
| step 3 | 250 pcm | 37 | 1.6063 | 1.8216 | 13 % |

**2.7702 → 1.7791 → 1.7419 → 1.7226**, with increments **−0.9911, −0.0372, −0.0193**. The first
two ratios are 0.038 and 0.519, so after the huge first step the tail halves each time; a
geometric extrapolation of it gives a limit near **1.702**, peak ≈ 3279 kW. Three more steps at
48 min each would buy the third decimal.

Two things moved against the method as it worked. The usable trust region **shrank** from 250 pcm
to 150, and the model error at a fixed 250 pcm trust **grew** from 2.9 % to 12 % to 13 %. That is
the degeneracy tightening as the method succeeds: a flatter core sits *closer* to mode degeneracy,
so it admits a smaller linearisation, and the method's own progress erodes its step size.

**Best verified: MAX/AVG 1.7226, peak channel 3312.4 kW, k = 1.042069, 31 rods moved.**

### Which overturns the verdict of sections (17) and (18)

The admissibility threshold is sharp: 3200 MW over 1661 channels is a **1927 kW** average, so
[D]'s 3000–3200 kW ceiling is **MAX/AVG ≤ 1.557 to 1.661**.

| | MAX/AVG | peak | against the 3200 kW ceiling |
|---|---|---|---|
| base, sourced rods | 2.7702 | 5337 kW | **+67 %** |
| step 1 | 1.7791 | 3428 kW | +7.1 % |
| step 2 | 1.7419 | 3356 kW | +4.9 % |
| **step 3** | **1.7226** | **3319 kW** | **+3.7 %** |
| extrapolated limit | ≈1.702 | ≈3279 kW | ≈+2.5 % |

Sections (17) and (18) called the chequerboard placement **falsified**, at 2.46–2.79 and 70 %
outside. With the rod pattern actually solved rather than guessed it comes to **3.7 % outside**,
and that is **inside the model's own error bars**: `TG` is pinned ~120 K low, worth about
+500 pcm (A6b); the reflector is still a placeholder; and A6.4 measured the displacer and
drained-channel worths **7–10 % low**, which if corrected makes the rods stronger and the
achievable flattening better.

So the honest verdict is not "falsified" but **marginal, and the model cannot decide it**. That is
a real retraction of a conclusion committed twice today, and the thing that changed it was
measuring the control instead of searching it. The core-scale placements (7.615 and 10.159) are
untouched by this — they remain ruled out by a wide margin.

### A formulation bug that step 1 could not have caught

From step 2 on, `H[:,r]` is the response to moving rod r from **its own base depth** d₀ᵣ to
d₀ᵣ + 16, while the amplitude curve G is a function of **absolute** depth. The response to
putting that rod at absolute depth d is therefore

    H[:,r] · (g(d) − g(d₀ᵣ)) / (g(d₀ᵣ + 16) − g(d₀ᵣ))

and the LP variable is that coefficient. On step 1 every solved rod starts at zero, the
denominator is g(16) and it reduces to g(d)/g(16) — which is why the un-rebased form was right
there and silently wrong here. The first version of `solve()` also wrote **absolute** depths over
the base pattern, discarding the step it was supposed to build on.

Rebasing earns something beyond correctness: the coefficient may go **negative**, so the LP can
**withdraw** a rod. From step 2 on that is half the available control, and it was unreachable
before — the step-2 solve reports a variable range of −1.817 to +1.246 with 17 rods withdrawable.
The rebased code reproduces step 1 exactly (1.7286 model, 1.7791 DONJON, 17 rods), which is the
regression that says the reduction is right.

### A provenance hazard the content addressing caught

The pattern files were first named by a guessed step number taken from the base filename, and it
counted the wrong substring: **step 3 at 150 pcm overwrote the step-2 base pattern it had been
solved from**. The base survived only inside the step-3 `.npz`, where `jacobian()` stores it.

Recovering it exposed something worse and more interesting. The step-1 pattern *file* on disk
hashes to `787dd3d4`, but the base the step-2 matrix was actually measured about hashes to
**`03bbc453`** — they are different patterns. The step-1 solve had been re-run during the
rebasing regression, and the LP returned a **degenerate** optimum: same objective, same verified
1.7791, different depths. Had the filename been trusted, step 2's matrix would have been
attributed to a pattern it was never measured about, and nothing would have complained.

Both the stored matrix and the pattern a solve writes are now named from the **md5 of the base
pattern's content** (`base_id()`), so a renamed or regenerated file still resolves to the right
matrix and two different bases cannot collide — standing rule 7, earning itself. The chain was
then re-verified end to end: solving from the recovered step-2 base reproduces **3312.4 kW /
1.7226 / k = 1.042069** exactly.

The three matrices (2.5 MB each) and the two intermediate patterns are the artefact; the 159
per-probe decks and results, 62 MB, were deleted as regenerable, keeping the step-3 verification
itself.

### What this says about the physics, which is the durable part

The control's **character does not change** with the operating point. Re-measuring at the flatter
step-2 base:

| | eff rank | mode 1 | mode 2 | m = 1 content of the span |
|---|---|---|---|---|
| base = all rods out | 2.09 | 66.0 %, m = 1 0.647 | 19.7 %, m = 1 0.911 | 0.620 |
| base = the 1.7791 pattern | 2.66 | 50.8 %, m = 1 0.779 | 33.6 %, m = 1 0.815 | **0.687** |

Cancelling m = 1 in the **power** does not reduce the m = 1 character of the **control** — it rises
slightly. The tilt dominance is a property of the rod lattice and the core's neutronic size, not
of the state the core is in, so every SLP step meets the same wall: two tilt directions plus a
small m ≥ 2 residue, wherever it starts.

Section (19) found that 92 % of the rods' authority is the first azimuthal mode and concluded
that the only lever left was combinations whose m = 1 parts cancel. That is exactly what the LP
found — and the additivity limit is the same physics seen from the other side. The combinations
that cancel m = 1 are, by construction, the ones that leave the core sitting between
near-degenerate modes, which is precisely where superposition stops holding. **The control is
most useful exactly where it is least linear.** That is a statement about RBMK cores, not about
DONJON, and it is the quantitative form of why these reactors were hard to shape and hard to
keep flat.


## Where the project stands at the A8 boundary, and what A8 will not wait for — 2026-10-05 (21)

Tier A has reached the point the whole plan was pointing at: every input A8 consumes now exists
as a measured artefact rather than an assumption, and the remaining gaps are *priced* rather
than merely known. This section is the review, written before starting A8 so that the decision
to start it is on the record with its reasons.

### What is closed, with the number that closes it

| | Item | Closed by |
|---|---|---|
| A0–A2 | environment, quarantine, 3-D core on real units | k 1.123062; `DUAL 1 1` chosen by measurement after `MCFD 1` was shown to lose 31–34 % of absorber worth |
| A3 | RBMK lattice cell, self-shielded | k∞ **1.313968**, self-verifying volume fractions |
| A4 | SPH | resolved as **not applicable** at cell level |
| A5a | void coefficient | **+1.94 / +2.41 / +2.72 $** at 10.9 MWd/kgU, DRAGON and OpenMC converged |
| A5b/A6b | MULTICOMPO | **1728 points, 12 burnup nodes**; round trip 1.6 pcm; β_eff as a burnup curve, OpenMC to −1.3 % |
| A6.1–2 | CPS supercell | reproduces the single cell to **+2.8 pcm** |
| A6.5 | Unit 4 core, sourced | 1661 + 211 + 12 + 4 = **1888** positions, every count closing against a source not used to build it; displacer **+2060 pcm**; rod travel turns positive once the axial peak is below mid-plane |
| 1b | reflector | the 7152 pcm strip error does **not** propagate: the whole radial reflector is worth 131 pcm and 2.6 pcm leaks past it |
| 2b | `THM:` per-channel flow | invisible when unused (2 597 833 lines, 0 diffs), per-channel when used |
| A7a/b | coupled steady state | one channel against [D] p.95; Doppler **−230**, density **+331**, net **+101 pcm** |
| 0 | kinetics cost | `KINSOL:` on the full core: **0.430 s/step** severe, 0.090 frozen, **105 MB** |
| A6d | initial state | map, per-rod 01:22:30 pattern (**−110 pcm**), xenon level and field, response matrix, SLP to **1.7226** |

Four things were disproved and recorded as such rather than quietly dropped: A6.4b, the
fixed-point placement solve, the per-rod diagonal refinement, and the chequerboard verdict of
(17)/(18). That record is the reason the carried biases below can be trusted as bounds.

### What is carried into A8, all measured and all one-signed

| Bias | Size | Sign on the transient |
|---|---|---|
| `TG` pinned ~120 K below operating temperature | **+500 pcm** | raises k; nothing in DONJON computes a graphite temperature (Phase 2c unbuilt), and the COMPO's `TG` axis stops at 900 K, below the range |
| A6.4 neighbour spectrum | displacer and drained channel **7–10 % low** | makes rods **stronger** when corrected, so computed rod worths are lower bounds |
| A6.3 section worths | **5–12 %** from OpenMC | carried as the A′ correction, bracketed by B |
| burnup placement | up to **+10 860 pcm** across orderings | unresolvable from [PAV]; the largest single unknown in the model |

### The decision: A8 does not wait for the placement

A6d established two things that together settle the sequencing. The placement is **undecidable
from the available sources** — [PAV] gives counts and no map, iterating the refuelling rule
diverges, and the response-matrix solve puts the best achievable chequerboard 3.7 % outside
[D]'s operability ceiling, inside the model's own error bars. And A7's lesson, re-confirmed by
the burnup rebuild, is that **the differences are robust and the eigenvalue is the fragile
number**: the rebuild moved absolute k by 20 pcm and every feedback by ≤ 2 pcm.

A8 is a difference. So the placement enters A8 as a **band**, run across its variants and
reported as a spread, exactly the way the void coefficient is handled under brackets A′ and B.
Waiting for a placement rule the sources cannot supply would stall the objective indefinitely,
and would buy nothing an explicit band does not already give.

### Sequencing, with the cost of each item measured rather than guessed

1. **Source the fuel-failure criterion.** A8 is *defined* to stop at one and it has never been
   sourced. Hours of reading, and the scenario is undefined without it.
2. **Source the RBMK graphite temperature range**, then batch the `TG` axis extension past
   973 K into one COMPO rebuild. 18 h unattended, so it starts early and A8 is coded against
   the present table meanwhile. This is the largest known bias and the longest pole.
3. **Build the A8 deck.** At the measured 0.430 s/step, 4000 steps of 1 ms is **~29 min** per
   scenario — and that measurement was on IAEA constants with no `NCR:` or `THM:` in the loop,
   so it is a **floor, not a budget**. Cost is not what has kept A8 unbuilt; the device
   machinery is, since A6.5 deliberately placed the rods as base-map mixtures and built no
   `DEVINI:`/`DSET:` devices.
4. **Phase 2c graphite conduction**, which turns the `TG` bias from a band into a field.
5. **Defer A6c formally** into the report's known gaps. The loading map is in a 1993–94
   Kurchatov report that is not online; leaving A6c open as a task implies it is being worked,
   and it is not. It is our only measured core-level reference, so its absence is a stated
   limitation of the model, not a pending item.

Tier B and A9 stay parallel, after A8.

## A8: the rods become devices, and three bugs between here and a moving rod — 2026-10-05 (22)

A base-map rod cannot move. `insag_col()` writes the absorber and displacer straight into the
`GEO:` `MIX` block, which is literal text in the deck: once `GEO:`/`USPLIT:`/`TRIVAT:` have run
the mixture field is fixed, and nothing in CLE-2000 can rewrite 6700 integers between time
steps. Regenerating the geometry mid-transient is not an option either, because `INIKIN:` carries
the precursor field on the tracking object's unknown vector and a new `TRACK` invalidates it.

So A8 needs `DEVINI:`/`DSET:`/`NEWMAC:`, and `U4_DEV=1` builds all 211 CPS rods as **389
ROD-DEVICES**: 121 RR + 21 AZ + 36 AZOC each as an absorber *and* a displacer, 12 AR and 21 USP
as an absorber alone.

### Every design choice here was forced by the source, not chosen

| Choice | What forces it |
|---|---|
| **two single-part devices per rod**, not one three-part rod | the real RR rod is 5.00 + 1.25 + 4.50 = **10.75 m** and `DEVGET.f:119-133` rejects any `MAXPOS` outside the 8 m mesh |
| absorber `FROM H+`, displacer `FROM H-` | `DEVGET.f:216-223` **clamps** the position to the mesh, so each part must be declared from the end it never leaves through. A displacer declared `H+` stops the moment it starts leaving the bottom, 525 cm short |
| `XFAC 1.0`, where the default is **2.0** | `NEWMXS.f:61` is σ += XFAC·VF·Δσ, and our Δσ is a whole-cell difference, not a CANDU supercell's |
| `MOVE`, not the default `FADE` | a fading rod scales its deltas in place instead of moving |
| single-part devices (again) | `MOVPOS.f:159` stores `ROD-POS` as **6** reals where `DEVGET.f:246` stored **6·NPART**, so `MOVDEV:` silently truncates a multi-part rod to its first part. With NPART = 1 the bug cannot bite, which is how `MOVDEV:` becomes usable |
| `MOVDEV: … SPEED` for the scram | `MOVPOS.f:111-134` moves the position in **true cm/s along the axis**, so three group statements replace 389 per-rod updates, each rod starting from its own depth |

The last two are worth putting together: the two-device split was forced by a geometry
constraint, and it independently dodges a data-truncation bug and makes the whole scram
expressible in three lines. That was luck, not design, and it is recorded as luck.

### Bug 1: `DEVINI:` must precede `RESINI:`, and getting it wrong is silent

`DEVINI:` appends its device mixtures to MATEX's **`MAT-INIT`** (`DEVDRV.f:143`). `RESINI:`
builds the **`MAT`** record from `MAT-INIT` *at whatever length it has when `RESINI:` runs*
(`RESIND.f:118-126`). And the fuel-map form of `MACINI:` reads **`MAT`**, not `MAT-INIT`
(`MACINI.f:202`).

Put `DEVINI:` after `RESINI:` and `MAT` is 778 entries short. Every device mixture is then read
as a virtual region, and `MACCRE:` packs the macrolib at a stride 778 smaller than the `NMIX`
every reader indexes it by. Two things follow and **neither aborts**: the device cross sections
come out **zero**, so the rods do nothing; and the fission records come out **mis-strided**, so
`NUSIGF` for isotope 9 is read out of isotope 10's data. The bundled `Example1.x2m` has the order
right. This deck did not.

### Bug 2: `U4_RODS=wat` is not an unrodded core

`U4_DEV` needs the base map to hold **no rod material at all**, because `DMIX`'s reference
mixture is the water column. `U4_RODS=wat` is not that: it leaves `RODCOL` water but keeps
`BANKCOL` at `stack(0)`, so the 36 AZOC channels still carry their withdrawn displacer. That is
correct for the base-map route and is exactly the 2026-10-04 fix recorded in section (14) — and
it is a **double count** for the device route, which then adds its own (displacer − water) delta
on top of a node that already holds the displacer:

```
NTOT0 = 0.391106 + (-0.175640) = 0.215466   against SIGW00 = 0.390100
```

a **negative removal cross section**, and `TRIVAA:` stopped with `TRISYS: NEGATIVE XS IN GROUP 2`.
`U4_DEV=1` now forces `BANKCOL` to water and refuses `U4_TILT`.

### Bug 3: DONJON positions every rod along the X axis, whatever `AXIS` says

With the first two fixed the deck ran, and gave k = 1.044609 against the base map's 1.044059 —
**+55 pcm**, with the peak channel the same. I attributed that to the axial-reflector overhang:
the device route unavoidably puts a parked absorber in the reflector above the core, because
`NEWMVF.f:78-82` clips a part to the **mesh**, not to the core, while the base map does not track
rods outside the active core at all.

**That attribution was wrong, and measuring it is what found the real bug.** `U4_RODFULL=1` tracks
the rods over all 32 planes in the base map, making the two routes describe the same geometry;
the overhang turned out to be worth **−1.3 pcm** (1.044059 → 1.044046) and to move the power
distribution not at all. So +55 pcm was something else.

Diffing the two macrolibs node by node localised it exactly: **542 nodes held water where the
base map held absorber, and 190 of them were in each of planes 31 and 32** — that is *every*
top-entry absorber, while every displacer and every bottom-entry USP absorber placed correctly.
Instrumenting `NEWMVF:` at entry gave the rod's position as

```
z = [1359.375, 1859.375]       against a mesh that ends at 800
```

and 1359.375 = 1450 − 0.0625 × 1450, where **1450 cm is the X extent of this core and 800 cm is
the Z extent**. `DEVGET.f:220-222` and `MOVPOS.f:113-134` compute the rod position from
`LIMIT(1)`/`LIMIT(2)` — the X faces — *regardless of `IAXIS`*. (Two of **five** copies of that
formula; see the next subsection, where patching only these two produced a fake result.) The `MAXPOS` validation in the
same routine is correctly axis-indexed; only the positioning is not.

Why this has survived upstream: for `FROM H-` the formula is
`LEVEL*(LENG(2) − LIMIT(1)) + LIMIT(1)`, which is **invisible whenever the two axes share a zero
origin** — so our displacers and USP rods worked, and so does every bundled deck, all of which
move their rods along Y in a core whose X and Y origins are both 0. For `FROM H+` a Z-axis rod is
placed at `X+ − LEVEL·(X+ − LENG(1))` and lands outside the mesh entirely whenever the core is
wider than it is tall. An RBMK is 14.5 m wide and 8 m tall.

### Bug 3 again: the formula has FIVE copies, and patching two of them produced a fake result

The axis fix above was applied to `DEVGET.f` (which `DEVINI:` uses to place a rod from its
`LEVEL`) and to `MOVPOS.f` (which `MOVDEV:` uses for its `ROD` form). The static decks were then
exact, the gate passed, and the first transient produced what looked like the result A8 exists to
find: the power rising 9.3 % over 0.41 s and then turning over as the absorber took hold.

**It was an artefact, and this is the retraction.** `MOVDEV:`'s `GROUP` form does not go through
`MOVPOS.f` at all — it goes through **`MOVGRP.f`**, which carries its own copy of the same
arithmetic. Running `MOVDEV: … EDIT 2` printed the rod it had just moved:

```
MOVCHK: MOVE A ROD BY 1319.3750
Z- 1319.3750      Z+ 1819.3750
```

against a mesh that ends at 800 cm, and 1319.375 is exactly
`(1450 − 0.0625 × 1450) − 40` — the unpatched X-limit formula, one 40 cm step on from where the
unpatched `DEVGET:` had put it. So every absorber was being teleported out of the geometry, where
`NEWMVF.f:78-82` clipped it to nothing. **The 9.3 % power rise was absorbers being deleted from
the core.** It had the shape of the result, the right order of magnitude, and the right timing,
and it was entirely spurious.

Grepping for the formula rather than for the routine found **five** copies in `Donjon/src`:

| routine | reached from |
|---|---|
| `DEVGET.f` | `DEVINI:`, placing a rod at its initial `LEVEL` |
| `MOVPOS.f` | `MOVDEV:`, `ROD` form |
| `MOVGRP.f` | `MOVDEV:`, `GROUP` form |
| `DSETGR.f` | `DSET:`, `ROD-GROUP` form |
| `DSET1D.f` | `DSET:`, `ROD` form |

All five had `LIMIT(1)`/`LIMIT(2)` hard-wired. They must agree or `DEVINI:`, `DSET:` and `MOVDEV:`
put the same rod in three different places, which is precisely what happened. The patch now
covers all five.

**What caught it was a check built to answer a different question.** `A8KFINAL` solves the final
rod geometry statically at the end of a transient and prints its eigenvalue, so that the trace can
be anchored to a static number. One `MOVDEV:` step of 1.0 s at 40 cm/s must therefore reproduce a
static deck built independently with every depth advanced 40 cm:

| | k |
|---|---|
| before the `MOVGRP.f` fix | 1.044095 |
| after it | **1.043293** |
| static deck at +40 cm, built from the depth file | **1.043293** |

Seven figures, from two decks that share no code path beyond the core itself. That check is now
emitted by every transient the generator writes, because a trace whose geometry has not been
anchored to a static eigenvalue is not evidence.

**Standing rule 6 is about our files; this is the same failure in someone else's.** "A fix that
lives in a copy of the file is not a fix" was written after the bound-hydrogen correction sat in
`RbmkLibH.c2m` while the decks being quoted called the broken original. Here the duplication was
upstream's, and the lesson is the same with the search widened: grep for the *expression*, not for
the routine you happened to be reading.

### Two patches, and the regression that says they are invisible when unused

| Patch | What it does |
|---|---|
| `0002-NEWMAC-multi-isotope-macrolib` | `NEWMGT:` aborted on any macrolib whose `NUSIGF`/`CHI` are `NMIX*NBFIS` long, which is every macrolib `NCR:` builds from our MULTICOMPO (**NBFIS = 18**). `NEWMPT:` already declines to write those records back, so leaving them at zero applies no device delta to them — exact for a non-fissile device and wrong for one that moves fuel. `NEWMAC:` now **checks** every rod part and every liquid-controller level against the macrolib's own `NUSIGF` and refuses if any device mixture is fissile, so the degradation can never be silent |
| `0003-DEVINI-MOVDEV-axis-indexed-core-limits` | index `LIMIT` by the rod's declared axis in both `DEVGET.f` and `MOVPOS.f`, which must agree or a rod moved by `MOVDEV:` would not land where `DEVINI:` put it |

Both are in `patches/`, applied idempotently by `tools/apply_patches.sh`, because `5.1/` is
gitignored and a change made only there is lost by a fresh clone. The three bundled decks that
exercise devices — `AFMtest.x2m`, `Candu6.x2m`, `candu6_iram.x2m` — were run before and after and
compared whole-listing: **18 423 comparable lines, 0 differences**. The same discipline the
`THM:` patch shipped with.

It was the NBFIS guard, added for an unrelated reason, that caught bug 1; `TRISYS:` that caught
bug 2; and a node-by-node macrolib diff that caught bug 3 after my own explanation of it failed.
None of the three was found by reading the deck.

### The gate: two independent routes to the same core, agreeing exactly

`U4_RODFULL=1` makes the base map describe the geometry the devices describe, so the two can be
compared with nothing left over. `col32()` derives the full 32-plane column from the rod's
absolute position and is asserted against `stack()`, `stack_abs()` and `stack_bot()` at all 29
depths the 25 cm mesh allows, so the new path cannot drift from the one every A6d result used.

| pattern | | k | peak channel | MAX/AVG | peak ch |
|---|---|---|---|---|---|
| the sourced 01:22:30 depths | base map, 32 planes | 1.044046 | 3025.1 kW | 1.5730 | 3244 |
| | **389 devices** | **1.044046** | **3025.1 kW** | **1.5730** | **3244** |
| every rod 24 planes in (600 cm) | base map, 32 planes | 0.9407398 | 4125.0 kW | 2.1514 | 3747 |
| | **389 devices** | **0.9407398** | **4125.0 kW** | **2.1514** | **3747** |

Writing a mixture map and letting `NEWMAC:` compute volume-fraction deltas from `MAXPOS` and
`LEVEL` are completely different code paths through DONJON, and they agree to **seven figures in
k** at both ends of the travel — the second pattern being a −10 300 pcm perturbation from the
first. That is the regression that licenses moving the rods.

### What this does NOT establish

The devices reproduce the base map **on the 25 cm mesh**, which is the only geometry the base map
can express. `U4_DEVQ=0` lets a rod tip sit mid-node, where `NEWMVF:` splits the node by volume
fraction and there is no base-map answer to check against — and that is precisely the capability
A8 needs, since a rod at 0.4 m/s crosses a 25 cm plane in 0.625 s. The sub-node interpolation is
therefore **unverified against anything** so far, and a timestep study is the only thing that will
test it.

## A8's last two unsourced inputs, both already in the repository — 2026-10-05 (23)

### The fuel-failure criterion

`PROJECT_PLAN` has carried "stops at a defined **fuel-failure criterion** (to be sourced, e.g. a
fuel-enthalpy threshold)" since the plan was written. It is an enthalpy threshold, and it is in
INSAG-7 p. 67 — a source that has been in `sources/` since 2026-09-26. Quoting the mechanism it
attributes to Japanese direct experimental work (its Ref. [35]):

| enthalpy, cal/g UO₂ | kJ/kg | behaviour |
|---|---|---|
| **220** (T = 3300 K) | **920.5** | the fuel elements begin to **disintegrate** |
| 285 | 1192.4 | the fuel elements **rupture** |
| 320 | 1338.9 | they **explode and disperse in small pieces** |

at INSAG-7's own conversion of 1 cal = 4.184 J. The scope boundary in `PROJECT_PLAN` — "the
scenario runs to fuel failure and stops" — therefore becomes **220 cal/g UO₂ = 920.5 kJ/kg**, the
conservative end, and the other two are reported alongside rather than averaged.

INSAG-7 attaches its own caveat and it is carried verbatim rather than paraphrased away: the RBMK
fuel elements "are not entirely identical with the fuel elements used by the Japanese scientists",
so "there may be quantitative discrepancies between the critical enthalpies of the model and the
real fuel elements". A threshold with a stated provenance and a stated caveat is what a gate needs;
a single number with neither is what rule 1 exists to prevent.

This is the second time an input recorded as missing turned out to be in a source already on disk —
the 01:22:30 per-rod depths were the first (section 14). The lesson is the cheap one: search the
sources before scoping the work to find them.

### The comparison target is a band, and the band is the initial state

A8's gate says "compared (not tuned) with INSAG-7 Appendix II's three independent reconstructions".
Reading what those reconstructions actually say changes how the comparison has to be framed.
INSAG-7 p. 69, on Ref. [28]:

> within the limits of a 20% variation in initial power density, the rate of thermal power
> increase may be 400 MW/s or 1000 MW/s by 6 s to 7 s after the start of the transient.
> Accordingly, after 6.5 s, the total reactor power may be **31 or 64 times** higher than the
> initial level. The critical fuel enthalpy may be reached for either **5 or 40** fuel assemblies.

and on Ref. [17], flatly: "The Commission cannot accept the conclusion drawn in Ref. [17], because
the authors are unable to guarantee a high degree of accuracy and the reliability of the
calculation techniques used."

So **a 20 % change in the initial power distribution moves the published answer by a factor of two
in power and a factor of eight in damaged assemblies**, and one of the three reconstructions is
disclaimed by the body that collected it. Two things follow for A8.

First, the comparison target is **31×–64× at 6.5 s and 400–1000 MW/s**, a band, not a number, and
a result inside that band is agreement while a result outside it is the finding.

Second, and this is the part that matters for the method: INSAG-7 is independently asserting that
**the initial-state uncertainty dominates the transient's outcome** — which is exactly what the
A6d row predicted in 2026-09-26 ("its uncertainty probably dominates the transient's") and exactly
what section (13) then measured at up to +10 860 pcm across orderings of [PAV]'s histogram. The
decision recorded in section (21) — that A8 does not wait for a burnup placement the sources cannot
supply, and instead runs across the placement band the way the void coefficient is run across
brackets A′ and B — is therefore not a convenience. It is the only form in which the published
reference can be compared against at all.

## A8: the AZ-5 ramp is negative in this state, and A6.5 said it would be — 2026-10-05 (24)

With the rods movable and anchored (section 22), the first question A8 can ask is the one the
whole project was built for: what is the reactivity of the AZ-5 insertion from the sourced
01:22:30 pattern? The static answer is cheaper and more reliable than the transient, so it comes
first — `tools/a8_ramp.py` advances every CPS rod by d cm from its sourced depth and solves the
core, quoting reactivity the way `KINSOL:` normalises it, ρ = 1 − k(0)/k(d).

| travel, cm | 0 | 5 | 10 | 15 | 20 | 25 | 30 | 40 | 50 | 60 | 80 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **ρ, pcm** | 0 | −10.8 | −19.3 | −25.5 | −30.0 | −32.8 | −48.5 | −72.2 | −88.3 | −129.0 | −202.4 | **−293.1** |
| peak channel, kW | 3025 | 3024 | 3022 | 3021 | 3019 | 3018 | 3016 | 3012 | 3008 | 3002 | 2990 | 3011 |

**Monotonically negative throughout.** There is no positive window anywhere in the first metre of
travel, and the peak channel power falls with it. So in this core state AZ-5 is an ordinary scram.

### Which is what A6.5 predicted, with the condition it attached

Section (5)'s gate measured the displacer sweep as **−175 pcm over the first 1.25 m with a
centre-peaked flux**, turning positive **only once the axial peak is driven below the mid-plane** —
"the sign tracks the peak in both directions". This core's axial peak is at **bundle 14 of 28**,
i.e. the mid-plane, so the gate's condition for a positive sweep is **not met** and the gate
predicts a negative ramp. It is negative. A6.5 was measured on a uniform bank driven from fully
withdrawn and this is the sourced pattern driven by devices, two different configurations through
two different mechanisms in the code, and they agree on sign and order of magnitude.

That is the useful form of the result: **the positive scram is a property of the axial flux shape,
not of the rod geometry**. What sets that shape — the axial xenon and burnup distribution — is the
part A6b and A6d could not source.

*Corrected in (26).* This paragraph first said the real core was bottom-peaked at 01:23:40. It was
not: INSAG-7 Fig. II-5 (p. 116) describes a "double peaked shape with a large upper maximum", and
Fig. II-9 at t = 0 peaks at about 1.5 some 175 cm below the core top. The bottom peak is what the
transient *produced*. And our negative first second is not a disagreement with the reconstructions —
all three INSAG-7 models show reactivity falling in the first second (p. 119).

### What each part of the rod contributes

`U4_DEVADV` advances one device group at a time, which decomposes the ramp for the price of a
static solve. At 40 cm of travel:

| moved 40 cm | ρ, pcm | share |
|---|---|---|
| the 190 top-entry absorbers | **−51.7** | 72 % |
| the 178 graphite displacers | **−20.5** | 28 % |
| the 21 bottom-entry USP absorbers | −11.2 | 16 % |
| absorbers + displacers together | −56.3 | |
| **all three together (measured)** | **−72.2** | |
| the three parts summed | −83.5 | |
| **non-additivity** | **+11.3** | **14 %** |

Every part is negative, including the displacer. Nothing here is cancelling anything; the scram is
negative because all three contributions point the same way. And the parts over-predict the total
by 14 %, which is the same sub-additivity section (20) ran into from the other direction — the
parts shield each other.

Neither single-group row is a configuration of a real reactor: a rod's absorber and its displacer
are one rigid body. They are controls, and the deck header says so.

### A sawtooth with the period of the axial mesh

The local slope of ρ(d) is not smooth. Per interval, in pcm/cm:

| interval | 0–5 | 5–10 | 10–15 | 15–20 | 20–25 | 25–30 | 30–40 | 40–50 | 50–60 | 60–80 |
|---|---|---|---|---|---|---|---|---|---|---|
| dρ/dd | −2.16 | −1.70 | −1.24 | −0.90 | −0.56 | **−3.14** | −2.37 | −1.61 | **−4.07** | −3.67 |

The slope decays smoothly to near zero and then jumps by a factor of five, twice, **at 25 cm and
at 50 cm** — exactly the 25 cm axial plane pitch. The reason is structural: every rod starts on a
plane boundary, because `insag_col()` quantises the sourced depths to the mesh, so all 389 device
tips cross a node boundary *simultaneously* and their individual slope breaks superpose instead of
averaging out. The underlying trend is about −2.5 pcm/cm and the breaks modulate the local slope
around it by roughly ±20 pcm of accumulated worth.

Two things follow. **The 25 cm axial mesh, not only the timestep, limits how finely rod motion can
be resolved in A8** — a rod at 0.4 m/s crosses a plane every 0.625 s, so a 4 s scram crosses six
or seven and the ripple will appear in the power trace as a real feature of the discretisation.
And the smoothness *within* each 25 cm interval is the only evidence that `NEWMVF:`'s sub-node
volume-fraction interpolation works at all, the base map having no answer to compare against off
the mesh: a broken interpolation would have given a staircase, and it gives a smooth curve with
breaks only where the model must have them.

### The regression caught a bug in the patch that the physics would have hidden

Extending patch 0003 from two copies of the formula to five broke `AFMtest.x2m`, which stopped
silently after `LZC:` with no abort message. The cause was mine: in `DSETGR.f` and `DSET1D.f` the
`CORE-LIMITS` fetch happens **before** `IAXIS` is read, so `ILIM=2*IAXIS-1` placed beside the
fetch indexed `LIMIT` with uninitialised memory. `MOVGRP.f` reads `AXIS` first and was
unaffected, which is why our own decks ran correctly and only the bundled one fell over.

Moving the assignment after the `AXIS` read fixes it, and the three bundled device decks are again
**byte-identical across 18 423 comparable lines**. A patch that is invisible when unused is not a
nicety — it is the only thing that would have caught this, because our own decks never exercised
the `DSET:` path.

## A8's first transient, and what it is honestly evidence of — 2026-10-05 (25)

With `MOVGRP.f` fixed and the anchor in place, the 1 s AZ-5 transient from the sourced 01:22:30
pattern at the sourced 0.4 m/s:

| t, s | 0.01 | 0.05 | 0.10 | 0.20 | 0.30 | 0.50 | 0.70 | 1.00 |
|---|---|---|---|---|---|---|---|---|
| **P/P₀** | 0.99986 | 0.99812 | 0.99412 | 0.98283 | 0.97024 | 0.94784 | 0.92733 | **0.86929** |

Monotone decrease from the first step, and the **anchor is exact**: 40 cm of travel, k = 1.043293,
ρ = −72.2 pcm against the static ramp's −72.2. The null transient on the same build holds power
constant to every printed digit with its anchor at k = 1.044046, and ramp point zero still returns
1.044046 after all five patches — so the whole chain is consistent on the final code.

### The timestep is converged, and that sets the A8 budget

The same 1.0 s at **200 × 5 ms** instead of 100 × 10 ms:

| t, s | 0.10 | 0.20 | 0.30 | 0.50 | 0.70 | 0.90 | 1.00 |
|---|---|---|---|---|---|---|---|
| dt = 10 ms | 0.99412 | 0.98283 | 0.97024 | 0.94784 | 0.92733 | 0.88847 | 0.86929 |
| dt = 5 ms | 0.99364 | 0.98165 | 0.96876 | 0.94720 | 0.92652 | 0.88674 | **0.86760** |
| change | −0.05 % | −0.12 % | −0.15 % | −0.07 % | −0.09 % | −0.19 % | **−0.19 %** |

Worst difference **0.00173 in P/P₀**, which is **4.4 % of the 0.0386 the prompt-lifetime sweep
alone spans** at the same time — the discretisation error is some twenty times below the model's
own parameter uncertainty. So **dt = 10 ms is adequate here**, and a 4 s scenario costs 44 minutes
rather than the 7.4 hours a 1 ms step would.

**Scoped deliberately.** This is a slow monotone ramp of −72 pcm over a second. A prompt excursion
— the 31×-to-64× rise in 6.5 s that INSAG-7 reports — is a different regime and this says nothing
about the step it would need. The convergence statement travels with the transient it was measured
on, which is the same discipline section (20)'s trust region needed.

### Point kinetics from the measured ramp, and the restraint it forces

Six-group point kinetics driven by ρ(t) = ρ(speed · t) from the *measured* static ramp, with λ from
the COMPO, the per-precursor β shape from the COMPO's own `NUSIGF0i/NUSIGF`, and the prompt
lifetime swept rather than derived (`tools/a8_pk.py`):

| t, s | DONJON 3-D | Λ = 0.5 ms | Λ = 1 ms | Λ = 2 ms |
|---|---|---|---|---|
| 0.05 | 0.99812 | 0.99818 | 0.99901 | 0.99948 |
| 0.20 | 0.98283 | 0.98170 | 0.98795 | 0.99294 |
| 0.50 | 0.94784 | 0.94949 | 0.95868 | 0.97108 |
| 1.00 | 0.86929 | 0.88079 | 0.89639 | 0.91940 |

Two methods sharing nothing but the core — 3-D space-time diffusion, and a six-group ODE driven by
static eigenvalues — agree to 0.0009 in P/P₀ at 0.05 s and 0.0271 at 1.0 s.

**And that is where the claim has to stop.** The Λ sweep alone spans **0.0386** at 1.0 s, so the
3-D residual is *inside* it. It is not evidence of a spatial effect, and the temptation to read it
as one is exactly the error that produced the retracted 9.3 % rise. What can be said is the
negative: **in this regime the transient is point-kinetic to within what the prompt lifetime
allows.** Which is what a symmetric whole-core scram ought to be — every rod moves together, so
there is nothing to drive the shape.

That is worth stating plainly because `PROJECT_PLAN` opens by arguing that spatial resolution is
mandatory for this reactor. It is — but not because a *scram* is spatially interesting. It is
mandatory because of the **initial** spatial non-uniformity: INSAG-7's Kv = 5.5 and its "strong
power density deformations", and its statement (p. 69) that a 20 % change in the initial power
density moves the answer between 31× and 64×. The spatial content of the accident is in the state
the transient starts from, not in the rod motion. Our core, on flat burnup, does not have it.

### What A8 has, and the one thing it still needs

Everything the transient consumes is now built, sourced and checked: movable rods verified against
the base map to seven figures, delayed data from the COMPO as a burnup field, a sourced rod speed,
a sourced fuel-failure threshold, a converged timestep, a static anchor on every run, and an
independent point-kinetics cross-check.

What it does not have is the **measured axial flux shape** (double-humped, upper maximum — see the
correction in (24)), and section (24) argued, and (26) confirmed, that the axial shape decides the
sign of the ramp. The axial shape follows the axial burnup and xenon distributions,
and this model holds both uniform within a channel because the generator writes `INST-BVAL CHAN`.
`RESPAR.f:518-531` shows **`INST-BVAL BUND`** accepts a burnup per channel *per bundle* — 1661 × 28
= 46 508 values, bundle-major — and `RESPAR.f:690` adds `AXIAL-PFORM` beside it. The capability is
there and unused; the sourced basis for it is INSAG-7 Figs. II-7 / II-8, already listed as A8's
comparison targets and, being plots, digitisable the way Fig. II-6 was.

So A8's remaining work is not solver work. It is the same thing A6b and A6d ran out of: the
**initial state**, now narrowed from "the burnup placement" to one specific missing axis.

## The axial probe: the ramp's sign follows the axial peak — 2026-10-06 (26)

Section (24) inferred from A6.5 that the AZ-5 ramp's sign is set by the axial flux shape. That claim
has now been tested directly in the device model, not just inferred.

**Machinery.** `U4_AXBURN` gives every bundle a burnup multiplier, normalised to a mean of 1 so each
channel keeps its burnup. It takes `cos:<a>` (a symmetric cosine bump, so a>0 burns the middle
harder), `tilt:<t>` (linear; t>0 burns the top harder) or `file:<path>`. It writes the multipliers
through `INST-BVAL BUND` (bundle-major, `RESPAR.f:518-531`), and the stem gets an `_ax<md5>` suffix.
`U4_PBUND=1` prints `POWER-BUND`; `tools/a8_axial.py` reduces it to the axial shape, with D measured
from the core top in INSAG-7's convention.
**Regression:** if every bundle is given its channel's own burnup, the `BUND` route reproduces `CHAN`
exactly: k 1.044046, peak 3025.1 kW.

**Axial shapes.** On flat burnup the core is a bare cosine, peaking at 1.658 at bundle 14 and
falling to 0.13–0.21 at the ends. A modest shape moves the peak to one end:

| `U4_AXBURN` | k | axial peak | value |
|---|---|---|---|
| none | 1.044046 | bundle 14 (mid) | 1.658 |
| cos:0.5 | 1.030672 | bundle 8 (lower) | 1.454 |
| cos:1 | 1.027057 | bundle 6 | 1.777 |
| cos:2 | 1.028800 | bundle 5 | 2.452 |
| tilt:+0.4 | 1.065369 | bundle 7 (lower) | 2.272 |
| tilt:−0.4 | 1.059310 | bundle 21 (upper, D = 188 cm) | 2.184 |

A *symmetric* flattening sends the field to the bottom rather than flattening it. The core is 7 m
tall, so its first two axial modes are nearly degenerate, and the small asymmetry from the rods
(inserted from the top) and the reflectors decides which end wins. This is the same instability
INSAG-7 attributes to the real core, and it means the initial axial shape must be **sourced, not
chosen**: any reasonable-looking guess lands at one end or the other.

**Static ramps**, ρ = 1 − k₀/k(d) in pcm, using the same rod pattern and the same devices:

| shape | 10 cm | 25 cm | 40 cm | 80 cm |
|---|---|---|---|---|
| flat (24) — mid-peaked | −10.8 | −25.5 | −72.2 | −202.4* |
| tilt:+0.4 — bottom-peaked | +69.5 | +185.0 | +257.0 | **+358.1** |
| cos:1 — bottom-peaked | +53.3 | +170.0 | +253.9 | **+407.5** |
| tilt:−0.4 — top-peaked | −170.1 | −383.9 | −664.7 | **−1407.9** |

\*from the reference ramp at the nearest tabulated depth.

**The sign follows the peak, both ways, and the effect is large:** the same rods inserting the same
distance give anywhere from +400 to −1400 pcm depending only on where the axial flux sits. This
confirms the A6.5 mechanism in the full-core device model: the graphite displacers push water out
of the bottom of the channels, and that is worth more than the absorbers entering at the top
whenever the flux is at the bottom.

**What this does not say.** None of these shapes is the real one. The measured t = 0 field (Fig. II-9;
see the correction in (24)) was double-humped with the **upper** maximum the larger. Our probe says
that, on its own, gives a negative ramp at first, which matches the first-second reactivity drop in
all three INSAG-7 models. Whether this core then turns positive as the rods go deeper and the
lower hump grows is the question the 4/6/7 s curves of Fig. II-9 can answer, and they are the
independent test.

**Next.** Digitise Fig. II-9. Treat its t = 0 curve as the *input*, solving for the axial burnup
multiplier that reproduces it (an inverse problem, reported as such and not as validation), and its
4 / 6 / 7 s curves as the *test*. II-8's twelve measured detector profiles are a cross-check on the
t = 0 shape.

## The measured initial shape, inverted, and the 4–7 s shapes it predicts — 2026-10-06 (27)

**Digitisation.** `tools/digitise_fig_II9.py` takes 37 markers off the native 300 dpi scan of
INSAG-7 Fig. II-9: 8 at 0 s, 10 at 4 s, 10 at 6 s and 9 at 7 s. The axes are calibrated from the
printed ticks (residuals under 1 px). The x zero sits about 7 cm right of the drawn axis, which is
carried as an x uncertainty of ±7 cm. An overlay of the points on the figure was checked by eye and
accepted. Data: `sources/derived/insag7_fig_II9_axial.csv`.

**Inversion (a fit, not a validation).** `tools/a8_axinvert.py` solves for the per-bundle burnup
multiplier that makes the static device-model core reproduce the 0 s curve. The profile is
log g = Σ cₙPₙ, six Legendre modes, renormalised to mean 1 so each channel keeps its burnup.
It is fitted by Levenberg–Marquardt with a finite-difference Jacobian and a 4 % trust region,
at 18 s per static solve.

- **A simple multiplicative fixed point fails here.** A burnup tilt of about ±5 % end to end
  swings the flux from the upper hump to a bottom peak (RMS 0.84 / 0.37 / 0.90 / 0.26 as the step
  halved). This is the axial near-degeneracy of (26) again.
- **Result.** The fit reached RMS 0.020 and max 0.048 over 28 bundles, with k 1.023557. It was
  stopped where further iterations only grew the high modes (0.0214 → 0.0200), i.e. were fitting
  noise. Saved as `sources/derived/insag7_fig_II9_t0_axburn_fit.txt`.
- **The fitted profile is physically ordinary.** Burnup ×1.22 in the middle and ×0.50–0.52 at both
  ends, slightly heavier in the lower half: the cosine-like burnup a long-run core accumulates.
  It is still an *effective* profile, because it lumps axial burnup, xenon, void and rod shading
  into the one knob the model has.

**The test: Fig. II-9's 4 / 6 / 7 s curves, never used in the fit.** From the fitted state, every
CPS rod is advanced by the sourced 40 cm/s × t, and the core is solved statically with no TH
feedback:

| travel | ρ, pcm | axial peak | upper/lower hump | RMS vs 4 s | 6 s | 7 s |
|---|---|---|---|---|---|---|
| 0 | 0 | 1.42 at D 162 | 1.49 | 1.110 | 1.294 | 1.411 |
| 10 | −96.9 | 1.22 at D 188 | 1.07 | | | |
| 25 | −130.5 | 1.43 at D 562 | 0.69 | | | |
| 40 | −140.9 | 1.69 at D 562 | 0.56 | 0.514 | 0.703 | 0.826 |
| 80 | −77.9 | 2.08 at D 588 | 0.41 | 0.233 | 0.401 | 0.529 |
| 160 (= 4 s) | −330.8 | 2.34 at D 612 | 0.31 | **0.163** | 0.182 | 0.305 |
| 240 (= 6 s) | −710.1 | 2.70 at D 612 | 0.19 | 0.331 | **0.172** | **0.152** |
| 280 (= 7 s) | −871.6 | 2.90 at D 612 | 0.14 | 0.452 | 0.281 | 0.179 |

The best-matching travel for each measured time is the one the sourced rod speed predicts: 4 s ↔
160 cm and 6 s ↔ 240 cm. For 7 s, 240 cm (0.152) and 280 cm (0.179) are close, and the 7 s curve
was recorded as rods were being stopped. Measured peaks are 2.49 / 2.67 / 2.80; the model gives
2.34 / 2.70 / 2.90. **The model peak sits about 35 cm (1.5 bundles) deeper** than measured, which is
the main residual. This mirrors the ~7 cm calibration offset in the figure only in direction, so it
is not explained by it.

What this shows: **the displacement of the flux maximum to the core bottom, which is the content of
Fig. II-9's caption, is reproduced by rod motion alone from the measured initial shape.** The flip
is fast. By 25 cm of travel the absorbers entering the top have already moved the peak into the lower
half, because the near-degenerate core needs only a small perturbation to change which end
dominates.

What it does not show:

- **The ramp from this state is negative at every depth.** It is non-monotonic: −141 pcm at 40 cm
  recovers to −78 at 80 cm, so the rods *add* +63 pcm between 40 and 80 cm once the flux sits at the
  bottom, where the displacers are expelling water. But the net never crosses zero in this static,
  feedback-free model.
- So the positive excursion needs what is not yet in it: void feedback, which turns the bottom
  power rise into steam and positive reactivity (A8.3). All three INSAG-7 models also show
  reactivity falling in the first second (p. 119).
- **The comparison is static eigenshapes, not a kinetics run.** Section (25) showed a symmetric
  scram here is point-kinetic within the Λ spread, which supports reading shape off static solves,
  but the 4–7 s window in the real core had feedback acting as well.

**Next.** Put THM feedback in the kinetics loop (A8.3) and run the transient from this fitted state.
The question becomes whether the bottom-shifted power plus the void coefficient turns the
−78 pcm plateau positive, and how this compares to INSAG-7's 3.5× / 9× / 80× model band.

## A8.3: thermal-hydraulic feedback in the transient, and the surge that does not come — 2026-10-07 (28)

Every kinetics step now couples to `THM:`. The order within a step is: `NCR:` (fuel cross sections
from the THM-updated map) → `MACINI:` → `NEWMAC:` → `TRIVAA:` → `KINSOL:` → `FLPOW:` (power from the
kinetics object) → `THM: … TIME t dt`. The feedback is explicit, with one step of lag.

### The initial state is now the 01:23 state, sourced

`U4_TH=acc` takes INSAG-7 p. 64's initial condition:

- **200 MW(th)**;
- **56 000 m³/h** with eight pumps (4.176 m/s mean over 1661 × 22.427 cm²);
- inlet subcooling **3 °C**, placed below `THM:`'s own IF97 saturation.

The 01:23 pressure is not given anywhere in the repository, so [D]'s design pressure is kept. The
subcooling is what decides boiling onset, and it is sourced. With feedback on, the steady state
converges in 14 passes, with no limit cycle: there is hardly any boiling to switch. Peak fuel
temperature is 611 K. Coolant density runs 0.739 → 0.721 g/cm³, i.e. a little steam near the top
only, which is INSAG-7's description. The axial shape still matches Fig. II-9 at t = 0 (rms 0.020),
so the (27) fit carries over without a re-fit.

### Three defects in the transient driver, each found by measurement

| | symptom | cause | fix |
|---|---|---|---|
| memory | — | `THM:` keeps every transient step, ~11 MB each: **77 GB at 7000 steps** on a 110 GB machine | patch 0004, `HISTORY n` |
| tolerance | abort on step 1 | `ERMAXC` is read only by THMTRS; A7's 1e-6 had never been tested | 1e-3 (upstream default); 1e-5 agrees to 1.1e-6 in P/P0 |
| fixed point | abort at t = 0.1–0.35 s | see below | patch 0006, `FLOW-RELAX w` |

**The fixed-point defect.** THMTRS's flow pass is a fixed point on the coolant density: node K's
mass flux and enthalpy use the previous pass's density through 0.5·ρ·HZ/dt. In a boiling node,
dρ/dh ≈ (ρ_l − ρ_g)/h_fg, so the gain of that map grows as **1/dt** and **1/G**. It exceeded one in
channel 1433 (1.33 m/s, the 2nd percentile of flow) at t = 0.345 s. The mass-flux error there jumped
from 2.4e-4 to 0.10 and oscillated for 30 passes. That is deterministic, and no tolerance can fix it.

Patch 0006 under-relaxes the carried density, which changes the path to the fixed point but not
the fixed point itself. A residue of isolated channels still ends on the discrete boiling-onset
switch: up to 2 per step, error 3.9 % / 7.7 % / 19.6 % at 10 / 5 / 2.5 ms, i.e. ∝ 1/dt. Patch 0005
accepts and counts them. They do not move the answer: ω = 0.5 and ω = 0.25 agree to 2e-6, and the
timestep converges despite them. All three patches are opt-in, and `channel_mphy`'s listing is
unchanged without them.

### Verification

- **Null transient** with feedback: P/P0 = 1.000003 after 0.1 s; the final static k matches to 1e-6.
- **Timestep**, P/P0 at 1 s: 0.665483 at 2.5 ms, 0.665695 at 5 ms (+0.032 %), 0.667171 at 10 ms
  (+0.254 %). **5 ms is converged to ~0.03 %**, and the 7 s run uses it.
- **Reproducibility:** the 7 s run's value at 1 s is bit-identical to the separate 1 s run.
- **Cost:** 17 s/step (KINSOL 6.6, NCR 4.1, THM 2.9, FLPOW 2.7). The 7 s run took 6 h 50 min at
  1.6 GB.

### The result: AZ-5 from the fitted 01:23 state is a monotonic shutdown

| t, s | 0.5 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| P/P0, feedback | 0.790 | 0.666 | 0.581 | 0.462 | 0.315 | 0.214 | 0.151 | **0.111** |
| P/P0, TH frozen | 0.790 | 0.665 | 0.581 | 0.462 | 0.314 | 0.214 | 0.151 | 0.111 |
| feedback effect | +0.02 % | +0.07 % | +0.11 % | +0.11 % | +0.17 % | +0.25 % | +0.33 % | +0.41 % |

The feedback is small and positive. The fuel cools 611 → 589 K (Doppler, positive), while the steam
collapses as power falls (coolant density 0.721 → 0.734 g/cm³, which is negative in this reactor).
Over 7 s these nearly cancel.

**Compared with INSAG-7's three reconstructions (pp. 119–121), not tuned to them:**

1. *"All three models indicate a drop in reactivity during the first one second."* **Reproduced.**
2. *"Then, the neutron field is redistributed, the maximum shifts to the bottom of the core."*
   **Reproduced.** The shapes against Fig. II-9:

   | model t | peak | rms vs 4 s | 6 s | 7 s |
   |---|---|---|---|---|
   | 4 s | 2.10 at D 588 | **0.210** | 0.341 | 0.476 |
   | 6 s | 2.35 at D 612 | 0.192 | **0.198** | 0.322 |
   | 7 s | 2.49 at D 612 | 0.246 | 0.169 | **0.258** |

   Measured peaks are 2.49 / 2.67 / 2.80. The transient's shape *lags* the measured one by about
   1 s and peaks about 15 % lower. (27)'s static eigenshapes instead ran slightly ahead and deep,
   which is the expected effect of the delayed neutrons holding the field back.
3. *"…and the reactivity and the integrated power level start to increase."* **Not reproduced.**
   The surge in the models is 3.5× / 9× / 80×. Here power falls to 0.11 by 7 s.

So the disagreement is specific: the redistribution happens, but the bottom of this core never
gains enough reactivity to turn the total around. The static ramp from this state (27) gains
**+63 pcm between 40 and 80 cm** of travel and is negative everywhere else. With power falling,
the positive void coefficient cannot help: less steam is negative reactivity.

**Candidates, in the order to test them:**

1. **The CPS cross sections' water-to-graphite worth.** A6.4b measured a one-signed bias in the
   rod cell (it perturbs its neighbours' spectrum by ±3 %). The positive part of the scram is
   exactly the bottom water column → graphite swap. The rod geometry itself checks against the
   design (5 m absorber, 1.25 m water, 4.5 m displacer, 1.25 m water below).
2. **Bracket B.** Every A8 run uses the DRAGON void coefficient. The OpenMC-corrected bracket is
   several times more positive (~0.6 $ vs ~2.7 $). That matters only once power rises, but it
   changes how much bottom reactivity is needed to start a rise.
3. **The pre-AZ-5 boundary conditions.** The 36 s pump coastdown from 01:23:04, which reduces flow
   and raises the inlet temperature, is not modelled; the inlet is held at the 01:23 state.
4. **The rod pattern at 01:23:40.** The sourced pattern is the 01:22:30 one. The number of RR rods
   fully withdrawn sets how many displacers carry a bottom water column.

## AZ-5 did not drive the USP rods, and with that fixed the scram is positive — 2026-10-07 (29)

### A modelling error, found in the source rather than the code

Every A8 run so far moved all three device groups at AZ-5, including the 21 bottom-entry USP
(shortened) absorbers. In 1986 they were not driven by the EPS signal. INSAG-7 p. 46 lists, among
the proposals made **before** the accident and implemented only after it, "to insert shortened
absorber rods into the core in response to an emergency protection signal". The deck comment that
called `U4_MOVGRP=123` "the only physical case" was wrong. `U4_MOVGRP=12` is the 1986 AZ-5. The
default stays 123 so that earlier results reproduce, and the comment now says which is which.

This matters far more than its 21 rods suggest. The USP absorbers enter from below, which is
exactly where the displacers expel water and where the flux moves during the scram. They were
cancelling the positive scram at its source.

**Static ramp from the fitted state** (`A8_USP=0 tools/a8_ramp.py`, same deck family as (27)),
ρ = 1 − k₀/k(d) in pcm:

| travel, cm | 10 | 25 | 40 | 80 | 160 (4 s) | 240 (6 s) | 280 (7 s) |
|---|---|---|---|---|---|---|---|
| USP driven, (27) | −96.9 | −130.5 | −140.9 | −77.9 | −330.8 | −710.1 | −871.6 |
| **USP held** | −89.9 | −106.5 | −74.3 | **+152.2** | **+281.0** | **+141.3** | +15.5 |

So the inserted reactivity is negative for the first ~50 cm (about 1.2 s) and positive from there
to about 7 s, peaking at +281 pcm = **+0.53 $** (β = 0.00529 at 10.9 MWd/kg) near 160 cm. That
matches the one quantitative statement INSAG-7 makes about it (p. 39, citing Ref. [20]): "In the
case of a non-regulation ORM of 7 control rods, during the first eight seconds after triggering of
EPS-5 the inserted reactivity is positive." The USP rods alone were worth about −610 pcm at 160 cm.
The static shapes are unchanged in kind: the peak moves to D 612 cm by 160 cm of travel.

### The coupled 7 s transient

Same deck as (28) except that group 3 (USP) does not move: 5 ms with feedback (local), 10 ms with
feedback and 10 ms frozen-TH (spark).

| t, s | 0.5 | 1 | 1.5 | 2 | 2.5 | 3 | 3.5 | 4 | 4.5 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **P/P0, 5 ms, feedback** | 0.805 | 0.716 | 0.739 | 0.870 | 1.110 | 1.434 | 1.765 | 1.955 | **1.975** | 1.946 | 1.603 | **1.145** |
| P/P0, 10 ms, feedback | 0.807 | 0.717 | 0.738 | 0.867 | 1.105 | 1.426 | 1.754 | 1.949 | 1.974 | 1.944 | 1.600 | 1.145 |
| P/P0, 10 ms, TH frozen | 0.807 | 0.717 | 0.737 | 0.867 | 1.110 | 1.447 | 1.813 | 2.070 | 2.175 | 2.167 | 1.895 | 1.383 |
| (28): USP driven, feedback | 0.790 | 0.666 | | 0.581 | | 0.462 | | 0.315 | | 0.214 | 0.151 | 0.111 |

The 5 ms run took 6 h 53 min at 1.6 GB, with at most 2 cycling channels per step (worst
accepted 8.1e-2). Fuel peaks at 629.6 K and the minimum coolant density falls to 0.682 g/cm³.

- **Timestep:** 5 ms and 10 ms agree to 0.7 % (worst at 3.5 s; 0.007 % at 7 s) over the whole 7 s, so 10 ms suffices for this
  transient.
- **Power rises.** From a minimum of 0.714 at about 1.1 s it climbs to **1.976× at 4.43 s** and then falls as the
  absorbers take over. The minimum, the turn and the timing match the shape of the reconstructions.
  The amplitude does not: INSAG-7's three models give 3.5× / 9× / 80× (pp. 119–121).
- **Axial shapes against Fig. II-9 (10 ms run):**

  | model t | peak | rms vs 4 s | 6 s | 7 s |
  |---|---|---|---|---|
  | 4 s | 2.50 at D 612 | **0.227** | 0.146 | 0.242 |
  | 6 s | 2.74 at D 612 | 0.348 | **0.184** | 0.141 |
  | 7 s | 2.86 at D 612 | 0.424 | 0.253 | **0.157** |

  Measured peaks are 2.49 / 2.67 / 2.80. With the USP rods driven they were 2.10 / 2.35 / 2.49,
  15 % low. Now they are within 3 %. The 4 s shape matches the measured 6 s curve best, so the
  redistribution now runs slightly ahead of the measurement where before it lagged by about 1 s.

### The feedback is negative, and INSAG-7 says it should be positive

The frozen-TH control isolates the rods: on its own the ramp drives power to **2.18×** at 4.6 s.
Feedback *lowers* that: −1.5 % at 3 s, −5.8 % at 4 s, −10.3 % at 5 s, −17.2 % at 7 s. In (28)
the feedback was +0.4 %, but there power was falling; now that power rises, the net feedback is
seen to be negative.

A static measurement says the same thing without any kinetics. The accident-state steady solve
(fitted axial burnup, devices, prop flows) at 200 MW and 300 MW, flow and inlet held
(`U4_PACC`, new):

| | k at 200 MW | k at 300 MW | Δρ per +100 MW |
|---|---|---|---|
| full feedback | 1.027370 | 1.027338 | **−3.0 pcm** |
| density pinned (`U4_VOIDFB=0`, Doppler only) | 1.027679 | 1.027473 | −19.5 pcm |
| void part (difference) | | | **+16.5 pcm** |

The model's power coefficient in the 01:23 state is **−0.57 × 10⁻⁴ β/MW**: small and negative.
INSAG-7 p. 3: "At the time of the accident, the void and power coefficients of reactivity were
both positive." p. 36 gives the measured fast power coefficient rising to **+0.6 × 10⁻⁴ β/MW** as
the void effect rose to +5 β, valid above 50 % power. This is the disagreement that now stands
between the model and the surge. The rods are no longer the problem: they reproduce INSAG-7's
statement about the first 8 s and the Fig. II-9 shapes to 3 %.

### What sets the void side, in the order to test

1. **The void worth of the cross sections (bracket B).** The production COMPO (bracket A) gives
   +1.95 $ for full voiding of 10.9 MWd/kg fuel; B gives +2.72 $; INSAG-7 p. 3 gives +4–5 β for
   the steady-state refuelling regime and p. 36 gives up to +4.9 β measured at Chernobyl Unit 1. Even B is low
   against that. The void part of the power coefficient would need to grow by about 20 pcm per
   100 MW (×2.2) just to make the total cross zero.
2. **The fitted axial burnup profile.** It puts the core ends at ×0.50–0.52 of the channel burnup,
   about 5.5 MWd/kg, because burnup was the only axial knob the inversion had ((27)). The void
   coefficient falls steeply at low burnup (+0.91 $ at 5 MWd/kg against +1.95 $ at 10.9), and
   the bottom is exactly where the scram concentrates the flux. If the real bottom shape came partly
   from xenon rather than burnup, the model's bottom void worth is understated. The inversion is
   not unique, and this is the axis on which it is not.
3. **The pre-AZ-5 TH state.** INSAG-7 p. 8: the inlet "may not have been subcooled at all", and
   the 36 s coastdown from 01:23:04 cut the flow before AZ-5. Both move boiling onset down into
   the region where the flux is going.

The CPS water/graphite worth (the old candidate 1) has dropped out: the A6.4 bias is 7–10 % on
the displacer, and the rods now match the sourced statement without it.

## Is the TH feedback realistic? Where the steam is, and how much it is worth — 2026-10-07 (30)

(29) found the net TH feedback negative where INSAG-7 says positive. Before changing cross sections,
this section checks that THM puts the steam in the right place, and measures the core's void worth.

**Machinery.** `U4_THDUMP=1` (stem `_thd`, default decks byte-identical) prints every channel's
converged axial EPSILON, XFL, DENSITY, POWER and ENTHALPY. `tools/a8_thcheck.py` reduces them to
per-bundle void, boiling fraction and onset height, and differences two states. `U4_DCA` is now
keyed into the A7 stem under `U4_VOIDFB=0`; before, two pinned densities wrote the same deck name.

**The 01:23 state matches the source and the energy balance.** At 200 MW, 56 000 m³/h and 3 °C
subcooling, the coolant gains 17.4 kJ/kg across the core and the subcooling takes 16.2 kJ/kg
(IAPWS-IF97 at 7.38 MPa), so an average channel saturates only after ~93 % of its heat. THM agrees:
the sum of POWER is 199.52 MW; boiling begins at bundle 25–26 (of 28, from the bottom) in every
channel; void exists only in the top 3–4 bundles, 1.4 % in the top plane. INSAG-7 p. 64: "a low level
of subcooling ... (3°C) and a correspondingly low steam quality, which was observed only in the
upper part of the core". The axial power peaks at bundle 22 (D 162 cm), Fig. II-9's upper hump.

**Nominal sanity check** (3200 MW, same axial state): boiling onset median bundle 12, upper-half void
56 %, exit flow quality mean 17.6 %, max 28.7 %. Malko (KURRI-KR-79) gives boiling from ~2.5 m above
the inlet and 14.5 wt% at the outlet at nominal; A7a gave 16.5 % against [D]'s 19.6 % for one channel.

**Where added power puts the steam (static, axial shape held):**

| | 200 MW | 300 MW |
|---|---|---|
| boiling onset, median / 10 % / 90 % | 26 / 25 / 26 | 19 / 18 / 20 |
| mean void, lower half | 0 | **0** |
| mean void, upper half | 0.23 % | 4.05 % |

All the new steam lands in the upper half. INSAG-7 p. 64 says a small power increase "could result in
a much higher increase in the volumetric steam quality in the lower part of the core than in the
upper part". With the axial shape held, the model cannot do that: the bottom stays below saturation.
In the transient the shape moves to the bottom, so the decisive check is a void dump *during* the
transient at 4–6 s, not yet done.

**One TH simplification is relevant.** Our decks run THM with `IPRES=0`, constant pressure along the
channel. Malko gives 8.2 MPa at the inlet falling to ~7 MPa at the outlet. Malko's own account of the
mechanism is pressure-driven: "A decrease of a pressure or an increase of a temperature of water at
the inlet to the core could cause a local boiling of water in the lower part of the core", which is
what the pump coastdown does. Malko also attributes the 3 °C figure to the pumps' "cavitation and
boiling surplus", so where along the loop the 3 °C applies is itself uncertain.

**The core's void worth is half the sourced value.** The 01:23 state with every fuel channel's
coolant density pinned (`U4_VOIDFB=0`, Doppler live):

| pinned D-COOL | k |
|---|---|
| 0.74 g/cm³ (liquid) | 1.027292 |
| 0.02 g/cm³ (steam) | 1.040571 |
| **void worth** | **+1242 pcm = +2.35 β** |

INSAG-7 p. 83 (Annex I, quoting Ref. [46] on the causes) gives "the large void reactivity effect
(5βeff)"; p. 36 gives up to +4.9 β measured at Chernobyl Unit 1; Malko "up to 5 βeff". The core
value (2.35 β) is a little above the cell-level bracket A (1.95 $ at 10.9 MWd/kg) because of the
fitted burnup and the rod pattern. Bracket B would scale the cell value by ~1.39, which lands near
3.3 β: closer, still short. Unit 4 had a single additional absorber (INSAG-7 pp. 67, 107), so its
void effect should sit at the top of the sourced range.

**Burnup sources.** No further spatial or axial burnup data was found: [PAV]'s 8-group histogram is
the only published Unit 4 burnup information located (web search 2026-10-07, KURRI-KR-79 papers
included), and the Behrens and Ignalina reports on disk carry no axial profile. The fitted axial
profile (ends ×0.50–0.52) is a typical long-run RBMK shape, but the inversion lumps xenon into it.

**Next, in order.**
1. **Void cross sections (bracket B in the core).** Build a corrected copy of the fuel COMPO whose
   coolant-density dependence carries the OpenMC void worth (`void_bracket.corrections`), keyed by
   its own stem, so NCR interpolates it in both the steady and the transient paths. Gate: the pinned
   0.74/0.02 pair reproduces the bracket's cell ratio in the core.
2. **Transient void dump** at 4–6 s, to see whether the steam reaches the lower half.
3. **Separate xenon from burnup in the axial inversion**, using the sourced power history and the
   existing per-channel xenon solver extended per bundle, since bottom burnup sets bottom void worth.
4. **`IPRES=1` and the coastdown**, the pressure route to bottom boiling.

## Bracket B in the core, where the steam goes in the transient, and xenon separated from burnup — 2026-10-08 (31)

**Bracket B is built and gated.** `tools/compo_voidB.py` writes `_ACompoVB`, a copy of the fuel
MULTICOMPO in which every one of the 1296 points below 0.72 g/cm³ carries bracket B's void worth.
At each point it rebuilds the two-group k∞ exactly as `NCR: MACRO` does: the fresh nominal point
gives 1.313957 against DRAGON's 1.313968. It then adds the thermal absorption to `*MAC*RES` (NTOT0,
NG, STRD) that moves k∞ by `void_bracket.corrections` B − A; the re-read worst miss is 0.014 pcm.
`U4_VOIDB=1` stages it, keyed on its md5 (`_vB65c86e`). The correction is zero at and above 0.72,
which is where the bracket is defined from.

| 01:23 state | A | B |
|---|---|---|
| core void worth, 0.74 → 0.02 pinned | +1242 pcm = 2.35 β | **+1702 pcm = 3.22 β** |
| power coefficient, 200 → 300 MW | −3.0 pcm / 100 MW | **+2.7 pcm / 100 MW ≈ +0.5 × 10⁻⁴ β/MW** |

B makes the static power coefficient positive, close to INSAG-7 p. 36's +0.6 × 10⁻⁴ β/MW, though
the void worth is still short of the sourced ~5 β.

**In the transient, B changes nothing:** at most 0.009 % in P/P0 over 7 s (10 ms, USP held, feedback).
`U4_KINVOID=1` dumps the fuel map's D-COOL at 1–7 s, and `tools/a8_voidz.py` shows why:

| t, s | P/P0 | lower-half power share | void, lower half | void, upper half |
|---|---|---|---|---|
| 1 | 0.717 | 0.608 | 0.0000 | 0.0025 |
| 3 | 1.426 | 0.849 | 0.0000 | 0.0007 |
| 5 | 1.943 | 0.914 | 0.0000 | 0.0052 |
| 7 | 1.145 | 0.947 | 0.0010 | 0.0241 |

With 89–95 % of the power in the lower half from 4 s on, the lower half never boils: the boiling
front reaches bundles 9–11 (D ≈ 450 cm) only by 7 s. The steam that forms sits in the upper half,
where the power share has collapsed to 0.05–2 % per bundle, so it carries almost no reactivity
weight. With 3 °C of subcooling (16.2 kJ/kg) and the fuel's heat-transfer lag, bottom boiling does
not arrive within the window. **The limit on the surge in this model is thermal-hydraulic, not the
void cross sections.**

**Xenon separated from burnup.** `U4_XEAX=1` gives each bundle its own xenon. Its frozen power ratio
is the channel's radial share times the *measured* t = 0 axial shape, so the field does not depend
on the burnup it is separated from. Two defects were found on the way:

- **`a6b_xenon.xenon_at_0123` started every channel at the core-average equilibrium**, whatever its
  power ratio, so a 0.1× bundle carried full-average iodine into the run-down: 0.944 × Xe_eq at 01:23
  instead of 0.227. Fixed by starting each channel at its own ratio's equilibrium; scale 1 is
  unchanged at 1.039. **The per-channel xenon fields of section (21) were built with the defect** and
  understated the spread, so their flattening numbers (4731 kW, 2.460) need re-measuring before
  they are quoted again.
- **DONJON's `ECHO` overflowed a 129-byte buffer once a deck passed 9999 lines** (`redget_c.c:404`,
  `%04d` line numbers), aborting under `_FORTIFY_SOURCE`. Patch 0007 widens it and terminates at the
  real line end. The `channel_mphy` regression is unchanged (2 597 833 lines), and binaries match
  on both machines.

Flat burnup with xenon alone gives a single cosine peaked at bundle 13, not the upper hump. The
LM refit with the xenon field converges at **rms 0.0201**, as good as the burnup-only fit
(`sources/derived/insag7_fig_II9_t0_axburn_fit_xe.txt`), and the burnup profile hardly moves:

| bundle (bottom up) | 1 | 2 | 3 | 4 | 14 (peak) | 28 |
|---|---|---|---|---|---|---|
| burnup only (27) | 0.517 | 0.691 | 0.832 | 0.934 | 1.222 | 0.502 |
| with xenon | 0.538 | 0.721 | 0.863 | 0.962 | 1.220 | 0.511 |

So the depleted core bottom is not a xenon artefact of the inversion, and step 3 does not raise
the bottom void worth materially.

**Step 4 started, and the first attempt failed.** The same transient with 1 °C inlet subcooling
(`U4_SUBC=1.0`, B, a sensitivity rather than a sourced state) aborted at 2.01 s: THMTRS reported a
heat flux of 1.39 × 10⁷ W/m² against a CHF of 1.8 × 10⁶, then `THMPH: CONVERGENCE FAILURE`. A heat
flux that large is impossible at this core power, so this is a single-channel numerical failure,
not physics, and it needs a diagnosis before the subcooling sensitivity means anything. P/P0 at
2 s was 0.744, against 0.867 at 3 °C.

## The 1 °C abort was a NaN; fixed, less subcooling lowers the surge — 2026-10-08 (32)

**The abort is diagnosed and fixed (patch 0008).** Two instrumented local runs of the (31) deck
(`U4_SUBC=1.0`, bracket B, 10 ms) traced it to one place.

- It starts in the top two nodes (K = 29–30) of a few low-flow peripheral channels (fuel-map
  columns 52–53). There the coolant is just saturated (quality ≈ 0.8 %), linear power has collapsed
  to 30–40 W/m and the mass flux is ≈ 400 kg/m²s.
- THMTRS builds the mass flux from continuity with a fixed inlet flow, so a node density change
  moves it by HZ/(2·DTIME) = 12.5 (kg/m²s) per kg/m³. When the boiling-onset switch K0 removes a
  node's void in one pass, the flux at the outlet reverses: the instrumented run read
  **G = −117.7 kg/m²s**.
- THMH2O then evaluates Dittus–Boelter on the signed Reynolds number (REL = −15 182), so
  `REL**0.8` is NaN, and `TWAL=MAX(273.15,NaN)` returns **273.15 K**. A 273 K clad against 568 K
  fuel gives the 1.39 × 10⁷ W/m² heat flux. The single-phase pass hits the same NaN, so the wall
  stays there, the node enthalpy runs away, and THMPH is finally handed **4.0 kJ/kg** (water at
  1 °C), where its Newton iteration fails.

Patch 0008 evaluates THMH2O's correlations at |G|, which is identical to upstream whenever G > 0.
The `channel_mphy` regression is unchanged (2 597 833 lines). No 3 °C transient ever reached this
path: a NaN wall always exceeds CHF and warns, and none of them warned. So no earlier result moves.
**Limitation:** the momentary reversal is itself an artefact of the fixed-inlet continuity solve,
and the energy equation still upwinds from below. The patch stops it crashing the run; it does not
make reversed flow physical. These nodes run at 30–40 W/m, against a core average of ≈ 0.7 kW/m
at 150 MW (150 MW / (1661 × 18 pins × 7 m)).

**The 1 °C transient now runs to 7 s with no CHF warning (13 532 s, 1.6 GB RSS), and the surge is
smaller, not larger.**

| t (s) | P/P0, 3 °C (B) | P/P0, 1 °C (B) | ratio | lower-half void 3 °C / 1 °C | upper-half void 3 °C / 1 °C |
|---|---|---|---|---|---|
| 1 | 0.717 | 0.674 | 0.94 | 0.0000 / 0.0044 | 0.0025 / 0.0740 |
| 2 | 0.867 | 0.744 | 0.86 | 0.0000 / 0.0046 | 0.0013 / 0.0702 |
| 3 | 1.426 | 1.077 | 0.75 | 0.0000 / 0.0062 | 0.0007 / 0.0687 |
| 4 | 1.949 | 1.324 | 0.68 | 0.0000 / 0.0113 | 0.0011 / 0.0732 |
| 5 | 1.943 | 1.299 | 0.67 | 0.0000 / 0.0184 | 0.0052 / 0.0825 |
| 6 | 1.600 | 1.079 | 0.67 | 0.0004 / 0.0245 | 0.0151 / 0.0914 |
| 7 | 1.145 | 0.783 | 0.68 | 0.0010 / 0.0276 | 0.0241 / 0.0962 |

The 1 °C peak is 1.326 at 4.35 s, against 1.976 at 4.43 s at 3 °C. At 1 °C the lower half does
boil, reaching 2.8 % by 7 s, yet power falls from 4.35 s onward. So more lower-core steam does not,
in this model, produce the INSAG-7 surge. The ratio is already 0.94 at 1 s, before the rods reach
the bottom.

**Corrected 2026-10-09: it is the initial state, not the feedback.** I first read the early gap as
void collapse during the power dip. The frozen-TH twin (`U4_KINFB=0`, same 1 °C steady state)
says otherwise:

| t (s) | 3 °C frozen | 3 °C fb | fb/frozen | 1 °C frozen | 1 °C fb | fb/frozen | frozen 1 °C / 3 °C |
|---|---|---|---|---|---|---|---|
| 1 | 0.717 | 0.717 | 1.00 | 0.674 | 0.674 | 1.00 | 0.94 |
| 3 | 1.447 | 1.426 | 0.99 | 1.080 | 1.077 | 1.00 | 0.75 |
| 4.5 | 2.175 | 1.974 | 0.91 | 1.329 | 1.324 | 1.00 | 0.61 |
| 7 | 1.383 | 1.145 | 0.83 | 0.784 | 0.783 | 1.00 | 0.57 |

At 1 °C the net TH feedback during the transient is nil (fb/frozen 0.995–1.004). At 3 °C it is
−17 % by 7 s. The whole 1 °C reduction comes from the different starting state: frozen 1 °C peaks
at 1.332 at 4.23 s, against 2.176 at 4.57 s. The likely mechanism is the t = 0 axial shape (more
upper-half steam pulls the flux up, which weakens the bottom-tip positive scram); it is being
checked against the static t = 0 shapes. The 1 °C frozen run took 4611 s and 1.4 GB RSS.

**Not yet separated:** how much of the 0.68 is the different initial state, and how much is
feedback. The 1 °C core has a different t = 0 flux shape and rod-ramp worth, and the burnup
inversion was fitted to the 3 °C state, so its starting axial shape no longer matches Fig. II-9.
This is a sensitivity, not a better estimate. Next: the local void coefficient in the low-burnup
bottom bundles, which carry the lower-half steam.

## Starting state, not feedback; flow; where steam is worth anything — 2026-10-09 (33)

All runs local (spark2), sequential.

**1. At 1 °C the transient feedback is nil; the starting state does it all.** This is the correction
already folded into (32). Frozen-TH at 1 °C peaks at 1.332 (4.23 s) against 2.176 (4.57 s) at
3 °C, and fb/frozen stays within 0.995–1.004 throughout. The static t = 0 shapes, below, show the
mechanism and how small a shape change it takes.

**2. Void worth by height** (`tools/a8_zonevoid.py`, new). The tool exports the converged fuel map
(`FMAPX := FMAP`) and lowers D-COOL by 0.1 g/cm³ in one 4-bundle zone at a time. It re-imports
each map into the same converged deck and runs one NCR:/MACINI:/NEWMAC:/TRIVAA:/FLUD: pass. The
re-imported unedited map reproduces FINAL keff to 0.00 pcm in all five states. Δρ in pcm per
0.1 g/cm³, zones bottom (z1) to top:

| state | z1–4 | z5–8 | z9–12 | z13–16 | z17–20 | z21–24 | z25–28 | all | Σ zones |
|---|---|---|---|---|---|---|---|---|---|
| 3 °C, B | +5.7 | +28.9 | +37.1 | +44.0 | +59.7 | +50.9 | +8.1 | +229.3 | +234.4 |
| 1 °C, B | +5.1 | +26.2 | +35.2 | +44.5 | +61.6 | +50.3 | +5.6 | +224.9 | +228.5 |
| 3 °C, A | +2.9 | +22.2 | +29.9 | +36.1 | +47.2 | +36.7 | +1.7 | +174.4 | +176.6 |
| 3 °C, B, Q×0.85 | +5.7 | +28.7 | +36.9 | +44.0 | +59.8 | +51.6 | +8.0 | +229.8 | +234.7 |
| 3 °C, B, Q×0.90 | +5.7 | +28.8 | +37.0 | +44.0 | +59.7 | +51.2 | +8.1 | +229.7 | +234.7 |

Every zone is positive and the zones are near-additive (within 2 %). Divided by Σφ² over the zone
(t = 0 shape), the local worth is 3.4 at the bottom against 11.4 in z13–16 for B, and 1.7 against
9.4 for A. So per unit importance, the bottom zone is worth a third (B) to a fifth (A) of the
mid-core. **Caveat:** the top zone is just as low (2.3 / 0.5), despite its high burnup. A large part
of the end-zone deficit is therefore leakage next to the axial reflector, not the bottom's low
burnup; this test cannot separate the two. Either way, the result for the accident is the same:
where the transient moves the power, steam is worth least. That is consistent with (31)/(32), where
lower-half boiling never produced a surge.

**t = 0 axial shapes** (pass-1 POWER-BUND, rms against Fig. II-9 t = 0):

| state | rms | bottom 3 bundles | lower-half power share |
|---|---|---|---|
| 3 °C (A or B) | 0.0306 | 0.435 0.593 0.715 | 0.421 |
| 1 °C, B | 0.0347 | 0.411 0.561 0.677 | 0.407 |
| Q×0.85 | 0.0296 | 0.433 0.591 0.713 | 0.420 |
| Q×0.90 | 0.0301 | 0.434 0.593 0.714 | 0.421 |

At 1 °C the shape moves 1.4 points of power share upward. That is enough to cut the frozen-TH peak
from 2.18 to 1.33: the scram's positive tip depends steeply on the initial bottom flux, as in (26)
(the core is axially near-degenerate). It is the same sensitivity INSAG-7 p. 69 states for its own
answer (31× to 64× for ±20 % initial power density). The burnup inversion was fitted to the 3 °C
state, so the 1 °C result is a sensitivity on a mis-shaped start, not a better estimate. A refit at
1 °C would restore the measured t = 0 shape.

**3. Coastdown and pressure, from the sources.**
- **Flow.** INSAG-7 p. 64 gives 56 000 m³/h at 01:23, before the test. Sec. 1-4.6.2 says the flow
  had fallen 10–15 % by 01:23:39. `U4_QFRAC` (keyed `q…` in the stem; the default decks are
  byte-identical, static and kinetic both checked) runs that band. Full 7 s transients at 3 °C, B,
  10 ms, no CHF warnings:

| Q | peak P/P0 (t) | P/P0 at 7 s | lower-half void at 7 s | wall time |
|---|---|---|---|---|
| 1.00 | 1.976 (4.43 s) | 1.145 | 0.0010 | — |
| 0.90 | 1.955 (4.42 s) | 1.135 | — | 20 993 s |
| 0.85 | 1.926 (4.41 s) | 1.120 | 0.0041 | 13 570 s |

  Less flow means slightly less power: −2.5 % at Q×0.85. The t = 0 shape barely moves (rms 0.0296)
  and the zone worths do not move at all. The coastdown during the 7 s (≈0.3–0.4 %/s, to the pump
  trips at 01:23:46 = t 6 s) is smaller still, so no in-transient flow patch was written.
- **Pressure.** INSAG-7 (Commission note to the USSR account, p. 60): the drum pressure was
  *rising* at ≈6 kPa/s from 01:23:04, and it rose sharply only at 01:23:47 (after t = 7 s). Malko
  gives an 8.2 MPa inlet against ≈7 MPa outlet. With IPRES=0 the whole channel sits at the outlet
  pressure, so the bottom already has the least local subcooling a depressurisation could produce:
  3 °C against ≈14 °C with the real inlet pressure. IPRES=1 could only reduce bottom boiling.
  THMTRS also freezes node pressures at their steady values (PREST = PREST0), so a transient
  depressurisation would need a patch. It is not written, because the sourced direction is the
  other way.

**What this leaves.** Bracket B, subcooling, flow and pressure all move the surge by a few percent
or reduce it. None of them reaches INSAG's 3.5–80×. The one lever measured to move the answer by a
large factor is the initial axial shape, and that is fixed by the measured Fig. II-9 t = 0 through
the burnup inversion. The open questions are now the 01:23:40 initial state beyond its axial shape
(the radial shape and the rod pattern at AZ-5), and the CPS-channel water/graphite worth that the
displacers act on.

## Where A8 stands, and the gaps in order — 2026-10-09 (34)

**Reproduced.**
- The 01:23 steady state: steam only in the top bundles (INSAG-7 p. 64).
- AZ-5 with the USP rods held: a positive scram over the first metre (+281 pcm, INSAG-7 p. 39).
- The first-second dip to 0.71.
- The flux shift to the core bottom: Fig. II-9 peaks 2.49/2.74/2.86 against 2.49/2.67/2.80.
- Timestep convergence to 0.7 %. THM patches 0001–0008, each with a regression.

**Not reproduced: the surge.** The peak is ≈ 2× at 4.4 s against INSAG's 3.5–80×. None of the
tested levers moves it by more than a few percent upward (sections 29–33):

| lever | effect on the peak |
|---|---|
| bracket B | ≤ 0.01 % |
| subcooling 3 → 1 °C | 0.67×, via the starting shape |
| flow × 0.85 | −2.5 % |
| depressurisation | not sourced; IPRES=0 already bounds it |
| TH feedback at 3 °C | net −17 % |

Two findings explain it:
- Steam is worth least where the power goes: the end zones are worth 1/3–1/5 of mid-core per φ².
- The answer is hypersensitive to the initial axial shape: 1.4 points of lower-half power share
  cut the peak by 40 %, as INSAG-7 p. 69 says of its own calculation.

**Gaps, in order.**
1. **The 01:23:40 initial state beyond its axial shape.** The radial shape and its coupling to
   the axial one: the inversion fits only the core-average axial profile. Also the rod pattern at
   AZ-5 rather than at 01:22:30.
2. **The CPS-channel water/graphite worth** that the displacers act on, never independently
   checked.
3. **The void worth** is 2.35–3.22 β against ≈ 5 β sourced; the lattice-level reason is owed.

**Housekeeping.**
- The flow reversal in THMTRS is an artefact (0008 only stops the crash).
- The inversion is tied to the 3 °C full-flow state.
- spark still runs the pre-0008 binary.
- The section (21) per-channel xenon numbers need re-measuring before they are quoted.

## Gap 2 closed: CPS worths corrected to OpenMC, and the surge appears — 2026-10-10 (35)

Overnight, local (spark2), sequential.

**Gap 1, rod pattern at AZ-5: already sourced.** INSAG-7 p. 65 gives the automatic-regulator
positions last recorded at 01:22:37 as 1.4, 1.6 and 0.2 m for AR 1/2/3. Our channel map has
exactly those (four rods each at 140, 160 and 20 cm). From 01:19:57 to 01:23:30 the "one
overcompensation upwards" signal stopped the AR rods moving into the core. So the 01:22:30
pattern is the AZ-5 pattern to the resolution the sources give, and there is nothing to change.

**Gap 2: the CPS-channel worths were biased against the positive scram from both sides.** These
are measurements already on file, never acted on (`openmc/cps_verify.py table` and `a64`),
3 × 3 supercell:

| | absorber, ABS − WAT | displacer, DSP − WAT |
|---|---|---|
| OpenMC, 10 MWd/kg, dca 0.72 | −8955 | +3964 |
| DRAGON production, same state | −10 454 (17 % too strong) | +3553 (10 % too weak) |
| A64V (DONJON core-equivalent), 10.9 MWd/kg | −10 896 | +3350 |

`tools/compo_cpsB.py` (new) rebuilds mixture 5 of the ABS and DSP CPS COMPOs as
Σ_WAT + f (Σ_T − Σ_WAT), record by record, at all 18 points. f is solved by secant iteration on
a one-state A64V deck, so that the core-equivalent supercell carries
W_DRAGON(10.9) × W_OpenMC(10) / W_prod(10): −9090.5 and +4018.7 pcm. It converged in three
iterations to **f_ABS = 0.8026, f_DSP = 1.2016** (worth errors +0.001 %). f = 1 reproduces the
original COMPOs to 0.0 pcm. `U4_CPSB=1` stages the rebuilt files (stem `_cB<md5>`); default decks
are byte-identical. As with bracket B, the target is an independent method, not the accident.

**Static ramp** (`A8_USP=0 tools/a8_ramp.py`), ρ in pcm:

| travel, cm | 10 | 25 | 40 | 80 | 160 | 240 | 280 |
|---|---|---|---|---|---|---|---|
| original (re-run, identical to (29)) | −89.9 | −106.5 | −74.3 | +152.2 | +281.0 | +141.3 | +15.5 |
| U4_CPSB=1, original fit | −82.7 | −92.0 | −47.7 | +220.6 | +383.6 | +234.1 | +100.8 |
| **U4_CPSB=1, refitted** | −86.1 | −83.9 | −17.9 | **+302.4** | **+511.0** | **+379.0** | **+258.1** |

The corrected rods change the t = 0 shape (upper/lower 1.49 → 1.42; the old fit's rms against
Fig. II-9 t = 0 goes from 0.020 to 0.039), so the inversion was redone with them
(`sources/derived/insag7_fig_II9_t0_axburn_fit_cB.txt`, rms 0.0194, 59 solves, bottom bundle
0.468). The peak positive scram is then **+511 pcm = +0.97 $** (β = 0.00529), against +0.53 $.

**The 7 s transient** (bracket B, 3 °C, 56 000 m³/h, USP held, 10 ms; ≈ 2 h 40 min):

| t, s | 0.5 | 1.0 | 1.5 | 2.0 | 2.5 | 3.0 | 3.5 | 4.0 | 4.38 |
|---|---|---|---|---|---|---|---|---|---|
| with TH feedback | 0.817 | 0.763 | 0.879 | 1.282 | 2.338 | 5.034 | 10.78 | 19.98 | **37.1** |
| frozen TH | 0.817 | 0.763 | 0.879 | 1.287 | 2.385 | 5.414 | 13.45 | 30.89 | — |

The frozen-TH twin runs on to a peak of **223×** at 6.5 s and 210× at 7 s (4860 s, 1.4 GB).

- **The feedback run stops at 4.38 s on `THMH2O: DRY OUT REACHED IN CHANNEL 50 39 24`**, at 37×
  (7.4 GW) and still rising about 2 % per step. *[Corrected in (36): this was written as a
  physical boiling crisis and it was not. The slice was 100 J/kg subcooled; the Saha-Zuber
  profile fit, evaluated below its net-vapour point, returned x = 1 and a NaN heat-transfer
  coefficient. Patches 0009-0013 remove it and the run continues to a peak.]* Max fuel
  temperature 774 K, min coolant density 0.544. Energy deposited by then is 5.2 GJ, about 24 kJ/kg UO₂ on average,
  far below the 920 kJ/kg failure enthalpy (INSAG-7 p. 67).
- **It is rod-driven.** There is no void anywhere in the lower half at 1, 2 or 3 s, yet power is
  5× at 3 s. The net TH feedback is negative: fb/frozen is 0.93 at 3 s and 0.65 at 4 s, as the
  fuel heats faster than the steam forms. Void appears only from about 3.5 s (lower half 3.6 %,
  upper half 6.9 % at 4 s).
- **Against the record.** Power passes 530 MW at **2.59 s**, and the e-folding period is under
  20 s from 1.05 s (0.63–0.78 s between 2.5 and 4 s). INSAG-7 Table I-1 records both emergency
  signals (power > 530 MW and excursion period < 20 s) at 01:23:43, about 3 s after EPS-5. INSAG-7
  (p. 121, on its own three models): "none of the three models reproduces the reactor runaway
  when, three seconds after EPS-5 is triggered, signals are generated". This one does. 37× at
  dryout and still rising sits inside the published 3.5–80× band; INSAG-7 p. 67 says "several
  tens of times during a period of about 5 s".
- Fig. II-9 shapes: rms 0.23/0.25/0.30 at 2/3/4 s against the 4 s curve, peak at D 612 cm.

**Gap 3, void worth: narrowed, not closed.**
- The lattice void worth from 0.72 to 0.02 g/cm³ at 10 MWd/kg is ≈ 900 pcm in DRAGON and
  ≈ 1500 pcm in OpenMC (≈ 1.9 β against 3.1 β at 10.9 MWd/kg). It rises steeply with burnup:
  OpenMC 837 / 1499 / 2321 / 3671 pcm at 5 / 10 / 15 / 20 MWd/kg.
- TG and TF move it by only ±10 % over the whole COMPO range (818–1027 pcm at 10 MWd/kg), so they
  are not the missing factor.
- INSAG-7 p. 36 puts the measured whole-core void effect at "+5 βeff" for 2 % fuel at
  1100–1200 MW·d/t per assembly (≈ 10 MWd/kg) with 26–30 manual rods of ORM. That is ≈ 1.6× even
  OpenMC's lattice value. The Smolensk-3 data (TECDOC-722) are post-1986 cores (≤ 0.3 β with
  additional absorbers) and do not help.
- What remains is a source question, not a run: how the measured "void effect" was defined.
  It matters less than it did, because the surge above is rod-driven and void feedback joins
  late.

**Timestep (5 ms twin, `kin1400…dt0005`).** P/P0 at 1.0 / 1.5 / 3.0 / 3.5 / 4.0 s is
0.7632 / 0.8820 / 5.137 / 11.12 / 20.85, against 0.7631 / 0.8791 / 5.034 / 10.78 / 19.98 at 10 ms:
+0.0, +0.3, +2.0, +3.1 and +4.4 %. That is a time shift of about 0.03 s at a 0.6–0.8 s period, so
the excursion is timestep-converged to a few percent through 4 s. The 5 ms run stops at 4.095 s
(24×) on `THMTRS: CONVERGENCE FAILURE IN FLOW CALCULATION`. This is the flow fixed point whose
gain grows as 1/dt (patches 0005/0006), now in rapidly boiling channels, so the halved step
cannot follow the run to dryout. The 10 ms run reaches it.

**Caveats.**
- U4_PCHAN (the flow valving) still comes from the original fit's channel powers.
- The CPS correction is fitted at one state (10.9 MWd/kg, dca 0.72, TF 900) and applied at all
  18 points; the core reads only that state.

## A8 through the excursion: five THM defects, and the band — 2026-10-15 (36)

Local (spark2), sequential. Patches 0009–0014; `tools/a8_insag.py` (new); band inputs in
`sources/derived/`.

### The 4.38 s "dry out" was not a boiling crisis

Patch 0009 (an uncooled slice no longer aborts a transient, and its state is printed) showed the
first slice: H = 1.2868 MJ/kg against H_l,sat = 1.2869 MJ/kg, 100 J/kg subcooled, with quality
x = 1. Five defects, all transient-only, all upstream THMTRS/THMH2O, each found by measurement:

| patch | defect | how it showed |
|---|---|---|
| 0010 | the Saha-Zuber/Levy profile fit x = (xe + F3)/(1 + F3), F3 = −xd·exp(xe/xd − 1), was evaluated below its net-vapour point, where the exponent is positive: F3 ~ 1E15, x = 1, REL = 0, F = Inf, S = NaN, a NaN HCONV ("DRY OUT"). Below xd the fit's own value is x = 0 | the 0009 print |
| 0011 | THMTRS sets XFL(K) = XFL(K−1) and the fit took MAX(XFL0, fit): a boiling bottom under not-yet-heated water handed its quality to every slice above (density 534 kg/m³ in all 20 upper slices), and continuity turned the snap-back into −3000 kg/m²/s at the outlet and a negative enthalpy. In a transient the fit is local (and floored at 0: at xe = xd it rounds to −1E-10, and a negative x makes the Martinelli parameter NaN) | `THMH2O: NEGATIVE INPUT ENTHALPY` at 4.80 s |
| 0012 | the energy equation took every face's enthalpy from the slice below; with the flux reversed above a boiling bottom (−1600 kg/m²/s, water falling back) it drew on the wrong side and oscillated odd-even. Donor-cell faces now | `CONVERGENCE FAILURE IN FLOW CALCULATION` |
| 0013 | (a) a fixed FLOW-RELAX either damps the hardest channel or wastes the others: halve it whenever a pass fails to reduce the error. (b) the relaxation was applied after the pass, but THMH2O writes each slice's new density in place and the next slice's continuity reads it in the same pass, so the march was never damped: relax in place too. (c) the mass-flux error was relative to the local flux, meaningless where the flow reverses: relative to max(\|G\|, G_in) | the same, in 89 channels once 0011 removed the max |

The method was the point. Replaying one channel's power history from the core run through THM
alone (`gen.py` in the session scratch: steady THM at t = 0, then `RESINI: REACTOR-POW /
AXIAL-PFORM` + `THM: TIME` per step, the core deck's own options) takes 3.5 s against 3 h for the
core, and all 1661 channels screen in 8–12 min on 12 cores. Failures inside the real 0–4.8 s
history: 5 before 0011, 89 with 0011–0012, 16 with 0013(a), **0** with 0013(a)–(c).

`channel_mphy` regression: every line of 2.6 million identical except the printed flow-iteration
error where G < G_in (5th digit, 0013(c) by design), all 15 708 iteration counts identical; the
digest is re-baselined on that listing. Patch 0014 (NCR: `CLAMP`, opt-in, `U4_NCRCLAMP=1`) holds a
fuel-map parameter at the COMPO axis edge instead of aborting; see the tilt case below.

### The band

Bracket B unless stated; 3 °C subcooling; flow valved to the corrected-CPS channel powers
(`a8_fit_pchan_cB.txt`, 510–3110 kW; the refit moved nothing by more than 0.3 % through 4 s);
10 ms. Initial-shape band: INSAG-7 p. 69 says a "20 % variation in initial power density" moves
Ref. [28] between 31× and 64× at 6.5 s. Its form is not given; here the Fig. II-9 t = 0 target is
multiplied by (1 ∓ 0.1 x), x = −1 at the bottom, so the bottom-to-top ratio changes by
1.1/0.9 = 1.22, and re-inverted (`A8_TILT`, rms 0.0195 / 0.0194). P/P0, P0 = 200 MW:

| case | 3 s | 4 s | 5 s | 6 s | 6.5 s | peak | at | energy | hottest fuel | stop |
|---|---|---|---|---|---|---|---|---|---|---|
| B | 5.0 | 20.0 | 138 | 88 | 51 | **182** | 5.32 s | 54.6 GJ | 495 kJ/kg | 6.88 s ¹ |
| A | 5.0 | 19.7 | 70 | 48 | 30 | **78** | 5.28 s | 31.0 GJ | 370 kJ/kg | 6.89 s ¹ |
| B, flow × 0.85 | 4.9 | 20.5 | 193 | 87 | 53 | **228** | 5.21 s | 63.7 GJ | 527 kJ/kg | 7.00 s |
| B, tilt toward bottom | 11.3 | 170 | — | — | — | **418** | 4.42 s | 50.2 GJ ² | 537 kJ/kg ² | 4.57 s ³ |
| B, tilt toward top | 2.4 | 5.5 | 7.2 | 8.1 | — | **8.1** | 5.93 s | 4.5 GJ | 121 kJ/kg | 6.17 s ¹ |

¹ flow convergence failure after the peak, power falling. ² to 4.57 s. ³ the hottest bundle's
effective fuel temperature passed the TF axis top, 2000 K (NCR abort). Re-run with
`U4_NCRCLAMP=1` (`…fi60cc01cl…`): identical to the printed digit up to 4.57 s, where NCR held 3
bundles at 2000 K (2004.1 K the hottest), and then stopped one step later, at 4.58 s, on a THM flow
convergence failure. So the bottom-tilted case ends 0.16 s after its peak whichever way the table
edge is handled. Its fuel enthalpy is still rising at the end (537 kJ/kg), so whether it would
reach 920 kJ/kg is open.

All five dip in the first second (0.69–0.83 at 0.8–1.1 s) and cross 530 MW at 2.29–3.10 s with
the period under 20 s from 0.9–1.1 s. B repeated on the final binary agrees with the first B run
to the printed digit through the peak (181.64× at 5.32 s both).

### Against INSAG-7

- **The 01:23:43 signals.** Every case reproduces them; the top-tilted case crosses 530 MW at
  3.10 s, on the recorded 3 s. INSAG-7 p. 121: none of its three models did.
- **The magnitude.** INSAG-7 p. 121 gives 3.5× (Model 2), ~9× (Model 3) and ~80× (Model 1).
  Fig. II-11, digitised (`insag7_fig_II11_model1.csv`), plots Model 1 in units of the 3200 MW
  nominal power, peaking at 4.94 near 7.9 s: 79× the 200 MW start, which is where "~80×" comes
  from. This band spans 8× to 418× and contains all three; A (78×) is Model 1's magnitude, the
  top tilt (8×) is Model 3's. Ref. [28] (p. 69) gives 31× or 64× at 6.5 s; B and A give 51× and
  30× there.
- **The timing.** Ours peaks at 4.4–5.9 s, Model 1 at ~7.9 s. Ours is 6× Model 1 at 5 s (B). The
  early rise is rod-driven, as in (35). Model 1's total reactivity (Fig. II-11) is 0.72 β at
  3.5 s and ~0.9 β from 4.5 s, comparable to our static rod ramp's +0.97 $ at 160 cm (4 s), so
  why its power rises more slowly cannot be read from the figure (its curve includes its own
  feedback; ours is static and rods-only).
- **What dominates.** The initial axial shape: a ±10 % tilt moves the peak 50-fold. Then the
  void worth (A → B 2.3×) and the flow (× 0.85: +25 %). Exactly the ordering of INSAG-7 p. 122:
  "very strong dependence ... on the potential error level of the initial axial distribution,
  the void reactivity effect value, the change in the reactivity level when the water column ...
  is replaced by the graphite displacer".
- **Fuel.** No case reaches 220 cal/g = 920 kJ/kg (INSAG-7 p. 67) in the hottest bundle. INSAG-7
  p. 69 has Ref. [28] reaching it in 5 or 40 assemblies. Two reasons it is low here, both
  stated: Kv peaks at 3.9–4.2 against ~6.0 (p. 121) and 5.5 (p. 67, Ref. [28]), and THM's
  bundle is one 25 cm slice of the channel average (no rod-to-rod or pellet-radial peaking), with
  MAX-T-FUEL a Rowlands-weighted effective temperature, converted through Fink's UO₂ enthalpy.

### Caveats

- The tilt is one form of the 20 %; the source names no form.
- Flow-convergence failures after the peak remain in four cases (0013 does not cover deep
  two-phase flow just after a 400× peak, nor at falling power); peaks and energies to that point
  are unaffected, but the bottom-tilted case's fuel enthalpy is cut off while still rising.
- MAX-T-FUEL is a bundle effective temperature; the enthalpy read from it is a bundle average.
- U4_NCRCLAMP freezes Doppler above 2000 K, so post-clamp power and enthalpy would be upper
  estimates; it acted for one step before the THM stop, so no result here depends on it.

### Next

1. Carry the bottom-tilted case past 4.58 s: find the failing channel with the single-channel
   replay (its history is in the result) and extend 0013, then see whether any bundle reaches
   920 kJ/kg.
2. The fuel-enthalpy reading is a bundle average; a pin-peaking factor and the pellet radial
   profile would turn it into the quantity the 220 cal/g criterion is defined on.
3. Gap 3 (void worth ≈ half the sourced value) is still a source question.

## The bottom-tilted case to 7 s, and rod peaking — 2026-10-16 (37)

**Patch 0015** (THMH2O): the drift-flux term ρ_l ρ_g V_gj / G sends the void to zero as the mass
flux passes through zero. Channel 1605 (inlet 1.55 m/s), 0.14 s after the 418× peak, read a 6.5 %
quality slice as liquid (371 → 526 kg/m³ in one step), and continuity drove its outlet to
−7000 kg/m²/s; the single-channel screen found it as the only failure in the bottom-tilted
history. |G| is now floored at ρ_l V_gj (≈ 150 kg/m²/s) in that term, since steam still rises
through stagnant water at about V_gj; identical to upstream wherever |G| ≥ ρ_l V_gj. Screens:
0 failures over all 1661 channels on the bottom-tilted history to 5.0 s and on B to 4.8 s.
channel_mphy regression unchanged.

Re-runs (all peaks identical to the printed digit, so 0015 changes nothing up to a peak):

| case | stop before | stop now | energy | hottest bundle |
|---|---|---|---|---|
| B, tilt toward bottom (CLAMP) | 4.58 s | **7.00 s** | **106.0 GJ** | **656 kJ/kg** (2300 K) |
| B | 6.88 s | 7.00 s | 55.5 GJ | 496 kJ/kg |
| B, tilt toward top | 6.17 s | 7.00 s | 5.8 GJ | 133 kJ/kg |
| A | 6.89 s | 6.85 s ¹ | 30.8 GJ | 370 kJ/kg |

¹ still a post-peak flow-convergence failure.

**Rod-to-rod peaking** (`openmc/pin_peaking.py`, `pin_peaking.json`): kappa-fission in the 12
outer against the 6 inner rods of the 18-rod bundle, 50k × 250 active, σ ≈ 0.05 %:

| fuel | dca 0.72 | dca 0.15 |
|---|---|---|
| 10 MWd/kg (depl_gb10_ed) | 1.036 | 1.024 |
| fresh | 1.049 | 1.039 |

So the hottest rod sits 2–5 % above the bundle average THM reports. The bottom-tilted case's
hottest rod is then ≈ 680 kJ/kg at 7 s, against 920 kJ/kg (220 cal/g): rod peaking is not what
separates the band from fuel failure. Kv (≈ 4 against INSAG's ~6) and the radial initial shape
remain the candidates.

This closes the DONJON band as Tier B's reference set. Further work moves to Tier B
(`TIER_B_WORKPLAN.md`): a Julia/CUDA engine verified against these runs, with momentum/pressure
TH and uncertainty propagation conditioned on recorded data only.

## Tier B begins: B0/B1 parity, and why the spatial method is fixed — 2026-10-18 (38)

Tier B (`TIER_B_WORKPLAN.md`): a Julia/CUDA engine, `tierb/RBMKCore.jl`, verified against the
DONJON band before it is used for anything new.

**B0, cross sections.** `tools/tierb_export_xs.py` has DONJON's own NCR evaluate the fuel COMPO at
all 1728 grid nodes and the A8 reference mixtures, and writes HDF5. Julia interpolates
multilinearly. Two things the gate found: NCR interpolates the diffusion coefficient as 1/D
(interpolating D directly is off by 8e-5), and DONJON stores per-isotope ν·Σ_f mixture-fastest.
Gate, 26 seeded off-grid states: worst 2.4e-7 (single-precision storage).

**B1, the static core.**
- The engine reads the generated deck itself (GEO: planes, INST-BVAL BUND, DEVINI rods with
  DEVGET/MOVCHK placement, NEWMAC's volume-fraction ΔΣ and additive 1/D). Its per-element cross
  sections match DONJON's final MACRD for all 79 360 elements, worst 1.3e-7.
- Mesh-centred FD (TRIVAC MCFD 1) is reproduced exactly: k = 1.0232573 against 1.023257,
  bundle powers rms 0.018 %.
- But the reference band uses DUAL 1 1, and at 25 cm the two differ by **−423 pcm** in k and up
  to 31 % in bundle power. Refinement does not reconcile them: FD gives 1.0232573 / 1.0267377 /
  1.0284529 at 25 / 12.5 / 8.33 cm (apparent order ≈ 0.3), and DONJON's higher-order elements give
  DUAL 1 1 / 2 2 / 3 3 = 1.027709 / 1.029215 / 1.030559.
- The reason is in the data, not the solver. The CPS cross sections were SPH-equivalenced in
  DRAGON *on DUAL 1 1 at 25 cm* (A6.4; COMPO comment "SPH (TRIVAT DUAL 1 1)"), and A6.3 found
  MCFD 1 loses 31–34 % of absorber worth and cannot carry an SPH equivalence. Homogenised,
  equivalenced cross sections are tied to the scheme they were equivalenced for: refining the mesh
  or changing the element breaks the equivalence rather than converging. So "mesh convergence" is
  not the right question for this model; the consistent method is DUAL 1 1 at 25 cm.
- `RBMKCore.Mixed` implements RT0 with the consistent current mass (TRIVAC DUAL 1 1): cell fluxes
  eliminated, an SPD face system per group (244 144 faces), AMG-CG. On DONJON's MACRD:
  **k = 1.027709 (−0.01 pcm), bundle powers rms 0.018 %, max 0.037 %.** Gate passed. It is slow on
  the CPU (13 min); speed is B6's.

**B2, kinetics (in progress).** `RBMKCore.Kinetics` follows TRIVAC KINXSD/KINSRC/KINPRC (fission
/k₀, θ = 0.8 for flux and precursors, per-isotope precursors). On the FD operator the 1 s null
transient holds P/P₀ to 0.9999938. It is being moved onto the mixed-dual operator next, against an
MCFD 1 and then a DUAL 1 1 reference.

## Tier B: B2 and B3 verified, the GPU path, and a solver-tolerance bias in the DONJON band — 2026-10-18 (39)

**B2, kinetics on the RT0 operator.** `RBMKCore.DualKinetics` carries KINSOL's θ scheme onto the
mixed-dual operator. The θ-scaled leakage is the Fick system with the current mass divided by θ.
Each step is solved by FGMRES on the cell system, with a block Gauss–Seidel preconditioner over the
groups (AMG-CG on each condensed face system).
- **Null transient.** The power-iteration polish of the eigenpair leaves a steady residual of 1.7e-7,
  and that alone drifts the 1 s null transient by −8.8e-6. A Wielandt (shifted-inverse) polish
  takes the residual to 9e-11, and the null transient then holds **P/P₀ − 1 = −1.1e-11**.
- **FD against DONJON MCFD 1** (frozen TH, AZ-5, same deck): within 0.1–1.6 % over 7 s; peak
  2271× against 2238×. (The ten-fold MCFD/DUAL difference, 2238× against 223×, is B1's spatial
  result showing up in a transient.)
- **RT0 against DONJON DUAL 1 1:** −0.27 % at 0.1 s, ≈ 0 at 1–2 s, then a drift to −6 %; peak
  **210.9× at 6.50 s against 223.5× at 6.43 s**.
- **The cause is DONJON's own convergence tolerance.** KINSOL solves each step to EPSOUT = 1e-4
  (`KINRD2.f:58`, the decks' default), starting from the previous flux. That is the same size as
  a step's change. Re-run with `EXTE 2000 1.0E-7`, DONJON's steps 1–4 give 0.9993804 / 0.9982035
  / 0.9965190 / 0.9943693 against RT0's 0.9993819 / 0.9982071 / 0.9965243 / 0.9943765, i.e.
  1.5–7e-6, where the default run sits 2.2e-4 to 1.2e-3 away. At 3.5 min per step, a converged 7 s DONJON
  reference would take about 40 h; a 100-step one is running.
- **Δt halving:** the peak moves −0.91 % (209.0× at 6.45 s at 5 ms). Gate passed.
- The current DONJON binary reproduces the Oct-10 DUAL trace to every printed digit (294 steps
  re-run), so the patches since then do not enter a frozen-TH run.

**Consequence for Tier A.** Every A8 band number (35)–(37) was computed at EPSOUT = 1e-4. In the
frozen-TH case that tolerance lowers the converged peak by about 6 %. The band's qualitative
results (the alarms at 2.3–3.1 s, the ordering of the cases) are earlier than the drift and
unaffected, but its peak powers and energies carry a bias of this order. The B4 run below measures
it in the coupled case. The converged numbers now come from Tier B.

**B3, the THM: port.** `RBMKCore.Channel` ports THMDRV/THMTRS (with patches 0005, 0006 and
0009–0015), THMH2O, THMPH, THMROD and the UO₂/Zircaloy functions. Properties come from THM's own
freesteam sources, built from DONJON's tree (`Water.jl`). The reference is DONJON THM itself on a
frozen power shape (`tools/tierb_thmref.py`): a fresh steady state, then 35 transient steps of
0.01 s with the power doubling every 5 (×128), using the A8 transient keywords. Results over
1661 × 28 bundles at every checkpoint:
- **T-FUEL:** rms 0.0045 K, max 0.035 K. The maximum is one bundle, offset by a constant amount
  from t = 0, inside THM's ERMAXT of 0.05 K.
- **D-COOL:** rms ≤ 1.6e-5 g/cm³. The maximum, ≤ 2.6e-3, is in isolated bundles at the Saha–Zuber
  onset switch (REAL*4 against Float64 flips K0, the limit cycle documented in the A7 deck).
- **Cost:** 3.3 s for the core's steady state; 4–30 s per transient step on 4–6 contended
  threads.

**B6 groundwork, the GPU.** The RT0 face systems are well conditioned. Jacobi-PCG on cuSPARSE
solves them in 38/129 iterations, 0.034/0.044 s, against 0.65/2.0 s for AMG-CG on the CPU
(`GPUDual.jl`).
- **Eigenproblem:** k = 1.027708847 against DONJON's 1.027709, residual 7e-11, bundle powers rms
  0.0174 % against DUAL 1 1, in 158 s (CPU: 787 s idle, about 3000 s under load).
- **Kinetics:** CPU and GPU agree to 1e-11 in P/P₀ and 3e-10 in flux, at about 1.8 s per step
  against about 40 s.
- **Incident:** CUDA.jl frees device arrays only when Julia's GC runs, and on the unified memory
  its pool grew about 5 GB per step, to 30 GB in 6 steps, before I stopped the run. Every GPU run
  now has to set `JULIA_CUDA_HARD_MEMORY_LIMIT` (the code refuses to run without it), per-step
  operators are freed explicitly, and a watchdog kills any of these jobs above 12 GB. The pool is
  now flat at 4.1 GiB.

**B4, the coupled transient** (band B, `…pc99b7f3_dev_axf527ca_kin700v40g12shvdfr025fi60cc01dt001_vB65c86e_cB4af83e`,
RT0 on the GPU plus the THM port, in the deck's own step order; t = 0 from DONJON's FMAP, bundle
powers rms 0.017 %, TH rebuilt to 0.038 K). The ratio to DONJON follows the frozen case step for
step: 0.997 at 0.1 s, 1.0005 at 1–2 s, 0.955 at 4.5 s. The fuel temperatures track (812 K against
819 K at 4.5 s), so the TH adds no discrepancy of its own; the difference is the kinetics
tolerance. Over the whole run:
- 530 MW crossed at **2.59 s in both**;
- peak **182.75× at 5.33 s against 181.66× at 5.32 s (+0.6 %)**;
- energy to the peak 24.83 against 25.55 GJ (−2.8 %), and to 6.97 s 54.94 against 55.29 GJ
  (−0.6 %).

All three B4 gates pass (0.05 s, 10 %, 10 %). The feedback-limited peak is far less sensitive to
DONJON's tolerance bias than the frozen-TH runaway (0.6 % against 6 %): Doppler and void set it
through the deposited energy, which a few pcm of rod-reactivity history barely moves.

The run stopped at 6.98 s: one channel's THMTRS flow iteration failed to come under CYCLE-OK's
0.1 cap in 60 iterations, after the peak. DONJON's patch-0015 run passed that point with its
slightly different trajectory. The fixed-point flow solver is the fragile part of the inherited
TH, and B3b's momentum model replaces it.

Cost: about 5 s per step through the rise (kinetics 1–2 s on the GPU, cross sections 1–2 s, TH
1.5 s) and 20 s per step past the peak, where the TH is the bottleneck. That was before the 3–6×
TH speed-up committed alongside this section. The remaining band cases (A, flow ×0.85, both tilts)
are queued.


## Tier B: B4 passes on the whole band; where THMTRS still fails — 2026-10-18 (40)

All five band cases were rerun coupled (GPU RT0 + the THMTRS port, t = 0 from each case's DONJON
FMAP) and compared with their DONJON listings by `tools/tierb_bandcmp.py`:

| case | 530 MW (DONJON / Tier B) | peak DONJON | peak Tier B | energy to DONJON's peak | Tier B reached |
|---|---|---|---|---|---|
| B (`…axf527ca…_vB65c86e`) | 2.59 / 2.59 s | 181.66× at 5.32 s | 182.75× at 5.33 s | −2.8 % | 6.97 s |
| A (`…axf527ca…_cB4af83e`, no vB) | 2.59 / 2.59 s | 78.29× at 5.28 s | 79.18× at 5.29 s | −1.4 % | 5.86 s |
| flow ×0.85 (`accq085`) | 2.60 / 2.60 s | 228.43× at 5.21 s | 228.22× at 5.23 s | −3.4 % | 6.64 s |
| tilt top (`axc335c6`) | 3.10 / 3.10 s | 8.09× at 5.93 s | 8.17× at 6.04 s | −0.1 % | 7.00 s |
| tilt bottom (`ax53a84d`, CLAMP) | 2.29 / 2.29 s | 417.65× at 4.42 s | 415.07× at 4.43 s | −4.5 % | 7.00 s |

Every case passes all three B4 gates (530 MW within 0.05 s — identical in all five; peak within
10 % — within 1.4 %; energy to peak within 10 % — within 4.5 %). The energy is consistently low
by a few per cent, the sign of DONJON's KINSOL tolerance bias (39), which accumulates through the
rise. The bottom-tilted case ends at 105.2 GJ against DONJON's 106 GJ (37).

Two cases stop after their peaks, both in the THMTRS port's flow fixed point (one channel's
iteration does not come under CYCLE-OK's cap): A at 5.86 s and flow ×0.85 at 6.64 s. DONJON's own
patched THM passed those points on its slightly different trajectory (A's DONJON listing ends at
6.85 s). The first replacement tried, the B3b column march with its Gauss–Seidel sweeps for reversed
faces (`B4_TH=col`), failed earlier in A, at 4.80 s ("reversed-flow sweeps did not converge"):
marching does not survive the post-peak flow reversals either. (41) is the replacement that does.


## Tier B: B3b — a simultaneous Newton channel solver, and why marching fails — 2026-10-18 (41)

**What replaces THMTRS's flow fixed point** (`tierb/RBMKCore.jl/src/Column.jl`). The channel is a
conservative finite-volume column (cells = fuel slices, face mass fluxes, donor-cell enthalpy,
backward Euler) with THM's closures. Three solvers were built on it, in order:

1. *The upward march* (`col_step`). With upward faces the column is block lower-triangular and one
   march is exact; with THMTRS's own discretisation (`scheme=:thm`) it reproduces the ramp gate
   (D-COOL rms ≤ 3.9e-5). Reversed faces need Gauss–Seidel sweeps, and those failed in band A at
   4.80 s, earlier than THMTRS (40).
2. *Momentum and lines, by shooting* (`Lines.col_step_loop`). The pressure marches up through each
   cell's momentum balance ([D] pp. 68–69 friction), the channel sits between its group header and
   drum (water line + ZRK valve [D] Table 3.1, steam-water line), and the inlet flux is shot to
   meet the drum pressure. **This fails structurally near saturation:** a pressure error returns
   through the void as a flux error ~ (dz/dt)·∂ρ/∂p and again as a pressure error through the
   cell's inertia, a gain ~ (dz/dt)²·∂ρ/∂p per boiling cell — about 0.3 at 10 ms and 1.25 at 5 ms
   with 3 K subcooling. The mismatch in Gin became steep and discontinuous (+964 → −626 kgf/cm²
   over 25 kg/m²/s), smaller steps made it worse, and the 77 → 89 kgf/cm² "pressure spike" it
   produced was an artefact.
3. *Simultaneous Newton* (`Lines.col_step_newton`, `col_step_newton_flux`). All cells' mass, energy
   and momentum balances and both line equations are one system, x = [Gin; (h, p, G) per cell;
   p_top], solved by Newton with a banded finite-difference Jacobian (3 colours × 3 unknowns),
   backtracking, and a per-channel Jacobian cache (chord Newton). A dense 86×86 LU per channel,
   CPU, 59 kB.

**Newton needs smooth closures, and THM's are not, in four places.** Each was found by scanning
the residual along the failed Newton direction, and each is changed only on this path (`tight`,
`localonset`; the THMTRS port and its gate are untouched, T-FUEL rms still 0.0045 K):
- Saha–Zuber onset is fixed at the first cell past onset and carried up the column, so the next
  cell's void jumps from 0 when the onset changes cell (the same switch as the A7 limit cycle,
  (11)). Here: the local-conditions form, onset subcooling from the cell's own heat flux and flow.
  This is a **modelling change**: the Newton model's own steady state differs from THM's by up to
  2.4e-3 g/cm³ in D-COOL (one channel), 0.09 K in T-FUEL.
- Inner tolerances (rod ↔ wall 1e-3 K, THMH2O's wall 1e-5, THMPH 1e-5, a 0.1 K saturation switch)
  made the residual noisy at 1e-5: iterated to fixed points.
- THMH2O's sticky KWA = 0 wall iteration stops on either side of saturation depending on its path:
  replaced by a bracketed root with the regime a function of T_w alone (unique: T_w,new falls as
  the nucleate term grows).
- `prop_pT` at exactly T_sat rounds to either phase (liquid k, μ, cp jump): never evaluated there.

**Single channel** (`test/b3b_lines.jl`; line geometry and header/drum pressures are placeholders,
`sourced=false`, gaps 1, 2, 5, 6 in `sources/derived/b3b_loop_data.md`). The valve closure from the
steady state gives 9.6 kgf/cm² across a 1.40 cm² throat, inside [D] Table 3.1's 6.2–14 kgf/cm² and
0.9–2.5 cm². Null transient exact over 1 s. Power ×20 over 1 s: 3–4 Newton iterations per step, no
sub-steps; Δt = 10, 5 and 2.5 ms agree to 1 kg/m²/s in Gin, 0.01 kgf/cm² and 0.001 in exit void.
Heating throttles the inlet flux 2587 → 2498 kg/m²/s at constant header pressure; a 3 kgf/cm²
header fall then cuts it 16 %.

**Band A coupled** (`B4_TH=newton`: THM's boundary conditions, inlet flux prescribed, p = outlet
pressure; starting from DONJON's state):
- 530 MW at 2.59 s (DONJON 2.59); peak **75.97× at 5.31 s against 78.29× at 5.28 s (−3.0 %)**;
  energy to DONJON's peak −5.0 % (THMTRS port: +1.1 %, −1.4 %). All three B4 gates pass. The extra
  deficit against the THMTRS port appears from 4 s, when the boiling front moves down, so it is the
  local-onset change, not the solver;
- **runs to 6.91 s**, past THMTRS's 5.86 s failure and DONJON's own 6.85 s end, and tracks DONJON
  after the peak: 47.65× against 47.71× at 6 s, 30.21× against 30.24× at 6.5 s, 23.10× against
  23.17× at 6.85 s.
- It stopped at 6.91 s on one channel where eight sub-steps did not converge, with a kink in the
  void profile at the cell the hottest wall is in (0.57 between 0.65 and 0.66), probably a fifth
  non-smooth closure (the KWA = 3 post-dryout branch); to be scanned as the other four were.

Cost: ~6 s per core step for the TH (10 threads) before the 2× closure speed-up, against ~1.5 s
for the THMTRS port; B6 needs an analytic or AD Jacobian and fewer tight inner iterations.

**What this does not yet do.** The loop boundary conditions (header from the pumps, drum
pressure) are built and tested on one channel but not run core-wide, because the line geometry,
the 01:23 header and drum pressures and the pump curve are unsourced. The data INSAG-7 recorded
after the alarms (drum pressure 75.2/88.2 kgf/cm² and flow −40 % at +7/+8 s) are what that model
is for, and they cannot be used to tune it.


## The 01:23 drum pressure: recorded, ~10 kgf/cm² below the decks, and worth +34 % on the peak — 2026-10-19 (42)

**Sources found.** (a) The DREG record of the SKALA tape in digital form (Dmitriev, VNIIAES;
`sources/accidont/`, `derived/dreg_0123_mfcc.csv`): per loop, drum pressure, level, feedwater,
MCP-inlet temperature and each pump's flow from 01:00 to 01:23:48, the discrete alarms, and the
01:00 PRIZMA per-channel cartograms (flows, powers, burnups; scans, not yet transcribed).
(b) Mochizuki, NED 237 (2007) [MOC07]: a dimensioned quarter-loop of Unit 4 with elevations
(`derived/mochizuki2007_loop.csv`). (c) The Ignalina RBMK-1500 Source Book [ALM98]: pump inertia
(GD² = 15 t·m², confirming [D]; [MOC07]'s 1500 kg·m² is a slip), drum ID 2.6 m, header lengths,
and the ZRK valve's Δp(Q) at eight openings, ξ = 0.63–1.4 in the velocity-head form
(`derived/ignalina_zrk_valve.csv`). Gap status: `derived/b3b_loop_data.md`.

**The decks' pressure was the post-excursion value.** Before AZ-5 the drums read 63.2–65.0
(left) and 64.1–68.6 (right) kgf/cm²; 75.2/88.4 only at 01:23:48. The `acc` decks' 75.3 kgf/cm²
(7.384 MPa) is INSAG-7's +8 s left-drum reading. At a fixed 3 K subcooling the lower pressure
raises the density drop per unit quality by ~20 % (ρ_l/ρ_g 18.9 → 22.4) — more positive void
feedback per unit of excess enthalpy.

**Band B rerun at 66.8 kgf/cm²** (the mean of the last two pre-AZ-5 readings, read as absolute;
`U4_POUT=66.8`, deck `…acco668…`, new DONJON t = 0 dump, Tier B RT0 + THMTRS port, 3 K kept):

| | 75.3 (decks) | 66.8 (DREG) | |
|---|---|---|---|
| 530 MW | 2.59 s | 2.58 s | |
| peak | 182.8× at 5.33 s | **245.4× at 5.22 s** | +34 % |
| energy at peak | 25.2 GJ | 28.7 GJ | +14 % |
| energy at 6.9 s | 54.4 GJ | 65.3 GJ | +20 % |
| T-FUEL max at end | 1889 K | 1998 K | +110 K |

The first 3 s (the alarm timing) move by ≤ 3 %: the rods drive them and there is little steam. The
difference grows from 4 s, when boiling spreads down the core. The run reached 7.00 s (THMTRS
did not fail this time). This **retracts PROGRESS (33)**'s "pressure moves the surge by a few
percent or reduces it": it was argued from the 7.38 MPa level and the sign of a pressure rise,
not from the level itself.

**Independent of the TH solver.** The same pair with the B3b Newton column (`B4_TH=newton`):

| band B | THMTRS port | Newton column |
|---|---|---|
| peak, 75.3 → 66.8 kgf/cm² | 182.8× → 245.4× (+34 %) | 173.1× → 230.2× (+33 %) |
| energy at 6.9 s | 54.4 → 65.3 GJ (+20 %) | 52.5 → 62.7 GJ (+19.5 %) |
| 530 MW | 2.59 → 2.58 s | 2.59 → 2.58 s |
| reached | 6.97 / 7.00 s | 7.00 / 7.00 s |

The Newton column sits 5–6 % below the port at both pressures (its local Saha–Zuber onset, as in
band A, (41)) and runs both cases to 7 s without a failure.

**The subcooling is probably also mis-placed.** The loop scaffold (`Loop.leg_state`) mixes drum
liquid with the recorded feedwater (~150 t/h at ~165 °C per side) and adds the pumps' shaft power
([ALM98] 4.3 MW each). With the DREG drum pressure it predicts the pump-inlet water at
280.7 °C (281.7 if Psd is gauge) against DREG's recorded **281 °C**, and the water entering the
core at the drum's own saturation temperature: **0 K subcooling against the drum pressure**, ~2.9 K
against a core-bottom pressure ~3 kgf/cm² higher. INSAG-7's "3 °C" is then a core-bottom figure,
and the decks — which apply it at THM's single (outlet) pressure — give the core too much
subcooling, in the direction that also suppresses the surge. A single-pressure THM cannot represent
both ends; this is what the B3b loop model is for.

**What this does not touch:** the Tier B verification (B2, B3, B4 parity: both codes always saw the
same inputs) and the B3b solver results.


## Tier B: B3b-3 — the core-wide loop model against the DREG run-down record, and AZ-5 through it — 2026-10-20 (43)

> **Numbers RETRACTED in (44):** two loop energy errors (graphite heat 28x low; feedwater
> subcooling counted twice). The flow-drop finding and the solver changes stand.

**What was built.** `src/Loop.jl` + `test/loop_setup.jl`: two loop halves, each a lumped saturated
drum (on drum + steam-piping volume), four parallel MCPs sharing one pressure rise, a lumped leg
(inertia, loss, elevation) to the group headers, and every fuel channel of the half as a Newton
column with its own inlet line, ZRK throat and outlet line (B3b-2). The header pressure and the
pump flow close per step by a 2×2 Newton through each channel's dGin/dph from its own Jacobian.
Leg temperature from mixing drum liquid, feedwater and pump heat. `test/b3b_loop_core.jl` runs it
TH-only from 01:23:04 (stop valves shut, pumps 3, 4 of each side running down with TG-8) to
01:23:40 at the deck's t = 0 power field; `b4_coupled.jl B4_TH=loop` continues it through AZ-5.

**Inputs, each sourced or labelled.**

| item | value | source / status |
|---|---|---|
| drum pressure at 01:23:04 | 63.2 L / 64.5 R kgf/cm² | DREG Psd, read as absolute |
| leg loss at nominal | 4.31 kgf/cm² (pipe friction 0.24 + the rest) | closed from drum 70 / pressure header 86.0 (Leningrad training text) / group header 82.7 ([D] p. 50) at 37 500 t/h, 6 pumps — this carries the throttling-regulating valve |
| steam volume to the stop valves | 296 m³ per half | Ignalina's 404.7 m³ ([ALM98]) × RBMK-1000/1500 steam flow 5600/7650; bracket 0–405 for B5 |
| graphite → coolant heat | 34 MW into the fuel channels (26–40) | `tools/graphite_heat.py`: lumped stack, f_g = 5 % ([ALM98] p. 56), conductance closed at the nominal stack temperature 570–750 °C ([D]), integrated through the INSAG-7 power history from 3200 MW; Tg(01:23) 340–420 °C, τ 1.2–2.4 h. [MOC07]'s ~80 MW (20 per quarter) is ~2× this |
| loop split | by the core's x mid-line: L 826, R 835 channels | ASSUMPTION (decision 5) |
| run-down pump speed | a(t) = 1 − 6.0e-4 t (a = 0.978 at 01:23:40) | inferred from DREG per-pump flows through the head curve (below); hsh = 1.2 ASSUMPTION |
| half-loop flow at 01:23:04 | 6049 L / 6074 R kg/s | DREG pump sums; the deck's within-half valving shape kept |
| feedwater | DREG Gfw, Tfw per side | record |
| ZRK loss | ξ(A) 0.63–1.39 | [ALM98] Fig. 5.5 |

**Pump speeds from the flows.** Pumps 1, 2 on the grid and 3, 4 on TG-8 share one pressure rise,
so on the head curve h = hsh·a² − (hsh−1)v² the run-down pumps' speed follows from their flow
against the grid pumps': a² = [hsh − (hsh−1)(v_g² − v_c²)]/hsh. INSAG-7 has no TG-8 frequency
record. The fitted run-down at AZ-5 depends on the unsourced shut-off ratio: a = 0.987 / 0.978 /
0.966 / 0.956 for hsh 1.1 / 1.2 / 1.35 / 1.5.

**The deck's valving splits the halves.** `U4_FLOW=prop` valves every channel by its 01:23 power,
which gives L 6290 / R 5433 kg/s (±7 % about their mean); DREG has the halves equal
(28.95 / 29.02 ×1000 m³/h). The loop takes each half's flow from DREG and keeps the deck's shape
within it. Both were run (full core, hsh 1.2, dt 0.5 s):

| 01:23:04 → 01:23:40 | model, deck flows | model, DREG flows | DREG |
|---|---|---|---|
| drum L, kgf/cm² | 63.24 → 65.98 | 63.24 → 65.98 | 63.21 → 66.11 |
| drum R | 64.54 → 67.02 | 64.54 → 67.00 | 64.40 → 68.6 (01:23:39) |
| half flow L, Σ4 pumps (m³/h) | −1.2 % | −1.2 % | **−12.3 %** |
| half flow R | −1.1 % | −1.1 % | **−13.5 %** |
| grid pump, end | 7.96 L / 7.06 R | 7.70 L / 7.75 R | 7.01, 6.79 L / 7.46, 6.44 R |
| run-down pump, end | 6.85 L / 5.78 R | 6.55 L / 6.61 R | 5.95, 5.65 L / 5.63, 5.58 R |
| pump inlet | 277.9 → 280.7 L, 279.5 → 281.8 R | same | 281 (constant) |
| drum level | +20 L / +15 R mm | +20 L / +16 R mm | (Hsd: one drum, noisy) |

(DREG's interpolated 70.0 R at 01:23:40 is between 68.6 at 01:23:39 and 80.1 at 01:23:47.)

**The drum pressures follow the record without any fitted constant**: +2.7 kgf/cm² in 36 s against
the recorded +2.9 (L) and +4.2 (R, to 01:23:39). They are set by the steam volume, the steam
production at 200 MW + graphite heat, and the feedwater; nothing was adjusted to them.

**The recorded flow drop is not reproduced, with any head curve.** The model loses 1–2 % of the
half-loop flow over the run-down; DREG records −12 to −14 %. Steeper head curves (hsh 1.35, 1.5)
give only −2.3 / −2.8 % (1/40-subsample runs); hsh 2.0 drives the run-down pumps' flow to zero.
The cause is the grid pumps: in the model the slowing run-down pumps unload the common header and
the grid pumps' flow rises (7.3 → 7.8–8.0), while the record has the grid pumps flat or falling.
With one pressure header and an unchanged circuit, that is impossible: the record implies the
circuit's resistance rose by ~25–30 % over the 36 s (rising void in the core, which this power
field does not produce), or the grid pumps also slowed, or the flowmeters read low (the cavitation
/ measurement debate around the 01:23 flows). This is a finding to carry into B5 as a conditioning
datum with that ambiguity stated, not a parameter to tune.

**AZ-5 with the loop (`B4_TH=loop`, band B, deck `…acco668…`).** The loop's own state at
01:23:40 (after the 36 s above at the FMAP power) replaces DONJON's T-FUEL/D-COOL; the t = 0
eigenpair is recomputed on it (k0 1.031670; bundle powers 1.9 % rms from DONJON's, max 4.7 %;
T-FUEL within 2.8 K; D-COOL 0.662–0.750 against DONJON's 0.734–0.754 — the loop's core has more
steam, its inlet being at the drum's saturation rather than 3 K below the outlet pressure's). Both
halves are then stepped with the kinetics at 10 ms: no steam out (stop valves shut; BRU-K at
01:23:48), DREG feedwater, the run-down pumps on the fitted a(t) throughout (their trip/coast
times are not sourced). Same cross sections, rods and kinetics as (42):

| band B, 66.8 kgf/cm² deck | THMTRS port, fixed p | Newton column, fixed p | **loop** |
|---|---|---|---|
| 530 MW | 2.58 s | 2.58 s | **2.69 s** |
| peak | 245.4× at 5.22 s | 230.2× at 5.24 s | **110.4× at 5.78 s** |
| energy at peak | 28.7 GJ | 27.5 GJ | 21.3 GJ |
| energy at 6.9 s | 65.3 GJ | 62.7 GJ | **38.5 GJ** (−39 %) |
| T-FUEL max | 1998 K | 1974 K | 1703 K |
| reached | 7.00 s | 7.00 s | 7.00 s |

The loop halves the peak and takes 39 % off the energy. Not yet separated: the loop's different
starting state (more void, inlet at saturation, a recomputed eigenpair), the pressure rising
through the excursion (drum +3.2 kgf/cm², header +4.6 by 7 s, collapsing void), and the flow
falling (−11 % by 7 s, which works the other way). Each is one rerun (e.g. the loop's t = 0 state
under fixed-pressure TH); that decomposition is the next step before any reading of the number.

**Against the post-AZ-5 record**, the loop is too slow:

| | +5 s (01:23:45) | +6 s | +7 s | +8 s |
|---|---|---|---|---|
| drum L, model | 66.59 | 67.51 | 69.23 | — |
| drum L, DREG | 67.5 | 72.8 | — | 75.2 |
| drum R, model | 67.58 | 68.48 | 70.13 | — |
| drum R, DREG | — | — | 80.1 | 88.4 |
| half flow, model | −4 % | −11 % | −11 % | — |

INSAG-7 has the flow down ~40 % at +7/+8 s; the model −11 %. The recorded pressure rise from
+5 s (+5 kgf/cm² in 1 s, L; +8.3 in 1 s, R from 01:23:47) is five to six times the model's (+0.9 and +1.7 over the same seconds). Either
the excursion was stronger than this model's (consistent with the fixed-pressure runs, which
reach 230–245×), or the steam path to the drums is faster than a lumped drum on 615 m³ (the steam
volume assumption is the obvious candidate: 0 m³ would roughly double dp/dt), or both. This is the
first test of the excursion against a recorded loop quantity, and it fails in a direction that
says the loop model is not yet the better estimate of the peak.

**Solver changes.** The per-channel throat closure (`valve_area`) solves the Newton model's steady
state; where a single steady step stalls on the closures' noise floor (~5 Pa on a momentum row) it
now marches in pseudo-time with a geometrically growing step. On the Newton path only, Chen's
nucleate term is switched by the wall superheat alone (THM's "bulk quality > 0" switch made the
wall flux jump at the onset cell), and the Chen Δp_sat is capped below T_crit in the wall-root
bracket. The THMTRS port is untouched; the Newton band-B numbers of (42) predate this change.

Getting the coupled run through the excursion took four more (each found by dumping the failing
channel step and replaying it alone, `Loop.FAILDUMP`; all on the Newton path only):
the two-phase friction multiplier's x^(1/8) (infinite slope at x = 0⁺) regularised below x = 1e-3;
in the local-onset closure a cell with zero heat flux had x = 0 even past saturation, so its void
jumped to ~x_eq as the flux turned positive — now x = x_eq, the profile's own limit; the wall-root
bracket widened instead of failing; a failed channel step retried with full Newton (the chord
Jacobian reused across sub-steps stalled where full Newton does not). A counted last-resort
acceptance (|r| < 1e-3) exists and was never used (0 in 700 steps). Pressure-row noise floor
10 Pa (mass/energy rows 1e-5). The TH-only runs above predate the first two of these; both act
only where x < 1e-3 or a cell's heat flux vanishes. Cost: 24 min for the 36 s pre-run (cached by
content), ~10–30 s per 10 ms step on 18 threads, ~4 h for 7 s; checkpoints every 50 steps.


## Tier B: the loop's effect decomposed, and the steam volume is not the problem — 2026-10-21 (44)

**(43) is RETRACTED in its numbers.** Two energy errors in the loop, found by the steam-volume grid
below (graphite heat 26 → 40 MW moved the pre-AZ-5 drum pressure by 0.01 kgf/cm²; an audit at
+100 MW per half showed +3.4 MW reaching the drum):
1. the graphite heat (`qext`) was divided by the lattice-cell volume instead of the coolant volume
   (THM's `fcool` carries `rapcool = 3 sass/(nfuel acool)` for that): it entered at 1/28, ~1.2 MW
   instead of 34;
2. feedwater was mixed into the core-inlet leg AND fed to the drum, which also gave up the full
   loop flow: its subcooling (~22 MW per half) cooled twice. It joins the drum liquid in the
   downcomer mixers ([D]), so the drum now gives up W − w_fw and does not receive it.
Both add ~38 MW per half. (43)'s "drum pressures follow DREG unfitted" and its 110× AZ-5 peak came
from the erroneous model; its qualitative flow finding stands (below).

**Steam volume: sourcing.** [ALM98] Table 5.1's 404.7 m³ per loop is "pipes from separator drums
to turbine" (RBMK-1500). Both designs use 600 mm main steam lines ([ALM98] p. 39; TECDOC-722
III.3.1 for Smolensk-3, an RBMK-1000), so the volume follows the line lengths and layout, not the
power rating: (43)'s scaling by steam flow had no basis. No RBMK-1000 lengths were found. [D]: each
drum's 14 steam outlets split 7/7 between the two turbines' collectors, so the halves share one
steam system (`sources/derived/b3b_loop_data.md`).

**Steam volume: what the pre-AZ-5 record allows** (TH-only, 01:23:04 → 01:23:40, 1/8 of the
channels, corrected model; drum pressure rise in kgf/cm²):

| V per half (m³) | 0 | 150 | 296 | 405 | 600 | 900 | DREG |
|---|---|---|---|---|---|---|---|
| L, Qg 34 MW | +4.47 | +4.03 | +3.68 | +3.45 | +3.11 | +2.70 | +2.90 |
| R, Qg 34 MW | +3.84 | +3.46 | +3.15 | +2.95 | +2.66 | +2.31 | +4.20 |
| mean, Qg 26–40 | 4.0–4.3 | 3.6–3.8 | 3.3–3.5 | 3.1–3.3 | 2.8–3.0 | 2.4–2.6 | 3.55 |

With the halves sharing steam, the mean is the constraint: **V ≈ 150–450 m³**, excluding 0 and 900.
The halves separately disagree (L wants ~700, R exceeds the model even at 0): a shared steam
system or a Psd offset. Qg moves the rise by ~0.25 per 14 MW. The pre-AZ-5 flow drop is still not
reproduced (model −1.1 % for every V and Qg against DREG's −12/−14 %).

**AZ-5 with the corrected loop** (band B, deck `…acco668…`, hsh 1.2, Qg 34 MW; full core, 10 ms,
no loose acceptances in any run). The t = 0 state is the loop's own after the 36 s pre-run:
k0 1.03184, bundle powers 2.8 % rms from DONJON's (max 6.3 %), D-COOL 0.645–0.748 against
DONJON's 0.734–0.754 — the loop's core starts with more steam.

| run | 530 MW | peak | E at peak | E at 6.9 s | T-FUEL max |
|---|---|---|---|---|---|
| THMTRS port, fixed p (42) | 2.58 s | 245.4× at 5.22 s | 28.7 GJ | 65.3 GJ | 1998 K |
| Newton column, fixed p (42) | 2.58 s | 230.2× at 5.24 s | 27.5 GJ | 62.7 GJ | 1974 K |
| D-B: loop state, all loop boundaries frozen after AZ-5 | 2.77 s | 108.2× at 5.94 s | 21.0 GJ | 36.3 GJ | 1681 K |
| D-C: drum frozen (= unlimited steam volume) | 2.77 s | 89.2× at 5.95 s | 19.0 GJ | 32.0 GJ | 1599 K |
| **L0: full loop, V = 296 m³** | **2.77 s** | **84.7× at 5.97 s** | 18.5 GJ | **30.8 GJ** | 1575 K |
| V = 0 | 2.76 s | 85.5× at 5.95 s | 18.6 GJ | 31.2 GJ | 1581 K |
| V = 450 | 2.77 s | 84.4× at 5.99 s | 18.7 GJ | 30.7 GJ | 1573 K |

**Decomposition** (shares of ln(230/84.7) = 1.00): the loop's starting state and per-channel
hydraulics (D-B against fixed p) **76 %**; header/pump/flow dynamics (D-C against D-B) 19 %; the
drum pressure rise (L0 against D-C) 5 %. With the header held (D-B) the channels' own two-phase
pressure drop takes the core flow down 19 % by +6 s; the loop's pumps answer the falling flow with
more head (the header rises 3 kgf/cm²) and hold the drop to 9 %, so less void and a lower peak.
D-B does not separate the starting state from the change from fixed-flow to fixed-Δp channels;
since Δp-driven channels lose flow as they void (which raises a peak), the reduction most likely
comes from the starting state — the next run (fixed-pressure, fixed-flow TH from the loop's
state) decides it.

**The steam volume does not matter, and does not explain the slow pressure rise.** 0 → 450 m³
moves the peak by 1 % and the energy by 1.6 %. After AZ-5 the drum pressure rises

| kgf/cm² | +5 s | +6 s | +7 s | +8 s |
|---|---|---|---|---|
| DREG L | 67.5 | 72.8 | — | 75.2 |
| DREG R | — | — | 80.1 | 88.4 |
| model L, V = 0 / 296 / 450 | 68.6 / 67.6 / 67.2 | 69.5 / 68.3 / 67.9 | 71.2 / 69.7 / 69.1 | — |
| model R, V = 0 / 296 / 450 | 69.4 / 68.5 / 68.1 | 70.2 / 69.2 / 68.8 | 71.9 / 70.5 / 70.0 | — |

Even with no steam piping the model's +6 s rise is +0.9 kgf/cm² per second where L recorded +5.3;
the core flow falls 10 % by +7 s against INSAG-7's ~40 %. The record therefore asks for either far
more energy reaching the water by +6 s than this model's 19.0 GJ (the fixed-pressure Newton run has
52.1 GJ there), or a faster pressure response than a lumped drum in thermal equilibrium can give: here
every joule entering the drum is shared with its ~170 t of saturated liquid before the pressure
moves; a steam space that pressurises ahead of the liquid (non-equilibrium) would respond several
times faster to the same energy. Both are open; the second is a model-form question about the drum,
not a parameter.

**What this does to the B5 inputs:** the steam volume drops off the list of first-order
uncertainties for the excursion (it stays a pre-AZ-5 conditioning input, 150–450 m³); the
starting-state question (inlet subcooling and the core's void at 01:23:40) is the dominant one,
consistent with (33)/(42); the drum's model form joins the list.


## Tier B: a non-equilibrium drum — the post-AZ-5 pressure rise up to triples, the peak does not move — 2026-10-21 (45)

**Why.** (44) left the post-AZ-5 drum pressure rising 3–6× slower than recorded and pointed at the
equilibrium drum: every joule entering it was shared with ~170 t of saturated liquid before the
pressure moved. At a 1–2 s excursion that is the wrong limit.

**The model (`Loop.Drum2`, `DRUM_TAU=τ`).** Per loop half, a vapor region (M_g, H_g) and a liquid
region (M_l, H_l) at one pressure in the fixed drum + steam-piping volume; each may leave
saturation (the vapor superheats under compression, the liquid falls subcooled). Per region
dH − V dp = Σ h dm, so the p dV work is exact; p closes M_g v_g(p,h_g) + M_l v_l(p,h_l) = V. The
risers' mixture is separated at the drum pressure; the downcomers draw the liquid region's own
enthalpy (so a subcooled drum also cools the core inlet). Exchange: condensation on the subcooled
liquid, Γ = M_l c_p (T_sat − T_l)/(h_fg τ), and phase separation of any two-phase content at the end
of each step (flashing is immediate, condensation rate-limited). τ → 0 tracks the equilibrium drum
(4 % over 10 s); conservation to 1e-11. **τ is an ASSUMPTION** (the drum's steam enters below the
water and bubbles through the submerged perforated sheet, which argues for fast condensation;
no RBMK value was found). A 1 s 2000 MW pulse: +1.7 (equilibrium), +3.2 (τ 1 s), +6.6 (10 s),
+7.6 kgf/cm² (frozen liquid).

**τ and V conditioned on the pre-AZ-5 record only** (TH-only 01:23:04 → 01:23:40, 1/8 of the
channels, Qg 34 MW; mean of the halves' rise, DREG 3.55 kgf/cm²):

| τ \ V (m³) | 150 | 296 | 450 |
|---|---|---|---|
| equilibrium | 3.74 | 3.41 | — |
| 1 s | 3.53 | 3.38 | 3.24 |
| 10 s | 4.23 | 3.97 | 3.67 |
| ∞ | 6.37 | 5.76 | 5.18 |

A frozen liquid is excluded; the record fixes a ridge (τ 1 s, V ≈ 150), (τ 3–4 s, V ≈ 296),
(τ 10 s, V ≳ 450) and cannot separate τ from V. The post-AZ-5 record stays an independent check.

**AZ-5 along the ridge** (band B, `…acco668…`, hsh 1.2, Qg 34 MW, full core, 10 ms; no loose
acceptances; each run's t = 0 state is its own pre-run's, k0 1.03159–1.03173, bundle powers
1.1–2.0 % rms from DONJON's):

| | 530 MW | peak | E at peak | E at 6.9 s | T-FUEL max |
|---|---|---|---|---|---|
| Newton column, fixed p (42) | 2.58 s | 230.2× at 5.24 s | 27.5 GJ | 62.7 GJ | 1974 K |
| equilibrium drum, V 296 (44) | 2.77 s | 84.7× at 5.97 s | 18.5 GJ | 30.8 GJ | 1575 K |
| τ 1 s, V 150 | 2.69 s | 96.3× at 5.80 s | 20.0 GJ | 35.2 GJ | 1646 K |
| τ 3 s, V 296 | 2.71 s | 80.0× at 5.90 s | 18.3 GJ | 30.7 GJ | 1566 K |
| τ 10 s, V 450 | 2.65 s | 88.5× at 5.81 s | 19.6 GJ | 33.8 GJ | 1620 K |

| drum pressure, kgf/cm² | rise +5 → +6 s (L) | +6 → +7 s (L) | L at +7 s | R at +7 s | core flow at +7 s |
|---|---|---|---|---|---|
| equilibrium | +0.70 | +1.40 | 69.7 | 70.5 | −9.8 % |
| τ 1 s | +1.75 | +2.31 | 72.7 | 73.3 | −9.8 % |
| τ 3 s | +1.77 | +2.73 | 72.9 | 73.6 | −8.4 % |
| τ 10 s | +2.15 | +3.58 | 74.2 | 74.8 | −8.1 % |
| DREG / INSAG-7 | +5.3 | — | 75.2 at +8 s | 80.1 | ~−40 % |

**Reading.**
1. The non-equilibrium drum is the right model form: it multiplies the post-AZ-5 rise by 1.7–3 (2.5–3.1 over +5 → +6 s, 1.7–2.6 over +6 → +7 s),
   and the left drum at +7 s comes within 1–2.5 kgf/cm² of the record's +8 s value, with τ and V
   fixed beforehand by the pre-AZ-5 rise. The +5 → +6 s jump (+5.3 recorded) is still 2.5–3×
   faster than any case, and the right drum (80.1 at +7 s, 88.4 at +8 s) is far out of reach.
2. **The peak does not move with the drum**: 80–96× against 85× at equilibrium. The fast
   pressure rise starts as the power peaks (~5.8–6.0 s), too late to collapse void before it;
   the spread between the cases follows their starting states (D-COOL minimum 0.654–0.669 at
   t = 0; τ and V also change the pre-run) more than the drum after AZ-5.
3. The core flow still falls ~8–10 % by +7 s against ~40 %. What the model misses after AZ-5 is
   therefore in the core, not the drum: more energy reaching the water (the fixed-pressure runs
   have 52 GJ by +6 s against 20–24 here), or a mechanism neither model has — fuel fragmentation
   and fuel–coolant interaction, or the channel ruptures INSAG-7 dates at +9 s and which the right
   drum's 8 kgf/cm² per second may already be showing.

**What changes for B5:** the drum is now `Drum2` with (τ, V) on the pre-AZ-5 ridge as one
conditioned uncertain input; its effect on the peak is ±10 %, below the starting state's.


## Tier B: what the post-AZ-5 record asks of the core, and the loop's effect split in four — 2026-10-22 (46)

**1. The energy the recorded drum rise needs** (`test/drum_energy_bound.jl`). The two-region drum
alone, from saturated regions (subcooled liquid would condense more: a LOWER bound), heated for
1 s by riser mixture carrying X; X solved for the model's own rise and for the record's, per loop
half, at each (τ, V) of the pre-AZ-5 ridge (45):

| per half | model's own rise | record | extra | floor: frozen liquid, V 150–450 |
|---|---|---|---|---|
| L, +5 → +6 s (+5.3 kgf/cm²) | 0.7–0.9 GW | 2.0–2.8 GW | 1.2–1.9 GW | 0.8–1.8 GW |
| R, +7 → +8 s (+8.3 from 80.1) | 1.0–1.3 GW | 3.0–3.9 GW | 1.8–2.9 GW | 1.3–2.8 GW |

In the model the core releases 12.8–15.9 GJ between +5 and +6 s (both halves), of which
~11–13 % reaches the drums within the second; the record needs ~30–40 %. An intact pellet
(r = 5.75 mm, UO₂ diffusivity ~1e-6 m²/s) gives up its heat over several seconds, so the record
asks for prompt fuel-to-coolant transfer: fragmented fuel. At the 300–350 kJ/kg the model's
hottest fuel holds above the coolant (T-FUEL 1650 K), the extra 2.5–5.7 GJ is ~8–19 t of UO₂,
the fuel of ~35–80 channels. But in this model no fuel approaches the 920 kJ/kg failure threshold
by +6 s, so the record ALSO asks for more energy deposited than the model gives — in the direction
of the fixed-pressure runs (T-FUEL 1974 K, 52 GJ by +6 s against 20–24). Channel ruptures vent
coolant into the reactor space and lower the circuit pressure: they cannot make the rise, and may
be what ended it (INSAG-7: the rupture signal at +9 s).

**2. The 76 % of (44) split** (D-A: the loop's state at AZ-5 with every channel's inlet flux and
pressure field frozen at their AZ-5 values, `freeze=:chan`, `col_step_newton_frozen` — fixed
flow, fixed pressure, as the fixed-pressure runs, but from the loop's own state; t = 0 identical
to D-B/D-C/L0, k0 1.031840):

| | 530 MW | peak | E at 6.9 s | T-FUEL max | share of ln(230/84.7) |
|---|---|---|---|---|---|
| fixed pressure, Newton (42) | 2.58 s | 230.2× at 5.24 s | 62.7 GJ | 1974 K | |
| D-A: loop state, flows + pressure fields frozen | 2.76 s | 144.9× at 5.62 s | 43.5 GJ | 1767 K | **46 % starting state** |
| D-B: channel flows free, loop boundaries frozen | 2.77 s | 108.2× at 5.94 s | 36.3 GJ | 1681 K | **29 % channel hydraulics** |
| D-C: + header, pumps, flow | 2.77 s | 89.2× at 5.95 s | 32.0 GJ | 1599 K | 19 % |
| L0: + drum pressure (equilibrium) | 2.77 s | 84.7× at 5.97 s | 30.8 GJ | 1575 K | 5 % |

**Correction to (44):** it guessed the channel hydraulics could only RAISE the peak (a channel at
fixed Δp loses flow as it voids). They lower it by 29 %. With both ends held, a voiding channel's
rising two-phase pressure drop pressurises its lower cells; in D-A those pressures cannot rise.
That is a negative void feedback through the local pressure, acting low in the core where this
excursion is driven — the mechanism is a reading, not yet shown cell by cell. The starting state
(the loop's inlet near the drum's saturation, more steam at AZ-5: D-COOL 0.645–0.748 against
DONJON's 0.734–0.754, and the loop's own power shape) is the largest single term.

**Where this leaves the excursion.** Every loop effect in this model lowers the peak (230 → 85×,
80–96× with the non-equilibrium drum), while the post-AZ-5 record needs more energy in the water
than any loop case delivers, and faster. The two are reconciled only by something the model does
not have between +5 and +7 s — fuel fragmentation with prompt fuel-coolant heat transfer (which
also raises local pressure and collapses flow, both in the record's direction: the flow fell ~40 %)
— or by a starting state with less steam than the loop's (the dominant term above, and set by the
inlet temperature, the pre-AZ-5 flow drop the model does not reproduce, and the graphite heat).


## Tier B: fuel failure criteria sourced — no case fragments fuel, and the cladding needs a boiling-crisis model — 2026-10-23 (47)

**Where 920 kJ/kg came from.** INSAG-7 p. 67: "the fuel elements begin to disintegrate at an
enthalpy of 220 cal/g UO₂ (T = 3300 K) … at 285 cal/g the fuel elements rupture, and at 320 cal/g
they explode and disperse", from "Japanese experts" (NSRR fresh-fuel pulse tests), with INSAG-7's
own caveat that RBMK rods differ. It is a DISINTEGRATION threshold, not the onset of failure; this
log had called it "fuel failure" since (24). With THM's UO₂ c_p, 220 cal/g is ~2800 K pellet
average, not 3300 K (the NSRR figures are deposited energies).

**The sourced criteria** (`sources/derived/fuel_failure_criteria.md`; [HOZ] Hózer, IGR/BIGR/GIDRA
on Zr-1%Nb VVER fuel; [NEA10] NEA/CSNI/R(2010)1), all in peak radial-average enthalpy:

| cal/g | what | for Unit 4 |
|---|---|---|
| ~120 | irradiated fuel dispersed after PCMI cladding failure | lower bound only: > 40 MWd/kgU, PWR/BWR cladding; Unit 4 ~10 MWd/kgU, Zr-1%Nb does not fail by PCMI in the tests |
| ~160 | Zr-1%Nb cladding ballooning failure, fresh and irradiated, pulses to 950 ms, no pulse-width effect | cladding breach with little fuel dispersal |
| 193–195 | failure correlations at 10 MWd/kgU | as above |
| 240–270 | rod fragmentation (fresh rods; IGR VVER: failure = fragmentation at 270) | yes |
| 285–325 | molten fuel expelled: violent FCI and pressure pulses | yes |

Cladding: 1200 °C / 18 % local oxidation design limits, 700 °C operational (TECDOC-722 Table 1).
The drum record's prompt heat transfer (46) needs DISPERSED fuel: 240–325 cal/g, not the ~160 of
ballooning. INSAG-7's 220 is not an over-estimate for that mechanism.

**Against the model** (`test/fuel_diag.jl`, every step, bundle-average enthalpy from THM's UO₂ c_p,
226.6 t of fuel; band B `…acco668…`):

| | fixed pressure (Newton) | loop, two-region drum τ 3 s, V 296 |
|---|---|---|
| peak / energy at 7 s | 230.2× at 5.24 s / 63.5 GJ | 80.0× at 5.90 s / 31.4 GJ |
| hottest bundle enthalpy | 156 cal/g (7.0 s) | 106 cal/g (7.0 s) |
| fuel above 120 cal/g | 31 t (from 5.41 s) | 0 |
| fuel above 160 / 240 / 285 cal/g | 0 / 0 / 0 | 0 / 0 / 0 |
| cladding maximum | 438 °C | 400 °C |

With the OpenMC pin peaking (1.02–1.05) the fixed-pressure case's hottest pin just touches the
160 cal/g ballooning boundary; fragmentation would need ~1.6× more local energy there, ~2.3× in
the loop case. **No case in this model disperses fuel**, so none can make the recorded post-AZ-5
drum rise — consistent with (46).

**The cladding temperatures are not physics.** THM's `CRITFL` (1.8 MW/m² in the decks) only aborts
the steady solve; in a transient there is no critical-heat-flux dryout — the wall stays in nucleate
boiling until the coolant has evaporated completely. Real hot channels in a 1–2 s excursion would
pass the boiling crisis (annular-film dryout; the critical quality and CHF correlation for RBMK bundles are still to be sourced) and their cladding
would heat by hundreds of K within a second. The 700/1200 °C check, and with it the cladding's own
failure path and the dryout's effect on heat transfer to the coolant (it REDUCES it: less energy to
the water, more kept in the fuel and cladding), wait for a CHF + post-CHF model.

**Where this leaves the question.** The record after +5 s needs ~8–19 t of dispersed fuel; the model
deposits at most ~2/3 of the fragmentation enthalpy in its hottest bundle even at fixed pressure.
Closing it needs a more concentrated excursion (the starting state, the dominant term of (46); the
local power peaking INSAG-7 quotes, Kv = 5.5 (corrected in (48); first written 5.8, an OCR misread) with a ~30× power rise, against this model's), and a
boiling-crisis model for the cladding. The next model work, in order: (1) CHF/post-CHF on the Newton
path; (2) the local peaking: where the hottest bundle sits against Kv; (3) the starting-state probe.


## Tier B: the excursion is concentrated axially as INSAG-7 has it, but too flat radially; CHF sourced — 2026-10-23 (48)

**Local peaking.** `test/shape_diag.jl`, wired into `b4_coupled.jl`, writes the power shape every step
(`b4_shape_*.txt`): Kv = max bundle / mean bundle, Kr = max channel / mean channel, Kz = max plane /
mean plane, and the adiabatic local energy ∫p dt per kg of each bundle's fuel. Bundle powers every
0.1 s from 3.5 s go to `b4_pw_*.bin`. The two (47) cases were rerun with it; their trace, fuel and
loop files are byte-identical to (47).

INSAG-7's numbers (read from the page images): Kv = **5.5** in Ref. [28], with the core power ~30× its
initial value (p. 67; **(47) said 5.8, an OCR misread, corrected**); "approximately 6.0" in all three
INSAG Models (p. 121); initial radial peaking 2.0 in Ref. [28] (p. 66). INSAG does not say at which
moment Ref. [28]'s Kv applies, nor its averaging volume; a bundle (25 cm × one channel) is used here.

| | fixed pressure (Newton) | loop, τ 3 s, V 296 | INSAG-7 |
|---|---|---|---|
| t = 0: Kv / Kr / Kz | 2.52 / 1.60 / 1.43 | same | Kr 2.0 (Ref. [28]) |
| at 30× (4.24 s / 4.79 s): Kv / Kr / Kz | 3.98 / 1.54 / 2.61 | 3.99 / 1.49 / 2.64 | Kv 5.5 at ~30× |
| hottest bundle at 30×, × the initial mean bundle | 121 | 120 | 5.5 × 30 ≈ 165 |
| at the peak: Kv / Kr / Kz | 3.54 / 1.44 / 2.48 (230×, 5.24 s) | 3.87 / 1.46 / 2.65 (80×, 5.90 s) | |
| lower-half power share at the peak | 0.909 | 0.929 | "practically all … lower part" (p. 66) |
| hottest bundle | 88 cm above the fuel bottom, r 180–310 cm | same plane, r 250–290 cm | "about 2 m" (p. 66) |
| top 1 / 10 / 100 / 1000 bundles at the peak (× mean) | 3.56 / 3.53 / 3.44 / 3.19 | 3.87 / 3.82 / 3.71 / 3.40 | |
| adiabatic ∫p dt, hottest bundle, at the peak / 7 s | 111 / 244 cal/g | 82 / 128 cal/g | |
| actual enthalpy rise there (fuel_diag) | 86 / 136 cal/g | 62 / 86 cal/g | |
| fuel with adiabatic ∫p dt ≥ 160 / 240 cal/g at 7 s | 31.0 / 0.12 t | 0 / 0 | |

What this says:
- **Axially the model concentrates the power as INSAG-7 describes** (Kz 2.5–2.8, > 90 % in the lower
  half), though the peak plane is at 0.9 m against INSAG's ~2 m (the ~35 cm-too-deep flux shift of
  (27) carried into the excursion).
- **Radially it is broad, and flattens during the excursion** (Kr 1.60 → 1.44–1.46). The top 1000
  bundles all sit within 10 % of the hottest, so the energy goes into tens of tonnes, not a few
  channels. The shape is the same in both cases: the loop lowers the amplitude, not the shape — the
  radial flatness is the neutronics and the starting state, not the TH.
- **Kv falls short by 5.5 / 3.5–4.0 ≈ 1.4–1.55**, about the factor (47) found the hottest bundle short
  of fragmentation (1.6× fixed pressure). A coincidence in size, not yet a demonstrated cause: a more
  peaked radial field changes the feedback and the total too.
- **The fuel is nearly adiabatic through the pulse**: 77 % (fixed pressure) and 76 % (loop) of the
  locally deposited energy is still in the hottest bundle at the peak, 56 % / 67 % at 7 s. Even with
  no heat removal at all only 0.12 t passes 240 cal/g. So no heat-transfer model can make this
  excursion fragment fuel; the energy has to be deposited more locally.
- **Fig. II-7** (the initial radial field, p. 120): its highest contour is 160 — if its contours are
  % of the mean, the model's t = 0 channel maximum of 160 % matches in magnitude, but Fig. II-7's
  high region is narrower and off-centre, the model's broad (a plateau of 140–150 % over the inner
  ~3 m). The text's "2.0" may be on a different basis from the figure. Digitising Fig. II-7 with its
  orientation sourced is still to do; the orientation also bears on the recorded left/right drum
  asymmetry, where the model splits power 51/49.

**CHF and post-CHF sourced** (`sources/derived/chf_postchf_correlations.md`, 13 sources in
`sources/README.md`):
- CHF onset: the RBMK designers' critical-power formula, [D] p. 70 (full-scale 18-rod, 7 m rig;
  the design-stage predecessor had 8.7 % rms error). Checked against the page image and recomputed:
  at 30 t/h, q_cr ≈ 0.66 MW/m², N_cr ≈ 3.5 MW, critical exit quality ≈ 0.28 — the dryout quality
  (47) left unsourced. Its printed subcooling coefficient 4.07 contradicts the energy balance, which
  gives 39.4 × 4.184 / 4 = 41.2 (a misprint, ≤ 2 % effect at Unit 4's near-saturated inlet). It reduces
  exactly to a local q_cr(x, G). No pressure term (fitted at ~7 MPa), no validity range stated.
  At low quality and subcooled: min(this, the 2006 look-up table × bundle factors), the table being a
  third-party transcription not checked against the paywalled primary.
- Post-CHF: the RELAP5/MOD3 set [R5V4] (Chen transition, modified Bromley film boiling with
  subcooling, vapour Dittus–Boelter, radiation), with Groeneveld–Stewart T_min if rewetting matters.
- Transient CHF: no reliable predictions or ~7 MPa data for ~1 s ramps ([TD1203] §3.7.3); at 30–100×
  nominal heat flux the crisis is unavoidable whatever the correlation, so steady CHF, ×2 as the
  sensitivity bound. Oxidation: Cathcart–Pawel / Baker–Just (Zircaloy); E110 burst and oxidation
  laws not found.

**Where this leaves the question.** The deficit is now located: energy reaches the fuel ~1.4–1.6×
too uniformly across the core radius, while the axial concentration and the fuel's adiabatic
retention are as INSAG-7 describes. CHF/post-CHF will give physical cladding temperatures and failure
modes but cannot close the fragmentation gap. Next, in order: (1) the initial radial field against
Fig. II-7 (digitise, orient, and probe a more peaked/off-centre radial start within the sourced
range, as the axial tilt was probed in (36)); (2) CHF/post-CHF on the Newton path with the sourced
set; (3) the starting-state probe of (47).


## Tier B: Fig. II-7 against the model's radial field, boiling crisis in the channels, and starting-state probes — 2026-10-24 (49)

**INSAG-7 Fig. II-7 digitised** (`tools/digitise_fig_II7.py` → `sources/derived/insag7_fig_II7_lattice.csv`; the
"radial distribution of the initial neutron field", Ref. [28]'s 01:22:30 reconstruction). Contours are
every 10 with labels every 20 (15–17 lines from the outline in to the 160 loop; an interval of 20 would
give 8); read at every fuel channel as the median count of lines to the outside over 72 rays; the field
averages 104 over the 1661 channels, so the levels are % of the core mean. Precision: one band, ~one cell.
- **Its peaking is 1.54**, the model's t = 0 channel-power peaking 1.60. INSAG's "radial peaking 2.0"
  (p. 66, Ref. [28]) is a power figure; the flux map Ref. [28] printed does not reach it.
- **Orientation decides the shape comparison.** The model's lattice is registered exactly to Fig. II-6
  (all 1888 positions); assuming Fig. II-7 is printed the same way (same reconstruction, same section):

| Fig. II-7 orientation vs Fig. II-6 | correlation with the model's t = 0 channel powers | rms |
|---|---|---|
| as printed (assumed) | 0.60 | 31 % |
| rotated 90° | **0.885** | 17 % |
| mirrored | 0.861 | 19 % |

  The model's radial field is set by the sourced 01:22:30 rod pattern on a flat burnup; that it matches
  the figure turned by 90° to r = 0.885 suggests the figure is printed rotated against Fig. II-6. Not
  decided here; both are carried.

**Radial starting states** (DONJON t = 0 dumps, generator `U4_BURNMAP`; flow valving as in the base deck
unless stated):

| state | t = 0 channel Kr | Kv | vs Fig. II-7 as printed (r, rms) | verdict |
|---|---|---|---|---|
| base (flat radial burnup) | 1.60 | 2.52 | 0.60, 31 % | matches the figure rotated 90° |
| `chess`: [PAV]'s histogram, fresh and burnt alternating | 3.47 | 5.10 | 0.05, 57 % | excluded (contradicts the figure and INSAG's 2.0) |
| `chk25`: ±25 % alternating (the most [PAV]'s 1.2–13.7 MWd/kgU spread allows) | 1.69 | 2.55 | 0.58, 32 % | channel-scale variation is smoothed by the flux: 2.0 is not reachable this way |
| `pl2p8_0p4`: planar tilt solved to Fig. II-7 as printed, re-valved to its own powers | 1.78 | 2.45 | **0.913, 18 %** | the "as printed" bracket |

The planar response is strongly non-linear (a 10 % tilt gives Kr 3.2–3.6: the radial field is near a
first-azimuthal-mode degeneracy, as in (21)); the fit is linearised from ±10 % runs and verified in DONJON.
Ref. [28]'s Kr 2.0 with Fig. II-7's flux would need fresh assemblies clustered in the high-flux region —
the unsourced placement problem.

**The tilted ("as printed") start in the AZ-5 transient** (fixed pressure, Newton, band B):
- Kv 4.94–4.96 at 3–4 s (7–37×), the hottest bundle at 184× the initial mean at 37× — close to Ref. [28]'s
  Kv 5.5 at ~30× (≈ 165×), against the base case's 3.98 and 121× at 30× (48).
- Peak **253.8× at 4.91 s** (base 230.2× at 5.24 s); hottest bundle 158.5 cal/g at 5.5 s, still rising
  (base 127 at 5.5 s, 156 at 7 s); 24.5 t above 120 cal/g at 5.5 s; adiabatic ∫p dt in the hottest bundle
  225 cal/g by 5.5 s.
- It stops at 5.30 s on the COMPO's 2000 K T-FUEL axis, and with `B4_CLAMP=1` (T-FUEL held at the axis
  end, Doppler frozen there: an upper estimate after it) at 5.56 s in a channel Newton (an iterate at
  h = −1.1e7 J/kg; the fixed-pressure path has no loose fallback, the loop path does). The end state is
  therefore not reached; the trend is ~160–170 cal/g, short of fragmentation (240–270).

**Boiling crisis and post-CHF heat transfer** (`ThmOpts.postchf`, Newton path; sources and status in
`sources/derived/chf_postchf_correlations.md`):
- CHF = min([D] p. 70 RBMK critical-power formula in local form, 2006 LUT × K1 K2); transition boiling
  Bjornard–Griffith between T_CHF and T_min (continuous at both ends, which the Newton solver needs; RELAP5's
  Chen form as printed jumps at CHF); modified Bromley film boiling + vapour convection + radiation;
  T_min Groeneveld–Stewart (411 °C at 7 MPa); of the wall roots the one nearest the step-start wall
  temperature (hysteresis). At 7 MPa, 3729 kg/m²s: 3.4 MW/m² at x = 0, 0.96 at x = 0.25; film boiling
  carries 0.1–0.7 MW/m², so the wall flux falls ~10× at the crisis.
- Two numerical fixes it needed, both only under `postchf`: THM's Zircaloy ρc_p segments are
  discontinuous at 1090 and 1243 K (joined continuously through the same vertices), and THM stores rod
  heat as c(T₁)T₁ − c(T₀)T₀, whose effective capacity c + T dc/dT is ~21× the true one in the α–β spike —
  its fixed point cannot converge there. The cladding now stores H(T₁) − H(T₀) (`zr_csec`; also alone as
  `ThmOpts.zrsec`). THM's form overstates the cladding's heat capacity by ~20 % even at 560 K.
- With `postchf` off, every result is unchanged (30-step B4 newton trace byte-identical).

Single channel (604, the base case's hottest, driven by its recorded bundle powers):

| | first dry node | cladding max at 6 / 7 s | fuel centre at 7 s |
|---|---|---|---|
| no CHF | — | 309 / 308 °C | 2238 K |
| CHF ×1 | 5.30 s | 713 / 893 °C | 2238 K |
| CHF ×2 (transient-enhancement bound) | 5.63 s | 323 / 458 °C (most nodes rewet by 7 s) | 2238 K |

Core, fixed pressure (band B):

| | peak | E at 7 s | hottest bundle 7 s | cladding max 7 s | fuel with cladding > 700 °C | dry nodes (fuel) |
|---|---|---|---|---|---|---|
| base (48) | 230.2× at 5.24 s | 63.5 GJ | 155.7 cal/g | 430 °C | 0 | — |
| `zrsec` only | 242.7× at 5.21 s | 65.3 GJ | 157.9 cal/g | 432 °C | 0 | — |
| `postchf` (+ `B4_CLAMP` after 6.0 s) | 242.7× at 5.21 s | 61.3 GJ | 156.4 cal/g | **946 °C** | **21.9 t** | 7617 (37 t) at 6 s |

- The +5 % in the peak is the cladding heat-storage form, not CHF (`zrsec` alone gives the same peak to the
  digit): heat leaves the cladding ~20 % faster, more void, earlier.
- Dryout starts at the peak (49 nodes at 5.25 s) and spreads to 37 t of fuel by 5.75 s; it lowers the
  post-peak power (−6 % energy at 7 s), since dry channels make less void.
- The cladding passes 700 °C in 22 t of fuel by 7 s, none 1200 °C. The fuel enthalpy moves −1.5 cal/g: the
  fuel is adiabatic through the pulse, as (48) said, so CHF cannot make fragmentation.
- The CHF ×2 single-channel result (458 °C) shows the cladding outcome is set by the unsourced
  transient-CHF enhancement.

**Starting-state probe** (loop, τ 3 s, V 296 m³):
- *Recorded flow imposed* (`LOOP_WREC=1`: each half's pump flow = DREG through the pre-run, the implied leg
  loss held after AZ-5): the recorded −12/−14 % needs the leg loss ×1.82 (L) / ×1.94 (R) — a large unsourced
  resistance or head loss. At AZ-5: W 5271/5198 kg/s against 5919/5951, minimum D-COOL 0.639 against 0.654,
  drum pressures unchanged. The excursion is **slower**, not faster: 3.4× at 3 s (base 4.0), 32.5× at 5 s
  (base 38.8). [to 5.1 s; run continuing]
- *Psd as gauge* (+1.033 kgf/cm²) and *Qg 26 MW*: [pending]

**Running conditions.** Another job on this machine held 35–66 GB of GPU memory all night. A memory guard
(kill my newest run if MemAvailable < 12 GB, later < 8 GB) stopped runs three times; loop runs resumed
from their 50-step checkpoints (`B4_CKPT_FILE`), fixed-pressure runs were restarted.


## Standing rules

1. **Every asserted value must come from a calculation, never from a constant chosen to
   make the assert pass.** Violating this produced the tuned `MAC:` block.

2. **Every deck must verify what it actually built, not what it was meant to build.**
   Violating this produced a CANDU-6 bundle that survived ~86 deck variants, a full audit,
   and six branch calculations before anyone measured its volume fractions. The check that
   caught it costs one run and eight lines of CLE-2000.

3. **An error message from DRAGON is a statement about the input until proven otherwise.**
   Three separate "tool limitations" were a missing declaration, a 13-character name, and a
   missing colon — each demonstrated correctly in a bundled reference deck.

4. **No physics number is validated until a second, independent method reproduces it.**
   Internal consistency is not validation: the tuned `MAC:` block, the CANDU bundle, and the
   +1957 pcm void coefficient were each internally consistent and each wrong. Rule 2 catches
   *building the wrong thing*; only an independent method catches *computing the right thing
   wrongly*. The CANDU-6 control is the template — run the new method on a case where the old
   one is trusted, before trusting the new method on the case you care about.

5. **A DRAGON `.result` is not evidence unless it postdates the deck.** Delete it before
   re-running. A stale result reporting the previous run's failure is indistinguishable from
   a real one, and it fooled this session's monitor once. Related: `cd X && cmd &` puts the
   `cd` inside the background subshell, so a following command runs from the wrong directory
   and silently does nothing.

6. **A fix that lives in a copy of the file is not a fix.** The bound-hydrogen correction
   existed as `RbmkLibH.c2m` for a full day while `rbmk_cell_a3.x2m` and `rbmk_a5_void.x2m`
   — the only two decks whose numbers were being quoted — kept calling the broken original.
   Six diagnostic decks were written against the corrected copy, which made the fix look
   applied. Correct the file everything calls; if a deliberately-wrong variant is needed for
   a comparison, that is the one that gets the new name and the do-not-use banner.

7. **A cache without a key is a silent substitution.** A derived artifact kept beside its
   source must carry a digest of that source in its name. The decompressed draglib sat in
   the `libraries` submodule for five days after the submodule moved to a different library
   revision, and every run preferred it because it was already there — see the 2026-09-24
   entry. "The file is already there" is not evidence that it is the right file.

---

*Last updated: 2026-10-24 (49) (INSAG-7 Fig. II-7 digitised: peaking 1.54 against the model's 1.60, and the model's radial field matches it rotated 90 degrees (r 0.885), not as printed (0.60); a planar burnup tilt fitted to it as printed gives Kv ~5 at 7-37x as Ref. [28]'s 5.5 at ~30x, a peak 254x at 4.91 s and the hottest bundle at 158.5 cal/g by 5.5 s; boiling crisis and post-CHF heat transfer in the channels: dryout from the peak over ~37 t, cladding to 946 C (22 t above 700 C), fuel enthalpy unchanged; the recorded pre-AZ-5 flow drop needs the leg loss doubled and makes the excursion slower; gauge/Qg probes pending). Previously: 2026-10-23 (48) (local peaking: the excursion's axial concentration matches INSAG-7 (Kz 2.5-2.8, >90 % in the lower half) but it is radially flat (Kr 1.44-1.60, Kv 3.5-4.0 against Ref. [28]'s 5.5 -- not 5.8 as (47) said), and the fuel is nearly adiabatic through the pulse, so the fragmentation shortfall is where the energy is deposited, not heat transfer; CHF sourced: the RBMK designers' critical-power formula ([D] p. 70, critical exit quality ~0.28) and the RELAP5/MOD3 post-CHF set). Previously: 2026-10-23 (47) (INSAG-7's 220 cal/g is a disintegration threshold from NSRR fresh fuel, not failure onset; sourced criteria: Zr-1%Nb ballooning ~160 cal/g (IGR/BIGR, long pulses), fragmentation 240-270, violent FCI 285-325; the hottest bundle reaches 156 cal/g at fixed pressure and 106 in the loop, so no case disperses fuel; the model has no critical-heat-flux dryout, so its cladding temperatures (<= 438 C) are not physics -- CHF/post-CHF is the next model need). Previously: 2026-10-22 (46) (the recorded post-AZ-5 drum rise needs 2.0-2.8 GW (L) and 3.0-3.9 GW (R) per half reaching the drum, against the model's 0.7-1.3: ~30-40 % of the released energy in the water within a second, which needs fragmented fuel (~8-19 t UO2) and more energy deposited than the loop model gives; the loop's 230x -> 85x split: starting state 46 %, channel hydraulics 29 % (negative, correcting (44)), header/pumps/flow 19 %, drum 5 %). Previously: 2026-10-21 (45) (a two-region non-equilibrium drum (vapor and liquid regions at one pressure, condensation on the subcooled liquid with time constant tau); the pre-AZ-5 record excludes a frozen liquid and fixes a (tau, V) ridge from (1 s, 150 m3) to (10 s, 450 m3); along it the post-AZ-5 drum pressure rises 1.7-3x faster than at equilibrium and the left drum at +7 s comes within 1-2.5 kgf/cm2 of the record, but the peak stays 80-96x (85x at equilibrium) because the fast rise starts at the peak; the core flow still falls only 8-10 % against ~40 %, so what is missing after AZ-5 is in the core, not the drum). Previously: 2026-10-21 (44) ((43)'s numbers retracted: graphite heat entered 28x low and feedwater cooled twice; corrected, the pre-AZ-5 record constrains the steam volume to ~150-450 m3 per half (mean of the halves; 600 mm main steam lines in both designs, so Ignalina's 404.7 is not scaled by power); AZ-5 with the corrected loop: 530 MW at 2.77 s, peak 84.7x at 5.97 s, 30.8 GJ at 6.9 s, against 230x / 62.7 GJ at fixed pressure; decomposed: starting state + channel hydraulics 76 %, header/pump/flow dynamics 19 %, drum pressure rise 5 %; the steam volume moves the peak by 1 % and does not explain the recorded post-AZ-5 pressure rise, which is 3-6x faster than the model's even at 0 m3: too little energy reaches the water, or an equilibrium drum is too stiff). Previously: 2026-10-20 (43) (the B3b-3 core-wide loop model: drums, pumps, legs and all 1661 channels with their own lines; from 01:23:04 to AZ-5 the drum pressures follow DREG unfitted (+2.7 kgf/cm2 vs +2.9/+4.2) but the recorded -12/-14 % flow drop is not reproduced (model -1 %) for any head curve; graphite heat 26-40 MW, steam volume 296 m3, run-down pump speed inferred from the DREG flows; AZ-5 with the loop: 530 MW at 2.69 s, peak 110x at 5.78 s against 230x fixed-pressure, energy at 6.9 s -39 %, but the post-AZ-5 drum pressure rise is 5-6x slower than recorded and the flow falls 11 % against ~40 %, so the loop is not yet the better estimate of the peak; four Newton-path closure non-smoothnesses fixed). Previously: 2026-10-19 (42) (the DREG tape record puts the 01:23 drums at 63-68.6 kgf/cm2, ~10 below the decks' 75.3, which was INSAG-7's +8 s value; band B at 66.8: peak 245x vs 183x (+34 %), energy at 6.9 s +20 %, 530 MW unchanged; a loop mixing model with the recorded feedwater and pump heat reproduces DREG's 281 C pump-inlet temperature and puts the core inlet at the drum's saturation temperature, so INSAG-7's 3 C is a core-bottom figure; sources found: DREG, Mochizuki 2007, Ignalina Source Book). Previously: 2026-10-18 (41) (B4 passes on all five band cases with the THMTRS port, 530 MW identical, peaks within 1.4 %, energy within 4.5 %, but A and flow x0.85 stop after their peaks in THMTRS's flow fixed point; B3b: shooting on the inlet flux fails structurally near saturation (gain (dz/dt)^2 drho/dp per boiling cell), so the channel is solved by a simultaneous Newton, which needed four THM closure non-smoothnesses fixed on its path (local Saha-Zuber onset, inner tolerances, sticky KWA wall root, prop_pT at Tsat); single channel dt-converged, 3-4 iterations; band A coupled runs to 6.91 s, past THMTRS's 5.86 s and DONJON's 6.85 s, peak 75.97x vs 78.29x, post-peak within 0.3 % of DONJON). Previously: 2026-10-18 (39) (Tier B: RT0 kinetics null 1e-11, Δt-halving peak −0.91 %; the DONJON band's KINSOL default EPSOUT 1e-4 biases the frozen-TH peak by ~6 % (at 1e-7 DONJON = RT0 to 1.5e-6..1.4e-5); THM: port = DONJON THM (T-FUEL rms 0.0045 K); GPU RT0 = CPU to 1e-11, ~20x faster; pure-Julia IF97 = freesteam to 6e-13; B4 coupled band B: 530 MW at 2.59 s both, peak 182.75x vs 181.66x, energy to peak -2.8 %). Previously: 2026-10-18 (38) (Tier B begins: B0 cross-section export reproduces NCR to 2.4e-7; B1 element cross sections reproduce MACRD to 1.3e-7; FD reproduces MCFD 1 exactly but differs from the reference DUAL 1 1 by -423 pcm and is not reconciled by refinement, because the CPS cross sections are SPH-equivalenced on DUAL 1 1 at 25 cm; a Julia RT0 mixed-dual solver reproduces DUAL 1 1 to -0.01 pcm and bundle powers to 0.018 %; B2 kinetics null transient 6e-6). Previously: 2026-10-16 (37) (patch 0015 drift-flux floor at stagnation; the bottom-tilted case now runs to 7 s: 418x at 4.42 s, 106 GJ, hottest bundle 656 kJ/kg; B and the top tilt also reach 7 s, peaks unchanged; OpenMC rod peaking 1.02-1.05, so the hottest rod is ~680 kJ/kg, not 920; the DONJON band is now the Tier B reference set). Previously: 2026-10-15 (36) (A8 through the excursion: the 4.38 s "dry out" was the Saha-Zuber profile fit evaluated below its net-vapour point (x = 1 for subcooled water), not a boiling crisis -- (35) corrected in place; five transient-only THM defects fixed (0009 uncooled slice no longer aborts, 0010 fit only above the net-vapour point, 0011 local fit quality in a transient, 0012 donor-cell energy faces under reversed flow, 0013 adaptive and in-march flow relaxation with the mass-flux error against the inlet flux), found by replaying single channels from the core run (3.5 s against 3 h) and screened over all 1661 channels to zero failures; 0014 NCR CLAMP (opt-in); the band: B 182x at 5.32 s, A 78x, flow x0.85 228x, initial shape tilted +-10 % 418x / 8x -- all cross 530 MW at 2.3-3.1 s, the INSAG-7 Model 1 "~80x" is Fig. II-11's 4.94 x 3200 MW, and the band contains all three INSAG-7 models; no case reaches 920 kJ/kg in the hottest bundle, Kv 3.9-4.2 against ~6). Previously: 2026-10-10 (35) (gap 2 closed: the CPS COMPOs rebuilt so the core-equivalent supercell carries OpenMC's absorber and displacer worth (f_ABS 0.8026, f_DSP 1.2016); with the t=0 inversion redone the static positive scram is +511 pcm = +0.97 $ against +0.53 $; the 7 s transient now runs away -- 5x at 3 s, 20x at 4 s, 37x at 4.38 s when the hottest channel reaches dryout -- passing 530 MW at 2.59 s with a sub-second period, the 01:23:43 signals INSAG-7 says none of its three models reproduced; rod-driven, TH feedback net negative; gap 1's rod pattern already matches the 01:22:37 record; gap 3 narrowed to a source question). Previously: 2026-10-09 (34) (status summary: what A8 reproduces, the surge it does not, and the three gaps in order -- initial state beyond the axial shape, CPS-channel worth, void worth). Previously: 2026-10-09 (33) (at 1 C the TH feedback is nil, frozen/fb within 0.5 %, and the smaller surge is the starting state: the t=0 shape moves 1.4 points of power share upward and the frozen peak falls 2.18 -> 1.33; zone void worths by a new export/edit/re-import tool, exact round trip, all positive, bottom zone ~1/3 (B) to 1/5 (A) of mid-core per unit phi^2, partly end-zone leakage; INSAG-7 flow fell 10-15 % by AZ-5 (U4_QFRAC): peak 1.976 -> 1.955 (0.90) -> 1.926 (0.85); drum pressure was rising, IPRES=0 already bounds bottom subcooling, no pressure patch). Previously: 2026-10-08 (32) (the 1 C abort was THMH2O taking REL**0.8 of a NEGATIVE Reynolds number after a continuity-driven flow reversal at the outlet of low-flow peripheral channels, NaN hidden as a 273.15 K wall by MAX; patch 0008 evaluates the correlations at |G|, upstream-identical for G>0, channel_mphy regression unchanged, no 3 C run affected; the 1 C transient now runs to 7 s and peaks LOWER, 1.326 at 4.35 s against 1.976, ratio 0.68 from 4 s on, although the lower half boils to 2.8 %; initial-state vs feedback not yet split). Previously: 2026-10-08 (31) (bracket B built as _ACompoVB and gated: core void worth 2.35 -> 3.22 beta, power coefficient -3.0 -> +2.7 pcm/100 MW (~+0.5e-4 beta/MW vs INSAG +0.6e-4); in the transient B changes nothing (<= 0.009 %) because the lower half never boils within 7 s even with 95 % of the power there, so the limit is thermal-hydraulic; per-bundle xenon from the measured t=0 shape, with two defects fixed (a6b_xenon started every channel at core-average equilibrium; ECHO buffer overflow past 9999 deck lines, patch 0007); the xenon-aware burnup fit (rms 0.0201) is nearly the burnup-only one, bottom 0.517 -> 0.538; a 1 C subcooling transient aborted at 2.01 s in THMTRS, to diagnose). Previously: 2026-10-07 (30) (TH check: the 01:23 steady state puts steam only in the top 3-4 bundles, matching INSAG-7 p. 64 and the energy balance (17.4 kJ/kg rise vs 16.2 kJ/kg subcooling); +50 % power adds void only in the upper half, so the lower-half boiling INSAG-7 describes must come from the transient shape shift or the inlet pressure (IPRES=0 here; Malko gives 8.2 -> 7 MPa); the core void worth of the 01:23 state is +1242 pcm = +2.35 beta against ~5 beta sourced (INSAG-7 p. 83, p. 36; Malko); no further burnup data found; next: bracket B as a corrected COMPO, a transient void dump, xenon/burnup separation, IPRES=1 + coastdown). Previously: 2026-10-07 (29) (AZ-5 in 1986 did NOT drive the 21 bottom-entry USP rods (INSAG-7 p. 46); with them held (U4_MOVGRP=12) the static ramp from the fitted state is positive from ~50 to ~290 cm, +281 pcm = +0.53 $ at 160 cm, matching INSAG-7 p. 39 (ORM 7: inserted reactivity positive for the first 8 s); the coupled 7 s transient dips to 0.714 and rises to 1.976x at 4.43 s, 5 ms and 10 ms agree to 0.7 %, and the Fig. II-9 peaks are now 2.49/2.74/2.86 against 2.49/2.67/2.80; the surge stays small against 3.5-80x because the net feedback is NEGATIVE (-17 % at 7 s against a frozen-TH 2.18x peak), and statically the 01:23 state has a power coefficient of -3.0 pcm per +100 MW (Doppler -19.5, void +16.5) = -0.57e-4 beta/MW where INSAG-7 p. 3/p. 36 says positive, up to +0.6e-4; next: bracket B, the burnup-only axial inversion lowering the bottom void worth, and the coastdown/zero-subcooling inlet). Previously: 2026-10-07 (28) (A8.3: THM feedback inside the kinetics loop from the sourced 01:23 TH state (200 MW, 56 000 m3/h, 3 C subcooling). Three THM patches: 0004 bounded history (77 GB otherwise), 0005 counted limit-cycle acceptance, 0006 density under-relaxation, because THMTRS's flow fixed point has gain ~1/(dt G) and diverged in a 1.33 m/s channel. Timestep converged to 0.03 % at 5 ms. The 7 s AZ-5 run reproduces the first-second reactivity drop and the shift of the flux to the bottom (Fig. II-9 4/6/7 s rms 0.21/0.20/0.26), but power falls to 0.11 by 7 s with feedback +0.4 %, against INSAG-7's 3.5-80x surge; candidates are the CPS water/graphite worth, bracket B, the pump coastdown and the 01:23:40 rod pattern). Previously: 2026-10-06 (27) (INSAG-7 Fig. II-9 digitised; its t=0 axial flux inverted by Levenberg-Marquardt to a per-bundle burnup profile, rms 0.020, cosine-like; from that state, rods advanced at the sourced 40 cm/s reproduce the measured 4/6/7 s shift of the flux peak to the core bottom, peaks 2.34/2.70/2.90 against 2.49/2.67/2.80 and about 35 cm too deep, with no TH feedback; the static ramp stays negative, with +63 pcm added between 40 and 80 cm, so the excursion needs void feedback, A8.3). Previously: 2026-10-06 (26) (AXIAL PROBE: per-bundle burnup through INST-BVAL BUND; the AZ-5 static ramp sign follows the axial flux peak, +358/+408 pcm at 80 cm bottom-peaked against -1408 pcm top-peaked; the core is axially near-degenerate; corrected (24)/(25), which wrongly called the 01:23:40 field bottom-peaked, since INSAG-7 II-5/II-9 show it double-humped with an upper maximum). Previously: 2026-10-05 (24) (A8 STARTED AND THE RODS NOW MOVE: all 211 CPS rods are built as 389 single-part DONJON ROD-DEVICES, two per rod because the real rod is 10.75 m and DEVGET: rejects a MAXPOS outside the 8 m mesh, which independently dodges MOVPOS.f:159 truncating ROD-POS and makes the whole scram three MOVDEV: statements; the gate is exact, with the base map and the device route agreeing to SEVEN FIGURES in k at the sourced 01:22:30 pattern and at every rod 24 planes in, -10 300 pcm apart; the null transient holds power to 2.2e-6; KINXSD.f:168-170 divides the fission cross sections by k_eff so the transient starts exactly critical and the absolute eigenvalue is DIVIDED OUT, which is the quantitative reason A8 is a difference; FOUR bugs, none found by reading the deck -- DEVINI: must precede RESINI: or the device cross sections are silently zero and the fission records mis-strided, U4_RODS=wat is not an unrodded core so 36 AZOC displacers were double-counted into a negative removal cross section, and the rod position formula has FIVE copies in Donjon/src all using the X-axis limits whatever AXIS says, of which patching two was enough to make every static deck exact and the gate pass while producing A FAKE 9.3 % POWER RISE that was absorbers being deleted from the core, retracted and caught by a static anchor added for another purpose; the fifth bug was mine, ILIM computed from uninitialised IAXIS, caught by the patch-invisibility regression our own decks could never have caught; and the RESULTS: the 1 s transient falls monotonically to P/P0 0.86929 with its static anchor exact, the TIMESTEP IS CONVERGED (halving dt moves P/P0 by -0.19 %, which is 4.4 % of what the prompt-lifetime sweep alone spans, so dt=10 ms is adequate for this slow ramp and a 4 s scenario costs 44 min), point kinetics driven by the measured ramp agrees to 0.0271 in P/P0 at 1 s against a Lambda spread of 0.0386 -- so the residual is INSIDE the model's own uncertainty and is NOT evidence of a spatial effect, the honest reading being that a symmetric whole-core scram is point-kinetic and the accident's spatial content lives in the INITIAL state rather than the rod motion; the AZ-5 ramp is NEGATIVE in this state, 0 to -293 pcm over the first metre, monotonic, decomposing at 40 cm into absorbers -51.7, displacers -20.5, USP -11.2 against -72.2 together and -83.5 summed, so 14 % sub-additive -- which is exactly what gate A6.5 predicted with the condition it attached, since the displacer sweep only turns positive once the axial peak is below the mid-plane and this core peaks at bundle 14 of 28, making the positive scram a property of the AXIAL FLUX SHAPE and not of the rod geometry; the ramp also carries a sawtooth with the 25 cm axial mesh period because every rod starts on a plane boundary and all 389 tips cross together, so the mesh bounds rod-motion resolution as much as the timestep does; KINSOL: costs 6.6 s/step with TRIVAA at 30 ms and NEWMAC at 15 ms, so 44 min for 4 s at dt=10 ms; and both remaining unsourced A8 inputs were in sources already on disk -- fuel failure at 220 cal/g UO2 = 920.5 kJ/kg from INSAG-7 p. 67, and p. 69's statement that a 20 % change in initial power density moves the published answer between 31x and 64x, which is INSAG-7 independently asserting that the initial-state uncertainty dominates; and A8's remaining work is not solver work -- RESPAR.f:518-531's INST-BVAL BUND takes a burnup per channel PER BUNDLE and is unused, so the bottom-peaked axial flux that decides the sign of the scram is a capability that exists and has not been fed, the sourced basis being INSAG-7 Figs. II-7/II-8). Previously: 2026-10-05 (21) (the A6d segment closed and the project reached the A8 boundary: the burnup PLACEMENT is the largest unknown in the model at up to +10 860 pcm across orderings of [PAV]'s histogram and is undecidable from the sources, since iterating the refuelling rule diverges; the 01:22:30 rod pattern is built per rod and worth only -110 pcm, 2.3 pcm per rod, which is the operating-margin problem arrived at from geometry; the xenon LEVEL is solved from the sourced history at 1.039x equilibrium (-2352 pcm) with every constant read out of the COMPO's own DEPL-CHAIN, and the FIELD costs mixtures rather than an axis (U4_XEBINS, byte-identical at 1 bin and bit-identical k at 4 identical bins) -- xenon is a genuine flattening agent, worth -16 % on the peak channel, because at 200 MW Xe tracks the iodine left by the PAST power shape; the naive field iteration DIVERGES and under-relaxation at 0.35 is physics, not convenience; a full-power-equilibrium field flattens the same spread to 0.2 % while costing -73 pcm against -193, which FALSIFIED my own 3.4x sensitivity prediction; and the rod pattern was solved for by a 1661 x 190 response matrix -- the response factorises (fixed direction, cosine >= 0.9975, times one universal amplitude curve), 92 % of the rods' authority is the FIRST AZIMUTHAL MODE with no class escaping it, and sequential linear programming with a trust region on total rod worth descends 2.7702 -> 1.7791 -> 1.7419 -> 1.7226 with every step verified in DONJON, which lands 3.7 % outside [D]'s ceiling and therefore RETRACTS the chequerboard verdict of (17)/(18) to marginal rather than falsified; the unconstrained LP had promised 1.4369 and DONJON returned 2.8285, worse than its own starting point, because the combinations that cancel m = 1 are exactly the ones that park the core between near-degenerate modes -- the control is most useful where it is least linear; and section (21) records the decision that A8 does NOT wait for the placement, which enters as a band the way the void bracket does, because A8 is a difference and the differences are the robust numbers here). Previously: 2026-10-03 (12) (the burnup rebuild landed: 12 nodes / 1728 points in 18.1 h, round trip 1.6 pcm, BU 0 unchanged at 1.313968, and the core's own burnup interval now measured at +8.7 pcm on an axis that had never been tested -- the A6d blocker is cleared where it matters; refining the depletion grid removed a systematic 20-29 pcm step error the previous grid still carried; re-running A7 moved absolute k by -20 pcm and every feedback by <= 2 pcm, which says the differences are robust and the eigenvalue is the fragile number; and the burnup gate point was badly chosen -- 250 MWd/t is where the curve is steepest but [PAV]'s lowest group is 1200, so the 1341 pcm it reports belongs to a state the model never evaluates, the same mistake the TG axis was caught making one day earlier). Previously: 2026-10-02 (11) (A7 converges, and the thing that does not is a switch: last night's ERMAXT diagnosis was WRONG -- bit-identical k means bit-identical power and therefore a residual of exactly zero, so a plateau is a limit cycle, and it is K0, the integer boiling-onset node index set by the Saha-Zuber test at THMH2O.f:383 and gating the two-phase block at :147, with DTSUB depending on heat flux so the switch sits inside the Picard loop; proved by pinning the density, which drops the residual to 0.031 K and dk to exactly zero; k bit-identical at RELAX 1.0/0.5/0.2 so the loop now converges on the eigenvalue; the loop also deleted FLUX on its last pass, so the power-shape block had NEVER run and every A7 run died with kernel error 666 after printing its results; converged feedback Doppler -227, density +306, net +80 pcm; first power shape, peaking 1.8289 -> 1.5719, peak channel 3517 -> 3022 kW; all four flow x feedback cases converge, so the flow-distribution spread is measurable for the first time at 59.4 pcm, while the two density-pinned cases agree to 0.5 pcm). Previously: 2026-10-02 (10) (the 1152-point COMPO landed in 9 h 33 min, round trip 1.3 pcm over 12 nodes including the two newly added axis values, off-grid 30.4 pcm -- and the axis decomposition attributes 31.1 of it to TG alone against 1.0 for DCA and 0.4 for TF, so the two axes just widened are free and the gate had been measuring an axis the core pins on a node; CUBIC rejected on measurement at -48.3 pcm; TWO untested things found: dk/dTG is +400-450 pcm per 100 K and the TG axis stops below operating temperature, so pinning it biases the core ~+500 pcm and today's core k is not an eigenvalue; and the burnup axis, interpolated in every core calculation ever run here, is off by +2099 pcm at 500 MWd/t because the equilibrium xenon knee falls inside the first node interval -- the core's own 10 900 is flat at 2-3 pcm but [PAV] puts 10.4 % of the core at 1.2 MWd/kgU, ~+1170 pcm each, a hard A6d blocker). Previously: 2026-10-01 (9) (A6b scoped down and the COMPO rebuild launched: the xenon AXIS turns out not to be needed at all -- Xe135 and I135 are in the stored MICR list and NCRLIB.f:268 lets NCR: MICRO replace their densities before rebuilding the embedded macrolib, so a xenon field costs a clause and no rebuild -- which leaves A6b's COMPO work as just the two A7b axis widenings; 1152-point rebuild running, ~10 h, with the working 840-point database preserved; DRAGON's -p does nothing for this deck, 118.15 s at 1 thread against 118.18 s at 8). Previously: 2026-10-01 (8) (A7b: the coupled Picard loop runs and converges geometrically at r = 0.40, Doppler feedback worth -240 pcm, extrapolated k = 1.036471 -- and then stops because the A5b MULTICOMPO's branch axes are too narrow for a real core at BOTH ends: DCA tops out at 0.72 g/cm3 where the subcooled inlet is 0.778, and TF floors at 600 K where a low-power channel end sits at 586 K; both are one more value on an existing axis and both go into the A6b rebuild, with the DCA pin priced at 103 pcm upper bound). Previously: 2026-10-01 (7) (A7a: one fuel channel against [D] p.95, the project's first comparison against anything but another code -- outlet temperature 289.47 against 289.3, exit quality 16.50 % against a published 19.6 % that lies OUTSIDE the box [D]'s own power and flow ranges allow, so the model closes its own energy balance to 1.2 % and the residual is the source's internal inconsistency; two THM: default traps found (Bowring's XFL never reverts to the thermodynamic quality, SET-PARAM addresses by P-NAME and needs SAME for a LOCAL parameter); the equivalent CLUSTER pitch resolved by measurement, since the hydraulic diameter reaches nothing compared once the surface is boiling; the centreline gap inverted to a gap conductance of ~1700-2800 W/m2/K that the sourced 100 um gap independently supports). Previously: 2026-10-01 (6) (Phase 2b: THM: patched for per-channel inlet velocity -- SPEED CHAN <list> through the existing THMINP, with the scratch copy THMDRV's self-overwrite demands; proved invisible when unused (2 597 833 comparable lines of channel_mphy.x2m, 0 differences) and provably per-channel when used (fuel temperature falls monotonically with velocity across four channels); the patch lives in patches/ because 5.1/ is gitignored, applied idempotently by tools/apply_patches.sh from bootstrap). Previously: 2026-10-01 (5) (gate A6.5 measured: the graphite displacer is worth +2060 pcm against a water column, and the first 1.25 m of rod travel is -175 pcm with a centre-peaked flux but turns POSITIVE, up to +177 pcm, once the axial peak is driven below the mid-plane -- the sign tracks the peak in both directions, so the gate's mechanism is present and conditional exactly as the gate states it; that puts A6b (xenon) and A6d (burnup placement) on the critical path to A8 by measurement). Previously: 2026-10-01 (4) (A6.5: the Unit 4 core deck solves the whole chain for the first time -- NCR: x2 -> MACINI: -> DUAL 1 1 -> FLUD: -> FLPOW: on real cross sections in every mixture, k = 1.018278 reported not asserted, 8.1 s; the stack boundary closes a third sourced count exactly (156 cooled reflector channels); the radial reflector is worth 131 pcm and only 2.6 pcm leaks past it, which closes the Phase 1b question -- the 7152 pcm strip error does not propagate). Previously: 2026-10-01 (3) (Phase 1b: reflector geometry sourced and closed three ways; OpenMC shows DRAGON's OPEN-BOUNDARY solution is wrong by 2-5x here, which retracts the earlier 'diffusion cannot do reflectors' conclusion -- no published result is affected, all are reflected; closing the supercell avoids it and leaves 7152 pcm on a test that over-weights the reflector; SPH fails in seven variants). Previously: 2026-10-01 (superposition test: the A6.4 environment effect is the SPH factor, spanning 1.00-1.56; sub-additive and not a function of the eight-ring count, so a continuous environment axis is viable but weeks of work; two read-out bugs corrected, k-based conclusions unaffected; radial reflector sourced at 3+1 rings from [BEH96]). Previously: 2026-09-30 (2) (A6.4b disproved: no rod-only SPH equivalence can close gate A6.4,
shown by a ±20 % factor sweep that never reaches the gate; the cause is the rod perturbing its
neighbours' spectrum by ±3 % at zero burnup, not the rod cell itself; carried as a measured
one-signed bias). Previously: 2026-09-30 (Phase 0 of the transient: `KINSOL:` runs on the full core for the first time; a severe step costs 0.430 s against 0.090 s frozen, so A8 is hours not days and Tier B stays parallel; `OVERV` and `TRIVAA: UNIT` found to be undocumented prerequisites). Previously: 2026-09-29 (A6.3 table complete, gate missed at 5-12 %; MCFD 1 shown to lose 31-34 % of absorber worth and to be unable to carry an SPH equivalence at all, while DUAL 1 1 costs 8 %; the thermal-scattering interpolation hypothesis for the WAT residual eliminated by measurement; Unit 4 core geometry and 1661-channel fuel map generated from the sourced map and accepted by DONJON; recommendation recorded against porting out of Fortran). Previously: 2026-09-27 (A6: CPS cells built and verified in both codes; A6.3 gate missed, residual carried as the A′ correction; A6.4 homogenisation exact but neighbour data 7–10 % low, closing via a rod-cell equivalence; A6d Unit 4 channel map sourced by registering two digitisations, all counts closing; fuel COMPO rebuilt on the corrected depletion grid, bracket +1.94 / +2.41 / +2.72 $ at 10.9 MWd/kgU). Previously: 2026-09-26 (2) (project assessment; Tier A reordered: A6 → A6b Xe → A6c Smolensk-3 → A6d initial state → A7–A9). Previously: 2026-09-26 (Phase C: SHEM-361 + Zr SS production, 840-point COMPO, void bracket +1.95 / +2.42 / +2.72 $ at 10.9 MWd/kgU; depletion step study). Previously: 2026-09-25 (3) (Phase A–B on the GB10: void gap within criterion on both cells; nominal 240 pcm residual attributed; burnup-normalisation convention found; 8× mesh and accident reference pending). Previously: 2026-09-24 (4) (re-baselined in both codes on the closed geometry; the
bracket straddles prompt criticality at the accident burnup, ~0.6 $ DRAGON vs ~2.7 $ OpenMC;
OpenMC β_eff 0.006739 confirms DRAGON to −1.3 %). Previously: 2026-09-24 (3) (cell geometry closed against eight new sources; clad OD 13.58;
k∞ 1.304123 on the pinned library; Unit 4 accident burnup 10.9 MWd/kgU, not 20 — the bracket
needs re-framing). Previously: 2026-09-24 (repo restructured for a clean clone; found that every DRAGON
number below was produced against a draglib the repo does not ship — −87 pcm on the A3 cell,
re-baseline pending — see the 2026-09-24 entry). Previously: 2026-09-23 (3) (A5b full 630-point COMPO built and verified: round trip
6.4 pcm worst, off-grid interpolation 27 pcm worst, β curve 0.006824 → 0.004680 measured and
confirmed against OpenMC to −0.5 %; full-void worth at discharge +4.7 $ (DRAGON) / +8.6 $
(OpenMC) — prompt-supercritical at both ends of the bracket)*
