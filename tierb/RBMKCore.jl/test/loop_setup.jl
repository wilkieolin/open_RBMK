# Shared set-up of the B3b-3 core-wide loop model (used by b3b_loop_core.jl and b4_coupled.jl
# with B4_TH=loop).  See b3b_loop_core.jl's header for every input's source.
using RBMKCore.Channel, RBMKCore.Column, RBMKCore.Column.Lines, RBMKCore.Loop, RBMKCore.IF97
import RBMKCore
using Printf, Statistics

const LKGF = 98066.5
const LROOT = joinpath(@__DIR__, "..", "..", "..")

"""DREG analogue record: Dict((side, param) => [(t s after 01:23:04, value)])."""
function load_dreg()
    dreg = Dict{Tuple{String,String},Vector{Tuple{Float64,Float64}}}()
    for l in eachline(joinpath(LROOT, "sources", "derived", "dreg_mfcc_full.csv"))
        (startswith(l, "#") || startswith(l, "side")) && continue
        side, tm, p, v = split(l, ",")
        tryparse(Float64, v) === nothing && continue
        h, m, s = parse.(Int, split(tm, ":"))
        push!(get!(dreg, (String(side), String(p)), Tuple{Float64,Float64}[]),
              ((h - 1) * 3600 + (m - 23) * 60 + s - 4.0, parse(Float64, v)))
    end
    for v in values(dreg); sort!(v); end
    dreg
end
function dinterp(dreg, side, p, t)
    pts = dreg[(side, p)]
    t <= pts[1][1] && return pts[1][2]
    t >= pts[end][1] && return pts[end][2]
    k = findlast(x -> x[1] <= t, pts); (t0, v0), (t1, v1) = pts[k], pts[k+1]
    v0 + (v1 - v0) * (t - t0) / (t1 - t0)
end

"""Linear run-down a(t) = 1 - k t of pumps 3, 4 fitted to the speeds the DREG flows imply
(common pressure rise with pumps 1, 2 at grid speed; head curve with shut-off ratio hsh)."""
function infer_rundown(dreg, hsh; tmax=36.0)
    apts = Tuple{Float64,Float64}[]
    for side in ("L", "R")
        ts = sort(unique([t for p in ("Gmcp1", "Gmcp2", "Gmcp3", "Gmcp4") for (t, _) in dreg[(side, p)]]))
        for t in ts
            (0.0 <= t <= tmax) || continue
            val(p) = (x = filter(z -> z[1] == t, dreg[(side, p)]); isempty(x) ? nothing : x[1][2])
            g = filter(!isnothing, [val("Gmcp1"), val("Gmcp2")]); c = filter(!isnothing, [val("Gmcp3"), val("Gmcp4")])
            (isempty(g) || isempty(c)) && continue
            vg = mean(g) / 8.0
            for q in c
                push!(apts, (t, sqrt(max(0.0, (hsh - (hsh - 1) * (vg^2 - (q / 8.0)^2)) / hsh))))
            end
        end
    end
    -sum(t * (a - 1) for (t, a) in apts) / sum(t^2 for (t, _) in apts), length(apts)
end

# [ALM98] Fig. 5.5: ZRK loss coefficient against throat area (mm2)
const XIA = [(54.0, 1.39), (102.0, 1.39), (153.0, 0.98), (206.0, 0.84), (263.0, 0.85), (319.0, 0.70),
             (437.0, 0.68), (691.0, 0.65)]
function xi_of(Amm2)
    Amm2 <= XIA[1][1] && return XIA[1][2]; Amm2 >= XIA[end][1] && return XIA[end][2]
    k = findlast(x -> x[1] <= Amm2, XIA); (a0, x0), (a1, x1) = XIA[k], XIA[k+1]
    x0 + (x1 - x0) * (Amm2 - a0) / (a1 - a0)
end

