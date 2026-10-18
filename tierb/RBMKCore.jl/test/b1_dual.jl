# B1 solver gate, mixed-dual: RT0 (TRIVAC DUAL 1 1) on DONJON's own MACRD
# against DONJON's k and POWER-BUND.
using RBMKCore.Diffusion, RBMKCore.Mixed, Printf, Statistics
include("b1_solver_load.jl")
include("b1_power_read.jl")
mesh, ntot, D, scat, fiss, hfac, kref = load_b1(REF)
t = @elapsed p = build_dual(mesh, ntot, D, scat, fiss, hfac)
@printf("dual problem: %d cells, %d faces, built in %.1f s\n", length(p.cell), size(p.K[1], 1), t)
t = @elapsed (k, phi) = solve_k_dual(p; verbose=true)
@printf("RT0 k = %.6f   DONJON DUAL 1 1 k = %.6f   diff %+.2f pcm  (%.0f s)\n",
        k, kref, (k - kref) / (k * kref) * 1e5, t)
pd = dual_power_density(p, phi) .* p.vol
reg = mesh.index[p.cell]
isfuel = [sum(fiss[r, :, :]) > 0 for r in reg]
ref = power_bund(joinpath(RES, "rbmk_unit4_core_dev_axf527ca_cB4af83e.don.result"))
a = pd[isfuel] ./ sum(pd[isfuel]); b = ref ./ sum(ref); rel = (a .- b) ./ b
@printf("bundle power vs DONJON DUAL 1 1: rms %.4f %%  max %.4f %%\n", 100sqrt(mean(rel .^ 2)), 100maximum(abs.(rel)))
