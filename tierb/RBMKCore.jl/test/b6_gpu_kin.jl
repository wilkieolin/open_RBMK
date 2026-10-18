# B6 gate 2: GPU kinetics (GPUDual) against the CPU reference (DualKinetics),
# stepping both from the same state.  Frozen TH, as B2.
#   julia --project=. test/b6_gpu_kin.jl az5 <fmap.h5> <ncompare> [nsteps_gpu]
using RBMKCore.XS, RBMKCore.CoreModel, RBMKCore.Diffusion, RBMKCore.Mixed, RBMKCore.DualKinetics, RBMKCore.GPUDual, CUDA
using Printf, HDF5

const ROOT = joinpath(@__DIR__, "..", "..", "..")
const KSTEM = "rbmk_unit4_a7_acc_pc7e2115_dev_axf527ca_kin700v40g12nofbshvdfr025fi60cc01dt001_vB65c86e_cB4af83e"
const LAMBDA = [1.333600E-02, 3.273900E-02, 1.207800E-01, 3.027800E-01, 8.494900E-01, 2.853000E+00]

mode = get(ARGS, 1, "null")
d = read_deck(joinpath(ROOT, "decks", "Donjon", "data", KSTEM * ".don"))
xsf = joinpath(ROOT, "tierb", "xs", "tierb_xs_af4c362b.h5")       # bracket B fuel + cB CPS
fuel = load_fuel(xsf); ref = load_ref(xsf)
tf = dca = nothing
if length(ARGS) >= 2 && !isempty(ARGS[2])
    h = h5open(ARGS[2]); tf = read(h["T-FUEL"]); dca = read(h["D-COOL"]); close(h)
    println("fuel state from ", ARGS[2], ": TF ", extrema(tf), " DCA ", extrema(dca))
else
    d.fuelstate["TF"] = 900.0; d.fuelstate["DCA"] = 0.72
    println("fuel state: static TF 900 K, DCA 0.72 (mechanics test only)")
end
haskey(d.fuelstate, "TG") || (d.fuelstate["TG"] = 750.0)
base = element_base(d, fuel, ref; tf, dca)
mesh = Mesh(d.nx, d.ny, d.nz, diff(d.meshx), diff(d.meshy), diff(d.meshz),
            [m > 0 ? e : 0 for (e, m) in enumerate(d.mix)])

function problem_at(shift)
    r = apply_rods(base, d, ref, rod_boxes(d; shift))
    p = build_dual(mesh, r.ntot, 1 ./ r.invd, r.scat, base.fiss, r.hfac)
    cells = p.cell
    vol = p.vol
    ng, nd, ni = 2, length(LAMBDA), size(base.nud, 4)
    Pd = [vol .* base.nud[cells, g, dd, i] for g in 1:ng, dd in 1:nd, i in 1:ni]
    chid = [base.chid[cells, g, dd, i] for g in 1:ng, dd in 1:nd, i in 1:ni]
    Fd = [sum(chid[g, dd, i] .* Pd[gp, dd, i] for i in 1:ni) for g in 1:ng, gp in 1:ng, dd in 1:nd]
    p, Fd, Pd, chid, base.overv[cells, :]
end

p0, Fd0, Pd0, chid0, ov0 = problem_at(Dict{Int,Float64}())
G0 = gdual(p0)
t = @elapsed begin
    k0, phig = gsolve_k(G0; tol=1e-6)
    k0, phig, r0 = gwielandt(G0, k0, phig)
end
@printf("t=0 (GPU): k0 = %.9f residual %.2e (%.0f s)\n", k0, r0, t); flush(stdout)
phi = [Array(f) for f in phig]
x0 = dual_kin_xs(p0, Fd0, Pd0, chid0, ov0, k0)
sc = dual_kin_init(x0, phi, LAMBDA, k0)
sg = gkin_init(sc)
P0 = dual_kin_power(x0, sc)
v = 40.0; dt = 0.01
ncmp = parse(Int, get(ARGS, 3, "5")); ngpu = parse(Int, get(ARGS, 4, string(ncmp)))
movers = mode == "null" ? Int[] : vcat(get(d.groups, 1, Int[]), get(d.groups, 2, Int[]))
scache = DualStepCache()
for n in 1:ngpu
    tt = n * dt
    shift = Dict(id => v * tt for id in movers)
    tb = @elapsed begin
        p, Fd, Pd, chid, ov = problem_at(shift)
        x = dual_kin_xs(p, Fd, Pd, chid, ov, k0)
    end
    tu = @elapsed (xg = gkin_xs(x; topo=G0))
    tg = @elapsed (ng_ = gkin_step!(sg, xg, LAMBDA, dt)); CUDA.synchronize()
    Pg = gkin_power(xg, sg) / P0
    if n <= ncmp
        tc = @elapsed (nc_ = dual_kin_step!(sc, x, LAMBDA, dt; cache=scache))
        Pc = dual_kin_power(x, sc) / P0
        dphi = maximum(maximum(abs.(Array(sg.phi[g]) .- sc.phi[g])) / maximum(abs.(sc.phi[g])) for g in 1:2)
        @printf("step %3d t %.2f  CPU P/P0 %.8e (%d it, %.1f s)  GPU %.8e (%d it, %.1f s)  dP %.1e  max dphi %.1e\n",
                n, tt, Pc, nc_, tc, Pg, ng_, tg, (Pg - Pc) / Pc, dphi)
    else
        (n % 10 == 0) && @printf("step %3d t %.2f  GPU P/P0 %.6e  (%d it; build %.1f upload %.1f step %.1f s)\n", n, tt, Pg, ng_, tb, tu, tg)
    end
    flush(stdout)
    gkin_free!(xg)
    (n % 10 == 0 || n <= 3) && (@printf("  device: used %.2f GiB, pool %.2f GiB\n", CUDA.used_memory() / 2^30, CUDA.cached_memory() / 2^30); flush(stdout))
end
