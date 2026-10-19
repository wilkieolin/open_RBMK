# B3b-3 scaffold checks (Loop.jl): drum, pumps, and a loop half of two channel columns
# standing for its 830 channels.  Geometry placeholders as in b3b_lines_setup.jl
# (sourced=false); the drum pressure is DREG's pre-AZ-5 66.8 kgf/cm2 read as absolute.
using RBMKCore.Channel, RBMKCore.Column, RBMKCore.Column.Lines, RBMKCore.Loop, RBMKCore.IF97, Printf
import RBMKCore.Column.Lines as LN
const KGF = 98066.5

println("== drum")
V = leg_unit4().Vdrum
for p in (6.0e6, 6.551e6, 7.384e6)
    d = drum_init(p, V, 0.5V)
    p2, s = drum_pressure(d, V)
    @printf("  p %.4f MPa -> drum_pressure %.6f MPa (rel %.1e); M %.0f t, U %.3e J\n", p / 1e6, p2 / 1e6, p2 / p - 1, d.M / 1e3, d.U)
end
let p = 6.551e6, d = drum_init(p, V, 0.5V)
    s = Loop.sat(p); x = 0.05; W = 5000.0; hin = s.hl + x * (s.hg - s.hl); wst = W * x
    for n in 1:100; d, _ = drum_step(d, V, 0.01, [W], [hin], W - wst, wst); end
    p2, _ = drum_pressure(d, V)
    @printf("  balanced flows 1 s: dp %.3e Pa, dM %.3e kg\n", p2 - p, d.M - drum_init(p, V, 0.5V).M)
    d = drum_init(p, V, 0.5V)
    for n in 1:100; d, _ = drum_step(d, V, 0.01, [W], [hin], W - wst, 0.0); end
    p3, _ = drum_pressure(d, V)
    @printf("  steam outlet shut, %.0f kg/s of x=%.2f mixture in: dp/dt %.1f kPa/s (INSAG-7 p. 60 records ~6 kPa/s; here no steam-line volume, no feedwater cooling)\n",
            W, x, (p3 - p) / 1e3)
end

println("== pump (rated point; ASSUMPTION hsh = $(pump_mcp().hsh))")
pp = pump_mcp(); rho = 760.0
@printf("  head at rated: %.1f m; torque %.0f N m (= Pshaft/wr %.0f)\n", pump_head(pp, pp.wr, pp.Qr, rho) / (rho * 9.81),
        pump_torque(pp, pp.wr, pp.Qr, rho), pp.Pshaft / pp.wr)
let w = pp.wr, t = 0.0
    # free coastdown into a fixed quadratic system (Q ~ w): J dw/dt = -T
    ts = Float64[]
    while w > 0.1pp.wr
        Q = pp.Qr * w / pp.wr; w -= 0.01 * pump_torque(pp, w, Q, rho) / pp.J; t += 0.01
        (isempty(ts) && w < 0.5pp.wr) && push!(ts, t)
    end
    @printf("  free coastdown on a quadratic system: half speed at %.1f s, 10 %% at %.1f s ([ALM98]: full stop 120-300 s)\n", ts[1], t)
end

println("== loop half: two columns standing for 415 + 415 channels")
include("b3b_lines_setup.jl")             # g, o, pow, bu, tin, L (lines), st, ...
pdd = 66.8KGF
tind = tsat97(pdd) - 3.0
leg = leg_unit4()
cs = ColState[]; lines = ChanLines[]; Avs = Float64[]; geoms = []; pows = []; burns = []
Gins = [2587.0, 2200.0]; pfs = [1.0, 0.6]
# header pressure from the leg at the channels' total flow, rated pump speed
rho_l = prop_pT97(pdd, tind).rho
Wtot = sum(415 * G * L.Ach for G in Gins)
Qp = Wtot / rho_l / leg.npump
phd = pdd + rho_l * 9.81 * leg.dz + pump_head(pp, pp.wr, Qp, rho_l) - leg.Kf * Wtot^2 / rho_l
@printf("  W %.0f kg/s (%.0f m3/h per pump), ph - pd %.2f kgf/cm2 (no throttling-valve loss: open item)\n", Wtot, Qp * 3600, (phd - pdd) / KGF)
for (G, f) in zip(Gins, pfs)
    s0 = thm_steady(g, o, pow .* f, bu, G / prop_pT97(pdd, tind).rho, tind, pdd)
    c = col_from_steady(s0, g, G / prop_pT97(pdd, tind).rho, tind, pdd)
    local Av, dpv, sst = valve_area(g, o, c, pow .* f, bu, L, phd, pdd, tind, G)
    @printf("  channel P x%.1f: Gin %.0f, valve dp %.2f kgf/cm2, throat %.2f cm2\n", f, G, dpv / KGF, Av * 1e4)
    push!(cs, sst); push!(lines, L); push!(Avs, Av); push!(geoms, g); push!(pows, pow .* f); push!(burns, bu)
