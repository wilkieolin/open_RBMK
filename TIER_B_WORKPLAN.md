# Tier B workplan — a differentiable, GPU-resident RBMK engine in Julia

## Context

Tier A (DRAGON → DONJON) has reached a natural checkpoint. From a sourced 01:23:40 state, AZ-5
produces the first-second dip and the two 01:23:43 alarms (530 MW, period < 20 s) at 2.3–3.1 s.
INSAG-7 says none of its three models reproduced those alarms. The surge peaks at 8–418× depending
on the case (PROGRESS 35–36).

Three limits now stop progress toward a grounded fuel-failure answer:

1. **Cost.** A 7 s DONJON transient takes 4–6 h. The question is now uncertainty propagation
   (starting shape, burnup placement, void worth, flow, B₄C density), which needs hundreds to
   thousands of runs.
2. **Thermal-hydraulics.** THM holds pressure fixed and has no momentum equation. It needed
   patches 0004–0015 to survive the excursion. The post-alarm recorded data are exactly what it
   cannot produce (INSAG-7 pp. 54–55):
   - drum pressure and flow at +7/+8 s (75/88 kg/cm², flow −40 %);
   - the fuel-channel rupture signal at +9 s.
3. **Interactivity.** The project goal is a real-time engine for the mnemonic panel (Tier C).
   DONJON cannot be that (PROJECT_PLAN "Tier B — online engine").

**Intended outcome.** A standalone Julia/CUDA engine that:
- reads Tier A's cross sections;
- reproduces DONJON's static and transient results to stated tolerances;
- adds a momentum/pressure TH with loop boundary conditions;
- answers the fuel-failure question as a **prediction with uncertainty**: inputs carry sourced
  ranges, the model is conditioned only on recorded data, and fuel failure is an output.
  Nothing is tuned to the accident.

The same engine then runs in real time for Tier C.

**Standing rules carried over:**
- no tuned constants;
- content-addressed inputs;
- every number comes from an artefact newer than its inputs;
- an independent check for every new physics claim;
- memory analysed before any GPU allocation (110 GB unified; a dense core matrix would be
  ~277 GB, so never form one).

---

## Architecture

New Julia package `tierb/RBMKCore.jl` (project-local `Project.toml`/`Manifest.toml`, Julia
1.12.7 from juliaup). Modules:

| module | content |
|---|---|
| `XS` | cross-section tables exported from the DRAGON COMPOs (fuel `_ACompo` / bracket B `_ACompoVB`, CPS `_CCompo{WAT,ABS,DSP}` incl. `cB`, reflector `_RCompo`). Multilinear interpolation in (burnup, DCA, TF, TG) as NCR `LINEAR`, plus the Xe-135 micro substitution NCR `MICRO` performs |
| `Core` | geometry and maps from the Tier A generator: 58×58×32 mesh, 25 cm pitch, per-node mixture, per-bundle burnup, the 389 rod devices, the U4_PCHAN valving |
| `Diffusion` | 2-group mesh-centred finite difference on the DONJON mesh, CSR on GPU (CUDA.jl), Krylov.jl GMRES/BiCGStab with a block-Jacobi or ILU(0) preconditioner. Eigenvalue by power iteration with Chebyshev/Wielandt acceleration |
| `Kinetics` | 6 delayed groups, θ-method (θ=1 then θ=½), adaptive Δt. Rod motion by volume-weighted partial-node homogenisation, measured against DONJON's plane-stepped devices (the 25 cm sawtooth, PROGRESS 24) |
| `TH` | 1661 parallel 1-D channels: a drift-flux mixture model (mass, momentum, energy) with pressure; radial fuel conduction (~10 rings, UO₂/Zr properties); gap conductance; heat transfer (Dittus-Boelter, Chen, CHF + post-CHF). Loop boundary conditions: inlet header pressure from the main pumps with their recorded rundown, outlet at the drum pressure (lumped drum mass/energy). The patch 0008–0015 lessons are built in: correlations at \|G\|, donor-cell fluxes, local quality, drift floor at stagnation |
| `Coupling` | operator split per step, with a fixed-point option for verification |
| `UQ` | GlobalSensitivity.jl (Morris, then Sobol), SciMLSensitivity / Enzyme gradients of scalar outputs, Turing.jl Bayesian conditioning, ensembles batched on GPU |
| `Live` | real-time loop and state streaming for Tier C (later) |

### Data path, Python to Julia (no hand transcription)

- **`tools/tierb_export_xs.py`.** Reuses the ASCII COMPO parser in `tools/compo_voidB.py`
  (`parse`, `nums`), which `tools/compo_cpsB.py` already uses on the CPS COMPOs. It writes HDF5:
  - per COMPO: the parameter axes;
  - per calculation: 2-group Σ_t, Σ_s(g→g′), νΣ_f, κΣ_f/H-factor, D or Σ_tr, χ, 1/v;
  - Xe-135 micro absorption and density, and the DEPL-CHAIN constants `a6b_xenon.py` reads;
  - β_i and λ_i (from the kinetics records INIKIN reads).

  Content hashes of the source COMPOs are stored in the file.
