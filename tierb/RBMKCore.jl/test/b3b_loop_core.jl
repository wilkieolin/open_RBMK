# B3b-3 core-wide loop model, thermal-hydraulics only: 01:23:04 (turbine stop valves shut,
# four MCPs start running down with TG-8) to 01:23:40 (AZ-5), against the DREG record.
#
#   julia --project=. -t 10 test/b3b_loop_core.jl <stem> <dumpdir> [hsh=1.2] [Vsteam=296] [Qg_MW=34] [dt=0.5]
#   env B3B_SUB=n (every n-th channel stands for n; smoke tests), B3B_WDECK=1 (the deck's flows)
#
# Power field: the deck's t = 0 FMAP (BUND-PW, 200 MW), held -- INSAG-7: no power increase
# during the run-down.  Neutronics off.  Boundary conditions, all from records:
#   drums      DREG Psd at 01:23:04 (63.2 L, 64.5 R kgf/cm2, read as ABSOLUTE)
#   steam      none after 01:23:04 (stop valves shut; BRU-K only at 01:23:48)
#   feedwater  DREG Gfw/Tfw per side, interpolated
#   pumps      1, 2 of each side at 1000 rpm (grid); 3, 4 at the speed inferred from the DREG
#              flows (common pressure rise, head curve with shut-off ratio hsh -- the
#              ASSUMPTION), as a linear run-down fitted to all four pumps' inferred points
#   flow       each half's at 01:23:04 = its DREG pump flows; within the half the deck's A7
#              valving (SPEED CHAN) shape.  Each channel's ZRK throat is closed from that
#              state, with xi(A) from [ALM98] Fig. 5.5
#   split      loops by the core's x mid-line (decision 5: an ASSUMPTION, 50/50)
#   graphite   Qg MW into the fuel channels' coolant (tools/graphite_heat.py: 26-40 MW),
#              distributed like the channel power
# Outputs: per side and time, drum pressure, each pump's flow, pump-inlet temperature, the
# drum level change -- each against DREG.  Written to <dumpdir>/b3b_loop_core_<tag>.csv.
using RBMKCore.LcmAscii
include("loop_setup.jl")

stem = ARGS[1]; dumpdir = ARGS[2]
hsh = parse(Float64, get(ARGS, 3, "1.2")); Vst = parse(Float64, get(ARGS, 4, "296"))
QgMW = parse(Float64, get(ARGS, 5, "34")); dt = parse(Float64, get(ARGS, 6, "0.5"))
SUB = parse(Int, get(ENV, "B3B_SUB", "1")); WDECK = get(ENV, "B3B_WDECK", "0") == "1"
tag = @sprintf("h%g_v%g_q%g_dt%g", hsh, Vst, QgMW, dt) * (SUB == 1 ? "" : "_sub$SUB") * (WDECK ? "_wdeck" : "")
dreg = load_dreg()

# ---------------------------------------------------------------- deck and t = 0 FMAP
deckpath = joinpath(LROOT, "decks", "Donjon", "data", stem * ".don")
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
@assert length(chans) == 1661 && length(speed) == 1661
@printf("deck %s: INLET %.4f MPa %.2f K\n", stem, pout / 1e6, tin_deck)

# ---------------------------------------------------------------- pumps, leg, halves
kfit, npts = infer_rundown(dreg, hsh)
@printf("run-down pumps: %d inferred speed points, a(t) = 1 - %.3e t  (a = %.4f at 01:23:40); hsh %.2f (ASSUMPTION)\n",
        npts, kfit, 1 - 36kfit, hsh)
speedfrac(t) = max(0.0, 1 - kfit * t)
pp = PumpParams(hsh=hsh)
leg = leg_unit4(pp; Vsteam=Vst)
@printf("leg: I %.1f 1/m, loss at nominal %.2f kgf/cm2 (pipe %.2f + closed), drum %.0f m3 + steam piping %.0f m3\n",
        leg.I, leg.Kf * 5208^2 / 768 / LKGF, leg.Kpipe * 5208^2 / 768 / LKGF, leg.Vdrum, leg.Vsteam)
H = build_halves(chans, hz, hx, hy, pw0, burn, tf0, speed, pout, tin_deck, clus, radius, rodm, o, pp, leg, QgMW, dreg;
                 sub=SUB, wdreg=!WDECK)

# ---------------------------------------------------------------- transient
out = open(joinpath(dumpdir, "b3b_loop_core_" * tag * ".csv"), "w")
println(out, "# t_s side pd_kgf ph_kgf W_kgs Q1 Q2 Q3 Q4 (1000 m3/h) tin_C level_m  DREG: Psd Q1 Q2 Q3 Q4 Tin")
Vl0 = Dict(s => drum_liquid(H[s].L) for s in ("L", "R"))
for n in 1:round(Int, 36.0 / dt)
    t = n * dt
    for side in ("L", "R")
        L = H[side].L
        a = speedfrac(t) * pp.wr
        wfw = dinterp(dreg, side, "Gfw", t) / 3.6; hfw = prop_pT97(L.pd, dinterp(dreg, side, "Tfw", t) + 273.15).h
        tt = @elapsed loop_step!(L, H[side].g, o, H[side].pow, H[side].burn, dt; wst=0.0, wfw, hfw,
                                 pumpmode=Any[:grid, :grid, a, a], qext=H[side].qext)
        rho = prop_pT97(L.pd, min(L.tin, tsat97(L.pd) - 1e-6)).rho
        dp, _ = pumps_dp(pp, L.w, L.W / rho, rho)
        Qs = [pump_flow(pp, w, dp, rho) * 3.6 for w in L.w]          # 1000 m3/h
        lev = drum_level(drum_liquid(L)) - drum_level(Vl0[side])
        dr(p) = dinterp(dreg, side, p, t)
        @printf(out, "%.2f %s %.4f %.4f %.2f %.3f %.3f %.3f %.3f %.3f %.4f  %.2f %.2f %.2f %.2f %.2f %.1f\n", t, side,
                L.pd / LKGF, L.ph / LKGF, L.W, Qs..., L.tin - 273.15, lev, dr("Psd"), dr("Gmcp1"), dr("Gmcp2"),
                dr("Gmcp3"), dr("Gmcp4"), dr("Tin"))
        flush(out)
        (n % 4 == 0 || n == 1) && (@printf("t %5.1f %s pd %.2f (DREG %.2f) ph %.2f  Q %s (DREG %.2f/%.2f/%.2f/%.2f)  Tin %.2f (DREG %.1f)  dlevel %+.0f mm  (%.1f s)\n",
                                           t, side, L.pd / LKGF, dr("Psd"), L.ph / LKGF, join([@sprintf("%.2f", q) for q in Qs], "/"),
                                           dr("Gmcp1"), dr("Gmcp2"), dr("Gmcp3"), dr("Gmcp4"), L.tin - 273.15, dr("Tin"), 1e3lev, tt);
                                   flush(stdout))
    end
end
close(out)
