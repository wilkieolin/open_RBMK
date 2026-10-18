# B2: space-time kinetics with rods, frozen thermal-hydraulics.
#   julia --project=. test/b2_kinetics.jl null      # rods held: power flat
#   julia --project=. test/b2_kinetics.jl az5 [fmap.h5] [nsteps]
using RBMKCore.XS, RBMKCore.CoreModel, RBMKCore.Diffusion, RBMKCore.Kinetics
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
    p = build_problem(mesh, r.ntot, 1 ./ r.invd, r.scat, base.fiss, r.hfac)
    cells = p.cell
    vol = p.vol
    ng, nd, ni = 2, length(LAMBDA), size(base.nud, 4)
    Pd = [vol .* base.nud[cells, g, dd, i] for g in 1:ng, dd in 1:nd, i in 1:ni]
    chid = [base.chid[cells, g, dd, i] for g in 1:ng, dd in 1:nd, i in 1:ni]
    Fd = [sum(chid[g, dd, i] .* Pd[gp, dd, i] for i in 1:ni) for g in 1:ng, gp in 1:ng, dd in 1:nd]
    p, Fd, Pd, chid, base.overv[cells, :]
end

p0, Fd, Pd, chid, ov = problem_at(Dict{Int,Float64}())
t = @elapsed (k0, phi) = solve_k_arnoldi(p0)
@printf("t=0: k0 = %.6f  (%.0f s)\n", k0, t); flush(stdout)
x0 = kin_xs(p0, Fd, Pd, chid, ov, k0)
s = kin_init(x0, phi, LAMBDA, k0)
P0 = kin_power(x0, s)
v = 40.0; dt = 0.01
nsteps = parse(Int, get(ARGS, 3, mode == "null" ? "100" : "700"))
movers = vcat(get(d.groups, 1, Int[]), get(d.groups, 2, Int[]))
println("rods: $(length(d.rods)), moving groups 1+2: $(length(movers)) rods")
for n in 1:nsteps
    tt = n * dt
    shift = mode == "null" ? Dict{Int,Float64}() : Dict(id => v * tt for id in movers)
    p, Fd, Pd, chid, ov = problem_at(shift)
    x = kin_xs(p, Fd, Pd, chid, ov, k0)
    te = @elapsed kin_step!(s, x, LAMBDA, dt)
    P = kin_power(x, s)
    (n % 10 == 0 || n <= 3) && (@printf("step %4d t %.2f  P/P0 %.6e  (%.1f s/step)\n", n, tt, P / P0, te); flush(stdout))
end