- **`decks/Donjon/data/gen_rbmk_unit4.py`, new `U4_EXPORT=<path>` sidecar.** Writes the core
  description the deck is built from as JSON/HDF5: mesh, mixtures, burnup per bundle, rod
  devices and travel, PCHAN velocities, inlet conditions. Decks stay byte-identical; this is
  checked on a static and a kinetic deck, the same way as for `U4_CPSB`.

### GPU memory analysis (written into each module's first commit as an asserted budget)

| item | size |
|---|---|
| diffusion | 107 648 nodes × 2 groups = 215 k unknowns; 7-point stencil + group coupling ≈ 1.7 M nnz → ~20 MB CSR (Float64) |
| Krylov workspace | GMRES(30) ≈ 30 × 215 k × 8 B ≈ 52 MB |
| precursors | 6 × 46 508 fuel nodes, < 3 MB |
| TH | 1661 × 28 × ~16 state variables + 10 fuel rings ≈ 1.2 M values, ~10 MB |
| one run | < 150 MB |
| UQ ensembles batched on device | capped at 64 concurrent members (~10 GB), set explicitly and asserted |

No dense matrix is ever formed. A Jacobian for implicit TH stays block-tridiagonal per channel.

---

## Phases and gates (verification against Tier A first, new physics second)

### B0 — environment and data export
- `tierb/` package skeleton; CUDA.jl device check; an asserted allocation helper.
- Run `tierb_export_xs.py` on the production COMPOs and on the cB/VB variants.
- Add `U4_EXPORT` to the generator.

**Gate.** Julia's interpolated macroscopic cross sections match NCR's macrolib to ≤ 1e-6
relative, at 20 random states plus every node. A one-state DONJON deck prints the reference
(pattern: the A64V deck in `compo_cpsB.py:deck`).

### B1 — static diffusion
- 2-group FD eigenvalue on the Unit 4 core.
- The DUAL 1 1 → FD discretisation difference is measured, not assumed. A refined-mesh FD run
  (12.5 cm) separates mesh error from method error.

**Gate.** Against the cB fitted state (`rbmk_unit4_core_dev_axf527ca_cB4af83e`, k = 1.027709):
- k within a stated, measured tolerance (target ≤ 100 pcm);
- bundle powers rms ≤ 2 %;
- the static rod ramp (`a8_ramp.py`, +511 pcm at 160 cm) within 5 %.

### B2 — kinetics with rods, frozen TH

**Gate.**
- The frozen-TH cB transient: DONJON reaches 223× at 6.5 s
  (`…kin700v40g12nofbshvdfr025fi60cc01dt001_vB65c86e_cB4af83e`); its trace is the reference.
- The 1 s null transient holds power to 1e-5.
- Halving Δt moves the peak by < 1 %.

### B3 — channel TH
Built and verified standalone before it is coupled.

**Gates.**
- Steady single channel against [D] p.95 (A7a: outlet 289.3 °C, energy balance).
- The 01:23 steady state: steam only in the top bundles (INSAG-7 p. 64).
- The single-channel replays from this session (`gen.py`/`allB.json`) run cleanly for all 1661
  channels.
- Where the old and new models' assumptions coincide (fixed pressure, HEM), the results agree
  with THM.

**Status (2026-10-18).** The THM-equivalent part is done. `Channel.jl` is a line-by-line port of
THM, verified against DONJON THM itself on a steady state and a ×128 power ramp: T-FUEL rms
0.0045 K, D-COOL rms ≤ 1.6e-5 g/cm³ (PROGRESS 39).

**B3b, momentum, pressure and the loop (solver built and verified on one channel; THM-boundary Newton run coupled on band A to 6.91 s — PROGRESS 41; core-wide loop boundary conditions wait on gaps 1, 2, 5, 6 of `sources/derived/b3b_loop_data.md`).** This is what the post-AZ-5 record
constrains and THM cannot represent:
- two loop halves (left/right), each with a drum separator (lumped mass and energy, steam to the
  closed turbine, feedwater about 120 t/h per side), downcomers, four MCPs, the pressure header
  and the group distribution headers;
- each channel with its ZRK valve, inlet line, the drift-flux channel, and the steam-water outlet
  line to its drum.

Data to condition on (INSAG-7):
- drum pressure rising at about 6 kPa/s from 01:23:04, when the turbine stop valve closed (p. 60);
- four of the eight MCPs coasting down with TG-8 (pp. 54–55);
- at +7 s, flow −40 % on MCPs 11, 12, 21 and 22 and a sharp pressure rise, then 75.2/88.2
  kg/cm² (left/right) at +8 s (p. 55);
