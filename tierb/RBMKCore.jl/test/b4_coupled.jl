# B4: the coupled transient -- RT0 kinetics (DualKinetics) + the THM: port
# (Channel) in the A8 deck's own order, against DONJON's band runs:
#   MOVDEV (rods), NCR on the FMAP state, KINSOL, FLPOW (bundle powers),
#   THM: transient (new T-FUEL, D-COOL for the next step).
# The coupling is explicit, as in the deck: the cross sections of step n
# use the TH state left by step n-1.
#
#   JULIA_CUDA_HARD_MEMORY_LIMIT=8GiB julia --project=. -t 8 test/b4_coupled.jl <stem> <t=0 dump dir> [nsteps] [dt]
# Kinetics on the GPU (GPUDual, = the CPU DualKinetics to 1e-11), TH on the CPU threads.
# <t=0 dump dir>: tools/tierb_kinref.py <stem> --dual --t0only (fmap0.asc).
using RBMKCore.XS, RBMKCore.CoreModel, RBMKCore.Diffusion, RBMKCore.Mixed, RBMKCore.DualKinetics
using RBMKCore.LcmAscii, RBMKCore.Channel, RBMKCore.Water, RBMKCore.GPUDual, RBMKCore.Column, RBMKCore.IF97, CUDA
import RBMKCore
using RBMKCore.Column.Lines: col_step_newton_flux, NewtonCache
# TH solver: B4_TH=thmtrs (the THMTRS port, default), col (Column, the B3b march, scheme B4_SCHEME=thm|fv)
# or newton (Column.Lines.col_step_newton_flux: THM's boundary conditions, simultaneous Newton, smooth closures)
const THSOLVER = get(ENV, "B4_TH", "thmtrs"); const SCHEME = Symbol(get(ENV, "B4_SCHEME", "thm"))
using Printf, HDF5

const ROOT = joinpath(@__DIR__, "..", "..", "..")
const LAMBDA = [1.333600E-02, 3.273900E-02, 1.207800E-01, 3.027800E-01, 8.494900E-01, 2.853000E+00]
const P0MW = 200.0                     # INIKIN NORM POWER-INI

stem = ARGS[1]; dumpdir = ARGS[2]
nsteps = parse(Int, get(ARGS, 3, "700")); dt = parse(Float64, get(ARGS, 4, "0.01"))
deckpath = joinpath(ROOT, "decks", "Donjon", "data", stem * ".don")
d = read_deck(deckpath)
haskey(d.fuelstate, "TG") || (d.fuelstate["TG"] = 750.0)
# the cross-section export for the deck's COMPOs: bracket B fuel (vB65c86e) or production, + cB CPS
@assert occursin("cB4af83e", stem) "cross sections: the exports carry the cB CPS only"
xsf = joinpath(ROOT, "tierb", "xs", occursin("vB65c86e", stem) ? "tierb_xs_af4c362b.h5" : "tierb_xs_664b244a.h5")
ncrclamp = occursin("MACRO LINEAR CLAMP", read(deckpath, String))   # U4_NCRCLAMP decks (patch 0014)
println("cross sections ", basename(xsf), ncrclamp ? ", NCR CLAMP" : "")
fuel = load_fuel(xsf); ref = load_ref(xsf)
mesh = Mesh(d.nx, d.ny, d.nz, diff(d.meshx), diff(d.meshy), diff(d.meshz),
            [m > 0 ? e : 0 for (e, m) in enumerate(d.mix)])

