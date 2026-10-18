# B2 on the mixed-dual RT0 operator (TRIVAC DUAL 1 1), frozen TH.
#   julia --project=. test/b2_dual.jl null      # rods held: power flat
#   julia --project=. test/b2_dual.jl az5 [fmap.h5] [nsteps]
using RBMKCore.XS, RBMKCore.CoreModel, RBMKCore.Diffusion, RBMKCore.Mixed, RBMKCore.DualKinetics
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

p0, Fd, Pd, chid, ov = problem_at(Dict{Int,Float64}())
# the t = 0 eigenproblem (~13 min on CPU) is cached by a hash of its operator
key = string(hash((p0.K, p0.R, p0.S, p0.F)); base=16)
cache = joinpath(ROOT, "tierb", "xs", "cache", "dual_k_" * key * ".h5")
t = @elapsed if isfile(cache)
    k0, phi = h5open(h -> (read(h["k"]), [read(h["phi$g"]) for g in 1:2]), cache)
    println("t=0 eigenpair from cache ", basename(cache))
else
    k0, phi = solve_k_dual(p0; verbose=true)
    mkpath(dirname(cache))
    h5open(cache, "w") do h; h["k"] = k0; h["phi1"] = phi[1]; h["phi2"] = phi[2]; end
end
# Wielandt polish to a 1e-10 steady residual (the null-transient floor), cached too
pcache = replace(cache, ".h5" => "_w.h5")
if isfile(pcache)
    k0, phi = h5open(h -> (read(h["k"]), [read(h["phi$g"]) for g in 1:2]), pcache)
else
    tw = @elapsed (k0, phi, rw) = dual_wielandt_polish(p0, k0, phi; verbose=true)
    @printf("wielandt polish: k %.9f residual %.2e (%.0f s)\n", k0, rw, tw)
    h5open(pcache, "w") do h; h["k"] = k0; h["phi1"] = phi[1]; h["phi2"] = phi[2]; end
end
@printf("t=0: k0 = %.6f  (%.0f s)\n", k0, t); flush(stdout)
x0 = dual_kin_xs(p0, Fd, Pd, chid, ov, k0)
s = dual_kin_init(x0, phi, LAMBDA, k0)
P0 = dual_kin_power(x0, s)
@printf("t=0 steady residual %.2e\n", dual_steady_residual(x0, phi))
v = 40.0; dt = 0.01
nsteps = parse(Int, get(ARGS, 3, mode == "null" ? "100" : "700"))
movers = vcat(get(d.groups, 1, Int[]), get(d.groups, 2, Int[]))
println("rods: $(length(d.rods)), moving groups 1+2: $(length(movers)) rods")
scache = DualStepCache(); timing = []
for n in 1:nsteps
    tt = n * dt
    shift = mode == "null" ? Dict{Int,Float64}() : Dict(id => v * tt for id in movers)
    tb = @elapsed (p, Fd, Pd, chid, ov) = problem_at(shift)
    x = dual_kin_xs(p, Fd, Pd, chid, ov, k0)
    te = @elapsed (nit = dual_kin_step!(s, x, LAMBDA, dt; cache=scache, timing))
    P = dual_kin_power(x, s)
    (n % 10 == 0 || n <= 3) && (@printf("step %4d t %.2f  P/P0 %.6e  (%d it, %.1f s/step: build %.1f setup %.1f amg %.1f solve %.1f)\n", n, tt, P / P0, nit, te, tb, timing[end]...); flush(stdout))
    n == nsteps && @printf("final t %.2f  P/P0 - 1 = %.3e\n", tt, P / P0 - 1)
end