- the channel-rupture signal at +9 s.

Found so far in [D]:
- nominal state (p. 50): 37 500 t/h, separator 70 kgf/cm², group distribution headers 82.7
  kgf/cm², 270/284 °C, mean exit quality 14.5 %;
- the two-phase friction method and the slip correlation (pp. 68–69, OCR-garbled, to be
  re-read from the page images);
- every ZRK valve has the same characteristic Q/√ΔP = f(h) (p. 69);
- the measured channel-with-inlet ΔP(Q) on Leningrad-1 (Fig. 3.10, p. 70), digitised in
  `sources/derived/D_fig3_10_channel_dp.csv`, with its caption ambiguity noted;
- the RBMK CHF correlation (p. 70).

Sources still to read: [D]'s circuit chapter (the pump head curve and the flow regulation,
around PDF pp. 150–175); [TD722] and [USP] for loop resistances and RELAP5-style nodalisations
of RBMK circuits. Every resistance must come from a source or from closing a sourced steady state
(the 01:23 flow of 56 000 m³/h at 200 MW), never from fitting the accident.

### B4 — coupled transient, Tier A parity

**Gate.** With THM-equivalent options (fixed pressure, no momentum), the band cases match DONJON:
- the time of 530 MW within 0.05 s;
- the peak within 10 %;
- the energy to peak within 10 %.

Then switch on momentum, pressure and the loop boundary conditions, and report the change as
new physics, not as a fit.

### B5 — grounding and UQ (the scientific goal)

- **Data to condition on**, each sourced:
  - the t = 0 axial shape (Fig. II-8/II-9 t = 0) and radial map (Fig. II-7);
  - the 01:22:30 rod pattern (Fig. II-6);
  - the 01:23:43 alarms;
  - drum pressure and flow at +7/+8 s and the channel-rupture signal at +9 s (INSAG-7
    pp. 54–55);
  - damage concentrated in the lower core;
  - fuel location (PAV), as an end-state check.
- **Uncertain inputs**, each a sourced range:
  - burnup placement (PROGRESS 21);
  - starting shape (the A8_TILT form and others);
  - void worth (brackets A/B);
  - CPS worth correction;
  - flow (×0.85–1.0);
  - subcooling;
  - B₄C density band;
  - pin peaking (OpenMC `pin_peaking.py`).
- **Morris screening**, then Sobol on the survivors. Outputs:
  - time to 530 MW;
  - peak power and time;
  - energy to peak;
  - max peak-rod enthalpy;
  - number of assemblies above 220 cal/g;
  - time of the drum-pressure rise.
- **Turing.jl posterior**, conditioned on recorded data only. Fuel failure is then reported as
  P(any assembly > 920 kJ/kg) with its sensitivities. No input is tuned to it.

### B6 — real time
- Profile; batch the TH on GPU; fixed Δt (~10 ms) with sub-cycling in the excursion.

**Gate.** ≥ 1× real time for the full core at 10 ms through a 7 s AZ-5. The state is exposed for
Tier C.

---

## Tier A while B runs
- Finish the in-flight queue (patch 0015 runs, the OpenMC pin peaking); these complete the B4
  reference set.
- Commit patch 0015 and its regression.
- The Fig. II-7 radial comparison (cheap) feeds B5's data list.
- Check whether Fig. II-9's 4/6/7 s curves are model output rather than measurement, and correct
  PROGRESS 26–35 where they were called an independent test.
- DONJON is then frozen as the reference. No new THM patches unless a reference run needs one.

## Files

| file | change |
|---|---|
| new `tierb/RBMKCore.jl/` (`Project.toml`, `src/{XS,Core,Diffusion,Kinetics,TH,Coupling,UQ}.jl`, `test/`) | the engine |
| new `tools/tierb_export_xs.py` | COMPO → HDF5, reusing `tools/compo_voidB.py` |
| `decks/Donjon/data/gen_rbmk_unit4.py` | `U4_EXPORT` sidecar only; decks byte-identical |
| new `tierb/reference/` | content-addressed copies (or hashes + paths) of the DONJON reference results used by each gate |
| `PROJECT_PLAN.md`, new `TIER_B_WORKPLAN.md`, `PROGRESS.md` | the B0–B6 gates and status |

## Verification
- `julia --project=tierb/RBMKCore.jl -e 'using Pkg; Pkg.test()'` runs each gate as a test
  against `tierb/reference/`, with stated tolerances.
- Every gate reports its number against the DONJON one in PROGRESS, including failures.
- An independent check for every new physics claim:
  - OpenMC for any cross-section question;
  - [D] p.95 and INSAG-7 for TH;
  - single-channel replay against THM.
- `nvidia-smi` and an asserted per-run budget on the first GPU run of each module.
