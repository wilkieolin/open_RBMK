# B3b-3 core-wide loop model, thermal-hydraulics only: 01:23:04 (turbine stop valves shut,
# four MCPs start running down with TG-8) to 01:23:40 (AZ-5), against the DREG record.
#
#   julia --project=. -t 10 test/b3b_loop_core.jl <stem> <dumpdir> [hsh=1.2] [Vsteam=296] [Qg_MW=34] [dt=0.5]
#
# Power field: the deck's t = 0 FMAP (BUND-PW, 200 MW), held -- INSAG-7: no power increase
# during the run-down.  Neutronics off.  Boundary conditions, all from records:
#   drums      DREG Psd at 01:23:04 (63.2 L, 64.5 R kgf/cm2, read as ABSOLUTE)
#   steam      none after 01:23:04 (stop valves shut; BRU-K only at 01:23:48)
#   feedwater  DREG Gfw/Tfw per side, interpolated
#   pumps      1, 2 of each side at 1000 rpm (grid); 3, 4 at the speed inferred from the DREG
#              flows (common pressure rise, head curve with shut-off ratio hsh -- the
#              ASSUMPTION), as a linear run-down fitted to all four pumps' inferred points
#   channels   the deck's A7 valving (SPEED CHAN) sets each channel's flow at 01:23:04; its
#              ZRK throat is closed from that state, with xi(A) from [ALM98] Fig. 5.5
#   split      loops by the core's x mid-line (decision 5: an ASSUMPTION, 50/50)
#   graphite   Qg MW into the fuel channels' coolant (tools/graphite_heat.py: 26-40 MW),
#              distributed like the channel power
# Outputs: per side and time, drum pressure, each pump's flow, pump-inlet temperature, the
# drum level change -- each against DREG.  Written to <dumpdir>/b3b_loop_core_<tag>.csv.
using RBMKCore.LcmAscii, RBMKCore.Channel, RBMKCore.Column, RBMKCore.Column.Lines, RBMKCore.Loop, RBMKCore.IF97
import RBMKCore
using Printf, Statistics

const ROOT = joinpath(@__DIR__, "..", "..", "..")
const KGF = 98066.5
stem = ARGS[1]; dumpdir = ARGS[2]
hsh = parse(Float64, get(ARGS, 3, "1.2")); Vst = parse(Float64, get(ARGS, 4, "296"))
QgMW = parse(Float64, get(ARGS, 5, "34")); dt = parse(Float64, get(ARGS, 6, "0.5"))
tag = @sprintf("h%g_v%g_q%g_dt%g", hsh, Vst, QgMW, dt)

# ---------------------------------------------------------------- DREG
dreg = Dict{Tuple{String,String},Vector{Tuple{Float64,Float64}}}()
for l in eachline(joinpath(ROOT, "sources", "derived", "dreg_mfcc_full.csv"))
    (startswith(l, "#") || startswith(l, "side")) && continue
    side, tm, p, v = split(l, ",")
    tryparse(Float64, v) === nothing && continue
    h, m, s = parse.(Int, split(tm, ":"))
    t = (h - 1) * 3600 + (m - 23) * 60 + s - 4.0          # s after 01:23:04
    push!(get!(dreg, (side, p), Tuple{Float64,Float64}[]), (t, parse(Float64, v)))
end
function interp(side, p, t)
    pts = sort(dreg[(side, p)])
    t <= pts[1][1] && return pts[1][2]
    t >= pts[end][1] && return pts[end][2]
    k = findlast(x -> x[1] <= t, pts); (t0, v0), (t1, v1) = pts[k], pts[k+1]
    v0 + (v1 - v0) * (t - t0) / (t1 - t0)
end