# --- THM: keywords of the deck (steady call) and the A8 transient's
deck = read(deckpath, String)
blk = deck[findfirst("  THER FMAP := THM: FMAP ::", deck).start:end]
blk = blk[1:findfirst("\n    ;\n", blk).stop]
num(key) = parse.(Float64, split(match(Regex(key * raw"\s+([-0-9.E+ ]+)\n"), blk).captures[1]))
pout, tin = num("INLET"); radius = num("RADIUS"); clus = num("CLUSTER"); rodm = Int.(num("RODMESH"))
conv = num("CONV"); hgap = num("HGAP")[1]; critfl = num("CRITFL")[1]
sp = blk[findfirst("SPEED CHAN", blk).stop+1:findfirst("CLUSTER", blk).start-1]
speed = [parse(Float64, t) for l in split(sp, '\n') if !startswith(strip(l), "*") for t in split(l)]
@assert length(speed) == 1661
tr = match(r"THM: THER FMAP :: EDIT 0 TIME <<t0>> <<dt>> HISTORY 2\s+CONV (\S+) (\S+) (\S+) (\S+) (\S+) CYCLE-OK (\S+) FLOW-RELAX (\S+) ;", deck)
@assert tr !== nothing "transient THM: call not found"
tv = parse.(Float64, tr.captures)
o_s = ThmOpts(cflux=critfl, khgap=hgap, maxit1=Int(conv[1]), maxit2=Int(conv[2]), ermaxt=conv[4])
o_t = ThmOpts(cflux=critfl, khgap=hgap, maxit1=Int(tv[1]), maxit2=Int(tv[2]), maxitc=Int(tv[3]),
              ermaxt=tv[4], ermaxc=tv[5], cyccap=tv[6], frlx=tv[7])
println("THM: INLET $pout $tin, transient CONV $(tv[1:5]) CYCLE-OK $(tv[6]) FLOW-RELAX $(tv[7])")

# --- t = 0 FMAP from DONJON
rf = lcm_read(joinpath(dumpdir, "fmap0.asc"))
par = lcm_params(rf)
tf = copy(par["T-FUEL"]); dca = copy(par["D-COOL"])
pw0 = lcm_get(rf, "BUND-PW"); burn = lcm_get(rf, "BURN-INST")
mx = lcm_get(rf, "MESHX"); my = lcm_get(rf, "MESHY"); mz = lcm_get(rf, "MESHZ")
nx, ny, nz = length(mx) - 1, length(my) - 1, length(mz) - 1
hx, hy, hz = diff(mx) ./ 100, diff(my) ./ 100, diff(mz) ./ 100
bmix = lcm_get(rf, "BMIX")
chans = Tuple{Int,Int,Vector{Int}}[]
for iy in 1:ny, ix in 1:nx
    iel = (iy - 1) * nx + ix
    planes = [iz for iz in 1:nz if bmix[(iz-1)*nx*ny+iel] != 0]
    isempty(planes) || push!(chans, (ix, iy, planes))
end
nch = length(chans); nb = length(chans[1][3])
@printf("t=0 FMAP: %d channels x %d bundles, BUND-PW %.3f MW, TF %.1f-%.1f K, DCA %.4f-%.4f\n",
        nch, nb, sum(pw0) / 1e3, extrema(tf)..., extrema(dca)...)

# --- neutronics
function problem_at(base, shift)
    r = apply_rods(base, d, ref, rod_boxes(d; shift))
    p = build_dual(mesh, r.ntot, 1 ./ r.invd, r.scat, base.fiss, r.hfac)
    cells = p.cell; vol = p.vol
    ng, nd, ni = 2, length(LAMBDA), size(base.nud, 4)
    Pd = [vol .* base.nud[cells, g, dd, i] for g in 1:ng, dd in 1:nd, i in 1:ni]
    chid = [base.chid[cells, g, dd, i] for g in 1:ng, dd in 1:nd, i in 1:ni]
    Fd = [sum(chid[g, dd, i] .* Pd[gp, dd, i] for i in 1:ni) for g in 1:ng, gp in 1:ng, dd in 1:nd]
    p, Fd, Pd, chid, base.overv[cells, :]
end
base = element_base(d, fuel, ref; tf, dca, clamp=ncrclamp)
p0, Fd0, Pd0, chid0, ov0 = problem_at(base, Dict{Int,Float64}())
fuelcell = findall(i -> sum(base.fiss[p0.cell[i], :, :]) > 0, eachindex(p0.cell))
@assert length(fuelcell) == nch * nb
key = string(hash((p0.K, p0.R, p0.S, p0.F)); base=16)
cache = joinpath(ROOT, "tierb", "xs", "cache", "dual_k_" * key * "_w.h5")
G0 = gdual(p0)
if isfile(cache)
    k0, phi = h5open(h -> (read(h["k"]), [read(h["phi$g"]) for g in 1:2]), cache)
    println("t=0 eigenpair from cache ", basename(cache))
