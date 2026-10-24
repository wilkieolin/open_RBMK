# Single-channel check of the boiling-crisis / post-CHF wall model (ThmOpts.postchf, PROGRESS (49)):
# one channel of the band-B deck on the Newton path at THM's boundary conditions (fixed inlet flux
# and outlet pressure), driven by the bundle powers of a b4_coupled newton run (b4_pw_*.bin every
# 0.1 s from 3.5 s; before that the 3.5 s shape scaled by the trace's P/P0), postchf off and on.
#   julia --project=. test/chf_single.jl <stem> <dumpdir> <channel> [chfmul=1]
import RBMKCore
using RBMKCore.LcmAscii, RBMKCore.Channel, RBMKCore.Column, RBMKCore.IF97, Printf
using RBMKCore.Column.Lines: col_step_newton_flux, NewtonCache
using Serialization
stem, D, ich = ARGS[1], ARGS[2], parse(Int, ARGS[3]); mul = parse(Float64, get(ARGS, 4, "1"))
deck = read(joinpath(@__DIR__, "..", "..", "..", "decks", "Donjon", "data", stem * ".don"), String)
blk = deck[findfirst("  THER FMAP := THM: FMAP ::", deck).start:end]; blk = blk[1:findfirst("\n    ;\n", blk).stop]
num(key) = parse.(Float64, split(match(Regex(key * raw"\s+([-0-9.E+ ]+)\n"), blk).captures[1]))
pout, tin = num("INLET"); radius = num("RADIUS"); clus = num("CLUSTER"); rodm = Int.(num("RODMESH"))
conv = num("CONV"); hgap = num("HGAP")[1]; critfl = num("CRITFL")[1]
sp = blk[findfirst("SPEED CHAN", blk).stop+1:findfirst("CLUSTER", blk).start-1]
speed = [parse(Float64, t) for l in split(sp, '\n') if !startswith(strip(l), "*") for t in split(l)]
tr = match(r"THM: THER FMAP :: EDIT 0 TIME <<t0>> <<dt>> HISTORY 2\s+CONV (\S+) (\S+) (\S+) (\S+) (\S+) CYCLE-OK (\S+) FLOW-RELAX (\S+) ;", deck)
tv = parse.(Float64, tr.captures)
o_s = ThmOpts(cflux=critfl, khgap=hgap, maxit1=Int(conv[1]), maxit2=Int(conv[2]), ermaxt=conv[4])
mk(post; zrsec=false) = ThmOpts(zrsec=zrsec, cflux=critfl, khgap=hgap, maxit1=Int(tv[1]), maxit2=Int(tv[2]), maxitc=Int(tv[3]), ermaxt=tv[4],
                   ermaxc=tv[5], cyccap=tv[6], frlx=tv[7], postchf=post, chfmul=mul)
rf = lcm_read(joinpath(D, "fmap0.asc")); par = lcm_params(rf)
tf = par["T-FUEL"]; pw0 = lcm_get(rf, "BUND-PW"); burn = lcm_get(rf, "BURN-INST")
mx = lcm_get(rf, "MESHX"); my = lcm_get(rf, "MESHY"); mz = lcm_get(rf, "MESHZ"); bmix = lcm_get(rf, "BMIX")
nx, ny, nz = length(mx) - 1, length(my) - 1, length(mz) - 1
hx, hy, hz = diff(mx) ./ 100, diff(my) ./ 100, diff(mz) ./ 100
chans = Tuple{Int,Int,Vector{Int}}[]
for iy in 1:ny, ix in 1:nx
    iel = (iy - 1) * nx + ix; planes = [iz for iz in 1:nz if bmix[(iz-1)*nx*ny+iel] != 0]
    isempty(planes) || push!(chans, (ix, iy, planes))
