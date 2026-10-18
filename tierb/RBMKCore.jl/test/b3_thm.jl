# B3: the THM: port (RBMKCore.Channel) against DONJON THM: on the same power.
#   julia --project=. -t 8 test/b3_thm.jl steady <fmap with BUND-PW> <fmap with THM's T-FUEL/D-COOL>
#   julia --project=. -t 8 test/b3_thm.jl ramp <refdir>        # tools/tierb_thmref.py output
using RBMKCore.LcmAscii, RBMKCore.Channel, RBMKCore.Water
using Printf, Statistics

const ROOT = joinpath(@__DIR__, "..", "..", "..")
const KSTEM = "rbmk_unit4_a7_acc_pc7e2115_dev_axf527ca_kin700v40g12nofbshvdfr025fi60cc01dt001_vB65c86e_cB4af83e"

# the deck's own THM: keywords (steady call)
deck = read(joinpath(ROOT, "decks", "Donjon", "data", KSTEM * ".don"), String)
blk = deck[findfirst("  THER FMAP := THM: FMAP ::", deck).start:end]
blk = blk[1:findfirst("\n    ;\n", blk).stop]
num(key) = parse.(Float64, split(match(Regex(key * raw"\s+([-0-9.E+ ]+)\n"), blk).captures[1]))
inlet = num("INLET"); radius = num("RADIUS"); clus = num("CLUSTER"); rodm = Int.(num("RODMESH"))
conv = num("CONV"); hgap = num("HGAP")[1]; critfl = num("CRITFL")[1]
sp = blk[findfirst("SPEED CHAN", blk).stop+1:findfirst("CLUSTER", blk).start-1]
speed = [parse(Float64, t) for l in split(sp, '\n') if !startswith(strip(l), "*") for t in split(l)]
@assert length(speed) == 1661 "SPEED CHAN: $(length(speed))"
pout, tin = inlet
println("THM keywords: INLET $inlet CLUSTER $clus RADIUS $radius RODMESH $rodm CONV $conv HGAP $hgap CRITFL $critfl")

function core_layout(recs)
    mx = lcm_get(recs, "MESHX"); my = lcm_get(recs, "MESHY"); mz = lcm_get(recs, "MESHZ")
    nx, ny, nz = length(mx) - 1, length(my) - 1, length(mz) - 1
    bmix = lcm_get(recs, "BMIX")
    chans = Tuple{Int,Int,Vector{Int}}[]        # (ix, iy, fuel planes)
    for iy in 1:ny, ix in 1:nx
        iel = (iy - 1) * nx + ix
        planes = [iz for iz in 1:nz if bmix[(iz-1)*nx*ny+iel] != 0]
        isempty(planes) || push!(chans, (ix, iy, planes))
    end
    (; nx, ny, nz, hx=diff(mx) ./ 100, hy=diff(my) ./ 100, hz=diff(mz) ./ 100, chans)
end

function steady_core(lay, pw, burn, tf0; o)
    nch = length(lay.chans); nb = length(lay.chans[1][3])
    tf = zeros(nch * nb); dc = zeros(nch * nb); states = Vector{Any}(undef, nch)
    Threads.@threads for ich in 1:nch
        ix, iy, planes = lay.chans[ich]
        g = chan_geom(lay.hz, lay.hx[ix] * lay.hy[iy]; pitch=clus[1], nfuel=clus[2], rc=radius[1],
                      rig=radius[2], rgg=radius[3], nfd=rodm[1], ndtot=rodm[2])
        pow = zeros(lay.nz); bu = zeros(lay.nz); t0 = fill(900.0, lay.nz)
        for (ib, iz) in enumerate(planes)
            ima = (ib - 1) * nch + ich
            pow[iz] = pw[ima] * 1e3; bu[iz] = burn[ima]; t0[iz] = tf0[ima]
        end
        st = thm_steady(g, o, pow, bu, speed[ich], tin, pout; tcomb0=t0)
        states[ich] = (g, st, pow, bu)
        for (ib, iz) in enumerate(planes)
            ima = (ib - 1) * nch + ich
            tf[ima] = st.tcomb[iz]; dc[ima] = st.dcool[iz] / 1e3
        end
    end
    tf, dc, states
end

function compare(label, tf, dc, ref)
    rt = ref["T-FUEL"]; rd = ref["D-COOL"]
    dT = tf .- rt; dD = dc .- rd
    @printf("%-10s T-FUEL: max|d| %.4f K  rms %.4f K   D-COOL: max|d| %.2e  rms %.2e g/cc   (ref TF %.1f-%.1f, DC %.4f-%.4f)\n",
            label, maximum(abs.(dT)), sqrt(mean(dT .^ 2)), maximum(abs.(dD)), sqrt(mean(dD .^ 2)),
            extrema(rt)..., extrema(rd)...)
    i = argmax(abs.(dT)); j = argmax(abs.(dD))
    @printf("           worst TF bundle %d: %.3f vs %.3f;  worst DC bundle %d: %.5f vs %.5f\n", i, tf[i], rt[i], j, dc[j], rd[j])
end

mode = ARGS[1]
if mode == "steady"
    rp = lcm_read(ARGS[2]); rr = lcm_read(ARGS[3])
    lay = core_layout(rp)
    pw = lcm_get(rp, "BUND-PW"); burn = lcm_get(rp, "BURN-INST"); ref = lcm_params(rr)
    tf0 = lcm_params(rp)["T-FUEL"]
    o = ThmOpts(cflux=critfl, khgap=hgap, maxit1=Int(conv[1]), maxit2=Int(conv[2]), ermaxt=conv[4])
    @printf("%d channels x %d bundles, P = %.3f MW\n", length(lay.chans), length(lay.chans[1][3]), sum(pw) / 1e3)
    t = @elapsed (tf, dc, _) = steady_core(lay, pw, burn, tf0; o)
    @printf("steady TH of the core: %.1f s\n", t)
    compare("steady", tf, dc, ref)
end
