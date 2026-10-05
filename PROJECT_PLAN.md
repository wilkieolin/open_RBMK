# RBMK-1000 Coupled Neutronics/TH — Project Plan

> **Draglib caveat (2026-09-24).** Every DRAGON number in this document was measured
> against a draglib that is not the one the `libraries` submodule pins — a decompressed
> leftover from an earlier revision that the `.access` hook preferred because it was
> already on disk. The offset is −87 pcm on the A3 cell (1.310172 → 1.308679). The hook is
> fixed; the numbers are not yet re-baselined. See the 2026-09-24 entry in `PROGRESS.md`.


> **Rewritten 2026-09-22 after an audit.** The previous plan's Stage 4 blocker (SPH
> homogenization) was a misdiagnosis, and its priority list was aimed at the wrong problems.
> Full audit: `EVALUATION.md`. Current work order: `TIER_A_WORKPLAN.md`.

## Objective

A 3-D spatially-resolved coupled neutronics/thermal-hydraulics RBMK-1000 model driving a
historically accurate **RBMK mnemonic display** — 1661 channel outlet temperatures, 211 rod
positions, in-core detector readings — in real time, capable of reproducing the Chernobyl
accident conditions including the **AZ-5 positive-scram transient**.

**Scope boundary:** the scenario runs to **fuel failure** and stops. Fuel disassembly, the
steam explosion, and core destruction are out of scope (they require MELCOR or RELAP-SCDAP).

## Why spatial resolution is mandatory

The RBMK's neutron migration length (~1 m) is small against its 12 m diameter, so the core is
weakly coupled and behaves as semi-autonomous regions. That is the origin of its
first-azimuthal-mode xenon instability and of the local excursion that initiated the accident.
A point-kinetics model would not merely miss panel detail — it would miss the phenomenon that
made the accident possible. The mnemonic panel exists *because* the reactor was spatially
unstable.

---

## Architecture

| Tier | Contents | Runs |
|---|---|---|
| **A — offline physics** | DRAGON5 lattice cells → MULTICOMPO → DONJON5 3-D steady state + reference AZ-5 `KINSOL:` transient + `DETECT:` traces | minutes–hours per case |
| **B — online engine** | Standalone 2-group nodal/FD diffusion, 6 delayed-precursor groups, 1-D per-channel TH. GB10 GPU. Reads Tier A cross sections; validated against Tier A. | kHz target; shape ≥10 Hz |
| **C — mnemonic panel** | Channel temps, rod positions, detector signals with SPND response lag | display rate |

**DONJON cannot be the live engine.** It is single-threaded with no GPU path, and one shape
solve is 0.2–3 s — enough for channel temperatures at ~1 Hz, but it would step straight over
the ~4-second excursion that is the point of the scenario. Tier A is what makes Tier B
trustworthy, not what runs the display.

Working-set estimate for Tier B: 67 k nodes × 2 groups ≈ a few MB, plus ~1.6 MB of precursors
and a smaller TH state. Well under 100 MB — no memory risk on the ~110 GB budget.

---

## Roadmap

### Tier A — offline physics (current work; see `TIER_A_WORKPLAN.md`)