# ---------------------------------------------------------------- deck and t = 0 FMAP
deckpath = joinpath(ROOT, "decks", "Donjon", "data", stem * ".don")
deck = read(deckpath, String)
blk = deck[findfirst("  THER FMAP := THM: FMAP ::", deck).start:end]
blk = blk[1:findfirst("\n    ;\n", blk).stop]
num(key) = parse.(Float64, split(match(Regex(key * raw"\s+([-0-9.E+ ]+)\n"), blk).captures[1]))
pout, tin_deck = num("INLET"); radius = num("RADIUS"); clus = num("CLUSTER"); rodm = Int.(num("RODMESH"))
conv = num("CONV"); hgap = num("HGAP")[1]; critfl = num("CRITFL")[1]
sp = blk[findfirst("SPEED CHAN", blk).stop+1:findfirst("CLUSTER", blk).start-1]
speed = [parse(Float64, t) for l in split(sp, '\n') if !startswith(strip(l), "*") for t in split(l)]
o = ThmOpts(cflux=critfl, khgap=hgap, maxit1=Int(conv[1]), maxit2=Int(conv[2]), ermaxt=conv[4])
rf = lcm_read(joinpath(dumpdir, "fmap0.asc"))
par = lcm_params(rf)
tf0 = par["T-FUEL"]; pw0 = lcm_get(rf, "BUND-PW"); burn = lcm_get(rf, "BURN-INST")
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
nch = length(chans)
@assert nch == 1661 && length(speed) == 1661
xmid = 0.5 * (minimum(c[1] for c in chans) + maximum(c[1] for c in chans))
sides = Dict("L" => [i for i in 1:nch if chans[i][1] <= xmid], "R" => [i for i in 1:nch if chans[i][1] > xmid])
SUB = parse(Int, get(ENV, "B3B_SUB", "1"))          # smoke tests: every SUB-th channel stands for SUB
tag *= SUB == 1 ? "" : "_sub$SUB"
@printf("deck %s: INLET %.4f MPa %.2f K; loops split at x %.1f: L %d, R %d channels\n", stem, pout / 1e6, tin_deck,
        xmid, length(sides["L"]), length(sides["R"]))

# ---------------------------------------------------------------- pumps: speeds from DREG flows
pp = PumpParams(hsh=hsh)
apts = Tuple{Float64,Float64}[]
for side in ("L", "R")
    ts = sort(unique([t for p in ("Gmcp1", "Gmcp2", "Gmcp3", "Gmcp4") for (t, _) in dreg[(side, p)]]))
    for t in ts
        (0.0 <= t <= 36.0) || continue
        val(p) = (x = filter(z -> z[1] == t, dreg[(side, p)]); isempty(x) ? nothing : x[1][2])
        g = filter(!isnothing, [val("Gmcp1"), val("Gmcp2")]); c = filter(!isnothing, [val("Gmcp3"), val("Gmcp4")])
        (isempty(g) || isempty(c)) && continue
        vg = mean(g) / 8.0
        for q in c
            push!(apts, (t, sqrt(max(0.0, (hsh - (hsh - 1) * (vg^2 - (q / 8.0)^2)) / hsh))))
        end
    end
end
# least squares a(t) = 1 - k t (the run-down starts at 01:23:04 from full speed)
kfit = -sum(t * (a - 1) for (t, a) in apts) / sum(t^2 for (t, _) in apts)
@printf("run-down pumps: %d inferred speed points, a(t) = 1 - %.3e t  (a = %.4f at 01:23:40); hsh %.2f (ASSUMPTION)\n",
        length(apts), kfit, 1 - 36kfit, hsh)
speedfrac(t) = max(0.0, 1 - kfit * t)

# ---------------------------------------------------------------- channels and loop halves
leg = leg_unit4(pp; Vsteam=Vst)
@printf("leg: I %.1f 1/m, loss at nominal %.2f kgf/cm2 (pipe %.2f + closed), drum %.0f m3 + steam piping %.0f m3\n",
        leg.I, leg.Kf * 5208^2 / 768 / KGF, leg.Kpipe * 5208^2 / 768 / KGF, leg.Vdrum, leg.Vsteam)
# [ALM98] Fig. 5.5: xi of the ZRK throat area (mm2) -- the velocity-head reduction of its curves
const XIA = [(54.0, 1.39), (102.0, 1.39), (153.0, 0.98), (206.0, 0.84), (263.0, 0.85), (319.0, 0.70),
             (437.0, 0.68), (691.0, 0.65)]
function xi_of(Amm2)
    Amm2 <= XIA[1][1] && return XIA[1][2]; Amm2 >= XIA[end][1] && return XIA[end][2]
    k = findlast(x -> x[1] <= Amm2, XIA); (a0, x0), (a1, x1) = XIA[k], XIA[k+1]
    x0 + (x1 - x0) * (Amm2 - a0) / (a1 - a0)
end
Gsum = sum(speed[i] * prop_pT97(pout, tin_deck).rho * 22.427082e-4 for i in 1:nch)
@printf("deck valving: total %.0f kg/s (%.0f m3/h)\n", Gsum, Gsum / 760 * 3600)