else
    t = @elapsed begin
        k0, phig = gsolve_k(G0; tol=1e-6)
        k0, phig, rw = gwielandt(G0, k0, phig)
    end
    phi = [Array(f) for f in phig]
    @printf("t=0 eigenpair (GPU): k %.9f residual %.2e (%.0f s)\n", k0, rw, t)
    mkpath(dirname(cache))
    h5open(cache, "w") do h; h["k"] = k0; h["phi1"] = phi[1]; h["phi2"] = phi[2]; end
end
x0 = dual_kin_xs(p0, Fd0, Pd0, chid0, ov0, k0)
s = dual_kin_init(x0, phi, LAMBDA, k0)
sg = gkin_init(s)
Pall0 = dual_kin_power(x0, s)
# FLPOW: BUND-PW (kW) = E-POW * (H phi V)_bundle / sum_all (H phi V)
cellpow(p, phi) = sum(p.hfac[:, g] .* phi[g] .* p.vol for g in 1:2)
bundle_kw(pc, epow) = pc[fuelcell] .* (epow * 1e3 / sum(pc))
pwn = bundle_kw(cellpow(p0, phi), P0MW)
@printf("t=0: k0 %.6f; bundle powers vs DONJON BUND-PW: rms %.3f %%  max %.3f %%\n", k0,
        100 * sqrt(sum(((pwn .- pw0) ./ pw0) .^ 2) / length(pw0)), 100 * maximum(abs.((pwn .- pw0) ./ pw0)))

# --- TH: channel states from a steady THM: on DONJON's t = 0 power
geoms = Vector{ChanGeom}(undef, nch); states = Vector{Any}(undef, nch); burns = Vector{Vector{Float64}}(undef, nch)
Threads.@threads for ich in 1:nch
    ix, iy, planes = chans[ich]
    g = chan_geom(hz, hx[ix] * hy[iy]; pitch=clus[1], nfuel=clus[2], rc=radius[1], rig=radius[2], rgg=radius[3],
                  nfd=rodm[1], ndtot=rodm[2])
    pow = zeros(nz); bu = zeros(nz); t0 = fill(900.0, nz)
    for (ib, iz) in enumerate(planes)
        ima = (ib - 1) * nch + ich
        pow[iz] = pw0[ima] * 1e3; bu[iz] = burn[ima]; t0[iz] = tf[ima]
    end
    geoms[ich] = g; burns[ich] = bu
    st = thm_steady(g, o_s, pow, bu, speed[ich], tin, pout; tcomb0=t0)
    states[ich] = THSOLVER in ("col", "newton") ? col_from_steady(st, g, speed[ich], tin, pout) : st
end
caches = [NewtonCache() for _ in 1:nch]
if THSOLVER == "newton"
    # how far THM's steady state is from the Newton model's own (local onset, tight
    # closures): reported, not applied -- the transient starts from DONJON's state
    dd = zeros(nch); dt_ = zeros(nch)
    Threads.@threads for ich in 1:nch
        planes = chans[ich][3]; pow = zeros(nz)
        for (ib, iz) in enumerate(planes); pow[iz] = pw0[(ib-1)*nch+ich] * 1e3; end
        x = states[ich]
        for _ in 1:3
            x = col_step_newton_flux(geoms[ich], o_t, x, pow, burns[ich], speed[ich] * prop_pT97(pout, tin).rho, tin, 1e5)
        end
        dd[ich] = maximum(abs(x.rho[iz] - states[ich].rho[iz]) for iz in planes)
        dt_[ich] = maximum(abs(x.tcomb[iz] - states[ich].tcomb[iz]) for iz in planes)
    end
    @printf("Newton model's own steady vs THM's: D-COOL max |d| %.2e g/cc (channel %d), T-FUEL max |d| %.3f K\n",
            maximum(dd) / 1e3, argmax(dd), maximum(dt_))