| # | Task | Gate |
|---|---|---|
| A0 | Environment + regression baseline | `iaea3d_fuelmap.x2m` → 1.028980 |
| A1 | Quarantine fabricated artifacts | tree contains no tuned-`MAC:` or invented-syntax decks |
| A2 | Run the corrected core | ✅ **done 2026-09-23** — 49×49×32, 1225 × 1225 × 800 cm, 76 832 regions, converged, **k_eff = 1.123062** on IAEA 2-group constants (geometry/solver check only). `FLUD:` **1 s** at `MCFD 1` vs 729 s at `DUAL 3 3`. Three other generators still carry PITCH in metres. <br>**Solver superseded 2026-09-28:** `MCFD 1` loses 31–34 % of absorber worth once a rod cell exists and cannot carry a converged SPH equivalence at all. Production is `DUAL 1 1`, which is **not** `DUAL 3 3` — 2.11 s / 56 MB against MCFD's 1.95 s / 39 MB on this same core, agreeing to 0.7 pcm with no absorber present. |
| A3 | Lattice cell on **RBMK** dimensions + `USS:` + volume-fraction guardrail | ✅ done — **k∞ = 1.313968** on the production SHEM-361 + Zr-SS library (2026-09-26); history: **k∞ = 1.310172** (post bound-hydrogen fix, 2026-09-23; 1.3128 before it); graphite 89.6 %, coolant 3.77 % asserted in-deck |
| A4 | SPH homogenization | ✅ resolved — **not applicable at cell level** (`SPHDRV: INVALID NUMBER OF MACRO-REGIONS`); moved to the core reflector and rod cells |
| A5a | Depletion (`EVO:`) + void branches vs burnup | ✅ **closed 2026-09-26** by the method-convergence segment (`METHOD_CONVERGENCE_PLAN.md`): converged DRAGON and matched OpenMC agree within the plan's criteria; full voiding at 10.9 MWd/kgU is +2.4 to +2.75 $ in every variant. *History:* ⚠️ **half-passed.** Sign and burnup trend confirmed independently by OpenMC; **magnitude is not** — OpenMC gives ~2× DRAGON at discharge and ~12× at fresh fuel. The +1957 pcm / ~4 β figure is **retracted** (`PROGRESS.md`). Carried forward as a 2× bracket, by decision |
| A5b | MULTICOMPO export from the corrected cell — **was the biggest structural gap** | ✅ **done 2026-09-23.** `Dragon/compo/_ACompo`, 113.9 MB, 630 points, axes burnup × DCA × TF × TG (Xe deferred). Round trip to DONJON 6.4 pcm worst over 8 nodes spanning every axis; off-grid `LINEAR` interpolation 27 pcm worst. β **measured** from `NDEL 6`: 0.006824 → 0.004680 over 0–20 MWd/t, confirmed against OpenMC prompt-vs-total to −0.5 %. The second COMPO was **replaced by a correction table** (`openmc/void_bracket.py`) — DRAGON has no cross-section scaling facility anywhere in the write path, so it cannot produce one; see PROGRESS.md "A5b.1d". At discharge burnup the bracket collapses to a single multiplier ≈ 1.9. Applying it is the first item of A7. **Superseded 2026-09-26:** rebuilt on SHEM-361 + Zr self-shielding, 840 points (nodes 7.5 / 12.5 added), 152 MB, round trip 6.7 pcm, off-grid 21.2 pcm; the multiplier is replaced by additive variants A / A′ / B (full void at 10.9 MWd/kgU: +1.95 / +2.42 / +2.72 $); see PROGRESS.md "Phase C". |
| A6 | CPS channel cells: B₄C, graphite displacer, water column, on the A′ basis (`A6_CPS_PLAN.md`) | displacer-only insertion gives **positive** reactivity <br>**Status 2026-09-29:** A6.1 and A6.2 passed (supercell reproduces the single cell to +2.8 pcm). **A6.3 gate missed:** converged DRAGON is 5–12 % from OpenMC on the section worths, carried as the measured A′ correction (+60 to +1107 pcm) and localised — the absolute-k comparison shows convergence fixes the water column at dca 0.72 and the absorber at 0.02, so the residual is spectral, not a single data error. **A6.4 gate failed with the cause found:** homogenisation, SPH and the solver are exact (~1 pcm) but fuel-COMPO neighbours cost 7–10 % on the displacer and drained-channel worths; A6.4b (an explicit rod-cell equivalence) was chosen, built and **disproved 2026-09-30**: matching the rod's flux makes the worth error worse, matching its removal rate will not converge, and a +/-20 % sweep of the rod factors never brings the worth within -3.45 % of a 1 % gate. The cause is not the rod cell -- the eight fuel cells around it differ from infinite-lattice fuel by +/-3 % at zero burnup, because the rod perturbs the spectrum across the whole 75 cm supercell. Carried as a measured one-signed bias (displacer and drained channel low 7-10 %, absorber within +/-3 %) unless A8 proves sensitive. **A6.5:** the core exists on the sourced map (`gen_rbmk_unit4.py`, 52×52×32, all 227 CPS channels placed) but has placeholder reflector data and no rod devices. |
| A6b | **Fuel COMPO rebuild** (new, 2026-09-26). The Xe axis was dropped 2026-10-01 once `NCRLIB.f:268` and `:533-538` showed `NCR: … MICRO` overrides a stored isotope density and rebuilds the embedded macrolib, so Xe135/I135 can be set at run time from the stored `MICR 31` list without an axis. **Qualified 2026-10-04:** `MICRO` reads one scalar per isotope per MIX (`NCRRGR.f:326` → `:919`, `CONC(NTOT,ISO)` indexed by *mixture*, with no channel index on that path), so that holds for a uniform xenon LEVEL. A xenon FIELD — which 01:23 demands, the poisoning being shaped by local power history — needs one fuel mixture per xenon bin with `FMIX` assigning channels. Still no rebuild; the cost is mixtures. **Level solved 2026-10-05** (`tools/a6b_xenon.py`): equilibrium xenon is worth **−2352 pcm** in this core, and the 01:23 level is **1.039×** that, worth **−92 pcm** more — every constant read from the COMPO's own `DEPL-CHAIN` (the decay constants return the accepted 6.570/9.140 h half-lives, which validates units and indexing) with σφ₀ calibrated from the stored equilibrium rather than a flux estimate, and the history from INSAG-7 Table I-I. The level is therefore adequate as a uniform value. **The slope is the real finding:** xenon peaked at 1.18× after the power reduction, fell below equilibrium by 23:10, and at 01:23 was only **8 % of the way** into a climb towards 1.502× (≈ −1180 pcm), entered 50 min earlier against a 9.14 h timescale — against 47 inserted rods worth −110 pcm. The **field** remains open and needs a per-channel flux history; INSAG-7 §I-4.7 notes no such study was ever done. Scope became the two axis ends A7b hit: `DCA` to 0.80, `TF` to 530 K. **Field solved 2026-10-05 — no rebuild needed.** `U4_XEBINS=N` splits the fuel into N mixtures and gives each channel its bin through the fuel map's `MIX` array, one `NCR: … MICRO` clause per bin, so the field costs mixtures and not an axis as predicted. Verified before use: `U4_XEBINS=1` emits a **byte-identical** deck, and four bins at identical densities give **bit-identical k** (+0.00 pcm). The level/shape split is clean — raising a *uniform* xenon to the field's mean costs −102 pcm and leaves the power distribution identical to four decimals, which is the control; replacing it with a field of the same mean costs a further **−84 pcm** and moves the peak channel **−7.6 %**. | round trip ≤ 10 pcm, off-grid ≤ 30 pcm <br>**Done 2026-10-02.** 34 408 s CPU, 1152 branch points, 208 MB — +37.1 % in file size against +37.1 % in tensor size. Round trip **1.3 pcm** over 12 nodes, now including four at the newly added `DCA` 0.80 / `TF` 530 that the old node set never touched. Off-grid **30.4 pcm**, 0.4 over — but the axis decomposition attributes **31.1 pcm of it to `TG` alone**, against 1.0 for `DCA` and 0.4 for `TF`, and the core deck pins `TG` on a node, so the realised error is ~1 pcm. `CUBIC` rejected on measurement (−48.3 pcm at BU 20 000; `NCR.f:139` has one global flag). **New blocker found for Phase 2c:** the `TG` axis tops out at 900 K = 627 °C while our own deck comment (uncited, and needing a source) puts RBMK graphite at 500–700 °C, and dk/dTG is **+400–450 pcm per 100 K** at the core's burnup, so pinning `TG` at 750 K biases the core by ~+500 pcm. The next rebuild must extend `TG` past 973 K and refine it. **And a second, larger one:** every off-grid point ever used held burnup on a node, so the burnup axis — interpolated in *every* core calculation — had never been tested. Measured 2026-10-02 against depletion points the COMPO did not store as nodes: **+2099 pcm at 500 MWd/t**, −74 at 3500, +171 at 17 500. The core's own 10 900 is in the flat region (2–3 pcm, so A7 is unaffected), but the fresh-fuel knee is a hard A6d blocker — see that row. **Fixed 2026-10-03:** rebuilt at **12 burnup nodes / 1728 branch points** in 18.1 h (500, 1000, 3500, 17 500 promoted; 250 and 11 250 added as deliberate non-nodes so the gate can still fail). Structural gates all pass — 1728/1728 rows, 12 nodes, no absurd row, file size ×1.5007 against a tensor ×1.5, and BU 0 unchanged at **1.313968**. Round trip **1.6 pcm**. **Burnup at the core's own interval: +8.7 pcm**, measured, where the axis had previously never been tested. Refining the depletion grid also removed a **systematic 20–29 pcm** step error the 11-point grid still carried. Off-grid stays 30.4 pcm because `TG` owns it and `TG` is untouched. Residual: the 0–500 interval is still +1341 pcm (the xenon knee is inside it) — no Unit 4 assembly is there, [PAV]'s lowest group being 1200 — and the interval that group *does* sit in, 1000–2000, was not sampled by the gate. That was a bad gate-point choice (250 instead of ~1500) and the next rebuild moves it. |
| A6c | **Smolensk-3 cold zero-power start-up** ([BEH96]; promoted from the deferred Phase D, 2026-09-26). The first core-level measured reference: two critical and two subcritical states with the initial loading described. Tests the 3-D DONJON core with rods, before thermal hydraulics are added. | measured critical states reproduced within the graphite-impurity band; subcriticals ordered correctly; result reported, not tuned <br>**Blocked on an input (2026-09-26):** [BEH96] gives the four states and measured k, but the loading map, including which 28 rods were withdrawn, is in its Ref. 5 (Behrens et al., Kurchatov/Bremen, 1993–94). That report is not online (OSTI/ETDEWEB hold abstracts only). Needs the report, or a substitute from the same group ([ALX98] cites the same sources). The measured rod references that *are* in hand are [BEH96] Table I: critical assemblies 1→1a and 3→3a (4 rods to 148 / 168 cm, −0.26 / −0.15 %Δk) and assembly 8 (rod simulators voided, −0.28 %). They need the D2 facility model. |
| A6d | **Unit 4 initial state at 01:22:30** as a sourced deliverable (new, 2026-09-26): channel map, burnup distribution consistent with [PAV]'s assembly counts, rod pattern (INSAG-7 Fig. II-6, digitised), power, flow, inlet subcooling, axial and radial shape (INSAG-7 Figs. II-7, II-8). Its uncertainty probably dominates the transient's. | every input traceable to a page; DONJON steady state reproduces INSAG-7's reconstructed shape; input ranges recorded for A8 sensitivity <br>**Sources in hand (2026-09-26):** rod depths and site lattice, digitised (211 rods + 12 empty sites; `sources/derived/insag7_fig_II6_012230.csv`); the burnup histogram in 8 groups, 1659 assemblies averaging 10.9 MWd/kgU ([PAV] Table 1; no spatial map, so placement is a stated rule with a sensitivity); one additional absorber and one empty channel (INSAG-7 pp. 67, 107). Figs. II-7 / II-8 are contour and shape plots: comparison targets, not inputs. **Channel map DONE 2026-09-27:** Dollezhal Fig. 2.3 digitised and registered against INSAG-7 Fig. II-6 — exact, all 223 rod sites at a single offset, nothing left over. 1661 fuel + 211 rods + 12 ДКЭ(в) + 4 start-up chambers = 1888 positions, every count closing against a source that was not used to build it. `sources/derived/unit4_channel_map.csv`. **Still needed:** the burnup *placement* rule, the types of 32 of the 211 rods (recorded per row in `type_source`), and the power/flow/xenon state. **Blocked on the COMPO, 2026-10-02:** the placement rule spreads channels over [PAV]'s histogram, and **172 of 1659 assemblies (10.4 %) sit at 1.2 MWd/kgU** — inside the 0–2000 MWd/t node interval, where the equilibrium xenon/samarium knee makes linear interpolation misprice k by about **+1170 pcm** per assembly. Pinning every channel at the 10.9 average hides this; using the real histogram does not. The burnup axis needs nodes at 500 and 3500 before A6d placement means anything. **Unblocked 2026-10-03:** the COMPO now carries 12 burnup nodes including 500, 1000 and 3500, so [PAV]'s fresh group sits in a 1000–2000 interval entirely past the xenon knee instead of a 0–2000 one spanning it. The improvement is large but **not measured** — the gate sampled 250 and 11 250, not 1000–2000 — so the placement rule should carry that as a stated uncertainty until the next rebuild moves the gate point. **2026-10-04:** per-channel burnup is wired (`INST-BVAL CHAN` + `INST-BURN`), and the placement measured at up to **+10 860 pcm** across orderings of [PAV]'s histogram — the largest single unknown in the model. Solving for it by iterating the refuelling rule **diverges** (gain > 1, no restoring mechanism). The **01:22:30 rod pattern is now built per rod** from the `depth_cm` column with all four constructions (AR absorber-only, USP bottom-entry 3.5 m), and is worth only **−110 pcm** — 2.3 pcm for 47 rods, the operating-margin problem arrived at from geometry. With flat burnup it puts the core at **3025 kW / MAX-AVG 1.573, inside [D]'s published 3000–3200 kW** — the first physically achievable power distribution the model has produced. That reading was briefly retracted and is **reinstated 2026-10-05**: `U4_XENON=stored` leaves the COMPO's depleted Xe/I in place and those densities *are* the 3200 MW equilibrium (`xenon_equilibrium(1,1)` returns the stored value to every digit), so the default decks carry full-power poison under a full-power normalisation and the comparison is internally consistent. Only the `U4_XEHIST=0123` field runs mix states; see PROGRESS (17). With a realistic burnup spread it does not flatten at all, so the remaining agent is **xenon**, and placement + rods + xenon must be solved together. **All three solved together 2026-10-05, and the placement still fails.** Xenon is a genuine flattening agent — at 200 MW burnout is negligible against decay, so Xe-135 tracks the iodine left by the *past* power shape and high-power channels carry more poison, which is negative feedback on the shape. On the realistic (chequerboard) spread with the 01:22:30 rods it takes the peak channel 5609 → **4731 kW** and MAX/AVG 2.916 → **2.460**, −16 % and −193 pcm. That is still far from the 1.573 the flat-burnup core gives, so a realistic spread **plus** the sourced rods **plus** a self-consistent xenon field does not produce an operable shape: the real placement has to be more ordered than any of these guesses. Two method notes. The naive fixed-point field rebuild **diverges** (5609 → 4137 → 5870 → 4561 → 6568 kW) — loop gain above one, and also wrong physics, since a 9.14 h time constant cannot respond to a power it has just changed; under-relaxing at w = 0.35 (`U4_XERELAX`) converges in six passes and shows the one-pass 4137 kW was a 26 % over-correction. And the **full-power test needs a different field**: these runs normalise to 3200 MWth while the field belongs to the 200 MW state, and at full power Xe_eq saturates with flux, which predicted 3.4× less flattening (sensitivity 0.249 against 0.841). **Measured, and the prediction was wrong:** `U4_XEHIST=equil1.0` converges to 4722 kW / **2.4556** against the 01:23 field's 4731 / 2.4600 — the shapes agree to 0.2 % — while costing **−73 pcm** against −193. The sensitivity prices the gradient at the peak, but this spread gets flattened from its low-power tail, where the equilibrium field falls to 0.50× equilibrium against the transient's 0.94×. So the operability conclusion holds for either field, and for A8 the peaking is robust to the choice of field while the eigenvalue is not. |
| A7 | Couple: 3-D steady state with `NCR:` + `THM:` | converged critical core at 3200 MWth <br>**A7a done 2026-10-01** (one channel against [D] p.95). **A7b converges 2026-10-02:** all four flow × feedback cases reach the criterion in 12 passes. Converged feedback, reactivity (1728-point table, AZOC displacers corrected, 2026-10-04): Doppler **−230 pcm**, density **+331**, net **+101**. Flow-distribution spread **64.2 pcm** (measurable only now the `DCA` axis reaches the inlet); the two density-pinned cases agree to 0.5 pcm, which is the check that the pin severs the flow→k path. Cold k is now **1.045255** and the converged coupled k **1.046365**; the earlier values were ~610 pcm low because 36 AZOC channels were modelled as water rather than as withdrawn rods holding their displacers (see the gotcha table). Two things had to be fixed to get here: the loop deleted `FLUX` on its last pass so the power block had never run (kernel error 666, *after* the results printed), and the convergence test had to move to the eigenvalue because the temperature field has a limit cycle at the Saha-Zuber boiling-onset switch that no tolerance removes — k is bit-identical at `RELAX` 1.0/0.5/0.2. **Not critical, and should not yet be read as an eigenvalue:** `TG` is pinned ~120 K below operating temperature, worth about +500 pcm (see A6b). Reinforced by the 2026-10-03 rebuild: it moved absolute k by ~20 pcm (the depletion-step error it removed) and every feedback by ≤ 2 pcm, so on this model the differences are robust and the eigenvalue is the fragile number. A8 is driven by differences. |
| A8 | Reference AZ-5 transient: `INIKIN:`/`KINSOL:` + `DSET:`, from the A6d state, under bracket variants A′ and B; stops at a defined **fuel-failure criterion** (to be sourced, e.g. a fuel-enthalpy threshold) | prompt power rise before absorber takes over; compared (not tuned) with INSAG-7 Appendix II's three independent reconstructions |
| A9 | Detectors: `DETINI:`/`DETECT:` + SPND lag | traces respond to local rod motion, not just global power |