halves = Dict{String,Any}(); geomv = Dict{String,Any}(); powv = Dict{String,Any}(); burnv = Dict{String,Any}(); qextv = Dict{String,Any}()
for side in ("L", "R")
    idx = sides[side]
    W = sum(speed[i] * prop_pT97(pout, tin_deck).rho for i in idx) * 22.427082e-4   # the whole half
    idx = idx[1:SUB:end]
    pd0 = interp(side, "Psd", 0.0) * KGF
    wfw = interp(side, "Gfw", 0.0) / 3.6; hfw = prop_pT97(pd0, interp(side, "Tfw", 0.0) + 273.15).h
    # inlet mass flux of each channel from the deck's valving; the half's pump flow is their sum
    Gt = [speed[i] * prop_pT97(pout, tin_deck).rho for i in idx]
    Ach = 22.427082e-4
    rho0 = prop_pT97(pd0, tsat97(pd0) - 1).rho
    dpp, _ = pumps_dp(pp, fill(pp.wr, 4), W / rho0, rho0)
    ph0 = pd0 + rho0 * 9.81 * leg.dz + dpp - leg.Kf * W^2 / rho0
    _, tin0 = leg_state(pp, fill(pp.wr, 4), pd0, ph0, W, wfw, hfw)
    @printf("%s: pd %.2f, ph %.2f kgf/cm2, W %.0f kg/s (%.0f m3/h per pump), core inlet %.2f C (Tsat drum %.2f), feedwater %.0f t/h\n",
            side, pd0 / KGF, ph0 / KGF, W, W / rho0 / 4 * 3600, tin0 - 273.15, tsat97(pd0) - 273.15, wfw * 3.6)
    n = length(idx)
    gs = Vector{Any}(undef, n); pows = Vector{Any}(undef, n); bus = Vector{Any}(undef, n); qx = Vector{Any}(undef, n)
    cs = Vector{ColState}(undef, n); lns = Vector{ChanLines}(undef, n); Avs = zeros(n)
    Ptot = sum(pw0) * 1e3
    tclose = @elapsed Threads.@threads for j in 1:n
        i = idx[j]; ix, iy, planes = chans[i]
        g = chan_geom(hz, hx[ix] * hy[iy]; pitch=clus[1], nfuel=clus[2], rc=radius[1], rig=radius[2],
                      rgg=radius[3], nfd=rodm[1], ndtot=rodm[2])
        pow = zeros(nz); bu = zeros(nz); t0 = fill(900.0, nz)
        for (ib, iz) in enumerate(planes)
            ima = (ib - 1) * nch + i
            pow[iz] = pw0[ima] * 1e3; bu[iz] = burn[ima]; t0[iz] = tf0[ima]
        end
        q = pow .* (QgMW * 1e6 / Ptot)
        Lc = ChanLines(Ach=Ach, Ain=pi / 4 * 0.050^2, Din=0.050, Lin=27.5, dzin=11.8 - 12.15,
                       xi_valve=0.81, Aout=pi / 4 * 0.068^2, Dout=0.068, Lout=17.85 + 5.6, dzout=33.65 - 20.0,
                       Kout=2.0, eps_bundle=(18 * 6.79^2 + 7.5^2) / 40.0^2, sourced=false)
        tg = min(tin0, tsat97(pd0) - 1.0)                    # (THM's steady needs a subcooled inlet: a first guess only)
        st = thm_steady(g, o, pow .+ q, bu, Gt[j] / prop_pT97(pd0, tg).rho, tg, pd0; tcomb0=t0)
        c0 = col_from_steady(st, g, Gt[j] / prop_pT97(pd0, tg).rho, tg, pd0)
        Av, dpv, sst = valve_area(g, o, c0, pow, bu, Lc, ph0, pd0, tin0, Gt[j]; qext=q)
        # xi depends on the opening ([ALM98] Fig. 5.5): A = W / sqrt(2 rho dpv / xi(A)), fixed point
        rhoA = prop_pT97(ph0, tin0).rho
        for _ in 1:20
            Av = Gt[j] * Ach / sqrt(2rhoA * dpv / xi_of(Av * 1e6))
        end
        Lc = ChanLines(Ach=Ach, Ain=Lc.Ain, Din=Lc.Din, Lin=Lc.Lin, dzin=Lc.dzin, xi_valve=xi_of(Av * 1e6),
                       Aout=Lc.Aout, Dout=Lc.Dout, Lout=Lc.Lout, dzout=Lc.dzout, Kout=Lc.Kout,
                       eps_bundle=Lc.eps_bundle, sourced=false)
        gs[j] = g; pows[j] = pow; bus[j] = bu; qx[j] = q; cs[j] = sst; lns[j] = Lc; Avs[j] = Av
    end
    @printf("  %s: %d channel throats closed in %.0f s; throat %.2f-%.2f cm2 (mean %.2f)\n", side, n, tclose,
            1e4 * minimum(Avs), 1e4 * maximum(Avs), 1e4 * mean(Avs))
    # the drum at its normal level (1.8 m above the bottom, [MOC07]) at pd0
    R = 1.3; h = 1.8; Al = R^2 * acos((R - h) / R) - (R - h) * sqrt(2R * h - h^2)
    drum = Loop.drum_init(pd0, leg.Vdrum + leg.Vsteam, Al * 60.0)
    halves[side] = LoopHalf(leg, pp, fill(pp.wr, 4), W, ph0, drum, pd0, tin0, cs,
                            [NewtonCache() for _ in 1:n], lns, Avs, fill(Float64(SUB), n))
    geomv[side] = gs; powv[side] = pows; burnv[side] = bus; qextv[side] = qx
