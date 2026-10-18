# B6 gate 1: the GPU RT0 eigenproblem on DONJON's own MACRD (the B1 case)
# against DONJON DUAL 1 1 (k = 1.027709) and the CPU RT0 (787 s).
using RBMKCore, RBMKCore.Diffusion, RBMKCore.Mixed, RBMKCore.GPUDual, CUDA, Printf, Statistics
include("b1_solver_load.jl")
include("b1_power_read.jl")
mesh, ntot, D, scat, fiss, hfac, kref = load_b1(REF)
p = build_dual(mesh, ntot, D, scat, fiss, hfac)
G = gdual(p)
@printf("device reservation %.1f MiB\n", G.bytes / 2^20)
gsolve_k(G; tol=1e-6)                       # compile
t = @elapsed (k, phi) = gsolve_k(G; verbose=true)
@printf("GPU RT0 k = %.6f  DONJON %.6f  diff %+.2f pcm  (%.1f s)\n", k, kref, (k - kref) / (k * kref) * 1e5, t)
t = @elapsed (k, phi, r) = gwielandt(G, k, phi; verbose=true)
@printf("polished: k = %.9f  residual %.2e  (%.1f s)\n", k, r, t)
pd = sum(p.hfac[:, g] .* Array(phi[g]) for g in 1:2) .* p.vol
reg = mesh.index[p.cell]
isfuel = [sum(fiss[r, :, :]) > 0 for r in reg]
ref = power_bund(joinpath(RES, "rbmk_unit4_core_dev_axf527ca_cB4af83e.don.result"))
a = pd[isfuel] ./ sum(pd[isfuel]); b = ref ./ sum(ref); rel = (a .- b) ./ b
@printf("bundle power vs DONJON DUAL 1 1: rms %.4f %%  max %.4f %%\n", 100sqrt(mean(rel .^ 2)), 100maximum(abs.(rel)))
