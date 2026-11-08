---
id: 19
status: done
priority: Normal
blocked_by: []
tags: [tier-b, neutronics, numerics, gpu, infra]
---

# Tier B B0-B2: cross-section export, the RT0/DUAL 1 1 spatial method, kinetics, and the GPU path

The Julia/CUDA engine `tierb/RBMKCore.jl` was brought to parity with DONJON for cross sections (B0), the static core (B1) and frozen-TH kinetics (B2). B1 found that the spatial method can't be chosen freely: the CPS cross sections were SPH-equivalenced on DUAL 1 1 at 25 cm, so the engine implements RT0 (TRIVAC DUAL 1 1) and matches k to -0.01 pcm. B2 passed and showed that DONJON's own KINSOL tolerance (EPSOUT = 1e-4) biases the frozen-TH peak by about 6 %. The RT0 face systems were moved onto the GPU, which needed a hard memory limit on CUDA.jl's pool.

**Sources:** PROGRESS (38), (39) (B2, GPU and solver-tolerance parts); key files: `TIER_B_WORKPLAN.md`, `tools/tierb_export_xs.py`, `tierb/RBMKCore.jl/src/{Mixed.jl,Kinetics.jl,DualKinetics.jl,GPUDual.jl}` (`RBMKCore.Mixed`, `RBMKCore.Kinetics`, `RBMKCore.DualKinetics`), `KINRD2.f:58` (DONJON).

## Outcome
- B0: NCR evaluates the fuel COMPO at all 1728 grid nodes plus the A8 reference mixtures, and Julia interpolates multilinearly. NCR interpolates D as 1/D (interpolating D directly is off by 8e-5), and per-isotope nu-Sigma_f is stored mixture-fastest. Gate over 26 seeded off-grid states: worst 2.4e-7 (single-precision storage).
- B1: per-element cross sections match DONJON's final MACRD for all 79 360 elements, worst 1.3e-7. MCFD 1 is reproduced exactly: k = 1.0232573 vs 1.023257, bundle powers rms 0.018 %.
- FD vs DUAL 1 1 at 25 cm: -423 pcm in k and up to 31 % in bundle power. Refining the mesh doesn't close the gap. FD gives 1.0232573 / 1.0267377 / 1.0284529 at 25 / 12.5 / 8.33 cm (apparent order about 0.3), and DUAL 1 1 / 2 2 / 3 3 gives 1.027709 / 1.029215 / 1.030559.
- The reason is in the data: SPH-equivalenced cross sections are tied to DUAL 1 1 at 25 cm (A6.4; A6.3 found MCFD 1 loses 31-34 % of absorber worth). The consistent method is DUAL 1 1 at 25 cm, and "mesh convergence" is not the right question.
- RT0 with consistent current mass (244 144 faces, AMG-CG): **k = 1.027709 (-0.01 pcm), bundle powers rms 0.018 %, max 0.037 %**. B1 gate passed (13 min on the CPU).
- B2 on FD: the 1 s null transient holds P/P0 to 0.9999938. On RT0, a Wielandt polish takes the eigenpair residual from 1.7e-7 to 9e-11, and the null transient then holds **P/P0 - 1 = -1.1e-11** (the 1.7e-7 residual alone had drifted it by -8.8e-6).
- FD vs DONJON MCFD 1 (frozen TH, AZ-5): within 0.1-1.6 % over 7 s, peak 2271x vs 2238x.
- RT0 vs DONJON DUAL 1 1: peak **210.9x at 6.50 s vs 223.5x at 6.43 s**. The cause is KINSOL's EPSOUT = 1e-4. Re-run with `EXTE 2000 1.0E-7`, DONJON's steps 1-4 agree with RT0 to 1.5-7e-6 (the default run is 2.2e-4 to 1.2e-3 away).
- Halving dt moves the peak by -0.91 % (209.0x at 6.45 s at 5 ms). Gate passed.
- Consequence for Tier A: every A8 band number in (35)-(37) was computed at EPSOUT = 1e-4. That lowers the frozen-TH peak by about 6 %. The alarm timings and the case ordering are unaffected. The converged numbers now come from Tier B.
- GPU: Jacobi-PCG on cuSPARSE solves the face systems in 38/129 iterations (0.034/0.044 s), vs 0.65/2.0 s for AMG-CG on the CPU. The eigenproblem gives k = 1.027708847, residual 7e-11, bundle rms 0.0174 %, in 158 s (CPU: 787 s idle). For kinetics, CPU and GPU agree to 1e-11 in P/P0, at about 1.8 s per step vs about 40 s.
- GPU memory incident: the CUDA.jl pool grew about 5 GB per step, to 30 GB in 6 steps. `JULIA_CUDA_HARD_MEMORY_LIMIT` is now mandatory, operators are freed explicitly, and a 12 GB watchdog is in place. The pool is flat at 4.1 GiB.

## Narrative
- 2026-10-18: (38) Tier B started. B0 passed after finding NCR's 1/D interpolation and the mixture-fastest nu-Sigma_f layout. B1 reproduced MCFD 1 exactly but sat -423 pcm from the DUAL 1 1 reference, and refining the mesh didn't close it. The diagnosis was that the SPH equivalence ties the cross sections to DUAL 1 1 at 25 cm, so `RBMKCore.Mixed` (RT0) was built and matched k to -0.01 pcm. B2 kinetics (KINXSD/KINSRC/KINPRC, theta = 0.8) held the FD null transient to 0.9999938; the next step was moving it onto the mixed-dual operator. (by @assistant)
- 2026-10-18: (39) `RBMKCore.DualKinetics` was built on RT0 (FGMRES with a block Gauss-Seidel preconditioner). The null-transient drift was traced to the power-iteration residual and fixed with a Wielandt polish. The 6 % gap to DONJON DUAL 1 1 was traced to KINSOL's EPSOUT = 1e-4: re-run tight, DONJON agrees to about 1e-6 per step. A converged 7 s DONJON reference would take about 40 h, so a 100-step one was started. The current DONJON binary reproduces the Oct-10 DUAL trace digit for digit (294 steps). B2 gates passed. The RT0 path was moved to the GPU, and after the pool-growth incident every GPU run must set a hard memory limit. (by @assistant)