end

# ---------------------------------------------------------------- transient
out = open(joinpath(dumpdir, "b3b_loop_core_" * tag * ".csv"), "w")
println(out, "# t_s side pd_kgf ph_kgf W_kgs Q1 Q2 Q3 Q4 (1000 m3/h) tin_C level_m  DREG: Psd Q1 Q2 Q3 Q4 Tin")
Vl0 = Dict(s => (d = halves[s].drum; ps = Loop.sat(halves[s].pd); x = (d.U / d.M - ps.ul) / (ps.ug - ps.ul);
                 d.M * (1 - x) * ps.vl) for s in ("L", "R"))
nst = round(Int, 36.0 / dt)
for n in 1:nst
    t = n * dt
    for side in ("L", "R")
        L = halves[side]
        a = speedfrac(t) * pp.wr
        wfw = interp(side, "Gfw", t) / 3.6; hfw = prop_pT97(L.pd, interp(side, "Tfw", t) + 273.15).h
        tt = @elapsed loop_step!(L, geomv[side], o, powv[side], burnv[side], dt; wst=0.0, wfw, hfw,
                                 pumpmode=Any[:grid, :grid, a, a], qext=qextv[side])
        rho = prop_pT97(L.pd, min(L.tin, tsat97(L.pd) - 1e-6)).rho
        dp, _ = pumps_dp(pp, L.w, L.W / rho, rho)
        Qs = [pump_flow(pp, w, dp, rho) * 3.6 for w in L.w]          # 1000 m3/h
        ps = Loop.sat(L.pd); x = (L.drum.U / L.drum.M - ps.ul) / (ps.ug - ps.ul)
        lev = drum_level(L.drum.M * (1 - x) * ps.vl) - drum_level(Vl0[side])
        dr(p) = interp(side, p, t)
        @printf(out, "%.2f %s %.4f %.4f %.2f %.3f %.3f %.3f %.3f %.3f %.4f  %.2f %.2f %.2f %.2f %.2f %.1f\n", t, side,
                L.pd / KGF, L.ph / KGF, L.W, Qs..., L.tin - 273.15, lev, dr("Psd"), dr("Gmcp1"), dr("Gmcp2"),
                dr("Gmcp3"), dr("Gmcp4"), dr("Tin"))
        flush(out)
        (n % 4 == 0 || n == 1) && @printf("t %5.1f %s pd %.2f (DREG %.2f) ph %.2f  Q %s (DREG %.2f/%.2f/%.2f/%.2f)  Tin %.2f (DREG %.1f)  dlevel %+.0f mm  (%.1f s)\n",
                                          t, side, L.pd / KGF, dr("Psd"), L.ph / KGF, join([@sprintf("%.2f", q) for q in Qs], "/"),
                                          dr("Gmcp1"), dr("Gmcp2"), dr("Gmcp3"), dr("Gmcp4"), L.tin - 273.15, dr("Tin"), 1e3lev, tt)
    end
end
close(out)