A0–A5 are largely mechanical. A6–A9 require physics judgement — check in before starting them.

**Order from 2026-09-26:** A6 → A6b → A6c → A6d → A7 → A8 → A9, then Tier B. A6b and A6c come first because xenon and a measured core-level reference both bear on every later step; A6d comes before A7 because the reconstructed initial state is what A7 has to converge to and what A8 starts from.

**Update 2026-09-22:** A3 has been rebuilt on RBMK dimensions (the previous cell was a
CANDU-6 bundle) with `USS:` self-shielding and an in-deck volume-fraction guardrail, and A5
showed a positive void coefficient rising with burnup. A4 turned out not to apply at cell
level. Details and remaining caveats in `PROGRESS.md`.

**Update 2026-09-23 (OpenMC cross-check).** The ~4 β figure quoted in the 09-22 update is
**retracted** — it matched the historically quoted Chernobyl magnitude by coincidence,
produced by a free-gas-hydrogen bug now fixed. OpenMC gives ~8 β at 20 MWd/kg. What survives
independent confirmation is the **sign and the burnup trend**, plus the cell geometry
(analytic volume fractions match DRAGON's tracking to every printed digit) and the method
itself (a CANDU-6 control agrees between the two codes to 1.3 %).

**The A5 gate, restated.** Both earlier numeric targets were wrong: "+2 to +5 pcm/%void" by
an order of magnitude, and the 09-22 correction to "+1 to +3 % Δk/k" is also exceeded —
OpenMC gives +4.0 %. State the gate qualitatively: **positive, and rising steeply with
burnup, at operating burnup**. A fresh unpoisoned cell can legitimately read near zero. The
magnitude is carried as a bracket between the two codes until A8 shows whether it matters.

**Update 2026-09-26 (method convergence closed; the plan reordered).** The lattice-level void gap between DRAGON and OpenMC is closed (PROGRESS.md, "Phase A–B", "Phase C"). Where confidence now stands:

| Level | Confidence |
|---|---|
| Fuel-cell void worth | **good, ±10 %**: two methods plus a third-party benchmark agree |
| Fuel-cell absolute k∞ | **moderate**: DRAGON 240–430 pcm below OpenMC (attributed, not closed), plus ~75–130 pcm depletion step error |
| Anything whole-core (rods, map, TH, transient) | **none yet**: not built or not verified |
| Against measurement | **none at any level**: A6c is the first |

The single-channel full-void figure is not the core void reactivity. That also depends on leakage, rods and the axial shape, which is why A6–A6d come next.

### Tier B — online engine
Standalone GPU solver reading the A5 MULTICOMPO, validated against the A8 transient and A9
detector traces, including through the excursion rather than only at steady state.
Working set is a few MB (76 832 nodes × 2 groups + 6 precursor groups) — no memory risk on
the ~110 GB budget, but never form a dense node-by-node matrix: at 76 832² that is ~47 GB.

### Tier C — mnemonic panel
Driven entirely by Tier B.

---

## Key gotchas (verified against source)

| Gotcha | Evidence |
|---|---|
| `GEO:` mesh coordinates are **centimetres** | contrast `iaea3d_fuelmap.x2m:99` (correct) with `rbmk_core_3d_realistic.don:1417` |
| SPH needs a `SEQ_BINARY` tracking file; NXT **is** supported | `SPH.F:140`, `SPH.F:239`, `NXT.f:42`; pattern in `twimsE_proc/TCWE13.c2m` |
| `EDI: COND` accepts **real energies in eV** as well as group indices | `EDIGET.f:380-400` — use `COND 0.625`, not `COND 24` |
| The APOLIB99 library is **172 groups**, not 99 | `NGRO 172` in `rbmk_cell_dlib99_v2.result:371` |
| `TRIVAA:` requires `UNIT` for anything feeding `INIKIN:`/`KINSOL:` | `TRIVAA.f:174` |
| Use `MCFD 1`, not `DUAL 3 3` | ~40× fewer unknowns; `AFMtest.x2m` precedent |
| Transient THM is **HEM-only** | `THMTRS.f:157` hardcodes `IDFM=0`; `THM.f:1102` passes no `IDFM`/`IPRES` |
| `MOVDEV:` truncates multi-part rods — use `DSET:` | `DEVGET.f:246` vs `MOVPOS.f:159` / `MOVGRP.f:175` vs `NEWMDV.f:97` |
| Rods with `LEVEL < 1e-4` are skipped entirely | `NEWMDV.f:92` — put the parked displacer in the base map |
| `XENON:` is equilibrium-only | `XENCAL.f` — add Xe as an explicit COMPO axis for dynamics |
| `EXCELT:` needs `TRAK` before `TISO` | `twlup_proc/TCWU07.c2m:66` |
| CLE-2000 object/module/procedure names are capped at **12 characters** | `Ganlib/src/objstk.c:189` — longer names give `INVALID OBJECT/MODULE NAME`, which looks like a parser bug and is not |
| Re-creating an existing object needs `X := DELETE: X ;` first | `rep900_mco.x2m:409`; not `DELETE X ;` |
| `rdragon` copies `data/<bare-arg>` — pass the **`.x2m`** or a stale extensionless file shadows the deck | `rdragon:99` |
| COMPO's 2nd `L_EDIT` slot is **group form factors**, not SPH | `COMCAL.f:24`; an SPH edit passed there is silently ignored |
| CLE-2000 inline comments are `!` or `(* *)`; a bare `*` comments only at line start | a trailing `* note` after `;` is parsed as tokens |
| `SPLITR` takes one value per **annulus**, not per region | `CARCEL 5` needs 5 values; the corner region cannot be split |
| `USS:` needs `SUBG` in the `LIB:` block | otherwise `USS: THE INPUT INTERNAL LIBRARY HAS NO SUBGROUPS` |
| SPH cannot correct a `MERG COMP` (single-region) homogenization | `SPHDRV: INVALID NUMBER OF MACRO-REGIONS (9 1)` — needs one region per tracking macro-region |
| Merged volumes live in `MIXTURESVOL`, not `VOLUME` | inside the edition's saved directory |
| Graphite must actually moderate | check `SCAT` has non-zero σ(1→2) in every moderator mixture |
| **A DRAGON geometry with an open (`VOID`) boundary gives a wrong solution here** — 2–5× too much leakage, while fully reflected ones are right to 170 pcm. Geometry, boundary keywords, tracking density and leakage model all eliminated; cause unknown. Close the geometry, or verify against OpenMC. | `openmc/slab.py`: a 1 m fuel slab with one vacuum face is 1.198662 ± 69 pcm in OpenMC, 0.849315 in DRAGON |
| Mixture **0** in a DONJON reactor geometry is a *virtual volume*, and the boundary condition is applied at the **real/virtual interface**, not at the grid edge | `USPMIX.f:52` drops `MAT(IEL)==0`; verified by k being bit-identical for 1, 3 and 5 cells of mixture-0 padding (`tools/u4_leakage.sh`) |
| `USPLIT:` needs `NREFL + NFUEL` to equal the **highest material index** — no gaps | `@USPLIT: WRONG NUMBER OF REFLECTOR OR FUEL TYPES`; put reflector mixtures first and fuel last, as `1Sap_vs_3Sap.x2m:29` does |
| `MACINI:` indexes the non-fuel macrolib by **material number**, and demands an `H-FACTOR` block in the combined macrolib | `MACINI.f:274`; so `MACREF`'s `NMIX` is `max(RMIX)` and every index below it must be defined |
| A Picard loop that `DELETE:`s `FLUX` at the end of its body leaves **nothing for the code after the loop** — the deck dies with kernel error 666 after printing the loop's own results, so the failure looks like a clean finish | `cle2000_c: LINKED_LIST *FLUX* IS NOT DEFINED(2)`; re-solve once after the loop, which is also the right order because the in-loop power predates that pass's `THM:` update |
| `NCR:` interpolation is **one global `LINEAR`/`CUBIC` flag**, not per axis, and `CUBIC` is not uniformly better | `NCR.f:139`, set at `:167-170`; measured −48.3 pcm at BU 20 000 where `LINEAR` gave −14.4 |
| `THM:` relaxes **all five** local feedback fields with the single `RELAX` factor, so the residual it reports is `RELAX` × the raw pass-to-pass step — under-relaxing makes convergence *look* better without changing it | `THM.f:1187` sets `RELAX0=RELAX` for every `ITYPE 2` parameter; `:1207-1245` apply it |
| `NCR: … MICRO` needs **`ALL`**, not `ONLY` — `ONLY` discards every isotope not listed, throwing away the whole depleted inventory — and it must come **last** in the `MIX` clause | `NCRLIB.f:364` (`GO TO 110` skips unlisted isotopes); `NCRRGR.f:316-335` reads isotope/value pairs until `ENDMIX` |
| An isotope density written back through `MICRO` must be the one `NCR:` would have **interpolated**, not the nearest stored node — otherwise it is a silent perturbation | Xe-135 falls 11 % across the 10 000→15 000 MWd/t nodes, so the node value at the core's 10 900 is 2.03 % high and costs 49 pcm. The control is to write the density back and require a no-op |
| A withdrawn graphite-displacer rod is **not an empty channel** — it still holds 4.5 m of displacer in the core, so modelling a withdrawn bank as a water column removes moderator | 36 AZOC channels were water at `U4_TILT=0`; correcting them to `stack(0)` is worth **+609 pcm** and moves channel peaking 1.829 → 1.590, against +522 pcm predicted by scaling A6.5's 142-channel displacer measurement |
| The coupled steady state has a **limit cycle that no tolerance removes**: `K0`, the index of the boiling-onset node, is an integer set by a threshold test that sits inside the Picard loop | `THMH2O.f:383` `IF(TCALO.GE.TSAT-DTSUB) K0=K`, reset at `:276`, gating the two-phase block at `:147`; `DTSUB` depends on heat flux. Converge on the eigenvalue and report the field residuals |
| Rebuilding a xenon field from the latest power each pass **diverges** — and under-relaxation is physics here, not a numerical convenience | Measured 5609 → 4137 → 5870 → 4561 → 6568 kW on the peak channel: loop gain above one. Xenon's 9.14 h time constant cannot respond to a power it has just changed, so the undamped iteration asserts something false; w = 0.35 converges in six passes and the first pass over-corrects by 26 % |
| A core shape normalised to the nominal rating may be compared against an operating channel-power limit **only if the xenon matches that power too** | `U4_XENON=stored` is the 3200 MW equilibrium, so the default decks are consistent and the comparison holds. A `U4_XEHIST=0123` field is the 200 MW transient distribution under a 3200 MW normalisation, and its peak channel power is not a full-power number — quote the `equil` field instead |
| Inserting every control rod makes this core **less** flat, not more — rods flatten only when positioned individually | Flat burnup, 211 rods: out 1.590 MAX/AVG, fully in **2.249**, at a cost of −5552 pcm. The rod sites are not uniformly distributed, so suppressing them all distorts the shape instead of levelling it |
| A textbook low-leakage placement — burnt fuel inside, fresh at the periphery — is the **second worst** arrangement of [PAV]'s histogram | MAX/AVG 7.615 against 2.791 for nearest-neighbour alternation and 1.590 for flat. The histogram is too wide to group spatially: 172 assemblies at 1.2 MWd/kgU make a reactivity island wherever they are put together, and k = 1.314 fresh is steep enough that the flux finds it |
| A xenon field's **shape** effect is nearly independent of *which* field; its **level** effect is not — so do not price a field by its local sensitivity | The 01:23 transient field and the 3200 MW equilibrium field give MAX/AVG 2.4600 and 2.4556 — 0.2 % apart — while costing −193 and −73 pcm. The sensitivity dln(Xe)/dln(s) = 1/(1+σφ/λ_Xe) is 0.841 at 200 MW against 0.249 at 3200 and predicted 3.4× less flattening, which is wrong: it prices the gradient at the peak, and a wide spread gets flattened from its low-power tail, where the equilibrium field falls to 0.50× against the transient's 0.94× |
| `NCR:` with a fuel map on the RHS takes `NMIX` from the map (`NCH × NB`), and rejects a smaller explicit one | `NCR.f:127` then `NCR.f:157`; omit `NMIX` on the `TABLE` call |
| `NCR: … TABLE` can `SET` burnup instead of reading it from the map, with no `INST-BURN` | `NCRRGR.f:717` prints "L_MAP values overwritten by the SET option"; `NCRMAP.f` then reads nothing |
| `THMDRV` **overwrites its own `SPEED` argument** (sets it from `MFLOW/DCOOL(1)`, the outlet velocity) | `THMDRV.f:266,286`; hand it a scratch copy or Picard iteration 2 silently runs on iteration 1's outlet velocity. `THMTRS` takes `SPDIN` and is safe |
| `THMINP` has handled the `CHAN <one value per channel>` form since 2018 — only `THM:`'s own parser did not | `THMINP.f:43`; that is why `patches/0001-THM-per-channel-inlet-velocity.patch` is 139 lines and not a rewrite |
| A source change inside `5.1/` is **invisible to this repo and lost by a submodule update** | `5.1/` is pinned upstream and gitignored; patches live in `patches/` and `tools/apply_patches.sh` reapplies them from `bootstrap.sh` |
| `THM:`'s default boiling model never reverts to the thermodynamic quality | Bowring (`ISUBM=1`) damps vapour generation by `1/(1+Π)` and `Π` stays positive after the bulk saturates (`THMH2O.f:161`); use `SAHA` (`ISUBM=2`), whose `F2 = (h-h_f)/h_fg` is the energy balance (`THMH2O.f:165`) |
| `THM:`'s gap correlation implies a much tighter gap than RBMK fuel has | measured against [D] p.95's 2100 C centreline and against bare helium conduction over the sourced 100 um gap, which agree on ~1700-2800 W/m2/K; set `HGAP` explicitly |
| `SET-PARAM` addresses a fuel-map parameter by **`P-NAME`, not `PARKEY`**, and a `LOCAL` one needs `SAME`/`CHAN`/`BUND` before its value | `RESPAR.f:139-176`; only a `GLOBAL` parameter takes a bare number |
| `THM:` writes back only into parameters named `T-FUEL`, `D-COOL`, `T-COOL`, `T-SURF`, `P-COOL` | `THM.f:1172-1174`; `NCR:` then reads them by `PARKEY`, which is why the two names differ |
| `THM:`'s `CLUSTER` is an infinite **triangular** array, so one pitch cannot match an RBMK channel's flow area, hydraulic diameter and heated perimeter | `THM.f:963-971`; match the flow area — measured 2026-10-01, the hydraulic diameter reaches nothing compared once the surface is in nucleate boiling |
| A COMPO built on a lattice-cell *nominal* state will not cover a real core: the subcooled inlet is **denser** than nominal and a low-power channel end is **colder** than the fuel-temperature floor | measured 2026-10-01 by running the A7 Picard loop -- `DCA` wanted 0.778 against an axis top of 0.72, `TF` wanted 586 K against a floor of 600; `NCR:` has no clamp, so the axis has to cover it |
| `UTL:` must be in the `MODULE` list before any `UTL:` call parses | otherwise `objstk: OBJECT/MODULE NOT YET DECLARED`, error 5004, which does not point at the module list |
| The flat `POWER-CHAN` block, not `FLPOW:`'s radial-plane table, is the handover for per-channel data | it is in **channel order** -- what `RESPFM.f:74-82` finds and what `THMINP` reads a `CHAN` list in |

---

## Standing rules

The authoritative list, with the incident behind each one, is in `PROGRESS.md`. In short:

1. **Every asserted value must come from a calculation, never from a constant chosen to make
   the assert pass.**
2. **Every deck must verify what it actually built, not what it was meant to build.**
3. **An error message from DRAGON is a statement about the input until proven otherwise.**
4. **No physics number is validated until a second, independent method reproduces it.**
5. **A DRAGON `.result` is not evidence unless it postdates the deck.** Delete it before
   re-running.
6. **A fix that lives in a copy of the file is not a fix.** Correct the file everything calls.

---

## Key gotcha added 2026-09-23

**Coolant hydrogen must be `H1_H2O`, not `H1`.** `DLIB_99` contains both; bare `H1` is
free-gas, with no bound-water thermal scattering law, and it overstates water's moderating
power — which suppresses the positive void coefficient. Every bundled reference deck
(`twlup_proc/`, `rep900_mco_proc/`) uses the bound form. Worth +140 pcm at full void and
−264 pcm on k∞. Same applies to `H2_D2O` and `C12_GR`.

---

*Last updated: 2026-09-29 (A6 status through A6.5; A2's solver superseded — `DUAL 1 1`, not
`MCFD 1`, because MCFD loses a third of the absorber worth; A6d's channel map closed and
sourced). Previously: 2026-09-23 (A5a downgraded to half-passed; A2 restated; hydrogen gotcha
and full standing-rule list added)*
