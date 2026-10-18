# B1 solver gate (see b1_solver_load.jl)
using RBMKCore.Diffusion, Printf
include("b1_solver_load.jl")
mesh, ntot, D, scat, fiss, hfac, kref = load_b1(REF)
t = @elapsed p = build_problem(mesh, ntot, D, scat, fiss, hfac)
@printf("problem: %d unknowns per group, built in %.1f s\n", length(p.cell), t)
t = @elapsed (k, phi) = solve_k_arnoldi(p; verbose=true)
@printf("FD k = %.6f   DONJON (DUAL 1 1) k = %.6f   diff %+.1f pcm   (%.1f s)\n",
        k, kref, (k - kref) / (k * kref) * 1e5, t)
