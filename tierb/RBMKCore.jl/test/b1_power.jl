# B1 power-shape check: FD bundle powers against DONJON's POWER-BUND, for
# DONJON MCFD 1 (same method: must agree) and DUAL 1 1 (the reference).
using RBMKCore.Diffusion, Printf, Statistics
include("b1_solver_load.jl")

function power_bund(result)
    L = readlines(result)
    i = findlast(l -> occursin("CONTENT OF BLOCK 'POWER-BUND", l), L)
    v = Float64[]
    for l in L[i+1:end]
        t = split(l)
        isempty(t) && (isempty(v) ? continue : break)
        x = tryparse.(Float64, t)
        any(isnothing, x) && break
        append!(v, x)
    end
    v
end

const RES = joinpath(@__DIR__, "..", "..", "..", "5.1", "Donjon", "Linux_aarch64")
mesh, ntot, D, scat, fiss, hfac, kref = load_b1(REF)
p = build_problem(mesh, ntot, D, scat, fiss, hfac)
k, phi = solve_k_arnoldi(p)
pd = power_density(p, phi) .* p.vol
# fuel elements (fissile regions) in element-scan order -- x fastest, then
# y, then z -- which is POWER-BUND's order (channel fastest, bottom bundle
# first); the fuel region numbers are not the last block (5051-74310 here)
reg = mesh.index[p.cell]
isfuel = [sum(fiss[r, :, :]) > 0 for r in reg]
nfuel = count(isfuel)
pf = pd[isfuel]
for (tag, f) in (("MCFD 1", "rbmk_unit4_core_dev_axf527ca_cB4af83e_mcfd.don.result"),
                 ("DUAL 1 1", "rbmk_unit4_core_dev_axf527ca_cB4af83e.don.result"))
    ref = power_bund(joinpath(RES, f))
    length(ref) == nfuel || error("$tag: POWER-BUND length $(length(ref))")
    a = pf ./ sum(pf); b = ref ./ sum(ref)
    rel = (a .- b) ./ b
    @printf("%-9s bundle power vs FD: rms %.3f %%  max %.3f %%  (corr %.6f)\n",
            tag, 100sqrt(mean(rel .^ 2)), 100maximum(abs.(rel)), cor(a, b))
end
