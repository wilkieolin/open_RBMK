# B1 input gate: the per-element cross sections the engine builds from the
# deck (mixture map, fuel map, XS tables, rod devices) against DONJON's own
# MACRD after NCR + MACINI + NEWMAC (tools/tierb_export_core.py).
using RBMKCore.XS, RBMKCore.CoreModel, HDF5, Printf, Test

const ROOT = joinpath(@__DIR__, "..", "..", "..")
const STEM = "rbmk_unit4_core_dev_axf527ca_cB4af83e"
d = read_deck(joinpath(ROOT, "decks", "Donjon", "data", STEM * ".don"))
println("deck: $(d.nx)x$(d.ny)x$(d.nz), $(count(==(8), d.mix)) fuel elements, ",
        "$(length(d.burnup)) burnups, $(length(d.rods)) rods, fuel state $(d.fuelstate)")
xsf = joinpath(ROOT, "tierb", "xs", "tierb_xs_664b244a.h5")
fuel = load_fuel(xsf); ref = load_ref(xsf)
x = element_xs(d, fuel, ref)

h = h5open(joinpath(ROOT, "tierb", "xs", STEM, "b1ref.h5"))
idx = Int.(read(h["matex"]["INDEX"]))
@test (idx .> 0) == (d.mix .> 0)
ntotR = read(h["macrd"]["NTOT0"]); diffR = read(h["macrd"]["DIFF"]); scR = read(h["macrd"]["SCAT"])
hR = read(h["macrd"]["H-FACTOR"]); nu = read(h["macrd"]["NUSIGF"]); chi = read(h["macrd"]["CHI"])
close(h)
els = findall(>(0), idx)
worst = Dict{String,Tuple{Float64,Int}}()
note(k, r, e) = (r > get(worst, k, (0.0, 0))[1]) && (worst[k] = (r, e))
for e in els
    r = idx[e]
    for g in 1:2
        note("NTOT0", abs(x.ntot[e,g] - ntotR[g,r]) / ntotR[g,r], e)
        note("DIFF", abs(1 / x.invd[e,g] - diffR[g,r]) / diffR[g,r], e)
        hR[g,r] != 0 && note("H-FACTOR", abs(x.hfac[e,g] - hR[g,r]) / abs(hR[g,r]), e)
        for gf in 1:2
            s = scR[gf, g, r]
            s != 0 && note("SCAT", abs(x.scat[e,g,gf] - s) / abs(s), e)
            F = sum(chi[g, i, r] * nu[gf, i, r] for i in axes(nu, 2))
            F != 0 && note("FISS", abs(x.fiss[e,g,gf] - F) / abs(F), e)
        end
    end
end
for (k, (v, e)) in sort(collect(worst))
    @printf("%-9s worst relative difference %.2e  (element %d, mixture %d)\n", k, v, e, d.mix[e])
    @test v <= 1e-5
end
