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
# or loop (B3b-3: both loop halves, Loop.loop_step! -- drums, pumps, legs, per-channel ZRK lines; the
# TH state at t = 0 is the loop's own after its 01:23:04 -> 01:23:40 run-down at the FMAP power, so the
# t = 0 eigenpair is recomputed on it.  B4_HSH (1.2), B4_VST (296 m3), B4_QG (34 MW): as b3b_loop_core.jl)
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
# B4_CHF=1: the boiling crisis and post-CHF wall heat transfer on the Newton path (Channel's
# ThmOpts.postchf, PROGRESS (49)); B4_CHFMUL: transient CHF enhancement (1, sensitivity 2);
# B4_ZRSEC=1: only the cladding's enthalpy-form heat storage that postchf implies (to separate it)
const CHF = get(ENV, "B4_CHF", "0") == "1"; const CHFMUL = parse(Float64, get(ENV, "B4_CHFMUL", "1"))
const ZRSEC = get(ENV, "B4_ZRSEC", "0") == "1"
o_t = ThmOpts(cflux=critfl, khgap=hgap, maxit1=Int(tv[1]), maxit2=Int(tv[2]), maxitc=Int(tv[3]),
              ermaxt=tv[4], ermaxc=tv[5], cyccap=tv[6], frlx=tv[7], postchf=CHF, chfmul=CHFMUL, zrsec=ZRSEC)
const CHFTAG = (CHF ? "_chf" * (CHFMUL == 1 ? "" : @sprintf("x%g", CHFMUL)) : "") * (ZRSEC && !CHF ? "_zrsec" : "")
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