end
kmax = findlast(!=(0.0), pow)
s = Loop.sat(pdd)
wout = [415 * c.G[kmax] * L.Ach for c in cs]; hout = [c.h[kmax] for c in cs]
wst0 = sum(wout .* (hout .- s.hl)) / (s.hg - s.hl)        # steam made (feedwater at h_l,sat: null test)
drum = drum_init(pdd, leg.Vdrum, 0.5leg.Vdrum)
LH = LoopHalf(leg, pp, fill(pp.wr, leg.npump), Wtot, phd, drum, drum_pressure(drum, leg.Vdrum)[1], cs,
              [NewtonCache() for _ in cs], lines, Avs, [415.0, 415.0])
println("  -- null, 0.5 s")
for n in 1:50
    loop_step!(LH, geoms, o, pows, burns, i -> tind, 0.01; tleg=tind, wst=wst0, wfw=wst0, hfw=s.hl)
    n % 10 == 0 && @printf("    t %.2f  W %.2f kg/s  ph %.5f  pd %.5f kgf/cm2\n", n * 0.01, LH.W, LH.ph / KGF, LH.pd / KGF)
end
println("  -- turbine stop (steam out -> 0), two pumps free-running down, 3 s")
for n in 1:300
    loop_step!(LH, geoms, o, pows, burns, i -> tind, 0.01; tleg=tind, wst=0.0, wfw=wst0, hfw=s.hl,
               pumpmode=[:grid, :grid, :coast, :coast])
    n % 50 == 0 && @printf("    t %.2f  W %.1f kg/s  pumps %s rpm  ph %.3f  pd %.3f kgf/cm2  x_out %.4f/%.4f\n",
                           n * 0.01, LH.W, join(round.(Int, LH.w .* 60 / 2pi), "/"), LH.ph / KGF, LH.pd / KGF,
                           LH.chans[1].xfl[kmax], LH.chans[2].xfl[kmax])
end

println("== the core-inlet state the loop predicts (no imposed subcooling)")
# DREG 01:23:00-01:23:39, per loop half: drum 66.8 kgf/cm2 (read as absolute), feedwater ~150 t/h
# at ~165 C, MCP inlet temperature recorded 281 C; total flow 56 000 m3/h (INSAG-7 p. 64), 8 pumps.
for (lab, pdk) in (("absolute", 66.8), ("gauge (+1 at)", 67.8))
    pd = pdk * KGF
    ws = fill(pp.wr, 4)
    rho = prop_pT97(pd, tsat97(pd) - 1).rho
    W = 28000.0 / 3600 * rho
    dpp, _ = pumps_dp(pp, ws, W / rho, rho)
    ph = pd + rho * 9.81 * leg_unit4().dz + dpp - leg_unit4().Kf * W^2 / rho
    hfw = prop_pT97(pd, 165.0 + 273.15).h
    hleg, Tleg = leg_state(pp, ws, pd, ph, W, 150 / 3.6, hfw)
    Tpi = let hl = Loop.sat(pd).hl; hm = ((W - 150 / 3.6) * hl + 150 / 3.6 * hfw) / W
        Tq = tsat97(pd) - 1; for _ in 1:30; q = prop_pT97(pd + 2e5, Tq); Tq += (hm - q.h) / q.cp; end; Tq end
    @printf("  Psd %s: drum Tsat %.2f C; pump inlet %.2f C (DREG 281); after pumps %.2f C; group-header Tsat %.2f C\n",
            lab, tsat97(pd) - 273.15, Tpi - 273.15, Tleg - 273.15, tsat97(ph) - 273.15)
    @printf("      subcooling against the drum pressure %.2f K; against the core-bottom pressure (~pd + 3 kgf/cm2) %.2f K (INSAG-7: 3)\n",
            tsat97(pd) - Tleg, tsat97(pd + 3KGF) - Tleg)
end