end
nch = length(chans); ix, iy, planes = chans[ich]
g = chan_geom(hz, hx[ix] * hy[iy]; pitch=clus[1], nfuel=clus[2], rc=radius[1], rig=radius[2], rgg=radius[3], nfd=rodm[1], ndtot=rodm[2])
pow0 = zeros(nz); bu = zeros(nz); t0 = fill(900.0, nz)
for (ib, iz) in enumerate(planes); k = (ib-1)*nch+ich; pow0[iz] = pw0[k]*1e3; bu[iz] = burn[k]; t0[iz] = tf[k]; end
st = thm_steady(g, o_s, pow0, bu, speed[ich], tin, pout; tcomb0=t0)
s00 = col_from_steady(st, g, speed[ich], tin, pout)
Gin = speed[ich] * prop_pT97(pout, tin).rho
# power history
trc = [parse.(Float64, split(l)) for l in eachline(joinpath(D, "b4_trace_dt0.01_newton.txt")) if !startswith(l, "#")]
io = open(joinpath(D, "b4_pw_dt0.01_newton.bin")); snaps = Tuple{Float64,Vector{Float64}}[]
while !eof(io); t = read(io, Float64); v = Vector{Float64}(undef, nch*28); read!(io, v); push!(snaps, (t, [v[(ib-1)*nch+ich] for ib in 1:28])); end
P(t) = (k = findmin(abs.([r[1] for r in trc] .- t))[2]; trc[k][2])
function chpow(t)
    sh = if t < snaps[1][1]
        snaps[1][2] .* (P(t) / P(snaps[1][1]))
    else
        k = min(searchsortedlast([s[1] for s in snaps], t), length(snaps) - 1)
        f = clamp((t - snaps[k][1]) / (snaps[k+1][1] - snaps[k][1]), 0, 1); (1 - f) .* snaps[k][2] .+ f .* snaps[k+1][2]
    end
    pw = zeros(nz); for (ib, iz) in enumerate(planes); pw[iz] = sh[ib] * 1e3; end; pw
end
@printf("channel %d (ix %d iy %d): inlet %.3f m/s, t=0 %.0f kW, hottest-bundle peak %.0f kW\n", ich, ix, iy, speed[ich],
        sum(pow0)/1e3, maximum(maximum(s[2]) for s in snaps))
res = Dict{Any,Any}()
for post in (false, true, :zrsec)
    o = post === :zrsec ? mk(false; zrsec=true) : mk(post); s = deepcopy(s00); cache = NewtonCache(); out = []
    for n in 1:700
        t = 0.01n
        s = try
            col_step_newton_flux(g, o, s, chpow(t), bu, Gin, tin, 0.01; cache)
        catch e
            @printf("postchf=%s: failed at t = %.2f s (%s); last Tclad %.1f C\n", post, t, sprint(showerror, e)[1:min(end, 80)],
                    isempty(out) ? NaN : out[end][2])
            haskey(ENV, "THMROD_DEBUG") && serialize(ENV["THMROD_DEBUG"], RBMKCore.Channel.FAILROD[])
            break
        end
        nd = g.ndtot
        push!(out, (t, maximum(s.temps[nd, k] for k in planes) - 273.15, count(k -> s.kwa[k] >= 4, planes),
                    maximum(s.temps[1, k] for k in planes) - 273.15, minimum(s.rho[k] for k in planes)))
    end
    res[post] = out
end
println("   t    | off: Tclad_max  Tcl_fuel rho_min | on: Tclad_max  dry nodes  Tcl_fuel rho_min | zrsec only: Tclad rho_min")
for n in (100, 300, 400, 450, 480, 500, 510, 520, 530, 550, 575, 600, 650, 700)
    (n <= length(res[false]) && n <= length(res[true])) || continue
    a = res[false][n]; b = res[true][n]; c = res[:zrsec][n]
    @printf("%6.2f | %8.1f %8.1f %6.1f | %8.1f %4d %8.1f %6.1f | %8.1f %6.1f\n", a[1], a[2], a[4], a[5], b[2], b[3], b[4], b[5], c[2], c[5])
end
k1 = findfirst(r -> r[3] > 0, res[true])
println(k1 === nothing ? "no dryout" : @sprintf("first dry node at %.2f s; identical before: %s", res[true][k1][1],
        all(res[true][n][2] == res[:zrsec][n][2] for n in 1:min(k1-1, length(res[:zrsec])))) * " (against zrsec only)")