# --- B4_TH=loop: the loop's run-down from 01:23:04 to AZ-5 (01:23:40) at the FMAP power
if THSOLVER == "loop"
    include("loop_setup.jl"); using SHA, Serialization
    hsh = parse(Float64, get(ENV, "B4_HSH", "1.2")); Vst = parse(Float64, get(ENV, "B4_VST", "296"))
    QgMW = parse(Float64, get(ENV, "B4_QG", "34"))
    # B4_FREEZE=pd|bc: after AZ-5 only (the pre-run, and so the t = 0 state, is unchanged);
    # see Loop.loop_step!'s `freeze` -- the decomposition of the loop's effect (PROGRESS (44))
    FREEZE = Symbol(get(ENV, "B4_FREEZE", "none"))
    dreg = load_dreg()
    XTAG = (get(ENV, "LOOP_PSD_GAUGE", "0") == "1" ? "_pg" : "") * (get(ENV, "LOOP_WREC", "0") == "1" ? "_wrec" : "")
    kfit, npts = infer_rundown(dreg, hsh)
    @printf("loop: run-down pumps a(t) = 1 - %.3e t from %d DREG points (hsh %.2f ASSUMPTION); a(AZ-5) %.4f\n",
            kfit, npts, hsh, 1 - 36kfit)
    pp = PumpParams(hsh=hsh); leg = leg_unit4(pp; Vsteam=Vst)
    halves = build_halves(chans, hz, hx, hy, pw0, burn, tf, speed, pout, tin, clus, radius, rodm, o_s, pp, leg, QgMW, dreg)
    # the run-down pumps: the DREG-fitted a(t) also through the 7 s after AZ-5 (an ASSUMPTION:
    # the trip/coast times of pumps 3, 4 are not sourced; DREG flows exist to 01:23:43)
    rundown(tabs) = Any[:grid, :grid, max(0.0, 1 - kfit * tabs) * pp.wr, max(0.0, 1 - kfit * tabs) * pp.wr]
    # LOOP_WREC=1 (starting-state probe, PROGRESS (49)): through the pre-run each half's pump flow
    # is the DREG record (loop_step!'s Wpres) -- the recorded -12/-14 % that the model's own pumps
    # and leg do not give (43); the leg loss it implies (Loop.KEFF) is averaged over the last
    # second before AZ-5 and held after it (an ASSUMPTION: the cause of the drop is unsourced; it
    # enters as a leg resistance).  The post-AZ-5 record stays a check.
    WREC = get(ENV, "LOOP_WREC", "0") == "1"
    PGAUGE = get(ENV, "LOOP_PSD_GAUGE", "0") == "1"
    kacc = Dict("L" => Float64[], "R" => Float64[])
    function loop_advance!(tabs, dtl, chpow)
        for side in ("L", "R")
            H = halves[side]; Lh = H.L
            wfw = dinterp(dreg, side, "Gfw", tabs) / 3.6
            hfw = prop_pT97(Lh.pd, dinterp(dreg, side, "Tfw", tabs) + 273.15).h
            Wp = (WREC && tabs <= 36.0 + 1e-9) ? dreg_flow(dreg, side, tabs, Lh.pd) : nothing
            loop_step!(Lh, H.g, o_t, [chpow(i) for i in H.idx], H.burn, dtl; wst=0.0, wfw, hfw,
                       pumpmode=rundown(tabs), qext=H.qext, freeze=tabs > 36.0 ? FREEZE : :none, Wpres=Wp)
            if Wp !== nothing
                tabs >= 35.0 - 1e-9 && push!(kacc[side], RBMKCore.Loop.KEFF[Lh])
                if tabs >= 36.0 - 1e-9
                    kf = sum(kacc[side]) / length(kacc[side]); lg = Lh.leg
                    Lh.leg = RBMKCore.Loop.LegParams(I=lg.I, Kf=kf, Kpipe=lg.Kpipe, dz=lg.dz, Vdrum=lg.Vdrum,
                                                     Vsteam=lg.Vsteam, npump=lg.npump, sourced=false)
                    @printf("  %s: recorded flow imposed to AZ-5; leg loss held after it: Kf %.4g (was %.4g, x%.2f)\n",
                            side, kf, lg.Kf, kf / lg.Kf)
                end
            end
        end
    end
    loopline(tabs) = join([@sprintf("%s pd %.3f (DREG %.2f) ph %.3f W %.0f tin %.2f", s, halves[s].L.pd / LKGF,
                                    dinterp(dreg, s, "Psd", tabs), halves[s].L.ph / LKGF, halves[s].L.W,
                                    halves[s].L.tin - 273.15) for s in ("L", "R")], " | ")
    function loop_to_fmap!(tf, dca)
        for side in ("L", "R"), (j, i) in enumerate(halves[side].idx)
            st = halves[side].L.chans[j]
            for (ib, iz) in enumerate(chans[i][3])
                tf[(ib-1)*nch+i] = st.tcomb[iz]; dca[(ib-1)*nch+i] = st.rho[iz] / 1e3
            end
        end
    end
    powfmap = Dict(i => H.pow[j] for H in values(halves) for (j, i) in enumerate(H.idx))
    # the pre-run is ~40 min: cached on the content of everything it depends on (the TH sources,
    # this setup, the DREG record, the t = 0 FMAP and the deck) and its parameters
    srcs = [joinpath(@__DIR__, "..", "src", f) for f in ("Channel.jl", "Column.jl", "Loop.jl", "IF97.jl")]
    push!(srcs, joinpath(@__DIR__, "loop_setup.jl"), joinpath(LROOT, "sources", "derived", "dreg_mfcc_full.csv"),
          joinpath(dumpdir, "fmap0.asc"), deckpath)
    prekey = bytes2hex(sha1(join([read(f, String) for f in srcs]) * string((hsh, Vst, QgMW, get(ENV, "DRUM_TAU", "eq"))) * (PGAUGE ? "pg" : "") * (WREC ? "wrec" : "") * CHFTAG))[1:12]
    precache = joinpath(dumpdir, "b4_loop_prerun_" * prekey * ".jls")
    # explicit override, for a code change that only touches paths which failed before (logged)
    haskey(ENV, "B4_PRERUN_FILE") && (precache = ENV["B4_PRERUN_FILE"];
                                      println("EXPLICIT OVERRIDE: pre-run from ", precache, " (key would be ", prekey, ")"))
    tpre = 0.0
    if isfile(precache)
        halves = deserialize(precache)
        println("loop pre-run from cache ", basename(precache), ": ", loopline(36.0))
    else
        tpre = @elapsed for n in 1:72
            loop_advance!(0.5n, 0.5, i -> powfmap[i])
            n % 8 == 0 && (println(@sprintf("  pre-run t %4.1f  ", 0.5n), loopline(0.5n)); flush(stdout))
        end
        serialize(precache, halves)
    end
    tf0d = copy(tf); dca0d = copy(dca)
    loop_to_fmap!(tf, dca)
    @printf("loop at AZ-5 (%.0f s): vs DONJON's FMAP T-FUEL max |d| %.1f K, D-COOL %.4f-%.4f (DONJON %.4f-%.4f)\n",
            tpre, maximum(abs.(tf .- tf0d)), extrema(dca)..., extrema(dca0d)...)