"""
Build both loop halves at 01:23:04.  chans: (ix, iy, fuel planes) per channel in the core's
order; pw0/burn/tf0 per bundle (BUND-PW kW, BURN, T-FUEL) in FMAP order (ib-1)*nch + ich;
speed: the deck's SPEED CHAN.  Returns a NamedTuple of per-side vectors (global channel indices
`idx`, geometries, powers, burns, graphite heat) and the LoopHalf objects.
"""
function build_halves(chans, hz, hx, hy, pw0, burn, tf0, speed, pout, tin_deck, clus, radius, rodm, o, pp, leg,
                      QgMW, dreg; sub=1)
    nch = length(chans); nz = length(hz)
    xmid = 0.5 * (minimum(c[1] for c in chans) + maximum(c[1] for c in chans))
    sides = Dict("L" => [i for i in 1:nch if chans[i][1] <= xmid], "R" => [i for i in 1:nch if chans[i][1] > xmid])
    Ach = 22.427082e-4
    rdeck = prop_pT97(pout, tin_deck).rho
    Ptot = sum(pw0) * 1e3
    out = Dict{String,Any}()
    for side in ("L", "R")
        W = sum(speed[i] * rdeck for i in sides[side]) * Ach
        idx = sides[side][1:sub:end]
        pd0 = dinterp(dreg, side, "Psd", 0.0) * LKGF
        wfw = dinterp(dreg, side, "Gfw", 0.0) / 3.6; hfw = prop_pT97(pd0, dinterp(dreg, side, "Tfw", 0.0) + 273.15).h
        Gt = [speed[i] * rdeck for i in idx]
        rho0 = prop_pT97(pd0, tsat97(pd0) - 1).rho
        dpp, _ = pumps_dp(pp, fill(pp.wr, 4), W / rho0, rho0)
        ph0 = pd0 + rho0 * 9.81 * leg.dz + dpp - leg.Kf * W^2 / rho0
        _, tin0 = leg_state(pp, fill(pp.wr, 4), pd0, ph0, W, wfw, hfw)
        @printf("%s: %d channels; pd %.2f, ph %.2f kgf/cm2, W %.0f kg/s (%.0f m3/h per pump), core inlet %.2f C (drum Tsat %.2f), feedwater %.0f t/h\n",
                side, length(sides[side]), pd0 / LKGF, ph0 / LKGF, W, W / rho0 / 4 * 3600, tin0 - 273.15,
                tsat97(pd0) - 273.15, wfw * 3.6)
        n = length(idx)
        gs = Vector{Any}(undef, n); pows = Vector{Vector{Float64}}(undef, n); bus = Vector{Any}(undef, n)
        qx = Vector{Vector{Float64}}(undef, n)
        cs = Vector{ColState}(undef, n); lns = Vector{ChanLines}(undef, n); Avs = zeros(n)
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
            tg = min(tin0, tsat97(pd0) - 1.0)
            st = thm_steady(g, o, pow .+ q, bu, Gt[j] / prop_pT97(pd0, tg).rho, tg, pd0; tcomb0=t0)
            c0 = col_from_steady(st, g, Gt[j] / prop_pT97(pd0, tg).rho, tg, pd0)
            Av, dpv, sst = valve_area(g, o, c0, pow, bu, Lc, ph0, pd0, tin0, Gt[j]; qext=q)
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
        R = 1.3; h = 1.8; Al = R^2 * acos((R - h) / R) - (R - h) * sqrt(2R * h - h^2)
        drum = Loop.drum_init(pd0, leg.Vdrum + leg.Vsteam, Al * 60.0)
        LH = LoopHalf(leg, pp, fill(pp.wr, 4), W, ph0, drum, pd0, tin0, cs, [NewtonCache() for _ in 1:n], lns, Avs,
                      fill(Float64(sub), n))
        out[side] = (L=LH, idx=idx, g=gs, pow=pows, burn=bus, qext=qx, Ptot=Ptot, QgMW=QgMW)
    end
    out
end

"""Liquid volume in the drums of a loop half (for level changes)."""
function drum_liquid(L::LoopHalf)
    ps = Loop.sat(L.pd); x = (L.drum.U / L.drum.M - ps.ul) / (ps.ug - ps.ul)
    L.drum.M * (1 - x) * ps.vl
end