end
println("TH solver: ", THSOLVER, THSOLVER == "col" ? " ($SCHEME)" : "")
tfs = [states[ich].tcomb[chans[ich][3][ib]] for ib in 1:nb for ich in 1:nch]
@printf("t=0 TH rebuilt: T-FUEL vs FMAP0 max |d| %.3f K\n", maximum(abs.(tfs .- tf)))

# --- the transient
movers = vcat(get(d.groups, 1, Int[]), get(d.groups, 2, Int[]))
out = open(joinpath(dumpdir, @sprintf("b4_trace_dt%g%s.txt", dt, THSOLVER == "col" ? "_col" * string(SCHEME) :
                                                            THSOLVER == "newton" ? "_newton" : "")), "w")
println(out, "# t_s P/P0 E_GJ TFmax_K DCAmin ncyc kin_it")
energy = 0.0; Pprev = P0MW
for n in 1:nsteps
    tt = n * dt
    shift = Dict(id => 40.0 * tt for id in movers)
    tb = @elapsed begin
        b = element_base(d, fuel, ref; tf, dca, clamp=ncrclamp)
        p, Fd, Pd, chid, ov = problem_at(b, shift)
        x = dual_kin_xs(p, Fd, Pd, chid, ov, k0)
    end
    tk = @elapsed begin
        xg = gkin_xs(x; topo=G0)
        nit = gkin_step!(sg, xg, LAMBDA, dt)
        gkin_free!(xg)
        pc = cellpow(x.p, [Array(f) for f in sg.phi])
    end
    P = sum(pc) / Pall0
    pwk = bundle_kw(pc, P0MW * P)
    ncyc = Threads.Atomic{Int}(0)
    tth = @elapsed Threads.@threads for ich in 1:nch
        planes = chans[ich][3]
        pow = zeros(nz)
        for (ib, iz) in enumerate(planes)
            pow[iz] = pwk[(ib-1)*nch+ich] * 1e3
        end
        if THSOLVER == "col"
            s1 = col_step(geoms[ich], o_t, states[ich], pow, burns[ich], speed[ich] * prop_pT97(pout, tin).rho, tin, dt;
                          scheme=SCHEME)
            Threads.atomic_add!(ncyc, s1.substeps)          # (column: sub-steps taken)
            dcol = s1.rho
        elseif THSOLVER == "newton"
            s1 = col_step_newton_flux(geoms[ich], o_t, states[ich], pow, burns[ich], speed[ich] * prop_pT97(pout, tin).rho,
                                      tin, dt; cache=caches[ich])
            Threads.atomic_add!(ncyc, s1.substeps)
            dcol = s1.rho
        else
            s1 = thm_transient(geoms[ich], o_t, states[ich], pow, burns[ich], speed[ich], tin, pout, dt)
            Threads.atomic_add!(ncyc, s1.ncyc)
            dcol = s1.dcool
        end
        states[ich] = s1
        for (ib, iz) in enumerate(planes)
            tf[(ib-1)*nch+ich] = s1.tcomb[iz]; dca[(ib-1)*nch+ich] = dcol[iz] / 1e3
        end
    end
    global energy += 0.5 * (Pprev + P0MW * P) * dt / 1e3; global Pprev = P0MW * P
    @printf(out, "%.4f %.6e %.5e %.2f %.5f %d %d\n", tt, P, energy, maximum(tf), minimum(dca), ncyc[], nit)
    flush(out)
    (n % 10 == 0 || n <= 3) && (@printf("step %4d t %.2f  P/P0 %.5e  E %.3f GJ  TFmax %.1f  DCAmin %.4f  ncyc %d  (%d it; build %.1f kin %.1f th %.1f s)\n",
                                       n, tt, P, energy, maximum(tf), minimum(dca), ncyc[], nit, tb, tk, tth); flush(stdout))
end
close(out)