end

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
THSOLVER == "loop" || Threads.@threads for ich in 1:nch
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
if THSOLVER != "loop"
    tfs = [states[ich].tcomb[chans[ich][3][ib]] for ib in 1:nb for ich in 1:nch]
    @printf("t=0 TH rebuilt: T-FUEL vs FMAP0 max |d| %.3f K\n", maximum(abs.(tfs .- tf)))
end

# --- the transient
movers = vcat(get(d.groups, 1, Int[]), get(d.groups, 2, Int[]))
out = open(joinpath(dumpdir, @sprintf("b4_trace_dt%g%s.txt", dt, THSOLVER == "col" ? "_col" * string(SCHEME) :
                                                            THSOLVER == "newton" ? "_newton" * CHFTAG :
                                                            THSOLVER == "loop" ? @sprintf("_loop_h%g_v%g_q%g", hsh, Vst, QgMW) * (haskey(ENV, "DRUM_TAU") ? "_tau" * ENV["DRUM_TAU"] : "") * XTAG * CHFTAG * (FREEZE === :none ? "" : "_frz" * string(FREEZE)) : "")), "w")
println(out, "# t_s P/P0 E_GJ TFmax_K DCAmin ncyc kin_it")
# fuel / cladding against the failure criteria, every step (test/fuel_diag.jl)
include("fuel_diag.jl")
fuel_items() = THSOLVER == "loop" ?
    [(H.g[j], H.L.chans[j], chans[i][3]) for H in values(halves) for (j, i) in enumerate(H.idx)] :
    [(geoms[ich], states[ich], chans[ich][3]) for ich in 1:nch]
fout = open(replace(out.name[7:end-1], "b4_trace_" => "b4_fuel_"), "w")
println(fout, fuel_header()); fd0 = fuel_diag(fuel_items())
@printf(fout, "# total fuel %.2f t; t = 0: %s\n", fd0.mtot / 1e3, fuel_line(0.0, fd0))
# power shape against INSAG-7's Kv / Kr / Kz, and the adiabatic local energy (test/shape_diag.jl);
# bundle powers every 0.1 s from 3.5 s appended to b4_pw_*.bin as (t, pwk) Float64 records
include("shape_diag.jl")
sacc = ShapeAcc(pw0, nch, nb, fd0.mtot / length(pw0))
sout = open(replace(out.name[7:end-1], "b4_trace_" => "b4_shape_"), "w")
println(sout, shape_header()); println(sout, shape_line!(sacc, 0.0, 0.0, pw0))
pwout = open(replace(replace(out.name[7:end-1], "b4_trace_" => "b4_pw_"), ".txt" => ".bin"), "w")
THSOLVER == "loop" && (lout = open(joinpath(dumpdir, @sprintf("b4_loop_dt%g_h%g_v%g_q%g", dt, hsh, Vst, QgMW) * (haskey(ENV, "DRUM_TAU") ? "_tau" * ENV["DRUM_TAU"] : "") * XTAG * CHFTAG * (FREEZE === :none ? "" : "_frz" * string(FREEZE)) * ".txt"), "w"))
energy = 0.0; Pprev = P0MW
# B4_TH=loop checkpoints (the transient is hours): every B4_CKPT steps the kinetics state, the loop
# halves, the FMAP fields and the trace lines; B4_RESUME=1 restarts from the latest.  Keyed on the
# pre-run key, dt and the driver's and kinetics' sources.
n0 = 0; trl = String[]; lol = String[]
if THSOLVER == "loop"
    CKPT = parse(Int, get(ENV, "B4_CKPT", "50"))
    ckkey = bytes2hex(sha1(prekey * string(dt) * string(FREEZE) * read(@__FILE__, String) *
                           read(joinpath(@__DIR__, "..", "src", "GPUDual.jl"), String) *
                           read(joinpath(@__DIR__, "..", "src", "DualKinetics.jl"), String)))[1:12]
    ckfile = joinpath(dumpdir, "b4_loop_ckpt_" * ckkey * ".jls")
    haskey(ENV, "B4_CKPT_FILE") && (ckfile = ENV["B4_CKPT_FILE"];
                                    println("EXPLICIT OVERRIDE: checkpoint ", ckfile, " (key would be ", ckkey, ")"))
    if get(ENV, "B4_RESUME", "0") == "1" && isfile(ckfile)
        ck = deserialize(ckfile)
        global n0 = ck.n; global energy = ck.energy; global Pprev = ck.Pprev; global halves = ck.halves
        tf .= ck.tf; dca .= ck.dca; global trl = ck.trl; global lol = ck.lol
        global sg = GKinState(map(CuArray, ck.phi), map(CuArray, ck.C), map(CuArray, ck.Pd), ck.t)
        foreach(l -> println(out, l), trl); foreach(l -> println(lout, l), lol)
        hasproperty(ck, :eadia) ? (sacc.e .= ck.eadia) : println("checkpoint has no adiabatic energies: b4_shape's Eadia restarts at 0")
        println("resumed from ", basename(ckfile), " at step ", n0)
    end
end
for n in n0+1:nsteps
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
    tth = THSOLVER == "loop" ? @elapsed(begin
        try
            loop_advance!(36.0 + tt, dt, i -> (pw = zeros(nz); for (ib, iz) in enumerate(chans[i][3]);
                                                                 pw[iz] = pwk[(ib-1)*nch+i] * 1e3; end; pw))
        catch e
            fd = RBMKCore.Loop.FAILDUMP[]
            fd === nothing || (serialize(joinpath(dumpdir, @sprintf("b4_loop_colfail_t%.2f.jls", tt)), fd);
                               println("failing channel step dumped (channel ", fd.i, ")"))
            rethrow()
        end
        loop_to_fmap!(tf, dca)
        # (ncyc in loop mode: channel steps accepted under Loop.LOOSE this step; worst |r| so far)
        LN = RBMKCore.Column.Lines
        Threads.atomic_add!(ncyc, LN.LOOSE_N[]); LN.LOOSE_N[] = 0
        ll = @sprintf("%.4f ", tt) * loopline(36.0 + tt) * @sprintf(" | loose %d worst %.2e", ncyc[], LN.LOOSE_MAX[])
        push!(lol, ll)
        println(lout, ll); flush(lout)
    end) : @elapsed Threads.@threads for ich in 1:nch
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
    tl = @sprintf("%.4f %.6e %.5e %.2f %.5f %d %d", tt, P, energy, maximum(tf), minimum(dca), ncyc[], nit)
    println(out, tl); push!(trl, tl)
    THSOLVER in ("loop", "newton") && (println(fout, fuel_line(tt, fuel_diag(fuel_items()))); flush(fout))
    println(sout, shape_line!(sacc, tt, dt, pwk)); flush(sout)
    (tt >= 3.5 - 1e-9 && n % 10 == 0) && (write(pwout, tt); write(pwout, pwk); flush(pwout))
    if THSOLVER == "loop" && n % CKPT == 0
        serialize(ckfile * ".tmp", (; n, energy, Pprev, halves, tf, dca, trl, lol, phi=map(Array, sg.phi),
                                    C=map(Array, sg.C), Pd=map(Array, sg.Pd_old), t=sg.t, eadia=sacc.e))
        mv(ckfile * ".tmp", ckfile; force=true)
    end
    flush(out)
    (n % 10 == 0 || n <= 3) && (@printf("step %4d t %.2f  P/P0 %.5e  E %.3f GJ  TFmax %.1f  DCAmin %.4f  ncyc %d  (%d it; build %.1f kin %.1f th %.1f s)\n",
                                       n, tt, P, energy, maximum(tf), minimum(dca), ncyc[], nit, tb, tk, tth); flush(stdout))
end
close(out); close(fout); close(sout); close(pwout); THSOLVER == "loop" && close(lout)
